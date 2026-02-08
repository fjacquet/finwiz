"""
Tiingo adapter for data acquisition.

Fallback adapter for international stocks using Tiingo API.
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Any

from finwiz.data.adapters.base_adapter import BaseDataAdapter, DataAcquisitionError, FundamentalData

logger = logging.getLogger(__name__)


class TiingoAdapter(BaseDataAdapter):
    """
    Adapter for Tiingo API (international stocks).

    API Details:
    - Endpoint: https://api.tiingo.com/tiingo/fundamentals
    - Rate Limit: Varies by plan (free tier available)
    - Coverage: International stocks, 99.9% uptime

    Strengths:
    - Excellent international coverage
    - High reliability (99.9% uptime)
    - Good for non-US exchanges

    Limitations:
    - Requires API key
    - Rate limited
    """

    def __init__(self, timeout_seconds: float = 3.0) -> None:
        """Initialize Tiingo adapter."""
        super().__init__(timeout_seconds)
        self.api_key = os.getenv("TIINGO_API_KEY")
        if not self.api_key:
            logger.warning("TIINGO_API_KEY not set - adapter will be unavailable")

    @property
    def source_name(self) -> str:
        """Return the name of this data source."""
        return "tiingo"

    def is_available(self) -> bool:
        """Check if Tiingo API key is available."""
        return self.api_key is not None

    async def get_fundamental_data(self, ticker: str) -> FundamentalData:
        """Get fundamental data from Tiingo asynchronously."""
        if not self.is_available():
            raise DataAcquisitionError("Tiingo API key not available")
        try:
            loop = asyncio.get_running_loop()
            raw = await asyncio.wait_for(
                loop.run_in_executor(None, self.get_fundamentals, ticker, self.timeout_seconds),
                timeout=self.timeout_seconds,
            )
            return FundamentalData(
                ticker=ticker,
                source="Tiingo",
                timestamp=datetime.now(),
                confidence=0.75,
                return_on_equity=raw.get("roe"),
                debt_to_equity=raw.get("debt_to_equity"),
                revenue_growth=raw.get("revenue_growth"),
                profit_margin=raw.get("profit_margin"),
            )
        except Exception as e:
            raise DataAcquisitionError(f"Tiingo error for {ticker}: {e}")

    def get_fundamentals(self, ticker: str, timeout: float = 3.0) -> dict[str, Any]:
        """
        Extract fundamentals from Tiingo (international) with timeout.

        API Call:
        GET /tiingo/fundamentals/{ticker}/statements
        Headers: {'Authorization': 'Token {api_key}'}

        Args:
            ticker: Stock ticker symbol
            timeout: Maximum time to wait (seconds)

        Returns:
            Dictionary with:
            - roe: From financial statements
            - debt_to_equity: From balance sheet
            - revenue_growth: From income statement
            - profit_margin: From income statement

        Raises:
            Exception: If data acquisition fails

        """
        if not self.api_key:
            raise ValueError("TIINGO_API_KEY not configured")

        try:
            import requests

            # Make API request for fundamentals
            url = f"https://api.tiingo.com/tiingo/fundamentals/{ticker}/statements"
            headers = {"Authorization": f"Token {self.api_key}", "Content-Type": "application/json"}

            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()

            data = response.json()

            # Check if we got valid data
            if not data or not isinstance(data, list) or len(data) == 0:
                raise ValueError(f"No fundamentals data for {ticker}")

            # Get most recent statement
            latest = data[0]

            # Extract metrics from statement data
            # Tiingo structure varies, so we need to handle different formats
            result = {
                "roe": self._extract_metric(latest, ["roe", "returnOnEquity"]),
                "debt_to_equity": self._extract_metric(latest, ["debtToEquity", "debt_to_equity"]),
                "revenue_growth": self._extract_metric(latest, ["revenueGrowth", "revenue_growth"]),
                "profit_margin": self._extract_metric(latest, ["profitMargin", "profit_margin"]),
            }

            logger.debug(f"Tiingo extracted data for {ticker}: {result}")
            return result

        except Exception as e:
            logger.warning(f"Tiingo failed for {ticker}: {e}")
            raise

    def _extract_metric(self, data: dict, keys: list[str]) -> float | None:
        """
        Extract metric trying multiple possible keys.

        Args:
            data: Tiingo response data
            keys: List of possible keys to try

        Returns:
            Float value or None if not found

        """
        for key in keys:
            try:
                value = data.get(key)
                if value is not None:
                    return float(value)
            except (ValueError, TypeError):
                continue
        return None
