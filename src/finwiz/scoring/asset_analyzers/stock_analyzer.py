"""
Stock Analyzer Strategy.

Implements asset-specific analysis for stocks.
Part of Phase 2A refactoring using Strategy Pattern.
Updated in Phase 2A.3 to use centralized ScoringThresholds.
"""

from __future__ import annotations

import logging
from typing import Any

from finwiz.scoring.asset_analyzers.base import AssetAnalyzer
from finwiz.scoring.scoring_thresholds import get_thresholds

logger = logging.getLogger(__name__)


class StockAnalyzer(AssetAnalyzer):
    """
    Stock-specific analysis strategy.

    Focuses on:
    - ROE (Return on Equity)
    - Debt-to-Equity ratio
    - Revenue growth
    - Profit margins

    Phase 2A.3: Uses centralized ScoringThresholds for all thresholds.
    """

    def __init__(self) -> None:
        """Initialize the stock analyzer."""
        self.logger = logger
        self.thresholds = get_thresholds()  # Default thresholds

    def calculate_fundamental_score(self, data: dict[str, Any]) -> tuple[float, dict[str, Any]]:
        """
        Calculate fundamental score for stocks.

        Scoring components:
        - ROE (40%): Return on Equity
        - Debt (30%): Debt-to-Equity ratio
        - Growth (20%): Revenue growth
        - Margin (10%): Profit margin

        Args:
            data: Dictionary containing stock analysis data

        Returns:
            Tuple of (score, details_dict)

        """
        details = {}

        # ROE (Return on Equity) - target 15%+
        roe = self._safe_get_float(data, "roe", 0.0)
        roe_score = self._score_roe(roe)
        details["roe"] = roe
        details["roe_score"] = roe_score

        # Debt-to-Equity ratio - lower is better
        debt_equity = self._safe_get_float(data, "debt_to_equity", 1.0)
        debt_score = self._score_debt_to_equity(debt_equity)
        details["debt_to_equity"] = debt_equity
        details["debt_score"] = debt_score

        # Revenue growth - target 10%+
        revenue_growth = self._safe_get_float(data, "revenue_growth", 0.0)
        growth_score = self._score_revenue_growth(revenue_growth)
        details["revenue_growth"] = revenue_growth
        details["growth_score"] = growth_score

        # Profit margin
        profit_margin = self._safe_get_float(data, "profit_margin", 0.0)
        margin_score = self._score_profit_margin(profit_margin)
        details["profit_margin"] = profit_margin
        details["margin_score"] = margin_score

        # Weighted average using configured weights
        fundamental_score = (
            self.thresholds.weight_stock_roe * roe_score
            + self.thresholds.weight_stock_debt * debt_score
            + self.thresholds.weight_stock_growth * growth_score
            + self.thresholds.weight_stock_margin * margin_score
        )

        details["fundamental_score"] = fundamental_score
        return fundamental_score, details

    def extract_metrics(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Extract stock-specific metrics from raw data.

        Args:
            data: Dictionary containing raw analysis data

        Returns:
            Dictionary with stock-specific metrics

        """
        return {
            "roe": self._safe_get_float(data, "roe", 0.0),
            "debt_to_equity": self._safe_get_float(data, "debt_to_equity", 1.0),
            "revenue_growth": self._safe_get_float(data, "revenue_growth", 0.0),
            "profit_margin": self._safe_get_float(data, "profit_margin", 0.0),
            "earnings_per_share": self._safe_get_float(data, "earnings_per_share", 0.0),
            "price_to_earnings": self._safe_get_float(data, "price_to_earnings", 0.0),
            "price_to_book": self._safe_get_float(data, "price_to_book", 0.0),
            "free_cash_flow": self._safe_get_float(data, "free_cash_flow", 0.0),
            "current_ratio": self._safe_get_float(data, "current_ratio", 1.0),
            "quick_ratio": self._safe_get_float(data, "quick_ratio", 1.0),
        }

    def validate_data(self, data: dict[str, Any]) -> bool:
        """
        Validate that required stock data fields are present.

        Args:
            data: Dictionary containing analysis data

        Returns:
            True if all required fields are present, False otherwise

        """
        required_fields = ["roe", "debt_to_equity", "revenue_growth", "profit_margin"]
        return all(field in data and data[field] is not None for field in required_fields)

    def _score_roe(self, roe: float) -> float:
        """Score ROE (Return on Equity) using configured thresholds."""
        if roe >= self.thresholds.roe_excellent:
            return 1.0
        elif roe >= self.thresholds.roe_very_good:
            return 0.8
        elif roe >= self.thresholds.roe_good:
            return 0.6
        elif roe >= self.thresholds.roe_acceptable:
            return 0.4
        else:
            return 0.2

    def _score_debt_to_equity(self, debt_equity: float) -> float:
        """Score Debt-to-Equity ratio (lower is better) using configured thresholds."""
        if debt_equity <= self.thresholds.debt_very_low:
            return 1.0
        elif debt_equity <= self.thresholds.debt_low:
            return 0.8
        elif debt_equity <= self.thresholds.debt_moderate:
            return 0.6
        elif debt_equity <= self.thresholds.debt_high:
            return 0.4
        else:
            return 0.2

    def _score_revenue_growth(self, revenue_growth: float) -> float:
        """Score revenue growth rate using configured thresholds."""
        if revenue_growth >= self.thresholds.growth_excellent:
            return 1.0
        elif revenue_growth >= self.thresholds.growth_very_good:
            return 0.8
        elif revenue_growth >= self.thresholds.growth_good:
            return 0.6
        elif revenue_growth >= self.thresholds.growth_acceptable:
            return 0.4
        else:
            return 0.2

    def _score_profit_margin(self, profit_margin: float) -> float:
        """Score profit margin using configured thresholds."""
        if profit_margin >= self.thresholds.margin_excellent:
            return 1.0
        elif profit_margin >= self.thresholds.margin_very_good:
            return 0.8
        elif profit_margin >= self.thresholds.margin_good:
            return 0.6
        elif profit_margin >= self.thresholds.margin_acceptable:
            return 0.4
        else:
            return 0.2

    def _safe_get_float(self, data: dict[str, Any], key: str, default: float) -> float:
        """Safely extract float value from data dictionary."""
        try:
            value = data.get(key)
            if value is None:
                return default
            return float(value)
        except (ValueError, TypeError):
            return default
