"""
Feedback Insights Module.

Generates insights and patterns from feedback analysis.
"""

import numpy as np
import pandas as pd

from finwiz.schemas.feedback import PerformanceFeedback, PerformanceOutcome, RecommendationOutcome, UserFeedback
from finwiz.services.feedback.analytics import FeedbackAnalytics


class FeedbackInsights:
    """Generates insights from feedback data."""

    @staticmethod
    def generate_insights(user_feedback: list[UserFeedback], performance_feedback: list[PerformanceFeedback]) -> list[str]:
        """Generate key insights from feedback analysis."""
        insights = []

        if user_feedback:
            # Use pandas Series for vectorized calculation
            acceptance_series = pd.Series([f.outcome == RecommendationOutcome.ACCEPTED for f in user_feedback])
            acceptance_rate = acceptance_series.mean()
            insights.append(f"Overall acceptance rate: {acceptance_rate:.1%}")

            # Asset type insights
            by_asset = FeedbackAnalytics.calculate_acceptance_by_asset(user_feedback)
            best_asset = max(by_asset.items(), key=lambda x: x[1]) if by_asset else None
            if best_asset:
                insights.append(f"Best performing asset type: {best_asset[0]} ({best_asset[1]:.1%} acceptance)")

        if performance_feedback:
            # Use pandas Series for vectorized calculations
            outperformance_series = pd.Series([p.performance_outcome == PerformanceOutcome.OUTPERFORMED for p in performance_feedback])
            outperformance_rate = outperformance_series.mean()
            insights.append(f"Outperformance rate: {outperformance_rate:.1%}")

            grade_maintenance_series = pd.Series([p.grade_maintained for p in performance_feedback])
            grade_maintenance = grade_maintenance_series.mean()
            insights.append(f"A+ grade maintenance rate: {grade_maintenance:.1%}")

        return insights

    @staticmethod
    def identify_success_patterns(user_feedback: list[UserFeedback], performance_feedback: list[PerformanceFeedback]) -> list[str]:
        """Identify patterns in successful recommendations."""
        patterns = []

        # Successful recommendations (accepted and outperformed)
        successful_symbols = set()
        for p in performance_feedback:
            if p.performance_outcome == PerformanceOutcome.OUTPERFORMED:
                successful_symbols.add(p.symbol)

        successful_feedback = [f for f in user_feedback if f.symbol in successful_symbols and f.outcome == RecommendationOutcome.ACCEPTED]

        if successful_feedback:
            # Analyze score patterns using pandas Series
            scores_series = pd.Series([f.recommended_score for f in successful_feedback])
            avg_score = scores_series.mean()
            patterns.append(f"Successful recommendations average score: {avg_score:.3f}")

        # Analyze grade patterns
        if performance_feedback:
            grade_maintained_count = sum(1 for p in performance_feedback if p.grade_maintained)
            grade_maintenance_rate = grade_maintained_count / len(performance_feedback)
            patterns.append(f"A+ grade maintenance rate: {grade_maintenance_rate:.1%}")

        # Analyze timing patterns
        if successful_feedback:
            holding_periods = []
            for f in successful_feedback:
                matching_perf = next((p for p in performance_feedback if p.symbol == f.symbol), None)
                if matching_perf:
                    holding_periods.append(matching_perf.holding_period_days)

            if holding_periods:
                # Use pandas Series for vectorized calculation
                holding_series = pd.Series(holding_periods)
                avg_holding = holding_series.mean()
                patterns.append(f"Successful recommendations average holding period: {avg_holding:.1f} days")

        return patterns

    @staticmethod
    def assess_data_quality(user_feedback: list[UserFeedback], performance_feedback: list[PerformanceFeedback]) -> float:
        """Assess the quality of feedback data collected."""
        if not user_feedback:
            return 0.0

        quality_score = 0.0

        # Check completeness of feedback
        complete_feedback = sum(1 for f in user_feedback if f.reasons and f.confidence_rating > 0)
        completeness_score = complete_feedback / len(user_feedback)
        quality_score += completeness_score * 0.4

        # Check performance data availability
        feedback_with_performance = sum(1 for f in user_feedback if any(p.original_recommendation_id == f.recommendation_id for p in performance_feedback))
        performance_coverage = feedback_with_performance / len(user_feedback)
        quality_score += performance_coverage * 0.3

        # Check recency of data
        from datetime import datetime

        recent_feedback = sum(1 for f in user_feedback if (datetime.now() - f.timestamp).days <= 30)
        recency_score = recent_feedback / len(user_feedback)
        quality_score += recency_score * 0.3

        return min(quality_score, 1.0)

    @staticmethod
    def calculate_confidence_in_insights(user_feedback: list[UserFeedback], performance_feedback: list[PerformanceFeedback]) -> float:
        """Calculate confidence level in generated insights."""
        if not user_feedback and not performance_feedback:
            return 0.0

        confidence_factors = []

        # Data volume factor
        total_data_points = len(user_feedback) + len(performance_feedback)
        volume_factor = min(total_data_points / 100, 1.0)  # Normalize to 100 data points
        confidence_factors.append(volume_factor * 0.4)

        # Data quality factor
        quality_factor = FeedbackInsights.assess_data_quality(user_feedback, performance_feedback)
        confidence_factors.append(quality_factor * 0.3)

        # Consistency factor (how consistent are the patterns)
        if user_feedback:
            acceptance_rates = FeedbackAnalytics.calculate_acceptance_by_asset(user_feedback)
            if len(acceptance_rates) > 1:
                rate_values = list(acceptance_rates.values())
                consistency = 1.0 - (np.std(rate_values) / np.mean(rate_values)) if np.mean(rate_values) > 0 else 0.0
                confidence_factors.append(max(0.0, consistency) * 0.3)
            else:
                confidence_factors.append(0.3)

        return sum(confidence_factors)

    @staticmethod
    def calculate_asset_metrics(user_feedback: list[UserFeedback], performance_feedback: list[PerformanceFeedback], asset_type: str) -> dict[str, float]:
        """Calculate metrics for a specific asset type."""
        asset_user_feedback = [f for f in user_feedback if f.asset_type == asset_type]

        # Get performance feedback for this asset type (simplified matching)
        asset_symbols = set(f.symbol for f in asset_user_feedback)
        asset_performance = [p for p in performance_feedback if p.symbol in asset_symbols]

        metrics = {}

        if asset_user_feedback:
            # Use pandas Series for vectorized calculations
            acceptance_series = pd.Series([f.outcome == RecommendationOutcome.ACCEPTED for f in asset_user_feedback])
            metrics["acceptance_rate"] = acceptance_series.mean()

            confidence_ratings = [f.confidence_rating for f in asset_user_feedback if f.confidence_rating]
            metrics["average_confidence"] = pd.Series(confidence_ratings).mean() if confidence_ratings else 0.0

        if asset_performance:
            # Use pandas Series for vectorized calculations
            outperformance_series = pd.Series([p.performance_outcome == PerformanceOutcome.OUTPERFORMED for p in asset_performance])
            metrics["outperformance_rate"] = outperformance_series.mean()

            grade_maintenance_series = pd.Series([p.grade_maintained for p in asset_performance])
            metrics["grade_maintenance_rate"] = grade_maintenance_series.mean()

            alpha_series = pd.Series([p.alpha for p in asset_performance])
            metrics["average_alpha"] = alpha_series.mean()

        return metrics
