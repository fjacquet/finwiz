"""
Unit tests for feature flag definitions.

Tests for environment variable helpers and default flag creation.
"""

from finwiz.config.features.definitions import (
    CircuitBreakerState,
    FallbackStrategy,
    FeatureFlagConfig,
    FeatureFlagStrategy,
    create_default_flags,
    get_env_bool,
    get_env_float,
    get_env_int,
)


class TestGetEnvBool:
    """Tests for get_env_bool function."""

    def test_should_return_true_for_true_string(self, mocker):
        """Test returns True for 'true' value."""
        mocker.patch.dict("os.environ", {"TEST_KEY": "true"})

        result = get_env_bool("TEST_KEY")

        assert result is True

    def test_should_return_true_for_1_string(self, mocker):
        """Test returns True for '1' value."""
        mocker.patch.dict("os.environ", {"TEST_KEY": "1"})

        result = get_env_bool("TEST_KEY")

        assert result is True

    def test_should_return_true_for_yes_string(self, mocker):
        """Test returns True for 'yes' value."""
        mocker.patch.dict("os.environ", {"TEST_KEY": "yes"})

        result = get_env_bool("TEST_KEY")

        assert result is True

    def test_should_return_true_for_on_string(self, mocker):
        """Test returns True for 'on' value."""
        mocker.patch.dict("os.environ", {"TEST_KEY": "on"})

        result = get_env_bool("TEST_KEY")

        assert result is True

    def test_should_return_true_for_enabled_string(self, mocker):
        """Test returns True for 'enabled' value."""
        mocker.patch.dict("os.environ", {"TEST_KEY": "enabled"})

        result = get_env_bool("TEST_KEY")

        assert result is True

    def test_should_return_false_for_false_string(self, mocker):
        """Test returns False for 'false' value."""
        mocker.patch.dict("os.environ", {"TEST_KEY": "false"})

        result = get_env_bool("TEST_KEY")

        assert result is False

    def test_should_return_default_when_not_set(self, mocker):
        """Test returns default when env var not set."""
        mocker.patch.dict("os.environ", {}, clear=True)

        result = get_env_bool("NONEXISTENT_KEY", default=True)

        assert result is True

    def test_should_be_case_insensitive(self, mocker):
        """Test handles uppercase values."""
        mocker.patch.dict("os.environ", {"TEST_KEY": "TRUE"})

        result = get_env_bool("TEST_KEY")

        assert result is True


class TestGetEnvFloat:
    """Tests for get_env_float function."""

    def test_should_return_float_value(self, mocker):
        """Test returns float from env var."""
        mocker.patch.dict("os.environ", {"TEST_KEY": "3.14"})

        result = get_env_float("TEST_KEY")

        assert result == 3.14

    def test_should_return_default_for_invalid(self, mocker):
        """Test returns default for invalid float."""
        mocker.patch.dict("os.environ", {"TEST_KEY": "not_a_float"})

        result = get_env_float("TEST_KEY", default=1.5)

        assert result == 1.5

    def test_should_return_default_when_not_set(self, mocker):
        """Test returns default when not set."""
        mocker.patch.dict("os.environ", {}, clear=True)

        result = get_env_float("NONEXISTENT_KEY", default=2.5)

        assert result == 2.5

    def test_should_handle_integer_string(self, mocker):
        """Test handles integer string as float."""
        mocker.patch.dict("os.environ", {"TEST_KEY": "42"})

        result = get_env_float("TEST_KEY")

        assert result == 42.0


class TestGetEnvInt:
    """Tests for get_env_int function."""

    def test_should_return_int_value(self, mocker):
        """Test returns int from env var."""
        mocker.patch.dict("os.environ", {"TEST_KEY": "42"})

        result = get_env_int("TEST_KEY")

        assert result == 42

    def test_should_return_default_for_invalid(self, mocker):
        """Test returns default for invalid int."""
        mocker.patch.dict("os.environ", {"TEST_KEY": "not_an_int"})

        result = get_env_int("TEST_KEY", default=10)

        assert result == 10

    def test_should_return_default_when_not_set(self, mocker):
        """Test returns default when not set."""
        mocker.patch.dict("os.environ", {}, clear=True)

        result = get_env_int("NONEXISTENT_KEY", default=5)

        assert result == 5

    def test_should_return_default_for_float_string(self, mocker):
        """Test returns default for float string."""
        mocker.patch.dict("os.environ", {"TEST_KEY": "3.14"})

        result = get_env_int("TEST_KEY", default=3)

        assert result == 3


class TestCreateDefaultFlags:
    """Tests for create_default_flags function."""

    def test_should_create_default_flags(self, mocker):
        """Test creates all default flags."""
        # Mock env to use defaults
        mocker.patch.dict("os.environ", {}, clear=True)

        flags = create_default_flags()

        assert "perplexity_research" in flags

    def test_should_configure_flags_from_environment(self, mocker):
        """Test configures flags from environment variables."""
        mocker.patch.dict(
            "os.environ",
            {
                "FF_STRICT_VALIDATION": "false",
                "FF_STRICT_VALIDATION_ROLLOUT": "50.0",
            },
        )

        flags = create_default_flags()

        strict_flag = flags["strict_validation"]
        assert strict_flag.enabled is False
        assert strict_flag.rollout_percentage == 50.0

    def test_should_set_correct_strategies(self, mocker):
        """Test flags have correct strategies."""
        mocker.patch.dict("os.environ", {}, clear=True)

        flags = create_default_flags()

        # Check some flags have expected strategies
        assert flags["strict_validation"].strategy == FeatureFlagStrategy.PERCENTAGE
        assert flags["perplexity_research"].strategy == FeatureFlagStrategy.CIRCUIT_BREAKER

    def test_should_set_fallback_strategies(self, mocker):
        """Test flags have fallback strategies."""
        mocker.patch.dict("os.environ", {}, clear=True)

        flags = create_default_flags()

        for flag_config in flags.values():
            assert flag_config.fallback_strategy is not None


class TestCircuitBreakerStateDataclass:
    """Additional tests for CircuitBreakerState dataclass."""

    def test_should_have_last_success_time_field(self):
        """Test CircuitBreakerState has last_success_time field."""
        state = CircuitBreakerState()

        assert hasattr(state, "last_success_time")
        assert state.last_success_time == 0.0


class TestFeatureFlagConfigDataclass:
    """Additional tests for FeatureFlagConfig dataclass."""

    def test_should_have_all_optional_fields(self):
        """Test FeatureFlagConfig has all expected fields."""
        config = FeatureFlagConfig(name="test")

        assert hasattr(config, "enabled")
        assert hasattr(config, "strategy")
        assert hasattr(config, "rollout_percentage")
        assert hasattr(config, "fallback_strategy")
        assert hasattr(config, "circuit_breaker_threshold")
        assert hasattr(config, "circuit_breaker_timeout")
        assert hasattr(config, "description")

    def test_should_have_correct_defaults(self):
        """Test FeatureFlagConfig has correct default values."""
        config = FeatureFlagConfig(name="test")

        assert config.enabled is False
        assert config.strategy == FeatureFlagStrategy.BOOLEAN
        assert config.rollout_percentage == 0.0
        assert config.fallback_strategy == FallbackStrategy.DISABLE
        assert config.circuit_breaker_threshold == 5
        assert config.circuit_breaker_timeout == 300
        assert config.description == ""
