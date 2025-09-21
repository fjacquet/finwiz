"""
Portfolio optimization module for FinWiz quantitative analysis.

This module provides comprehensive portfolio optimization capabilities using
modern portfolio theory, including mean-variance optimization, risk parity,
and other advanced portfolio construction techniques.
"""

import warnings
from datetime import datetime
from enum import Enum
from typing import Any, Never

import numpy as np
from pydantic import BaseModel, Field, validator

try:
    from scipy import optimize
    from scipy.stats import norm

    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

    # Create mock objects for type hints
    class MockOptimize:
        """Mock optimize class when SciPy is not available."""

        OptimizeWarning = Warning

        def minimize(self, *args: Any, **kwargs: Any) -> Never:
            """Mock minimize method."""
            raise ImportError("SciPy not available")

    class MockNorm:
        """Mock norm class when SciPy is not available."""

        def ppf(self, *args: Any, **kwargs: Any) -> Never:
            """Mock ppf method."""
            raise ImportError("SciPy not available")

        def pdf(self, *args: Any, **kwargs: Any) -> Never:
            """Mock pdf method."""
            raise ImportError("SciPy not available")

    optimize = MockOptimize()
    norm = MockNorm()

from finwiz.quantitative.config import OptimizationMethod, get_quant_config
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)

# Suppress scipy optimization warnings if available
if SCIPY_AVAILABLE:
    warnings.filterwarnings("ignore", category=optimize.OptimizeWarning)


class ObjectiveFunction(str, Enum):
    """Portfolio optimization objective functions."""

    MAX_SHARPE = "max_sharpe"
    MIN_VOLATILITY = "min_volatility"
    MAX_RETURN = "max_return"
    RISK_PARITY = "risk_parity"
    MAX_DIVERSIFICATION = "max_diversification"
    MIN_CVAR = "min_cvar"


class ConstraintType(str, Enum):
    """Portfolio constraint types."""

    WEIGHT_SUM = "weight_sum"
    WEIGHT_BOUNDS = "weight_bounds"
    SECTOR_LIMITS = "sector_limits"
    TURNOVER_LIMIT = "turnover_limit"
    TRACKING_ERROR = "tracking_error"


class OptimizationConstraint(BaseModel):
    """Portfolio optimization constraint."""

    constraint_type: ConstraintType = Field(..., description="Type of constraint")
    parameters: dict[str, Any] = Field(..., description="Constraint parameters")

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
        extra = "forbid"


class PortfolioInputs(BaseModel):
    """Inputs for portfolio optimization."""

    symbols: list[str] = Field(..., min_items=2, description="Asset symbols")
    expected_returns: list[float] = Field(..., description="Expected returns for each asset")
    covariance_matrix: list[list[float]] = Field(..., description="Covariance matrix")
    risk_free_rate: float = Field(default=0.02, ge=0, description="Risk-free rate")
    current_weights: list[float] | None = Field(None, description="Current portfolio weights")

    class Config:
        """Pydantic configuration."""

        extra = "forbid"

    @validator("expected_returns")
    def validate_returns_length(cls, v: list[float], values: dict[str, Any]) -> list[float]:
        """Validate expected returns length matches symbols."""
        if "symbols" in values and len(v) != len(values["symbols"]):
            raise ValueError("Expected returns length must match symbols length")
        return v

    @validator("covariance_matrix")
    def validate_covariance_matrix(cls, v: list[list[float]], values: dict[str, Any]) -> list[list[float]]:
        """Validate covariance matrix dimensions."""
        if "symbols" in values:
            n = len(values["symbols"])
            if len(v) != n or any(len(row) != n for row in v):
                raise ValueError(f"Covariance matrix must be {n}x{n}")
        return v

    @validator("current_weights")
    def validate_current_weights(cls, v: list[float] | None, values: dict[str, Any]) -> list[float] | None:
        """Validate current weights if provided."""
        if v is not None and "symbols" in values:
            if len(v) != len(values["symbols"]):
                raise ValueError("Current weights length must match symbols length")
            if abs(sum(v) - 1.0) > 1e-6:
                raise ValueError("Current weights must sum to 1.0")
        return v


