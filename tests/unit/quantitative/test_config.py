"""
Unit tests for quantitative analysis configuration system.

Tests configuration loading, validation, feature flag integration,
and environment variable management for the quantitative analysis framework.
"""

import os
import tempfile
from pathlib import Path

import pytest
from pydantic import ValidationError
from pytest import approx

from finwiz.quantitative.config import (
    BacktestConfig,
    BacktestFramework,
    DataProvider,
    DataProviderConfig,
    QuantConfig,
    QuantitativeConfigManager,
    ScreenerConfig,
    ScreeningCriteria,
    TechnicalIndicator,
    get_backtest_config,
    get_quant_config,
    get_quantitative_config_manager,
    get_screener_config,
)


class TestDataProviderConfig:
    """Test DataProviderConfig functionality."""

    def test_should_create_default_config_when_minimal_params_provided(self):
        """Test creating DataProviderConfig with minimal parameters."""
        # Arrange & Act
        config = DataProviderConfig(provider=DataProvider.YFINANCE)

        # Assert
        assert config.provider == DataProvider.YFINANCE
        assert config.api_key is None
        assert config.rate_limit_per_minute == 60
        assert config.timeout_seconds == 30
        assert config.retry_attempts == 3
        assert config.cache_ttl_minutes == 60
        assert config.base_url is None
        assert config.additional_params == {}

    def test_should_create_config_with_custom_params_when_provided(self):
        """Test creating DataProviderConfig with custom parameters."""
        # Arrange & Act
        config = DataProviderConfig(
            provider=DataProvider.ALPHA_VANTAGE,
            api_key="test_key",
            rate_limit_per_minute=5,
            timeout_seconds=45,
            retry_attempts=2,
            cache_ttl_minutes=120,
            base_url="https://api.example.com",
            additional_params={"format": "json"},
        )

        # Assert
        assert config.provider == DataProvider.ALPHA_VANTAGE
        assert config.api_key == "test_key"
        assert config.rate_limit_per_minute == 5
        assert config.timeout_seconds == 45
        assert config.retry_attempts == 2
        assert config.cache_ttl_minutes == 120
        assert config.base_url == "https://api.example.com"
        assert config.additional_params == {"format": "json"}


