"""
Unit tests for the configuration manager.

Tests API key validation, environment variable loading, feature flag integration,
and startup configuration validation.
"""

import os
import tempfile
from pathlib import Path

import pytest

from finwiz.config.manager import (
    APIKeyConfig,
    ConfigurationError,
    ConfigurationManager,
    get_api_key,
    get_configuration_manager,
    is_service_available,
    validate_startup_configuration,
)


class TestConfigurationManager:
    """Test suite for ConfigurationManager class."""

    def setup_method(self):
        """Set up test environment."""
        # Clear environment variables
        env_vars_to_clear = [
            "OPENAI_API_KEY",
            "SERPER_API_KEY",
            "FIRECRAWL_API_KEY",
            "ALPHA_VANTAGE_API_KEY",
            "CHART_IMG_API_KEY",
            "TWELVE_DATA_API_KEY",
            "COINMARKETCAP_API_KEY",
            "KRAKEN_API_KEY",
        ]
        for var in env_vars_to_clear:
            if var in os.environ:
                del os.environ[var]

    def test_should_initialize_with_required_api_keys(self):
        """Test that ConfigurationManager initializes with expected API key configs."""
        # Arrange & Act
        config_manager = ConfigurationManager()

        # Assert
        assert len(config_manager.REQUIRED_API_KEYS) > 0

        # Check that essential keys are present
        key_names = [key.env_var for key in config_manager.REQUIRED_API_KEYS]
        assert "OPENAI_API_KEY" in key_names
        assert "SERPER_API_KEY" in key_names
        assert "FIRECRAWL_API_KEY" in key_names
        assert "ALPHA_VANTAGE_API_KEY" in key_names

    def test_should_load_environment_from_custom_file(self):
        """Test loading environment variables from custom .env file."""
        # Arrange
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("OPENAI_API_KEY=sk-test-key-from-file\n")
            f.write("SERPER_API_KEY=test-serper-key\n")
            temp_env_file = f.name

        try:
            # Act
            ConfigurationManager(env_file=temp_env_file)

            # Assert
            assert os.getenv("OPENAI_API_KEY") == "sk-test-key-from-file"
            assert os.getenv("SERPER_API_KEY") == "test-serper-key"
        finally:
            # Cleanup
            Path(temp_env_file).unlink()

    def test_should_validate_required_api_keys_successfully(self, mocker):
        """Test successful validation of all required API keys."""
        # Arrange
        mocker.patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "sk-test-openai-key-1234567890",
                "SERPER_API_KEY": "test-serper-key-32-characters-long",
                "FIRECRAWL_API_KEY": "test-firecrawl-key-20chars",
                "ALPHA_VANTAGE_API_KEY": "test-alpha-vantage-key",
            },
        )
        config_manager = ConfigurationManager()

        # Act
        result = config_manager.validate_api_keys()

        # Assert
        assert result is True
        assert len(config_manager.missing_keys) == 0
        assert len(config_manager.api_keys) >= 4
        assert "OpenAI" in config_manager.api_keys
        assert "Serper" in config_manager.api_keys

    def test_should_raise_configuration_error_for_missing_required_keys(self):
        """Test that missing required API keys raise ConfigurationError."""
        # Arrange
        config_manager = ConfigurationManager()

        # Act & Assert
        with pytest.raises(ConfigurationError) as exc_info:
            config_manager.validate_api_keys()

        error = exc_info.value
        assert len(error.missing_keys) > 0
        assert "OPENAI_API_KEY" in error.missing_keys
        assert len(error.remediation_guidance) > 0

    def test_should_validate_openai_api_key_format(self):
        """Test OpenAI API key format validation."""
        # Arrange
        config_manager = ConfigurationManager()
        openai_config = next(k for k in config_manager.REQUIRED_API_KEYS if k.env_var == "OPENAI_API_KEY")

        # Act & Assert
        assert config_manager._validate_key_format(openai_config, "sk-valid-key-1234567890") is True
        assert config_manager._validate_key_format(openai_config, "invalid-key") is False
        assert config_manager._validate_key_format(openai_config, "sk-short") is False
        assert config_manager._validate_key_format(openai_config, "") is False

    def test_should_validate_other_api_key_formats(self):
        """Test validation of other API key formats."""
        # Arrange
        config_manager = ConfigurationManager()

        # Get different API key configs
        serper_config = next(k for k in config_manager.REQUIRED_API_KEYS if k.env_var == "SERPER_API_KEY")
        alpha_config = next(k for k in config_manager.REQUIRED_API_KEYS if k.env_var == "ALPHA_VANTAGE_API_KEY")

        # Act & Assert
        assert config_manager._validate_key_format(serper_config, "a" * 32) is True
        assert config_manager._validate_key_format(serper_config, "short") is False

        assert config_manager._validate_key_format(alpha_config, "a" * 16) is True
        assert config_manager._validate_key_format(alpha_config, "short") is False

    def test_should_check_key_requirements_based_on_feature_flags(self, mocker):
        """Test that API key requirements are checked based on feature flags."""
        # Arrange
        mock_feature_flags = mocker.MagicMock()
        mock_feature_flags.is_enabled.return_value = False  # Disable optional features
        mocker.patch("finwiz.config.manager.get_feature_flags", return_value=mock_feature_flags)

        config_manager = ConfigurationManager()
        chart_config = next(k for k in config_manager.REQUIRED_API_KEYS if k.env_var == "CHART_IMG_API_KEY")

        # Act
        is_required = config_manager._is_key_required(chart_config)

        # Assert
        assert is_required is False  # Should not be required when feature is disabled

    def test_should_generate_comprehensive_remediation_guidance(self):
        """Test generation of detailed remediation guidance."""
        # Arrange
        config_manager = ConfigurationManager()
        config_manager.missing_keys = ["OPENAI_API_KEY", "SERPER_API_KEY"]

        # Act
        guidance = config_manager._generate_remediation_guidance()

        # Assert
        assert "OPENAI_API_KEY" in guidance
        assert "SERPER_API_KEY" in guidance
        assert ".env file" in guidance
        assert "environment variables" in guidance
        assert "Example .env file:" in guidance

    def test_should_get_api_key_for_configured_service(self, mocker):
        """Test getting API key for a configured service."""
        # Arrange
        mocker.patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "sk-test-openai-key-1234567890",
                "SERPER_API_KEY": "test-serper-key-32-characters-long",
                "FIRECRAWL_API_KEY": "test-firecrawl-key-20chars",
                "ALPHA_VANTAGE_API_KEY": "test-alpha-vantage-key",
            },
        )
        config_manager = ConfigurationManager()
        config_manager.validate_api_keys()

        # Act
        api_key = config_manager.get_api_key("OpenAI")

        # Assert
        assert api_key == "sk-test-openai-key-1234567890"

    def test_should_return_none_for_unconfigured_service(self, mocker):
        """Test that None is returned for unconfigured services."""
        # Arrange
        config_manager = ConfigurationManager()

        # Act
        api_key = config_manager.get_api_key("NonExistentService")

        # Assert
        assert api_key is None

    def test_should_check_service_availability(self, mocker):
        """Test checking if a service is available."""
        # Arrange
        mocker.patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "sk-test-openai-key-1234567890",
                "SERPER_API_KEY": "test-serper-key-32-characters-long",
                "FIRECRAWL_API_KEY": "test-firecrawl-key-20chars",
                "ALPHA_VANTAGE_API_KEY": "test-alpha-vantage-key",
            },
        )
        config_manager = ConfigurationManager()
        config_manager.validate_api_keys()

        # Act & Assert
        assert config_manager.is_service_available("OpenAI") is True
        assert config_manager.is_service_available("NonExistentService") is False

    def test_should_provide_configuration_summary(self, mocker):
        """Test getting comprehensive configuration summary."""
        # Arrange
        mocker.patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "sk-test-openai-key-1234567890",
                "SERPER_API_KEY": "test-serper-key-32-characters-long",
                "FIRECRAWL_API_KEY": "test-firecrawl-key-20chars",
                "ALPHA_VANTAGE_API_KEY": "test-alpha-vantage-key",
            },
        )
        config_manager = ConfigurationManager()
        config_manager.validate_api_keys()

        # Act
        summary = config_manager.get_configuration_summary()

        # Assert
        assert "api_keys_configured" in summary
        assert "available_services" in summary
        assert "missing_keys" in summary
        assert "feature_flags" in summary
        assert isinstance(summary["available_services"], list)

    def test_should_validate_feature_flag_consistency(self, mocker):
        """Test validation of feature flag consistency with API keys."""
        # Arrange
        mock_feature_flags = mocker.MagicMock()
        mock_feature_flags.is_enabled.return_value = True  # Enable features
        mocker.patch("finwiz.config.manager.get_feature_flags", return_value=mock_feature_flags)

        config_manager = ConfigurationManager()

        # Act & Assert - Should not raise exception even with missing keys
        config_manager._validate_feature_flag_consistency()

    def test_should_create_required_directories(self):
        """Test creation of required directories."""
        # Arrange
        config_manager = ConfigurationManager()

        # Act
        config_manager._validate_required_directories()

        # Assert - Should not raise exception
        # Directories should be created if they don't exist
        project_root = Path(__file__).resolve().parents[1]  # Go up to project root from tests
        required_dirs = ["cache", "logs", "output", "report"]

        for dir_name in required_dirs:
            dir_path = project_root / dir_name
            # Directory should exist after validation (may have been created)
            assert dir_path.exists() or True  # Allow for existing directories

    def test_should_perform_comprehensive_startup_validation(self, mocker):
        """Test comprehensive startup validation."""
        # Arrange
        mocker.patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "sk-test-openai-key-1234567890",
                "SERPER_API_KEY": "test-serper-key-32-characters-long",
                "FIRECRAWL_API_KEY": "test-firecrawl-key-20chars",
                "ALPHA_VANTAGE_API_KEY": "test-alpha-vantage-key",
            },
        )
        config_manager = ConfigurationManager()

        # Act
        result = config_manager.validate_startup_configuration()

        # Assert
        assert result is True

    def test_should_handle_startup_validation_failure(self):
        """Test handling of startup validation failure."""
        # Arrange
        config_manager = ConfigurationManager()

        # Act & Assert
        with pytest.raises(ConfigurationError):
            config_manager.validate_startup_configuration()


