"""
Scoring package for A+ Investment Scoring Tool.

This package contains scoring algorithms and criteria evaluators for
comprehensive investment analysis.
"""

from finwiz.tools.scoring.scoring_algorithms import (
    calculate_fundamental_score,
    calculate_quality_score,
    calculate_risk_score,
    calculate_technical_score,
    get_scoring_weights,
    score_crypto_fundamentals,
    score_etf_fundamentals,
    score_stock_fundamentals,
)
from finwiz.tools.scoring.scoring_criteria import (
    analyze_strengths_weaknesses,
    assess_market_regime,
    calculate_confidence_level,
    generate_a_plus_rationale,
    get_dynamic_criteria,
)

__all__ = [
    # Scoring algorithms
    "calculate_fundamental_score",
    "calculate_technical_score",
    "calculate_quality_score",
    "calculate_risk_score",
    "get_scoring_weights",
    "score_etf_fundamentals",
    "score_stock_fundamentals",
    "score_crypto_fundamentals",
    # Criteria evaluators
    "assess_market_regime",
    "get_dynamic_criteria",
    "analyze_strengths_weaknesses",
    "generate_a_plus_rationale",
    "calculate_confidence_level",
]
