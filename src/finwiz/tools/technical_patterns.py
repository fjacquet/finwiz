"""
Technical Pattern Recognition.

This module contains pattern recognition algorithms for identifying support/resistance,
confluence zones, pivot points, and overall signal determination.
"""

from __future__ import annotations

import statistics

from finwiz.tools.logger import get_logger
from finwiz.tools.technical_models import (
    ConfluenceZone,
    FibonacciLevels,
    IndicatorSignal,
    PriceData,
    SupportResistance,
    SupportResistanceLevel,
)

logger = get_logger(__name__)


class TechnicalPatterns:
    """Pattern recognition algorithms for technical analysis."""

    def __init__(self) -> None:
        """Initialize pattern recognition with standard parameters."""
        # Parameters for support/resistance detection
        self.min_touches = 2
        self.price_tolerance = 0.02  # 2% tolerance for level grouping
        self.volume_threshold = 1.2  # 20% above average volume for confirmation

        # Confluence zone parameters
        self.confluence_tolerance = 0.01  # 1% tolerance for confluence
        self.min_confluence_indicators = 2

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

    def _find_nearest_level(
        self, levels: list[SupportResistanceLevel], current_price: float, level_type: str
    ) -> float | None:
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
