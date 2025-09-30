"""
Rebalancing Report Generator for FinWiz portfolio rebalancing reports.

This module extends the existing HTML report framework to generate comprehensive
rebalancing analysis reports with interactive elements and PDF export functionality.
"""

import logging
from pathlib import Path

from finwiz.schemas.portfolio_rebalancing import RebalancingResult
from finwiz.tools.html_report_generator import HTMLReportGenerator
from finwiz.tools.rebalancing_sections import RebalancingSections
from finwiz.tools.rebalancing_templates import RebalancingTemplates

logger = logging.getLogger(__name__)


class RebalancingReportGenerator(HTMLReportGenerator):
    """
    Generates comprehensive HTML reports for portfolio rebalancing analysis.

    Extends the existing HTMLReportGenerator with rebalancing-specific functionality
    including interactive trade execution elements and scenario comparison tables.
    """

    # Rebalancing-specific emoji mappings
    REBALANCING_EMOJI_MAP = {
        "rebalancing": "⚖️",
        "trade": "💱",
        "buy": "📈",
        "sell": "📉",
        "hold": "⏸️",
        "urgent": "�",
        "cost": "�",
        "improvement": "✅",
        "warning": "⚠️",
        "target": "🎯",
        "current": "📊",
        "projected": "🔮",
        "scenario": "🎭",
        "execution": "⚡",
    }

    def __init__(self, template_path: str | None = None) -> None:
        """Initialize the rebalancing report generator."""
        super().__init__(template_path)
        # Add rebalancing-specific emojis to the base emoji map
        self.EMOJI_MAP.update(self.REBALANCING_EMOJI_MAP)

        # Initialize helper classes
        self.section_generator = RebalancingSections()
        self.templates = RebalancingTemplates()

    def generate_rebalancing_report(
        self,
        result: RebalancingResult,
        title: str = "Portfolio Rebalancing Analysis",
        language: str = "en",
        include_interactive: bool = True,
    ) -> str:
        """
        Generate a comprehensive rebalancing report.

        Args:
            result: Rebalancing analysis result
            title: Report title
            language: Report language (en/fr)
            include_interactive: Whether to include interactive elements

        Returns:
            Complete HTML report as string

        """
        # Clear any existing sections
        self.clear_sections()

        # Add all report sections
        self._add_executive_summary(result, language)
        self._add_current_portfolio_section(result, language)
        self._add_trade_recommendations_section(result, language, include_interactive)
        self._add_projected_portfolio_section(result, language)
        self._add_cost_analysis_section(result, language)
        self._add_risk_analysis_section(result, language)

        if result.alternative_scenarios:
            self._add_alternative_scenarios_section(result, language)

        self._add_execution_summary_section(result, language)

        # Generate the HTML report
        html_content = self.generate_html(title, language)

        # Add interactive elements if requested
        if include_interactive:
            html_content = self.templates.add_interactive_elements(html_content)

        logger.info(f"Generated rebalancing report with {len(self.sections)} sections")
        return html_content

    def _add_executive_summary(self, result: RebalancingResult, language: str) -> None:
        """Add executive summary section."""
        is_french = language == "fr"
        title = "Résumé Exécutif" if is_french else "Executive Summary"
        content = self.section_generator.generate_executive_summary_content(result, language)
        self.add_section(title, content, "rebalancing", order=1)

    def _add_current_portfolio_section(self, result: RebalancingResult, language: str) -> None:
        """Add current portfolio analysis section."""
        is_french = language == "fr"
        title = "Analyse du Portefeuille Actuel" if is_french else "Current Portfolio Analysis"
        content = self.section_generator.generate_current_portfolio_content(result, language)
        self.add_section(title, content, "current", order=2)

    def _add_trade_recommendations_section(self, result: RebalancingResult, language: str, include_interactive: bool) -> None:
        """Add trade recommendations section."""
        is_french = language == "fr"
        title = "Recommandations de Trading" if is_french else "Trade Recommendations"
        content = self.section_generator.generate_trade_recommendations_content(result, language, include_interactive)
        self.add_section(title, content, "trade", order=3)

    def _add_projected_portfolio_section(self, result: RebalancingResult, language: str) -> None:
        """Add projected portfolio analysis section."""
        is_french = language == "fr"
        title = "Portefeuille Projeté Après Rééquilibrage" if is_french else "Projected Portfolio After Rebalancing"
        content = self.section_generator.generate_projected_portfolio_content(result, language)
        self.add_section(title, content, "projected", order=4)

    def _add_cost_analysis_section(self, result: RebalancingResult, language: str) -> None:
        """Add cost analysis section."""
        is_french = language == "fr"
        title = "Analyse des Coûts" if is_french else "Cost Analysis"
        content = self.section_generator.generate_cost_analysis_content(result, language)
        self.add_section(title, content, "cost", order=5)

    def _add_risk_analysis_section(self, result: RebalancingResult, language: str) -> None:
        """Add risk analysis section."""
        is_french = language == "fr"
        title = "Analyse des Risques" if is_french else "Risk Analysis"
        content = self.section_generator.generate_risk_analysis_content(result, language)
        self.add_section(title, content, "risk", order=6)

    def _add_alternative_scenarios_section(self, result: RebalancingResult, language: str) -> None:
        """Add alternative scenarios section."""
        is_french = language == "fr"
        title = "Scénarios Alternatifs" if is_french else "Alternative Scenarios"
        content = self.section_generator.generate_alternative_scenarios_content(result, language)
        self.add_section(title, content, "scenario", order=7)

    def _add_execution_summary_section(self, result: RebalancingResult, language: str) -> None:
        """Add execution summary section."""
        is_french = language == "fr"
        title = "Résumé d'Exécution" if is_french else "Execution Summary"
        content = self.section_generator.generate_execution_summary_content(result, language)
        self.add_section(title, content, "execution", order=8)

    def export_to_pdf(self, html_content: str, output_path: str) -> None:
        """
        Export HTML report to PDF format.

        Args:
            html_content: HTML content to convert
            output_path: Path where to save the PDF file

        Note:
            This delegates to the templates module for PDF preparation.

        """
        try:
            # Use templates module to prepare for PDF export
            html_with_note = self.templates.prepare_pdf_export(html_content)

            # Save HTML file that can be converted to PDF
            html_path = output_path.replace(".pdf", ".html") if output_path.endswith(".pdf") else f"{output_path}.html"

            output_file = Path(html_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(html_with_note, encoding="utf-8")

            logger.info(f"HTML report saved to {html_path} (ready for PDF conversion)")

        except Exception as e:
            logger.error(f"Error exporting to PDF: {e}")
            raise
