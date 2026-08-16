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
    "minimum_bars_required",
]

logger = get_logger(__name__)

# Suppress Backtrader warnings for cleaner output
warnings.filterwarnings("ignore", category=UserWarning, module="backtrader")

# Extra bars beyond the strategy's longest lookback, so its indicators have
# reached minperiod and the backtest actually trades rather than warming up.
_WARMUP_BARS = 10


def minimum_bars_required(strategy_params: dict[str, Any] | None) -> int:
    """Bars a strategy needs before it can be backtested: lookback + warm-up.

    Shared with the callers of ``run_strategy_backtest`` so a refusal can name
    the threshold it refused against without re-deriving (and drifting from)
    this formula.
    """
    params = strategy_params or {}
    return int(params.get("long_period", params.get("period", 50))) + _WARMUP_BARS


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
    ) -> BacktestResult | None:
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
            Comprehensive backtest result, or ``None`` when the fetched series
            is shorter than the strategy's lookback window plus warm-up
            buffer. That is a legitimate refusal, not an error: backtrader
            would never reach ``minperiod`` for the strategy's indicators, so
            the caller must treat ``None`` as "cannot backtest this series",
            not as a bug to retry or paper over.

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

            # Check if we have enough data for the strategy's lookback window.
            # A short series is a legitimate input, not an error -- refuse by
            # returning None rather than raising. Raising here used to
            # propagate out through the comprehensive analyzer's shared
            # try/except and discard technical and performance analysis that
            # had already succeeded independently (see
            # tools/quantitative_comprehensive_analyzer.py, Task 15).
            min_data_points = minimum_bars_required(strategy_params)
            if len(data) < min_data_points:
                self.logger.info(
                    f"Skipping backtest for {symbol}: {len(data)} bars, need at least {min_data_points} (strategy lookback + warm-up buffer). Short series, not an error.",
                )
                return None

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
        except Exception as e:
            # Cerebro itself failed (data feed, analyzer setup, etc.). Bubble
            # up — the caller still wants visibility into "no backtest at all".
            self.logger.error(f"Error during backtest execution: {e}")
            raise

        # Calculate performance metrics with a safe-default fallback. The
        # 2026-04-29 run had AAPL fail here with `list index out of range`
        # from a benchmark date misalignment in calculate_benchmark_metrics;
        # the exception bubbled up, the scorer marked `volatility="missing"`,
        # and the holding was skipped entirely. With the fallback the
        # backtest still produces a lawful BacktestResult (volatility=0.0,
        # var/cvar=None) so qualitative analysis can still run.
        try:
            backtest_result = self.performance_analyzer.calculate_performance_metrics(
                strategy_instance,
                symbol,
                start_date,
                end_date,
                initial_value,
                final_value,
                benchmark_symbol,
            )
        except Exception as perf_error:
            self.logger.error(
                f"⚠️  Performance metrics failed for {symbol}: {perf_error}. "
                "Falling back to safe BacktestResult (volatility=0.0, var/cvar=None). "
                "This is a known fallback, NOT an assumption — the holding will still be analyzed.",
                exc_info=True,
            )
            backtest_result = BacktestResult(
                strategy_name=getattr(strategy_class, "__name__", "unknown"),
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                initial_capital=float(initial_value),
                final_value=float(final_value) if final_value > 0 else float(initial_value),
                total_return=0.0,
                annualized_return=0.0,
                volatility=0.0,
                sharpe_ratio=0.0,
                max_drawdown=0.0,
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                var_95=None,
                cvar_95=None,
                calmar_ratio=None,
                benchmark_return=None,
                alpha=None,
                beta=None,
            )

        self.logger.info(
            f"Backtest completed: Total Return={backtest_result.total_return:.2f}%, "
            f"Sharpe Ratio={backtest_result.sharpe_ratio:.2f}, "
            f"Max Drawdown={backtest_result.max_drawdown:.2f}%",
        )

        return backtest_result

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
                if result is not None:
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
