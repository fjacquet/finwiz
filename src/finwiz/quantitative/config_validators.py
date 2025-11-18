"""
Validators for quantitative analysis configuration.

This module provides Pydantic validators for configuration classes.
"""

from typing import Any

from pydantic import validator

from finwiz.quantitative.config_defaults import get_default_provider_configs


class ConfigValidators:
    """Collection of validators for configuration classes."""

    @staticmethod
    @validator("data_provider_configs", pre=True, always=True)
    def setup_default_provider_configs(cls, v: dict, values: dict[str, Any]) -> dict[str, Any]:
        """Set up default configurations for data providers."""
        if not v:
            v = {}

        # Get default configurations
        default_configs = get_default_provider_configs()

        # Merge with provided configs
        for provider, config in default_configs.items():
            if provider not in v:
                v[provider] = config

        return v

    @staticmethod
    @validator("cache_config", pre=True, always=True)
    def setup_cache_directory(cls, v: Any):
        """Ensure cache directory exists."""
        from finwiz.quantitative.config_defaults import CacheConfig

        if isinstance(v, dict):
            v = CacheConfig(**v)
        elif v is None:
            v = CacheConfig()

        # Create cache directory if it doesn't exist
        v.cache_dir.mkdir(parents=True, exist_ok=True)

        return v

    @staticmethod
    @validator("position_sizing_method")
    def validate_position_sizing_method(cls, v: str) -> str:
        """Validate position sizing method."""
        valid_methods = ["fixed_amount", "percent_of_portfolio", "kelly_criterion", "volatility_adjusted"]
        if v not in valid_methods:
            raise ValueError(f"Position sizing method must be one of: {valid_methods}")
        return v

    @staticmethod
    @validator("rebalancing_frequency")
    def validate_rebalancing_frequency(cls, v: str) -> str:
        """Validate rebalancing frequency."""
        valid_frequencies = ["daily", "weekly", "monthly", "quarterly", "annually"]
        if v not in valid_frequencies:
            raise ValueError(f"Rebalancing frequency must be one of: {valid_frequencies}")
        return v
