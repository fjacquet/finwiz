"""
SEC Citation Validation and Integration.

This module provides comprehensive SEC/EDGAR citation extraction, validation,
and consolidation for report integration.
"""

import logging
import re
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import urlparse

from pydantic import BaseModel, Field, HttpUrl
from pydantic import ValidationError as PydanticValidationError

from ..schemas.integration import SECCitation


class SECFilingInfo(BaseModel):
    """Information extracted from SEC filing URL."""

    ticker: str = Field(description="Stock ticker symbol")
    filing_type: str = Field(description="Type of filing (10-K, 10-Q, etc.)")
    filing_year: int | None = Field(default=None, description="Year of filing")
    cik: str | None = Field(default=None, description="Central Index Key")
    accession_number: str | None = Field(default=None, description="SEC accession number")


class SECCitationValidationResult(BaseModel):
    """Result of SEC citation validation."""

    is_valid: bool = Field(description="Whether the citation is valid")
    validation_timestamp: datetime = Field(description="When validation was performed")
    validation_errors: list[str] = Field(default_factory=list, description="List of validation errors")
    validation_warnings: list[str] = Field(default_factory=list, description="List of validation warnings")
    filing_info: SECFilingInfo | None = Field(default=None, description="Extracted filing information")
    url_accessible: bool | None = Field(default=None, description="Whether the URL is accessible (if checked)")


class ConsolidatedSECCitations(BaseModel):
    """Consolidated SEC citations for report integration."""

    citations_by_ticker: dict[str, list[SECCitation]] = Field(
        default_factory=dict, description="Citations organized by ticker symbol"
    )
    citations_by_filing_type: dict[str, list[SECCitation]] = Field(
        default_factory=dict, description="Citations organized by filing type"
    )
    unique_citations: list[SECCitation] = Field(default_factory=list, description="Deduplicated list of unique citations")
    validation_summary: dict[str, Any] = Field(default_factory=dict, description="Summary of validation results")
    consolidation_timestamp: datetime = Field(description="When consolidation was performed")


