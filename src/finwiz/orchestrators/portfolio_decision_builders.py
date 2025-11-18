"""
Helper functions for building portfolio holding decisions.

This module contains pure functions for building HoldingDecision components
from validation results and holding data.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from finwiz.schemas.common import RiskAssessmentStandardized
from finwiz.schemas.portfolio_processing import AssetClass, RawHolding
from finwiz.schemas.portfolio_review import HoldingDecision
from finwiz.utils.grading_system import score_to_grade


def calculate_score(is_valid: bool, asset_class: AssetClass) -> float:
    """
    Calculate composite score for a holding using improved shallow validation.

    This method provides more realistic scores for validated holdings when deep
    analysis is not enabled. The scoring assumes that holdings in a portfolio
    are generally reasonable investments that passed initial screening.

    Args:
        is_valid: Whether the holding passed validation
        asset_class: Type of asset

    Returns:
        Composite score between 0.0 and 1.0

    Scoring Logic:
        - Valid holdings: 0.75 base (B grade) - assumes reasonable quality
        - ETFs: +0.05 for diversification benefit
        - Invalid holdings: 0.3 (F grade) - requires manual review

    """
    if not is_valid:
        # Invalid holdings get low score - requires manual review
        return 0.3

    # Base score for validated holdings - assumes reasonable quality
    # This gives a B grade (75%) which is appropriate for holdings that:
    # - Passed ticker validation
    # - Are in an active portfolio
    # - Haven't been analyzed in depth yet
    base = 0.75

    # ETFs get a slight boost for diversification benefit
    if asset_class == "etf":
        base += 0.05

    # Stocks and crypto maintain base score
    # Deep analysis will provide more accurate scoring when enabled

    return min(base, 1.0)


def assess_risk(is_valid: bool, validation_result: dict[str, Any]) -> RiskAssessmentStandardized:
    """
    Assess risk for a holding.

    Args:
        is_valid: Whether validation passed
        validation_result: Validation result dictionary

    Returns:
        Standardized risk assessment

    """
    if is_valid:
        return RiskAssessmentStandardized(
            score=2.0,
            level="Medium",
            risk_factors=["Baseline risk - ticker validated"],
        )

    # Higher risk for invalid holdings
    reason = validation_result.get("reason", "Unknown validation failure")
    return RiskAssessmentStandardized(
        score=4.5,
        level="Very High",
        risk_factors=[
            "Validation failed",
            f"Reason: {reason}",
            "Unable to verify ticker existence",
        ],
    )


def build_rationale(
    is_valid: bool,
    validation_result: dict[str, Any],
    holding: RawHolding,
) -> list[str]:
    """
    Build rationale bullets for a holding decision.

    Args:
        is_valid: Whether validation passed
        validation_result: Validation result
        holding: Raw holding data

    Returns:
        List of rationale bullet points

    """
    rationale: list[str] = []

    # Add analysis depth indicator
    rationale.append("⚡ Validation rapide (analyse superficielle)")
    rationale.append("💡 Activez DEEP_PORTFOLIO_ANALYSIS=true pour une analyse complète")

    if is_valid:
        rationale.append("✅ Ticker validé avec succès")
        source = validation_result.get("meta", {}).get("source", "unknown")
        rationale.append(f"Source de données: {source}")
        rationale.append("📊 Note basée sur la validation du ticker uniquement")
        rationale.append("🔍 L'analyse approfondie fournira des métriques détaillées")
    else:
        rationale.append("⚠️ Échec de la validation du ticker")
        reason = validation_result.get("reason", "Unknown reason")
        rationale.append(f"Problème de validation: {reason}")
        rationale.append("📋 Inclus dans le rapport pour transparence")
        rationale.append("🔧 Révision manuelle requise")

    # Add source information
    rationale.append(f"📁 Source: {Path(holding.source_file).name}, ligne {holding.line_number}")

    return rationale


def build_citations(validation_result: dict[str, Any]) -> list[str]:
    """
    Build citations list from validation result.

    Args:
        validation_result: Validation result dictionary

    Returns:
        List of citation strings

    """
    citations: list[str] = []

    source = validation_result.get("meta", {}).get("source")
    if source == "yahoo":
        citations.append("Yahoo Finance")
    elif source == "coinbase":
        citations.append("Coinbase Products API")

    return citations


def create_error_decision(
    holding: RawHolding,
    base_currency: str,
    error_message: str,
) -> HoldingDecision:
    """
    Create a minimal decision for a holding that failed to process.

    Args:
        holding: Raw holding that failed
        base_currency: Base currency
        error_message: Error message

    Returns:
        HoldingDecision with error information

    """
    grade_info = score_to_grade(0.0)

    return HoldingDecision(
        asset_class=holding.asset_class,
        name=holding.name,
        ticker=holding.ticker,
        currency=holding.currency or base_currency,
        decision="SELL",  # type: ignore[arg-type]
        composite_score=0.0,
        grade=grade_info.grade,  # type: ignore[arg-type]
        grade_description="Processing Error",
        recommended_action="Review manually",
        risk=RiskAssessmentStandardized(
            score=5.0,
            level="Very High",
            risk_factors=["Processing error", error_message],
        ),
        rationale_bullets=[
            "❌ Failed to process holding",
            f"Error: {error_message}",
            "Manual review required",
        ],
        citations=[],
        alternatives=[],
        data_freshness="stale",  # type: ignore[arg-type]
    )
