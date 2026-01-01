"""
Scoring algorithms for A+ Investment Scoring Tool.

This module contains the core scoring algorithms for evaluating ETFs, stocks,
and cryptocurrencies across fundamental, technical, quality, and risk dimensions.
"""

from typing import Any

from finwiz.schemas.tools import MarketRegime, ScoringCriteria


def calculate_fundamental_score(symbol: str, asset_type: str, data: dict[str, Any], criteria: ScoringCriteria) -> float:
    """Calculate fundamental analysis score."""
    try:
        if asset_type == "etf":
            return score_etf_fundamentals(data, criteria)
        elif asset_type == "stock":
            return score_stock_fundamentals(data, criteria)
        elif asset_type == "crypto":
            return score_crypto_fundamentals(data, criteria)
        else:
            return 0.5  # Default score for unknown types

    except Exception:
        return 0.5  # Default on error


def score_etf_fundamentals(data: dict[str, Any], criteria: ScoringCriteria) -> float:
    """Score ETF fundamental characteristics."""
    score = 0.0
    max_score = 0.0

    # Expense ratio (30% weight)
    expense_ratio = data.get("expense_ratio", 0.5)
    if expense_ratio <= criteria.etf_max_expense_ratio:
        score += 0.3
    elif expense_ratio <= criteria.etf_max_expense_ratio * 1.5:
        score += 0.15
    max_score += 0.3

    # AUM/Liquidity (25% weight)
    aum = data.get("aum", 0)
    if aum >= criteria.etf_min_aum:
        score += 0.25
    elif aum >= criteria.etf_min_aum * 0.5:
        score += 0.125
    max_score += 0.25

    # Tracking error (25% weight)
    tracking_error = data.get("tracking_error", 0.01)
    if tracking_error <= criteria.etf_max_tracking_error:
        score += 0.25
    elif tracking_error <= criteria.etf_max_tracking_error * 2:
        score += 0.125
    max_score += 0.25

    # Track record (20% weight)
    history_years = data.get("history_years", 0)
    if history_years >= criteria.etf_min_history_years:
        score += 0.20
    elif history_years >= criteria.etf_min_history_years * 0.5:
        score += 0.10
    max_score += 0.20

    return min(score / max_score if max_score > 0 else 0.5, 1.0)


def score_stock_fundamentals(data: dict[str, Any], criteria: ScoringCriteria) -> float:
    """Score stock fundamental characteristics."""
    score = 0.0
    max_score = 0.0

    # ROE (25% weight)
    roe = data.get("roe", 0.1)
    if roe >= criteria.stock_min_roe:
        score += 0.25
    elif roe >= criteria.stock_min_roe * 0.8:
        score += 0.125
    max_score += 0.25

    # Revenue growth (25% weight)
    revenue_growth = data.get("revenue_growth", 0.05)
    if revenue_growth >= criteria.stock_min_revenue_growth:
        score += 0.25
    elif revenue_growth >= criteria.stock_min_revenue_growth * 0.7:
        score += 0.125
    max_score += 0.25

    # Debt management (20% weight)
    debt_to_equity = data.get("debt_to_equity", 0.5)
    if debt_to_equity <= criteria.stock_max_debt_to_equity:
        score += 0.20
    elif debt_to_equity <= criteria.stock_max_debt_to_equity * 1.5:
        score += 0.10
    max_score += 0.20

    # Market cap/Liquidity (15% weight)
    market_cap = data.get("market_cap", 0)
    if market_cap >= criteria.stock_min_market_cap:
        score += 0.15
    elif market_cap >= criteria.stock_min_market_cap * 0.5:
        score += 0.075
    max_score += 0.15

    # Free cash flow (15% weight)
    fcf_positive = data.get("fcf_positive", False)
    fcf_growing = data.get("fcf_growing", False)
    if fcf_positive and fcf_growing:
        score += 0.15
    elif fcf_positive:
        score += 0.075
    max_score += 0.15

    return min(score / max_score if max_score > 0 else 0.5, 1.0)


def score_crypto_fundamentals(data: dict[str, Any], criteria: ScoringCriteria) -> float:
    """Score cryptocurrency fundamental characteristics."""
    score = 0.0
    max_score = 0.0

    # Market cap (30% weight)
    market_cap = data.get("market_cap", 0)
    if market_cap >= criteria.crypto_min_market_cap:
        score += 0.30
    elif market_cap >= criteria.crypto_min_market_cap * 0.5:
        score += 0.15
    max_score += 0.30

    # Daily volume (25% weight)
    daily_volume = data.get("daily_volume", 0)
    if daily_volume >= criteria.crypto_min_daily_volume:
        score += 0.25
    elif daily_volume >= criteria.crypto_min_daily_volume * 0.5:
        score += 0.125
    max_score += 0.25

    # Age/Maturity (20% weight)
    age_months = data.get("age_months", 0)
    if age_months >= criteria.crypto_min_age_months:
        score += 0.20
    elif age_months >= criteria.crypto_min_age_months * 0.7:
        score += 0.10
    max_score += 0.20

    # Institutional adoption (15% weight)
    institutional_adoption = data.get("institutional_adoption", False)
    if institutional_adoption:
        score += 0.15
    max_score += 0.15

    # Utility/Use case (10% weight)
    real_utility = data.get("real_utility", False)
    if real_utility:
        score += 0.10
    max_score += 0.10

    return min(score / max_score if max_score > 0 else 0.5, 1.0)


