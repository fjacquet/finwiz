"""
Enhanced Technical Analyzer Tool with Perplexity Integration.

This tool wraps the TechnicalAnalyzer class and enhances it with Perplexity Sonar
search for recent analyst opinions, price targets, and technical commentary.
"""

from __future__ import annotations

import asyncio

import yfinance as yf
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from finwiz.schemas.perplexity import SonarArticle
from finwiz.tools.logger import get_logger
from finwiz.tools.perplexity_analysis_integration import PerplexityAnalysisIntegration
from finwiz.tools.technical_analyzer import PriceData, TechnicalAnalyzer
from finwiz.utils.feature_flags import get_feature_flags

logger = get_logger(__name__)


class EnhancedTechnicalAnalysisInput(BaseModel):
    """Input schema for enhanced technical analysis."""

    ticker: str = Field(..., description="The ticker symbol (e.g., 'AAPL', 'SPY', 'BTC-USD')")
    asset_type: str = Field("stock", description="Asset type: 'stock', 'etf', or 'crypto'")
    lookback_days: int = Field(100, description="Number of days of price data to analyze (50-365)")
    include_perplexity: bool = Field(True, description="Whether to include Perplexity Sonar insights")


class EnhancedTechnicalAnalyzerTool(BaseTool):
    """
    Enhanced technical analysis tool with Perplexity Sonar integration.

    Combines comprehensive technical analysis (Fibonacci, support/resistance, indicators)
    with recent analyst opinions and technical commentary from Perplexity Sonar.
    """

    name: str = "Enhanced Technical Analyzer"
    description: str = (
        "Perform comprehensive technical analysis including Fibonacci levels, support/resistance, "
        "technical indicators, and confluence zones. Optionally enhanced with recent analyst "
        "opinions and technical commentary from Perplexity Sonar."
    )
    args_schema: type[BaseModel] = EnhancedTechnicalAnalysisInput

    def _get_perplexity_integration(self) -> PerplexityAnalysisIntegration | None:
        """Get Perplexity integration instance if enabled."""
        feature_flags = get_feature_flags()

        # Check feature flag status and log for debugging
        is_enabled = feature_flags.is_enabled("perplexity_research")
        fallback_strategy = feature_flags.get_fallback_strategy("perplexity_research").value

        from finwiz.tools.perplexity_analysis_integration import PerplexityOperationLogger

        PerplexityOperationLogger.log_feature_flag_status("technical_analysis", is_enabled, fallback_strategy)

        if not is_enabled:
            return None

        try:
            integration = PerplexityAnalysisIntegration()
            if integration.is_available:
                logger.debug("Perplexity Sonar integration available for enhanced technical analysis")
                return integration
            else:
                logger.warning("Perplexity integration initialized but API key not available")
                return None
        except Exception as e:
            logger.error(f"Failed to initialize Perplexity integration: {str(e)}")
            return None

    def _run(self, ticker: str, asset_type: str = "stock", lookback_days: int = 100, include_perplexity: bool = True) -> str:
        """Execute enhanced technical analysis."""
        try:
            logger.info(f"Starting enhanced technical analysis for {ticker} ({asset_type})")

            # Get price data
            price_data = self._get_price_data(ticker, lookback_days)
            if not price_data:
                return f"Error: Unable to fetch price data for {ticker}"

            # Perform technical analysis
            technical_analyzer = TechnicalAnalyzer()
            technical_result = technical_analyzer.analyze(ticker, price_data)

            # Optionally get Perplexity insights
            perplexity_insights = []
            if include_perplexity:
                perplexity_integration = self._get_perplexity_integration()
                if perplexity_integration:
                    perplexity_insights = asyncio.run(self._get_perplexity_technical_insights(ticker, asset_type))

            # Format comprehensive response
            return self._format_enhanced_technical_response(
                ticker=ticker,
                asset_type=asset_type,
                technical_result=technical_result,
                perplexity_insights=perplexity_insights,
            )

        except Exception as e:
            logger.error(f"Error in enhanced technical analysis for {ticker}: {str(e)}")
            return f"Error performing enhanced technical analysis for {ticker}: {str(e)}"

    def _get_price_data(self, ticker: str, lookback_days: int) -> PriceData | None:
        """Get historical price data for technical analysis."""
        try:
            # Use yfinance to get historical data
            ticker_obj = yf.Ticker(ticker)
            hist = ticker_obj.history(period=f"{lookback_days}d")

            if hist.empty:
                logger.error(f"No price data available for {ticker}")
                return None

            # Convert to PriceData format
            price_data = PriceData(
                dates=[date.to_pydatetime() for date in hist.index],
                opens=hist["Open"].tolist(),
                highs=hist["High"].tolist(),
                lows=hist["Low"].tolist(),
                closes=hist["Close"].tolist(),
                volumes=hist["Volume"].astype(int).tolist(),
            )

            logger.info(f"Retrieved {price_data.length} days of price data for {ticker}")
            return price_data

        except Exception as e:
            logger.error(f"Error fetching price data for {ticker}: {str(e)}")
            return None

    async def _get_perplexity_technical_insights(self, ticker: str, asset_type: str) -> list[SonarArticle]:
        """Get technical analysis insights from Perplexity Sonar."""
        perplexity_integration = self._get_perplexity_integration()
        if not perplexity_integration:
            return []

        try:
            sonar_result = await perplexity_integration.search_technical_analysis(
                ticker=ticker, asset_type=asset_type, max_results=8
            )

            if sonar_result.success:
                logger.info(f"Retrieved {len(sonar_result.results)} Perplexity technical insights for {ticker}")
                return sonar_result.results
                # Success tracking is handled automatically in PerplexityOperationLogger.log_search_success
            else:
                logger.warning(f"Perplexity technical search failed for {ticker}: {sonar_result.error_message}")
                # Failure tracking is handled automatically in PerplexityOperationLogger.log_search_failure
                return []

        except Exception as e:
            logger.warning(f"Perplexity technical search failed for {ticker}: {str(e)}")

            # Record failure for feature flag tracking
            from finwiz.tools.perplexity_analysis_integration import PerplexityFeatureFlagTracker

            PerplexityFeatureFlagTracker.record_operation_failure(ticker, "technical", "integration_error")
            return []

    def _format_enhanced_technical_response(
        self, ticker: str, asset_type: str, technical_result, perplexity_insights: list[SonarArticle]
    ) -> str:
        """Format comprehensive enhanced technical analysis response."""
        response = f"# Enhanced Technical Analysis for {ticker} ({asset_type.upper()})\n\n"

        # Technical Analysis Summary
        response += "## 📊 Technical Analysis Summary\n"
        response += f"- **Overall Signal**: {technical_result.overall_signal.title()}\n"
        response += f"- **Signal Confidence**: {technical_result.signal_confidence:.1%}\n"
        response += f"- **Analysis Date**: {technical_result.analysis_date.strftime('%Y-%m-%d %H:%M')}\n\n"

        # Fibonacci Levels
        fib = technical_result.fibonacci_levels
        response += "## 📈 Fibonacci Analysis\n"
        response += f"- **Trend Direction**: {fib.trend_direction.title()}\n"
        response += f"- **Swing High**: ${fib.swing_high:.2f} ({fib.swing_high_date.strftime('%Y-%m-%d')})\n"
        response += f"- **Swing Low**: ${fib.swing_low:.2f} ({fib.swing_low_date.strftime('%Y-%m-%d')})\n"
        response += f"- **Current Price**: ${fib.current_price:.2f}\n"

        if fib.nearest_support:
            response += f"- **Nearest Support**: ${fib.nearest_support:.2f}\n"
        if fib.nearest_resistance:
            response += f"- **Nearest Resistance**: ${fib.nearest_resistance:.2f}\n"

        # Key Fibonacci Levels
        response += "\n### Key Fibonacci Levels:\n"
        key_levels = [level for level in fib.levels if level.ratio in [0.236, 0.382, 0.5, 0.618, 0.786]]
        for level in key_levels[:5]:
            response += f"- **{level.ratio}** ({level.level_type}): ${level.price:.2f}\n"

        # Support and Resistance
        sr = technical_result.support_resistance
        response += "\n## 🎯 Support & Resistance\n"
        response += f"- **Current Price**: ${sr.current_price:.2f}\n"
        if sr.nearest_support:
            response += f"- **Nearest Support**: ${sr.nearest_support:.2f}\n"
        if sr.nearest_resistance:
            response += f"- **Nearest Resistance**: ${sr.nearest_resistance:.2f}\n"
        response += f"- **Support/Resistance Ratio**: {sr.support_resistance_ratio:.2f}\n"

        # Strong Support Levels
        strong_supports = [level for level in sr.support_levels if level.strength >= 0.7][:3]
        if strong_supports:
            response += "\n### Strong Support Levels:\n"
            for level in strong_supports:
                response += f"- **${level.price:.2f}** (Strength: {level.strength:.2f}, Touches: {level.touch_count})\n"

        # Strong Resistance Levels
        strong_resistances = [level for level in sr.resistance_levels if level.strength >= 0.7][:3]
        if strong_resistances:
            response += "\n### Strong Resistance Levels:\n"
            for level in strong_resistances:
                response += f"- **${level.price:.2f}** (Strength: {level.strength:.2f}, Touches: {level.touch_count})\n"

        # Technical Indicators
        if technical_result.indicator_signals:
            response += "\n## 🔧 Technical Indicators\n"
            for signal in technical_result.indicator_signals:
                signal_emoji = "🟢" if signal.signal_type == "buy" else "🔴" if signal.signal_type == "sell" else "🟡"
                response += (
                    f"- {signal_emoji} **{signal.indicator_name}**: {signal.description} (Strength: {signal.strength:.2f})\n"
                )

        # Confluence Zones
        if technical_result.confluence_zones:
            response += "\n## 🎯 Confluence Zones\n"
            for i, zone in enumerate(technical_result.confluence_zones[:3], 1):
                zone_emoji = "🟢" if zone.zone_type == "support" else "🔴" if zone.zone_type == "resistance" else "🟡"
                response += f"{i}. {zone_emoji} **{zone.zone_type.title()} Zone**: ${zone.price_range[0]:.2f} - ${zone.price_range[1]:.2f}\n"
                response += f"   - Confluence Score: {zone.confluence_score:.2f}\n"
                response += f"   - Contributing: {', '.join(zone.contributing_indicators)}\n\n"

        # Perplexity Insights
        if perplexity_insights:
            response += "## 🔍 Market Analysis & Price Targets (Perplexity Sonar)\n"
            response += f"Recent technical analysis and analyst opinions ({len(perplexity_insights)} articles):\n\n"

            for i, article in enumerate(perplexity_insights, 1):
                content_emoji = {"news": "📰", "analysis": "📊", "earnings": "💰", "regulatory": "⚖️"}.get(
                    article.content_type, "📊"
                )

                response += f"{i}. {content_emoji} **{article.title}**\n"
                response += f"   - Publisher: {article.publisher}\n"
                response += f"   - Relevance: {article.relevance_score:.2f}\n"
                if article.summary:
                    response += f"   - Summary: {article.summary[:200]}{'...' if len(article.summary) > 200 else ''}\n"
                response += f"   - URL: {article.url}\n\n"

        # Analysis Summary
        response += "## 📈 Enhanced Analysis Summary\n"
        response += f"This comprehensive technical analysis for {ticker} combines:\n"
        response += "- **Fibonacci Analysis**: Key retracement and extension levels\n"
        response += "- **Support/Resistance**: Dynamic levels based on price action\n"
        response += "- **Technical Indicators**: Multi-indicator confluence analysis\n"
        response += "- **Confluence Zones**: Areas where multiple technical factors align\n"

        if perplexity_insights:
            response += f"- **Market Insights**: {len(perplexity_insights)} recent analyst opinions and technical commentary\n\n"
            response += "**Enhanced with Perplexity Sonar**: Recent market analysis provides context for technical levels "
            response += "and helps validate or challenge purely mathematical indicators.\n\n"
        else:
            response += "\n"

        response += "**Trading Recommendation**: Consider the overall signal, confluence zones, and market context "
        response += "when making trading decisions. Technical analysis should be combined with fundamental analysis "
        response += "and proper risk management.\n"

        return response
