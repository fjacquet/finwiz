"""
Utility Orchestrator for FinWiz Flow.

This module provides utility functions for data processing including:
- Crew output parsing for holdings
- Grade distribution calculation
- SEC filing URL extraction and validation
"""

import re
from datetime import datetime
from typing import Any

from finwiz.cache.analysis_cache_manager import CrewAnalysisResult
from finwiz.flow_state import FinwizState
from finwiz.tools.logger import get_logger
from finwiz.tools.sec_filing_url_generator import SECFilingURLGenerator
from finwiz.utils.grading_system import score_to_grade
from finwiz.utils.url_validator import get_url_validator


class UtilityOrchestrator:
    """Utility functions for data processing."""

    def __init__(self, state: FinwizState, **dependencies: Any) -> None:
        """
        Initialize the UtilityOrchestrator.

        Args:
            state: FinwizState instance for accessing workflow state
            **dependencies: Additional dependencies (not currently used)

        """
        self.state = state
        self.logger = get_logger(self.__class__.__name__)
        self.dependencies = dependencies

    def parse_crew_output_for_holding(
        self,
        crew_result: Any,
        ticker: str,
        asset_class: str,
        crew_name: str,
    ) -> CrewAnalysisResult:
        """
        Parse crew output and extract scores for holding analysis.

        Args:
            crew_result: Result from crew.kickoff() execution
            ticker: Stock/ETF/crypto ticker symbol
            asset_class: Asset class (stock, etf, crypto)
            crew_name: Name of crew that performed analysis

        Returns:
            CrewAnalysisResult object with extracted scores and grade

        Requirements: 9.1

        """
        try:
            # Extract scores from pydantic or raw output
            fundamental_score, technical_score, risk_score, composite_score = self._extract_scores(crew_result)

            # Ensure composite_score is valid
            if composite_score is None:
                raise ValueError(f"Failed to calculate composite_score for {ticker}")
            composite_score = max(0.0, min(1.0, composite_score))

            # Calculate letter grade
            grade_info = score_to_grade(composite_score)

            self.logger.info(f"Parsed {ticker}: composite={composite_score:.3f}, grade={grade_info.grade}, fund={fundamental_score}, tech={technical_score}, risk={risk_score}")

            return CrewAnalysisResult(
                ticker=ticker,
                asset_class=asset_class,
                crew_name=crew_name,
                analyzed_at=datetime.now(),
                fundamental_score=fundamental_score,
                technical_score=technical_score,
                risk_score=risk_score,
                composite_score=composite_score,
                grade=grade_info.grade,
                metrics={
                    "grade_description": grade_info.description,
                    "recommended_action": grade_info.action,
                    "grade_emoji": grade_info.emoji,
                },
                raw_output={"crew_result": str(crew_result)[:500]},
            )

        except Exception as e:
            self.logger.error(f"Failed to parse crew output for {ticker}: {e}", exc_info=True)
            raise ValueError(f"Failed to parse crew output for {ticker}") from e

    def _extract_scores(self, crew_result: Any) -> tuple[float | None, float | None, float | None, float | None]:
        """Extract scores from crew result."""
        if hasattr(crew_result, "pydantic") and crew_result.pydantic:
            return self._extract_from_pydantic(crew_result.pydantic)
        elif hasattr(crew_result, "raw") and crew_result.raw:
            return self._extract_from_raw(str(crew_result.raw))
        return None, None, None, None

    def _extract_from_pydantic(self, data: Any) -> tuple[float | None, float | None, float | None, float | None]:
        """Extract scores from pydantic data."""
        fund = float(data.fundamental_score) if hasattr(data, "fundamental_score") else None
        tech = float(data.technical_score) if hasattr(data, "technical_score") else None
        risk = None
        if hasattr(data, "risk_score"):
            raw_risk = float(data.risk_score)
            risk = raw_risk / 5.0 if raw_risk > 1.0 else raw_risk
        comp = float(data.composite_score) if hasattr(data, "composite_score") else self._calculate_composite(fund, tech, risk)
        return fund, tech, risk, comp

    def _extract_from_raw(self, raw_text: str) -> tuple[float | None, float | None, float | None, float | None]:
        """Extract scores from raw text."""
        raw_text = raw_text.lower()
        fund = self._extract_score(raw_text, r"fundamental[_\s]+score[:\s]+([0-9.]+)")
        tech = self._extract_score(raw_text, r"technical[_\s]+score[:\s]+([0-9.]+)")
        risk_raw = self._extract_score(raw_text, r"risk[_\s]+score[:\s]+([0-9.]+)")
        risk = risk_raw / 5.0 if risk_raw and risk_raw > 1.0 else risk_raw
        comp = self._calculate_composite(fund, tech, risk)
        return fund, tech, risk, comp

    def _extract_score(self, text: str, pattern: str) -> float | None:
        """Extract single score from text using regex pattern."""
        match = re.search(pattern, text)
        return float(match.group(1)) if match else None

    def _calculate_composite(self, fund: float | None, tech: float | None, risk: float | None) -> float | None:
        """Calculate composite score with risk penalty."""
        scores = [s for s in [fund, tech] if s is not None]
        if not scores:
            return None
        composite = sum(scores) / len(scores)
        return composite * (1.0 - risk * 0.10) if risk else composite

    def calculate_grade_distribution(
        self,
        holdings: list[dict[str, Any]],
    ) -> dict[str, int]:
        """
        Calculate grade distribution across holdings.

        Aggregates grades from holdings to provide a distribution summary.
        Handles both dict-based holdings and objects with grade attributes.

        Args:
            holdings: List of holdings with grade information

        Returns:
            Dictionary with grade counts (e.g., {"A+": 10, "A": 5, "B": 3, ...})

        Requirements: 9.2

        """
        grade_counts: dict[str, int] = {}

        for holding in holdings:
            # Extract grade from holding (supports both dict and object)
            if isinstance(holding, dict):
                grade = holding.get("grade", "N/A")
            elif hasattr(holding, "grade"):
                grade = holding.grade
            else:
                grade = "N/A"

            # Increment count for this grade
            grade_counts[grade] = grade_counts.get(grade, 0) + 1

        return grade_counts

    def extract_sec_filing_urls(
        self,
        crew_output: Any,
    ) -> dict[str, dict[str, str]]:
        """
        Extract SEC filing URLs from crew output.

        Args:
            crew_output: Crew execution output or state containing analysis results

        Returns:
            Dictionary mapping ticker to filing URLs

        Requirements: 9.3

        """
        sec_filing_urls = {}
        url_generator = SECFilingURLGenerator()
        url_validator = get_url_validator()

        try:
            # Extract from deep_analysis_results
            sec_filing_urls.update(self._extract_from_deep_analysis(url_generator, url_validator))

            # Extract from stock_analysis_result
            sec_filing_urls.update(self._extract_from_stock_analysis(sec_filing_urls, url_generator, url_validator))

            self.logger.info(f"Extracted SEC filing URLs for {len(sec_filing_urls)} stock holdings" if sec_filing_urls else "No SEC filing URLs found")
            return sec_filing_urls

        except Exception as e:
            self.logger.warning(f"Failed to extract SEC filing URLs: {e}", exc_info=True)
            return {}

    def _extract_from_deep_analysis(
        self,
        url_generator: SECFilingURLGenerator,
        url_validator: Any,
    ) -> dict[str, dict[str, str]]:
        """Extract SEC URLs from deep analysis results."""
        sec_urls = {}
        if hasattr(self.state, "deep_analysis_results") and self.state.deep_analysis_results:
            for ticker, analysis in self.state.deep_analysis_results.items():
                if isinstance(analysis, dict) and analysis.get("asset_class", "").lower() == "stock":
                    sec_data = analysis.get("sec_filing_urls") or analysis.get("sec_filings")
                    if sec_data and isinstance(sec_data, dict):
                        validated = self.validate_and_fix_sec_urls(sec_data, ticker, url_generator, url_validator)
                        if validated:
                            sec_urls[ticker] = validated
        return sec_urls

    def _extract_from_stock_analysis(
        self,
        existing_urls: dict[str, dict[str, str]],
        url_generator: SECFilingURLGenerator,
        url_validator: Any,
    ) -> dict[str, dict[str, str]]:
        """Extract SEC URLs from stock analysis result."""
        sec_urls = {}
        if hasattr(self.state, "stock_analysis_result") and self.state.stock_analysis_result:
            stock_result = self.state.stock_analysis_result
            if isinstance(stock_result, dict):
                sec_data = stock_result.get("sec_filing_urls") or stock_result.get("sec_filings")
                if sec_data and isinstance(sec_data, dict):
                    for ticker, urls in sec_data.items():
                        if ticker not in existing_urls:
                            validated = self.validate_and_fix_sec_urls(urls, ticker, url_generator, url_validator)
                            if validated:
                                sec_urls[ticker] = validated
        return sec_urls

    def validate_and_fix_sec_urls(
        self,
        urls: dict[str, str],
        ticker: str,
        url_generator: SECFilingURLGenerator | None = None,
        url_validator: Any | None = None,
    ) -> dict[str, str]:
        """
        Validate SEC URLs and regenerate them if invalid.

        Args:
            urls: Dictionary of filing type to URL
            ticker: Stock ticker symbol
            url_generator: Optional SECFilingURLGenerator instance
            url_validator: Optional URL validator instance

        Returns:
            Dictionary of validated/fixed URLs

        Requirements: 9.4

        """
        if url_generator is None:
            url_generator = SECFilingURLGenerator()
        if url_validator is None:
            url_validator = get_url_validator()

        validated_urls = {}

        for filing_type, url in urls.items():
            # Generate URL if missing or invalid
            if not url or not isinstance(url, str) or not url_validator.is_valid_url(url, f"SEC {ticker} {filing_type}"):
                metadata = url_generator.get_filing_metadata(ticker, filing_type)
                if metadata and metadata.get("filing_url"):
                    validated_urls[filing_type] = metadata["filing_url"]
                    self.logger.info(f"{'Generated' if not url else 'Regenerated'} SEC URL for {ticker} {filing_type}")
            else:
                validated_urls[filing_type] = url

        return validated_urls
