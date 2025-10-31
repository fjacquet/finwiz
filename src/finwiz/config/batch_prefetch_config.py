"""
Batch prefetch configuration module.

This module provides configuration management for batch data pre-fetching,
including environment variable loading, validation, and logging.

Requirements: 17.57, 17.58, 17.59, 17.60
"""

import os
from dataclasses import dataclass

from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


@dataclass
class BatchPrefetchConfig:
    """
    Configuration for batch data pre-fetching.

    Attributes:
        enabled: Whether batch pre-fetching is enabled (default: True)
        alpha_vantage_rate_limit: Alpha Vantage API rate limit in calls per minute (default: 5)
        min_holdings_for_batch: Minimum number of holdings to trigger batch mode (default: 10)

    """

    enabled: bool = True
    alpha_vantage_rate_limit: int = 5
    min_holdings_for_batch: int = 10

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        self._validate()

    def _validate(self) -> None:
        """
        Validate configuration values.

        Raises:
            ValueError: If configuration values are invalid

        """
        if self.alpha_vantage_rate_limit < 1:
            raise ValueError(f"alpha_vantage_rate_limit must be >= 1, got {self.alpha_vantage_rate_limit}")

        if self.alpha_vantage_rate_limit > 100:
            logger.warning(f"alpha_vantage_rate_limit is very high ({self.alpha_vantage_rate_limit}). Ensure you have a premium API key to avoid rate limit errors.")

        if self.min_holdings_for_batch < 1:
            raise ValueError(f"min_holdings_for_batch must be >= 1, got {self.min_holdings_for_batch}")

    def log_configuration(self) -> None:
        """Log the current configuration settings."""
        logger.info("=" * 80)
        logger.info("BATCH PREFETCH CONFIGURATION")
        logger.info("=" * 80)
        logger.info(f"  Batch Mode Enabled: {self.enabled}")
        logger.info(f"  Min Holdings for Batch: {self.min_holdings_for_batch}")
        logger.info("")
        logger.info("  Data Sources (Priority Order):")
        logger.info("    1. Yahoo Finance: ALWAYS ENABLED (Primary)")
        logger.info("       - Provides: Company info, fundamentals, price, history")
        logger.info("       - Performance: ~2-5 seconds for 66 tickers")
        logger.info("       - Rate limit: 600 requests/minute")
        logger.info("")

        # Check if Alpha Vantage is enabled via environment
        alpha_vantage_enabled = should_use_alpha_vantage()
        if alpha_vantage_enabled:
            logger.warning("    2. Alpha Vantage: ENABLED (Optional)")
            logger.warning(f"       - Rate limit: {self.alpha_vantage_rate_limit} calls/minute")
            logger.warning("       - Performance: ~13 minutes for 66 tickers")
            logger.warning("       - ⚠️  Adds significant overhead")
            logger.warning("       - ⚠️  Yahoo Finance already provides all essential data")
            logger.warning("       - Recommendation: Disable for optimal performance")
        else:
            logger.info("    2. Alpha Vantage: DISABLED (Recommended)")
            logger.info("       - Yahoo Finance provides all essential data")
            logger.info("       - ✓ Optimal performance configuration")

        logger.info("")
        if not self.enabled:
            logger.warning("  ⚠️  Batch pre-fetch is DISABLED - using sequential mode")
        else:
            logger.info("  ✓ Batch pre-fetch is ENABLED for portfolio analysis")

        logger.info("=" * 80)


def load_batch_prefetch_config() -> BatchPrefetchConfig:
    """
    Load batch prefetch configuration from environment variables.

    Environment Variables:
        BATCH_PREFETCH_ENABLED: Enable/disable batch pre-fetching (default: true)
            Accepted values: true, false, 1, 0, yes, no, on, off

        ALPHA_VANTAGE_RATE_LIMIT: Alpha Vantage API rate limit in calls per minute (default: 5)
            Free tier: 5 calls/minute
            Premium tier: 75 calls/minute

        BATCH_PREFETCH_MIN_HOLDINGS: Minimum holdings to trigger batch mode (default: 10)

    Returns:
        BatchPrefetchConfig: Validated configuration object

    Raises:
        ValueError: If configuration values are invalid

    Requirements: 17.57, 17.58, 17.59, 17.60

    """
    # Load BATCH_PREFETCH_ENABLED (default: true)
    enabled_str = os.getenv("BATCH_PREFETCH_ENABLED", "true").lower().strip()
    enabled = enabled_str in {"true", "1", "yes", "on"}

    # Load ALPHA_VANTAGE_RATE_LIMIT (default: 5)
    rate_limit_str = os.getenv("ALPHA_VANTAGE_RATE_LIMIT", "5").strip()
    try:
        alpha_vantage_rate_limit = int(rate_limit_str)
    except ValueError:
        logger.warning(f"Invalid ALPHA_VANTAGE_RATE_LIMIT value: '{rate_limit_str}'. Using default: 5")
        alpha_vantage_rate_limit = 5

    # Load BATCH_PREFETCH_MIN_HOLDINGS (default: 10)
    min_holdings_str = os.getenv("BATCH_PREFETCH_MIN_HOLDINGS", "10").strip()
    try:
        min_holdings_for_batch = int(min_holdings_str)
    except ValueError:
        logger.warning(f"Invalid BATCH_PREFETCH_MIN_HOLDINGS value: '{min_holdings_str}'. Using default: 10")
        min_holdings_for_batch = 10

    # Create and validate configuration
    config = BatchPrefetchConfig(
        enabled=enabled,
        alpha_vantage_rate_limit=alpha_vantage_rate_limit,
        min_holdings_for_batch=min_holdings_for_batch,
    )

    return config


def should_use_alpha_vantage() -> bool:
    """
    Check if Alpha Vantage should be used.

    Yahoo Finance is ALWAYS used as the primary data source.
    This function only determines if Alpha Vantage should be used
    as an OPTIONAL secondary source.

    Returns:
        False by default (Yahoo Finance only - recommended)
        True only if explicitly enabled via environment variable

    Note:
        Alpha Vantage adds ~13 minutes for 66 tickers with minimal benefit.
        Yahoo Finance provides all essential data.

    """
    enabled_str = os.getenv("ENABLE_ALPHA_VANTAGE", "false").lower().strip()
    return enabled_str in {"true", "1", "yes", "on"}


def get_batch_prefetch_config(log_config: bool = True) -> BatchPrefetchConfig:
    """
    Get batch prefetch configuration with optional logging.

    This is the main entry point for accessing batch prefetch configuration.

    Args:
        log_config: Whether to log the configuration (default: True)

    Returns:
        BatchPrefetchConfig: Validated configuration object

    Requirements: 17.57, 17.58, 17.59, 17.60

    """
    config = load_batch_prefetch_config()

    if log_config:
        config.log_configuration()

    return config


# Singleton instance for caching configuration
_config_instance: BatchPrefetchConfig | None = None


def get_cached_batch_prefetch_config() -> BatchPrefetchConfig:
    """
    Get cached batch prefetch configuration.

    This function caches the configuration to avoid repeated environment
    variable lookups and validation.

    Returns:
        BatchPrefetchConfig: Cached configuration object

    """
    global _config_instance

    if _config_instance is None:
        _config_instance = load_batch_prefetch_config()

    return _config_instance


def reset_config_cache() -> None:
    """
    Reset the cached configuration.

    This is useful for testing or when environment variables change.
    """
    global _config_instance
    _config_instance = None