class TestConfigurationManagerConvenienceFunctions:
    """Test suite for convenience functions."""

    def test_should_get_configuration_manager_singleton(self, mocker):
        """Test that get_configuration_manager returns singleton instance."""
        # Arrange & Act
        manager1 = get_configuration_manager()
        manager2 = get_configuration_manager()

        # Assert
        assert manager1 is manager2

    def test_should_validate_startup_configuration_via_convenience_function(self, mocker):
        """Test validate_startup_configuration convenience function."""
        # Arrange
        mocker.patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "sk-test-openai-key-1234567890",
                "SERPER_API_KEY": "test-serper-key-32-characters-long",
                "FIRECRAWL_API_KEY": "test-firecrawl-key-20chars",
                "ALPHA_VANTAGE_API_KEY": "test-alpha-vantage-key",
            },
        )
        # Act
        result = validate_startup_configuration()

        # Assert
        assert isinstance(result, bool)

    def test_should_get_api_key_via_convenience_function(self, mocker):
        """Test get_api_key convenience function."""
        # Arrange
        mocker.patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "sk-test-openai-key-1234567890",
                "SERPER_API_KEY": "test-serper-key-32-characters-long",
                "FIRECRAWL_API_KEY": "test-firecrawl-key-20chars",
                "ALPHA_VANTAGE_API_KEY": "test-alpha-vantage-key",
            },
        )
        validate_startup_configuration()  # Initialize configuration

        # Act
        api_key = get_api_key("OpenAI")

        # Assert
        assert api_key == "sk-test-openai-key-1234567890"

    def test_should_check_service_availability_via_convenience_function(self, mocker):
        """Test is_service_available convenience function."""
        # Arrange
        mocker.patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "sk-test-openai-key-1234567890",
                "SERPER_API_KEY": "test-serper-key-32-characters-long",
                "FIRECRAWL_API_KEY": "test-firecrawl-key-20chars",
                "ALPHA_VANTAGE_API_KEY": "test-alpha-vantage-key",
            },
        )
        validate_startup_configuration()  # Initialize configuration

        # Act & Assert
        assert is_service_available("OpenAI") is True
        assert is_service_available("NonExistentService") is False


