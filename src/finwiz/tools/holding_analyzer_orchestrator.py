"""
Holding Analyzer Orchestrator - Coordinates deep analysis across stock/ETF/crypto crews.

This module orchestrates individual holding analysis by:
- Checking for existing crew analysis (< 7 days old)
- Triggering appropriate crew if analysis missing/stale
- Mapping crew outputs to portfolio review schema
- Handling analysis failures with graceful fallback
- Implementing performance optimizations (caching, parallel processing, rate limiting)
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from finwiz.schemas.portfolio_review import AssetClass
from finwiz.tools.logger import get_logger
from finwiz.utils.cache_manager import CacheConfig, CacheManager, cache_key
from finwiz.utils.rate_limiter import get_rate_limiter

logger = get_logger(__name__)


class HoldingAnalysis(BaseModel):
    """Complete analysis for a single holding."""

    # Basic info
    ticker: str
    name: str
    asset_class: AssetClass
    currency: str

    # Analysis data
    fundamental_analysis: dict | None = None
    technical_analysis: dict | None = None
    sec_citations: list[dict] = Field(default_factory=list)

    # Metadata
    analysis_date: datetime
    data_freshness: Literal["fresh", "recent", "stale"]
    crew_analysis_used: str | None = None
    composite_score: float = Field(ge=0.0, le=1.0, default=0.65)
    confidence_level: float = Field(ge=0.0, le=1.0, default=0.5)


class HoldingAnalyzerOrchestrator:
    """Orchestrate deep analysis for portfolio holdings across crews with performance optimizations."""

    def __init__(
        self,
        output_dir: Path = Path("output"),
        enable_caching: bool = True,
        enable_rate_limiting: bool = True,
        parallel_batch_size: int = 10,
    ) -> None:
        """
        Initialize the orchestrator with performance optimizations.

        Args:
            output_dir: Base output directory for crew outputs
            enable_caching: Enable intelligent caching (default: True)
            enable_rate_limiting: Enable rate limiting (default: True)
            parallel_batch_size: Number of holdings to process in parallel (default: 10)

        """
        self.output_dir = output_dir
        self.stock_output_dir = output_dir / "stock"
        self.etf_output_dir = output_dir / "etf"
        self.crypto_output_dir = output_dir / "crypto"

        # Performance optimization settings
        self.enable_caching = enable_caching
        self.enable_rate_limiting = enable_rate_limiting
        self.parallel_batch_size = parallel_batch_size

        # Initialize cache manager with custom config for portfolio analysis
        if self.enable_caching:
            self.cache_manager = CacheManager(
                config=CacheConfig(
                    default_ttl=604800,  # 7 days for crew analysis
                    max_memory_items=500,  # Support large portfolios
                    cache_directory="cache/portfolio_analysis",
                    auto_cleanup=True,
                    cleanup_interval=3600,  # Cleanup every hour
                )
            )
            logger.info("Cache manager initialized for portfolio analysis")
        else:
            self.cache_manager = None

        # Initialize rate limiter
        if self.enable_rate_limiting:
            self.rate_limiter = get_rate_limiter()
            logger.info("Rate limiter initialized")
        else:
            self.rate_limiter = None

        # Connection pool for HTTP requests (simulated - would use httpx.AsyncClient in production)
        self._connection_pool_size = 10
        self._active_connections = 0

    async def analyze_holdings_parallel(
        self,
        holdings: list[dict[str, Any]],
    ) -> list[HoldingAnalysis]:
        """
        Analyze multiple holdings in parallel with batching and rate limiting.

        Args:
            holdings: List of holding dicts with ticker, asset_class, currency, name

        Returns:
            List of HoldingAnalysis results

        """
        logger.info(f"Starting parallel analysis of {len(holdings)} holdings")
        start_time = datetime.now()

        results = []
        total_batches = (len(holdings) + self.parallel_batch_size - 1) // self.parallel_batch_size

        # Process holdings in batches to avoid overwhelming the system
        for batch_idx in range(0, len(holdings), self.parallel_batch_size):
            batch = holdings[batch_idx : batch_idx + self.parallel_batch_size]
            batch_num = batch_idx // self.parallel_batch_size + 1

            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} holdings)")

            # Create async tasks for batch
            tasks = [
                self.analyze_holding_async(
                    ticker=h.get("ticker", ""),
                    asset_class=h.get("asset_class", "stock"),
                    currency=h.get("currency", "USD"),
                    name=h.get("name", ""),
                )
                for h in batch
            ]

            # Execute batch in parallel
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Handle results and exceptions
            for holding, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    logger.error(
                        f"Error analyzing {holding.get('ticker')}: {result}",
                        extra={"ticker": holding.get("ticker"), "error": str(result)},
                    )
                    # Create baseline analysis for failed holdings
                    result = self._create_baseline_analysis(
                        ticker=holding.get("ticker", ""),
                        asset_class=holding.get("asset_class", "stock"),
                        currency=holding.get("currency", "USD"),
                        name=holding.get("name", ""),
                    )

                results.append(result)

            # Small delay between batches to respect rate limits
            if batch_idx + self.parallel_batch_size < len(holdings):
                await asyncio.sleep(1.0)

        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(
            f"Completed parallel analysis of {len(holdings)} holdings in {elapsed:.2f}s",
            extra={
                "total_holdings": len(holdings),
                "elapsed_seconds": elapsed,
                "avg_per_holding": elapsed / len(holdings) if holdings else 0,
            },
        )

        return results

    async def analyze_holding_async(
        self,
        ticker: str,
        asset_class: AssetClass,
        currency: str,
        name: str = "",
    ) -> HoldingAnalysis:
        """
        Async version of analyze_holding for parallel processing.

        Args:
            ticker: Ticker symbol
            asset_class: Asset class (stock/etf/crypto)
            currency: Currency denomination
            name: Holding name (optional)

        Returns:
            HoldingAnalysis with crew-specific data mapped to schema

        """
        logger.debug(
            "Analyzing holding (async)",
            extra={
                "ticker": ticker,
                "asset_class": asset_class,
                "currency": currency,
            },
        )

        # Check cache first (with async support)
        if self.enable_caching and self.cache_manager:
            cache_key_str = cache_key("holding_analysis", ticker, asset_class)
            cached_result = await self.cache_manager.get(cache_key_str)

            if cached_result:
                logger.info(
                    "Cache hit for holding analysis",
                    extra={"ticker": ticker, "asset_class": asset_class},
                )
                return cached_result

        # Check for crew output files
        cached_analysis = self.get_cached_analysis(ticker, asset_class, max_age_days=7)

        if cached_analysis:
            logger.info(
                "Using cached crew output",
                extra={
                    "ticker": ticker,
                    "cache_age_days": cached_analysis.get("age_days", 0),
                },
            )
            result = self._map_cached_to_holding_analysis(
                ticker=ticker,
                asset_class=asset_class,
                currency=currency,
                name=name,
                cached_data=cached_analysis,
            )

            # Store in cache manager for faster future access
            if self.enable_caching and self.cache_manager:
                await self.cache_manager.set(
                    cache_key_str,
                    result,
                    ttl=604800,  # 7 days
                    tags={"holding_analysis", asset_class},
                )

            return result

        # No cache - return baseline with warning
        logger.warning(
            "No fresh crew analysis available, using baseline",
            extra={"ticker": ticker, "asset_class": asset_class},
        )

        result = self._create_baseline_analysis(
            ticker=ticker,
            asset_class=asset_class,
            currency=currency,
            name=name,
        )

        # Cache baseline result with shorter TTL
        if self.enable_caching and self.cache_manager:
            await self.cache_manager.set(
                cache_key_str,
                result,
                ttl=3600,  # 1 hour for baseline
                tags={"holding_analysis", "baseline", asset_class},
            )

        return result

    def analyze_holding(
        self,
        ticker: str,
        asset_class: AssetClass,
        currency: str,
        name: str = "",
    ) -> HoldingAnalysis:
        """
        Analyze a single holding (synchronous version).

        This is the main entry point for synchronous usage.
        For async usage, use analyze_holding_async() directly.

        Args:
            ticker: Ticker symbol
            asset_class: Asset class (stock/etf/crypto)
            currency: Currency denomination
            name: Holding name (optional)

        Returns:
            HoldingAnalysis with crew-specific data mapped to schema

        """
        logger.debug(
            "Analyzing holding (sync)",
            extra={
                "ticker": ticker,
                "asset_class": asset_class,
                "currency": currency,
            },
        )

        # Check for crew output files
        cached_analysis = self.get_cached_analysis(ticker, asset_class, max_age_days=7)

        if cached_analysis:
            logger.info(
                "Using cached crew output",
                extra={
                    "ticker": ticker,
                    "cache_age_days": cached_analysis.get("age_days", 0),
                },
            )
            return self._map_cached_to_holding_analysis(
                ticker=ticker,
                asset_class=asset_class,
                currency=currency,
                name=name,
                cached_data=cached_analysis,
            )

        # No cache - return baseline with warning
        logger.warning(
            "No fresh crew analysis available, using baseline",
            extra={"ticker": ticker, "asset_class": asset_class},
        )

        return self._create_baseline_analysis(
            ticker=ticker,
            asset_class=asset_class,
            currency=currency,
            name=name,
        )

    def get_cached_analysis(
        self,
        ticker: str,
        asset_class: AssetClass,
        max_age_days: int = 7,
    ) -> dict | None:
        """
        Check for recent crew analysis output.

        Args:
            ticker: Ticker symbol
            asset_class: Asset class to determine output directory
            max_age_days: Maximum age in days for cache validity

        Returns:
            Cached analysis dict if found and fresh, None otherwise

        """
        # Determine output directory based on asset class
        if asset_class == "stock":
            output_dir = self.stock_output_dir
        elif asset_class == "etf":
            output_dir = self.etf_output_dir
        elif asset_class == "crypto":
            output_dir = self.crypto_output_dir
        else:
            logger.warning(f"Unknown asset class: {asset_class}")
            return None

        # Check for latest symlink first
        latest_file = output_dir / f"{asset_class}_latest.json"
        if latest_file.exists():
            try:
                with open(latest_file) as f:
                    data = json.load(f)

                # Check if this analysis is for our ticker
                # (crew outputs may contain multiple tickers)
                if self._contains_ticker_analysis(data, ticker):
                    # Check age
                    file_mtime = datetime.fromtimestamp(latest_file.stat().st_mtime)
                    age = datetime.now() - file_mtime
                    age_days = age.days

                    if age_days <= max_age_days:
                        logger.info(
                            "Found cached analysis",
                            extra={
                                "ticker": ticker,
                                "age_days": age_days,
                                "file": str(latest_file),
                            },
                        )
                        data["age_days"] = age_days
                        return data

                    logger.info(
                        "Cached analysis too old",
                        extra={"ticker": ticker, "age_days": age_days},
                    )
            except Exception as e:
                logger.error(
                    "Error reading cached analysis",
                    extra={"ticker": ticker, "error": str(e)},
                )

        return None

    def _contains_ticker_analysis(self, data: dict, ticker: str) -> bool:
        """
        Check if crew output contains analysis for the given ticker.

        Args:
            data: Crew output data
            ticker: Ticker to search for

        Returns:
            True if ticker analysis found

        """
        # Check various possible locations in crew output
        # This is a simplified check - actual implementation would be more robust
        raw_output = data.get("raw_output", "")
        if ticker.upper() in raw_output.upper():
            return True

        # Check pydantic output if present
        pydantic_output = data.get("pydantic")
        if pydantic_output and isinstance(pydantic_output, dict):
            ticker_field = pydantic_output.get("ticker", "")
            if ticker.upper() == ticker_field.upper():
                return True

        return False

    def _map_cached_to_holding_analysis(
        self,
        ticker: str,
        asset_class: AssetClass,
        currency: str,
        name: str,
        cached_data: dict,
    ) -> HoldingAnalysis:
        """
        Map cached crew output to HoldingAnalysis schema.

        Args:
            ticker: Ticker symbol
            asset_class: Asset class
            currency: Currency
            name: Holding name
            cached_data: Cached crew output

        Returns:
            HoldingAnalysis with mapped data

        """
        age_days = cached_data.get("age_days", 0)

        # Determine freshness
        if age_days <= 2:
            freshness = "fresh"
        elif age_days <= 7:
            freshness = "recent"
        else:
            freshness = "stale"

        # Extract analysis data from crew output
        fundamental_analysis = self._extract_fundamental_analysis(cached_data, asset_class)
        technical_analysis = self._extract_technical_analysis(cached_data)
        sec_citations = self._extract_sec_citations(cached_data)

        # Extract composite score if available
        composite_score = self._extract_composite_score(cached_data)

        return HoldingAnalysis(
            ticker=ticker,
            name=name or ticker,
            asset_class=asset_class,
            currency=currency,
            fundamental_analysis=fundamental_analysis,
            technical_analysis=technical_analysis,
            sec_citations=sec_citations,
            analysis_date=datetime.now(),
            data_freshness=freshness,
            crew_analysis_used=f"{asset_class}_crew",
            composite_score=composite_score,
            confidence_level=0.8 if freshness == "fresh" else 0.6,
        )

    def _extract_fundamental_analysis(self, data: dict, asset_class: AssetClass) -> dict | None:
        """Extract fundamental analysis from crew output."""
        # For stocks: look for 10-K insights, financial metrics
        if asset_class == "stock":
            pydantic_output = data.get("pydantic")
            if pydantic_output and isinstance(pydantic_output, dict):
                return {
                    "ten_k_insights": pydantic_output.get("ten_k_insights", {}),
                    "financial_metrics": pydantic_output.get("financial_metrics", {}),
                }

        # For ETFs: look for expense ratio, holdings, tracking error
        elif asset_class == "etf":
            pydantic_output = data.get("pydantic")
            if pydantic_output and isinstance(pydantic_output, dict):
                return {
                    "expense_ratio": pydantic_output.get("expense_ratio"),
                    "tracking_error": pydantic_output.get("tracking_error"),
                    "holdings": pydantic_output.get("holdings", []),
                }

        return None

    def _extract_technical_analysis(self, data: dict) -> dict | None:
        """Extract technical analysis from crew output."""
        pydantic_output = data.get("pydantic")
        if pydantic_output and isinstance(pydantic_output, dict):
            return {
                "technical_indicators": pydantic_output.get("technical_indicators", {}),
                "price_patterns": pydantic_output.get("price_patterns", {}),
            }
        return None

    def _extract_sec_citations(self, data: dict) -> list[dict]:
        """Extract SEC citations from crew output."""
        pydantic_output = data.get("pydantic")
        if pydantic_output and isinstance(pydantic_output, dict):
            citations = pydantic_output.get("sec_citations", [])
            if isinstance(citations, list):
                return citations
        return []

    def _extract_composite_score(self, data: dict) -> float:
        """Extract composite score from crew output."""
        pydantic_output = data.get("pydantic")
        if pydantic_output and isinstance(pydantic_output, dict):
            score = pydantic_output.get("composite_score")
            if isinstance(score, (int, float)):
                return float(score)
        return 0.65  # Default baseline

    def _create_baseline_analysis(
        self,
        ticker: str,
        asset_class: AssetClass,
        currency: str,
        name: str,
    ) -> HoldingAnalysis:
        """
        Create baseline analysis when no crew data available.

        Args:
            ticker: Ticker symbol
            asset_class: Asset class
            currency: Currency
            name: Holding name

        Returns:
            Baseline HoldingAnalysis

        """
        # Baseline scores by asset class
        baseline_scores = {
            "stock": 0.60,
            "etf": 0.65,
            "crypto": 0.55,
        }

        return HoldingAnalysis(
            ticker=ticker,
            name=name or ticker,
            asset_class=asset_class,
            currency=currency,
            fundamental_analysis=None,
            technical_analysis=None,
            sec_citations=[],
            analysis_date=datetime.now(),
            data_freshness="stale",
            crew_analysis_used=None,
            composite_score=baseline_scores.get(asset_class, 0.60),
            confidence_level=0.3,  # Low confidence for baseline
        )

    def trigger_crew_analysis(
        self,
        ticker: str,
        asset_class: AssetClass,
    ) -> dict[str, Any]:
        """
        Trigger appropriate crew for fresh analysis.

        Note: This is a placeholder for future implementation.
        In production, this would actually kick off the crew.

        Args:
            ticker: Ticker symbol
            asset_class: Asset class to determine which crew to use

        Returns:
            Crew analysis output

        """
        logger.info(
            "Triggering crew analysis",
            extra={"ticker": ticker, "asset_class": asset_class},
        )

        # Placeholder - would actually trigger crew in production
        raise NotImplementedError("Crew triggering not yet implemented - use cached analysis or baseline")
