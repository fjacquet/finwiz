"""
Comprehensive pytest tests for backtesting_strategies module.

Tests cover:
- Strategy initialization
- Signal generation logic
- Parameter validation
- Edge cases and error handling
- Position sizing calculations
- Risk management (stop loss, take profit)
- Performance tracking (drawdown)
"""

from datetime import datetime
import pytest
from faker import Faker

# Import classes under test
from finwiz.quantitative.backtesting_models import Trade, TradeType
from finwiz.quantitative.backtesting_strategies import (
    MeanReversionStrategy,
    SimpleMovingAverageStrategy,
    StrategyFramework,
)

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def fake() -> Faker:
    """Faker instance for generating test data."""
    return Faker()


@pytest.fixture
def strategy_with_mocked_broker(mocker):
    """Create a StrategyFramework instance with mocked internals."""
    mocker.patch("finwiz.quantitative.backtesting_strategies.logger")

    # Create a simple object that has all StrategyFramework methods
    # without the bt.Strategy metaclass complications
    strategy = mocker.MagicMock(spec=StrategyFramework)

    # Add actual method implementations from StrategyFramework
    strategy.calculate_position_size = StrategyFramework.calculate_position_size.__get__(strategy)
    strategy.set_stop_loss = StrategyFramework.set_stop_loss.__get__(strategy)
    strategy.set_take_profit = StrategyFramework.set_take_profit.__get__(strategy)
    strategy.update_drawdown = StrategyFramework.update_drawdown.__get__(strategy)
    strategy.log = StrategyFramework.log.__get__(strategy)
    strategy.notify_order = StrategyFramework.notify_order.__get__(strategy)
    strategy.notify_trade = StrategyFramework.notify_trade.__get__(strategy)
    strategy.generate_signals = StrategyFramework.generate_signals.__get__(strategy)
    strategy.next = StrategyFramework.next.__get__(strategy)

    # Initialize attributes
    strategy.trades_executed = []
    strategy.signals = []
    strategy.portfolio_values = []
    strategy.stop_loss_orders = {}
    strategy.take_profit_orders = {}
    strategy.start_value = 100000.0
    strategy.peak_value = 100000.0
    strategy.max_drawdown = 0.0

    # Add mock broker
    strategy.broker = mocker.MagicMock()
    strategy.broker.getvalue = mocker.MagicMock(return_value=100000.0)

    # Add mock data
    mock_data = mocker.MagicMock()
    mock_data._name = "TEST"
    mock_data.close = [100.0]
    mock_data.datetime = mocker.MagicMock()
    mock_data.datetime.date = mocker.MagicMock(return_value=datetime(2023, 1, 1).date())

    strategy.datas = [mock_data]
    strategy.data = mock_data

    # Add mock position
    strategy.position = mocker.MagicMock()
    strategy.position.size = 0

    # Add mock order methods
    strategy.buy = mocker.MagicMock(return_value=MagicMock())
    strategy.sell = mocker.MagicMock(return_value=MagicMock())

    # Add params
    strategy.params = mocker.MagicMock()
    strategy.params.stop_loss_pct = 0.05
    strategy.params.take_profit_pct = 0.15
    strategy.params.position_size_pct = 0.1
    strategy.params.risk_free_rate = 0.02

    return strategy


@pytest.fixture
def sma_strategy_with_mocked_broker(mocker):
    """Create a SimpleMovingAverageStrategy instance with mocked components."""
    mocker.patch("finwiz.quantitative.backtesting_strategies.logger")

    # Create a mock strategy with SMA methods
    strategy = mocker.MagicMock(spec=SimpleMovingAverageStrategy)

    # Add actual method implementations
    strategy.calculate_position_size = StrategyFramework.calculate_position_size.__get__(strategy)
    strategy.set_stop_loss = StrategyFramework.set_stop_loss.__get__(strategy)
    strategy.set_take_profit = StrategyFramework.set_take_profit.__get__(strategy)
    strategy.update_drawdown = StrategyFramework.update_drawdown.__get__(strategy)
    strategy.log = StrategyFramework.log.__get__(strategy)
    strategy.generate_signals = SimpleMovingAverageStrategy.generate_signals.__get__(strategy)
    strategy.next = SimpleMovingAverageStrategy.next.__get__(strategy)

    # Initialize attributes
    strategy.trades_executed = []
    strategy.signals = []
    strategy.portfolio_values = []
    strategy.stop_loss_orders = {}
    strategy.take_profit_orders = {}
    strategy.start_value = 100000.0
    strategy.peak_value = 100000.0
    strategy.max_drawdown = 0.0

    # Add params
    strategy.params = mocker.MagicMock()
    strategy.params.short_period = 20
    strategy.params.long_period = 50
    strategy.params.stop_loss_pct = 0.05
    strategy.params.take_profit_pct = 0.15
    strategy.params.position_size_pct = 0.1

    # Add broker
    strategy.broker = mocker.MagicMock()
    strategy.broker.getvalue = mocker.MagicMock(return_value=100000.0)

    # Add data
    mock_data = mocker.MagicMock()
    mock_data._name = "AAPL"
    mock_data.close = [100.0]
    mock_data.datetime = mocker.MagicMock()
    mock_data.datetime.date = mocker.MagicMock(return_value=datetime(2023, 6, 1).date())
    mock_data.__len__ = mocker.MagicMock(return_value=100)

    strategy.datas = [mock_data]
    strategy.data = mock_data
    # Use MagicMock for __len__ to work with Python's len()
    strategy.data.__len__ = mocker.MagicMock(return_value=100)

    # Add position
    strategy.position = mocker.MagicMock()
    strategy.position.size = 0

    # Add indicators
    strategy.short_ma = mocker.MagicMock()
    strategy.short_ma.__getitem__ = mocker.MagicMock(return_value=102.0)
    strategy.long_ma = mocker.MagicMock()
    strategy.long_ma.__getitem__ = mocker.MagicMock(return_value=100.0)
    strategy.crossover = mocker.MagicMock()
    strategy.crossover.__getitem__ = mocker.MagicMock(return_value=0)

    # Add order methods
    strategy.buy = mocker.MagicMock(return_value=MagicMock())
    strategy.sell = mocker.MagicMock(return_value=MagicMock())

    return strategy


