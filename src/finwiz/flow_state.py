"""
Flow State Management for FinWiz Application.

This module contains state management classes and utilities for the CrewAI flow,
including state containers and state-related helper methods.
"""

import os
from datetime import datetime
from typing import Any

from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class FinwizState:
    """Represents the state for the FinWiz analysis flow."""

    etf_result: str = ""
    crypto_result: str = ""
    stock_result: str = ""


class FlowStateManager:
    """Manages flow state and provides state-related utilities."""

    def __init__(self) -> None:
        """Initialize the FlowStateManager."""
        self.logger = get_logger(__name__)

    def create_flow_inputs(self) -> dict[str, Any]:
        """Create standardized flow inputs with current timestamp and session information."""
        today = datetime.now()
        inputs = {
            "current_day": today.day,
            "current_month": today.month,
            "current_year": today.year,
            "current_date": today.strftime("%Y-%m-%d"),
            "full_date": today.strftime("%B %d, %Y"),
            "timestamp": today.strftime("%Y-%m-%d %H:%M:%S"),
            "report_language": "fr",
            # Session information available via environment variables
            "has_existing_session": os.getenv("FINWIZ_HAS_EXISTING_SESSION", "false") == "true",
            "session_id": os.getenv("FINWIZ_SESSION_ID", ""),
            "analysis_count": int(os.getenv("FINWIZ_ANALYSIS_COUNT", "0")),
        }

        self.logger.debug(f"Flow inputs prepared with timestamp: {inputs['timestamp']}")

        if inputs["has_existing_session"]:
            self.logger.debug(f"Flow initialized with existing session: {inputs['session_id']}")
        else:
            self.logger.debug("Flow initialized without existing session")

        return inputs

    def check_core_analysis_availability(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Check which core analysis crews are available and their status."""
        stock_available = inputs.get("stock_analysis_success", False) or (
            inputs.get("stock_analysis_fallback", False) and inputs.get("stock_analysis_result") is not None
        )
        etf_available = inputs.get("etf_analysis_success", False) or (
            inputs.get("etf_analysis_fallback", False) and inputs.get("etf_analysis_result") is not None
        )
        crypto_available = inputs.get("crypto_analysis_success", False) or (
            inputs.get("crypto_analysis_fallback", False) and inputs.get("crypto_analysis_result") is not None
        )

        available_crews = []
        if stock_available:
            available_crews.append("stock")
        if etf_available:
            available_crews.append("etf")
        if crypto_available:
            available_crews.append("crypto")

        failed_crews = []
        if inputs.get("stock_analysis_error"):
            failed_crews.append("stock")
        if inputs.get("etf_analysis_error"):
            failed_crews.append("etf")
        if inputs.get("crypto_analysis_error"):
            failed_crews.append("crypto")

        disabled_crews = []
        if inputs.get("stock_analysis_disabled"):
            disabled_crews.append("stock")
        if inputs.get("etf_analysis_disabled"):
            disabled_crews.append("etf")
        if inputs.get("crypto_analysis_disabled"):
            disabled_crews.append("crypto")

        return {
            "any_available": len(available_crews) > 0,
            "stock_available": stock_available,
            "etf_available": etf_available,
            "crypto_available": crypto_available,
            "available_crews": available_crews,
            "failed_crews": failed_crews,
            "disabled_crews": disabled_crews,
            "total_available": len(available_crews),
            "total_failed": len(failed_crews),
            "total_disabled": len(disabled_crews),
        }

    def extract_market_conditions(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Extract market conditions from core analysis results."""
        conditions = {}

        if inputs.get("stock_analysis_result"):
            # Extract market sentiment and trends from stock analysis
            conditions["stock_market_sentiment"] = "Available from stock analysis"

        if inputs.get("etf_analysis_result"):
            # Extract sector trends from ETF analysis
            conditions["sector_trends"] = "Available from ETF analysis"

        if inputs.get("crypto_analysis_result"):
            # Extract crypto market dynamics
            conditions["crypto_market_dynamics"] = "Available from crypto analysis"

        return conditions

    def extract_market_context_from_core_analysis(self, core_analysis_data: dict[str, Any]) -> dict[str, Any]:
        """
        Extract market context information from core analysis results.

        Args:
            core_analysis_data: Dictionary containing core analysis results

        Returns:
            Dictionary with extracted market context

        """
        market_context = {
            "overall_sentiment": "neutral",
            "market_trends": [],
            "risk_factors": [],
            "opportunities": [],
            "sector_analysis": {},
        }

        try:
            # Extract from stock analysis
            if "stock_analysis" in core_analysis_data:
                stock_data = core_analysis_data["stock_analysis"]

                # Extract market sentiment from stock analysis
                if "market_sentiments" in stock_data:
                    sentiments = stock_data["market_sentiments"]
                    if sentiments and len(sentiments) > 0:
                        # Calculate overall sentiment
                        positive_count = sum(1 for s in sentiments if s.get("sentiment", "").lower() in ["positive", "bullish"])
                        negative_count = sum(1 for s in sentiments if s.get("sentiment", "").lower() in ["negative", "bearish"])

                        if positive_count > negative_count:
                            market_context["overall_sentiment"] = "positive"
                        elif negative_count > positive_count:
                            market_context["overall_sentiment"] = "negative"

                # Extract sector information
                if "sector_analysis" in stock_data:
                    market_context["sector_analysis"] = stock_data["sector_analysis"]

            # Extract from ETF analysis
            if "etf_analysis" in core_analysis_data:
                etf_data = core_analysis_data["etf_analysis"]

                # Extract sector trends from ETF analysis
                if "sector_trends" in etf_data:
                    market_context["market_trends"].extend(etf_data["sector_trends"])

            # Extract from crypto analysis
            if "crypto_analysis" in core_analysis_data:
                crypto_data = core_analysis_data["crypto_analysis"]

                # Extract crypto market dynamics
                if "market_dynamics" in crypto_data:
                    market_context["market_trends"].append(f"Crypto: {crypto_data['market_dynamics']}")

            # Extract common risk factors
            for analysis_type, analysis_data in core_analysis_data.items():
                if "risk_factors" in analysis_data:
                    risk_factors = analysis_data["risk_factors"]
                    if isinstance(risk_factors, list):
                        market_context["risk_factors"].extend(risk_factors)

            # Extract opportunities
            for analysis_type, analysis_data in core_analysis_data.items():
                if "opportunities" in analysis_data:
                    opportunities = analysis_data["opportunities"]
                    if isinstance(opportunities, list):
                        market_context["opportunities"].extend(opportunities)

            self.logger.debug(f"Extracted market context from {len(core_analysis_data)} core analysis results")
            return market_context

        except Exception as e:
            self.logger.warning(f"Failed to extract market context from core analysis: {e}")
            return market_context

    def prepare_core_analysis_summary(self, consolidated_data: dict[str, Any]) -> dict[str, Any]:
        """
        Prepare a summary of core analysis results for the reporter.

        Args:
            consolidated_data: Consolidated data from all crews

        Returns:
            Dictionary with core analysis summary

        """
        summary = {
            "available_analyses": [],
            "total_recommendations": 0,
            "overall_market_sentiment": "neutral",
            "key_insights": [],
            "risk_assessment": {
                "overall_risk_level": "medium",
                "major_risk_factors": [],
            },
            "investment_opportunities": {
                "stocks": [],
                "etfs": [],
                "cryptos": [],
            },
        }

        try:
            # Process each core analysis type
            for crew_type in ["stock", "etf", "crypto"]:
                if crew_type in consolidated_data:
                    summary["available_analyses"].append(crew_type)
                    crew_data = consolidated_data[crew_type]

                    # Extract recommendations
                    if "raw_output" in crew_data:
                        # Count recommendations in raw output
                        raw_output = str(crew_data["raw_output"]).lower()
                        if "buy" in raw_output or "strong buy" in raw_output:
                            summary["total_recommendations"] += raw_output.count("buy")

                    # Extract key insights from tasks output
                    if "tasks_output" in crew_data:
                        for task in crew_data["tasks_output"]:
                            if isinstance(task, dict) and "raw" in task:
                                task_content = str(task["raw"])
                                if len(task_content) > 100:  # Meaningful content
                                    summary["key_insights"].append(
                                        {
                                            "source": crew_type,
                                            "insight": task_content[:200] + "..." if len(task_content) > 200 else task_content,
                                        }
                                    )

                    # Extract investment opportunities
                    opportunities_key = f"{crew_type}s" if crew_type != "crypto" else "cryptos"
                    if opportunities_key in summary["investment_opportunities"]:
                        # Extract symbols or opportunities from the analysis
                        if "pydantic" in crew_data and crew_data["pydantic"]:
                            pydantic_data = crew_data["pydantic"]
                            if "opportunities" in pydantic_data:
                                summary["investment_opportunities"][opportunities_key].extend(
                                    pydantic_data["opportunities"][:3]  # Top 3
                                )

            # Determine overall market sentiment
            sentiment_data = consolidated_data.get("market_sentiment", {})
            if sentiment_data.get("aggregated_scores"):
                scores = sentiment_data["aggregated_scores"]
                positive = scores.get("positive", 0)
                negative = scores.get("negative", 0)

                if positive > negative + 0.1:
                    summary["overall_market_sentiment"] = "positive"
                elif negative > positive + 0.1:
                    summary["overall_market_sentiment"] = "negative"
                else:
                    summary["overall_market_sentiment"] = "neutral"

            # Extract major risk factors
            for crew_type in ["stock", "etf", "crypto"]:
                if crew_type in consolidated_data:
                    crew_data = consolidated_data[crew_type]
                    if "raw_output" in crew_data:
                        raw_output = str(crew_data["raw_output"]).lower()
                        # Look for risk-related keywords
                        risk_keywords = ["risk", "volatility", "uncertainty", "concern", "warning"]
                        for keyword in risk_keywords:
                            if keyword in raw_output:
                                summary["risk_assessment"]["major_risk_factors"].append(f"{crew_type}: {keyword}")

            # Determine overall risk level
            risk_factor_count = len(summary["risk_assessment"]["major_risk_factors"])
            if risk_factor_count >= 5:
                summary["risk_assessment"]["overall_risk_level"] = "high"
            elif risk_factor_count >= 2:
                summary["risk_assessment"]["overall_risk_level"] = "medium"
            else:
                summary["risk_assessment"]["overall_risk_level"] = "low"

            self.logger.debug(f"Prepared core analysis summary with {len(summary['available_analyses'])} analyses")
            return summary

        except Exception as e:
            self.logger.warning(f"Failed to prepare core analysis summary: {e}")
            return summary

    def get_degraded_functionality_summary(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Get summary of degraded functionality across the system."""
        degraded_summary = {
            "has_degraded_functionality": False,
            "degraded_crews": [],
            "fallback_strategies_used": [],
            "missing_features": [],
            "data_quality_issues": [],
        }

        # Check for crew-specific degraded functionality
        for crew_name in ["stock", "etf", "crypto"]:
            degraded_functionality = inputs.get(f"{crew_name}_degraded_functionality", [])
            if degraded_functionality:
                degraded_summary["has_degraded_functionality"] = True
                degraded_summary["degraded_crews"].append(crew_name)
                degraded_summary["missing_features"].extend(degraded_functionality)

            fallback_strategy = inputs.get(f"{crew_name}_fallback_strategy")
            if fallback_strategy:
                degraded_summary["fallback_strategies_used"].append(f"{crew_name}: {fallback_strategy}")

        # Check for data quality issues
        if inputs.get("stale_data_warnings"):
            degraded_summary["data_quality_issues"].append("stale_data")

        if inputs.get("integrated_data_error"):
            degraded_summary["data_quality_issues"].append("integration_error")

        return degraded_summary