class TestQuantConfig:
    """Test QuantConfig functionality."""

    def test_should_create_default_config_when_no_params_provided(self):
        """Test creating QuantConfig with default values."""
        # Arrange & Act
        config = QuantConfig()

        # Assert
        assert config.primary_data_provider == DataProvider.YFINANCE
        assert DataProvider.ALPHA_VANTAGE in config.fallback_data_providers
        assert DataProvider.TWELVE_DATA in config.fallback_data_providers
        assert config.default_lookback_days == 252
        assert config.min_data_points == 50
        assert config.risk_free_rate == approx(0.02)
        assert TechnicalIndicator.SMA in config.enabled_indicators
        assert TechnicalIndicator.RSI in config.enabled_indicators
        assert config.feature_flags_enabled is True
        assert config.strict_validation is True
        assert config.graceful_degradation is True

    def test_should_setup_default_provider_configs_when_none_provided(self):
        """Test automatic setup of default data provider configurations."""
        # Arrange & Act
        config = QuantConfig()

        # Assert
        assert DataProvider.YFINANCE in config.data_provider_configs
        assert DataProvider.ALPHA_VANTAGE in config.data_provider_configs
        assert DataProvider.TWELVE_DATA in config.data_provider_configs

        yfinance_config = config.data_provider_configs[DataProvider.YFINANCE]
        assert yfinance_config.provider == DataProvider.YFINANCE
        assert yfinance_config.rate_limit_per_minute == 2000

        alpha_vantage_config = config.data_provider_configs[DataProvider.ALPHA_VANTAGE]
        assert alpha_vantage_config.provider == DataProvider.ALPHA_VANTAGE
        assert alpha_vantage_config.rate_limit_per_minute == 5

    def test_should_create_cache_directory_when_config_created(self):
        """Test cache directory creation during configuration setup."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir) / "test_cache"

            # Act
            config = QuantConfig(cache_config={"cache_dir": cache_dir})

            # Assert
            assert config.cache_config.cache_dir == cache_dir
            assert cache_dir.exists()

    def test_should_validate_lookback_days_range_when_provided(self):
        """Test validation of lookback days parameter."""
        # Test valid range
        config = QuantConfig(default_lookback_days=100)
        assert config.default_lookback_days == 100

        # Test minimum boundary
        config = QuantConfig(default_lookback_days=30)
        assert config.default_lookback_days == 30

        # Test maximum boundary
        config = QuantConfig(default_lookback_days=2520)
        assert config.default_lookback_days == 2520

        # Test invalid values
        with pytest.raises(ValidationError):
            QuantConfig(default_lookback_days=10)  # Too low

        with pytest.raises(ValidationError):
            QuantConfig(default_lookback_days=3000)  # Too high

    def test_should_validate_risk_free_rate_range_when_provided(self):
        """Test validation of risk-free rate parameter."""
        # Test valid range
        config = QuantConfig(risk_free_rate=0.05)
        assert config.risk_free_rate == approx(0.05)

        # Test boundary values
        config = QuantConfig(risk_free_rate=0.0)
        assert config.risk_free_rate == approx(0.0)

        config = QuantConfig(risk_free_rate=0.1)
        assert config.risk_free_rate == approx(0.1)

        # Test invalid values
        with pytest.raises(ValidationError):
            QuantConfig(risk_free_rate=-0.01)  # Negative

        with pytest.raises(ValidationError):
            QuantConfig(risk_free_rate=0.15)  # Too high

    def test_should_reject_extra_fields_when_strict_validation_enabled(self):
        """Test that extra fields are rejected in strict mode."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            QuantConfig(invalid_field="should_fail")

        assert "Extra inputs are not permitted" in str(exc_info.value)

    def test_should_load_api_keys_from_environment_when_available(self, mocker):
        """Test loading API keys from environment variables."""
        # Arrange
        mocker.patch.dict("os.environ", {"ALPHA_VANTAGE_API_KEY": "test_alpha_key"})

        # Act
        config = QuantConfig()

        # Assert
        alpha_vantage_config = config.data_provider_configs[DataProvider.ALPHA_VANTAGE]
        assert alpha_vantage_config.api_key == "test_alpha_key"

    def test_should_return_provider_config_when_requested(self):
        """Test getting specific data provider configuration."""
        # Arrange
        config = QuantConfig()

        # Act
        yfinance_config = config.get_data_provider_config(DataProvider.YFINANCE)
        nonexistent_config = config.get_data_provider_config(DataProvider.QUANDL)

        # Assert
        assert yfinance_config is not None
        assert yfinance_config.provider == DataProvider.YFINANCE
        assert nonexistent_config is None

    def test_should_identify_available_providers_when_api_keys_present(self, mocker):
        """Test identification of available data providers."""
        # Arrange
        mocker.patch.dict("os.environ", {"ALPHA_VANTAGE_API_KEY": "test_key"})
        config = QuantConfig()

        # Act
        available_providers = config.get_available_providers()

        # Assert
        assert DataProvider.YFINANCE in available_providers  # No API key required
        assert DataProvider.ALPHA_VANTAGE in available_providers  # API key provided

    def test_should_identify_unavailable_providers_when_api_keys_missing(self, mocker):
        """Test identification of unavailable providers when API keys are missing."""
        # Arrange
        mocker.patch.dict("os.environ", {}, clear=True)
        config = QuantConfig()

        # Act
        is_alpha_vantage_available = config.is_provider_available(DataProvider.ALPHA_VANTAGE)
        is_twelve_data_available = config.is_provider_available(DataProvider.TWELVE_DATA)
        is_yfinance_available = config.is_provider_available(DataProvider.YFINANCE)

        # Assert
        assert not is_alpha_vantage_available  # Requires API key
        assert not is_twelve_data_available  # Requires API key
        assert is_yfinance_available  # No API key required

    def test_should_return_indicator_config_when_requested(self):
        """Test getting configuration for specific technical indicators."""
        # Arrange
        config = QuantConfig()

        # Act
        rsi_config = config.get_indicator_config(TechnicalIndicator.RSI)
        macd_config = config.get_indicator_config(TechnicalIndicator.MACD)
        nonexistent_config = config.get_indicator_config(TechnicalIndicator.ICHIMOKU)

        # Assert
        assert rsi_config == {"period": 14, "overbought": 70, "oversold": 30}
        assert macd_config == {"fast": 12, "slow": 26, "signal": 9}
        assert nonexistent_config == {}


