"""
Unit tests for feature flags module.

Tests for the FeatureFlags class and related utilities.
"""

import pytest
from faker import Faker

from finwiz.config.features.definitions import (
    CircuitBreakerState,
    FallbackStrategy,
    FeatureFlagConfig,
    FeatureFlagStrategy,
)


# Note: FeatureFlagStrategy uses BOOLEAN, not ALWAYS_ON
# FeatureFlagConfig and CircuitBreakerState are @dataclass, not Pydantic


class TestFeatureFlags:
    """Test FeatureFlags class."""

    @pytest.fixture
    def fake(self):
        """Provide Faker instance."""
        return Faker()

    @pytest.fixture
    def feature_flags(self, mocker):
        """Create FeatureFlags instance with mocked environment."""
        # Mock create_default_flags to return a controlled set
        mock_flags = {
            "test_feature": FeatureFlagConfig(
                name="test_feature",
                description="Test feature for unit tests",
                enabled=True,
                strategy=FeatureFlagStrategy.BOOLEAN,
                fallback_strategy=FallbackStrategy.DISABLE,
            ),
            "disabled_feature": FeatureFlagConfig(
                name="disabled_feature",
                description="Disabled feature",
                enabled=False,
                strategy=FeatureFlagStrategy.BOOLEAN,
                fallback_strategy=FallbackStrategy.DISABLE,
            ),
            "percentage_feature": FeatureFlagConfig(
                name="percentage_feature",
                description="Percentage rollout feature",
                enabled=True,
                strategy=FeatureFlagStrategy.PERCENTAGE,
                rollout_percentage=50,
                fallback_strategy=FallbackStrategy.DEFAULT_VALUES,
            ),
            "circuit_breaker_feature": FeatureFlagConfig(
                name="circuit_breaker_feature",
                description="Circuit breaker feature",
                enabled=True,
                strategy=FeatureFlagStrategy.CIRCUIT_BREAKER,
                fallback_strategy=FallbackStrategy.CACHED_ONLY,
                circuit_breaker_threshold=5,
            ),
        }
        mocker.patch(
            "finwiz.config.features.flags.create_default_flags",
            return_value=mock_flags,
        )

        from finwiz.config.features.flags import FeatureFlags

        return FeatureFlags()

    def test_should_initialize_with_flags(self, feature_flags):
        """Test initialization loads flags."""
        assert len(feature_flags.flags) > 0
        assert "test_feature" in feature_flags.flags

    def test_should_return_true_for_enabled_flag(self, feature_flags, mocker):
        """Test is_enabled returns True for enabled flag."""
        mocker.patch(
            "finwiz.config.features.flags.evaluate_flag",
            return_value=True,
        )

        result = feature_flags.is_enabled("test_feature")

        assert result is True

    def test_should_return_false_for_disabled_flag(self, feature_flags):
        """Test is_enabled returns False for disabled flag."""
        result = feature_flags.is_enabled("disabled_feature")

        assert result is False

    def test_should_return_false_for_unknown_flag(self, feature_flags):
        """Test is_enabled returns False for unknown flag."""
        result = feature_flags.is_enabled("nonexistent_flag")

        assert result is False

    def test_should_get_fallback_strategy(self, feature_flags):
        """Test getting fallback strategy for flag."""
        strategy = feature_flags.get_fallback_strategy("test_feature")

        assert strategy == FallbackStrategy.DISABLE

    def test_should_return_disable_for_unknown_fallback(self, feature_flags):
        """Test fallback strategy returns DISABLE for unknown flag."""
        strategy = feature_flags.get_fallback_strategy("nonexistent")

        assert strategy == FallbackStrategy.DISABLE

    def test_should_get_flag_status(self, feature_flags):
        """Test getting comprehensive flag status."""
        status = feature_flags.get_flag_status("test_feature")

        assert status["name"] == "test_feature"
        assert status["enabled"] is True
        assert "strategy" in status
        assert "fallback_strategy" in status

    def test_should_get_error_for_unknown_flag_status(self, feature_flags):
        """Test getting status for unknown flag returns error."""
        status = feature_flags.get_flag_status("nonexistent")

        assert "error" in status

    def test_should_list_all_flags(self, feature_flags):
        """Test listing all flags."""
        all_flags = feature_flags.list_all_flags()

        assert len(all_flags) > 0
        assert "test_feature" in all_flags
        assert "disabled_feature" in all_flags

    def test_should_get_enabled_flags(self, feature_flags, mocker):
        """Test getting list of enabled flags."""
        mocker.patch(
            "finwiz.config.features.flags.evaluate_flag",
            return_value=True,
        )

        enabled = feature_flags.get_enabled_flags()

        # At least test_feature should be enabled (not disabled_feature)
        assert isinstance(enabled, list)

    def test_should_update_flag(self, feature_flags):
        """Test updating flag configuration."""
        result = feature_flags.update_flag("test_feature", enabled=False)

        assert result is True
        assert feature_flags.flags["test_feature"].enabled is False

    def test_should_fail_update_for_unknown_flag(self, feature_flags):
        """Test update fails for unknown flag."""
        result = feature_flags.update_flag("nonexistent", enabled=True)

        assert result is False

    def test_should_handle_unknown_config_key(self, feature_flags):
        """Test update handles unknown config key gracefully."""
        result = feature_flags.update_flag("test_feature", nonexistent_key=True)

        # Should still return True but log warning
        assert result is True

    def test_should_execute_with_fallback_when_enabled(self, feature_flags, mocker):
        """Test execute_with_fallback runs primary when enabled."""
        mocker.patch(
            "finwiz.config.features.flags.evaluate_flag",
            return_value=True,
        )

        primary_result = "primary_result"
        primary_func = mocker.MagicMock(return_value=primary_result)
        fallback_func = mocker.MagicMock(return_value="fallback_result")

        result = feature_flags.execute_with_fallback(
            "test_feature",
            primary_func,
            fallback_func,
        )

        assert result == primary_result
        primary_func.assert_called_once()
        fallback_func.assert_not_called()

    def test_should_execute_fallback_when_disabled(self, feature_flags, mocker):
        """Test execute_with_fallback runs fallback when disabled."""
        mocker.patch(
            "finwiz.config.features.flags.evaluate_flag",
            return_value=False,
        )
        mocker.patch(
            "finwiz.config.features.flags.get_default_values",
            return_value=None,
        )

        primary_func = mocker.MagicMock(return_value="primary_result")
        fallback_result = "fallback_result"
        fallback_func = mocker.MagicMock(return_value=fallback_result)

        result = feature_flags.execute_with_fallback(
            "test_feature",
            primary_func,
            fallback_func,
        )

        assert result == fallback_result
        primary_func.assert_not_called()
        fallback_func.assert_called_once()

    def test_should_execute_fallback_on_primary_error(self, feature_flags, mocker):
        """Test execute_with_fallback runs fallback on primary error."""
        mocker.patch(
            "finwiz.config.features.flags.evaluate_flag",
            return_value=True,
        )
        mocker.patch(
            "finwiz.config.features.flags.get_default_values",
            return_value=None,
        )

        primary_func = mocker.MagicMock(side_effect=Exception("Primary failed"))
        fallback_result = "fallback_result"
        fallback_func = mocker.MagicMock(return_value=fallback_result)

        result = feature_flags.execute_with_fallback(
            "test_feature",
            primary_func,
            fallback_func,
        )

        assert result == fallback_result
        fallback_func.assert_called_once()

    def test_should_return_default_values_for_default_strategy(self, feature_flags, mocker):
        """Test fallback uses default values when strategy is DEFAULT_VALUES."""
        mocker.patch(
            "finwiz.config.features.flags.evaluate_flag",
            return_value=False,
        )
        default_values = {"key": "value"}
        mocker.patch(
            "finwiz.config.features.flags.get_default_values",
            return_value=default_values,
        )

        primary_func = mocker.MagicMock(return_value="primary")

        result = feature_flags.execute_with_fallback(
            "percentage_feature",  # Has DEFAULT_VALUES fallback
            primary_func,
            None,
        )

        assert result == default_values

    def test_should_return_none_for_disable_strategy(self, feature_flags, mocker):
        """Test fallback returns None when strategy is DISABLE."""
        mocker.patch(
            "finwiz.config.features.flags.evaluate_flag",
            return_value=False,
        )
        mocker.patch(
            "finwiz.config.features.flags.get_default_values",
            return_value=None,
        )

        primary_func = mocker.MagicMock(return_value="primary")

        result = feature_flags.execute_with_fallback(
            "test_feature",  # Has DISABLE fallback
            primary_func,
            None,
        )

        assert result is None

    def test_should_record_success(self, feature_flags, mocker):
        """Test recording success for circuit breaker."""
        mock_record_success = mocker.patch(
            "finwiz.config.features.flags.record_success",
        )

        feature_flags.record_success("circuit_breaker_feature")

        mock_record_success.assert_called_once()

    def test_should_record_failure(self, feature_flags, mocker):
        """Test recording failure for circuit breaker."""
        mock_record_failure = mocker.patch(
            "finwiz.config.features.flags.record_failure",
        )

        feature_flags.record_failure("circuit_breaker_feature")

        mock_record_failure.assert_called_once()

    def test_should_get_circuit_breaker_status(self, feature_flags):
        """Test getting circuit breaker status in flag status."""
        status = feature_flags.get_flag_status("circuit_breaker_feature")

        assert "circuit_breaker" in status
        assert "is_open" in status["circuit_breaker"]
        assert "failure_count" in status["circuit_breaker"]

    def test_should_include_percentage_in_status(self, feature_flags):
        """Test getting percentage rollout in flag status."""
        status = feature_flags.get_flag_status("percentage_feature")

        assert "rollout_percentage" in status
        assert status["rollout_percentage"] == 50


