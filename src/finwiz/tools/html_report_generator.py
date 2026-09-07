"""
HTML Report Generator for FinWiz financial analysis reports.

This module provides HTML-first output standards with UTF-8 encoding,
emoji support, and French report section requirements using BeautifulSoup4
for secure HTML generation.

Re-exports from reporting submodules for backward compatibility.
"""

import logging
from typing import Any

from finwiz.tools.reporting.report_formatters import HTMLReportFormatter
from finwiz.tools.reporting.report_sections import (
    ReportSectionBuilder,
)

logger = logging.getLogger(__name__)


class HTMLReportGenerator:
    """
    Generates HTML reports with UTF-8 encoding and emoji support.

    Implements FinWiz HTML-first output standards including French report
    section requirements (Synthèse 10-K, Sentiment du Marché).

    This class orchestrates report generation by delegating to specialized
    components: ReportSectionBuilder for building sections and HTMLReportFormatter
    for formatting and rendering HTML.
    """

    def __init__(self, template_path: str | None = None) -> None:
        """
        Initialize the HTML report generator.

        Args:
            template_path: Optional path to custom HTML template

        """
        self.template_path = template_path or "src/finwiz/templates/html_template.html"
        self.unified_template_path = "src/finwiz/templates/unified_portfolio_report.html"
        self.section_builder = ReportSectionBuilder()
        self.formatter = HTMLReportFormatter(template_path)

    def add_section(self, title: str, content: str, emoji_key: str | None = None, order: int = 0) -> None:
        """
        Add a section to the report.

        Args:
            title: Section title
            content: Section content in HTML format
            emoji_key: Key for emoji from EMOJI_MAP
            order: Display order (lower numbers appear first)

        """
        self.section_builder.add_section(title, content, emoji_key, order)

    def add_french_section(self, section_key: str, content: str) -> None:
        """
        Add a required French section to the report.

        Args:
            section_key: Key from FRENCH_SECTIONS
            content: Section content in HTML format

        Raises:
            ValueError: If section_key is not a valid French section

        """
        self.section_builder.add_french_section(section_key, content)

    def add_rebalancing_section(self, title: str, content: str, order: int = 0) -> None:
        """
        Add a rebalancing-specific section to the report.

        Args:
            title: Section title
            content: Section content in HTML format
            order: Display order

        """
        self.section_builder.add_rebalancing_section(title, content, order)

    def add_portfolio_overview_section(self, portfolio_data: dict[str, Any]) -> None:
        """
        Add portfolio overview section with key metrics.

        Args:
            portfolio_data: Portfolio analysis data

        """
        self.section_builder.add_portfolio_overview_section(portfolio_data)

    def add_rebalancing_summary_section(self, rebalancing_data: dict[str, Any]) -> None:
        """
        Add rebalancing summary section.

        Args:
            rebalancing_data: Rebalancing analysis data

        """
        self.section_builder.add_rebalancing_summary_section(rebalancing_data)

    def add_trade_recommendations_section(self, trades: list[dict[str, Any]]) -> None:
        """
        Add trade recommendations section.

        Args:
            trades: List of trade recommendations

        """
        self.section_builder.add_trade_recommendations_section(trades)

    def clear_sections(self) -> None:
        """Clear all sections from the report."""
        self.section_builder.clear_sections()
        logger.debug("Cleared all report sections")

    def generate_html(self, title: str = "FinWiz Financial Report", language: str = "en") -> str:
        """
        Generate the complete HTML report using BeautifulSoup4.

        Args:
            title: Report title
            language: Report language (en/fr)

        Returns:
            Complete HTML report as string

        """
        sections = self.section_builder.get_sorted_sections()
        return self.formatter.generate_html(title, sections, language)

    def validate_html_output(self, html_content: str) -> dict[str, Any]:
        """
        Validate HTML output for compliance with FinWiz standards.

        Args:
            html_content: HTML content to validate

        Returns:
            Validation result with compliance status and issues

        """
        return self.formatter.validate_html_output(html_content)

    def save_report(self, html_content: str, file_path: str) -> None:
        """
        Save HTML report to file with proper UTF-8 encoding.

        Args:
            html_content: HTML content to save
            file_path: Path where to save the file

        """
        self.formatter.save_report(html_content, file_path)

    def generate_unified_html(self, title: str, language: str = "en") -> str:
        """
        Generate unified HTML report using the unified template.

        Args:
            title: Report title
            language: Report language

        Returns:
            Complete HTML report

        """
        sections = self.section_builder.get_sorted_sections()
        return self.formatter.generate_unified_html(title, sections, language)

    def generate_html_fallback(self, title: str, language: str = "en") -> str:
        """
        Generate HTML report using fallback template with BeautifulSoup4.

        Args:
            title: Report title
            language: Report language

        Returns:
            Complete HTML report

        """
        sections = self.section_builder.get_sorted_sections()
        return self.formatter.generate_html_fallback(title, sections, language)
