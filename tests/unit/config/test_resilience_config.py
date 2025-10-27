"""Unit tests for ResilienceConfig."""

import pytest

from finwiz.config.resilience_config import (
    ResilienceConfig,
    get_resilience_config,
    reset_resilience_config,
)


class TestResilienceConfig:
    """Test suite for ResilienceConfig."""

    def setup_method(self):
        """Reset singleton before each test."""
        reset_resilience_config()

    def teardown_method(self):
        """Reset singleton after each test."""
        reset_resilience_config()

    def test_should_create_config_with_valid_values(self):
        """Test creating config with valid values."""
        # Act
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
            state_cleanup_max_age_days=7,
        )

        # Assert
        assert config.max_retries == 3
        assert config.retry_base_delay == 2.0
        assert config.retry_max_delay == 60.0
        assert config.holding_timeout == 300
        assert config.flow_timeout == 7200
        assert config.auto_resume is False
        assert config.state_max_age_hours == 24
        assert config.parallel_limit == 10
        assert config.deep_analysis_parallel_limit == 3

    def test_should_validate_successfully_with_valid_config(self):
        """Test validation passes with valid configuration."""
        # Arrange
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
            state_cleanup_max_age_days=7,
        )

        # Act & Assert - should not raise
        config.validate()

    def test_should_reject_holding_timeout_greater_than_flow_timeout(self):
        """Test validation fails when holding_timeout >= flow_timeout."""
        # Arrange
        config = ResilienceConfig(
            max_retries=3,
            retry_base_delay=2.0,
            retry_max_delay=60.0,
            holding_timeout=7200,
            flow_timeout=7200,  # Equal to holding_timeout
            auto_resume=False,
            state_max_age_hours=24,
            parallel_limit=10,
            deep_analysis_parallel_limit=3,
            cleanup_state_on_success=False,
            state_cleanup_max_age_days=7,
        )

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            config.validate()
        assert "holding_timeout" in str(exc_info.value)
        assert "must be less than flow_timeout" in str(exc_info.value)

    def test_should_reject_holding_timeout_exceeding_flow_timeout(self):
        """Test validation fails when holding_timeout > flow_timeout."""
        # Arrange
        config = ResilienceConfig(
            max_retries=3,
            retry_base_delay=2.0,
            retry_max_delay=60.0,
            holding_timeout=8000,
            flow_timeout=7200,
            auto_resume=False,
            state_max_age_hours=24,
            parallel_limit=10,
            deep_analysis_parallel_limit=3,
            cleanup_state_on_success=False,
            state_cleanup_max_age_days=7,
        )

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            config.validate()
        assert "holding_timeout" in str(exc_info.value)
        assert "must be less than flow_timeout" in str(exc_info.value)

    def test_should_reject_negative_max_retries(self):
        """Test validation fails when max_retries is negative."""
        # Arrange
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

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            config.validate()
        assert "max_retries must be non-negative" in str(exc_info.value)

    def test_should_accept_zero_max_retries(self):
        """Test validation passes when max_retries is zero."""
        # Arrange
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

        # Act & Assert - should not raise
        config.validate()

    def test_should_reject_non_positive_retry_base_delay(self):
        """Test validation fails when retry_base_delay is not positive."""
        # Arrange
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

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            config.validate()
        assert "retry_base_delay must be positive" in str(exc_info.value)

    def test_should_reject_retry_max_delay_less_than_base_delay(self):
        """Test validation fails when retry_max_delay <= retry_base_delay."""
        # Arrange
        config = ResilienceConfig(
            max_retries=3,
            retry_base_delay=60.0,
            retry_max_delay=60.0,  # Equal to base delay
            holding_timeout=300,
            flow_timeout=7200,
            auto_resume=False,
            state_max_age_hours=24,
            parallel_limit=10,
            deep_analysis_parallel_limit=3,
            cleanup_state_on_success=False,
            state_cleanup_max_age_days=7,
        )

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            config.validate()
        assert "retry_max_delay" in str(exc_info.value)
        assert "must be greater than retry_base_delay" in str(exc_info.value)

    def test_should_reject_state_max_age_hours_less_than_one(self):
        """Test validation fails when state_max_age_hours < 1."""
        # Arrange
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

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            config.validate()
        assert "state_max_age_hours must be at least 1" in str(exc_info.value)

    def test_should_accept_state_max_age_hours_equal_to_one(self):
        """Test validation passes when state_max_age_hours is 1."""
        # Arrange
        config = ResilienceConfig(
            max_retries=3,
            retry_base_delay=2.0,
            retry_max_delay=60.0,
            holding_timeout=300,
            flow_timeout=7200,
            auto_resume=False,
            state_max_age_hours=1,
            parallel_limit=10,
            deep_analysis_parallel_limit=3,
            cleanup_state_on_success=False,
            state_cleanup_max_age_days=7,
        )

        # Act & Assert - should not raise
        config.validate()

    def test_should_reject_parallel_limit_less_than_one(self):
        """Test validation fails when parallel_limit < 1."""
        # Arrange
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

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            config.validate()
        assert "parallel_limit must be at least 1" in str(exc_info.value)

    def test_should_reject_deep_analysis_parallel_limit_less_than_one(self):
        """Test validation fails when deep_analysis_parallel_limit < 1."""
        # Arrange
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

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            config.validate()
        assert "deep_analysis_parallel_limit must be at least 1" in str(exc_info.value)

    def test_should_load_from_env_with_all_variables_set(self, mocker):
        """Test loading configuration from environment variables."""
        # Arrange
        mocker.patch.dict(
            "os.environ",
            {
                "FINWIZ_MAX_RETRIES": "5",
                "FINWIZ_RETRY_BASE_DELAY": "3.0",
                "FINWIZ_RETRY_MAX_DELAY": "120.0",
                "FINWIZ_HOLDING_TIMEOUT": "600",
                "FINWIZ_FLOW_TIMEOUT": "10800",
                "FINWIZ_AUTO_RESUME": "true",
                "FINWIZ_STATE_MAX_AGE_HOURS": "48",
                "FINWIZ_PARALLEL_LIMIT": "20",
                "FINWIZ_DEEP_ANALYSIS_PARALLEL_LIMIT": "5",
            },
        )

        # Act
        config = get_resilience_config()

        # Assert
        assert config.max_retries == 5
        assert config.retry_base_delay == 3.0
        assert config.retry_max_delay == 120.0
        assert config.holding_timeout == 600
        assert config.flow_timeout == 10800
        assert config.auto_resume is True
        assert config.state_max_age_hours == 48
        assert config.parallel_limit == 20
        assert config.deep_analysis_parallel_limit == 5

    def test_should_use_defaults_when_env_variables_not_set(self, mocker):
        """Test that defaults are used when environment variables are not set."""
        # Arrange
        mocker.patch.dict("os.environ", {}, clear=True)

        # Act
        config = get_resilience_config()

        # Assert
        assert config.max_retries == 3
        assert config.retry_base_delay == 2.0
        assert config.retry_max_delay == 60.0
        assert config.holding_timeout == 300
        assert config.flow_timeout == 7200
        assert config.auto_resume is False
        assert config.state_max_age_hours == 24
        assert config.parallel_limit == 10
        assert config.deep_analysis_parallel_limit == 3

    def test_should_handle_partial_env_variables(self, mocker):
        """Test loading with only some environment variables set."""
        # Arrange
        mocker.patch.dict(
            "os.environ",
            {
                "FINWIZ_MAX_RETRIES": "5",
                "FINWIZ_FLOW_TIMEOUT": "10800",
            },
            clear=True,
        )

        # Act
        config = get_resilience_config()

        # Assert
        assert config.max_retries == 5
        assert config.retry_base_delay == 2.0  # default
        assert config.retry_max_delay == 60.0  # default
        assert config.holding_timeout == 300  # default
        assert config.flow_timeout == 10800
        assert config.auto_resume is False  # default
        assert config.state_max_age_hours == 24  # default
        assert config.parallel_limit == 10  # default
        assert config.deep_analysis_parallel_limit == 3  # default

    def test_should_parse_auto_resume_true_values(self, mocker):
        """Test parsing of various true values for auto_resume."""
        # Test different true values (implementation only checks for "true")
        for value in ["true", "True", "TRUE"]:
            reset_resilience_config()
            mocker.patch.dict("os.environ", {"FINWIZ_AUTO_RESUME": value}, clear=True)

            config = get_resilience_config()
            assert config.auto_resume is True, f"Failed for value: {value}"

    def test_should_parse_auto_resume_false_values(self, mocker):
        """Test parsing of various false values for auto_resume."""
        # Test different false values (anything not "true" is false)
        for value in ["false", "False", "FALSE", "no", "NO", "0", "", "yes", "1"]:
            reset_resilience_config()
            mocker.patch.dict("os.environ", {"FINWIZ_AUTO_RESUME": value}, clear=True)

            config = get_resilience_config()
            assert config.auto_resume is False, f"Failed for value: {value}"

    def test_should_fallback_to_old_parallel_limit_variable(self, mocker):
        """Test fallback to PORTFOLIO_PARALLEL_LIMIT when FINWIZ_PARALLEL_LIMIT not set."""
        # Arrange
        mocker.patch.dict(
            "os.environ",
            {
                "PORTFOLIO_PARALLEL_LIMIT": "15",
            },
            clear=True,
        )

        # Act
        config = get_resilience_config()

        # Assert
        assert config.parallel_limit == 15

    def test_should_fallback_to_old_deep_analysis_parallel_limit_variable(self, mocker):
        """Test fallback to DEEP_ANALYSIS_PARALLEL_LIMIT when FINWIZ_ version not set."""
        # Arrange
        mocker.patch.dict(
            "os.environ",
            {
                "DEEP_ANALYSIS_PARALLEL_LIMIT": "7",
            },
            clear=True,
        )

        # Act
        config = get_resilience_config()

        # Assert
        assert config.deep_analysis_parallel_limit == 7

    def test_should_prefer_new_variable_over_old_variable(self, mocker):
        """Test that new FINWIZ_ prefixed variables take precedence over old ones."""
        # Arrange
        mocker.patch.dict(
            "os.environ",
            {
                "FINWIZ_PARALLEL_LIMIT": "20",
                "PORTFOLIO_PARALLEL_LIMIT": "15",
                "FINWIZ_DEEP_ANALYSIS_PARALLEL_LIMIT": "8",
                "DEEP_ANALYSIS_PARALLEL_LIMIT": "5",
            },
            clear=True,
        )

        # Act
        config = get_resilience_config()

        # Assert
        assert config.parallel_limit == 20  # New variable wins
        assert config.deep_analysis_parallel_limit == 8  # New variable wins

    def test_should_use_default_when_both_variables_missing(self, mocker):
        """Test that defaults are used when both old and new variables are missing."""
        # Arrange
        mocker.patch.dict("os.environ", {}, clear=True)

        # Act
        config = get_resilience_config()

        # Assert
        assert config.parallel_limit == 10  # Default
        assert config.deep_analysis_parallel_limit == 3  # Default

    def test_should_implement_singleton_pattern(self, mocker):
        """Test that get_resilience_config returns the same instance."""
        # Arrange
        mocker.patch.dict(
            "os.environ",
            {
                "FINWIZ_MAX_RETRIES": "5",
            },
            clear=True,
        )

        # Act
        config1 = get_resilience_config()
        config2 = get_resilience_config()

        # Assert
        assert config1 is config2  # Same instance

    def test_should_cache_config_after_first_load(self, mocker):
        """Test that configuration is cached and not reloaded on subsequent calls."""
        # Arrange
        mocker.patch.dict(
            "os.environ",
            {
                "FINWIZ_MAX_RETRIES": "5",
            },
            clear=True,
        )

        # Act
        config1 = get_resilience_config()
        assert config1.max_retries == 5

        # Change environment variable
        mocker.patch.dict(
            "os.environ",
            {
                "FINWIZ_MAX_RETRIES": "10",
            },
        )

        config2 = get_resilience_config()

        # Assert - should still have old value (cached)
        assert config2.max_retries == 5
        assert config1 is config2

    def test_should_reload_config_after_reset(self, mocker):
        """Test that configuration is reloaded after reset_resilience_config."""
        # Arrange
        mocker.patch.dict(
            "os.environ",
            {
                "FINWIZ_MAX_RETRIES": "5",
            },
            clear=True,
        )

        # Act
        config1 = get_resilience_config()
        assert config1.max_retries == 5

        # Reset and change environment
        reset_resilience_config()
        mocker.patch.dict(
            "os.environ",
            {
                "FINWIZ_MAX_RETRIES": "10",
            },
        )

        config2 = get_resilience_config()

        # Assert - should have new value
        assert config2.max_retries == 10
        assert config1 is not config2

    def test_should_raise_validation_error_on_invalid_config(self, mocker):
        """Test that get_resilience_config raises ValueError on invalid configuration."""
        # Arrange - set invalid configuration
        mocker.patch.dict(
            "os.environ",
            {
                "FINWIZ_HOLDING_TIMEOUT": "7200",
                "FINWIZ_FLOW_TIMEOUT": "7200",  # Invalid: equal to holding_timeout
            },
            clear=True,
        )

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            get_resilience_config()
        assert "holding_timeout" in str(exc_info.value)
        assert "must be less than flow_timeout" in str(exc_info.value)

    def test_should_handle_float_values_for_delays(self, mocker):
        """Test that float values are properly parsed for delay settings."""
        # Arrange
        mocker.patch.dict(
            "os.environ",
            {
                "FINWIZ_RETRY_BASE_DELAY": "2.5",
                "FINWIZ_RETRY_MAX_DELAY": "90.75",
            },
            clear=True,
        )

        # Act
        config = get_resilience_config()

        # Assert
        assert config.retry_base_delay == 2.5
        assert config.retry_max_delay == 90.75

    def test_should_handle_integer_values_for_timeouts(self, mocker):
        """Test that integer values are properly parsed for timeout settings."""
        # Arrange
        mocker.patch.dict(
            "os.environ",
            {
                "FINWIZ_HOLDING_TIMEOUT": "450",
                "FINWIZ_FLOW_TIMEOUT": "9000",
            },
            clear=True,
        )

        # Act
        config = get_resilience_config()

        # Assert
        assert config.holding_timeout == 450
        assert config.flow_timeout == 9000
        assert isinstance(config.holding_timeout, int)
        assert isinstance(config.flow_timeout, int)
