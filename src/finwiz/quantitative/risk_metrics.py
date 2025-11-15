"""
Risk metrics and assessment models for portfolio rebalancing.

This module defines data models for risk warnings, thresholds, and assessments.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class RiskLevel(str, Enum):
    """Risk level enumeration."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskWarningType(str, Enum):
    """Risk warning type enumeration."""

    CONCENTRATION = "CONCENTRATION"
    TURNOVER = "TURNOVER"
    VOLATILITY = "VOLATILITY"
    TAX_IMPLICATIONS = "TAX_IMPLICATIONS"
    POSITION_SIZE = "POSITION_SIZE"
    MARKET_IMPACT = "MARKET_IMPACT"


class RiskWarning(BaseModel):
    """Individual risk warning."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    warning_type: RiskWarningType = Field(..., description="Type of risk warning")
    risk_level: RiskLevel = Field(..., description="Severity level of the risk")
    symbol: str | None = Field(None, description="Affected symbol (if applicable)")
    message: str = Field(..., min_length=10, description="Detailed warning message")
    recommendation: str = Field(..., min_length=10, description="Recommended action")
    impact_score: float = Field(..., ge=0, le=10, description="Impact score (0=minimal, 10=severe)")


class ConcentrationLimits(BaseModel):
    """Concentration limit configuration."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    max_single_position: float = Field(default=0.20, gt=0, le=1, description="Maximum weight for single position")
    max_sector_concentration: float = Field(default=0.30, gt=0, le=1, description="Maximum sector concentration")
    max_top_5_positions: float = Field(default=0.60, gt=0, le=1, description="Maximum weight of top 5 positions")
    min_number_positions: int = Field(default=5, ge=1, description="Minimum number of positions")


class TurnoverLimits(BaseModel):
    """Portfolio turnover limit configuration."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    max_annual_turnover: float = Field(default=1.0, gt=0, description="Maximum annual turnover ratio")
    max_monthly_turnover: float = Field(default=0.25, gt=0, description="Maximum monthly turnover ratio")
    warning_threshold: float = Field(default=0.5, gt=0, description="Turnover warning threshold")


class VolatilityThresholds(BaseModel):
    """Market volatility threshold configuration."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    low_volatility_threshold: float = Field(default=0.15, gt=0, description="Low volatility threshold (15%)")
    high_volatility_threshold: float = Field(default=0.30, gt=0, description="High volatility threshold (30%)")
    extreme_volatility_threshold: float = Field(default=0.50, gt=0, description="Extreme volatility threshold (50%)")


class TaxLossHarvestingConfig(BaseModel):
    """Tax-loss harvesting configuration."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    enable_tax_awareness: bool = Field(default=True, description="Enable tax-loss harvesting awareness")
    short_term_threshold_days: int = Field(default=365, ge=1, description="Short-term capital gains threshold")
    minimum_loss_threshold: float = Field(default=0.05, gt=0, description="Minimum loss threshold for harvesting")
    wash_sale_period_days: int = Field(default=30, ge=1, description="Wash sale rule period")


class RiskManagerConfig(BaseModel):
    """Risk manager configuration."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    concentration_limits: ConcentrationLimits = Field(default_factory=ConcentrationLimits)
    turnover_limits: TurnoverLimits = Field(default_factory=TurnoverLimits)
    volatility_thresholds: VolatilityThresholds = Field(default_factory=VolatilityThresholds)
    tax_config: TaxLossHarvestingConfig = Field(default_factory=TaxLossHarvestingConfig)
    enable_position_size_warnings: bool = Field(default=True, description="Enable position size warnings")
    enable_market_impact_warnings: bool = Field(default=True, description="Enable market impact warnings")


class RiskAssessment(BaseModel):
    """Comprehensive risk assessment result."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    overall_risk_score: float = Field(..., ge=0, le=10, description="Overall risk score")
    warnings: list[RiskWarning] = Field(default_factory=list, description="Risk warnings")
    concentration_risk: float = Field(..., ge=0, le=10, description="Concentration risk score")
    turnover_risk: float = Field(..., ge=0, le=10, description="Turnover risk score")
    volatility_risk: float = Field(..., ge=0, le=10, description="Volatility risk score")
    tax_efficiency_score: float = Field(..., ge=0, le=10, description="Tax efficiency score")
    recommended_tolerance_adjustment: float | None = Field(None, description="Recommended tolerance adjustment")
    rebalancing_frequency_recommendation: str = Field(..., description="Recommended rebalancing frequency")