class TestBacktestConfig:
    """Test BacktestConfig functionality."""

    def test_should_create_default_config_when_no_params_provided(self):
        """Test creating BacktestConfig with default values."""
        # Arrange & Act
        config = BacktestConfig()

        # Assert
        assert config.framework == BacktestFramework.BACKTRADER
        assert config.initial_capital == approx(100000.0)
        assert config.position_sizing_method == "fixed_amount"
        assert config.max_position_size == approx(0.1)
        assert config.stop_loss_pct == approx(0.05)
        assert config.take_profit_pct == approx(0.15)
        assert config.max_drawdown_limit == approx(0.2)
        assert config.commission_pct == approx(0.001)
        assert config.slippage_pct == approx(0.0005)
        assert config.benchmark_symbol == "SPY"
        assert config.rebalancing_frequency == "monthly"
        assert config.confidence_level == approx(0.95)
        assert config.rolling_window_days == 252
        assert config.generate_plots is True
        assert config.save_trades is True
        assert config.detailed_analytics is True

    def test_should_validate_initial_capital_positive_when_provided(self):
        """Test validation of initial capital parameter."""
        # Test valid value
        config = BacktestConfig(initial_capital=50000.0)
        assert config.initial_capital == approx(50000.0)

        # Test invalid values
        with pytest.raises(ValidationError):
            BacktestConfig(initial_capital=0.0)  # Zero

        with pytest.raises(ValidationError):
            BacktestConfig(initial_capital=-1000.0)  # Negative

    def test_should_validate_position_sizing_method_when_provided(self):
        """Test validation of position sizing method."""
        # Test valid methods
        valid_methods = ["fixed_amount", "percent_of_portfolio", "kelly_criterion", "volatility_adjusted"]
        for method in valid_methods:
            config = BacktestConfig(position_sizing_method=method)
            assert config.position_sizing_method == method

        # Test invalid method
        with pytest.raises(ValidationError):
            BacktestConfig(position_sizing_method="invalid_method")

    def test_should_validate_max_position_size_range_when_provided(self):
        """Test validation of maximum position size parameter."""
        # Test valid range
        config = BacktestConfig(max_position_size=0.05)
        assert config.max_position_size == approx(0.05)

        # Test boundary values
        config = BacktestConfig(max_position_size=1.0)
        assert config.max_position_size == approx(1.0)

        # Test invalid values
        with pytest.raises(ValidationError):
            BacktestConfig(max_position_size=0.0)  # Zero

        with pytest.raises(ValidationError):
            BacktestConfig(max_position_size=1.5)  # Greater than 100%

    def test_should_validate_rebalancing_frequency_when_provided(self):
        """Test validation of rebalancing frequency."""
        # Test valid frequencies
        valid_frequencies = ["daily", "weekly", "monthly", "quarterly", "annually"]
        for frequency in valid_frequencies:
            config = BacktestConfig(rebalancing_frequency=frequency)
            assert config.rebalancing_frequency == frequency

        # Test invalid frequency
        with pytest.raises(ValidationError):
            BacktestConfig(rebalancing_frequency="invalid_frequency")

    def test_should_return_rebalancing_days_when_requested(self):
        """Test conversion of rebalancing frequency to days."""
        # Arrange & Act & Assert
        config = BacktestConfig(rebalancing_frequency="daily")
        assert config.get_rebalancing_days() == 1

        config = BacktestConfig(rebalancing_frequency="weekly")
        assert config.get_rebalancing_days() == 7

        config = BacktestConfig(rebalancing_frequency="monthly")
        assert config.get_rebalancing_days() == 30

        config = BacktestConfig(rebalancing_frequency="quarterly")
        assert config.get_rebalancing_days() == 90

        config = BacktestConfig(rebalancing_frequency="annually")
        assert config.get_rebalancing_days() == 365

    def test_should_validate_confidence_level_range_when_provided(self):
        """Test validation of confidence level parameter."""
        # Test valid range
        config = BacktestConfig(confidence_level=0.99)
        assert config.confidence_level == approx(0.99)

        # Test invalid values
        with pytest.raises(ValidationError):
            BacktestConfig(confidence_level=0.0)  # Zero

        with pytest.raises(ValidationError):
            BacktestConfig(confidence_level=1.0)  # Equal to 1

        with pytest.raises(ValidationError):
            BacktestConfig(confidence_level=1.5)  # Greater than 1


