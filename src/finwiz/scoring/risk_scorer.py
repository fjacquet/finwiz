"""
Risk Scoring Module.

Handles risk assessment scoring based on volatility, drawdown, and beta.
Extracted from DeepAnalysisScorer as part of Phase 2A refactoring.
Updated in Phase 2A.3 to use centralized ScoringThresholds.
"""

from __future__ import annotations

import logging
from typing import Any

from finwiz.scoring.scoring_thresholds import ScoringThresholds, get_thresholds

logger = logging.getLogger(__name__)


class RiskScorer:
    """
    Risk assessment scorer for all asset classes.

    Calculates risk scores based on:
    - Volatility (annual volatility)
    - Maximum drawdown
    - Beta (market sensitivity)

    Returns scores on 0-1 scale where 1 = low risk.

    Phase 2A.3: Uses centralized ScoringThresholds for all thresholds.
    """

    def __init__(self, thresholds: ScoringThresholds | None = None) -> None:
        """
        Initialize the risk scorer.

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

    def calculate_risk_score(self, data: dict[str, Any]) -> tuple[float, dict[str, Any]]:
        """
        Calculate risk score (0-1 scale, where 1 = low risk).

        Based on volatility, maximum drawdown, and beta.

        Args:
            data: Dictionary containing risk analysis data

        Returns:
            Tuple of (score, details_dict)

        """
        details = {}

        # Volatility - lower is better (annual volatility) using configured thresholds
        volatility = self._safe_get_float(data, "volatility", 0.20)
        if volatility <= self.thresholds.volatility_very_low:
            vol_score = 1.0
        elif volatility <= self.thresholds.volatility_low:
            vol_score = 0.8
        elif volatility <= self.thresholds.volatility_moderate:
            vol_score = 0.6
        elif volatility <= self.thresholds.volatility_high:
            vol_score = 0.4
        else:  # Above high threshold
            vol_score = 0.2

        details["volatility"] = volatility
        details["volatility_score"] = vol_score

        # Maximum drawdown - lower is better (negative values) using configured thresholds
        max_drawdown = self._safe_get_float(data, "max_drawdown", -0.20)
        max_drawdown = abs(max_drawdown)  # Convert to positive for comparison

        if max_drawdown <= self.thresholds.drawdown_very_low:
            drawdown_score = 1.0
        elif max_drawdown <= self.thresholds.drawdown_low:
            drawdown_score = 0.8
        elif max_drawdown <= self.thresholds.drawdown_moderate:
            drawdown_score = 0.6
        elif max_drawdown <= self.thresholds.drawdown_high:
            drawdown_score = 0.4
        else:  # Above high threshold
            drawdown_score = 0.2

        details["max_drawdown"] = -max_drawdown  # Store as negative
        details["drawdown_score"] = drawdown_score

        # Beta - closer to 1.0 is better for most assets using configured thresholds
        beta = self._safe_get_float(data, "beta", 1.0)
        beta_deviation = abs(beta - 1.0)

        if beta_deviation <= self.thresholds.beta_excellent:
            beta_score = 1.0
        elif beta_deviation <= self.thresholds.beta_very_good:
            beta_score = 0.8
        elif beta_deviation <= self.thresholds.beta_good:
            beta_score = 0.6
        elif beta_deviation <= self.thresholds.beta_acceptable:
            beta_score = 0.4
        else:  # Above acceptable threshold
            beta_score = 0.2

        details["beta"] = beta
        details["beta_deviation"] = beta_deviation
        details["beta_score"] = beta_score

        # Weighted average using configured weights
        risk_score = self.thresholds.weight_risk_volatility * vol_score + self.thresholds.weight_risk_drawdown * drawdown_score + self.thresholds.weight_risk_beta * beta_score

        details["risk_score"] = risk_score
        return risk_score, details

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
