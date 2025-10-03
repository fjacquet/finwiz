"""
Pydantic schemas for A+ Investment Feedback and Learning System.

This module defines the data models for collecting user feedback on A+ recommendations,
tracking performance outcomes, and implementing learning mechanisms to improve
discovery criteria over time.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from .investment_discovery import APlusCriteria
from .portfolio_review import Grade


class FeedbackType(str, Enum):
    """Types of feedback that can be collected."""

    RECOMMENDATION_ACCEPTANCE = "recommendation_acceptance"
    PERFORMANCE_OUTCOME = "performance_outcome"
    CRITERIA_ADJUSTMENT = "criteria_adjustment"
    USER_PREFERENCE = "user_preference"


class FeedbackSentiment(str, Enum):
    """User sentiment towards recommendations."""

    VERY_POSITIVE = "very_positive"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    VERY_NEGATIVE = "very_negative"


class RecommendationOutcome(str, Enum):
    """Outcome of A+ recommendations."""

    ACCEPTED = "accepted"
    REJECTED = "rejected"
    PARTIALLY_ACCEPTED = "partially_accepted"
    DEFERRED = "deferred"


class PerformanceOutcome(str, Enum):
    """Performance outcome of accepted recommendations."""

    OUTPERFORMED = "outperformed"
    MET_EXPECTATIONS = "met_expectations"
    UNDERPERFORMED = "underperformed"
    SIGNIFICANT_LOSS = "significant_loss"


class UserFeedback(BaseModel):
    """User feedback on A+ investment recommendations."""

    feedback_id: str = Field(..., description="Unique feedback identifier")
    user_id: str = Field(..., description="User identifier (anonymized)")
    feedback_type: FeedbackType = Field(..., description="Type of feedback")
    timestamp: datetime = Field(default_factory=datetime.now, description="When feedback was provided")

    # Recommendation context
    recommendation_id: str = Field(..., description="ID of the recommendation being evaluated")
    symbol: str = Field(..., description="Investment symbol")
    asset_type: Literal["etf", "stock", "crypto"] = Field(..., description="Type of asset")
    recommended_grade: Grade = Field(..., description="Grade assigned by system")
    recommended_score: float = Field(..., ge=0.0, le=1.0, description="Score assigned by system")

    # User response
    outcome: RecommendationOutcome = Field(..., description="What user did with recommendation")
    sentiment: FeedbackSentiment = Field(..., description="User sentiment")
    confidence_rating: int = Field(..., ge=1, le=5, description="User confidence in their decision (1-5)")

    # Detailed feedback
    reasons: list[str] = Field(default_factory=list, description="Reasons for acceptance/rejection")
    alternative_chosen: Optional[str] = Field(None, description="Alternative investment chosen instead")
    allocation_percentage: Optional[float] = Field(None, ge=0.0, le=100.0, description="Actual allocation if accepted")

    # Context
    portfolio_context: dict[str, Any] = Field(default_factory=dict, description="Portfolio context at time of decision")
    market_conditions: dict[str, Any] = Field(default_factory=dict, description="Market conditions at time of decision")

    # Optional comments
    user_comments: str = Field(default="", description="Free-form user comments")


class PerformanceFeedback(BaseModel):
    """Performance feedback for accepted A+ recommendations."""

    feedback_id: str = Field(..., description="Unique feedback identifier")
    original_recommendation_id: str = Field(..., description="Original recommendation ID")
    symbol: str = Field(..., description="Investment symbol")

    # Performance data
    evaluation_date: datetime = Field(..., description="Date of performance evaluation")
    holding_period_days: int = Field(..., ge=1, description="Days since investment")

    # Returns
    absolute_return: float = Field(..., description="Absolute return percentage")
    benchmark_return: float = Field(..., description="Benchmark return for same period")
    alpha: float = Field(..., description="Alpha vs benchmark")

    # Risk metrics
    volatility: float = Field(..., ge=0.0, description="Volatility during holding period")
    max_drawdown: float = Field(..., le=0.0, description="Maximum drawdown experienced")
    sharpe_ratio: Optional[float] = Field(None, description="Sharpe ratio if calculable")

    # Grade tracking
    current_grade: Grade = Field(..., description="Current grade of investment")
    grade_maintained: bool = Field(..., description="Whether A+ grade was maintained")
    grade_changes: list[dict[str, Any]] = Field(default_factory=list, description="History of grade changes")

    # Outcome assessment
    performance_outcome: PerformanceOutcome = Field(..., description="Overall performance assessment")
    met_expectations: bool = Field(..., description="Whether performance met user expectations")

    # Context
    market_regime_during_period: str = Field(..., description="Market regime during holding period")
    significant_events: list[str] = Field(default_factory=list, description="Significant events affecting performance")


class CriteriaAdjustment(BaseModel):
    """Record of criteria adjustments based on feedback learning."""

    adjustment_id: str = Field(..., description="Unique adjustment identifier")
    timestamp: datetime = Field(default_factory=datetime.now, description="When adjustment was made")

    # Adjustment details
    criteria_before: APlusCriteria = Field(..., description="Criteria before adjustment")
    criteria_after: APlusCriteria = Field(..., description="Criteria after adjustment")
    adjustment_reason: str = Field(..., description="Reason for adjustment")

    # Learning context
    feedback_sample_size: int = Field(..., ge=1, description="Number of feedback samples used")
    confidence_level: float = Field(..., ge=0.0, le=1.0, description="Confidence in adjustment")
    expected_improvement: float = Field(..., description="Expected improvement in success rate")

    # Validation
    backtesting_validation: bool = Field(default=False, description="Whether adjustment was backtested")
    validation_results: dict[str, Any] = Field(default_factory=dict, description="Backtesting results")

    # Rollback capability
    can_rollback: bool = Field(default=True, description="Whether adjustment can be rolled back")
    rollback_conditions: list[str] = Field(default_factory=list, description="Conditions that would trigger rollback")


class LearningMetrics(BaseModel):
    """Metrics for the learning system performance."""

    # Time period
    evaluation_period_start: datetime = Field(..., description="Start of evaluation period")
    evaluation_period_end: datetime = Field(..., description="End of evaluation period")

    # Recommendation metrics
    total_recommendations: int = Field(..., ge=0, description="Total A+ recommendations made")
    acceptance_rate: float = Field(..., ge=0.0, le=1.0, description="Percentage of recommendations accepted")
    rejection_rate: float = Field(..., ge=0.0, le=1.0, description="Percentage of recommendations rejected")

    # Performance metrics
    recommendations_with_outcomes: int = Field(..., ge=0, description="Recommendations with performance data")
    outperformance_rate: float = Field(..., ge=0.0, le=1.0, description="Percentage that outperformed benchmark")
    grade_maintenance_rate: float = Field(..., ge=0.0, le=1.0, description="Percentage maintaining A+ grade")

    # Learning effectiveness
    criteria_adjustments_made: int = Field(..., ge=0, description="Number of criteria adjustments")
    improvement_in_acceptance: float = Field(..., description="Change in acceptance rate")
    improvement_in_performance: float = Field(..., description="Change in performance outcomes")

    # User satisfaction
    average_confidence_rating: float = Field(..., ge=1.0, le=5.0, description="Average user confidence rating")
    positive_sentiment_rate: float = Field(..., ge=0.0, le=1.0, description="Percentage of positive sentiment")

    # Asset type breakdown
    etf_metrics: dict[str, float] = Field(default_factory=dict, description="ETF-specific metrics")
    stock_metrics: dict[str, float] = Field(default_factory=dict, description="Stock-specific metrics")
    crypto_metrics: dict[str, float] = Field(default_factory=dict, description="Crypto-specific metrics")


class FeedbackSummary(BaseModel):
    """Summary of feedback for reporting and analysis."""

    summary_date: datetime = Field(default_factory=datetime.now, description="Date of summary generation")
    period_days: int = Field(..., ge=1, description="Number of days covered in summary")

    # Overall statistics
    total_feedback_items: int = Field(..., ge=0, description="Total feedback items collected")
    unique_users: int = Field(..., ge=0, description="Number of unique users providing feedback")
    unique_recommendations: int = Field(..., ge=0, description="Number of unique recommendations evaluated")

    # Acceptance analysis
    acceptance_by_asset_type: dict[str, float] = Field(default_factory=dict, description="Acceptance rates by asset type")
    acceptance_by_grade: dict[Grade, float] = Field(default_factory=dict, description="Acceptance rates by grade")
    acceptance_trends: dict[str, float] = Field(default_factory=dict, description="Acceptance rate trends over time")

    # Performance analysis
    performance_by_asset_type: dict[str, dict[str, float]] = Field(
        default_factory=dict, description="Performance metrics by asset type"
    )
    top_performing_recommendations: list[dict[str, Any]] = Field(
        default_factory=list, description="Best performing recommendations"
    )
    underperforming_recommendations: list[dict[str, Any]] = Field(
        default_factory=list, description="Worst performing recommendations"
    )

    # Learning insights
    key_insights: list[str] = Field(default_factory=list, description="Key insights from feedback analysis")
    recommended_adjustments: list[str] = Field(default_factory=list, description="Recommended criteria adjustments")
    success_patterns: list[str] = Field(default_factory=list, description="Patterns in successful recommendations")
    failure_patterns: list[str] = Field(default_factory=list, description="Patterns in failed recommendations")

    # Quality metrics
    data_quality_score: float = Field(..., ge=0.0, le=1.0, description="Quality of feedback data collected")
    confidence_in_insights: float = Field(..., ge=0.0, le=1.0, description="Confidence in derived insights")
    sample_size_adequacy: bool = Field(..., description="Whether sample size is adequate for conclusions")


class LearningConfiguration(BaseModel):
    """Configuration for the learning system."""

    # Learning parameters
    min_feedback_samples: int = Field(default=10, ge=1, description="Minimum feedback samples before learning")
    learning_rate: float = Field(default=0.1, ge=0.01, le=1.0, description="Rate of criteria adjustment")
    confidence_threshold: float = Field(default=0.7, ge=0.5, le=1.0, description="Minimum confidence for adjustments")

    # Adjustment limits
    max_criteria_change: float = Field(default=0.2, ge=0.05, le=0.5, description="Maximum change per adjustment")
    adjustment_frequency_days: int = Field(default=30, ge=7, le=365, description="Minimum days between adjustments")

    # Validation requirements
    require_backtesting: bool = Field(default=True, description="Whether to require backtesting validation")
    min_backtest_years: int = Field(default=3, ge=1, le=10, description="Minimum years for backtesting")

    # Rollback conditions
    auto_rollback_enabled: bool = Field(default=True, description="Whether to enable automatic rollback")
    rollback_performance_threshold: float = Field(default=-0.1, description="Performance drop that triggers rollback")
    rollback_acceptance_threshold: float = Field(default=-0.2, description="Acceptance drop that triggers rollback")

    # Asset-specific settings
    asset_specific_learning: bool = Field(default=True, description="Whether to learn separately by asset type")
    weight_by_asset_performance: bool = Field(default=True, description="Whether to weight learning by asset performance")
