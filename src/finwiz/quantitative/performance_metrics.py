"""
Performance Metrics Calculation.

This module provides performance metrics calculation functionality including
Sharpe ratio, maximum drawdown, returns analysis, and other statistical measures.
"""

import warnings

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

# Optional scipy imports
try:
    import importlib.util

    SCIPY_AVAILABLE = importlib.util.find_spec("scipy") is not None
except ImportError:
    SCIPY_AVAILABLE = False
    warnings.warn("SciPy not available. Some statistical features may be limited.")

from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class PerformanceMetrics(BaseModel):
    """Comprehensive performance metrics for a trading strategy or portfolio."""

    # Return metrics
    total_return: float = Field(..., description="Total return over the period")
    annualized_return: float = Field(..., description="Annualized return")
    volatility: float = Field(..., description="Annualized volatility")
    sharpe_ratio: float = Field(..., description="Sharpe ratio")
    sortino_ratio: float = Field(..., description="Sortino ratio")

    # Risk metrics
    max_drawdown: float = Field(..., description="Maximum drawdown")
    max_drawdown_duration: int = Field(..., description="Maximum drawdown duration in days")
    downside_deviation: float = Field(..., description="Downside deviation")
    var_95: float = Field(..., description="Value at Risk (95%)")
    cvar_95: float = Field(..., description="Conditional Value at Risk (95%)")

    # Trade metrics (optional)
    win_rate: float | None = Field(None, description="Percentage of winning trades")
    profit_factor: float | None = Field(None, description="Profit factor")
    avg_win: float | None = Field(None, description="Average winning trade")
    avg_loss: float | None = Field(None, description="Average losing trade")

    # Statistical metrics
    skewness: float = Field(..., description="Return distribution skewness")
    kurtosis: float = Field(..., description="Return distribution kurtosis")
    calmar_ratio: float = Field(..., description="Calmar ratio (annual return / max drawdown)")

    # Benchmark comparison (optional)
    alpha: float | None = Field(None, description="Alpha vs benchmark")
    beta: float | None = Field(None, description="Beta vs benchmark")
    information_ratio: float | None = Field(None, description="Information ratio vs benchmark")
    tracking_error: float | None = Field(None, description="Tracking error vs benchmark")