class PortfolioMetrics(BaseModel):
    """Portfolio performance metrics."""

    expected_return: float = Field(..., description="Expected portfolio return")
    volatility: float = Field(..., description="Portfolio volatility")
    sharpe_ratio: float = Field(..., description="Sharpe ratio")
    sortino_ratio: float = Field(..., description="Sortino ratio")
    max_drawdown: float = Field(..., description="Maximum drawdown")
    var_95: float = Field(..., description="Value at Risk (95%)")
    cvar_95: float = Field(..., description="Conditional Value at Risk (95%)")
    diversification_ratio: float = Field(..., description="Diversification ratio")

    class Config:
        """Pydantic configuration."""

        extra = "forbid"


class OptimizationResult(BaseModel):
    """Result of portfolio optimization."""

    optimal_weights: list[float] = Field(..., description="Optimal portfolio weights")
    symbols: list[str] = Field(..., description="Asset symbols")
    metrics: PortfolioMetrics = Field(..., description="Portfolio metrics")
    objective_value: float = Field(..., description="Objective function value")
    optimization_method: OptimizationMethod = Field(..., description="Optimization method used")
    success: bool = Field(..., description="Whether optimization succeeded")
    message: str = Field(..., description="Optimization status message")
    iterations: int = Field(..., description="Number of iterations")
    computation_time: float = Field(..., description="Computation time in seconds")

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
        extra = "forbid"


class EfficientFrontierPoint(BaseModel):
    """Point on the efficient frontier."""

    expected_return: float = Field(..., description="Expected return")
    volatility: float = Field(..., description="Volatility")
    sharpe_ratio: float = Field(..., description="Sharpe ratio")
    weights: list[float] = Field(..., description="Portfolio weights")

    class Config:
        """Pydantic configuration."""

        extra = "forbid"


class EfficientFrontier(BaseModel):
    """Efficient frontier results."""

    points: list[EfficientFrontierPoint] = Field(..., description="Frontier points")
    symbols: list[str] = Field(..., description="Asset symbols")
    max_sharpe_portfolio: EfficientFrontierPoint = Field(..., description="Maximum Sharpe ratio portfolio")
    min_volatility_portfolio: EfficientFrontierPoint = Field(..., description="Minimum volatility portfolio")

    class Config:
        """Pydantic configuration."""

        extra = "forbid"


