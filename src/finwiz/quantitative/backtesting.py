"""
Backtesting engine with Backtrader framework for FinWiz.

This module provides comprehensive backtesting capabilities including:
- BacktestingEngine class using Backtrader for strategy execution
- StrategyFramework base class for custom trading strategies
- Portfolio management, position sizing, and risk management features
- Performance analysis and reporting integration
- Multi-strategy backtesting support
"""

import warnings
from datetime import datetime
from enum import Enum
from typing import Any

import backtrader as bt
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field, validator

from finwiz.quantitative.config import BacktestConfig, get_backtest_config
from finwiz.quantitative.data import HistoricalDataManager
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)

# Suppress Backtrader warnings for cleaner output
warnings.filterwarnings("ignore", category=UserWarning, module="backtrader")


class PositionSizingMethod(str, Enum):
    """Position sizing methods for backtesting."""

    FIXED_AMOUNT = "fixed_amount"
    PERCENT_OF_PORTFOLIO = "percent_of_portfolio"
    KELLY_CRITERION = "kelly_criterion"
    VOLATILITY_ADJUSTED = "volatility_adjusted"


class TradeType(str, Enum):
    """Types of trades in backtesting."""

    BUY = "BUY"
    SELL = "SELL"
    SHORT = "SHORT"
    COVER = "COVER"


class TradeStatus(str, Enum):
    """Status of trades in backtesting."""

    OPEN = "OPEN"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


class Trade(BaseModel):
    """Represents a single trade in the backtesting system."""

    trade_id: str = Field(..., description="Unique identifier for the trade")
    symbol: str = Field(..., description="Symbol traded")
    trade_type: TradeType = Field(..., description="Type of trade (BUY/SELL/SHORT/COVER)")
    status: TradeStatus = Field(..., description="Current status of the trade")

    # Entry details
    entry_date: datetime = Field(..., description="Date when trade was entered")
    entry_price: float = Field(..., gt=0, description="Price at which trade was entered")
    quantity: int = Field(..., gt=0, description="Number of shares/units traded")

    # Exit details (optional for open trades)
    exit_date: datetime | None = Field(None, description="Date when trade was exited")
    exit_price: float | None = Field(None, description="Price at which trade was exited")

    # Financial metrics
    commission: float = Field(default=0.0, ge=0, description="Commission paid for the trade")
    slippage: float = Field(default=0.0, ge=0, description="Slippage cost for the trade")

    # Performance metrics (calculated)
    pnl: float | None = Field(None, description="Profit/Loss for the trade")
    pnl_percent: float | None = Field(None, description="Profit/Loss percentage")
    holding_period_days: int | None = Field(None, description="Number of days trade was held")

    # Risk management
    stop_loss_price: float | None = Field(None, description="Stop loss price if set")
    take_profit_price: float | None = Field(None, description="Take profit price if set")

    # Strategy context
    strategy_name: str = Field(..., description="Name of strategy that generated the trade")
    signal_strength: float | None = Field(None, ge=0, le=1, description="Strength of signal that triggered trade")

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}

    @validator("exit_price")
    def validate_exit_price_positive(cls, v: float | None) -> float | None:
        """Validate exit price is positive if provided."""
        if v is not None and v <= 0:
            raise ValueError("Exit price must be positive")
        return v

    def calculate_pnl(self) -> None:
        """Calculate PnL metrics for the trade."""
        if self.exit_price is None or self.status != TradeStatus.CLOSED:
            return

        if self.trade_type in [TradeType.BUY, TradeType.COVER]:
            # Long position or covering short
            gross_pnl = (self.exit_price - self.entry_price) * self.quantity
        else:
            # Short position
            gross_pnl = (self.entry_price - self.exit_price) * self.quantity

        # Subtract costs
        total_costs = self.commission + self.slippage
        self.pnl = gross_pnl - total_costs

        # Calculate percentage return
        if self.entry_price > 0:
            self.pnl_percent = (self.pnl / (self.entry_price * self.quantity)) * 100

    def calculate_holding_period(self) -> None:
        """Calculate holding period in days."""
        if self.exit_date is not None:
            self.holding_period_days = (self.exit_date - self.entry_date).days


