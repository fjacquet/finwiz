"""
Unit tests for BacktestingTool.

Tests the backtesting tool functionality including multi-regime analysis,
risk-adjusted performance metrics, and validation criteria.
"""

import json
from datetime import datetime

import pandas as pd
import pytest

from finwiz.tools.backtesting_tool import (
    BacktestingInput,
    BacktestingResult,
    BacktestingTool,
    MarketRegime,
    get_backtesting_tool,
)


class TestBacktestingInput:
    """Test BacktestingInput schema validation."""

    def test_should_create_valid_input_with_defaults(self):
        """Test creating input with default values."""
        # Arrange & Act
        input_data = BacktestingInput(symbol="AAPL")

        # Assert
        assert input_data.symbol == "AAPL"
        assert input_data.strategy == "sma_crossover"
        assert input_data.backtest_period_years == 5
        assert input_data.benchmark_symbol == "SPY"
        assert input_data.initial_capital == 100000.0
        assert input_data.include_regime_analysis is True
        assert input_data.strategy_params == {}

    def test_should_create_valid_input_with_custom_values(self):
        """Test creating input with custom values."""
        # Arrange & Act
        input_data = BacktestingInput(
            symbol="TSLA",
            strategy="momentum",
            backtest_period_years=3,
            benchmark_symbol="QQQ",
            initial_capital=50000.0,
            include_regime_analysis=False,
            strategy_params={"short_period": 10, "long_period": 30},
        )

        # Assert
        assert input_data.symbol == "TSLA"
        assert input_data.strategy == "momentum"
        assert input_data.backtest_period_years == 3
        assert input_data.benchmark_symbol == "QQQ"
        assert input_data.initial_capital == 50000.0
        assert input_data.include_regime_analysis is False
        assert input_data.strategy_params == {"short_period": 10, "long_period": 30}

    def test_should_validate_backtest_period_range(self):
        """Test validation of backtest period range."""
        # Test minimum
        with pytest.raises(ValueError):
            BacktestingInput(symbol="AAPL", backtest_period_years=0)

        # Test maximum
        with pytest.raises(ValueError):
            BacktestingInput(symbol="AAPL", backtest_period_years=11)

        # Test valid range
        input_data = BacktestingInput(symbol="AAPL", backtest_period_years=1)
        assert input_data.backtest_period_years == 1

        input_data = BacktestingInput(symbol="AAPL", backtest_period_years=10)
        assert input_data.backtest_period_years == 10

    def test_should_validate_initial_capital_positive(self):
        """Test validation of positive initial capital."""
        with pytest.raises(ValueError):
            BacktestingInput(symbol="AAPL", initial_capital=0)

        with pytest.raises(ValueError):
            BacktestingInput(symbol="AAPL", initial_capital=-1000)


class TestMarketRegime:
    """Test MarketRegime model."""

    def test_should_create_valid_market_regime(self):
        """Test creating a valid market regime."""
        # Arrange
        start_date = datetime(2020, 1, 1)
        end_date = datetime(2020, 12, 31)

        # Act
        regime = MarketRegime(
            regime_type="bull",
            start_date=start_date,
            end_date=end_date,
            duration_days=365,
            market_return=15.5,
            strategy_return=18.2,
            outperformance=2.7,
            sharpe_ratio=1.25,
            max_drawdown=-8.5,
        )

        # Assert
        assert regime.regime_type == "bull"
        assert regime.start_date == start_date
        assert regime.end_date == end_date
        assert regime.duration_days == 365
        assert regime.market_return == 15.5
        assert regime.strategy_return == 18.2
        assert regime.outperformance == 2.7
        assert regime.sharpe_ratio == 1.25
        assert regime.max_drawdown == -8.5


class TestBacktestingResult:
    """Test BacktestingResult model."""

    def test_should_create_valid_backtesting_result(self):
        """Test creating a valid backtesting result."""
        # Arrange
        start_date = datetime(2019, 1, 1)
        end_date = datetime(2024, 1, 1)

        # Act
        result = BacktestingResult(
            symbol="AAPL",
            strategy_name="SimpleMovingAverageStrategy",
            backtest_period_years=5,
            total_return=85.5,
            annualized_return=13.2,
            benchmark_return=75.0,
            excess_return=10.5,
            sharpe_ratio=1.15,
            sortino_ratio=1.35,
            calmar_ratio=0.85,
            information_ratio=0.65,
            max_drawdown=-12.5,
            volatility=18.5,
            downside_deviation=12.8,
            total_trades=45,
            win_rate=0.62,
            backtest_start_date=start_date,
            backtest_end_date=end_date,
            initial_capital=100000.0,
            final_value=185500.0,
        )

        # Assert
        assert result.symbol == "AAPL"
        assert result.strategy_name == "SimpleMovingAverageStrategy"
        assert result.total_return == 85.5
        assert result.sharpe_ratio == 1.15
        assert result.validation_score == 0.0  # Default value
        assert result.validation_passed is False  # Default value


