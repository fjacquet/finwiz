"""
Feedback Integration Tool for A+ Investment Discovery.

This tool integrates the feedback learning system with the investment discovery
process, enabling continuous improvement of A+ criteria based on user feedback
and performance outcomes.
"""

import asyncio
from typing import Any

from crewai.tools import BaseTool

from finwiz.schemas.feedback import (
    PerformanceFeedback,
    PerformanceOutcome,
    RecommendationOutcome,
    UserFeedback,
)
from finwiz.schemas.investment_discovery import APlusCriteria
from finwiz.schemas.tools import (
    CriteriaOptimizationInput,
    FeedbackCollectionInput,
    PerformanceTrackingInput,
)
from finwiz.services.feedback_service import get_feedback_service
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class FeedbackCollectionTool(BaseTool):
    """Tool for collecting user feedback on A+ recommendations."""

    name: str = "feedback_collection_tool"
    description: str = """
    Collect user feedback on A+ investment recommendations to improve future discoveries.
    Use this tool when users provide feedback on whether they accepted or rejected
    A+ recommendations and their reasons for the decision.
    """

    def _run(self, **kwargs: Any) -> dict[str, Any]:
        """Collect user feedback synchronously."""
        return asyncio.run(self._arun(**kwargs))

    async def _arun(self, **kwargs: Any) -> dict[str, Any]:
        """Collect user feedback on A+ recommendations."""
        try:
            input_data = FeedbackCollectionInput.model_validate(kwargs)
            feedback_service = get_feedback_service()

            # Create feedback record
            feedback = UserFeedback(
                feedback_id="",  # Will be generated
                user_id=input_data.user_id,
                recommendation_id=input_data.recommendation_id,
                symbol=input_data.symbol,
                asset_type=input_data.asset_type,
                recommended_grade="A+",  # Assuming A+ recommendations
                recommended_score=0.95,  # Default A+ score
                outcome=RecommendationOutcome(input_data.outcome),
                sentiment=input_data.sentiment,
                confidence_rating=input_data.confidence_rating,
                reasons=input_data.reasons,
                user_comments=input_data.user_comments,
                feedback_type="recommendation_acceptance",
            )

            # Collect feedback
            feedback_id = await feedback_service.collect_user_feedback(feedback)

            result = {
                "success": True,
                "feedback_id": feedback_id,
                "message": f"Collected feedback for {input_data.symbol}",
                "outcome": input_data.outcome,
                "will_improve_future_recommendations": True,
            }

            logger.info(f"Collected user feedback: {input_data.symbol} - {input_data.outcome}")
            return result

        except Exception as e:
            logger.error(f"Failed to collect user feedback: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to collect feedback",
            }


class PerformanceTrackingTool(BaseTool):
    """Tool for tracking performance outcomes of A+ recommendations."""

    name: str = "performance_tracking_tool"
    description: str = """
    Track the performance outcomes of accepted A+ recommendations to measure
    the effectiveness of the discovery system and improve future recommendations.
    Use this tool to record how A+ investments have performed over time.
    """

    def _run(self, **kwargs: Any) -> dict[str, Any]:
        """Track performance synchronously."""
        return asyncio.run(self._arun(**kwargs))

    async def _arun(self, **kwargs: Any) -> dict[str, Any]:
        """Track performance outcomes of A+ recommendations."""
        try:
            input_data = PerformanceTrackingInput.model_validate(kwargs)
            feedback_service = get_feedback_service()

            # Calculate alpha and performance outcome
            alpha = input_data.absolute_return - input_data.benchmark_return

            # Determine performance outcome
            if alpha > 0.02:  # Outperformed by >2%
                performance_outcome = PerformanceOutcome.OUTPERFORMED
            elif alpha > -0.02:  # Within 2% of benchmark
                performance_outcome = PerformanceOutcome.MET_EXPECTATIONS
            elif alpha > -0.10:  # Underperformed but not severely
                performance_outcome = PerformanceOutcome.UNDERPERFORMED
            else:  # Significant underperformance
                performance_outcome = PerformanceOutcome.SIGNIFICANT_LOSS

            # Create performance record
            performance = PerformanceFeedback(
                feedback_id="",  # Will be generated
                original_recommendation_id=input_data.recommendation_id,
                symbol=input_data.symbol,
                holding_period_days=input_data.holding_period_days,
                absolute_return=input_data.absolute_return,
                benchmark_return=input_data.benchmark_return,
                alpha=alpha,
                current_grade=input_data.current_grade,
                grade_maintained=input_data.grade_maintained,
                performance_outcome=performance_outcome,
                met_expectations=performance_outcome in [PerformanceOutcome.OUTPERFORMED, PerformanceOutcome.MET_EXPECTATIONS],
                volatility=0.0,  # Would need additional data
                max_drawdown=0.0,  # Would need additional data
                market_regime_during_period="unknown",  # Would need market data
            )

            # Record performance
            performance_id = await feedback_service.record_performance_outcome(performance)

            result = {
                "success": True,
                "performance_id": performance_id,
                "symbol": input_data.symbol,
                "alpha": alpha,
                "performance_outcome": performance_outcome.value,
                "grade_maintained": input_data.grade_maintained,
                "message": f"Recorded performance for {input_data.symbol}: {performance_outcome.value}",
            }

            logger.info(f"Recorded performance outcome: {input_data.symbol} - {performance_outcome.value}")
            return result

        except Exception as e:
            logger.error(f"Failed to record performance outcome: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to record performance outcome",
            }


