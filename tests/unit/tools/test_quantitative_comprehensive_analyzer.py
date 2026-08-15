"""Unit tests for perform_comprehensive_analysis in quantitative_comprehensive_analyzer.py.

Technical analysis, backtesting, and performance analysis are three
independent computations over the same price history. Before this fix, all
three lived inside one shared try/except: a refusal or crash in ANY of them
-- for example a backtest whose series is shorter than the strategy's
lookback window -- discarded the OTHER TWO as well, even though they had
already succeeded independently. That is the actual mechanism behind
"drops the holding's entire quantitative payload": volatility comes from
performance_metrics, not from the backtest, so a backtest-side failure used
to take volatility down with it for no reason connected to volatility
itself. See Task 15.
"""

import json
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import pytest

from finwiz.quantitative.performance import PerformanceAnalyzer
from finwiz.quantitative.technical import TechnicalAnalysisEngine
from finwiz.schemas.tools import QuantitativeAnalysisInput
from finwiz.tools.quantitative_comprehensive_analyzer import perform_comprehensive_analysis


def _ohlcv(rows: int) -> pd.DataFrame:
    """Deterministic synthetic OHLCV data -- no loop-grown series, no network."""
    idx = pd.bdate_range("2024-01-01", periods=rows)
    rng = np.random.default_rng(0)
    close = 100 + np.cumsum(rng.normal(0, 1, rows))
    close = np.maximum(close, 1.0)
    return pd.DataFrame(
        {
            "Open": close * 0.99,
            "High": close * 1.01,
            "Low": close * 0.98,
            "Close": close,
            "Volume": rng.integers(1000, 5000, rows).astype(float),
        },
        index=idx,
    )


@pytest.fixture
def input_data() -> QuantitativeAnalysisInput:
    return QuantitativeAnalysisInput(symbol="TEST", asset_class="stock")


@pytest.fixture
def date_range() -> tuple[datetime, datetime]:
    end_date = datetime(2024, 6, 1)
    start_date = end_date - timedelta(days=90)
    return start_date, end_date


@pytest.fixture
def technical_engine() -> TechnicalAnalysisEngine:
    return TechnicalAnalysisEngine()


@pytest.fixture
def performance_analyzer() -> PerformanceAnalyzer:
    return PerformanceAnalyzer()


class TestBacktestFailureIsolation:
    """A backtest refusal or crash must not discard technical/performance results."""

    def test_backtest_none_preserves_performance_volatility(self, mocker, input_data, date_range, technical_engine, performance_analyzer):
        """run_strategy_backtest returning None (a short-series refusal, per
        Task 15's backtesting.py fix) must still yield a valid comprehensive
        result with performance_metrics.volatility populated -- that is
        where the scorer reads volatility from (deep_analysis_data_collector
        .flatten_collected_data), not from backtest_result."""
        start_date, end_date = date_range
        data = _ohlcv(65)
        backtesting_engine = mocker.Mock()
        backtesting_engine.run_strategy_backtest.return_value = None

        result_json = perform_comprehensive_analysis(
            data,
            input_data,
            start_date,
            end_date,
            technical_engine,
            backtesting_engine,
            performance_analyzer,
        )

        result = json.loads(result_json)
        assert result["backtest_result"] is None
        assert result["performance_metrics"]["volatility"] is not None
        assert result["technical_analysis"] is not None

    def test_backtest_exception_preserves_performance_volatility(self, mocker, input_data, date_range, technical_engine, performance_analyzer):
        """Whatever the exact exception a crashing backtest raises (an
        IndexError shaped like the 2026-08-15 run's "index N is out of
        bounds for axis 0 with size N", a bare "list index out of range",
        or anything else), it must not discard technical/performance
        analysis that already succeeded independently."""
        start_date, end_date = date_range
        data = _ohlcv(65)
        backtesting_engine = mocker.Mock()
        backtesting_engine.run_strategy_backtest.side_effect = IndexError("index 65 is out of bounds for axis 0 with size 65")

        result_json = perform_comprehensive_analysis(
            data,
            input_data,
            start_date,
            end_date,
            technical_engine,
            backtesting_engine,
            performance_analyzer,
        )

        result = json.loads(result_json)
        assert result["backtest_result"] is None
        assert result["performance_metrics"]["volatility"] is not None

    def test_performance_failure_preserves_backtest_and_technical(self, mocker, input_data, date_range, technical_engine):
        """The isolation cuts both ways: a performance-analysis failure must
        not discard a backtest result that already succeeded."""
        start_date, end_date = date_range
        data = _ohlcv(65)
        backtesting_engine = mocker.Mock()
        fake_backtest_result = mocker.Mock(
            strategy_name="SimpleMovingAverageStrategy",
            symbol="TEST",
            total_return=1.0,
            annualized_return=2.0,
            sharpe_ratio=0.5,
            max_drawdown=-3.0,
            total_trades=1,
            win_rate=1.0,
            volatility=10.0,
            var_95=None,
            start_date=start_date,
            end_date=end_date,
            initial_capital=100000.0,
            final_value=101000.0,
        )
        backtesting_engine.run_strategy_backtest.return_value = fake_backtest_result
        performance_analyzer = mocker.Mock()
        performance_analyzer.analyze_performance.side_effect = ZeroDivisionError("division by zero")

        result_json = perform_comprehensive_analysis(
            data,
            input_data,
            start_date,
            end_date,
            technical_engine,
            backtesting_engine,
            performance_analyzer,
        )

        result = json.loads(result_json)
        assert result["backtest_result"] is not None
        assert result["backtest_result"]["volatility"] == 10.0
        assert result["performance_metrics"] is None
        assert result["technical_analysis"] is not None

    def test_all_three_failing_returns_a_clean_error_not_a_crash(self, mocker, input_data, date_range):
        """When technical, backtest, and performance analysis all fail, the
        function returns an error string rather than propagating an
        unhandled exception up to the caller."""
        start_date, end_date = date_range
        data = _ohlcv(65)
        technical_engine = mocker.Mock()
        technical_engine.analyze_symbol.side_effect = RuntimeError("boom")
        backtesting_engine = mocker.Mock()
        backtesting_engine.run_strategy_backtest.side_effect = RuntimeError("boom")
        performance_analyzer = mocker.Mock()
        performance_analyzer.analyze_performance.side_effect = RuntimeError("boom")

        result = perform_comprehensive_analysis(
            data,
            input_data,
            start_date,
            end_date,
            technical_engine,
            backtesting_engine,
            performance_analyzer,
        )

        assert isinstance(result, str)
        assert "error" in result.lower()
        with pytest.raises(json.JSONDecodeError):
            json.loads(result)
