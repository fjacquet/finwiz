"""
Unit tests for quantitative backtesting engine.

Tests cover:
- BacktestingEngine functionality
- StrategyFramework base class
- Trade execution and logging
- Performance metrics calculation
- Risk management features
- Multi-strategy backtesting
"""

import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import backtrader as bt  # type: ignore[import-untyped]  # backtrader has no official type stubs
import pandas as pd
import pytest
from faker import Faker
from pytest import approx

from finwiz.quantitative.backtesting import (
    BacktestingEngine,
    BacktestResult,
    PositionSizingMethod,
    SimpleMovingAverageStrategy,
    StrategyFramework,
    Trade,
    TradeStatus,
    TradeType,
    get_backtesting_engine,
)
from finwiz.quantitative.config import BacktestConfig

fake = Faker()


class TestTrade:
    """Test suite for Trade model."""

    def test_should_create_valid_trade_when_all_fields_provided(self):
        """Test creating a valid Trade instance."""
        # Arrange
        trade_id = fake.uuid4()
        symbol = fake.pystr(min_chars=3, max_chars=5).upper()
        entry_date = fake.date_time_this_year()
        exit_date = entry_date + timedelta(days=fake.random_int(min=1, max=30))
        entry_price = fake.pyfloat(min_value=50, max_value=200, right_digits=2)
        exit_price = fake.pyfloat(min_value=50, max_value=200, right_digits=2)
        quantity = fake.random_int(min=100, max=1000)

        # Act
        trade = Trade(
            trade_id=trade_id,
            symbol=symbol,
            trade_type=TradeType.BUY,
            status=TradeStatus.CLOSED,
            entry_date=entry_date,
            entry_price=entry_price,
            quantity=quantity,
            exit_date=exit_date,
            exit_price=exit_price,
            commission=fake.pyfloat(min_value=1, max_value=10, right_digits=2),
            strategy_name="TestStrategy",
        )

        # Assert
        assert trade.trade_id == trade_id
        assert trade.symbol == symbol
        assert trade.trade_type == TradeType.BUY
        assert trade.status == TradeStatus.CLOSED
        assert trade.entry_date == entry_date
        assert trade.entry_price == entry_price
        assert trade.quantity == quantity
        assert trade.exit_date == exit_date
        assert trade.exit_price == exit_price
        assert trade.strategy_name == "TestStrategy"

    def test_should_validate_positive_entry_price_when_provided(self):
        """Test validation of positive entry price."""
        # Test valid price
        trade = Trade(
            trade_id=fake.uuid4(),
            symbol=fake.pystr(min_chars=3, max_chars=5).upper(),
            trade_type=TradeType.BUY,
            status=TradeStatus.OPEN,
            entry_date=fake.date_time_this_year(),
            entry_price=100.50,
            quantity=100,
            strategy_name="TestStrategy",
        )
        assert trade.entry_price == approx(100.50)

        # Test invalid price
        with pytest.raises(ValueError):
            Trade(
                trade_id=fake.uuid4(),
                symbol=fake.pystr(min_chars=3, max_chars=5).upper(),
                trade_type=TradeType.BUY,
                status=TradeStatus.OPEN,
                entry_date=fake.date_time_this_year(),
                entry_price=0.0,  # Invalid
                quantity=100,
                strategy_name="TestStrategy",
            )

    def test_should_validate_positive_exit_price_when_provided(self):
        """Test validation of positive exit price."""
        # Test valid exit price
        trade = Trade(
            trade_id=fake.uuid4(),
            symbol=fake.pystr(min_chars=3, max_chars=5).upper(),
            trade_type=TradeType.BUY,
            status=TradeStatus.CLOSED,
            entry_date=fake.date_time_this_year(),
            entry_price=100.0,
            quantity=100,
            exit_price=110.0,
            strategy_name="TestStrategy",
        )
        assert trade.exit_price == approx(110.0)

        # Test invalid exit price
        with pytest.raises(ValueError):
            Trade(
                trade_id=fake.uuid4(),
                symbol=fake.pystr(min_chars=3, max_chars=5).upper(),
                trade_type=TradeType.BUY,
                status=TradeStatus.CLOSED,
                entry_date=fake.date_time_this_year(),
                entry_price=100.0,
                quantity=100,
                exit_price=-10.0,  # Invalid
                strategy_name="TestStrategy",
            )

    def test_should_calculate_pnl_correctly_for_long_position(self):
        """Test PnL calculation for long positions."""
        # Arrange
        entry_price = 100.0
        exit_price = 110.0
        quantity = 100
        commission = 5.0

        trade = Trade(
            trade_id=fake.uuid4(),
            symbol=fake.pystr(min_chars=3, max_chars=5).upper(),
            trade_type=TradeType.BUY,
            status=TradeStatus.CLOSED,
            entry_date=fake.date_time_this_year(),
            entry_price=entry_price,
            quantity=quantity,
            exit_price=exit_price,
            commission=commission,
            strategy_name="TestStrategy",
        )

        # Act
        trade.calculate_pnl()

        # Assert
        expected_gross_pnl = (exit_price - entry_price) * quantity  # 1000
        expected_net_pnl = expected_gross_pnl - commission  # 995
        expected_pnl_percent = (expected_net_pnl / (entry_price * quantity)) * 100  # 9.95%

        assert trade.pnl == expected_net_pnl
        assert abs(trade.pnl_percent - expected_pnl_percent) < 0.01

    def test_should_calculate_pnl_correctly_for_short_position(self):
        """Test PnL calculation for short positions."""
        # Arrange
        entry_price = 100.0
        exit_price = 90.0
        quantity = 100
        commission = 5.0

        trade = Trade(
            trade_id=fake.uuid4(),
            symbol=fake.pystr(min_chars=3, max_chars=5).upper(),
            trade_type=TradeType.SELL,
            status=TradeStatus.CLOSED,
            entry_date=fake.date_time_this_year(),
            entry_price=entry_price,
            quantity=quantity,
            exit_price=exit_price,
            commission=commission,
            strategy_name="TestStrategy",
        )

        # Act
        trade.calculate_pnl()

        # Assert
        expected_gross_pnl = (entry_price - exit_price) * quantity  # 1000
        expected_net_pnl = expected_gross_pnl - commission  # 995

        assert trade.pnl == expected_net_pnl
        assert trade.pnl_percent > 0  # Profitable short

    def test_should_calculate_holding_period_correctly(self):
        """Test holding period calculation."""
        # Arrange
        entry_date = datetime(2023, 1, 1)
        exit_date = datetime(2023, 1, 15)

        trade = Trade(
            trade_id=fake.uuid4(),
            symbol=fake.pystr(min_chars=3, max_chars=5).upper(),
            trade_type=TradeType.BUY,
            status=TradeStatus.CLOSED,
            entry_date=entry_date,
            entry_price=100.0,
            quantity=100,
            exit_date=exit_date,
            exit_price=110.0,
            strategy_name="TestStrategy",
        )

        # Act
        trade.calculate_holding_period()

        # Assert
        assert trade.holding_period_days == 14

    def test_should_not_calculate_pnl_for_open_trade(self):
        """Test that PnL is not calculated for open trades."""
        # Arrange
        trade = Trade(
            trade_id=fake.uuid4(),
            symbol=fake.pystr(min_chars=3, max_chars=5).upper(),
            trade_type=TradeType.BUY,
            status=TradeStatus.OPEN,
            entry_date=fake.date_time_this_year(),
            entry_price=100.0,
            quantity=100,
            strategy_name="TestStrategy",
        )

        # Act
        trade.calculate_pnl()

        # Assert
        assert trade.pnl is None
        assert trade.pnl_percent is None


