"""
Chart-img API Tool

Generates chart images for a given symbol and timeframe using the Chart-img API.
Environment variables required:
- CHART_IMG_API_KEY (required)
- CHART_IMG_BASE_URL (optional; defaults to https://api.chart-img.com/v1/stock)

This tool returns a data URL (base64-encoded PNG) suitable for embedding in HTML.
"""

from __future__ import annotations

import base64
import os
from typing import Literal

import requests
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class ChartImgInput(BaseModel):
    symbol: str = Field(..., description="Ticker symbol, e.g., AAPL, SPY, BTCUSD")
    interval: str = Field("1day", description="Bar interval, e.g., 1min, 5min, 1h, 1day")
    range: str = Field("6mo", description="Time range, e.g., 1mo, 3mo, 6mo, 1y, 5y, max")
    width: int = Field(900, description="Image width in pixels")
    height: int = Field(500, description="Image height in pixels")
    theme: Literal["light", "dark"] = Field("light", description="Chart theme")


class ChartImgTool(BaseTool):
    name: str = "Chart-img Generator"
    description: str = (
        "Generates a PNG chart image via Chart-img for a given symbol and timeframe, "
        "returning a data URL string. Requires CHART_IMG_API_KEY."
    )
    args_schema: type[BaseModel] = ChartImgInput

    def _run(
        self,
        symbol: str,
        interval: str = "1day",
        range: str = "6mo",
        width: int = 900,
        height: int = 500,
        theme: str = "light",
    ) -> str:
        api_key = os.getenv("CHART_IMG_API_KEY")
        if not api_key:
            return "Error: CHART_IMG_API_KEY environment variable not set."
        base_url = os.getenv("CHART_IMG_BASE_URL", "https://api.chart-img.com/v1/stock")

        headers = {"x-api-key": api_key}
        params = {
            "symbol": symbol,
            "interval": interval,
            "range": range,
            "width": width,
            "height": height,
            "theme": theme,
        }
        try:
            resp = requests.get(base_url, headers=headers, params=params, timeout=20)
            resp.raise_for_status()
            content_type = resp.headers.get("Content-Type", "image/png")
            b64 = base64.b64encode(resp.content).decode("ascii")
            return f"data:{content_type};base64,{b64}"
        except Exception as e:
            return f"Error generating chart image for {symbol}: {e}"
