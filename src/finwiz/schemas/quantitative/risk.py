"""Risk management and scenario analysis models for quantitative analysis."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


# Risk Management Models
class RiskWarning(BaseModel):
    """Individual risk warning."""

    warning_type: Literal["concentration", "volatility", "drawdown", "correlation", "liquidity"] = Field(..., description="Type of risk warning")
    severity: Literal["low", "medium", "high", "critical"] = Field(..., description="Severity level")
    message: str = Field(..., description="Warning message")
    affected_assets: list[str] = Field(..., description="Assets affected by this warning")
    recommended_action: str = Field(..., description="Recommended action to address warning")
    threshold_breached: float | None = Field(None, description="Threshold value that was breached")
    current_value: float | None = Field(None, description="Current value that triggered warning")


class ConcentrationLimits(BaseModel):
    """Concentration limit configuration."""

    max_single_position: float = Field(0.1, description="Maximum weight for single position")
    max_sector_exposure: float = Field(0.3, description="Maximum exposure to single sector")
    max_country_exposure: float = Field(0.5, description="Maximum exposure to single country")
    min_number_positions: int = Field(10, description="Minimum number of positions")


class TurnoverLimits(BaseModel):
    """Portfolio turnover limit configuration."""

    max_monthly_turnover: float = Field(0.2, description="Maximum monthly turnover")
    max_annual_turnover: float = Field(1.0, description="Maximum annual turnover")
    transaction_cost_threshold: float = Field(0.01, description="Transaction cost threshold")


class VolatilityThresholds(BaseModel):
    """Market volatility threshold configuration."""

    low_volatility: float = Field(0.1, description="Low volatility threshold")
    medium_volatility: float = Field(0.2, description="Medium volatility threshold")
    high_volatility: float = Field(0.3, description="High volatility threshold")
    extreme_volatility: float = Field(0.5, description="Extreme volatility threshold")


class RiskManagerConfig(BaseModel):
    """Risk manager configuration."""

    concentration_limits: ConcentrationLimits = Field(default_factory=lambda: ConcentrationLimits())
    turnover_limits: TurnoverLimits = Field(default_factory=lambda: TurnoverLimits())
    volatility_thresholds: VolatilityThresholds = Field(default_factory=lambda: VolatilityThresholds())

    # Global settings
    enable_risk_monitoring: bool = Field(True, description="Enable risk monitoring")
    alert_frequency: Literal["real_time", "daily", "weekly"] = Field("daily", description="Alert frequency")


class RiskAssessment(BaseModel):
    """Comprehensive risk assessment result."""

    assessment_date: datetime = Field(..., description="Date of risk assessment")
    portfolio_id: str = Field(..., description="Portfolio identifier")

    # Risk metrics
    portfolio_volatility: float = Field(..., description="Portfolio volatility")
    var_95: float = Field(..., description="Value at Risk (95%)")
    cvar_95: float = Field(..., description="Conditional Value at Risk (95%)")
    max_drawdown: float = Field(..., description="Maximum drawdown")

    # Risk warnings
    warnings: list[RiskWarning] = Field(default_factory=list, description="Risk warnings")
    overall_risk_level: Literal["low", "medium", "high", "critical"] = Field(..., description="Overall risk level")

    # Recommendations
    risk_reduction_suggestions: list[str] = Field(default_factory=list, description="Risk reduction suggestions")
    position_adjustments: dict[str, float] = Field(default_factory=dict, description="Suggested position adjustments")


# Scenario Analysis Models
class ScenarioParameters(BaseModel):
    """Parameters for scenario analysis."""

    scenario_name: str = Field(..., description="Name of the scenario")
    description: str = Field(..., description="Description of the scenario")

    # Market parameters
    market_shock: float = Field(0.0, description="Market shock percentage")
    volatility_multiplier: float = Field(1.0, description="Volatility multiplier")
    correlation_adjustment: float = Field(0.0, description="Correlation adjustment")

    # Asset-specific shocks
    asset_shocks: dict[str, float] = Field(default_factory=dict, description="Asset-specific shocks")
    sector_shocks: dict[str, float] = Field(default_factory=dict, description="Sector-specific shocks")

    # Time parameters
    shock_duration: int = Field(1, description="Duration of shock in periods")
    recovery_periods: int = Field(0, description="Number of recovery periods")


class MonteCarloResult(BaseModel):
    """Result of Monte Carlo simulation."""

    simulation_name: str = Field(..., description="Name of the simulation")
    num_simulations: int = Field(..., description="Number of simulations run")
    time_horizon: int = Field(..., description="Time horizon in periods")

    # Results statistics
    mean_return: float = Field(..., description="Mean return across simulations")
    median_return: float = Field(..., description="Median return across simulations")
    std_return: float = Field(..., description="Standard deviation of returns")

    # Percentile results
    percentile_5: float = Field(..., description="5th percentile return")
    percentile_25: float = Field(..., description="25th percentile return")
    percentile_75: float = Field(..., description="75th percentile return")
    percentile_95: float = Field(..., description="95th percentile return")

    # Risk metrics
    probability_of_loss: float = Field(..., description="Probability of loss")
    expected_shortfall: float = Field(..., description="Expected shortfall (CVaR)")
    maximum_loss: float = Field(..., description="Maximum loss observed")

    # Simulation metadata
    random_seed: int | None = Field(None, description="Random seed used")
    execution_time: float = Field(..., description="Execution time in seconds")