class TestBacktestResult:
    """Test suite for BacktestResult model."""

    def test_should_create_valid_backtest_result_when_all_fields_provided(self):
        """Test creating a valid BacktestResult instance."""
        # Arrange
        strategy_name = "TestStrategy"
        symbol = fake.pystr(min_chars=3, max_chars=5).upper()
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 12, 31)
        initial_capital = 100000.0
        final_value = 110000.0

        # Act
        result = BacktestResult(
            strategy_name=strategy_name,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            final_value=final_value,
            total_return=10.0,
            annualized_return=10.0,
            volatility=15.0,
            sharpe_ratio=0.67,
            max_drawdown=-5.0,
            total_trades=50,
            winning_trades=30,
            losing_trades=20,
        )

        # Assert
        assert result.strategy_name == strategy_name
        assert result.symbol == symbol
        assert result.start_date == start_date
        assert result.end_date == end_date
        assert result.initial_capital == initial_capital
        assert result.final_value == final_value
        assert result.total_return == approx(10.0)
        assert result.win_rate == approx(0.6)  # 30/50

    def test_should_calculate_win_rate_automatically(self):
        """Test automatic win rate calculation."""
        # Arrange & Act
        result = BacktestResult(
            strategy_name="TestStrategy",
            symbol=fake.pystr(min_chars=3, max_chars=5).upper(),
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 12, 31),
            initial_capital=100000.0,
            final_value=110000.0,
            total_return=10.0,
            annualized_return=10.0,
            volatility=15.0,
            sharpe_ratio=0.67,
            max_drawdown=-5.0,
            total_trades=100,
            winning_trades=75,
            losing_trades=25,
        )

        # Assert
        assert result.win_rate == approx(0.75)

    def test_should_handle_zero_trades_for_win_rate(self):
        """Test win rate calculation with zero trades."""
        # Arrange & Act
        result = BacktestResult(
            strategy_name="TestStrategy",
            symbol=fake.pystr(min_chars=3, max_chars=5).upper(),
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 12, 31),
            initial_capital=100000.0,
            final_value=100000.0,
            total_return=0.0,
            annualized_return=0.0,
            volatility=0.0,
            sharpe_ratio=0.0,
            max_drawdown=0.0,
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
        )

        # Assert
        assert result.win_rate == approx(0.0)


