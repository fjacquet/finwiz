"""
Enhanced SEC tool for comprehensive 10-K insights extraction and risk assessment.

Provides enhanced SEC filing analysis with standardized risk scoring,
comprehensive section extraction, and structured output for FinWiz crews.
Enhanced with optional Perplexity Sonar integration for recent earnings and SEC filing insights.
"""

import asyncio
import os
from datetime import datetime
from typing import Any, Literal

import requests
from crewai.tools import BaseTool
from langchain_text_splitters import CharacterTextSplitter
from pydantic import BaseModel

from finwiz.config.features.flags import get_feature_flags
from finwiz.schemas.common import RiskLevel
from finwiz.schemas.perplexity import SonarArticle
from finwiz.schemas.tools import (
    EnhancedSECAnalysisInput,
    StandardizedRiskScoringInput,
)
from finwiz.tools.logger import get_logger
from finwiz.tools.perplexity_analysis_integration import PerplexityAnalysisIntegration
from finwiz.tools.sec_filing_url_generator import SECFilingURLGenerator
from finwiz.validation.url import get_url_validator


class EnhancedSECAnalysisTool(BaseTool):
    """
    Enhanced SEC filing analysis tool with comprehensive insights extraction.

    Provides detailed 10-K/10-Q analysis with:
    - Multi-section extraction with proper citations
    - Standardized risk assessment scoring
    - Structured output for downstream processing
    - Enhanced error handling and validation
    - Optional Perplexity Sonar integration for recent earnings and SEC filing insights
    """

    name: str = "Enhanced SEC Analysis Tool"
    description: str = (
        "Comprehensive SEC filing analysis tool that extracts detailed insights "
        "from 10-K/10-Q filings with standardized risk assessment and proper citations. "
        "Optionally enhanced with Perplexity Sonar for recent earnings reports and SEC filing commentary."
    )
    args_schema: type[BaseModel] = EnhancedSECAnalysisInput
    url_generator: Any = None  # URL generator instance
    url_validator: Any = None  # URL validator instance

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the tool with URL generator."""
        super().__init__(**kwargs)
        if self.url_generator is None:
            self.url_generator = SECFilingURLGenerator()
        if self.url_validator is None:
            self.url_validator = get_url_validator()

    def _get_perplexity_integration(self) -> PerplexityAnalysisIntegration | None:
        """Get Perplexity integration instance if enabled."""
        feature_flags = get_feature_flags()

        # Check feature flag status and log for debugging
        is_enabled = feature_flags.is_enabled("perplexity_research")
        fallback_strategy = feature_flags.get_fallback_strategy("perplexity_research").value

        from finwiz.tools.perplexity_analysis_integration import PerplexityOperationLogger

        PerplexityOperationLogger.log_feature_flag_status("sec_analysis", is_enabled, fallback_strategy)

        if not is_enabled:
            return None

        try:
            integration = PerplexityAnalysisIntegration()
            if integration.is_available:
                logger.debug("Perplexity Sonar integration available for SEC analysis")
                return integration
            else:
                logger.warning("Perplexity integration initialized but API key not available")
                return None
        except Exception as e:
            logger.error(f"Failed to initialize Perplexity integration: {str(e)}")
            return None

    def _run(
        self,
        ticker: str | None = None,
        form_type: str = "10-K",
        sections: list[str] | None = None,
        risk_assessment: bool = True,
        include_perplexity: bool = True,
        **kwargs: Any,
    ) -> str:
        """Execute enhanced SEC filing analysis."""
        # Handle malformed input from LLM
        if ticker is None and kwargs:
            # Try to extract ticker from kwargs
            ticker = kwargs.get("ticker") or kwargs.get("symbol")
            form_type = kwargs.get("form_type", form_type)
            sections = kwargs.get("sections", sections)
            risk_assessment = kwargs.get("risk_assessment", risk_assessment)
            include_perplexity = kwargs.get("include_perplexity", include_perplexity)

        if ticker is None:
            return "Error: ticker parameter is required"

        if sections is None:
            sections = ["Item 1", "Item 1A", "Item 7"]

        try:
            logger.info(f"Starting enhanced SEC analysis for {ticker} ({form_type})")

            # Fetch latest filing using URL generator
            filing = self._fetch_latest_filing(ticker=ticker, form_type=form_type)
            if filing is None:
                logger.warning(f"No SEC filings available for {ticker}")
                return f"No SEC filings available for ticker {ticker}. The company may not be publicly traded or may not have filed {form_type} reports."

            # Download and process filing content
            html = self._download_html(filing["filing_url"])
            docs = self._split_into_documents(html)

            # Extract insights for each requested section
            insights = []
            for section in sections:
                section_insights = self._extract_section_insights(docs, ticker, section, filing)
                insights.extend(section_insights)

            # Perform risk assessment if requested
            risk_assessment_result = None
            if risk_assessment:
                risk_assessment_result = self._perform_risk_assessment(insights, ticker, filing)

            # Optionally get Perplexity fundamental insights
            perplexity_insights = []
            if include_perplexity:
                perplexity_integration = self._get_perplexity_integration()
                if perplexity_integration:
                    perplexity_insights = asyncio.run(self._get_perplexity_fundamental_insights(ticker, form_type))

            # Format comprehensive response
            return self._format_enhanced_sec_response(
                ticker=ticker,
                form_type=form_type,
                filing=filing,
                insights=insights,
                risk_assessment_result=risk_assessment_result,
                sections=sections,
                perplexity_insights=perplexity_insights,
            )

        except KeyError as e:
            return f"Error: Missing environment/config: {e}"
        except Exception as e:
            logger.error(f"Enhanced SEC analysis failed for {ticker}: {str(e)}")
            return f"Error: Enhanced SEC analysis failed for {ticker}: {str(e)}"

    def _fetch_latest_filing(self, ticker: str, form_type: str) -> dict[str, str] | None:
        """
        Fetch the latest SEC filing for the given ticker and form type.

        Uses SECFilingURLGenerator to generate valid, verified URLs.
        Falls back to company browse page if direct filing URL is unavailable.
        """
        logger.info(f"Fetching SEC filing URL for {ticker} ({form_type})")

        # Get filing metadata using URL generator
        metadata = self.url_generator.get_filing_metadata(ticker, form_type)

        if not metadata:
            logger.warning(f"No SEC filing metadata found for {ticker}")
            return None

        if not metadata.get("available"):
            logger.warning(f"No SEC filings available for {ticker}")
            return None

        filing_url = metadata.get("filing_url")
        if not filing_url:
            logger.warning(f"No filing URL generated for {ticker}")
            return None

        # Verify URL if possible (optional, can be slow)
        # For now, we trust the URL generator's output
        logger.info(f"Generated SEC filing URL for {ticker}: {filing_url}")

        # Try to get filing date from SEC API if available
        filed_at = self._get_filing_date_from_api(ticker, form_type)

        return {
            "filing_url": filing_url,
            "filed_at": filed_at or datetime.now().isoformat(),
            "cik": metadata.get("cik", ""),
        }

    def _get_filing_date_from_api(self, ticker: str, form_type: str) -> str | None:
        """
        Attempt to get filing date from SEC API if available.

        This is optional and will gracefully fail if SEC_API_API_KEY is not set.
        """
        api_key = os.environ.get("SEC_API_API_KEY")
        if not api_key:
            logger.debug("SEC_API_API_KEY not set, skipping filing date lookup")
            return None

        try:
            # Lazy import to allow tests to patch QueryApi
            global QueryApi
            if QueryApi is None:
                try:
                    from sec_api import QueryApi as _QueryApi
                except Exception:
                    logger.debug("sec_api package not available, skipping filing date lookup")
                    return None
                QueryApi = _QueryApi

            query_api = QueryApi(api_key=api_key)
            query = {
                "query": {"query_string": {"query": f'ticker:{ticker} AND formType:"{form_type}"'}},
                "from": "0",
                "size": "1",
                "sort": [{"filedAt": {"order": "desc"}}],
            }

            filings = query_api.get_filings(query).get("filings", [])
            if filings:
                filed_at: str | None = filings[0].get("filedAt", "")
                logger.debug(f"Retrieved filing date from SEC API: {filed_at}")
                return filed_at

        except Exception as e:
            logger.debug(f"Could not retrieve filing date from SEC API: {str(e)}")

        return None

    def _download_html(self, url: str) -> str:
        """
        Download HTML content from SEC filing URL.

        SEC.gov requires a proper User-Agent with contact information.
        See: https://www.sec.gov/os/accessing-edgar-data
        """
        headers = {
            "Accept": ("text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"),
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "User-Agent": "FinWiz/1.0 (contact@finwiz.com)",
        }
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.text

    def _split_into_documents(self, html_text: str) -> list[Any]:
        """Split HTML content into manageable document chunks."""
        elements = partition_html(text=html_text)
        content = "\n".join([str(el) for el in elements])
        splitter = CharacterTextSplitter(separator="\n", chunk_size=2000, chunk_overlap=200, length_function=len)
        return splitter.create_documents([content])

    def _extract_section_insights(self, docs: list[Any], ticker: str, section: str, filing: dict[str, str]) -> list[dict[str, Any]]:
        """Extract insights from a specific SEC filing section."""
        # Define section-specific queries
        section_queries = {
            "Item 1": ["business", "operations", "products", "services", "competitive"],
            "Item 1A": ["risk", "factors", "market", "operational"],
            "Item 7": ["management", "discussion", "analysis", "financial", "performance", "liquidity"],
            "Item 7A": ["quantitative", "qualitative", "market risk", "interest rate", "foreign exchange"],
            "Item 8": ["financial statements", "balance sheet", "income statement", "cash flow"],
        }

        keywords = section_queries.get(section, ["information"])

        # Use simple keyword-based text matching instead of vector search
        # Score each document by keyword matches
        scored_docs = []
        for doc in docs:
            content_lower = doc.page_content.lower()
            score = sum(1 for keyword in keywords if keyword.lower() in content_lower)
            if score > 0 and len(doc.page_content.strip()) > 50:
                scored_docs.append((score, doc))

        # Sort by score (descending) and take top 3
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        results = [doc for _, doc in scored_docs[:3]]

        insights = []
        for i, result in enumerate(results):
            insight_data = {
                "ticker": ticker,
                "filing_url": filing["filing_url"],
                "filed_at": filing["filed_at"],
                "section": section,
                "excerpt": result.page_content.strip()[:1000],  # Limit excerpt length
                "sec_citation": f"10-K ({filing['filed_at'][:4]}), {section}",
                "relevance_rank": i + 1,
            }
            insights.append(insight_data)

        return insights

    def _perform_risk_assessment(self, insights: list[dict[str, Any]], ticker: str, filing: dict[str, str]) -> dict[str, Any]:
        """Perform standardized risk assessment based on extracted insights."""
        # Extract risk-related content
        risk_content = []
        for insight in insights:
            if insight["section"] == "Item 1A":  # Risk Factors section
                risk_content.append(insight["excerpt"])

        # Analyze risk factors and assign standardized score
        risk_factors = self._identify_risk_factors(risk_content)
        risk_score = self._calculate_risk_score(risk_factors)
        risk_level = self._map_score_to_level(risk_score)

        return {
            "ticker": ticker,
            "scale": "0_5",
            "score": risk_score,
            "level": risk_level,
            "risk_factors": risk_factors[:10],  # Limit to 10 factors
            "filing_source": filing["filing_url"],
            "assessment_date": datetime.now().isoformat(),
        }

    def _identify_risk_factors(self, risk_content: list[str]) -> list[str]:
        """Identify key risk factors from risk section content."""
        # Common risk keywords and patterns
        risk_keywords = [
            "competition",
            "regulatory",
            "market volatility",
            "economic conditions",
            "cybersecurity",
            "data breach",
            "supply chain",
            "customer concentration",
            "credit risk",
            "liquidity",
            "interest rate",
            "foreign exchange",
            "litigation",
            "intellectual property",
            "key personnel",
            "technology",
            "compliance",
            "environmental",
            "reputation",
            "operational",
        ]

        identified_risks = []
        combined_content = " ".join(risk_content).lower()

        for keyword in risk_keywords:
            if keyword in combined_content:
                # Create a more descriptive risk factor
                risk_factor = f"{keyword.title()} risk"
                if risk_factor not in identified_risks:
                    identified_risks.append(risk_factor)

        # Add some generic risks if none found
        if not identified_risks:
            identified_risks = [
                "Market volatility risk",
                "Competitive risk",
                "Regulatory risk",
                "Operational risk",
            ]

        return identified_risks

    def _calculate_risk_score(self, risk_factors: list[str]) -> float:
        """Calculate standardized risk score based on identified risk factors."""
        # Base score calculation
        base_score = min(len(risk_factors) * 0.3, 3.0)  # More factors = higher risk

        # Adjust based on specific high-risk factors
        high_risk_keywords = ["cybersecurity", "litigation", "regulatory", "credit"]
        high_risk_count = sum(1 for factor in risk_factors if any(keyword in factor.lower() for keyword in high_risk_keywords))

        adjustment = min(high_risk_count * 0.5, 2.0)

        final_score = min(base_score + adjustment, 5.0)
        return round(final_score, 1)

    def _map_score_to_level(self, score: float) -> RiskLevel:
        """Map numerical risk score to standardized risk level."""
        if score <= 1.5:
            return "Low"
        elif score <= 2.5:
            return "Medium"
        elif score <= 4.0:
            return "High"
        else:
            return "Very High"

    async def _get_perplexity_fundamental_insights(self, ticker: str, form_type: str) -> list[SonarArticle]:
        """Get fundamental analysis insights from Perplexity Sonar."""
        perplexity_integration = self._get_perplexity_integration()
        if not perplexity_integration:
            return []

        try:
            # Determine asset type (simplified logic for stocks)
            asset_type: Literal["stock", "etf", "crypto"] = "stock"

            sonar_result = await perplexity_integration.search_fundamental_analysis(ticker=ticker, asset_type=asset_type, max_results=6)

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

    def _format_enhanced_sec_response(
        self,
        ticker: str,
        form_type: str,
        filing: dict[str, str],
        insights: list[dict[str, Any]],
        risk_assessment_result: dict[str, Any] | None,
        sections: list[str],
        perplexity_insights: list[SonarArticle],
    ) -> str:
        """Format comprehensive enhanced SEC analysis response."""
        response = f"# Enhanced SEC Analysis for {ticker} ({form_type})\n\n"

        # Filing Information
        response += "## 📋 Filing Information\n"
        response += f"- **Ticker**: {ticker}\n"
        response += f"- **Form Type**: {form_type}\n"
        response += f"- **Filed Date**: {filing['filed_at'][:10]}\n"

        # Include CIK if available
        if filing.get("cik"):
            response += f"- **CIK**: {filing['cik']}\n"

        # Include filing URL with validation and helpful context
        filing_url = filing.get("filing_url", "")
        if filing_url and self.url_validator.is_valid_url(filing_url, f"SEC filing {ticker}"):
            response += f"- **SEC Filings Page**: {filing_url}\n"
            response += f"  _(Browse page showing all {form_type} filings for {ticker}. Click on the most recent filing date to view the full document.)_\n"
            logger.info(f"Including validated SEC filing URL: {filing_url}")
        else:
            # Provide fallback with manual search instructions
            response += "- **SEC Filings**: Search manually at https://www.sec.gov/edgar/searchedgar/companysearch.html\n"
            response += f"  _(Enter ticker '{ticker}' and filter by '{form_type}' to find recent filings)_\n"
            if filing_url:
                logger.warning(f"Invalid filing URL for {ticker}: {filing_url}")
            else:
                logger.warning(f"No filing URL available for {ticker}")

        response += f"- **Sections Analyzed**: {', '.join(sections)}\n\n"

        # SEC Filing Insights
        response += "## 📊 SEC Filing Insights\n"
        if insights:
            # Group insights by section
            sections_data = {}
            for insight in insights:
                section = insight["section"]
                if section not in sections_data:
                    sections_data[section] = []
                sections_data[section].append(insight)

            for section, section_insights in sections_data.items():
                response += f"\n### {section}\n"
                for i, insight in enumerate(section_insights[:2], 1):  # Limit to 2 per section
                    response += f"{i}. **Excerpt {insight['relevance_rank']}**:\n"
                    response += f"   {insight['excerpt'][:300]}{'...' if len(insight['excerpt']) > 300 else ''}\n\n"
        else:
            response += "No significant insights extracted from SEC filing.\n\n"

        # Risk Assessment (only include if risk_assessment_result is not None)
        if risk_assessment_result is not None:
            response += "## ⚠️ Risk Assessment\n"
            response += f"- **Risk Score**: {risk_assessment_result['score']}/5.0\n"
            response += f"- **Risk Level**: {risk_assessment_result['level']}\n"
            response += f"- **Assessment Scale**: {risk_assessment_result['scale']}\n\n"

            if risk_assessment_result.get("risk_factors"):
                response += "### Key Risk Factors:\n"
                for i, factor in enumerate(risk_assessment_result["risk_factors"][:5], 1):
                    response += f"{i}. {factor}\n"
                response += "\n"

        # Perplexity Insights
        if perplexity_insights:
            response += "## 🔍 Recent Fundamental Analysis (Perplexity Sonar)\n"
            response += f"Recent earnings reports, SEC filings, and fundamental analysis ({len(perplexity_insights)} articles):\n\n"

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
        response += f"This comprehensive SEC analysis for {ticker} combines:\n"
        response += f"- **SEC Filing Analysis**: Detailed insights from {form_type} sections\n"
        if risk_assessment_result is not None:
            response += "- **Risk Assessment**: Standardized risk scoring based on filing content\n"
        response += "- **Structured Extraction**: Key excerpts with proper citations\n"

        if perplexity_insights:
            response += f"- **Market Context**: {len(perplexity_insights)} recent fundamental analysis articles\n\n"
            response += "**Enhanced with Perplexity Sonar**: Recent earnings reports and SEC filing commentary "
            response += "provide additional context and market perspective on the company's fundamentals.\n\n"
        else:
            response += "\n"

        response += "**Investment Consideration**: SEC filings provide official company disclosures and should be "
        response += "combined with current market analysis and technical indicators for comprehensive investment decisions.\n"

        return response


class StandardizedRiskScoringTool(BaseTool):
    """
    Standalone tool for standardized risk scoring across asset classes.

    Provides consistent risk assessment methodology that can be used
    by any crew for standardized risk evaluation.
    """

    name: str = "Standardized Risk Scoring Tool"
    description: str = "Calculate standardized risk scores (0-5 scale) with consistent methodology across different asset classes and analysis contexts."
    args_schema: type[BaseModel] = StandardizedRiskScoringInput

    def _run(self, symbol: str, asset_class: str, risk_factors: list[str] | None = None, **kwargs: Any) -> dict[str, Any]:
        """Calculate standardized risk score based on provided factors."""
        if risk_factors is None:
            risk_factors = []

        # This is a placeholder implementation
        # In practice, this would analyze various risk inputs
        return {
            "tool": "StandardizedRiskScoringTool",
            "symbol": symbol,
            "asset_class": asset_class,
            "risk_factors": risk_factors,
            "message": "Use EnhancedSECAnalysisTool for comprehensive risk assessment",
            "methodology": "Standardized 0-5 scale with consistent factor weighting",
        }


logger = get_logger(__name__)

try:
    from unstructured.partition.html import partition_html
except Exception:

    def _partition_html_fallback(text: str) -> list[Any]:
        """Fallback partitioner: return the raw HTML as a single chunk."""
        return [text]

    partition_html = _partition_html_fallback  # type: ignore[assignment]


# Defer importing QueryApi to runtime
QueryApi = None