class BacktestResult(BaseModel):
    """Comprehensive backtesting result."""

    # Strategy information
    strategy_name: str = Field(..., description="Name of the backtested strategy")
    symbol: str = Field(..., description="Symbol backtested")
    start_date: datetime = Field(..., description="Backtest start date")
    end_date: datetime = Field(..., description="Backtest end date")

    # Configuration
    initial_capital: float = Field(..., gt=0, description="Initial capital for backtesting")
    final_value: float = Field(..., gt=0, description="Final portfolio value")

    # Performance metrics
    total_return: float = Field(..., description="Total return percentage")
    annualized_return: float = Field(..., description="Annualized return percentage")
    volatility: float = Field(..., ge=0, description="Annualized volatility")
    sharpe_ratio: float = Field(..., description="Sharpe ratio")
    max_drawdown: float = Field(..., le=0, description="Maximum drawdown percentage")

    # Trade statistics
    total_trades: int = Field(..., ge=0, description="Total number of trades")
    winning_trades: int = Field(..., ge=0, description="Number of winning trades")
    losing_trades: int = Field(..., ge=0, description="Number of losing trades")
    win_rate: float = Field(default=0.0, ge=0, le=1, description="Win rate percentage")

    # Risk metrics
    var_95: float | None = Field(None, description="Value at Risk (95% confidence)")
    cvar_95: float | None = Field(None, description="Conditional Value at Risk (95%)")
    calmar_ratio: float | None = Field(None, description="Calmar ratio (return/max drawdown)")

    # Detailed trade records
    trades: list[Trade] = Field(default_factory=list, description="List of all trades executed")

    # Daily portfolio values for analysis
    portfolio_values: dict[str, float] = Field(default_factory=dict, description="Daily portfolio values")

    # Benchmark comparison
    benchmark_return: float | None = Field(None, description="Benchmark return for comparison")
    alpha: float | None = Field(None, description="Alpha relative to benchmark")
    beta: float | None = Field(None, description="Beta relative to benchmark")

    # Execution timestamp
    backtest_timestamp: datetime = Field(default_factory=datetime.now, description="When backtest was executed")

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}

    @validator("win_rate", always=True)
    def calculate_win_rate(cls, v: float, values: dict[str, Any]) -> float:
        """Calculate win rate from winning and total trades if not explicitly set."""
        # If win_rate is the default value (0.0), calculate it
        if v == 0.0 and "total_trades" in values and values["total_trades"] > 0:
            winning_trades = values.get("winning_trades", 0)
            return winning_trades / values["total_trades"]
        return v


class StrategyFramework(bt.Strategy):
    """
    Base class for custom trading strategies in the backtesting framework.

    Provides common functionality for:
    - Position sizing and risk management
    - Trade execution and logging
    - Performance tracking
    - Signal generation interface
    """

    params = (
        ("stop_loss_pct", 0.05),  # 5% stop loss
        ("take_profit_pct", 0.15),  # 15% take profit
        ("position_size_pct", 0.1),  # 10% of portfolio per position
        ("risk_free_rate", 0.02),  # 2% risk-free rate
    )

    def __init__(self) -> None:
        """Initialize strategy framework."""
        self.trades_executed = []
        self.signals = []
        self.portfolio_values = []

        # Risk management
        self.stop_loss_orders = {}
        self.take_profit_orders = {}

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
                self.log(
                    f"BUY EXECUTED: Price={order.executed.price:.2f}, Size={order.executed.size}, Cost={order.executed.value:.2f}"
                )
            else:
                self.log(
                    f"SELL EXECUTED: Price={order.executed.price:.2f}, Size={order.executed.size}, Cost={order.executed.value:.2f}"
                )

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