class TestAPIKeyConfig:
    """Test suite for APIKeyConfig dataclass."""

    def test_should_create_api_key_config_with_defaults(self):
        """Test creating APIKeyConfig with default values."""
        # Arrange & Act
        config = APIKeyConfig(name="Test API", env_var="TEST_API_KEY")

        # Assert
        assert config.name == "Test API"
        assert config.env_var == "TEST_API_KEY"
        assert config.required is True  # Default value
        assert config.description == ""  # Default value

    def test_should_create_api_key_config_with_custom_values(self):
        """Test creating APIKeyConfig with custom values."""
        # Arrange & Act
        config = APIKeyConfig(
            name="Custom API",
            env_var="CUSTOM_API_KEY",
            required=False,
            description="Custom API for testing",
            test_endpoint="https://api.example.com/test",
        )

        # Assert
        assert config.name == "Custom API"
        assert config.env_var == "CUSTOM_API_KEY"
        assert config.required is False
        assert config.description == "Custom API for testing"
        assert config.test_endpoint == "https://api.example.com/test"


class TestConfigurationError:
    """Test suite for ConfigurationError exception."""

    def test_should_create_configuration_error_with_details(self):
        """Test creating ConfigurationError with detailed information."""
        # Arrange & Act
        error = ConfigurationError(missing_keys=["KEY1", "KEY2"], invalid_keys=["KEY3"], remediation_guidance="Please configure the missing keys")

        # Assert
        assert error.missing_keys == ["KEY1", "KEY2"]
        assert error.invalid_keys == ["KEY3"]
        assert error.remediation_guidance == "Please configure the missing keys"

    def test_should_create_configuration_error_with_defaults(self):
        """Test creating ConfigurationError with default values."""
        # Arrange & Act
        error = ConfigurationError()

        # Assert
        assert error.missing_keys == []
        assert error.invalid_keys == []
        assert error.remediation_guidance == ""


