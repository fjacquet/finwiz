"""
Flow State Utility Functions for FinWiz Application.

Contains extraction utility functions for flow state management.
Complex analysis functions are in flow_state_analysis.py.
"""

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .flow_state_models import FinwizState

# Re-export prepare_core_analysis_summary for backward compatibility
from .flow_state_analysis import prepare_core_analysis_summary

__all__ = [
    "check_core_analysis_availability",
    "extract_market_conditions",
    "extract_market_context_from_core_analysis",
    "get_degraded_functionality_summary",
    "prepare_core_analysis_summary",
]


def check_core_analysis_availability(
    state: "FinwizState",
    logger: logging.Logger,
) -> dict[str, Any]:
    """Check which core analysis crews are available and their status."""
    from .integration.manager import CrewDataIntegrationManager

    integration_manager = CrewDataIntegrationManager()

    stock_available = False
    etf_available = False
    crypto_available = False

    try:
        stock_data = integration_manager.get_crew_data_with_freshness_check("stock", max_age_hours=24, warn_on_stale=False)
        stock_available = stock_data is not None

        etf_data = integration_manager.get_crew_data_with_freshness_check("etf", max_age_hours=24, warn_on_stale=False)
        etf_available = etf_data is not None

        crypto_data = integration_manager.get_crew_data_with_freshness_check("crypto", max_age_hours=24, warn_on_stale=False)
        crypto_available = crypto_data is not None

    except Exception as e:
        logger.warning(f"Failed to check actual data availability, falling back to state flags: {e}")
        stock_available = state.stock_analysis_success or (state.stock_analysis_fallback and state.stock_analysis_result is not None)
        etf_available = state.etf_analysis_success or (state.etf_analysis_fallback and state.etf_analysis_result is not None)
        crypto_available = state.crypto_analysis_success or (state.crypto_analysis_fallback and state.crypto_analysis_result is not None)

    available_crews = []
    if stock_available:
        available_crews.append("stock")
    if etf_available:
        available_crews.append("etf")
    if crypto_available:
        available_crews.append("crypto")

    failed_crews = []
    if state.stock_analysis_error:
        failed_crews.append("stock")
    if state.etf_analysis_error:
        failed_crews.append("etf")
    if state.crypto_analysis_error:
        failed_crews.append("crypto")

    disabled_crews = []
    if state.stock_analysis_disabled:
        disabled_crews.append("stock")
    if state.etf_analysis_disabled:
        disabled_crews.append("etf")
    if state.crypto_analysis_disabled:
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


def extract_market_conditions(state: "FinwizState") -> dict[str, Any]:
    """Extract market conditions from core analysis results."""
    conditions: dict[str, Any] = {}

    if state.stock_analysis_result:
        conditions["stock_market_sentiment"] = "Available from stock analysis"
    if state.etf_analysis_result:
        conditions["sector_trends"] = "Available from ETF analysis"
    if state.crypto_analysis_result:
        conditions["crypto_market_dynamics"] = "Available from crypto analysis"

    return conditions


def extract_market_context_from_core_analysis(
    core_analysis_data: dict[str, Any],
    logger: logging.Logger,
) -> dict[str, Any]:
    """Extract market context information from core analysis results."""
    market_context: dict[str, Any] = {
        "overall_sentiment": "neutral",
        "market_trends": [],
        "risk_factors": [],
        "opportunities": [],
        "sector_analysis": {},
    }

    try:
        # Extract from stock analysis
        if "stock_analysis" in core_analysis_data:
            _extract_stock_context(core_analysis_data["stock_analysis"], market_context)

        # Extract from ETF analysis
        if "etf_analysis" in core_analysis_data:
            _extract_etf_context(core_analysis_data["etf_analysis"], market_context)

        # Extract from crypto analysis
        if "crypto_analysis" in core_analysis_data:
            _extract_crypto_context(core_analysis_data["crypto_analysis"], market_context)

        # Extract common risk factors and opportunities
        _extract_common_factors(core_analysis_data, market_context)

        logger.debug(f"Extracted market context from {len(core_analysis_data)} analyses")
        return market_context

    except Exception as e:
        logger.warning(f"Failed to extract market context from core analysis: {e}")
        return market_context


def _extract_stock_context(
    stock_data: dict[str, Any],
    market_context: dict[str, Any],
) -> None:
    """Extract context from stock analysis data."""
    if "market_sentiments" in stock_data:
        sentiments = stock_data["market_sentiments"]
        if sentiments and len(sentiments) > 0:
            positive_count = sum(1 for s in sentiments if s.get("sentiment", "").lower() in ["positive", "bullish"])
            negative_count = sum(1 for s in sentiments if s.get("sentiment", "").lower() in ["negative", "bearish"])

            if positive_count > negative_count:
                market_context["overall_sentiment"] = "positive"
            elif negative_count > positive_count:
                market_context["overall_sentiment"] = "negative"

    if "sector_analysis" in stock_data:
        market_context["sector_analysis"] = stock_data["sector_analysis"]


def _extract_etf_context(
    etf_data: dict[str, Any],
    market_context: dict[str, Any],
) -> None:
    """Extract context from ETF analysis data."""
    if "sector_trends" in etf_data:
        market_context["market_trends"].extend(etf_data["sector_trends"])


def _extract_crypto_context(
    crypto_data: dict[str, Any],
    market_context: dict[str, Any],
) -> None:
    """Extract context from crypto analysis data."""
    if "market_dynamics" in crypto_data:
        market_context["market_trends"].append(f"Crypto: {crypto_data['market_dynamics']}")


def _extract_common_factors(
    core_analysis_data: dict[str, Any],
    market_context: dict[str, Any],
) -> None:
    """Extract common risk factors and opportunities from all analyses."""
    for analysis_data in core_analysis_data.values():
        if isinstance(analysis_data, dict):
            if "risk_factors" in analysis_data:
                risk_factors = analysis_data["risk_factors"]
                if isinstance(risk_factors, list):
                    market_context["risk_factors"].extend(risk_factors)

            if "opportunities" in analysis_data:
                opportunities = analysis_data["opportunities"]
                if isinstance(opportunities, list):
                    market_context["opportunities"].extend(opportunities)


def get_degraded_functionality_summary(state: "FinwizState") -> dict[str, Any]:
    """Get summary of degraded functionality across the system."""
    degraded_summary: dict[str, Any] = {
        "has_degraded_functionality": False,
        "degraded_crews": [],
        "fallback_strategies_used": [],
        "missing_features": [],
        "data_quality_issues": [],
    }

    degraded_funcs = {
        "stock": state.stock_degraded_functionality,
        "etf": state.etf_degraded_functionality,
        "crypto": state.crypto_degraded_functionality,
    }

    for crew_name, degraded_functionality in degraded_funcs.items():
        if degraded_functionality:
            degraded_summary["has_degraded_functionality"] = True
            degraded_summary["degraded_crews"].append(crew_name)
            degraded_summary["missing_features"].extend(degraded_functionality)

    fallback_strategies = {
        "stock": state.stock_fallback_strategy,
        "etf": state.etf_fallback_strategy,
        "crypto": state.crypto_fallback_strategy,
    }

    for crew_name, fallback_strategy in fallback_strategies.items():
        if fallback_strategy:
            degraded_summary["fallback_strategies_used"].append(f"{crew_name}: {fallback_strategy}")

    if state.stale_data_warnings:
        degraded_summary["data_quality_issues"].append("stale_data")

    if state.integrated_data_error:
        degraded_summary["data_quality_issues"].append("integration_error")

    return degraded_summary