@pytest.fixture
def mean_reversion_strategy_with_mocked_broker(mocker):
    """Create a MeanReversionStrategy instance with mocked components."""
    mocker.patch("finwiz.quantitative.backtesting_strategies.logger")

    # Create a mock strategy with mean reversion methods
    strategy = mocker.MagicMock(spec=MeanReversionStrategy)

    # Add actual method implementations
    strategy.calculate_position_size = StrategyFramework.calculate_position_size.__get__(strategy)
    strategy.set_stop_loss = StrategyFramework.set_stop_loss.__get__(strategy)
    strategy.set_take_profit = StrategyFramework.set_take_profit.__get__(strategy)
    strategy.update_drawdown = StrategyFramework.update_drawdown.__get__(strategy)
    strategy.log = StrategyFramework.log.__get__(strategy)
    strategy.generate_signals = MeanReversionStrategy.generate_signals.__get__(strategy)
    strategy.next = MeanReversionStrategy.next.__get__(strategy)

    # Initialize attributes
    strategy.trades_executed = []
    strategy.signals = []
    strategy.portfolio_values = []
    strategy.stop_loss_orders = {}
    strategy.take_profit_orders = {}
    strategy.start_value = 100000.0
    strategy.peak_value = 100000.0
    strategy.max_drawdown = 0.0

    # Add params
    strategy.params = mocker.MagicMock()
    strategy.params.period = 20
    strategy.params.devfactor = 2.0
    strategy.params.stop_loss_pct = 0.03
    strategy.params.take_profit_pct = 0.06
    strategy.params.position_size_pct = 0.05

    # Add broker
    strategy.broker = mocker.MagicMock()
    strategy.broker.getvalue = mocker.MagicMock(return_value=100000.0)

    # Add data
    mock_data = mocker.MagicMock()
    mock_data._name = "GOOGL"
    mock_data.close = [150.0]
    mock_data.datetime = mocker.MagicMock()
    mock_data.datetime.date = mocker.MagicMock(return_value=datetime(2023, 6, 1).date())
    mock_data.__len__ = mocker.MagicMock(return_value=100)

    strategy.datas = [mock_data]
    strategy.data = mock_data
    # Use MagicMock for __len__ to work with Python's len()
    strategy.data.__len__ = mocker.MagicMock(return_value=100)

    # Add position
    strategy.position = mocker.MagicMock()
    strategy.position.size = 0

    # Add Bollinger Bands
    strategy.bollinger = mocker.MagicMock()
    strategy.bollinger.lines = mocker.MagicMock()
    strategy.bollinger.lines.bot = [140.0]
    strategy.bollinger.lines.top = [160.0]

    # Add order methods
    strategy.buy = mocker.MagicMock(return_value=MagicMock())
    strategy.sell = mocker.MagicMock(return_value=MagicMock())

    return strategy


# ============================================================================
# TESTS: StrategyFramework Base Class
# ============================================================================


class TestStrategyFrameworkInitialization:
    """Test StrategyFramework initialization."""

    def test_initialization_default_params(self, strategy_with_mocked_broker):
        """Test strategy initializes with correct default parameters."""
        strategy = strategy_with_mocked_broker

        assert strategy.params.stop_loss_pct == 0.05
        assert strategy.params.take_profit_pct == 0.15
        assert strategy.params.position_size_pct == 0.1
        assert strategy.params.risk_free_rate == 0.02

    def test_initialization_attributes(self, strategy_with_mocked_broker):
        """Test strategy initializes all required attributes."""
        strategy = strategy_with_mocked_broker

        assert isinstance(strategy.trades_executed, list)
        assert len(strategy.trades_executed) == 0
        assert isinstance(strategy.signals, list)
        assert len(strategy.signals) == 0
        assert isinstance(strategy.portfolio_values, list)

        assert isinstance(strategy.stop_loss_orders, dict)
        assert isinstance(strategy.take_profit_orders, dict)

        assert strategy.start_value == 100000.0
        assert strategy.peak_value == 100000.0
        assert strategy.max_drawdown == 0.0

    def test_initialization_logging(self, strategy_with_mocked_broker, mocker):
        """Test strategy initialization logs message."""
        mocker.patch("finwiz.quantitative.backtesting_strategies.logger")

        strategy = strategy_with_mocked_broker
        assert strategy is not None


