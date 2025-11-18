"""
Risk-based recommendations for portfolio rebalancing.

This module provides functions for generating recommendations based on
risk assessments, including tolerance adjustments and rebalancing frequency.
"""

from __future__ import annotations

from finwiz.quantitative.risk_metrics import (
    RiskLevel,
    RiskWarning,
    RiskWarningType,
)


def recommend_tolerance_adjustment(
    warnings: list[RiskWarning],
    market_volatility: float | None,
) -> float | None:
    """
    Recommend tolerance band adjustment based on risk assessment.

    Args:
        warnings: List of risk warnings
        market_volatility: Current market volatility (optional)

    Returns:
        Recommended tolerance adjustment (0-1 scale) or None if no adjustment needed

    """
    high_risk_warnings = [w for w in warnings if w.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]]

    if not high_risk_warnings:
        return None

    # Check for volatility warnings
    volatility_warnings = [w for w in high_risk_warnings if w.warning_type == RiskWarningType.VOLATILITY]
    if volatility_warnings and market_volatility:
        if market_volatility > 0.40:
            return 0.15  # Suggest 15% tolerance in extreme volatility
        elif market_volatility > 0.25:
            return 0.10  # Suggest 10% tolerance in high volatility

    # Check for turnover warnings
    turnover_warnings = [w for w in high_risk_warnings if w.warning_type == RiskWarningType.TURNOVER]
    if turnover_warnings:
        return 0.08  # Suggest 8% tolerance to reduce turnover

    return None


def recommend_rebalancing_frequency(
    warnings: list[RiskWarning],
    market_volatility: float | None,
) -> str:
    """
    Recommend rebalancing frequency based on risk assessment.

    Args:
        warnings: List of risk warnings
        market_volatility: Current market volatility (optional)

    Returns:
        Recommended rebalancing frequency as a string

    """
    high_risk_count = len([w for w in warnings if w.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]])

    if high_risk_count >= 3:
        return "Delay rebalancing until risks subside"
    elif high_risk_count >= 2:
        return "Quarterly rebalancing with careful monitoring"
    elif market_volatility and market_volatility > 0.30:
        return "Semi-annual rebalancing during high volatility periods"
    elif any(w.warning_type == RiskWarningType.TURNOVER for w in warnings):
        return "Quarterly rebalancing to manage turnover"
    else:
        return "Monthly rebalancing with standard monitoring"