class TestBacktestingTool:
    """Test BacktestingTool functionality."""

    @pytest.fixture
    def backtesting_tool(self):
        """Create BacktestingTool instance for testing."""
        return BacktestingTool()

    @pytest.fixture
    def mock_backtest_result(self, mocker):
        """Create mock backtest result."""
        mock_result = mocker.MagicMock()
        mock_result.strategy_name = "SimpleMovingAverageStrategy"
        mock_result.total_return = 25.5
        mock_result.annualized_return = 12.8
        mock_result.benchmark_return = 18.5
        mock_result.sharpe_ratio = 1.25
        mock_result.max_drawdown = -8.5
        mock_result.volatility = 16.2
        mock_result.total_trades = 35
        mock_result.win_rate = 0.65
        mock_result.var_95 = -2.1
        mock_result.cvar_95 = -3.2
        mock_result.calmar_ratio = 1.51
        mock_result.start_date = datetime(2019, 1, 1)
        mock_result.end_date = datetime(2024, 1, 1)
        mock_result.initial_capital = 100000.0
        mock_result.final_value = 125500.0
        mock_result.portfolio_values = {
            "2019-01-01": 100000.0,
            "2019-06-01": 105000.0,
            "2020-01-01": 110000.0,
            "2020-06-01": 115000.0,
            "2021-01-01": 120000.0,
            "2021-06-01": 125000.0,
            "2022-01-01": 125500.0,
        }
        mock_result.trades = []
        return mock_result

    @pytest.fixture
    def mock_benchmark_data(self):
        """Create mock benchmark data for regime analysis."""
        dates = pd.date_range(start="2019-01-01", end="2024-01-01", freq="D")
        # Create data with different regimes
        prices = []
        base_price = 100.0

        for i, date in enumerate(dates):
            # Simulate different market regimes
            if i < len(dates) // 3:  # Bull market
                daily_return = 0.0008  # ~20% annual
            elif i < 2 * len(dates) // 3:  # Bear market
                daily_return = -0.0004  # ~-10% annual
            else:  # Sideways market
                daily_return = 0.0001  # ~2.5% annual

            base_price *= 1 + daily_return
            prices.append(base_price)

        return pd.DataFrame(
            {
                "Close": prices,
                "Open": [p * 0.999 for p in prices],
                "High": [p * 1.002 for p in prices],
                "Low": [p * 0.998 for p in prices],
                "Volume": [1000000] * len(prices),
            },
            index=dates,
        )

    def test_should_have_correct_tool_properties(self, backtesting_tool):
        """Test tool has correct name and description."""
        # Assert
        assert backtesting_tool.name == "Backtesting Tool"
        assert "comprehensive historical backtesting" in backtesting_tool.description.lower()
        assert backtesting_tool.args_schema == BacktestingInput

    def test_should_run_basic_backtest_successfully(self, mocker, backtesting_tool, mock_backtest_result):
        """Test successful basic backtesting execution."""
        # Arrange
        mock_backtesting_engine = mocker.patch("finwiz.tools.backtesting_tool.get_backtesting_engine")
        mock_data_manager = mocker.patch("finwiz.tools.backtesting_tool.get_historical_data_manager")
        mock_perf_analyzer = mocker.patch("finwiz.tools.backtesting_tool.get_performance_analyzer")

        mock_engine = mocker.MagicMock()
        mock_engine.run_strategy_backtest.return_value = mock_backtest_result
        mock_backtesting_engine.return_value = mock_engine

        mock_dm = mocker.MagicMock()
        mock_data_manager.return_value = mock_dm

        mock_pa = mocker.MagicMock()
        mock_perf_analyzer.return_value = mock_pa

        # Act
        result_json = backtesting_tool._run(symbol="AAPL", strategy="sma_crossover", backtest_period_years=5, include_regime_analysis=False)

        # Assert
        result = json.loads(result_json)
        assert result["symbol"] == "AAPL"
        assert result["strategy_name"] == "SimpleMovingAverageStrategy"
        assert result["total_return"] == 25.5
        assert result["sharpe_ratio"] == 1.25
        assert "validation_score" in result
        assert "validation_passed" in result

        # Verify engine was called correctly
        mock_engine.run_strategy_backtest.assert_called_once()
        call_args = mock_engine.run_strategy_backtest.call_args
        assert call_args.kwargs["symbol"] == "AAPL"

    def test_should_perform_regime_analysis_when_enabled(
        self,
        mocker,
        backtesting_tool,
        mock_backtest_result,
        mock_benchmark_data,
    ):
        """Test regime analysis functionality."""
        # Arrange
        mock_backtesting_engine = mocker.patch("finwiz.tools.backtesting_tool.get_backtesting_engine")
        mock_data_manager = mocker.patch("finwiz.tools.backtesting_tool.get_historical_data_manager")
        mock_perf_analyzer = mocker.patch("finwiz.tools.backtesting_tool.get_performance_analyzer")

        mock_engine = mocker.MagicMock()
        mock_engine.run_strategy_backtest.return_value = mock_backtest_result
        mock_backtesting_engine.return_value = mock_engine

        mock_dm = mocker.MagicMock()
        mock_dm.fetch_historical_data.return_value = mock_benchmark_data
        mock_data_manager.return_value = mock_dm

        mock_pa = mocker.MagicMock()
        mock_perf_analyzer.return_value = mock_pa

        # Act
        result_json = backtesting_tool._run(symbol="AAPL", strategy="sma_crossover", include_regime_analysis=True)

        # Assert
        result = json.loads(result_json)
        assert "regime_analysis" in result
        assert "regime_consistency" in result

        # Should have called fetch_historical_data for benchmark
        mock_dm.fetch_historical_data.assert_called()

    def test_should_get_correct_strategy_class(self, backtesting_tool):
        """Test strategy class mapping."""
        # Arrange & Act & Assert
        from finwiz.quantitative.backtesting import SimpleMovingAverageStrategy

        assert backtesting_tool._get_strategy_class("sma_crossover") == SimpleMovingAverageStrategy
        assert backtesting_tool._get_strategy_class("buy_and_hold") == SimpleMovingAverageStrategy
        assert backtesting_tool._get_strategy_class("momentum") == SimpleMovingAverageStrategy
        assert backtesting_tool._get_strategy_class("unknown") == SimpleMovingAverageStrategy

    def test_should_calculate_additional_metrics(self, backtesting_tool, mock_backtest_result):
        """Test calculation of additional risk-adjusted metrics."""
        # Arrange
        mock_backtest_result.portfolio_values = {
            "2019-01-01": 100000.0,
            "2019-01-02": 101000.0,
            "2019-01-03": 99500.0,
            "2019-01-04": 102000.0,
            "2019-01-05": 98000.0,
        }

        # Act
        additional_metrics = backtesting_tool._calculate_additional_metrics(mock_backtest_result)

        # Assert
        assert isinstance(additional_metrics, dict)
        # Should calculate some metrics even with limited data

    def test_should_identify_market_regimes(self, backtesting_tool, mock_benchmark_data):
        """Test market regime identification."""
        # Act
        regimes = backtesting_tool._identify_market_regimes(mock_benchmark_data)

        # Assert
        assert isinstance(regimes, list)
        assert len(regimes) > 0

        for regime in regimes:
            assert "type" in regime
            assert regime["type"] in ["bull", "bear", "sideways"]
            assert "start_date" in regime
            assert "end_date" in regime
            assert "market_return" in regime

    def test_should_validate_strategy_performance(self, backtesting_tool, mock_backtest_result):
        """Test strategy validation logic."""
        # Arrange
        additional_metrics = {"sortino_ratio": 1.5, "information_ratio": 0.8}
        regime_analysis = [
            MarketRegime(
                regime_type="bull",
                start_date=datetime(2019, 1, 1),
                end_date=datetime(2020, 1, 1),
                duration_days=365,
                market_return=20.0,
                strategy_return=25.0,
                outperformance=5.0,
                sharpe_ratio=1.3,
                max_drawdown=-5.0,
            ),
            MarketRegime(
                regime_type="bear",
                start_date=datetime(2020, 1, 1),
                end_date=datetime(2021, 1, 1),
                duration_days=365,
                market_return=-15.0,
                strategy_return=-8.0,
                outperformance=7.0,
                sharpe_ratio=0.8,
                max_drawdown=-12.0,
            ),
        ]

        # Act
        validation_score, validation_passed, validation_notes = backtesting_tool._validate_strategy(mock_backtest_result, additional_metrics, regime_analysis)

        # Assert
        assert isinstance(validation_score, float)
        assert 0.0 <= validation_score <= 1.0
        assert isinstance(validation_passed, bool)
        assert isinstance(validation_notes, list)
        assert len(validation_notes) > 0

    def test_should_handle_empty_benchmark_data_gracefully(self, backtesting_tool):
        """Test handling of empty benchmark data."""
        # Arrange
        empty_data = pd.DataFrame()

        # Act
        regimes = backtesting_tool._identify_market_regimes(empty_data)

        # Assert
        assert isinstance(regimes, list)
        assert len(regimes) == 0  # Should return empty list for invalid data

    def test_should_handle_backtesting_errors_gracefully(self, mocker, backtesting_tool):
        """Test error handling in backtesting execution."""
        # Arrange
        mock_backtesting_engine = mocker.patch("finwiz.tools.backtesting_tool.get_backtesting_engine")
        mock_engine = mocker.MagicMock()
        mock_engine.run_strategy_backtest.side_effect = Exception("Backtesting failed")
        mock_backtesting_engine.return_value = mock_engine

        # Act
        result = backtesting_tool._run(symbol="INVALID")

        # Assert
        assert "Error performing backtesting" in result

    def test_should_validate_high_performing_strategy(self, mocker, backtesting_tool):
        """Test validation of a high-performing strategy."""
        # Arrange
        high_perf_result = mocker.MagicMock()
        high_perf_result.annualized_return = 15.0  # Above 8% minimum
        high_perf_result.sharpe_ratio = 1.5  # Above 1.0 minimum
        high_perf_result.max_drawdown = -10.0  # Above -25% limit
        high_perf_result.win_rate = 0.70  # Above 45% minimum

        additional_metrics = {}
        regime_analysis = [
            MarketRegime(
                regime_type="bull",
                start_date=datetime(2019, 1, 1),
                end_date=datetime(2020, 1, 1),
                duration_days=365,
                market_return=20.0,
                strategy_return=25.0,
                outperformance=5.0,
                sharpe_ratio=1.5,
                max_drawdown=-8.0,
            ),
            MarketRegime(
                regime_type="bear",
                start_date=datetime(2020, 1, 1),
                end_date=datetime(2021, 1, 1),
                duration_days=365,
                market_return=-10.0,
                strategy_return=5.0,
                outperformance=15.0,
                sharpe_ratio=1.2,
                max_drawdown=-12.0,
            ),
        ]

        # Act
        validation_score, validation_passed, validation_notes = backtesting_tool._validate_strategy(high_perf_result, additional_metrics, regime_analysis)

        # Assert
        assert validation_score > 0.7  # Should pass validation threshold
        assert validation_passed is True
        assert any("passed" in note.lower() for note in validation_notes)

    def test_should_validate_poor_performing_strategy(self, mocker, backtesting_tool):
        """Test validation of a poor-performing strategy."""
        # Arrange
        poor_perf_result = mocker.MagicMock()
        poor_perf_result.annualized_return = 3.0  # Below 8% minimum
        poor_perf_result.sharpe_ratio = 0.5  # Below 1.0 minimum
        poor_perf_result.max_drawdown = -30.0  # Below -25% limit
        poor_perf_result.win_rate = 0.35  # Below 45% minimum

        additional_metrics = {}
        regime_analysis = []

        # Act
        validation_score, validation_passed, validation_notes = backtesting_tool._validate_strategy(poor_perf_result, additional_metrics, regime_analysis)

        # Assert
        assert validation_score < 0.7  # Should fail validation threshold
        assert validation_passed is False
        assert len(validation_notes) > 1  # Should have multiple failure notes


class TestBacktestingToolFactory:
    """Test factory function."""

    def test_should_create_backtesting_tool_instance(self):
        """Test factory function creates correct instance."""
        # Act
        tool = get_backtesting_tool()

        # Assert
        assert isinstance(tool, BacktestingTool)
        assert tool.name == "Backtesting Tool"
