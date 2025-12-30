"""Backtesting and performance models for quantitative analysis."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from finwiz.schemas.quantitative.enums import MarketRegimeType, TradeStatus, TradeType


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

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})

    @field_validator("exit_price")
    @classmethod
    def validate_exit_price_positive(cls, v: float | None) -> float | None:
        """Validate exit price is positive if provided."""
        if v is not None and v <= 0:
            raise ValueError("Exit price must be positive")
        return v


class MarketRegime(BaseModel):
    """Market regime analysis result."""

    regime_type: MarketRegimeType = Field(..., description="Type of market regime")
    confidence: float = Field(..., ge=0, le=1, description="Confidence in regime classification")
    start_date: datetime = Field(..., description="Start date of the regime")
    end_date: datetime | None = Field(None, description="End date of the regime (None if current)")
    characteristics: dict[str, Any] = Field(default_factory=dict, description="Regime characteristics")


class BacktestResult(BaseModel):
    """Comprehensive backtesting result."""

    # Strategy information
    strategy_name: str = Field(..., description="Name of the backtested strategy")
    symbol: str = Field(..., description="Symbol backtested")
    start_date: datetime = Field(..., description="Backtest start date")
    end_date: datetime = Field(..., description="Backtest end date")

    # Performance metrics
    total_return: float = Field(..., description="Total return over the period")
    annualized_return: float = Field(..., description="Annualized return")
    volatility: float = Field(..., description="Annualized volatility")
    sharpe_ratio: float = Field(..., description="Sharpe ratio")
    max_drawdown: float = Field(..., description="Maximum drawdown")

    # Trade statistics
    total_trades: int = Field(..., description="Total number of trades")
    winning_trades: int = Field(..., description="Number of winning trades")
    losing_trades: int = Field(..., description="Number of losing trades")
    win_rate: float = Field(..., description="Percentage of winning trades")

    # Market regime analysis
    regimes: list[MarketRegime] = Field(default_factory=list, description="Market regimes during backtest")


class PerformanceMetrics(BaseModel):
    """Comprehensive performance metrics for a trading strategy or portfolio."""

    # Return metrics
    total_return: float = Field(..., description="Total return over the period")
    annualized_return: float = Field(..., description="Annualized return")
    volatility: float = Field(..., description="Annualized volatility")
    sharpe_ratio: float = Field(..., description="Sharpe ratio")
    sortino_ratio: float = Field(..., description="Sortino ratio")

    # Risk metrics
    max_drawdown: float = Field(..., description="Maximum drawdown")
    max_drawdown_duration: int = Field(..., description="Maximum drawdown duration in days")
    downside_deviation: float = Field(..., description="Downside deviation")
    var_95: float = Field(..., description="Value at Risk (95%)")
    cvar_95: float = Field(..., description="Conditional Value at Risk (95%)")

    # Trade metrics (optional)
    win_rate: float | None = Field(None, description="Percentage of winning trades")
    profit_factor: float | None = Field(None, description="Profit factor")
    avg_win: float | None = Field(None, description="Average winning trade")
    avg_loss: float | None = Field(None, description="Average losing trade")

    # Statistical metrics
    skewness: float = Field(..., description="Return distribution skewness")
    kurtosis: float = Field(..., description="Return distribution kurtosis")
    calmar_ratio: float = Field(..., description="Calmar ratio (annual return / max drawdown)")

    # Benchmark comparison (optional)
    alpha: float | None = Field(None, description="Alpha vs benchmark")
    beta: float | None = Field(None, description="Beta vs benchmark")
    information_ratio: float | None = Field(None, description="Information ratio vs benchmark")
    tracking_error: float | None = Field(None, description="Tracking error vs benchmark")
