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
from finwiz.schemas.tools import (
    APlusScore,
    APlusScoringInput,
    MarketRegime,
    ScoringCriteria,
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
        self._market_regime_cache = None
        self._cache_timestamp = None

    def _run(
        self,
        symbol: str,
        asset_type: Literal["etf", "stock", "crypto"],
        fundamental_data: dict[str, Any] = None,
        market_context: dict[str, Any] = None,
        custom_criteria: dict[str, float] = None,
    ) -> dict[str, Any]:
        """Execute A+ scoring analysis."""
        try:
            # Normalize inputs
            symbol = symbol.upper().strip()
            fundamental_data = fundamental_data or {}
            market_context = market_context or {}
            custom_criteria = custom_criteria or {}

            # Get current market regime
            market_regime = self._assess_market_regime(market_context)

            # Get dynamic scoring criteria
            scoring_criteria = self._get_dynamic_criteria(market_regime, custom_criteria)

            # Calculate component scores
            fundamental_score = self._calculate_fundamental_score(symbol, asset_type, fundamental_data, scoring_criteria)
            technical_score = self._calculate_technical_score(symbol, asset_type, fundamental_data, market_regime)
            quality_score = self._calculate_quality_score(symbol, asset_type, fundamental_data, scoring_criteria)
            risk_score = self._calculate_risk_score(symbol, asset_type, fundamental_data, market_regime)

            # Calculate composite score with weights
            weights = self._get_scoring_weights(asset_type, market_regime)
            composite_score = (
                fundamental_score * weights["fundamental"] + technical_score * weights["technical"] + quality_score * weights["quality"] + risk_score * weights["risk"]
            )

            # Generate grade info
            grade_info = score_to_grade(composite_score)

            # Analyze strengths and weaknesses
            strengths, weaknesses = self._analyze_strengths_weaknesses(
                symbol,
                asset_type,
                fundamental_data,
                {"fundamental": fundamental_score, "technical": technical_score, "quality": quality_score, "risk": risk_score},
            )

            # Generate A+ rationale
            a_plus_rationale = self._generate_a_plus_rationale(symbol, asset_type, composite_score, strengths, weaknesses, market_regime)

            # Calculate confidence level
            confidence_level = self._calculate_confidence_level(fundamental_data, market_regime, composite_score)

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

    def _assess_market_regime(self, market_context: dict[str, Any]) -> MarketRegime:
        """Assess current market regime from context data."""
        try:
            # Use cached regime if recent (within 1 hour)
            if self._market_regime_cache and self._cache_timestamp and (datetime.now() - self._cache_timestamp).seconds < 3600:
                return self._market_regime_cache

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
                regime_type=regime_type,
                vix_level=vix_level,
                inflation_rate=inflation_rate,
                interest_rate_trend=interest_rate_trend,
                market_stress_level=stress_level,
            )

            # Cache the result
            self._market_regime_cache = regime
            self._cache_timestamp = datetime.now()

            return regime

        except Exception:
            # Return default regime on error
            return MarketRegime()

    def _get_dynamic_criteria(self, market_regime: MarketRegime, custom_criteria: dict[str, float]) -> ScoringCriteria:
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

    def _calculate_fundamental_score(self, symbol: str, asset_type: str, data: dict[str, Any], criteria: ScoringCriteria) -> float:
        """Calculate fundamental analysis score."""
        try:
            if asset_type == "etf":
                return self._score_etf_fundamentals(data, criteria)
            elif asset_type == "stock":
                return self._score_stock_fundamentals(data, criteria)
            elif asset_type == "crypto":
                return self._score_crypto_fundamentals(data, criteria)
            else:
                return 0.5  # Default score for unknown types

        except Exception:
            return 0.5  # Default on error

    def _score_etf_fundamentals(self, data: dict[str, Any], criteria: ScoringCriteria) -> float:
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

    def _score_stock_fundamentals(self, data: dict[str, Any], criteria: ScoringCriteria) -> float:
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

    def _score_crypto_fundamentals(self, data: dict[str, Any], criteria: ScoringCriteria) -> float:
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

    def _calculate_technical_score(self, symbol: str, asset_type: str, data: dict[str, Any], regime: MarketRegime) -> float:
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

            return min(max(technical_score, 0.0), 1.0)

        except Exception:
            return 0.5

    def _calculate_quality_score(self, symbol: str, asset_type: str, data: dict[str, Any], criteria: ScoringCriteria) -> float:
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

            return min(max(quality_score, 0.0), 1.0)

        except Exception:
            return 0.5

    def _calculate_risk_score(self, symbol: str, asset_type: str, data: dict[str, Any], regime: MarketRegime) -> float:
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

            return risk_score

        except Exception:
            return 0.5

    def _get_scoring_weights(self, asset_type: str, regime: MarketRegime) -> dict[str, float]:
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

    def _analyze_strengths_weaknesses(self, symbol: str, asset_type: str, data: dict[str, Any], scores: dict[str, float]) -> tuple[list[str], list[str]]:
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

    def _generate_a_plus_rationale(self, symbol: str, asset_type: str, score: float, strengths: list[str], weaknesses: list[str], regime: MarketRegime) -> str:
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

    def _calculate_confidence_level(self, data: dict[str, Any], regime: MarketRegime, score: float) -> float:
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
