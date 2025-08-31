"""
Alpha Vantage News Sentiment Tool.

Wraps Alpha Vantage NEWS_SENTIMENT endpoint to fetch news & sentiment for a ticker.
Environment variable required: ALPHA_VANTAGE_API_KEY
Docs: https://www.alphavantage.co/documentation/#news-sentiment
"""

from __future__ import annotations

import os
from typing import Literal

import requests
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class AlphaVantageNewsInput(BaseModel):
    """Input schema for Alpha Vantage News Sentiment tool."""

    tickers: str = Field(..., description="Comma-separated tickers, e.g., AAPL,MSFT or BTC")
    sort: Literal["LATEST", "EARLIEST", "RELEVANCE"] = Field("LATEST", description="Sorting strategy for results")
    time_from: str | None = Field(None, description="ISO8601 start time (YYYYMMDDTHHMM)")
    time_to: str | None = Field(None, description="ISO8601 end time (YYYYMMDDTHHMM)")
    limit: int | None = Field(50, description="Max number of items to return")
    topics: str | None = Field(None, description="Comma-separated topics filter (e.g., technology,financial_markets)")


class AlphaVantageNewsSentimentTool(BaseTool):
    """Fetch news and sentiment from Alpha Vantage for specified tickers."""

    name: str = "Alpha Vantage News Sentiment"
    description: str = (
        "Fetches news and sentiment using Alpha Vantage NEWS_SENTIMENT endpoint. Requires ALPHA_VANTAGE_API_KEY in environment."
    )
    args_schema: type[BaseModel] = AlphaVantageNewsInput

    base_url: str = "https://www.alphavantage.co/query"

    def _run(
        self,
        tickers: str,
        sort: str = "LATEST",
        time_from: str | None = None,
        time_to: str | None = None,
        limit: int | None = 50,
        topics: str | None = None,
    ) -> str:
        api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        if not api_key:
            return "Error: ALPHA_VANTAGE_API_KEY environment variable not set."

        params: dict[str, str | int] = {
            "function": "NEWS_SENTIMENT",
            "tickers": tickers,
            "sort": sort,
            "apikey": api_key,
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
