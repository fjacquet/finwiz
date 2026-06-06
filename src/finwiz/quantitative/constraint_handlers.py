"""
Constraint handlers for portfolio optimization.

This module provides constraint handling functionality for portfolio optimization,
including weight constraints, sector limits, turnover constraints, and other
portfolio construction constraints.
"""

from enum import StrEnum
from typing import Any

import numpy as np
from pydantic import BaseModel, Field

from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class ConstraintType(StrEnum):
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


class ConstraintHandler:
    """
    Handles portfolio optimization constraints.

    Provides methods to build and validate constraints for different
    optimization frameworks (scipy, cvxpy, etc.).
    """

    def __init__(self) -> None:
        """Initialize constraint handler."""
        pass

    def build_scipy_constraints(
        self,
        n_assets: int,
        constraints: list[OptimizationConstraint] | None = None,
        target_return: float | None = None,
        returns: np.ndarray | None = None,
    ) -> list[dict[str, Any]]:
        """
        Build constraints for scipy optimization.

        Args:
            n_assets: Number of assets in portfolio
            constraints: List of optimization constraints
            target_return: Target return for constraint (optional)
            returns: Expected returns array (required if target_return specified)

        Returns:
            List of scipy constraint dictionaries

        """
        constraints_list = []

        # Always add weights sum to 1 constraint
        constraints_list.append({"type": "eq", "fun": lambda x: np.sum(x) - 1.0})

        # Add target return constraint if specified
        if target_return is not None and returns is not None:
            constraints_list.append({"type": "eq", "fun": lambda x: np.dot(x, returns) - target_return})

        # Add custom constraints
        if constraints:
            for constraint in constraints:
                if constraint.constraint_type == ConstraintType.WEIGHT_SUM:
                    # Custom weight sum constraint
                    target_sum = constraint.parameters.get("target_sum", 1.0)
                    constraints_list.append({"type": "eq", "fun": lambda x, ts=target_sum: np.sum(x) - ts})

                elif constraint.constraint_type == ConstraintType.SECTOR_LIMITS:
                    # Sector constraint implementation
                    sector_map = constraint.parameters.get("sector_map", {})
                    limits = constraint.parameters.get("limits", {})

                    for sector, asset_indices in sector_map.items():
                        if sector in limits:
                            min_weight, max_weight = limits[sector]

                            # Minimum sector weight constraint
                            if min_weight > 0:
                                constraints_list.append(
                                    {
                                        "type": "ineq",
                                        "fun": lambda x, indices=asset_indices, min_w=min_weight: np.sum(x[indices]) - min_w,
                                    }
                                )

                            # Maximum sector weight constraint
                            if max_weight < 1.0:
                                constraints_list.append(
                                    {
                                        "type": "ineq",
                                        "fun": lambda x, indices=asset_indices, max_w=max_weight: max_w - np.sum(x[indices]),
                                    }
                                )

                elif constraint.constraint_type == ConstraintType.TURNOVER_LIMIT:
                    # Turnover constraint (requires current weights)
                    max_turnover = constraint.parameters.get("max_turnover", 0.5)
                    current_weights = constraint.parameters.get("current_weights")

                    if current_weights is not None:
                        current_weights = np.array(current_weights)
                        constraints_list.append(
                            {
                                "type": "ineq",
                                "fun": lambda x, curr_w=current_weights, max_to=max_turnover: max_to - np.sum(np.abs(x - curr_w)),
                            }
                        )

                elif constraint.constraint_type == ConstraintType.TRACKING_ERROR:
                    # Tracking error constraint (requires benchmark weights and covariance)
                    max_te = constraint.parameters.get("max_tracking_error", 0.05)
                    benchmark_weights = constraint.parameters.get("benchmark_weights")
                    covariance_matrix = constraint.parameters.get("covariance_matrix")

                    if benchmark_weights is not None and covariance_matrix is not None:
                        benchmark_weights = np.array(benchmark_weights)
                        covariance_matrix = np.array(covariance_matrix)

                        def tracking_error_constraint(x: np.ndarray) -> float:
                            active_weights = x - benchmark_weights
                            tracking_variance = np.dot(active_weights.T, np.dot(covariance_matrix, active_weights))
                            tracking_error = np.sqrt(tracking_variance)
                            return float(max_te - tracking_error)

                        constraints_list.append({"type": "ineq", "fun": tracking_error_constraint})

        return constraints_list

    def build_weight_bounds(
        self,
        n_assets: int,
        constraints: list[OptimizationConstraint] | None = None,
        default_bounds: tuple[float, float] = (0.0, 1.0),
    ) -> list[tuple[float, float]]:
        """
        Build weight bounds for optimization.

        Args:
            n_assets: Number of assets
            constraints: List of optimization constraints
            default_bounds: Default bounds for all assets

        Returns:
            List of (min_weight, max_weight) tuples for each asset

        """
        bounds = [default_bounds] * n_assets

        if constraints:
            for constraint in constraints:
                if constraint.constraint_type == ConstraintType.WEIGHT_BOUNDS:
                    # Asset-specific weight bounds
                    asset_bounds = constraint.parameters.get("bounds", {})

                    for asset_idx, (min_w, max_w) in asset_bounds.items():
                        if 0 <= asset_idx < n_assets:
                            bounds[asset_idx] = (min_w, max_w)

        return bounds

    def validate_constraints(
        self,
        weights: np.ndarray,
        constraints: list[OptimizationConstraint] | None = None,
        tolerance: float = 1e-6,
    ) -> tuple[bool, list[str]]:
        """
        Validate that portfolio weights satisfy constraints.

        Args:
            weights: Portfolio weights to validate
            constraints: List of constraints to check
            tolerance: Numerical tolerance for constraint violations

        Returns:
            Tuple of (is_valid, list_of_violations)

        """
        violations = []

        # Check weights sum to 1
        weight_sum = np.sum(weights)
        if abs(weight_sum - 1.0) > tolerance:
            violations.append(f"Weights sum to {weight_sum:.6f}, expected 1.0")

        # Check non-negative weights (assuming long-only by default)
        if np.any(weights < -tolerance):
            negative_indices = np.where(weights < -tolerance)[0]
            violations.append(f"Negative weights at indices: {negative_indices.tolist()}")

        # Check custom constraints
        if constraints:
            for constraint in constraints:
                if constraint.constraint_type == ConstraintType.WEIGHT_BOUNDS:
                    asset_bounds = constraint.parameters.get("bounds", {})

                    for asset_idx, (min_w, max_w) in asset_bounds.items():
                        if 0 <= asset_idx < len(weights):
                            weight = weights[asset_idx]
                            if weight < min_w - tolerance:
                                violations.append(f"Asset {asset_idx} weight {weight:.6f} below minimum {min_w}")
                            if weight > max_w + tolerance:
                                violations.append(f"Asset {asset_idx} weight {weight:.6f} above maximum {max_w}")

                elif constraint.constraint_type == ConstraintType.SECTOR_LIMITS:
                    sector_map = constraint.parameters.get("sector_map", {})
                    limits = constraint.parameters.get("limits", {})

                    for sector, asset_indices in sector_map.items():
                        if sector in limits:
                            min_weight, max_weight = limits[sector]
                            sector_weight = np.sum(weights[asset_indices])

                            if sector_weight < min_weight - tolerance:
                                violations.append(f"Sector {sector} weight {sector_weight:.6f} below minimum {min_weight}")
                            if sector_weight > max_weight + tolerance:
                                violations.append(f"Sector {sector} weight {sector_weight:.6f} above maximum {max_weight}")

                elif constraint.constraint_type == ConstraintType.TURNOVER_LIMIT:
                    max_turnover = constraint.parameters.get("max_turnover", 0.5)
                    current_weights = constraint.parameters.get("current_weights")

                    if current_weights is not None:
                        current_weights = np.array(current_weights)
                        turnover = np.sum(np.abs(weights - current_weights))

                        if turnover > max_turnover + tolerance:
                            violations.append(f"Turnover {turnover:.6f} exceeds maximum {max_turnover}")

        is_valid = len(violations) == 0
        return is_valid, violations
