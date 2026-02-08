"""
Alpha Vantage News Sentiment Tool.

Wraps Alpha Vantage NEWS_SENTIMENT endpoint to fetch news & sentiment for a ticker.
Environment variable required: ALPHA_VANTAGE_API_KEY
Docs: https://www.alphavantage.co/documentation/#news-sentiment
"""

from __future__ import annotations

import requests
from crewai.tools import BaseTool
from pydantic import BaseModel

# Import schema from centralized location
from finwiz.config.endpoints import ALPHA_VANTAGE_BASE
from finwiz.schemas.tools import AlphaVantageNewsInput
from finwiz.tools.api_key_validation import validate_api_key


class AlphaVantageNewsSentimentTool(BaseTool):
    """Fetch news and sentiment from Alpha Vantage for specified tickers."""

    name: str = "Alpha Vantage News Sentiment"
    description: str = "Fetches news and sentiment using Alpha Vantage NEWS_SENTIMENT endpoint. Requires ALPHA_VANTAGE_API_KEY in environment."
    args_schema: type[BaseModel] = AlphaVantageNewsInput

    base_url: str = ALPHA_VANTAGE_BASE

    def model_post_init(self, __context: object) -> None:
        """Validate API key at instantiation (fail-fast)."""
        super().model_post_init(__context)
        self._api_key = validate_api_key("ALPHA_VANTAGE_API_KEY", self.__class__.__name__)

    def _run(
        self,
        tickers: str,
        sort: str = "LATEST",
        time_from: str | None = None,
        time_to: str | None = None,
        limit: int | None = 50,
        topics: str | None = None,
    ) -> str:
        params: dict[str, str | int] = {
            "function": "NEWS_SENTIMENT",
            "tickers": tickers,
            "sort": sort,
            "apikey": self._api_key,
        }
        if time_from:
            params["time_from"] = time_from
        if time_to:
            params["time_to"] = time_to
        if limit is not None:
            params["limit"] = limit
        if topics:
            params["topics"] = topics

        try:
            resp = requests.get(self.base_url, params=params, timeout=15)
            resp.raise_for_status()
            return resp.text
        except Exception as e:
            # Catch broad exceptions to provide a stable error surface in tools
            return f"Error fetching Alpha Vantage news sentiment: {e}"
