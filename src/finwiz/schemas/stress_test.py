"""Pydantic models for portfolio stress testing scenarios and results."""

from enum import StrEnum

from pydantic import BaseModel, Field


class StressScenarioType(StrEnum):
    """Types of stress test scenarios."""

    MARKET_CRASH = "market_crash"
    RATE_SHOCK = "rate_shock"
    SECTOR_SHOCK = "sector_shock"


class StressTestScenario(BaseModel):
    """Definition of a single stress test scenario."""

    name: str = Field(description="Human-readable scenario name")
    scenario_type: StressScenarioType
    description: str = Field(description="What this scenario simulates")

    # Market crash parameters
    market_shock_pct: float = Field(default=0.0, description="Broad market shock as decimal (e.g. -0.20)")

    # Rate shock parameters
    rate_change_bps: int = Field(default=0, description="Interest rate change in basis points (e.g. 200 = +2%)")

    # Sector shock parameters
    target_sector: str | None = Field(default=None, description="GICS sector to shock")
    sector_shock_pct: float = Field(default=0.0, description="Sector-specific shock as decimal")
    non_target_spillover_pct: float = Field(default=0.0, description="Spillover impact on non-target sectors")


class HoldingStressImpact(BaseModel):
    """Projected impact of a stress scenario on a single holding."""

    ticker: str
    asset_type: str = Field(description="stock, etf, or crypto")
    sector: str | None = None
    beta: float | None = None
    current_weight_pct: float = Field(description="Portfolio weight as percentage")
    projected_change_pct: float = Field(description="Projected price change as decimal")
    projected_pnl: float = Field(default=0.0, description="Projected P&L contribution")
    sensitivity_label: str = Field(description="HIGH, MEDIUM, or LOW")


class PortfolioStressTestResult(BaseModel):
    """Aggregated result of running a stress scenario against a portfolio."""

    scenario: StressTestScenario
    total_portfolio_impact_pct: float = Field(description="Weighted portfolio impact as decimal")
    total_projected_pnl: float = Field(default=0.0)
    holding_impacts: list[HoldingStressImpact] = Field(default_factory=list)
    most_affected: list[str] = Field(default_factory=list, description="Top 3 most impacted tickers")
    least_affected: list[str] = Field(default_factory=list, description="Top 3 least impacted tickers")
    run_timestamp: str = Field(default="")
