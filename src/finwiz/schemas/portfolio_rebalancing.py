"""
Portfolio rebalancing schemas for FinWiz.

This module provides Pydantic models for portfolio rebalancing functionality,
including portfolio configuration, holdings, trade recommendations, and
comprehensive validation logic.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class TradeAction(str, Enum):
    """Trade action enumeration."""

    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class UrgencyLevel(str, Enum):
    """Trade urgency level enumeration."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RebalancingMethod(str, Enum):
    """Rebalancing optimization method enumeration."""

    MINIMIZE_TRADES = "MINIMIZE_TRADES"
    MINIMIZE_COSTS = "MINIMIZE_COSTS"
    RISK_AWARE = "RISK_AWARE"
    TAX_EFFICIENT = "TAX_EFFICIENT"


class RebalancingRecommendation(str, Enum):
    """Overall rebalancing recommendation enumeration."""

    REBALANCE_NOW = "REBALANCE_NOW"
    REBALANCE_SOON = "REBALANCE_SOON"
    MONITOR = "MONITOR"
    NO_ACTION = "NO_ACTION"


class Holding(BaseModel):
    """Individual portfolio holding."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    symbol: str = Field(..., description="Stock/ETF/Crypto symbol", min_length=1, max_length=10)
    shares: float = Field(..., gt=0, description="Number of shares held")
    cost_basis: float | None = Field(None, gt=0, description="Average cost basis per share")
    acquisition_date: datetime | None = Field(None, description="Date of acquisition")

    @field_validator("symbol")
    @classmethod
    def validate_symbol_format(cls, v: str) -> str:
        """Validate symbol format."""
        if not v.replace("-", "").replace(".", "").isalnum():
            raise ValueError("Symbol must contain only alphanumeric characters, hyphens, and periods")
        return v.upper()


class PortfolioConfiguration(BaseModel):
    """Portfolio rebalancing configuration schema."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    # Portfolio holdings
    holdings: list[Holding] = Field(..., min_length=1, description="Current portfolio holdings")

    # Target allocation
    target_weights: dict[str, float] = Field(..., description="Target percentage weights for each symbol (0.0 to 1.0)")

    # Tolerance settings
    tolerance_bands: dict[str, float] = Field(
        default_factory=dict, description="Tolerance bands for each position (defaults to global tolerance)"
    )
    global_tolerance: float = Field(default=0.05, gt=0.0, le=0.5, description="Default tolerance band (0.05 = ±5%)")

    # Capital constraints
    available_capital: float = Field(
        default=0.0, description="Available capital for rebalancing (positive=invest, negative=withdraw)"
    )

    # Trading parameters
    transaction_cost_rate: float = Field(default=0.001, ge=0.0, le=0.1, description="Transaction cost as percentage of trade value")
    min_trade_size: float = Field(default=0.01, gt=0.0, description="Minimum trade size to execute")

    # Optimization settings
    rebalancing_method: RebalancingMethod = Field(
        default=RebalancingMethod.MINIMIZE_TRADES, description="Rebalancing optimization method"
    )

    @field_validator("target_weights")
    @classmethod
    def validate_target_weights_values(cls, v: dict[str, float]) -> dict[str, float]:
        """Validate individual target weight values."""
        for symbol, weight in v.items():
            if not (0.0 <= weight <= 1.0):
                raise ValueError(f"Target weight for {symbol} must be between 0.0 and 1.0, got {weight}")
        return v

    @field_validator("tolerance_bands")
    @classmethod
    def validate_tolerance_bands_values(cls, v: dict[str, float]) -> dict[str, float]:
        """Validate tolerance band values."""
        for symbol, tolerance in v.items():
            if not (0.001 <= tolerance <= 0.5):
                raise ValueError(f"Tolerance for {symbol} must be between 0.1% and 50%, got {tolerance}")
        return v

    @model_validator(mode="after")
    def validate_portfolio_consistency(self) -> PortfolioConfiguration:
        """Validate overall portfolio configuration consistency."""
        # Check that target weights sum to 100% or less
        total_weight = sum(self.target_weights.values())
        if total_weight > 1.01:  # Allow small rounding errors
            raise ValueError(f"Target weights sum to {total_weight:.1%}, must be ≤ 100%")

        # Check that all holdings have target weights
        holding_symbols = {holding.symbol for holding in self.holdings}
        target_symbols = set(self.target_weights.keys())

        missing_targets = holding_symbols - target_symbols
        if missing_targets:
            raise ValueError(f"Missing target weights for holdings: {', '.join(missing_targets)}")

        extra_targets = target_symbols - holding_symbols
        if extra_targets:
            raise ValueError(f"Target weights specified for non-held symbols: {', '.join(extra_targets)}")

        # Validate tolerance bands reference valid symbols
        invalid_tolerance_symbols = set(self.tolerance_bands.keys()) - target_symbols
        if invalid_tolerance_symbols:
            raise ValueError(f"Tolerance bands specified for invalid symbols: {', '.join(invalid_tolerance_symbols)}")

        return self