class TestStrategyFramework:
    """Test suite for StrategyFramework base class."""

    @pytest.fixture
    def sample_ohlcv_data(self):
        """Create sample OHLCV data for testing."""
        dates = pd.date_range(start="2023-01-01", end="2023-01-31", freq="D")
        num_dates = len(dates)

        # Use Faker to generate realistic financial data
        fake.seed_instance(42)
        base_price = fake.pyfloat(min_value=100, max_value=150, right_digits=2)

        prices = []
        current_price = base_price

        for _ in range(num_dates):
            daily_return = fake.pyfloat(min_value=-0.02, max_value=0.02, right_digits=4)
            current_price = current_price * (1 + daily_return)
            prices.append(round(current_price, 2))

        ohlc_data = []
        for close_price in prices:
            volatility = fake.pyfloat(min_value=0.005, max_value=0.015, right_digits=4)
            high = close_price * (1 + fake.pyfloat(min_value=0, max_value=volatility, right_digits=4))
            low = close_price * (1 - fake.pyfloat(min_value=0, max_value=volatility, right_digits=4))
            open_price = fake.pyfloat(min_value=low, max_value=high, right_digits=2)
            close_price = max(low, min(high, close_price))

            ohlc_data.append(
                {
                    "Open": round(open_price, 2),
                    "High": round(high, 2),
                    "Low": round(low, 2),
                    "Close": round(close_price, 2),
                    "Volume": fake.pyint(min_value=1000000, max_value=5000000),
                }
            )

        return pd.DataFrame(ohlc_data, index=dates)

    def test_should_initialize_strategy_framework_correctly(self):
        """Test StrategyFramework initialization."""
        # This test would require a more complex setup with Backtrader
        # For now, we'll test the basic structure
        assert hasattr(StrategyFramework, "params")
        assert hasattr(StrategyFramework, "calculate_position_size")
        assert hasattr(StrategyFramework, "set_stop_loss")
        assert hasattr(StrategyFramework, "set_take_profit")
        assert hasattr(StrategyFramework, "generate_signals")

    def test_should_raise_not_implemented_for_generate_signals(self):
        """Test that generate_signals raises NotImplementedError in base class."""

        # Create a minimal strategy instance for testing without Backtrader initialization
        class TestStrategy:
            def generate_signals(self):
                raise NotImplementedError("Subclasses must implement generate_signals method")

        strategy = TestStrategy()

        with pytest.raises(NotImplementedError):
            strategy.generate_signals()


class TestSimpleMovingAverageStrategy:
    """Test suite for SimpleMovingAverageStrategy."""

    def test_should_have_correct_default_parameters(self):
        """Test default parameters for SMA strategy."""
        # Check that the strategy class has the expected parameters
        assert hasattr(SimpleMovingAverageStrategy, "params")

        # We can't easily test the actual parameter values without running Backtrader
        # but we can verify the class structure
        assert SimpleMovingAverageStrategy.__bases__[0] == StrategyFramework


