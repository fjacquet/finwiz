"""Tests for MacroScorer (Phase 15 - MACRO-05 through MACRO-07)."""

from __future__ import annotations

from typing import Any

import pytest

from finwiz.schemas.macro import MacroSnapshot
from finwiz.scoring.macro_scorer import MacroScorer
from finwiz.scoring.thresholds import ScoringThresholds

# ---------------------------------------------------------------------------
# Fixtures & helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def scorer() -> MacroScorer:
    return MacroScorer()


@pytest.fixture
def custom_scorer() -> MacroScorer:
    return MacroScorer(
        thresholds=ScoringThresholds(
            macro_sensitivity_stock=1.5,
            macro_sensitivity_etf=1.0,
            macro_sensitivity_crypto=0.5,
        )
    )


def _make_macro_snapshot(**overrides: Any) -> dict[str, Any]:
    """Create a MacroSnapshot dict with sensible defaults, overriding any field."""
    defaults: dict[str, Any] = {
        "vix": 20.0,
        "fed_rate": 4.5,
        "cpi_yoy": 3.0,
        "treasury_10y": 4.0,
        "treasury_2y": 3.5,
        "yield_curve_spread": 0.5,
    }
    defaults.update(overrides)
    return defaults


def _make_macro_data(**snapshot_overrides: Any) -> dict[str, Any]:
    """Wrap snapshot into the data dict expected by calculate_macro_score."""
    snap = MacroSnapshot(**_make_macro_snapshot(**snapshot_overrides))
    return {"macro_snapshot": snap.model_dump(mode="json")}


# ---------------------------------------------------------------------------
# MACRO-07: No-data / robustness
# ---------------------------------------------------------------------------


class TestMacroScorerNoData:
    def test_no_macro_data(self, scorer: MacroScorer) -> None:
        score, details = scorer.calculate_macro_score({})
        assert score is None
        assert details["reason"] == "no_macro_data"

    def test_none_macro_data(self, scorer: MacroScorer) -> None:
        score, details = scorer.calculate_macro_score({"macro_snapshot": None})
        assert score is None
        assert details["reason"] == "no_macro_data"

    def test_invalid_type(self, scorer: MacroScorer) -> None:
        score, details = scorer.calculate_macro_score({"macro_snapshot": "bad"})
        assert score is None
        assert details["reason"] == "invalid_macro_data_type"


# ---------------------------------------------------------------------------
# MACRO-05: Yield curve classification
# ---------------------------------------------------------------------------


class TestYieldCurveClassification:
    @pytest.mark.parametrize(
        ("spread", "expected"),
        [
            (-1.0, "inverted"),
            (-0.01, "inverted"),
            (0.0, "flat"),
            (0.25, "flat"),
            (0.49, "flat"),
            (0.5, "normal"),
            (1.0, "normal"),
            (1.99, "normal"),
            (2.0, "steep"),
            (3.0, "steep"),
        ],
    )
    def test_classification_boundaries(self, scorer: MacroScorer, spread: float, expected: str) -> None:
        assert scorer.classify_yield_curve(spread) == expected


# ---------------------------------------------------------------------------
# MACRO-06: Macro scoring components
# ---------------------------------------------------------------------------


class TestMacroScoring:
    def test_high_vix_negative_score(self, scorer: MacroScorer) -> None:
        data = _make_macro_data(vix=35.0, yield_curve_spread=1.0, fed_rate=3.0)
        score, details = scorer.calculate_macro_score(data)
        assert score is not None
        assert score < 0

    def test_low_vix_positive_score(self, scorer: MacroScorer) -> None:
        data = _make_macro_data(vix=12.0, yield_curve_spread=1.0, fed_rate=3.0)
        score, details = scorer.calculate_macro_score(data)
        assert score is not None
        assert score > 0

    def test_inverted_yield_curve_negative(self, scorer: MacroScorer) -> None:
        data = _make_macro_data(vix=17.0, yield_curve_spread=-0.5, fed_rate=3.0)
        score, details = scorer.calculate_macro_score(data)
        assert score is not None
        assert score < 0

    def test_steep_yield_curve_positive(self, scorer: MacroScorer) -> None:
        data = _make_macro_data(vix=17.0, yield_curve_spread=2.5, fed_rate=3.0)
        score, details = scorer.calculate_macro_score(data)
        assert score is not None
        assert score > 0

    def test_tight_policy_negative(self, scorer: MacroScorer) -> None:
        data = _make_macro_data(vix=17.0, yield_curve_spread=1.0, fed_rate=6.0)
        score, details = scorer.calculate_macro_score(data)
        assert score is not None
        assert score < 0

    def test_accommodative_positive(self, scorer: MacroScorer) -> None:
        data = _make_macro_data(vix=17.0, yield_curve_spread=1.0, fed_rate=1.5)
        score, details = scorer.calculate_macro_score(data)
        assert score is not None
        assert score > 0

    def test_score_clamped_to_bounds(self, scorer: MacroScorer) -> None:
        # Extreme negative: high VIX + inverted curve + tight policy
        data = _make_macro_data(vix=50.0, yield_curve_spread=-2.0, fed_rate=8.0)
        score, _ = scorer.calculate_macro_score(data)
        assert score is not None
        assert -1.0 <= score <= 1.0

        # Extreme positive: low VIX + steep curve + accommodative
        data = _make_macro_data(vix=10.0, yield_curve_spread=3.0, fed_rate=1.0)
        score, _ = scorer.calculate_macro_score(data)
        assert score is not None
        assert -1.0 <= score <= 1.0

    def test_all_none_fields(self, scorer: MacroScorer) -> None:
        # MacroSnapshot with all scoring fields None
        snap = MacroSnapshot(
            vix=None,
            fed_rate=None,
            cpi_yoy=None,
            treasury_10y=None,
            treasury_2y=None,
            yield_curve_spread=None,
        )
        data = {"macro_snapshot": snap.model_dump(mode="json")}
        score, details = scorer.calculate_macro_score(data)
        # With all None fields, score should be 0.0 (no components contribute)
        assert score is not None
        assert score == pytest.approx(0.0)
        assert details["confidence"] == pytest.approx(0.0)
        assert details["yield_curve_regime"] == "unknown"