class PriceData(BaseModel):
    """Market price data for a symbol."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    symbol: str = Field(..., description="Symbol")
    price: float = Field(..., gt=0, description="Current market price")
    timestamp: datetime = Field(default_factory=datetime.now, description="Price timestamp")
    source: str = Field(default="yahoo_finance", description="Data source")
    currency: str = Field(default="USD", description="Price currency")


class TradeRecommendation(BaseModel):
    """Individual trade recommendation schema."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    # Trade details
    symbol: str = Field(..., description="Stock symbol")
    action: TradeAction = Field(..., description="Trade action (BUY/SELL/HOLD)")
    quantity: float = Field(..., description="Number of shares to trade")
    current_price: float = Field(..., gt=0, description="Current market price")

    # Financial impact
    trade_value: float = Field(..., description="Total value of trade")
    estimated_commission: float = Field(..., ge=0, description="Estimated commission cost")
    estimated_spread_cost: float = Field(..., ge=0, description="Estimated bid-ask spread cost")
    total_estimated_cost: float = Field(..., ge=0, description="Total estimated transaction cost")

    # Portfolio impact
    current_weight: float = Field(..., ge=0, le=1, description="Current portfolio weight")
    target_weight: float = Field(..., ge=0, le=1, description="Target portfolio weight")
    weight_deviation: float = Field(..., description="Current deviation from target")
    projected_weight_after_trade: float = Field(..., ge=0, le=1, description="Projected weight after trade")

    # Execution details
    priority: int = Field(..., ge=1, le=10, description="Execution priority (1=highest)")
    urgency: UrgencyLevel = Field(..., description="Trade urgency level")
    rationale: str = Field(..., min_length=10, description="Rationale for trade recommendation")

    # Risk considerations
    tax_implications: str | None = Field(None, description="Tax implications if applicable")
    market_impact_warning: str | None = Field(None, description="Market impact warnings")

    @model_validator(mode="after")
    def validate_trade_consistency(self) -> TradeRecommendation:
        """Validate trade recommendation consistency."""
        # Validate trade value calculation
        expected_trade_value = abs(self.quantity * self.current_price)
        if abs(self.trade_value - expected_trade_value) > 0.01:
            raise ValueError(f"Trade value {self.trade_value} doesn't match quantity × price {expected_trade_value}")

        # Validate total cost calculation
        expected_total_cost = self.estimated_commission + self.estimated_spread_cost
        if abs(self.total_estimated_cost - expected_total_cost) > 0.01:
            raise ValueError(f"Total cost {self.total_estimated_cost} doesn't match sum of components {expected_total_cost}")

        # Validate action consistency with quantity
        if self.action == TradeAction.BUY and self.quantity <= 0:
            raise ValueError("BUY action requires positive quantity")
        elif self.action == TradeAction.SELL and self.quantity <= 0:
            raise ValueError("SELL action requires positive quantity")
        elif self.action == TradeAction.HOLD and self.quantity != 0:
            raise ValueError("HOLD action should have zero quantity")

        return self


