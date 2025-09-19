"""
Performance analysis and reporting system for FinWiz quantitative analysis.

This module provides comprehensive performance analysis capabilities including:
- Performance metrics calculation (Sharpe ratio, maximum drawdown, returns)
- Portfolio optimization using PyPortfolioOpt for efficient frontier calculations
- Performance visualization and reporting capabilities
- Risk-adjusted return analysis and benchmarking
"""

import warnings
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

# Optional visualization imports
try:
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    warnings.warn("Plotly not available. Visualization features will be disabled.")

# Optional scipy imports
try:
    from scipy import stats

    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    warnings.warn("SciPy not available. Some statistical features may be limited.")

# Portfolio optimization imports
try:
    from pypfopt import EfficientFrontier, expected_returns, risk_models
    from pypfopt.discrete_allocation import DiscreteAllocation, get_latest_prices
    from pypfopt.objective_functions import L2_reg

    PYPFOPT_AVAILABLE = True
except ImportError:
    PYPFOPT_AVAILABLE = False
    warnings.warn("PyPortfolioOpt not available. Portfolio optimization features will be disabled.")

from finwiz.quantitative.config import BacktestConfig, get_backtest_config
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class PerformanceMetrics(BaseModel):
    """Comprehensive performance metrics for a trading strategy or portfolio."""

    # Return metrics
    total_return: float = Field(..., description="Total return over the period")
    annualized_return: float = Field(..., description="Annualized return")
    daily_return_mean: float = Field(..., description="Mean daily return")
    daily_return_std: float = Field(..., description="Standard deviation of daily returns")

    # Risk-adjusted metrics
    sharpe_ratio: float = Field(..., description="Sharpe ratio (risk-adjusted return)")
    sortino_ratio: float = Field(..., description="Sortino ratio (downside risk-adjusted return)")
    calmar_ratio: float = Field(..., description="Calmar ratio (return/max drawdown)")
    information_ratio: float | None = Field(None, description="Information ratio vs benchmark")

    # Risk metrics
    max_drawdown: float = Field(..., description="Maximum drawdown")
    max_drawdown_duration: int = Field(..., description="Maximum drawdown duration in days")
    volatility: float = Field(..., description="Annualized volatility")
    downside_deviation: float = Field(..., description="Downside deviation")
    var_95: float = Field(..., description="Value at Risk (95% confidence)")
    cvar_95: float = Field(..., description="Conditional Value at Risk (95% confidence)")

    # Statistical metrics
    skewness: float = Field(..., description="Skewness of returns")
    kurtosis: float = Field(..., description="Kurtosis of returns")
    beta: float | None = Field(None, description="Beta vs benchmark")
    alpha: float | None = Field(None, description="Alpha vs benchmark")

    # Trade statistics
    win_rate: float | None = Field(None, description="Percentage of winning trades")
    profit_factor: float | None = Field(None, description="Ratio of gross profit to gross loss")
    avg_win: float | None = Field(None, description="Average winning trade")
    avg_loss: float | None = Field(None, description="Average losing trade")

    # Period information
    start_date: datetime = Field(..., description="Start date of analysis period")
    end_date: datetime = Field(..., description="End date of analysis period")
    total_days: int = Field(..., description="Total number of days in analysis")
    trading_days: int = Field(..., description="Number of trading days")

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class PortfolioOptimizationResult(BaseModel):
    """Results from portfolio optimization."""

    # Optimization parameters
    optimization_method: str = Field(..., description="Optimization method used")
    risk_free_rate: float = Field(..., description="Risk-free rate used")
    target_return: float | None = Field(None, description="Target return for optimization")
    target_risk: float | None = Field(None, description="Target risk for optimization")

    # Optimal weights
    weights: dict[str, float] = Field(..., description="Optimal portfolio weights")

    # Expected performance
    expected_annual_return: float = Field(..., description="Expected annual return")
    annual_volatility: float = Field(..., description="Expected annual volatility")
    sharpe_ratio: float = Field(..., description="Expected Sharpe ratio")

    # Efficient frontier data
    efficient_frontier_returns: list[float] = Field(default_factory=list, description="Returns on efficient frontier")
    efficient_frontier_volatilities: list[float] = Field(default_factory=list, description="Volatilities on efficient frontier")
    efficient_frontier_sharpe: list[float] = Field(default_factory=list, description="Sharpe ratios on efficient frontier")

    # Discrete allocation (if applicable)
    discrete_allocation: dict[str, int] | None = Field(None, description="Discrete share allocation")
    leftover_cash: float | None = Field(None, description="Leftover cash after discrete allocation")
    total_portfolio_value: float | None = Field(None, description="Total portfolio value for discrete allocation")


