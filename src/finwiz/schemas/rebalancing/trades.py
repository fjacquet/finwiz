"""
Trade-Related Portfolio Rebalancing Models.

Models for trade recommendations, cost analysis, and execution planning.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .enums import TradeAction, UrgencyLevel


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