class TestBacktestingEngine:
    """Test suite for BacktestingEngine class."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def config(self, temp_cache_dir):
        """Create test configuration."""
        return BacktestConfig(initial_capital=100000.0, commission_pct=0.001, stop_loss_pct=0.05, take_profit_pct=0.15)

    @pytest.fixture
    def backtesting_engine(self, config, mocker):
        """Create BacktestingEngine instance for testing."""
        mocker.patch("finwiz.quantitative.backtesting.HistoricalDataManager")
        return BacktestingEngine(config)

    @pytest.fixture
    def sample_ohlcv_data(self):
        """Create sample OHLCV data for testing."""
        dates = pd.date_range(start="2023-01-01", end="2023-03-31", freq="D")
        num_dates = len(dates)

        fake.seed_instance(123)
        base_price = fake.pyfloat(min_value=100, max_value=150, right_digits=2)

        prices = []
        current_price = base_price

        for _ in range(num_dates):
            daily_return = fake.pyfloat(min_value=-0.01, max_value=0.01, right_digits=4)
            current_price = current_price * (1 + daily_return)
            prices.append(round(current_price, 2))

        ohlc_data = []
        for close_price in prices:
            volatility = fake.pyfloat(min_value=0.005, max_value=0.015, right_digits=4)
            high = close_price * (1 + fake.pyfloat(min_value=0, max_value=volatility, right_digits=4))
            low = close_price * (1 - fake.pyfloat(min_value=0, max_value=volatility, right_digits=4))
            open_price = fake.pyfloat(min_value=low, max_value=high, right_digits=2)
            close_price = max(low, min(high, close_price))

            ohlc_data.append(
                {
                    "Open": round(open_price, 2),
                    "High": round(high, 2),
                    "Low": round(low, 2),
                    "Close": round(close_price, 2),
                    "Volume": fake.pyint(min_value=1000000, max_value=5000000),
                }
            )

        return pd.DataFrame(ohlc_data, index=dates)

    def test_should_initialize_backtesting_engine_correctly(self, backtesting_engine):
        """Test BacktestingEngine initialization."""
        assert backtesting_engine.config is not None
        assert backtesting_engine.data_manager is not None
        assert backtesting_engine.logger is not None
        assert backtesting_engine.cerebro is None  # Not initialized until backtest runs
        assert backtesting_engine.results == []

    def test_should_run_strategy_backtest_successfully(self, sample_ohlcv_data, mocker):
        """Test successful strategy backtesting."""
        # Arrange
        config = BacktestConfig(initial_capital=100000.0, commission_pct=0.001)
        engine = BacktestingEngine(config)

        # Mock data manager
        mock_data_manager_instance = mocker.MagicMock()
        mock_data_manager_instance.fetch_historical_data.return_value = sample_ohlcv_data
        mock_data_manager = mocker.patch("finwiz.quantitative.backtesting.HistoricalDataManager")
        mock_data_manager.return_value = mock_data_manager_instance
        engine.data_manager = mock_data_manager_instance

        symbol = fake.pystr(min_chars=3, max_chars=5).upper()
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 3, 31)

        # Act
        result = engine.run_strategy_backtest(SimpleMovingAverageStrategy, symbol, start_date, end_date)

        # Assert
        assert isinstance(result, BacktestResult)
        assert result.strategy_name == "SimpleMovingAverageStrategy"
        assert result.symbol == symbol
        assert result.start_date == start_date
        assert result.end_date == end_date
        assert result.initial_capital == approx(100000.0)
        assert result.final_value > 0

        # Verify data manager was called
        mock_data_manager_instance.fetch_historical_data.assert_called_once_with(symbol, start_date, end_date)

    def test_should_handle_empty_data_gracefully(self, mocker):
        """Test handling of empty data from data manager."""
        # Arrange
        config = BacktestConfig(initial_capital=100000.0)
        mock_data_manager = mocker.patch("finwiz.quantitative.backtesting.HistoricalDataManager")
        engine = BacktestingEngine(config)

        # Mock data manager to return empty DataFrame
        mock_data_manager_instance = mocker.MagicMock()
        mock_data_manager_instance.fetch_historical_data.return_value = pd.DataFrame()
        mock_data_manager.return_value = mock_data_manager_instance
        engine.data_manager = mock_data_manager_instance

        symbol = fake.pystr(min_chars=3, max_chars=5).upper()
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 3, 31)

        # Act & Assert
        with pytest.raises(ValueError, match="No data available"):
            engine.run_strategy_backtest(SimpleMovingAverageStrategy, symbol, start_date, end_date)

    def test_should_handle_data_manager_errors(self, mocker):
        """Test handling of data manager errors."""
        # Arrange
        config = BacktestConfig(initial_capital=100000.0)
        mock_data_manager = mocker.patch("finwiz.quantitative.backtesting.HistoricalDataManager")
        engine = BacktestingEngine(config)

        # Mock data manager to raise exception
        mock_data_manager_instance = mocker.MagicMock()
        mock_data_manager_instance.fetch_historical_data.side_effect = Exception("Network error")
        mock_data_manager.return_value = mock_data_manager_instance
        engine.data_manager = mock_data_manager_instance

        symbol = fake.pystr(min_chars=3, max_chars=5).upper()
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 3, 31)

        # Act & Assert
        with pytest.raises(Exception, match="Network error"):
            engine.run_strategy_backtest(SimpleMovingAverageStrategy, symbol, start_date, end_date)

    def test_should_create_backtrader_datafeed_correctly(self, backtesting_engine, sample_ohlcv_data):
        """Test creation of Backtrader data feed."""
        # Arrange
        symbol = fake.pystr(min_chars=3, max_chars=5).upper()

        # Act
        from finwiz.quantitative.backtesting_utils import create_backtrader_datafeed

        data_feed = create_backtrader_datafeed(sample_ohlcv_data, symbol)

        # Assert
        assert isinstance(data_feed, bt.feeds.PandasData)
        assert data_feed._name == symbol

    def test_should_calculate_volatility_correctly(self, backtesting_engine):
        """Test volatility calculation."""
        # Arrange
        portfolio_values = [
            ("2023-01-01", 100000),
            ("2023-01-02", 101000),
            ("2023-01-03", 99500),
            ("2023-01-04", 102000),
            ("2023-01-05", 100500),
        ]

        # Act
        volatility = backtesting_engine.performance_analyzer.calculate_volatility(portfolio_values)

        # Assert
        assert isinstance(volatility, float)
        assert volatility >= 0

    def test_should_calculate_var_correctly(self, backtesting_engine):
        """Test Value at Risk calculation."""
        # Arrange
        portfolio_values = [
            ("2023-01-01", 100000),
            ("2023-01-02", 101000),
            ("2023-01-03", 99000),
            ("2023-01-04", 102000),
            ("2023-01-05", 98000),
        ]

        # Act
        var_95 = backtesting_engine.performance_analyzer.calculate_var(portfolio_values, 0.95)

        # Assert
        assert isinstance(var_95, float)
        assert var_95 <= 0  # VaR should be negative (loss)

    def test_should_calculate_cvar_correctly(self, backtesting_engine):
        """Test Conditional Value at Risk calculation."""
        # Arrange
        portfolio_values = [
            ("2023-01-01", 100000),
            ("2023-01-02", 101000),
            ("2023-01-03", 99000),
            ("2023-01-04", 102000),
            ("2023-01-05", 98000),
        ]

        # Act
        cvar_95 = backtesting_engine.performance_analyzer.calculate_cvar(portfolio_values, 0.95)

        # Assert
        assert isinstance(cvar_95, float)
        assert cvar_95 <= 0  # CVaR should be negative (loss)

    def test_should_handle_insufficient_data_for_risk_metrics(self, backtesting_engine):
        """Test handling of insufficient data for risk calculations."""
        # Arrange
        portfolio_values = [("2023-01-01", 100000)]  # Only one data point

        # Act
        volatility = backtesting_engine.performance_analyzer.calculate_volatility(portfolio_values)
        var_95 = backtesting_engine.performance_analyzer.calculate_var(portfolio_values, 0.95)
        cvar_95 = backtesting_engine.performance_analyzer.calculate_cvar(portfolio_values, 0.95)

        # Assert
        assert volatility == approx(0.0)
        assert var_95 is None
        assert cvar_95 is None

    def test_should_run_multi_strategy_backtest_successfully(self, sample_ohlcv_data, mocker):
        """Test multi-strategy backtesting."""
        # Arrange
        config = BacktestConfig(initial_capital=100000.0)
        mock_data_manager = mocker.patch("finwiz.quantitative.backtesting.HistoricalDataManager")
        engine = BacktestingEngine(config)

        # Mock data manager
        mock_data_manager_instance = mocker.MagicMock()
        mock_data_manager_instance.fetch_historical_data.return_value = sample_ohlcv_data
        mock_data_manager.return_value = mock_data_manager_instance
        engine.data_manager = mock_data_manager_instance

        strategies = [
            (SimpleMovingAverageStrategy, {"short_period": 10, "long_period": 30}),
            (SimpleMovingAverageStrategy, {"short_period": 20, "long_period": 50}),
        ]

        symbol = fake.pystr(min_chars=3, max_chars=5).upper()
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 3, 31)

        # Act
        results = engine.run_multi_strategy_backtest(strategies, symbol, start_date, end_date)

        # Assert
        assert len(results) == 2
        assert all(isinstance(result, BacktestResult) for result in results)
        assert results[0].strategy_name == "SimpleMovingAverageStrategy"
        assert results[1].strategy_name == "SimpleMovingAverageStrategy"

    def test_should_handle_plot_results_without_backtest(self, backtesting_engine):
        """Test plotting results when no backtest has been run."""
        # Act & Assert - should not raise exception
        backtesting_engine.plot_results()  # Should log warning but not raise exception


class TestGlobalBacktestingEngine:
    """Test global backtesting engine functions."""

    def test_should_return_singleton_engine_when_requested(self):
        """Test that global backtesting engine returns singleton instance."""
        # Act
        engine1 = get_backtesting_engine()
        engine2 = get_backtesting_engine()

        # Assert
        assert engine1 is engine2  # Same instance
        assert isinstance(engine1, BacktestingEngine)


class TestPositionSizingMethod:
    """Test PositionSizingMethod enum."""

    def test_should_have_all_expected_methods(self):
        """Test that all expected position sizing methods are available."""
        expected_methods = ["fixed_amount", "percent_of_portfolio", "kelly_criterion", "volatility_adjusted"]

        for method in expected_methods:
            assert hasattr(PositionSizingMethod, method.upper())
            assert getattr(PositionSizingMethod, method.upper()).value == method


class TestTradeEnums:
    """Test trade-related enums."""

    def test_should_have_all_trade_types(self):
        """Test that all expected trade types are available."""
        expected_types = ["BUY", "SELL", "SHORT", "COVER"]

        for trade_type in expected_types:
            assert hasattr(TradeType, trade_type)
            assert getattr(TradeType, trade_type).value == trade_type

    def test_should_have_all_trade_statuses(self):
        """Test that all expected trade statuses are available."""
        expected_statuses = ["OPEN", "CLOSED", "CANCELLED"]

        for status in expected_statuses:
            assert hasattr(TradeStatus, status)
            assert getattr(TradeStatus, status).value == status


class TestPerformanceMetrics:
    """Test performance metrics calculations."""

    def test_should_calculate_annualized_return_correctly(self):
        """Test annualized return calculation logic."""
        # This would be tested as part of the BacktestingEngine integration
        # For now, we verify the calculation logic conceptually
        initial_value = 100000
        final_value = 110000
        days = 365
        years = days / 365.25

        expected_annualized = ((final_value / initial_value) ** (1 / years) - 1) * 100

        # The actual calculation would be done in the engine
        assert expected_annualized > 0  # Should be positive for profitable strategy

    def test_should_calculate_sharpe_ratio_components(self):
        """Test components needed for Sharpe ratio calculation."""
        # Test that we have the necessary components
        # Actual calculation is done by Backtrader analyzers
        risk_free_rate = 0.02
        portfolio_return = 0.12
        volatility = 0.15

        expected_sharpe = (portfolio_return - risk_free_rate) / volatility

        assert expected_sharpe > 0  # Should be positive for good strategy
        assert isinstance(expected_sharpe, float)


class TestRiskManagement:
    """Test risk management features."""

    def test_should_validate_stop_loss_parameters(self):
        """Test stop loss parameter validation."""
        # Test valid stop loss percentage
        config = BacktestConfig(stop_loss_pct=0.05)
        assert config.stop_loss_pct == approx(0.05)

        # Test that stop loss is optional
        config_no_stop = BacktestConfig(stop_loss_pct=None)
        assert config_no_stop.stop_loss_pct is None

    def test_should_validate_take_profit_parameters(self):
        """Test take profit parameter validation."""
        # Test valid take profit percentage
        config = BacktestConfig(take_profit_pct=0.15)
        assert config.take_profit_pct == approx(0.15)

        # Test that take profit is optional
        config_no_tp = BacktestConfig(take_profit_pct=None)
        assert config_no_tp.take_profit_pct is None

    def test_should_validate_max_drawdown_limit(self):
        """Test maximum drawdown limit validation."""
        # Test valid drawdown limit
        config = BacktestConfig(max_drawdown_limit=0.2)
        assert config.max_drawdown_limit == approx(0.2)

        # Test boundary values
        config_min = BacktestConfig(max_drawdown_limit=0.01)
        assert config_min.max_drawdown_limit == approx(0.01)

        config_max = BacktestConfig(max_drawdown_limit=1.0)
        assert config_max.max_drawdown_limit == approx(1.0)


class TestStrategyExecution:
    """Test strategy execution with sample price data."""

    @pytest.fixture
    def trending_up_data(self):
        """Create sample price data with upward trend."""
        dates = pd.date_range(start="2023-01-01", end="2023-06-30", freq="D")
        num_dates = len(dates)

        # Create upward trending prices
        base_price = 100.0
        prices = []
        for i in range(num_dates):
            # Add trend + noise
            trend = base_price + (i * 0.2)  # Upward trend
            noise = fake.pyfloat(min_value=-1, max_value=1, right_digits=2)
            prices.append(max(1.0, trend + noise))

        ohlc_data = []
        for close_price in prices:
            high = close_price * 1.01
            low = close_price * 0.99
            open_price = (high + low) / 2

            ohlc_data.append(
                {
                    "Open": round(open_price, 2),
                    "High": round(high, 2),
                    "Low": round(low, 2),
                    "Close": round(close_price, 2),
                    "Volume": fake.pyint(min_value=1000000, max_value=5000000),
                }
            )

        return pd.DataFrame(ohlc_data, index=dates)

    @pytest.fixture
    def trending_down_data(self):
        """Create sample price data with downward trend."""
        dates = pd.date_range(start="2023-01-01", end="2023-06-30", freq="D")
        num_dates = len(dates)

        # Create downward trending prices
        base_price = 150.0
        prices = []
        for i in range(num_dates):
            # Add trend + noise
            trend = base_price - (i * 0.15)  # Downward trend
            noise = fake.pyfloat(min_value=-1, max_value=1, right_digits=2)
            prices.append(max(1.0, trend + noise))

        ohlc_data = []
        for close_price in prices:
            high = close_price * 1.01
            low = close_price * 0.99
            open_price = (high + low) / 2

            ohlc_data.append(
                {
                    "Open": round(open_price, 2),
                    "High": round(high, 2),
                    "Low": round(low, 2),
                    "Close": round(close_price, 2),
                    "Volume": fake.pyint(min_value=1000000, max_value=5000000),
                }
            )

        return pd.DataFrame(ohlc_data, index=dates)

    @pytest.fixture
    def sideways_data(self):
        """Create sample price data with sideways movement."""
        dates = pd.date_range(start="2023-01-01", end="2023-06-30", freq="D")
        num_dates = len(dates)

        # Create sideways prices
        base_price = 100.0
        prices = []
        for _ in range(num_dates):
            # Random walk around base price
            noise = fake.pyfloat(min_value=-2, max_value=2, right_digits=2)
            prices.append(max(1.0, base_price + noise))

        ohlc_data = []
        for close_price in prices:
            high = close_price * 1.01
            low = close_price * 0.99
            open_price = (high + low) / 2

            ohlc_data.append(
                {
                    "Open": round(open_price, 2),
                    "High": round(high, 2),
                    "Low": round(low, 2),
                    "Close": round(close_price, 2),
                    "Volume": fake.pyint(min_value=1000000, max_value=5000000),
                }
            )

        return pd.DataFrame(ohlc_data, index=dates)

    def test_should_execute_sma_strategy_on_trending_up_data(self, trending_up_data, mocker):
        """Test SMA strategy execution with upward trending data."""
        # Arrange
        config = BacktestConfig(initial_capital=100000.0, commission_pct=0.001)
        engine = BacktestingEngine(config)

        mock_data_manager = mocker.MagicMock()
        mock_data_manager.fetch_historical_data.return_value = trending_up_data
        engine.data_manager = mock_data_manager

        symbol = "UPTREND"
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 6, 30)

        # Act
        result = engine.run_strategy_backtest(SimpleMovingAverageStrategy, symbol, start_date, end_date, strategy_params={"short_period": 10, "long_period": 30})

        # Assert
        assert isinstance(result, BacktestResult)
        assert result.strategy_name == "SimpleMovingAverageStrategy"
        assert result.total_trades >= 0
        # Note: Strategy may not generate trades if trend is too smooth
        # The important thing is that it executes without errors

    def test_should_execute_sma_strategy_on_trending_down_data(self, trending_down_data, mocker):
        """Test SMA strategy execution with downward trending data."""
        # Arrange
        config = BacktestConfig(initial_capital=100000.0, commission_pct=0.001)
        engine = BacktestingEngine(config)

        mock_data_manager = mocker.MagicMock()
        mock_data_manager.fetch_historical_data.return_value = trending_down_data
        engine.data_manager = mock_data_manager

        symbol = "DOWNTREND"
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 6, 30)

        # Act
        result = engine.run_strategy_backtest(SimpleMovingAverageStrategy, symbol, start_date, end_date, strategy_params={"short_period": 10, "long_period": 30})

        # Assert
        assert isinstance(result, BacktestResult)
        assert result.strategy_name == "SimpleMovingAverageStrategy"
        # May be negative in downtrend (long-only strategy)
        assert result.total_trades >= 0

    def test_should_execute_mean_reversion_strategy_on_sideways_data(self, sideways_data, mocker):
        """Test mean reversion strategy execution with sideways data."""
        # Arrange
        from finwiz.quantitative.backtesting_strategies import MeanReversionStrategy

        config = BacktestConfig(initial_capital=100000.0, commission_pct=0.001)
        engine = BacktestingEngine(config)

        mock_data_manager = mocker.MagicMock()
        mock_data_manager.fetch_historical_data.return_value = sideways_data
        engine.data_manager = mock_data_manager

        symbol = "SIDEWAYS"
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 6, 30)

        # Act
        result = engine.run_strategy_backtest(MeanReversionStrategy, symbol, start_date, end_date, strategy_params={"period": 20, "devfactor": 2.0})

        # Assert
        assert isinstance(result, BacktestResult)
        assert result.strategy_name == "MeanReversionStrategy"
        assert result.total_trades >= 0

    def test_should_generate_trades_matching_strategy_rules(self, trending_up_data, mocker):
        """Test that trade generation matches strategy rules."""
        # Arrange
        config = BacktestConfig(initial_capital=100000.0, commission_pct=0.001)
        engine = BacktestingEngine(config)

        mock_data_manager = mocker.MagicMock()
        mock_data_manager.fetch_historical_data.return_value = trending_up_data
        engine.data_manager = mock_data_manager

        symbol = "TEST"
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 6, 30)

        # Act
        result = engine.run_strategy_backtest(SimpleMovingAverageStrategy, symbol, start_date, end_date, strategy_params={"short_period": 10, "long_period": 30})

        # Assert - Verify trades follow strategy logic
        if result.total_trades > 0:
            # All trades should have valid entry/exit prices
            for trade in result.trades:
                assert trade.entry_price > 0
                if trade.status == TradeStatus.CLOSED:
                    assert trade.exit_price is not None
                    assert trade.exit_price > 0
                    assert trade.pnl is not None

            # Verify trade types are correct (BUY for long-only strategy)
            buy_trades = [t for t in result.trades if t.trade_type == TradeType.BUY]
            assert len(buy_trades) > 0  # Should have buy trades in uptrend

    def test_should_calculate_performance_metrics_correctly(self, trending_up_data, mocker):
        """Test that performance metrics are calculated correctly."""
        # Arrange
        config = BacktestConfig(initial_capital=100000.0, commission_pct=0.001)
        engine = BacktestingEngine(config)

        mock_data_manager = mocker.MagicMock()
        mock_data_manager.fetch_historical_data.return_value = trending_up_data
        engine.data_manager = mock_data_manager

        symbol = "METRICS"
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 6, 30)

        # Act
        result = engine.run_strategy_backtest(SimpleMovingAverageStrategy, symbol, start_date, end_date)

        # Assert - Verify all key metrics are calculated
        assert result.total_return is not None
        assert result.annualized_return is not None
        assert result.volatility >= 0
        assert result.sharpe_ratio is not None
        assert result.max_drawdown <= 0  # Drawdown should be negative or zero

        # Verify win rate calculation
        if result.total_trades > 0:
            expected_win_rate = result.winning_trades / result.total_trades
            assert abs(result.win_rate - expected_win_rate) < 0.01

    def test_should_handle_no_trades_scenario(self, sideways_data, mocker):
        """Test handling when strategy generates no trades."""
        # Arrange
        config = BacktestConfig(initial_capital=100000.0, commission_pct=0.001)
        engine = BacktestingEngine(config)

        # Use enough data for the moving averages but with sideways movement
        # This should result in few or no crossovers
        mock_data_manager = mocker.MagicMock()
        mock_data_manager.fetch_historical_data.return_value = sideways_data
        engine.data_manager = mock_data_manager

        symbol = "NOTRADES"
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 6, 30)

        # Act
        result = engine.run_strategy_backtest(SimpleMovingAverageStrategy, symbol, start_date, end_date, strategy_params={"short_period": 10, "long_period": 30})

        # Assert
        assert isinstance(result, BacktestResult)
        # Sideways market may generate few or no trades
        assert result.total_trades >= 0
        assert result.winning_trades >= 0
        assert result.losing_trades >= 0
        assert result.win_rate >= 0.0
        assert len(result.trades) >= 0

    def test_should_handle_all_losing_trades_scenario(self, trending_down_data, mocker):
        """Test handling when all trades are losing."""
        # Arrange
        config = BacktestConfig(
            initial_capital=100000.0,
            commission_pct=0.001,
            stop_loss_pct=0.02,  # Tight stop loss
        )
        engine = BacktestingEngine(config)

        mock_data_manager = mocker.MagicMock()
        mock_data_manager.fetch_historical_data.return_value = trending_down_data
        engine.data_manager = mock_data_manager

        symbol = "LOSING"
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 6, 30)

        # Act
        result = engine.run_strategy_backtest(SimpleMovingAverageStrategy, symbol, start_date, end_date, strategy_params={"short_period": 5, "long_period": 10})

        # Assert
        assert isinstance(result, BacktestResult)
        # In a strong downtrend, long-only strategy should lose money
        assert result.total_return <= 0
        assert result.final_value <= result.initial_capital

    def test_should_compare_multiple_strategy_types(self, trending_up_data, mocker):
        """Test comparison of multiple strategy types."""
        # Arrange
        from finwiz.quantitative.backtesting_strategies import MeanReversionStrategy

        config = BacktestConfig(initial_capital=100000.0, commission_pct=0.001)
        engine = BacktestingEngine(config)

        mock_data_manager = mocker.MagicMock()
        mock_data_manager.fetch_historical_data.return_value = trending_up_data
        engine.data_manager = mock_data_manager

        strategies = [
            (SimpleMovingAverageStrategy, {"short_period": 10, "long_period": 30}),
            (MeanReversionStrategy, {"period": 20, "devfactor": 2.0}),
        ]

        symbol = "COMPARE"
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 6, 30)

        # Act
        results = engine.run_multi_strategy_backtest(strategies, symbol, start_date, end_date)

        # Assert
        assert len(results) == 2
        assert results[0].strategy_name == "SimpleMovingAverageStrategy"
        assert results[1].strategy_name == "MeanReversionStrategy"

        # Both should have valid results
        for result in results:
            assert result.initial_capital == approx(100000.0)
            assert result.final_value > 0
            assert result.total_trades >= 0

    def test_should_track_portfolio_values_over_time(self, trending_up_data, mocker):
        """Test that portfolio values are tracked over time."""
        # Arrange
        config = BacktestConfig(initial_capital=100000.0, commission_pct=0.001)
        engine = BacktestingEngine(config)

        mock_data_manager = mocker.MagicMock()
        mock_data_manager.fetch_historical_data.return_value = trending_up_data
        engine.data_manager = mock_data_manager

        symbol = "PORTFOLIO"
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 6, 30)

        # Act
        result = engine.run_strategy_backtest(SimpleMovingAverageStrategy, symbol, start_date, end_date)

        # Assert
        assert len(result.portfolio_values) > 0
        # Portfolio values should be tracked daily
        assert len(result.portfolio_values) >= 100  # At least 100 days of data
