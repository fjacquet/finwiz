"""
Rebalancing Report Generator for portfolio rebalancing HTML reports.

Generates HTML reports from rebalancing crew results using Jinja2 templates.
"""

from datetime import datetime
from typing import Any

from finwiz.reporting.base_report_generator import BaseReportGenerator


class RebalancingReportGenerator(BaseReportGenerator):
    """
    Generate HTML reports for portfolio rebalancing recommendations.

    Uses the rebalancing_report.html template to render professional
    reports with trade recommendations and allocation changes.
    """

    def get_template_name(self) -> str:
        """Return the rebalancing report template path."""
        return "crew_reports/rebalancing_report.html"

    def get_required_fields(self) -> list[str]:
        """Return required fields for rebalancing reports."""
        return [
            "holdings_analyzed",
            "deep_analyses_reviewed",
            "opportunities_discovered",
            "current_total_value",
            "current_allocation",
            "target_allocation",
            "expected_return",
            "expected_risk",
            "sharpe_ratio",
        ]

    def prepare_template_variables(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Prepare variables for rebalancing report template rendering.

        Args:
            data: Input data dictionary containing rebalancing results

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

        # Ensure portfolio metrics have defaults
        template_vars.setdefault("holdings_analyzed", 0)
        template_vars.setdefault("deep_analyses_reviewed", 0)
        template_vars.setdefault("opportunities_discovered", 0)
        template_vars.setdefault("current_total_value", 0.0)

        # Ensure allocation dicts exist
        template_vars.setdefault("current_allocation", {})
        template_vars.setdefault("target_allocation", {})

        # Ensure trades list exists
        template_vars.setdefault("trades_required", [])

        # Ensure performance metrics have defaults
        template_vars.setdefault("expected_return", 0.0)
        template_vars.setdefault("expected_risk", 0.0)
        template_vars.setdefault("sharpe_ratio", 0.0)

        # Ensure improvement analysis fields exist
        template_vars.setdefault("improvement_summary", None)
        template_vars.setdefault("risk_reduction", None)
        template_vars.setdefault("return_improvement", None)

        # Ensure data sources list exists
        if "data_sources" not in template_vars or not template_vars["data_sources"]:
            template_vars["data_sources"] = self._get_default_data_sources()

        # Ensure report paths exist
        template_vars.setdefault("report_json_path", "N/A")
        template_vars.setdefault("report_html_path", "N/A")

        return template_vars

    def _get_default_data_sources(self) -> list[str]:
        """Return default data sources for rebalancing analysis."""
        return [
            "Deep Analysis Results",
            "Portfolio Holdings Data",
            "A+ Discovery Results",
            "FinWiz Optimization Engine",
        ]

    def get_sample_data(self) -> dict[str, Any]:
        """Return sample data for template validation."""
        return {
            "session_id": "test-session",
            "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "holdings_analyzed": 15,
            "deep_analyses_reviewed": 15,
            "opportunities_discovered": 3,
            "current_total_value": 250000.00,
            "current_allocation": {
                "AAPL": 0.25,
                "MSFT": 0.20,
                "VOO": 0.30,
                "BND": 0.15,
                "CASH": 0.10,
            },
            "target_allocation": {
                "AAPL": 0.20,
                "MSFT": 0.20,
                "VOO": 0.35,
                "BND": 0.15,
                "NVDA": 0.05,
                "CASH": 0.05,
            },
            "trades_required": [
                {
                    "action": "SELL",
                    "ticker": "AAPL",
                    "asset_class": "stock",
                    "quantity": 50,
                    "rationale": "Reduce concentration to target allocation",
                },
                {
                    "action": "BUY",
                    "ticker": "VOO",
                    "asset_class": "etf",
                    "quantity": 25,
                    "rationale": "Increase broad market exposure",
                },
                {
                    "action": "BUY",
                    "ticker": "NVDA",
                    "asset_class": "stock",
                    "quantity": 10,
                    "rationale": "Add A+ rated opportunity to portfolio",
                },
            ],
            "expected_return": 0.12,
            "expected_risk": 0.15,
            "sharpe_ratio": 0.80,
            "improvement_summary": "Rebalancing improves diversification and adds exposure to high-conviction A+ opportunities.",
            "risk_reduction": 0.02,
            "return_improvement": 0.015,
            "data_sources": ["Deep Analysis", "Portfolio Data", "A+ Discovery"],
            "report_json_path": "/output/reports/test/rebalancing_crew/rebalancing_export.json",
            "report_html_path": "/output/reports/test/rebalancing_crew/rebalancing_report.html",
        }
