"""
Discovery Report Generator for A+ investment opportunities HTML reports.

Generates HTML reports from discovery crew results using Jinja2 templates.
"""

from datetime import datetime
from typing import Any

from finwiz.reporting.base_report_generator import BaseReportGenerator


class DiscoveryReportGenerator(BaseReportGenerator):
    """
    Generate HTML reports for A+ investment discovery results.

    Uses the discovery_report.html template to render professional
    reports listing A+ rated investment opportunities.
    """

    def get_template_name(self) -> str:
        """Return the discovery report template path."""
        return "crew_reports/discovery_report.html"

    def get_required_fields(self) -> list[str]:
        """Return required fields for discovery reports."""
        return ["opportunities"]

    def prepare_template_variables(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Prepare variables for discovery report template rendering.

        Args:
            data: Input data dictionary containing discovery results

        Returns:
            Dictionary of template variables with defaults applied

        """
        template_vars = data.copy()

        # Ensure analysis_date is formatted
        if "analysis_date" not in template_vars or not template_vars["analysis_date"]:
            template_vars["analysis_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(template_vars["analysis_date"], datetime):
            template_vars["analysis_date"] = template_vars["analysis_date"].strftime("%Y-%m-%d %H:%M:%S")

        # Ensure session_id exists
        template_vars.setdefault("session_id", "default")

        # Ensure opportunities list exists
        template_vars.setdefault("opportunities", [])

        # Ensure optional fields have defaults
        template_vars.setdefault("screening_criteria", None)
        template_vars.setdefault("market_context", None)

        # Ensure data sources list exists
        if "data_sources" not in template_vars or not template_vars["data_sources"]:
            template_vars["data_sources"] = self._get_default_data_sources()

        # Ensure report paths exist
        template_vars.setdefault("report_json_path", "N/A")
        template_vars.setdefault("report_html_path", "N/A")

        return template_vars

    def _get_default_data_sources(self) -> list[str]:
        """Return default data sources for discovery analysis."""
        return [
            "Yahoo Finance API",
            "FinWiz Python Scoring Engine",
            "Market Screening Algorithms",
            "Fundamental Analysis",
        ]

    def get_sample_data(self) -> dict[str, Any]:
        """Return sample data for template validation."""
        return {
            "session_id": "test-session",
            "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "opportunities": [
                {
                    "ticker": "NVDA",
                    "name": "NVIDIA Corporation",
                    "asset_class": "stock",
                    "grade": "A+",
                    "composite_score": 0.92,
                    "rationale": "Market leader in AI accelerators with exceptional growth trajectory.",
                },
                {
                    "ticker": "COST",
                    "name": "Costco Wholesale",
                    "asset_class": "stock",
                    "grade": "A+",
                    "composite_score": 0.89,
                    "rationale": "Consistent revenue growth with strong membership model and defensive characteristics.",
                },
            ],
            "screening_criteria": {
                "min_grade": "A+",
                "min_score": 0.85,
                "asset_classes": ["stock", "etf"],
                "market_cap_min": 10000000000,
            },
            "market_context": "Current market conditions favor quality growth stocks with strong fundamentals.",
            "data_sources": ["Yahoo Finance API", "Market Screening", "Fundamental Analysis"],
            "report_json_path": "/output/reports/test/discovery_crew/discovery_export.json",
            "report_html_path": "/output/reports/test/discovery_crew/discovery_report.html",
        }
