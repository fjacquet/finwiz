"""
Advanced Technical Indicators.

MACD, Bollinger Bands, Stochastic, ATR, ADX, CCI, Williams %R calculations.
"""

from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd

from .technical_indicators import TALibWrappers
from .technical_models import SignalStrength, SignalType, TechnicalIndicatorResult, TechnicalSignal


class AdvancedIndicators:
    """Calculator for advanced technical indicators."""

    def __init__(self, logger: Any) -> None:
        """Initialize with logger."""
        self.logger = logger

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
        close_prices = np.asarray(data["Close"].values, dtype=np.float64)

        if len(close_prices) < slow + signal:
            raise ValueError(f"Insufficient data for MACD: need {slow + signal}, have {len(close_prices)}")

        macd_line, macd_signal, macd_histogram = TALibWrappers.macd(close_prices, fast, slow, signal)

        current_macd = macd_line[-1]
        current_signal = macd_signal[-1]
        current_histogram = macd_histogram[-1]
        current_price = close_prices[-1]
        signals = []

        if not (np.isnan(current_macd) or np.isnan(current_signal) or np.isnan(current_histogram)):
            # MACD line crossing signal line
            if current_macd > current_signal and current_histogram > 0:
                if len(macd_histogram) > 1 and macd_histogram[-2] <= 0:  # Just crossed above
                    signal_type = SignalType.BUY
                    strength = SignalStrength.STRONG
                    confidence = 0.85
                    description = "MACD bullish crossover - strong buy signal"
                else:
                    signal_type = SignalType.BUY
                    strength = SignalStrength.MODERATE
                    confidence = 0.7
                    description = "MACD above signal line - bullish momentum"
            elif current_macd < current_signal and current_histogram < 0:
                if len(macd_histogram) > 1 and macd_histogram[-2] >= 0:  # Just crossed below
                    signal_type = SignalType.SELL
                    strength = SignalStrength.STRONG
                    confidence = 0.85
                    description = "MACD bearish crossover - strong sell signal"
                else:
                    signal_type = SignalType.SELL
                    strength = SignalStrength.MODERATE
                    confidence = 0.7
                    description = "MACD below signal line - bearish momentum"
            else:
                signal_type = SignalType.HOLD
                strength = SignalStrength.WEAK
                confidence = 0.4
                description = "MACD signals are mixed or neutral"

            signals.append(
                TechnicalSignal(
                    indicator="MACD",
                    signal_type=signal_type,
                    strength=strength,
                    confidence=confidence,
                    timestamp=datetime.now(),
                    price_level=current_price,
                    description=description,
                    metadata={
                        "macd_line": current_macd,
                        "signal_line": current_signal,
                        "histogram": current_histogram,
                        "fast": fast,
                        "slow": slow,
                        "signal_period": signal,
                    },
                )
            )

        return TechnicalIndicatorResult(
            indicator_name="MACD",
            signals=signals,
            raw_values={
                "MACD_line": macd_line.tolist(),
                "MACD_signal": macd_signal.tolist(),
                "MACD_histogram": macd_histogram.tolist(),
            },
            metadata={"fast": fast, "slow": slow, "signal": signal},
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
        close_prices = np.asarray(data["Close"].values, dtype=np.float64)

        if len(close_prices) < period:
            raise ValueError(f"Insufficient data for Bollinger Bands: need {period}, have {len(close_prices)}")

        upper_band, middle_band, lower_band = TALibWrappers.bollinger_bands(close_prices, period, std_dev)

        current_price = close_prices[-1]
        current_upper = upper_band[-1]
        current_middle = middle_band[-1]
        current_lower = lower_band[-1]
        signals = []

        if not (np.isnan(current_upper) or np.isnan(current_middle) or np.isnan(current_lower)):
            # Calculate position within bands
            band_width = current_upper - current_lower
            price_position = (current_price - current_lower) / band_width if band_width > 0 else 0.5

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
                description = "Price near lower Bollinger Band - potential support"
            else:
                signal_type = SignalType.HOLD
                strength = SignalStrength.WEAK
                confidence = 0.4
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
                        "period": period,
                        "std_dev": std_dev,
                    },
                )
            )

        return TechnicalIndicatorResult(
            indicator_name="Bollinger_Bands",
            signals=signals,
            raw_values={
                "upper_band": upper_band.tolist(),
                "middle_band": middle_band.tolist(),
                "lower_band": lower_band.tolist(),
            },
            metadata={"period": period, "std_dev": std_dev},
        )