def calculate_technical_score(symbol: str, asset_type: str, data: dict[str, Any], regime: MarketRegime) -> float:
    """Calculate technical analysis score."""
    # Simplified technical scoring - in production would use actual technical indicators
    try:
        momentum = data.get("momentum_score", 0.5)
        trend_strength = data.get("trend_strength", 0.5)
        volatility_score = data.get("volatility_score", 0.5)

        # Adjust weights based on market regime
        if regime.regime_type == "volatile":
            # Emphasize stability in volatile markets
            technical_score = momentum * 0.3 + trend_strength * 0.3 + volatility_score * 0.4
        else:
            # Standard weighting
            technical_score = momentum * 0.4 + trend_strength * 0.4 + volatility_score * 0.2

        return float(min(max(technical_score, 0.0), 1.0))

    except Exception:
        return 0.5


def calculate_quality_score(symbol: str, asset_type: str, data: dict[str, Any], criteria: ScoringCriteria) -> float:
    """Calculate quality/governance score."""
    try:
        # Asset-specific quality metrics
        if asset_type == "etf":
            issuer_quality = data.get("issuer_reputation", 0.7)
            regulatory_compliance = data.get("regulatory_compliance", 0.8)
            transparency = data.get("transparency_score", 0.7)
            quality_score = issuer_quality * 0.4 + regulatory_compliance * 0.3 + transparency * 0.3

        elif asset_type == "stock":
            management_quality = data.get("management_quality", 0.7)
            governance_score = data.get("governance_score", 0.7)
            competitive_moat = data.get("competitive_moat", 0.6)
            quality_score = management_quality * 0.3 + governance_score * 0.3 + competitive_moat * 0.4

        elif asset_type == "crypto":
            team_quality = data.get("team_quality", 0.6)
            development_activity = data.get("development_activity", 0.6)
            community_strength = data.get("community_strength", 0.6)
            quality_score = team_quality * 0.4 + development_activity * 0.3 + community_strength * 0.3

        else:
            quality_score = 0.5

        return float(min(max(quality_score, 0.0), 1.0))

    except Exception:
        return 0.5


def calculate_risk_score(symbol: str, asset_type: str, data: dict[str, Any], regime: MarketRegime) -> float:
    """Calculate risk-adjusted score (higher is better)."""
    try:
        # Base risk assessment
        volatility = data.get("volatility", 0.2)
        beta = data.get("beta", 1.0)
        max_drawdown = data.get("max_drawdown", 0.2)

        # Calculate risk penalty
        volatility_penalty = min(volatility / 0.3, 1.0)  # Normalize to 30% volatility
        beta_penalty = abs(beta - 1.0) / 2.0  # Penalty for high beta
        drawdown_penalty = min(max_drawdown / 0.5, 1.0)  # Normalize to 50% drawdown

        # Adjust for market regime
        if regime.market_stress_level == "high":
            # Penalize risk more in high stress
            risk_penalty = (volatility_penalty * 0.4 + beta_penalty * 0.3 + drawdown_penalty * 0.3) * 1.2
        else:
            risk_penalty = volatility_penalty * 0.4 + beta_penalty * 0.3 + drawdown_penalty * 0.3

        # Convert penalty to score (1 - penalty)
        risk_score = max(1.0 - risk_penalty, 0.0)

        return float(risk_score)

    except Exception:
        return 0.5


def get_scoring_weights(asset_type: str, regime: MarketRegime) -> dict[str, float]:
    """Get scoring weights based on asset type and market regime."""
    base_weights = {
        "etf": {"fundamental": 0.4, "technical": 0.2, "quality": 0.3, "risk": 0.1},
        "stock": {"fundamental": 0.35, "technical": 0.25, "quality": 0.25, "risk": 0.15},
        "crypto": {"fundamental": 0.3, "technical": 0.3, "quality": 0.2, "risk": 0.2},
    }

    weights = base_weights.get(asset_type, base_weights["stock"])

    # Adjust weights based on market regime
    if regime.market_stress_level == "high":
        # Emphasize quality and risk in stressed markets
        weights["quality"] += 0.1
        weights["risk"] += 0.1
        weights["technical"] -= 0.1
        weights["fundamental"] -= 0.1

    # Ensure weights sum to 1.0
    total = sum(weights.values())
    return {k: v / total for k, v in weights.items()}
