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
from typing import Any

from finwiz.quantitative.config import BacktestConfig, get_backtest_config
from finwiz.quantitative.data import HistoricalDataManager
from finwiz.tools.logger import get_logger

# Import models and enums from separate modules
from .backtesting_models import BacktestResult, PositionSizingMethod, Trade, TradeStatus, TradeType
from .backtesting_strategies import SimpleMovingAverageStrategy, StrategyFramework
from .backtesting_utils import create_backtrader_datafeed, setup_cerebro

# Re-export for backward compatibility
__all__ = [
    "BacktestResult",
    "BacktestingEngine",
    "PositionSizingMethod",
    "SimpleMovingAverageStrategy",
    "StrategyFramework",
    "Trade",
    "TradeStatus",
    "TradeType",
    "get_backtesting_engine",
]

logger = get_logger(__name__)

# Suppress Backtrader warnings for cleaner output
warnings.filterwarnings("ignore", category=UserWarning, module="backtrader")


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

        # Initialize performance analyzer
        from .backtesting_performance import BacktestingPerformanceAnalyzer

        self.performance_analyzer = BacktestingPerformanceAnalyzer(self.data_manager, self.config)

        # Initialize Backtrader cerebro
        self.cerebro = None
        self.results: list[Any] = []

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
        self.cerebro = setup_cerebro(self.config)

        # Add strategy with parameters
        strategy_params = strategy_params or {}
        self.cerebro.addstrategy(strategy_class, **strategy_params)

        # Fetch and add data
        try:
            data = self.data_manager.fetch_historical_data(symbol, start_date, end_date)
            if data.empty:
                raise ValueError(f"No data available for {symbol}")

            # Check if we have enough data for the strategy
            min_data_points = strategy_params.get("long_period", strategy_params.get("period", 50)) + 10
            if len(data) < min_data_points:
                raise ValueError(f"Insufficient data for {symbol}: got {len(data)} rows, need at least {min_data_points} for strategy parameters")

            # Convert to Backtrader data feed
            bt_data = create_backtrader_datafeed(data, symbol)
            self.cerebro.adddata(bt_data)

        except Exception as e:
            self.logger.error(f"Error loading data for {symbol}: {e}")
            raise

        # Add analyzers for performance metrics
        self.performance_analyzer.add_analyzers(self.cerebro)

        # Run backtest
        self.logger.info(f"Running backtest from {start_date} to {end_date}")
        initial_value = self.cerebro.broker.getvalue()

        try:
            results = self.cerebro.run()
            final_value = self.cerebro.broker.getvalue()

            # Extract strategy instance
            strategy_instance = results[0]

            # Calculate performance metrics
            backtest_result = self.performance_analyzer.calculate_performance_metrics(strategy_instance, symbol, start_date, end_date, initial_value, final_value, benchmark_symbol)

            self.logger.info(
                f"Backtest completed: Total Return={backtest_result.total_return:.2f}%, "
                f"Sharpe Ratio={backtest_result.sharpe_ratio:.2f}, "
                f"Max Drawdown={backtest_result.max_drawdown:.2f}%"
            )

            return backtest_result

        except Exception as e:
            self.logger.error(f"Error during backtest execution: {e}")
            raise

    def run_multi_strategy_backtest(self, strategies: list[tuple[type, dict[str, Any]]], symbol: str, start_date: datetime, end_date: datetime) -> list[BacktestResult]:
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

    def plot_results(self, save_path: str | None = None) -> None:
        """
        Plot backtesting results.

        Args:
            save_path: Optional path to save the plot

        """
        self.performance_analyzer.plot_results(self.cerebro, save_path)


# Global backtesting engine instance
_backtesting_engine: BacktestingEngine | None = None


def get_backtesting_engine() -> BacktestingEngine:
    """Get the global backtesting engine instance."""
    global _backtesting_engine
    if _backtesting_engine is None:
        _backtesting_engine = BacktestingEngine()
    return _backtesting_engine