class PortfolioAnalysis(BaseModel):
    """Analysis of portfolio composition."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    total_value: float = Field(..., gt=0, description="Total portfolio value")
    weightings: dict[str, float] = Field(..., description="Current percentage weightings")
    deviations_from_target: dict[str, float] = Field(..., description="Deviations from target weights")
    positions_needing_rebalancing: list[str] = Field(default_factory=list, description="Symbols needing rebalancing")
    risk_metrics: dict[str, float] = Field(default_factory=dict, description="Portfolio risk metrics")

    @field_validator("weightings")
    @classmethod
    def validate_weightings_sum(cls, v: dict[str, float]) -> dict[str, float]:
        """Validate that weightings sum to approximately 1.0."""
        total = sum(v.values())
        if not (0.95 <= total <= 1.05):  # Allow some tolerance for rounding
            raise ValueError(f"Portfolio weightings sum to {total:.3f}, should be close to 1.0")
        return v


class CostAnalysis(BaseModel):
    """Transaction cost analysis."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    total_transaction_costs: float = Field(..., ge=0, description="Total estimated transaction costs")
    commission_costs: float = Field(..., ge=0, description="Total commission costs")
    spread_costs: float = Field(..., ge=0, description="Total bid-ask spread costs")
    market_impact_costs: float = Field(default=0.0, ge=0, description="Estimated market impact costs")
    cost_as_percentage: float = Field(..., ge=0, description="Costs as percentage of portfolio value")
    break_even_days: int | None = Field(None, ge=0, description="Days to break even on rebalancing costs")


class AlternativeScenario(BaseModel):
    """Alternative rebalancing scenario."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    scenario_name: str = Field(..., description="Scenario description")
    modified_parameters: dict[str, Any] = Field(..., description="Parameters changed from base scenario")
    projected_outcome: str = Field(..., description="Expected outcome description")
    cost_difference: float = Field(..., description="Cost difference vs base scenario")
    risk_difference: float = Field(..., description="Risk difference vs base scenario")


class ExecutionSummary(BaseModel):
    """Summary of rebalancing execution requirements."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    total_trades_required: int = Field(..., ge=0, description="Total number of trades required")
    positions_requiring_action: int = Field(..., ge=0, description="Number of positions requiring action")
    positions_within_tolerance: int = Field(..., ge=0, description="Number of positions within tolerance")
    estimated_execution_time: str = Field(..., description="Estimated time to execute all trades")
    capital_required: float = Field(..., description="Net capital required (positive) or freed (negative)")


class RebalancingResult(BaseModel):
    """Complete rebalancing analysis result schema."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    # Analysis metadata
    analysis_timestamp: datetime = Field(default_factory=datetime.now, description="Analysis timestamp")
    portfolio_id: str | None = Field(None, description="Portfolio identifier")

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


class RebalancingNeed(BaseModel):
    """Individual position rebalancing need assessment."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    symbol: str = Field(..., description="Symbol requiring rebalancing")
    current_weight: float = Field(..., ge=0, le=1, description="Current portfolio weight")
    target_weight: float = Field(..., ge=0, le=1, description="Target portfolio weight")
    deviation: float = Field(..., description="Absolute deviation from target")
    tolerance_band: float = Field(..., gt=0, description="Tolerance band for this position")
    exceeds_tolerance: bool = Field(..., description="Whether deviation exceeds tolerance")
    urgency_score: float = Field(..., ge=0, le=1, description="Urgency score (0=low, 1=high)")
    recommended_action: TradeAction = Field(..., description="Recommended action")


class PortfolioMetrics(BaseModel):
    """Portfolio-level metrics and statistics."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    total_value: float = Field(..., gt=0, description="Total portfolio value")
    number_of_positions: int = Field(..., ge=1, description="Number of positions")
    largest_position_weight: float = Field(..., ge=0, le=1, description="Weight of largest position")
    concentration_risk_score: float = Field(..., ge=0, le=10, description="Concentration risk score")
    diversification_ratio: float = Field(..., ge=0, le=1, description="Diversification ratio")
    effective_number_of_positions: float = Field(..., ge=1, description="Effective number of positions")
    turnover_if_rebalanced: float = Field(..., ge=0, description="Portfolio turnover if rebalanced")
    cash_weight: float = Field(default=0.0, ge=0, le=1, description="Cash as percentage of portfolio")


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
    portfolio_value_after: float | None = Field(None, gt=0, description="Portfolio value after rebalancing")

    # Metrics
    total_transaction_costs: float = Field(..., ge=0, description="Actual transaction costs incurred")
    positions_rebalanced: int = Field(..., ge=0, description="Number of positions actually rebalanced")
    deviation_improvement: float = Field(..., description="Improvement in portfolio deviation from targets")

    # Notes
    execution_notes: str | None = Field(None, description="Notes about the execution")


class PositionHistory(BaseModel):
    """Historical tracking for individual position rebalancing."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    symbol: str = Field(..., description="Position symbol")
    rebalancing_frequency: int = Field(..., ge=0, description="Number of times rebalanced")
    average_deviation: float = Field(..., ge=0, description="Average deviation from target weight")
    max_deviation: float = Field(..., ge=0, description="Maximum deviation observed")
    last_rebalanced: datetime | None = Field(None, description="Last rebalancing date")
    total_trades: int = Field(..., ge=0, description="Total number of trades executed")
    total_transaction_costs: float = Field(..., ge=0, description="Total transaction costs for this position")