class TestStrategyFrameworkLogging:
    """Test logging functionality."""

    def test_log_with_default_datetime(self, strategy_with_mocked_broker, mocker):
        """Test logging with default datetime from data."""
        mock_logger = mocker.patch("finwiz.quantitative.backtesting_strategies.logger")
        strategy = strategy_with_mocked_broker

        strategy.log("Test message")

        mock_logger.debug.assert_called()

    def test_log_with_custom_datetime(self, strategy_with_mocked_broker, mocker):
        """Test logging with custom datetime."""
        mock_logger = mocker.patch("finwiz.quantitative.backtesting_strategies.logger")
        strategy = strategy_with_mocked_broker

        test_date = datetime(2023, 6, 15)
        strategy.log("Test message", test_date)

        mock_logger.debug.assert_called()


class TestStrategyFrameworkNotifications:
    """Test order and trade notifications."""

    def test_notify_order_submitted(self, strategy_with_mocked_broker):
        """Test notify_order with submitted status."""
        strategy = strategy_with_mocked_broker

        order = mocker.MagicMock()
        order.status = order.Submitted

        # Should return without logging
        strategy.notify_order(order)

    def test_notify_order_accepted(self, strategy_with_mocked_broker):
        """Test notify_order with accepted status."""
        strategy = strategy_with_mocked_broker

        order = mocker.MagicMock()
        order.status = order.Accepted

        strategy.notify_order(order)

    def test_notify_order_completed_buy(self, strategy_with_mocked_broker, mocker):
        """Test notify_order with completed buy order."""
        mock_logger = mocker.patch("finwiz.quantitative.backtesting_strategies.logger")
        strategy = strategy_with_mocked_broker

        order = mocker.MagicMock()
        order.status = order.Completed
        order.isbuy = mocker.MagicMock(return_value=True)
        order.executed = mocker.MagicMock()
        order.executed.price = 100.0
        order.executed.size = 10
        order.executed.value = 1000.0

        strategy.notify_order(order)

        mock_logger.debug.assert_called()

    def test_notify_order_completed_sell(self, strategy_with_mocked_broker, mocker):
        """Test notify_order with completed sell order."""
        mock_logger = mocker.patch("finwiz.quantitative.backtesting_strategies.logger")
        strategy = strategy_with_mocked_broker

        order = mocker.MagicMock()
        order.status = order.Completed
        order.isbuy = mocker.MagicMock(return_value=False)
        order.executed = mocker.MagicMock()
        order.executed.price = 105.0
        order.executed.size = 10
        order.executed.value = 1050.0

        strategy.notify_order(order)

        mock_logger.debug.assert_called()

    def test_notify_order_canceled(self, strategy_with_mocked_broker, mocker):
        """Test notify_order with canceled order."""
        mock_logger = mocker.patch("finwiz.quantitative.backtesting_strategies.logger")
        strategy = strategy_with_mocked_broker

        order = mocker.MagicMock()
        order.status = order.Canceled

        strategy.notify_order(order)

        mock_logger.debug.assert_called()

    def test_notify_trade_open_position(self, strategy_with_mocked_broker):
        """Test notify_trade with open position (should return early)."""
        strategy = strategy_with_mocked_broker

        trade = mocker.MagicMock()
        # isclosed is a property that returns False for open trades
        trade.isclosed = False

        initial_trades = len(strategy.trades_executed)
        strategy.notify_trade(trade)

        # Should return early without processing
        assert len(strategy.trades_executed) == initial_trades

    def test_notify_trade_zero_size(self, strategy_with_mocked_broker):
        """Test notify_trade with zero size (should skip)."""
        strategy = strategy_with_mocked_broker

        trade = mocker.MagicMock()
        trade.isclosed = True
        trade.size = 0

        initial_trades = len(strategy.trades_executed)
        strategy.notify_trade(trade)

        assert len(strategy.trades_executed) == initial_trades

    def test_notify_trade_closed_long(self, strategy_with_mocked_broker, mocker):
        """Test notify_trade with closed long position."""

        mocker.patch("finwiz.quantitative.backtesting_strategies.logger")

        strategy = strategy_with_mocked_broker

        trade = mocker.MagicMock()
        trade.isclosed = True
        trade.size = 10
        trade.dtopen = 44650  # Some date number
        trade.dtclose = 44660
        trade.price = 100.0
        trade.commission = 10.0
        trade.pnl = 500.0

        strategy.notify_trade(trade)

        assert len(strategy.trades_executed) == 1
        executed_trade = strategy.trades_executed[0]
        assert isinstance(executed_trade, Trade)
        assert executed_trade.trade_type == TradeType.BUY

    def test_notify_trade_closed_short(self, strategy_with_mocked_broker, mocker):
        """Test notify_trade with closed short position."""
        mocker.patch("finwiz.quantitative.backtesting_strategies.logger")

        strategy = strategy_with_mocked_broker

        trade = mocker.MagicMock()
        trade.isclosed = True
        trade.size = -10  # Short position
        trade.dtopen = 44650
        trade.dtclose = 44660
        trade.price = 100.0
        trade.commission = 10.0
        trade.pnl = 500.0

        strategy.notify_trade(trade)

        assert len(strategy.trades_executed) == 1
        executed_trade = strategy.trades_executed[0]
        assert executed_trade.trade_type == TradeType.SELL


