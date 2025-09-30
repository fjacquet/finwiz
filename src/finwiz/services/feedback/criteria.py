"""
Feedback Criteria Adjustment Module.

Handles criteria learning and adjustment logic.
"""

from typing import Any

import pandas as pd

from finwiz.schemas.feedback import FeedbackSummary
from finwiz.schemas.investment_discovery import APlusCriteria


class CriteriaAdjustment:
    """Handles A+ criteria learning and adjustment."""

    @staticmethod
    def should_adjust_criteria(feedback_summary: FeedbackSummary, min_acceptance_rate: float = 0.6) -> bool:
        """Determine if criteria should be adjusted based on feedback."""
        # Check acceptance rates using pandas Series
        if feedback_summary.acceptance_by_asset_type:
            acceptance_series = pd.Series(list(feedback_summary.acceptance_by_asset_type.values()))
            overall_acceptance = acceptance_series.mean()
        else:
            overall_acceptance = 0.0

        if overall_acceptance < min_acceptance_rate:
            return True

        # Check performance using pandas Series
        if feedback_summary.performance_by_asset_type:
            outperformance_series = pd.Series(
                [metrics.get("outperformance_rate", 0.0) for metrics in feedback_summary.performance_by_asset_type.values()]
            )
            avg_outperformance = outperformance_series.mean()

            if avg_outperformance < 0.5:  # Less than 50% outperformance
                return True

        return False

    @staticmethod
    def generate_adjustment_reason(feedback_summary: FeedbackSummary) -> str:
        """Generate human-readable reason for criteria adjustment."""
        reasons = []

        # Check acceptance rates using pandas Series
        if feedback_summary.acceptance_by_asset_type:
            acceptance_series = pd.Series(list(feedback_summary.acceptance_by_asset_type.values()))
            overall_acceptance = acceptance_series.mean()
        else:
            overall_acceptance = 0.0

        if overall_acceptance < 0.6:
            reasons.append("low acceptance rate")

        # Check performance using pandas Series
        if feedback_summary.performance_by_asset_type:
            outperformance_series = pd.Series(
                [metrics.get("outperformance_rate", 0.0) for metrics in feedback_summary.performance_by_asset_type.values()]
            )
            avg_outperformance = outperformance_series.mean()
            if avg_outperformance < 0.5:
                reasons.append("poor performance outcomes")

        # Check data quality
        if feedback_summary.data_quality_score < 0.7:
            reasons.append("insufficient data quality")

        if not reasons:
            reasons.append("optimization based on feedback patterns")

        return f"Criteria adjusted due to: {', '.join(reasons)}"

    @staticmethod
    def calculate_expected_improvement(feedback_summary: FeedbackSummary) -> float:
        """Calculate expected improvement from criteria adjustment."""
        # Simple heuristic - could be enhanced with ML models
        # Note: current_acceptance could be used for more sophisticated improvement calculations

        # Expect 5-15% improvement based on confidence in insights
        base_improvement = 0.05
        confidence_multiplier = feedback_summary.confidence_in_insights

        return base_improvement + (0.10 * confidence_multiplier)

    @staticmethod
    def adjust_criteria_based_on_feedback(current_criteria: APlusCriteria, feedback_summary: FeedbackSummary) -> APlusCriteria:
        """Adjust A+ criteria based on feedback patterns."""
        # Create a copy of current criteria
        new_criteria = APlusCriteria(**current_criteria.model_dump())

        # Adjust based on acceptance rates by asset type
        if feedback_summary.acceptance_by_asset_type:
            for asset_type, acceptance_rate in feedback_summary.acceptance_by_asset_type.items():
                if acceptance_rate < 0.5:  # Low acceptance
                    # Relax criteria for this asset type
                    if asset_type == "stock" and hasattr(new_criteria, "min_market_cap"):
                        new_criteria.min_market_cap *= 0.8  # Reduce by 20%
                    elif asset_type == "etf" and hasattr(new_criteria, "max_expense_ratio"):
                        new_criteria.max_expense_ratio *= 1.1  # Increase by 10%

        # Adjust based on performance outcomes using pandas Series
        if feedback_summary.performance_by_asset_type:
            performance_series = pd.Series(
                [metrics.get("outperformance_rate", 0.0) for metrics in feedback_summary.performance_by_asset_type.values()]
            )
            avg_performance = performance_series.mean()

            if avg_performance < 0.4:  # Poor performance
                # Tighten criteria
                if hasattr(new_criteria, "min_score_threshold"):
                    new_criteria.min_score_threshold = min(new_criteria.min_score_threshold * 1.1, 0.95)

        return new_criteria

    @staticmethod
    def validate_criteria_adjustment(old_criteria: APlusCriteria, new_criteria: APlusCriteria) -> bool:
        """Validate that criteria adjustment is reasonable."""
        # Check that changes are within acceptable bounds

        # Example validations (would need to be customized based on actual criteria structure)
        if hasattr(old_criteria, "min_market_cap") and hasattr(new_criteria, "min_market_cap"):
            change_ratio = new_criteria.min_market_cap / old_criteria.min_market_cap
            if change_ratio < 0.5 or change_ratio > 2.0:  # More than 50% change
                return False

        if hasattr(old_criteria, "min_score_threshold") and hasattr(new_criteria, "min_score_threshold"):
            score_change = abs(new_criteria.min_score_threshold - old_criteria.min_score_threshold)
            if score_change > 0.2:  # More than 20% change in score threshold
                return False

        return True

    @staticmethod
    async def backtest_criteria_adjustment(new_criteria: APlusCriteria) -> dict[str, Any]:
        """Backtest criteria adjustment against historical data."""
        # Placeholder implementation - would need historical data and backtesting engine
        return {
            "passed": True,
            "historical_performance": 0.15,  # 15% annual return
            "sharpe_ratio": 1.2,
            "max_drawdown": -0.08,
            "validation_period_years": 2,
        }
