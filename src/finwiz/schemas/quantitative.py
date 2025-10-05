"""
Quantitative analysis schemas for FinWiz crew integration.

This module provides Pydantic models for integrating quantitative analysis
capabilities into Stock, ETF, and Crypto crews, including backtesting results,
technical analysis, and performance metrics.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class QuantitativeBacktestResult(BaseModel):
    """Simplified backtesting result for crew integration."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    symbol: str = Field(..., description="Symbol backtested")
    strategy_name: str = Field(..., description="Strategy used for backtesting")

    # Performance metrics
    total_return: float = Field(..., description="Total return percentage")
    annualized_return: float = Field(..., description="Annualized return percentage")
    sharpe_ratio: float = Field(..., description="Sharpe ratio")
    max_drawdown: float = Field(..., description="Maximum drawdown percentage")

    # Trade statistics
    total_trades: int = Field(..., ge=0, description="Total number of trades")
    win_rate: float = Field(..., ge=0, le=1, description="Win rate percentage")

    # Risk metrics
    volatility: float = Field(..., ge=0, description="Annualized volatility")
    var_95: float | None = Field(None, description="Value at Risk (95% confidence)")

    # Execution details
    backtest_start_date: datetime = Field(..., description="Backtest start date")
    backtest_end_date: datetime = Field(..., description="Backtest end date")
    initial_capital: float = Field(..., gt=0, description="Initial capital used")
    final_value: float = Field(..., gt=0, description="Final portfolio value")


class QuantitativeTechnicalAnalysis(BaseModel):
    """Technical analysis result for crew integration."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    symbol: str = Field(..., description="Symbol analyzed")
    timeframe: str = Field(..., description="Timeframe of analysis")

    # Overall signal
    overall_signal: str = Field(..., description="Overall technical signal (BUY/SELL/HOLD)")
    overall_confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence level")
    signal_strength: str = Field(..., description="Signal strength level")

    # Signal counts
    bullish_signals_count: int = Field(default=0, description="Number of bullish signals")
    bearish_signals_count: int = Field(default=0, description="Number of bearish signals")
    neutral_signals_count: int = Field(default=0, description="Number of neutral signals")

    # Key indicators
    rsi_value: float | None = Field(None, description="Current RSI value")
    macd_signal: str | None = Field(None, description="MACD signal description")
    bollinger_position: str | None = Field(None, description="Position relative to Bollinger Bands")

    # Analysis timestamp
    analysis_timestamp: datetime = Field(default_factory=datetime.now, description="When analysis was performed")


class QuantitativePerformanceMetrics(BaseModel):
    """Performance metrics for crew integration."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    symbol: str = Field(..., description="Symbol analyzed")

    # Return metrics
    total_return: float = Field(..., description="Total return over period")
    annualized_return: float = Field(..., description="Annualized return")

    # Risk-adjusted metrics
    sharpe_ratio: float = Field(..., description="Sharpe ratio")
    sortino_ratio: float = Field(..., description="Sortino ratio")
    calmar_ratio: float = Field(..., description="Calmar ratio")

    # Risk metrics
    max_drawdown: float = Field(..., description="Maximum drawdown")
    volatility: float = Field(..., description="Annualized volatility")
    var_95: float = Field(..., description="Value at Risk (95% confidence)")

    # Statistical metrics
    skewness: float = Field(..., description="Skewness of returns")
    kurtosis: float = Field(..., description="Kurtosis of returns")

    # Benchmark comparison (optional)
    alpha: float | None = Field(None, description="Alpha vs benchmark")
    beta: float | None = Field(None, description="Beta vs benchmark")
    information_ratio: float | None = Field(None, description="Information ratio")

    # Period information
    start_date: datetime = Field(..., description="Analysis start date")
    end_date: datetime = Field(..., description="Analysis end date")
    total_days: int = Field(..., description="Total days in analysis")


