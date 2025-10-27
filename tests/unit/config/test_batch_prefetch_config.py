"""
Unit tests for batch prefetch configuration module.

Tests configuration loading, validation, and environment variable handling.
"""

import os

import pytest

from finwiz.config.batch_prefetch_config import (
    BatchPrefetchConfig,
    get_batch_prefetch_config,
    load_batch_prefetch_config,
    reset_config_cache,
)


class TestBatchPrefetchConfig:
    """Test suite for BatchPrefetchConfig."""

    def test_should_create_config_with_defaults(self) -> None:
        """Test creating config with default values."""
        config = BatchPrefetchConfig()

        assert config.enabled is True
        assert config.alpha_vantage_rate_limit == 5
        assert config.min_holdings_for_batch == 10

    def test_should_create_config_with_custom_values(self) -> None:
        """Test creating config with custom values."""
        config = BatchPrefetchConfig(enabled=False, alpha_vantage_rate_limit=75, min_holdings_for_batch=20)

        assert config.enabled is False
        assert config.alpha_vantage_rate_limit == 75
        assert config.min_holdings_for_batch == 20

    def test_should_reject_invalid_rate_limit(self) -> None:
        """Test that invalid rate limit raises ValueError."""
        with pytest.raises(ValueError, match="alpha_vantage_rate_limit must be >= 1"):
            BatchPrefetchConfig(alpha_vantage_rate_limit=0)

    def test_should_reject_invalid_min_holdings(self) -> None:
        """Test that invalid min holdings raises ValueError."""
        with pytest.raises(ValueError, match="min_holdings_for_batch must be >= 1"):
            BatchPrefetchConfig(min_holdings_for_batch=0)

    def test_should_warn_on_high_rate_limit(self, caplog) -> None:
        """Test that high rate limit triggers warning."""
        BatchPrefetchConfig(alpha_vantage_rate_limit=150)

        assert "very high" in caplog.text.lower()
        assert "premium" in caplog.text.lower()


class TestLoadBatchPrefetchConfig:
    """Test suite for load_batch_prefetch_config."""

    def test_should_load_defaults_when_no_env_vars(self, mocker) -> None:
        """Test loading defaults when environment variables are not set."""
        # Mock environment to have no batch prefetch variables
        # Remove the keys entirely rather than setting to empty string
        env_copy = os.environ.copy()
        for key in ["BATCH_PREFETCH_ENABLED", "ALPHA_VANTAGE_RATE_LIMIT", "BATCH_PREFETCH_MIN_HOLDINGS"]:
            env_copy.pop(key, None)

        mocker.patch.dict(os.environ, env_copy, clear=True)

        config = load_batch_prefetch_config()

        assert config.enabled is True  # Default
        assert config.alpha_vantage_rate_limit == 5  # Default
        assert config.min_holdings_for_batch == 10  # Default

    def test_should_load_enabled_from_env_true(self, mocker) -> None:
        """Test loading enabled=true from environment."""
        mocker.patch.dict(os.environ, {"BATCH_PREFETCH_ENABLED": "true"})

        config = load_batch_prefetch_config()

        assert config.enabled is True

    def test_should_load_enabled_from_env_false(self, mocker) -> None:
        """Test loading enabled=false from environment."""
        mocker.patch.dict(os.environ, {"BATCH_PREFETCH_ENABLED": "false"})

        config = load_batch_prefetch_config()

        assert config.enabled is False

    def test_should_load_enabled_from_env_variations(self, mocker) -> None:
        """Test loading enabled from various environment variable formats."""
        test_cases = [
            ("1", True),
            ("yes", True),
            ("on", True),
            ("0", False),
            ("no", False),
            ("off", False),
            ("invalid", False),
        ]

        for env_value, expected in test_cases:
            mocker.patch.dict(os.environ, {"BATCH_PREFETCH_ENABLED": env_value})
            config = load_batch_prefetch_config()
            assert config.enabled == expected, f"Failed for env_value={env_value}"

    def test_should_load_rate_limit_from_env(self, mocker) -> None:
        """Test loading rate limit from environment."""
        mocker.patch.dict(os.environ, {"ALPHA_VANTAGE_RATE_LIMIT": "75"})

        config = load_batch_prefetch_config()

        assert config.alpha_vantage_rate_limit == 75

    def test_should_handle_invalid_rate_limit_env(self, mocker, caplog) -> None:
        """Test handling invalid rate limit in environment."""
        mocker.patch.dict(os.environ, {"ALPHA_VANTAGE_RATE_LIMIT": "invalid"})

        config = load_batch_prefetch_config()

        assert config.alpha_vantage_rate_limit == 5  # Default
        assert "Invalid ALPHA_VANTAGE_RATE_LIMIT" in caplog.text

    def test_should_load_min_holdings_from_env(self, mocker) -> None:
        """Test loading min holdings from environment."""
        mocker.patch.dict(os.environ, {"BATCH_PREFETCH_MIN_HOLDINGS": "20"})

        config = load_batch_prefetch_config()

        assert config.min_holdings_for_batch == 20

    def test_should_handle_invalid_min_holdings_env(self, mocker, caplog) -> None:
        """Test handling invalid min holdings in environment."""
        mocker.patch.dict(os.environ, {"BATCH_PREFETCH_MIN_HOLDINGS": "invalid"})

        config = load_batch_prefetch_config()

        assert config.min_holdings_for_batch == 10  # Default
        assert "Invalid BATCH_PREFETCH_MIN_HOLDINGS" in caplog.text