class TestScreenerConfig:
    """Test ScreenerConfig functionality."""

    def test_should_create_default_config_when_no_params_provided(self):
        """Test creating ScreenerConfig with default values."""
        # Arrange & Act
        config = ScreenerConfig()

        # Assert
        assert config.universe == ["SP500", "NASDAQ100", "RUSSELL2000"]
        assert config.custom_symbols == []
        assert config.min_market_cap == 1e9
        assert config.max_market_cap is None
        assert config.min_avg_volume == 1000000
        assert config.min_price == approx(5.0)
        assert ScreeningCriteria.PE_RATIO in config.screening_criteria
        assert ScreeningCriteria.ROE in config.screening_criteria
        assert config.max_results == 50
        assert config.sort_by == "market_cap"
        assert config.sort_ascending is False
        assert config.include_fundamental_analysis is True
        assert config.include_technical_analysis is True
        assert config.include_peer_comparison is True

    def test_should_validate_min_market_cap_non_negative_when_provided(self):
        """Test validation of minimum market cap parameter."""
        # Test valid value
        config = ScreenerConfig(min_market_cap=5e8)
        assert config.min_market_cap == 5e8

        # Test zero value
        config = ScreenerConfig(min_market_cap=0)
        assert config.min_market_cap == 0

        # Test invalid value
        with pytest.raises(ValidationError):
            ScreenerConfig(min_market_cap=-1000)  # Negative

    def test_should_validate_max_results_range_when_provided(self):
        """Test validation of maximum results parameter."""
        # Test valid range
        config = ScreenerConfig(max_results=25)
        assert config.max_results == 25

        # Test boundary values
        config = ScreenerConfig(max_results=1)
        assert config.max_results == 1

        config = ScreenerConfig(max_results=500)
        assert config.max_results == 500

        # Test invalid values
        with pytest.raises(ValidationError):
            ScreenerConfig(max_results=0)  # Zero

        with pytest.raises(ValidationError):
            ScreenerConfig(max_results=1000)  # Too high

    def test_should_return_criteria_filter_when_requested(self):
        """Test getting filter configuration for specific screening criteria."""
        # Arrange
        config = ScreenerConfig()

        # Act
        pe_filter = config.get_criteria_filter(ScreeningCriteria.PE_RATIO)
        roe_filter = config.get_criteria_filter(ScreeningCriteria.ROE)
        nonexistent_filter = config.get_criteria_filter(ScreeningCriteria.BETA)

        # Assert
        assert pe_filter == {"min": 5, "max": 25}
        assert roe_filter == {"min": 0.15}
        assert nonexistent_filter is None

    def test_should_add_criteria_filter_when_requested(self):
        """Test adding new screening criteria filter."""
        # Arrange
        config = ScreenerConfig()

        # Act
        config.add_criteria_filter(ScreeningCriteria.BETA, min_val=0.5, max_val=1.5)

        # Assert
        beta_filter = config.get_criteria_filter(ScreeningCriteria.BETA)
        assert beta_filter == {"min": 0.5, "max": 1.5}

    def test_should_remove_criteria_filter_when_requested(self):
        """Test removing existing screening criteria filter."""
        # Arrange
        config = ScreenerConfig()
        assert config.get_criteria_filter(ScreeningCriteria.PE_RATIO) is not None

        # Act
        config.remove_criteria_filter(ScreeningCriteria.PE_RATIO)

        # Assert
        assert config.get_criteria_filter(ScreeningCriteria.PE_RATIO) is None

    def test_should_handle_partial_criteria_filter_when_added(self):
        """Test adding criteria filter with only min or max value."""
        # Arrange
        config = ScreenerConfig()

        # Act - Add filter with only min value
        config.add_criteria_filter(ScreeningCriteria.VOLUME, min_val=1000000)

        # Assert
        volume_filter = config.get_criteria_filter(ScreeningCriteria.VOLUME)
        assert volume_filter == {"min": 1000000}

        # Act - Add filter with only max value
        config.add_criteria_filter(ScreeningCriteria.DIVIDEND_YIELD, max_val=0.08)

        # Assert
        dividend_filter = config.get_criteria_filter(ScreeningCriteria.DIVIDEND_YIELD)
        assert dividend_filter == {"max": 0.08}


