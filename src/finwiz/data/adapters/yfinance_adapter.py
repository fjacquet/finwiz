"""Async wrapper for YFinance adapter."""

import asyncio
from datetime import datetime
from typing import Any

try:
    import yfinance as yf
except ImportError:
    yf = None

import builtins

from finwiz.config.yfinance_config import configure_yfinance
from finwiz.tools.logger import get_logger

from .base_adapter import BaseDataAdapter, DataAcquisitionError, FundamentalData, TimeoutError


class YFinanceAdapter(BaseDataAdapter):
    """YFinance adapter for fundamental data acquisition.

    Primary adapter for US stocks. Fast and free, but sometimes missing data.
    Uses yfinance v1.0+ retry mechanism for improved reliability.
    """

    def __init__(self, timeout_seconds: float = 3.0) -> None:
        super().__init__(timeout_seconds)
        self.logger = get_logger(__name__)

        if yf is None:
            self.logger.warning("yfinance not installed, YFinanceAdapter will be unavailable")
        else:
            # Configure yfinance with centralized settings (retry mechanism, etc.)
            configure_yfinance()

    @property
    def source_name(self) -> str:
        """Return the name of this data source."""
        return "yfinance"

    def is_available(self) -> bool:
        """Check if yfinance is available."""
        return yf is not None

    async def get_fundamental_data(self, ticker: str) -> FundamentalData:
        """Get fundamental data from yfinance.

        Args:
            ticker: Stock ticker symbol

        Returns:
            FundamentalData with available metrics

        Raises:
            DataAcquisitionError: If data cannot be acquired
            TimeoutError: If request times out
        """
        if not self.is_available():
            raise DataAcquisitionError("yfinance not available")

        try:
            # Run yfinance call in thread pool to avoid blocking
            data = await asyncio.wait_for(asyncio.get_event_loop().run_in_executor(None, self._fetch_yfinance_data, ticker), timeout=self.timeout_seconds)

            return self._parse_yfinance_data(ticker, data)

        except builtins.TimeoutError:
            raise TimeoutError(f"YFinance request timed out after {self.timeout_seconds}s for {ticker}")
        except Exception as e:
            raise DataAcquisitionError(f"YFinance error for {ticker}: {str(e)}")

    def _fetch_yfinance_data(self, ticker: str) -> dict:
        """Fetch data from yfinance (blocking call)."""
        try:
            stock = yf.Ticker(ticker)
            info: dict[str, Any] = stock.info

            if not info or "symbol" not in info:
                raise DataAcquisitionError(f"No data returned for {ticker}")

            return info

        except Exception as e:
            self.logger.debug(f"YFinance fetch error for {ticker}: {e}")
            raise

    def _parse_yfinance_data(self, ticker: str, data: dict) -> FundamentalData:
        """Parse yfinance data into standardized format."""
        warnings = []

        # Extract ROE
        roe = self._extract_float(data, "returnOnEquity", warnings, "ROE")

        # Extract Debt to Equity
        debt_to_equity = self._extract_float(data, "debtToEquity", warnings, "Debt-to-equity")

        # Extract Revenue Growth
        revenue_growth = self._extract_float(data, "revenueGrowth", warnings, "Revenue growth")

        # Extract Profit Margin
        profit_margin = self._extract_float(data, "profitMargins", warnings, "Profit margin")

        # Create FundamentalData object
        fundamental_data = FundamentalData(
            ticker=ticker,
            source="YFinance",
            timestamp=datetime.now(),
            confidence=1.0,  # YFinance is primary source
            return_on_equity=roe,
            debt_to_equity=debt_to_equity,
            revenue_growth=revenue_growth,
            profit_margin=profit_margin,
            raw_data=data,
            warnings=warnings,
        )

        if warnings:
            self.logger.debug(f"YFinance warnings for {ticker}: {warnings}")

        return fundamental_data

    def _extract_float(self, data: dict, key: str, warnings: list, field_name: str) -> float | None:
        """Extract float value from yfinance data."""
        try:
            value = data.get(key)
            if value is None:
                warnings.append(f"{field_name} not available")
                return None
            return float(value)
        except (ValueError, TypeError):
            warnings.append(f"{field_name} invalid format")
            return None
