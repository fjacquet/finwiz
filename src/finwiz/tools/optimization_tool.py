"""
Portfolio optimization tool for CrewAI agents.

This module provides portfolio optimization capabilities using modern portfolio theory
and various optimization algorithms to find optimal asset allocations.
"""

import json
from typing import Any

import numpy as np
from crewai.tools import BaseTool
from pydantic import BaseModel

from finwiz.schemas.tools import OptimizationInput
from finwiz.tools.logger import get_logger


class OptimizationTool(BaseTool):
    """
    Tool for portfolio optimization using modern portfolio theory.

    This tool provides CrewAI agents with the ability to optimize portfolio
    allocations based on various criteria including risk-return optimization,
    risk parity, and custom constraints.
    """

    name: str = "Portfolio Optimization Tool"
    description: str = (
        "Optimize portfolio allocations using modern portfolio theory. "
        "Supports mean-variance optimization, risk parity, and custom constraints. "
        "Provides optimal weights and expected portfolio characteristics."
    )
    args_schema: type[BaseModel] = OptimizationInput

    def _run(
        self,
        assets: list[str],
        expected_returns: dict[str, float] | None = None,
        risk_tolerance: float = 0.5,
        optimization_method: str = "mean_variance",
        constraints: dict[str, Any] | None = None,
        target_return: float | None = None,
        max_weight: float = 0.4,
        min_weight: float = 0.0,
    ) -> str:
        """
        Execute portfolio optimization.

        Args:
            assets: List of asset symbols to optimize
            expected_returns: Expected returns for each asset (optional)
            risk_tolerance: Risk tolerance (0.0 = risk averse, 1.0 = risk seeking)
            optimization_method: Optimization method
            constraints: Additional constraints
            target_return: Target return for optimization
            max_weight: Maximum weight per asset
            min_weight: Minimum weight per asset

        Returns:
            JSON string with optimization results

        """
        try:
            logger.info(f"Starting portfolio optimization for {len(assets)} assets")

            # Validate inputs
            input_data = OptimizationInput(
                assets=assets,
                expected_returns=expected_returns,
                risk_tolerance=risk_tolerance,
                optimization_method=optimization_method,
                constraints=constraints,
                target_return=target_return,
                max_weight=max_weight,
                min_weight=min_weight,
            )

            # Perform optimization based on method
            if input_data.optimization_method == "mean_variance":
                result = self._mean_variance_optimization(input_data)
            elif input_data.optimization_method == "risk_parity":
                result = self._risk_parity_optimization(input_data)
            elif input_data.optimization_method == "equal_weight":
                result = self._equal_weight_optimization(input_data)
            else:
                raise ValueError(f"Unknown optimization method: {input_data.optimization_method}")

            logger.info("Portfolio optimization completed successfully")
            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"Portfolio optimization failed: {e}")
            error_result = {"success": False, "error": str(e), "error_type": type(e).__name__}
            return json.dumps(error_result, indent=2)

    def _mean_variance_optimization(self, input_data: OptimizationInput) -> dict[str, Any]:
        """Perform mean-variance optimization."""
        try:
            n_assets = len(input_data.assets)

            # Use provided expected returns or generate estimates
            if input_data.expected_returns:
                returns = np.array([input_data.expected_returns.get(asset, 0.08) for asset in input_data.assets])
            else:
                # Default expected returns (simplified)
                returns = np.random.normal(0.08, 0.02, n_assets)  # 8% +/- 2%

            # Generate simplified covariance matrix (in practice, use historical data)
            # This is a placeholder implementation
            volatilities = np.random.uniform(0.15, 0.25, n_assets)  # 15-25% volatility
            correlations = np.random.uniform(0.3, 0.7, (n_assets, n_assets))
            np.fill_diagonal(correlations, 1.0)
            cov_matrix = np.outer(volatilities, volatilities) * correlations

            # Simple mean-variance optimization (simplified)
            # In practice, use scipy.optimize or cvxpy
            2 * (1 - input_data.risk_tolerance)  # Convert to risk aversion parameter

            # Equal weight as starting point, then adjust based on risk tolerance
            base_weights = np.ones(n_assets) / n_assets

            # Adjust weights based on expected returns and risk tolerance
            return_adjustment = (returns - np.mean(returns)) * input_data.risk_tolerance
            adjusted_weights = base_weights + return_adjustment * 0.1

            # Normalize and apply constraints
            adjusted_weights = np.maximum(adjusted_weights, input_data.min_weight)
            adjusted_weights = np.minimum(adjusted_weights, input_data.max_weight)
            adjusted_weights = adjusted_weights / np.sum(adjusted_weights)  # Normalize

            # Calculate portfolio metrics
            portfolio_return = np.dot(adjusted_weights, returns)
            portfolio_risk = np.sqrt(np.dot(adjusted_weights, np.dot(cov_matrix, adjusted_weights)))
            sharpe_ratio = portfolio_return / portfolio_risk if portfolio_risk > 0 else 0

            # Create weight dictionary
            optimal_weights = {asset: float(weight) for asset, weight in zip(input_data.assets, adjusted_weights)}

            return {
                "success": True,
                "optimization_method": "mean_variance",
                "optimal_weights": optimal_weights,
                "portfolio_metrics": {
                    "expected_return": float(portfolio_return),
                    "expected_risk": float(portfolio_risk),
                    "sharpe_ratio": float(sharpe_ratio),
                    "risk_tolerance_used": input_data.risk_tolerance,
                },
                "constraints_applied": {
                    "max_weight": input_data.max_weight,
                    "min_weight": input_data.min_weight,
                    "weights_sum": float(np.sum(adjusted_weights)),
                },
                "recommendations": [
                    f"Largest allocation: {max(optimal_weights.items(), key=lambda x: x[1])[0]} ({max(optimal_weights.values()):.1%})",
                    ("Most diversified allocation" if max(optimal_weights.values()) < 0.3 else "Consider further diversification"),
                    f"Expected Sharpe ratio: {sharpe_ratio:.2f}",
                ],
                "note": ("This is a simplified optimization. Production implementation should use historical data and advanced optimization libraries."),
            }

        except Exception as e:
            logger.error(f"Error in mean-variance optimization: {e}")
            return {"success": False, "error": str(e)}

    def _risk_parity_optimization(self, input_data: OptimizationInput) -> dict[str, Any]:
        """Perform risk parity optimization."""
        try:
            n_assets = len(input_data.assets)

            # Risk parity: equal risk contribution from each asset
            # Simplified implementation - equal weights adjusted for volatility

            # Generate simplified volatility estimates
            volatilities = np.random.uniform(0.15, 0.25, n_assets)

            # Inverse volatility weighting (simplified risk parity)
            inv_vol_weights = 1 / volatilities
            risk_parity_weights = inv_vol_weights / np.sum(inv_vol_weights)

            # Apply constraints
            risk_parity_weights = np.maximum(risk_parity_weights, input_data.min_weight)
            risk_parity_weights = np.minimum(risk_parity_weights, input_data.max_weight)
            risk_parity_weights = risk_parity_weights / np.sum(risk_parity_weights)

            # Create weight dictionary
            optimal_weights = {asset: float(weight) for asset, weight in zip(input_data.assets, risk_parity_weights)}

            # Calculate portfolio metrics (simplified)
            portfolio_risk = np.sqrt(np.mean(volatilities**2))  # Simplified
            expected_return = 0.08  # Placeholder

            return {
                "success": True,
                "optimization_method": "risk_parity",
                "optimal_weights": optimal_weights,
                "portfolio_metrics": {
                    "expected_return": expected_return,
                    "expected_risk": float(portfolio_risk),
                    "risk_contribution_balance": "Equal risk contribution target",
                },
                "constraints_applied": {
                    "max_weight": input_data.max_weight,
                    "min_weight": input_data.min_weight,
                    "weights_sum": float(np.sum(risk_parity_weights)),
                },
                "recommendations": [
                    "Risk parity approach balances risk contribution across assets",
                    "Lower volatility assets receive higher weights",
                    "Good for risk-conscious investors",
                ],
                "note": "Simplified risk parity implementation. Production version should use iterative optimization.",
            }

        except Exception as e:
            logger.error(f"Error in risk parity optimization: {e}")
            return {"success": False, "error": str(e)}

    def _equal_weight_optimization(self, input_data: OptimizationInput) -> dict[str, Any]:
        """Perform equal weight optimization."""
        try:
            n_assets = len(input_data.assets)
            equal_weights = np.ones(n_assets) / n_assets

            # Apply constraints if needed
            if input_data.max_weight < (1.0 / n_assets):
                # If max weight constraint is binding, adjust
                equal_weights = np.full(n_assets, input_data.max_weight)
                equal_weights = equal_weights / np.sum(equal_weights)

            # Create weight dictionary
            optimal_weights = {asset: float(weight) for asset, weight in zip(input_data.assets, equal_weights)}

            return {
                "success": True,
                "optimization_method": "equal_weight",
                "optimal_weights": optimal_weights,
                "portfolio_metrics": {
                    "expected_return": 0.08,  # Placeholder
                    "expected_risk": 0.18,  # Placeholder
                    "diversification_benefit": "Maximum diversification across assets",
                },
                "constraints_applied": {
                    "max_weight": input_data.max_weight,
                    "min_weight": input_data.min_weight,
                    "weights_sum": float(np.sum(equal_weights)),
                },
                "recommendations": [
                    "Equal weighting provides maximum diversification",
                    "Simple and robust approach",
                    "Good baseline for comparison with other strategies",
                ],
                "note": "Equal weight strategy assumes no superior information about expected returns.",
            }

        except Exception as e:
            logger.error(f"Error in equal weight optimization: {e}")
            return {"success": False, "error": str(e)}


def get_optimization_tool() -> OptimizationTool:
    """Get an instance of the optimization tool."""
    return OptimizationTool()


logger = get_logger(__name__)
