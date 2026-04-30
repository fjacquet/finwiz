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
        # Use a series of equal positive returns so np.percentile produces a
        # threshold ABOVE every realised return — the ``returns <= threshold``
        # mask is then empty, exercising the "tail empty, fall back to VaR"
        # branch deterministically. (CodeRabbit follow-up: the previous
        # 2-point input made VaR equal the only return, so the fallback path
        # was not actually triggered.)
        portfolio_values = [
            ("d1", 100.0),
            ("d2", 110.0),
            ("d3", 121.0),
            ("d4", 133.1),
        ]
        var = analyzer.calculate_var(portfolio_values, 0.95)
        cvar = analyzer.calculate_cvar(portfolio_values, 0.95)
        assert cvar is not None
        assert np.isfinite(cvar)
        # When the tail is empty, the function returns var verbatim.
        assert cvar == var


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


# ---------------------------------------------------------------------------
# WS-B — Backtester resilience regression tests (2026-04-29 follow-up)
# ---------------------------------------------------------------------------


class _FakeDataManager:
    """Minimal data manager that returns a configurable benchmark frame.

    Hand-rolled stub — pytest-mock is overkill for a storage-only stand-in.
    """

    def __init__(self, frame):
        self._frame = frame

    def fetch_historical_data(self, *_args, **_kwargs):
        return self._frame


class _FakeConfig:
    risk_free_rate = 0.045


class TestCalculateBenchmarkMetricsResilience:
    """The 2026-04-29 run failed when the benchmark frame was empty or
    misaligned with the holding's trading days. Calling ``.iloc[0]`` on an
    empty Series raised ``IndexError``, which propagated up through
    ``calculate_performance_metrics`` and made the scorer mark
    ``volatility="missing"``. The function must now degrade gracefully.
    """

    def _make_analyzer(self, frame):
        return BacktestingPerformanceAnalyzer(data_manager=_FakeDataManager(frame), config=_FakeConfig())  # type: ignore[arg-type]

    def test_empty_benchmark_returns_neutral_defaults(self):
        import pandas as pd

        analyzer = self._make_analyzer(pd.DataFrame(columns=["Close"]))
        result = analyzer.calculate_benchmark_metrics(
            portfolio_values={"2026-04-01": 100.0, "2026-04-02": 102.0},
            benchmark_symbol="^GSPC",
            start_date=__import__("datetime").datetime(2026, 4, 1),
            end_date=__import__("datetime").datetime(2026, 4, 2),
        )
        assert result == (0.0, 0.0, 1.0)

    def test_one_row_benchmark_returns_neutral_defaults(self):
        import pandas as pd

        frame = pd.DataFrame({"Close": [100.0]}, index=pd.to_datetime(["2026-04-01"]))
        analyzer = self._make_analyzer(frame)
        result = analyzer.calculate_benchmark_metrics(
            portfolio_values={"2026-04-01": 100.0, "2026-04-02": 102.0},
            benchmark_symbol="^GSPC",
            start_date=__import__("datetime").datetime(2026, 4, 1),
            end_date=__import__("datetime").datetime(2026, 4, 2),
        )
        assert result == (0.0, 0.0, 1.0)

    def test_zero_initial_benchmark_returns_neutral_defaults(self):
        import pandas as pd

        frame = pd.DataFrame(
            {"Close": [0.0, 100.0]},
            index=pd.to_datetime(["2026-04-01", "2026-04-02"]),
        )
        analyzer = self._make_analyzer(frame)
        result = analyzer.calculate_benchmark_metrics(
            portfolio_values={"2026-04-01": 100.0, "2026-04-02": 102.0},
            benchmark_symbol="^GSPC",
            start_date=__import__("datetime").datetime(2026, 4, 1),
            end_date=__import__("datetime").datetime(2026, 4, 2),
        )
        assert result == (0.0, 0.0, 1.0)


class TestCalculatePerformanceMetricsShortPortfolio:
    """When Backtrader never produced ≥2 portfolio_values entries (empty
    data feed, all-NaN inputs, date-range collapse), downstream metric
    extraction is meaningless. The pre-validation guard returns a lawful
    BacktestResult (volatility=0.0) instead of letting the IndexError
    bubble up to mark the holding as "missing volatility".
    """

    def test_empty_portfolio_values_returns_safe_result(self):
        from datetime import datetime

        analyzer = BacktestingPerformanceAnalyzer(data_manager=_FakeDataManager(None), config=_FakeConfig())  # type: ignore[arg-type]

        class _Strat:
            portfolio_values = []

        result = analyzer.calculate_performance_metrics(
            strategy_instance=_Strat(),  # type: ignore[arg-type]
            symbol="ASML",
            start_date=datetime(2026, 4, 1),
            end_date=datetime(2026, 4, 30),
            initial_value=10000.0,
            final_value=10000.0,
        )
        assert result.volatility == 0.0
        assert result.var_95 is None
        assert result.cvar_95 is None
        assert result.symbol == "ASML"

    def test_one_entry_portfolio_values_returns_safe_result(self):
        from datetime import datetime

        analyzer = BacktestingPerformanceAnalyzer(data_manager=_FakeDataManager(None), config=_FakeConfig())  # type: ignore[arg-type]

        class _Strat:
            portfolio_values = [("2026-04-01", 10000.0)]

        result = analyzer.calculate_performance_metrics(
            strategy_instance=_Strat(),  # type: ignore[arg-type]
            symbol="AAPL",
            start_date=datetime(2026, 4, 1),
            end_date=datetime(2026, 4, 30),
            initial_value=10000.0,
            final_value=10000.0,
        )
        assert result.volatility == 0.0
        assert result.total_trades == 0
        assert result.symbol == "AAPL"
