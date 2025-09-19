"""
Quantitative analysis configuration system for FinWiz.

This module provides comprehensive configuration classes for quantitative analysis,
backtesting, and screening capabilities with feature flag integration and
environment variable management.
"""

import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, validator

from finwiz.tools.logger import get_logger
from finwiz.utils.feature_flags import get_feature_flags

logger = get_logger(__name__)


class DataProvider(str, Enum):
    """Supported data providers for quantitative analysis."""

    YFINANCE = "yfinance"
    ALPHA_VANTAGE = "alpha_vantage"
    TWELVE_DATA = "twelve_data"
    QUANDL = "quandl"
    IEX_CLOUD = "iex_cloud"


class BacktestFramework(str, Enum):
    """Supported backtesting frameworks."""

    BACKTRADER = "backtrader"
    ZIPLINE = "zipline"
    VECTORBT = "vectorbt"
    CUSTOM = "custom"


class OptimizationMethod(str, Enum):
    """Portfolio optimization methods."""

    MEAN_VARIANCE = "mean_variance"
    BLACK_LITTERMAN = "black_litterman"
    RISK_PARITY = "risk_parity"
    HIERARCHICAL_RISK_PARITY = "hrp"
    CRITICAL_LINE_ALGORITHM = "cla"
    EFFICIENT_FRONTIER = "efficient_frontier"


class TechnicalIndicator(str, Enum):
    """Supported technical indicators."""

    SMA = "sma"
    EMA = "ema"
    RSI = "rsi"
    MACD = "macd"
    BOLLINGER_BANDS = "bollinger_bands"
    STOCHASTIC = "stochastic"
    ATR = "atr"
    ADX = "adx"
    CCI = "cci"
    WILLIAMS_R = "williams_r"
    FIBONACCI = "fibonacci"
    ICHIMOKU = "ichimoku"


class ScreeningCriteria(str, Enum):
    """Stock screening criteria."""

    MARKET_CAP = "market_cap"
    PE_RATIO = "pe_ratio"
    PB_RATIO = "pb_ratio"
    DIVIDEND_YIELD = "dividend_yield"
    ROE = "roe"
    ROA = "roa"
    DEBT_TO_EQUITY = "debt_to_equity"
    REVENUE_GROWTH = "revenue_growth"
    EARNINGS_GROWTH = "earnings_growth"
    PRICE_MOMENTUM = "price_momentum"
    VOLUME = "volume"
    BETA = "beta"


@dataclass
class DataProviderConfig:
    """Configuration for data providers."""

    provider: DataProvider
    api_key: str | None = None
    rate_limit_per_minute: int = 60
    timeout_seconds: int = 30
    retry_attempts: int = 3
    cache_ttl_minutes: int = 60
    base_url: str | None = None
    additional_params: dict[str, Any] = field(default_factory=dict)


@dataclass
class CacheConfig:
    """Configuration for data caching."""

    enabled: bool = True
    cache_dir: Path = Path("cache/quantitative")
    max_cache_size_mb: int = 1000
    default_ttl_minutes: int = 60
    price_data_ttl_minutes: int = 15
    fundamental_data_ttl_hours: int = 24
    news_data_ttl_minutes: int = 30
    cleanup_interval_hours: int = 6


