"""Unit tests for ``discovery.market_data.factor_score_from_returns`` calibration.

The factor score gates discovery candidates against the C grade floor (0.65,
``grading_system.py``). These tests pin both ends of the ladder: a genuinely
strong return series must be able to reach the floor, and a flat/weak/negative
one must not. Beyond the degenerate constant-return series (zero volatility by
construction), several cases use a two-point alternating series that has an
*exact*, controllable mean and population std (matching ``numpy.std()``'s
default ``ddof=0``) so the volatility term is genuinely exercised rather than
pinned at its maximum.
"""

from __future__ import annotations

import pytest

from finwiz.discovery.market_data import factor_score_from_returns
from finwiz.scoring.grading_system import score_to_grade

ACTIONABLE_FLOOR = 0.65
ACTIONABLE_GRADES = {"C", "C+", "B", "B+", "A", "A+"}


def _constant_returns(daily: float, days: int = 126) -> list[float]:
    """A zero-volatility series: every day returns exactly ``daily``."""
    return [daily] * days


def _two_point_returns(cumulative: float, daily_vol: float, days: int = 126) -> list[float]:
    """An alternating series with an exact target cumulative return and daily std.

    Solves the constant per-day rate ``d`` that compounds to ``cumulative`` over
    ``days``, then alternates ``d + daily_vol`` / ``d - daily_vol`` so the
    population standard deviation (``numpy.std()`` default ``ddof=0``) is
    exactly ``daily_vol`` -- unlike a constant series, this exercises the
    volatility term instead of always pinning it at 1.0.
    """
    d = (1.0 + cumulative) ** (1.0 / days) - 1.0
    return [d + daily_vol if i % 2 == 0 else d - daily_vol for i in range(days)]


class TestShortSeries:
    def test_none_input_returns_none(self) -> None:
        assert factor_score_from_returns(None) is None

    def test_too_short_returns_none(self) -> None:
        assert factor_score_from_returns([0.01, 0.01]) is None


class TestCalibrationAgainstGradeLadder:
    """Pin both ends: strong performers must clear C, weak ones must not."""

    def test_strong_low_volatility_performer_clears_the_actionable_floor(self) -> None:
        # ~+30% over six months with a smooth daily gain -- an unambiguously good candidate.
        score = factor_score_from_returns(_constant_returns(0.0021))

        assert score is not None
        assert score >= ACTIONABLE_FLOOR
        assert score_to_grade(score).grade in ACTIONABLE_GRADES

    def test_flat_performer_stays_below_the_floor(self) -> None:
        score = factor_score_from_returns(_constant_returns(0.0))

        assert score is not None
        assert score < ACTIONABLE_FLOOR

    def test_declining_performer_scores_low(self) -> None:
        score = factor_score_from_returns(_constant_returns(-0.002))

        assert score is not None
        assert score < 0.5

    def test_realistic_strong_candidate_with_ordinary_volatility_clears_the_floor(self) -> None:
        # +12% cumulative over 126 trading days (~+25%/yr) with 1.5% daily volatility
        # -- realistic for a solid mid-cap, not the idealized zero-vol series above.
        returns = _two_point_returns(cumulative=0.12, daily_vol=0.015)
        score = factor_score_from_returns(returns)

        assert score is not None
        assert score >= ACTIONABLE_FLOOR
        assert score_to_grade(score).grade in ACTIONABLE_GRADES

    def test_realistic_mediocre_candidate_with_ordinary_volatility_stays_below_the_floor(self) -> None:
        # +8% cumulative over 126 trading days (~+16%/yr) with the same 1.5% daily
        # volatility -- a middling candidate must not clear the bar just because
        # the scale widened. This guards against "calibrating so hard everything clears."
        returns = _two_point_returns(cumulative=0.08, daily_vol=0.015)
        score = factor_score_from_returns(returns)

        assert score is not None
        assert score < ACTIONABLE_FLOOR

    def test_higher_cumulative_return_scores_higher_at_fixed_volatility(self) -> None:
        weaker = factor_score_from_returns(_two_point_returns(cumulative=0.05, daily_vol=0.015))
        stronger = factor_score_from_returns(_two_point_returns(cumulative=0.20, daily_vol=0.015))

        assert weaker is not None
        assert stronger is not None
        assert stronger > weaker

    def test_higher_volatility_scores_lower_at_fixed_cumulative_return(self) -> None:
        calmer = factor_score_from_returns(_two_point_returns(cumulative=0.10, daily_vol=0.010))
        choppier = factor_score_from_returns(_two_point_returns(cumulative=0.10, daily_vol=0.035))

        assert calmer is not None
        assert choppier is not None
        assert calmer > choppier


class TestScoreRange:
    @pytest.mark.parametrize("daily", [-0.05, -0.001, 0.0, 0.001, 0.05])
    def test_score_stays_in_unit_range(self, daily: float) -> None:
        score = factor_score_from_returns(_constant_returns(daily))

        assert score is not None
        assert 0.0 <= score <= 1.0
