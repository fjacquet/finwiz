"""
Chart-img API Tool.

Generates chart images for a given symbol and timeframe using the Chart-img API.
Environment variables required:
- CHART_IMG_API_KEY (required)
- CHART_IMG_BASE_URL (optional; defaults to https://api.chart-img.com/v1/stock)

This tool returns a data URL (base64-encoded PNG) suitable for embedding in HTML.
"""

from __future__ import annotations

import base64
import os

import requests
from crewai.tools import BaseTool
from pydantic import BaseModel

# Import schema from centralized location
from finwiz.schemas.tools import ChartImgInput
from finwiz.infrastructure.decorators.api_decorators import api_tool
from finwiz.infrastructure.resilience.rate_limiter import APIProvider


class ChartImgTool(BaseTool):
    """Tool for generating chart images via Chart-img API."""

    name: str = "Chart-img Generator"
    description: str = "Generates a PNG chart image via Chart-img for a given symbol and timeframe, returning a data URL string. Requires CHART_IMG_API_KEY."
    args_schema: type[BaseModel] = ChartImgInput

    @api_tool(
        provider=APIProvider.CHART_IMG,
        endpoint="chart_generation",
        timeout=25.0,
        default_return="Error: Unable to generate chart image",
    )
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
        params: dict[str, str] = {
            "symbol": symbol,
            "interval": interval,
            "range": range,
            "width": str(width),
            "height": str(height),
            "theme": theme,
        }

        resp = requests.get(base_url, headers=headers, params=params, timeout=20)
        resp.raise_for_status()
        content_type = resp.headers.get("Content-Type", "image/png")
        b64 = base64.b64encode(resp.content).decode("ascii")
        return f"data:{content_type};base64,{b64}"
