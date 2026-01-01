"""
Strategy framework and implementations for backtesting.

This module contains the base strategy framework and concrete strategy
implementations for use with the backtesting engine.
"""

from datetime import datetime
from typing import Any

import backtrader as bt  # backtrader has no official type stubs

from finwiz.tools.logger import get_logger

# Import the enums and models from the models module
from .backtesting_models import Trade, TradeStatus, TradeType

logger = get_logger(__name__)


class StrategyFramework(bt.Strategy):
    """
    Base class for custom trading strategies in the backtesting framework.

    Provides common functionality for:
    - Position sizing and risk management
    - Trade execution and logging
    - Performance tracking
    - Signal generation interface
    """

    params: tuple[tuple[str, float], ...] = (
        ("stop_loss_pct", 0.05),  # 5% stop loss
        ("take_profit_pct", 0.15),  # 15% take profit
        ("position_size_pct", 0.1),  # 10% of portfolio per position
        ("risk_free_rate", 0.02),  # 2% risk-free rate
    )

    def __init__(self) -> None:
        """Initialize strategy framework."""
        self.trades_executed: list[Any] = []
        self.signals: list[Any] = []
        self.portfolio_values: list[Any] = []

        # Risk management
        self.stop_loss_orders: dict[str, Any] = {}
        self.take_profit_orders: dict[str, Any] = {}

        # Performance tracking
        self.start_value = self.broker.getvalue()
        self.peak_value = self.start_value
        self.max_drawdown = 0.0

        logger.info(f"Initialized {self.__class__.__name__} strategy")

    def log(self, txt: str, dt: datetime | None = None) -> None:
        """Log strategy messages with timestamp."""
        dt = dt or self.datas[0].datetime.date(0)
        logger.debug(f"{dt.isoformat()}: {txt}")

    def notify_order(self, order: bt.Order) -> None:
        """Handle order notifications from Backtrader."""
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f"BUY EXECUTED: Price={order.executed.price:.2f}, Size={order.executed.size}, Cost={order.executed.value:.2f}")
            else:
                self.log(f"SELL EXECUTED: Price={order.executed.price:.2f}, Size={order.executed.size}, Cost={order.executed.value:.2f}")

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f"Order {order.status}")

    def notify_trade(self, trade: bt.Trade) -> None:
        """Handle trade notifications from Backtrader."""
        if not trade.isclosed:
            return

        # Skip trades with zero size
        if trade.size == 0:
            return

        # Create trade record
        trade_record = Trade(
            trade_id=f"{self.data._name}_{len(self.trades_executed)}",
            symbol=self.data._name,
            trade_type=TradeType.BUY if trade.size > 0 else TradeType.SELL,
            status=TradeStatus.CLOSED,
            entry_date=bt.num2date(trade.dtopen),
            entry_price=trade.price,
            quantity=abs(trade.size),
            exit_date=bt.num2date(trade.dtclose),
            exit_price=trade.price,
            commission=trade.commission,
            strategy_name=self.__class__.__name__,
        )

        # Calculate PnL
        trade_record.calculate_pnl()
        trade_record.calculate_holding_period()

        self.trades_executed.append(trade_record)

        self.log(f"TRADE CLOSED: PnL={trade.pnl:.2f}, PnL%={trade_record.pnl_percent:.2f}%")

    def calculate_position_size(self, price: float) -> int:
        """
        Calculate position size based on configured method.

        Args:
            price: Current price of the asset

        Returns:
            Number of shares to trade

        """
        portfolio_value = self.broker.getvalue()

        if self.params.position_size_pct <= 0:
            return 0

        # Calculate dollar amount to invest
        dollar_amount = portfolio_value * self.params.position_size_pct

        # Convert to shares (rounded down)
        shares = int(dollar_amount / price)

        return max(0, shares)

    def set_stop_loss(self, price: float) -> bt.Order | None:
        """
        Set stop loss order.

        Args:
            price: Stop loss price

        Returns:
            Stop loss order if created

        """
        if self.position and self.params.stop_loss_pct > 0:
            if self.position.size > 0:  # Long position
                stop_price = price * (1 - self.params.stop_loss_pct)
                return self.sell(exectype=bt.Order.Stop, price=stop_price)
            else:  # Short position
                stop_price = price * (1 + self.params.stop_loss_pct)
                return self.buy(exectype=bt.Order.Stop, price=stop_price)
        return None

    def set_take_profit(self, price: float) -> bt.Order | None:
        """
        Set take profit order.

        Args:
            price: Current price

        Returns:
            Take profit order if created

        """
        if self.position and self.params.take_profit_pct > 0:
            if self.position.size > 0:  # Long position
                target_price = price * (1 + self.params.take_profit_pct)
                return self.sell(exectype=bt.Order.Limit, price=target_price)
            else:  # Short position
                target_price = price * (1 - self.params.take_profit_pct)
                return self.buy(exectype=bt.Order.Limit, price=target_price)
        return None

    def update_drawdown(self) -> None:
        """Update maximum drawdown tracking."""
        current_value = self.broker.getvalue()

        if current_value > self.peak_value:
            self.peak_value = current_value

        drawdown = (self.peak_value - current_value) / self.peak_value
        if drawdown > self.max_drawdown:
            self.max_drawdown = drawdown

    def generate_signals(self) -> list[dict[str, Any]]:
        """
        Generate trading signals based on strategy logic.

        This method should be overridden by concrete strategy implementations.

        Returns:
            List of signal dictionaries with signal information

        """
        raise NotImplementedError("Subclasses must implement generate_signals method")

    def next(self) -> None:
        """
        Execute main strategy logic for each bar.

        This method should be overridden by concrete strategy implementations.
        """
        # Update performance tracking
        self.update_drawdown()

        # Record portfolio value
        current_value = self.broker.getvalue()
        current_date = self.datas[0].datetime.date(0).isoformat()
        self.portfolio_values.append((current_date, current_value))

        # Default implementation - subclasses should override
        pass


