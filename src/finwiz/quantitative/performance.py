"""
Performance analysis and reporting system for FinWiz quantitative analysis.

This module provides comprehensive performance analysis capabilities including:
- Performance metrics calculation (Sharpe ratio, maximum drawdown, returns)
- Portfolio optimization using PyPortfolioOpt for efficient frontier calculations
- Performance visualization and reporting capabilities
- Risk-adjusted return analysis and benchmarking
"""

from typing import Any

import pandas as pd

from finwiz.quantitative.config import BacktestConfig, get_backtest_config
from finwiz.quantitative.performance_benchmarks import (
    BenchmarkAnalyzer,
    PerformanceReport,
    PortfolioOptimizationResult,
)
from finwiz.quantitative.performance_metrics import MetricsCalculator
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class PerformanceAnalyzer:
    """
    Comprehensive performance analysis engine for trading strategies and portfolios.

    Provides calculation of performance metrics, risk analysis, and portfolio optimization
    using industry-standard methodologies and professional-grade libraries.
    """

    def __init__(self, config: BacktestConfig | None = None) -> None:
        """
        Initialize performance analyzer.

        Args:
            config: Backtesting configuration with performance parameters

        """
        self.config = config or get_backtest_config()
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")

        # Initialize component analyzers
        self.metrics_calculator = MetricsCalculator()
        self.benchmark_analyzer = BenchmarkAnalyzer(config)

    def analyze_performance(
        self,
        returns: pd.Series,
        benchmark_returns: pd.Series | None = None,
        trades: pd.DataFrame | None = None,
        strategy_name: str = "Strategy",
        benchmark_name: str | None = None,
    ) -> PerformanceReport:
        """
        Perform comprehensive performance analysis.

        Args:
            returns: Series of strategy returns
            benchmark_returns: Optional benchmark returns for comparison
            trades: Optional DataFrame with trade information
            strategy_name: Name of the strategy
            benchmark_name: Name of the benchmark

        Returns:
            PerformanceReport with comprehensive analysis results

        """
        self.logger.info(f"Starting performance analysis for {strategy_name}")

        try:
            # Calculate strategy metrics
            strategy_metrics = self.metrics_calculator.calculate_performance_metrics(returns, trades)

            # Calculate benchmark metrics if provided
            benchmark_metrics = None
            relative_performance = None
            if benchmark_returns is not None:
                benchmark_metrics = self.metrics_calculator.calculate_performance_metrics(benchmark_returns)
                relative_performance = self.metrics_calculator.calculate_relative_performance(strategy_metrics, benchmark_metrics)

            # Generate visualization data
            equity_curve_data = self.metrics_calculator.generate_equity_curve_data(returns, benchmark_returns)
            drawdown_data = self.metrics_calculator.generate_drawdown_data(returns)
            returns_distribution_data = self.metrics_calculator.generate_returns_distribution_data(returns, benchmark_returns)

            # Create performance report
            report = PerformanceReport(
                strategy_metrics=strategy_metrics,
                benchmark_metrics=benchmark_metrics,
                relative_performance=relative_performance,
                equity_curve_data=equity_curve_data,
                drawdown_data=drawdown_data,
                returns_distribution_data=returns_distribution_data,
                analysis_period=f"{returns.index[0]} to {returns.index[-1]}",
                total_observations=len(returns),
            )

            self.logger.info(f"Performance analysis completed for {strategy_name}")
            return report

        except Exception as e:
            self.logger.error(f"Performance analysis failed for {strategy_name}: {e}")
            raise

    def optimize_portfolio(
        self,
        price_data: pd.DataFrame,
        optimization_method: str = "max_sharpe",
        weight_bounds: tuple[float, float] = (0.0, 1.0),
        target_return: float | None = None,
        target_volatility: float | None = None,
        l2_gamma: float = 0.1,
        total_portfolio_value: float | None = None,
    ) -> PortfolioOptimizationResult:
        """
        Optimize portfolio allocation using PyPortfolioOpt.

        Args:
            price_data: DataFrame with price data for assets
            optimization_method: Optimization method ('max_sharpe', 'min_volatility', 'efficient_return', 'efficient_risk')
            weight_bounds: Tuple of (min_weight, max_weight) for each asset
            target_return: Target return for 'efficient_return' method
            target_volatility: Target volatility for 'efficient_risk' method
            l2_gamma: L2 regularization parameter
            total_portfolio_value: Total portfolio value for discrete allocation

        Returns:
            PortfolioOptimizationResult with optimization results

        """
        return self.benchmark_analyzer.optimize_portfolio(
            price_data=price_data,
            optimization_method=optimization_method,
            weight_bounds=weight_bounds,
            target_return=target_return,
            target_volatility=target_volatility,
            l2_gamma=l2_gamma,
            total_portfolio_value=total_portfolio_value,
        )

    def generate_performance_visualization(self, performance_report: PerformanceReport, save_path: str | None = None) -> Any | None:
        """
        Generate comprehensive performance visualization.

        Args:
            performance_report: Performance report to visualize
            save_path: Optional path to save the visualization

        Returns:
            Plotly figure object or None if Plotly is not available

        """
        return self.benchmark_analyzer.generate_performance_visualization(performance_report, save_path)

    def generate_optimization_visualization(
        self, optimization_result: PortfolioOptimizationResult, save_path: str | None = None
    ) -> Any | None:
        """
        Generate portfolio optimization visualization.

        Args:
            optimization_result: Portfolio optimization results
            save_path: Optional path to save the visualization

        Returns:
            Plotly figure object or None if Plotly is not available

        """
        return self.benchmark_analyzer.generate_optimization_visualization(optimization_result, save_path)


# Factory function for easy instantiation
def get_performance_analyzer(config: BacktestConfig | None = None) -> PerformanceAnalyzer:
    """
    Get a performance analyzer instance.

    Args:
        config: Optional backtest configuration

    Returns:
        PerformanceAnalyzer instance

    """
    return PerformanceAnalyzer(config)
