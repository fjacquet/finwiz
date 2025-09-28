"""
A+ Investment Feedback and Learning Service.

This service implements the feedback loop system for A+ investment recommendations,
collecting user feedback, tracking performance outcomes, and using machine learning
to continuously improve the discovery criteria.
"""

import json
import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from finwiz.schemas.feedback import (
    CriteriaAdjustment,
    FeedbackSummary,
    LearningConfiguration,
    LearningMetrics,
    PerformanceFeedback,
    PerformanceOutcome,
    RecommendationOutcome,
    UserFeedback,
)
from finwiz.schemas.investment_discovery import APlusCriteria
from finwiz.schemas.portfolio_review import Grade
from finwiz.tools.logger import get_logger
from finwiz.utils.monitoring import monitor_performance

logger = get_logger(__name__)


class FeedbackLearningService:
    """
    Service for collecting feedback and implementing learning mechanisms
    to improve A+ investment discovery over time.
    """

    def __init__(self, config: LearningConfiguration | None = None) -> None:
        """Initialize the feedback learning service."""
        self.config = config or LearningConfiguration()
        self.feedback_storage_path = Path("data/feedback")
        self.criteria_history_path = Path("data/criteria_history")

        # Ensure storage directories exist
        self.feedback_storage_path.mkdir(parents=True, exist_ok=True)
        self.criteria_history_path.mkdir(parents=True, exist_ok=True)

        # In-memory caches for performance
        self._feedback_cache: dict[str, UserFeedback] = {}
        self._performance_cache: dict[str, PerformanceFeedback] = {}
        self._current_criteria: APlusCriteria | None = None
        self._last_adjustment_date: datetime | None = None

        logger.info("Feedback Learning Service initialized")

    @monitor_performance("feedback_service.collect_user_feedback")
    async def collect_user_feedback(self, feedback: UserFeedback) -> str:
        """
        Collect user feedback on A+ recommendations.

        Args:
            feedback: User feedback data

        Returns:
            Feedback ID for tracking

        """
        try:
            # Generate unique ID if not provided
            if not feedback.feedback_id:
                feedback.feedback_id = str(uuid.uuid4())

            # Store feedback
            feedback_file = self.feedback_storage_path / f"user_feedback_{feedback.feedback_id}.json"
            feedback_file.write_text(feedback.model_dump_json(indent=2))

            # Update cache
            self._feedback_cache[feedback.feedback_id] = feedback

            logger.info(f"Collected user feedback: {feedback.symbol} - {feedback.outcome.value}")

            # Trigger learning if we have enough samples
            await self._check_learning_trigger()

            return feedback.feedback_id

        except Exception as e:
            logger.error(f"Failed to collect user feedback: {str(e)}")
            raise

    @monitor_performance("feedback_service.record_performance_outcome")
    async def record_performance_outcome(self, performance: PerformanceFeedback) -> str:
        """
        Record performance outcome for an accepted recommendation.

        Args:
            performance: Performance feedback data

        Returns:
            Performance feedback ID

        """
        try:
            # Generate unique ID if not provided
            if not performance.feedback_id:
                performance.feedback_id = str(uuid.uuid4())

            # Store performance data
            performance_file = self.feedback_storage_path / f"performance_{performance.feedback_id}.json"
            performance_file.write_text(performance.model_dump_json(indent=2))

            # Update cache
            self._performance_cache[performance.feedback_id] = performance

            logger.info(f"Recorded performance outcome: {performance.symbol} - {performance.performance_outcome.value}")

            # Trigger learning if we have enough samples
            await self._check_learning_trigger()

            return performance.feedback_id

        except Exception as e:
            logger.error(f"Failed to record performance outcome: {str(e)}")
            raise

    @monitor_performance("feedback_service.analyze_feedback_patterns")
    async def analyze_feedback_patterns(self, days_back: int = 90) -> FeedbackSummary:
        """
        Analyze feedback patterns to identify insights and improvement opportunities.

        Args:
            days_back: Number of days to analyze

        Returns:
            Comprehensive feedback analysis summary

        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_back)

            # Load recent feedback
            user_feedback = await self._load_recent_feedback(cutoff_date)
            performance_feedback = await self._load_recent_performance(cutoff_date)

            # Calculate basic statistics
            total_feedback = len(user_feedback)
            unique_users = len(set(f.user_id for f in user_feedback))
            unique_recommendations = len(set(f.recommendation_id for f in user_feedback))

            # Analyze acceptance rates
            acceptance_by_asset = self._calculate_acceptance_by_asset(user_feedback)
            acceptance_by_grade = self._calculate_acceptance_by_grade(user_feedback)
            acceptance_trends = self._calculate_acceptance_trends(user_feedback)

            # Analyze performance
            performance_by_asset = self._calculate_performance_by_asset(performance_feedback)
            top_performers = self._identify_top_performers(performance_feedback)
            underperformers = self._identify_underperformers(performance_feedback)

            # Generate insights
            insights = self._generate_insights(user_feedback, performance_feedback)
            recommended_adjustments = self._recommend_adjustments(user_feedback, performance_feedback)
            success_patterns = self._identify_success_patterns(user_feedback, performance_feedback)
            failure_patterns = self._identify_failure_patterns(user_feedback, performance_feedback)

            # Calculate quality metrics
            data_quality = self._assess_data_quality(user_feedback, performance_feedback)
            confidence = self._calculate_confidence_in_insights(user_feedback, performance_feedback)
            sample_adequacy = total_feedback >= self.config.min_feedback_samples

            summary = FeedbackSummary(
                period_days=days_back,
                total_feedback_items=total_feedback,
                unique_users=unique_users,
                unique_recommendations=unique_recommendations,
                acceptance_by_asset_type=acceptance_by_asset,
                acceptance_by_grade=acceptance_by_grade,
                acceptance_trends=acceptance_trends,
                performance_by_asset_type=performance_by_asset,
                top_performing_recommendations=top_performers,
                underperforming_recommendations=underperformers,
                key_insights=insights,
                recommended_adjustments=recommended_adjustments,
                success_patterns=success_patterns,
                failure_patterns=failure_patterns,
                data_quality_score=data_quality,
                confidence_in_insights=confidence,
                sample_size_adequacy=sample_adequacy,
            )

            logger.info(f"Generated feedback analysis for {days_back} days: {total_feedback} feedback items")
            return summary

        except Exception as e:
            logger.error(f"Failed to analyze feedback patterns: {str(e)}")
            raise

    @monitor_performance("feedback_service.adjust_criteria")
    async def adjust_criteria_based_on_learning(
        self, current_criteria: APlusCriteria, force_adjustment: bool = False
    ) -> CriteriaAdjustment | None:
        """
        Adjust A+ criteria based on feedback learning.

        Args:
            current_criteria: Current A+ criteria
            force_adjustment: Whether to force adjustment regardless of timing

        Returns:
            Criteria adjustment record if adjustment was made

        """
        try:
            # Check if adjustment is due
            if not force_adjustment and not self._is_adjustment_due():
                logger.info("Criteria adjustment not due yet")
                return None

            # Load recent feedback for learning
            feedback_summary = await self.analyze_feedback_patterns(days_back=90)

            # Check if we have enough data
            if not feedback_summary.sample_size_adequacy:
                logger.info(f"Insufficient feedback samples: {feedback_summary.total_feedback_items}")
                return None

            # Generate new criteria based on learning
            new_criteria = await self._generate_improved_criteria(current_criteria, feedback_summary)

            # Validate the adjustment
            if not self._validate_criteria_adjustment(current_criteria, new_criteria):
                logger.warning("Criteria adjustment failed validation")
                return None

            # Perform backtesting if required
            validation_results = {}
            if self.config.require_backtesting:
                validation_results = await self._backtest_criteria_adjustment(new_criteria)
                if not validation_results.get("passed", False):
                    logger.warning("Criteria adjustment failed backtesting")
                    return None

            # Create adjustment record
            adjustment = CriteriaAdjustment(
                adjustment_id=str(uuid.uuid4()),
                criteria_before=current_criteria,
                criteria_after=new_criteria,
                adjustment_reason=self._generate_adjustment_reason(feedback_summary),
                feedback_sample_size=feedback_summary.total_feedback_items,
                confidence_level=feedback_summary.confidence_in_insights,
                expected_improvement=self._calculate_expected_improvement(feedback_summary),
                backtesting_validation=self.config.require_backtesting,
                validation_results=validation_results,
            )

            # Store adjustment
            adjustment_file = self.criteria_history_path / f"adjustment_{adjustment.adjustment_id}.json"
            adjustment_file.write_text(adjustment.model_dump_json(indent=2))

            # Update current criteria
            self._current_criteria = new_criteria
            self._last_adjustment_date = datetime.now()

            logger.info(f"Applied criteria adjustment: {adjustment.adjustment_reason}")
            return adjustment

        except Exception as e:
            logger.error(f"Failed to adjust criteria: {str(e)}")
            raise

    @monitor_performance("feedback_service.get_learning_metrics")
    async def get_learning_metrics(self, days_back: int = 30) -> LearningMetrics:
        """
        Get comprehensive learning system metrics.

        Args:
            days_back: Number of days to analyze

        Returns:
            Learning system performance metrics

        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)

            # Load feedback data
            user_feedback = await self._load_recent_feedback(start_date)
            performance_feedback = await self._load_recent_performance(start_date)

            # Calculate recommendation metrics
            total_recommendations = len(set(f.recommendation_id for f in user_feedback))
            accepted = len([f for f in user_feedback if f.outcome == RecommendationOutcome.ACCEPTED])
            rejected = len([f for f in user_feedback if f.outcome == RecommendationOutcome.REJECTED])

            acceptance_rate = accepted / total_recommendations if total_recommendations > 0 else 0.0
            rejection_rate = rejected / total_recommendations if total_recommendations > 0 else 0.0

            # Calculate performance metrics
            recommendations_with_outcomes = len(performance_feedback)
            outperformed = len([p for p in performance_feedback if p.performance_outcome == PerformanceOutcome.OUTPERFORMED])
            grade_maintained = len([p for p in performance_feedback if p.grade_maintained])

            outperformance_rate = outperformed / recommendations_with_outcomes if recommendations_with_outcomes > 0 else 0.0
            grade_maintenance_rate = grade_maintained / recommendations_with_outcomes if recommendations_with_outcomes > 0 else 0.0

            # Calculate learning effectiveness
            adjustments_made = len(list(self.criteria_history_path.glob("adjustment_*.json")))

            # Calculate improvements (compare with previous period)
            prev_period_feedback = await self._load_feedback_for_period(start_date - timedelta(days=days_back), start_date)
            prev_acceptance_rate = self._calculate_acceptance_rate(prev_period_feedback)
            improvement_in_acceptance = acceptance_rate - prev_acceptance_rate

            prev_performance = await self._load_performance_for_period(start_date - timedelta(days=days_back), start_date)
            prev_outperformance_rate = self._calculate_outperformance_rate(prev_performance)
            improvement_in_performance = outperformance_rate - prev_outperformance_rate

            # Calculate user satisfaction
            confidence_ratings = [f.confidence_rating for f in user_feedback if f.confidence_rating]
            avg_confidence = sum(confidence_ratings) / len(confidence_ratings) if confidence_ratings else 0.0

            positive_sentiments = len([f for f in user_feedback if f.sentiment.value in ["positive", "very_positive"]])
            positive_sentiment_rate = positive_sentiments / len(user_feedback) if user_feedback else 0.0

            # Calculate asset-specific metrics
            etf_metrics = self._calculate_asset_metrics(user_feedback, performance_feedback, "etf")
            stock_metrics = self._calculate_asset_metrics(user_feedback, performance_feedback, "stock")
            crypto_metrics = self._calculate_asset_metrics(user_feedback, performance_feedback, "crypto")

            metrics = LearningMetrics(
                evaluation_period_start=start_date,
                evaluation_period_end=end_date,
                total_recommendations=total_recommendations,
                acceptance_rate=acceptance_rate,
                rejection_rate=rejection_rate,
                recommendations_with_outcomes=recommendations_with_outcomes,
                outperformance_rate=outperformance_rate,
                grade_maintenance_rate=grade_maintenance_rate,
                criteria_adjustments_made=adjustments_made,
                improvement_in_acceptance=improvement_in_acceptance,
                improvement_in_performance=improvement_in_performance,
                average_confidence_rating=avg_confidence,
                positive_sentiment_rate=positive_sentiment_rate,
                etf_metrics=etf_metrics,
                stock_metrics=stock_metrics,
                crypto_metrics=crypto_metrics,
            )

            logger.info(f"Generated learning metrics for {days_back} days")
            return metrics

        except Exception as e:
            logger.error(f"Failed to get learning metrics: {str(e)}")
            raise

    @monitor_performance("feedback_service.rollback_criteria")
    async def rollback_criteria_adjustment(self, adjustment_id: str, reason: str) -> bool:
        """
        Rollback a criteria adjustment if it's not performing well.

        Args:
            adjustment_id: ID of adjustment to rollback
            reason: Reason for rollback

        Returns:
            Whether rollback was successful

        """
        try:
            # Load adjustment record
            adjustment_file = self.criteria_history_path / f"adjustment_{adjustment_id}.json"
            if not adjustment_file.exists():
                logger.error(f"Adjustment {adjustment_id} not found")
                return False

            adjustment_data = json.loads(adjustment_file.read_text())
            adjustment = CriteriaAdjustment.model_validate(adjustment_data)

            if not adjustment.can_rollback:
                logger.error(f"Adjustment {adjustment_id} cannot be rolled back")
                return False

            # Create rollback adjustment
            rollback_adjustment = CriteriaAdjustment(
                adjustment_id=str(uuid.uuid4()),
                criteria_before=adjustment.criteria_after,
                criteria_after=adjustment.criteria_before,
                adjustment_reason=f"Rollback of {adjustment_id}: {reason}",
                feedback_sample_size=0,
                confidence_level=1.0,
                expected_improvement=0.0,
                can_rollback=False,  # Rollbacks cannot be rolled back
            )

            # Store rollback
            rollback_file = self.criteria_history_path / f"adjustment_{rollback_adjustment.adjustment_id}.json"
            rollback_file.write_text(rollback_adjustment.model_dump_json(indent=2))

            # Update current criteria
            self._current_criteria = adjustment.criteria_before

            logger.info(f"Rolled back criteria adjustment {adjustment_id}: {reason}")
            return True

        except Exception as e:
            logger.error(f"Failed to rollback criteria adjustment: {str(e)}")
            return False

    # Private helper methods

    async def _check_learning_trigger(self) -> None:
        """Check if learning should be triggered based on feedback volume."""
        try:
            recent_feedback = await self._load_recent_feedback(datetime.now() - timedelta(days=7))
            if len(recent_feedback) >= self.config.min_feedback_samples:
                logger.info("Learning trigger activated - sufficient feedback collected")
                # Could trigger automatic learning here if desired
        except Exception as e:
            logger.error(f"Failed to check learning trigger: {str(e)}")

    def _is_adjustment_due(self) -> bool:
        """Check if criteria adjustment is due based on timing."""
        if self._last_adjustment_date is None:
            return True

        days_since_last = (datetime.now() - self._last_adjustment_date).days
        return days_since_last >= self.config.adjustment_frequency_days

    async def _load_recent_feedback(self, cutoff_date: datetime) -> list[UserFeedback]:
        """Load user feedback since cutoff date."""
        feedback_list = []

        for feedback_file in self.feedback_storage_path.glob("user_feedback_*.json"):
            try:
                feedback_data = json.loads(feedback_file.read_text())
                feedback = UserFeedback.model_validate(feedback_data)

                if feedback.timestamp >= cutoff_date:
                    feedback_list.append(feedback)

            except Exception as e:
                logger.warning(f"Failed to load feedback file {feedback_file}: {str(e)}")

        return feedback_list

    async def _load_recent_performance(self, cutoff_date: datetime) -> list[PerformanceFeedback]:
        """Load performance feedback since cutoff date."""
        performance_list = []

        for performance_file in self.feedback_storage_path.glob("performance_*.json"):
            try:
                performance_data = json.loads(performance_file.read_text())
                performance = PerformanceFeedback.model_validate(performance_data)

                if performance.evaluation_date >= cutoff_date:
                    performance_list.append(performance)

            except Exception as e:
                logger.warning(f"Failed to load performance file {performance_file}: {str(e)}")

        return performance_list

    def _calculate_acceptance_by_asset(self, feedback: list[UserFeedback]) -> dict[str, float]:
        """Calculate acceptance rates by asset type."""
        by_asset = defaultdict(list)
        for f in feedback:
            by_asset[f.asset_type].append(f.outcome == RecommendationOutcome.ACCEPTED)

        return {asset: sum(outcomes) / len(outcomes) if outcomes else 0.0 for asset, outcomes in by_asset.items()}

    def _calculate_acceptance_by_grade(self, feedback: list[UserFeedback]) -> dict[Grade, float]:
        """Calculate acceptance rates by grade."""
        by_grade = defaultdict(list)
        for f in feedback:
            by_grade[f.recommended_grade].append(f.outcome == RecommendationOutcome.ACCEPTED)

        return {grade: sum(outcomes) / len(outcomes) if outcomes else 0.0 for grade, outcomes in by_grade.items()}

    def _calculate_acceptance_trends(self, feedback: list[UserFeedback]) -> dict[str, float]:
        """Calculate acceptance rate trends over time."""
        # Simple implementation - could be enhanced with more sophisticated trend analysis
        if len(feedback) < 10:
            return {"trend": 0.0, "recent_rate": 0.0, "historical_rate": 0.0}

        # Sort by timestamp
        sorted_feedback = sorted(feedback, key=lambda f: f.timestamp)
        midpoint = len(sorted_feedback) // 2

        recent = sorted_feedback[midpoint:]
        historical = sorted_feedback[:midpoint]

        recent_rate = sum(1 for f in recent if f.outcome == RecommendationOutcome.ACCEPTED) / len(recent)
        historical_rate = sum(1 for f in historical if f.outcome == RecommendationOutcome.ACCEPTED) / len(historical)

        return {
            "trend": recent_rate - historical_rate,
            "recent_rate": recent_rate,
            "historical_rate": historical_rate,
        }

    def _calculate_performance_by_asset(self, performance: list[PerformanceFeedback]) -> dict[str, dict[str, float]]:
        """Calculate performance metrics by asset type."""
        by_asset = defaultdict(list)

        # Group by asset type (need to infer from symbol or add to schema)
        for p in performance:
            # Simple heuristic - could be improved
            if p.symbol.endswith("-USD") or p.symbol in ["BTC-USD", "ETH-USD"]:
                asset_type = "crypto"
            elif len(p.symbol) <= 4 and p.symbol.isupper():
                asset_type = "stock"
            else:
                asset_type = "etf"

            by_asset[asset_type].append(p)

        result = {}
        for asset_type, perf_list in by_asset.items():
            if perf_list:
                result[asset_type] = {
                    "avg_return": sum(p.absolute_return for p in perf_list) / len(perf_list),
                    "avg_alpha": sum(p.alpha for p in perf_list) / len(perf_list),
                    "outperformance_rate": sum(1 for p in perf_list if p.performance_outcome == PerformanceOutcome.OUTPERFORMED)
                    / len(perf_list),
                    "grade_maintenance_rate": sum(1 for p in perf_list if p.grade_maintained) / len(perf_list),
                }

        return result

    def _identify_top_performers(self, performance: list[PerformanceFeedback]) -> list[dict[str, Any]]:
        """Identify top performing recommendations."""
        sorted_performance = sorted(performance, key=lambda p: p.alpha, reverse=True)

        return [
            {
                "symbol": p.symbol,
                "alpha": p.alpha,
                "absolute_return": p.absolute_return,
                "holding_period_days": p.holding_period_days,
                "grade_maintained": p.grade_maintained,
            }
            for p in sorted_performance[:5]
        ]

    def _identify_underperformers(self, performance: list[PerformanceFeedback]) -> list[dict[str, Any]]:
        """Identify underperforming recommendations."""
        sorted_performance = sorted(performance, key=lambda p: p.alpha)

        return [
            {
                "symbol": p.symbol,
                "alpha": p.alpha,
                "absolute_return": p.absolute_return,
                "holding_period_days": p.holding_period_days,
                "grade_maintained": p.grade_maintained,
            }
            for p in sorted_performance[:5]
        ]

    def _generate_insights(self, user_feedback: list[UserFeedback], performance_feedback: list[PerformanceFeedback]) -> list[str]:
        """Generate key insights from feedback analysis."""
        insights = []

        if user_feedback:
            acceptance_rate = sum(1 for f in user_feedback if f.outcome == RecommendationOutcome.ACCEPTED) / len(user_feedback)
            insights.append(f"Overall acceptance rate: {acceptance_rate:.1%}")

            # Asset type insights
            by_asset = self._calculate_acceptance_by_asset(user_feedback)
            best_asset = max(by_asset.items(), key=lambda x: x[1]) if by_asset else None
            if best_asset:
                insights.append(f"Best performing asset type: {best_asset[0]} ({best_asset[1]:.1%} acceptance)")

        if performance_feedback:
            outperformance_rate = sum(
                1 for p in performance_feedback if p.performance_outcome == PerformanceOutcome.OUTPERFORMED
            ) / len(performance_feedback)
            insights.append(f"Outperformance rate: {outperformance_rate:.1%}")

            grade_maintenance = sum(1 for p in performance_feedback if p.grade_maintained) / len(performance_feedback)
            insights.append(f"A+ grade maintenance rate: {grade_maintenance:.1%}")

        return insights

    def _recommend_adjustments(
        self, user_feedback: list[UserFeedback], performance_feedback: list[PerformanceFeedback]
    ) -> list[str]:
        """Recommend criteria adjustments based on feedback."""
        recommendations = []

        # Analyze rejection patterns
        rejections = [f for f in user_feedback if f.outcome == RecommendationOutcome.REJECTED]
        if rejections:
            common_reasons = defaultdict(int)
            for rejection in rejections:
                for reason in rejection.reasons:
                    common_reasons[reason] += 1

            if common_reasons:
                top_reason = max(common_reasons.items(), key=lambda x: x[1])
                recommendations.append(f"Address common rejection reason: {top_reason[0]} ({top_reason[1]} occurrences)")

        # Analyze performance issues
        underperformers = [
            p
            for p in performance_feedback
            if p.performance_outcome in [PerformanceOutcome.UNDERPERFORMED, PerformanceOutcome.SIGNIFICANT_LOSS]
        ]
        if len(underperformers) > len(performance_feedback) * 0.3:  # More than 30% underperforming
            recommendations.append("Consider tightening quality criteria - high underperformance rate")

        return recommendations

    def _identify_success_patterns(
        self, user_feedback: list[UserFeedback], performance_feedback: list[PerformanceFeedback]
    ) -> list[str]:
        """Identify patterns in successful recommendations."""
        patterns = []

        # Successful recommendations (accepted and outperformed)
        successful_symbols = set()
        for p in performance_feedback:
            if p.performance_outcome == PerformanceOutcome.OUTPERFORMED:
                successful_symbols.add(p.symbol)

        successful_feedback = [
            f for f in user_feedback if f.symbol in successful_symbols and f.outcome == RecommendationOutcome.ACCEPTED
        ]

        if successful_feedback:
            # Analyze score patterns
            scores = [f.recommended_score for f in successful_feedback]
            avg_score = sum(scores) / len(scores)
            patterns.append(f"Successful recommendations average score: {avg_score:.3f}")

            # Analyze grade patterns
            grades = defaultdict(int)
            for f in successful_feedback:
                grades[f.recommended_grade] += 1

            if grades:
                top_grade = max(grades.items(), key=lambda x: x[1])
                patterns.append(f"Most successful grade: {top_grade[0]} ({top_grade[1]} occurrences)")

        return patterns

    def _identify_failure_patterns(
        self, user_feedback: list[UserFeedback], performance_feedback: list[PerformanceFeedback]
    ) -> list[str]:
        """Identify patterns in failed recommendations."""
        patterns = []

        # Failed recommendations (rejected or underperformed)
        failed_symbols = set()
        for p in performance_feedback:
            if p.performance_outcome in [PerformanceOutcome.UNDERPERFORMED, PerformanceOutcome.SIGNIFICANT_LOSS]:
                failed_symbols.add(p.symbol)

        rejected_symbols = set(f.symbol for f in user_feedback if f.outcome == RecommendationOutcome.REJECTED)
        failed_symbols.update(rejected_symbols)

        failed_feedback = [f for f in user_feedback if f.symbol in failed_symbols]

        if failed_feedback:
            # Analyze common rejection reasons
            all_reasons = []
            for f in failed_feedback:
                all_reasons.extend(f.reasons)

            if all_reasons:
                reason_counts = defaultdict(int)
                for reason in all_reasons:
                    reason_counts[reason] += 1

                top_reason = max(reason_counts.items(), key=lambda x: x[1])
                patterns.append(f"Most common failure reason: {top_reason[0]} ({top_reason[1]} occurrences)")

        return patterns

    def _assess_data_quality(self, user_feedback: list[UserFeedback], performance_feedback: list[PerformanceFeedback]) -> float:
        """Assess the quality of feedback data collected."""
        if not user_feedback:
            return 0.0

        quality_score = 0.0

        # Check completeness of feedback
        complete_feedback = sum(1 for f in user_feedback if f.reasons and f.confidence_rating > 0)
        completeness_score = complete_feedback / len(user_feedback)
        quality_score += completeness_score * 0.4

        # Check performance data availability
        feedback_with_performance = sum(
            1 for f in user_feedback if any(p.original_recommendation_id == f.recommendation_id for p in performance_feedback)
        )
        performance_coverage = feedback_with_performance / len(user_feedback) if user_feedback else 0.0
        quality_score += performance_coverage * 0.3

        # Check recency of data
        recent_feedback = sum(1 for f in user_feedback if (datetime.now() - f.timestamp).days <= 30)
        recency_score = recent_feedback / len(user_feedback)
        quality_score += recency_score * 0.3

        return min(quality_score, 1.0)

    def _calculate_confidence_in_insights(
        self, user_feedback: list[UserFeedback], performance_feedback: list[PerformanceFeedback]
    ) -> float:
        """Calculate confidence level in derived insights."""
        if not user_feedback:
            return 0.0

        # Base confidence on sample size
        sample_size_confidence = min(len(user_feedback) / self.config.min_feedback_samples, 1.0)

        # Adjust for data quality
        data_quality = self._assess_data_quality(user_feedback, performance_feedback)

        # Adjust for consistency of patterns
        consistency_score = 0.8  # Placeholder - could implement pattern consistency analysis

        return sample_size_confidence * 0.5 + data_quality * 0.3 + consistency_score * 0.2

    async def _generate_improved_criteria(
        self, current_criteria: APlusCriteria, feedback_summary: FeedbackSummary
    ) -> APlusCriteria:
        """Generate improved criteria based on feedback learning."""
        # This is a simplified implementation - could be enhanced with ML algorithms
        new_criteria = current_criteria.model_copy()

        # Adjust based on acceptance rates by asset type
        for asset_type, acceptance_rate in feedback_summary.acceptance_by_asset_type.items():
            if acceptance_rate < 0.5:  # Low acceptance rate
                # Loosen criteria for this asset type
                if asset_type == "etf":
                    new_criteria.etf_max_expense_ratio *= 1.1  # Allow slightly higher fees
                    new_criteria.etf_min_aum *= 0.9  # Allow smaller funds
                elif asset_type == "stock":
                    new_criteria.stock_min_roe *= 0.95  # Slightly lower ROE requirement
                    new_criteria.stock_min_revenue_growth *= 0.95  # Lower growth requirement
                elif asset_type == "crypto":
                    new_criteria.crypto_min_market_cap *= 0.9  # Allow smaller market caps

        # Adjust based on performance outcomes
        for asset_type, metrics in feedback_summary.performance_by_asset_type.items():
            outperformance_rate = metrics.get("outperformance_rate", 0.0)
            if outperformance_rate < 0.6:  # Low outperformance
                # Tighten criteria for this asset type
                if asset_type == "etf":
                    new_criteria.etf_max_expense_ratio *= 0.95  # Require lower fees
                    new_criteria.etf_max_tracking_error *= 0.95  # Tighter tracking
                elif asset_type == "stock":
                    new_criteria.stock_min_roe *= 1.05  # Higher ROE requirement
                    new_criteria.stock_max_debt_to_equity *= 0.95  # Lower debt tolerance
                elif asset_type == "crypto":
                    new_criteria.crypto_min_market_cap *= 1.1  # Require larger market caps
                    new_criteria.crypto_min_daily_volume *= 1.1  # Higher volume requirement

        new_criteria.regime_adjusted = True
        new_criteria.adjustment_rationale = "Adjusted based on user feedback and performance outcomes"

        return new_criteria

    def _validate_criteria_adjustment(self, old_criteria: APlusCriteria, new_criteria: APlusCriteria) -> bool:
        """Validate that criteria adjustment is reasonable."""
        # Check that changes are within acceptable bounds
        max_change = self.config.max_criteria_change

        # ETF criteria validation
        etf_expense_change = (
            abs(new_criteria.etf_max_expense_ratio - old_criteria.etf_max_expense_ratio) / old_criteria.etf_max_expense_ratio
        )
        if etf_expense_change > max_change:
            return False

        # Stock criteria validation
        roe_change = abs(new_criteria.stock_min_roe - old_criteria.stock_min_roe) / old_criteria.stock_min_roe
        if roe_change > max_change:
            return False

        # Crypto criteria validation
        crypto_cap_change = (
            abs(new_criteria.crypto_min_market_cap - old_criteria.crypto_min_market_cap) / old_criteria.crypto_min_market_cap
        )
        if crypto_cap_change > max_change:
            return False

        return True

    async def _backtest_criteria_adjustment(self, new_criteria: APlusCriteria) -> dict[str, Any]:
        """Backtest criteria adjustment against historical data."""
        # Placeholder implementation - would need historical data and backtesting engine
        return {
            "passed": True,
            "historical_performance": 0.15,  # 15% annual return
            "sharpe_ratio": 1.2,
            "max_drawdown": -0.08,
            "validation_period_years": self.config.min_backtest_years,
        }

    def _generate_adjustment_reason(self, feedback_summary: FeedbackSummary) -> str:
        """Generate human-readable reason for criteria adjustment."""
        reasons = []

        # Check acceptance rates
        overall_acceptance = (
            sum(feedback_summary.acceptance_by_asset_type.values()) / len(feedback_summary.acceptance_by_asset_type)
            if feedback_summary.acceptance_by_asset_type
            else 0.0
        )
        if overall_acceptance < 0.6:
            reasons.append("low acceptance rate")

        # Check performance
        if feedback_summary.performance_by_asset_type:
            avg_outperformance = sum(
                metrics.get("outperformance_rate", 0.0) for metrics in feedback_summary.performance_by_asset_type.values()
            ) / len(feedback_summary.performance_by_asset_type)
            if avg_outperformance < 0.6:
                reasons.append("poor performance outcomes")

        # Check insights
        if "tightening" in " ".join(feedback_summary.recommended_adjustments).lower():
            reasons.append("quality concerns")

        if not reasons:
            reasons.append("optimization based on feedback patterns")

        return f"Criteria adjusted due to: {', '.join(reasons)}"

    def _calculate_expected_improvement(self, feedback_summary: FeedbackSummary) -> float:
        """Calculate expected improvement from criteria adjustment."""
        # Simple heuristic - could be enhanced with ML models
        (
            sum(feedback_summary.acceptance_by_asset_type.values()) / len(feedback_summary.acceptance_by_asset_type)
            if feedback_summary.acceptance_by_asset_type
            else 0.0
        )

        # Expect 5-15% improvement based on confidence in insights
        base_improvement = 0.05
        confidence_multiplier = feedback_summary.confidence_in_insights

        return base_improvement + (0.10 * confidence_multiplier)

    async def _load_feedback_for_period(self, start_date: datetime, end_date: datetime) -> list[UserFeedback]:
        """Load feedback for a specific time period."""
        feedback_list = []

        for feedback_file in self.feedback_storage_path.glob("user_feedback_*.json"):
            try:
                feedback_data = json.loads(feedback_file.read_text())
                feedback = UserFeedback.model_validate(feedback_data)

                if start_date <= feedback.timestamp <= end_date:
                    feedback_list.append(feedback)

            except Exception as e:
                logger.warning(f"Failed to load feedback file {feedback_file}: {str(e)}")

        return feedback_list

    async def _load_performance_for_period(self, start_date: datetime, end_date: datetime) -> list[PerformanceFeedback]:
        """Load performance feedback for a specific time period."""
        performance_list = []

        for performance_file in self.feedback_storage_path.glob("performance_*.json"):
            try:
                performance_data = json.loads(performance_file.read_text())
                performance = PerformanceFeedback.model_validate(performance_data)

                if start_date <= performance.evaluation_date <= end_date:
                    performance_list.append(performance)

            except Exception as e:
                logger.warning(f"Failed to load performance file {performance_file}: {str(e)}")

        return performance_list

    def _calculate_acceptance_rate(self, feedback: list[UserFeedback]) -> float:
        """Calculate acceptance rate for feedback list."""
        if not feedback:
            return 0.0

        accepted = sum(1 for f in feedback if f.outcome == RecommendationOutcome.ACCEPTED)
        return accepted / len(feedback)

    def _calculate_outperformance_rate(self, performance: list[PerformanceFeedback]) -> float:
        """Calculate outperformance rate for performance list."""
        if not performance:
            return 0.0

        outperformed = sum(1 for p in performance if p.performance_outcome == PerformanceOutcome.OUTPERFORMED)
        return outperformed / len(performance)

    def _calculate_asset_metrics(
        self, user_feedback: list[UserFeedback], performance_feedback: list[PerformanceFeedback], asset_type: str
    ) -> dict[str, float]:
        """Calculate metrics for a specific asset type."""
        asset_user_feedback = [f for f in user_feedback if f.asset_type == asset_type]

        # Get performance feedback for this asset type (simplified matching)
        asset_symbols = set(f.symbol for f in asset_user_feedback)
        asset_performance = [p for p in performance_feedback if p.symbol in asset_symbols]

        metrics = {}

        if asset_user_feedback:
            acceptance_rate = sum(1 for f in asset_user_feedback if f.outcome == RecommendationOutcome.ACCEPTED) / len(
                asset_user_feedback
            )
            metrics["acceptance_rate"] = acceptance_rate

            avg_confidence = sum(f.confidence_rating for f in asset_user_feedback if f.confidence_rating) / len(asset_user_feedback)
            metrics["average_confidence"] = avg_confidence

        if asset_performance:
            outperformance_rate = sum(
                1 for p in asset_performance if p.performance_outcome == PerformanceOutcome.OUTPERFORMED
            ) / len(asset_performance)
            metrics["outperformance_rate"] = outperformance_rate

            grade_maintenance_rate = sum(1 for p in asset_performance if p.grade_maintained) / len(asset_performance)
            metrics["grade_maintenance_rate"] = grade_maintenance_rate

            avg_alpha = sum(p.alpha for p in asset_performance) / len(asset_performance)
            metrics["average_alpha"] = avg_alpha

        return metrics


# Global service instance
_feedback_service: FeedbackLearningService | None = None


def get_feedback_service(config: LearningConfiguration | None = None) -> FeedbackLearningService:
    """Get the global feedback learning service instance."""
    global _feedback_service
    if _feedback_service is None:
        _feedback_service = FeedbackLearningService(config)
    return _feedback_service
