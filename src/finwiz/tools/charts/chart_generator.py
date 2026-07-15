"""
Chart generation utilities using Chart-img API.

This module provides chart image generation capabilities for technical analysis.
"""

import base64
import os

import requests

from finwiz.config.endpoints import CHART_IMG_BASE
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class ChartGenerator:
    """Generates chart images using Chart-img API."""

    def __init__(self) -> None:
        """Initialize the chart generator."""
        self.api_key = os.getenv("CHART_IMG_API_KEY")
        self.base_url = CHART_IMG_BASE

        # Chart generation parameters
        self.default_width = 1200
        self.default_height = 800
        self.default_theme = "light"

    def generate_chart(self, symbol: str, timeframe: str, interval: str, width: int, height: int) -> str:
        """
        Generate chart image using Chart-img API.

        Args:
            symbol: Stock ticker symbol
            timeframe: Time range for the chart (1mo, 3mo, 6mo, 1y, 5y, max)
            interval: Bar interval (1min, 5min, 1h, 1day)
            width: Chart width in pixels
            height: Chart height in pixels

        Returns:
            Data URL of the generated chart image

        """
        headers = {"x-api-key": self.api_key}
        params: dict[str, str] = {
            "symbol": symbol,
            "interval": interval,
            "range": timeframe,
            "width": str(width),
            "height": str(height),
            "theme": self.default_theme,
        }

        try:
            response = requests.get(self.base_url, headers=headers, params=params, timeout=30)
            response.raise_for_status()

            content_type = response.headers.get("Content-Type", "image/png")
            b64_content = base64.b64encode(response.content).decode("ascii")
            return f"data:{content_type};base64,{b64_content}"

        except Exception as e:
            logger.error(f"Error generating chart for {symbol}: {e}")
            return f"Error generating chart image for {symbol}: {e}"

    def generate_chart_url(
        self,
        symbol: str,
        timeframe: str = "6mo",
        interval: str = "1day",
        width: int = 900,
        height: int = 500,
        _theme: str = "light",
    ) -> str:
        """
        Generate a chart image URL for embedding.

        This is a convenience method that just generates the chart without analysis.

        Args:
            symbol: Stock ticker symbol
            timeframe: Time range for the chart
            interval: Bar interval
            width: Chart width in pixels
            height: Chart height in pixels
            _theme: Chart theme (light or dark) — accepted for call-signature
                compatibility but not forwarded; this generator always uses
                `self.default_theme`.

        Returns:
            Data URL of the generated chart

        """
        return self.generate_chart(symbol, timeframe, interval, width, height)
