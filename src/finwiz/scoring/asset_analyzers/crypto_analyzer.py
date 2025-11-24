"""
Crypto Analyzer Strategy.

Implements asset-specific analysis for cryptocurrencies.
Part of Phase 2A refactoring using Strategy Pattern.
Updated in Phase 2A.3 to use centralized ScoringThresholds.
"""

from __future__ import annotations

import logging
from typing import Any

from finwiz.scoring.asset_analyzers.base import AssetAnalyzer
from finwiz.scoring.scoring_thresholds import get_thresholds

logger = logging.getLogger(__name__)


class CryptoAnalyzer(AssetAnalyzer):
    """
    Cryptocurrency-specific analysis strategy.

    Focuses on:
    - Market capitalization
    - Trading volume (24h)
    - Age/maturity
    - Adoption metrics

    Phase 2A.3: Uses centralized ScoringThresholds for all thresholds.
    """

    def __init__(self) -> None:
        """Initialize the crypto analyzer."""
        super().__init__()  # Initialize base class
        self.logger = logger
        self.thresholds = get_thresholds()  # Default thresholds

    def calculate_fundamental_score(self, data: dict[str, Any]) -> tuple[float, dict[str, Any]]:
        """
        Calculate fundamental score for cryptocurrencies.

        Scoring components:
        - Market cap (40%): Higher is better for stability
        - Volume (30%): Higher is better for liquidity
        - Age (20%): Older is more established
        - Supply metrics (10%): Tokenomics quality

        Args:
            data: Dictionary containing crypto analysis data

        Returns:
            Tuple of (score, details_dict)

        """
        details = {}

        # Market capitalization - higher is better for stability
        market_cap = self._safe_get_float(data, "market_cap", 0.0)
        market_cap_score = self._score_market_cap(market_cap)
        details["market_cap"] = market_cap
        details["market_cap_score"] = market_cap_score

        # 24h trading volume - higher is better for liquidity
        volume_24h = self._safe_get_float(data, "volume_24h", 0.0)
        volume_score = self._score_volume(volume_24h)
        details["volume_24h"] = volume_24h
        details["volume_score"] = volume_score

        # Age in years - older is more established
        age_years = self._safe_get_float(data, "age_years", 0.0)
        age_score = self._score_age(age_years)
        details["age_years"] = age_years
        details["age_score"] = age_score

        # Supply metrics - tokenomics quality
        circulating_supply = self._safe_get_float(data, "circulating_supply", 0.0)
        max_supply = self._safe_get_float(data, "max_supply", 0.0)
        supply_score = self._score_supply_metrics(circulating_supply, max_supply)
        details["circulating_supply"] = circulating_supply
        details["max_supply"] = max_supply
        details["supply_score"] = supply_score

        # Weighted average (Market cap 40%, Volume 30%, Age 20%, Supply 10%)
        fundamental_score = 0.40 * market_cap_score + 0.30 * volume_score + 0.20 * age_score + 0.10 * supply_score

        details["fundamental_score"] = fundamental_score
        return fundamental_score, details

    def extract_metrics(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Extract crypto-specific metrics from raw data.

        Args:
            data: Dictionary containing raw analysis data

        Returns:
            Dictionary with crypto-specific metrics

        """
        return {
            "market_cap": self._safe_get_float(data, "market_cap", 0.0),
            "volume_24h": self._safe_get_float(data, "volume_24h", 0.0),
            "age_years": self._safe_get_float(data, "age_years", 0.0),
            "circulating_supply": self._safe_get_float(data, "circulating_supply", 0.0),
            "max_supply": self._safe_get_float(data, "max_supply", 0.0),
            "total_supply": self._safe_get_float(data, "total_supply", 0.0),
            "market_cap_rank": data.get("market_cap_rank", 0),
            "all_time_high": self._safe_get_float(data, "all_time_high", 0.0),
            "all_time_low": self._safe_get_float(data, "all_time_low", 0.0),
        }

    def validate_data(self, data: dict[str, Any]) -> bool:
        """
        Validate that required crypto data fields are present.

        Args:
            data: Dictionary containing analysis data

        Returns:
            True if all required fields are present, False otherwise

        """
        required_fields = ["market_cap", "volume_24h", "age_years"]
        return all(field in data and data[field] is not None for field in required_fields)

    def _score_market_cap(self, market_cap: float) -> float:
        """Score market capitalization (higher is better) using configured thresholds."""
        if market_cap >= self.thresholds.market_cap_mega:
            return 1.0
        elif market_cap >= self.thresholds.market_cap_large:
            return 0.8
        elif market_cap >= self.thresholds.market_cap_mid:
            return 0.6
        elif market_cap >= self.thresholds.market_cap_small:
            return 0.4
        else:
            return 0.2

    def _score_volume(self, volume_24h: float) -> float:
        """Score 24h trading volume (higher is better) using configured thresholds."""
        if volume_24h >= self.thresholds.volume_very_high:
            return 1.0
        elif volume_24h >= self.thresholds.volume_high:
            return 0.8
        elif volume_24h >= self.thresholds.volume_good:
            return 0.6
        elif volume_24h >= self.thresholds.volume_moderate:
            return 0.4
        else:
            return 0.2

    def _score_age(self, age_years: float) -> float:
        """Score age in years (older is better) using configured thresholds."""
        if age_years >= self.thresholds.age_very_established:
            return 1.0
        elif age_years >= self.thresholds.age_established:
            return 0.8
        elif age_years >= self.thresholds.age_maturing:
            return 0.6
        elif age_years >= self.thresholds.age_young:
            return 0.4
        else:
            return 0.2

    def _score_supply_metrics(self, circulating_supply: float, max_supply: float) -> float:
        """Score supply metrics (tokenomics quality) using configured thresholds."""
        if max_supply <= 0:
            # Unlimited supply - neutral score
            return 0.5

        # Calculate circulation ratio
        circulation_ratio = circulating_supply / max_supply if max_supply > 0 else 0.0

        # Score based on circulation ratio using configured thresholds
        if circulation_ratio >= self.thresholds.circulation_high:
            return 1.0
        elif circulation_ratio >= self.thresholds.circulation_good:
            return 0.8
        elif circulation_ratio >= self.thresholds.circulation_moderate:
            return 0.6
        elif circulation_ratio >= self.thresholds.circulation_early:
            return 0.4
        else:
            return 0.2

    def _safe_get_float(self, data: dict[str, Any], key: str, default: float) -> float:
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
