"""
Unit tests for batch prefetch configuration.

Tests for BatchPrefetchConfig class and related functions.
"""

import pytest
from faker import Faker

from finwiz.config.batch_prefetch_config import (
    BatchPrefetchConfig,
    load_batch_prefetch_config,
    should_use_alpha_vantage,
    get_batch_prefetch_config,
    get_cached_batch_prefetch_config,
    reset_config_cache,
)


class TestBatchPrefetchConfig:
    """Tests for BatchPrefetchConfig dataclass."""

    @pytest.fixture
    def fake(self):
        """Provide Faker instance."""
        return Faker()

    def test_should_initialize_with_defaults(self):
        """Test initialization with default values."""
        config = BatchPrefetchConfig()

        assert config.enabled is True
        assert config.alpha_vantage_rate_limit == 5
        assert config.min_holdings_for_batch == 10

    def test_should_initialize_with_custom_values(self, fake):
        """Test initialization with custom values."""
        rate_limit = fake.random_int(min=1, max=100)
        min_holdings = fake.random_int(min=1, max=50)

        config = BatchPrefetchConfig(
            enabled=False,
            alpha_vantage_rate_limit=rate_limit,
            min_holdings_for_batch=min_holdings,
        )

        assert config.enabled is False
        assert config.alpha_vantage_rate_limit == rate_limit
        assert config.min_holdings_for_batch == min_holdings

    def test_should_raise_for_zero_rate_limit(self):
        """Test validation fails for zero rate limit."""
        with pytest.raises(ValueError, match="alpha_vantage_rate_limit must be >= 1"):
            BatchPrefetchConfig(alpha_vantage_rate_limit=0)

    def test_should_raise_for_negative_rate_limit(self):
        """Test validation fails for negative rate limit."""
        with pytest.raises(ValueError, match="alpha_vantage_rate_limit must be >= 1"):
            BatchPrefetchConfig(alpha_vantage_rate_limit=-1)

    def test_should_raise_for_zero_min_holdings(self):
        """Test validation fails for zero min holdings."""
        with pytest.raises(ValueError, match="min_holdings_for_batch must be >= 1"):
            BatchPrefetchConfig(min_holdings_for_batch=0)

    def test_should_raise_for_negative_min_holdings(self):
        """Test validation fails for negative min holdings."""
        with pytest.raises(ValueError, match="min_holdings_for_batch must be >= 1"):
            BatchPrefetchConfig(min_holdings_for_batch=-5)

    def test_should_warn_for_high_rate_limit(self, mocker):
        """Test warning is logged for high rate limit."""
        mock_logger = mocker.patch("finwiz.config.batch_prefetch_config.logger")

        BatchPrefetchConfig(alpha_vantage_rate_limit=150)

        mock_logger.warning.assert_called()

    def test_should_log_configuration(self, mocker):
        """Test log_configuration logs config details."""
        mock_logger = mocker.patch("finwiz.config.batch_prefetch_config.logger")
        config = BatchPrefetchConfig()

        config.log_configuration()

        assert mock_logger.info.called


class TestLoadBatchPrefetchConfig:
    """Tests for load_batch_prefetch_config function."""

    @pytest.fixture(autouse=True)
    def reset_cache(self):
        """Reset config cache before each test."""
        reset_config_cache()
        yield
        reset_config_cache()

    def test_should_load_default_config(self, mocker):
        """Test loading config with defaults."""
        mocker.patch.dict("os.environ", {}, clear=True)

        config = load_batch_prefetch_config()

        assert config.enabled is True
        assert config.alpha_vantage_rate_limit == 5
        assert config.min_holdings_for_batch == 10

    def test_should_load_enabled_true(self, mocker):
        """Test loading enabled=true from env."""
        mocker.patch.dict("os.environ", {"BATCH_PREFETCH_ENABLED": "true"})

        config = load_batch_prefetch_config()

        assert config.enabled is True

    def test_should_load_enabled_1(self, mocker):
        """Test loading enabled=1 from env."""
        mocker.patch.dict("os.environ", {"BATCH_PREFETCH_ENABLED": "1"})

        config = load_batch_prefetch_config()

        assert config.enabled is True

    def test_should_load_enabled_yes(self, mocker):
        """Test loading enabled=yes from env."""
        mocker.patch.dict("os.environ", {"BATCH_PREFETCH_ENABLED": "yes"})

        config = load_batch_prefetch_config()

        assert config.enabled is True

    def test_should_load_enabled_on(self, mocker):
        """Test loading enabled=on from env."""
        mocker.patch.dict("os.environ", {"BATCH_PREFETCH_ENABLED": "on"})

        config = load_batch_prefetch_config()

        assert config.enabled is True

    def test_should_load_enabled_false(self, mocker):
        """Test loading enabled=false from env."""
        mocker.patch.dict("os.environ", {"BATCH_PREFETCH_ENABLED": "false"})

        config = load_batch_prefetch_config()

        assert config.enabled is False

    def test_should_load_rate_limit_from_env(self, mocker):
        """Test loading rate limit from env."""
        mocker.patch.dict("os.environ", {"ALPHA_VANTAGE_RATE_LIMIT": "75"})

        config = load_batch_prefetch_config()

        assert config.alpha_vantage_rate_limit == 75

    def test_should_use_default_for_invalid_rate_limit(self, mocker):
        """Test default rate limit for invalid env value."""
        mocker.patch.dict("os.environ", {"ALPHA_VANTAGE_RATE_LIMIT": "invalid"})

        config = load_batch_prefetch_config()

        assert config.alpha_vantage_rate_limit == 5

    def test_should_load_min_holdings_from_env(self, mocker):
        """Test loading min holdings from env."""
        mocker.patch.dict("os.environ", {"BATCH_PREFETCH_MIN_HOLDINGS": "20"})

        config = load_batch_prefetch_config()

        assert config.min_holdings_for_batch == 20

    def test_should_use_default_for_invalid_min_holdings(self, mocker):
        """Test default min holdings for invalid env value."""
        mocker.patch.dict("os.environ", {"BATCH_PREFETCH_MIN_HOLDINGS": "abc"})

        config = load_batch_prefetch_config()

        assert config.min_holdings_for_batch == 10