class QuantConfig(BaseModel):
    """
    Main configuration class for quantitative analysis capabilities.

    Provides comprehensive configuration for data providers, caching,
    feature flags, and analysis parameters.
    """

    # Data provider configuration
    primary_data_provider: DataProvider = Field(
        default=DataProvider.YFINANCE, description="Primary data provider for historical data"
    )

    fallback_data_providers: list[DataProvider] = Field(
        default=[DataProvider.ALPHA_VANTAGE, DataProvider.TWELVE_DATA], description="Fallback data providers in order of preference"
    )

    data_provider_configs: dict[DataProvider, DataProviderConfig] = Field(
        default_factory=dict, description="Configuration for each data provider"
    )

    # Cache configuration
    cache_config: CacheConfig = Field(default_factory=CacheConfig, description="Data caching configuration")

    # Analysis parameters
    default_lookback_days: int = Field(
        default=252, ge=30, le=2520, description="Default lookback period in trading days (1 year = 252 days)"
    )

    min_data_points: int = Field(default=50, ge=20, description="Minimum data points required for analysis")

    risk_free_rate: float = Field(default=0.02, ge=0.0, le=0.1, description="Risk-free rate for Sharpe ratio calculations")

    # Technical analysis configuration
    enabled_indicators: list[TechnicalIndicator] = Field(
        default=[
            TechnicalIndicator.SMA,
            TechnicalIndicator.EMA,
            TechnicalIndicator.RSI,
            TechnicalIndicator.MACD,
            TechnicalIndicator.BOLLINGER_BANDS,
        ],
        description="Enabled technical indicators",
    )

    indicator_params: dict[TechnicalIndicator, dict[str, Any]] = Field(
        default_factory=lambda: {
            TechnicalIndicator.SMA: {"periods": [20, 50, 200]},
            TechnicalIndicator.EMA: {"periods": [12, 26, 50]},
            TechnicalIndicator.RSI: {"period": 14, "overbought": 70, "oversold": 30},
            TechnicalIndicator.MACD: {"fast": 12, "slow": 26, "signal": 9},
            TechnicalIndicator.BOLLINGER_BANDS: {"period": 20, "std_dev": 2},
        },
        description="Parameters for technical indicators",
    )

    # Feature flag integration
    feature_flags_enabled: bool = Field(default=True, description="Enable feature flag integration")

    # Validation and error handling
    strict_validation: bool = Field(default=True, description="Enable strict data validation")

    graceful_degradation: bool = Field(default=True, description="Enable graceful degradation on errors")

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
        validate_assignment = True
        extra = "forbid"

    @validator("data_provider_configs", pre=True, always=True)
    def setup_default_provider_configs(cls, v: dict, values: dict) -> dict:
        """Set up default configurations for data providers."""
        if not v:
            v = {}

        # Setup default configurations for common providers
        default_configs = {
            DataProvider.YFINANCE: DataProviderConfig(
                provider=DataProvider.YFINANCE,
                rate_limit_per_minute=2000,  # yfinance is quite permissive
                timeout_seconds=30,
                retry_attempts=3,
                cache_ttl_minutes=15,
            ),
            DataProvider.ALPHA_VANTAGE: DataProviderConfig(
                provider=DataProvider.ALPHA_VANTAGE,
                api_key=os.getenv("ALPHA_VANTAGE_API_KEY"),
                rate_limit_per_minute=5,  # Free tier limit
                timeout_seconds=30,
                retry_attempts=2,
                cache_ttl_minutes=60,
                base_url="https://www.alphavantage.co/query",
            ),
            DataProvider.TWELVE_DATA: DataProviderConfig(
                provider=DataProvider.TWELVE_DATA,
                api_key=os.getenv("TWELVE_DATA_API_KEY"),
                rate_limit_per_minute=8,  # Free tier limit
                timeout_seconds=30,
                retry_attempts=2,
                cache_ttl_minutes=30,
                base_url="https://api.twelvedata.com",
            ),
        }

        # Merge with provided configs
        for provider, config in default_configs.items():
            if provider not in v:
                v[provider] = config

        return v

    @validator("cache_config", pre=True, always=True)
    def setup_cache_directory(cls, v: Any) -> CacheConfig:
        """Ensure cache directory exists."""
        if isinstance(v, dict):
            v = CacheConfig(**v)
        elif v is None:
            v = CacheConfig()

        # Create cache directory if it doesn't exist
        v.cache_dir.mkdir(parents=True, exist_ok=True)

        return v

    def get_data_provider_config(self, provider: DataProvider) -> DataProviderConfig | None:
        """Get configuration for a specific data provider."""
        return self.data_provider_configs.get(provider)

    def is_provider_available(self, provider: DataProvider) -> bool:
        """Check if a data provider is available and configured."""
        config = self.get_data_provider_config(provider)
        if not config:
            return False

        # Check if API key is required and available
        if provider in [DataProvider.ALPHA_VANTAGE, DataProvider.TWELVE_DATA]:
            return config.api_key is not None

        return True

    def get_available_providers(self) -> list[DataProvider]:
        """Get list of available and configured data providers."""
        return [provider for provider in DataProvider if self.is_provider_available(provider)]

    def get_indicator_config(self, indicator: TechnicalIndicator) -> dict[str, Any]:
        """Get configuration for a specific technical indicator."""
        return self.indicator_params.get(indicator, {})


