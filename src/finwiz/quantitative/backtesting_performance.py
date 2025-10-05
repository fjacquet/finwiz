"""
Performance analysis utilities for backtesting.

This module contains performance metrics calculation, benchmark comparison,
and risk analysis functions for backtesting results.
"""

from datetime import datetime
from typing import Any

import backtrader as bt  # type: ignore[import-untyped]  # backtrader has no official type stubs
import numpy as np

from finwiz.quantitative.data import HistoricalDataManager
from finwiz.tools.logger import get_logger

# Import the models from the models module
from .backtesting_models import BacktestResult

logger = get_logger(__name__)


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
        volatility = self.calculate_volatility(strategy_instance.portfolio_values)

        # Portfolio values dictionary
        portfolio_values = {date: value for date, value in strategy_instance.portfolio_values}

        # Benchmark comparison
        benchmark_return = None
        alpha = None
        beta = None

        if benchmark_symbol:
            try:
                benchmark_return, alpha, beta = self.calculate_benchmark_metrics(
                    portfolio_values, benchmark_symbol, start_date, end_date
                )
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
        returns = np.diff(values) / values[:-1]

        if len(returns) == 0:
            return 0.0

        daily_vol = np.std(returns)
        annualized_vol = daily_vol * np.sqrt(252)  # Assuming 252 trading days

        return annualized_vol * 100  # Convert to percentage

    def calculate_var(self, portfolio_values: list[tuple[str, float]], confidence: float) -> float | None:
        """Calculate Value at Risk."""
        if len(portfolio_values) < 2:
            return None

        values = [value for _, value in portfolio_values]
        returns = np.diff(values) / values[:-1]

        if len(returns) == 0:
            return None

        return np.percentile(returns, (1 - confidence) * 100) * 100

    def calculate_cvar(self, portfolio_values: list[tuple[str, float]], confidence: float) -> float | None:
        """Calculate Conditional Value at Risk."""
        var = self.calculate_var(portfolio_values, confidence)
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

    def calculate_benchmark_metrics(
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

    def calculate_information_ratio(self, portfolio_returns: list[float], benchmark_returns: list[float]) -> float:
        """Calculate Information Ratio (active return / tracking error)."""
        if len(portfolio_returns) != len(benchmark_returns) or len(portfolio_returns) < 2:
            return 0.0

        portfolio_returns = np.array(portfolio_returns)
        benchmark_returns = np.array(benchmark_returns)

        active_returns = portfolio_returns - benchmark_returns
        active_return = np.mean(active_returns)
        tracking_error = np.std(active_returns)

        if tracking_error == 0:
            return 0.0

        return (active_return / tracking_error) * np.sqrt(252)  # Annualized

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
        return (mean_excess_return / downside_deviation) * np.sqrt(252)

    def calculate_maximum_drawdown_duration(self, portfolio_values: list[tuple[str, float]]) -> int:
        """Calculate the maximum drawdown duration in days."""
        if len(portfolio_values) < 2:
            return 0

        values = [value for _, value in portfolio_values]
        peak = values[0]
        max_duration = 0
        current_duration = 0

        for value in values[1:]:
            if value > peak:
                peak = value
                current_duration = 0
            else:
                current_duration += 1
                max_duration = max(max_duration, current_duration)

        return max_duration

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
