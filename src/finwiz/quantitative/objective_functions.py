"""
Objective functions for portfolio optimization.

This module provides various objective functions used in portfolio optimization,
including Sharpe ratio maximization, volatility minimization, return maximization,
and risk parity objectives.
"""

from collections.abc import Callable
from enum import Enum
from typing import Any, Never

import numpy as np

try:
    from scipy.stats import norm

    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

    class MockNorm:
        """Mock norm class when SciPy is not available."""

        def ppf(self, *args: Any, **kwargs: Any) -> Never:
            """Mock ppf method."""
            raise ImportError("SciPy not available")

        def pdf(self, *args: Any, **kwargs: Any) -> Never:
            """Mock pdf method."""
            raise ImportError("SciPy not available")

    norm = MockNorm()

from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class ObjectiveFunction(str, Enum):
    """Portfolio optimization objective functions."""

    MAX_SHARPE = "max_sharpe"
    MIN_VOLATILITY = "min_volatility"
    MAX_RETURN = "max_return"
    RISK_PARITY = "risk_parity"
    MAX_DIVERSIFICATION = "max_diversification"
    MIN_CVAR = "min_cvar"


class ObjectiveFunctionCalculator:
    """
    Calculator for portfolio optimization objective functions.

    Provides methods to calculate various objective functions used in
    portfolio optimization, including their gradients where applicable.
    """

    def __init__(self) -> None:
        """Initialize objective function calculator."""
        pass

    def get_objective_function(
        self,
        objective: ObjectiveFunction,
        returns: np.ndarray,
        cov_matrix: np.ndarray,
        risk_free_rate: float = 0.02,
        **kwargs: Any,
    ) -> Callable[[np.ndarray], float]:
        """
        Get objective function for optimization.

        Args:
            objective: Type of objective function
            returns: Expected returns array
            cov_matrix: Covariance matrix
            risk_free_rate: Risk-free rate
            **kwargs: Additional parameters for specific objectives

        Returns:
            Objective function that takes weights and returns scalar value

        """
        if objective == ObjectiveFunction.MAX_SHARPE:
            return self._max_sharpe_objective(returns, cov_matrix, risk_free_rate)
        elif objective == ObjectiveFunction.MIN_VOLATILITY:
            return self._min_volatility_objective(cov_matrix)
        elif objective == ObjectiveFunction.MAX_RETURN:
            return self._max_return_objective(returns)
        elif objective == ObjectiveFunction.RISK_PARITY:
            return self._risk_parity_objective(cov_matrix)
        elif objective == ObjectiveFunction.MAX_DIVERSIFICATION:
            return self._max_diversification_objective(cov_matrix)
        elif objective == ObjectiveFunction.MIN_CVAR:
            confidence_level = kwargs.get("confidence_level", 0.05)
            return self._min_cvar_objective(returns, cov_matrix, confidence_level)
        else:
            raise ValueError(f"Objective function {objective} not implemented")

    def _max_sharpe_objective(
        self,
        returns: np.ndarray,
        cov_matrix: np.ndarray,
        risk_free_rate: float,
    ) -> Callable[[np.ndarray], float]:
        """Create maximum Sharpe ratio objective function."""

        def objective_func(weights: np.ndarray) -> float:
            portfolio_return = np.dot(weights, returns)
            portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))

            if portfolio_vol == 0:
                return -np.inf

            # Return negative Sharpe ratio for minimization
            return -(portfolio_return - risk_free_rate) / portfolio_vol

        return objective_func

    def _min_volatility_objective(self, cov_matrix: np.ndarray) -> Callable[[np.ndarray], float]:
        """Create minimum volatility objective function."""

        def objective_func(weights: np.ndarray) -> float:
            return np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))

        return objective_func

    def _max_return_objective(self, returns: np.ndarray) -> Callable[[np.ndarray], float]:
        """Create maximum return objective function."""

        def objective_func(weights: np.ndarray) -> float:
            # Return negative return for minimization
            return -np.dot(weights, returns)

        return objective_func

    def _risk_parity_objective(self, cov_matrix: np.ndarray) -> Callable[[np.ndarray], float]:
        """Create risk parity objective function."""

        def objective_func(weights: np.ndarray) -> float:
            """Risk parity objective function."""
            n_assets = len(weights)

            # Avoid division by zero
            weights = np.maximum(weights, 1e-8)

            portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))

            if portfolio_vol == 0:
                return np.inf

            marginal_contrib = np.dot(cov_matrix, weights) / portfolio_vol
            contrib = weights * marginal_contrib

            # Target equal risk contribution
            target_contrib = portfolio_vol / n_assets
            return np.sum((contrib - target_contrib) ** 2)

        return objective_func

    def _max_diversification_objective(self, cov_matrix: np.ndarray) -> Callable[[np.ndarray], float]:
        """Create maximum diversification ratio objective function."""

        def objective_func(weights: np.ndarray) -> float:
            # Calculate diversification ratio
            weighted_avg_vol = np.dot(weights, np.sqrt(np.diag(cov_matrix)))
            portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))

            if portfolio_vol == 0:
                return -np.inf

            diversification_ratio = weighted_avg_vol / portfolio_vol

            # Return negative for minimization (we want to maximize diversification)
            return -diversification_ratio

        return objective_func

    def _min_cvar_objective(
        self,
        returns: np.ndarray,
        cov_matrix: np.ndarray,
        confidence_level: float,
    ) -> Callable[[np.ndarray], float]:
        """Create minimum Conditional Value at Risk (CVaR) objective function."""
        if not SCIPY_AVAILABLE:
            logger.warning("SciPy not available, using volatility as CVaR proxy")
            return self._min_volatility_objective(cov_matrix)

        def objective_func(weights: np.ndarray) -> float:
            portfolio_return = np.dot(weights, returns)
            portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))

            if portfolio_vol == 0:
                return np.inf

            # Calculate CVaR assuming normal distribution
            var_quantile = norm.ppf(confidence_level, portfolio_return, portfolio_vol)
            cvar = portfolio_return - portfolio_vol * norm.pdf(norm.ppf(confidence_level)) / confidence_level

            # Return CVaR (already negative for losses, so minimize directly)
            return -cvar  # Minimize negative CVaR (maximize CVaR)

        return objective_func

    def calculate_objective_value(
        self,
        weights: np.ndarray,
        returns: np.ndarray,
        cov_matrix: np.ndarray,
        risk_free_rate: float,
        objective: ObjectiveFunction,
        **kwargs: Any,
    ) -> float:
        """
        Calculate objective function value for given weights.

        Args:
            weights: Portfolio weights
            returns: Expected returns
            cov_matrix: Covariance matrix
            risk_free_rate: Risk-free rate
            objective: Objective function type
            **kwargs: Additional parameters

        Returns:
            Objective function value (positive, not negated)

        """
        portfolio_return = np.dot(weights, returns)
        portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))

        if objective == ObjectiveFunction.MAX_SHARPE:
            return (portfolio_return - risk_free_rate) / portfolio_vol if portfolio_vol > 0 else 0
        elif objective == ObjectiveFunction.MIN_VOLATILITY:
            return portfolio_vol
        elif objective == ObjectiveFunction.MAX_RETURN:
            return portfolio_return
        elif objective == ObjectiveFunction.RISK_PARITY:
            # Calculate risk parity score (lower is better)
            n_assets = len(weights)
            weights = np.maximum(weights, 1e-8)

            if portfolio_vol == 0:
                return np.inf

            marginal_contrib = np.dot(cov_matrix, weights) / portfolio_vol
            contrib = weights * marginal_contrib
            target_contrib = portfolio_vol / n_assets

            return np.sum((contrib - target_contrib) ** 2)
        elif objective == ObjectiveFunction.MAX_DIVERSIFICATION:
            # Calculate diversification ratio
            weighted_avg_vol = np.dot(weights, np.sqrt(np.diag(cov_matrix)))
            return weighted_avg_vol / portfolio_vol if portfolio_vol > 0 else 1
        elif objective == ObjectiveFunction.MIN_CVAR:
            if not SCIPY_AVAILABLE:
                return portfolio_vol

            confidence_level = kwargs.get("confidence_level", 0.05)
            var_quantile = norm.ppf(confidence_level, portfolio_return, portfolio_vol)
            cvar = portfolio_return - portfolio_vol * norm.pdf(norm.ppf(confidence_level)) / confidence_level
            return -cvar  # Return positive CVaR value
        else:
            return 0.0

    def get_gradient_function(
        self,
        objective: ObjectiveFunction,
        returns: np.ndarray,
        cov_matrix: np.ndarray,
        risk_free_rate: float = 0.02,
    ) -> Callable[[np.ndarray], np.ndarray] | None:
        """
        Get gradient function for objective (if available).

        Args:
            objective: Type of objective function
            returns: Expected returns array
            cov_matrix: Covariance matrix
            risk_free_rate: Risk-free rate

        Returns:
            Gradient function or None if not available

        """
        if objective == ObjectiveFunction.MIN_VOLATILITY:
            return self._min_volatility_gradient(cov_matrix)
        elif objective == ObjectiveFunction.MAX_RETURN:
            return self._max_return_gradient(returns)
        else:
            # Gradients for other objectives are more complex
            return None

    def _min_volatility_gradient(self, cov_matrix: np.ndarray) -> Callable[[np.ndarray], np.ndarray]:
        """Create gradient function for minimum volatility objective."""

        def gradient_func(weights: np.ndarray) -> np.ndarray:
            portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))

            if portfolio_vol == 0:
                return np.zeros_like(weights)

            return np.dot(cov_matrix, weights) / portfolio_vol

        return gradient_func

    def _max_return_gradient(self, returns: np.ndarray) -> Callable[[np.ndarray], np.ndarray]:
        """Create gradient function for maximum return objective."""

        def gradient_func(weights: np.ndarray) -> np.ndarray:
            # Gradient of negative return
            return -returns

        return gradient_func

    def validate_objective_parameters(
        self,
        objective: ObjectiveFunction,
        returns: np.ndarray,
        cov_matrix: np.ndarray,
        **kwargs: Any,
    ) -> tuple[bool, list[str]]:
        """
        Validate parameters for objective function.

        Args:
            objective: Objective function type
            returns: Expected returns
            cov_matrix: Covariance matrix
            **kwargs: Additional parameters

        Returns:
            Tuple of (is_valid, list_of_errors)

        """
        errors = []

        # Basic validation
        if len(returns) != cov_matrix.shape[0] or len(returns) != cov_matrix.shape[1]:
            errors.append("Returns length must match covariance matrix dimensions")

        if not np.allclose(cov_matrix, cov_matrix.T):
            errors.append("Covariance matrix must be symmetric")

        eigenvals = np.linalg.eigvals(cov_matrix)
        if np.any(eigenvals <= 0):
            errors.append("Covariance matrix must be positive definite")

        # Objective-specific validation
        if objective == ObjectiveFunction.MIN_CVAR:
            confidence_level = kwargs.get("confidence_level", 0.05)
            if not (0 < confidence_level < 1):
                errors.append("Confidence level must be between 0 and 1")

        is_valid = len(errors) == 0
        return is_valid, errors
