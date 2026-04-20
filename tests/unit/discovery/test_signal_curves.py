"""Unit tests for rebalanced signal curves.

Anchor-point tests lock in the public shape of each curve so that
``MomentumScanner`` / ``BreakoutDetector`` consumers can rely on:

* Volume ``1.0`` → neutral ``0.5`` (normal volume is neither signal nor penalty).
* RSI ``65`` → peak ``1.0`` (bullish regime).
* Strong movers (ROC 50%+) separate from decent ones (ROC 28%).
* Monotonicity holds on the segments PM reasoning depends on.

Plus an explicit gate test for the signal-strength filter that excludes
SUSHI/DLR-class noise from the opportunity list.
"""

from __future__ import annotations

import pytest

from finwiz.discovery.signal_curves import (
    has_at_least_one_strong_signal,
    momentum_signal_score,
    rsi_signal_score,
    volume_anomaly_score,
)


class TestVolumeAnomalyScore:
    """Volume curve: neutral band at 1x, saturation at 3x, no cliffs."""

    @pytest.mark.parametrize(
        ("ratio", "expected"),
        [
            (-0.1, 0.0),
            (0.0, 0.0),
            (0.3, 0.1),
            (0.5, 0.1),
            (0.8, 0.5),
            (1.0, 0.5),
            (1.2, 0.5),
            (3.0, 1.0),
            (5.0, 1.0),
        ],
    )
    def test_anchor_points(self, ratio: float, expected: float) -> None:
        assert volume_anomaly_score(ratio) == pytest.approx(expected, abs=1e-9)

    def test_ramp_between_neutral_and_saturation_is_monotone(self) -> None:
        """Between 1.2 and 3.0 the curve must never decrease."""
        prev = volume_anomaly_score(1.2)
        for step in range(1, 19):
            ratio = 1.2 + step * 0.1
            score = volume_anomaly_score(ratio)
            assert score >= prev, f"non-monotone at ratio {ratio}: {score} < {prev}"
            prev = score

    def test_mid_ramp_lies_between_endpoints(self) -> None:
        """At ratio 2.0 the score sits strictly between 0.5 and 1.0."""
        score = volume_anomaly_score(2.0)
        assert 0.5 < score < 1.0


class TestRsiSignalScore:
    """RSI curve: smooth hump peaking at 65, monotone taper on each side, no inversion cliff."""

    @pytest.mark.parametrize(
        ("rsi", "expected"),
        [
            (20.0, 0.5),
            (30.0, 0.5),
            (50.0, 0.4),
            (65.0, 1.0),
            (80.0, 0.7),
            (90.0, 0.4),
            (100.0, 0.3),
        ],
    )
    def test_anchor_points(self, rsi: float, expected: float) -> None:
        assert rsi_signal_score(rsi) == pytest.approx(expected, abs=1e-9)

    def test_peak_is_at_65(self) -> None:
        peak = rsi_signal_score(65.0)
        for rsi in (30.0, 50.0, 60.0, 70.0, 80.0, 90.0):
            assert rsi_signal_score(rsi) <= peak

    def test_no_cliff_at_80(self) -> None:
        """AMD-at-79 regression: the old curve inverted at RSI 80 (0.8 → 0.3).

        The new curve must be smooth across that boundary.
        """
        below = rsi_signal_score(79.9)
        above = rsi_signal_score(80.0)
        assert abs(below - above) < 0.05


class TestMomentumSignalScore:
    """ROC curve: zero for negatives, separates strong movers from decent ones."""

    @pytest.mark.parametrize(
        ("roc", "expected"),
        [
            (-0.5, 0.0),
            (0.0, 0.0),
            (0.05, 0.3),
            (0.10, 0.5),
            (0.20, 0.85),
            (0.30, 0.95),
            (0.50, 1.0),
            (1.11, 1.0),
        ],
    )
    def test_anchor_points(self, roc: float, expected: float) -> None:
        assert momentum_signal_score(roc) == pytest.approx(expected, abs=1e-9)

    def test_strong_mover_separates_from_decent(self) -> None:
        """ENJ's 111% must score higher than AMD's 28%.

        Under the pre-rebalance curve (min(1, roc/20.0)) both saturated at 1.0.
        """
        amd = momentum_signal_score(0.28)
        enj = momentum_signal_score(1.11)
        assert enj > amd, f"strong mover must separate: enj={enj} vs amd={amd}"

    def test_monotone_on_positive_range(self) -> None:
        prev = 0.0
        for i in range(0, 51):
            roc = i * 0.02  # 0% → 100% in 2% steps
            score = momentum_signal_score(roc)
            assert score >= prev, f"non-monotone at roc {roc}: {score} < {prev}"
            prev = score


class TestHasAtLeastOneStrongSignal:
    """Signal-strength gate — keeps SUSHI / DLR-class noise out of the opportunity list."""

    def test_volume_inflection_alone_passes(self) -> None:
        assert has_at_least_one_strong_signal(1.8, 55.0, 0.05, "stock") is True

    def test_rsi_in_active_band_alone_passes(self) -> None:
        assert has_at_least_one_strong_signal(1.0, 70.0, 0.02, "stock") is True

    def test_roc_above_threshold_alone_passes(self) -> None:
        assert has_at_least_one_strong_signal(1.0, 55.0, 0.12, "stock") is True

    def test_all_weak_signals_rejected(self) -> None:
        """SUSHI-class: normal volume + mid-60s RSI + single-digit ROC."""
        assert has_at_least_one_strong_signal(1.0, 55.0, 0.03, "crypto") is False

    def test_dlr_class_rejected(self) -> None:
        """DLR-class: drifting volume, RSI just above 50, mild ROC."""
        assert has_at_least_one_strong_signal(0.9, 52.0, 0.04, "stock") is False

    def test_rsi_above_active_band_does_not_pass_alone(self) -> None:
        """RSI 85 is exhaustion, not active bullishness — must rely on another signal."""
        assert has_at_least_one_strong_signal(1.0, 85.0, 0.02, "stock") is False