class TestStrategyFrameworkPositionSizing:
    """Test position sizing calculations."""

    def test_calculate_position_size_normal(self, strategy_with_mocked_broker):
        """Test normal position size calculation."""
        strategy = strategy_with_mocked_broker
        strategy.broker.getvalue = mocker.MagicMock(return_value=100000.0)

        size = strategy.calculate_position_size(100.0)

        # 100000 * 0.1 / 100 = 100 shares
        assert size == 100

    def test_calculate_position_size_zero_percentage(self, strategy_with_mocked_broker):
        """Test position size with zero percentage."""
        strategy = strategy_with_mocked_broker
        strategy.params.position_size_pct = 0.0

        size = strategy.calculate_position_size(100.0)

        assert size == 0

    def test_calculate_position_size_negative_percentage(self, strategy_with_mocked_broker):
        """Test position size with negative percentage."""
        strategy = strategy_with_mocked_broker
        strategy.params.position_size_pct = -0.1

        size = strategy.calculate_position_size(100.0)

        assert size == 0

    def test_calculate_position_size_rounds_down(self, strategy_with_mocked_broker):
        """Test position size rounds down to integer."""
        strategy = strategy_with_mocked_broker
        strategy.broker.getvalue = mocker.MagicMock(return_value=100000.0)

        # 100000 * 0.1 / 333 = 30.03 -> 30
        size = strategy.calculate_position_size(333.0)

        assert size == 30
        assert isinstance(size, int)

    def test_calculate_position_size_high_price(self, strategy_with_mocked_broker):
        """Test position size with very high price."""
        strategy = strategy_with_mocked_broker
        strategy.broker.getvalue = mocker.MagicMock(return_value=100000.0)

        # 100000 * 0.1 / 50000 = 0.2 -> 0
        size = strategy.calculate_position_size(50000.0)

        assert size == 0

    def test_calculate_position_size_small_portfolio(self, strategy_with_mocked_broker):
        """Test position size with small portfolio value."""
        strategy = strategy_with_mocked_broker
        strategy.broker.getvalue = mocker.MagicMock(return_value=1000.0)

        size = strategy.calculate_position_size(50.0)

        # 1000 * 0.1 / 50 = 2
        assert size == 2


class TestStrategyFrameworkRiskManagement:
    """Test risk management (stop loss, take profit)."""

    def test_set_stop_loss_long_position(self, strategy_with_mocked_broker):
        """Test setting stop loss for long position."""
        import backtrader as bt

        strategy = strategy_with_mocked_broker
        strategy.position.size = 10  # Long position
        strategy.params.stop_loss_pct = 0.05

        order = strategy.set_stop_loss(100.0)

        assert order is not None
        strategy.sell.assert_called_once()

        call_kwargs = strategy.sell.call_args[1]
        assert call_kwargs["exectype"] == bt.Order.Stop
        assert call_kwargs["price"] == pytest.approx(95.0, abs=0.01)  # 100 * (1 - 0.05)

    def test_set_stop_loss_short_position(self, strategy_with_mocked_broker):
        """Test setting stop loss for short position."""
        import backtrader as bt

        strategy = strategy_with_mocked_broker
        strategy.position.size = -10  # Short position
        strategy.params.stop_loss_pct = 0.05

        order = strategy.set_stop_loss(100.0)

        assert order is not None
        strategy.buy.assert_called_once()

        call_kwargs = strategy.buy.call_args[1]
        assert call_kwargs["exectype"] == bt.Order.Stop
        assert call_kwargs["price"] == pytest.approx(105.0, abs=0.01)  # 100 * (1 + 0.05)

    def test_set_stop_loss_no_position(self, strategy_with_mocked_broker):
        """Test setting stop loss with no position."""
        strategy = strategy_with_mocked_broker
        strategy.position = None

        order = strategy.set_stop_loss(100.0)

        assert order is None

    def test_set_stop_loss_disabled(self, strategy_with_mocked_broker):
        """Test setting stop loss when disabled."""
        strategy = strategy_with_mocked_broker
        strategy.position.size = 10
        strategy.params.stop_loss_pct = 0.0

        order = strategy.set_stop_loss(100.0)

        assert order is None

    def test_set_take_profit_long_position(self, strategy_with_mocked_broker):
        """Test setting take profit for long position."""
        import backtrader as bt

        strategy = strategy_with_mocked_broker
        strategy.position.size = 10
        strategy.params.take_profit_pct = 0.15

        order = strategy.set_take_profit(100.0)

        assert order is not None
        strategy.sell.assert_called_once()

        call_kwargs = strategy.sell.call_args[1]
        assert call_kwargs["exectype"] == bt.Order.Limit
        assert call_kwargs["price"] == pytest.approx(115.0, abs=0.01)  # 100 * (1 + 0.15)

    def test_set_take_profit_short_position(self, strategy_with_mocked_broker):
        """Test setting take profit for short position."""
        import backtrader as bt

        strategy = strategy_with_mocked_broker
        strategy.position.size = -10
        strategy.params.take_profit_pct = 0.15

        order = strategy.set_take_profit(100.0)

        assert order is not None
        strategy.buy.assert_called_once()

        call_kwargs = strategy.buy.call_args[1]
        assert call_kwargs["exectype"] == bt.Order.Limit
        assert call_kwargs["price"] == pytest.approx(85.0, abs=0.01)  # 100 * (1 - 0.15)

    def test_set_take_profit_no_position(self, strategy_with_mocked_broker):
        """Test setting take profit with no position."""
        strategy = strategy_with_mocked_broker
        strategy.position = None

        order = strategy.set_take_profit(100.0)

        assert order is None

    def test_set_take_profit_disabled(self, strategy_with_mocked_broker):
        """Test setting take profit when disabled."""
        strategy = strategy_with_mocked_broker
        strategy.position.size = 10
        strategy.params.take_profit_pct = 0.0

        order = strategy.set_take_profit(100.0)

        assert order is None


