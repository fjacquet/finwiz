"""Unit tests for perform_backtesting (quantitative analysis tool's backtest path)."""

import json
from datetime import datetime

import pandas as pd

from finwiz.schemas.tools import QuantitativeAnalysisInput
from finwiz.tools.quantitative_backtesting_analyzer import perform_backtesting


def _input_data() -> QuantitativeAnalysisInput:
    return QuantitativeAnalysisInput(symbol="AAPL", asset_class="stock", analysis_type="backtest")


def _price_data() -> pd.DataFrame:
    dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
    return pd.DataFrame({"Close": [100.0 + i for i in range(30)]}, index=dates)


def test_returns_named_refusal_when_series_too_short_to_backtest(mocker):
    """A short series is a refusal by name, never an internal NoneType message.

    ``run_strategy_backtest`` returns None when the fetched series is shorter
    than the strategy's lookback plus warm-up. Reading attributes off that None
    used to raise AttributeError, which the shared except turned into
    "Backtesting error: 'NoneType' object has no attribute 'strategy_name'" --
    an internal detail handed to an agent in place of the reason.
    """
    engine = mocker.MagicMock()
    engine.run_strategy_backtest.return_value = None

    result = perform_backtesting(_price_data(), _input_data(), datetime(2024, 1, 1), datetime(2024, 1, 30), engine)

    assert "NoneType" not in result
    assert "AAPL" in result
    assert "Insufficient data" in result
    # The bar count the strategy needs: long_period 50 + 10-bar warm-up buffer.
    assert "60" in result


def test_returns_backtest_json_when_engine_produces_a_result(mocker):
    """The success path still serialises the engine result unchanged."""
    engine = mocker.MagicMock()
    backtest = engine.run_strategy_backtest.return_value
    backtest.strategy_name = "SimpleMovingAverageStrategy"
    backtest.total_return = 25.5
    backtest.annualized_return = 12.8
    backtest.sharpe_ratio = 1.25
    backtest.max_drawdown = -8.5
    backtest.total_trades = 35
    backtest.win_rate = 0.65
    backtest.volatility = 16.2
    backtest.var_95 = -2.1
    backtest.start_date = datetime(2024, 1, 1)
    backtest.end_date = datetime(2024, 1, 30)
    backtest.initial_capital = 100000.0
    backtest.final_value = 125500.0

    result = json.loads(perform_backtesting(_price_data(), _input_data(), datetime(2024, 1, 1), datetime(2024, 1, 30), engine))

    assert result["symbol"] == "AAPL"
    assert result["strategy_name"] == "SimpleMovingAverageStrategy"
    assert result["total_return"] == 25.5


def test_reports_engine_failures_as_errors(mocker):
    """A raise is still an error -- only the short-series case is a refusal."""
    engine = mocker.MagicMock()
    engine.run_strategy_backtest.side_effect = RuntimeError("cerebro exploded")

    result = perform_backtesting(_price_data(), _input_data(), datetime(2024, 1, 1), datetime(2024, 1, 30), engine)

    assert "Backtesting error" in result
    assert "cerebro exploded" in result
