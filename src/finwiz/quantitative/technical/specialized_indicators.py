"""
Specialized Technical Indicators.

Fibonacci retracements, ATR, ADX, CCI, Williams %R, and other specialized calculations.
"""

from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd

from .technical_indicators import TALibWrappers
from .technical_models import SignalStrength, SignalType, TechnicalIndicatorResult, TechnicalSignal


class SpecializedIndicators:
    """Calculator for specialized technical indicators."""

    def __init__(self, logger: Any) -> None:
        """Initialize with logger."""
        self.logger = logger

    def calculate_fibonacci_retracements(self, data: pd.DataFrame, lookback_period: int = 50) -> TechnicalIndicatorResult:
        """
        Calculate Fibonacci retracement levels.

        Args:
            data: OHLCV data DataFrame
            lookback_period: Period to look back for swing high/low

        Returns:
            Technical indicator result with Fibonacci levels and signals

        """
        close_prices = data["Close"].values.astype(np.float64)

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

        # Calculate Fibonacci levels using numpy for efficiency
        price_range = swing_high - swing_low
        fib_ratios = np.array([0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0])
        fib_names = ["0.0", "23.6", "38.2", "50.0", "61.8", "78.6", "100.0"]

        if is_uptrend:
            fib_prices = swing_low + (price_range * fib_ratios)
        else:
            fib_prices = swing_high - (price_range * fib_ratios)

        fib_levels = dict(zip(fib_names, fib_prices))

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

                    strength = SignalStrength.MODERATE
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
                                "price_diff_pct": price_diff_pct,
                            },
                        )
                    )

        return TechnicalIndicatorResult(
            indicator_name="Fibonacci",
            signals=signals,
            raw_values=fib_levels,
            metadata={
                "lookback_period": lookback_period,
                "swing_high": swing_high,
                "swing_low": swing_low,
                "is_uptrend": is_uptrend,
            },
        )

    def calculate_atr(self, data: pd.DataFrame, period: int = 14) -> TechnicalIndicatorResult:
        """
        Calculate Average True Range using TA-Lib.

        Args:
            data: OHLCV data DataFrame
            period: ATR calculation period

        Returns:
            Technical indicator result with ATR values and signals

        """
        high_prices = np.asarray(data["High"].values, dtype=np.float64)
        low_prices = np.asarray(data["Low"].values, dtype=np.float64)
        close_prices = np.asarray(data["Close"].values, dtype=np.float64)

        if len(close_prices) < period + 1:
            raise ValueError(f"Insufficient data for ATR: need {period + 1}, have {len(close_prices)}")

        atr = TALibWrappers.atr(high_prices, low_prices, close_prices, period)
        current_atr = atr[-1]
        current_price = close_prices[-1]
        signals = []

        if not np.isnan(current_atr):
            # ATR is primarily used for volatility assessment, not direct buy/sell signals
            atr_pct = (current_atr / current_price) * 100

            if atr_pct > 5:  # High volatility
                signal_type = SignalType.HOLD
                strength = SignalStrength.MODERATE
                confidence = 0.6
                description = f"High volatility detected: ATR is {atr_pct:.1f}% of price"
            elif atr_pct < 1:  # Low volatility
                signal_type = SignalType.HOLD
                strength = SignalStrength.WEAK
                confidence = 0.4
                description = f"Low volatility: ATR is {atr_pct:.1f}% of price"
            else:
                signal_type = SignalType.HOLD
                strength = SignalStrength.WEAK
                confidence = 0.3
                description = f"Normal volatility: ATR is {atr_pct:.1f}% of price"

            signals.append(
                TechnicalSignal(
                    indicator="ATR",
                    signal_type=signal_type,
                    strength=strength,
                    confidence=confidence,
                    timestamp=datetime.now(),
                    price_level=current_price,
                    description=description,
                    metadata={
                        "atr_value": current_atr,
                        "atr_percentage": atr_pct,
                        "period": period,
                    },
                )
            )

        return TechnicalIndicatorResult(
            indicator_name="ATR",
            signals=signals,
            raw_values={"ATR": atr.tolist()},
            metadata={"period": period},
        )