class PerformanceAttribution(BaseModel):
    """Performance attribution analysis for rebalancing effectiveness."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    # Time period
    start_date: datetime = Field(..., description="Analysis start date")
    end_date: datetime = Field(..., description="Analysis end date")

    # Performance metrics
    rebalanced_return: float = Field(..., description="Return with rebalancing")
    buy_and_hold_return: float = Field(..., description="Return without rebalancing")
    rebalancing_alpha: float = Field(..., description="Excess return from rebalancing")

    # Risk metrics
    rebalanced_volatility: float = Field(..., ge=0, description="Volatility with rebalancing")
    buy_and_hold_volatility: float = Field(..., ge=0, description="Volatility without rebalancing")
    risk_reduction: float = Field(..., description="Risk reduction from rebalancing")

    # Cost analysis
    total_rebalancing_costs: float = Field(..., ge=0, description="Total costs of rebalancing")
    net_benefit: float = Field(..., description="Net benefit after costs")
    cost_drag: float = Field(..., description="Performance drag from transaction costs")

    # Frequency analysis
    rebalancing_frequency: int = Field(..., ge=0, description="Number of rebalancing events")
    average_days_between_rebalancing: float = Field(..., gt=0, description="Average days between rebalancing")


class TrendAnalysis(BaseModel):
    """Trend analysis for optimal rebalancing frequency identification."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    # Analysis parameters
    analysis_period_days: int = Field(..., gt=0, description="Analysis period in days")
    frequency_scenarios: list[int] = Field(..., description="Rebalancing frequencies tested (days)")

    # Optimal frequency results
    optimal_frequency_days: int = Field(..., gt=0, description="Optimal rebalancing frequency in days")
    optimal_tolerance_band: float = Field(..., gt=0, description="Optimal tolerance band percentage")

    # Performance by frequency
    frequency_performance: dict[int, float] = Field(..., description="Performance by frequency (days -> return)")
    frequency_costs: dict[int, float] = Field(..., description="Costs by frequency (days -> total cost)")
    frequency_risk: dict[int, float] = Field(..., description="Risk by frequency (days -> volatility)")

    # Recommendations
    recommended_frequency: int = Field(..., gt=0, description="Recommended rebalancing frequency")
    recommended_tolerance: float = Field(..., gt=0, description="Recommended tolerance band")
    confidence_score: float = Field(..., ge=0, le=1, description="Confidence in recommendations")


class RebalancingAnalytics(BaseModel):
    """Comprehensive analytics dashboard data."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    # Portfolio identification
    portfolio_id: str = Field(..., description="Portfolio identifier")
    analysis_date: datetime = Field(default_factory=datetime.now, description="Analysis date")

    # Historical summary
    total_rebalancing_events: int = Field(..., ge=0, description="Total rebalancing events")
    first_rebalancing_date: datetime | None = Field(None, description="First rebalancing date")
    last_rebalancing_date: datetime | None = Field(None, description="Last rebalancing date")

    # Performance metrics
    performance_attribution: PerformanceAttribution = Field(..., description="Performance attribution analysis")
    trend_analysis: TrendAnalysis = Field(..., description="Trend analysis results")

    # Position-level analytics
    position_histories: list[PositionHistory] = Field(..., description="Individual position histories")
    most_rebalanced_positions: list[str] = Field(..., description="Positions requiring most frequent rebalancing")

    # Effectiveness metrics
    average_deviation_improvement: float = Field(..., ge=0, description="Average improvement in portfolio deviation")
    rebalancing_success_rate: float = Field(..., ge=0, le=1, description="Success rate of rebalancing recommendations")
    cost_efficiency_score: float = Field(..., ge=0, le=10, description="Cost efficiency score (1-10)")

    # Recommendations
    strategy_recommendations: list[str] = Field(..., description="Strategic recommendations based on analysis")
    tolerance_adjustment_suggestions: dict[str, float] = Field(
        default_factory=dict, description="Suggested tolerance adjustments by position"
    )
    target_weight_suggestions: dict[str, float] = Field(default_factory=dict, description="Suggested target weight adjustments")
