"""Hybrid Analysis Data Collector.

Handles multi-source data collection for hybrid Python/AI analysis.
Extracted from hybrid_analysis_flow.py for single responsibility.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import logging
from typing import Any

logger = logging.getLogger(__name__)


class HybridDataCollector:
    """Collects raw data from multiple sources for hybrid analysis."""

    def __init__(self):
        """Initialize with DataSourceOrchestrator."""
        from finwiz.data.data_source_orchestrator import DataSourceOrchestrator

        self.data_orchestrator = DataSourceOrchestrator(
            total_timeout=10.0,
            per_source_timeout=3.0,
            enable_validation=True,
        )
        self.logger = logger

    def collect_raw_data(
        self,
        ticker: str,
        asset_class: str,
        existing_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Collect raw data for analysis using DataSourceOrchestrator.

        Args:
            ticker: Stock ticker symbol
            asset_class: Asset class (stock, etf, crypto)
            existing_data: Pre-populated data (if available)

        Returns:
            Dictionary containing all raw data needed for analysis
        """
        # If raw_data already provided for THIS ticker, use it
        if existing_data and existing_data.get("ticker") == ticker:
            self.logger.info(f"Using pre-populated raw_data for {ticker}")
            return existing_data

        self.logger.info(f"Collecting raw data for {ticker} ({asset_class}) using DataSourceOrchestrator")

        collected_data = {
            "ticker": ticker,
            "asset_class": asset_class,
        }

        asset_class_lower = asset_class.lower()
        if asset_class_lower == "stock":
            collected_data = self._collect_stock_data(ticker, collected_data)
        elif asset_class_lower == "etf":
            collected_data = self._collect_etf_data(ticker, collected_data)
        elif asset_class_lower == "crypto":
            collected_data = self._collect_crypto_data(ticker, collected_data)

        return collected_data

    def _collect_stock_data(self, ticker: str, collected_data: dict[str, Any]) -> dict[str, Any]:
        """Collect stock-specific fundamental data using DataSourceOrchestrator."""
        try:
            # Handle event loop scenarios
            try:
                loop = asyncio.get_running_loop()
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    orchestration_result = executor.submit(
                        asyncio.run,
                        self.data_orchestrator.get_fundamental_data(ticker, sector=None),
                    ).result()
            except RuntimeError:
                orchestration_result = asyncio.run(
                    self.data_orchestrator.get_fundamental_data(ticker, sector=None)
                )

            # Extract fundamental metrics
            if orchestration_result.return_on_equity is not None:
                collected_data["roe"] = orchestration_result.return_on_equity
                self.logger.debug(f"Got roe: {orchestration_result.return_on_equity}")

            if orchestration_result.debt_to_equity is not None:
                collected_data["debt_to_equity"] = orchestration_result.debt_to_equity
                self.logger.debug(f"Got debt_to_equity: {orchestration_result.debt_to_equity}")

            if orchestration_result.revenue_growth is not None:
                collected_data["revenue_growth"] = orchestration_result.revenue_growth
                self.logger.debug(f"Got revenue_growth: {orchestration_result.revenue_growth}")

            if orchestration_result.profit_margin is not None:
                collected_data["profit_margin"] = orchestration_result.profit_margin
                self.logger.debug(f"Got profit_margin: {orchestration_result.profit_margin}")

            # Store orchestration metadata
            collected_data["data_lineage"] = orchestration_result.lineage.to_dict()
            collected_data["data_confidence"] = orchestration_result.confidence
            collected_data["data_sources_attempted"] = orchestration_result.sources_attempted
            collected_data["data_sources_succeeded"] = orchestration_result.sources_succeeded
            collected_data["used_fallback"] = orchestration_result.used_fallback

            if orchestration_result.warnings:
                self.logger.warning(f"Data orchestration warnings for {ticker}: {orchestration_result.warnings}")

            self.logger.info(
                f"DataSourceOrchestrator completed: completeness={orchestration_result.get_completeness_score():.1%}, "
                f"confidence={orchestration_result.confidence:.2f}, "
                f"sources={orchestration_result.sources_succeeded}"
            )

        except Exception as e:
            self.logger.error(f"DataSourceOrchestrator failed for {ticker}: {e}", exc_info=True)
            self.logger.warning(f"Continuing with partial data for {ticker}")

        return collected_data

    def _collect_etf_data(self, ticker: str, collected_data: dict[str, Any]) -> dict[str, Any]:
        """Collect ETF-specific data."""
        try:
            self.logger.info(f"🐍 Collecting ETF data for {ticker}")
            from finwiz.tools.enhanced_etf_tool import EnhancedETFAnalysisTool

            etf_tool = EnhancedETFAnalysisTool()
            etf_result = etf_tool._run(
                ticker=ticker,
                include_factsheet=True,
                include_risk_assessment=False,
                include_perplexity=False,
            )

            if isinstance(etf_result, dict):
                etf_data = etf_result.get("etf_data", etf_result)

                collected_data["expense_ratio"] = etf_data.get("expense_ratio", 0.0)
                collected_data["aum"] = etf_data.get("aum", 0.0)
                collected_data["tracking_error"] = etf_data.get("tracking_error", 0.0)
                collected_data["dividend_yield"] = etf_data.get("dividend_yield", 0.0)

                self.logger.info(
                    f"✅ Got ETF data: expense_ratio={collected_data['expense_ratio']}, "
                    f"aum={collected_data['aum']}, tracking_error={collected_data['tracking_error']}"
                )
                collected_data["etf_info"] = etf_result
            else:
                self.logger.warning(f"⚠️ ETF tool returned unexpected type: {type(etf_result)}")
                self._set_etf_defaults(collected_data)

        except Exception as e:
            self.logger.error(f"❌ ETF data collection failed for {ticker}: {e}", exc_info=True)
            self._set_etf_defaults(collected_data)

        return collected_data

    def _set_etf_defaults(self, collected_data: dict[str, Any]) -> None:
        """Set default values for ETF when data collection fails."""
        collected_data["expense_ratio"] = 0.005  # Default 0.5%
        collected_data["aum"] = 1e9  # Default $1B AUM
        collected_data["tracking_error"] = 0.01  # Default 1%
        collected_data["etf_info"] = {}

    def _collect_crypto_data(self, ticker: str, collected_data: dict[str, Any]) -> dict[str, Any]:
        """Collect crypto-specific data."""
        try:
            self.logger.info(f"🐍 Collecting crypto data for {ticker}")
            from finwiz.tools.enhanced_crypto_tool import EnhancedCryptoAnalysisTool

            crypto_tool = EnhancedCryptoAnalysisTool()
            crypto_result = crypto_tool._run(
                symbol=ticker,
                include_thesis=False,
                include_risk_assessment=False,
                include_perplexity=False,
            )

            if isinstance(crypto_result, dict):
                crypto_data = crypto_result.get("crypto_data", crypto_result)

                # Map total_volume to volume_24h (CoinGecko uses total_volume)
                collected_data["volume_24h"] = crypto_data.get(
                    "total_volume", crypto_data.get("volume_24h", 0.0)
                )
                collected_data["market_cap"] = crypto_data.get("market_cap", 0.0)
                collected_data["circulating_supply"] = crypto_data.get("circulating_supply", 0.0)
                collected_data["max_supply"] = crypto_data.get(
                    "max_supply", crypto_data.get("total_supply", 0.0)
                )

                # Calculate age from known mapping
                collected_data["age_years"] = self._get_crypto_age(ticker)

                self.logger.info(
                    f"✅ Got crypto data: volume_24h={collected_data['volume_24h']}, "
                    f"age_years={collected_data['age_years']}, market_cap={collected_data['market_cap']}"
                )
                collected_data["crypto_info"] = crypto_result
            else:
                self.logger.warning(f"⚠️ Crypto tool returned unexpected type: {type(crypto_result)}")
                self._set_crypto_defaults(collected_data, ticker)

        except Exception as e:
            self.logger.error(f"❌ Crypto data collection failed for {ticker}: {e}", exc_info=True)
            self._set_crypto_defaults(collected_data, ticker)

        return collected_data

    def _get_crypto_age(self, ticker: str) -> float:
        """Get crypto age in years from known mapping."""
        age_mapping = {
            "BTC": 15.0, "BTC-USD": 15.0,
            "ETH": 9.0, "ETH-USD": 9.0,
            "ADA": 7.0, "ADA-USD": 7.0,
            "SOL": 4.0, "SOL-USD": 4.0,
            "AVAX": 4.0, "AVAX-USD": 4.0,
            "DOT": 4.0, "DOT-USD": 4.0,
        }
        ticker_base = ticker.replace("-USD", "").upper()
        return age_mapping.get(ticker_base, 3.0)

    def _set_crypto_defaults(self, collected_data: dict[str, Any], ticker: str) -> None:
        """Set default values for crypto when data collection fails."""
        collected_data["volume_24h"] = 1e9  # Default $1B volume
        collected_data["age_years"] = self._get_crypto_age(ticker)
        collected_data["market_cap"] = 10e9  # Default $10B market cap
        collected_data["crypto_info"] = {}
