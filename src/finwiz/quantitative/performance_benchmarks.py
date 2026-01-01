"""
Performance Benchmarking and Comparison.

This module provides benchmarking functionality including portfolio optimization,
efficient frontier calculations, and performance comparison against benchmarks.
"""

import warnings
from typing import Any

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

# Portfolio optimization imports
try:
    from pypfopt import (  # pypfopt has no official type stubs
        EfficientFrontier,
        expected_returns,
        risk_models,
    )
    from pypfopt.discrete_allocation import (  # pypfopt has no official type stubs
        DiscreteAllocation,
        get_latest_prices,
    )
    from pypfopt.objective_functions import L2_reg  # pypfopt has no official type stubs

    PYPFOPT_AVAILABLE = True
except ImportError:
    PYPFOPT_AVAILABLE = False
    warnings.warn("PyPortfolioOpt not available. Portfolio optimization features will be disabled.")

# Optional visualization imports
try:
    import plotly.graph_objects as go  # plotly has no official type stubs
    from plotly.subplots import make_subplots  # plotly has no official type stubs

    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    warnings.warn("Plotly not available. Visualization features will be disabled.")

from finwiz.quantitative.config import BacktestConfig
from finwiz.quantitative.performance_metrics import MetricsCalculator, PerformanceMetrics
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class PortfolioOptimizationResult(BaseModel):
    """Results from portfolio optimization."""

    # Optimization results
    optimal_weights: dict[str, float] = Field(..., description="Optimal portfolio weights")
    expected_return: float = Field(..., description="Expected portfolio return")
    volatility: float = Field(..., description="Portfolio volatility")
    sharpe_ratio: float = Field(..., description="Portfolio Sharpe ratio")

    # Efficient frontier data
    frontier_returns: list[float] = Field(default_factory=list, description="Efficient frontier returns")
    frontier_volatilities: list[float] = Field(default_factory=list, description="Efficient frontier volatilities")
    frontier_sharpe_ratios: list[float] = Field(default_factory=list, description="Efficient frontier Sharpe ratios")

    # Discrete allocation (if applicable)
    discrete_allocation: dict[str, int] | None = Field(None, description="Discrete share allocation")
    leftover_funds: float | None = Field(None, description="Leftover funds after discrete allocation")

    # Performance metrics
    performance_metrics: PerformanceMetrics | None = Field(None, description="Portfolio performance metrics")


class PerformanceReport(BaseModel):
    """Comprehensive performance analysis report."""

    # Strategy performance
    strategy_metrics: PerformanceMetrics = Field(..., description="Strategy performance metrics")
    benchmark_metrics: PerformanceMetrics | None = Field(None, description="Benchmark performance metrics")

    # Relative performance
    relative_performance: dict[str, float] | None = Field(None, description="Relative performance vs benchmark")

    # Visualization data
    equity_curve_data: dict[str, list] = Field(default_factory=dict, description="Equity curve visualization data")
    drawdown_data: dict[str, list] = Field(default_factory=dict, description="Drawdown visualization data")
    returns_distribution_data: dict[str, list] = Field(default_factory=dict, description="Returns distribution data")

    # Portfolio optimization (if applicable)
    optimization_result: PortfolioOptimizationResult | None = Field(None, description="Portfolio optimization results")

    # Analysis metadata
    strategy_name: str = Field(default="Strategy", description="Name of the strategy")
    benchmark_name: str | None = Field(None, description="Name of the benchmark")
    analysis_period: str = Field(..., description="Analysis period")
    total_observations: int = Field(..., description="Total number of observations")


