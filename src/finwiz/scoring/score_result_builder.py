"""Score Result Builder for Deep Analysis.

Handles grade assignment, recommendations, and result building.
Extracted from deep_analysis_scorer.py for single responsibility.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Literal

from finwiz.flow_state import DeepAnalysisResult
from finwiz.scoring.scoring_thresholds import ScoringThresholds, get_thresholds

if TYPE_CHECKING:
    from finwiz.schemas.data_lineage import DataLineage
    from finwiz.utils.data_quality_metrics import DataQualityMetrics

logger = logging.getLogger(__name__)


class ScoreResultBuilder:
    """Builds final DeepAnalysisResult with grades and recommendations."""

    def __init__(self, thresholds: ScoringThresholds | None = None) -> None:
        """Initialize with scoring thresholds."""
        self.thresholds = thresholds or get_thresholds()
        self.logger = logger

    def build_result(
        self,
        ticker: str,
        asset_class: str,
        composite_score: float,
        scores: dict[str, Any],
        data: dict[str, Any],
        lineage_tracker: DataLineage,
        data_quality_metrics: DataQualityMetrics,
    ) -> DeepAnalysisResult:
        """
        Build final DeepAnalysisResult from calculated scores.

        Args:
            ticker: Asset ticker symbol
            asset_class: Asset class (stock, etf, crypto)
            composite_score: Weighted composite score
            scores: Dictionary with component scores and details
            data: Dictionary containing all analysis data
            lineage_tracker: Data lineage tracker
            data_quality_metrics: Data quality metrics tracker

        Returns:
            Complete DeepAnalysisResult
        """
        # Assign grade and recommendation
        grade = self.assign_grade(composite_score)

        # Track grade assignment in lineage
        lineage_tracker.add_calculation(
            step_id="grade_assignment",
            step_name="grade",
            inputs={"composite_score": composite_score},
            calculation="Grade assignment based on composite score",
            formula=f"grading_scale[{composite_score:.3f}]",
            output=grade,
            metadata={
                "grading_scale": {
                    self.thresholds.grade_a_plus: "A+",
                    self.thresholds.grade_a: "A",
                    self.thresholds.grade_b: "B",
                    self.thresholds.grade_c: "C",
                    self.thresholds.grade_d: "D",
                    0.0: "F",
                }
            },
        )

        recommendation = self.generate_recommendation(composite_score, grade)
        confidence = self._calculate_confidence(
            scores["fundamental_score"],
            scores["technical_score"],
            scores["risk_score"],
            data,
        )
        rationale = self.generate_rationale(
            ticker,
            asset_class,
            composite_score,
            grade,
            scores["fundamental_details"],
            scores["technical_details"],
            scores["risk_details"],
        )

        # Get data quality summary
        data_quality_summary = data_quality_metrics.get_summary()

        # Log data quality metrics
        quality_level = data_quality_summary["quality_level"]
        field_tracking = data_quality_summary.get("field_tracking", {})
        self.logger.info(
            f"📊 Data quality for {ticker}: "
            f"completeness={data_quality_summary['completeness_score']:.1%}, "
            f"quality={data_quality_summary['quality_score']:.1%}, "
            f"calculated={field_tracking.get('calculated', 0)}/{field_tracking.get('total_expected', 0)} fields"
        )

        if quality_level == "low":
            self.logger.warning(
                f"⚠️ Low data quality for {ticker}: completeness={data_quality_summary['completeness_score']:.1%}, quality={data_quality_summary['quality_score']:.1%}"
            )

        # Finalize lineage with final values
        lineage_tracker.final_values = {
            "composite_score": composite_score,
            "grade": grade,
            "recommendation": recommendation,
            "fundamental_score": scores["fundamental_score"],
            "technical_score": scores["technical_score"],
            "risk_score": scores["risk_score"],
        }

        result = DeepAnalysisResult(
            ticker=ticker,
            asset_class=asset_class,
            crew_name="python_scorer",
            composite_score=composite_score,
            grade=grade,
            recommendation=recommendation,
            rationale=rationale,
            risk_details=scores["risk_details"],
            fundamental_score=scores["fundamental_score"],
            technical_score=scores["technical_score"],
            risk_score=scores["risk_score"],
            fundamental_details=scores["fundamental_details"],
            technical_details=scores["technical_details"],
            data_freshness_hours=0.0,
            confidence_level=confidence,
            warnings=[],
            cached=False,
            data_quality=data_quality_summary,
            lineage=lineage_tracker.model_dump(),
        )

        # Log successful scoring with data quality info
        self.logger.info(
            f"✅ Python scoring completed for {ticker}: "
            f"Grade {grade} ({composite_score:.3f}), "
            f"Recommendation {recommendation} ({confidence:.1%} confidence), "
            f"Quality: {quality_level} ({data_quality_summary['completeness_score']:.1%} complete)"
        )

        return result

    def assign_grade(self, composite_score: float) -> str:
        """
        Assign letter grade based on composite score using configured thresholds.

        Matches official grading system in grading_system.py:
        - A+: >= 95%
        - A:  >= 85%
        - B+: >= 80%
        - B:  >= 75%
        - C+: >= 70%
        - C:  >= 65%
        - D:  >= 50%
        - F:  < 50%

        Args:
            composite_score: Composite score (0.0 to 1.0)

        Returns:
            Letter grade (A+, A, B+, B, C+, C, D, F)
        """
        if composite_score >= self.thresholds.grade_a_plus:
            return "A+"
        elif composite_score >= self.thresholds.grade_a:
            return "A"
        elif composite_score >= self.thresholds.grade_b_plus:
            return "B+"
        elif composite_score >= self.thresholds.grade_b:
            return "B"
        elif composite_score >= self.thresholds.grade_c_plus:
            return "C+"
        elif composite_score >= self.thresholds.grade_c:
            return "C"
        elif composite_score >= self.thresholds.grade_d:
            return "D"
        else:
            return "F"

    def generate_recommendation(self, composite_score: float, grade: str) -> Literal["BUY", "HOLD", "SELL"]:
        """
        Generate investment recommendation based on composite score.

        Args:
            composite_score: Composite score (0.0 to 1.0)
            grade: Letter grade

        Returns:
            Investment recommendation
        """
        if composite_score >= self.thresholds.buy_threshold:
            return "BUY"
        elif composite_score <= self.thresholds.sell_threshold:
            return "SELL"
        else:
            return "HOLD"

    def generate_rationale(
        self,
        ticker: str,
        asset_class: str,
        composite_score: float,
        grade: str,
        fundamental_details: dict[str, Any],
        technical_details: dict[str, Any],
        risk_details: dict[str, Any],
    ) -> str:
        """
        Generate template-based rationale for the recommendation.

        Args:
            ticker: Asset ticker
            asset_class: Asset class
            composite_score: Composite score
            grade: Letter grade
            fundamental_details: Fundamental analysis details
            technical_details: Technical analysis details
            risk_details: Risk analysis details

        Returns:
            Detailed rationale string
        """
        # Start with overall assessment
        rationale_parts = [f"{ticker} receives a {grade} grade with a composite score of {composite_score:.2f}."]

        # Fundamental analysis summary
        fund_score = fundamental_details.get("fundamental_score", 0.5)
        rationale_parts.append(self._get_fundamental_rationale(asset_class, fund_score, fundamental_details))

        # Technical analysis summary
        tech_score = technical_details.get("technical_score", 0.5)
        rsi = technical_details.get("rsi", 50.0)
        trend = technical_details.get("trend_direction", "sideways")
        rationale_parts.append(f"Technical analysis (score: {tech_score:.2f}) indicates {trend} trend with RSI at {rsi:.1f}.")

        # Risk assessment summary
        risk_score = risk_details.get("risk_score", 0.5)
        volatility = risk_details.get("volatility", 0.20)
        max_dd = risk_details.get("max_drawdown", -0.20)
        rationale_parts.append(f"Risk assessment (score: {risk_score:.2f}) shows {volatility:.1%} volatility and maximum drawdown of {max_dd:.1%}.")

        # Recommendation rationale
        rationale_parts.append(self._get_recommendation_rationale(composite_score))

        return " ".join(rationale_parts)

    def _get_fundamental_rationale(self, asset_class: str, fund_score: float, fundamental_details: dict[str, Any]) -> str:
        """Generate fundamental-specific rationale based on asset class."""
        if asset_class == "stock":
            roe = fundamental_details.get("roe", 0.0)
            debt_equity = fundamental_details.get("debt_to_equity", 1.0)
            growth = fundamental_details.get("revenue_growth", 0.0)
            return f"Fundamental analysis (score: {fund_score:.2f}) shows ROE of {roe:.1%}, debt-to-equity of {debt_equity:.2f}, and revenue growth of {growth:.1%}."
        elif asset_class == "etf":
            expense = fundamental_details.get("expense_ratio", 1.0)
            tracking = fundamental_details.get("tracking_error", None)
            tracking_available = fundamental_details.get("tracking_error_available", False)
            if tracking_available and tracking is not None:
                return f"Fundamental analysis (score: {fund_score:.2f}) shows expense ratio of {expense:.2%} and tracking error of {tracking:.2%}."
            else:
                return f"Fundamental analysis (score: {fund_score:.2f}) shows expense ratio of {expense:.2%}. Note: Tracking error data not available for this ETF."
        elif asset_class == "crypto":
            market_cap = fundamental_details.get("market_cap", 0.0)
            volume = fundamental_details.get("volume_24h", 0.0)
            return f"Fundamental analysis (score: {fund_score:.2f}) shows market cap of ${market_cap / 1e9:.1f}B and 24h volume of ${volume / 1e6:.0f}M."
        return f"Fundamental analysis (score: {fund_score:.2f})."

    def _get_recommendation_rationale(self, composite_score: float) -> str:
        """Generate recommendation-specific rationale."""
        if composite_score >= self.thresholds.buy_threshold:
            return "Strong fundamentals, favorable technical indicators, and manageable risk profile support a BUY recommendation."
        elif composite_score <= self.thresholds.sell_threshold:
            return "Weak fundamentals, unfavorable technical setup, or elevated risk profile warrant a SELL recommendation."
        else:
            return "Mixed signals across fundamental, technical, and risk factors suggest a HOLD recommendation pending further developments."

    def _calculate_confidence(
        self,
        fundamental_score: float,
        technical_score: float,
        risk_score: float,
        data: dict[str, Any],
    ) -> float:
        """Calculate confidence level based on data quality and score consistency."""
        # Base confidence from score consistency
        scores = [fundamental_score, technical_score, risk_score]
        score_std = (sum((s - sum(scores) / 3) ** 2 for s in scores) / 3) ** 0.5

        # Lower standard deviation = higher confidence
        consistency_confidence = max(0.5, 1.0 - score_std * 2)

        # Data quality confidence (check for missing key metrics)
        data_quality = 1.0
        key_fields = ["current_price", "volatility", "rsi"]
        missing_fields = sum(1 for field in key_fields if field not in data or data[field] is None)
        data_quality -= missing_fields * 0.1

        # Combined confidence
        return float(min(1.0, max(0.3, consistency_confidence * data_quality)))

    def is_quality_company(self, fundamental_score: float, fundamental_details: dict[str, Any]) -> bool:
        """
        Detect if company qualifies as "quality" for adaptive weights.

        Quality criteria (stocks):
        - High fundamental score (>=0.80 / 80%)
        - Excellent ROE (>=20%)
        - Low debt (debt/equity <=0.5)
        - Strong margins (>=15%)

        Args:
            fundamental_score: Overall fundamental score
            fundamental_details: Detailed fundamental metrics

        Returns:
            True if company qualifies as quality
        """
        # Require strong fundamental score first
        if fundamental_score < 0.80:
            return False

        # Stock-specific quality checks
        roe = fundamental_details.get("roe", 0.0)
        debt_to_equity = fundamental_details.get("debt_to_equity", 999)
        profit_margin = fundamental_details.get("profit_margin", 0.0)

        # Quality thresholds
        has_high_roe = roe >= 0.20
        has_low_debt = debt_to_equity <= 0.5
        has_strong_margins = profit_margin >= 0.15

        # Need at least 2 out of 3 quality indicators
        quality_indicators = sum([has_high_roe, has_low_debt, has_strong_margins])
        return bool(quality_indicators >= 2)

    def create_error_result(self, ticker: str, asset_class: str, error_msg: str) -> DeepAnalysisResult:
        """Create a default result for error cases."""
        # Ensure asset_class is valid for Pydantic validation
        valid_asset_class = asset_class if asset_class in ["stock", "etf", "crypto"] else "stock"

        return DeepAnalysisResult(
            ticker=ticker,
            asset_class=valid_asset_class,
            crew_name="python_scorer",
            composite_score=0.3,
            grade="D",
            recommendation="HOLD",
            rationale=f"Analysis failed due to error: {error_msg}",
            risk_details={"error": 1.0},
            fundamental_score=0.3,
            technical_score=0.3,
            risk_score=0.3,
            data_freshness_hours=0.0,
            confidence_level=0.1,
            warnings=[f"Analysis failed: {error_msg}"],
            cached=False,
        )
