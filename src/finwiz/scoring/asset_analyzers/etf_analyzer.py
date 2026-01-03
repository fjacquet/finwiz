"""
ETF Analyzer Strategy.

Implements asset-specific analysis for ETFs.
Part of Phase 2A refactoring using Strategy Pattern.
Updated in Phase 2A.3 to use centralized ScoringThresholds.
"""

from __future__ import annotations

import logging
from typing import Any

from finwiz.scoring.asset_analyzers.base import AssetAnalyzer
from finwiz.scoring.thresholds import get_thresholds

logger = logging.getLogger(__name__)


class ETFAnalyzer(AssetAnalyzer):
    """
    ETF-specific analysis strategy.

    Focuses on:
    - Expense ratio
    - Tracking error
    - Assets Under Management (AUM)
    - Diversification quality

    Phase 2A.3: Uses centralized ScoringThresholds for all thresholds.
    """

    def __init__(self) -> None:
        """Initialize the ETF analyzer."""
        super().__init__()  # Initialize base class
        self.logger = logger
        self.thresholds = get_thresholds()  # Default thresholds

    def calculate_fundamental_score(self, data: dict[str, Any]) -> tuple[float, dict[str, Any]]:
        """
        Calculate fundamental score for ETFs.

        Scoring components:
        - Expense ratio (50%): Lower is better
        - Tracking error (30%): Lower is better
        - AUM (20%): Higher is better for liquidity

        Args:
            data: Dictionary containing ETF analysis data

        Returns:
            Tuple of (score, details_dict)

        """
        details: dict[str, Any] = {}

        # Expense ratio - lower is better
        expense_ratio = self._safe_get_float(data, "expense_ratio", 1.0)
        assert expense_ratio is not None, "expense_ratio should not be None with default 1.0"
        expense_score = self._score_expense_ratio(expense_ratio)
        details["expense_ratio"] = expense_ratio
        details["expense_score"] = expense_score

        # Tracking error - lower is better (optional field)
        tracking_error_raw = data.get("tracking_error")
        tracking_available = tracking_error_raw is not None
        tracking_error: float | None = None
        tracking_score: float = 0.5

        if tracking_available and tracking_error_raw is not None:
            try:
                tracking_error = float(tracking_error_raw)
                tracking_score = self._score_tracking_error(tracking_error)
            except (ValueError, TypeError) as e:
                # Invalid tracking error value - use neutral score
                tracking_error = None
                tracking_score = 0.5
                tracking_available = False
                self.logger.warning(f"⚠️ Invalid tracking_error value '{tracking_error_raw}': {e}, using neutral score")
        else:
            # Tracking error not available - use neutral score
            tracking_error = None
            tracking_score = 0.5

        details["tracking_error"] = tracking_error
        details["tracking_error_available"] = tracking_available
        details["tracking_score"] = tracking_score

        # AUM (Assets Under Management) - higher is better for liquidity
        aum: float | None = self._safe_get_float(data, "aum", None)
        aum_available = aum is not None and aum > 0
        aum_score: float = 0.5

        if aum_available and aum is not None:
            aum_score = self._score_aum(aum)
        else:
            aum_score = 0.5  # Neutral score when data unavailable

        details["aum"] = aum
        details["aum_available"] = aum_available
        details["aum_score"] = aum_score

        # Weighted average using configured weights
        fundamental_score = self.thresholds.weight_etf_expense * expense_score + self.thresholds.weight_etf_tracking * tracking_score + self.thresholds.weight_etf_aum * aum_score

        details["fundamental_score"] = fundamental_score
        return fundamental_score, details

    def extract_metrics(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Extract ETF-specific metrics from raw data.

        Args:
            data: Dictionary containing raw analysis data

        Returns:
            Dictionary with ETF-specific metrics

        """
        return {
            "expense_ratio": self._safe_get_float(data, "expense_ratio", 1.0),
            "tracking_error": self._safe_get_float(data, "tracking_error", 1.0),
            "aum": self._safe_get_float(data, "aum", 0.0),
            "dividend_yield": self._safe_get_float(data, "dividend_yield", 0.0),
            "top_holdings": data.get("top_holdings", []),
            "sector_allocation": data.get("sector_allocation", {}),
            "geographic_allocation": data.get("geographic_allocation", {}),
        }

    def validate_data(self, data: dict[str, Any]) -> bool:
        """
        Validate that required ETF data fields are present.

        Args:
            data: Dictionary containing analysis data

        Returns:
            True if all required fields are present, False otherwise

        """
        # Only expense_ratio is truly required for ETFs
        # tracking_error and aum are optional
        return "expense_ratio" in data and data["expense_ratio"] is not None

    def _score_expense_ratio(self, expense_ratio: float) -> float:
        """Score expense ratio (lower is better) using configured thresholds."""
        if expense_ratio <= self.thresholds.expense_excellent:
            return 1.0
        elif expense_ratio <= self.thresholds.expense_very_good:
            return 0.8
        elif expense_ratio <= self.thresholds.expense_good:
            return 0.6
        elif expense_ratio <= self.thresholds.expense_acceptable:
            return 0.4
        else:
            return 0.2

    def _score_tracking_error(self, tracking_error: float) -> float:
        """Score tracking error (lower is better) using configured thresholds."""
        if tracking_error <= self.thresholds.tracking_excellent:
            return 1.0
        elif tracking_error <= self.thresholds.tracking_very_good:
            return 0.8
        elif tracking_error <= self.thresholds.tracking_good:
            return 0.6
        elif tracking_error <= self.thresholds.tracking_acceptable:
            return 0.4
        else:
            return 0.2

    def _score_aum(self, aum: float) -> float:
        """Score Assets Under Management (higher is better) using configured thresholds."""
        if aum >= self.thresholds.aum_excellent:
            return 1.0
        elif aum >= self.thresholds.aum_very_good:
            return 0.8
        elif aum >= self.thresholds.aum_good:
            return 0.6
        elif aum >= self.thresholds.aum_acceptable:
            return 0.4
        else:
            return 0.2

    def _safe_get_float(self, data: dict[str, Any], key: str, default: float | None) -> float | None:
        """Safely extract float value from data dictionary."""
        try:
            value = data.get(key)
            if value is None:
                self._track_calculated_field(key, None, default)
                return default
            float_value = float(value)
            self._track_calculated_field(key, float_value, default)
            return float_value
        except (ValueError, TypeError):
            self._track_calculated_field(key, None, default)
            return default
