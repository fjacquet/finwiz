"""
Performance analysis utilities for backtesting.

This module contains performance metrics calculation, benchmark comparison,
and risk analysis functions for backtesting results.
"""

import math
from datetime import datetime
from typing import Any

import backtrader as bt  # backtrader has no official type stubs
import numpy as np

from finwiz.quantitative.data import HistoricalDataManager
from finwiz.tools.logger import get_logger

# Import the models from the models module
from .backtesting_models import BacktestResult

logger = get_logger(__name__)


def _safe_int(value: Any, default: int = 0) -> int:
    """Convert to int, treating NaN/None as default."""
    if value is None:
        return default
    try:
        if math.isnan(float(value)):
            return default
    except (TypeError, ValueError):
        return default
    return int(value)


def _finite_returns_from_values(values: list[float]) -> np.ndarray:
    """Compute period-over-period returns and drop non-finite entries.

    Returns an empty array when fewer than 2 finite values are available or
    when every period contains a zero divisor (which would yield NaN/inf in
    ``np.diff(values) / values[:-1]``).
    """
    arr = np.asarray(values, dtype=float)
    if arr.size < 2:
        return np.empty(0, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        returns = np.diff(arr) / arr[:-1]
    return returns[np.isfinite(returns)]


class BacktestingPerformanceAnalyzer:
    """Performance analysis utilities for backtesting results."""

    def __init__(self, data_manager: HistoricalDataManager, config: Any) -> None:
        """
        Initialize performance analyzer.

        Args:
            data_manager: Historical data manager instance
            config: Backtesting configuration

        """
        self.data_manager = data_manager
        self.config = config
        self.logger = logger

    def add_analyzers(self, cerebro: bt.Cerebro) -> None:
        """Add performance analyzers to Cerebro."""
        # Returns analyzer
        cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")

        # Sharpe ratio analyzer
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe", riskfreerate=self.config.risk_free_rate, annualize=True)

        # Drawdown analyzer
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")

        # Trade analyzer
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")

        # VaR analyzer if available
        try:
            cerebro.addanalyzer(bt.analyzers.VWR, _name="vwr")
        except AttributeError:
            pass  # VaR analyzer not available in this version

    def calculate_performance_metrics(
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
        # WS-B.3 — Defensive: when Backtrader didn't run any bars (empty
        # data feed, all-NaN inputs, date-range collapse), portfolio_values
        # is empty and downstream metric extraction is meaningless. Emit a
        # safe-default BacktestResult so the holding can still be analyzed
        # qualitatively (vs. blowing up the scorer with `volatility=missing`).
        portfolio_values_list = getattr(strategy_instance, "portfolio_values", []) or []
        if len(portfolio_values_list) < 2:
            logger.warning(
                f"⚠️  portfolio_values too short for {symbol} (len={len(portfolio_values_list)} < 2). Strategy never executed? Returning safe-default BacktestResult.",
            )
            return BacktestResult(
                strategy_name=type(strategy_instance).__name__,
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
            total_trades = _safe_int(trade_analysis.get("total", {}).get("total", 0))
            winning_trades = _safe_int(trade_analysis.get("won", {}).get("total", 0))
            losing_trades = _safe_int(trade_analysis.get("lost", {}).get("total", 0))

        # Calculate volatility from portfolio values
        volatility = self.calculate_volatility(strategy_instance.portfolio_values)

        # Portfolio values dictionary
        portfolio_values = {date: value for date, value in strategy_instance.portfolio_values}

        # Benchmark comparison
        benchmark_return = None
        alpha = None
        beta = None

        if benchmark_symbol:
            try:
                benchmark_return, alpha, beta = self.calculate_benchmark_metrics(portfolio_values, benchmark_symbol, start_date, end_date)
            except Exception as e:
                self.logger.warning(f"Could not calculate benchmark metrics: {e}")

        # Risk metrics
        var_95 = self.calculate_var(strategy_instance.portfolio_values, 0.95)
        cvar_95 = self.calculate_cvar(strategy_instance.portfolio_values, 0.95)
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

    def calculate_volatility(self, portfolio_values: list[tuple[str, float]]) -> float:
        """Calculate annualized volatility from portfolio values."""
        if len(portfolio_values) < 2:
            return 0.0

        values = [value for _, value in portfolio_values]
        returns = _finite_returns_from_values(values)

        if returns.size == 0:
            return 0.0

        daily_vol = np.std(returns)
        if not np.isfinite(daily_vol):
            return 0.0
        annualized_vol = daily_vol * np.sqrt(252)  # Assuming 252 trading days

        return float(annualized_vol * 100)  # Convert to percentage

    def calculate_var(self, portfolio_values: list[tuple[str, float]], confidence: float) -> float | None:
        """Calculate Value at Risk."""
        if len(portfolio_values) < 2:
            return None

        values = [value for _, value in portfolio_values]
        returns = _finite_returns_from_values(values)

        if returns.size == 0:
            return None

        pct = np.percentile(returns, (1 - confidence) * 100)
        if not np.isfinite(pct):
            return None
        return float(pct * 100)

    def calculate_cvar(self, portfolio_values: list[tuple[str, float]], confidence: float) -> float | None:
        """Calculate Conditional Value at Risk."""
        var = self.calculate_var(portfolio_values, confidence)
        if var is None:
            return None

        values = [value for _, value in portfolio_values]
        returns = _finite_returns_from_values(values)

        # CVaR is the average of returns below VaR threshold
        threshold = var / 100  # Convert back to decimal
        tail_returns = returns[returns <= threshold]

        if tail_returns.size == 0:
            return var

        mean = np.mean(tail_returns)
        if not np.isfinite(mean):
            return var
        return float(mean * 100)

    def calculate_benchmark_metrics(self, portfolio_values: dict[str, float], benchmark_symbol: str, start_date: datetime, end_date: datetime) -> tuple[float, float, float]:
        """Calculate benchmark comparison metrics.

        Returns safe defaults ``(0.0, 0.0, 1.0)`` when the benchmark is
        empty, has fewer than 2 rows, or its first close price is non-finite
        / zero — instead of raising ``ValueError`` / ``ZeroDivisionError`` /
        ``IndexError`` upward, where they would explode the whole backtest
        and mark the holding as "missing volatility" downstream. The 2026-04-29
        run had the IndexError variant trigger AAPL's skip.
        """
        # Fetch benchmark data
        benchmark_data = self.data_manager.fetch_historical_data(benchmark_symbol, start_date, end_date)

        # Empty or too short — neutral defaults rather than aborting.
        if benchmark_data.empty or len(benchmark_data) < 2:
            logger.warning(
                f"Benchmark {benchmark_symbol} returned {len(benchmark_data)} rows; using neutral defaults (benchmark_return=0.0, alpha=0.0, beta=1.0).",
            )
            return 0.0, 0.0, 1.0

        # Calculate benchmark return
        initial_benchmark = benchmark_data["Close"].iloc[0]
        final_benchmark = benchmark_data["Close"].iloc[-1]
        if not np.isfinite(initial_benchmark) or initial_benchmark == 0 or not np.isfinite(final_benchmark):
            logger.warning(
                f"Benchmark {benchmark_symbol} has non-finite or zero anchor price; using neutral defaults.",
            )
            return 0.0, 0.0, 1.0
        benchmark_return = ((final_benchmark - initial_benchmark) / initial_benchmark) * 100

        # Calculate alpha and beta (simplified calculation)
        # This is a basic implementation - more sophisticated methods could be used
        portfolio_returns = []
        benchmark_returns = []

        portfolio_dates = sorted(portfolio_values.keys())

        for i in range(1, len(portfolio_dates)):
            date = portfolio_dates[i]
            prev_date = portfolio_dates[i - 1]

            # Portfolio return — guard against zero-or-non-finite previous value.
            # Without this, a flat-zero portfolio_value at prev_date raises
            # ZeroDivisionError or yields NaN that contaminates the
            # benchmark-vs-portfolio covariance below. (CodeRabbit follow-up.)
            prev_value = portfolio_values[prev_date]
            if not np.isfinite(prev_value) or prev_value == 0:
                continue
            port_return = (portfolio_values[date] - prev_value) / prev_value
            if not np.isfinite(port_return):
                continue
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
            except (ValueError, TypeError, KeyError, IndexError) as e:
                logger.warning(f"Failed to calculate benchmark return for date {date}: {e}")
                benchmark_returns.append(0.0)

        if len(portfolio_returns) > 1 and len(benchmark_returns) > 1:
            # Calculate beta using covariance
            portfolio_returns_arr = np.array(portfolio_returns)
            benchmark_returns_arr = np.array(benchmark_returns)

            covariance = np.cov(portfolio_returns_arr, benchmark_returns_arr)[0, 1]
            benchmark_variance = np.var(benchmark_returns_arr)

            beta = covariance / benchmark_variance if benchmark_variance != 0 else 1.0

            # Calculate alpha
            portfolio_mean_return = np.mean(portfolio_returns_arr)
            benchmark_mean_return = np.mean(benchmark_returns_arr)
            risk_free_daily = self.config.risk_free_rate / 252  # Daily risk-free rate

            alpha = (portfolio_mean_return - risk_free_daily) - beta * (benchmark_mean_return - risk_free_daily)
            alpha = alpha * 252 * 100  # Annualize and convert to percentage
        else:
            alpha = 0.0
            beta = 1.0

        return benchmark_return, alpha, beta

    def calculate_sortino_ratio(self, portfolio_values: list[tuple[str, float]], risk_free_rate: float = 0.02) -> float:
        """Calculate Sortino Ratio (return / downside deviation)."""
        if len(portfolio_values) < 2:
            return 0.0

        values = [value for _, value in portfolio_values]
        returns = np.diff(values) / values[:-1]

        if len(returns) == 0:
            return 0.0

        # Calculate excess returns
        daily_rf_rate = risk_free_rate / 252
        excess_returns = returns - daily_rf_rate

        # Calculate downside deviation (only negative returns)
        downside_returns = excess_returns[excess_returns < 0]
        if len(downside_returns) == 0:
            return float("inf")  # No downside risk

        downside_deviation = np.std(downside_returns)
        if downside_deviation == 0:
            return float("inf")

        # Annualized Sortino ratio
        mean_excess_return = np.mean(excess_returns)
        return float((mean_excess_return / downside_deviation) * np.sqrt(252))

    def plot_results(self, cerebro: bt.Cerebro, save_path: str | None = None) -> None:
        """
        Plot backtesting results.

        Args:
            cerebro: Backtrader Cerebro instance
            save_path: Optional path to save the plot

        """
        if cerebro is None:
            self.logger.warning("No backtest results to plot")
            return

        try:
            if save_path:
                cerebro.plot(savefig=save_path)
            else:
                cerebro.plot()
        except Exception as e:
            self.logger.error(f"Error plotting results: {e}")
