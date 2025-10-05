"""
Core Portfolio Rebalancing Models.

Basic data models for holdings, configuration, and price data.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .enums import RebalancingMethod


class Holding(BaseModel):
    """Individual portfolio holding."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    symbol: str = Field(..., description="Stock/ETF/Crypto symbol", min_length=1, max_length=10)
    shares: float = Field(..., gt=0, description="Number of shares held")
    cost_basis: Optional[float] = Field(None, gt=0, description="Average cost basis per share")
    acquisition_date: Optional[datetime] = Field(None, description="Date of acquisition")

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