class BenchmarkAnalyzer:
    """
    Benchmarking and portfolio optimization analyzer.

    This class provides methods for portfolio optimization, efficient frontier
    calculations, and performance comparison against benchmarks.
    """

    def __init__(self, config: BacktestConfig | None = None) -> None:
        """
        Initialize benchmark analyzer.

        Args:
            config: Optional backtest configuration

        """
        self.config = config
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")
        self.metrics_calculator = MetricsCalculator()

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

        Raises:
            ValueError: If PyPortfolioOpt is not available or invalid parameters

        """
        if not PYPFOPT_AVAILABLE:
            raise ValueError("PyPortfolioOpt is not available. Please install it to use portfolio optimization features.")

        if len(price_data.columns) < 2:
            raise ValueError("At least 2 assets are required for portfolio optimization")

        try:
            # Calculate expected returns and covariance matrix
            mu = expected_returns.mean_historical_return(price_data)
            S = risk_models.sample_cov(price_data)

            # Create efficient frontier
            ef = EfficientFrontier(mu, S, weight_bounds=weight_bounds)

            # Add L2 regularization
            ef.add_objective(L2_reg, gamma=l2_gamma)

            # Optimize based on method
            if optimization_method == "max_sharpe":
                weights = ef.max_sharpe()
            elif optimization_method == "min_volatility":
                weights = ef.min_volatility()
            elif optimization_method == "efficient_return":
                if target_return is None:
                    raise ValueError("target_return must be specified for 'efficient_return' method")
                weights = ef.efficient_return(target_return)
            elif optimization_method == "efficient_risk":
                if target_volatility is None:
                    raise ValueError("target_volatility must be specified for 'efficient_risk' method")
                weights = ef.efficient_risk(target_volatility)
            else:
                raise ValueError(f"Unknown optimization method: {optimization_method}")

            # Get portfolio performance
            expected_return, volatility, sharpe_ratio = ef.portfolio_performance(verbose=False)

            # Generate efficient frontier
            frontier_returns, frontier_volatilities, frontier_sharpe = self.generate_efficient_frontier(mu, S, weight_bounds)

            # Discrete allocation if portfolio value is provided
            discrete_allocation = None
            leftover_funds = None

            if total_portfolio_value is not None:
                latest_prices = get_latest_prices(price_data)
                da = DiscreteAllocation(weights, latest_prices, total_portfolio_value=total_portfolio_value)
                discrete_allocation, leftover_funds = da.lp_portfolio()

            return PortfolioOptimizationResult(
                optimal_weights=weights,
                expected_return=expected_return,
                volatility=volatility,
                sharpe_ratio=sharpe_ratio,
                frontier_returns=frontier_returns,
                frontier_volatilities=frontier_volatilities,
                frontier_sharpe_ratios=frontier_sharpe,
                discrete_allocation=discrete_allocation,
                leftover_funds=leftover_funds,
            )

        except Exception as e:
            self.logger.error(f"Portfolio optimization failed: {e}")
            raise

    def generate_efficient_frontier(self, mu: pd.Series, S: pd.DataFrame, weight_bounds: tuple[float, float], n_points: int = 100) -> tuple[list[float], list[float], list[float]]:
        """
        Generate efficient frontier data.

        Args:
            mu: Expected returns
            S: Covariance matrix
            weight_bounds: Weight bounds for optimization
            n_points: Number of points on the frontier

        Returns:
            Tuple of (returns, volatilities, sharpe_ratios)

        """
        if not PYPFOPT_AVAILABLE:
            return [], [], []

        try:
            # Generate target returns
            min_ret = mu.min()
            max_ret = mu.max()
            target_returns = np.linspace(min_ret, max_ret, n_points)

            frontier_returns = []
            frontier_volatilities = []
            frontier_sharpe = []

            for target_ret in target_returns:
                try:
                    ef = EfficientFrontier(mu, S, weight_bounds=weight_bounds)
                    ef.efficient_return(target_ret)
                    ret, vol, sharpe = ef.portfolio_performance(verbose=False)

                    frontier_returns.append(ret)
                    frontier_volatilities.append(vol)
                    frontier_sharpe.append(sharpe)

                except Exception:
                    # Skip points that can't be optimized
                    continue

            return frontier_returns, frontier_volatilities, frontier_sharpe

        except Exception as e:
            self.logger.error(f"Efficient frontier generation failed: {e}")
            return [], [], []

    def generate_performance_visualization(self, performance_report: PerformanceReport, save_path: str | None = None) -> Any | None:
        """
        Generate comprehensive performance visualization.

        Args:
            performance_report: Performance report to visualize
            save_path: Optional path to save the visualization

        Returns:
            Plotly figure object or None if Plotly is not available

        """
        if not PLOTLY_AVAILABLE:
            self.logger.warning("Plotly not available. Cannot generate visualization.")
            return None

        try:
            # Create subplots
            fig = make_subplots(
                rows=2,
                cols=2,
                subplot_titles=("Equity Curve", "Drawdown", "Returns Distribution", "Performance Metrics"),
                specs=[[{"secondary_y": False}, {"secondary_y": False}], [{"secondary_y": False}, {"type": "table"}]],
            )

            # Equity curve
            equity_data = performance_report.equity_curve_data
            if equity_data and "dates" in equity_data and "strategy_equity" in equity_data:
                fig.add_trace(
                    go.Scatter(
                        x=equity_data["dates"],
                        y=equity_data["strategy_equity"],
                        name="Strategy",
                        line=dict(color="blue"),
                    ),
                    row=1,
                    col=1,
                )

                if "benchmark_equity" in equity_data:
                    fig.add_trace(
                        go.Scatter(
                            x=equity_data["dates"],
                            y=equity_data["benchmark_equity"],
                            name="Benchmark",
                            line=dict(color="red", dash="dash"),
                        ),
                        row=1,
                        col=1,
                    )

            # Drawdown
            drawdown_data = performance_report.drawdown_data
            if drawdown_data and "dates" in drawdown_data and "drawdown" in drawdown_data:
                fig.add_trace(
                    go.Scatter(
                        x=drawdown_data["dates"],
                        y=drawdown_data["drawdown"],
                        name="Drawdown",
                        fill="tozeroy",
                        line=dict(color="red"),
                    ),
                    row=1,
                    col=2,
                )

            # Returns distribution
            returns_data = performance_report.returns_distribution_data
            if returns_data and "strategy_returns" in returns_data:
                fig.add_trace(
                    go.Histogram(
                        x=returns_data["strategy_returns"],
                        name="Strategy Returns",
                        opacity=0.7,
                        nbinsx=50,
                    ),
                    row=2,
                    col=1,
                )

                if "benchmark_returns" in returns_data:
                    fig.add_trace(
                        go.Histogram(
                            x=returns_data["benchmark_returns"],
                            name="Benchmark Returns",
                            opacity=0.7,
                            nbinsx=50,
                        ),
                        row=2,
                        col=1,
                    )

            # Performance metrics table
            metrics = performance_report.strategy_metrics
            metrics_data = [
                ["Total Return", f"{metrics.total_return:.2%}"],
                ["Annualized Return", f"{metrics.annualized_return:.2%}"],
                ["Volatility", f"{metrics.volatility:.2%}"],
                ["Sharpe Ratio", f"{metrics.sharpe_ratio:.2f}"],
                ["Max Drawdown", f"{metrics.max_drawdown:.2%}"],
                ["Calmar Ratio", f"{metrics.calmar_ratio:.2f}"],
            ]

            fig.add_trace(
                go.Table(
                    header=dict(values=["Metric", "Value"], fill_color="lightblue"),
                    cells=dict(values=list(zip(*metrics_data)), fill_color="white"),
                ),
                row=2,
                col=2,
            )

            # Update layout
            fig.update_layout(
                title="Performance Analysis Report",
                height=800,
                showlegend=True,
            )

            # Save if path provided
            if save_path:
                fig.write_html(save_path)
                self.logger.info(f"Performance visualization saved to {save_path}")

            return fig

        except Exception as e:
            self.logger.error(f"Visualization generation failed: {e}")
            return None

    def generate_optimization_visualization(self, optimization_result: PortfolioOptimizationResult, save_path: str | None = None) -> Any | None:
        """
        Generate portfolio optimization visualization.

        Args:
            optimization_result: Portfolio optimization results
            save_path: Optional path to save the visualization

        Returns:
            Plotly figure object or None if Plotly is not available

        """
        if not PLOTLY_AVAILABLE:
            self.logger.warning("Plotly not available. Cannot generate visualization.")
            return None

        try:
            # Create subplots
            fig = make_subplots(
                rows=1,
                cols=2,
                subplot_titles=("Efficient Frontier", "Portfolio Weights"),
                specs=[[{"secondary_y": False}, {"type": "pie"}]],
            )

            # Efficient frontier
            if optimization_result.frontier_returns and optimization_result.frontier_volatilities:
                fig.add_trace(
                    go.Scatter(
                        x=optimization_result.frontier_volatilities,
                        y=optimization_result.frontier_returns,
                        mode="lines",
                        name="Efficient Frontier",
                        line=dict(color="blue"),
                    ),
                    row=1,
                    col=1,
                )

                # Optimal portfolio point
                fig.add_trace(
                    go.Scatter(
                        x=[optimization_result.volatility],
                        y=[optimization_result.expected_return],
                        mode="markers",
                        name="Optimal Portfolio",
                        marker=dict(color="red", size=10),
                    ),
                    row=1,
                    col=1,
                )

            # Portfolio weights pie chart
            weights = optimization_result.optimal_weights
            if weights:
                # Filter out very small weights for cleaner visualization
                filtered_weights = {k: v for k, v in weights.items() if v > 0.01}

                fig.add_trace(
                    go.Pie(
                        labels=list(filtered_weights.keys()),
                        values=list(filtered_weights.values()),
                        name="Portfolio Weights",
                    ),
                    row=1,
                    col=2,
                )

            # Update layout
            fig.update_layout(
                title="Portfolio Optimization Results",
                height=500,
                showlegend=True,
            )

            # Update x and y axis labels for efficient frontier
            fig.update_xaxes(title_text="Volatility", row=1, col=1)
            fig.update_yaxes(title_text="Expected Return", row=1, col=1)

            # Save if path provided
            if save_path:
                fig.write_html(save_path)
                self.logger.info(f"Optimization visualization saved to {save_path}")

            return fig

        except Exception as e:
            self.logger.error(f"Optimization visualization generation failed: {e}")
            return None
