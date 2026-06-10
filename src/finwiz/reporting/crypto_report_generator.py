"""
Crypto Report Generator for cryptocurrency analysis HTML reports.

Generates HTML reports from CryptoCrewExport data using Jinja2 templates.
"""

from datetime import datetime
from typing import Any

from finwiz.reporting.base_report_generator import BaseReportGenerator


class CryptoReportGenerator(BaseReportGenerator):
    """
    Generate HTML reports for cryptocurrency analysis results.

    Uses the crypto_report.html template to render professional
    reports from CryptoCrewExport data.
    """

    def get_template_name(self) -> str:
        """Return the crypto report template path."""
        return "crew_reports/crypto_report.html"

    def get_required_fields(self) -> list[str]:
        """Return required fields for crypto reports."""
        return ["ticker", "asset_class", "composite_score", "grade", "recommendation", "confidence", "rationale", "volatility_30d", "max_drawdown"]

    def prepare_template_variables(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Prepare variables for crypto report template rendering.

        Args:
            data: Input data dictionary (typically from CryptoCrewExport.model_dump())

        Returns:
            Dictionary of template variables with defaults applied

        """
        template_vars = data.copy()

        # Apply shared defaults (analysis_date, session_id, data_sources, report paths).
        self._apply_common_defaults(template_vars)

        # Ensure asset_class is lowercase for template CSS classes
        template_vars["asset_class"] = template_vars.get("asset_class", "crypto").lower()

        # Ensure crypto-specific fields have defaults
        template_vars.setdefault("volatility_30d", 0.0)
        template_vars.setdefault("max_drawdown", 0.0)
        template_vars.setdefault("thesis", None)
        template_vars.setdefault("technical_analysis", None)
        template_vars.setdefault("risk_assessment", None)

        return template_vars

    def _get_default_data_sources(self) -> list[str]:
        """Return default data sources for crypto analysis."""
        return [
            "Yahoo Finance API",
            "FinWiz Python Scoring Engine",
            "CoinMarketCap API",
            "CoinGecko API",
        ]

    def get_sample_data(self) -> dict[str, Any]:
        """Return sample data for template validation."""
        return {
            "ticker": "BTC-USD",
            "asset_class": "crypto",
            "composite_score": 0.72,
            "grade": "B",
            "recommendation": "HOLD",
            "confidence": 0.75,
            "rationale": "Leading cryptocurrency with strong network effects but elevated volatility.",
            "session_id": "test-session",
            "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "volatility_30d": 0.45,
            "max_drawdown": -0.35,
            "thesis": {
                "project_name": "Bitcoin",
                "use_case": "Store of value, Digital gold",
                "technology": "Proof of Work blockchain",
                "market_cap": 850000000000,
                "circulating_supply": 19500000,
                "max_supply": 21000000,
            },
            "technical_analysis": {
                "rsi": 52.8,
                "macd": 1250.0,
                "support_level": 38000,
                "resistance_level": 48000,
            },
            "risk_assessment": {
                "risk_score": 7,
                "systematic_risk": 1.5,
                "idiosyncratic_risk": 0.8,
                "risk_factors": ["High volatility", "Regulatory uncertainty", "Market sentiment"],
                "mitigation_strategies": ["Position sizing", "Dollar-cost averaging"],
            },
            "data_sources": ["CoinMarketCap", "CoinGecko", "Yahoo Finance"],
            "report_json_path": "/output/reports/test/crypto_crew/BTC-USD_export.json",
            "report_html_path": "/output/reports/test/crypto_crew/BTC-USD_report.html",
        }