# ---------------------------------------------------------------------------
# SCORE-04: Per-asset-class sensitivity
# ---------------------------------------------------------------------------


class TestAssetClassSensitivity:
    def test_stock_full_sensitivity(self, scorer: MacroScorer) -> None:
        data = _make_macro_data(vix=35.0, yield_curve_spread=-0.5, fed_rate=6.0)
        score_stock, details = scorer.calculate_macro_score(data, asset_class="stock")
        assert score_stock is not None
        assert details["sensitivity"] == pytest.approx(1.0)

    def test_etf_moderate_sensitivity(self, scorer: MacroScorer) -> None:
        data = _make_macro_data(vix=35.0, yield_curve_spread=-0.5, fed_rate=6.0)
        score_etf, details = scorer.calculate_macro_score(data, asset_class="etf")
        assert score_etf is not None
        assert details["sensitivity"] == pytest.approx(0.7)

    def test_crypto_low_sensitivity(self, scorer: MacroScorer) -> None:
        data = _make_macro_data(vix=35.0, yield_curve_spread=-0.5, fed_rate=6.0)
        score_crypto, details = scorer.calculate_macro_score(data, asset_class="crypto")
        assert score_crypto is not None
        assert details["sensitivity"] == pytest.approx(0.3)

    def test_sensitivity_ordering(self, scorer: MacroScorer) -> None:
        """Same macro input: |stock_score| > |etf_score| > |crypto_score|."""
        data = _make_macro_data(vix=35.0, yield_curve_spread=-0.5, fed_rate=6.0)
        score_stock, _ = scorer.calculate_macro_score(data, asset_class="stock")
        score_etf, _ = scorer.calculate_macro_score(data, asset_class="etf")
        score_crypto, _ = scorer.calculate_macro_score(data, asset_class="crypto")
        assert score_stock is not None
        assert score_etf is not None
        assert score_crypto is not None
        assert abs(score_stock) > abs(score_etf) > abs(score_crypto)

    def test_custom_sensitivity(self, custom_scorer: MacroScorer) -> None:
        data = _make_macro_data(vix=35.0, yield_curve_spread=-0.5, fed_rate=6.0)
        _, details = custom_scorer.calculate_macro_score(data, asset_class="stock")
        assert details["sensitivity"] == pytest.approx(1.5)


# ---------------------------------------------------------------------------
# Confidence computation
# ---------------------------------------------------------------------------


class TestConfidence:
    def test_full_confidence(self, scorer: MacroScorer) -> None:
        """All 5 key fields present -> confidence=1.0."""
        data = _make_macro_data(vix=20.0, fed_rate=4.5, cpi_yoy=3.0, treasury_10y=4.0, treasury_2y=3.5)
        _, details = scorer.calculate_macro_score(data)
        assert details["confidence"] == pytest.approx(1.0)
        assert details["available_macro_fields"] == 5

    def test_partial_confidence(self, scorer: MacroScorer) -> None:
        """3 of 5 fields present -> confidence=0.6."""
        snap = MacroSnapshot(vix=20.0, fed_rate=4.5, cpi_yoy=3.0, treasury_10y=None, treasury_2y=None)
        data = {"macro_snapshot": snap.model_dump(mode="json")}
        _, details = scorer.calculate_macro_score(data)
        assert details["confidence"] == pytest.approx(0.6)
        assert details["available_macro_fields"] == 3

    def test_zero_confidence(self, scorer: MacroScorer) -> None:
        """0 of 5 fields present -> confidence=0.0."""
        snap = MacroSnapshot(vix=None, fed_rate=None, cpi_yoy=None, treasury_10y=None, treasury_2y=None, yield_curve_spread=None)
        data = {"macro_snapshot": snap.model_dump(mode="json")}
        _, details = scorer.calculate_macro_score(data)
        assert details["confidence"] == pytest.approx(0.0)
        assert details["available_macro_fields"] == 0


# ---------------------------------------------------------------------------
# Input type handling
# ---------------------------------------------------------------------------


class TestMacroSnapshotInput:
    def test_accepts_dict(self, scorer: MacroScorer) -> None:
        """macro_snapshot as dict (from model_dump) -> works."""
        data = _make_macro_data(vix=20.0)
        score, details = scorer.calculate_macro_score(data)
        assert score is not None
        assert "macro_score" in details

    def test_accepts_model(self, scorer: MacroScorer) -> None:
        """macro_snapshot as MacroSnapshot instance -> works."""
        snap = MacroSnapshot(**_make_macro_snapshot())
        data = {"macro_snapshot": snap}
        score, details = scorer.calculate_macro_score(data)
        assert score is not None
        assert "macro_score" in details
