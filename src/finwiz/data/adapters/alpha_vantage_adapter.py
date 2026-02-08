"""
Alpha Vantage adapter for data acquisition.

Fallback adapter using Alpha Vantage API for better fundamental data.
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Any

from finwiz.data.adapters.base_adapter import BaseDataAdapter, DataAcquisitionError, FundamentalData

logger = logging.getLogger(__name__)


class AlphaVantageAdapter(BaseDataAdapter):
    """
    Adapter for Alpha Vantage API.

    API Details:
    - Endpoint: https://www.alphavantage.co/query
    - Function: OVERVIEW for company fundamentals
    - Rate Limit: 500 calls/day (free tier)
    - Coverage: 60+ exchanges globally

    Strengths:
    - Better fundamental data than yfinance
    - Official API with documentation
    - Good international coverage

    Limitations:
    - Rate limited (500/day)
    - Requires API key
    """

    def __init__(self, timeout_seconds: float = 3.0) -> None:
        """Initialize Alpha Vantage adapter."""
        super().__init__(timeout_seconds)
        self.api_key = os.getenv("ALPHA_VANTAGE_API_KEY") or os.getenv("ALPHA_VANTAGE_KEY")
        if not self.api_key:
            logger.warning("ALPHA_VANTAGE_API_KEY not set - adapter will be unavailable")

    @property
    def source_name(self) -> str:
        """Return the name of this data source."""
        return "alpha_vantage"

    def is_available(self) -> bool:
        """Check if Alpha Vantage API key is available."""
        return self.api_key is not None

    async def get_fundamental_data(self, ticker: str) -> FundamentalData:
        """Get fundamental data from Alpha Vantage asynchronously."""
        if not self.is_available():
            raise DataAcquisitionError("Alpha Vantage API key not available")
        try:
            loop = asyncio.get_running_loop()
            raw = await asyncio.wait_for(
                loop.run_in_executor(None, self.get_fundamentals, ticker, self.timeout_seconds),
                timeout=self.timeout_seconds,
            )
            return FundamentalData(
                ticker=ticker,
                source="AlphaVantage",
                timestamp=datetime.now(),
                confidence=0.85,
                return_on_equity=raw.get("roe"),
                debt_to_equity=raw.get("debt_to_equity"),
                revenue_growth=raw.get("revenue_growth"),
                profit_margin=raw.get("profit_margin"),
            )
        except Exception as e:
            raise DataAcquisitionError(f"Alpha Vantage error for {ticker}: {e}")

    def get_fundamentals(self, ticker: str, timeout: float = 3.0) -> dict[str, Any]:
        """
        Extract fundamentals from Alpha Vantage with timeout.

        API Call:
        GET /query?function=OVERVIEW&symbol={ticker}&apikey={key}

        Args:
            ticker: Stock ticker symbol
            timeout: Maximum time to wait (seconds)

        Returns:
            Dictionary with:
            - roe: From 'ReturnOnEquityTTM'
            - debt_to_equity: From 'DebtToEquityRatio'
            - revenue_growth: From 'QuarterlyRevenueGrowthYOY'
            - profit_margin: From 'ProfitMargin'

        Raises:
            Exception: If data acquisition fails

        """
        if not self.api_key:
            raise ValueError("ALPHA_VANTAGE_API_KEY not configured")

        try:
            import requests

            # Make API request
            url = "https://www.alphavantage.co/query"
            params = {"function": "OVERVIEW", "symbol": ticker, "apikey": self.api_key}

            response = requests.get(url, params=params, timeout=timeout)
            response.raise_for_status()

            data = response.json()

            # Check for API errors
            if "Error Message" in data:
                raise ValueError(f"Alpha Vantage error: {data['Error Message']}")

            if "Note" in data:
                # Rate limit message
                raise ValueError(f"Alpha Vantage rate limit: {data['Note']}")

            # Check if we got valid data
            if "Symbol" not in data:
                raise ValueError(f"No data returned for {ticker}")

            # Extract fundamentals
            result = {
                "roe": self._extract_float(data, "ReturnOnEquityTTM"),
                "debt_to_equity": self._extract_float(data, "DebtToEquityRatio"),
                "revenue_growth": self._extract_float(data, "QuarterlyRevenueGrowthYOY"),
                "profit_margin": self._extract_float(data, "ProfitMargin"),
            }

            logger.debug(f"Alpha Vantage extracted data for {ticker}: {result}")
            return result

        except Exception as e:
            logger.warning(f"Alpha Vantage failed for {ticker}: {e}")
            raise

    def _extract_float(self, data: dict, key: str) -> float | None:
        """
        Safely extract float value from API response.

        Args:
            data: Alpha Vantage response dictionary
            key: Key to extract

        Returns:
            Float value or None if not present/invalid

        """
        try:
            value = data.get(key)
            if value is None or value == "None" or value == "":
                return None
            return float(value)
        except (ValueError, TypeError):
            return None
