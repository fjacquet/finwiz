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
        # risk_metrics is sourced from the backtest only, passed through
        # exactly as BacktestResult reports it (percent-scaled -- -3.0 here
        # means a -3% drawdown) -- no mixing with perf_metrics' fractional
        # scale (see generate_recommendation's docstring for why that mixing
        # is unsafe: only volatility has a normalizer, max_drawdown does
        # not). DeepAnalysisDataCollector._flatten_recursive additionally
        # excludes this whole risk_metrics block from the scorer's flat dict
        # (Task 15 review round 2) precisely because it is percent-scaled
        # and would otherwise be misread against the scorer's fractional
        # thresholds -- see test_deep_analysis_data_collector.py::TestFlattenExcludesPercentScaledDuplicates.
        assert result["quantitative_recommendation"]["risk_metrics"]["max_drawdown"] == -3.0
        assert result["quantitative_recommendation"]["risk_metrics"]["volatility"] == 10.0

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


class TestNoFabricatedRiskMetrics:
    """Review round 1, Critical: a fabricated 0.0 in risk_metrics used to
    leak into the scorer's flat dict (via
    DeepAnalysisDataCollector._flatten_recursive, which walks the whole
    quantitative_analysis payload and picks up the first "volatility" key it
    finds anywhere -- including quantitative_recommendation.risk_metrics)
    and defeat three of this plan's own defenses at once: Task 4/5's
    price-history volatility fallback (which only fires when the field is
    genuinely absent), and the Task 6 critical-field gate (which only
    refuses a holding by name when the field is missing). A 0.0 satisfies
    both checks and scores an unanalyzable holding as the safest one in the
    portfolio. These tests verify the fix end to end, through the real
    downstream consumers, not just perform_comprehensive_analysis in
    isolation."""

    def test_short_series_omits_risk_metrics_and_gate_refuses_by_name(self, mocker, input_data, date_range, technical_engine, performance_analyzer):
        """Reproduces the reviewer's scenario with real engines, nothing
        mocked: a single row of data is enough for analyze_symbol to
        succeed trivially (no indicator has enough history to fire, so
        there are simply no signals), but too short for the backtest
        (needs >= 60 bars, refuses with None) and too short for
        analyze_performance (pct_change().dropna() on 1 row yields 0
        returns, raising ZeroDivisionError internally).

        Verifies, through the real DeepAnalysisDataCollector.flatten_collected_data
        and the real critical_fields_config.validate_critical_fields -- not just
        perform_comprehensive_analysis's own JSON -- that:
        1. quantitative_recommendation.risk_metrics has no volatility/max_drawdown key.
        2. The flattened dict the scorer receives has no "volatility" key.
        3. The critical-field gate raises CriticalFieldError naming volatility
           as (missing), not as an invalid/absurd value -- i.e. the holding is
           refused by name, not scored as risk-free.
        """
        from finwiz.config.critical_fields_config import CriticalFieldError, validate_critical_fields
        from finwiz.orchestrators.deep_analysis_data_collector import DeepAnalysisDataCollector

        start_date, end_date = date_range
        data = _ohlcv(1)
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
        assert result["performance_metrics"] is None
        assert result["technical_analysis"] is not None

        risk_metrics = result["quantitative_recommendation"]["risk_metrics"]
        assert "volatility" not in risk_metrics, f"fabricated volatility leaked into risk_metrics: {risk_metrics}"
        assert "max_drawdown" not in risk_metrics, f"fabricated max_drawdown leaked into risk_metrics: {risk_metrics}"

        # Downstream: the real flattener the scorer's data collector uses.
        collector = DeepAnalysisDataCollector(state=mocker.MagicMock())
        collected = {
            "ticker": "TEST",
            "asset_class": "stock",
            "ticker_info": {"beta": 1.0},  # short-circuits the network-hitting beta fallback
            "quantitative_analysis": result,
        }
        flattened = collector.flatten_collected_data(collected)
        assert "volatility" not in flattened, f"fabricated volatility reached the scorer's flat dict: {flattened.get('volatility')}"

        # The gate: refuses by name, not silently passes a fabricated zero.
        with pytest.raises(CriticalFieldError) as exc_info:
            validate_critical_fields("TEST", "stock", flattened)
        assert "volatility (missing)" in exc_info.value.missing_fields

    def test_technical_failure_does_not_fabricate_signal_or_counts(self, mocker, input_data, date_range, performance_analyzer):
        """When technical analysis fails, technical_signal must not present
        the fabricated "HOLD" as if it were a computed neutral signal, and
        bullish/bearish signal counts must not be fabricated as 0 -- both
        looked like real computed values before this fix."""
        start_date, end_date = date_range
        data = _ohlcv(65)
        technical_engine = mocker.Mock()
        technical_engine.analyze_symbol.side_effect = RuntimeError("boom")
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
        assert result["technical_analysis"] is None
        recommendation = result["quantitative_recommendation"]
        assert recommendation["technical_signal"] == "N/A"
        assert "bullish_signals" not in recommendation["key_indicators"]
        assert "bearish_signals" not in recommendation["key_indicators"]