class BacktestConfig(BaseModel):
    """
    Configuration for backtesting engine and strategy execution.

    Provides comprehensive settings for backtesting parameters,
    risk management, and performance analysis.
    """

    # Framework configuration
    framework: BacktestFramework = Field(default=BacktestFramework.BACKTRADER, description="Backtesting framework to use")

    # Capital and position sizing
    initial_capital: float = Field(default=100000.0, gt=0, description="Initial capital for backtesting")

    position_sizing_method: str = Field(
        default="fixed_amount", description="Position sizing method: fixed_amount, percent_of_portfolio, kelly_criterion"
    )

    max_position_size: float = Field(default=0.1, gt=0, le=1.0, description="Maximum position size as fraction of portfolio")

    # Risk management
    stop_loss_pct: float | None = Field(default=0.05, gt=0, le=0.5, description="Stop loss percentage (0.05 = 5%)")

    take_profit_pct: float | None = Field(default=0.15, gt=0, description="Take profit percentage (0.15 = 15%)")

    max_drawdown_limit: float = Field(default=0.2, gt=0, le=1.0, description="Maximum allowed drawdown before stopping strategy")

    # Transaction costs
    commission_pct: float = Field(default=0.001, ge=0, le=0.01, description="Commission as percentage of trade value")

    slippage_pct: float = Field(default=0.0005, ge=0, le=0.01, description="Slippage as percentage of trade value")

    # Execution parameters
    benchmark_symbol: str = Field(default="SPY", description="Benchmark symbol for performance comparison")

    rebalancing_frequency: str = Field(default="monthly", description="Rebalancing frequency: daily, weekly, monthly, quarterly")

    # Analysis parameters
    confidence_level: float = Field(default=0.95, gt=0, lt=1, description="Confidence level for VaR calculations")

    rolling_window_days: int = Field(default=252, gt=0, description="Rolling window for performance metrics")

    risk_free_rate: float = Field(default=0.02, ge=0.0, le=0.1, description="Risk-free rate for Sharpe ratio calculations")

    # Output configuration
    generate_plots: bool = Field(default=True, description="Generate performance plots")

    save_trades: bool = Field(default=True, description="Save individual trade records")

    detailed_analytics: bool = Field(default=True, description="Generate detailed performance analytics")

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
        validate_assignment = True
        extra = "forbid"

    @validator("position_sizing_method")
    def validate_position_sizing_method(cls, v: str) -> str:
        """Validate position sizing method."""
        valid_methods = ["fixed_amount", "percent_of_portfolio", "kelly_criterion", "volatility_adjusted"]
        if v not in valid_methods:
            raise ValueError(f"Position sizing method must be one of: {valid_methods}")
        return v

    @validator("rebalancing_frequency")
    def validate_rebalancing_frequency(cls, v: str) -> str:
        """Validate rebalancing frequency."""
        valid_frequencies = ["daily", "weekly", "monthly", "quarterly", "annually"]
        if v not in valid_frequencies:
            raise ValueError(f"Rebalancing frequency must be one of: {valid_frequencies}")
        return v

    def get_rebalancing_days(self) -> int:
        """Get rebalancing frequency in days."""
        frequency_map = {"daily": 1, "weekly": 7, "monthly": 30, "quarterly": 90, "annually": 365}
        return frequency_map.get(self.rebalancing_frequency, 30)


class ScreenerConfig(BaseModel):
    """
    Configuration for stock screening and fundamental analysis.

    Provides settings for screening criteria, filters, and
    fundamental analysis parameters.
    """

    # Screening universe
    universe: list[str] = Field(
        default=["SP500", "NASDAQ100", "RUSSELL2000"], description="Stock universe for screening (indices or custom lists)"
    )

    custom_symbols: list[str] = Field(default_factory=list, description="Custom list of symbols to screen")

    # Market cap filters
    min_market_cap: float | None = Field(
        default=1e9,  # $1B
        ge=0,
        description="Minimum market cap in USD",
    )

    max_market_cap: float | None = Field(default=None, description="Maximum market cap in USD")

    # Liquidity filters
    min_avg_volume: int = Field(default=1000000, ge=0, description="Minimum average daily volume")

    min_price: float = Field(default=5.0, ge=0, description="Minimum stock price")

    # Fundamental criteria
    screening_criteria: dict[ScreeningCriteria, dict[str, Any]] = Field(
        default_factory=lambda: {
            ScreeningCriteria.PE_RATIO: {"min": 5, "max": 25},
            ScreeningCriteria.PB_RATIO: {"min": 0.5, "max": 3.0},
            ScreeningCriteria.ROE: {"min": 0.15},
            ScreeningCriteria.DEBT_TO_EQUITY: {"max": 0.5},
            ScreeningCriteria.REVENUE_GROWTH: {"min": 0.05},
        },
        description="Screening criteria with min/max values",
    )

    # Technical filters
    technical_filters: dict[str, Any] = Field(
        default_factory=lambda: {
            "rsi_range": {"min": 30, "max": 70},
            "price_above_sma": {"period": 50},
            "volume_spike": {"threshold": 1.5},
        },
        description="Technical analysis filters",
    )

    # Sector and industry filters
    included_sectors: list[str] = Field(default_factory=list, description="Sectors to include (empty = all sectors)")

    excluded_sectors: list[str] = Field(default_factory=list, description="Sectors to exclude")

    included_industries: list[str] = Field(default_factory=list, description="Industries to include (empty = all industries)")

    excluded_industries: list[str] = Field(default_factory=list, description="Industries to exclude")

    # Output configuration
    max_results: int = Field(default=50, gt=0, le=500, description="Maximum number of results to return")

    sort_by: str = Field(default="market_cap", description="Sort results by: market_cap, pe_ratio, roe, revenue_growth, etc.")

    sort_ascending: bool = Field(default=False, description="Sort in ascending order")

    # Analysis depth
    include_fundamental_analysis: bool = Field(default=True, description="Include detailed fundamental analysis")

    include_technical_analysis: bool = Field(default=True, description="Include technical analysis")

    include_peer_comparison: bool = Field(default=True, description="Include peer comparison analysis")

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
        validate_assignment = True
        extra = "forbid"

    def get_criteria_filter(self, criteria: ScreeningCriteria) -> dict[str, Any] | None:
        """Get filter configuration for specific screening criteria."""
        return self.screening_criteria.get(criteria)

    def add_criteria_filter(self, criteria: ScreeningCriteria, min_val: float | None = None, max_val: float | None = None) -> None:
        """Add or update screening criteria filter."""
        filter_config = {}
        if min_val is not None:
            filter_config["min"] = min_val
        if max_val is not None:
            filter_config["max"] = max_val

        if filter_config:
            self.screening_criteria[criteria] = filter_config

    def remove_criteria_filter(self, criteria: ScreeningCriteria) -> None:
        """Remove screening criteria filter."""
        if criteria in self.screening_criteria:
            del self.screening_criteria[criteria]


