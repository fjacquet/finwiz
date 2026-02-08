"""
Data models and enums for backtesting.

This module contains Pydantic models and enums used throughout
the backtesting system.
"""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, validator


class PositionSizingMethod(StrEnum):
    """Position sizing methods for backtesting."""

    FIXED_AMOUNT = "fixed_amount"
    PERCENT_OF_PORTFOLIO = "percent_of_portfolio"
    KELLY_CRITERION = "kelly_criterion"
    VOLATILITY_ADJUSTED = "volatility_adjusted"


class TradeType(StrEnum):
    """Types of trades in backtesting."""

    BUY = "BUY"
    SELL = "SELL"
    SHORT = "SHORT"
    COVER = "COVER"


class TradeStatus(StrEnum):
    """Status of trades in backtesting."""

    OPEN = "OPEN"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


class Trade(BaseModel):
    """Represents a single trade in the backtesting system."""

    trade_id: str = Field(..., description="Unique identifier for the trade")
    symbol: str = Field(..., description="Symbol traded")
    trade_type: TradeType = Field(..., description="Type of trade (BUY/SELL/SHORT/COVER)")
    status: TradeStatus = Field(..., description="Current status of the trade")

    # Entry details
    entry_date: datetime = Field(..., description="Date when trade was entered")
    entry_price: float = Field(..., gt=0, description="Price at which trade was entered")
    quantity: int = Field(..., gt=0, description="Number of shares/units traded")

    # Exit details (optional for open trades)
    exit_date: datetime | None = Field(None, description="Date when trade was exited")
    exit_price: float | None = Field(None, description="Price at which trade was exited")

    # Financial metrics
    commission: float = Field(default=0.0, ge=0, description="Commission paid for the trade")
    slippage: float = Field(default=0.0, ge=0, description="Slippage cost for the trade")

    # Performance metrics (calculated)
    pnl: float | None = Field(None, description="Profit/Loss for the trade")
    pnl_percent: float | None = Field(None, description="Profit/Loss percentage")
    holding_period_days: int | None = Field(None, description="Number of days trade was held")

    # Risk management
    stop_loss_price: float | None = Field(None, description="Stop loss price if set")
    take_profit_price: float | None = Field(None, description="Take profit price if set")

    # Strategy context
    strategy_name: str = Field(..., description="Name of strategy that generated the trade")
    signal_strength: float | None = Field(None, ge=0, le=1, description="Strength of signal that triggered trade")

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}

    @validator("exit_price")
    def validate_exit_price_positive(cls, v: float | None) -> float | None:
        """Validate exit price is positive if provided."""
        if v is not None and v <= 0:
            raise ValueError("Exit price must be positive")
        return v

    def calculate_pnl(self) -> None:
        """Calculate PnL metrics for the trade."""
        if self.exit_price is None or self.status != TradeStatus.CLOSED:
            return

        if self.trade_type in [TradeType.BUY, TradeType.COVER]:
            # Long position or covering short
            gross_pnl = (self.exit_price - self.entry_price) * self.quantity
        else:
            # Short position
            gross_pnl = (self.entry_price - self.exit_price) * self.quantity

        # Subtract costs
        total_costs = self.commission + self.slippage
        self.pnl = gross_pnl - total_costs

        # Calculate percentage return
        if self.entry_price > 0:
            self.pnl_percent = (self.pnl / (self.entry_price * self.quantity)) * 100

    def calculate_holding_period(self) -> None:
        """Calculate holding period in days."""
        if self.exit_date is not None:
            self.holding_period_days = (self.exit_date - self.entry_date).days


class BacktestResult(BaseModel):
    """Comprehensive backtesting result."""

    # Strategy information
    strategy_name: str = Field(..., description="Name of the backtested strategy")
    symbol: str = Field(..., description="Symbol backtested")
    start_date: datetime = Field(..., description="Backtest start date")
    end_date: datetime = Field(..., description="Backtest end date")

    # Configuration
    initial_capital: float = Field(..., gt=0, description="Initial capital for backtesting")
    final_value: float = Field(..., gt=0, description="Final portfolio value")

    # Performance metrics
    total_return: float = Field(..., description="Total return percentage")
    annualized_return: float = Field(..., description="Annualized return percentage")
    volatility: float = Field(..., ge=0, description="Annualized volatility")
    sharpe_ratio: float = Field(..., description="Sharpe ratio")
    max_drawdown: float = Field(..., le=0, description="Maximum drawdown percentage")

    # Trade statistics
    total_trades: int = Field(..., ge=0, description="Total number of trades")
    winning_trades: int = Field(..., ge=0, description="Number of winning trades")
    losing_trades: int = Field(..., ge=0, description="Number of losing trades")
    win_rate: float = Field(default=0.0, ge=0, le=1, description="Win rate percentage")

    # Risk metrics
    var_95: float | None = Field(None, description="Value at Risk (95% confidence)")
    cvar_95: float | None = Field(None, description="Conditional Value at Risk (95%)")
    calmar_ratio: float | None = Field(None, description="Calmar ratio (return/max drawdown)")

    # Detailed trade records
    trades: list[Trade] = Field(default_factory=list, description="List of all trades executed")

    # Daily portfolio values for analysis
    portfolio_values: dict[str, float] = Field(default_factory=dict, description="Daily portfolio values")

    # Benchmark comparison
    benchmark_return: float | None = Field(None, description="Benchmark return for comparison")
    alpha: float | None = Field(None, description="Alpha relative to benchmark")
    beta: float | None = Field(None, description="Beta relative to benchmark")

    # Execution timestamp
    backtest_timestamp: datetime = Field(default_factory=datetime.now, description="When backtest was executed")

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}

    @validator("win_rate", always=True)
    def calculate_win_rate(cls, v: float, values: dict[str, Any]) -> float:
        """Calculate win rate from winning and total trades if not explicitly set."""
        # If win_rate is the default value (0.0), calculate it
        if v == 0.0 and "total_trades" in values and values["total_trades"] > 0:
            winning_trades = values.get("winning_trades", 0)
            return float(winning_trades) / float(values["total_trades"])
        return v
