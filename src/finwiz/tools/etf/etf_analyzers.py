"""
ETF analysis utilities for comprehensive ETF evaluation.

Provides methods for ETF risk assessment, factsheet construction,
and performance analysis.
"""

from datetime import datetime
from typing import Any

from pydantic import ValidationError

from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class ETFAnalyzer:
    """Utility class for analyzing ETF data and constructing factsheets."""

    @staticmethod
    def perform_etf_risk_assessment(
        ticker: str, factsheet_data: dict[str, Any], holdings_data: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Perform standardized risk assessment for ETF."""
        try:
            risk_factors = []
            base_score = 1.0  # Start with low risk

            # Assess expense ratio risk
            expense_ratio = factsheet_data.get("expense_ratio", 0.2)
            if expense_ratio > 1.0:
                risk_factors.append("High expense ratio")
                base_score += 0.5
            elif expense_ratio > 0.5:
                risk_factors.append("Moderate expense ratio")
                base_score += 0.2

            # Assess concentration risk from holdings
            if holdings_data:
                top_holding_weight = max([h.get("weight_pct", 0) for h in holdings_data], default=0)
                if top_holding_weight > 20:
                    risk_factors.append("High concentration risk")
                    base_score += 1.0
                elif top_holding_weight > 10:
                    risk_factors.append("Moderate concentration risk")
                    base_score += 0.5

            # Assess tracking risk
            tracking_diff = factsheet_data.get("tracking_diff")
            if tracking_diff and abs(tracking_diff) > 2.0:
                risk_factors.append("High tracking error")
                base_score += 0.8
            elif tracking_diff and abs(tracking_diff) > 1.0:
                risk_factors.append("Moderate tracking error")
                base_score += 0.3

            # Assess replication method risk
            replication = factsheet_data.get("replication_method", "other")
            if replication == "synthetic":
                risk_factors.append("Counterparty risk from synthetic replication")
                base_score += 0.5

            # Add general ETF risks
            risk_factors.extend(["Market volatility risk", "Liquidity risk during stress periods"])

            # Calculate final score and level
            final_score = min(base_score, 5.0)
            risk_level = ETFAnalyzer.map_score_to_level(final_score)

            return {
                "ticker": ticker,
                "scale": "0_5",
                "score": round(final_score, 1),
                "level": risk_level,
                "risk_factors": risk_factors[:10],  # Limit to 10 factors
                "assessment_date": datetime.now().isoformat(),
            }

        except Exception as e:
            # Return default risk assessment on error
            return {
                "ticker": ticker,
                "scale": "0_5",
                "score": 2.5,
                "level": "Medium",
                "risk_factors": ["General market risk", "ETF-specific risks"],
                "assessment_date": datetime.now().isoformat(),
                "error": f"Risk assessment error: {e}",
            }

    @staticmethod
    def map_score_to_level(score: float) -> str:
        """Map numerical risk score to standardized risk level."""
        if score <= 1.5:
            return "Low"
        elif score <= 2.5:
            return "Medium"
        elif score <= 4.0:
            return "High"
        else:
            return "Very High"

    @staticmethod
    def construct_etf_factsheet(
        ticker: str,
        factsheet_data: dict[str, Any],
        holdings_data: list[dict[str, Any]],
        risk_assessment: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Construct ETF factsheet object from extracted data."""
        try:
            from datetime import date

            # Convert holdings to proper format
            top_holdings = []
            for holding in holdings_data:
                try:
                    top_holding = {
                        "ticker": holding["ticker"],
                        "weight_pct": holding["weight_pct"],
                        "source_url": holding["source_url"],
                        "as_of": holding["as_of"],
                    }
                    top_holdings.append(top_holding)
                except (KeyError, ValidationError):
                    continue  # Skip invalid holdings

            # Convert risk assessment if available
            risk = None
            if risk_assessment:
                try:
                    risk = {
                        "scale": risk_assessment["scale"],
                        "score": risk_assessment["score"],
                        "level": risk_assessment["level"],
                        "risk_factors": risk_assessment["risk_factors"],
                    }
                except KeyError:
                    pass  # Skip invalid risk assessment

            # Construct factsheet
            factsheet = {
                "schema_version": 1,
                "ticker": ticker,
                "issuer": factsheet_data.get("issuer", "Unknown"),
                "expense_ratio": factsheet_data.get("expense_ratio", 0.2),
                "tracking_diff": factsheet_data.get("tracking_diff"),
                "replication_method": factsheet_data.get("replication_method", "other"),
                "factsheet_url": factsheet_data.get("factsheet_url", f"https://finance.yahoo.com/quote/{ticker}"),
                "as_of": factsheet_data.get("as_of", date.today()),
                "factsheet_highlights": factsheet_data.get("factsheet_highlights", []),
                "top_holdings": top_holdings,
                "risk": risk,
            }

            return factsheet

        except Exception as e:
            # Return minimal factsheet on error
            from datetime import date

            return {
                "schema_version": 1,
                "ticker": ticker,
                "issuer": "Unknown",
                "expense_ratio": 0.2,
                "factsheet_url": f"https://finance.yahoo.com/quote/{ticker}",
                "as_of": date.today(),
                "error": f"Factsheet construction error: {e}",
            }
