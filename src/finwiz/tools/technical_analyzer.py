"""
Advanced Technical Analysis Tools.

This module provides comprehensive technical analysis capabilities including
Fibonacci retracements, support/resistance levels, and multi-indicator confluence
zone detection for enhanced trading signal identification.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from datetime import datetime

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PriceData:
    """Price data structure for technical analysis."""

    dates: list[datetime]
    opens: list[float]
    highs: list[float]
    lows: list[float]
    closes: list[float]
    volumes: list[int]

    def __post_init__(self) -> None:
        """Validate that all lists have the same length."""
        lengths = [
            len(self.dates),
            len(self.opens),
            len(self.highs),
            len(self.lows),
            len(self.closes),
            len(self.volumes),
        ]
        if len(set(lengths)) != 1:
            raise ValueError("All price data lists must have the same length")

    @property
    def length(self) -> int:
        """Get the number of data points."""
        return len(self.dates)

    def to_dataframe(self) -> pd.DataFrame:
        """Convert to pandas DataFrame for easier analysis."""
        return pd.DataFrame(
            {
                "date": self.dates,
                "open": self.opens,
                "high": self.highs,
                "low": self.lows,
                "close": self.closes,
                "volume": self.volumes,
            }
        )


class FibonacciLevel(BaseModel):
    """Individual Fibonacci retracement level."""

    model_config = ConfigDict(extra="forbid")

    ratio: float = Field(..., description="Fibonacci ratio (e.g., 0.382, 0.618)")
    price: float = Field(..., description="Price level for this ratio")
    percentage: float = Field(..., description="Percentage retracement")
    level_type: str = Field(..., description="Type: retracement or extension")


class FibonacciLevels(BaseModel):
    """Complete Fibonacci analysis result."""

    model_config = ConfigDict(extra="forbid")

    swing_high: float = Field(..., description="Swing high price used for calculation")
    swing_low: float = Field(..., description="Swing low price used for calculation")
    swing_high_date: datetime = Field(..., description="Date of swing high")
    swing_low_date: datetime = Field(..., description="Date of swing low")
    trend_direction: str = Field(..., description="uptrend or downtrend")
    levels: list[FibonacciLevel] = Field(default_factory=list, description="Fibonacci levels")
    current_price: float = Field(..., description="Current price for reference")
    nearest_support: float | None = Field(None, description="Nearest Fibonacci support level")
    nearest_resistance: float | None = Field(None, description="Nearest Fibonacci resistance level")


class SupportResistanceLevel(BaseModel):
    """Individual support or resistance level."""

    model_config = ConfigDict(extra="forbid")

    price: float = Field(..., description="Price level")
    level_type: str = Field(..., description="support or resistance")
    strength: float = Field(..., ge=0.0, le=1.0, description="Strength of the level (0-1)")
    touch_count: int = Field(..., ge=1, description="Number of times price touched this level")
    last_touch_date: datetime = Field(..., description="Date of last touch")
    volume_confirmation: bool = Field(default=False, description="Whether volume confirms the level")


class SupportResistance(BaseModel):
    """Complete support and resistance analysis."""

    model_config = ConfigDict(extra="forbid")

    support_levels: list[SupportResistanceLevel] = Field(default_factory=list)
    resistance_levels: list[SupportResistanceLevel] = Field(default_factory=list)
    current_price: float = Field(..., description="Current price for reference")
    nearest_support: float | None = Field(None, description="Nearest support level")
    nearest_resistance: float | None = Field(None, description="Nearest resistance level")
    support_resistance_ratio: float = Field(..., description="Ratio of support to resistance levels")


class IndicatorSignal(BaseModel):
    """Individual technical indicator signal."""

    model_config = ConfigDict(extra="forbid")

    indicator_name: str = Field(..., description="Name of the technical indicator")
    signal_type: str = Field(..., description="buy, sell, or neutral")
    strength: float = Field(..., ge=0.0, le=1.0, description="Signal strength (0-1)")
    value: float = Field(..., description="Current indicator value")
    threshold: float | None = Field(None, description="Threshold value if applicable")
    description: str = Field(..., description="Human-readable signal description")


class ConfluenceZone(BaseModel):
    """Zone where multiple technical indicators align."""

    model_config = ConfigDict(extra="forbid")

    price_range: tuple[float, float] = Field(..., description="Price range of confluence zone")
    zone_type: str = Field(..., description="support, resistance, or reversal")
    confluence_score: float = Field(..., ge=0.0, le=1.0, description="Strength of confluence (0-1)")
    contributing_indicators: list[str] = Field(default_factory=list, description="Indicators in confluence")
    fibonacci_level: float | None = Field(None, description="Fibonacci level if present")
    support_resistance_level: float | None = Field(None, description="S/R level if present")
    signal_strength: float = Field(..., ge=0.0, le=1.0, description="Overall signal strength")


class TechnicalAnalysisResult(BaseModel):
    """Complete technical analysis result."""

    model_config = ConfigDict(extra="forbid")

    ticker: str = Field(..., description="Analyzed ticker symbol")
    analysis_date: datetime = Field(default_factory=datetime.now)
    fibonacci_levels: FibonacciLevels
    support_resistance: SupportResistance
    indicator_signals: list[IndicatorSignal] = Field(default_factory=list)
    confluence_zones: list[ConfluenceZone] = Field(default_factory=list)
    overall_signal: str = Field(..., description="buy, sell, or neutral")
    signal_confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence")


class TechnicalAnalyzer:
    """
    Advanced technical analysis engine.

    Provides comprehensive technical analysis including:
    - Fibonacci retracements and extensions
    - Dynamic support and resistance levels
    - Multi-indicator confluence zones
    - Signal strength assessment
    """

    def __init__(self) -> None:
        """Initialize the technical analyzer."""
        # Standard Fibonacci ratios
        self.fib_ratios = [0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0]
        self.fib_extensions = [1.272, 1.414, 1.618, 2.0, 2.618]

        # Parameters for support/resistance detection
        self.min_touches = 2
        self.price_tolerance = 0.02  # 2% tolerance for level grouping
        self.volume_threshold = 1.2  # 20% above average volume for confirmation

        # Confluence zone parameters
        self.confluence_tolerance = 0.01  # 1% tolerance for confluence
        self.min_confluence_indicators = 2

    def analyze(self, ticker: str, price_data: PriceData) -> TechnicalAnalysisResult:
        """
        Perform comprehensive technical analysis.

        Args:
            ticker: The ticker symbol being analyzed
            price_data: Historical price data

        Returns:
            Complete technical analysis result

        """
        logger.info(f"Starting technical analysis for {ticker}")

        if price_data.length < 20:
            raise ValueError("Insufficient data for technical analysis (minimum 20 periods required)")

        # Calculate Fibonacci levels
        fibonacci_levels = self.calculate_fibonacci_levels(price_data)

        # Identify support and resistance levels
        support_resistance = self.identify_support_resistance(price_data)

        # Calculate technical indicators
        indicator_signals = self.calculate_indicator_signals(price_data)

        # Find confluence zones
        confluence_zones = self.find_confluence_zones(
            fibonacci_levels, support_resistance, indicator_signals, price_data.closes[-1]
        )

        # Determine overall signal
        overall_signal, signal_confidence = self.determine_overall_signal(
            fibonacci_levels, support_resistance, indicator_signals, confluence_zones
        )

        return TechnicalAnalysisResult(
            ticker=ticker,
            fibonacci_levels=fibonacci_levels,
            support_resistance=support_resistance,
            indicator_signals=indicator_signals,
            confluence_zones=confluence_zones,
            overall_signal=overall_signal,
            signal_confidence=signal_confidence,
        )

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
                levels.append(FibonacciLevel(ratio=ratio, price=fib_price, percentage=ratio * 100, level_type="retracement"))

            # Add extensions above the high
            for ratio in self.fib_extensions:
                fib_price = swing_high + (price_range * (ratio - 1))
                levels.append(FibonacciLevel(ratio=ratio, price=fib_price, percentage=ratio * 100, level_type="extension"))
        else:
            # For downtrend, calculate retracements from low to high
            for ratio in self.fib_ratios:
                fib_price = swing_low + (price_range * ratio)
                levels.append(FibonacciLevel(ratio=ratio, price=fib_price, percentage=ratio * 100, level_type="retracement"))

            # Add extensions below the low
            for ratio in self.fib_extensions:
                fib_price = swing_low - (price_range * (ratio - 1))
                levels.append(FibonacciLevel(ratio=ratio, price=fib_price, percentage=ratio * 100, level_type="extension"))

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

    def identify_support_resistance(self, price_data: PriceData) -> SupportResistance:
        """Identify dynamic support and resistance levels."""
        current_price = price_data.closes[-1]

        # Find pivot points (local highs and lows)
        pivot_highs = self._find_pivot_highs(price_data.highs)
        pivot_lows = self._find_pivot_lows(price_data.lows)

        # Group similar price levels
        resistance_levels = self._group_price_levels(pivot_highs, price_data, "resistance")
        support_levels = self._group_price_levels(pivot_lows, price_data, "support")

        # Find nearest levels
        nearest_support = self._find_nearest_level(support_levels, current_price, "support")
        nearest_resistance = self._find_nearest_level(resistance_levels, current_price, "resistance")

        # Calculate support/resistance ratio
        sr_ratio = len(support_levels) / max(len(resistance_levels), 1)

        return SupportResistance(
            support_levels=support_levels,
            resistance_levels=resistance_levels,
            current_price=current_price,
            nearest_support=nearest_support,
            nearest_resistance=nearest_resistance,
            support_resistance_ratio=sr_ratio,
        )

    def calculate_indicator_signals(self, price_data: PriceData) -> list[IndicatorSignal]:
        """Calculate signals from various technical indicators."""
        signals = []

        # Convert to DataFrame for easier calculation
        df = price_data.to_dataframe()

        # RSI Signal
        rsi = self._calculate_rsi(df["close"])
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
        macd_line, signal_line, histogram = self._calculate_macd(df["close"])
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
        bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(df["close"])
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

    def find_confluence_zones(
        self,
        fibonacci_levels: FibonacciLevels,
        support_resistance: SupportResistance,
        indicator_signals: list[IndicatorSignal],
        current_price: float,
    ) -> list[ConfluenceZone]:
        """Find zones where multiple technical factors align."""
        confluence_zones = []

        # Combine all significant price levels
        all_levels = []

        # Add Fibonacci levels
        for fib_level in fibonacci_levels.levels:
            all_levels.append(
                {
                    "price": fib_level.price,
                    "type": "fibonacci",
                    "strength": 0.7 if fib_level.ratio in [0.382, 0.618] else 0.5,
                    "source": f"Fib {fib_level.ratio}",
                }
            )

        # Add support/resistance levels
        for sr_level in support_resistance.support_levels + support_resistance.resistance_levels:
            all_levels.append(
                {
                    "price": sr_level.price,
                    "type": "support_resistance",
                    "strength": sr_level.strength,
                    "source": f"S/R {sr_level.level_type}",
                }
            )

        # Group nearby levels into confluence zones
        grouped_levels = self._group_confluence_levels(all_levels, current_price)

        for group in grouped_levels:
            if len(group) >= self.min_confluence_indicators:
                # Calculate zone boundaries
                prices = [level["price"] for level in group]
                min_price = min(prices)
                max_price = max(prices)

                # Determine zone type
                zone_type = self._determine_zone_type(group, current_price)

                # Calculate confluence score
                confluence_score = self._calculate_confluence_score(group)

                # Get contributing indicators
                contributing_indicators = [level["source"] for level in group]

                # Find Fibonacci and S/R levels in this zone
                fib_level = next((level["price"] for level in group if level["type"] == "fibonacci"), None)
                sr_level = next((level["price"] for level in group if level["type"] == "support_resistance"), None)

                confluence_zones.append(
                    ConfluenceZone(
                        price_range=(min_price, max_price),
                        zone_type=zone_type,
                        confluence_score=confluence_score,
                        contributing_indicators=contributing_indicators,
                        fibonacci_level=fib_level,
                        support_resistance_level=sr_level,
                        signal_strength=confluence_score,
                    )
                )

        # Sort by confluence score
        confluence_zones.sort(key=lambda x: x.confluence_score, reverse=True)

        return confluence_zones[:5]  # Return top 5 confluence zones

    def determine_overall_signal(
        self,
        fibonacci_levels: FibonacciLevels,
        support_resistance: SupportResistance,
        indicator_signals: list[IndicatorSignal],
        confluence_zones: list[ConfluenceZone],
    ) -> tuple[str, float]:
        """Determine overall trading signal and confidence."""
        buy_signals = 0
        sell_signals = 0
        total_strength = 0

        # Weight indicator signals
        for signal in indicator_signals:
            if signal.signal_type == "buy":
                buy_signals += signal.strength
            elif signal.signal_type == "sell":
                sell_signals += signal.strength
            total_strength += signal.strength

        # Consider confluence zones
        for zone in confluence_zones:
            zone_strength = zone.confluence_score * 0.5  # Weight confluence zones
            if zone.zone_type == "support" and fibonacci_levels.current_price <= zone.price_range[1]:
                buy_signals += zone_strength
            elif zone.zone_type == "resistance" and fibonacci_levels.current_price >= zone.price_range[0]:
                sell_signals += zone_strength
            total_strength += zone_strength

        # Consider Fibonacci levels
        current_price = fibonacci_levels.current_price
        if fibonacci_levels.nearest_support and fibonacci_levels.nearest_resistance:
            support_distance = abs(current_price - fibonacci_levels.nearest_support) / current_price
            resistance_distance = abs(current_price - fibonacci_levels.nearest_resistance) / current_price

            if support_distance < 0.02:  # Within 2% of support
                buy_signals += 0.3
            elif resistance_distance < 0.02:  # Within 2% of resistance
                sell_signals += 0.3

            total_strength += 0.3

        # Determine signal
        if total_strength == 0:
            return "neutral", 0.0

        signal_ratio = (buy_signals - sell_signals) / total_strength
        confidence = min(1.0, total_strength / 3.0)  # Normalize confidence

        if signal_ratio > 0.2:
            return "buy", confidence
        elif signal_ratio < -0.2:
            return "sell", confidence
        else:
            return "neutral", confidence * 0.5

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

    def _find_pivot_highs(self, highs: list[float], window: int = 5) -> list[tuple[int, float]]:
        """Find pivot high points in price data."""
        pivots = []
        for i in range(window, len(highs) - window):
            if all(highs[i] >= highs[j] for j in range(i - window, i + window + 1) if j != i):
                pivots.append((i, highs[i]))
        return pivots

    def _find_pivot_lows(self, lows: list[float], window: int = 5) -> list[tuple[int, float]]:
        """Find pivot low points in price data."""
        pivots = []
        for i in range(window, len(lows) - window):
            if all(lows[i] <= lows[j] for j in range(i - window, i + window + 1) if j != i):
                pivots.append((i, lows[i]))
        return pivots

    def _group_price_levels(
        self, pivots: list[tuple[int, float]], price_data: PriceData, level_type: str
    ) -> list[SupportResistanceLevel]:
        """Group similar price levels and calculate their strength."""
        if not pivots:
            return []

        # Group pivots by similar price levels
        grouped_pivots = []
        for index, price in pivots:
            added_to_group = False
            for group in grouped_pivots:
                group_price = statistics.mean([p[1] for p in group])
                if abs(price - group_price) / group_price <= self.price_tolerance:
                    group.append((index, price))
                    added_to_group = True
                    break

            if not added_to_group:
                grouped_pivots.append([(index, price)])

        # Create support/resistance levels
        levels = []
        for group in grouped_pivots:
            if len(group) >= self.min_touches:
                avg_price = statistics.mean([p[1] for p in group])
                touch_count = len(group)

                # Calculate strength based on touch count and volume
                strength = min(1.0, touch_count / 5.0)  # Max strength at 5 touches

                # Get last touch date
                last_index = max([p[0] for p in group])
                last_touch_date = price_data.dates[last_index]

                # Check volume confirmation (simplified)
                volume_confirmation = self._check_volume_confirmation(group, price_data)

                levels.append(
                    SupportResistanceLevel(
                        price=avg_price,
                        level_type=level_type,
                        strength=strength,
                        touch_count=touch_count,
                        last_touch_date=last_touch_date,
                        volume_confirmation=volume_confirmation,
                    )
                )

        return levels

    def _find_nearest_level(self, levels: list[SupportResistanceLevel], current_price: float, level_type: str) -> float | None:
        """Find the nearest support or resistance level."""
        if not levels:
            return None

        if level_type == "support":
            support_levels = [level.price for level in levels if level.price < current_price]
            return max(support_levels) if support_levels else None
        else:
            resistance_levels = [level.price for level in levels if level.price > current_price]
            return min(resistance_levels) if resistance_levels else None

    def _check_volume_confirmation(self, group: list[tuple[int, float]], price_data: PriceData) -> bool:
        """Check if volume confirms the support/resistance level."""
        if not price_data.volumes:
            return False

        # Calculate average volume
        avg_volume = statistics.mean(price_data.volumes)

        # Check if volume was above average at touch points
        above_avg_count = 0
        for index, _ in group:
            if index < len(price_data.volumes) and price_data.volumes[index] > avg_volume * self.volume_threshold:
                above_avg_count += 1

        return above_avg_count >= len(group) * 0.5  # At least 50% of touches had high volume

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _calculate_macd(
        self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
    ) -> tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate MACD indicator."""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram

    def _calculate_bollinger_bands(
        self, prices: pd.Series, period: int = 20, std_dev: int = 2
    ) -> tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate Bollinger Bands."""
        middle = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        return upper, middle, lower

    def _group_confluence_levels(self, levels: list[dict], current_price: float) -> list[list[dict]]:
        """Group price levels that are close together for confluence analysis."""
        if not levels:
            return []

        # Sort levels by price
        sorted_levels = sorted(levels, key=lambda x: x["price"])

        groups = []
        current_group = [sorted_levels[0]]

        for level in sorted_levels[1:]:
            # Check if this level is close to the current group
            group_avg_price = statistics.mean([level_item["price"] for level_item in current_group])
            price_diff = abs(level["price"] - group_avg_price) / group_avg_price

            if price_diff <= self.confluence_tolerance:
                current_group.append(level)
            else:
                if len(current_group) >= self.min_confluence_indicators:
                    groups.append(current_group)
                current_group = [level]

        # Don't forget the last group
        if len(current_group) >= self.min_confluence_indicators:
            groups.append(current_group)

        return groups

    def _determine_zone_type(self, group: list[dict], current_price: float) -> str:
        """Determine if a confluence zone is support, resistance, or reversal."""
        avg_price = statistics.mean([level["price"] for level in group])

        if avg_price < current_price:
            return "support"
        elif avg_price > current_price:
            return "resistance"
        else:
            return "reversal"

    def _calculate_confluence_score(self, group: list[dict]) -> float:
        """Calculate the strength of a confluence zone."""
        # Base score on number of confluent factors
        base_score = min(1.0, len(group) / 4.0)  # Max score at 4 factors

        # Weight by individual strengths
        avg_strength = statistics.mean([level["strength"] for level in group])

        # Bonus for having both Fibonacci and S/R levels
        has_fib = any(level["type"] == "fibonacci" for level in group)
        has_sr = any(level["type"] == "support_resistance" for level in group)

        bonus = 0.2 if has_fib and has_sr else 0.0

        return min(1.0, base_score * avg_strength + bonus)
