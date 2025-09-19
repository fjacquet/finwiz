"""
Technical analysis engine with TA-Lib integration for FinWiz.

This module provides comprehensive technical analysis capabilities including:
- TA-Lib wrapper functions for technical indicators
- Calculation methods for SMA, RSI, MACD, Bollinger Bands, and other indicators
- Confluence detection and signal generation capabilities
- Multi-timeframe analysis support
- Signal strength scoring and validation
"""

import warnings
from datetime import datetime
from enum import Enum
from typing import Any

import numpy as np
import pandas as pd
import talib
from pydantic import BaseModel, Field, validator

from finwiz.quantitative.config import TechnicalIndicator, get_quant_config
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)

# Suppress TA-Lib warnings for cleaner output
warnings.filterwarnings("ignore", category=RuntimeWarning, module="talib")


class SignalType(str, Enum):
    """Types of technical analysis signals."""

    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    STRONG_BUY = "STRONG_BUY"
    STRONG_SELL = "STRONG_SELL"


class SignalStrength(str, Enum):
    """Signal strength levels."""

    VERY_WEAK = "very_weak"
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    VERY_STRONG = "very_strong"


class TechnicalSignal(BaseModel):
    """Represents a technical analysis signal."""

    indicator: str = Field(..., description="Name of the technical indicator")
    signal_type: SignalType = Field(..., description="Type of signal generated")
    strength: SignalStrength = Field(..., description="Strength of the signal")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence level (0.0 to 1.0)")
    timestamp: datetime = Field(..., description="When the signal was generated")
    price_level: float = Field(..., description="Price level when signal was generated")
    description: str = Field(..., description="Human-readable description of the signal")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional signal metadata")

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class ConfluenceZone(BaseModel):
    """Represents a confluence zone where multiple indicators align."""

    price_level: float = Field(..., description="Price level of the confluence zone")
    signal_type: SignalType = Field(..., description="Overall signal type for the zone")
    strength: SignalStrength = Field(..., description="Combined strength of all signals")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence level")
    contributing_signals: list[TechnicalSignal] = Field(..., description="Signals contributing to the confluence")
    zone_range: tuple[float, float] = Field(..., description="Price range of the confluence zone (min, max)")
    timestamp: datetime = Field(..., description="When the confluence was detected")

    @validator("zone_range")
    def validate_zone_range(cls, v: tuple[float, float]) -> tuple[float, float]:
        """Validate that zone range is properly ordered."""
        if v[0] > v[1]:
            raise ValueError("Zone range minimum must be less than maximum")
        return v