class CriteriaOptimizationTool(BaseTool):
    """Tool for optimizing A+ criteria based on feedback learning."""

    name: str = "criteria_optimization_tool"
    description: str = """
    Optimize A+ discovery criteria based on collected user feedback and performance
    outcomes. This tool implements machine learning to continuously improve the
    quality of A+ recommendations by adjusting screening criteria.
    """

    def _run(self, **kwargs: Any) -> dict[str, Any]:
        """Optimize criteria synchronously."""
        return asyncio.run(self._arun(**kwargs))

    async def _arun(self, **kwargs: Any) -> dict[str, Any]:
        """Optimize A+ criteria based on feedback learning."""
        try:
            input_data = CriteriaOptimizationInput.model_validate(kwargs)
            feedback_service = get_feedback_service()

            # Convert current criteria
            current_criteria = APlusCriteria.model_validate(input_data.current_criteria)

            # Attempt criteria adjustment
            adjustment = await feedback_service.adjust_criteria_based_on_learning(
                current_criteria=current_criteria, force_adjustment=input_data.force_adjustment
            )

            if adjustment:
                result = {
                    "success": True,
                    "adjustment_made": True,
                    "adjustment_id": adjustment.adjustment_id,
                    "adjustment_reason": adjustment.adjustment_reason,
                    "confidence_level": adjustment.confidence_level,
                    "expected_improvement": adjustment.expected_improvement,
                    "new_criteria": adjustment.criteria_after.model_dump(),
                    "message": f"Criteria adjusted: {adjustment.adjustment_reason}",
                }
            else:
                result = {
                    "success": True,
                    "adjustment_made": False,
                    "message": "No criteria adjustment needed at this time",
                    "reason": "Insufficient feedback data or adjustment not due",
                }

            logger.info(f"Criteria optimization result: adjustment_made={result['adjustment_made']}")
            return result

        except Exception as e:
            logger.error(f"Failed to optimize criteria: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to optimize criteria",
            }