class MetricsCalculator:
    """
    Calculator for performance metrics.

    This class provides methods to calculate various performance metrics
    from returns data and trade information.
    """

    def __init__(self) -> None:
        """Initialize the metrics calculator."""
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")

    def calculate_performance_metrics(self, returns: pd.Series, trades: pd.DataFrame | None = None) -> PerformanceMetrics:
        """
        Calculate comprehensive performance metrics.

        Args:
            returns: Series of returns
            trades: Optional DataFrame with trade information

        Returns:
            PerformanceMetrics object with calculated metrics

        """
        # Basic return statistics
        total_return = (1 + returns).prod() - 1
        annualized_return = (1 + returns).prod() ** (252 / len(returns)) - 1
        volatility = returns.std() * np.sqrt(252)

        # Risk-adjusted metrics
        sharpe_ratio = annualized_return / volatility if volatility > 0 else 0
        downside_deviation = self.calculate_downside_deviation(returns)
        sortino_ratio = annualized_return / downside_deviation if downside_deviation > 0 else 0

        # Drawdown metrics
        max_drawdown, max_drawdown_duration = self.calculate_max_drawdown(returns)

        # Risk metrics
        var_95 = np.percentile(returns, 5)
        cvar_95 = returns[returns <= var_95].mean()

        # Statistical metrics
        skewness = returns.skew()
        kurtosis = returns.kurtosis()
        calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0

        # Trade metrics (if trades data is provided)
        win_rate = None
        profit_factor = None
        avg_win = None
        avg_loss = None

        if trades is not None and not trades.empty:
            if "pnl" in trades.columns:
                winning_trades = trades[trades["pnl"] > 0]
                losing_trades = trades[trades["pnl"] < 0]

                win_rate = len(winning_trades) / len(trades) * 100 if len(trades) > 0 else 0
                avg_win = winning_trades["pnl"].mean() if len(winning_trades) > 0 else 0
                avg_loss = losing_trades["pnl"].mean() if len(losing_trades) > 0 else 0

                total_wins = winning_trades["pnl"].sum() if len(winning_trades) > 0 else 0
                total_losses = abs(losing_trades["pnl"].sum()) if len(losing_trades) > 0 else 0
                profit_factor = total_wins / total_losses if total_losses > 0 else float("inf")

        return PerformanceMetrics(
            total_return=total_return,
            annualized_return=annualized_return,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            max_drawdown=max_drawdown,
            max_drawdown_duration=max_drawdown_duration,
            downside_deviation=downside_deviation,
            var_95=var_95,
            cvar_95=cvar_95,
            win_rate=win_rate,
            profit_factor=profit_factor,
            avg_win=avg_win,
            avg_loss=avg_loss,
            skewness=skewness,
            kurtosis=kurtosis,
            calmar_ratio=calmar_ratio,
        )

    def calculate_max_drawdown(self, returns: pd.Series) -> tuple[float, int]:
        """
        Calculate maximum drawdown and its duration.

        Args:
            returns: Series of returns

        Returns:
            Tuple of (max_drawdown, max_duration_days)

        """
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max

        # Find maximum drawdown
        max_drawdown = drawdown.min()

        # Calculate drawdown duration
        is_drawdown = drawdown < 0
        drawdown_periods = []
        current_period = 0

        for in_drawdown in is_drawdown:
            if in_drawdown:
                current_period += 1
            else:
                if current_period > 0:
                    drawdown_periods.append(current_period)
                current_period = 0

        # Don't forget the last period if it ends in drawdown
        if current_period > 0:
            drawdown_periods.append(current_period)

        max_duration = max(drawdown_periods) if drawdown_periods else 0

        return max_drawdown, max_duration

    def calculate_downside_deviation(self, returns: pd.Series, target_return: float = 0) -> float:
        """
        Calculate downside deviation.

        Args:
            returns: Series of returns
            target_return: Target return threshold

        Returns:
            Annualized downside deviation

        """
        downside_returns = returns[returns < target_return]
        if len(downside_returns) == 0:
            return 0.0
        return np.sqrt(((downside_returns - target_return) ** 2).mean()) * np.sqrt(252)

    def calculate_relative_performance(
        self, strategy_metrics: PerformanceMetrics, benchmark_metrics: PerformanceMetrics
    ) -> dict[str, float]:
        """
        Calculate relative performance metrics vs benchmark.

        Args:
            strategy_metrics: Strategy performance metrics
            benchmark_metrics: Benchmark performance metrics

        Returns:
            Dictionary with relative performance metrics

        """
        return {
            "excess_return": strategy_metrics.annualized_return - benchmark_metrics.annualized_return,
            "relative_sharpe": strategy_metrics.sharpe_ratio - benchmark_metrics.sharpe_ratio,
            "relative_volatility": strategy_metrics.volatility - benchmark_metrics.volatility,
            "relative_max_drawdown": strategy_metrics.max_drawdown - benchmark_metrics.max_drawdown,
        }

    def generate_equity_curve_data(self, returns: pd.Series, benchmark_returns: pd.Series | None = None) -> dict[str, list]:
        """
        Generate data for equity curve visualization.

        Args:
            returns: Strategy returns
            benchmark_returns: Optional benchmark returns

        Returns:
            Dictionary with equity curve data

        """
        cumulative_returns = (1 + returns).cumprod()

        data = {
            "dates": returns.index.tolist(),
            "strategy_equity": cumulative_returns.tolist(),
        }

        if benchmark_returns is not None:
            benchmark_cumulative = (1 + benchmark_returns).cumprod()
            data["benchmark_equity"] = benchmark_cumulative.tolist()

        return data

    def generate_drawdown_data(self, returns: pd.Series) -> dict[str, list]:
        """
        Generate data for drawdown visualization.

        Args:
            returns: Series of returns

        Returns:
            Dictionary with drawdown data

        """
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max

        return {"dates": returns.index.tolist(), "drawdown": drawdown.tolist()}

    def generate_returns_distribution_data(self, returns: pd.Series, benchmark_returns: pd.Series | None = None) -> dict[str, list]:
        """
        Generate data for returns distribution visualization.

        Args:
            returns: Strategy returns
            benchmark_returns: Optional benchmark returns

        Returns:
            Dictionary with distribution data

        """
        data = {"strategy_returns": returns.tolist()}

        if benchmark_returns is not None:
            data["benchmark_returns"] = benchmark_returns.tolist()

        return data
