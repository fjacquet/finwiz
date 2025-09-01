"""
Enhanced SEC tool for comprehensive 10-K insights extraction and risk assessment.

Provides enhanced SEC filing analysis with standardized risk scoring,
comprehensive section extraction, and structured output for FinWiz crews.
"""

import os
from datetime import datetime
from typing import Any, Literal

import requests
from crewai.tools import BaseTool
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from pydantic import BaseModel, Field

from finwiz.schemas.common import RiskLevel

try:
    from unstructured.partition.html import partition_html
except Exception:

    def partition_html(text: str) -> list[Any]:
        """Fallback partitioner: return the raw HTML as a single chunk."""
        return [text]


# Defer importing QueryApi to runtime
QueryApi = None


class EnhancedSECAnalysisInput(BaseModel):
    """Input schema for Enhanced SEC Analysis Tool."""

    ticker: str = Field(..., description="The stock ticker symbol, e.g., AAPL")
    form_type: Literal["10-K", "10-Q"] = Field(default="10-K", description="SEC form type to analyze")
    sections: list[Literal["Item 1", "Item 1A", "Item 7", "Item 7A", "Item 8"]] = Field(
        default=["Item 1", "Item 1A", "Item 7"], description="SEC sections to extract insights from"
    )
    risk_assessment: bool = Field(default=True, description="Whether to perform standardized risk assessment")


class EnhancedSECAnalysisTool(BaseTool):
    """
    Enhanced SEC filing analysis tool with comprehensive insights extraction.

    Provides detailed 10-K/10-Q analysis with:
    - Multi-section extraction with proper citations
    - Standardized risk assessment scoring
    - Structured output for downstream processing
    - Enhanced error handling and validation
    """

    name: str = "Enhanced SEC Analysis Tool"
    description: str = (
        "Comprehensive SEC filing analysis tool that extracts detailed insights "
        "from 10-K/10-Q filings with standardized risk assessment and proper citations."
    )
    args_schema: type[BaseModel] = EnhancedSECAnalysisInput

    def _run(
        self, ticker: str, form_type: str = "10-K", sections: list[str] = None, risk_assessment: bool = True
    ) -> dict[str, Any]:
        """Execute enhanced SEC filing analysis."""
        if sections is None:
            sections = ["Item 1", "Item 1A", "Item 7"]

        try:
            # Fetch latest filing
            filing = self._fetch_latest_filing(ticker=ticker, form_type=form_type)
            if filing is None:
                return {
                    "error": f"No {form_type} filing found for ticker {ticker}",
                    "ticker": ticker,
                    "form_type": form_type,
                }

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

            return {
                "ticker": ticker,
                "form_type": form_type,
                "filing_url": filing["filing_url"],
                "filed_at": filing["filed_at"],
                "insights": insights,
                "risk_assessment": risk_assessment_result,
                "sections_analyzed": sections,
                "analysis_timestamp": datetime.now().isoformat(),
            }

        except KeyError as e:
            return {"error": f"Missing environment/config: {e}"}
        except Exception as e:
            return {"error": f"Enhanced SEC analysis failed: {e}"}

    def _fetch_latest_filing(self, ticker: str, form_type: str) -> dict[str, str] | None:
        """Fetch the latest SEC filing for the given ticker and form type."""
        api_key = os.environ.get("SEC_API_API_KEY")
        if not api_key:
            raise KeyError("SEC_API_API_KEY")

        # Lazy import to allow tests to patch QueryApi
        global QueryApi
        if QueryApi is None:
            try:
                from sec_api import QueryApi as _QueryApi
            except Exception as e:
                raise e
            QueryApi = _QueryApi

        query_api = QueryApi(api_key=api_key)
        query = {
            "query": {"query_string": {"query": f'ticker:{ticker} AND formType:"{form_type}"'}},
            "from": "0",
            "size": "1",
            "sort": [{"filedAt": {"order": "desc"}}],
        }

        filings = query_api.get_filings(query).get("filings", [])
        if not filings:
            return None

        filing = filings[0]
        return {
            "filing_url": filing.get("linkToFilingDetails", ""),
            "filed_at": filing.get("filedAt", ""),
        }

    def _download_html(self, url: str) -> str:
        """Download HTML content from SEC filing URL."""
        headers = {
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;q=0.9,"
                "image/avif,image/webp,image/apng,*/*;q=0.8,"
                "application/signed-exchange;v=b3;q=0.7"
            ),
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
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
            "Item 1": "business description, operations, products, services, competitive advantages",
            "Item 1A": "risk factors, business risks, market risks, operational risks",
            "Item 7": "management discussion analysis, financial performance, liquidity, capital resources",
            "Item 7A": "quantitative qualitative disclosures market risk, interest rate risk, foreign exchange risk",
            "Item 8": "financial statements, balance sheet, income statement, cash flow statement",
        }

        query = section_queries.get(section, f"information about {section}")

        # Use vector similarity search to find relevant content
        retriever = FAISS.from_documents(docs, OpenAIEmbeddings()).as_retriever()
        results = retriever.get_relevant_documents(query, k=3)

        insights = []
        for i, result in enumerate(results):
            if len(result.page_content.strip()) > 50:  # Filter out very short excerpts
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


class StandardizedRiskScoringInput(BaseModel):
    """Input schema for Standardized Risk Scoring Tool."""
    
    symbol: str = Field(..., description="The asset symbol (stock ticker, ETF, or crypto)")
    asset_class: str = Field(..., description="Type of asset being analyzed")
    risk_factors: list[str] = Field(default=[], description="List of identified risk factors")


class StandardizedRiskScoringTool(BaseTool):
    """
    Standalone tool for standardized risk scoring across asset classes.

    Provides consistent risk assessment methodology that can be used
    by any crew for standardized risk evaluation.
    """

    name: str = "Standardized Risk Scoring Tool"
    description: str = (
        "Calculate standardized risk scores (0-5 scale) with consistent methodology "
        "across different asset classes and analysis contexts."
    )
    args_schema: type[BaseModel] = StandardizedRiskScoringInput

    def _run(self, symbol: str, asset_class: str, risk_factors: list[str] = None, **kwargs) -> dict[str, Any]:
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
