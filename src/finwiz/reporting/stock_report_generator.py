"""
Stock Report Generator for stock analysis HTML reports.

Generates HTML reports from StockCrewExport data using Jinja2 templates.
"""

from datetime import datetime
from typing import Any

from finwiz.reporting.base_report_generator import BaseReportGenerator


class StockReportGenerator(BaseReportGenerator):
    """
    Generate HTML reports for stock analysis results.

    Uses the stock_report.html template to render professional
    reports from StockCrewExport data.
    """

    def get_template_name(self) -> str:
        """Return the stock report template path."""
        return "crew_reports/stock_report.html"

    def get_required_fields(self) -> list[str]:
        """Return required fields for stock reports."""
        return ["ticker", "asset_class", "composite_score", "grade", "recommendation", "confidence", "rationale"]

    def prepare_template_variables(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Prepare variables for stock report template rendering.

        Args:
            data: Input data dictionary (typically from StockCrewExport.model_dump())

        Returns:
            Dictionary of template variables with defaults applied

        """
        template_vars = data.copy()

        # Apply shared defaults (analysis_date, session_id, data_sources, report paths).
        self._apply_common_defaults(template_vars)

        # Ensure asset_class is lowercase for template CSS classes
        template_vars["asset_class"] = template_vars.get("asset_class", "stock").lower()

        # Ensure optional sections have defaults
        template_vars.setdefault("fundamental_analysis", None)
        template_vars.setdefault("technical_indicators", None)
        template_vars.setdefault("risk_assessment", None)

        return template_vars

    def _get_default_data_sources(self) -> list[str]:
        """Return default data sources for stock analysis."""
        return [
            "Yahoo Finance API",
            "FinWiz Python Scoring Engine",
            "SEC EDGAR Database",
            "Alpha Vantage API",
        ]

    def get_sample_data(self) -> dict[str, Any]:
        """Return sample data for template validation."""
        return {
            "ticker": "AAPL",
            "asset_class": "stock",
            "composite_score": 0.82,
            "grade": "A",
            "recommendation": "BUY",
            "confidence": 0.88,
            "rationale": "Strong fundamentals with consistent revenue growth and market leadership in technology sector.",
            "session_id": "test-session",
            "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "fundamental_analysis": {
                "company_name": "Apple Inc.",
                "sector": "Technology",
                "industry": "Consumer Electronics",
                "market_cap": 2800000000000,
                "revenue": 394000000000,
                "net_income": 97000000000,
                "pe_ratio": 28.5,
                "debt_to_equity": 1.76,
            },
            "technical_indicators": {
                "rsi": 58.3,
                "macd": 2.45,
                "moving_average_50": 178.25,
                "moving_average_200": 172.50,
            },
            "risk_assessment": {
                "risk_score": 4,
                "systematic_risk": 1.12,
                "idiosyncratic_risk": 0.18,
                "risk_factors": ["Market volatility", "Supply chain dependencies"],
                "mitigation_strategies": ["Diversification", "Long-term holding"],
            },
            "data_sources": ["Yahoo Finance API", "SEC EDGAR", "Alpha Vantage"],
            "report_json_path": "/output/reports/test/stock_crew/AAPL_export.json",
            "report_html_path": "/output/reports/test/stock_crew/AAPL_report.html",
        }
