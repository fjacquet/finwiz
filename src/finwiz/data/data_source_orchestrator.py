"""Data source orchestrator for multi-source fundamental data acquisition."""

import asyncio
import builtins
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from finwiz.data.adapters.alpha_vantage_adapter import AlphaVantageAdapter
from finwiz.data.adapters.base_adapter import (
    BaseDataAdapter,
    DataAcquisitionError,
    FundamentalData,
    InvalidDataError,
    TimeoutError,
)
from finwiz.data.adapters.eod_adapter import EODAdapter
from finwiz.data.adapters.industry_averages import IndustryAveragesAdapter
from finwiz.data.adapters.intrinio_adapter import IntrinioAdapter
from finwiz.data.adapters.tiingo_adapter import TiingoAdapter
from finwiz.data.adapters.yfinance_adapter import YFinanceAdapter
from finwiz.tools.logger import get_logger


@dataclass
class DataLineage:
    """Track which source provided each field."""

    return_on_equity_source: str | None = None
    debt_to_equity_source: str | None = None
    revenue_growth_source: str | None = None
    profit_margin_source: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        """Convert to dictionary."""
        return {
            "return_on_equity": self.return_on_equity_source,
            "debt_to_equity": self.debt_to_equity_source,
            "revenue_growth": self.revenue_growth_source,
            "profit_margin": self.profit_margin_source,
        }


@dataclass
class OrchestrationResult:
    """Result from data source orchestration."""

    ticker: str
    timestamp: datetime

    # Fundamental data
    return_on_equity: float | None = None
    debt_to_equity: float | None = None
    revenue_growth: float | None = None
    profit_margin: float | None = None

    # Metadata
    lineage: DataLineage = field(default_factory=DataLineage)
    confidence: float = 0.0
    sources_attempted: list[str] = field(default_factory=list)
    sources_succeeded: list[str] = field(default_factory=list)
    sources_failed: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    used_fallback: bool = False

    def is_complete(self) -> bool:
        """Check if all fields have been populated."""
        return all(
            [
                self.return_on_equity is not None,
                self.debt_to_equity is not None,
                self.revenue_growth is not None,
                self.profit_margin is not None,
            ]
        )

    def get_completeness_score(self) -> float:
        """Get completeness score (0.0 to 1.0)."""
        fields = [
            self.return_on_equity,
            self.debt_to_equity,
            self.revenue_growth,
            self.profit_margin,
        ]
        populated = sum(1 for f in fields if f is not None)
        return populated / len(fields)


