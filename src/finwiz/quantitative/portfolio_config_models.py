"""
Data models and enums for portfolio configuration management.

This module contains Pydantic models and enums used throughout
the portfolio configuration system.
"""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from finwiz.schemas.portfolio_rebalancing import PortfolioConfiguration, RebalancingMethod


class StrategyTemplate(StrEnum):
    """Pre-defined portfolio strategy templates."""

    BALANCED = "balanced"
    AGGRESSIVE_GROWTH = "aggressive_growth"
    CONSERVATIVE = "conservative"
    DIVIDEND_FOCUSED = "dividend_focused"
    SECTOR_ROTATION = "sector_rotation"
    EQUAL_WEIGHT = "equal_weight"
    MARKET_CAP_WEIGHTED = "market_cap_weighted"
    CUSTOM = "custom"


class ConfigurationStatus(StrEnum):
    """Portfolio configuration status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
    DRAFT = "draft"


class PortfolioConfigurationMetadata(BaseModel):
    """Metadata for portfolio configuration."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    config_id: str = Field(..., description="Unique configuration identifier")
    name: str = Field(..., min_length=1, max_length=100, description="Configuration name")
    description: str = Field(default="", max_length=500, description="Configuration description")
    strategy_template: StrategyTemplate = Field(default=StrategyTemplate.CUSTOM, description="Strategy template used")
    status: ConfigurationStatus = Field(default=ConfigurationStatus.DRAFT, description="Configuration status")

    # Versioning
    version: int = Field(default=1, ge=1, description="Configuration version number")
    parent_config_id: str | None = Field(None, description="Parent configuration ID for versioning")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    created_by: str = Field(default="system", description="Creator identifier")

    # Tags and categorization
    tags: list[str] = Field(default_factory=list, max_length=10, description="Configuration tags")
    category: str = Field(default="general", description="Configuration category")

    # Performance tracking
    last_rebalanced: datetime | None = Field(None, description="Last rebalancing timestamp")
    performance_notes: str = Field(default="", max_length=1000, description="Performance notes")

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        """Validate tags format."""
        validated_tags = []
        for tag in v:
            clean_tag = tag.strip().lower()
            if clean_tag and len(clean_tag) <= 20:
                validated_tags.append(clean_tag)
        return validated_tags


class PortfolioConfigurationVersion(BaseModel):
    """Versioned portfolio configuration."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    metadata: PortfolioConfigurationMetadata = Field(..., description="Configuration metadata")
    configuration: PortfolioConfiguration = Field(..., description="Portfolio configuration")
    change_summary: str = Field(default="", description="Summary of changes in this version")
    validation_errors: list[str] = Field(default_factory=list, description="Validation errors if any")


class ConfigurationTemplate(BaseModel):
    """Template for creating portfolio configurations."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    template_id: str = Field(..., description="Template identifier")
    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    strategy_type: StrategyTemplate = Field(..., description="Strategy type")

    # Template configuration
    target_weights: dict[str, float] = Field(..., description="Default target weights")
    global_tolerance: float = Field(default=0.05, description="Default tolerance")
    rebalancing_method: RebalancingMethod = Field(default=RebalancingMethod.MINIMIZE_TRADES, description="Default rebalancing method")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now, description="Template creation date")
    is_system_template: bool = Field(default=False, description="Whether this is a system template")
    usage_count: int = Field(default=0, ge=0, description="Number of times template has been used")
