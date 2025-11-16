"""
Signal analysis and validation for Twelve Data indicators.

This module provides signal analysis functionality for technical indicators,
including RSI, MACD, Bollinger Bands, and Stochastic oscillators.
"""

from __future__ import annotations

from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class SignalAnalyzer:
    """
    Signal analyzer for technical indicators.

    This class provides methods to analyze technical indicators and generate
    trading signals from indicator values.
    """

    def __init__(self) -> None:
        """Initialize the signal analyzer."""
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

    def analyze_macd_signal(self, macd_values: list) -> tuple[str, float]:
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

    def analyze_bollinger_squeeze(self, bb_values: list) -> str:
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

    def analyze_bollinger_position(self, bb_values: list, symbol: str) -> str:
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

    def analyze_stochastic_crossover(self, stoch_values: list) -> str:
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
        rsi_data: object | None,
        macd_data: object | None,
        bollinger_data: object | None,
        stochastic_data: object | None,
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
