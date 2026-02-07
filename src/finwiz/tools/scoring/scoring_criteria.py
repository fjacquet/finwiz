"""
Scoring criteria evaluators for A+ Investment Scoring Tool.

This module contains functions for assessing market regimes, generating dynamic
criteria, analyzing strengths/weaknesses, and generating scoring rationales.
"""

from datetime import datetime
from typing import Any, Literal, cast

from finwiz.schemas.tools import MarketRegime, ScoringCriteria
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


def assess_market_regime(
    market_context: dict[str, Any],
    cache: dict[str, Any] | None = None,
) -> MarketRegime:
    """Assess current market regime from context data."""
    try:
        # Use cached regime if recent (within 1 hour)
        if cache and cache.get("regime") and cache.get("timestamp"):
            if (datetime.now() - cache["timestamp"]).seconds < 3600:
                regime: MarketRegime = cache["regime"]
                return regime

        # Extract market indicators from context
        vix_level = market_context.get("vix", 20.0)
        inflation_rate = market_context.get("inflation", 3.0)

        # Determine regime type
        if vix_level > 30:
            regime_type = "volatile"
        elif vix_level > 25:
            regime_type = "bear"
        elif vix_level < 15:
            regime_type = "bull"
        else:
            regime_type = "sideways"

        # Determine interest rate trend
        rate_change = market_context.get("rate_change_6m", 0.0)
        if rate_change > 0.5:
            interest_rate_trend = "rising"
        elif rate_change < -0.5:
            interest_rate_trend = "falling"
        else:
            interest_rate_trend = "stable"

        # Determine stress level
        if vix_level > 35 or inflation_rate > 6:
            stress_level = "high"
        elif vix_level > 25 or inflation_rate > 4:
            stress_level = "medium"
        else:
            stress_level = "low"

        regime = MarketRegime(
            regime_type=cast(Literal["bull", "bear", "sideways", "volatile"], regime_type),
            vix_level=vix_level,
            inflation_rate=inflation_rate,
            interest_rate_trend=cast(Literal["rising", "falling", "stable"], interest_rate_trend),
            market_stress_level=cast(Literal["low", "medium", "high"], stress_level),
        )

        # Update cache if provided
        if cache is not None:
            cache["regime"] = regime
            cache["timestamp"] = datetime.now()

        return regime

    except (KeyError, TypeError, ValueError, AttributeError) as e:
        logger.warning(f"Failed to assess market regime: {e}")
        # Return default regime on error
        return MarketRegime()


def get_dynamic_criteria(market_regime: MarketRegime, custom_criteria: dict[str, float]) -> ScoringCriteria:
    """Get dynamic scoring criteria adjusted for market conditions."""
    criteria = ScoringCriteria()

    # Adjust criteria based on market regime
    if market_regime.regime_type == "bear" or market_regime.market_stress_level == "high":
        # Tighten quality requirements in bear markets
        criteria.stock_min_roe = 0.25  # Higher ROE requirement
        criteria.stock_max_debt_to_equity = 0.2  # Lower debt tolerance
        criteria.etf_max_expense_ratio = 0.10  # Lower cost tolerance
        criteria.crypto_min_market_cap = 20e9  # Higher market cap requirement

    elif market_regime.regime_type == "bull":
        # Slightly relax criteria in bull markets
        criteria.stock_min_roe = 0.18
        criteria.stock_max_debt_to_equity = 0.4
        criteria.etf_max_expense_ratio = 0.20

    # Adjust for inflation
    if market_regime.inflation_rate > 4:
        # Favor real assets and pricing power
        criteria.stock_min_revenue_growth = 0.20  # Higher growth requirement

    # Apply custom criteria overrides
    for key, value in custom_criteria.items():
        if hasattr(criteria, key):
            setattr(criteria, key, value)

    return criteria