class QuantitativeRecommendation(BaseModel):
    """Quantitative-based investment recommendation."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    symbol: str = Field(..., description="Symbol for recommendation")
    recommendation: str = Field(..., description="Investment recommendation (BUY/HOLD/SELL)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in recommendation")

    # Quantitative justification
    technical_signal: str = Field(..., description="Technical analysis signal")
    backtest_performance: str | None = Field(None, description="Backtesting performance summary")
    risk_assessment: str = Field(..., description="Risk assessment summary")

    # Target metrics
    target_return: float | None = Field(None, description="Expected return percentage")
    target_timeframe: str | None = Field(None, description="Investment timeframe")
    stop_loss_level: float | None = Field(None, description="Recommended stop loss level")
    take_profit_level: float | None = Field(None, description="Recommended take profit level")

    # Supporting data
    key_indicators: dict[str, Any] = Field(default_factory=dict, description="Key technical indicators")
    risk_metrics: dict[str, float] = Field(default_factory=dict, description="Risk metrics")

    # Analysis metadata
    analysis_date: datetime = Field(default_factory=datetime.now, description="Date of analysis")
    methodology: str = Field(default="quantitative_analysis", description="Analysis methodology used")


class EnhancedStockAnalysis(BaseModel):
    """Enhanced stock analysis with quantitative capabilities."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    # Basic information
    ticker: str = Field(..., description="Stock ticker symbol")
    company_name: str | None = Field(None, description="Company name")

    # Quantitative analysis results
    technical_analysis: QuantitativeTechnicalAnalysis | None = Field(None, description="Technical analysis results")
    backtest_result: QuantitativeBacktestResult | None = Field(None, description="Backtesting results")
    performance_metrics: QuantitativePerformanceMetrics | None = Field(None, description="Performance metrics")

    # Investment recommendation
    quantitative_recommendation: QuantitativeRecommendation | None = Field(None, description="Quantitative recommendation")

    # Analysis metadata
    analysis_timestamp: datetime = Field(default_factory=datetime.now, description="Analysis timestamp")
    quantitative_enabled: bool = Field(default=True, description="Whether quantitative analysis was performed")


class EnhancedETFAnalysis(BaseModel):
    """Enhanced ETF analysis with quantitative capabilities."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    # Basic information
    ticker: str = Field(..., description="ETF ticker symbol")
    fund_name: str | None = Field(None, description="ETF fund name")

    # Quantitative analysis results
    technical_analysis: QuantitativeTechnicalAnalysis | None = Field(None, description="Technical analysis results")
    backtest_result: QuantitativeBacktestResult | None = Field(None, description="Backtesting results")
    performance_metrics: QuantitativePerformanceMetrics | None = Field(None, description="Performance metrics")

    # ETF-specific quantitative metrics
    tracking_error_analysis: dict[str, float] | None = Field(None, description="Tracking error analysis")
    benchmark_correlation: float | None = Field(None, description="Correlation with benchmark")

    # Investment recommendation
    quantitative_recommendation: QuantitativeRecommendation | None = Field(None, description="Quantitative recommendation")

    # Analysis metadata
    analysis_timestamp: datetime = Field(default_factory=datetime.now, description="Analysis timestamp")
    quantitative_enabled: bool = Field(default=True, description="Whether quantitative analysis was performed")


class EnhancedCryptoAnalysis(BaseModel):
    """Enhanced crypto analysis with quantitative capabilities."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    # Basic information
    symbol: str = Field(..., description="Crypto symbol")
    name: str | None = Field(None, description="Cryptocurrency name")

    # Quantitative analysis results
    technical_analysis: QuantitativeTechnicalAnalysis | None = Field(None, description="Technical analysis results")
    backtest_result: QuantitativeBacktestResult | None = Field(None, description="Backtesting results")
    performance_metrics: QuantitativePerformanceMetrics | None = Field(None, description="Performance metrics")

    # Crypto-specific quantitative metrics
    volatility_analysis: dict[str, float] | None = Field(None, description="Volatility analysis")
    correlation_analysis: dict[str, float] | None = Field(None, description="Correlation with other assets")

    # Investment recommendation
    quantitative_recommendation: QuantitativeRecommendation | None = Field(None, description="Quantitative recommendation")

    # Analysis metadata
    analysis_timestamp: datetime = Field(default_factory=datetime.now, description="Analysis timestamp")
    quantitative_enabled: bool = Field(default=True, description="Whether quantitative analysis was performed")