class TestQuantitativeConfigManager:
    """Test QuantitativeConfigManager functionality."""

    def test_should_initialize_manager_when_created(self, mocker):
        """Test initialization of QuantitativeConfigManager."""
        # Arrange
        mock_get_feature_flags = mocker.patch("finwiz.utils.feature_flags.get_feature_flags")
        mock_feature_flags = mock_get_feature_flags.return_value
        mock_feature_flags.is_enabled.return_value = True

        # Act
        manager = QuantitativeConfigManager()

        # Assert
        assert manager.quant_config is not None
        assert manager.backtest_config is not None
        assert manager.screener_config is not None
        assert manager.feature_flags is not None

    def test_should_load_config_from_environment_when_available(self, mocker):
        """Test loading configuration from environment variables."""
        # Arrange
        mock_get_feature_flags = mocker.patch("finwiz.utils.feature_flags.get_feature_flags")
        mock_feature_flags = mock_get_feature_flags.return_value
        mock_feature_flags.is_enabled.return_value = True
        mocker.patch.dict(
            os.environ,
            {
                "QUANT_PRIMARY_DATA_PROVIDER": "alpha_vantage",
                "QUANT_LOOKBACK_DAYS": "500",
                "QUANT_RISK_FREE_RATE": "0.03",
            },
        )

        # Act
        manager = QuantitativeConfigManager()

        # Assert
        assert manager.quant_config.primary_data_provider == DataProvider.ALPHA_VANTAGE
        assert manager.quant_config.default_lookback_days == 500
        assert manager.quant_config.risk_free_rate == approx(0.03)

    def test_should_load_backtest_config_from_environment_when_available(self, mocker):
        """Test loading backtesting configuration from environment variables."""
        # Arrange
        mock_get_feature_flags = mocker.patch("finwiz.utils.feature_flags.get_feature_flags")
        mock_feature_flags = mock_get_feature_flags.return_value
        mock_feature_flags.is_enabled.return_value = True

        mocker.patch.dict("os.environ", {"BACKTEST_INITIAL_CAPITAL": "250000", "BACKTEST_COMMISSION_PCT": "0.002", "BACKTEST_FRAMEWORK": "zipline"})

        # Act
        manager = QuantitativeConfigManager()

        # Assert
        assert manager.backtest_config.initial_capital == approx(250000.0)
        assert manager.backtest_config.commission_pct == approx(0.002)
        assert manager.backtest_config.framework == BacktestFramework.ZIPLINE

    def test_should_load_screener_config_from_environment_when_available(self, mocker):
        """Test loading screener configuration from environment variables."""
        # Arrange
        mock_get_feature_flags = mocker.patch("finwiz.utils.feature_flags.get_feature_flags")
        mock_feature_flags = mock_get_feature_flags.return_value
        mock_feature_flags.is_enabled.return_value = True

        mocker.patch.dict("os.environ", {"SCREENER_MIN_MARKET_CAP": "5000000000", "SCREENER_MAX_RESULTS": "25"})

        # Act
        manager = QuantitativeConfigManager()

        # Assert
        assert manager.screener_config.min_market_cap == 5e9
        assert manager.screener_config.max_results == 25

    def test_should_return_feature_flag_status_when_requested(self, mocker):
        """Test checking feature flag status."""
        # Arrange
        mock_get_feature_flags = mocker.patch("finwiz.utils.feature_flags.get_feature_flags")
        mock_feature_flags = mock_get_feature_flags.return_value
        mock_feature_flags.is_enabled.side_effect = lambda flag: {
            "quantitative_analysis": True,
            "quantitative_backtesting": False,
            "stock_screening": True,
        }.get(flag, False)

        manager = QuantitativeConfigManager()

        # Act & Assert
        assert manager.is_quantitative_analysis_enabled() is True
        assert manager.is_backtesting_enabled() is False
        assert manager.is_screening_enabled() is True

    def test_should_validate_configuration_successfully_when_providers_available(self, mocker):
        """Test successful configuration validation."""
        # Arrange
        mock_get_feature_flags = mocker.patch("finwiz.utils.feature_flags.get_feature_flags")
        mock_feature_flags = mock_get_feature_flags.return_value
        mock_feature_flags.is_enabled.return_value = True

        mocker.patch.dict("os.environ", {"ALPHA_VANTAGE_API_KEY": "test_key"})

        manager = QuantitativeConfigManager()

        # Act
        is_valid = manager.validate_configuration()

        # Assert
        assert is_valid is True

    def test_should_fail_validation_when_no_providers_available(self, mocker):
        """Test configuration validation failure when no providers are available."""
        # Arrange
        mock_get_feature_flags = mocker.patch("finwiz.utils.feature_flags.get_feature_flags")
        mock_feature_flags = mock_get_feature_flags.return_value
        mock_feature_flags.is_enabled.return_value = True

        mocker.patch.dict("os.environ", {}, clear=True)
        # Create config with no available providers
        mocker.patch.object(QuantConfig, "get_available_providers", return_value=[])
        manager = QuantitativeConfigManager()

        # Act
        is_valid = manager.validate_configuration()

        # Assert
        assert is_valid is False

    def test_should_return_configuration_summary_when_requested(self, mocker):
        """Test getting configuration summary."""
        # Arrange
        mock_get_feature_flags = mocker.patch("finwiz.utils.feature_flags.get_feature_flags")
        mock_feature_flags = mock_get_feature_flags.return_value
        mock_feature_flags.is_enabled.side_effect = lambda flag: {
            "quantitative_analysis": True,
            "quantitative_backtesting": True,
            "stock_screening": False,
        }.get(flag, False)
        mock_feature_flags.list_all_flags.return_value = {"test": "flags"}

        manager = QuantitativeConfigManager()

        # Act
        summary = manager.get_configuration_summary()

        # Assert
        assert "quantitative_analysis_enabled" in summary
        assert "backtesting_enabled" in summary
        assert "screening_enabled" in summary
        assert "primary_data_provider" in summary
        assert "available_providers" in summary
        assert "cache_enabled" in summary
        assert "initial_capital" in summary
        assert summary["quantitative_analysis_enabled"] is True
        assert summary["backtesting_enabled"] is True
        assert summary["screening_enabled"] is False