class QuantitativeConfigManager:
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
        self.config_file = config_file
        self.feature_flags = get_feature_flags()

        # Initialize configurations
        self.quant_config = self._load_quant_config()
        self.backtest_config = self._load_backtest_config()
        self.screener_config = self._load_screener_config()

        logger.info("Quantitative configuration manager initialized")

    def _load_quant_config(self) -> QuantConfig:
        """Load quantitative analysis configuration."""
        config_data = {}

        # Load from environment variables
        if os.getenv("QUANT_PRIMARY_DATA_PROVIDER"):
            config_data["primary_data_provider"] = os.getenv("QUANT_PRIMARY_DATA_PROVIDER")

        if os.getenv("QUANT_LOOKBACK_DAYS"):
            try:
                config_data["default_lookback_days"] = int(os.getenv("QUANT_LOOKBACK_DAYS"))
            except ValueError:
                logger.warning("Invalid QUANT_LOOKBACK_DAYS value, using default")

        if os.getenv("QUANT_RISK_FREE_RATE"):
            try:
                config_data["risk_free_rate"] = float(os.getenv("QUANT_RISK_FREE_RATE"))
            except ValueError:
                logger.warning("Invalid QUANT_RISK_FREE_RATE value, using default")

        # Feature flag integration
        config_data["feature_flags_enabled"] = self.feature_flags.is_enabled("quantitative_analysis")
        config_data["strict_validation"] = self.feature_flags.is_enabled("strict_validation")

        return QuantConfig(**config_data)

    def _load_backtest_config(self) -> BacktestConfig:
        """Load backtesting configuration."""
        config_data = {}

        # Load from environment variables
        if os.getenv("BACKTEST_INITIAL_CAPITAL"):
            try:
                config_data["initial_capital"] = float(os.getenv("BACKTEST_INITIAL_CAPITAL"))
            except ValueError:
                logger.warning("Invalid BACKTEST_INITIAL_CAPITAL value, using default")

        if os.getenv("BACKTEST_COMMISSION_PCT"):
            try:
                config_data["commission_pct"] = float(os.getenv("BACKTEST_COMMISSION_PCT"))
            except ValueError:
                logger.warning("Invalid BACKTEST_COMMISSION_PCT value, using default")

        if os.getenv("BACKTEST_FRAMEWORK"):
            config_data["framework"] = os.getenv("BACKTEST_FRAMEWORK")

        return BacktestConfig(**config_data)

    def _load_screener_config(self) -> ScreenerConfig:
        """Load screener configuration."""
        config_data = {}

        # Load from environment variables
        if os.getenv("SCREENER_MIN_MARKET_CAP"):
            try:
                config_data["min_market_cap"] = float(os.getenv("SCREENER_MIN_MARKET_CAP"))
            except ValueError:
                logger.warning("Invalid SCREENER_MIN_MARKET_CAP value, using default")

        if os.getenv("SCREENER_MAX_RESULTS"):
            try:
                config_data["max_results"] = int(os.getenv("SCREENER_MAX_RESULTS"))
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
                fallback_available = any(
                    self.quant_config.is_provider_available(provider) for provider in self.quant_config.fallback_data_providers
                )
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