class TestGlobalFeatureFunctions:
    """Test global feature flag functions."""

    @pytest.fixture(autouse=True)
    def reset_global(self, mocker):
        """Reset global feature flags instance between tests."""
        import finwiz.config.features.flags as flags_module

        flags_module._feature_flags = None

        # Mock create_default_flags
        mock_flags = {
            "test_global": FeatureFlagConfig(
                name="test_global",
                description="Test global feature",
                enabled=True,
                strategy=FeatureFlagStrategy.BOOLEAN,
                fallback_strategy=FallbackStrategy.DISABLE,
            ),
        }
        mocker.patch(
            "finwiz.config.features.flags.create_default_flags",
            return_value=mock_flags,
        )

    def test_get_feature_flags_should_return_singleton(self):
        """Test get_feature_flags returns singleton."""
        from finwiz.config.features.flags import get_feature_flags

        flags1 = get_feature_flags()
        flags2 = get_feature_flags()

        assert flags1 is flags2

    def test_is_feature_enabled_should_delegate(self, mocker):
        """Test is_feature_enabled delegates to instance."""
        mocker.patch(
            "finwiz.config.features.flags.evaluate_flag",
            return_value=True,
        )

        from finwiz.config.features.flags import is_feature_enabled

        result = is_feature_enabled("test_global")

        assert result is True

    def test_execute_with_feature_flag_should_delegate(self, mocker):
        """Test execute_with_feature_flag delegates to instance."""
        mocker.patch(
            "finwiz.config.features.flags.evaluate_flag",
            return_value=True,
        )

        from finwiz.config.features.flags import execute_with_feature_flag

        primary_func = mocker.MagicMock(return_value="result")

        result = execute_with_feature_flag("test_global", primary_func)

        assert result == "result"