class TestGlobalConfigurationFunctions:
    """Test global configuration management functions."""

    def test_should_return_singleton_manager_when_requested(self, mocker):
        """Test that global configuration manager returns singleton instance."""
        # Arrange
        mock_get_feature_flags = mocker.patch("finwiz.utils.feature_flags.get_feature_flags")
        mock_feature_flags = mock_get_feature_flags.return_value
        mock_feature_flags.is_enabled.return_value = True

        # Act
        manager1 = get_quantitative_config_manager()
        manager2 = get_quantitative_config_manager()

        # Assert
        assert manager1 is manager2  # Same instance

    def test_should_return_quant_config_when_requested(self, mocker):
        """Test convenience function for getting quantitative config."""
        # Arrange
        mock_get_feature_flags = mocker.patch("finwiz.utils.feature_flags.get_feature_flags")
        mock_feature_flags = mock_get_feature_flags.return_value
        mock_feature_flags.is_enabled.return_value = True

        # Act
        config = get_quant_config()

        # Assert
        assert isinstance(config, QuantConfig)
        assert config.primary_data_provider == DataProvider.YFINANCE

    def test_should_return_backtest_config_when_requested(self, mocker):
        """Test convenience function for getting backtest config."""
        # Arrange
        mock_get_feature_flags = mocker.patch("finwiz.utils.feature_flags.get_feature_flags")
        mock_feature_flags = mock_get_feature_flags.return_value
        mock_feature_flags.is_enabled.return_value = True

        # Act
        config = get_backtest_config()

        # Assert
        assert isinstance(config, BacktestConfig)
        assert config.framework == BacktestFramework.BACKTRADER

    def test_should_return_screener_config_when_requested(self, mocker):
        """Test convenience function for getting screener config."""
        # Arrange
        mock_get_feature_flags = mocker.patch("finwiz.utils.feature_flags.get_feature_flags")
        mock_feature_flags = mock_get_feature_flags.return_value
        mock_feature_flags.is_enabled.return_value = True

        # Act
        config = get_screener_config()

        # Assert
        assert isinstance(config, ScreenerConfig)
        assert config.universe == ["SP500", "NASDAQ100", "RUSSELL2000"]


