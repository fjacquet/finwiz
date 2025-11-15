"""
Twelve Data API Tool for technical indicators (RSI, MACD, Bollinger Bands).

This tool wraps the Twelve Data HTTP API to fetch selected indicators for a symbol.
Environment variable required: TWELVE_DATA_API_KEY
"""

from __future__ import annotations

from typing import Any

import asyncio
import os

import requests
from crewai.tools import BaseTool
from pydantic import BaseModel

# Import schema from centralized location
from finwiz.schemas.tools import TwelveDataIndicatorInput
from finwiz.tools.logger import get_logger
from finwiz.tools.perplexity_analysis_integration import PerplexityAnalysisIntegration
from finwiz.utils.api_decorators import api_tool
from finwiz.utils.feature_flags import get_feature_flags
from finwiz.utils.rate_limiter import APIProvider

logger = get_logger(__name__)


class TwelveDataIndicatorTool(BaseTool):
    """
    Fetch a technical indicator from Twelve Data for a given symbol/interval.

    Supported indicators: rsi, macd, bbands
    Enhanced with optional Perplexity Sonar integration for technical analysis insights.
    """

    name: str = "Twelve Data Indicator"
    description: str = (
        "Fetches RSI/MACD/BBANDS from Twelve Data for a symbol and interval. "
        "Optionally enhanced with Perplexity Sonar for technical analysis insights. "
        "Requires TWELVE_DATA_API_KEY in environment."
    )
    args_schema: type[BaseModel] = TwelveDataIndicatorInput

    base_url: str = "https://api.twelvedata.com"

    def _get_perplexity_integration(self) -> PerplexityAnalysisIntegration | None:
        """Get Perplexity integration instance if enabled."""
        feature_flags = get_feature_flags()

        if not feature_flags.is_enabled("perplexity_research"):
            return None

        try:
            integration = PerplexityAnalysisIntegration()
            if integration.is_available:
                logger.debug("Perplexity Sonar integration available for technical analysis")
                return integration
            else:
                logger.warning("Perplexity integration initialized but API key not available")
                return None
        except Exception as e:
            logger.error(f"Failed to initialize Perplexity integration: {str(e)}")
            return None

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
        try:
            logger.info(f"Fetching {indicator} data for {symbol} with optional Perplexity enhancement")

            # Get technical indicator data from Twelve Data
            twelve_data_result = self._get_twelve_data_indicator(symbol, interval, indicator, length, fast_period, slow_period, signal_period, outputsize)

            # Optionally enhance with Perplexity technical analysis insights
            perplexity_insights = asyncio.run(self._get_perplexity_technical_insights(symbol, indicator))

            # Combine results
            return self._format_enhanced_technical_response(
                symbol=symbol,
                indicator=indicator,
                twelve_data_result=twelve_data_result,
                perplexity_insights=perplexity_insights,
            )

        except Exception as e:
            logger.error(f"Error in enhanced technical analysis for {symbol}: {str(e)}")
            return f"Error performing enhanced technical analysis for {symbol}: {str(e)}"

    def _get_twelve_data_indicator(
        self,
        symbol: str,
        interval: str,
        indicator: str,
        length: int | None,
        fast_period: int | None,
        slow_period: int | None,
        signal_period: int | None,
        outputsize: int | None,
    ) -> str:
        """Get technical indicator data from Twelve Data API."""
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

    async def _get_perplexity_technical_insights(self, symbol: str, indicator: str) -> list[Any]:
        """Get technical analysis insights from Perplexity Sonar."""
        perplexity_integration = self._get_perplexity_integration()
        if not perplexity_integration:
            return []

        try:
            # Determine asset type (simplified logic)
            asset_type = self._determine_asset_type(symbol)

            # Search for technical analysis insights
            sonar_result = await perplexity_integration.search_technical_analysis(ticker=symbol, asset_type=asset_type, max_results=5)

            if sonar_result.success:
                feature_flags = get_feature_flags()
                feature_flags.record_success("perplexity_research")
                logger.info(f"Retrieved {len(sonar_result.results)} Perplexity technical insights for {symbol}")
                return sonar_result.results
            else:
                logger.warning(f"Perplexity technical search failed for {symbol}: {sonar_result.error_message}")
                feature_flags = get_feature_flags()
                feature_flags.record_failure("perplexity_research")
                return []

        except Exception as e:
            logger.warning(f"Perplexity technical search failed for {symbol}: {str(e)}")
            feature_flags = get_feature_flags()
            feature_flags.record_failure("perplexity_research")
            return []

    def _determine_asset_type(self, symbol: str) -> str:
        """Determine asset type from symbol (simplified logic)."""
        symbol_upper = symbol.upper()

        # Common crypto patterns
        if any(crypto in symbol_upper for crypto in ["BTC", "ETH", "USD", "USDT", "/"]):
            return "crypto"

        # Common ETF patterns
        if any(etf in symbol_upper for etf in ["SPY", "QQQ", "VTI", "IWM", "EFA", "EEM"]):
            return "etf"

        # Default to stock
        return "stock"

    def _format_enhanced_technical_response(self, symbol: str, indicator: str, twelve_data_result: str, perplexity_insights: list[Any]) -> str:
        """Format enhanced technical analysis response combining Twelve Data and Perplexity insights."""
        response = f"# Enhanced Technical Analysis: {indicator.upper()} for {symbol}\n\n"

        # Add Twelve Data results
        response += "## 📊 Technical Indicator Data (Twelve Data)\n"
        response += f"{twelve_data_result}\n\n"

        # Add Perplexity insights if available
        if perplexity_insights:
            response += "## 🔍 Market Analysis Insights (Perplexity Sonar)\n"
            response += f"Found {len(perplexity_insights)} recent technical analysis articles:\n\n"

            for i, article in enumerate(perplexity_insights, 1):
                content_emoji = {"news": "📰", "analysis": "📊", "earnings": "💰", "regulatory": "⚖️"}.get(article.content_type, "📰")

                response += f"{i}. {content_emoji} **{article.title}**\n"
                response += f"   - Publisher: {article.publisher}\n"
                response += f"   - Relevance: {article.relevance_score:.2f}\n"
                if article.summary:
                    response += f"   - Summary: {article.summary[:150]}{'...' if len(article.summary) > 150 else ''}\n"
                response += f"   - URL: {article.url}\n\n"

            response += "## 📈 Enhanced Analysis Summary\n"
            response += f"This technical analysis combines quantitative {indicator.upper()} data from Twelve Data "
            response += f"with {len(perplexity_insights)} recent market analysis articles from Perplexity Sonar. "
            response += "The combination provides both mathematical indicators and current market sentiment "
            response += "around technical levels and price movements.\n\n"
        else:
            response += "## 📈 Analysis Summary\n"
            response += f"Technical analysis based on {indicator.upper()} data from Twelve Data. "
            response += "No additional market insights available from Perplexity Sonar.\n\n"

        response += "**Note**: Combine technical indicators with fundamental analysis and market context for investment decisions."

        return response