class TechnicalIndicatorResult(BaseModel):
    """Result from a technical indicator calculation."""

    indicator: TechnicalIndicator = Field(..., description="Type of technical indicator")
    values: dict[str, float | list[float]] = Field(..., description="Calculated indicator values")
    signals: list[TechnicalSignal] = Field(default_factory=list, description="Generated signals")
    parameters: dict[str, Any] = Field(..., description="Parameters used for calculation")
    calculation_timestamp: datetime = Field(default_factory=datetime.now, description="When calculation was performed")

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class TechnicalAnalysisResult(BaseModel):
    """Comprehensive technical analysis result."""

    symbol: str = Field(..., description="Stock symbol analyzed")
    timeframe: str = Field(..., description="Timeframe of the analysis")
    analysis_timestamp: datetime = Field(default_factory=datetime.now, description="When analysis was performed")

    # Individual indicator results
    indicator_results: dict[str, TechnicalIndicatorResult] = Field(
        default_factory=dict, description="Results from individual indicators"
    )

    # Overall analysis
    overall_signal: SignalType = Field(..., description="Overall technical signal")
    overall_confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence level")
    signal_strength: SignalStrength = Field(..., description="Overall signal strength")

    # Confluence analysis
    confluence_zones: list[ConfluenceZone] = Field(default_factory=list, description="Detected confluence zones")

    # Summary statistics
    bullish_signals_count: int = Field(default=0, description="Number of bullish signals")
    bearish_signals_count: int = Field(default=0, description="Number of bearish signals")
    neutral_signals_count: int = Field(default=0, description="Number of neutral signals")

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class TechnicalAnalysisEngine:
    """
    Technical analysis engine with TA-Lib integration.

    Provides comprehensive technical analysis capabilities including:
    - Multiple technical indicators with TA-Lib backend
    - Signal generation and confluence detection
    - Multi-timeframe analysis support
    - Customizable parameters and thresholds
    """

    def __init__(self, config: Any | None = None) -> None:
        """
        Initialize technical analysis engine.

        Args:
            config: Quantitative analysis configuration

        """
        self.config = config or get_quant_config()
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")

        # Default parameters for indicators
        self.default_params = {
            TechnicalIndicator.SMA: {"periods": [20, 50, 200]},
            TechnicalIndicator.EMA: {"periods": [12, 26, 50]},
            TechnicalIndicator.RSI: {"period": 14, "overbought": 70, "oversold": 30},
            TechnicalIndicator.MACD: {"fast": 12, "slow": 26, "signal": 9},
            TechnicalIndicator.BOLLINGER_BANDS: {"period": 20, "std_dev": 2},
            TechnicalIndicator.STOCHASTIC: {"k_period": 14, "d_period": 3, "overbought": 80, "oversold": 20},
            TechnicalIndicator.ATR: {"period": 14},
            TechnicalIndicator.ADX: {"period": 14, "trend_threshold": 25},
            TechnicalIndicator.CCI: {"period": 20, "overbought": 100, "oversold": -100},
            TechnicalIndicator.WILLIAMS_R: {"period": 14, "overbought": -20, "oversold": -80},
            TechnicalIndicator.FIBONACCI: {"lookback_period": 50},
        }

    def analyze_symbol(
        self,
        data: pd.DataFrame,
        symbol: str,
        timeframe: str = "1d",
        indicators: list[TechnicalIndicator] | None = None,
    ) -> TechnicalAnalysisResult:
        """
        Perform comprehensive technical analysis on a symbol.

        Args:
            data: OHLCV data DataFrame
            symbol: Stock symbol
            timeframe: Timeframe of the data
            indicators: List of indicators to calculate (None = use config defaults)

        Returns:
            Comprehensive technical analysis result

        """
        self.logger.info(f"Starting technical analysis for {symbol} on {timeframe} timeframe")

        if indicators is None:
            indicators = self.config.enabled_indicators

        # Validate input data
        self._validate_data(data)

        # Calculate individual indicators
        indicator_results = {}
        all_signals = []

        for indicator in indicators:
            try:
                result = self._calculate_indicator(data, indicator, symbol)
                indicator_results[indicator.value] = result
                all_signals.extend(result.signals)
                self.logger.debug(f"Calculated {indicator.value} for {symbol}")
            except Exception as e:
                self.logger.error(f"Error calculating {indicator.value} for {symbol}: {e}")
                continue

        # Detect confluence zones
        confluence_zones = self._detect_confluence_zones(all_signals, data)

        # Generate overall signal
        overall_signal, overall_confidence, signal_strength = self._generate_overall_signal(all_signals)

        # Count signal types
        bullish_count = sum(1 for s in all_signals if s.signal_type in [SignalType.BUY, SignalType.STRONG_BUY])
        bearish_count = sum(1 for s in all_signals if s.signal_type in [SignalType.SELL, SignalType.STRONG_SELL])
        neutral_count = sum(1 for s in all_signals if s.signal_type == SignalType.HOLD)

        result = TechnicalAnalysisResult(
            symbol=symbol,
            timeframe=timeframe,
            indicator_results=indicator_results,
            overall_signal=overall_signal,
            overall_confidence=overall_confidence,
            signal_strength=signal_strength,
            confluence_zones=confluence_zones,
            bullish_signals_count=bullish_count,
            bearish_signals_count=bearish_count,
            neutral_signals_count=neutral_count,
        )

        self.logger.info(
            f"Technical analysis complete for {symbol}: {overall_signal.value} "
            f"(confidence: {overall_confidence:.2f}, {len(confluence_zones)} confluence zones)"
        )

        return result

    def calculate_sma(self, data: pd.DataFrame, periods: list[int]) -> TechnicalIndicatorResult:
        """
        Calculate Simple Moving Average using TA-Lib.

        Args:
            data: OHLCV data DataFrame
            periods: List of periods to calculate

        Returns:
            Technical indicator result with SMA values and signals

        """
        close_prices = data["Close"].values.astype(np.float64)
        sma_values = {}
        signals = []

        for period in periods:
            if len(close_prices) < period:
                self.logger.warning(f"Insufficient data for SMA({period}): need {period}, have {len(close_prices)}")
                continue

            sma = talib.SMA(close_prices, timeperiod=period)
            sma_values[f"SMA_{period}"] = sma.tolist()

            # Generate signals based on price vs SMA
            current_price = close_prices[-1]
            current_sma = sma[-1]

            if not np.isnan(current_sma):
                if current_price > current_sma * 1.02:  # 2% above SMA
                    signal_type = SignalType.BUY
                    strength = SignalStrength.MODERATE
                elif current_price < current_sma * 0.98:  # 2% below SMA
                    signal_type = SignalType.SELL
                    strength = SignalStrength.MODERATE
                else:
                    signal_type = SignalType.HOLD
                    strength = SignalStrength.WEAK

                confidence = min(0.9, abs(current_price - current_sma) / current_sma * 10)

                signals.append(
                    TechnicalSignal(
                        indicator=f"SMA_{period}",
                        signal_type=signal_type,
                        strength=strength,
                        confidence=confidence,
                        timestamp=datetime.now(),
                        price_level=current_price,
                        description=f"Price is {((current_price / current_sma - 1) * 100):.1f}% "
                        f"{'above' if current_price > current_sma else 'below'} SMA({period})",
                        metadata={"sma_value": current_sma, "period": period},
                    )
                )

        return TechnicalIndicatorResult(
            indicator=TechnicalIndicator.SMA,
            values=sma_values,
            signals=signals,
            parameters={"periods": periods},
        )

    def calculate_ema(self, data: pd.DataFrame, periods: list[int]) -> TechnicalIndicatorResult:
        """
        Calculate Exponential Moving Average using TA-Lib.

        Args:
            data: OHLCV data DataFrame
            periods: List of periods to calculate

        Returns:
            Technical indicator result with EMA values and signals

        """
        close_prices = data["Close"].values.astype(np.float64)
        ema_values = {}
        signals = []

        for period in periods:
            if len(close_prices) < period:
                self.logger.warning(f"Insufficient data for EMA({period}): need {period}, have {len(close_prices)}")
                continue

            ema = talib.EMA(close_prices, timeperiod=period)
            ema_values[f"EMA_{period}"] = ema.tolist()

            # Generate signals based on price vs EMA
            current_price = close_prices[-1]
            current_ema = ema[-1]

            if not np.isnan(current_ema):
                if current_price > current_ema * 1.015:  # 1.5% above EMA (more sensitive than SMA)
                    signal_type = SignalType.BUY
                    strength = SignalStrength.MODERATE
                elif current_price < current_ema * 0.985:  # 1.5% below EMA
                    signal_type = SignalType.SELL
                    strength = SignalStrength.MODERATE
                else:
                    signal_type = SignalType.HOLD
                    strength = SignalStrength.WEAK

                confidence = min(0.9, abs(current_price - current_ema) / current_ema * 15)

                signals.append(
                    TechnicalSignal(
                        indicator=f"EMA_{period}",
                        signal_type=signal_type,
                        strength=strength,
                        confidence=confidence,
                        timestamp=datetime.now(),
                        price_level=current_price,
                        description=f"Price is {((current_price / current_ema - 1) * 100):.1f}% "
                        f"{'above' if current_price > current_ema else 'below'} EMA({period})",
                        metadata={"ema_value": current_ema, "period": period},
                    )
                )

        return TechnicalIndicatorResult(
            indicator=TechnicalIndicator.EMA,
            values=ema_values,
            signals=signals,
            parameters={"periods": periods},
        )

    def calculate_rsi(
        self, data: pd.DataFrame, period: int = 14, overbought: float = 70, oversold: float = 30
    ) -> TechnicalIndicatorResult:
        """
        Calculate Relative Strength Index using TA-Lib.

        Args:
            data: OHLCV data DataFrame
            period: RSI calculation period
            overbought: Overbought threshold
            oversold: Oversold threshold

        Returns:
            Technical indicator result with RSI values and signals

        """
        close_prices = data["Close"].values.astype(np.float64)

        if len(close_prices) < period + 1:
            raise ValueError(f"Insufficient data for RSI({period}): need {period + 1}, have {len(close_prices)}")

        rsi = talib.RSI(close_prices, timeperiod=period)
        current_rsi = rsi[-1]

        signals = []

        if not np.isnan(current_rsi):
            if current_rsi > overbought:
                signal_type = SignalType.SELL
                strength = SignalStrength.STRONG if current_rsi > 80 else SignalStrength.MODERATE
                confidence = min(0.95, (current_rsi - overbought) / (100 - overbought))
                description = f"RSI is overbought at {current_rsi:.1f}"
            elif current_rsi < oversold:
                signal_type = SignalType.BUY
                strength = SignalStrength.STRONG if current_rsi < 20 else SignalStrength.MODERATE
                confidence = min(0.95, (oversold - current_rsi) / oversold)
                description = f"RSI is oversold at {current_rsi:.1f}"
            else:
                signal_type = SignalType.HOLD
                strength = SignalStrength.WEAK
                confidence = 0.3
                description = f"RSI is neutral at {current_rsi:.1f}"

            signals.append(
                TechnicalSignal(
                    indicator="RSI",
                    signal_type=signal_type,
                    strength=strength,
                    confidence=confidence,
                    timestamp=datetime.now(),
                    price_level=close_prices[-1],
                    description=description,
                    metadata={"rsi_value": current_rsi, "overbought": overbought, "oversold": oversold},
                )
            )

        return TechnicalIndicatorResult(
            indicator=TechnicalIndicator.RSI,
            values={"RSI": rsi.tolist()},
            signals=signals,
            parameters={"period": period, "overbought": overbought, "oversold": oversold},
        )

    def calculate_macd(self, data: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> TechnicalIndicatorResult:
        """
        Calculate MACD using TA-Lib.

        Args:
            data: OHLCV data DataFrame
            fast: Fast EMA period
            slow: Slow EMA period
            signal: Signal line EMA period

        Returns:
            Technical indicator result with MACD values and signals

        """
        close_prices = data["Close"].values.astype(np.float64)

        if len(close_prices) < slow + signal:
            raise ValueError(f"Insufficient data for MACD: need {slow + signal}, have {len(close_prices)}")

        macd_line, macd_signal, macd_histogram = talib.MACD(close_prices, fastperiod=fast, slowperiod=slow, signalperiod=signal)

        current_macd = macd_line[-1]
        current_signal = macd_signal[-1]
        current_histogram = macd_histogram[-1]

        signals = []

        if not (np.isnan(current_macd) or np.isnan(current_signal) or np.isnan(current_histogram)):
            # MACD line crossing signal line
            if current_macd > current_signal and current_histogram > 0:
                if len(macd_histogram) > 1 and macd_histogram[-2] <= 0:  # Just crossed above
                    signal_type = SignalType.BUY
                    strength = SignalStrength.STRONG
                    confidence = 0.8
                    description = "MACD bullish crossover - line crossed above signal"
                else:
                    signal_type = SignalType.BUY
                    strength = SignalStrength.MODERATE
                    confidence = 0.6
                    description = "MACD above signal line - bullish momentum"
            elif current_macd < current_signal and current_histogram < 0:
                if len(macd_histogram) > 1 and macd_histogram[-2] >= 0:  # Just crossed below
                    signal_type = SignalType.SELL
                    strength = SignalStrength.STRONG
                    confidence = 0.8
                    description = "MACD bearish crossover - line crossed below signal"
                else:
                    signal_type = SignalType.SELL
                    strength = SignalStrength.MODERATE
                    confidence = 0.6
                    description = "MACD below signal line - bearish momentum"
            else:
                signal_type = SignalType.HOLD
                strength = SignalStrength.WEAK
                confidence = 0.3
                description = "MACD signals are mixed or neutral"

            signals.append(
                TechnicalSignal(
                    indicator="MACD",
                    signal_type=signal_type,
                    strength=strength,
                    confidence=confidence,
                    timestamp=datetime.now(),
                    price_level=close_prices[-1],
                    description=description,
                    metadata={
                        "macd_line": current_macd,
                        "signal_line": current_signal,
                        "histogram": current_histogram,
                    },
                )
            )

        return TechnicalIndicatorResult(
            indicator=TechnicalIndicator.MACD,
            values={
                "MACD_line": macd_line.tolist(),
                "MACD_signal": macd_signal.tolist(),
                "MACD_histogram": macd_histogram.tolist(),
            },
            signals=signals,
            parameters={"fast": fast, "slow": slow, "signal": signal},
        )

    def calculate_bollinger_bands(self, data: pd.DataFrame, period: int = 20, std_dev: float = 2.0) -> TechnicalIndicatorResult:
        """
        Calculate Bollinger Bands using TA-Lib.

        Args:
            data: OHLCV data DataFrame
            period: Moving average period
            std_dev: Standard deviation multiplier

        Returns:
            Technical indicator result with Bollinger Bands values and signals

        """
        close_prices = data["Close"].values.astype(np.float64)

        if len(close_prices) < period:
            raise ValueError(f"Insufficient data for Bollinger Bands: need {period}, have {len(close_prices)}")

        upper_band, middle_band, lower_band = talib.BBANDS(close_prices, timeperiod=period, nbdevup=std_dev, nbdevdn=std_dev)

        current_price = close_prices[-1]
        current_upper = upper_band[-1]
        current_middle = middle_band[-1]
        current_lower = lower_band[-1]

        signals = []

        if not (np.isnan(current_upper) or np.isnan(current_middle) or np.isnan(current_lower)):
            band_width = current_upper - current_lower
            price_position = (current_price - current_lower) / band_width

            if current_price > current_upper:
                signal_type = SignalType.SELL
                strength = SignalStrength.STRONG
                confidence = min(0.9, (current_price - current_upper) / current_upper * 10)
                description = "Price above upper Bollinger Band - potentially overbought"
            elif current_price < current_lower:
                signal_type = SignalType.BUY
                strength = SignalStrength.STRONG
                confidence = min(0.9, (current_lower - current_price) / current_lower * 10)
                description = "Price below lower Bollinger Band - potentially oversold"
            elif price_position > 0.8:  # Near upper band
                signal_type = SignalType.SELL
                strength = SignalStrength.MODERATE
                confidence = 0.6
                description = "Price near upper Bollinger Band - caution advised"
            elif price_position < 0.2:  # Near lower band
                signal_type = SignalType.BUY
                strength = SignalStrength.MODERATE
                confidence = 0.6
                description = "Price near lower Bollinger Band - potential buying opportunity"
            else:
                signal_type = SignalType.HOLD
                strength = SignalStrength.WEAK
                confidence = 0.3
                description = "Price within normal Bollinger Band range"

            signals.append(
                TechnicalSignal(
                    indicator="Bollinger_Bands",
                    signal_type=signal_type,
                    strength=strength,
                    confidence=confidence,
                    timestamp=datetime.now(),
                    price_level=current_price,
                    description=description,
                    metadata={
                        "upper_band": current_upper,
                        "middle_band": current_middle,
                        "lower_band": current_lower,
                        "price_position": price_position,
                    },
                )
            )

        return TechnicalIndicatorResult(
            indicator=TechnicalIndicator.BOLLINGER_BANDS,
            values={
                "upper_band": upper_band.tolist(),
                "middle_band": middle_band.tolist(),
                "lower_band": lower_band.tolist(),
            },
            signals=signals,
            parameters={"period": period, "std_dev": std_dev},
        )

    def calculate_stochastic(
        self,
        data: pd.DataFrame,
        k_period: int = 14,
        d_period: int = 3,
        overbought: float = 80,
        oversold: float = 20,
    ) -> TechnicalIndicatorResult:
        """
        Calculate Stochastic Oscillator using TA-Lib.

        Args:
            data: OHLCV data DataFrame
            k_period: %K period
            d_period: %D period
            overbought: Overbought threshold
            oversold: Oversold threshold

        Returns:
            Technical indicator result with Stochastic values and signals

        """
        high_prices = data["High"].values.astype(np.float64)
        low_prices = data["Low"].values.astype(np.float64)
        close_prices = data["Close"].values.astype(np.float64)

        if len(close_prices) < k_period:
            raise ValueError(f"Insufficient data for Stochastic: need {k_period}, have {len(close_prices)}")

        slowk, slowd = talib.STOCH(
            high_prices, low_prices, close_prices, fastk_period=k_period, slowk_period=3, slowd_period=d_period
        )

        current_k = slowk[-1]
        current_d = slowd[-1]

        signals = []

        if not (np.isnan(current_k) or np.isnan(current_d)):
            if current_k > overbought and current_d > overbought:
                signal_type = SignalType.SELL
                strength = SignalStrength.STRONG if current_k > 90 else SignalStrength.MODERATE
                confidence = min(0.9, (current_k - overbought) / (100 - overbought))
                description = f"Stochastic overbought: %K={current_k:.1f}, %D={current_d:.1f}"
            elif current_k < oversold and current_d < oversold:
                signal_type = SignalType.BUY
                strength = SignalStrength.STRONG if current_k < 10 else SignalStrength.MODERATE
                confidence = min(0.9, (oversold - current_k) / oversold)
                description = f"Stochastic oversold: %K={current_k:.1f}, %D={current_d:.1f}"
            elif current_k > current_d and len(slowk) > 1 and slowk[-2] <= slowd[-2]:  # Bullish crossover
                signal_type = SignalType.BUY
                strength = SignalStrength.MODERATE
                confidence = 0.7
                description = "Stochastic bullish crossover: %K crossed above %D"
            elif current_k < current_d and len(slowk) > 1 and slowk[-2] >= slowd[-2]:  # Bearish crossover
                signal_type = SignalType.SELL
                strength = SignalStrength.MODERATE
                confidence = 0.7
                description = "Stochastic bearish crossover: %K crossed below %D"
            else:
                signal_type = SignalType.HOLD
                strength = SignalStrength.WEAK
                confidence = 0.3
                description = f"Stochastic neutral: %K={current_k:.1f}, %D={current_d:.1f}"

            signals.append(
                TechnicalSignal(
                    indicator="Stochastic",
                    signal_type=signal_type,
                    strength=strength,
                    confidence=confidence,
                    timestamp=datetime.now(),
                    price_level=close_prices[-1],
                    description=description,
                    metadata={"k_value": current_k, "d_value": current_d},
                )
            )

        return TechnicalIndicatorResult(
            indicator=TechnicalIndicator.STOCHASTIC,
            values={"slowk": slowk.tolist(), "slowd": slowd.tolist()},
            signals=signals,
            parameters={"k_period": k_period, "d_period": d_period, "overbought": overbought, "oversold": oversold},
        )

    def calculate_atr(self, data: pd.DataFrame, period: int = 14) -> TechnicalIndicatorResult:
        """
        Calculate Average True Range using TA-Lib.

        Args:
            data: OHLCV data DataFrame
            period: ATR calculation period

        Returns:
            Technical indicator result with ATR values

        """
        high_prices = data["High"].values.astype(np.float64)
        low_prices = data["Low"].values.astype(np.float64)
        close_prices = data["Close"].values.astype(np.float64)

        if len(close_prices) < period + 1:
            raise ValueError(f"Insufficient data for ATR: need {period + 1}, have {len(close_prices)}")

        atr = talib.ATR(high_prices, low_prices, close_prices, timeperiod=period)
        current_atr = atr[-1]
        current_price = close_prices[-1]

        # ATR doesn't generate buy/sell signals directly, but provides volatility context
        signals = []
        if not np.isnan(current_atr):
            volatility_pct = (current_atr / current_price) * 100

            if volatility_pct > 5:  # High volatility
                description = f"High volatility detected: ATR is {volatility_pct:.1f}% of price"
                strength = SignalStrength.STRONG
            elif volatility_pct > 2:  # Moderate volatility
                description = f"Moderate volatility: ATR is {volatility_pct:.1f}% of price"
                strength = SignalStrength.MODERATE
            else:  # Low volatility
                description = f"Low volatility: ATR is {volatility_pct:.1f}% of price"
                strength = SignalStrength.WEAK

            signals.append(
                TechnicalSignal(
                    indicator="ATR",
                    signal_type=SignalType.HOLD,  # ATR is informational
                    strength=strength,
                    confidence=0.8,
                    timestamp=datetime.now(),
                    price_level=current_price,
                    description=description,
                    metadata={"atr_value": current_atr, "volatility_pct": volatility_pct},
                )
            )

        return TechnicalIndicatorResult(
            indicator=TechnicalIndicator.ATR,
            values={"ATR": atr.tolist()},
            signals=signals,
            parameters={"period": period},
        )

    def calculate_adx(self, data: pd.DataFrame, period: int = 14, trend_threshold: float = 25) -> TechnicalIndicatorResult:
        """
        Calculate Average Directional Index using TA-Lib.

        Args:
            data: OHLCV data DataFrame
            period: ADX calculation period
            trend_threshold: Threshold for trend strength

        Returns:
            Technical indicator result with ADX values and signals

        """
        high_prices = data["High"].values.astype(np.float64)
        low_prices = data["Low"].values.astype(np.float64)
        close_prices = data["Close"].values.astype(np.float64)

        if len(close_prices) < period * 2:
            raise ValueError(f"Insufficient data for ADX: need {period * 2}, have {len(close_prices)}")

        adx = talib.ADX(high_prices, low_prices, close_prices, timeperiod=period)
        plus_di = talib.PLUS_DI(high_prices, low_prices, close_prices, timeperiod=period)
        minus_di = talib.MINUS_DI(high_prices, low_prices, close_prices, timeperiod=period)

        current_adx = adx[-1]
        current_plus_di = plus_di[-1]
        current_minus_di = minus_di[-1]

        signals = []

        if not (np.isnan(current_adx) or np.isnan(current_plus_di) or np.isnan(current_minus_di)):
            if current_adx > trend_threshold:
                if current_plus_di > current_minus_di:
                    signal_type = SignalType.BUY
                    strength = SignalStrength.STRONG if current_adx > 40 else SignalStrength.MODERATE
                    confidence = min(0.9, current_adx / 50)
                    description = (
                        f"Strong uptrend detected: ADX={current_adx:.1f}, +DI={current_plus_di:.1f} > -DI={current_minus_di:.1f}"
                    )
                else:
                    signal_type = SignalType.SELL
                    strength = SignalStrength.STRONG if current_adx > 40 else SignalStrength.MODERATE
                    confidence = min(0.9, current_adx / 50)
                    description = (
                        f"Strong downtrend detected: ADX={current_adx:.1f}, -DI={current_minus_di:.1f} > +DI={current_plus_di:.1f}"
                    )
            else:
                signal_type = SignalType.HOLD
                strength = SignalStrength.WEAK
                confidence = 0.3
                description = f"Weak trend: ADX={current_adx:.1f} below threshold {trend_threshold}"

            signals.append(
                TechnicalSignal(
                    indicator="ADX",
                    signal_type=signal_type,
                    strength=strength,
                    confidence=confidence,
                    timestamp=datetime.now(),
                    price_level=close_prices[-1],
                    description=description,
                    metadata={
                        "adx_value": current_adx,
                        "plus_di": current_plus_di,
                        "minus_di": current_minus_di,
                        "trend_threshold": trend_threshold,
                    },
                )
            )

        return TechnicalIndicatorResult(
            indicator=TechnicalIndicator.ADX,
            values={
                "ADX": adx.tolist(),
                "PLUS_DI": plus_di.tolist(),
                "MINUS_DI": minus_di.tolist(),
            },
            signals=signals,
            parameters={"period": period, "trend_threshold": trend_threshold},
        )

    def calculate_cci(
        self, data: pd.DataFrame, period: int = 20, overbought: float = 100, oversold: float = -100
    ) -> TechnicalIndicatorResult:
        """
        Calculate Commodity Channel Index using TA-Lib.

        Args:
            data: OHLCV data DataFrame
            period: CCI calculation period
            overbought: Overbought threshold
            oversold: Oversold threshold

        Returns:
            Technical indicator result with CCI values and signals

        """
        high_prices = data["High"].values.astype(np.float64)
        low_prices = data["Low"].values.astype(np.float64)
        close_prices = data["Close"].values.astype(np.float64)

        if len(close_prices) < period:
            raise ValueError(f"Insufficient data for CCI: need {period}, have {len(close_prices)}")

        cci = talib.CCI(high_prices, low_prices, close_prices, timeperiod=period)
        current_cci = cci[-1]

        signals = []

        if not np.isnan(current_cci):
            if current_cci > overbought:
                signal_type = SignalType.SELL
                strength = SignalStrength.STRONG if current_cci > 200 else SignalStrength.MODERATE
                confidence = min(0.9, (current_cci - overbought) / (200 - overbought))
                description = f"CCI overbought at {current_cci:.1f}"
            elif current_cci < oversold:
                signal_type = SignalType.BUY
                strength = SignalStrength.STRONG if current_cci < -200 else SignalStrength.MODERATE
                confidence = min(0.9, (oversold - current_cci) / (200 + oversold))
                description = f"CCI oversold at {current_cci:.1f}"
            else:
                signal_type = SignalType.HOLD
                strength = SignalStrength.WEAK
                confidence = 0.3
                description = f"CCI neutral at {current_cci:.1f}"

            signals.append(
                TechnicalSignal(
                    indicator="CCI",
                    signal_type=signal_type,
                    strength=strength,
                    confidence=confidence,
                    timestamp=datetime.now(),
                    price_level=close_prices[-1],
                    description=description,
                    metadata={
                        "cci_value": current_cci,
                        "overbought": overbought,
                        "oversold": oversold,
                    },
                )
            )

        return TechnicalIndicatorResult(
            indicator=TechnicalIndicator.CCI,
            values={"CCI": cci.tolist()},
            signals=signals,
            parameters={"period": period, "overbought": overbought, "oversold": oversold},
        )

    def calculate_williams_r(
        self, data: pd.DataFrame, period: int = 14, overbought: float = -20, oversold: float = -80
    ) -> TechnicalIndicatorResult:
        """
        Calculate Williams %R using TA-Lib.

        Args:
            data: OHLCV data DataFrame
            period: Williams %R calculation period
            overbought: Overbought threshold
            oversold: Oversold threshold

        Returns:
            Technical indicator result with Williams %R values and signals

        """
        high_prices = data["High"].values.astype(np.float64)
        low_prices = data["Low"].values.astype(np.float64)
        close_prices = data["Close"].values.astype(np.float64)

        if len(close_prices) < period:
            raise ValueError(f"Insufficient data for Williams %R: need {period}, have {len(close_prices)}")

        willr = talib.WILLR(high_prices, low_prices, close_prices, timeperiod=period)
        current_willr = willr[-1]

        signals = []

        if not np.isnan(current_willr):
            if current_willr > overbought:
                signal_type = SignalType.SELL
                strength = SignalStrength.STRONG if current_willr > -10 else SignalStrength.MODERATE
                confidence = min(0.9, (current_willr - overbought) / (0 - overbought))
                description = f"Williams %R overbought at {current_willr:.1f}"
            elif current_willr < oversold:
                signal_type = SignalType.BUY
                strength = SignalStrength.STRONG if current_willr < -90 else SignalStrength.MODERATE
                confidence = min(0.9, (oversold - current_willr) / (oversold + 100))
                description = f"Williams %R oversold at {current_willr:.1f}"
            else:
                signal_type = SignalType.HOLD
                strength = SignalStrength.WEAK
                confidence = 0.3
                description = f"Williams %R neutral at {current_willr:.1f}"

            signals.append(
                TechnicalSignal(
                    indicator="Williams_R",
                    signal_type=signal_type,
                    strength=strength,
                    confidence=confidence,
                    timestamp=datetime.now(),
                    price_level=close_prices[-1],
                    description=description,
                    metadata={
                        "willr_value": current_willr,
                        "overbought": overbought,
                        "oversold": oversold,
                    },
                )
            )

        return TechnicalIndicatorResult(
            indicator=TechnicalIndicator.WILLIAMS_R,
            values={"Williams_R": willr.tolist()},
            signals=signals,
            parameters={"period": period, "overbought": overbought, "oversold": oversold},
        )

    def calculate_fibonacci_retracements(self, data: pd.DataFrame, lookback_period: int = 50) -> TechnicalIndicatorResult:
        """
        Calculate Fibonacci retracement levels.

        Args:
            data: OHLCV data DataFrame
            lookback_period: Period to look back for high/low calculation

        Returns:
            Technical indicator result with Fibonacci levels and signals

        """
        close_prices = data["Close"].values.astype(np.float64)
        high_prices = data["High"].values.astype(np.float64)
        low_prices = data["Low"].values.astype(np.float64)

        if len(close_prices) < lookback_period:
            raise ValueError(f"Insufficient data for Fibonacci: need {lookback_period}, have {len(close_prices)}")

        # Calculate recent high and low
        recent_data = data.tail(lookback_period)
        swing_high = recent_data["High"].max()
        swing_low = recent_data["Low"].min()

        # Find the indices of swing high and low
        high_idx = recent_data["High"].idxmax()
        low_idx = recent_data["Low"].idxmin()

        # Determine trend direction
        is_uptrend = high_idx > low_idx

        # Calculate Fibonacci levels
        price_range = swing_high - swing_low
        fib_levels = {
            "0.0": swing_low if is_uptrend else swing_high,
            "23.6": swing_low + (price_range * 0.236) if is_uptrend else swing_high - (price_range * 0.236),
            "38.2": swing_low + (price_range * 0.382) if is_uptrend else swing_high - (price_range * 0.382),
            "50.0": swing_low + (price_range * 0.5) if is_uptrend else swing_high - (price_range * 0.5),
            "61.8": swing_low + (price_range * 0.618) if is_uptrend else swing_high - (price_range * 0.618),
            "78.6": swing_low + (price_range * 0.786) if is_uptrend else swing_high - (price_range * 0.786),
            "100.0": swing_high if is_uptrend else swing_low,
        }

        current_price = close_prices[-1]
        signals = []

        # Generate signals based on price proximity to Fibonacci levels
        for level_name, level_price in fib_levels.items():
            price_diff_pct = abs(current_price - level_price) / current_price

            if price_diff_pct < 0.01:  # Within 1% of Fibonacci level
                if level_name in ["23.6", "38.2", "50.0", "61.8"]:  # Key retracement levels
                    if is_uptrend:
                        signal_type = SignalType.BUY
                        description = f"Price near Fibonacci {level_name}% retracement support at {level_price:.2f}"
                    else:
                        signal_type = SignalType.SELL
                        description = f"Price near Fibonacci {level_name}% retracement resistance at {level_price:.2f}"

                    strength = SignalStrength.STRONG if level_name in ["38.2", "61.8"] else SignalStrength.MODERATE
                    confidence = 0.7 if level_name in ["38.2", "50.0", "61.8"] else 0.5

                    signals.append(
                        TechnicalSignal(
                            indicator="Fibonacci",
                            signal_type=signal_type,
                            strength=strength,
                            confidence=confidence,
                            timestamp=datetime.now(),
                            price_level=current_price,
                            description=description,
                            metadata={
                                "fib_level": level_name,
                                "fib_price": level_price,
                                "swing_high": swing_high,
                                "swing_low": swing_low,
                                "is_uptrend": is_uptrend,
                            },
                        )
                    )

        return TechnicalIndicatorResult(
            indicator=TechnicalIndicator.FIBONACCI,
            values=fib_levels,
            signals=signals,
            parameters={"lookback_period": lookback_period, "swing_high": swing_high, "swing_low": swing_low},
        )

    def _calculate_indicator(self, data: pd.DataFrame, indicator: TechnicalIndicator, symbol: str) -> TechnicalIndicatorResult:
        """Calculate a specific technical indicator."""
        params = self.config.get_indicator_config(indicator)
        if not params:
            params = self.default_params.get(indicator, {})

        try:
            if indicator == TechnicalIndicator.SMA:
                return self.calculate_sma(data, params.get("periods", [20, 50, 200]))
            elif indicator == TechnicalIndicator.EMA:
                return self.calculate_ema(data, params.get("periods", [12, 26, 50]))
            elif indicator == TechnicalIndicator.RSI:
                return self.calculate_rsi(
                    data,
                    params.get("period", 14),
                    params.get("overbought", 70),
                    params.get("oversold", 30),
                )
            elif indicator == TechnicalIndicator.MACD:
                return self.calculate_macd(
                    data,
                    params.get("fast", 12),
                    params.get("slow", 26),
                    params.get("signal", 9),
                )
            elif indicator == TechnicalIndicator.BOLLINGER_BANDS:
                return self.calculate_bollinger_bands(
                    data,
                    params.get("period", 20),
                    params.get("std_dev", 2),
                )
            elif indicator == TechnicalIndicator.STOCHASTIC:
                return self.calculate_stochastic(
                    data,
                    params.get("k_period", 14),
                    params.get("d_period", 3),
                    params.get("overbought", 80),
                    params.get("oversold", 20),
                )
            elif indicator == TechnicalIndicator.ATR:
                return self.calculate_atr(data, params.get("period", 14))
            elif indicator == TechnicalIndicator.ADX:
                return self.calculate_adx(
                    data,
                    params.get("period", 14),
                    params.get("trend_threshold", 25),
                )
            elif indicator == TechnicalIndicator.CCI:
                return self.calculate_cci(
                    data,
                    params.get("period", 20),
                    params.get("overbought", 100),
                    params.get("oversold", -100),
                )
            elif indicator == TechnicalIndicator.WILLIAMS_R:
                return self.calculate_williams_r(
                    data,
                    params.get("period", 14),
                    params.get("overbought", -20),
                    params.get("oversold", -80),
                )
            elif indicator == TechnicalIndicator.FIBONACCI:
                return self.calculate_fibonacci_retracements(
                    data,
                    params.get("lookback_period", 50),
                )
            else:
                raise ValueError(f"Unsupported indicator: {indicator}")

        except Exception as e:
            self.logger.error(f"Error calculating {indicator.value} for {symbol}: {e}")
            # Return empty result on error
            return TechnicalIndicatorResult(
                indicator=indicator,
                values={},
                signals=[],
                parameters=params,
            )

    def _detect_confluence_zones(self, signals: list[TechnicalSignal], data: pd.DataFrame) -> list[ConfluenceZone]:
        """Detect confluence zones where multiple indicators align."""
        if len(signals) < 2:
            return []

        confluence_zones = []
        current_price = data["Close"].iloc[-1]

        # Group signals by type and proximity
        buy_signals = [s for s in signals if s.signal_type in [SignalType.BUY, SignalType.STRONG_BUY]]
        sell_signals = [s for s in signals if s.signal_type in [SignalType.SELL, SignalType.STRONG_SELL]]

        # Detect bullish confluence
        if len(buy_signals) >= 2:
            avg_confidence = sum(s.confidence for s in buy_signals) / len(buy_signals)
            strength_scores = {"very_weak": 1, "weak": 2, "moderate": 3, "strong": 4, "very_strong": 5}
            avg_strength_score = sum(strength_scores.get(s.strength.value, 3) for s in buy_signals) / len(buy_signals)

            if avg_strength_score >= 3:  # At least moderate strength
                overall_strength = (
                    SignalStrength.VERY_STRONG
                    if avg_strength_score >= 4.5
                    else SignalStrength.STRONG
                    if avg_strength_score >= 3.5
                    else SignalStrength.MODERATE
                )

                confluence_zones.append(
                    ConfluenceZone(
                        price_level=current_price,
                        signal_type=SignalType.STRONG_BUY if avg_strength_score >= 4 else SignalType.BUY,
                        strength=overall_strength,
                        confidence=min(0.95, avg_confidence * 1.2),  # Boost confidence for confluence
                        contributing_signals=buy_signals,
                        zone_range=(current_price * 0.98, current_price * 1.02),  # 2% range
                        timestamp=datetime.now(),
                    )
                )

        # Detect bearish confluence
        if len(sell_signals) >= 2:
            avg_confidence = sum(s.confidence for s in sell_signals) / len(sell_signals)
            strength_scores = {"very_weak": 1, "weak": 2, "moderate": 3, "strong": 4, "very_strong": 5}
            avg_strength_score = sum(strength_scores.get(s.strength.value, 3) for s in sell_signals) / len(sell_signals)

            if avg_strength_score >= 3:  # At least moderate strength
                overall_strength = (
                    SignalStrength.VERY_STRONG
                    if avg_strength_score >= 4.5
                    else SignalStrength.STRONG
                    if avg_strength_score >= 3.5
                    else SignalStrength.MODERATE
                )

                confluence_zones.append(
                    ConfluenceZone(
                        price_level=current_price,
                        signal_type=SignalType.STRONG_SELL if avg_strength_score >= 4 else SignalType.SELL,
                        strength=overall_strength,
                        confidence=min(0.95, avg_confidence * 1.2),  # Boost confidence for confluence
                        contributing_signals=sell_signals,
                        zone_range=(current_price * 0.98, current_price * 1.02),  # 2% range
                        timestamp=datetime.now(),
                    )
                )

        return confluence_zones

    def _generate_overall_signal(self, signals: list[TechnicalSignal]) -> tuple[SignalType, float, SignalStrength]:
        """Generate overall signal from individual indicator signals."""
        if not signals:
            return SignalType.HOLD, 0.0, SignalStrength.VERY_WEAK

        # Weight signals by confidence and strength
        strength_weights = {
            SignalStrength.VERY_WEAK: 0.2,
            SignalStrength.WEAK: 0.4,
            SignalStrength.MODERATE: 0.6,
            SignalStrength.STRONG: 0.8,
            SignalStrength.VERY_STRONG: 1.0,
        }

        signal_weights = {
            SignalType.STRONG_BUY: 2.0,
            SignalType.BUY: 1.0,
            SignalType.HOLD: 0.0,
            SignalType.SELL: -1.0,
            SignalType.STRONG_SELL: -2.0,
        }

        weighted_score = 0.0
        total_weight = 0.0

        for signal in signals:
            signal_weight = signal_weights.get(signal.signal_type, 0.0)
            strength_weight = strength_weights.get(signal.strength, 0.6)
            weight = signal.confidence * strength_weight

            weighted_score += signal_weight * weight
            total_weight += weight

        if total_weight == 0:
            return SignalType.HOLD, 0.0, SignalStrength.VERY_WEAK

        normalized_score = weighted_score / total_weight
        overall_confidence = min(0.95, total_weight / len(signals))

        # Determine overall signal type
        if normalized_score > 1.5:
            overall_signal = SignalType.STRONG_BUY
            signal_strength = SignalStrength.VERY_STRONG
        elif normalized_score > 0.5:
            overall_signal = SignalType.BUY
            signal_strength = SignalStrength.STRONG if normalized_score > 1.0 else SignalStrength.MODERATE
        elif normalized_score < -1.5:
            overall_signal = SignalType.STRONG_SELL
            signal_strength = SignalStrength.VERY_STRONG
        elif normalized_score < -0.5:
            overall_signal = SignalType.SELL
            signal_strength = SignalStrength.STRONG if normalized_score < -1.0 else SignalStrength.MODERATE
        else:
            overall_signal = SignalType.HOLD
            signal_strength = SignalStrength.WEAK

        return overall_signal, overall_confidence, signal_strength

    def _validate_data(self, data: pd.DataFrame) -> None:
        """Validate input data for technical analysis."""
        if data.empty:
            raise ValueError("Data cannot be empty")

        required_columns = ["Open", "High", "Low", "Close", "Volume"]
        missing_columns = [col for col in required_columns if col not in data.columns]

        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

        if len(data) < 20:  # Minimum data points for meaningful analysis
            raise ValueError(f"Insufficient data points: need at least 20, got {len(data)}")

        # Check for invalid values
        price_columns = ["Open", "High", "Low", "Close"]
        for col in price_columns:
            if (data[col] <= 0).any():
                raise ValueError(f"Invalid values found in {col}: prices must be positive")

        # Check OHLC relationships
        if ((data["High"] < data["Low"]) | (data["High"] < data["Open"]) | (data["High"] < data["Close"])).any():
            raise ValueError("Invalid OHLC relationships: High must be >= Open, Low, Close")

        if ((data["Low"] > data["Open"]) | (data["Low"] > data["Close"])).any():
            raise ValueError("Invalid OHLC relationships: Low must be <= Open, Close")


# Convenience functions for direct indicator calculations
def calculate_technical_indicators(
    data: pd.DataFrame,
    symbol: str,
    indicators: list[TechnicalIndicator] | None = None,
    timeframe: str = "1d",
) -> TechnicalAnalysisResult:
    """
    Convenience function to calculate technical indicators.

    Args:
        data: OHLCV data DataFrame
        symbol: Stock symbol
        indicators: List of indicators to calculate
        timeframe: Data timeframe

    Returns:
        Technical analysis result

    """
    engine = TechnicalAnalysisEngine()
    return engine.analyze_symbol(data, symbol, timeframe, indicators)


def get_confluence_signals(data: pd.DataFrame, symbol: str, min_confluence: int = 2) -> list[ConfluenceZone]:
    """
    Get confluence zones from technical analysis.

    Args:
        data: OHLCV data DataFrame
        symbol: Stock symbol
        min_confluence: Minimum number of signals required for confluence

    Returns:
        List of confluence zones

    """
    result = calculate_technical_indicators(data, symbol)
    return [zone for zone in result.confluence_zones if len(zone.contributing_signals) >= min_confluence]