class PerformanceReport(BaseModel):
    """Comprehensive performance analysis report."""

    # Basic information
    strategy_name: str = Field(..., description="Name of the strategy or portfolio")
    benchmark_name: str | None = Field(None, description="Name of the benchmark")
    analysis_date: datetime = Field(default_factory=datetime.now, description="Date of analysis")

    # Performance metrics
    performance_metrics: PerformanceMetrics = Field(..., description="Comprehensive performance metrics")

    # Benchmark comparison (if available)
    benchmark_metrics: PerformanceMetrics | None = Field(None, description="Benchmark performance metrics")
    relative_performance: dict[str, float] | None = Field(None, description="Performance relative to benchmark")

    # Portfolio optimization results (if applicable)
    optimization_result: PortfolioOptimizationResult | None = Field(None, description="Portfolio optimization results")

    # Visualization data
    equity_curve_data: dict[str, list] = Field(default_factory=dict, description="Data for equity curve visualization")
    drawdown_data: dict[str, list] = Field(default_factory=dict, description="Data for drawdown visualization")
    returns_distribution_data: dict[str, list] = Field(default_factory=dict, description="Data for returns distribution")

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class PerformanceAnalyzer:
    """
    Comprehensive performance analysis engine for trading strategies and portfolios.

    Provides calculation of performance metrics, risk analysis, and portfolio optimization
    using industry-standard methodologies and professional-grade libraries.
    """

    def __init__(self, config: BacktestConfig | None = None):
        """
        Initialize performance analyzer.

        Args:
            config: Backtesting configuration with performance parameters

        """
        self.config = config or get_backtest_config()
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")

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
            returns: Series of strategy returns (daily)
            benchmark_returns: Series of benchmark returns (daily, optional)
            trades: DataFrame of individual trades (optional)
            strategy_name: Name of the strategy
            benchmark_name: Name of the benchmark

        Returns:
            Comprehensive performance report

        """
        self.logger.info(f"Analyzing performance for {strategy_name}")

        # Calculate performance metrics
        performance_metrics = self._calculate_performance_metrics(returns, trades)

        # Calculate benchmark metrics if provided
        benchmark_metrics = None
        relative_performance = None
        if benchmark_returns is not None:
            benchmark_metrics = self._calculate_performance_metrics(benchmark_returns)
            relative_performance = self._calculate_relative_performance(performance_metrics, benchmark_metrics)

        # Generate visualization data
        equity_curve_data = self._generate_equity_curve_data(returns, benchmark_returns)
        drawdown_data = self._generate_drawdown_data(returns)
        returns_distribution_data = self._generate_returns_distribution_data(returns, benchmark_returns)

        return PerformanceReport(
            strategy_name=strategy_name,
            benchmark_name=benchmark_name,
            performance_metrics=performance_metrics,
            benchmark_metrics=benchmark_metrics,
            relative_performance=relative_performance,
            equity_curve_data=equity_curve_data,
            drawdown_data=drawdown_data,
            returns_distribution_data=returns_distribution_data,
        )

    def optimize_portfolio(
        self,
        price_data: pd.DataFrame,
        method: str = "max_sharpe",
        target_return: float | None = None,
        target_risk: float | None = None,
        weight_bounds: tuple[float, float] = (0, 1),
        total_portfolio_value: float | None = None,
    ) -> PortfolioOptimizationResult:
        """
        Optimize portfolio using PyPortfolioOpt.

        Args:
            price_data: DataFrame with price data for assets (columns = assets, index = dates)
            method: Optimization method ('max_sharpe', 'min_volatility', 'efficient_return', 'efficient_risk')
            target_return: Target return for 'efficient_return' method
            target_risk: Target risk for 'efficient_risk' method
            weight_bounds: Bounds for asset weights
            total_portfolio_value: Total portfolio value for discrete allocation

        Returns:
            Portfolio optimization results

        Raises:
            RuntimeError: If PyPortfolioOpt is not available
            ValueError: If invalid parameters are provided

        """
        if not PYPFOPT_AVAILABLE:
            raise RuntimeError("PyPortfolioOpt is not available. Install with: pip install PyPortfolioOpt")

        self.logger.info(f"Optimizing portfolio using {method} method")

        # Validate inputs
        if price_data.empty:
            raise ValueError("Price data cannot be empty")

        if method not in ["max_sharpe", "min_volatility", "efficient_return", "efficient_risk"]:
            raise ValueError(f"Invalid optimization method: {method}")

        if method == "efficient_return" and target_return is None:
            raise ValueError("target_return must be specified for 'efficient_return' method")

        if method == "efficient_risk" and target_risk is None:
            raise ValueError("target_risk must be specified for 'efficient_risk' method")

        # Calculate expected returns and covariance matrix
        mu = expected_returns.mean_historical_return(price_data)
        S = risk_models.sample_cov(price_data)

        # Create efficient frontier
        ef = EfficientFrontier(mu, S, weight_bounds=weight_bounds)

        # Add L2 regularization to prevent extreme weights
        ef.add_objective(L2_reg, gamma=0.1)

        # Optimize based on method
        if method == "max_sharpe":
            weights = ef.max_sharpe(risk_free_rate=self.config.risk_free_rate)
        elif method == "min_volatility":
            weights = ef.min_volatility()
        elif method == "efficient_return":
            weights = ef.efficient_return(target_return)
        elif method == "efficient_risk":
            weights = ef.efficient_risk(target_risk)

        # Clean weights (remove tiny weights)
        cleaned_weights = ef.clean_weights()

        # Calculate expected performance
        expected_return, volatility, sharpe = ef.portfolio_performance(risk_free_rate=self.config.risk_free_rate, verbose=False)

        # Generate efficient frontier data
        frontier_returns, frontier_volatilities, frontier_sharpe = self._generate_efficient_frontier(mu, S, weight_bounds)

        # Discrete allocation if portfolio value is provided
        discrete_allocation = None
        leftover_cash = None
        if total_portfolio_value is not None:
            latest_prices = get_latest_prices(price_data)
            da = DiscreteAllocation(cleaned_weights, latest_prices, total_portfolio_value=total_portfolio_value)
            discrete_allocation, leftover_cash = da.lp_portfolio()

        return PortfolioOptimizationResult(
            optimization_method=method,
            risk_free_rate=self.config.risk_free_rate,
            target_return=target_return,
            target_risk=target_risk,
            weights=cleaned_weights,
            expected_annual_return=expected_return,
            annual_volatility=volatility,
            sharpe_ratio=sharpe,
            efficient_frontier_returns=frontier_returns,
            efficient_frontier_volatilities=frontier_volatilities,
            efficient_frontier_sharpe=frontier_sharpe,
            discrete_allocation=discrete_allocation,
            leftover_cash=leftover_cash,
            total_portfolio_value=total_portfolio_value,
        )

    def generate_performance_visualization(self, performance_report: PerformanceReport, save_path: str | None = None) -> Any | None:
        """
        Generate comprehensive performance visualization.

        Args:
            performance_report: Performance analysis report
            save_path: Optional path to save the visualization

        Returns:
            Plotly figure with performance visualizations (None if Plotly not available)

        Raises:
            RuntimeError: If Plotly is not available

        """
        if not PLOTLY_AVAILABLE:
            raise RuntimeError("Plotly is not available. Install with: pip install plotly")

        self.logger.info("Generating performance visualization")

        # Create subplots
        fig = make_subplots(
            rows=2,
            cols=2,
            subplot_titles=("Equity Curve", "Drawdown", "Returns Distribution", "Rolling Sharpe Ratio"),
            specs=[[{"secondary_y": False}, {"secondary_y": False}], [{"secondary_y": False}, {"secondary_y": False}]],
        )

        # Equity curve
        equity_data = performance_report.equity_curve_data
        if "dates" in equity_data and "strategy_equity" in equity_data:
            fig.add_trace(
                go.Scatter(
                    x=equity_data["dates"],
                    y=equity_data["strategy_equity"],
                    name=performance_report.strategy_name,
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
                        name=performance_report.benchmark_name or "Benchmark",
                        line=dict(color="red", dash="dash"),
                    ),
                    row=1,
                    col=1,
                )

        # Drawdown
        drawdown_data = performance_report.drawdown_data
        if "dates" in drawdown_data and "drawdown" in drawdown_data:
            fig.add_trace(
                go.Scatter(
                    x=drawdown_data["dates"],
                    y=drawdown_data["drawdown"],
                    name="Drawdown",
                    fill="tonexty",
                    fillcolor="rgba(255, 0, 0, 0.3)",
                    line=dict(color="red"),
                ),
                row=1,
                col=2,
            )

        # Returns distribution
        returns_data = performance_report.returns_distribution_data
        if "strategy_returns" in returns_data:
            fig.add_trace(
                go.Histogram(x=returns_data["strategy_returns"], name="Strategy Returns", opacity=0.7, nbinsx=50), row=2, col=1
            )

            if "benchmark_returns" in returns_data:
                fig.add_trace(
                    go.Histogram(x=returns_data["benchmark_returns"], name="Benchmark Returns", opacity=0.7, nbinsx=50),
                    row=2,
                    col=1,
                )

        # Rolling Sharpe ratio
        if "dates" in equity_data and "rolling_sharpe" in equity_data:
            fig.add_trace(
                go.Scatter(
                    x=equity_data["dates"], y=equity_data["rolling_sharpe"], name="Rolling Sharpe", line=dict(color="green")
                ),
                row=2,
                col=2,
            )

        # Update layout
        fig.update_layout(title=f"Performance Analysis: {performance_report.strategy_name}", height=800, showlegend=True)

        # Update axes labels
        fig.update_xaxes(title_text="Date", row=1, col=1)
        fig.update_yaxes(title_text="Cumulative Return", row=1, col=1)
        fig.update_xaxes(title_text="Date", row=1, col=2)
        fig.update_yaxes(title_text="Drawdown (%)", row=1, col=2)
        fig.update_xaxes(title_text="Daily Return", row=2, col=1)
        fig.update_yaxes(title_text="Frequency", row=2, col=1)
        fig.update_xaxes(title_text="Date", row=2, col=2)
        fig.update_yaxes(title_text="Rolling Sharpe Ratio", row=2, col=2)

        if save_path:
            fig.write_html(save_path)
            self.logger.info(f"Performance visualization saved to {save_path}")

        return fig

    def generate_optimization_visualization(
        self, optimization_result: PortfolioOptimizationResult, save_path: str | None = None
    ) -> Any | None:
        """
        Generate portfolio optimization visualization.

        Args:
            optimization_result: Portfolio optimization results
            save_path: Optional path to save the visualization

        Returns:
            Plotly figure with optimization visualizations (None if Plotly not available)

        Raises:
            RuntimeError: If Plotly is not available

        """
        if not PLOTLY_AVAILABLE:
            raise RuntimeError("Plotly is not available. Install with: pip install plotly")

        self.logger.info("Generating portfolio optimization visualization")

        # Create subplots
        fig = make_subplots(
            rows=1,
            cols=2,
            subplot_titles=("Efficient Frontier", "Portfolio Weights"),
            specs=[[{"secondary_y": False}, {"secondary_y": False}]],
        )

        # Efficient frontier
        if optimization_result.efficient_frontier_returns:
            fig.add_trace(
                go.Scatter(
                    x=optimization_result.efficient_frontier_volatilities,
                    y=optimization_result.efficient_frontier_returns,
                    mode="lines",
                    name="Efficient Frontier",
                    line=dict(color="blue"),
                ),
                row=1,
                col=1,
            )

            # Highlight optimal portfolio
            fig.add_trace(
                go.Scatter(
                    x=[optimization_result.annual_volatility],
                    y=[optimization_result.expected_annual_return],
                    mode="markers",
                    name="Optimal Portfolio",
                    marker=dict(color="red", size=10, symbol="star"),
                ),
                row=1,
                col=1,
            )

        # Portfolio weights
        assets = list(optimization_result.weights.keys())
        weights = list(optimization_result.weights.values())

        fig.add_trace(go.Bar(x=assets, y=weights, name="Portfolio Weights", marker=dict(color="lightblue")), row=1, col=2)

        # Update layout
        fig.update_layout(title=f"Portfolio Optimization: {optimization_result.optimization_method}", height=400, showlegend=True)

        # Update axes labels
        fig.update_xaxes(title_text="Volatility", row=1, col=1)
        fig.update_yaxes(title_text="Expected Return", row=1, col=1)
        fig.update_xaxes(title_text="Assets", row=1, col=2)
        fig.update_yaxes(title_text="Weight", row=1, col=2)

        if save_path:
            fig.write_html(save_path)
            self.logger.info(f"Optimization visualization saved to {save_path}")

        return fig

    def _calculate_performance_metrics(self, returns: pd.Series, trades: pd.DataFrame | None = None) -> PerformanceMetrics:
        """Calculate comprehensive performance metrics."""
        # Basic return statistics
        total_return = (1 + returns).prod() - 1
        annualized_return = (1 + returns.mean()) ** 252 - 1
        daily_return_mean = returns.mean()
        daily_return_std = returns.std()

        # Risk metrics
        volatility = returns.std() * np.sqrt(252)
        max_drawdown, max_dd_duration = self._calculate_max_drawdown(returns)
        downside_deviation = self._calculate_downside_deviation(returns)
        var_95 = returns.quantile(0.05)
        cvar_95 = returns[returns <= var_95].mean()

        # Risk-adjusted metrics
        sharpe_ratio = (annualized_return - self.config.risk_free_rate) / volatility if volatility > 0 else 0
        sortino_ratio = (annualized_return - self.config.risk_free_rate) / downside_deviation if downside_deviation > 0 else 0
        calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0

        # Statistical metrics
        skewness = returns.skew()
        kurtosis = returns.kurtosis()

        # Trade statistics (if trades provided)
        win_rate = None
        profit_factor = None
        avg_win = None
        avg_loss = None

        if trades is not None and not trades.empty:
            if "pnl" in trades.columns:
                winning_trades = trades[trades["pnl"] > 0]
                losing_trades = trades[trades["pnl"] < 0]

                win_rate = len(winning_trades) / len(trades) if len(trades) > 0 else 0

                if len(winning_trades) > 0 and len(losing_trades) > 0:
                    gross_profit = winning_trades["pnl"].sum()
                    gross_loss = abs(losing_trades["pnl"].sum())
                    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")
                    avg_win = winning_trades["pnl"].mean()
                    avg_loss = losing_trades["pnl"].mean()

        # Period information
        start_date = returns.index[0] if len(returns) > 0 else datetime.now()
        end_date = returns.index[-1] if len(returns) > 0 else datetime.now()
        total_days = (end_date - start_date).days
        trading_days = len(returns)

        return PerformanceMetrics(
            total_return=total_return,
            annualized_return=annualized_return,
            daily_return_mean=daily_return_mean,
            daily_return_std=daily_return_std,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            calmar_ratio=calmar_ratio,
            max_drawdown=max_drawdown,
            max_drawdown_duration=max_dd_duration,
            volatility=volatility,
            downside_deviation=downside_deviation,
            var_95=var_95,
            cvar_95=cvar_95,
            skewness=skewness,
            kurtosis=kurtosis,
            win_rate=win_rate,
            profit_factor=profit_factor,
            avg_win=avg_win,
            avg_loss=avg_loss,
            start_date=start_date,
            end_date=end_date,
            total_days=total_days,
            trading_days=trading_days,
        )

    def _calculate_max_drawdown(self, returns: pd.Series) -> tuple[float, int]:
        """Calculate maximum drawdown and its duration."""
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max

        max_drawdown = drawdown.min()

        # Calculate drawdown duration
        drawdown_start = None
        max_duration = 0
        current_duration = 0

        for i, dd in enumerate(drawdown):
            if dd < 0:
                if drawdown_start is None:
                    drawdown_start = i
                current_duration = i - drawdown_start + 1
            else:
                if current_duration > max_duration:
                    max_duration = current_duration
                drawdown_start = None
                current_duration = 0

        # Check if we ended in a drawdown
        if current_duration > max_duration:
            max_duration = current_duration

        return max_drawdown, max_duration

    def _calculate_downside_deviation(self, returns: pd.Series, target_return: float = 0) -> float:
        """Calculate downside deviation."""
        downside_returns = returns[returns < target_return]
        if len(downside_returns) == 0:
            return 0
        return np.sqrt(((downside_returns - target_return) ** 2).mean()) * np.sqrt(252)

    def _calculate_relative_performance(
        self, strategy_metrics: PerformanceMetrics, benchmark_metrics: PerformanceMetrics
    ) -> dict[str, float]:
        """Calculate performance relative to benchmark."""
        return {
            "excess_return": strategy_metrics.annualized_return - benchmark_metrics.annualized_return,
            "excess_volatility": strategy_metrics.volatility - benchmark_metrics.volatility,
            "relative_sharpe": strategy_metrics.sharpe_ratio - benchmark_metrics.sharpe_ratio,
            "relative_max_drawdown": strategy_metrics.max_drawdown - benchmark_metrics.max_drawdown,
            "tracking_error": abs(strategy_metrics.volatility - benchmark_metrics.volatility),
            "information_ratio": (strategy_metrics.annualized_return - benchmark_metrics.annualized_return)
            / abs(strategy_metrics.volatility - benchmark_metrics.volatility)
            if abs(strategy_metrics.volatility - benchmark_metrics.volatility) > 0
            else 0,
        }

    def _generate_efficient_frontier(
        self, mu: pd.Series, S: pd.DataFrame, weight_bounds: tuple[float, float], n_points: int = 100
    ) -> tuple[list[float], list[float], list[float]]:
        """Generate efficient frontier data points."""
        if not PYPFOPT_AVAILABLE:
            return [], [], []

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
                ret, vol, sharpe = ef.portfolio_performance(risk_free_rate=self.config.risk_free_rate, verbose=False)

                frontier_returns.append(ret)
                frontier_volatilities.append(vol)
                frontier_sharpe.append(sharpe)
            except:
                continue

        return frontier_returns, frontier_volatilities, frontier_sharpe

    def _generate_equity_curve_data(self, returns: pd.Series, benchmark_returns: pd.Series | None = None) -> dict[str, list]:
        """Generate data for equity curve visualization."""
        cumulative_returns = (1 + returns).cumprod()

        data = {"dates": returns.index.tolist(), "strategy_equity": cumulative_returns.tolist()}

        if benchmark_returns is not None:
            benchmark_cumulative = (1 + benchmark_returns).cumprod()
            data["benchmark_equity"] = benchmark_cumulative.tolist()

        # Calculate rolling Sharpe ratio
        rolling_window = min(252, len(returns) // 4)  # 1 year or 1/4 of data
        if rolling_window >= 30:
            rolling_sharpe = returns.rolling(rolling_window).apply(
                lambda x: (x.mean() * 252 - self.config.risk_free_rate) / (x.std() * np.sqrt(252)) if x.std() > 0 else 0
            )
            data["rolling_sharpe"] = rolling_sharpe.tolist()

        return data

    def _generate_drawdown_data(self, returns: pd.Series) -> dict[str, list]:
        """Generate data for drawdown visualization."""
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max * 100  # Convert to percentage

        return {"dates": returns.index.tolist(), "drawdown": drawdown.tolist()}

    def _generate_returns_distribution_data(
        self, returns: pd.Series, benchmark_returns: pd.Series | None = None
    ) -> dict[str, list]:
        """Generate data for returns distribution visualization."""
        data = {"strategy_returns": returns.tolist()}

        if benchmark_returns is not None:
            data["benchmark_returns"] = benchmark_returns.tolist()

        return data


# Factory function for easy instantiation
def get_performance_analyzer(config: BacktestConfig | None = None) -> PerformanceAnalyzer:
    """
    Get a performance analyzer instance.

    Args:
        config: Optional backtesting configuration

    Returns:
        PerformanceAnalyzer instance

    """
    return PerformanceAnalyzer(config)