class SimpleMovingAverageStrategy(StrategyFramework):
    """
    Simple Moving Average crossover strategy implementation.

    Generates buy signals when short MA crosses above long MA,
    and sell signals when short MA crosses below long MA.
    """

    params = (
        ("short_period", 20),
        ("long_period", 50),
        ("stop_loss_pct", 0.05),
        ("take_profit_pct", 0.15),
        ("position_size_pct", 0.1),
    )

    def __init__(self) -> None:
        """Initialize SMA strategy."""
        super().__init__()

        # Create moving averages
        self.short_ma = bt.indicators.SimpleMovingAverage(self.datas[0], period=self.params.short_period)
        self.long_ma = bt.indicators.SimpleMovingAverage(self.datas[0], period=self.params.long_period)

        # Crossover signal
        self.crossover = bt.indicators.CrossOver(self.short_ma, self.long_ma)

    def generate_signals(self) -> list[dict[str, Any]]:
        """Generate SMA crossover signals."""
        signals = []

        if len(self.data) < self.params.long_period:
            return signals

        current_date = self.datas[0].datetime.date(0)
        current_price = self.datas[0].close[0]

        if self.crossover[0] > 0:  # Bullish crossover
            signals.append(
                {
                    "date": current_date,
                    "signal": "BUY",
                    "price": current_price,
                    "strength": 0.7,
                    "reason": f"Short MA({self.params.short_period}) crossed above Long MA({self.params.long_period})",
                }
            )
        elif self.crossover[0] < 0:  # Bearish crossover
            signals.append(
                {
                    "date": current_date,
                    "signal": "SELL",
                    "price": current_price,
                    "strength": 0.7,
                    "reason": f"Short MA({self.params.short_period}) crossed below Long MA({self.params.long_period})",
                }
            )

        return signals

    def next(self) -> None:
        """Execute SMA strategy logic."""
        super().next()

        # Skip if not enough data
        if len(self.data) < self.params.long_period:
            return

        current_price = self.datas[0].close[0]

        # Generate and log signals
        signals = self.generate_signals()
        self.signals.extend(signals)

        # Execute trades based on crossover
        if not self.position:  # No position
            if self.crossover[0] > 0:  # Bullish crossover
                size = self.calculate_position_size(current_price)
                if size > 0:
                    self.buy(size=size)
                    self.log(f"BUY ORDER: Size={size}, Price={current_price:.2f}")

        else:  # Have position
            if self.crossover[0] < 0:  # Bearish crossover
                self.sell(size=self.position.size)
                self.log(f"SELL ORDER: Size={self.position.size}, Price={current_price:.2f}")


class MeanReversionStrategy(StrategyFramework):
    """
    Mean reversion strategy using Bollinger Bands.

    Buys when price touches lower band and sells when price touches upper band.
    """

    params = (
        ("period", 20),
        ("devfactor", 2.0),
        ("stop_loss_pct", 0.03),
        ("take_profit_pct", 0.06),
        ("position_size_pct", 0.05),
    )

    def __init__(self) -> None:
        """Initialize mean reversion strategy."""
        super().__init__()

        # Bollinger Bands
        self.bollinger = bt.indicators.BollingerBands(self.datas[0], period=self.params.period, devfactor=self.params.devfactor)

    def generate_signals(self) -> list[dict[str, Any]]:
        """Generate mean reversion signals."""
        signals = []

        if len(self.data) < self.params.period:
            return signals

        current_date = self.datas[0].datetime.date(0)
        current_price = self.datas[0].close[0]
        lower_band = self.bollinger.lines.bot[0]
        upper_band = self.bollinger.lines.top[0]

        if current_price <= lower_band:  # Oversold
            signals.append(
                {
                    "date": current_date,
                    "signal": "BUY",
                    "price": current_price,
                    "strength": 0.6,
                    "reason": f"Price ({current_price:.2f}) at lower Bollinger Band ({lower_band:.2f})",
                }
            )
        elif current_price >= upper_band:  # Overbought
            signals.append(
                {
                    "date": current_date,
                    "signal": "SELL",
                    "price": current_price,
                    "strength": 0.6,
                    "reason": f"Price ({current_price:.2f}) at upper Bollinger Band ({upper_band:.2f})",
                }
            )

        return signals

    def next(self) -> None:
        """Execute mean reversion strategy logic."""
        super().next()

        if len(self.data) < self.params.period:
            return

        current_price = self.datas[0].close[0]
        signals = self.generate_signals()
        self.signals.extend(signals)

        if not self.position:
            if current_price <= self.bollinger.lines.bot[0]:
                size = self.calculate_position_size(current_price)
                if size > 0:
                    self.buy(size=size)
                    self.log(f"BUY ORDER (Mean Reversion): Size={size}, Price={current_price:.2f}")
        else:
            if current_price >= self.bollinger.lines.top[0]:
                self.sell(size=self.position.size)
                self.log(f"SELL ORDER (Mean Reversion): Size={self.position.size}, Price={current_price:.2f}")