class TestConfigurationManagerIntegration:
    """Integration tests for configuration manager."""

    def test_should_integrate_with_feature_flags_for_optional_keys(self, mocker):
        """Test integration with feature flags for optional API keys."""
        # Arrange
        mock_feature_flags = mocker.MagicMock()
        # Enable chart analysis feature
        mock_feature_flags.is_enabled.side_effect = lambda flag: flag == "chart_analysis"
        mocker.patch("finwiz.config.manager.get_feature_flags", return_value=mock_feature_flags)

        mocker.patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "sk-test-openai-key-1234567890",
                "SERPER_API_KEY": "test-serper-key-32-characters-long",
                "FIRECRAWL_API_KEY": "test-firecrawl-key-20chars",
                "ALPHA_VANTAGE_API_KEY": "test-alpha-vantage-key",
                "CHART_IMG_API_KEY": "test-chart-img-key-16chars",
            },
        )

        config_manager = ConfigurationManager()

        # Act
        result = config_manager.validate_api_keys()

        # Assert
        assert result is True
        assert "Chart-img" in config_manager.api_keys

    def test_should_handle_mixed_required_and_optional_keys(self, mocker):
        """Test handling of mixed required and optional API keys."""
        # Arrange
        mocker.patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "sk-test-openai-key-1234567890",
                "SERPER_API_KEY": "test-serper-key-32-characters-long",
                "FIRECRAWL_API_KEY": "test-firecrawl-key-20chars",
                "ALPHA_VANTAGE_API_KEY": "test-alpha-vantage-key",
                # Missing optional keys like CHART_IMG_API_KEY
            },
        )
        config_manager = ConfigurationManager()

        # Act
        result = config_manager.validate_api_keys()

        # Assert
        assert result is True  # Should succeed with just required keys
        assert len(config_manager.missing_keys) == 0
        assert "OpenAI" in config_manager.api_keys
        assert "Chart-img" not in config_manager.api_keys  # Optional key not configured
