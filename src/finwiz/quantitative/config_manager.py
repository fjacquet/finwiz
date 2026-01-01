"""
Configuration manager for quantitative analysis.

This module provides the QuantitativeConfigManager class for centralized
configuration management with feature flag integration.
"""

import os
from pathlib import Path
from typing import Any

from finwiz.schemas.quantitative.config_models import BacktestConfig, QuantConfig, ScreenerConfig


class QuantitativeConfigManager:  # noqa: PLR0904
    """
    Manager class for quantitative analysis configuration.

    Provides centralized configuration management with feature flag
    integration and environment variable support.
    """

    def __init__(self, config_file: Path | None = None) -> None:
        """
        Initialize configuration manager.

        Args:
            config_file: Optional path to configuration file

        """
        from finwiz.utils.feature_flags import get_feature_flags

        self.config_file = config_file
        self.feature_flags = get_feature_flags()

        # Initialize configurations
        self.quant_config = self._load_quant_config()
        self.backtest_config = self._load_backtest_config()
        self.screener_config = self._load_screener_config()

        from finwiz.tools.logger import get_logger

        logger = get_logger(__name__)
        logger.info("Quantitative configuration manager initialized")

    def _load_quant_config(self) -> QuantConfig:
        """Load quantitative analysis configuration."""
        from finwiz.tools.logger import get_logger

        logger = get_logger(__name__)

        config_data: dict[str, Any] = {}

        # Load from environment variables
        if provider := os.getenv("QUANT_PRIMARY_DATA_PROVIDER"):
            config_data["primary_data_provider"] = provider

        if lookback_str := os.getenv("QUANT_LOOKBACK_DAYS"):
            try:
                config_data["default_lookback_days"] = int(lookback_str)
            except ValueError:
                logger.warning("Invalid QUANT_LOOKBACK_DAYS value, using default")

        if rate_str := os.getenv("QUANT_RISK_FREE_RATE"):
            try:
                config_data["risk_free_rate"] = float(rate_str)
            except ValueError:
                logger.warning("Invalid QUANT_RISK_FREE_RATE value, using default")

        # Feature flag integration
        config_data["feature_flags_enabled"] = self.feature_flags.is_enabled("quantitative_analysis")
        config_data["strict_validation"] = self.feature_flags.is_enabled("strict_validation")

        return QuantConfig(**config_data)

    def _load_backtest_config(self) -> BacktestConfig:
        """Load backtesting configuration."""
        from finwiz.tools.logger import get_logger

        logger = get_logger(__name__)

        config_data: dict[str, Any] = {}

        # Load from environment variables
        if capital_str := os.getenv("BACKTEST_INITIAL_CAPITAL"):
            try:
                config_data["initial_capital"] = float(capital_str)
            except ValueError:
                logger.warning("Invalid BACKTEST_INITIAL_CAPITAL value, using default")

        if commission_str := os.getenv("BACKTEST_COMMISSION_PCT"):
            try:
                config_data["commission_pct"] = float(commission_str)
            except ValueError:
                logger.warning("Invalid BACKTEST_COMMISSION_PCT value, using default")

        if framework := os.getenv("BACKTEST_FRAMEWORK"):
            config_data["framework"] = framework

        return BacktestConfig(**config_data)

    def _load_screener_config(self) -> ScreenerConfig:
        """Load screener configuration."""
        from finwiz.tools.logger import get_logger

        logger = get_logger(__name__)

        config_data: dict[str, Any] = {}

        # Load from environment variables
        if market_cap_str := os.getenv("SCREENER_MIN_MARKET_CAP"):
            try:
                config_data["min_market_cap"] = float(market_cap_str)
            except ValueError:
                logger.warning("Invalid SCREENER_MIN_MARKET_CAP value, using default")

        if max_results_str := os.getenv("SCREENER_MAX_RESULTS"):
            try:
                config_data["max_results"] = int(max_results_str)
            except ValueError:
                logger.warning("Invalid SCREENER_MAX_RESULTS value, using default")

        return ScreenerConfig(**config_data)

    def get_quant_config(self) -> QuantConfig:
        """Get quantitative analysis configuration."""
        return self.quant_config

    def get_backtest_config(self) -> BacktestConfig:
        """Get backtesting configuration."""
        return self.backtest_config

    def get_screener_config(self) -> ScreenerConfig:
        """Get screener configuration."""
        return self.screener_config

    def is_quantitative_analysis_enabled(self) -> bool:
        """Check if quantitative analysis is enabled via feature flags."""
        return self.feature_flags.is_enabled("quantitative_analysis")

    def is_backtesting_enabled(self) -> bool:
        """Check if backtesting is enabled via feature flags."""
        return self.feature_flags.is_enabled("quantitative_backtesting")

    def is_screening_enabled(self) -> bool:
        """Check if screening is enabled via feature flags."""
        return self.feature_flags.is_enabled("stock_screening")

    def validate_configuration(self) -> bool:
        """
        Validate all configurations.

        Returns:
            True if all configurations are valid

        """
        from finwiz.tools.logger import get_logger

        logger = get_logger(__name__)

        try:
            # Validate data provider availability
            available_providers = self.quant_config.get_available_providers()
            if not available_providers:
                logger.error("No data providers are available")
                return False

            # Check if primary provider is available
            if not self.quant_config.is_provider_available(self.quant_config.primary_data_provider):
                logger.warning(f"Primary data provider {self.quant_config.primary_data_provider} is not available")
                # Check if fallback providers are available
                fallback_available = any(self.quant_config.is_provider_available(provider) for provider in self.quant_config.fallback_data_providers)
                if not fallback_available:
                    logger.error("No fallback data providers are available")
                    return False

            # Validate cache directory
            if not self.quant_config.cache_config.cache_dir.exists():
                logger.error(f"Cache directory does not exist: {self.quant_config.cache_config.cache_dir}")
                return False

            logger.info("Quantitative configuration validation passed")
            return True

        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False

    def get_configuration_summary(self) -> dict[str, Any]:
        """Get summary of current configuration."""
        return {
            "quantitative_analysis_enabled": self.is_quantitative_analysis_enabled(),
            "backtesting_enabled": self.is_backtesting_enabled(),
            "screening_enabled": self.is_screening_enabled(),
            "primary_data_provider": self.quant_config.primary_data_provider,
            "available_providers": self.quant_config.get_available_providers(),
            "cache_enabled": self.quant_config.cache_config.enabled,
            "cache_directory": str(self.quant_config.cache_config.cache_dir),
            "initial_capital": self.backtest_config.initial_capital,
            "backtesting_framework": self.backtest_config.framework,
            "screening_universe": self.screener_config.universe,
            "max_screening_results": self.screener_config.max_results,
        }


# Global configuration manager instance
_config_manager: QuantitativeConfigManager | None = None


def get_quantitative_config_manager() -> QuantitativeConfigManager:
    """Get the global quantitative configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = QuantitativeConfigManager()
    return _config_manager


def get_quant_config() -> QuantConfig:
    """Get quantitative analysis configuration."""
    return get_quantitative_config_manager().get_quant_config()


def get_backtest_config() -> BacktestConfig:
    """Get backtesting configuration."""
    return get_quantitative_config_manager().get_backtest_config()


def get_screener_config() -> ScreenerConfig:
    """Get screener configuration."""
    return get_quantitative_config_manager().get_screener_config()
