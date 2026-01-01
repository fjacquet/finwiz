"""
Core portfolio optimization algorithms.

This module contains the core optimization algorithms for portfolio construction,
including mean-variance optimization, risk parity, Black-Litterman, and
Hierarchical Risk Parity (HRP).
"""

from typing import Any

import numpy as np

try:
    from scipy import optimize

    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    optimize = None  # type: ignore[assignment]

from finwiz.quantitative.config import OptimizationMethod
from finwiz.quantitative.constraint_handlers import ConstraintHandler, OptimizationConstraint
from finwiz.quantitative.objective_functions import ObjectiveFunction, ObjectiveFunctionCalculator
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class PortfolioOptimizationAlgorithms:
    """
    Core portfolio optimization algorithms.

    Provides implementations of various portfolio optimization algorithms
    including mean-variance, risk parity, Black-Litterman, and HRP.
    """

    def __init__(self) -> None:
        """Initialize optimization algorithms."""
        self.constraint_handler = ConstraintHandler()
        self.objective_calculator = ObjectiveFunctionCalculator()

    def optimize_mean_variance(
        self,
        returns: np.ndarray,
        cov_matrix: np.ndarray,
        risk_free_rate: float,
        objective: ObjectiveFunction,
        constraints: list[OptimizationConstraint] | None = None,
    ) -> np.ndarray:
        """
        Optimize using mean-variance optimization.

        Args:
            returns: Expected returns array
            cov_matrix: Covariance matrix
            risk_free_rate: Risk-free rate
            objective: Optimization objective
            constraints: Additional constraints

        Returns:
            Optimal portfolio weights

        """
        if not SCIPY_AVAILABLE or optimize is None:
            raise ImportError("SciPy is required for mean-variance optimization")

        # Assign to Any-typed variable for type checking
        scipy_opt: Any = optimize

        n_assets = len(returns)

        # Get objective function
        objective_func = self.objective_calculator.get_objective_function(objective, returns, cov_matrix, risk_free_rate)

        # Set up constraints
        constraints_list = self.constraint_handler.build_scipy_constraints(n_assets, constraints)

        # Add custom constraints based on objective type
        if constraints:
            for constraint in constraints:
                constraint_type_str = constraint.constraint_type if isinstance(constraint.constraint_type, str) else constraint.constraint_type.value
                if constraint_type_str == "weight_bounds":
                    # Will be handled in bounds parameter
                    pass
                elif constraint_type_str == "sector_limits":
                    # Already handled in constraint_handler
                    pass

        # Set bounds (default: long-only)
        bounds = self.constraint_handler.build_weight_bounds(n_assets, constraints)

        # Initial guess (equal weights)
        x0 = np.array([1.0 / n_assets] * n_assets)

        # Optimize
        result = scipy_opt.minimize(objective_func, x0, method="SLSQP", bounds=bounds, constraints=constraints_list, options={"maxiter": 1000, "ftol": 1e-9})

        if not result.success:
            logger.warning(f"Mean-variance optimization did not converge: {result.message}")

        weights: np.ndarray = result.x
        return weights

    def optimize_risk_parity(
        self,
        returns: np.ndarray,
        cov_matrix: np.ndarray,
        constraints: list[OptimizationConstraint] | None = None,
    ) -> np.ndarray:
        """
        Optimize using risk parity approach.

        Args:
            returns: Expected returns array
            cov_matrix: Covariance matrix
            constraints: Additional constraints

        Returns:
            Optimal portfolio weights

        """
        if not SCIPY_AVAILABLE or optimize is None:
            raise ImportError("SciPy is required for risk parity optimization")

        # Assign to Any-typed variable for type checking
        scipy_opt: Any = optimize

        n_assets = len(returns)

        # Get risk parity objective function
        objective_func = self.objective_calculator.get_objective_function(ObjectiveFunction.RISK_PARITY, returns, cov_matrix)

        # Constraints
        constraints_list = self.constraint_handler.build_scipy_constraints(n_assets, constraints)

        # Bounds (long-only with small lower bound to avoid division by zero)
        bounds: list[tuple[float, float]] = [(0.001, 1.0) for _ in range(n_assets)]

        # Override with custom bounds if provided
        if constraints:
            custom_bounds = self.constraint_handler.build_weight_bounds(n_assets, constraints, default_bounds=(0.001, 1.0))
            bounds = custom_bounds

        # Initial guess
        x0 = np.array([1.0 / n_assets] * n_assets)

        # Optimize
        result = scipy_opt.minimize(
            objective_func,
            x0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints_list,
            options={"maxiter": 1000, "ftol": 1e-9},
        )

        if not result.success:
            logger.warning(f"Risk parity optimization did not converge: {result.message}")

        weights: np.ndarray = result.x
        return weights

    def optimize_black_litterman(
        self,
        returns: np.ndarray,
        cov_matrix: np.ndarray,
        risk_free_rate: float,
        market_weights: np.ndarray | None = None,
        investor_views: dict[str, Any] | None = None,
        constraints: list[OptimizationConstraint] | None = None,
    ) -> np.ndarray:
        """
        Optimize using Black-Litterman model.

        Args:
            returns: Expected returns array
            cov_matrix: Covariance matrix
            risk_free_rate: Risk-free rate
            market_weights: Market capitalization weights (if None, uses equal weights)
            investor_views: Investor views dictionary (simplified implementation)
            constraints: Additional constraints

        Returns:
            Optimal portfolio weights

        """
        n_assets = len(returns)

        # Use market cap weights as prior (simplified - using equal weights if not provided)
        if market_weights is None:
            market_weights = np.array([1.0 / n_assets] * n_assets)

        # Risk aversion parameter (simplified)
        risk_aversion = 3.0

        # Implied equilibrium returns
        implied_returns = risk_aversion * np.dot(cov_matrix, market_weights)

        # Incorporate investor views (simplified implementation)
        if investor_views:
            # In a full implementation, this would use the Black-Litterman formula
            # For now, we'll blend the implied returns with any provided views
            view_adjustment = investor_views.get("return_adjustment", np.zeros(n_assets))
            confidence = investor_views.get("confidence", 0.5)

            adjusted_returns = (1 - confidence) * implied_returns + confidence * (implied_returns + view_adjustment)
        else:
            adjusted_returns = implied_returns

        # Use mean-variance optimization with adjusted returns
        return self.optimize_mean_variance(adjusted_returns, cov_matrix, risk_free_rate, ObjectiveFunction.MAX_SHARPE, constraints)

    def optimize_hierarchical_risk_parity(
        self,
        returns: np.ndarray,
        cov_matrix: np.ndarray,
        constraints: list[OptimizationConstraint] | None = None,
    ) -> np.ndarray:
        """
        Optimize using Hierarchical Risk Parity (HRP).

        Args:
            returns: Expected returns array
            cov_matrix: Covariance matrix
            constraints: Additional constraints (limited support)

        Returns:
            Optimal portfolio weights

        """
        n_assets = len(returns)

        # Calculate correlation matrix
        std_devs = np.sqrt(np.diag(cov_matrix))
        corr_matrix = cov_matrix / np.outer(std_devs, std_devs)

        # Distance matrix (1 - correlation)
        distance_matrix = 1 - corr_matrix

        # For simplicity, use inverse volatility weighting
        # Full HRP implementation would require hierarchical clustering
        inv_vol_weights = (1 / std_devs) / np.sum(1 / std_devs)

        # Apply basic constraints if provided
        if constraints:
            # Validate constraints
            is_valid, violations = self.constraint_handler.validate_constraints(inv_vol_weights, constraints)

            if not is_valid:
                logger.warning(f"HRP weights violate constraints: {violations}")
                # Fall back to equal weights
                fallback_weights: np.ndarray = np.array([1.0 / n_assets] * n_assets)
                return fallback_weights

        result_weights: np.ndarray = inv_vol_weights
        return result_weights

    def optimize_for_target_return(
        self,
        returns: np.ndarray,
        cov_matrix: np.ndarray,
        target_return: float,
        constraints: list[OptimizationConstraint] | None = None,
    ) -> np.ndarray | None:
        """
        Optimize for minimum volatility at target return.

        Args:
            returns: Expected returns array
            cov_matrix: Covariance matrix
            target_return: Target portfolio return
            constraints: Additional constraints

        Returns:
            Optimal weights or None if optimization fails

        """
        if not SCIPY_AVAILABLE or optimize is None:
            raise ImportError("SciPy is required for target return optimization")

        # Assign to Any-typed variable for type checking
        scipy_opt: Any = optimize

        n_assets = len(returns)

        # Objective: minimize volatility
        objective_func = self.objective_calculator.get_objective_function(ObjectiveFunction.MIN_VOLATILITY, returns, cov_matrix)

        # Constraints (including target return)
        constraints_list = self.constraint_handler.build_scipy_constraints(n_assets, constraints, target_return, returns)

        # Bounds
        bounds = self.constraint_handler.build_weight_bounds(n_assets, constraints)

        # Initial guess
        x0 = np.array([1.0 / n_assets] * n_assets)

        # Optimize
        result = scipy_opt.minimize(objective_func, x0, method="SLSQP", bounds=bounds, constraints=constraints_list, options={"maxiter": 1000, "ftol": 1e-9})

        return result.x if result.success else None

    def get_available_algorithms(self) -> list[OptimizationMethod]:
        """
        Get list of available optimization algorithms.

        Returns:
            List of available optimization methods

        """
        algorithms = [
            OptimizationMethod.MEAN_VARIANCE,
            OptimizationMethod.RISK_PARITY,
            OptimizationMethod.BLACK_LITTERMAN,
            OptimizationMethod.HIERARCHICAL_RISK_PARITY,
        ]

        return algorithms

    def validate_inputs(
        self,
        returns: np.ndarray,
        cov_matrix: np.ndarray,
        constraints: list[OptimizationConstraint] | None = None,
    ) -> tuple[bool, list[str]]:
        """
        Validate optimization inputs.

        Args:
            returns: Expected returns array
            cov_matrix: Covariance matrix
            constraints: Optimization constraints

        Returns:
            Tuple of (is_valid, list_of_errors)

        """
        errors = []

        # Basic validation
        if len(returns) != cov_matrix.shape[0] or len(returns) != cov_matrix.shape[1]:
            errors.append("Returns length must match covariance matrix dimensions")

        if not np.allclose(cov_matrix, cov_matrix.T):
            errors.append("Covariance matrix must be symmetric")

        # Check for positive definite covariance matrix
        eigenvals = np.linalg.eigvals(cov_matrix)
        if np.any(eigenvals <= 0):
            errors.append("Covariance matrix is not positive definite")

        # Validate constraints
        if constraints:
            for constraint in constraints:
                try:
                    # Basic constraint validation
                    if not hasattr(constraint, "constraint_type") or not hasattr(constraint, "parameters"):
                        errors.append(f"Invalid constraint structure: {constraint}")
                except Exception as e:
                    errors.append(f"Constraint validation error: {e}")

        is_valid = len(errors) == 0
        return is_valid, errors

    def regularize_covariance_matrix(
        self,
        cov_matrix: np.ndarray,
        regularization: float = 1e-8,
    ) -> np.ndarray:
        """
        Regularize covariance matrix to ensure positive definiteness.

        Args:
            cov_matrix: Original covariance matrix
            regularization: Regularization parameter

        Returns:
            Regularized covariance matrix

        """
        eigenvals = np.linalg.eigvals(cov_matrix)

        if np.any(eigenvals <= 0):
            logger.warning("Covariance matrix is not positive definite, adding regularization")
            # Add small regularization to diagonal
            regularization_matrix = regularization * np.eye(cov_matrix.shape[0])
            regularized: np.ndarray = cov_matrix + regularization_matrix
            return regularized

        result: np.ndarray = cov_matrix
        return result
