"""
Twelve Data API Tool for technical indicators (RSI, MACD, Bollinger Bands).

This tool wraps the Twelve Data HTTP API to fetch selected indicators for a symbol.
Environment variable required: TWELVE_DATA_API_KEY
"""

from __future__ import annotations

import os
from typing import Literal

import requests
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from finwiz.utils.api_decorators import api_tool
from finwiz.utils.rate_limiter import APIProvider


class TwelveDataIndicatorInput(BaseModel):
    """Input schema for Twelve Data indicator tool."""

    symbol: str = Field(..., description="Ticker symbol, e.g., AAPL, BTC/USD, SPY")
    interval: str = Field("1day", description="Interval, e.g., 1min, 5min, 1h, 1day")
    indicator: Literal["rsi", "macd", "bbands"] = Field(..., description="Indicator to fetch from Twelve Data")
    length: int | None = Field(None, description="Window length for indicators like RSI/BBANDS")
    fast_period: int | None = Field(None, description="Fast period for MACD")
    slow_period: int | None = Field(None, description="Slow period for MACD")
    signal_period: int | None = Field(None, description="Signal period for MACD")
    outputsize: int | None = Field(100, description="Number of data points to return (max depends on plan)")


class TwelveDataIndicatorTool(BaseTool):
    """
    Fetch a technical indicator from Twelve Data for a given symbol/interval.

    Supported indicators: rsi, macd, bbands
    """

    name: str = "Twelve Data Indicator"
    description: str = (
        "Fetches RSI/MACD/BBANDS from Twelve Data for a symbol and interval. Requires TWELVE_DATA_API_KEY in environment."
    )
    args_schema: type[BaseModel] = TwelveDataIndicatorInput

    base_url: str = "https://api.twelvedata.com"

    @api_tool(
        provider=APIProvider.TWELVE_DATA,
        endpoint="technical_indicators",
        timeout=20.0,
        default_return="Error: Unable to fetch technical indicator data",
    )
    def _run(
        self,
        symbol: str,
        interval: str = "1day",
        indicator: str = "rsi",
        length: int | None = None,
        fast_period: int | None = None,
        slow_period: int | None = None,
        signal_period: int | None = None,
        outputsize: int | None = 100,
    ) -> str:
        api_key = os.getenv("TWELVE_DATA_API_KEY")
        if not api_key:
            return "Error: TWELVE_DATA_API_KEY environment variable not set."

        endpoint = f"{self.base_url}/{indicator}"
        params: dict[str, str | int] = {
            "symbol": symbol,
            "interval": interval,
            "apikey": api_key,
        }
        if outputsize is not None:
            params["outputsize"] = outputsize
        if indicator == "rsi" and length is not None:
            params["time_period"] = length
        if indicator == "bbands" and length is not None:
            params["time_period"] = length
        if indicator == "macd":
            if fast_period is not None:
                params["fast"] = fast_period
            if slow_period is not None:
                params["slow"] = slow_period
            if signal_period is not None:
                params["signal"] = signal_period

        resp = requests.get(endpoint, params=params, timeout=15)
        resp.raise_for_status()
        return resp.text
