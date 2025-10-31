"""
Technical Analysis Algorithms.

This module contains mathematical algorithms and calculations for technical indicators
including RSI, MACD, Bollinger Bands, and Fibonacci levels.
"""

from __future__ import annotations

from datetime import datetime

import pandas as pd

from finwiz.tools.logger import get_logger
from finwiz.tools.technical_models import (
    FibonacciLevel,
    FibonacciLevels,
    IndicatorSignal,
    PriceData,
)

logger = get_logger(__name__)


class TechnicalAlgorithms:
    """Mathematical algorithms for technical analysis calculations."""

    def __init__(self) -> None:
        """Initialize technical algorithms with standard parameters."""
        # Standard Fibonacci ratios
        self.fib_ratios = [0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0]
        self.fib_extensions = [1.272, 1.414, 1.618, 2.0, 2.618]

    def calculate_fibonacci_levels(self, price_data: PriceData) -> FibonacciLevels:
        """Calculate Fibonacci retracement and extension levels."""
        # Find significant swing high and low
        swing_high, swing_low, high_date, low_date, trend = self._find_significant_swing(price_data)

        current_price = price_data.closes[-1]

        # Calculate Fibonacci levels
        price_range = swing_high - swing_low
        levels = []

        if trend == "uptrend":
            # For uptrend, calculate retracements from high to low
            for ratio in self.fib_ratios:
                fib_price = swing_high - (price_range * ratio)
                levels.append(
                    FibonacciLevel(
                        ratio=ratio,
                        price=fib_price,
                        percentage=ratio * 100,
                        level_type="retracement",
                    )
                )

            # Add extensions above the high
            for ratio in self.fib_extensions:
                fib_price = swing_high + (price_range * (ratio - 1))
                levels.append(
                    FibonacciLevel(
                        ratio=ratio,
                        price=fib_price,
                        percentage=ratio * 100,
                        level_type="extension",
                    )
                )
        else:
            # For downtrend, calculate retracements from low to high
            for ratio in self.fib_ratios:
                fib_price = swing_low + (price_range * ratio)
                levels.append(
                    FibonacciLevel(
                        ratio=ratio,
                        price=fib_price,
                        percentage=ratio * 100,
                        level_type="retracement",
                    )
                )

            # Add extensions below the low
            for ratio in self.fib_extensions:
                fib_price = swing_low - (price_range * (ratio - 1))
                levels.append(
                    FibonacciLevel(
                        ratio=ratio,
                        price=fib_price,
                        percentage=ratio * 100,
                        level_type="extension",
                    )
                )

        # Find nearest support and resistance
        nearest_support, nearest_resistance = self._find_nearest_fib_levels(levels, current_price)

        return FibonacciLevels(
            swing_high=swing_high,
            swing_low=swing_low,
            swing_high_date=high_date,
            swing_low_date=low_date,
            trend_direction=trend,
            levels=levels,
            current_price=current_price,
            nearest_support=nearest_support,
            nearest_resistance=nearest_resistance,
        )

    def calculate_indicator_signals(self, price_data: PriceData) -> list[IndicatorSignal]:
        """Calculate signals from various technical indicators."""
        signals = []

        # Convert to DataFrame for easier calculation
        df = price_data.to_dataframe()

        # RSI Signal
        rsi = self.calculate_rsi(df["close"])
        if len(rsi) > 0:
            current_rsi = rsi.iloc[-1]
            if current_rsi < 30:
                signals.append(
                    IndicatorSignal(
                        indicator_name="RSI",
                        signal_type="buy",
                        strength=min(1.0, (30 - current_rsi) / 30),
                        value=current_rsi,
                        threshold=30,
                        description=f"RSI oversold at {current_rsi:.1f}",
                    )
                )
            elif current_rsi > 70:
                signals.append(
                    IndicatorSignal(
                        indicator_name="RSI",
                        signal_type="sell",
                        strength=min(1.0, (current_rsi - 70) / 30),
                        value=current_rsi,
                        threshold=70,
                        description=f"RSI overbought at {current_rsi:.1f}",
                    )
                )
            else:
                signals.append(
                    IndicatorSignal(
                        indicator_name="RSI",
                        signal_type="neutral",
                        strength=0.5,
                        value=current_rsi,
                        description=f"RSI neutral at {current_rsi:.1f}",
                    )
                )

        # MACD Signal
        macd_line, signal_line, histogram = self.calculate_macd(df["close"])
        if len(macd_line) > 1:
            current_macd = macd_line.iloc[-1]
            current_signal = signal_line.iloc[-1]
            prev_macd = macd_line.iloc[-2]
            prev_signal = signal_line.iloc[-2]

            # MACD crossover
            if current_macd > current_signal and prev_macd <= prev_signal:
                signals.append(
                    IndicatorSignal(
                        indicator_name="MACD",
                        signal_type="buy",
                        strength=0.8,
                        value=current_macd,
                        description="MACD bullish crossover",
                    )
                )
            elif current_macd < current_signal and prev_macd >= prev_signal:
                signals.append(
                    IndicatorSignal(
                        indicator_name="MACD",
                        signal_type="sell",
                        strength=0.8,
                        value=current_macd,
                        description="MACD bearish crossover",
                    )
                )
            else:
                signals.append(
                    IndicatorSignal(
                        indicator_name="MACD",
                        signal_type="neutral",
                        strength=0.3,
                        value=current_macd,
                        description="MACD no clear signal",
                    )
                )

        # Moving Average Signal
        ma_20 = df["close"].rolling(window=20).mean()
        ma_50 = df["close"].rolling(window=50).mean()

        if len(ma_20) > 1 and len(ma_50) > 1:
            current_price = df["close"].iloc[-1]
            current_ma20 = ma_20.iloc[-1]
            current_ma50 = ma_50.iloc[-1]

            if current_price > current_ma20 > current_ma50:
                signals.append(
                    IndicatorSignal(
                        indicator_name="Moving Average",
                        signal_type="buy",
                        strength=0.7,
                        value=current_price,
                        description="Price above both MA20 and MA50",
                    )
                )
            elif current_price < current_ma20 < current_ma50:
                signals.append(
                    IndicatorSignal(
                        indicator_name="Moving Average",
                        signal_type="sell",
                        strength=0.7,
                        value=current_price,
                        description="Price below both MA20 and MA50",
                    )
                )
            else:
                signals.append(
                    IndicatorSignal(
                        indicator_name="Moving Average",
                        signal_type="neutral",
                        strength=0.4,
                        value=current_price,
                        description="Mixed moving average signals",
                    )
                )

        # Bollinger Bands Signal
        bb_upper, bb_middle, bb_lower = self.calculate_bollinger_bands(df["close"])
        if len(bb_upper) > 0:
            current_price = df["close"].iloc[-1]
            current_upper = bb_upper.iloc[-1]
            current_lower = bb_lower.iloc[-1]

            if current_price <= current_lower:
                signals.append(
                    IndicatorSignal(
                        indicator_name="Bollinger Bands",
                        signal_type="buy",
                        strength=0.6,
                        value=current_price,
                        threshold=current_lower,
                        description="Price at lower Bollinger Band",
                    )
                )
            elif current_price >= current_upper:
                signals.append(
                    IndicatorSignal(
                        indicator_name="Bollinger Bands",
                        signal_type="sell",
                        strength=0.6,
                        value=current_price,
                        threshold=current_upper,
                        description="Price at upper Bollinger Band",
                    )
                )
            else:
                signals.append(
                    IndicatorSignal(
                        indicator_name="Bollinger Bands",
                        signal_type="neutral",
                        strength=0.3,
                        value=current_price,
                        description="Price within Bollinger Bands",
                    )
                )

        return signals

    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate MACD indicator."""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram

    def calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std_dev: int = 2) -> tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate Bollinger Bands."""
        middle = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        return upper, middle, lower

    def _find_significant_swing(self, price_data: PriceData) -> tuple[float, float, datetime, datetime, str]:
        """Find the most significant swing high and low for Fibonacci calculation."""
        # Look for the highest high and lowest low in recent data
        lookback = min(50, price_data.length)  # Look back up to 50 periods

        recent_highs = price_data.highs[-lookback:]
        recent_lows = price_data.lows[-lookback:]
        recent_dates = price_data.dates[-lookback:]

        swing_high = max(recent_highs)
        swing_low = min(recent_lows)

        high_index = recent_highs.index(swing_high)
        low_index = recent_lows.index(swing_low)

        high_date = recent_dates[high_index]
        low_date = recent_dates[low_index]

        # Determine trend based on which came first
        if high_date > low_date:
            trend = "uptrend"
        else:
            trend = "downtrend"

        return swing_high, swing_low, high_date, low_date, trend

    def _find_nearest_fib_levels(self, levels: list[FibonacciLevel], current_price: float) -> tuple[float | None, float | None]:
        """Find nearest Fibonacci support and resistance levels."""
        support_levels = [level.price for level in levels if level.price < current_price]
        resistance_levels = [level.price for level in levels if level.price > current_price]

        nearest_support = max(support_levels) if support_levels else None
        nearest_resistance = min(resistance_levels) if resistance_levels else None

        return nearest_support, nearest_resistance