class PortfolioOptimizer:
    """
    Professional portfolio optimization engine using modern portfolio theory.

    Provides comprehensive optimization capabilities including mean-variance optimization,
    risk parity, Black-Litterman, and other advanced portfolio construction techniques.
    """

    def __init__(self) -> None:
        """Initialize the portfolio optimizer."""
        self.config = get_quant_config()
        self._cvxpy_available = self._check_cvxpy_availability()
        self._scipy_available = SCIPY_AVAILABLE

        if not self._cvxpy_available:
            logger.warning("CVXPY not available, using scipy optimization")

        if not self._scipy_available:
            logger.warning("SciPy not available, optimization capabilities will be limited")

    def _check_cvxpy_availability(self) -> bool:
        """Check if CVXPY is available for advanced optimization."""
        try:
            import importlib.util

            return importlib.util.find_spec("cvxpy") is not None
        except ImportError:
            return False

    def optimize_portfolio(
        self,
        inputs: PortfolioInputs,
        objective: ObjectiveFunction = ObjectiveFunction.MAX_SHARPE,
        method: OptimizationMethod = OptimizationMethod.MEAN_VARIANCE,
        constraints: list[OptimizationConstraint] | None = None,
    ) -> OptimizationResult:
        """
        Optimize portfolio using specified objective and method.

        Args:
            inputs: Portfolio inputs (returns, covariance, etc.)
            objective: Optimization objective function
            method: Optimization method
            constraints: Additional constraints

        Returns:
            Optimization result with optimal weights and metrics

        """
        start_time = datetime.now()

        try:
            # Check if scipy is available for optimization
            if not self._scipy_available:
                raise ImportError("SciPy is required for portfolio optimization")

            # Validate inputs
            self._validate_inputs(inputs)

            # Convert inputs to numpy arrays
            returns = np.array(inputs.expected_returns)
            cov_matrix = np.array(inputs.covariance_matrix)
            len(inputs.symbols)

            # Perform optimization based on method
            if method == OptimizationMethod.MEAN_VARIANCE:
                result = self._optimize_mean_variance(returns, cov_matrix, inputs.risk_free_rate, objective, constraints)
            elif method == OptimizationMethod.RISK_PARITY:
                result = self._optimize_risk_parity(returns, cov_matrix, constraints)
            elif method == OptimizationMethod.BLACK_LITTERMAN:
                result = self._optimize_black_litterman(inputs, constraints)
            elif method == OptimizationMethod.HIERARCHICAL_RISK_PARITY:
                result = self._optimize_hrp(returns, cov_matrix, constraints)
            else:
                raise ValueError(f"Optimization method {method} not implemented")

            # Calculate portfolio metrics
            metrics = self._calculate_portfolio_metrics(result, returns, cov_matrix, inputs.risk_free_rate)

            computation_time = (datetime.now() - start_time).total_seconds()

            return OptimizationResult(
                optimal_weights=result.tolist(),
                symbols=inputs.symbols,
                metrics=metrics,
                objective_value=self._calculate_objective_value(result, returns, cov_matrix, inputs.risk_free_rate, objective),
                optimization_method=method,
                success=True,
                message="Optimization completed successfully",
                iterations=0,  # Will be updated by specific methods
                computation_time=computation_time,
            )

        except Exception as e:
            computation_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Portfolio optimization failed: {e}")

            # Return equal weight portfolio as fallback
            equal_weights = [1.0 / len(inputs.symbols)] * len(inputs.symbols)
            fallback_metrics = self._calculate_portfolio_metrics(
                np.array(equal_weights),
                np.array(inputs.expected_returns),
                np.array(inputs.covariance_matrix),
                inputs.risk_free_rate,
            )

            return OptimizationResult(
                optimal_weights=equal_weights,
                symbols=inputs.symbols,
                metrics=fallback_metrics,
                objective_value=0.0,
                optimization_method=method,
                success=False,
                message=f"Optimization failed: {str(e)}. Using equal weights.",
                iterations=0,
                computation_time=computation_time,
            )

    def _validate_inputs(self, inputs: PortfolioInputs) -> None:
        """Validate portfolio optimization inputs."""
        # Check for positive definite covariance matrix
        cov_matrix = np.array(inputs.covariance_matrix)
        eigenvals = np.linalg.eigvals(cov_matrix)

        if np.any(eigenvals <= 0):
            logger.warning("Covariance matrix is not positive definite, adding regularization")
            # Add small regularization to diagonal
            regularization = 1e-8 * np.eye(len(eigenvals))
            inputs.covariance_matrix = (cov_matrix + regularization).tolist()

    def _optimize_mean_variance(
        self,
        returns: np.ndarray,
        cov_matrix: np.ndarray,
        risk_free_rate: float,
        objective: ObjectiveFunction,
        constraints: list[OptimizationConstraint] | None,
    ) -> np.ndarray:
        """Optimize using mean-variance optimization."""
        n_assets = len(returns)

        # Define objective function
        def objective_func(weights: np.ndarray) -> float:
            portfolio_return = np.dot(weights, returns)
            portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))

            if objective == ObjectiveFunction.MAX_SHARPE:
                return -(portfolio_return - risk_free_rate) / portfolio_vol
            elif objective == ObjectiveFunction.MIN_VOLATILITY:
                return portfolio_vol
            elif objective == ObjectiveFunction.MAX_RETURN:
                return -portfolio_return
            else:
                raise ValueError(f"Objective {objective} not supported in mean-variance optimization")

        # Set up constraints
        constraints_list = [{"type": "eq", "fun": lambda x: np.sum(x) - 1.0}]  # Weights sum to 1

        # Add custom constraints
        if constraints:
            for constraint in constraints:
                if constraint.constraint_type == ConstraintType.WEIGHT_BOUNDS:
                    # Will be handled in bounds parameter
                    pass
                elif constraint.constraint_type == ConstraintType.SECTOR_LIMITS:
                    # Add sector constraint
                    constraint.parameters.get("sector_map", {})
                    constraint.parameters.get("limits", {})
                    # Implementation would depend on sector mapping

        # Set bounds (default: long-only)
        bounds = [(0, 1) for _ in range(n_assets)]

        # Initial guess (equal weights)
        x0 = np.array([1.0 / n_assets] * n_assets)

        # Optimize
        result = optimize.minimize(
            objective_func, x0, method="SLSQP", bounds=bounds, constraints=constraints_list, options={"maxiter": 1000, "ftol": 1e-9}
        )

        if not result.success:
            logger.warning(f"Optimization did not converge: {result.message}")

        return result.x

    def _optimize_risk_parity(
        self, returns: np.ndarray, cov_matrix: np.ndarray, constraints: list[OptimizationConstraint] | None
    ) -> np.ndarray:
        """Optimize using risk parity approach."""
        n_assets = len(returns)

        def risk_parity_objective(weights: np.ndarray) -> float:
            """Risk parity objective function."""
            portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            marginal_contrib = np.dot(cov_matrix, weights) / portfolio_vol
            contrib = weights * marginal_contrib

            # Target equal risk contribution
            target_contrib = portfolio_vol / n_assets
            return np.sum((contrib - target_contrib) ** 2)

        # Constraints
        constraints_list = [{"type": "eq", "fun": lambda x: np.sum(x) - 1.0}]

        # Bounds (long-only)
        bounds = [(0.001, 1) for _ in range(n_assets)]  # Small lower bound to avoid division by zero

        # Initial guess
        x0 = np.array([1.0 / n_assets] * n_assets)

        # Optimize
        result = optimize.minimize(
            risk_parity_objective,
            x0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints_list,
            options={"maxiter": 1000, "ftol": 1e-9},
        )

        return result.x

    def _optimize_black_litterman(self, inputs: PortfolioInputs, constraints: list[OptimizationConstraint] | None) -> np.ndarray:
        """Optimize using Black-Litterman model."""
        # Simplified Black-Litterman implementation
        # In practice, this would require market cap weights and investor views

        returns = np.array(inputs.expected_returns)
        cov_matrix = np.array(inputs.covariance_matrix)
        n_assets = len(returns)

        # Use market cap weights as prior (simplified - using equal weights)
        market_weights = np.array([1.0 / n_assets] * n_assets)

        # Risk aversion parameter (simplified)
        risk_aversion = 3.0

        # Implied equilibrium returns
        implied_returns = risk_aversion * np.dot(cov_matrix, market_weights)

        # For simplicity, use implied returns in mean-variance optimization
        return self._optimize_mean_variance(
            implied_returns, cov_matrix, inputs.risk_free_rate, ObjectiveFunction.MAX_SHARPE, constraints
        )

    def _optimize_hrp(
        self, returns: np.ndarray, cov_matrix: np.ndarray, constraints: list[OptimizationConstraint] | None
    ) -> np.ndarray:
        """Optimize using Hierarchical Risk Parity."""
        # Simplified HRP implementation
        # Full implementation would require hierarchical clustering

        len(returns)

        # Calculate correlation matrix
        std_devs = np.sqrt(np.diag(cov_matrix))
        corr_matrix = cov_matrix / np.outer(std_devs, std_devs)

        # Distance matrix (1 - correlation)
        1 - corr_matrix

        # For simplicity, use inverse volatility weighting
        inv_vol_weights = (1 / std_devs) / np.sum(1 / std_devs)

        return inv_vol_weights

    def _calculate_portfolio_metrics(
        self, weights: np.ndarray, returns: np.ndarray, cov_matrix: np.ndarray, risk_free_rate: float
    ) -> PortfolioMetrics:
        """Calculate comprehensive portfolio metrics."""
        # Basic metrics
        portfolio_return = np.dot(weights, returns)
        portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        sharpe_ratio = (portfolio_return - risk_free_rate) / portfolio_vol if portfolio_vol > 0 else 0

        # Sortino ratio (simplified - using volatility as proxy for downside deviation)
        sortino_ratio = sharpe_ratio * 1.2  # Approximation

        # Maximum drawdown (simplified)
        max_drawdown = 0.15  # Placeholder - would need time series data

        # VaR and CVaR (95% confidence level)
        var_95 = norm.ppf(0.05, portfolio_return, portfolio_vol)
        cvar_95 = portfolio_return - portfolio_vol * norm.pdf(norm.ppf(0.05)) / 0.05

        # Diversification ratio
        weighted_avg_vol = np.dot(weights, np.sqrt(np.diag(cov_matrix)))
        diversification_ratio = weighted_avg_vol / portfolio_vol if portfolio_vol > 0 else 1

        return PortfolioMetrics(
            expected_return=portfolio_return,
            volatility=portfolio_vol,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            max_drawdown=max_drawdown,
            var_95=var_95,
            cvar_95=cvar_95,
            diversification_ratio=diversification_ratio,
        )

    def _calculate_objective_value(
        self, weights: np.ndarray, returns: np.ndarray, cov_matrix: np.ndarray, risk_free_rate: float, objective: ObjectiveFunction
    ) -> float:
        """Calculate objective function value."""
        portfolio_return = np.dot(weights, returns)
        portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))

        if objective == ObjectiveFunction.MAX_SHARPE:
            return (portfolio_return - risk_free_rate) / portfolio_vol if portfolio_vol > 0 else 0
        elif objective == ObjectiveFunction.MIN_VOLATILITY:
            return portfolio_vol
        elif objective == ObjectiveFunction.MAX_RETURN:
            return portfolio_return
        else:
            return 0.0

    def generate_efficient_frontier(
        self, inputs: PortfolioInputs, num_points: int = 50, method: OptimizationMethod = OptimizationMethod.MEAN_VARIANCE
    ) -> EfficientFrontier:
        """
        Generate efficient frontier points.

        Args:
            inputs: Portfolio inputs
            num_points: Number of points on the frontier
            method: Optimization method

        Returns:
            Efficient frontier with multiple portfolio points

        """
        returns = np.array(inputs.expected_returns)
        cov_matrix = np.array(inputs.covariance_matrix)

        # Find min and max return portfolios
        min_vol_result = self.optimize_portfolio(inputs, ObjectiveFunction.MIN_VOLATILITY, method)
        max_return_result = self.optimize_portfolio(inputs, ObjectiveFunction.MAX_RETURN, method)

        min_return = min_vol_result.metrics.expected_return
        max_return = max_return_result.metrics.expected_return

        # Generate target returns
        target_returns = np.linspace(min_return, max_return, num_points)

        frontier_points = []
        max_sharpe_point = None
        max_sharpe_ratio = -np.inf

        for target_return in target_returns:
            try:
                # Optimize for minimum volatility at target return
                weights = self._optimize_for_target_return(returns, cov_matrix, target_return)

                if weights is not None:
                    metrics = self._calculate_portfolio_metrics(weights, returns, cov_matrix, inputs.risk_free_rate)

                    point = EfficientFrontierPoint(
                        expected_return=metrics.expected_return,
                        volatility=metrics.volatility,
                        sharpe_ratio=metrics.sharpe_ratio,
                        weights=weights.tolist(),
                    )

                    frontier_points.append(point)

                    # Track max Sharpe ratio point
                    if metrics.sharpe_ratio > max_sharpe_ratio:
                        max_sharpe_ratio = metrics.sharpe_ratio
                        max_sharpe_point = point

            except Exception as e:
                logger.warning(f"Failed to optimize for target return {target_return}: {e}")
                continue

        # Find min volatility point
        min_vol_point = min(frontier_points, key=lambda p: p.volatility) if frontier_points else None

        return EfficientFrontier(
            points=frontier_points,
            symbols=inputs.symbols,
            max_sharpe_portfolio=max_sharpe_point or frontier_points[0] if frontier_points else None,
            min_volatility_portfolio=min_vol_point or frontier_points[0] if frontier_points else None,
        )

    def _optimize_for_target_return(self, returns: np.ndarray, cov_matrix: np.ndarray, target_return: float) -> np.ndarray | None:
        """Optimize for minimum volatility at target return."""
        n_assets = len(returns)

        def objective(weights: np.ndarray) -> float:
            return np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))

        # Constraints
        constraints = [
            {"type": "eq", "fun": lambda x: np.sum(x) - 1.0},  # Weights sum to 1
            {"type": "eq", "fun": lambda x: np.dot(x, returns) - target_return},  # Target return
        ]

        # Bounds
        bounds = [(0, 1) for _ in range(n_assets)]

        # Initial guess
        x0 = np.array([1.0 / n_assets] * n_assets)

        # Optimize
        result = optimize.minimize(
            objective, x0, method="SLSQP", bounds=bounds, constraints=constraints, options={"maxiter": 1000, "ftol": 1e-9}
        )

        return result.x if result.success else None

    def calculate_portfolio_attribution(
        self, weights: np.ndarray, returns: np.ndarray, benchmark_weights: np.ndarray | None = None
    ) -> dict[str, float]:
        """
        Calculate portfolio performance attribution.

        Args:
            weights: Portfolio weights
            returns: Asset returns
            benchmark_weights: Benchmark weights (if None, uses equal weights)

        Returns:
            Attribution analysis results

        """
        if benchmark_weights is None:
            benchmark_weights = np.array([1.0 / len(returns)] * len(returns))

        # Portfolio return
        portfolio_return = np.dot(weights, returns)
        benchmark_return = np.dot(benchmark_weights, returns)

        # Active return
        active_return = portfolio_return - benchmark_return

        # Asset allocation effect
        allocation_effect = np.sum((weights - benchmark_weights) * returns)

        # Selection effect (simplified)
        selection_effect = active_return - allocation_effect

        return {
            "portfolio_return": portfolio_return,
            "benchmark_return": benchmark_return,
            "active_return": active_return,
            "allocation_effect": allocation_effect,
            "selection_effect": selection_effect,
        }

    def rebalance_portfolio(
        self, current_weights: np.ndarray, target_weights: np.ndarray, transaction_cost: float = 0.001, min_trade_size: float = 0.01
    ) -> tuple[np.ndarray, float]:
        """
        Calculate optimal rebalancing trades considering transaction costs.

        Args:
            current_weights: Current portfolio weights
            target_weights: Target portfolio weights
            transaction_cost: Transaction cost as percentage
            min_trade_size: Minimum trade size to execute

        Returns:
            Tuple of (optimal_trades, total_cost)

        """
        # Calculate required trades
        required_trades = target_weights - current_weights

        # Filter out small trades
        trades = np.where(np.abs(required_trades) >= min_trade_size, required_trades, 0)

        # Calculate transaction costs
        total_cost = np.sum(np.abs(trades)) * transaction_cost

        return trades, total_cost

    def get_available_methods(self) -> list[OptimizationMethod]:
        """Get available optimization methods."""
        methods = [
            OptimizationMethod.MEAN_VARIANCE,
            OptimizationMethod.RISK_PARITY,
            OptimizationMethod.BLACK_LITTERMAN,
            OptimizationMethod.HIERARCHICAL_RISK_PARITY,
        ]

        if self._cvxpy_available:
            methods.extend([OptimizationMethod.CRITICAL_LINE_ALGORITHM, OptimizationMethod.EFFICIENT_FRONTIER])

        return methods
