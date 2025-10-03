"""
Rebalancing Results and History Models.

Models for rebalancing results, execution tracking, and historical records.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .analysis import PortfolioAnalysis
from .enums import RebalancingRecommendation, TradeAction
from .trades import AlternativeScenario, CostAnalysis, ExecutionSummary, TradeRecommendation


class RebalancingResult(BaseModel):
    """Complete rebalancing analysis result schema."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    # Analysis metadata
    analysis_timestamp: datetime = Field(default_factory=datetime.now, description="Analysis timestamp")
    portfolio_id: Optional[str] = Field(None, description="Portfolio identifier")

    # Current portfolio state
    current_portfolio: PortfolioAnalysis = Field(..., description="Current portfolio analysis")

    # Rebalancing recommendations
    trade_recommendations: list[TradeRecommendation] = Field(default_factory=list, description="Individual trade recommendations")

    # Projected outcomes
    projected_portfolio: PortfolioAnalysis = Field(..., description="Projected portfolio after rebalancing")

    # Cost analysis
    cost_analysis: CostAnalysis = Field(..., description="Transaction cost analysis")

    # Risk analysis
    current_risk_score: float = Field(..., ge=0, le=10, description="Current portfolio risk score")
    projected_risk_score: float = Field(..., ge=0, le=10, description="Projected risk score after rebalancing")
    risk_improvement: float = Field(..., description="Risk score improvement")

    # Execution summary
    execution_summary: ExecutionSummary = Field(..., description="Execution requirements summary")

    # Alternative scenarios
    alternative_scenarios: list[AlternativeScenario] = Field(
        default_factory=list, max_length=3, description="Alternative rebalancing scenarios"
    )

    # Recommendations
    overall_recommendation: RebalancingRecommendation = Field(..., description="Overall rebalancing recommendation")
    next_review_date: datetime = Field(..., description="Recommended next review date")

    @model_validator(mode="after")
    def validate_result_consistency(self) -> RebalancingResult:
        """Validate rebalancing result consistency."""
        # Validate that trade recommendations match execution summary
        actual_trades = len([t for t in self.trade_recommendations if t.action != TradeAction.HOLD])
        if actual_trades != self.execution_summary.total_trades_required:
            raise ValueError(f"Trade count mismatch: {actual_trades} vs {self.execution_summary.total_trades_required}")

        # Validate risk improvement calculation
        expected_improvement = self.current_risk_score - self.projected_risk_score
        if abs(self.risk_improvement - expected_improvement) > 0.01:
            raise ValueError(f"Risk improvement calculation error: {self.risk_improvement} vs {expected_improvement}")

        return self


class RebalancingHistoryEntry(BaseModel):
    """Historical record of a rebalancing action."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    # Metadata
    entry_id: str = Field(..., description="Unique identifier for this history entry")
    portfolio_id: str = Field(..., description="Portfolio identifier")
    timestamp: datetime = Field(default_factory=datetime.now, description="When rebalancing was executed")

    # Rebalancing details
    rebalancing_result: RebalancingResult = Field(..., description="Complete rebalancing analysis result")
    executed_trades: list[TradeRecommendation] = Field(..., description="Trades that were actually executed")
    execution_status: str = Field(..., description="Status of execution (COMPLETED, PARTIAL, FAILED)")

    # Performance tracking
    portfolio_value_before: float = Field(..., gt=0, description="Portfolio value before rebalancing")
    portfolio_value_after: Optional[float] = Field(None, gt=0, description="Portfolio value after rebalancing")

    # Metrics
    total_transaction_costs: float = Field(..., ge=0, description="Actual transaction costs incurred")
    positions_rebalanced: int = Field(..., ge=0, description="Number of positions actually rebalanced")
    deviation_improvement: float = Field(..., description="Improvement in portfolio deviation from targets")

    # Notes
    execution_notes: Optional[str] = Field(None, description="Notes about the execution")


class PositionHistory(BaseModel):
    """Historical tracking for individual position rebalancing."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    symbol: str = Field(..., description="Position symbol")
    rebalancing_frequency: int = Field(..., ge=0, description="Number of times rebalanced")
    average_deviation: float = Field(..., ge=0, description="Average deviation from target weight")
    max_deviation: float = Field(..., ge=0, description="Maximum deviation observed")
    last_rebalanced: Optional[datetime] = Field(None, description="Last rebalancing date")
    total_trades: int = Field(..., ge=0, description="Total number of trades executed")
    total_transaction_costs: float = Field(..., ge=0, description="Total transaction costs for this position")
