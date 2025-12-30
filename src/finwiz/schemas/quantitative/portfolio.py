"""Portfolio optimization models for quantitative analysis."""

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class OptimizationConstraint(BaseModel):
    """Portfolio optimization constraint."""

    constraint_type: Literal["weight", "turnover", "sector", "risk"] = Field(..., description="Type of constraint")
    target: str = Field(..., description="Target asset or constraint identifier")
    min_value: float | None = Field(None, description="Minimum value for constraint")
    max_value: float | None = Field(None, description="Maximum value for constraint")
    exact_value: float | None = Field(None, description="Exact value for constraint")


class PortfolioInputs(BaseModel):
    """Inputs for portfolio optimization."""

    assets: list[str] = Field(..., description="List of asset symbols")
    expected_returns: list[float] = Field(..., description="Expected returns for each asset")
    covariance_matrix: list[list[float]] = Field(..., description="Covariance matrix")
    constraints: list[OptimizationConstraint] = Field(default_factory=list, description="Optimization constraints")

    # Optimization parameters
    risk_aversion: float = Field(1.0, description="Risk aversion parameter")
    target_return: float | None = Field(None, description="Target return for optimization")
    target_risk: float | None = Field(None, description="Target risk for optimization")

    @model_validator(mode="after")
    def validate_dimensions(self) -> "PortfolioInputs":
        """Validate that dimensions match."""
        n_assets = len(self.assets)
        if len(self.expected_returns) != n_assets:
            raise ValueError("Expected returns length must match number of assets")
        if len(self.covariance_matrix) != n_assets:
            raise ValueError("Covariance matrix rows must match number of assets")
        for i, row in enumerate(self.covariance_matrix):
            if len(row) != n_assets:
                raise ValueError(f"Covariance matrix row {i} length must match number of assets")
        return self


class PortfolioMetrics(BaseModel):
    """Portfolio performance metrics."""

    expected_return: float = Field(..., description="Expected portfolio return")
    volatility: float = Field(..., description="Portfolio volatility")
    sharpe_ratio: float = Field(..., description="Sharpe ratio")

    # Risk metrics
    var_95: float = Field(..., description="Value at Risk (95%)")
    cvar_95: float = Field(..., description="Conditional Value at Risk (95%)")
    max_drawdown: float = Field(..., description="Maximum drawdown")

    # Diversification metrics
    diversification_ratio: float = Field(..., description="Diversification ratio")
    concentration_index: float = Field(..., description="Concentration index (HHI)")
    effective_number_assets: float = Field(..., description="Effective number of assets")


class OptimizationResult(BaseModel):
    """Result of portfolio optimization."""

    weights: dict[str, float] = Field(..., description="Optimal portfolio weights")
    metrics: PortfolioMetrics = Field(..., description="Portfolio performance metrics")

    # Optimization details
    optimization_method: str = Field(..., description="Optimization method used")
    convergence_status: str = Field(..., description="Optimization convergence status")
    iterations: int = Field(..., description="Number of optimization iterations")

    # Constraints satisfaction
    constraints_satisfied: bool = Field(..., description="Whether all constraints were satisfied")
    constraint_violations: list[str] = Field(default_factory=list, description="List of constraint violations")


class EfficientFrontierPoint(BaseModel):
    """Point on the efficient frontier."""

    expected_return: float = Field(..., description="Expected return for this point")
    volatility: float = Field(..., description="Volatility for this point")
    sharpe_ratio: float = Field(..., description="Sharpe ratio for this point")
    weights: dict[str, float] = Field(..., description="Portfolio weights for this point")
