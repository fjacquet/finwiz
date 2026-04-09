"""
Enhanced ETF analysis tool for comprehensive factsheet parsing and holdings extraction.

Provides enhanced ETF analysis with factsheet parsing, expense ratio extraction,
tracking difference analysis, and top holdings extraction with proper validation.
Enhanced with optional Perplexity Sonar integration for recent ETF performance updates and holdings changes.
"""

import asyncio
from datetime import datetime
from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel

from finwiz.config.features.flags import get_feature_flags
from finwiz.schemas.perplexity import SonarArticle
from finwiz.schemas.tools import (
    EnhancedETFAnalysisInput,
    ETFTrackingAnalysisInput,
)
from finwiz.tools.etf.etf_analyzers import ETFAnalyzer
from finwiz.tools.etf.etf_data_fetchers import ETFDataFetcher
from finwiz.tools.logger import get_logger
from finwiz.tools.perplexity_analysis_integration import PerplexityAnalysisIntegration

logger = get_logger(__name__)


class EnhancedETFAnalysisTool(BaseTool):
    """
    Enhanced ETF analysis tool with comprehensive factsheet parsing.

    Provides detailed ETF analysis including:
    - Factsheet parsing for expense ratios and tracking differences
    - Top holdings extraction with weights and validation
    - Risk assessment based on concentration and volatility
    - Structured output for downstream processing
    - Optional Perplexity Sonar integration for recent ETF performance updates and holdings changes
    """

    name: str = "Enhanced ETF Analysis Tool"
    description: str = (
        "Comprehensive ETF analysis tool that parses factsheets, extracts holdings, "
        "calculates tracking differences, and performs risk assessment. "
        "Optionally enhanced with Perplexity Sonar for recent ETF performance updates and holdings changes."
    )
    args_schema: type[BaseModel] = EnhancedETFAnalysisInput

    def _get_perplexity_integration(self) -> PerplexityAnalysisIntegration | None:
        """Get Perplexity integration instance if enabled."""
        feature_flags = get_feature_flags()

        # Check feature flag status and log for debugging
        is_enabled = feature_flags.is_enabled("perplexity_research")
        fallback_strategy = feature_flags.get_fallback_strategy("perplexity_research").value

        from finwiz.tools.perplexity_analysis_integration import PerplexityOperationLogger

        PerplexityOperationLogger.log_feature_flag_status("etf_analysis", is_enabled, fallback_strategy)

        if not is_enabled:
            return None

        try:
            integration = PerplexityAnalysisIntegration()
            if integration.is_available:
                logger.debug("Perplexity Sonar integration available for ETF analysis")
                return integration
            else:
                logger.warning("Perplexity integration initialized but API key not available")
                return None
        except Exception as e:
            logger.error(f"Failed to initialize Perplexity integration: {e!s}")
            return None

    def _run(
        self,
        ticker: str,
        include_holdings: bool = True,
        include_risk_assessment: bool = True,
        max_holdings: int = 10,
        include_perplexity: bool = True,
    ) -> dict[str, Any]:
        """Execute enhanced ETF analysis."""
        try:
            logger.info(f"Starting enhanced ETF analysis for {ticker}")

            # Normalize ticker
            ticker = ticker.upper().strip()

            # Extract factsheet data
            factsheet_data = self._extract_factsheet_data(ticker)
            if "error" in factsheet_data:
                return factsheet_data

            # Extract top holdings if requested
            holdings_data = []
            if include_holdings:
                holdings_data = self._extract_top_holdings(ticker, max_holdings)

            # Perform risk assessment if requested
            risk_assessment = None
            if include_risk_assessment:
                risk_assessment = self._perform_etf_risk_assessment(ticker, factsheet_data, holdings_data)

            # Optionally get Perplexity ETF insights
            perplexity_insights = []
            if include_perplexity:
                perplexity_integration = self._get_perplexity_integration()
                if perplexity_integration:
                    perplexity_insights = asyncio.run(self._get_perplexity_etf_insights(ticker))

            # Construct ETF factsheet object
            etf_factsheet = self._construct_etf_factsheet(ticker, factsheet_data, holdings_data, risk_assessment)

            return {
                "ticker": ticker,
                "factsheet": etf_factsheet,
                "holdings_count": len(holdings_data),
                "risk_assessment": risk_assessment,
                "perplexity_insights": perplexity_insights,
                "analysis_timestamp": datetime.now().isoformat(),
                "data_sources": factsheet_data.get("sources", []),
            }

        except Exception as e:
            logger.error(f"Enhanced ETF analysis failed for {ticker}: {e!s}")
            return {"error": f"Enhanced ETF analysis failed for {ticker}: {e}"}

    def _extract_factsheet_data(self, ticker: str) -> dict[str, Any]:
        """Extract factsheet data from various sources."""
        return ETFDataFetcher.extract_factsheet_data(ticker)

    def _extract_top_holdings(self, ticker: str, max_holdings: int) -> list[dict[str, Any]]:
        """Extract top holdings for the ETF."""
        return ETFDataFetcher.extract_top_holdings(ticker, max_holdings)

    def _perform_etf_risk_assessment(self, ticker: str, factsheet_data: dict[str, Any], holdings_data: list[dict[str, Any]]) -> dict[str, Any]:
        """Perform standardized risk assessment for ETF."""
        return ETFAnalyzer.perform_etf_risk_assessment(ticker, factsheet_data, holdings_data)

    def _construct_etf_factsheet(
        self,
        ticker: str,
        factsheet_data: dict[str, Any],
        holdings_data: list[dict[str, Any]],
        risk_assessment: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Construct ETF factsheet object from extracted data."""
        return ETFAnalyzer.construct_etf_factsheet(ticker, factsheet_data, holdings_data, risk_assessment)

    async def _get_perplexity_etf_insights(self, ticker: str) -> list[SonarArticle]:
        """Get ETF-specific insights from Perplexity Sonar."""
        perplexity_integration = self._get_perplexity_integration()
        if not perplexity_integration:
            return []

        try:
            # Create ETF-specific search query
            query = f"{ticker} ETF fund performance holdings changes expense ratio tracking error"

            sonar_result = await perplexity_integration.search_financial_news(query=query, ticker=ticker, asset_type="etf", analysis_type="general", max_results=6)

            if sonar_result.success:
                logger.info(f"Retrieved {len(sonar_result.results)} Perplexity ETF insights for {ticker}")
                return sonar_result.results
                # Success tracking is handled automatically in PerplexityOperationLogger.log_search_success
            else:
                logger.warning(f"Perplexity ETF search failed for {ticker}: {sonar_result.error_message}")
                # Failure tracking is handled automatically in PerplexityOperationLogger.log_search_failure
                return []

        except Exception as e:
            logger.warning(f"Perplexity ETF search failed for {ticker}: {e!s}")
            return []


class ETFTrackingAnalysisTool(BaseTool):
    """
    Specialized tool for ETF tracking performance analysis.

    Analyzes tracking error, tracking difference, and performance
    attribution for ETFs against their benchmarks.
    """

    name: str = "ETF Tracking Analysis Tool"
    description: str = "Analyze ETF tracking performance including tracking error, tracking difference, and performance attribution analysis."
    args_schema: type[BaseModel] = ETFTrackingAnalysisInput

    def _run(self, ticker: str, **kwargs: Any) -> dict[str, Any]:
        """Analyze ETF tracking performance."""
        return {
            "tool": "ETFTrackingAnalysisTool",
            "ticker": ticker,
            "message": "Use EnhancedETFAnalysisTool for comprehensive tracking analysis",
            "methodology": "Tracking error and difference calculation with benchmark comparison",
        }
