"""
A+ Investment Scoring Tool for proactive discovery of exceptional investment opportunities.

This tool implements comprehensive A+ scoring for ETFs, stocks, and cryptocurrencies
using dynamic criteria that adapt to market conditions. Integrates with the existing
FinWiz grading system to identify investments with A+ potential (score ≥ 0.95).
"""

from datetime import datetime
from typing import Any, Literal

from crewai.tools import BaseTool
from pydantic import BaseModel

# Import schemas from centralized location
from finwiz.schemas.tools import APlusScore, APlusScoringInput
from finwiz.tools.scoring import (
    analyze_strengths_weaknesses,
    assess_market_regime,
    calculate_confidence_level,
    calculate_fundamental_score,
    calculate_quality_score,
    calculate_risk_score,
    calculate_technical_score,
    generate_a_plus_rationale,
    get_dynamic_criteria,
    get_scoring_weights,
)
from finwiz.utils.grading_system import score_to_grade


class APlusScoringTool(BaseTool):
    """
    A+ Investment Scoring Tool for discovering exceptional investment opportunities.

    This tool provides comprehensive A+ scoring for ETFs, stocks, and cryptocurrencies
    using dynamic criteria that adapt to market conditions. It integrates with the
    existing FinWiz grading system to identify investments with A+ potential.

    Key Features:
    - Dynamic criteria adjustment based on market regime
    - Comprehensive scoring across multiple dimensions
    - Integration with existing grading system
    - Detailed rationale and confidence assessment
    """

    name: str = "A+ Investment Scoring Tool"
    description: str = (
        "Comprehensive A+ scoring tool that evaluates ETFs, stocks, and cryptocurrencies "
        "using dynamic criteria adapted to current market conditions. Identifies investments "
        "with A+ potential (score ≥ 0.95) through multi-dimensional analysis."
    )
    args_schema: type[BaseModel] = APlusScoringInput

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the A+ Scoring Tool with caching capabilities."""
        super().__init__(**kwargs)
        self._regime_cache: dict[str, Any] = {}

    def _run(
        self,
        symbol: str,
        asset_type: Literal["etf", "stock", "crypto"],
        fundamental_data: dict[str, Any] | None = None,
        market_context: dict[str, Any] | None = None,
        custom_criteria: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        """Execute A+ scoring analysis."""
        try:
            # Normalize inputs
            symbol = symbol.upper().strip()
            fundamental_data = fundamental_data or {}
            market_context = market_context or {}
            custom_criteria = custom_criteria or {}

            # Get current market regime
            market_regime = assess_market_regime(market_context, self._regime_cache)

            # Get dynamic scoring criteria
            scoring_criteria = get_dynamic_criteria(market_regime, custom_criteria)

            # Calculate component scores
            fundamental_score = calculate_fundamental_score(symbol, asset_type, fundamental_data, scoring_criteria)
            technical_score = calculate_technical_score(symbol, asset_type, fundamental_data, market_regime)
            quality_score = calculate_quality_score(symbol, asset_type, fundamental_data, scoring_criteria)
            risk_score = calculate_risk_score(symbol, asset_type, fundamental_data, market_regime)

            # Calculate composite score with weights
            weights = get_scoring_weights(asset_type, market_regime)
            composite_score = (
                fundamental_score * weights["fundamental"] + technical_score * weights["technical"] + quality_score * weights["quality"] + risk_score * weights["risk"]
            )

            # Generate grade info
            grade_info = score_to_grade(composite_score)

            # Analyze strengths and weaknesses
            strengths, weaknesses = analyze_strengths_weaknesses(
                symbol,
                asset_type,
                fundamental_data,
                {
                    "fundamental": fundamental_score,
                    "technical": technical_score,
                    "quality": quality_score,
                    "risk": risk_score,
                },
            )

            # Generate A+ rationale
            a_plus_rationale = generate_a_plus_rationale(symbol, asset_type, composite_score, strengths, weaknesses, market_regime)

            # Calculate confidence level
            confidence_level = calculate_confidence_level(fundamental_data, market_regime, composite_score)

            # Create A+ score object
            a_plus_score = APlusScore(
                symbol=symbol,
                asset_type=asset_type,
                composite_score=composite_score,
                grade_info=grade_info,
                fundamental_score=fundamental_score,
                technical_score=technical_score,
                quality_score=quality_score,
                risk_score=risk_score,
                strengths=strengths,
                weaknesses=weaknesses,
                a_plus_rationale=a_plus_rationale,
                confidence_level=confidence_level,
                market_regime=market_regime,
                scoring_criteria=scoring_criteria,
                analysis_timestamp=datetime.now(),
            )

            return {
                "symbol": symbol,
                "asset_type": asset_type,
                "a_plus_score": a_plus_score.model_dump(),
                "is_a_plus_candidate": composite_score >= 0.95,
                "grade": grade_info.grade,
                "percentage": grade_info.percentage,
                "recommendation": grade_info.action,
                "analysis_summary": {
                    "composite_score": composite_score,
                    "component_scores": {
                        "fundamental": fundamental_score,
                        "technical": technical_score,
                        "quality": quality_score,
                        "risk": risk_score,
                    },
                    "top_strengths": strengths[:3],
                    "main_concerns": weaknesses[:2],
                    "confidence": confidence_level,
                },
            }

        except Exception as e:
            return {
                "error": f"A+ scoring failed for {symbol}: {str(e)}",
                "symbol": symbol,
                "asset_type": asset_type,
                "composite_score": 0.0,
                "is_a_plus_candidate": False,
            }
