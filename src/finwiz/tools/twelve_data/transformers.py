"""
Data transformers for Twelve Data API responses.

This module provides data transformation functionality for Twelve Data API responses,
converting raw API data into structured Pydantic models with analyzed signals.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from finwiz.tools.logger import get_logger
from finwiz.tools.twelve_data.validators import SignalAnalyzer

logger = get_logger(__name__)


class TechnicalIndicatorValue(BaseModel):
    """Individual technical indicator data point."""

    model_config = ConfigDict(extra="forbid")

    datetime: str = Field(..., description="Timestamp of the data point")
    value: float = Field(..., description="Indicator value")


class RSIData(BaseModel):
    """RSI (Relative Strength Index) indicator data."""

    model_config = ConfigDict(extra="forbid")

    symbol: str = Field(..., description="Ticker symbol")
    interval: str = Field(..., description="Time interval")
    time_period: int = Field(..., description="RSI calculation period")
    values: list[TechnicalIndicatorValue] = Field(default_factory=list)
    current_value: float | None = Field(None, description="Most recent RSI value")
    signal: str = Field(..., description="overbought, oversold, or neutral")
    signal_strength: float = Field(..., ge=0.0, le=1.0, description="Signal strength")


class MACDValue(BaseModel):
    """Individual MACD data point."""

    model_config = ConfigDict(extra="forbid")

    datetime: str = Field(..., description="Timestamp of the data point")
    macd: float = Field(..., description="MACD line value")
    macd_signal: float = Field(..., description="MACD signal line value")
    macd_histogram: float = Field(..., description="MACD histogram value")


class MACDData(BaseModel):
    """MACD (Moving Average Convergence Divergence) indicator data."""

    model_config = ConfigDict(extra="forbid")

    symbol: str = Field(..., description="Ticker symbol")
    interval: str = Field(..., description="Time interval")
    fast_period: int = Field(..., description="Fast EMA period")
    slow_period: int = Field(..., description="Slow EMA period")
    signal_period: int = Field(..., description="Signal line EMA period")
    values: list[MACDValue] = Field(default_factory=list)
    current_macd: float | None = Field(None, description="Most recent MACD value")
    current_signal: float | None = Field(None, description="Most recent signal value")
    crossover_signal: str = Field(..., description="bullish, bearish, or neutral")
    signal_strength: float = Field(..., ge=0.0, le=1.0, description="Signal strength")


class BollingerBandsValue(BaseModel):
    """Individual Bollinger Bands data point."""

    model_config = ConfigDict(extra="forbid")

    datetime: str = Field(..., description="Timestamp of the data point")
    upper_band: float = Field(..., description="Upper Bollinger Band")
    middle_band: float = Field(..., description="Middle Bollinger Band (SMA)")
    lower_band: float = Field(..., description="Lower Bollinger Band")


class BollingerBandsData(BaseModel):
    """Bollinger Bands indicator data."""

    model_config = ConfigDict(extra="forbid")

    symbol: str = Field(..., description="Ticker symbol")
    interval: str = Field(..., description="Time interval")
    time_period: int = Field(..., description="Moving average period")
    std_dev: int = Field(..., description="Standard deviation multiplier")
    values: list[BollingerBandsValue] = Field(default_factory=list)
    squeeze_condition: str = Field(..., description="squeeze, expansion, or normal")
    position_signal: str = Field(..., description="above_upper, below_lower, or within_bands")


class StochasticValue(BaseModel):
    """Individual Stochastic oscillator data point."""

    model_config = ConfigDict(extra="forbid")

    datetime: str = Field(..., description="Timestamp of the data point")
    slow_k: float = Field(..., description="Slow %K value")
    slow_d: float = Field(..., description="Slow %D value")


class StochasticData(BaseModel):
    """Stochastic oscillator indicator data."""

    model_config = ConfigDict(extra="forbid")

    symbol: str = Field(..., description="Ticker symbol")
    interval: str = Field(..., description="Time interval")
    fastkperiod: int = Field(..., description="Fast %K period")
    slowkperiod: int = Field(..., description="Slow %K period")
    slowdperiod: int = Field(..., description="Slow %D period")
    values: list[StochasticValue] = Field(default_factory=list)
    current_k: float | None = Field(None, description="Most recent %K value")
    current_d: float | None = Field(None, description="Most recent %D value")
    signal: str = Field(..., description="overbought, oversold, or neutral")
    crossover_signal: str = Field(..., description="bullish, bearish, or neutral")


class TechnicalIndicatorSummary(BaseModel):
    """Summary of all technical indicators for a symbol."""

    model_config = ConfigDict(extra="forbid")

    symbol: str = Field(..., description="Ticker symbol")
    interval: str = Field(..., description="Time interval")
    timestamp: str = Field(..., description="Analysis timestamp")
    rsi_data: RSIData | None = Field(None, description="RSI indicator data")
    macd_data: MACDData | None = Field(None, description="MACD indicator data")
    bollinger_data: BollingerBandsData | None = Field(None, description="Bollinger Bands data")
    stochastic_data: StochasticData | None = Field(None, description="Stochastic oscillator data")
    overall_signal: str = Field(..., description="buy, sell, or neutral")
    signal_confidence: float = Field(..., ge=0.0, le=1.0, description="Overall signal confidence")
    consensus_indicators: int = Field(..., description="Number of indicators in consensus")


class TwelveDataTransformers:
    """
    Data transformers for Twelve Data API responses.

    This class provides methods to transform raw API responses into structured
    Pydantic models with analyzed trading signals.
    """

    def __init__(self) -> None:
        """Initialize the transformers."""
        self.signal_analyzer = SignalAnalyzer()