class BacktestingEngine:
    """
    Comprehensive backtesting engine using Backtrader framework.

    Features:
    - Multiple strategy support
    - Advanced position sizing and risk management
    - Comprehensive performance analysis
    - Portfolio optimization integration
    - Benchmark comparison capabilities
    """

    def __init__(self, config: BacktestConfig | None = None) -> None:
        """
        Initialize backtesting engine.

        Args:
            config: Backtesting configuration

        """
        self.config = config or get_backtest_config()
        self.data_manager = HistoricalDataManager()
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")

        # Initialize Backtrader cerebro
        self.cerebro = None
        self.results = []

    def run_strategy_backtest(
        self,
        strategy_class: type,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        strategy_params: dict[str, Any] | None = None,
        benchmark_symbol: str | None = None,
    ) -> BacktestResult:
        """
        Execute comprehensive backtesting workflow with professional-grade tools.

        Args:
            strategy_class: Strategy class to backtest
            symbol: Symbol to backtest
            start_date: Backtest start date
            end_date: Backtest end date
            strategy_params: Optional strategy parameters
            benchmark_symbol: Optional benchmark symbol for comparison

        Returns:
            Comprehensive backtest result

        """
        self.logger.info(f"Starting backtest for {strategy_class.__name__} on {symbol}")

        # Initialize Cerebro
        self.cerebro = bt.Cerebro()

        # Set initial capital
        self.cerebro.broker.setcash(self.config.initial_capital)

        # Set commission
        self.cerebro.broker.setcommission(commission=self.config.commission_pct)

        # Add strategy with parameters
        strategy_params = strategy_params or {}
        self.cerebro.addstrategy(strategy_class, **strategy_params)

        # Fetch and add data
        try:
            data = self.data_manager.fetch_historical_data(symbol, start_date, end_date)
            if data.empty:
                raise ValueError(f"No data available for {symbol}")

            # Convert to Backtrader data feed
            bt_data = self._create_backtrader_datafeed(data, symbol)
            self.cerebro.adddata(bt_data)

        except Exception as e:
            self.logger.error(f"Error loading data for {symbol}: {e}")
            raise

        # Add analyzers for performance metrics
        self._add_analyzers()

        # Run backtest
        self.logger.info(f"Running backtest from {start_date} to {end_date}")
        initial_value = self.cerebro.broker.getvalue()

        try:
            results = self.cerebro.run()
            final_value = self.cerebro.broker.getvalue()

            # Extract strategy instance
            strategy_instance = results[0]

            # Calculate performance metrics
            backtest_result = self._calculate_performance_metrics(
                strategy_instance, symbol, start_date, end_date, initial_value, final_value, benchmark_symbol
            )

            self.logger.info(
                f"Backtest completed: Total Return={backtest_result.total_return:.2f}%, "
                f"Sharpe Ratio={backtest_result.sharpe_ratio:.2f}, "
                f"Max Drawdown={backtest_result.max_drawdown:.2f}%"
            )

            return backtest_result

        except Exception as e:
            self.logger.error(f"Error during backtest execution: {e}")
            raise

    def run_multi_strategy_backtest(
        self, strategies: list[tuple[type, dict[str, Any]]], symbol: str, start_date: datetime, end_date: datetime
    ) -> list[BacktestResult]:
        """
        Run multiple strategies and compare results.

        Args:
            strategies: List of (strategy_class, params) tuples
            symbol: Symbol to backtest
            start_date: Backtest start date
            end_date: Backtest end date

        Returns:
            List of backtest results for comparison

        """
        results = []

        for strategy_class, params in strategies:
            try:
                result = self.run_strategy_backtest(strategy_class, symbol, start_date, end_date, params)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Error backtesting {strategy_class.__name__}: {e}")
                continue

        return results

    def _create_backtrader_datafeed(self, data: pd.DataFrame, symbol: str) -> bt.feeds.PandasData:
        """
        Create Backtrader data feed from pandas DataFrame.

        Args:
            data: OHLCV data
            symbol: Symbol name

        Returns:
            Backtrader data feed

        """
        # Ensure proper column mapping
        data_feed = bt.feeds.PandasData(
            dataname=data,
            datetime=None,  # Use index as datetime
            open="Open",
            high="High",
            low="Low",
            close="Close",
            volume="Volume",
            openinterest=None,
        )

        # Set name for identification
        data_feed._name = symbol

        return data_feed

    def _add_analyzers(self) -> None:
        """Add performance analyzers to Cerebro."""
        # Returns analyzer
        self.cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")

        # Sharpe ratio analyzer
        self.cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe", riskfreerate=self.config.risk_free_rate, annualize=True)

        # Drawdown analyzer
        self.cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")

        # Trade analyzer
        self.cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")

        # VaR analyzer if available
        try:
            self.cerebro.addanalyzer(bt.analyzers.VWR, _name="vwr")
        except AttributeError:
            pass  # VaR analyzer not available in this version

    def _calculate_performance_metrics(
        self,
        strategy_instance: bt.Strategy,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        initial_value: float,
        final_value: float,
        benchmark_symbol: str | None = None,
    ) -> BacktestResult:
        """
        Calculate comprehensive performance metrics.

        Args:
            strategy_instance: Executed strategy instance
            symbol: Backtested symbol
            start_date: Backtest start date
            end_date: Backtest end date
            initial_value: Initial portfolio value
            final_value: Final portfolio value
            benchmark_symbol: Optional benchmark for comparison

        Returns:
            Comprehensive backtest result

        """
        # Basic performance metrics
        total_return = ((final_value - initial_value) / initial_value) * 100

        # Calculate annualized return
        days = (end_date - start_date).days
        years = days / 365.25
        annualized_return = ((final_value / initial_value) ** (1 / years) - 1) * 100 if years > 0 else 0

        # Extract analyzer results
        analyzers = strategy_instance.analyzers

        # Sharpe ratio
        sharpe_ratio = 0.0
        if hasattr(analyzers, "sharpe") and analyzers.sharpe.get_analysis():
            sharpe_analysis = analyzers.sharpe.get_analysis()
            sharpe_ratio = sharpe_analysis.get("sharperatio", 0.0) or 0.0

        # Drawdown
        max_drawdown = 0.0
        if hasattr(analyzers, "drawdown") and analyzers.drawdown.get_analysis():
            drawdown_analysis = analyzers.drawdown.get_analysis()
            drawdown_value = drawdown_analysis.get("max", {}).get("drawdown", 0.0) or 0.0
            # Ensure drawdown is negative (a loss)
            max_drawdown = -abs(drawdown_value)

        # Trade statistics
        total_trades = 0
        winning_trades = 0
        losing_trades = 0

        if hasattr(analyzers, "trades") and analyzers.trades.get_analysis():
            trade_analysis = analyzers.trades.get_analysis()
            total_trades = trade_analysis.get("total", {}).get("total", 0) or 0
            winning_trades = trade_analysis.get("won", {}).get("total", 0) or 0
            losing_trades = trade_analysis.get("lost", {}).get("total", 0) or 0

        # Calculate volatility from portfolio values
        volatility = self._calculate_volatility(strategy_instance.portfolio_values)

        # Portfolio values dictionary
        portfolio_values = {date: value for date, value in strategy_instance.portfolio_values}

        # Benchmark comparison
        benchmark_return = None
        alpha = None
        beta = None

        if benchmark_symbol:
            try:
                benchmark_return, alpha, beta = self._calculate_benchmark_metrics(
                    portfolio_values, benchmark_symbol, start_date, end_date
                )
            except Exception as e:
                self.logger.warning(f"Could not calculate benchmark metrics: {e}")

        # Risk metrics
        var_95 = self._calculate_var(strategy_instance.portfolio_values, 0.95)
        cvar_95 = self._calculate_cvar(strategy_instance.portfolio_values, 0.95)
        calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown != 0 else None

        return BacktestResult(
            strategy_name=strategy_instance.__class__.__name__,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_value,
            final_value=final_value,
            total_return=total_return,
            annualized_return=annualized_return,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=winning_trades / total_trades if total_trades > 0 else 0.0,
            var_95=var_95,
            cvar_95=cvar_95,
            calmar_ratio=calmar_ratio,
            trades=strategy_instance.trades_executed,
            portfolio_values=portfolio_values,
            benchmark_return=benchmark_return,
            alpha=alpha,
            beta=beta,
        )

    def _calculate_volatility(self, portfolio_values: list[tuple[str, float]]) -> float:
        """Calculate annualized volatility from portfolio values."""
        if len(portfolio_values) < 2:
            return 0.0

        values = [value for _, value in portfolio_values]
        returns = np.diff(values) / values[:-1]

        if len(returns) == 0:
            return 0.0

        daily_vol = np.std(returns)
        annualized_vol = daily_vol * np.sqrt(252)  # Assuming 252 trading days

        return annualized_vol * 100  # Convert to percentage

    def _calculate_var(self, portfolio_values: list[tuple[str, float]], confidence: float) -> float | None:
        """Calculate Value at Risk."""
        if len(portfolio_values) < 2:
            return None

        values = [value for _, value in portfolio_values]
        returns = np.diff(values) / values[:-1]

        if len(returns) == 0:
            return None

        return np.percentile(returns, (1 - confidence) * 100) * 100

    def _calculate_cvar(self, portfolio_values: list[tuple[str, float]], confidence: float) -> float | None:
        """Calculate Conditional Value at Risk."""
        var = self._calculate_var(portfolio_values, confidence)
        if var is None:
            return None

        values = [value for _, value in portfolio_values]
        returns = np.diff(values) / values[:-1]

        # CVaR is the average of returns below VaR threshold
        threshold = var / 100  # Convert back to decimal
        tail_returns = returns[returns <= threshold]

        if len(tail_returns) == 0:
            return var

        return np.mean(tail_returns) * 100

    def _calculate_benchmark_metrics(
        self, portfolio_values: dict[str, float], benchmark_symbol: str, start_date: datetime, end_date: datetime
    ) -> tuple[float, float, float]:
        """Calculate benchmark comparison metrics."""
        # Fetch benchmark data
        benchmark_data = self.data_manager.fetch_historical_data(benchmark_symbol, start_date, end_date)

        if benchmark_data.empty:
            raise ValueError(f"No benchmark data available for {benchmark_symbol}")

        # Calculate benchmark return
        initial_benchmark = benchmark_data["Close"].iloc[0]
        final_benchmark = benchmark_data["Close"].iloc[-1]
        benchmark_return = ((final_benchmark - initial_benchmark) / initial_benchmark) * 100

        # Calculate alpha and beta (simplified calculation)
        # This is a basic implementation - more sophisticated methods could be used
        portfolio_returns = []
        benchmark_returns = []

        portfolio_dates = sorted(portfolio_values.keys())

        for i in range(1, len(portfolio_dates)):
            date = portfolio_dates[i]
            prev_date = portfolio_dates[i - 1]

            # Portfolio return
            port_return = (portfolio_values[date] - portfolio_values[prev_date]) / portfolio_values[prev_date]
            portfolio_returns.append(port_return)

            # Benchmark return for same period
            try:
                date_obj = datetime.fromisoformat(date)
                benchmark_price = benchmark_data.loc[benchmark_data.index.date == date_obj.date(), "Close"]
                prev_date_obj = datetime.fromisoformat(prev_date)
                prev_benchmark_price = benchmark_data.loc[benchmark_data.index.date == prev_date_obj.date(), "Close"]

                if not benchmark_price.empty and not prev_benchmark_price.empty:
                    bench_return = (benchmark_price.iloc[0] - prev_benchmark_price.iloc[0]) / prev_benchmark_price.iloc[0]
                    benchmark_returns.append(bench_return)
                else:
                    benchmark_returns.append(0.0)
            except Exception:
                benchmark_returns.append(0.0)

        if len(portfolio_returns) > 1 and len(benchmark_returns) > 1:
            # Calculate beta using covariance
            portfolio_returns = np.array(portfolio_returns)
            benchmark_returns = np.array(benchmark_returns)

            covariance = np.cov(portfolio_returns, benchmark_returns)[0, 1]
            benchmark_variance = np.var(benchmark_returns)

            beta = covariance / benchmark_variance if benchmark_variance != 0 else 1.0

            # Calculate alpha
            portfolio_mean_return = np.mean(portfolio_returns)
            benchmark_mean_return = np.mean(benchmark_returns)
            risk_free_daily = self.config.risk_free_rate / 252  # Daily risk-free rate

            alpha = (portfolio_mean_return - risk_free_daily) - beta * (benchmark_mean_return - risk_free_daily)
            alpha = alpha * 252 * 100  # Annualize and convert to percentage
        else:
            alpha = 0.0
            beta = 1.0

        return benchmark_return, alpha, beta

    def plot_results(self, save_path: str | None = None) -> None:
        """
        Plot backtesting results.

        Args:
            save_path: Optional path to save the plot

        """
        if self.cerebro is None:
            self.logger.warning("No backtest results to plot")
            return

        try:
            if save_path:
                self.cerebro.plot(savefig=save_path)
            else:
                self.cerebro.plot()
        except Exception as e:
            self.logger.error(f"Error plotting results: {e}")


# Global backtesting engine instance
_backtesting_engine: BacktestingEngine | None = None


def get_backtesting_engine() -> BacktestingEngine:
    """Get the global backtesting engine instance."""
    global _backtesting_engine
    if _backtesting_engine is None:
        _backtesting_engine = BacktestingEngine()
    return _backtesting_engine
