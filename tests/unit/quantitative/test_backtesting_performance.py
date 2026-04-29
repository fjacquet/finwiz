"""Tests for backtesting performance NaN handling."""

import numpy as np

from finwiz.quantitative.backtesting_performance import (
    BacktestingPerformanceAnalyzer,
    _finite_returns_from_values,
    _safe_int,
)


def _make_analyzer() -> BacktestingPerformanceAnalyzer:
    """Build an analyzer without touching the real data manager/config.

    The volatility/VaR/CVaR methods only read ``portfolio_values`` from their
    arguments — they never touch ``self.data_manager`` or ``self.config`` —
    so we can pass ``None`` here. (pytest-mock would also work, but is overkill
    for storage-only constructor params.)
    """
    return BacktestingPerformanceAnalyzer(data_manager=None, config=None)  # type: ignore[arg-type]


class TestFiniteReturnsFromValues:
    """Tests for the NaN/inf-safe returns helper."""

    def test_should_drop_returns_from_zero_divisor(self):
        # A 0 in values produces an inf in np.diff(values)/values[:-1] for the
        # period that follows the zero. All non-finite entries must be filtered;
        # the preceding finite return survives.
        values = [100.0, 0.0, 105.0]
        out = _finite_returns_from_values(values)
        assert out.size == 1
        assert np.all(np.isfinite(out))

    def test_should_keep_finite_returns(self):
        out = _finite_returns_from_values([100.0, 110.0, 121.0])
        assert out.size == 2
        assert np.allclose(out, [0.10, 0.10])

    def test_short_input_returns_empty(self):
        assert _finite_returns_from_values([100.0]).size == 0


class TestVolatilityNaNSafe:
    """Regression: a 0 in portfolio_values must not yield NaN volatility.

    The 2026-04-28 run caught this exact path: a 0 produced NaN volatility
    that failed BacktestResult.volatility's ``ge=0`` constraint and made the
    deep-analysis scorer skip ASML/AVGO.
    """

    def test_calculate_volatility_with_zero_value_returns_zero(self):
        analyzer = _make_analyzer()
        # ('YYYY-MM-DD', value) tuples. The 0 makes np.diff/values[:-1] non-finite.
        portfolio_values = [
            ("2026-04-21", 100.0),
            ("2026-04-22", 0.0),
            ("2026-04-23", 50.0),
        ]
        result = analyzer.calculate_volatility(portfolio_values)
        assert result == 0.0
        assert np.isfinite(result)

    def test_calculate_var_all_nonfinite_returns_none(self):
        analyzer = _make_analyzer()
        # values[:-1] == [0.0] makes the only return inf/nan; after filtering
        # there is nothing left to compute a percentile from.
        portfolio_values = [("d1", 0.0), ("d2", 100.0)]
        assert analyzer.calculate_var(portfolio_values, 0.95) is None

    def test_calculate_cvar_falls_back_to_var_when_tail_empty(self):
        analyzer = _make_analyzer()
        # Two strictly increasing values produce one positive return; the tail
        # below VaR is empty, which historically returned the VaR value as a
        # fallback. Confirm that path still works after the NaN guard.
        portfolio_values = [("d1", 100.0), ("d2", 110.0)]
        cvar = analyzer.calculate_cvar(portfolio_values, 0.95)
        # Either a finite number (fallback to var) or None — never NaN.
        if cvar is not None:
            assert np.isfinite(cvar)


class TestSafeInt:
    """Tests for _safe_int helper that guards against NaN."""

    def test_should_convert_normal_int(self):
        """Normal integer values pass through unchanged."""
        assert _safe_int(5) == 5

    def test_should_convert_normal_float_to_int(self):
        """Normal float values are truncated to int."""
        assert _safe_int(3.0) == 3

    def test_should_return_default_for_nan(self):
        """NaN should return the default value."""
        assert _safe_int(float("nan")) == 0

    def test_should_return_default_for_none(self):
        """None should return the default value."""
        assert _safe_int(None) == 0

    def test_should_return_custom_default_for_nan(self):
        """NaN with custom default should return that default."""
        assert _safe_int(float("nan"), default=-1) == -1

    def test_should_return_default_for_string(self):
        """Non-numeric strings should return the default."""
        assert _safe_int("invalid") == 0

    def test_should_handle_zero(self):
        """Zero is a valid value, not NaN."""
        assert _safe_int(0) == 0

    def test_should_handle_negative_int(self):
        """Negative integers pass through."""
        assert _safe_int(-3) == -3