class SECCitationValidator:
    """
    Comprehensive SEC citation validator and consolidator.

    This class provides:
    - SEC/EDGAR citation extraction and validation
    - Filing date and URL verification logic
    - Citation consolidation for report integration
    - Duplicate detection and removal
    """

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """
        Initialize the SEC citation validator.

        Args:
            logger: Optional logger instance

        """
        self.logger = logger or self._setup_logging()

        # SEC URL patterns for validation
        self.sec_url_patterns = [
            r"https?://www\.sec\.gov/.*",
            r"https?://sec\.gov/.*",
            r"https?://www\.sec\.gov/Archives/edgar/.*",
            r"https?://sec\.gov/Archives/edgar/.*",
        ]

        # Filing type patterns
        self.filing_type_patterns = {
            "10-K": r"10-?K",
            "10-Q": r"10-?Q",
            "8-K": r"8-?K",
            "20-F": r"20-?F",
            "DEF 14A": r"DEF\s*14A",
            "S-1": r"S-?1",
        }

        # Citation format patterns
        self.citation_patterns = [
            r"(\d{1,2}-[KQ])\s*\((\d{4})\)",  # 10-K (2024)
            r"(\d{1,2}-[KQ])\s*\((\d{4})\),?\s*([^,]+)",  # 10-K (2024), Item 1A
            r"(\d{1,2}-[KQ])\s*\((\d{4})\),?\s*([^,]+),?\s*p\.\s*(\d+)",  # 10-K (2024), Item 1A, p. 17
        ]

        self.logger.info("SECCitationValidator initialized")

    def _setup_logging(self) -> logging.Logger:
        """Set up structured logging for SEC citation validation."""
        logger = logging.getLogger("finwiz.integration.sec_citation")

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)

        return logger

    def validate_sec_citation(self, citation: SECCitation, check_url_accessibility: bool = False) -> SECCitationValidationResult:
        """
        Validate a single SEC citation.

        Args:
            citation: SEC citation to validate
            check_url_accessibility: Whether to check if URL is accessible

        Returns:
            SECCitationValidationResult with validation details

        """
        self.logger.debug(f"Validating SEC citation for {citation.ticker}")

        result = SECCitationValidationResult(is_valid=True, validation_timestamp=datetime.now())

        try:
            # Validate ticker format
            if not self._validate_ticker_format(citation.ticker):
                result.validation_errors.append(f"Invalid ticker format: {citation.ticker}")
                result.is_valid = False

            # Validate filing URL
            url_validation = self._validate_filing_url(citation.filing_url)
            if not url_validation[0]:
                result.validation_errors.append(url_validation[1])
                result.is_valid = False
            else:
                result.filing_info = url_validation[2]

            # Validate filing date
            if not self._validate_filing_date(citation.filed_at):
                result.validation_errors.append(f"Invalid filing date: {citation.filed_at}")
                result.is_valid = False

            # Validate section format
            if not self._validate_section_format(citation.section):
                result.validation_warnings.append(f"Non-standard section format: {citation.section}")

            # Validate excerpt length and content
            if not self._validate_excerpt(citation.excerpt):
                result.validation_warnings.append("Excerpt is too short or appears incomplete")

            # Validate citation format
            if not self._validate_citation_format(citation.sec_citation):
                result.validation_warnings.append(f"Non-standard citation format: {citation.sec_citation}")

            # Check URL accessibility if requested
            if check_url_accessibility:
                result.url_accessible = self._check_url_accessibility(citation.filing_url)
                if not result.url_accessible:
                    result.validation_warnings.append("Filing URL may not be accessible")

            # Validate extraction timestamp
            if citation.extraction_timestamp > datetime.now():
                result.validation_errors.append("Extraction timestamp is in the future")
                result.is_valid = False

            self.logger.debug(
                f"SEC citation validation completed for {citation.ticker}",
                extra={
                    "is_valid": result.is_valid,
                    "error_count": len(result.validation_errors),
                    "warning_count": len(result.validation_warnings),
                },
            )

        except Exception as e:
            error_msg = f"SEC citation validation failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            result.validation_errors.append(error_msg)
            result.is_valid = False

        return result

    def validate_multiple_citations(
        self, citations: list[SECCitation], check_url_accessibility: bool = False
    ) -> dict[str, SECCitationValidationResult]:
        """
        Validate multiple SEC citations.

        Args:
            citations: List of SEC citations to validate
            check_url_accessibility: Whether to check URL accessibility

        Returns:
            Dictionary mapping citation identifiers to validation results

        """
        self.logger.info(f"Validating {len(citations)} SEC citations")

        results = {}

        for i, citation in enumerate(citations):
            try:
                citation_id = f"{citation.ticker}_{citation.section}_{i}"
                result = self.validate_sec_citation(citation, check_url_accessibility)
                results[citation_id] = result

            except Exception as e:
                error_msg = f"Failed to validate citation {i}: {str(e)}"
                self.logger.error(error_msg, exc_info=True)

                results[f"citation_{i}"] = SECCitationValidationResult(
                    is_valid=False, validation_timestamp=datetime.now(), validation_errors=[error_msg]
                )

        valid_count = sum(1 for r in results.values() if r.is_valid)
        self.logger.info(
            "SEC citation validation completed",
            extra={
                "total_citations": len(citations),
                "valid_citations": valid_count,
                "invalid_citations": len(citations) - valid_count,
            },
        )

        return results

    def consolidate_citations_for_report(
        self, crew_citations: dict[str, list[SECCitation]], deduplicate: bool = True
    ) -> ConsolidatedSECCitations:
        """
        Consolidate SEC citations from multiple crews for report integration.

        Args:
            crew_citations: Dictionary mapping crew names to their citations
            deduplicate: Whether to remove duplicate citations

        Returns:
            ConsolidatedSECCitations with organized and deduplicated citations

        """
        self.logger.info(
            "Consolidating SEC citations for report integration",
            extra={
                "crew_count": len(crew_citations),
                "total_citations": sum(len(citations) for citations in crew_citations.values()),
            },
        )

        consolidated = ConsolidatedSECCitations(consolidation_timestamp=datetime.now())

        try:
            # Collect all citations
            all_citations = []
            for crew_name, citations in crew_citations.items():
                all_citations.extend(citations)

            # Validate all citations
            validation_results = self.validate_multiple_citations(all_citations)

            # Filter valid citations
            valid_citations = []
            for i, citation in enumerate(all_citations):
                citation_id = f"{citation.ticker}_{citation.section}_{i}"
                if citation_id in validation_results and validation_results[citation_id].is_valid:
                    valid_citations.append(citation)

            # Deduplicate if requested
            if deduplicate:
                valid_citations = self._deduplicate_citations(valid_citations)

            consolidated.unique_citations = valid_citations

            # Organize by ticker
            for citation in valid_citations:
                ticker = citation.ticker.upper()
                if ticker not in consolidated.citations_by_ticker:
                    consolidated.citations_by_ticker[ticker] = []
                consolidated.citations_by_ticker[ticker].append(citation)

            # Organize by filing type
            for citation in valid_citations:
                filing_type = self._extract_filing_type(citation.sec_citation)
                if filing_type not in consolidated.citations_by_filing_type:
                    consolidated.citations_by_filing_type[filing_type] = []
                consolidated.citations_by_filing_type[filing_type].append(citation)

            # Create validation summary
            consolidated.validation_summary = {
                "total_citations_processed": len(all_citations),
                "valid_citations": len(valid_citations),
                "invalid_citations": len(all_citations) - len(valid_citations),
                "unique_tickers": len(consolidated.citations_by_ticker),
                "unique_filing_types": len(consolidated.citations_by_filing_type),
                "deduplication_applied": deduplicate,
                "validation_results": {
                    citation_id: {
                        "is_valid": result.is_valid,
                        "error_count": len(result.validation_errors),
                        "warning_count": len(result.validation_warnings),
                    }
                    for citation_id, result in validation_results.items()
                },
            }

            self.logger.info(
                "SEC citation consolidation completed",
                extra={
                    "valid_citations": len(valid_citations),
                    "unique_tickers": len(consolidated.citations_by_ticker),
                    "unique_filing_types": len(consolidated.citations_by_filing_type),
                },
            )

        except Exception as e:
            error_msg = f"SEC citation consolidation failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            consolidated.validation_summary = {"error": error_msg, "total_citations_processed": 0, "valid_citations": 0}

        return consolidated

    def extract_citations_from_crew_outputs(self, crew_outputs: dict[str, dict[str, Any]]) -> dict[str, list[SECCitation]]:
        """
        Extract SEC citations from crew outputs.

        Args:
            crew_outputs: Dictionary mapping crew names to their output data

        Returns:
            Dictionary mapping crew names to their SEC citations

        """
        self.logger.info("Extracting SEC citations from crew outputs", extra={"crew_count": len(crew_outputs)})

        crew_citations = {}

        for crew_name, output in crew_outputs.items():
            try:
                citations = []

                # Extract citations based on crew type and output structure
                if "sec_citations" in output:
                    # Direct SEC citations field
                    raw_citations = output["sec_citations"]
                    for raw_citation in raw_citations:
                        try:
                            citation = SECCitation.model_validate(raw_citation)
                            citations.append(citation)
                        except PydanticValidationError as e:
                            self.logger.warning(f"Invalid SEC citation in {crew_name} output: {str(e)}")

                elif "ten_k_insights" in output:
                    # Extract from 10-K insights (stock crew)
                    insights = output["ten_k_insights"]
                    citations.extend(self._extract_citations_from_insights(insights))

                # Look for citations in other fields
                citations.extend(self._extract_citations_from_text_fields(output))

                if citations:
                    crew_citations[crew_name] = citations
                    self.logger.debug(f"Extracted {len(citations)} citations from {crew_name} crew")

            except Exception as e:
                self.logger.error(f"Failed to extract citations from {crew_name} crew: {str(e)}", exc_info=True)

        total_citations = sum(len(citations) for citations in crew_citations.values())
        self.logger.info(
            "SEC citation extraction completed",
            extra={"total_citations": total_citations, "crews_with_citations": len(crew_citations)},
        )

        return crew_citations

    def _validate_ticker_format(self, ticker: str) -> bool:
        """Validate ticker symbol format."""
        if not ticker or not isinstance(ticker, str):
            return False

        # Basic ticker validation - 1-10 alphanumeric characters
        return bool(re.match(r"^[A-Z0-9]{1,10}$", ticker.upper()))

    def _validate_filing_url(self, url: HttpUrl) -> tuple[bool, str, SECFilingInfo | None]:
        """
        Validate SEC filing URL format and extract information.

        Returns:
            Tuple of (is_valid, error_message, filing_info)

        """
        try:
            url_str = str(url)

            # Check if URL matches SEC patterns
            is_sec_url = any(re.match(pattern, url_str, re.IGNORECASE) for pattern in self.sec_url_patterns)

            if not is_sec_url:
                return False, f"URL does not appear to be a valid SEC URL: {url_str}", None

            # Try to extract filing information from URL
            filing_info = self._extract_filing_info_from_url(url_str)

            return True, "", filing_info

        except Exception as e:
            return False, f"URL validation failed: {str(e)}", None

    def _validate_filing_date(self, filed_at: datetime) -> bool:
        """Validate filing date is reasonable."""
        if not isinstance(filed_at, datetime):
            return False

        # Filing date should be in the past but not too old (e.g., not before 1990)
        min_date = datetime(1990, 1, 1)
        max_date = datetime.now() + timedelta(days=1)  # Allow slight future dates for timezone issues

        return min_date <= filed_at <= max_date

    def _validate_section_format(self, section: str) -> bool:
        """Validate section format (e.g., 'Item 1A', 'Part I')."""
        if not section or not isinstance(section, str):
            return False

        # Common section patterns
        section_patterns = [
            r"Item\s+\d+[A-Z]?",  # Item 1A, Item 2, etc.
            r"Part\s+[IVX]+",  # Part I, Part II, etc.
            r"Section\s+\d+",  # Section 1, Section 2, etc.
            r"Business\s*Overview",
            r"MD&A",
            r"Risk\s*Factors",
            r"Liquidity",
            r"Segments?",
        ]

        return any(re.search(pattern, section, re.IGNORECASE) for pattern in section_patterns)

    def _validate_excerpt(self, excerpt: str) -> bool:
        """Validate excerpt content and length."""
        if not excerpt or not isinstance(excerpt, str):
            return False

        # Excerpt should be at least 20 characters and contain meaningful content
        if len(excerpt.strip()) < 20:
            return False

        # Should contain some alphabetic characters (not just numbers/symbols)
        if not re.search(r"[a-zA-Z]", excerpt):
            return False

        return True

    def _validate_citation_format(self, citation: str) -> bool:
        """Validate SEC citation format."""
        if not citation or not isinstance(citation, str):
            return False

        # Check against known citation patterns
        return any(re.search(pattern, citation, re.IGNORECASE) for pattern in self.citation_patterns)

    def _check_url_accessibility(self, url: HttpUrl) -> bool:
        """
        Check if URL is accessible (mock implementation).

        In a real implementation, this would make an HTTP request.
        For testing purposes, we'll just return True.
        """
        # Mock implementation - in reality would check HTTP status
        return True

    def _extract_filing_info_from_url(self, url: str) -> SECFilingInfo | None:
        """Extract filing information from SEC URL."""
        try:
            # Parse URL components
            parsed = urlparse(url)
            path_parts = parsed.path.split("/")

            # Look for common SEC URL patterns
            filing_info = SECFilingInfo(ticker="", filing_type="")

            # Try to extract CIK and accession number from URL
            for part in path_parts:
                if re.match(r"^\d{10}-\d{2}-\d{6}$", part):  # Accession number pattern
                    filing_info.accession_number = part
                elif re.match(r"^\d{10}$", part):  # CIK pattern
                    filing_info.cik = part

            # Try to extract filing type from filename
            if path_parts:
                filename = path_parts[-1]
                for filing_type, pattern in self.filing_type_patterns.items():
                    if re.search(pattern, filename, re.IGNORECASE):
                        filing_info.filing_type = filing_type
                        break

            return filing_info if filing_info.filing_type else None

        except Exception:
            return None

    def _extract_filing_type(self, citation: str) -> str:
        """Extract filing type from citation string."""
        for filing_type, pattern in self.filing_type_patterns.items():
            if re.search(pattern, citation, re.IGNORECASE):
                return filing_type

        return "Unknown"

    def _deduplicate_citations(self, citations: list[SECCitation]) -> list[SECCitation]:
        """Remove duplicate citations based on ticker, URL, and section."""
        seen = set()
        unique_citations = []

        for citation in citations:
            # Create a unique key based on ticker, URL, and section
            key = (citation.ticker.upper(), str(citation.filing_url).lower(), citation.section.lower().strip())

            if key not in seen:
                seen.add(key)
                unique_citations.append(citation)

        self.logger.debug(f"Deduplication: {len(citations)} -> {len(unique_citations)} citations")
        return unique_citations

    def _extract_citations_from_insights(self, insights: list[dict[str, Any]]) -> list[SECCitation]:
        """Extract SEC citations from 10-K insights."""
        citations = []

        for insight in insights:
            try:
                # Look for SEC-related fields in insights
                if all(field in insight for field in ["ticker", "filing_url", "section"]):
                    citation_data = {
                        "ticker": insight["ticker"],
                        "filing_url": insight["filing_url"],
                        "filed_at": insight.get("filed_at", datetime.now().isoformat()),
                        "section": insight["section"],
                        "excerpt": insight.get("insight", insight.get("content", "")),
                        "sec_citation": f"10-K, {insight['section']}",
                        "extraction_timestamp": datetime.now().isoformat(),
                        "validation_status": {
                            "is_valid": True,
                            "validation_timestamp": datetime.now().isoformat(),
                            "validation_errors": [],
                            "validation_warnings": [],
                            "schema_version": 1,
                        },
                    }

                    citation = SECCitation.model_validate(citation_data)
                    citations.append(citation)

            except Exception as e:
                self.logger.warning(f"Failed to extract citation from insight: {str(e)}")

        return citations

    def _extract_citations_from_text_fields(self, output: dict[str, Any]) -> list[SECCitation]:
        """Extract citations from text fields in output."""
        citations = []

        # This is a simplified implementation
        # In practice, would use NLP to extract citations from text

        return citations
