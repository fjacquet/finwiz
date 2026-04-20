"""
Quantitative analysis configuration system for FinWiz.

This module provides comprehensive configuration classes for quantitative analysis,
backtesting, and screening capabilities with feature flag integration and
environment variable management.

This is the main entry point that re-exports from specialized modules:
- config_defaults: Enums, dataclasses, and default values
- config_validators: Pydantic validators
- config_manager: Configuration classes and manager
"""

# Re-export from specialized modules for backward compatibility
from finwiz.quantitative.config_defaults import (
    BacktestFramework,
    CacheConfig,
    DataProvider,
    DataProviderConfig,
    OptimizationMethod,
    ScreeningCriteria,
    TechnicalIndicator,
    get_default_indicator_params,
    get_default_provider_configs,
    get_default_screening_criteria,
    get_default_technical_filters,
)
from finwiz.quantitative.config_manager import (
    QuantitativeConfigManager,
    get_backtest_config,
    get_quant_config,
    get_quantitative_config_manager,
    get_screener_config,
)
from finwiz.schemas.quantitative.config_models import BacktestConfig, QuantConfig, ScreenerConfig

__all__ = [
    # Enums
    "TechnicalIndicator",
    "DataProvider",
    "BacktestFramework",
    "OptimizationMethod",
    "ScreeningCriteria",
    # Dataclasses
    "DataProviderConfig",
    "CacheConfig",
    # Configuration classes
    "QuantConfig",
    "BacktestConfig",
    "ScreenerConfig",
    "QuantitativeConfigManager",
    # Helper functions
    "get_quantitative_config_manager",
    "get_quant_config",
    "get_backtest_config",
    "get_screener_config",
    "get_default_provider_configs",
    "get_default_indicator_params",
    "get_default_screening_criteria",
    "get_default_technical_filters",
]
