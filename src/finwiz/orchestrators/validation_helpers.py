"""
Helper functions for ValidationOrchestrator.

This module contains extraction and processing helpers to keep
ValidationOrchestrator under 300 lines.
"""

from typing import Any


def extract_stock_context(
    core_analysis_data: dict[str, Any],
    market_context: dict[str, Any],
) -> None:
    """Extract context from stock analysis."""
    stock_data = core_analysis_data.get("stock_analysis", {})
    if not stock_data:
        return

    # Extract sentiment
    if sentiments := stock_data.get("market_sentiments"):
        positive = sum(1 for s in sentiments if s.get("sentiment", "").lower() in ["positive", "bullish"])
        negative = sum(1 for s in sentiments if s.get("sentiment", "").lower() in ["negative", "bearish"])
        if positive > negative:
            market_context["overall_sentiment"] = "positive"
        elif negative > positive:
            market_context["overall_sentiment"] = "negative"

    # Extract sector analysis
    if sector_analysis := stock_data.get("sector_analysis"):
        market_context["sector_analysis"] = sector_analysis


def extract_etf_context(
    core_analysis_data: dict[str, Any],
    market_context: dict[str, Any],
) -> None:
    """Extract context from ETF analysis."""
    if etf_data := core_analysis_data.get("etf_analysis"):
        if sector_trends := etf_data.get("sector_trends"):
            market_context["market_trends"].extend(sector_trends)


def extract_crypto_context(
    core_analysis_data: dict[str, Any],
    market_context: dict[str, Any],
) -> None:
    """Extract context from crypto analysis."""
    if crypto_data := core_analysis_data.get("crypto_analysis"):
        if market_dynamics := crypto_data.get("market_dynamics"):
            market_context["market_trends"].append(f"Crypto: {market_dynamics}")


def extract_common_factors(
    core_analysis_data: dict[str, Any],
    market_context: dict[str, Any],
) -> None:
    """Extract common risk factors and opportunities."""
    for analysis_data in core_analysis_data.values():
        if not isinstance(analysis_data, dict):
            continue

        if "risk_factors" in analysis_data and isinstance(analysis_data["risk_factors"], list):
            market_context["risk_factors"].extend(analysis_data["risk_factors"])

        if "opportunities" in analysis_data and isinstance(analysis_data["opportunities"], list):
            market_context["opportunities"].extend(analysis_data["opportunities"])


def prepare_core_analysis_summary(
    consolidated_data: dict[str, Any],
    core_analysis_status: dict[str, Any],
) -> dict[str, Any]:
    """Prepare a summary of core analysis data."""
    summary = {key: core_analysis_status[key] for key in ["available_crews", "failed_crews", "disabled_crews", "total_available", "total_failed", "total_disabled"]}

    crew_data = consolidated_data.get("consolidated_crew_data", {})
    for crew_type in ["stock", "etf", "crypto"]:
        data_available = crew_type in crew_data and crew_data[crew_type]
        data_count = len(crew_data[crew_type]) if data_available and isinstance(crew_data[crew_type], list) else (1 if data_available else 0)
        summary[f"{crew_type}_summary"] = {
            "available": data_available,
            "data_count": data_count,
        }

    return summary
