"""
Technical Analysis Engine.

Main orchestrator for technical analysis using modular indicator calculators.
"""

import warnings
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd

from finwiz.quantitative.config import TechnicalIndicator, get_quant_config
from finwiz.tools.logger import get_logger

from .advanced_indicators import AdvancedIndicators
from .basic_indicators import BasicIndicators
from .specialized_indicators import SpecializedIndicators
from .technical_models import (
    ConfluenceZone,
    SignalStrength,
    SignalType,
    TechnicalAnalysisResult,
    TechnicalIndicatorResult,
    TechnicalSignal,
)

# Suppress TA-Lib warnings for cleaner output
warnings.filterwarnings("ignore", category=RuntimeWarning, module="talib")

logger = get_logger(__name__)


class TechnicalAnalysisEngine:
    """
    Technical analysis engine with TA-Lib integration.

    Provides comprehensive technical analysis capabilities including:
    - Multiple technical indicators (SMA, EMA, RSI, MACD, etc.)
    - Signal generation and confluence detection
    - Multi-timeframe analysis support
    """

    def __init__(self, config: Any | None = None) -> None:
        """
        Initialize technical analysis engine.

        Args:
            config: Optional configuration object

        """
        self.config = config or get_quant_config()
        self.logger = logger

        # Initialize indicator calculators
        self.basic_indicators = BasicIndicators(self.logger)
        self.advanced_indicators = AdvancedIndicators(self.logger)
        self.specialized_indicators = SpecializedIndicators(self.logger)

        # Default indicators to calculate
        self.default_indicators = [
            TechnicalIndicator.SMA,
            TechnicalIndicator.EMA,
            TechnicalIndicator.RSI,
            TechnicalIndicator.MACD,
            TechnicalIndicator.BOLLINGER_BANDS,
        ]

    def analyze_symbol(
        self,
        data: pd.DataFrame,
        symbol: str,
        timeframe: str = "1D",
        indicators: list[TechnicalIndicator] | None = None,
    ) -> TechnicalAnalysisResult:
        """
        Perform comprehensive technical analysis on a symbol.

        Args:
            data: OHLCV data DataFrame
            symbol: Symbol being analyzed
            timeframe: Timeframe of the data
            indicators: List of indicators to calculate (optional)

        Returns:
            Comprehensive technical analysis result

        """
        start_time = datetime.now()

        # Validate input data
        self._validate_data(data)

        # Use default indicators if none specified
        if indicators is None:
            indicators = self.default_indicators

        # Calculate individual indicators
        indicator_results = {}
        all_signals = []

        for indicator in indicators:
            try:
                result = self._calculate_indicator(data, indicator, symbol)
                indicator_results[indicator.value] = result
                all_signals.extend(result.signals)
            except Exception as e:
                self.logger.error(f"Failed to calculate {indicator.value} for {symbol}: {str(e)}")

        # Detect confluence zones
        confluence_zones = self._detect_confluence_zones(all_signals, data)

        # Generate overall signal
        overall_signal, overall_confidence, signal_strength = self._generate_overall_signal(all_signals)

        # Count signal types using numpy for efficiency
        signal_types = np.array([s.signal_type for s in all_signals])
        bullish_count = np.sum(np.isin(signal_types, [SignalType.BUY, SignalType.STRONG_BUY]))
        bearish_count = np.sum(np.isin(signal_types, [SignalType.SELL, SignalType.STRONG_SELL]))
        neutral_count = np.sum(signal_types == SignalType.HOLD)

        # Calculate analysis duration
        end_time = datetime.now()
        duration_ms = (end_time - start_time).total_seconds() * 1000

        result = TechnicalAnalysisResult(
            symbol=symbol,
            timeframe=timeframe,
            indicator_results=indicator_results,
            overall_signal=overall_signal,
            overall_confidence=overall_confidence,
            signal_strength=signal_strength,
            confluence_zones=confluence_zones,
            total_signals=len(all_signals),
            bullish_signals=int(bullish_count),
            bearish_signals=int(bearish_count),
            neutral_signals=int(neutral_count),
            analysis_duration_ms=duration_ms,
        )

        self.logger.info(
            f"Technical analysis complete for {symbol}: {overall_signal.value} "
            f"(confidence: {overall_confidence:.2f}, {len(confluence_zones)} confluence zones)"
        )

        return result

    def _calculate_indicator(self, data: pd.DataFrame, indicator: TechnicalIndicator, symbol: str) -> TechnicalIndicatorResult:
        """Calculate a specific technical indicator."""
        params = self.config.get_indicator_config(indicator)

        if indicator == TechnicalIndicator.SMA:
            return self.basic_indicators.calculate_sma(data, params.get("periods", [20, 50]))
        elif indicator == TechnicalIndicator.EMA:
            return self.basic_indicators.calculate_ema(data, params.get("periods", [12, 26]))
        elif indicator == TechnicalIndicator.RSI:
            return self.basic_indicators.calculate_rsi(
                data,
                params.get("period", 14),
                params.get("overbought", 70),
                params.get("oversold", 30),
            )
        elif indicator == TechnicalIndicator.MACD:
            return self.advanced_indicators.calculate_macd(
                data,
                params.get("fast", 12),
                params.get("slow", 26),
                params.get("signal", 9),
            )
        elif indicator == TechnicalIndicator.BOLLINGER_BANDS:
            return self.advanced_indicators.calculate_bollinger_bands(
                data,
                params.get("period", 20),
                params.get("std_dev", 2.0),
            )
        elif indicator == TechnicalIndicator.FIBONACCI:
            return self.specialized_indicators.calculate_fibonacci_retracements(
                data,
                params.get("lookback_period", 50),
            )
        elif indicator == TechnicalIndicator.ATR:
            return self.specialized_indicators.calculate_atr(
                data,
                params.get("period", 14),
            )
        else:
            raise ValueError(f"Unsupported indicator: {indicator}")

    def _detect_confluence_zones(self, signals: list[TechnicalSignal], data: pd.DataFrame) -> list[ConfluenceZone]:
        """Detect confluence zones where multiple indicators align."""
        if len(signals) < 2:
            return []

        confluence_zones = []
        current_price = data["Close"].iloc[-1]

        # Group signals by type and proximity
        buy_signals = [s for s in signals if s.signal_type in [SignalType.BUY, SignalType.STRONG_BUY]]
        sell_signals = [s for s in signals if s.signal_type in [SignalType.SELL, SignalType.STRONG_SELL]]

        # Detect bullish confluence using numpy for efficiency
        if len(buy_signals) >= 2:
            confidences = np.array([s.confidence for s in buy_signals])
            avg_confidence = np.mean(confidences)

            strength_scores = {"very_weak": 1, "weak": 2, "moderate": 3, "strong": 4, "very_strong": 5}
            strengths = np.array([strength_scores.get(s.strength.value, 3) for s in buy_signals])
            avg_strength_score = np.mean(strengths)

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

        # Detect bearish confluence using numpy for efficiency
        if len(sell_signals) >= 2:
            confidences = np.array([s.confidence for s in sell_signals])
            avg_confidence = np.mean(confidences)

            strength_scores = {"very_weak": 1, "weak": 2, "moderate": 3, "strong": 4, "very_strong": 5}
            strengths = np.array([strength_scores.get(s.strength.value, 3) for s in sell_signals])
            avg_strength_score = np.mean(strengths)

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

        # Weight signals by type and strength
        signal_weights = {
            SignalType.STRONG_BUY: 2.0,
            SignalType.BUY: 1.0,
            SignalType.HOLD: 0.0,
            SignalType.SELL: -1.0,
            SignalType.STRONG_SELL: -2.0,
        }

        strength_weights = {
            SignalStrength.VERY_STRONG: 1.0,
            SignalStrength.STRONG: 0.8,
            SignalStrength.MODERATE: 0.6,
            SignalStrength.WEAK: 0.4,
            SignalStrength.VERY_WEAK: 0.2,
        }

        # Vectorized signal weighting calculation using numpy
        signal_weights_array = np.array([signal_weights.get(s.signal_type, 0.0) for s in signals])
        strength_weights_array = np.array([strength_weights.get(s.strength, 0.6) for s in signals])
        confidences_array = np.array([s.confidence for s in signals])

        weights = confidences_array * strength_weights_array
        weighted_scores = signal_weights_array * weights

        total_weight = np.sum(weights)
        if total_weight == 0:
            return SignalType.HOLD, 0.0, SignalStrength.VERY_WEAK

        normalized_score = np.sum(weighted_scores) / total_weight
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
            raise ValueError("Input data is empty")

        required_columns = ["Open", "High", "Low", "Close", "Volume"]
        missing_columns = [col for col in required_columns if col not in data.columns]

        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

        if len(data) < 20:
            self.logger.warning(f"Limited data available: {len(data)} rows. Some indicators may not be reliable.")


# Convenience functions for backward compatibility
def calculate_technical_indicators(data: pd.DataFrame, symbol: str, timeframe: str = "1D") -> TechnicalAnalysisResult:
    """
    Calculate technical indicators for a symbol.

    Args:
        data: OHLCV data DataFrame
        symbol: Symbol to analyze
        timeframe: Data timeframe

    Returns:
        Technical analysis result

    """
    engine = TechnicalAnalysisEngine()
    return engine.analyze_symbol(data, symbol, timeframe)


def detect_confluence_zones(data: pd.DataFrame, symbol: str, min_confluence: int = 2) -> list[ConfluenceZone]:
    """
    Detect confluence zones for a symbol.

    Args:
        data: OHLCV data DataFrame
        symbol: Symbol to analyze
        min_confluence: Minimum number of signals for confluence

    Returns:
        List of confluence zones

    """
    result = calculate_technical_indicators(data, symbol)
    return [zone for zone in result.confluence_zones if len(zone.contributing_signals) >= min_confluence]


# Backward compatibility alias
get_confluence_signals = detect_confluence_zones
