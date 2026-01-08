"""
Portfolio decision utilities - Domain Layer Pure Functions.

This module contains pure functions for portfolio decision building:
- Score calculation
- Risk assessment
- Rationale generation
- Error handling

These functions are used by both portfolio_review.py and portfolio_holdings_processor.py.
Separated to avoid circular imports.
"""

from __future__ import annotations

from typing import Any

from finwiz.schemas.common import RiskAssessmentStandardized
from finwiz.schemas.portfolio_processing import AssetClass
from finwiz.schemas.portfolio_review import HoldingDecision
from finwiz.scoring.grading_system import score_to_grade

# =============================================================================
# Score Calculation
# =============================================================================


def calculate_score(is_valid: bool, asset_class: AssetClass) -> float:
    """Calculate composite score based on validation status.

    This is a simplified scoring for the holdings processor.
    Full scoring is done in deep analysis.

    Args:
        is_valid: Whether ticker validation passed
        asset_class: The asset class type

    Returns:
        Composite score between 0 and 1
    """
    if not is_valid:
        return 0.3  # Low score for invalid tickers

    # Base scores by asset class (will be refined in deep analysis)
    base_scores = {
        "stock": 0.6,
        "etf": 0.65,
        "crypto": 0.5,
        "unknown": 0.4,
    }
    return base_scores.get(asset_class, 0.5)


# =============================================================================
# Risk Assessment
# =============================================================================


def assess_risk(is_valid: bool, validation_result: dict[str, Any]) -> RiskAssessmentStandardized:
    """Assess risk based on validation results.

    Args:
        is_valid: Whether validation passed
        validation_result: Full validation result dict

    Returns:
        Standardized risk assessment
    """
    if not is_valid:
        return RiskAssessmentStandardized(
            score=4.5,
            level="High",
            risk_factors=["validation_failed", "data_quality_concerns"],
        )

    return RiskAssessmentStandardized(
        score=2.5,
        level="Medium",
        risk_factors=["pending_deep_analysis"],
    )


# =============================================================================
# Rationale Building
# =============================================================================


def build_rationale(
    is_valid: bool,
    validation_result: dict[str, Any],
    asset_class: AssetClass,
) -> str:
    """Build rationale string for holding decision.

    Args:
        is_valid: Whether validation passed
        validation_result: Full validation result dict
        asset_class: The asset class type

    Returns:
        Human-readable rationale string
    """
    if not is_valid:
        return f"Unable to validate {asset_class}. May be delisted or invalid ticker."

    return f"Validated {asset_class}. Pending deep analysis for detailed recommendation."


# =============================================================================
# Citations Building
# =============================================================================


def build_citations(validation_result: dict[str, Any]) -> list[str]:
    """Build citations from validation result.

    Args:
        validation_result: Full validation result dict

    Returns:
        List of citation strings
    """
    citations = []
    if validation_result.get("exchange"):
        citations.append(f"Exchange: {validation_result['exchange']}")
    if validation_result.get("currency"):
        citations.append(f"Currency: {validation_result['currency']}")
    return citations if citations else ["Yahoo Finance validation"]


# =============================================================================
# Error Decision Creation
# =============================================================================


def create_error_decision(
    ticker: str,
    name: str,
    asset_class: AssetClass,
    error_message: str,
) -> HoldingDecision:
    """Create a holding decision for error cases.

    Args:
        ticker: Ticker symbol
        name: Holding name
        asset_class: Asset class type
        error_message: Error description

    Returns:
        HoldingDecision with error status
    """
    grade_info = score_to_grade(0.0)
    return HoldingDecision(
        ticker=ticker,
        name=name,
        asset_class=asset_class,
        currency="USD",
        decision="KEEP",  # Conservative: keep until properly analyzed
        composite_score=0.0,
        grade=grade_info.grade,
        grade_description=grade_info.description,
        recommended_action="Review manually - processing error occurred",
        risk=RiskAssessmentStandardized(
            score=5.0,
            level="Very High",
            risk_factors=["processing_error", error_message],
        ),
        rationale_bullets=[f"Error during processing: {error_message}"],
        citations=[],
        alternatives=[],
        data_freshness="stale",  # Mark as stale when error occurred
    )


__all__ = [
    "calculate_score",
    "assess_risk",
    "build_rationale",
    "build_citations",
    "create_error_decision",
]