class DataSourceOrchestrator:
    """Orchestrate multi-source fundamental data acquisition with waterfall fallback.

    Waterfall Strategy:
    1. YFinance (primary, fast, free)
    2. Alpha Vantage (fallback, good fundamentals)
    3. Intrinio (fallback, SEC filings)
    4. Tiingo/EOD (international stocks)
    5. Industry Averages (last resort)

    Features:
    - 10-second total timeout across all sources
    - 3-second timeout per source
    - Data validation (reject invalid values)
    - Data lineage tracking
    - Automatic fallback on failure
    """

    def __init__(
        self,
        total_timeout: float = 10.0,
        per_source_timeout: float = 3.0,
        enable_validation: bool = True,
    ) -> None:
        """Initialize data source orchestrator.

        Args:
            total_timeout: Maximum time for entire orchestration (default 10.0s)
            per_source_timeout: Maximum time per data source (default 3.0s)
            enable_validation: Enable data validation (default True)
        """
        self.total_timeout = total_timeout
        self.per_source_timeout = per_source_timeout
        self.enable_validation = enable_validation
        self.logger = get_logger(__name__)

        # Initialize adapters in priority order (all implement async interface)
        self.adapters: list[BaseDataAdapter] = [
            YFinanceAdapter(timeout_seconds=per_source_timeout),
            AlphaVantageAdapter(timeout_seconds=per_source_timeout),
            IntrinioAdapter(timeout_seconds=per_source_timeout),
            TiingoAdapter(timeout_seconds=per_source_timeout),
            EODAdapter(timeout_seconds=per_source_timeout),
        ]

        # Industry averages as last resort
        self.fallback_adapter = IndustryAveragesAdapter()

    async def get_fundamental_data(
        self,
        ticker: str,
        sector: str | None = None,
    ) -> OrchestrationResult:
        """Get fundamental data using waterfall strategy.

        Args:
            ticker: Stock ticker symbol
            sector: Industry sector (for fallback only)

        Returns:
            OrchestrationResult with fundamental data and metadata
        """
        start_time = datetime.now()
        result = OrchestrationResult(
            ticker=ticker,
            timestamp=start_time,
        )

        try:
            # Try to get data with total timeout
            await asyncio.wait_for(self._orchestrate_data_acquisition(ticker, sector, result), timeout=self.total_timeout)
        except builtins.TimeoutError:
            self.logger.warning(f"Total timeout ({self.total_timeout}s) exceeded for {ticker}")
            result.warnings.append(f"Total timeout ({self.total_timeout}s) exceeded")

        # If still incomplete, use industry averages as last resort
        if not result.is_complete():
            self.logger.warning(f"Using industry averages for {ticker} - completeness: {result.get_completeness_score():.1%}")
            await self._apply_fallback(ticker, sector, result)

        # Calculate final confidence
        result.confidence = self._calculate_confidence(result)

        return result

    async def _orchestrate_data_acquisition(
        self,
        ticker: str,
        sector: str | None,
        result: OrchestrationResult,
    ) -> None:
        """Orchestrate data acquisition across sources."""
        for adapter in self.adapters:
            # Skip if already complete
            if result.is_complete():
                break

            # Skip if adapter not available
            if not adapter.is_available():
                self.logger.debug(f"Skipping {adapter.source_name} - not available")
                continue

            # Try to get data from this source
            result.sources_attempted.append(adapter.source_name)

            try:
                data = await adapter.get_fundamental_data(ticker)

                # Validate data if enabled
                if self.enable_validation and not data.is_valid():
                    self.logger.warning(f"{adapter.source_name} returned invalid data for {ticker}")
                    result.sources_failed.append(adapter.source_name)
                    result.warnings.append(f"{adapter.source_name}: Data failed validation")
                    continue

                # Merge data into result
                self._merge_data(data, result)
                result.sources_succeeded.append(adapter.source_name)

                self.logger.debug(f"{adapter.source_name} provided data for {ticker} - completeness: {result.get_completeness_score():.1%}")

            except (DataAcquisitionError, TimeoutError, InvalidDataError) as e:
                self.logger.debug(f"{adapter.source_name} failed for {ticker}: {e}")
                result.sources_failed.append(adapter.source_name)
                result.warnings.append(f"{adapter.source_name}: {e!s}")
            except Exception as e:
                self.logger.error(f"Unexpected error from {adapter.source_name} for {ticker}: {e}")
                result.sources_failed.append(adapter.source_name)
                result.warnings.append(f"{adapter.source_name}: Unexpected error - {e!s}")

    def _merge_data(self, data: FundamentalData, result: OrchestrationResult) -> None:
        """Merge data from source into result (only fill missing fields)."""
        # Only fill fields that are still None
        if result.return_on_equity is None and data.return_on_equity is not None:
            result.return_on_equity = data.return_on_equity
            result.lineage.return_on_equity_source = data.source

        if result.debt_to_equity is None and data.debt_to_equity is not None:
            result.debt_to_equity = data.debt_to_equity
            result.lineage.debt_to_equity_source = data.source

        if result.revenue_growth is None and data.revenue_growth is not None:
            result.revenue_growth = data.revenue_growth
            result.lineage.revenue_growth_source = data.source

        if result.profit_margin is None and data.profit_margin is not None:
            result.profit_margin = data.profit_margin
            result.lineage.profit_margin_source = data.source

        # Merge warnings
        if data.warnings:
            result.warnings.extend([f"{data.source}: {w}" for w in data.warnings])

    async def _apply_fallback(
        self,
        ticker: str,
        sector: str | None,
        result: OrchestrationResult,
    ) -> None:
        """Apply industry averages as fallback for missing fields."""
        try:
            fallback_data = await self.fallback_adapter.get_fundamental_data(ticker, sector)

            # Only fill fields that are still None
            self._merge_data(fallback_data, result)

            result.used_fallback = True
            result.sources_attempted.append("IndustryAverages")
            result.sources_succeeded.append("IndustryAverages")
            result.warnings.append("Used industry averages for missing fields")

        except Exception as e:
            self.logger.error(f"Fallback failed for {ticker}: {e}")
            result.warnings.append(f"Fallback failed: {e!s}")

    def _calculate_confidence(self, result: OrchestrationResult) -> float:
        """Calculate confidence score based on data sources and completeness."""
        # Base confidence on completeness
        completeness = result.get_completeness_score()

        # Adjust based on sources used
        if result.used_fallback:
            # Low confidence if using industry averages
            confidence = 0.5 * completeness
        elif "YFinance" in result.sources_succeeded:
            # High confidence if primary source succeeded
            confidence = 0.95 * completeness
        elif any(s in result.sources_succeeded for s in ["AlphaVantage", "Intrinio"]):
            # Good confidence if secondary sources succeeded
            confidence = 0.85 * completeness
        elif any(s in result.sources_succeeded for s in ["Tiingo", "EOD"]):
            # Moderate confidence if tertiary sources succeeded
            confidence = 0.75 * completeness
        else:
            # Low confidence if no sources succeeded
            confidence = 0.3 * completeness

        return confidence

    def get_available_adapters(self) -> list[str]:
        """Get list of available adapter names."""
        available = [adapter.source_name for adapter in self.adapters if adapter.is_available()]
        available.append("IndustryAverages")  # Always available
        return available

    def get_adapter_info(self) -> list[dict[str, Any]]:
        """Get information about all adapters."""
        info = [adapter.get_source_info() for adapter in self.adapters]
        info.append(self.fallback_adapter.get_source_info())
        return info
