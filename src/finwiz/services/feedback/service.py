"""
Main Feedback Learning Service.

Orchestrates the feedback learning system using modular components.
"""

from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

from finwiz.schemas.feedback import (
    CriteriaAdjustment,
    FeedbackSummary,
    LearningConfiguration,
    LearningMetrics,
    PerformanceFeedback,
    UserFeedback,
)
from finwiz.schemas.investment_discovery import APlusCriteria
from finwiz.services.feedback.analytics import FeedbackAnalytics
from finwiz.services.feedback.criteria import CriteriaAdjustment as CriteriaAdjuster
from finwiz.services.feedback.insights import FeedbackInsights
from finwiz.services.feedback.storage import FeedbackStorage
from finwiz.tools.logger import get_logger
from finwiz.utils.monitoring import monitor_performance

logger = get_logger(__name__)


class FeedbackLearningService:
    """
    Main service for collecting feedback and implementing learning mechanisms.

    This service improves A+ investment discovery over time through feedback analysis.
    """

    def __init__(self, config: LearningConfiguration | None = None) -> None:
        """Initialize the feedback learning service."""
        self.config = config or LearningConfiguration()

        # Initialize storage
        feedback_path = Path("data/feedback")
        performance_path = Path("data/performance")
        self.storage = FeedbackStorage(feedback_path, performance_path)

        # Initialize components
        self.analytics = FeedbackAnalytics()
        self.insights = FeedbackInsights()
        self.criteria_adjuster = CriteriaAdjuster()

        # Learning state
        self._last_adjustment_date: datetime | None = None

    @monitor_performance("feedback_service.collect_user_feedback")
    async def collect_user_feedback(self, feedback: UserFeedback) -> str:
        """Collect user feedback on A+ recommendations."""
        try:
            feedback_id = await self.storage.save_user_feedback(feedback)

            # Check if learning should be triggered
            await self._check_learning_trigger()

            logger.info(f"Collected user feedback for {feedback.symbol}: {feedback.outcome.value}")
            return feedback_id

        except Exception as e:
            logger.error(f"Failed to collect user feedback: {str(e)}")
            raise

    @monitor_performance("feedback_service.record_performance_outcome")
    async def record_performance_outcome(self, performance: PerformanceFeedback) -> str:
        """Record performance outcome for an accepted recommendation."""
        try:
            performance_id = await self.storage.save_performance_feedback(performance)

            logger.info(f"Recorded performance for {performance.symbol}: {performance.performance_outcome.value}")
            return performance_id

        except Exception as e:
            logger.error(f"Failed to record performance outcome: {str(e)}")
            raise

    @monitor_performance("feedback_service.analyze_feedback_patterns")
    async def analyze_feedback_patterns(self, days_back: int = 90) -> FeedbackSummary:
        """Analyze feedback patterns to identify insights and improvement opportunities."""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)

            # Load feedback data
            user_feedback = await self.storage.load_feedback_for_period(start_date, end_date)
            performance_feedback = await self.storage.load_performance_for_period(start_date, end_date)

            # Calculate metrics using analytics module
            acceptance_by_asset = self.analytics.calculate_acceptance_by_asset(user_feedback)
            acceptance_by_grade = self.analytics.calculate_acceptance_by_grade(user_feedback)
            acceptance_trends = self.analytics.calculate_acceptance_trends(user_feedback)
            performance_by_asset = self.analytics.calculate_performance_by_asset(performance_feedback)

            # Generate insights
            insights = self.insights.generate_insights(user_feedback, performance_feedback)
            success_patterns = self.insights.identify_success_patterns(user_feedback, performance_feedback)

            # Assess data quality and confidence
            data_quality_score = self.insights.assess_data_quality(user_feedback, performance_feedback)
            confidence_in_insights = self.insights.calculate_confidence_in_insights(user_feedback, performance_feedback)

            # Create summary
            summary = FeedbackSummary(
                analysis_period_start=start_date,
                analysis_period_end=end_date,
                total_feedback_count=len(user_feedback),
                total_performance_records=len(performance_feedback),
                acceptance_by_asset_type=acceptance_by_asset,
                acceptance_by_grade=acceptance_by_grade,
                acceptance_trends=acceptance_trends,
                performance_by_asset_type=performance_by_asset,
                key_insights=insights,
                success_patterns=success_patterns,
                data_quality_score=data_quality_score,
                confidence_in_insights=confidence_in_insights,
                top_performers=self.analytics.identify_top_performers(performance_feedback),
                underperformers=self.analytics.identify_underperformers(performance_feedback),
            )

            logger.info(f"Analyzed {len(user_feedback)} feedback records and {len(performance_feedback)} performance records")
            return summary

        except Exception as e:
            logger.error(f"Failed to analyze feedback patterns: {str(e)}")
            raise

    @monitor_performance("feedback_service.get_learning_metrics")
    async def get_learning_metrics(self, days_back: int = 30) -> LearningMetrics:
        """Get comprehensive learning system metrics."""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)

            # Load data
            user_feedback = await self.storage.load_feedback_for_period(start_date, end_date)
            performance_feedback = await self.storage.load_performance_for_period(start_date, end_date)

            # Calculate metrics
            total_recommendations = len(user_feedback)
            acceptance_rate = self.analytics.calculate_acceptance_rate(user_feedback)
            rejection_rate = 1.0 - acceptance_rate
            # Use pandas Series for vectorized counting
            outcomes_series = pd.Series([f.outcome is not None for f in user_feedback])
            recommendations_with_outcomes = outcomes_series.sum()
            outperformance_rate = self.analytics.calculate_outperformance_rate(performance_feedback)

            # Calculate user satisfaction using pandas Series.mean()
            confidence_ratings = [f.confidence_rating for f in user_feedback if f.confidence_rating]
            avg_confidence = pd.Series(confidence_ratings).mean() if confidence_ratings else 0.0

            # Calculate asset-specific metrics
            etf_metrics = self.insights.calculate_asset_metrics(user_feedback, performance_feedback, "etf")
            stock_metrics = self.insights.calculate_asset_metrics(user_feedback, performance_feedback, "stock")
            crypto_metrics = self.insights.calculate_asset_metrics(user_feedback, performance_feedback, "crypto")

            return LearningMetrics(
                evaluation_period_start=start_date,
                evaluation_period_end=end_date,
                total_recommendations=total_recommendations,
                acceptance_rate=acceptance_rate,
                rejection_rate=rejection_rate,
                recommendations_with_outcomes=recommendations_with_outcomes,
                outperformance_rate=outperformance_rate,
                average_confidence_rating=avg_confidence,
                etf_specific_metrics=etf_metrics,
                stock_specific_metrics=stock_metrics,
                crypto_specific_metrics=crypto_metrics,
            )

        except Exception as e:
            logger.error(f"Failed to get learning metrics: {str(e)}")
            raise

    async def adjust_criteria_based_on_feedback(self, current_criteria: APlusCriteria) -> CriteriaAdjustment | None:
        """Adjust A+ criteria based on recent feedback patterns."""
        try:
            # Analyze recent feedback
            feedback_summary = await self.analyze_feedback_patterns(days_back=90)

            # Check if adjustment is needed
            if not self.criteria_adjuster.should_adjust_criteria(feedback_summary):
                logger.info("No criteria adjustment needed based on current feedback")
                return None

            # Generate new criteria
            new_criteria = self.criteria_adjuster.adjust_criteria_based_on_feedback(current_criteria, feedback_summary)

            # Validate adjustment
            if not self.criteria_adjuster.validate_criteria_adjustment(current_criteria, new_criteria):
                logger.warning("Criteria adjustment validation failed")
                return None

            # Backtest adjustment
            backtest_results = await self.criteria_adjuster.backtest_criteria_adjustment(new_criteria)

            # Create adjustment record
            adjustment = CriteriaAdjustment(
                old_criteria=current_criteria,
                new_criteria=new_criteria,
                adjustment_reason=self.criteria_adjuster.generate_adjustment_reason(feedback_summary),
                expected_improvement=self.criteria_adjuster.calculate_expected_improvement(feedback_summary),
                backtest_results=backtest_results,
                feedback_summary=feedback_summary,
            )

            self._last_adjustment_date = datetime.now()
            logger.info(f"Generated criteria adjustment: {adjustment.adjustment_reason}")
            return adjustment

        except Exception as e:
            logger.error(f"Failed to adjust criteria: {str(e)}")
            raise

    # Private helper methods
    async def _check_learning_trigger(self) -> None:
        """Check if learning should be triggered based on feedback volume."""
        try:
            if self._is_adjustment_due():
                logger.info("Learning trigger activated - criteria adjustment may be due")
        except Exception as e:
            logger.error(f"Failed to check learning trigger: {str(e)}")

    def _is_adjustment_due(self) -> bool:
        """Check if criteria adjustment is due based on timing."""
        if self._last_adjustment_date is None:
            return True

        days_since_last = (datetime.now() - self._last_adjustment_date).days
        return days_since_last >= self.config.adjustment_frequency_days


# Global service instance
_feedback_service: FeedbackLearningService | None = None


def get_feedback_service(config: LearningConfiguration | None = None) -> FeedbackLearningService:
    """Get the global feedback learning service instance."""
    global _feedback_service
    if _feedback_service is None:
        _feedback_service = FeedbackLearningService(config)
    return _feedback_service
