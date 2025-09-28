"""
Alpha Vantage API Tools for FinWiz.

This module provides tools to interact with the Alpha Vantage API for fetching
comprehensive financial data, including fundamental data, technical indicators,
and more.
"""

import json
import logging
import os
from datetime import UTC, datetime
from typing import Any

import requests
from crewai.tools import BaseTool
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from finwiz.utils.api_decorators import api_tool
from finwiz.utils.cache_manager import cache_key, cached
from finwiz.utils.rate_limiter import APIProvider

logger = logging.getLogger(__name__)

load_dotenv()


class CompanyOverviewInput(BaseModel):
    """Input schema for the AlphaVantageCompanyOverviewTool."""

    ticker: str = Field(..., description="The stock ticker symbol to get information for.")


class AlphaVantageCompanyOverviewTool(BaseTool):
    """
    A tool to fetch company overview and fundamental data from Alpha Vantage.

    This tool uses the Alpha Vantage API to retrieve key financial metrics
    and company information for a given stock ticker. It requires an
    ALPHA_VANTAGE_API_KEY to be set in the environment variables.
    """

    name: str = "Alpha Vantage Company Overview"
    description: str = (
        "Fetches fundamental data and a company overview for a specific stock ticker "
        "from Alpha Vantage. Use this to get detailed financial metrics like Market Cap, "
        "P/E Ratio, EPS, and more."
    )
    args_schema: type[BaseModel] = CompanyOverviewInput

    def _run(self, ticker: str) -> str:
        """Execute the tool to fetch company overview data."""
        import asyncio

        # Use async wrapper for caching
        async def fetch_data() -> dict[str, Any]:
            return await self._fetch_company_overview(ticker)

        # Run in event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(fetch_data())

    @api_tool(
        provider=APIProvider.ALPHA_VANTAGE,
        endpoint="company_overview",
        timeout=15.0,
        default_return="Error: Unable to fetch company overview data",
    )
    async def _fetch_company_overview(self, ticker: str) -> str:
        """Fetch company overview data with caching."""
        cache_key_str = cache_key("alpha_vantage", "overview", ticker.upper())

        async def fetch_from_api() -> str:
            api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
            if not api_key:
                return "Error: ALPHA_VANTAGE_API_KEY environment variable not set."

            url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={api_key}"

            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            if not data or "Note" in data:
                return f"No data found for ticker {ticker}. It might be an invalid symbol."

            # Add timestamp for freshness validation
            data["timestamp"] = datetime.now(UTC).isoformat()

            # Log data retrieval for debugging
            logger.debug(f"Retrieved Alpha Vantage data for {ticker}")

            return json.dumps(data, indent=2)

        # Use caching with 30-minute TTL for company overview data
        return await cached(
            cache_key_str,
            fetch_from_api,
            ttl=1800,  # 30 minutes
            tags={"alpha_vantage", "company_overview", ticker.upper()},
        )
