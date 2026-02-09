"""
Unit tests for resilience configuration.

Tests for ResilienceConfig class and related functions.
"""

import pytest
from faker import Faker

from finwiz.config.resilience_config import (
    ResilienceConfig,
    get_resilience_config,
    reset_resilience_config,
)


class TestResilienceConfig:
    """Tests for ResilienceConfig dataclass."""

    @pytest.fixture
    def fake(self):
        """Provide Faker instance."""
        return Faker()

    @pytest.fixture
    def valid_config(self):
        """Create a valid config for testing."""
        return ResilienceConfig(
            max_retries=3,
            retry_base_delay=2.0,
            retry_max_delay=60.0,
            holding_timeout=300,
            flow_timeout=7200,
            auto_resume=False,
            state_max_age_hours=24,
            parallel_limit=10,
            deep_analysis_parallel_limit=3,
            cleanup_state_on_success=False,
            state_cleanup_max_age_days=7,
        )

    def test_should_initialize_with_valid_values(self, valid_config):
        """Test initialization with valid values."""
        assert valid_config.max_retries == 3
        assert valid_config.retry_base_delay == 2.0
        assert valid_config.retry_max_delay == 60.0
        assert valid_config.holding_timeout == 300
        assert valid_config.flow_timeout == 7200
        assert valid_config.auto_resume is False
        assert valid_config.state_max_age_hours == 24
        assert valid_config.parallel_limit == 10
        assert valid_config.deep_analysis_parallel_limit == 3
        assert valid_config.cleanup_state_on_success is False
        assert valid_config.state_cleanup_max_age_days == 7

    def test_should_validate_successfully(self, valid_config):
        """Test validation passes for valid config."""
        # Should not raise
        valid_config.validate()

    def test_should_raise_for_holding_timeout_gte_flow_timeout(self):
        """Test validation fails when holding_timeout >= flow_timeout."""
        config = ResilienceConfig(
            max_retries=3,
            retry_base_delay=2.0,
            retry_max_delay=60.0,
            holding_timeout=7200,  # Equal to flow_timeout
            flow_timeout=7200,
            auto_resume=False,
            state_max_age_hours=24,
            parallel_limit=10,
            deep_analysis_parallel_limit=3,
            cleanup_state_on_success=False,
            state_cleanup_max_age_days=7,
        )

        with pytest.raises(ValueError, match="holding_timeout.*must be less than flow_timeout"):
            config.validate()

    def test_should_raise_for_holding_timeout_greater_than_flow_timeout(self):
        """Test validation fails when holding_timeout > flow_timeout."""
        config = ResilienceConfig(
            max_retries=3,
            retry_base_delay=2.0,
            retry_max_delay=60.0,
            holding_timeout=8000,  # Greater than flow_timeout
            flow_timeout=7200,
            auto_resume=False,
            state_max_age_hours=24,
            parallel_limit=10,
            deep_analysis_parallel_limit=3,
            cleanup_state_on_success=False,
            state_cleanup_max_age_days=7,
        )

        with pytest.raises(ValueError, match="holding_timeout.*must be less than flow_timeout"):
            config.validate()

    def test_should_raise_for_negative_max_retries(self):
        """Test validation fails for negative max_retries."""
        config = ResilienceConfig(
            max_retries=-1,
            retry_base_delay=2.0,
            retry_max_delay=60.0,
            holding_timeout=300,
            flow_timeout=7200,
            auto_resume=False,
            state_max_age_hours=24,
            parallel_limit=10,
            deep_analysis_parallel_limit=3,
            cleanup_state_on_success=False,
            state_cleanup_max_age_days=7,
        )

        with pytest.raises(ValueError, match="max_retries must be non-negative"):
            config.validate()

    def test_should_allow_zero_max_retries(self):
        """Test validation passes for zero max_retries."""
        config = ResilienceConfig(
            max_retries=0,
            retry_base_delay=2.0,
            retry_max_delay=60.0,
            holding_timeout=300,
            flow_timeout=7200,
            auto_resume=False,
            state_max_age_hours=24,
            parallel_limit=10,
            deep_analysis_parallel_limit=3,
            cleanup_state_on_success=False,
            state_cleanup_max_age_days=7,
        )

        # Should not raise
        config.validate()

    def test_should_raise_for_zero_retry_base_delay(self):
        """Test validation fails for zero retry_base_delay."""
        config = ResilienceConfig(
            max_retries=3,
            retry_base_delay=0.0,
            retry_max_delay=60.0,
            holding_timeout=300,
            flow_timeout=7200,
            auto_resume=False,
            state_max_age_hours=24,
            parallel_limit=10,
            deep_analysis_parallel_limit=3,
            cleanup_state_on_success=False,
            state_cleanup_max_age_days=7,
        )

        with pytest.raises(ValueError, match="retry_base_delay must be positive"):
            config.validate()

    def test_should_raise_for_negative_retry_base_delay(self):
        """Test validation fails for negative retry_base_delay."""
        config = ResilienceConfig(
            max_retries=3,
            retry_base_delay=-1.0,
            retry_max_delay=60.0,
            holding_timeout=300,
            flow_timeout=7200,
            auto_resume=False,
            state_max_age_hours=24,
            parallel_limit=10,
            deep_analysis_parallel_limit=3,
            cleanup_state_on_success=False,
            state_cleanup_max_age_days=7,
        )

        with pytest.raises(ValueError, match="retry_base_delay must be positive"):
            config.validate()

    def test_should_raise_for_retry_max_delay_lte_base_delay(self):
        """Test validation fails when retry_max_delay <= retry_base_delay."""
        config = ResilienceConfig(
            max_retries=3,
            retry_base_delay=60.0,
            retry_max_delay=60.0,  # Equal to base
            holding_timeout=300,
            flow_timeout=7200,
            auto_resume=False,
            state_max_age_hours=24,
            parallel_limit=10,
            deep_analysis_parallel_limit=3,
            cleanup_state_on_success=False,
            state_cleanup_max_age_days=7,
        )

        with pytest.raises(ValueError, match="retry_max_delay.*must be greater than retry_base_delay"):
            config.validate()

    def test_should_raise_for_zero_state_max_age_hours(self):
        """Test validation fails for zero state_max_age_hours."""
        config = ResilienceConfig(
            max_retries=3,
            retry_base_delay=2.0,
            retry_max_delay=60.0,
            holding_timeout=300,
            flow_timeout=7200,
            auto_resume=False,
            state_max_age_hours=0,
            parallel_limit=10,
            deep_analysis_parallel_limit=3,
            cleanup_state_on_success=False,
            state_cleanup_max_age_days=7,
        )

        with pytest.raises(ValueError, match="state_max_age_hours must be at least 1"):
            config.validate()

    def test_should_raise_for_zero_parallel_limit(self):
        """Test validation fails for zero parallel_limit."""
        config = ResilienceConfig(
            max_retries=3,
            retry_base_delay=2.0,
            retry_max_delay=60.0,
            holding_timeout=300,
            flow_timeout=7200,
            auto_resume=False,
            state_max_age_hours=24,
            parallel_limit=0,
            deep_analysis_parallel_limit=3,
            cleanup_state_on_success=False,
            state_cleanup_max_age_days=7,
        )

        with pytest.raises(ValueError, match="parallel_limit must be at least 1"):
            config.validate()

    def test_should_raise_for_zero_deep_analysis_parallel_limit(self):
        """Test validation fails for zero deep_analysis_parallel_limit."""
        config = ResilienceConfig(
            max_retries=3,
            retry_base_delay=2.0,
            retry_max_delay=60.0,
            holding_timeout=300,
            flow_timeout=7200,
            auto_resume=False,
            state_max_age_hours=24,
            parallel_limit=10,
            deep_analysis_parallel_limit=0,
            cleanup_state_on_success=False,
            state_cleanup_max_age_days=7,
        )

        with pytest.raises(ValueError, match="deep_analysis_parallel_limit must be at least 1"):
            config.validate()

    def test_should_raise_for_zero_state_cleanup_max_age_days(self):
        """Test validation fails for zero state_cleanup_max_age_days."""
        config = ResilienceConfig(
            max_retries=3,
            retry_base_delay=2.0,
            retry_max_delay=60.0,
            holding_timeout=300,
            flow_timeout=7200,
            auto_resume=False,
            state_max_age_hours=24,
            parallel_limit=10,
            deep_analysis_parallel_limit=3,
            cleanup_state_on_success=False,
            state_cleanup_max_age_days=0,
        )

        with pytest.raises(ValueError, match="state_cleanup_max_age_days must be at least 1"):
            config.validate()


