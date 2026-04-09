"""
Data transformers for Twelve Data API responses.

This module provides data transformation functionality for Twelve Data API responses,
converting raw API data into structured Pydantic models with analyzed signals.
"""

from __future__ import annotations

from typing import Any

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

    def transform_rsi_response(self, api_response: dict[str, Any], symbol: str, interval: str, time_period: int) -> RSIData:
        """
        Transform RSI API response into structured data.

        Args:
            api_response: Raw API response
            symbol: Stock symbol
            interval: Time interval
            time_period: RSI calculation period

        Returns:
            RSIData object with analyzed signals

        """
        values = []
        current_value = None

        if api_response.get("values"):
            for item in api_response["values"]:
                value = TechnicalIndicatorValue(datetime=item["datetime"], value=float(item["rsi"]))
                values.append(value)

            # Most recent value is first
            current_value = values[0].value if values else None

        # Analyze signal
        signal, signal_strength = self.signal_analyzer.analyze_rsi_signal(current_value)

        return RSIData(
            symbol=symbol,
            interval=interval,
            time_period=time_period,
            values=values,
            current_value=current_value,
            signal=signal,
            signal_strength=signal_strength,
        )

    def transform_macd_response(self, api_response: dict[str, Any], symbol: str, interval: str, fast_period: int, slow_period: int, signal_period: int) -> MACDData:
        """
        Transform MACD API response into structured data.

        Args:
            api_response: Raw API response
            symbol: Stock symbol
            interval: Time interval
            fast_period: Fast EMA period
            slow_period: Slow EMA period
            signal_period: Signal line EMA period

        Returns:
            MACDData object with analyzed signals

        """
        values = []
        current_macd = None
        current_signal = None

        if api_response.get("values"):
            for item in api_response["values"]:
                value = MACDValue(
                    datetime=item["datetime"],
                    macd=float(item["macd"]),
                    macd_signal=float(item["macd_signal"]),
                    macd_histogram=float(item["macd_histogram"]),
                )
                values.append(value)

            if values:
                current_macd = values[0].macd
                current_signal = values[0].macd_signal

        # Analyze crossover signal
        crossover_signal, signal_strength = self.signal_analyzer.analyze_macd_signal(values)

        return MACDData(
            symbol=symbol,
            interval=interval,
            fast_period=fast_period,
            slow_period=slow_period,
            signal_period=signal_period,
            values=values,
            current_macd=current_macd,
            current_signal=current_signal,
            crossover_signal=crossover_signal,
            signal_strength=signal_strength,
        )

    def transform_bollinger_response(self, api_response: dict[str, Any], symbol: str, interval: str, time_period: int, std_dev: int) -> BollingerBandsData:
        """
        Transform Bollinger Bands API response into structured data.

        Args:
            api_response: Raw API response
            symbol: Stock symbol
            interval: Time interval
            time_period: Moving average period
            std_dev: Standard deviation multiplier

        Returns:
            BollingerBandsData object with analyzed signals

        """
        values = []

        if api_response.get("values"):
            for item in api_response["values"]:
                value = BollingerBandsValue(
                    datetime=item["datetime"],
                    upper_band=float(item["upper_band"]),
                    middle_band=float(item["middle_band"]),
                    lower_band=float(item["lower_band"]),
                )
                values.append(value)

        # Analyze squeeze condition and position
        squeeze_condition = self.signal_analyzer.analyze_bollinger_squeeze(values)
        position_signal = self.signal_analyzer.analyze_bollinger_position(values, symbol)

        return BollingerBandsData(
            symbol=symbol,
            interval=interval,
            time_period=time_period,
            std_dev=std_dev,
            values=values,
            squeeze_condition=squeeze_condition,
            position_signal=position_signal,
        )

    def transform_stochastic_response(self, api_response: dict[str, Any], symbol: str, interval: str, fastkperiod: int, slowkperiod: int, slowdperiod: int) -> StochasticData:
        """
        Transform Stochastic API response into structured data.

        Args:
            api_response: Raw API response
            symbol: Stock symbol
            interval: Time interval
            fastkperiod: Fast %K period
            slowkperiod: Slow %K period
            slowdperiod: Slow %D period

        Returns:
            StochasticData object with analyzed signals

        """
        values = []
        current_k = None
        current_d = None

        if api_response.get("values"):
            for item in api_response["values"]:
                value = StochasticValue(datetime=item["datetime"], slow_k=float(item["slow_k"]), slow_d=float(item["slow_d"]))
                values.append(value)

            if values:
                current_k = values[0].slow_k
                current_d = values[0].slow_d

        # Analyze signals
        signal = self.signal_analyzer.analyze_stochastic_signal(current_k, current_d)
        crossover_signal = self.signal_analyzer.analyze_stochastic_crossover(values)

        return StochasticData(
            symbol=symbol,
            interval=interval,
            fastkperiod=fastkperiod,
            slowkperiod=slowkperiod,
            slowdperiod=slowdperiod,
            values=values,
            current_k=current_k,
            current_d=current_d,
            signal=signal,
            crossover_signal=crossover_signal,
        )
