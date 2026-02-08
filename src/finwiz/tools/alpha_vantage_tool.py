"""
Alpha Vantage API Tools for FinWiz.

This module provides tools to interact with the Alpha Vantage API for fetching
comprehensive financial data, including fundamental data, technical indicators,
and more. Enhanced with optional Perplexity Sonar integration.
"""

import asyncio
import json
import os
from datetime import UTC, datetime
from typing import Literal, cast

import requests
from crewai.tools import BaseTool
from dotenv import load_dotenv
from pydantic import BaseModel

from finwiz.config.features.flags import get_feature_flags
from finwiz.infrastructure.caching.manager import cache_key, cached
from finwiz.infrastructure.decorators.api_decorators import api_tool
from finwiz.infrastructure.resilience.rate_limiter import APIProvider
from finwiz.schemas.perplexity import SonarArticle
from finwiz.schemas.tools import CompanyOverviewInput
from finwiz.tools.logger import get_logger
from finwiz.tools.perplexity_analysis_integration import PerplexityAnalysisIntegration

logger = get_logger(__name__)

load_dotenv()


class AlphaVantageCompanyOverviewTool(BaseTool):
    """
    A tool to fetch company overview and fundamental data from Alpha Vantage.

    This tool uses the Alpha Vantage API to retrieve key financial metrics
    and company information for a given stock ticker. It requires an
    ALPHA_VANTAGE_API_KEY to be set in the environment variables.
    Enhanced with optional Perplexity Sonar integration for recent fundamental analysis.
    """

    name: str = "Alpha Vantage Company Overview"
    description: str = (
        "Fetches fundamental data and a company overview for a specific stock ticker "
        "from Alpha Vantage. Use this to get detailed financial metrics like Market Cap, "
        "P/E Ratio, EPS, and more. Optionally enhanced with Perplexity Sonar for recent "
        "fundamental analysis and earnings commentary."
    )
    args_schema: type[BaseModel] = CompanyOverviewInput

    def _get_perplexity_integration(self) -> PerplexityAnalysisIntegration | None:
        """Get Perplexity integration instance if enabled."""
        feature_flags = get_feature_flags()

        if not feature_flags.is_enabled("perplexity_research"):
            return None

        try:
            integration = PerplexityAnalysisIntegration()
            if integration.is_available:
                logger.debug("Perplexity Sonar integration available for Alpha Vantage analysis")
                return integration
            else:
                logger.warning("Perplexity integration initialized but API key not available")
                return None
        except Exception as e:
            logger.error(f"Failed to initialize Perplexity integration: {str(e)}")
            return None

    def _run(self, ticker: str, include_perplexity: bool = True, prefetched_data: dict | None = None) -> str:
        """
        Execute the tool to fetch company overview data.

        Args:
            ticker: Stock ticker symbol
            include_perplexity: Whether to include Perplexity Sonar insights
            prefetched_data: Optional pre-fetched Alpha Vantage data from batch operation

        Returns:
            Formatted company overview string

        """
        try:
            # Check for pre-fetched data first
            if prefetched_data is not None and ticker in prefetched_data:
                logger.debug(f"Using pre-fetched Alpha Vantage data for {ticker} (source: batch)")
                alpha_vantage_data = prefetched_data[ticker]

                # If it's already a string (JSON), use it directly
                if isinstance(alpha_vantage_data, str):
                    pass
                else:
                    # Convert dict to JSON string
                    alpha_vantage_data = json.dumps(alpha_vantage_data, indent=2, default=str)
            else:
                # Fall back to live API call
                logger.info(f"Fetching Alpha Vantage company overview for {ticker} with optional Perplexity enhancement")
                alpha_vantage_data = asyncio.run(self._fetch_company_overview(ticker))

            # Optionally get Perplexity fundamental insights
            perplexity_insights = []
            if include_perplexity:
                perplexity_integration = self._get_perplexity_integration()
                if perplexity_integration:
                    perplexity_insights = asyncio.run(self._get_perplexity_fundamental_insights(ticker))

            # Format enhanced response
            return self._format_enhanced_overview_response(
                ticker=ticker,
                alpha_vantage_data=alpha_vantage_data,
                perplexity_insights=perplexity_insights,
            )

        except Exception as e:
            logger.error(f"Error in enhanced Alpha Vantage analysis for {ticker}: {str(e)}")
            return f"Error performing enhanced company overview analysis for {ticker}: {str(e)}"

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

            return json.dumps(data, indent=2, default=str)

        # Use caching with 30-minute TTL for company overview data
        result: str = await cached(
            cache_key_str,
            fetch_from_api,
            ttl=1800,  # 30 minutes
            tags={"alpha_vantage", "company_overview", ticker.upper()},
        )
        return result

    async def _get_perplexity_fundamental_insights(self, ticker: str) -> list[SonarArticle]:
        """Get fundamental analysis insights from Perplexity Sonar."""
        perplexity_integration = self._get_perplexity_integration()
        if not perplexity_integration:
            return []

        try:
            # Determine asset type (simplified logic for stocks)
            asset_type = "stock"

            sonar_result = await perplexity_integration.search_fundamental_analysis(ticker=ticker, asset_type=cast(Literal["stock", "etf", "crypto"], asset_type), max_results=5)

            if sonar_result.success:
                logger.info(f"Retrieved {len(sonar_result.results)} Perplexity fundamental insights for {ticker}")
                return sonar_result.results
                # Success tracking is handled automatically in PerplexityOperationLogger.log_search_success
            else:
                logger.warning(f"Perplexity fundamental search failed for {ticker}: {sonar_result.error_message}")
                # Failure tracking is handled automatically in PerplexityOperationLogger.log_search_failure
                return []

        except Exception as e:
            logger.warning(f"Perplexity fundamental search failed for {ticker}: {str(e)}")

            # Record failure for feature flag tracking
            from finwiz.tools.perplexity_logging import PerplexityFeatureFlagTracker

            PerplexityFeatureFlagTracker.record_operation_failure(ticker, "fundamental", "integration_error")
            return []

    def _format_enhanced_overview_response(self, ticker: str, alpha_vantage_data: str, perplexity_insights: list[SonarArticle]) -> str:
        """Format enhanced company overview response combining Alpha Vantage and Perplexity data."""
        response = f"# Enhanced Company Overview for {ticker}\n\n"

        # Add Alpha Vantage fundamental data
        response += "## 📊 Fundamental Data (Alpha Vantage)\n"

        # Try to parse and format Alpha Vantage data nicely
        try:
            av_data = json.loads(alpha_vantage_data)
            if isinstance(av_data, dict) and "Symbol" in av_data:
                # Format key metrics nicely
                response += f"**Company**: {av_data.get('Name', 'N/A')}\n"
                response += f"**Sector**: {av_data.get('Sector', 'N/A')}\n"
                response += f"**Industry**: {av_data.get('Industry', 'N/A')}\n"
                response += f"**Market Cap**: {av_data.get('MarketCapitalization', 'N/A')}\n"
                response += f"**P/E Ratio**: {av_data.get('PERatio', 'N/A')}\n"
                response += f"**EPS**: {av_data.get('EPS', 'N/A')}\n"
                response += f"**Revenue (TTM)**: {av_data.get('RevenueTTM', 'N/A')}\n"
                response += f"**Profit Margin**: {av_data.get('ProfitMargin', 'N/A')}\n"
                response += f"**Dividend Yield**: {av_data.get('DividendYield', 'N/A')}\n\n"

                if av_data.get("Description"):
                    response += f"**Description**: {av_data['Description'][:300]}{'...' if len(av_data['Description']) > 300 else ''}\n\n"
            else:
                response += f"{alpha_vantage_data}\n\n"
        except (json.JSONDecodeError, KeyError):
            response += f"{alpha_vantage_data}\n\n"

        # Add Perplexity insights if available
        if perplexity_insights:
            response += "## 🔍 Recent Fundamental Analysis (Perplexity Sonar)\n"
            response += f"Recent earnings reports and fundamental analysis ({len(perplexity_insights)} articles):\n\n"

            for i, article in enumerate(perplexity_insights, 1):
                content_emoji = {"news": "📰", "filing": "📋", "analysis": "📊", "earnings": "💰", "regulatory": "⚖️"}.get(article.content_type, "📊")

                response += f"{i}. {content_emoji} **{article.title}**\n"
                response += f"   - Publisher: {article.publisher}\n"
                response += f"   - Content Type: {article.content_type.title()}\n"
                response += f"   - Relevance: {article.relevance_score:.2f}\n"
                if article.summary:
                    response += f"   - Summary: {article.summary[:200]}{'...' if len(article.summary) > 200 else ''}\n"
                response += f"   - URL: {article.url}\n\n"

        # Analysis Summary
        response += "## 📈 Enhanced Analysis Summary\n"
        response += f"This comprehensive company overview for {ticker} combines:\n"
        response += "- **Alpha Vantage Data**: Official fundamental metrics and company information\n"
        response += "- **Financial Metrics**: Key ratios, profitability, and valuation data\n"

        if perplexity_insights:
            response += f"- **Market Context**: {len(perplexity_insights)} recent fundamental analysis articles\n\n"
            response += "**Enhanced with Perplexity Sonar**: Recent earnings reports and fundamental analysis "
            response += "provide current market perspective and analyst opinions on the company's financial performance.\n\n"
        else:
            response += "\n"

        response += "**Investment Consideration**: Combine fundamental data with technical analysis and market trends "
        response += "for comprehensive investment decisions. Consider the company's competitive position and growth prospects.\n"

        return response