class FeedbackAnalysisTool(BaseTool):
    """Tool for analyzing feedback patterns and generating insights."""

    name: str = "feedback_analysis_tool"
    description: str = """
    Analyze collected feedback to identify patterns, insights, and opportunities
    for improving A+ investment discovery. Use this tool to understand how well
    the system is performing and what adjustments might be needed.
    """

    def _run(self, days_back: int = 90) -> dict[str, Any]:
        """Analyze feedback synchronously."""
        return asyncio.run(self._arun(days_back=days_back))

    async def _arun(self, days_back: int = 90) -> dict[str, Any]:
        """Analyze feedback patterns and generate insights."""
        try:
            feedback_service = get_feedback_service()

            # Get feedback analysis
            feedback_summary = await feedback_service.analyze_feedback_patterns(days_back=days_back)

            # Get learning metrics
            learning_metrics = await feedback_service.get_learning_metrics(days_back=min(days_back, 30))

            result = {
                "success": True,
                "analysis_period_days": days_back,
                "total_feedback_items": feedback_summary.total_feedback_items,
                "unique_users": feedback_summary.unique_users,
                "sample_size_adequate": feedback_summary.sample_size_adequacy,
                # Acceptance analysis
                "overall_acceptance_rate": learning_metrics.acceptance_rate,
                "acceptance_by_asset_type": feedback_summary.acceptance_by_asset_type,
                "acceptance_trends": feedback_summary.acceptance_trends,
                # Performance analysis
                "outperformance_rate": learning_metrics.outperformance_rate,
                "grade_maintenance_rate": learning_metrics.grade_maintenance_rate,
                "performance_by_asset_type": feedback_summary.performance_by_asset_type,
                # Learning effectiveness
                "criteria_adjustments_made": learning_metrics.criteria_adjustments_made,
                "improvement_in_acceptance": learning_metrics.improvement_in_acceptance,
                "improvement_in_performance": learning_metrics.improvement_in_performance,
                # User satisfaction
                "average_confidence_rating": learning_metrics.average_confidence_rating,
                "positive_sentiment_rate": learning_metrics.positive_sentiment_rate,
                # Insights and recommendations
                "key_insights": feedback_summary.key_insights,
                "recommended_adjustments": feedback_summary.recommended_adjustments,
                "success_patterns": feedback_summary.success_patterns,
                "failure_patterns": feedback_summary.failure_patterns,
                # Quality metrics
                "data_quality_score": feedback_summary.data_quality_score,
                "confidence_in_insights": feedback_summary.confidence_in_insights,
                "message": f"Analyzed {feedback_summary.total_feedback_items} feedback items over {days_back} days",
            }

            logger.info(f"Generated feedback analysis: {feedback_summary.total_feedback_items} items analyzed")
            return result

        except Exception as e:
            logger.error(f"Failed to analyze feedback: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to analyze feedback patterns",
            }


class LearningMetricsTool(BaseTool):
    """Tool for getting comprehensive learning system metrics."""

    name: str = "learning_metrics_tool"
    description: str = """
    Get comprehensive metrics about the learning system performance, including
    recommendation success rates, performance outcomes, and system improvements
    over time. Use this tool to monitor the effectiveness of the feedback loop.
    """

    def _run(self, days_back: int = 30) -> dict[str, Any]:
        """Get learning metrics synchronously."""
        return asyncio.run(self._arun(days_back=days_back))

    async def _arun(self, days_back: int = 30) -> dict[str, Any]:
        """Get comprehensive learning system metrics."""
        try:
            feedback_service = get_feedback_service()

            # Get learning metrics
            metrics = await feedback_service.get_learning_metrics(days_back=days_back)

            result = {
                "success": True,
                "evaluation_period": {
                    "start_date": metrics.evaluation_period_start.isoformat(),
                    "end_date": metrics.evaluation_period_end.isoformat(),
                    "days": days_back,
                },
                # Recommendation metrics
                "recommendation_metrics": {
                    "total_recommendations": metrics.total_recommendations,
                    "acceptance_rate": metrics.acceptance_rate,
                    "rejection_rate": metrics.rejection_rate,
                },
                # Performance metrics
                "performance_metrics": {
                    "recommendations_with_outcomes": metrics.recommendations_with_outcomes,
                    "outperformance_rate": metrics.outperformance_rate,
                    "grade_maintenance_rate": metrics.grade_maintenance_rate,
                },
                # Learning effectiveness
                "learning_effectiveness": {
                    "criteria_adjustments_made": metrics.criteria_adjustments_made,
                    "improvement_in_acceptance": metrics.improvement_in_acceptance,
                    "improvement_in_performance": metrics.improvement_in_performance,
                },
                # User satisfaction
                "user_satisfaction": {
                    "average_confidence_rating": metrics.average_confidence_rating,
                    "positive_sentiment_rate": metrics.positive_sentiment_rate,
                },
                # Asset-specific metrics
                "asset_metrics": {
                    "etf": metrics.etf_metrics,
                    "stock": metrics.stock_metrics,
                    "crypto": metrics.crypto_metrics,
                },
                "message": f"Learning metrics for {days_back} days: {metrics.acceptance_rate:.1%} acceptance rate",
            }

            logger.info(f"Generated learning metrics for {days_back} days")
            return result

        except Exception as e:
            logger.error(f"Failed to get learning metrics: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get learning metrics",
            }


def get_feedback_tools() -> list[BaseTool]:
    """Get all feedback integration tools."""
    return [
        FeedbackCollectionTool(),
        PerformanceTrackingTool(),
        CriteriaOptimizationTool(),
        FeedbackAnalysisTool(),
        LearningMetricsTool(),
    ]
