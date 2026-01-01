"""Unit tests for yfinance configuration module."""

import pytest


class TestYFinanceSettings:
    """Tests for YFinanceSettings model."""

    def test_default_settings(self) -> None:
        """Test default YFinanceSettings values."""
        from finwiz.config.settings import YFinanceSettings

        settings = YFinanceSettings()

        assert settings.retries == 2
        assert settings.proxy is None
        assert settings.hide_exceptions is True
        assert settings.logging is False

    def test_custom_settings(self) -> None:
        """Test custom YFinanceSettings values."""
        from finwiz.config.settings import YFinanceSettings

        settings = YFinanceSettings(
            retries=5,
            proxy="http://proxy:8080",
            hide_exceptions=False,
            logging=True,
        )

        assert settings.retries == 5
        assert settings.proxy == "http://proxy:8080"
        assert settings.hide_exceptions is False
        assert settings.logging is True

    def test_retries_validation(self) -> None:
        """Test retries field validation."""
        from pydantic import ValidationError

        from finwiz.config.settings import YFinanceSettings

        # Valid range
        settings = YFinanceSettings(retries=0)
        assert settings.retries == 0

        settings = YFinanceSettings(retries=10)
        assert settings.retries == 10

        # Invalid: negative
        with pytest.raises(ValidationError):
            YFinanceSettings(retries=-1)

        # Invalid: too high
        with pytest.raises(ValidationError):
            YFinanceSettings(retries=11)


class TestGetYFinanceSettings:
    """Tests for get_yfinance_settings function."""

    def test_get_yfinance_settings(self) -> None:
        """Test get_yfinance_settings returns settings."""
        from finwiz.config.settings import get_yfinance_settings

        settings = get_yfinance_settings()

        assert settings is not None
        assert settings.retries == 2


class TestConfigureYFinance:
    """Tests for configure_yfinance function."""

    def test_configure_yfinance_first_call(self, mocker) -> None:
        """Test configure_yfinance returns True on first call."""
        from finwiz.config.yfinance_config import configure_yfinance, reset_yfinance_config

        # Reset state for clean test
        reset_yfinance_config()

        # Mock yfinance to avoid actual configuration
        mock_yf = mocker.MagicMock()
        mock_yf.config.network.retries = 0
        mock_yf.config.network.proxy = None
        mock_yf.config.debug.hide_exceptions = True
        mock_yf.config.debug.logging = False
        mocker.patch.dict("sys.modules", {"yfinance": mock_yf})

        result = configure_yfinance()

        assert result is True

    def test_configure_yfinance_second_call(self, mocker) -> None:
        """Test configure_yfinance returns False on second call."""
        from finwiz.config.yfinance_config import configure_yfinance, reset_yfinance_config

        # Reset state for clean test
        reset_yfinance_config()

        # Mock yfinance
        mock_yf = mocker.MagicMock()
        mock_yf.config.network.retries = 0
        mock_yf.config.network.proxy = None
        mock_yf.config.debug.hide_exceptions = True
        mock_yf.config.debug.logging = False
        mocker.patch.dict("sys.modules", {"yfinance": mock_yf})

        # First call
        configure_yfinance()

        # Second call should return False (already configured)
        result = configure_yfinance()

        assert result is False


class TestIsYFinanceConfigured:
    """Tests for is_yfinance_configured function."""

    def test_is_configured_after_configure(self, mocker) -> None:
        """Test is_yfinance_configured returns True after configuration."""
        from finwiz.config.yfinance_config import (
            configure_yfinance,
            is_yfinance_configured,
            reset_yfinance_config,
        )

        # Reset state
        reset_yfinance_config()

        # Mock yfinance
        mock_yf = mocker.MagicMock()
        mock_yf.config.network.retries = 0
        mock_yf.config.network.proxy = None
        mock_yf.config.debug.hide_exceptions = True
        mock_yf.config.debug.logging = False
        mocker.patch.dict("sys.modules", {"yfinance": mock_yf})

        assert is_yfinance_configured() is False
        configure_yfinance()
        assert is_yfinance_configured() is True


class TestResetYFinanceConfig:
    """Tests for reset_yfinance_config function."""

    def test_reset_clears_configured_state(self, mocker) -> None:
        """Test reset_yfinance_config clears the configured state."""
        from finwiz.config.yfinance_config import (
            configure_yfinance,
            is_yfinance_configured,
            reset_yfinance_config,
        )

        # Reset state
        reset_yfinance_config()

        # Mock yfinance
        mock_yf = mocker.MagicMock()
        mock_yf.config.network.retries = 0
        mock_yf.config.network.proxy = None
        mock_yf.config.debug.hide_exceptions = True
        mock_yf.config.debug.logging = False
        mocker.patch.dict("sys.modules", {"yfinance": mock_yf})

        configure_yfinance()
        assert is_yfinance_configured() is True

        reset_yfinance_config()
        assert is_yfinance_configured() is False


class TestGetYFinanceConfigStatus:
    """Tests for get_yfinance_config_status function."""

    def test_status_returns_dict(self) -> None:
        """Test get_yfinance_config_status returns a dictionary."""
        from finwiz.config.yfinance_config import get_yfinance_config_status

        status = get_yfinance_config_status()

        assert isinstance(status, dict)
        assert "configured" in status

    def test_status_includes_retry_settings(self, mocker) -> None:
        """Test status includes retry configuration."""
        from finwiz.config.yfinance_config import (
            configure_yfinance,
            get_yfinance_config_status,
            reset_yfinance_config,
        )

        # Reset and configure
        reset_yfinance_config()

        # Mock yfinance
        mock_yf = mocker.MagicMock()
        mock_yf.config.network.retries = 2
        mock_yf.config.network.proxy = None
        mock_yf.config.debug.hide_exceptions = True
        mock_yf.config.debug.logging = False
        mocker.patch.dict("sys.modules", {"yfinance": mock_yf})

        configure_yfinance()
        status = get_yfinance_config_status()

        assert status["configured"] is True
        assert status["retries"] == 2
