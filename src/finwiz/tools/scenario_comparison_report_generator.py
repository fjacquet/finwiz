"""
Scenario comparison report generator for portfolio rebalancing.

This module generates comprehensive HTML reports comparing different
rebalancing scenarios with side-by-side analysis and visualizations.
Delegates to specialized modules for section building and rendering.
"""

from __future__ import annotations

import logging
from datetime import datetime

from finwiz.quantitative.scenario_analysis import ScenarioAnalysisReport
from finwiz.tools.html_report_generator import HTMLReportGenerator
from finwiz.tools.scenario_report_renderer import render_scenario_report_template
from finwiz.tools.scenario_report_sections import (
    create_comparison_tables,
    create_monte_carlo_summary,
    create_recommendations_section,
    create_sensitivity_charts,
    create_summary_sections,
    extract_key_findings,
    extract_priority_actions,
    format_optimal_parameters,
)

logger = logging.getLogger(__name__)


class ScenarioComparisonReportGenerator(HTMLReportGenerator):
    """
    Generator for scenario comparison reports.

    Creates comprehensive HTML reports with side-by-side scenario comparisons,
    sensitivity analysis charts, Monte Carlo results, and implementation recommendations.
    """

    def __init__(self) -> None:
        """Initialize the scenario comparison report generator."""
        super().__init__()
        self.logger = logging.getLogger(__name__)

    def generate_scenario_comparison_report(self, scenario_report: ScenarioAnalysisReport, title: str = "Portfolio Rebalancing Scenario Analysis") -> str:
        """
        Generate comprehensive scenario comparison HTML report.

        Args:
            scenario_report: Complete scenario analysis results
            title: Report title

        Returns:
            HTML report string

        """
        self.logger.info("Generating scenario comparison report")

        # Prepare template data using section builders
        template_data = {
            "title": title,
            "report": scenario_report,
            "timestamp": datetime.now(),
            "base_currency": "USD",
            "summary_sections": create_summary_sections(scenario_report, extract_key_findings),
            "comparison_tables": create_comparison_tables(scenario_report),
            "sensitivity_charts": create_sensitivity_charts(scenario_report),
            "monte_carlo_summary": create_monte_carlo_summary(scenario_report),
            "recommendations": create_recommendations_section(scenario_report, format_optimal_parameters, extract_priority_actions),
        }

        # Generate HTML content using dedicated renderer
        html_content = render_scenario_report_template(template_data)

        self.logger.info("Scenario comparison report generated successfully")
        return html_content

    def export_scenario_report_to_html_file(
        self,
        scenario_report: ScenarioAnalysisReport,
        output_path: str,
        title: str = "Portfolio Rebalancing Scenario Analysis",
    ) -> str:
        """
        Export scenario comparison report to HTML file.

        Args:
            scenario_report: Complete scenario analysis results
            output_path: Path for HTML output
            title: Report title

        Returns:
            Path to generated HTML file

        """
        html_content = self.generate_scenario_comparison_report(scenario_report, title)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        self.logger.info(f"Scenario report exported to {output_path}")
        return output_path
