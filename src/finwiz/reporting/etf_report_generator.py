"""
ETF Report Generator for ETF analysis HTML reports.

Generates HTML reports from ETFCrewExport data using Jinja2 templates.
"""

from datetime import datetime
from typing import Any

from finwiz.reporting.base_report_generator import BaseReportGenerator


class ETFReportGenerator(BaseReportGenerator):
    """
    Generate HTML reports for ETF analysis results.

    Uses the etf_report.html template to render professional
    reports from ETFCrewExport data.
    """

    def get_template_name(self) -> str:
        """Return the ETF report template path."""
        return "crew_reports/etf_report.html"

    def get_required_fields(self) -> list[str]:
        """Return required fields for ETF reports."""
        return ["ticker", "asset_class", "composite_score", "grade", "recommendation", "confidence", "rationale", "expense_ratio"]

    def prepare_template_variables(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Prepare variables for ETF report template rendering.

        Args:
            data: Input data dictionary (typically from ETFCrewExport.model_dump())

        Returns:
            Dictionary of template variables with defaults applied

        """
        template_vars = data.copy()

        # Apply shared defaults (analysis_date, session_id, data_sources, report paths).
        self._apply_common_defaults(template_vars)

        # Ensure asset_class is lowercase for template CSS classes
        template_vars["asset_class"] = template_vars.get("asset_class", "etf").lower()

        # Ensure ETF-specific fields have defaults
        template_vars.setdefault("expense_ratio", 0.0)
        template_vars.setdefault("tracking_error", None)
        template_vars.setdefault("factsheet", None)
        template_vars.setdefault("top_holdings", None)
        template_vars.setdefault("risk_assessment", None)

        return template_vars

    def _get_default_data_sources(self) -> list[str]:
        """Return default data sources for ETF analysis."""
        return [
            "Yahoo Finance API",
            "FinWiz Python Scoring Engine",
            "ETF.com",
            "Morningstar",
        ]

    def get_sample_data(self) -> dict[str, Any]:
        """Return sample data for template validation."""
        return {
            "ticker": "VOO",
            "asset_class": "etf",
            "composite_score": 0.85,
            "grade": "A",
            "recommendation": "BUY",
            "confidence": 0.90,
            "rationale": "Low-cost S&P 500 tracker with excellent tracking efficiency and high liquidity.",
            "session_id": "test-session",
            "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "expense_ratio": 0.0003,
            "tracking_error": 0.0012,
            "factsheet": {
                "fund_name": "Vanguard S&P 500 ETF",
                "inception_date": "2010-09-07",
                "aum": 350000000000,
                "benchmark": "S&P 500 Index",
                "category": "Large Cap Blend",
            },
            "top_holdings": [
                {"symbol": "AAPL", "name": "Apple Inc.", "weight": 0.072},
                {"symbol": "MSFT", "name": "Microsoft Corp.", "weight": 0.068},
                {"symbol": "AMZN", "name": "Amazon.com Inc.", "weight": 0.035},
                {"symbol": "NVDA", "name": "NVIDIA Corp.", "weight": 0.032},
                {"symbol": "GOOGL", "name": "Alphabet Inc.", "weight": 0.021},
            ],
            "risk_assessment": {
                "risk_score": 3,
                "systematic_risk": 1.0,
                "idiosyncratic_risk": 0.05,
                "risk_factors": ["Market risk", "Concentration in large caps"],
                "mitigation_strategies": ["Broad diversification", "Long-term holding"],
            },
            "data_sources": ["Yahoo Finance API", "ETF.com", "Morningstar"],
            "report_json_path": "/output/reports/test/etf_crew/VOO_export.json",
            "report_html_path": "/output/reports/test/etf_crew/VOO_report.html",
        }
