"""
Pydantic configuration models for quantitative analysis.

This module provides the three main configuration classes:
- QuantConfig: Main quantitative analysis configuration
- BacktestConfig: Backtesting configuration
- ScreenerConfig: Stock screening configuration
"""

from typing import Any

from pydantic import BaseModel, Field

from finwiz.quantitative.config_defaults import (
    BacktestFramework,
    DataProvider,
    ScreeningCriteria,
    TechnicalIndicator,
    get_default_indicator_params,
    get_default_screening_criteria,
    get_default_technical_filters,
)


class QuantConfig(BaseModel):
    """
    Main configuration class for quantitative analysis capabilities.

    Provides comprehensive configuration for data providers, caching,
    feature flags, and analysis parameters.
    """

    # Data provider configuration
    primary_data_provider: DataProvider = Field(default=DataProvider.YFINANCE, description="Primary data provider for historical data")

    fallback_data_providers: list[DataProvider] = Field(
        default=[DataProvider.ALPHA_VANTAGE, DataProvider.TWELVE_DATA], description="Fallback data providers in order of preference"
    )

    data_provider_configs: dict[DataProvider, Any] = Field(default_factory=dict, description="Configuration for each data provider")

    # Cache configuration
    cache_config: Any = Field(default_factory=lambda: None, description="Data caching configuration")

    # Analysis parameters
    default_lookback_days: int = Field(default=252, ge=30, le=2520, description="Default lookback period in trading days (1 year = 252 days)")

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
        default_factory=get_default_indicator_params,
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

    # Validators imported at module level to avoid Pydantic field detection
    from finwiz.quantitative.config_validators import ConfigValidators as _ConfigValidators

    _setup_default_provider_configs = _ConfigValidators.setup_default_provider_configs
    _setup_cache_directory = _ConfigValidators.setup_cache_directory

    def get_data_provider_config(self, provider: DataProvider) -> Any | None:
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

    position_sizing_method: str = Field(default="fixed_amount", description="Position sizing method: fixed_amount, percent_of_portfolio, kelly_criterion")

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

    # Validators imported at module level to avoid Pydantic field detection
    from finwiz.quantitative.config_validators import ConfigValidators as _ConfigValidators

    _validate_position_sizing_method = _ConfigValidators.validate_position_sizing_method
    _validate_rebalancing_frequency = _ConfigValidators.validate_rebalancing_frequency

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
    universe: list[str] = Field(default=["SP500", "NASDAQ100", "RUSSELL2000"], description="Stock universe for screening (indices or custom lists)")

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
        default_factory=get_default_screening_criteria,
        description="Screening criteria with min/max values",
    )

    # Technical filters
    technical_filters: dict[str, Any] = Field(
        default_factory=get_default_technical_filters,
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
