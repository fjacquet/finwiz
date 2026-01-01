"""
Flow State Analysis Functions for FinWiz Application.

Contains complex analysis and summary preparation functions for flow state management.
"""

import logging
from typing import Any


def prepare_core_analysis_summary(
    consolidated_data: dict[str, Any],
    logger: logging.Logger,
) -> dict[str, Any]:
    """Prepare a summary of core analysis results for the reporter."""
    summary: dict[str, Any] = {
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
        crew_data_dict = consolidated_data.get("consolidated_crew_data", consolidated_data)

        for crew_type in ["stock", "etf", "crypto"]:
            if crew_type in crew_data_dict:
                summary["available_analyses"].append(crew_type)
                crew_data = crew_data_dict[crew_type]

                # Extract recommendations
                if "raw_output" in crew_data:
                    raw_output = str(crew_data["raw_output"]).lower()
                    if "buy" in raw_output or "strong buy" in raw_output:
                        summary["total_recommendations"] += raw_output.count("buy")

                # Extract key insights from tasks output
                if "tasks_output" in crew_data:
                    _extract_insights_from_tasks(crew_data, crew_type, summary)

                # Extract investment opportunities
                _extract_opportunities(crew_data, crew_type, summary)

        # Determine overall market sentiment
        _determine_market_sentiment(consolidated_data, summary)

        # Extract major risk factors
        _extract_risk_factors(consolidated_data, summary)

        # Determine overall risk level
        _determine_risk_level(summary)

        logger.debug(f"Prepared core analysis summary with {len(summary['available_analyses'])} analyses")
        return summary

    except Exception as e:
        logger.warning(f"Failed to prepare core analysis summary: {e}")
        return summary


def _extract_insights_from_tasks(
    crew_data: dict[str, Any],
    crew_type: str,
    summary: dict[str, Any],
) -> None:
    """Extract key insights from crew task outputs."""
    for task in crew_data["tasks_output"]:
        if isinstance(task, dict) and "raw" in task:
            task_content = str(task["raw"])
            if len(task_content) > 100:
                insight = task_content[:200] + "..." if len(task_content) > 200 else task_content
                summary["key_insights"].append(
                    {
                        "source": crew_type,
                        "insight": insight,
                    }
                )


def _extract_opportunities(
    crew_data: dict[str, Any],
    crew_type: str,
    summary: dict[str, Any],
) -> None:
    """Extract investment opportunities from crew data."""
    opportunities_key = f"{crew_type}s" if crew_type != "crypto" else "cryptos"
    if opportunities_key in summary["investment_opportunities"]:
        if "pydantic" in crew_data and crew_data["pydantic"]:
            pydantic_data = crew_data["pydantic"]
            if "opportunities" in pydantic_data:
                summary["investment_opportunities"][opportunities_key].extend(pydantic_data["opportunities"][:3])


def _determine_market_sentiment(
    consolidated_data: dict[str, Any],
    summary: dict[str, Any],
) -> None:
    """Determine overall market sentiment from consolidated data."""
    sentiment_data = consolidated_data.get("market_sentiment", {})
    if sentiment_data.get("aggregated_scores"):
        scores = sentiment_data["aggregated_scores"]
        positive = scores.get("positive", 0)
        negative = scores.get("negative", 0)

        if positive > negative + 0.1:
            summary["overall_market_sentiment"] = "positive"
        elif negative > positive + 0.1:
            summary["overall_market_sentiment"] = "negative"


def _extract_risk_factors(
    consolidated_data: dict[str, Any],
    summary: dict[str, Any],
) -> None:
    """Extract major risk factors from consolidated data."""
    crew_data_dict = consolidated_data.get("consolidated_crew_data", consolidated_data)
    for crew_type in ["stock", "etf", "crypto"]:
        if crew_type in crew_data_dict:
            crew_data = crew_data_dict[crew_type]
            if "raw_output" in crew_data:
                raw_output = str(crew_data["raw_output"]).lower()
                risk_keywords = [
                    "risk",
                    "volatility",
                    "uncertainty",
                    "concern",
                    "warning",
                ]
                for keyword in risk_keywords:
                    if keyword in raw_output:
                        summary["risk_assessment"]["major_risk_factors"].append(f"{crew_type}: {keyword}")


def _determine_risk_level(summary: dict[str, Any]) -> None:
    """Determine overall risk level based on risk factors."""
    risk_factor_count = len(summary["risk_assessment"]["major_risk_factors"])
    if risk_factor_count >= 5:
        summary["risk_assessment"]["overall_risk_level"] = "high"
    elif risk_factor_count >= 2:
        summary["risk_assessment"]["overall_risk_level"] = "medium"
    else:
        summary["risk_assessment"]["overall_risk_level"] = "low"
