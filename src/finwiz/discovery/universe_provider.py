"""
Dynamic universe provider for newcomer discovery.

Mines ETF holdings via yfinance to build candidate ticker universes,
with fallback to static ScreeningUtils lists when yfinance fails.
"""

from __future__ import annotations

from typing import Any, ClassVar

import yfinance as yf
from crewai_custom_tools.tools.analytics.screening_utils import ScreeningUtils

from finwiz.tools.logger import get_logger


class DynamicUniverseProvider:
    """Provides dynamic ticker universes by mining ETF holdings and static lists."""

    # Default seed ETFs for mining stock holdings
    DEFAULT_STOCK_SEED_ETFS: ClassVar[list[str]] = [
        "SPY",
        "QQQ",
        "VTI",
        "VGT",
        "VHT",
        "VFH",
        "VNQ",
        "XLE",
    ]
    DEFAULT_ETF_SEED_ETFS: ClassVar[list[str]] = [
        "VT",
        "AOA",
        "AOR",
    ]  # ETFs-of-ETFs for ETF discovery
    MARKET_REGION: ClassVar[str] = "us"

    def __init__(self, seed_etfs: list[str] | None = None) -> None:
        """Initialize with optional seed ETF overrides.

        Args:
            seed_etfs: Override default stock seed ETFs. If None, uses DEFAULT_STOCK_SEED_ETFS.
        """
        self._seed_etfs = seed_etfs
        self._screening_utils = ScreeningUtils()
        self._logger = get_logger(__name__)

    def get_universe(
        self,
        asset_class: str,
        exclude_tickers: list[str] | None = None,
    ) -> list[str]:
        """Get a ticker universe for the given asset class.

        Args:
            asset_class: One of "stock", "etf", "crypto".
            exclude_tickers: Tickers to exclude from the result.

        Returns:
            Sorted, deduplicated list of ticker symbols.
        """
        exclude_set = {t.upper() for t in (exclude_tickers or [])}
        source = "dynamic"

        if asset_class == "crypto":
            # yfinance doesn't have crypto ETF holdings, go straight to static
            tickers = self._fallback_static_universe("crypto")
            source = "static"
        else:
            seed_etfs = self._seed_etfs or self.DEFAULT_STOCK_SEED_ETFS if asset_class == "stock" else self.DEFAULT_ETF_SEED_ETFS
            try:
                tickers = self._mine_etf_holdings(seed_etfs)
            except (ValueError, Exception):
                self._logger.warning(
                    "Dynamic universe failed for %s, falling back to static",
                    asset_class,
                )
                tickers = self._fallback_static_universe(asset_class)
                source = "static"

            if not tickers:
                tickers = self._fallback_static_universe(asset_class)
                source = "static"

        # Deduplicate, filter exclusions, sort
        result = sorted({t.upper() for t in tickers} - exclude_set)

        self._logger.info(
            "Universe for %s: %d tickers (source=%s, excluded=%d)",
            asset_class,
            len(result),
            source,
            len(exclude_set),
        )
        return result

    def _mine_etf_holdings(self, etf_tickers: list[str]) -> list[str]:
        """Mine holdings from multiple seed ETFs.

        Args:
            etf_tickers: List of ETF tickers to mine holdings from.

        Returns:
            Sorted, deduplicated list of holding tickers.

        Raises:
            ValueError: If no holdings found from any seed ETF.
        """
        all_tickers: set[str] = set()

        for etf_ticker in etf_tickers:
            holdings = self._fetch_single_etf_holdings(etf_ticker)
            all_tickers.update(holdings)

        if not all_tickers:
            msg = "No holdings found from any seed ETF"
            raise ValueError(msg)

        return sorted(all_tickers)

    def _fetch_single_etf_holdings(self, etf_ticker: str) -> list[str]:
        """Fetch top holdings from a single ETF via yfinance.

        Args:
            etf_ticker: ETF ticker symbol (e.g. "SPY").

        Returns:
            List of holding ticker symbols. Empty list on any failure.
        """
        try:
            ticker_obj = yf.Ticker(etf_ticker)
            funds_data = ticker_obj.get_funds_data()
            holdings_df = funds_data.top_holdings

            if holdings_df is None or holdings_df.empty:
                self._logger.warning("No holdings data for ETF %s", etf_ticker)
                return []

            # Index contains the symbol names
            symbols = [str(sym).upper() for sym in holdings_df.index if sym is not None and str(sym).strip()]

            self._logger.debug(
                "Mined %d holdings from %s",
                len(symbols),
                etf_ticker,
            )
            return symbols

        except (ValueError, KeyError, OSError):
            self._logger.warning(
                "Failed to fetch holdings for ETF %s",
                etf_ticker,
                exc_info=True,
            )
            return []

    def _fallback_static_universe(self, asset_class: str) -> list[str]:
        """Get a static ticker universe from ScreeningUtils.

        Args:
            asset_class: One of "stock", "etf", "crypto".

        Returns:
            List of ticker symbols. Empty list on error.
        """
        try:
            result: dict[str, Any] = self._screening_utils.get_screening_universe(
                asset_class,
                self.MARKET_REGION,
            )

            if "error" in result:
                self._logger.warning(
                    "Static universe error for %s: %s",
                    asset_class,
                    result["error"],
                )
                return []

            symbols: list[str] = result.get("symbols", [])
            self._logger.debug(
                "Static universe for %s: %d symbols",
                asset_class,
                len(symbols),
            )
            return symbols

        except (ValueError, KeyError, AttributeError):
            self._logger.warning(
                "Failed to get static universe for %s",
                asset_class,
                exc_info=True,
            )
            return []
