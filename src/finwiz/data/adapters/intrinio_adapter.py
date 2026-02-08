"""
Intrinio adapter for data acquisition.

Fallback adapter using Intrinio Python SDK for SEC filings data.
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Any

from finwiz.data.adapters.base_adapter import BaseDataAdapter, DataAcquisitionError, FundamentalData

logger = logging.getLogger(__name__)


class IntrinioAdapter(BaseDataAdapter):
    """
    Adapter for Intrinio API.

    API Details:
    - SDK: intrinio_sdk (Python)
    - Endpoint: FundamentalsApi, CompanyApi
    - Coverage: SEC filings, financial statements

    Strengths:
    - Direct access to SEC filings
    - Comprehensive financial statements
    - Official Python SDK

    Limitations:
    - Limited free tier
    - Requires API key
    - US-focused
    """

    def __init__(self, timeout_seconds: float = 3.0) -> None:
        """Initialize Intrinio adapter."""
        super().__init__(timeout_seconds)
        self.api_key = os.getenv("INTRINIO_API_KEY")
        if not self.api_key:
            logger.warning("INTRINIO_API_KEY not set - adapter will be unavailable")

    @property
    def source_name(self) -> str:
        """Return the name of this data source."""
        return "intrinio"

    def is_available(self) -> bool:
        """Check if Intrinio API key is available."""
        return self.api_key is not None

    async def get_fundamental_data(self, ticker: str) -> FundamentalData:
        """Get fundamental data from Intrinio asynchronously."""
        if not self.is_available():
            raise DataAcquisitionError("Intrinio API key not available")
        try:
            loop = asyncio.get_running_loop()
            raw = await asyncio.wait_for(
                loop.run_in_executor(None, self.get_fundamentals, ticker, self.timeout_seconds),
                timeout=self.timeout_seconds,
            )
            return FundamentalData(
                ticker=ticker,
                source="Intrinio",
                timestamp=datetime.now(),
                confidence=0.80,
                return_on_equity=raw.get("roe"),
                debt_to_equity=raw.get("debt_to_equity"),
                revenue_growth=raw.get("revenue_growth"),
                profit_margin=raw.get("profit_margin"),
            )
        except Exception as e:
            raise DataAcquisitionError(f"Intrinio error for {ticker}: {e}")

    def get_fundamentals(self, ticker: str, timeout: float = 3.0) -> dict[str, Any]:
        """
        Extract fundamentals from Intrinio SEC filings with timeout.

        SDK Usage:
        intrinio.CompanyApi().get_company_fundamentals(
            identifier=ticker,
            statement_code='income_statement',
            latest_only=True
        )

        Args:
            ticker: Stock ticker symbol
            timeout: Maximum time to wait (seconds)

        Returns:
            Dictionary with:
            - roe: Calculated from net income / equity
            - debt_to_equity: From balance sheet
            - revenue_growth: From income statement
            - profit_margin: From income statement

        Raises:
            Exception: If data acquisition fails

        """
        if not self.api_key:
            raise ValueError("INTRINIO_API_KEY not configured")

        try:
            import intrinio_sdk as intrinio

            # Configure API client
            configuration = intrinio.Configuration()
            configuration.api_key["api_key"] = self.api_key
            api_client = intrinio.ApiClient(configuration)

            # Get company fundamentals
            company_api = intrinio.CompanyApi(api_client)

            # Get latest fundamental data
            fundamentals_response = company_api.get_company_fundamentals(identifier=ticker, latest_only=True, page_size=1)

            if not fundamentals_response.fundamentals:
                raise ValueError(f"No fundamentals data for {ticker}")

            fundamental_id = fundamentals_response.fundamentals[0].id

            # Get standardized financials
            fundamentals_api = intrinio.FundamentalsApi(api_client)
            financials = fundamentals_api.get_fundamental_standardized_financials(fundamental_id)

            # Extract metrics from standardized financials
            metrics = {}
            for item in financials.standardized_financials:
                tag = item.data_tag.tag if hasattr(item.data_tag, "tag") else None
                if tag == "roe":
                    metrics["roe"] = self._extract_float(item.value)
                elif tag == "debt_to_equity":
                    metrics["debt_to_equity"] = self._extract_float(item.value)
                elif tag == "revenue_growth":
                    metrics["revenue_growth"] = self._extract_float(item.value)
                elif tag == "profit_margin":
                    metrics["profit_margin"] = self._extract_float(item.value)

            # Fill in None for missing fields
            result = {
                "roe": metrics.get("roe"),
                "debt_to_equity": metrics.get("debt_to_equity"),
                "revenue_growth": metrics.get("revenue_growth"),
                "profit_margin": metrics.get("profit_margin"),
            }

            logger.debug(f"Intrinio extracted data for {ticker}: {result}")
            return result

        except Exception as e:
            logger.warning(f"Intrinio failed for {ticker}: {e}")
            raise

    def _extract_float(self, value: Any) -> float | None:
        """
        Safely extract float value.

        Args:
            value: Value to convert

        Returns:
            Float value or None if not present/invalid

        """
        try:
            if value is None:
                return None
            return float(value)
        except (ValueError, TypeError):
            return None