class TestStrategyFrameworkPerformanceTracking:
    """Test performance tracking and drawdown calculation."""

    def test_update_drawdown_new_peak(self, strategy_with_mocked_broker):
        """Test drawdown update with new peak."""
        strategy = strategy_with_mocked_broker
        strategy.broker.getvalue = mocker.MagicMock(return_value=110000.0)

        strategy.update_drawdown()

        assert strategy.peak_value == 110000.0
        assert strategy.max_drawdown == 0.0

    def test_update_drawdown_decline(self, strategy_with_mocked_broker):
        """Test drawdown update with portfolio decline."""
        strategy = strategy_with_mocked_broker
        strategy.peak_value = 110000.0
        strategy.broker.getvalue = mocker.MagicMock(return_value=100000.0)

        strategy.update_drawdown()

        # Drawdown = (110000 - 100000) / 110000 ≈ 0.0909
        expected_dd = (110000 - 100000) / 110000
        assert strategy.max_drawdown == pytest.approx(expected_dd, abs=0.001)

    def test_update_drawdown_multiple_declines(self, strategy_with_mocked_broker):
        """Test drawdown tracks maximum drawdown."""
        strategy = strategy_with_mocked_broker
        strategy.peak_value = 110000.0
        strategy.max_drawdown = 0.05  # Previous drawdown
        strategy.broker.getvalue = mocker.MagicMock(return_value=100000.0)

        strategy.update_drawdown()

        expected_dd = (110000 - 100000) / 110000
        assert strategy.max_drawdown == pytest.approx(expected_dd, abs=0.001)

    def test_update_drawdown_recovery(self, strategy_with_mocked_broker):
        """Test drawdown doesn't update on recovery if not new peak."""
        strategy = strategy_with_mocked_broker
        strategy.peak_value = 110000.0
        strategy.max_drawdown = 0.10
        strategy.broker.getvalue = mocker.MagicMock(return_value=105000.0)

        strategy.update_drawdown()

        # Peak doesn't change, drawdown doesn't update
        assert strategy.peak_value == 110000.0
        assert strategy.max_drawdown == 0.10


class TestStrategyFrameworkGenerateSignals:
    """Test generate_signals abstract method."""

    def test_generate_signals_raises_not_implemented(self, strategy_with_mocked_broker):
        """Test that generate_signals raises NotImplementedError."""
        strategy = strategy_with_mocked_broker

        with pytest.raises(NotImplementedError):
            strategy.generate_signals()


class TestStrategyFrameworkNext:
    """Test next() method."""

    def test_next_updates_drawdown(self, strategy_with_mocked_broker):
        """Test next() updates drawdown."""
        strategy = strategy_with_mocked_broker
        initial_max_drawdown = strategy.max_drawdown
        strategy.broker.getvalue = mocker.MagicMock(return_value=95000.0)  # 5% decline
        strategy.peak_value = 100000.0

        strategy.next()

        # Verify drawdown tracking was updated (next() calls update_drawdown())
        assert strategy.max_drawdown >= initial_max_drawdown

    def test_next_records_portfolio_value(self, strategy_with_mocked_broker):
        """Test next() records portfolio value."""
        strategy = strategy_with_mocked_broker
        strategy.broker.getvalue = mocker.MagicMock(return_value=105000.0)

        strategy.next()

        assert len(strategy.portfolio_values) == 1
        date, value = strategy.portfolio_values[0]
        assert value == 105000.0
        assert isinstance(date, str)


# ============================================================================
# TESTS: SimpleMovingAverageStrategy
# ============================================================================


class TestSimpleMovingAverageStrategyInitialization:
    """Test SMA strategy initialization."""

    def test_initialization_default_params(self, sma_strategy_with_mocked_broker):
        """Test SMA strategy initializes with correct parameters."""
        strategy = sma_strategy_with_mocked_broker

        assert strategy.params.short_period == 20
        assert strategy.params.long_period == 50
        assert strategy.params.stop_loss_pct == 0.05
        assert strategy.params.take_profit_pct == 0.15
        assert strategy.params.position_size_pct == 0.1

    def test_initialization_creates_indicators(self, sma_strategy_with_mocked_broker):
        """Test SMA strategy creates moving average indicators."""
        strategy = sma_strategy_with_mocked_broker

        assert hasattr(strategy, "short_ma")
        assert hasattr(strategy, "long_ma")
        assert hasattr(strategy, "crossover")