class TestEnvironmentVariableHandling:
    """Test environment variable handling and error cases."""

    def test_should_use_default_when_invalid_environment_value_provided(self, mocker):
        """Test handling of invalid environment variable values."""
        # Arrange
        mock_get_feature_flags = mocker.patch("finwiz.utils.feature_flags.get_feature_flags")
        mock_feature_flags = mock_get_feature_flags.return_value
        mock_feature_flags.is_enabled.return_value = True

        mocker.patch.dict("os.environ", {"QUANT_LOOKBACK_DAYS": "invalid_number"})

        # Act
        manager = QuantitativeConfigManager()

        # Assert
        # Should use default value when environment variable is invalid
        assert manager.quant_config.default_lookback_days == 252  # Default value

    def test_should_use_default_when_invalid_backtest_environment_value_provided(self, mocker):
        """Test handling of invalid backtesting environment variable values."""
        # Arrange
        mock_get_feature_flags = mocker.patch("finwiz.utils.feature_flags.get_feature_flags")
        mock_feature_flags = mock_get_feature_flags.return_value
        mock_feature_flags.is_enabled.return_value = True

        mocker.patch.dict("os.environ", {"BACKTEST_INITIAL_CAPITAL": "not_a_number"})

        # Act
        manager = QuantitativeConfigManager()

        # Assert
        # Should use default value when environment variable is invalid
        assert manager.backtest_config.initial_capital == approx(100000.0)  # Default value

    def test_should_use_default_when_invalid_screener_environment_value_provided(self, mocker):
        """Test handling of invalid screener environment variable values."""
        # Arrange
        mock_get_feature_flags = mocker.patch("finwiz.utils.feature_flags.get_feature_flags")
        mock_feature_flags = mock_get_feature_flags.return_value
        mock_feature_flags.is_enabled.return_value = True

        mocker.patch.dict("os.environ", {"SCREENER_MAX_RESULTS": "not_an_integer"})

        # Act
        manager = QuantitativeConfigManager()

        # Assert
        # Should use default value when environment variable is invalid
        assert manager.screener_config.max_results == 50  # Default value
