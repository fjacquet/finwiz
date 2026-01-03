"""
Technical Scoring Module.

Handles technical analysis scoring based on RSI, trend analysis, and momentum indicators.
Extracted from DeepAnalysisScorer as part of Phase 2A refactoring.
Updated in Phase 2A.3 to use centralized ScoringThresholds.
"""

from __future__ import annotations

import logging
from typing import Any

from finwiz.scoring.thresholds import ScoringThresholds, get_thresholds

logger = logging.getLogger(__name__)


class TechnicalScorer:
    """
    Technical analysis scorer for all asset classes.

    Calculates technical scores based on:
    - RSI (Relative Strength Index)
    - Trend analysis (moving averages)
    - MACD momentum indicators

    Phase 2A.3: Uses centralized ScoringThresholds for all thresholds.
    """

    def __init__(self, thresholds: ScoringThresholds | None = None) -> None:
        """
        Initialize the technical scorer.

        Args:
            thresholds: Optional custom thresholds (defaults to DEFAULT_THRESHOLDS)

        """
        self.logger = logger
        self.thresholds = thresholds or get_thresholds()
        self._data_quality_metrics = None

    def set_data_quality_metrics(self, metrics: Any) -> None:
        """
        Set data quality metrics tracker.

        Args:
            metrics: DataQualityMetrics instance for tracking field calculations

        """
        self._data_quality_metrics = metrics

    def calculate_technical_score(self, data: dict[str, Any]) -> tuple[float, dict[str, Any]]:
        """
        Calculate technical score based on RSI, trend analysis, and momentum.

        Args:
            data: Dictionary containing technical analysis data

        Returns:
            Tuple of (score, details_dict)

        """
        details: dict[str, Any] = {}

        # RSI (Relative Strength Index) - target neutral range using configured thresholds
        rsi = self._safe_get_float(data, "rsi", 50.0)
        if self.thresholds.rsi_neutral_min <= rsi <= self.thresholds.rsi_neutral_max:  # Neutral zone
            rsi_score = 1.0
        elif self.thresholds.rsi_good_min <= rsi <= self.thresholds.rsi_good_max:  # Good range
            rsi_score = 0.8
        elif self.thresholds.rsi_acceptable_min <= rsi <= self.thresholds.rsi_acceptable_max:  # Acceptable range
            rsi_score = 0.6
        elif self.thresholds.rsi_warning_min <= rsi <= self.thresholds.rsi_warning_max:  # Warning range
            rsi_score = 0.4
        else:  # Extreme overbought/oversold
            rsi_score = 0.2

        details["rsi"] = rsi
        details["rsi_score"] = rsi_score

        # Trend analysis (moving averages)
        price = self._safe_get_float(data, "current_price", 100.0)
        ma_50 = self._safe_get_float(data, "moving_avg_50", price)
        ma_200 = self._safe_get_float(data, "moving_avg_200", price)

        # Price vs moving averages
        if price > ma_50 > ma_200:  # Strong uptrend
            trend_score = 1.0
            trend_direction = "strong_uptrend"
        elif price > ma_50 and price > ma_200:  # Uptrend
            trend_score = 0.8
            trend_direction = "uptrend"
        elif price > ma_200:  # Weak uptrend
            trend_score = 0.6
            trend_direction = "weak_uptrend"
        elif price < ma_50 and price < ma_200 and ma_50 < ma_200:  # Strong downtrend
            trend_score = 0.2
            trend_direction = "strong_downtrend"
        elif price < ma_50 or price < ma_200:  # Downtrend
            trend_score = 0.4
            trend_direction = "downtrend"
        else:  # Sideways
            trend_score = 0.5
            trend_direction = "sideways"

        details["current_price"] = price
        details["moving_avg_50"] = ma_50
        details["moving_avg_200"] = ma_200
        details["trend_score"] = trend_score
        details["trend_direction"] = trend_direction

        # MACD momentum using configured threshold
        macd = self._safe_get_float(data, "macd", 0.0)
        macd_signal = self._safe_get_float(data, "macd_signal", 0.0)
        macd_diff = macd - macd_signal

        if macd_diff > 0 and macd > 0:  # Strong bullish momentum
            momentum_score = 1.0
        elif macd_diff > 0:  # Bullish momentum
            momentum_score = 0.8
        elif abs(macd_diff) < self.thresholds.macd_neutral_threshold:  # Neutral momentum
            momentum_score = 0.6
        elif macd_diff < 0:  # Bearish momentum
            momentum_score = 0.4
        else:  # Strong bearish momentum
            momentum_score = 0.2

        details["macd"] = macd
        details["macd_signal"] = macd_signal
        details["macd_diff"] = macd_diff
        details["momentum_score"] = momentum_score

        # Weighted average using configured weights
        technical_score = (
            self.thresholds.weight_technical_rsi * rsi_score + self.thresholds.weight_technical_trend * trend_score + self.thresholds.weight_technical_momentum * momentum_score
        )

        details["technical_score"] = technical_score
        return technical_score, details

    def _safe_get_float(self, data: dict[str, Any], key: str, default: float | None = None) -> float:
        """
        Safely extract float value from data dictionary.

        Args:
            data: Data dictionary
            key: Key to extract
            default: Default value if key is missing

        Returns:
            Float value from data

        """
        try:
            value = data.get(key)
            final_default = default if default is not None else 0.0
            if value is None:
                self._track_calculated_field(key, None, final_default)
                return final_default
            float_value = float(value)
            self._track_calculated_field(key, float_value, final_default)
            return float_value
        except (ValueError, TypeError):
            final_default = default if default is not None else 0.0
            self._track_calculated_field(key, None, final_default)
            return final_default

    def _track_calculated_field(self, field_name: str, value: Any, default: Any) -> None:
        """
        Track whether a field was successfully calculated or defaulted.

        Args:
            field_name: Name of the field
            value: Actual value extracted
            default: Default value that would be used

        """
        if self._data_quality_metrics is None:
            return

        # If value equals default, it means we're using fallback
        if value == default or value is None:
            self._data_quality_metrics.record_defaulted_field(field_name, default)
        else:
            self._data_quality_metrics.record_calculated_field(field_name)