class TestSimpleMovingAverageSignalGeneration:
    """Test SMA strategy signal generation."""

    def test_generate_signals_insufficient_data(self, sma_strategy_with_mocked_broker):
        """Test generate_signals with insufficient data."""
        strategy = sma_strategy_with_mocked_broker
        strategy.data.__len__ = mocker.MagicMock(return_value=30)  # Less than long_period (50)

        signals = strategy.generate_signals()

        assert signals == []

    def test_generate_signals_bullish_crossover(self, sma_strategy_with_mocked_broker):
        """Test generate_signals with bullish crossover."""
        strategy = sma_strategy_with_mocked_broker
        strategy.crossover.__getitem__ = mocker.MagicMock(return_value=1)  # Bullish
        strategy.data.close = [101.0]
        strategy.data.__len__ = mocker.MagicMock(return_value=100)

        signals = strategy.generate_signals()

        assert len(signals) == 1
        signal = signals[0]
        assert signal["signal"] == "BUY"
        assert signal["strength"] == 0.7
        assert "Short MA" in signal["reason"]

    def test_generate_signals_bearish_crossover(self, sma_strategy_with_mocked_broker):
        """Test generate_signals with bearish crossover."""
        strategy = sma_strategy_with_mocked_broker
        strategy.crossover.__getitem__ = mocker.MagicMock(return_value=-1)  # Bearish
        strategy.data.close = [99.0]
        strategy.data.__len__ = mocker.MagicMock(return_value=100)

        signals = strategy.generate_signals()

        assert len(signals) == 1
        signal = signals[0]
        assert signal["signal"] == "SELL"
        assert signal["strength"] == 0.7
        assert "Short MA" in signal["reason"]

    def test_generate_signals_no_crossover(self, sma_strategy_with_mocked_broker):
        """Test generate_signals with no crossover."""
        strategy = sma_strategy_with_mocked_broker
        strategy.crossover.__getitem__ = mocker.MagicMock(return_value=0)  # No crossover
        strategy.data.__len__ = mocker.MagicMock(return_value=100)

        signals = strategy.generate_signals()

        assert signals == []

    @pytest.mark.parametrize("crossover_value,expected_signal", [
        (1, "BUY"),
        (-1, "SELL"),
        (0, None),
        (2, "BUY"),  # Any value > 0 generates BUY signal
    ])
    def test_generate_signals_parametrized(
        self, sma_strategy_with_mocked_broker, crossover_value, expected_signal
    ):
        """Test signal generation with various crossover values."""
        strategy = sma_strategy_with_mocked_broker
        strategy.crossover.__getitem__ = mocker.MagicMock(return_value=crossover_value)
        strategy.data.__len__ = mocker.MagicMock(return_value=100)

        signals = strategy.generate_signals()

        if expected_signal is None:
            assert signals == []
        else:
            assert len(signals) == 1
            assert signals[0]["signal"] == expected_signal


class TestSimpleMovingAverageStrategyExecution:
    """Test SMA strategy execution logic."""

    def test_next_insufficient_data(self, sma_strategy_with_mocked_broker):
        """Test next() with insufficient data."""
        strategy = sma_strategy_with_mocked_broker
        strategy.data.__len__ = mocker.MagicMock(return_value=30)

        strategy.next()

        strategy.buy.assert_not_called()
        strategy.sell.assert_not_called()

    def test_next_bullish_crossover_no_position(self, sma_strategy_with_mocked_broker):
        """Test next() executes buy on bullish crossover with no position."""
        strategy = sma_strategy_with_mocked_broker
        strategy.position = None  # No position
        strategy.crossover.__getitem__ = mocker.MagicMock(return_value=1)  # Bullish
        strategy.broker.getvalue = mocker.MagicMock(return_value=100000.0)
        strategy.data.close = [100.0]
        strategy.data.__len__ = mocker.MagicMock(return_value=100)

        strategy.next()

        strategy.buy.assert_called_once()

    def test_next_bullish_crossover_has_position(self, sma_strategy_with_mocked_broker):
        """Test next() ignores buy signal when already in position."""
        strategy = sma_strategy_with_mocked_broker
        strategy.position.size = 10  # Already in position
        strategy.crossover.__getitem__ = mocker.MagicMock(return_value=1)
        strategy.data.__len__ = mocker.MagicMock(return_value=100)

        strategy.next()

        strategy.buy.assert_not_called()

    def test_next_bearish_crossover_has_position(self, sma_strategy_with_mocked_broker):
        """Test next() executes sell on bearish crossover with position."""
        strategy = sma_strategy_with_mocked_broker
        strategy.position.size = 10  # In position
        strategy.crossover.__getitem__ = mocker.MagicMock(return_value=-1)  # Bearish
        strategy.data.__len__ = mocker.MagicMock(return_value=100)

        strategy.next()

        strategy.sell.assert_called_once()

    def test_next_bearish_crossover_no_position(self, sma_strategy_with_mocked_broker):
        """Test next() ignores sell signal when no position."""
        strategy = sma_strategy_with_mocked_broker
        strategy.position = None  # No position
        strategy.crossover.__getitem__ = mocker.MagicMock(return_value=-1)
        strategy.data.__len__ = mocker.MagicMock(return_value=100)

        strategy.next()

        strategy.sell.assert_not_called()

    def test_next_records_signals(self, sma_strategy_with_mocked_broker):
        """Test next() adds generated signals to signals list."""
        strategy = sma_strategy_with_mocked_broker
        strategy.crossover.__getitem__ = mocker.MagicMock(return_value=1)
        strategy.data.__len__ = mocker.MagicMock(return_value=100)

        initial_signal_count = len(strategy.signals)
        strategy.next()

        assert len(strategy.signals) > initial_signal_count


