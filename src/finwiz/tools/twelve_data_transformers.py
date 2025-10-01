"""
Twelve Data Transformers.

This module provides data transformation and analysis functionality for Twelve Data API responses,
including technical indicator analysis, signal generation, and data processing.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from finwiz.tools.logger import get_logger

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

    This class provides methods to analyze technical indicators and generate
    trading signals from raw API data.
    """

    def __init__(self) -> None:
        """Initialize the transformers."""
        pass

    def analyze_rsi_signal(self, rsi_value: float | None) -> tuple[str, float]:
        """
        Analyze RSI value for overbought/oversold signals.

        Args:
            rsi_value: RSI value to analyze

        Returns:
            Tuple of (signal, strength) where signal is overbought/oversold/neutral

        """
        if rsi_value is None:
            return "neutral", 0.0

        if rsi_value >= 70:
            strength = min(1.0, (rsi_value - 70) / 30)
            return "overbought", strength
        elif rsi_value <= 30:
            strength = min(1.0, (30 - rsi_value) / 30)
            return "oversold", strength
        else:
            return "neutral", 0.3

    def analyze_macd_signal(self, macd_values: list[MACDValue]) -> tuple[str, float]:
        """
        Analyze MACD for crossover signals.

        Args:
            macd_values: List of MACD values (most recent first)

        Returns:
            Tuple of (signal, strength) where signal is bullish/bearish/neutral

        """
        if len(macd_values) < 2:
            return "neutral", 0.0

        current = macd_values[0]
        previous = macd_values[1]

        # Check for crossover
        if current.macd > current.macd_signal and previous.macd <= previous.macd_signal:
            # Bullish crossover
            strength = min(
                1.0,
                abs(current.macd - current.macd_signal) / abs(current.macd_signal) if current.macd_signal != 0 else 0.5,
            )
            return "bullish", strength
        elif current.macd < current.macd_signal and previous.macd >= previous.macd_signal:
            # Bearish crossover
            strength = min(
                1.0,
                abs(current.macd - current.macd_signal) / abs(current.macd_signal) if current.macd_signal != 0 else 0.5,
            )
            return "bearish", strength
        else:
            return "neutral", 0.2

    def analyze_bollinger_squeeze(self, bb_values: list[BollingerBandsValue]) -> str:
        """
        Analyze Bollinger Bands for squeeze conditions.

        Args:
            bb_values: List of Bollinger Bands values

        Returns:
            String indicating squeeze/expansion/normal condition

        """
        if len(bb_values) < 20:
            return "normal"

        # Calculate recent band widths
        recent_widths = []
        for value in bb_values[:10]:
            width = (value.upper_band - value.lower_band) / value.middle_band
            recent_widths.append(width)

        # Calculate historical average
        historical_widths = []
        for value in bb_values[10:]:
            width = (value.upper_band - value.lower_band) / value.middle_band
            historical_widths.append(width)

        if not historical_widths:
            return "normal"

        avg_recent = sum(recent_widths) / len(recent_widths)
        avg_historical = sum(historical_widths) / len(historical_widths)

        if avg_recent < avg_historical * 0.8:
            return "squeeze"
        elif avg_recent > avg_historical * 1.2:
            return "expansion"
        else:
            return "normal"

    def analyze_bollinger_position(self, bb_values: list[BollingerBandsValue], symbol: str) -> str:
        """
        Analyze price position relative to Bollinger Bands.

        Args:
            bb_values: List of Bollinger Bands values
            symbol: Stock symbol (for logging)

        Returns:
            String indicating position relative to bands

        """
        if not bb_values:
            return "within_bands"

        # This is a simplified analysis - in practice, you'd need current price
        # For now, we'll use the middle band as a proxy
        bb_values[0]

        # Simplified logic - would need actual price data
        return "within_bands"

    def analyze_stochastic_signal(self, k_value: float | None, d_value: float | None) -> str:
        """
        Analyze Stochastic for overbought/oversold conditions.

        Args:
            k_value: %K value
            d_value: %D value

        Returns:
            String indicating overbought/oversold/neutral condition

        """
        if k_value is None or d_value is None:
            return "neutral"

        avg_value = (k_value + d_value) / 2

        if avg_value >= 80:
            return "overbought"
        elif avg_value <= 20:
            return "oversold"
        else:
            return "neutral"

    def analyze_stochastic_crossover(self, stoch_values: list[StochasticValue]) -> str:
        """
        Analyze Stochastic for crossover signals.

        Args:
            stoch_values: List of Stochastic values (most recent first)

        Returns:
            String indicating bullish/bearish/neutral crossover

        """
        if len(stoch_values) < 2:
            return "neutral"

        current = stoch_values[0]
        previous = stoch_values[1]

        if current.slow_k > current.slow_d and previous.slow_k <= previous.slow_d:
            return "bullish"
        elif current.slow_k < current.slow_d and previous.slow_k >= previous.slow_d:
            return "bearish"
        else:
            return "neutral"

    def determine_overall_signal(
        self,
        rsi_data: RSIData | None,
        macd_data: MACDData | None,
        bollinger_data: BollingerBandsData | None,
        stochastic_data: StochasticData | None,
    ) -> tuple[str, float, int]:
        """
        Determine overall signal from all indicators.

        Args:
            rsi_data: RSI indicator data
            macd_data: MACD indicator data
            bollinger_data: Bollinger Bands data
            stochastic_data: Stochastic oscillator data

        Returns:
            Tuple of (signal, confidence, consensus_count)

        """
        bullish_signals = 0
        bearish_signals = 0
        total_indicators = 0
        total_strength = 0

        # Analyze RSI
        if rsi_data:
            total_indicators += 1
            if rsi_data.signal == "oversold":
                bullish_signals += 1
                total_strength += rsi_data.signal_strength
            elif rsi_data.signal == "overbought":
                bearish_signals += 1
                total_strength += rsi_data.signal_strength
            else:
                total_strength += 0.2

        # Analyze MACD
        if macd_data:
            total_indicators += 1
            if macd_data.crossover_signal == "bullish":
                bullish_signals += 1
                total_strength += macd_data.signal_strength
            elif macd_data.crossover_signal == "bearish":
                bearish_signals += 1
                total_strength += macd_data.signal_strength
            else:
                total_strength += 0.2

        # Analyze Bollinger Bands
        if bollinger_data:
            total_indicators += 1
            if bollinger_data.position_signal == "below_lower":
                bullish_signals += 1
                total_strength += 0.6
            elif bollinger_data.position_signal == "above_upper":
                bearish_signals += 1
                total_strength += 0.6
            else:
                total_strength += 0.2

        # Analyze Stochastic
        if stochastic_data:
            total_indicators += 1
            if stochastic_data.signal == "oversold" or stochastic_data.crossover_signal == "bullish":
                bullish_signals += 1
                total_strength += 0.5
            elif stochastic_data.signal == "overbought" or stochastic_data.crossover_signal == "bearish":
                bearish_signals += 1
                total_strength += 0.5
            else:
                total_strength += 0.2

        if total_indicators == 0:
            return "neutral", 0.0, 0

        # Determine consensus
        consensus = max(bullish_signals, bearish_signals)
        confidence = (total_strength / total_indicators) * (consensus / total_indicators)

        if bullish_signals > bearish_signals:
            return "buy", confidence, consensus
        elif bearish_signals > bullish_signals:
            return "sell", confidence, consensus
        else:
            return "neutral", confidence * 0.5, consensus

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

        if "values" in api_response and api_response["values"]:
            for item in api_response["values"]:
                value = TechnicalIndicatorValue(datetime=item["datetime"], value=float(item["rsi"]))
                values.append(value)

            # Most recent value is first
            current_value = values[0].value if values else None

        # Analyze signal
        signal, signal_strength = self.analyze_rsi_signal(current_value)

        return RSIData(
            symbol=symbol,
            interval=interval,
            time_period=time_period,
            values=values,
            current_value=current_value,
            signal=signal,
            signal_strength=signal_strength,
        )

    def transform_macd_response(
        self, api_response: dict[str, Any], symbol: str, interval: str, fast_period: int, slow_period: int, signal_period: int
    ) -> MACDData:
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

        if "values" in api_response and api_response["values"]:
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
        crossover_signal, signal_strength = self.analyze_macd_signal(values)

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

    def transform_bollinger_response(
        self, api_response: dict[str, Any], symbol: str, interval: str, time_period: int, std_dev: int
    ) -> BollingerBandsData:
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

        if "values" in api_response and api_response["values"]:
            for item in api_response["values"]:
                value = BollingerBandsValue(
                    datetime=item["datetime"],
                    upper_band=float(item["upper_band"]),
                    middle_band=float(item["middle_band"]),
                    lower_band=float(item["lower_band"]),
                )
                values.append(value)

        # Analyze squeeze condition and position
        squeeze_condition = self.analyze_bollinger_squeeze(values)
        position_signal = self.analyze_bollinger_position(values, symbol)

        return BollingerBandsData(
            symbol=symbol,
            interval=interval,
            time_period=time_period,
            std_dev=std_dev,
            values=values,
            squeeze_condition=squeeze_condition,
            position_signal=position_signal,
        )

    def transform_stochastic_response(
        self, api_response: dict[str, Any], symbol: str, interval: str, fastkperiod: int, slowkperiod: int, slowdperiod: int
    ) -> StochasticData:
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

        if "values" in api_response and api_response["values"]:
            for item in api_response["values"]:
                value = StochasticValue(datetime=item["datetime"], slow_k=float(item["slow_k"]), slow_d=float(item["slow_d"]))
                values.append(value)

            if values:
                current_k = values[0].slow_k
                current_d = values[0].slow_d

        # Analyze signals
        signal = self.analyze_stochastic_signal(current_k, current_d)
        crossover_signal = self.analyze_stochastic_crossover(values)

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
