"""Macro scoring engine for Phase 15.

Computes a normalized macro adjustment score from macroeconomic data
(VIX, yield curve, Fed rate) with per-asset-class sensitivity scaling.
"""

from __future__ import annotations

import logging
from typing import Any

from finwiz.schemas.macro import MacroSnapshot
from finwiz.scoring.thresholds import ScoringThresholds, get_thresholds

logger = logging.getLogger(__name__)


class MacroScorer:
    """Score macro environment impact on holdings.

    Follows the component scorer pattern (FundamentalScorer, TechnicalScorer,
    RiskScorer, SentimentScorer).  Receives raw data dict containing
    macro_snapshot, returns (score_or_None, details_dict).

    Key behaviors:
    - No macro data -> returns (None, {"reason": "no_macro_data"})
    - Has macro data -> computes VIX + yield-curve + Fed-rate composite score
    - Score scaled by per-asset-class sensitivity coefficient
    """

    def __init__(self, thresholds: ScoringThresholds | None = None) -> None:
        self.thresholds = thresholds or get_thresholds()

    def calculate_macro_score(
        self,
        data: dict[str, Any],
        asset_class: str = "stock",
    ) -> tuple[float | None, dict[str, Any]]:
        """Calculate macro adjustment score from raw analysis data.

        Args:
            data: Raw data dict. Expects data["macro_snapshot"] to be either:
                  - A dict (from MacroSnapshot.model_dump())
                  - A MacroSnapshot instance
                  - None (no macro data collected)
            asset_class: Asset class for sensitivity scaling ("stock", "etf", "crypto").

        Returns:
            Tuple of (score_or_None, details_dict).
            score is in [-1.0, +1.0] or None if no data.
            details contains scoring breakdown.
        """
        details: dict[str, Any] = {}

        # Extract macro snapshot data
        macro_raw = data.get("macro_snapshot")
        if macro_raw is None:
            details["reason"] = "no_macro_data"
            logger.debug("No macro snapshot data available")
            return None, details

        # Parse into MacroSnapshot if it's a dict
        try:
            if isinstance(macro_raw, dict):
                snapshot = MacroSnapshot(**macro_raw)
            elif isinstance(macro_raw, MacroSnapshot):
                snapshot = macro_raw
            else:
                details["reason"] = "invalid_macro_data_type"
                details["type"] = type(macro_raw).__name__
                logger.warning("Unexpected macro_snapshot type: %s", type(macro_raw))
                return None, details
        except Exception as e:
            details["reason"] = "parse_error"
            details["error"] = str(e)
            logger.warning("Failed to parse macro snapshot: %s", e)
            return None, details

        # Classify yield curve regime
        if snapshot.yield_curve_spread is not None:
            yield_regime = self.classify_yield_curve(snapshot.yield_curve_spread)
        else:
            yield_regime = "unknown"

        # Get market regime
        market_regime = snapshot.get_market_regime()

        # Compute regime score
        score = self._compute_regime_score(snapshot, yield_regime, market_regime, asset_class)

        # Compute confidence as proportion of available key fields
        confidence = self._compute_confidence(snapshot)

        # Get sensitivity applied
        sensitivity = self._get_asset_sensitivity(asset_class)

        # Build details
        details["yield_curve_regime"] = yield_regime
        details["market_regime"] = market_regime
        details["macro_score"] = score
        details["asset_class"] = asset_class
        details["confidence"] = confidence
        details["sensitivity"] = sensitivity
        details["available_macro_fields"] = self._count_available_fields(snapshot)

        logger.info(
            "Macro score for asset_class=%s: score=%.4f, confidence=%.4f, regime=%s, yield_curve=%s",
            asset_class,
            score,
            confidence,
            market_regime,
            yield_regime,
        )

        return score, details

    def classify_yield_curve(self, spread: float) -> str:
        """Classify yield curve regime from 10Y-2Y spread.

        Args:
            spread: 10Y-2Y Treasury spread in percentage points.

        Returns:
            One of "inverted", "flat", "normal", "steep".
        """
        if spread < self.thresholds.yield_curve_inverted:
            return "inverted"
        if spread < self.thresholds.yield_curve_flat:
            return "flat"
        if spread < self.thresholds.yield_curve_steep:
            return "normal"
        return "steep"

    def _compute_regime_score(
        self,
        snapshot: MacroSnapshot,
        yield_regime: str,
        market_regime: str,
        asset_class: str,
    ) -> float:
        """Compute macro regime score from components.

        Combines VIX, yield curve, and Fed rate signals into a single
        score in [-1.0, +1.0] where negative = headwinds, positive = tailwinds.

        Args:
            snapshot: Parsed MacroSnapshot data.
            yield_regime: Classified yield curve regime.
            market_regime: Classified market regime.
            asset_class: Asset class for sensitivity scaling.

        Returns:
            Clamped score in [-1.0, +1.0].
        """
        score = 0.0

        # VIX component
        if snapshot.vix is not None:
            if snapshot.vix > self.thresholds.macro_vix_high:
                score += -0.4
            elif snapshot.vix > self.thresholds.macro_vix_elevated:
                score += -0.1
            elif snapshot.vix < self.thresholds.macro_vix_low:
                score += 0.2

        # Yield curve component
        if yield_regime == "inverted":
            score += -0.3
        elif yield_regime == "flat":
            score += -0.1
        elif yield_regime == "steep":
            score += 0.2
        # "normal" and "unknown" contribute 0.0

        # Fed rate component
        if snapshot.fed_rate is not None:
            if snapshot.fed_rate > self.thresholds.macro_rate_tight:
                score += -0.1
            elif snapshot.fed_rate < self.thresholds.macro_rate_accommodative:
                score += 0.1

        # Apply per-asset-class sensitivity
        sensitivity = self._get_asset_sensitivity(asset_class)
        score *= sensitivity

        # Clamp to [-1.0, +1.0]
        return max(-1.0, min(1.0, score))

    def _get_asset_sensitivity(self, asset_class: str) -> float:
        """Get per-asset-class macro sensitivity coefficient.

        Args:
            asset_class: Asset class identifier.

        Returns:
            Sensitivity coefficient from thresholds.
        """
        if asset_class == "etf":
            return self.thresholds.macro_sensitivity_etf
        if asset_class == "crypto":
            return self.thresholds.macro_sensitivity_crypto
        return self.thresholds.macro_sensitivity_stock

    def _compute_confidence(self, snapshot: MacroSnapshot) -> float:
        """Compute data completeness confidence.

        Confidence = proportion of available key fields out of 5:
        vix, fed_rate, cpi_yoy, treasury_10y, treasury_2y.

        Args:
            snapshot: Parsed MacroSnapshot data.

        Returns:
            Confidence in [0.0, 1.0].
        """
        return self._count_available_fields(snapshot) / 5.0

    @staticmethod
    def _count_available_fields(snapshot: MacroSnapshot) -> int:
        """Count non-None key macro fields.

        Args:
            snapshot: Parsed MacroSnapshot data.

        Returns:
            Count of available fields (0-5).
        """
        count = 0
        if snapshot.vix is not None:
            count += 1
        if snapshot.fed_rate is not None:
            count += 1
        if snapshot.cpi_yoy is not None:
            count += 1
        if snapshot.treasury_10y is not None:
            count += 1
        if snapshot.treasury_2y is not None:
            count += 1
        return count