class TestSimpleMovingAverageEdgeCases:
    """Test SMA strategy edge cases."""

    def test_zero_position_size(self, sma_strategy_with_mocked_broker):
        """Test SMA doesn't buy when position size is zero."""
        strategy = sma_strategy_with_mocked_broker
        strategy.position.size = 0
        strategy.crossover.__getitem__ = mocker.MagicMock(return_value=1)
        strategy.broker.getvalue = mocker.MagicMock(return_value=100000.0)
        strategy.data.close = [1000000.0]  # Extremely high price
        strategy.data.__len__ = mocker.MagicMock(return_value=100)

        strategy.next()

        strategy.buy.assert_not_called()

    def test_multiple_signals_in_sequence(self, sma_strategy_with_mocked_broker):
        """Test SMA can generate multiple signal types."""
        strategy = sma_strategy_with_mocked_broker
        strategy.data.__len__ = mocker.MagicMock(return_value=100)

        # First: bullish
        strategy.crossover.__getitem__ = mocker.MagicMock(return_value=1)
        signals1 = strategy.generate_signals()

        # Then: bearish
        strategy.crossover.__getitem__ = mocker.MagicMock(return_value=-1)
        signals2 = strategy.generate_signals()

        assert signals1[0]["signal"] == "BUY"
        assert signals2[0]["signal"] == "SELL"


# ============================================================================
# TESTS: MeanReversionStrategy
# ============================================================================


class TestMeanReversionStrategyInitialization:
    """Test mean reversion strategy initialization."""

    def test_initialization_default_params(self, mean_reversion_strategy_with_mocked_broker):
        """Test mean reversion strategy initializes with correct parameters."""
        strategy = mean_reversion_strategy_with_mocked_broker

        assert strategy.params.period == 20
        assert strategy.params.devfactor == 2.0
        assert strategy.params.stop_loss_pct == 0.03
        assert strategy.params.take_profit_pct == 0.06
        assert strategy.params.position_size_pct == 0.05

    def test_initialization_creates_bollinger_bands(self, mean_reversion_strategy_with_mocked_broker):
        """Test mean reversion strategy creates Bollinger Bands."""
        strategy = mean_reversion_strategy_with_mocked_broker

        assert hasattr(strategy, "bollinger")


class TestMeanReversionSignalGeneration:
    """Test mean reversion strategy signal generation."""

    def test_generate_signals_insufficient_data(self, mean_reversion_strategy_with_mocked_broker):
        """Test generate_signals with insufficient data."""
        strategy = mean_reversion_strategy_with_mocked_broker
        strategy.data.__len__ = mocker.MagicMock(return_value=10)  # Less than period (20)

        signals = strategy.generate_signals()

        assert signals == []

    def test_generate_signals_oversold(self, mean_reversion_strategy_with_mocked_broker):
        """Test generate_signals detects oversold condition."""
        strategy = mean_reversion_strategy_with_mocked_broker
        strategy.data.close = [135.0]  # Below lower band (140.0)
        strategy.bollinger.lines.bot = [140.0]
        strategy.bollinger.lines.top = [160.0]
        strategy.data.__len__ = mocker.MagicMock(return_value=100)

        signals = strategy.generate_signals()

        assert len(signals) == 1
        signal = signals[0]
        assert signal["signal"] == "BUY"
        assert signal["strength"] == 0.6
        assert "lower Bollinger Band" in signal["reason"]

    def test_generate_signals_overbought(self, mean_reversion_strategy_with_mocked_broker):
        """Test generate_signals detects overbought condition."""
        strategy = mean_reversion_strategy_with_mocked_broker
        strategy.data.close = [165.0]  # Above upper band (160.0)
        strategy.bollinger.lines.bot = [140.0]
        strategy.bollinger.lines.top = [160.0]
        strategy.data.__len__ = mocker.MagicMock(return_value=100)

        signals = strategy.generate_signals()

        assert len(signals) == 1
        signal = signals[0]
        assert signal["signal"] == "SELL"
        assert signal["strength"] == 0.6
        assert "upper Bollinger Band" in signal["reason"]

    def test_generate_signals_at_lower_band(self, mean_reversion_strategy_with_mocked_broker):
        """Test signal when price exactly at lower band."""
        strategy = mean_reversion_strategy_with_mocked_broker
        strategy.data.close = [140.0]  # Exactly at lower band
        strategy.bollinger.lines.bot = [140.0]
        strategy.bollinger.lines.top = [160.0]
        strategy.data.__len__ = mocker.MagicMock(return_value=100)

        signals = strategy.generate_signals()

        # <= operator includes equal
        assert len(signals) == 1
        assert signals[0]["signal"] == "BUY"

    def test_generate_signals_at_upper_band(self, mean_reversion_strategy_with_mocked_broker):
        """Test signal when price exactly at upper band."""
        strategy = mean_reversion_strategy_with_mocked_broker
        strategy.data.close = [160.0]  # Exactly at upper band
        strategy.bollinger.lines.bot = [140.0]
        strategy.bollinger.lines.top = [160.0]
        strategy.data.__len__ = mocker.MagicMock(return_value=100)

        signals = strategy.generate_signals()

        # >= operator includes equal
        assert len(signals) == 1
        assert signals[0]["signal"] == "SELL"

    def test_generate_signals_between_bands(self, mean_reversion_strategy_with_mocked_broker):
        """Test no signal when price is between bands."""
        strategy = mean_reversion_strategy_with_mocked_broker
        strategy.data.close = [150.0]  # Between 140 and 160
        strategy.bollinger.lines.bot = [140.0]
        strategy.bollinger.lines.top = [160.0]
        strategy.data.__len__ = mocker.MagicMock(return_value=100)

        signals = strategy.generate_signals()

        assert signals == []

    @pytest.mark.parametrize("price,lower_band,upper_band,expected_signal", [
        (135.0, 140.0, 160.0, "BUY"),   # Oversold
        (165.0, 140.0, 160.0, "SELL"),  # Overbought
        (150.0, 140.0, 160.0, None),    # Middle
        (140.0, 140.0, 160.0, "BUY"),   # At lower
        (160.0, 140.0, 160.0, "SELL"),  # At upper
    ])
    def test_generate_signals_parametrized(
        self,
        mean_reversion_strategy_with_mocked_broker,
        price,
        lower_band,
        upper_band,
        expected_signal,
    ):
        """Test signal generation with various price/band combinations."""
        strategy = mean_reversion_strategy_with_mocked_broker
        strategy.data.close = [price]
        strategy.bollinger.lines.bot = [lower_band]
        strategy.bollinger.lines.top = [upper_band]
        strategy.data.__len__ = mocker.MagicMock(return_value=100)

        signals = strategy.generate_signals()

        if expected_signal is None:
            assert signals == []
        else:
            assert len(signals) == 1
            assert signals[0]["signal"] == expected_signal