class TestGetResilienceConfig:
    """Tests for get_resilience_config function."""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset singleton before each test."""
        reset_resilience_config()
        yield
        reset_resilience_config()

    def test_should_return_config_with_defaults(self, mocker):
        """Test returns config with default values."""
        mocker.patch.dict("os.environ", {}, clear=True)

        config = get_resilience_config()

        assert config.max_retries == 3
        assert config.retry_base_delay == 2.0
        assert config.retry_max_delay == 60.0
        assert config.holding_timeout == 600
        assert config.flow_timeout == 7200
        assert config.auto_resume is False
        assert config.state_max_age_hours == 24
        assert config.parallel_limit == 10
        assert config.deep_analysis_parallel_limit == 3
        assert config.cleanup_state_on_success is False
        assert config.state_cleanup_max_age_days == 7

    def test_should_load_max_retries_from_env(self, mocker):
        """Test loads max_retries from environment."""
        mocker.patch.dict("os.environ", {"FINWIZ_MAX_RETRIES": "5"})

        config = get_resilience_config()

        assert config.max_retries == 5

    def test_should_load_retry_base_delay_from_env(self, mocker):
        """Test loads retry_base_delay from environment."""
        mocker.patch.dict("os.environ", {"FINWIZ_RETRY_BASE_DELAY": "5.0"})

        config = get_resilience_config()

        assert config.retry_base_delay == 5.0

    def test_should_load_retry_max_delay_from_env(self, mocker):
        """Test loads retry_max_delay from environment."""
        mocker.patch.dict("os.environ", {"FINWIZ_RETRY_MAX_DELAY": "120.0"})

        config = get_resilience_config()

        assert config.retry_max_delay == 120.0

    def test_should_load_holding_timeout_from_env(self, mocker):
        """Test loads holding_timeout from environment."""
        mocker.patch.dict("os.environ", {"FINWIZ_HOLDING_TIMEOUT": "600"})

        config = get_resilience_config()

        assert config.holding_timeout == 600

    def test_should_load_flow_timeout_from_env(self, mocker):
        """Test loads flow_timeout from environment."""
        mocker.patch.dict("os.environ", {"FINWIZ_FLOW_TIMEOUT": "14400"})

        config = get_resilience_config()

        assert config.flow_timeout == 14400

    def test_should_load_auto_resume_true_from_env(self, mocker):
        """Test loads auto_resume=true from environment."""
        mocker.patch.dict("os.environ", {"FINWIZ_AUTO_RESUME": "true"})

        config = get_resilience_config()

        assert config.auto_resume is True

    def test_should_load_auto_resume_false_from_env(self, mocker):
        """Test loads auto_resume=false from environment."""
        mocker.patch.dict("os.environ", {"FINWIZ_AUTO_RESUME": "false"})

        config = get_resilience_config()

        assert config.auto_resume is False

    def test_should_load_state_max_age_hours_from_env(self, mocker):
        """Test loads state_max_age_hours from environment."""
        mocker.patch.dict("os.environ", {"FINWIZ_STATE_MAX_AGE_HOURS": "48"})

        config = get_resilience_config()

        assert config.state_max_age_hours == 48

    def test_should_load_parallel_limit_from_env(self, mocker):
        """Test loads parallel_limit from environment."""
        mocker.patch.dict("os.environ", {"FINWIZ_PARALLEL_LIMIT": "20"})

        config = get_resilience_config()

        assert config.parallel_limit == 20

    def test_should_fallback_to_old_parallel_limit_env(self, mocker):
        """Test falls back to PORTFOLIO_PARALLEL_LIMIT."""
        # Clear all env vars and set only the old-style one
        mocker.patch.dict(
            "os.environ",
            {"PORTFOLIO_PARALLEL_LIMIT": "15"},
            clear=True,
        )

        config = get_resilience_config()

        assert config.parallel_limit == 15

    def test_should_load_deep_analysis_parallel_limit_from_env(self, mocker):
        """Test loads deep_analysis_parallel_limit from environment."""
        mocker.patch.dict("os.environ", {"FINWIZ_DEEP_ANALYSIS_PARALLEL_LIMIT": "5"})

        config = get_resilience_config()

        assert config.deep_analysis_parallel_limit == 5

    def test_should_fallback_to_old_deep_analysis_limit_env(self, mocker):
        """Test falls back to DEEP_ANALYSIS_PARALLEL_LIMIT."""
        # Clear all env vars and set only the old-style one
        mocker.patch.dict(
            "os.environ",
            {"DEEP_ANALYSIS_PARALLEL_LIMIT": "4"},
            clear=True,
        )

        config = get_resilience_config()

        assert config.deep_analysis_parallel_limit == 4

    def test_should_load_cleanup_state_on_success_from_env(self, mocker):
        """Test loads cleanup_state_on_success from environment."""
        mocker.patch.dict("os.environ", {"FINWIZ_CLEANUP_STATE_ON_SUCCESS": "true"})

        config = get_resilience_config()

        assert config.cleanup_state_on_success is True

    def test_should_load_state_cleanup_max_age_days_from_env(self, mocker):
        """Test loads state_cleanup_max_age_days from environment."""
        mocker.patch.dict("os.environ", {"FINWIZ_STATE_CLEANUP_MAX_AGE_DAYS": "14"})

        config = get_resilience_config()

        assert config.state_cleanup_max_age_days == 14

    def test_should_return_singleton(self, mocker):
        """Test returns same instance on repeated calls."""
        mocker.patch.dict("os.environ", {}, clear=True)

        config1 = get_resilience_config()
        config2 = get_resilience_config()

        assert config1 is config2

    def test_should_validate_on_creation(self, mocker):
        """Test validates config on creation."""
        mocker.patch.dict(
            "os.environ",
            {
                "FINWIZ_HOLDING_TIMEOUT": "10000",
                "FINWIZ_FLOW_TIMEOUT": "5000",  # Less than holding_timeout
            },
        )

        with pytest.raises(ValueError, match="holding_timeout.*must be less than flow_timeout"):
            get_resilience_config()


class TestResetResilienceConfig:
    """Tests for reset_resilience_config function."""

    def test_should_reset_singleton(self, mocker):
        """Test resets singleton instance."""
        mocker.patch.dict("os.environ", {"FINWIZ_MAX_RETRIES": "5"})

        config1 = get_resilience_config()
        assert config1.max_retries == 5

        # Change env var
        mocker.patch.dict("os.environ", {"FINWIZ_MAX_RETRIES": "10"})

        # Reset singleton
        reset_resilience_config()

        config2 = get_resilience_config()

        # Should have new value
        assert config2.max_retries == 10