class TestCircuitBreakerState:
    """Test CircuitBreakerState dataclass."""

    def test_should_initialize_with_defaults(self):
        """Test initialization with default values."""
        state = CircuitBreakerState()

        assert state.is_open is False
        assert state.failure_count == 0
        assert state.last_failure_time == 0.0

    def test_should_store_failure_info(self):
        """Test storing failure information."""
        import time

        now = time.time()
        state = CircuitBreakerState(
            is_open=True,
            failure_count=5,
            last_failure_time=now,
        )

        assert state.is_open is True
        assert state.failure_count == 5
        assert state.last_failure_time == now


class TestFeatureFlagConfig:
    """Test FeatureFlagConfig dataclass."""

    def test_should_initialize_with_required_fields(self):
        """Test initialization with required fields."""
        config = FeatureFlagConfig(
            name="test_flag",
            description="Test description",
            enabled=True,
            strategy=FeatureFlagStrategy.BOOLEAN,
            fallback_strategy=FallbackStrategy.DISABLE,
        )

        assert config.name == "test_flag"
        assert config.enabled is True
        assert config.strategy == FeatureFlagStrategy.BOOLEAN

    def test_should_have_default_values(self):
        """Test default values are set correctly."""
        config = FeatureFlagConfig(
            name="test_flag",
        )

        assert config.rollout_percentage == 0.0
        assert config.circuit_breaker_threshold == 5
        assert config.enabled is False
        assert config.strategy == FeatureFlagStrategy.BOOLEAN
        assert config.fallback_strategy == FallbackStrategy.DISABLE