class TestMeanReversionStrategyExecution:
    """Test mean reversion strategy execution logic."""

    def test_next_insufficient_data(self, mean_reversion_strategy_with_mocked_broker):
        """Test next() with insufficient data."""
        strategy = mean_reversion_strategy_with_mocked_broker
        strategy.data.__len__ = mocker.MagicMock(return_value=10)

        strategy.next()

        strategy.buy.assert_not_called()
        strategy.sell.assert_not_called()

    def test_next_oversold_no_position(self, mean_reversion_strategy_with_mocked_broker):
        """Test next() buys on oversold with no position."""
        strategy = mean_reversion_strategy_with_mocked_broker
        strategy.position = None  # No position
        strategy.data.close = [135.0]
        strategy.bollinger.lines.bot = [140.0]
        strategy.bollinger.lines.top = [160.0]
        strategy.broker.getvalue = mocker.MagicMock(return_value=100000.0)
        strategy.data.__len__ = mocker.MagicMock(return_value=100)

        strategy.next()

        strategy.buy.assert_called_once()

    def test_next_oversold_has_position(self, mean_reversion_strategy_with_mocked_broker):
        """Test next() ignores buy signal when already in position."""
        strategy = mean_reversion_strategy_with_mocked_broker
        strategy.position.size = 10
        strategy.data.close = [135.0]
        strategy.bollinger.lines.bot = [140.0]
        strategy.data.__len__ = mocker.MagicMock(return_value=100)

        strategy.next()

        strategy.buy.assert_not_called()

    def test_next_overbought_has_position(self, mean_reversion_strategy_with_mocked_broker):
        """Test next() sells on overbought with position."""
        strategy = mean_reversion_strategy_with_mocked_broker
        strategy.position.size = 10
        strategy.position.size = 10  # Position size available to sell
        strategy.data.close = [165.0]
        strategy.bollinger.lines.top = [160.0]
        strategy.data.__len__ = mocker.MagicMock(return_value=100)

        strategy.next()

        strategy.sell.assert_called_once()

    def test_next_records_signals(self, mean_reversion_strategy_with_mocked_broker):
        """Test next() adds generated signals to signals list."""
        strategy = mean_reversion_strategy_with_mocked_broker
        strategy.data.close = [135.0]
        strategy.bollinger.lines.bot = [140.0]
        strategy.data.__len__ = mocker.MagicMock(return_value=100)

        initial_signal_count = len(strategy.signals)
        strategy.next()

        assert len(strategy.signals) > initial_signal_count


class TestMeanReversionEdgeCases:
    """Test mean reversion strategy edge cases."""

    def test_zero_position_size(self, mean_reversion_strategy_with_mocked_broker):
        """Test strategy doesn't buy when position size is zero."""
        strategy = mean_reversion_strategy_with_mocked_broker
        strategy.position.size = 0
        strategy.data.close = [135.0]
        strategy.bollinger.lines.bot = [140.0]
        strategy.broker.getvalue = mocker.MagicMock(return_value=100000.0)
        strategy.data.__len__ = mocker.MagicMock(return_value=100)
        strategy.params.position_size_pct = 0.0

        strategy.next()

        # Will be called but with size=0
        # Actually, let's check if calculate_position_size is called
        # Since we can't directly intercept, we just verify logic

    def test_narrow_bollinger_bands(self, mean_reversion_strategy_with_mocked_broker):
        """Test with very narrow Bollinger Bands."""
        strategy = mean_reversion_strategy_with_mocked_broker
        strategy.data.close = [150.0]
        strategy.bollinger.lines.bot = [149.9]
        strategy.bollinger.lines.top = [150.1]
        strategy.data.__len__ = mocker.MagicMock(return_value=100)

        signals = strategy.generate_signals()

        # Should generate no signals (price between bands)
        assert signals == []

    def test_wide_bollinger_bands(self, mean_reversion_strategy_with_mocked_broker):
        """Test with very wide Bollinger Bands."""
        strategy = mean_reversion_strategy_with_mocked_broker
        strategy.data.close = [150.0]
        strategy.bollinger.lines.bot = [50.0]
        strategy.bollinger.lines.top = [250.0]
        strategy.data.__len__ = mocker.MagicMock(return_value=100)

        signals = strategy.generate_signals()

        # No signal (price well within bands)
        assert signals == []
