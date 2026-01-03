"""
Utility Orchestrator for FinWiz Flow.

This module provides utility functions for SEC filing URL extraction and validation.
"""

from typing import Any

from finwiz.flow_state import FinwizState
from finwiz.tools.logger import get_logger
from finwiz.tools.sec_filing_url_generator import SECFilingURLGenerator
from finwiz.validation.url import get_url_validator


class UtilityOrchestrator:
    """Utility functions for SEC filing URL extraction."""

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

        """
        sec_filing_urls: dict[str, dict[str, str]] = {}
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
        sec_urls: dict[str, dict[str, str]] = {}
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
        sec_urls: dict[str, dict[str, str]] = {}
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

        """
        if url_generator is None:
            url_generator = SECFilingURLGenerator()
        if url_validator is None:
            url_validator = get_url_validator()

        validated_urls: dict[str, str] = {}

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
