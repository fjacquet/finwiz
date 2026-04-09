"""
Twelve Data Multi-Indicator Tool for fetching multiple technical indicators in one call.

This tool optimizes API usage by fetching RSI, MACD, and Bollinger Bands in a single operation.
Environment variable required: TWELVE_DATA_API_KEY
"""

from __future__ import annotations

import asyncio
from typing import Any, Literal

import requests
from crewai.tools import BaseTool
from pydantic import BaseModel

from finwiz.config.endpoints import TWELVE_DATA_BASE
from finwiz.config.features.flags import get_feature_flags
from finwiz.infrastructure.decorators.api_decorators import api_tool
from finwiz.infrastructure.resilience.rate_limiter import APIProvider
from finwiz.schemas.tools import TwelveDataMultiIndicatorInput
from finwiz.tools.api_key_validation import validate_api_key
from finwiz.tools.logger import get_logger
from finwiz.tools.perplexity_analysis_integration import PerplexityAnalysisIntegration

logger = get_logger(__name__)


class TwelveDataMultiIndicatorTool(BaseTool):
    """
    Fetch multiple technical indicators from Twelve Data in one call.

    Optimized for fetching RSI, MACD, and Bollinger Bands together.
    Enhanced with optional Perplexity Sonar integration for technical analysis insights.
    """

    name: str = "Twelve Data Multi-Indicator"
    description: str = (
        "Fetches multiple technical indicators (RSI, MACD, BBANDS) from Twelve Data in one call. "
        "Optionally enhanced with Perplexity Sonar for technical analysis insights. "
        "Requires TWELVE_DATA_API_KEY in environment."
    )
    args_schema: type[BaseModel] = TwelveDataMultiIndicatorInput

    base_url: str = TWELVE_DATA_BASE

    def model_post_init(self, __context: object) -> None:
        """Validate API key at instantiation (fail-fast)."""
        super().model_post_init(__context)
        self._api_key = validate_api_key("TWELVE_DATA_API_KEY", self.__class__.__name__)

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
            logger.error(f"Failed to initialize Perplexity integration: {e!s}")
            return None

    @api_tool(
        provider=APIProvider.TWELVE_DATA,
        endpoint="multi_technical_indicators",
        timeout=30.0,
        default_return="Error: Unable to fetch multi-indicator data",
    )
    def _run(
        self,
        symbol: str,
        interval: str = "1day",
        indicators: list[str] | None = None,
        rsi_period: int = 14,
        macd_fast: int = 12,
        macd_slow: int = 26,
        macd_signal: int = 9,
        bbands_period: int = 20,
        bbands_stddev: int = 2,
        outputsize: int = 100,
    ) -> str:
        """
        Fetch multiple technical indicators in one call.

        Args:
            symbol: Ticker symbol (e.g., AAPL, BTC/USD)
            interval: Time interval (e.g., 1day, 1h)
            indicators: List of indicators to fetch (default: all)
            rsi_period: RSI period (default: 14)
            macd_fast: MACD fast period (default: 12)
            macd_slow: MACD slow period (default: 26)
            macd_signal: MACD signal period (default: 9)
            bbands_period: Bollinger Bands period (default: 20)
            bbands_stddev: Bollinger Bands std dev (default: 2)
            outputsize: Number of data points (default: 100)

        Returns:
            Formatted string with all indicator results

        """
        try:
            # Default to all indicators if none specified
            if indicators is None:
                indicators = ["rsi", "macd", "bbands"]

            logger.info(f"Fetching {len(indicators)} indicators for {symbol} with optional Perplexity enhancement")

            # Fetch all indicators concurrently
            indicator_results = self._fetch_all_indicators(
                symbol=symbol,
                interval=interval,
                indicators=indicators,
                rsi_period=rsi_period,
                macd_fast=macd_fast,
                macd_slow=macd_slow,
                macd_signal=macd_signal,
                bbands_period=bbands_period,
                bbands_stddev=bbands_stddev,
                outputsize=outputsize,
            )

            # Optionally enhance with Perplexity technical analysis insights
            perplexity_insights = asyncio.run(self._get_perplexity_technical_insights(symbol))

            # Combine results
            return self._format_multi_indicator_response(
                symbol=symbol,
                interval=interval,
                indicator_results=indicator_results,
                perplexity_insights=perplexity_insights,
            )

        except Exception as e:
            logger.error(f"Error in multi-indicator analysis for {symbol}: {e!s}")
            return f"Error performing multi-indicator analysis for {symbol}: {e!s}"

    def _fetch_all_indicators(
        self,
        symbol: str,
        interval: str,
        indicators: list[str],
        rsi_period: int,
        macd_fast: int,
        macd_slow: int,
        macd_signal: int,
        bbands_period: int,
        bbands_stddev: int,
        outputsize: int,
    ) -> dict[str, Any]:
        """Fetch all requested indicators from Twelve Data API."""
        results: dict[str, str | dict[str, str]] = {}

        # Fetch RSI
        if "rsi" in indicators:
            try:
                results["rsi"] = self._fetch_indicator(
                    symbol=symbol,
                    interval=interval,
                    indicator="rsi",
                    api_key=self._api_key,
                    params={"time_period": rsi_period, "outputsize": outputsize},
                )
            except Exception as e:
                logger.error(f"Error fetching RSI: {e}")
                results["rsi"] = {"error": str(e)}

        # Fetch MACD
        if "macd" in indicators:
            try:
                results["macd"] = self._fetch_indicator(
                    symbol=symbol,
                    interval=interval,
                    indicator="macd",
                    api_key=self._api_key,
                    params={
                        "fast": macd_fast,
                        "slow": macd_slow,
                        "signal": macd_signal,
                        "outputsize": outputsize,
                    },
                )
            except Exception as e:
                logger.error(f"Error fetching MACD: {e}")
                results["macd"] = {"error": str(e)}

        # Fetch Bollinger Bands
        if "bbands" in indicators:
            try:
                results["bbands"] = self._fetch_indicator(
                    symbol=symbol,
                    interval=interval,
                    indicator="bbands",
                    api_key=self._api_key,
                    params={
                        "time_period": bbands_period,
                        "sd": bbands_stddev,
                        "outputsize": outputsize,
                    },
                )
            except Exception as e:
                logger.error(f"Error fetching Bollinger Bands: {e}")
                results["bbands"] = {"error": str(e)}

        return results

    def _fetch_indicator(self, symbol: str, interval: str, indicator: str, api_key: str, params: dict[str, Any]) -> str:
        """Fetch a single indicator from Twelve Data API."""
        endpoint = f"{self.base_url}/{indicator}"
        request_params: dict[str, str | int] = {
            "symbol": symbol,
            "interval": interval,
            "apikey": api_key,
            **params,
        }

        resp = requests.get(endpoint, params=request_params, timeout=15)
        resp.raise_for_status()
        return resp.text

    async def _get_perplexity_technical_insights(self, symbol: str) -> list[Any]:
        """Get technical analysis insights from Perplexity Sonar."""
        perplexity_integration = self._get_perplexity_integration()
        if not perplexity_integration:
            return []

        try:
            # Determine asset type
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
            logger.warning(f"Perplexity technical search failed for {symbol}: {e!s}")
            feature_flags = get_feature_flags()
            feature_flags.record_failure("perplexity_research")
            return []

    def _determine_asset_type(self, symbol: str) -> Literal["stock", "etf", "crypto"]:
        """Determine asset type from symbol."""
        symbol_upper = symbol.upper()

        # Common crypto patterns
        if any(crypto in symbol_upper for crypto in ["BTC", "ETH", "USD", "USDT", "/"]):
            return "crypto"

        # Common ETF patterns
        if any(etf in symbol_upper for etf in ["SPY", "QQQ", "VTI", "IWM", "EFA", "EEM"]):
            return "etf"

        # Default to stock
        return "stock"

    def _format_multi_indicator_response(self, symbol: str, interval: str, indicator_results: dict[str, Any], perplexity_insights: list[Any]) -> str:
        """Format multi-indicator response combining all data sources."""
        response = f"# 📊 Multi-Indicator Technical Analysis: {symbol}\n\n"
        response += f"**Interval**: {interval}\n"
        response += f"**Indicators**: {', '.join(indicator_results.keys()).upper()}\n\n"

        # Add each indicator's results
        for indicator, result in indicator_results.items():
            response += f"## {indicator.upper()} Analysis\n"
            if isinstance(result, dict) and "error" in result:
                response += f"⚠️ Error: {result['error']}\n\n"
            else:
                response += f"```json\n{result}\n```\n\n"

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
            response += f"This analysis combines {len(indicator_results)} technical indicators from Twelve Data "
            response += f"with {len(perplexity_insights)} recent market analysis articles from Perplexity Sonar. "
            response += "The combination provides both quantitative indicators and current market sentiment.\n\n"
        else:
            response += "## 📈 Analysis Summary\n"
            response += f"Technical analysis based on {len(indicator_results)} indicators from Twelve Data. "
            response += "No additional market insights available from Perplexity Sonar.\n\n"

        response += "**Note**: Combine multiple technical indicators with fundamental analysis for investment decisions."

        return response