class TestGetBatchPrefetchConfig:
    """Test suite for get_batch_prefetch_config."""

    def test_should_return_config_with_logging(self, mocker, caplog) -> None:
        """Test that get_batch_prefetch_config logs configuration."""
        import logging

        mocker.patch.dict(os.environ, {"BATCH_PREFETCH_ENABLED": "true"})

        # Set log level to INFO to capture the logs
        caplog.set_level(logging.INFO)

        config = get_batch_prefetch_config(log_config=True)

        assert config.enabled is True
        assert "BATCH PREFETCH CONFIGURATION" in caplog.text
        assert "Enabled: True" in caplog.text

    def test_should_return_config_without_logging(self, mocker, caplog) -> None:
        """Test that get_batch_prefetch_config can skip logging."""
        mocker.patch.dict(os.environ, {"BATCH_PREFETCH_ENABLED": "true"})

        config = get_batch_prefetch_config(log_config=False)

        assert config.enabled is True
        assert "BATCH PREFETCH CONFIGURATION" not in caplog.text


class TestConfigCaching:
    """Test suite for configuration caching."""

    def test_should_cache_config(self, mocker) -> None:
        """Test that configuration is cached."""
        from finwiz.config.batch_prefetch_config import get_cached_batch_prefetch_config

        # Reset cache first
        reset_config_cache()

        mocker.patch.dict(os.environ, {"BATCH_PREFETCH_ENABLED": "true"})

        # First call should load from environment
        config1 = get_cached_batch_prefetch_config()

        # Change environment
        mocker.patch.dict(os.environ, {"BATCH_PREFETCH_ENABLED": "false"})

        # Second call should return cached config (not reload)
        config2 = get_cached_batch_prefetch_config()

        assert config1.enabled is True
        assert config2.enabled is True  # Still cached value

    def test_should_reset_cache(self, mocker) -> None:
        """Test that cache can be reset."""
        from finwiz.config.batch_prefetch_config import get_cached_batch_prefetch_config

        # Reset cache first
        reset_config_cache()

        mocker.patch.dict(os.environ, {"BATCH_PREFETCH_ENABLED": "true"})

        # First call
        config1 = get_cached_batch_prefetch_config()
        assert config1.enabled is True

        # Change environment and reset cache
        mocker.patch.dict(os.environ, {"BATCH_PREFETCH_ENABLED": "false"})
        reset_config_cache()

        # Should reload from environment
        config2 = get_cached_batch_prefetch_config()
        assert config2.enabled is False