class TestShouldUseAlphaVantage:
    """Tests for should_use_alpha_vantage function."""

    def test_should_return_false_by_default(self, mocker):
        """Test returns False when env not set."""
        mocker.patch.dict("os.environ", {}, clear=True)

        result = should_use_alpha_vantage()

        assert result is False

    def test_should_return_false_when_disabled(self, mocker):
        """Test returns False when explicitly disabled."""
        mocker.patch.dict("os.environ", {"ENABLE_ALPHA_VANTAGE": "false"})

        result = should_use_alpha_vantage()

        assert result is False

    def test_should_return_true_when_enabled(self, mocker):
        """Test returns True when enabled."""
        mocker.patch.dict("os.environ", {"ENABLE_ALPHA_VANTAGE": "true"})

        result = should_use_alpha_vantage()

        assert result is True

    def test_should_return_true_for_1(self, mocker):
        """Test returns True for '1' value."""
        mocker.patch.dict("os.environ", {"ENABLE_ALPHA_VANTAGE": "1"})

        result = should_use_alpha_vantage()

        assert result is True

    def test_should_return_true_for_yes(self, mocker):
        """Test returns True for 'yes' value."""
        mocker.patch.dict("os.environ", {"ENABLE_ALPHA_VANTAGE": "yes"})

        result = should_use_alpha_vantage()

        assert result is True

    def test_should_return_true_for_on(self, mocker):
        """Test returns True for 'on' value."""
        mocker.patch.dict("os.environ", {"ENABLE_ALPHA_VANTAGE": "on"})

        result = should_use_alpha_vantage()

        assert result is True


class TestGetBatchPrefetchConfig:
    """Tests for get_batch_prefetch_config function."""

    @pytest.fixture(autouse=True)
    def reset_cache(self):
        """Reset config cache before each test."""
        reset_config_cache()
        yield
        reset_config_cache()

    def test_should_return_config(self, mocker):
        """Test returns config object."""
        mocker.patch.dict("os.environ", {}, clear=True)
        # Suppress logging
        mocker.patch("finwiz.config.batch_prefetch_config.logger")

        config = get_batch_prefetch_config(log_config=False)

        assert isinstance(config, BatchPrefetchConfig)

    def test_should_log_when_requested(self, mocker):
        """Test logs config when log_config=True."""
        mocker.patch.dict("os.environ", {}, clear=True)
        mock_logger = mocker.patch("finwiz.config.batch_prefetch_config.logger")

        get_batch_prefetch_config(log_config=True)

        assert mock_logger.info.called


class TestGetCachedBatchPrefetchConfig:
    """Tests for get_cached_batch_prefetch_config function."""

    @pytest.fixture(autouse=True)
    def reset_cache(self):
        """Reset config cache before each test."""
        reset_config_cache()
        yield
        reset_config_cache()

    def test_should_return_cached_config(self, mocker):
        """Test returns cached config on subsequent calls."""
        mocker.patch.dict("os.environ", {}, clear=True)

        config1 = get_cached_batch_prefetch_config()
        config2 = get_cached_batch_prefetch_config()

        assert config1 is config2

    def test_should_cache_config(self, mocker):
        """Test config is cached after first call."""
        mocker.patch.dict("os.environ", {"ALPHA_VANTAGE_RATE_LIMIT": "50"})

        config1 = get_cached_batch_prefetch_config()

        # Change env var
        mocker.patch.dict("os.environ", {"ALPHA_VANTAGE_RATE_LIMIT": "100"})

        config2 = get_cached_batch_prefetch_config()

        # Should still be original cached value
        assert config2.alpha_vantage_rate_limit == 50


class TestResetConfigCache:
    """Tests for reset_config_cache function."""

    def test_should_reset_cache(self, mocker):
        """Test cache is reset."""
        mocker.patch.dict("os.environ", {"ALPHA_VANTAGE_RATE_LIMIT": "50"})

        config1 = get_cached_batch_prefetch_config()
        assert config1.alpha_vantage_rate_limit == 50

        # Change env var
        mocker.patch.dict("os.environ", {"ALPHA_VANTAGE_RATE_LIMIT": "100"})

        # Reset cache
        reset_config_cache()

        config2 = get_cached_batch_prefetch_config()

        # Should be new value
        assert config2.alpha_vantage_rate_limit == 100
