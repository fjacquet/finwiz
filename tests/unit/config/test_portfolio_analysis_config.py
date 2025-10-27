"""Unit tests for PortfolioAnalysisConfig."""

import pytest
from pydantic import ValidationError

from finwiz.config.portfolio_analysis_config import PortfolioAnalysisConfig


class TestPortfolioAnalysisConfig:
    """Test suite for PortfolioAnalysisConfig."""

    def test_should_create_config_with_defaults(self):
        """Test creating config with default values."""
        # Act
        config = PortfolioAnalysisConfig()

        # Assert
        assert config.deep_analysis_enabled is True  # Changed from False to True (new default)
        assert config.enable_alternatives is True
        assert config.cache_enabled is True
        assert config.cache_ttl_hours == 24
        assert config.max_alternatives == 5
        assert config.deep_analysis_batch_size == 10

    def test_should_create_config_with_custom_values(self):
        """Test creating config with custom values."""
        # Act
        config = PortfolioAnalysisConfig(
            deep_analysis_enabled=True,
            enable_alternatives=False,
            cache_enabled=False,
            cache_ttl_hours=48,
            max_alternatives=3,
            deep_analysis_batch_size=20,
        )

        # Assert
        assert config.deep_analysis_enabled is True
        assert config.enable_alternatives is False
        assert config.cache_enabled is False
        assert config.cache_ttl_hours == 48
        assert config.max_alternatives == 3
        assert config.deep_analysis_batch_size == 20

    def test_should_validate_boolean_string_values_for_deep_analysis(self):
        """Test boolean string validation for deep_analysis_enabled."""
        # Test truthy values
        for value in ["1", "true", "True", "TRUE", "yes", "YES", "on", "ON"]:
            config = PortfolioAnalysisConfig(deep_analysis_enabled=value)
            assert config.deep_analysis_enabled is True, f"Failed for value: {value}"

        # Test falsy values
        for value in ["0", "false", "False", "FALSE", "no", "NO", "off", "OFF"]:
            config = PortfolioAnalysisConfig(deep_analysis_enabled=value)
            assert config.deep_analysis_enabled is False, f"Failed for value: {value}"

    def test_should_validate_boolean_string_values_for_alternatives(self):
        """Test boolean string validation for enable_alternatives."""
        # Test truthy values
        for value in ["1", "true", "yes", "on"]:
            config = PortfolioAnalysisConfig(enable_alternatives=value)
            assert config.enable_alternatives is True

        # Test falsy values
        for value in ["0", "false", "no", "off"]:
            config = PortfolioAnalysisConfig(enable_alternatives=value)
            assert config.enable_alternatives is False

    def test_should_validate_boolean_string_values_for_cache(self):
        """Test boolean string validation for cache_enabled."""
        # Test truthy values
        config = PortfolioAnalysisConfig(cache_enabled="true")
        assert config.cache_enabled is True

        # Test falsy values
        config = PortfolioAnalysisConfig(cache_enabled="false")
        assert config.cache_enabled is False

    def test_should_handle_whitespace_in_boolean_strings(self):
        """Test that whitespace is stripped from boolean strings."""
        # Act
        config = PortfolioAnalysisConfig(deep_analysis_enabled="  true  ", enable_alternatives="  yes  ", cache_enabled="  1  ")

        # Assert
        assert config.deep_analysis_enabled is True
        assert config.enable_alternatives is True
        assert config.cache_enabled is True

    def test_should_reject_invalid_cache_ttl_hours(self):
        """Test validation of cache_ttl_hours range."""
        # Test below minimum
        with pytest.raises(ValidationError) as exc_info:
            PortfolioAnalysisConfig(cache_ttl_hours=0)
        assert "greater than or equal to 1" in str(exc_info.value)

        # Test above maximum
        with pytest.raises(ValidationError) as exc_info:
            PortfolioAnalysisConfig(cache_ttl_hours=169)
        assert "less than or equal to 168" in str(exc_info.value)

    def test_should_accept_valid_cache_ttl_hours(self):
        """Test valid cache_ttl_hours values."""
        # Test minimum
        config = PortfolioAnalysisConfig(cache_ttl_hours=1)
        assert config.cache_ttl_hours == 1

        # Test maximum
        config = PortfolioAnalysisConfig(cache_ttl_hours=168)
        assert config.cache_ttl_hours == 168

        # Test middle value
        config = PortfolioAnalysisConfig(cache_ttl_hours=72)
        assert config.cache_ttl_hours == 72

    def test_should_reject_invalid_max_alternatives(self):
        """Test validation of max_alternatives range."""
        # Test below minimum
        with pytest.raises(ValidationError) as exc_info:
            PortfolioAnalysisConfig(max_alternatives=0)
        assert "greater than or equal to 1" in str(exc_info.value)

        # Test above maximum
        with pytest.raises(ValidationError) as exc_info:
            PortfolioAnalysisConfig(max_alternatives=11)
        assert "less than or equal to 10" in str(exc_info.value)

    def test_should_accept_valid_max_alternatives(self):
        """Test valid max_alternatives values."""
        # Test minimum
        config = PortfolioAnalysisConfig(max_alternatives=1)
        assert config.max_alternatives == 1

        # Test maximum
        config = PortfolioAnalysisConfig(max_alternatives=10)
        assert config.max_alternatives == 10

    def test_should_reject_invalid_batch_size(self):
        """Test validation of deep_analysis_batch_size range."""
        # Test below minimum
        with pytest.raises(ValidationError) as exc_info:
            PortfolioAnalysisConfig(deep_analysis_batch_size=0)
        assert "greater than or equal to 1" in str(exc_info.value)

        # Test above maximum
        with pytest.raises(ValidationError) as exc_info:
            PortfolioAnalysisConfig(deep_analysis_batch_size=51)
        assert "less than or equal to 50" in str(exc_info.value)

    def test_should_accept_valid_batch_size(self):
        """Test valid deep_analysis_batch_size values."""
        # Test minimum
        config = PortfolioAnalysisConfig(deep_analysis_batch_size=1)
        assert config.deep_analysis_batch_size == 1

        # Test maximum
        config = PortfolioAnalysisConfig(deep_analysis_batch_size=50)
        assert config.deep_analysis_batch_size == 50

    def test_should_load_from_env_with_all_variables_set(self, mocker):
        """Test loading configuration from environment variables."""
        # Arrange
        mocker.patch.dict(
            "os.environ",
            {
                "DEEP_PORTFOLIO_ANALYSIS": "true",
                "PORTFOLIO_ENABLE_ALTERNATIVES": "false",
                "PORTFOLIO_CACHE_ENABLED": "yes",
                "PORTFOLIO_CACHE_TTL_HOURS": "48",
                "PORTFOLIO_MAX_ALTERNATIVES": "7",
                "PORTFOLIO_DEEP_ANALYSIS_BATCH_SIZE": "15",
            },
        )

        # Act
        config = PortfolioAnalysisConfig.from_env()

        # Assert
        assert config.deep_analysis_enabled is True
        assert config.enable_alternatives is False
        assert config.cache_enabled is True
        assert config.cache_ttl_hours == 48
        assert config.max_alternatives == 7
        assert config.deep_analysis_batch_size == 15

    def test_should_use_defaults_when_env_variables_not_set(self, mocker):
        """Test that defaults are used when environment variables are not set."""
        # Arrange
        mocker.patch.dict("os.environ", {}, clear=True)

        # Act
        config = PortfolioAnalysisConfig.from_env()

        # Assert
        assert config.deep_analysis_enabled is True  # Changed from False to True (new default)
        assert config.enable_alternatives is True
        assert config.cache_enabled is True
        assert config.cache_ttl_hours == 24
        assert config.max_alternatives == 5
        assert config.deep_analysis_batch_size == 10

    def test_should_handle_partial_env_variables(self, mocker):
        """Test loading with only some environment variables set."""
        # Arrange
        mocker.patch.dict("os.environ", {"DEEP_PORTFOLIO_ANALYSIS": "1", "PORTFOLIO_CACHE_TTL_HOURS": "72"}, clear=True)

        # Act
        config = PortfolioAnalysisConfig.from_env()

        # Assert
        assert config.deep_analysis_enabled is True
        assert config.enable_alternatives is True  # default
        assert config.cache_enabled is True  # default
        assert config.cache_ttl_hours == 72
        assert config.max_alternatives == 5  # default
        assert config.deep_analysis_batch_size == 10  # default

    def test_should_fallback_to_defaults_on_invalid_integer_values(self, mocker):
        """Test fallback to defaults when integer values are invalid."""
        # Arrange
        mocker.patch.dict(
            "os.environ",
            {
                "PORTFOLIO_CACHE_TTL_HOURS": "invalid",
                "PORTFOLIO_MAX_ALTERNATIVES": "not_a_number",
                "PORTFOLIO_DEEP_ANALYSIS_BATCH_SIZE": "abc",
            },
        )

        # Act
        config = PortfolioAnalysisConfig.from_env()

        # Assert - should use defaults
        assert config.cache_ttl_hours == 24
        assert config.max_alternatives == 5
        assert config.deep_analysis_batch_size == 10

    def test_should_fallback_to_defaults_on_out_of_range_values(self, mocker):
        """Test fallback to defaults when values are out of valid range."""
        # Arrange
        mocker.patch.dict(
            "os.environ",
            {
                "PORTFOLIO_CACHE_TTL_HOURS": "200",  # > 168
                "PORTFOLIO_MAX_ALTERNATIVES": "15",  # > 10
                "PORTFOLIO_DEEP_ANALYSIS_BATCH_SIZE": "100",  # > 50
            },
        )

        # Act
        config = PortfolioAnalysisConfig.from_env()

        # Assert - should use defaults
        assert config.cache_ttl_hours == 24
        assert config.max_alternatives == 5
        assert config.deep_analysis_batch_size == 10

    def test_should_log_configuration_on_load(self, mocker):
        """Test that configuration is logged when loaded."""
        # Arrange
        mock_logger = mocker.patch("finwiz.config.portfolio_analysis_config.logger")
        mocker.patch.dict("os.environ", {"DEEP_PORTFOLIO_ANALYSIS": "true"})

        # Act
        PortfolioAnalysisConfig.from_env()

        # Assert
        assert mock_logger.info.called
        # Check that configuration values were logged
        log_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        assert any("Portfolio Analysis Configuration loaded" in call for call in log_calls)
        assert any("Deep Analysis Enabled: True" in call for call in log_calls)

    def test_should_validate_config_without_warnings(self, mocker):
        """Test config validation with valid settings."""
        # Arrange
        mock_logger = mocker.patch("finwiz.config.portfolio_analysis_config.logger")
        config = PortfolioAnalysisConfig(
            deep_analysis_enabled=True, cache_enabled=True, cache_ttl_hours=24, deep_analysis_batch_size=10, max_alternatives=5
        )

        # Act
        config.validate_config()

        # Assert
        # Should log success message
        log_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        assert any("Configuration validation passed without warnings" in call for call in log_calls)
        # Should not log any warnings
        assert not mock_logger.warning.called

    def test_should_warn_when_deep_analysis_enabled_without_cache(self, mocker):
        """Test warning when deep analysis is enabled but cache is disabled."""
        # Arrange
        mock_logger = mocker.patch("finwiz.config.portfolio_analysis_config.logger")
        config = PortfolioAnalysisConfig(deep_analysis_enabled=True, cache_enabled=False)

        # Act
        config.validate_config()

        # Assert
        assert mock_logger.warning.called
        warning_calls = [call[0][0] for call in mock_logger.warning.call_args_list]
        assert any("Deep analysis is enabled but caching is disabled" in call for call in warning_calls)

    def test_should_warn_when_cache_ttl_is_very_short(self, mocker):
        """Test warning when cache TTL is very short."""
        # Arrange
        mock_logger = mocker.patch("finwiz.config.portfolio_analysis_config.logger")
        config = PortfolioAnalysisConfig(cache_ttl_hours=3)

        # Act
        config.validate_config()

        # Assert
        assert mock_logger.warning.called
        warning_calls = [call[0][0] for call in mock_logger.warning.call_args_list]
        assert any("Cache TTL is very short" in call for call in warning_calls)

    def test_should_warn_when_batch_size_is_large(self, mocker):
        """Test warning when batch size is large."""
        # Arrange
        mock_logger = mocker.patch("finwiz.config.portfolio_analysis_config.logger")
        config = PortfolioAnalysisConfig(deep_analysis_batch_size=25)

        # Act
        config.validate_config()

        # Assert
        assert mock_logger.warning.called
        warning_calls = [call[0][0] for call in mock_logger.warning.call_args_list]
        assert any("Large batch size" in call for call in warning_calls)

    def test_should_warn_when_max_alternatives_is_high(self, mocker):
        """Test warning when max alternatives is high."""
        # Arrange
        mock_logger = mocker.patch("finwiz.config.portfolio_analysis_config.logger")
        config = PortfolioAnalysisConfig(max_alternatives=8)

        # Act
        config.validate_config()

        # Assert
        assert mock_logger.warning.called
        warning_calls = [call[0][0] for call in mock_logger.warning.call_args_list]
        assert any("High number of alternatives" in call for call in warning_calls)

    def test_should_log_multiple_warnings(self, mocker):
        """Test that multiple warnings are logged when multiple issues exist."""
        # Arrange
        mock_logger = mocker.patch("finwiz.config.portfolio_analysis_config.logger")
        config = PortfolioAnalysisConfig(
            deep_analysis_enabled=True, cache_enabled=False, cache_ttl_hours=2, deep_analysis_batch_size=30, max_alternatives=9
        )

        # Act
        config.validate_config()

        # Assert
        assert mock_logger.warning.call_count >= 4
        warning_calls = [call[0][0] for call in mock_logger.warning.call_args_list]
        assert any("Deep analysis is enabled but caching is disabled" in call for call in warning_calls)
        assert any("Cache TTL is very short" in call for call in warning_calls)
        assert any("Large batch size" in call for call in warning_calls)
        assert any("High number of alternatives" in call for call in warning_calls)