def analyze_strengths_weaknesses(symbol: str, asset_type: str, data: dict[str, Any], scores: dict[str, float]) -> tuple[list[str], list[str]]:
    """Analyze investment strengths and weaknesses."""
    strengths = []
    weaknesses = []

    # Analyze component scores
    if scores["fundamental"] >= 0.8:
        strengths.append("Excellent fundamental metrics")
    elif scores["fundamental"] <= 0.4:
        weaknesses.append("Weak fundamental performance")

    if scores["technical"] >= 0.8:
        strengths.append("Strong technical momentum")
    elif scores["technical"] <= 0.4:
        weaknesses.append("Poor technical indicators")

    if scores["quality"] >= 0.8:
        strengths.append("High quality management/structure")
    elif scores["quality"] <= 0.4:
        weaknesses.append("Quality concerns")

    if scores["risk"] >= 0.8:
        strengths.append("Favorable risk profile")
    elif scores["risk"] <= 0.4:
        weaknesses.append("Elevated risk levels")

    # Asset-specific analysis
    if asset_type == "etf":
        expense_ratio = data.get("expense_ratio", 0.5)
        if expense_ratio <= 0.1:
            strengths.append("Ultra-low expense ratio")
        elif expense_ratio >= 0.5:
            weaknesses.append("High expense ratio")

    elif asset_type == "stock":
        roe = data.get("roe", 0.1)
        if roe >= 0.25:
            strengths.append("Exceptional return on equity")
        elif roe <= 0.1:
            weaknesses.append("Low profitability")

    elif asset_type == "crypto":
        market_cap = data.get("market_cap", 0)
        if market_cap >= 50e9:
            strengths.append("Large, established market cap")
        elif market_cap <= 1e9:
            weaknesses.append("Small market cap risk")

    return strengths[:10], weaknesses[:10]


def generate_a_plus_rationale(
    symbol: str,
    asset_type: str,
    score: float,
    strengths: list[str],
    weaknesses: list[str],
    regime: MarketRegime,
) -> str:
    """Generate detailed A+ rationale."""
    if score >= 0.95:
        rationale = f"{symbol} achieves A+ status with a composite score of {score:.2f}. "
        rationale += f"Key strengths include: {', '.join(strengths[:3])}. "
        if weaknesses:
            rationale += f"Minor concerns: {', '.join(weaknesses[:2])}. "
        rationale += f"In the current {regime.regime_type} market environment, this investment "
        rationale += "demonstrates exceptional quality across all evaluation dimensions."
    elif score >= 0.85:
        rationale = f"{symbol} shows strong A-grade characteristics with a score of {score:.2f}. "
        rationale += f"Notable strengths: {', '.join(strengths[:2])}. "
        if weaknesses:
            rationale += f"Areas for improvement: {', '.join(weaknesses[:2])}. "
        rationale += "While not quite A+ level, this represents a high-quality investment opportunity."
    else:
        rationale = f"{symbol} scores {score:.2f}, indicating room for improvement to reach A+ status. "
        if strengths:
            rationale += f"Positive aspects: {', '.join(strengths[:2])}. "
        if weaknesses:
            rationale += f"Key concerns: {', '.join(weaknesses[:3])}. "
        rationale += "Consider monitoring for improvements in weak areas before investment."

    return rationale


def calculate_confidence_level(data: dict[str, Any], regime: MarketRegime, score: float) -> float:
    """Calculate confidence level in the scoring."""
    confidence = 0.7  # Base confidence

    # Adjust based on data completeness
    data_completeness = len([v for v in data.values() if v is not None]) / max(len(data), 1)
    confidence += (data_completeness - 0.5) * 0.2

    # Adjust based on market regime uncertainty
    if regime.market_stress_level == "high":
        confidence -= 0.1
    elif regime.regime_type == "volatile":
        confidence -= 0.05

    # Adjust based on score extremes (more confident in clear cases)
    if score >= 0.9 or score <= 0.3:
        confidence += 0.1

    return min(max(confidence, 0.0), 1.0)
