"""Configuration management for deep portfolio analysis."""

import logging
import os

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class PortfolioAnalysisConfig(BaseModel):
    """
    Configuration for deep portfolio analysis features.

    Deep analysis provides comprehensive crew-based evaluation of portfolio holdings
    including fundamental analysis, technical indicators, and risk assessment.

    When disabled, the system uses shallow validation which:
    - Only validates ticker existence
    - Assigns conservative baseline grades (B for valid, F for invalid)
    - Does not provide detailed metrics or alternatives

    Enable deep analysis for production use to get accurate grades and recommendations.
    """

    deep_analysis_enabled: bool = Field(
        default=True,  # Changed from False to True for better default experience
        description="Enable deep crew-based analysis for portfolio holdings (recommended for production)",
    )

    enable_alternatives: bool = Field(default=True, description="Enable A+ alternative matching for underperforming holdings")

    cache_enabled: bool = Field(default=True, description="Enable caching of crew analysis results")

    cache_ttl_hours: int = Field(
        default=24,
        ge=1,
        le=168,  # Max 1 week
        description="Cache time-to-live in hours",
    )

    max_alternatives: int = Field(default=5, ge=1, le=10, description="Maximum number of alternatives to return per holding")

    deep_analysis_batch_size: int = Field(default=10, ge=1, le=50, description="Number of holdings to process in each batch")

    @field_validator("deep_analysis_enabled", mode="before")
    @classmethod
    def validate_deep_analysis_enabled(cls, v: str | bool) -> bool:
        """Validate deep analysis enabled flag."""
        if isinstance(v, str):
            return v.strip().lower() in {"1", "true", "yes", "on"}
        return bool(v)

    @field_validator("enable_alternatives", mode="before")
    @classmethod
    def validate_enable_alternatives(cls, v: str | bool) -> bool:
        """Validate enable alternatives flag."""
        if isinstance(v, str):
            return v.strip().lower() in {"1", "true", "yes", "on"}
        return bool(v)

    @field_validator("cache_enabled", mode="before")
    @classmethod
    def validate_cache_enabled(cls, v: str | bool) -> bool:
        """Validate cache enabled flag."""
        if isinstance(v, str):
            return v.strip().lower() in {"1", "true", "yes", "on"}
        return bool(v)

    @classmethod
    def from_env(cls) -> "PortfolioAnalysisConfig":
        """
        Load configuration from environment variables with sensible defaults.

        Environment Variables:
            DEEP_PORTFOLIO_ANALYSIS: Enable deep analysis (default: true)
            PORTFOLIO_ENABLE_ALTERNATIVES: Enable A+ alternatives (default: true)
            PORTFOLIO_CACHE_ENABLED: Enable result caching (default: true)
            PORTFOLIO_CACHE_TTL_HOURS: Cache TTL in hours (default: 24)
            PORTFOLIO_MAX_ALTERNATIVES: Max alternatives per holding (default: 5)
            PORTFOLIO_DEEP_ANALYSIS_BATCH_SIZE: Batch size for processing (default: 10)

        Returns:
            PortfolioAnalysisConfig instance with loaded settings

        """
        try:
            # Parse integer values with validation
            cache_ttl = int(os.getenv("PORTFOLIO_CACHE_TTL_HOURS", "24"))
            max_alt = int(os.getenv("PORTFOLIO_MAX_ALTERNATIVES", "5"))
            batch_size = int(os.getenv("PORTFOLIO_DEEP_ANALYSIS_BATCH_SIZE", "10"))

            # Validate ranges - raise ValueError for out-of-range values
            if not (1 <= cache_ttl <= 168):
                raise ValueError(f"cache_ttl_hours {cache_ttl} out of range [1, 168]")
            if not (1 <= max_alt <= 10):
                raise ValueError(f"max_alternatives {max_alt} out of range [1, 10]")
            if not (1 <= batch_size <= 50):
                raise ValueError(f"deep_analysis_batch_size {batch_size} out of range [1, 50]")

            # Pass raw string values - field_validators handle str→bool coercion
            # This allows "true", "yes", "1", "on" and their variants
            config = cls(
                deep_analysis_enabled=os.getenv("DEEP_PORTFOLIO_ANALYSIS", "true"),  # type: ignore[arg-type]
                enable_alternatives=os.getenv("PORTFOLIO_ENABLE_ALTERNATIVES", "true"),  # type: ignore[arg-type]
                cache_enabled=os.getenv("PORTFOLIO_CACHE_ENABLED", "true"),  # type: ignore[arg-type]
                cache_ttl_hours=cache_ttl,
                max_alternatives=max_alt,
                deep_analysis_batch_size=batch_size,
            )

            # Log active configuration
            logger.info("Portfolio Analysis Configuration loaded:")
            logger.info(f"  Deep Analysis Enabled: {config.deep_analysis_enabled}")
            logger.info(f"  Enable Alternatives: {config.enable_alternatives}")
            logger.info(f"  Cache Enabled: {config.cache_enabled}")
            logger.info(f"  Cache TTL Hours: {config.cache_ttl_hours}")
            logger.info(f"  Max Alternatives: {config.max_alternatives}")
            logger.info(f"  Batch Size: {config.deep_analysis_batch_size}")

            return config

        except ValueError as e:
            logger.warning(f"Invalid configuration value, using defaults: {e}")
            # Return default configuration if validation fails
            default_config = cls()
            logger.info("Using default portfolio analysis configuration")
            return default_config
        except Exception as e:
            logger.error(f"Error loading configuration, using defaults: {e}")
            return cls()

    def validate_config(self) -> None:
        """Validate configuration values and log warnings for potential issues."""
        warnings = []

        if self.deep_analysis_enabled and not self.cache_enabled:
            warnings.append("Deep analysis is enabled but caching is disabled. This may result in high API costs and slow performance.")

        if self.cache_ttl_hours < 6:
            warnings.append(f"Cache TTL is very short ({self.cache_ttl_hours}h). Consider increasing for better performance.")

        if self.deep_analysis_batch_size > 20:
            warnings.append(f"Large batch size ({self.deep_analysis_batch_size}) may cause rate limiting issues with external APIs.")

        if self.max_alternatives > 7:
            warnings.append(f"High number of alternatives ({self.max_alternatives}) may overwhelm users with too many choices.")

        # Log warnings
        for warning in warnings:
            logger.warning(f"Configuration warning: {warning}")

        if not warnings:
            logger.info("Configuration validation passed without warnings")


# Global configuration instance
_config: PortfolioAnalysisConfig | None = None
