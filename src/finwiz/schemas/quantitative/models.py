"""
Quantitative analysis models for FinWiz.

This module contains Pydantic models for quantitative analysis, backtesting,
performance metrics, technical analysis, and portfolio optimization.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# Enums for quantitative analysis
class TradeType(str, Enum):
    """Type of trade."""

    BUY = "BUY"
    SELL = "SELL"
    SHORT = "SHORT"
    COVER = "COVER"


class TradeStatus(str, Enum):
    """Status of trade."""

    OPEN = "OPEN"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


class MarketRegimeType(str, Enum):
    """Market regime types."""

    BULL = "BULL"
    BEAR = "BEAR"
    SIDEWAYS = "SIDEWAYS"
    VOLATILE = "VOLATILE"


class SignalType(str, Enum):
    """Technical analysis signal types."""

    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    STRONG_BUY = "STRONG_BUY"
    STRONG_SELL = "STRONG_SELL"


# Backtesting Models
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


# Performance Metrics Models
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


# Technical Analysis Models
class TechnicalSignal(BaseModel):
    """Represents a technical analysis signal."""

    signal_type: SignalType = Field(..., description="Type of signal")
    strength: float = Field(..., ge=0, le=1, description="Signal strength (0-1)")
    confidence: float = Field(..., ge=0, le=1, description="Confidence in signal")
    timestamp: datetime = Field(..., description="When signal was generated")
    indicator_name: str = Field(..., description="Name of indicator generating signal")
    price_level: float | None = Field(None, description="Price level associated with signal")


class IndicatorSignal(BaseModel):
    """Individual technical indicator signal (legacy compatibility)."""

    indicator: str = Field(..., description="Indicator name")
    signal: SignalType = Field(..., description="Signal type")
    strength: float = Field(..., ge=0, le=1, description="Signal strength")
    value: float = Field(..., description="Indicator value")
    timestamp: datetime = Field(..., description="Signal timestamp")


class ConfluenceZone(BaseModel):
    """Represents a confluence zone where multiple indicators align."""

    price_level: float = Field(..., description="Price level of confluence")
    support_count: int = Field(..., description="Number of supporting indicators")
    resistance_count: int = Field(..., description="Number of resistance indicators")
    strength: float = Field(..., ge=0, le=1, description="Overall confluence strength")
    indicators: list[str] = Field(..., description="List of contributing indicators")
    zone_type: Literal["support", "resistance", "neutral"] = Field(..., description="Type of confluence zone")

    @field_validator("strength")
    @classmethod
    def validate_strength_range(cls, v: float) -> float:
        """Validate strength is between 0 and 1."""
        if not 0 <= v <= 1:
            raise ValueError("Strength must be between 0 and 1")
        return v


class FibonacciLevels(BaseModel):
    """Fibonacci retracement and extension levels."""

    high_price: float = Field(..., description="High price for Fibonacci calculation")
    low_price: float = Field(..., description="Low price for Fibonacci calculation")

    # Retracement levels
    retracement_23_6: float = Field(..., description="23.6% retracement level")
    retracement_38_2: float = Field(..., description="38.2% retracement level")
    retracement_50_0: float = Field(..., description="50.0% retracement level")
    retracement_61_8: float = Field(..., description="61.8% retracement level")
    retracement_78_6: float = Field(..., description="78.6% retracement level")

    # Extension levels
    extension_127_2: float = Field(..., description="127.2% extension level")
    extension_161_8: float = Field(..., description="161.8% extension level")
    extension_261_8: float = Field(..., description="261.8% extension level")


class SupportResistance(BaseModel):
    """Support and resistance levels analysis."""

    support_levels: list[float] = Field(..., description="Identified support levels")
    resistance_levels: list[float] = Field(..., description="Identified resistance levels")
    current_price: float = Field(..., description="Current price for context")

    # Strength indicators
    support_strength: list[float] = Field(..., description="Strength of each support level (0-1)")
    resistance_strength: list[float] = Field(..., description="Strength of each resistance level (0-1)")

    # Key levels
    key_support: float | None = Field(None, description="Most significant support level")
    key_resistance: float | None = Field(None, description="Most significant resistance level")

    @model_validator(mode="after")
    def validate_strength_lists_length(self) -> "SupportResistance":
        """Validate that strength lists match level lists length."""
        if len(self.support_strength) != len(self.support_levels):
            raise ValueError("Support strength list must match support levels list length")
        if len(self.resistance_strength) != len(self.resistance_levels):
            raise ValueError("Resistance strength list must match resistance levels list length")
        return self


class TechnicalIndicatorValue(BaseModel):
    """Individual technical indicator data point."""

    value: float = Field(..., description="Indicator value")
    signal: SignalType | None = Field(None, description="Signal generated by indicator")
    timestamp: datetime = Field(..., description="Timestamp of the value")


class TechnicalIndicatorSummary(BaseModel):
    """Summary of all technical indicators for a symbol."""

    symbol: str = Field(..., description="Symbol analyzed")
    timestamp: datetime = Field(..., description="Analysis timestamp")

    # Moving averages
    sma_20: float | None = Field(None, description="20-period Simple Moving Average")
    sma_50: float | None = Field(None, description="50-period Simple Moving Average")
    sma_200: float | None = Field(None, description="200-period Simple Moving Average")
    ema_12: float | None = Field(None, description="12-period Exponential Moving Average")
    ema_26: float | None = Field(None, description="26-period Exponential Moving Average")

    # Momentum indicators
    rsi: float | None = Field(None, description="Relative Strength Index")
    macd: float | None = Field(None, description="MACD line")
    macd_signal: float | None = Field(None, description="MACD signal line")
    macd_histogram: float | None = Field(None, description="MACD histogram")

    # Volatility indicators
    bollinger_upper: float | None = Field(None, description="Bollinger Band upper")
    bollinger_middle: float | None = Field(None, description="Bollinger Band middle")
    bollinger_lower: float | None = Field(None, description="Bollinger Band lower")
    atr: float | None = Field(None, description="Average True Range")


class TechnicalAnalysisResult(BaseModel):
    """Comprehensive technical analysis result."""

    symbol: str = Field(..., description="Symbol analyzed")
    timestamp: datetime = Field(..., description="Analysis timestamp")
    current_price: float = Field(..., description="Current price")

    # Overall assessment
    overall_signal: SignalType = Field(..., description="Overall technical signal")
    signal_strength: float = Field(..., ge=0, le=1, description="Overall signal strength")
    confidence: float = Field(..., ge=0, le=1, description="Confidence in analysis")

    # Component analysis
    indicators: TechnicalIndicatorSummary = Field(..., description="Technical indicators summary")
    signals: list[TechnicalSignal] = Field(..., description="Individual technical signals")
    confluence_zones: list[ConfluenceZone] = Field(..., description="Price confluence zones")
    support_resistance: SupportResistance = Field(..., description="Support and resistance analysis")
    fibonacci: FibonacciLevels | None = Field(None, description="Fibonacci analysis")

    # Market structure
    trend_direction: Literal["up", "down", "sideways"] = Field(..., description="Overall trend direction")
    trend_strength: float = Field(..., ge=0, le=1, description="Trend strength")

    # Risk levels
    stop_loss_suggestion: float | None = Field(None, description="Suggested stop loss level")
    take_profit_suggestion: float | None = Field(None, description="Suggested take profit level")


# Portfolio Optimization Models
class OptimizationConstraint(BaseModel):
    """Portfolio optimization constraint."""

    constraint_type: Literal["weight", "turnover", "sector", "risk"] = Field(..., description="Type of constraint")
    target: str = Field(..., description="Target asset or constraint identifier")
    min_value: float | None = Field(None, description="Minimum value for constraint")
    max_value: float | None = Field(None, description="Maximum value for constraint")
    exact_value: float | None = Field(None, description="Exact value for constraint")


class PortfolioInputs(BaseModel):
    """Inputs for portfolio optimization."""

    assets: list[str] = Field(..., description="List of asset symbols")
    expected_returns: list[float] = Field(..., description="Expected returns for each asset")
    covariance_matrix: list[list[float]] = Field(..., description="Covariance matrix")
    constraints: list[OptimizationConstraint] = Field(default_factory=list, description="Optimization constraints")

    # Optimization parameters
    risk_aversion: float = Field(1.0, description="Risk aversion parameter")
    target_return: float | None = Field(None, description="Target return for optimization")
    target_risk: float | None = Field(None, description="Target risk for optimization")

    @model_validator(mode="after")
    def validate_dimensions(self) -> "PortfolioInputs":
        """Validate that dimensions match."""
        n_assets = len(self.assets)
        if len(self.expected_returns) != n_assets:
            raise ValueError("Expected returns length must match number of assets")
        if len(self.covariance_matrix) != n_assets:
            raise ValueError("Covariance matrix rows must match number of assets")
        for i, row in enumerate(self.covariance_matrix):
            if len(row) != n_assets:
                raise ValueError(f"Covariance matrix row {i} length must match number of assets")
        return self


class PortfolioMetrics(BaseModel):
    """Portfolio performance metrics."""

    expected_return: float = Field(..., description="Expected portfolio return")
    volatility: float = Field(..., description="Portfolio volatility")
    sharpe_ratio: float = Field(..., description="Sharpe ratio")

    # Risk metrics
    var_95: float = Field(..., description="Value at Risk (95%)")
    cvar_95: float = Field(..., description="Conditional Value at Risk (95%)")
    max_drawdown: float = Field(..., description="Maximum drawdown")

    # Diversification metrics
    diversification_ratio: float = Field(..., description="Diversification ratio")
    concentration_index: float = Field(..., description="Concentration index (HHI)")
    effective_number_assets: float = Field(..., description="Effective number of assets")


class OptimizationResult(BaseModel):
    """Result of portfolio optimization."""

    weights: dict[str, float] = Field(..., description="Optimal portfolio weights")
    metrics: PortfolioMetrics = Field(..., description="Portfolio performance metrics")

    # Optimization details
    optimization_method: str = Field(..., description="Optimization method used")
    convergence_status: str = Field(..., description="Optimization convergence status")
    iterations: int = Field(..., description="Number of optimization iterations")

    # Constraints satisfaction
    constraints_satisfied: bool = Field(..., description="Whether all constraints were satisfied")
    constraint_violations: list[str] = Field(default_factory=list, description="List of constraint violations")


class EfficientFrontierPoint(BaseModel):
    """Point on the efficient frontier."""

    expected_return: float = Field(..., description="Expected return for this point")
    volatility: float = Field(..., description="Volatility for this point")
    sharpe_ratio: float = Field(..., description="Sharpe ratio for this point")
    weights: dict[str, float] = Field(..., description="Portfolio weights for this point")


# Screening Models
class ScreeningFilter(BaseModel):
    """Individual screening filter."""

    field: str = Field(..., description="Field to filter on")
    operator: Literal["gt", "lt", "gte", "lte", "eq", "ne", "in", "not_in"] = Field(..., description="Comparison operator")
    value: Any = Field(..., description="Value to compare against")
    weight: float = Field(1.0, description="Weight of this filter in scoring")


class StockData(BaseModel):
    """Stock data for screening."""

    symbol: str = Field(..., description="Stock symbol")
    name: str = Field(..., description="Company name")
    sector: str | None = Field(None, description="Sector")
    industry: str | None = Field(None, description="Industry")
    market_cap: float | None = Field(None, description="Market capitalization")

    # Valuation metrics
    pe_ratio: float | None = Field(None, description="Price-to-earnings ratio")
    pb_ratio: float | None = Field(None, description="Price-to-book ratio")
    ps_ratio: float | None = Field(None, description="Price-to-sales ratio")
    peg_ratio: float | None = Field(None, description="Price/earnings to growth ratio")

    # Financial metrics
    revenue_growth: float | None = Field(None, description="Revenue growth rate")
    earnings_growth: float | None = Field(None, description="Earnings growth rate")
    roe: float | None = Field(None, description="Return on equity")
    roa: float | None = Field(None, description="Return on assets")
    debt_to_equity: float | None = Field(None, description="Debt-to-equity ratio")

    # Market metrics
    beta: float | None = Field(None, description="Beta coefficient")
    dividend_yield: float | None = Field(None, description="Dividend yield")
    volume: int | None = Field(None, description="Average trading volume")


class ScreeningScore(BaseModel):
    """Screening score for a stock."""

    symbol: str = Field(..., description="Stock symbol")
    total_score: float = Field(..., description="Total screening score")
    component_scores: dict[str, float] = Field(..., description="Individual component scores")
    rank: int | None = Field(None, description="Rank among screened stocks")
    percentile: float | None = Field(None, description="Percentile ranking")


class ScreeningResult(BaseModel):
    """Result of stock screening."""

    filters_applied: list[ScreeningFilter] = Field(..., description="Filters that were applied")
    total_universe: int = Field(..., description="Total number of stocks in universe")
    filtered_count: int = Field(..., description="Number of stocks passing filters")

    # Results
    stocks: list[StockData] = Field(..., description="Stocks that passed screening")
    scores: list[ScreeningScore] = Field(..., description="Screening scores")

    # Metadata
    screening_date: datetime = Field(..., description="Date when screening was performed")
    execution_time: float = Field(..., description="Execution time in seconds")


class ScreeningSummary(BaseModel):
    """Summary of screening results."""

    total_screened: int = Field(..., description="Total number of stocks screened")
    passed_filters: int = Field(..., description="Number passing all filters")
    top_performers: list[str] = Field(..., description="Top performing symbols")

    # Statistics
    avg_score: float = Field(..., description="Average screening score")
    score_std: float = Field(..., description="Standard deviation of scores")
    score_range: tuple[float, float] = Field(..., description="Score range (min, max)")


# Risk Management Models
class RiskWarning(BaseModel):
    """Individual risk warning."""

    warning_type: Literal["concentration", "volatility", "drawdown", "correlation", "liquidity"] = Field(
        ..., description="Type of risk warning"
    )
    severity: Literal["low", "medium", "high", "critical"] = Field(..., description="Severity level")
    message: str = Field(..., description="Warning message")
    affected_assets: list[str] = Field(..., description="Assets affected by this warning")
    recommended_action: str = Field(..., description="Recommended action to address warning")
    threshold_breached: float | None = Field(None, description="Threshold value that was breached")
    current_value: float | None = Field(None, description="Current value that triggered warning")


class ConcentrationLimits(BaseModel):
    """Concentration limit configuration."""

    max_single_position: float = Field(0.1, description="Maximum weight for single position")
    max_sector_exposure: float = Field(0.3, description="Maximum exposure to single sector")
    max_country_exposure: float = Field(0.5, description="Maximum exposure to single country")
    min_number_positions: int = Field(10, description="Minimum number of positions")


class TurnoverLimits(BaseModel):
    """Portfolio turnover limit configuration."""

    max_monthly_turnover: float = Field(0.2, description="Maximum monthly turnover")
    max_annual_turnover: float = Field(1.0, description="Maximum annual turnover")
    transaction_cost_threshold: float = Field(0.01, description="Transaction cost threshold")


class VolatilityThresholds(BaseModel):
    """Market volatility threshold configuration."""

    low_volatility: float = Field(0.1, description="Low volatility threshold")
    medium_volatility: float = Field(0.2, description="Medium volatility threshold")
    high_volatility: float = Field(0.3, description="High volatility threshold")
    extreme_volatility: float = Field(0.5, description="Extreme volatility threshold")


class RiskManagerConfig(BaseModel):
    """Risk manager configuration."""

    concentration_limits: ConcentrationLimits = Field(default_factory=ConcentrationLimits)
    turnover_limits: TurnoverLimits = Field(default_factory=TurnoverLimits)
    volatility_thresholds: VolatilityThresholds = Field(default_factory=VolatilityThresholds)

    # Global settings
    enable_risk_monitoring: bool = Field(True, description="Enable risk monitoring")
    alert_frequency: Literal["real_time", "daily", "weekly"] = Field("daily", description="Alert frequency")


class RiskAssessment(BaseModel):
    """Comprehensive risk assessment result."""

    assessment_date: datetime = Field(..., description="Date of risk assessment")
    portfolio_id: str = Field(..., description="Portfolio identifier")

    # Risk metrics
    portfolio_volatility: float = Field(..., description="Portfolio volatility")
    var_95: float = Field(..., description="Value at Risk (95%)")
    cvar_95: float = Field(..., description="Conditional Value at Risk (95%)")
    max_drawdown: float = Field(..., description="Maximum drawdown")

    # Risk warnings
    warnings: list[RiskWarning] = Field(default_factory=list, description="Risk warnings")
    overall_risk_level: Literal["low", "medium", "high", "critical"] = Field(..., description="Overall risk level")

    # Recommendations
    risk_reduction_suggestions: list[str] = Field(default_factory=list, description="Risk reduction suggestions")
    position_adjustments: dict[str, float] = Field(default_factory=dict, description="Suggested position adjustments")


# Scenario Analysis Models
class ScenarioParameters(BaseModel):
    """Parameters for scenario analysis."""

    scenario_name: str = Field(..., description="Name of the scenario")
    description: str = Field(..., description="Description of the scenario")

    # Market parameters
    market_shock: float = Field(0.0, description="Market shock percentage")
    volatility_multiplier: float = Field(1.0, description="Volatility multiplier")
    correlation_adjustment: float = Field(0.0, description="Correlation adjustment")

    # Asset-specific shocks
    asset_shocks: dict[str, float] = Field(default_factory=dict, description="Asset-specific shocks")
    sector_shocks: dict[str, float] = Field(default_factory=dict, description="Sector-specific shocks")

    # Time parameters
    shock_duration: int = Field(1, description="Duration of shock in periods")
    recovery_periods: int = Field(0, description="Number of recovery periods")


class MonteCarloResult(BaseModel):
    """Result of Monte Carlo simulation."""

    simulation_name: str = Field(..., description="Name of the simulation")
    num_simulations: int = Field(..., description="Number of simulations run")
    time_horizon: int = Field(..., description="Time horizon in periods")

    # Results statistics
    mean_return: float = Field(..., description="Mean return across simulations")
    median_return: float = Field(..., description="Median return across simulations")
    std_return: float = Field(..., description="Standard deviation of returns")

    # Percentile results
    percentile_5: float = Field(..., description="5th percentile return")
    percentile_25: float = Field(..., description="25th percentile return")
    percentile_75: float = Field(..., description="75th percentile return")
    percentile_95: float = Field(..., description="95th percentile return")

    # Risk metrics
    probability_of_loss: float = Field(..., description="Probability of loss")
    expected_shortfall: float = Field(..., description="Expected shortfall (CVaR)")
    maximum_loss: float = Field(..., description="Maximum loss observed")

    # Simulation metadata
    random_seed: int | None = Field(None, description="Random seed used")
    execution_time: float = Field(..., description="Execution time in seconds")


# Data Models
class PriceData(BaseModel):
    """Price data structure for technical analysis."""

    symbol: str = Field(..., description="Symbol for the price data")
    timestamp: datetime = Field(..., description="Timestamp of the data point")

    # OHLCV data
    open: float = Field(..., description="Opening price")
    high: float = Field(..., description="High price")
    low: float = Field(..., description="Low price")
    close: float = Field(..., description="Closing price")
    volume: int = Field(..., description="Trading volume")

    # Adjusted prices (optional)
    adj_close: float | None = Field(None, description="Adjusted closing price")

    # Additional fields
    dividend: float | None = Field(None, description="Dividend amount")
    split_ratio: float | None = Field(None, description="Stock split ratio")

    @field_validator("high")
    @classmethod
    def validate_high_price(cls, v: float, info: Any) -> float:
        """Validate high price is >= low price."""
        if hasattr(info, "data") and "low" in info.data and v < info.data["low"]:
            raise ValueError("High price must be >= low price")
        return v

    @field_validator("volume")
    @classmethod
    def validate_volume_positive(cls, v: int) -> int:
        """Validate volume is non-negative."""
        if v < 0:
            raise ValueError("Volume must be non-negative")
        return v


class CachedDataInfo(BaseModel):
    """Information about cached data."""

    cache_key: str = Field(..., description="Cache key identifier")
    data_type: str = Field(..., description="Type of cached data")
    created_at: datetime = Field(..., description="When data was cached")
    expires_at: datetime | None = Field(None, description="When data expires")
    size_bytes: int = Field(..., description="Size of cached data in bytes")
    hit_count: int = Field(0, description="Number of cache hits")
    last_accessed: datetime | None = Field(None, description="Last access time")
