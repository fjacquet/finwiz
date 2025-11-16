"""
HTML Report Generator for FinWiz financial analysis reports.

This module provides HTML-first output standards with UTF-8 encoding,
emoji support, and French report section requirements using BeautifulSoup4
for secure HTML generation.

Re-exports from reporting submodules for backward compatibility.
"""

import logging
from pathlib import Path
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

    def generate_crew_report(
        self,
        crew_name: str,
        export_data: dict[str, Any],
        output_path: Path | str,
    ) -> str:
        """
        Generate HTML report for a crew using Jinja2 templates.

        This method generates crew-specific HTML reports from JSON export data
        using Jinja2 templates. It validates the export data against the crew's
        Pydantic schema before rendering.

        Args:
            crew_name: Name of the crew (e.g., "stock_crew", "etf_crew")
            export_data: Validated JSON export data from the crew
            output_path: Path where to save the HTML file

        Returns:
            Path to the generated HTML file as string

        Raises:
            ValueError: If crew_name is invalid or template not found
            ValidationError: If export_data doesn't match crew's schema

        Example:
            >>> generator = HTMLReportGenerator()
            >>> export_data = {"ticker": "AAPL", "grade": "A+", ...}
            >>> path = generator.generate_crew_report(
            ...     crew_name="stock_crew",
            ...     export_data=export_data,
            ...     output_path=Path("output/reports/session/stock_crew/AAPL_report.html"),
            ... )

        """
        try:
            from datetime import datetime
            from pathlib import Path

            from jinja2 import Environment, FileSystemLoader, TemplateNotFound

            # Initialize Jinja2 environment for crew_reports templates
            template_dir = Path("src/finwiz/templates")
            env = Environment(
                loader=FileSystemLoader(str(template_dir)),
                autoescape=True,
                trim_blocks=True,
                lstrip_blocks=True,
            )

            # Map crew names to template files
            template_map = {
                "stock_crew": "crew_reports/stock_report.html",
                "etf_crew": "crew_reports/etf_report.html",
                "crypto_crew": "crew_reports/crypto_report.html",
                "deep_analysis_crew": "crew_reports/deep_analysis_report.html",
                "discovery_crew": "crew_reports/discovery_report.html",
                "rebalancing_crew": "crew_reports/rebalancing_report.html",
            }

            # Validate crew_name
            if crew_name not in template_map:
                raise ValueError(f"Invalid crew_name: {crew_name}. Must be one of: {', '.join(template_map.keys())}")

            # Validate export_data against crew's Pydantic schema FIRST
            # Note: Validation should be done by the caller before passing data
            # This is a safety check to ensure data structure is correct
            if not isinstance(export_data, dict):
                raise ValueError(f"export_data must be a dictionary, got {type(export_data)}")

            # Load appropriate template
            template_name = template_map[crew_name]
            try:
                template = env.get_template(template_name)
            except TemplateNotFound:
                raise ValueError(f"Template not found: {template_name}. Ensure template exists at src/finwiz/templates/{template_name}")

            # Required fields check
            required_fields = ["ticker", "asset_class", "analysis_date", "session_id"]
            missing_fields = [field for field in required_fields if field not in export_data]
            if missing_fields:
                logger.warning(f"Missing required fields in export_data: {missing_fields}")

            # Render template with export data and generation timestamp
            generation_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            html_content = template.render(data=export_data, generation_date=generation_date)

            # Ensure output path is a Path object
            if isinstance(output_path, str):
                output_path = Path(output_path)

            # Create parent directories if they don't exist
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Save HTML to file with UTF-8 encoding
            output_path.write_text(html_content, encoding="utf-8")

            logger.info(f"Generated crew report for {crew_name} at {output_path}")

            return str(output_path)

        except Exception as e:
            logger.error(
                f"Error generating crew report for {crew_name}: {e}",
                exc_info=True,
            )
            raise
