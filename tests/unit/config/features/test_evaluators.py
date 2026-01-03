"""
Unit tests for feature flag evaluators.

Tests for the evaluate_flag, circuit breaker, and related functions.
"""

import time
import pytest
from faker import Faker

from finwiz.config.features.definitions import (
    CircuitBreakerState,
    FeatureFlagConfig,
    FeatureFlagStrategy,
    FallbackStrategy,
)
from finwiz.config.features.evaluators import (
    evaluate_flag,
    evaluate_circuit_breaker,
    record_success,
    record_failure,
    get_default_values,
)


class TestEvaluateFlag:
    """Tests for evaluate_flag function."""

    @pytest.fixture
    def fake(self):
        """Provide Faker instance."""
        return Faker()

    def test_should_return_enabled_for_boolean_strategy(self):
        """Test BOOLEAN strategy returns enabled value."""
        config = FeatureFlagConfig(
            name="test_flag",
            enabled=True,
            strategy=FeatureFlagStrategy.BOOLEAN,
        )

        result = evaluate_flag(config, None, None, {})

        assert result is True

    def test_should_return_disabled_for_boolean_strategy(self):
        """Test BOOLEAN strategy returns disabled value."""
        config = FeatureFlagConfig(
            name="test_flag",
            enabled=False,
            strategy=FeatureFlagStrategy.BOOLEAN,
        )

        result = evaluate_flag(config, None, None, {})

        assert result is False

    def test_should_evaluate_percentage_with_user_id(self, fake):
        """Test PERCENTAGE strategy uses deterministic hash for user."""
        config = FeatureFlagConfig(
            name="test_flag",
            enabled=True,
            strategy=FeatureFlagStrategy.PERCENTAGE,
            rollout_percentage=50.0,
        )
        user_id = fake.uuid4()

        # Run multiple times - should be deterministic
        result1 = evaluate_flag(config, user_id, None, {})
        result2 = evaluate_flag(config, user_id, None, {})

        assert result1 == result2

    def test_should_evaluate_percentage_without_user_id(self):
        """Test PERCENTAGE strategy uses random for no user."""
        config = FeatureFlagConfig(
            name="test_flag",
            enabled=True,
            strategy=FeatureFlagStrategy.PERCENTAGE,
            rollout_percentage=100.0,  # 100% should always pass
        )

        result = evaluate_flag(config, None, None, {})

        assert result is True

    def test_should_evaluate_percentage_at_zero(self):
        """Test PERCENTAGE strategy at 0% rollout."""
        config = FeatureFlagConfig(
            name="test_flag",
            enabled=True,
            strategy=FeatureFlagStrategy.PERCENTAGE,
            rollout_percentage=0.0,
        )

        result = evaluate_flag(config, None, None, {})

        assert result is False

    def test_should_evaluate_user_list_with_allowed_user(self, fake):
        """Test USER_LIST strategy with allowed user."""
        user_id = fake.uuid4()
        config = FeatureFlagConfig(
            name="test_flag",
            enabled=True,
            strategy=FeatureFlagStrategy.USER_LIST,
            allowed_users={user_id},
        )

        result = evaluate_flag(config, user_id, None, {})

        assert result is True

    def test_should_evaluate_user_list_with_disallowed_user(self, fake):
        """Test USER_LIST strategy with disallowed user."""
        config = FeatureFlagConfig(
            name="test_flag",
            enabled=True,
            strategy=FeatureFlagStrategy.USER_LIST,
            allowed_users={"allowed_user"},
        )

        result = evaluate_flag(config, "other_user", None, {})

        assert result is False

    def test_should_evaluate_user_list_with_no_user(self):
        """Test USER_LIST strategy with no user ID."""
        config = FeatureFlagConfig(
            name="test_flag",
            enabled=True,
            strategy=FeatureFlagStrategy.USER_LIST,
            allowed_users={"allowed_user"},
        )

        result = evaluate_flag(config, None, None, {})

        assert result is False

    def test_should_evaluate_time_window_within_window(self):
        """Test TIME_WINDOW strategy within active window."""
        now = time.time()
        config = FeatureFlagConfig(
            name="test_flag",
            enabled=True,
            strategy=FeatureFlagStrategy.TIME_WINDOW,
            start_time=now - 3600,  # 1 hour ago
            end_time=now + 3600,  # 1 hour from now
        )

        result = evaluate_flag(config, None, None, {})

        assert result is True

    def test_should_evaluate_time_window_before_start(self):
        """Test TIME_WINDOW strategy before start time."""
        now = time.time()
        config = FeatureFlagConfig(
            name="test_flag",
            enabled=True,
            strategy=FeatureFlagStrategy.TIME_WINDOW,
            start_time=now + 3600,  # 1 hour from now
            end_time=now + 7200,  # 2 hours from now
        )

        result = evaluate_flag(config, None, None, {})

        assert result is False

    def test_should_evaluate_time_window_after_end(self):
        """Test TIME_WINDOW strategy after end time."""
        now = time.time()
        config = FeatureFlagConfig(
            name="test_flag",
            enabled=True,
            strategy=FeatureFlagStrategy.TIME_WINDOW,
            start_time=now - 7200,  # 2 hours ago
            end_time=now - 3600,  # 1 hour ago
        )

        result = evaluate_flag(config, None, None, {})

        assert result is False

    def test_should_evaluate_circuit_breaker_strategy(self):
        """Test CIRCUIT_BREAKER strategy delegates correctly."""
        config = FeatureFlagConfig(
            name="test_flag",
            enabled=True,
            strategy=FeatureFlagStrategy.CIRCUIT_BREAKER,
            circuit_breaker_threshold=5,
        )
        circuit_breakers = {}

        result = evaluate_flag(config, None, None, circuit_breakers)

        # No breaker state means circuit is closed
        assert result is True


class TestEvaluateCircuitBreaker:
    """Tests for evaluate_circuit_breaker function."""

    def test_should_return_true_when_no_breaker_state(self):
        """Test circuit is closed when no state exists."""
        config = FeatureFlagConfig(
            name="test_flag",
            strategy=FeatureFlagStrategy.CIRCUIT_BREAKER,
        )

        result = evaluate_circuit_breaker(config, {})

        assert result is True

    def test_should_return_true_when_circuit_closed(self):
        """Test circuit closed state returns True."""
        config = FeatureFlagConfig(
            name="test_flag",
            strategy=FeatureFlagStrategy.CIRCUIT_BREAKER,
        )
        circuit_breakers = {
            "test_flag": CircuitBreakerState(
                is_open=False,
                failure_count=0,
            )
        }

        result = evaluate_circuit_breaker(config, circuit_breakers)

        assert result is True

    def test_should_return_false_when_circuit_open_within_timeout(self):
        """Test circuit open within timeout returns False."""
        config = FeatureFlagConfig(
            name="test_flag",
            strategy=FeatureFlagStrategy.CIRCUIT_BREAKER,
            circuit_breaker_timeout=300,  # 5 minutes
        )
        circuit_breakers = {
            "test_flag": CircuitBreakerState(
                is_open=True,
                failure_count=5,
                last_failure_time=time.time(),  # Just now
            )
        }

        result = evaluate_circuit_breaker(config, circuit_breakers)

        assert result is False

    def test_should_return_true_when_circuit_timeout_passed(self):
        """Test circuit moves to half-open after timeout."""
        config = FeatureFlagConfig(
            name="test_flag",
            strategy=FeatureFlagStrategy.CIRCUIT_BREAKER,
            circuit_breaker_timeout=1,  # 1 second
        )
        circuit_breakers = {
            "test_flag": CircuitBreakerState(
                is_open=True,
                failure_count=5,
                last_failure_time=time.time() - 2,  # 2 seconds ago
            )
        }

        result = evaluate_circuit_breaker(config, circuit_breakers)

        assert result is True
        # Breaker should be reset
        assert circuit_breakers["test_flag"].is_open is False
        assert circuit_breakers["test_flag"].failure_count == 0


class TestRecordSuccess:
    """Tests for record_success function."""

    def test_should_reset_failure_count_on_success(self):
        """Test success resets failure count."""
        circuit_breakers = {
            "test_flag": CircuitBreakerState(
                is_open=False,
                failure_count=3,
            )
        }

        record_success("test_flag", circuit_breakers)

        assert circuit_breakers["test_flag"].failure_count == 0

    def test_should_close_open_circuit_on_success(self):
        """Test success closes open circuit."""
        circuit_breakers = {
            "test_flag": CircuitBreakerState(
                is_open=True,
                failure_count=5,
            )
        }

        record_success("test_flag", circuit_breakers)

        assert circuit_breakers["test_flag"].is_open is False
        assert circuit_breakers["test_flag"].failure_count == 0

    def test_should_ignore_unknown_flag(self):
        """Test success ignores unknown flags."""
        circuit_breakers = {}

        # Should not raise
        record_success("unknown_flag", circuit_breakers)


class TestRecordFailure:
    """Tests for record_failure function."""

    def test_should_increment_failure_count(self):
        """Test failure increments counter."""
        flags = {
            "test_flag": FeatureFlagConfig(
                name="test_flag",
                strategy=FeatureFlagStrategy.CIRCUIT_BREAKER,
                circuit_breaker_threshold=5,
            )
        }
        circuit_breakers = {
            "test_flag": CircuitBreakerState(
                is_open=False,
                failure_count=0,
            )
        }

        record_failure("test_flag", flags, circuit_breakers)

        assert circuit_breakers["test_flag"].failure_count == 1

    def test_should_open_circuit_at_threshold(self):
        """Test circuit opens at threshold."""
        flags = {
            "test_flag": FeatureFlagConfig(
                name="test_flag",
                strategy=FeatureFlagStrategy.CIRCUIT_BREAKER,
                circuit_breaker_threshold=3,
            )
        }
        circuit_breakers = {
            "test_flag": CircuitBreakerState(
                is_open=False,
                failure_count=2,  # One more to hit threshold
            )
        }

        record_failure("test_flag", flags, circuit_breakers)

        assert circuit_breakers["test_flag"].is_open is True
        assert circuit_breakers["test_flag"].failure_count == 3

    def test_should_ignore_non_circuit_breaker_flags(self):
        """Test failure ignores non-circuit-breaker flags."""
        flags = {
            "test_flag": FeatureFlagConfig(
                name="test_flag",
                strategy=FeatureFlagStrategy.BOOLEAN,
            )
        }
        circuit_breakers = {
            "test_flag": CircuitBreakerState(
                is_open=False,
                failure_count=0,
            )
        }

        record_failure("test_flag", flags, circuit_breakers)

        # Should not increment for non-circuit-breaker
        assert circuit_breakers["test_flag"].failure_count == 0

    def test_should_ignore_unknown_flag(self):
        """Test failure ignores unknown flags."""
        flags = {}
        circuit_breakers = {}

        # Should not raise
        record_failure("unknown_flag", flags, circuit_breakers)


class TestGetDefaultValues:
    """Tests for get_default_values function."""

    def test_should_return_sentiment_defaults(self):
        """Test default values for sentiment analysis."""
        result = get_default_values("enhanced_sentiment_analysis")

        assert result["sentiment_score"] == 0.0
        assert result["article_count"] == 0
        assert result["source"] == "default"

    def test_should_return_technical_defaults(self):
        """Test default values for technical analysis."""
        result = get_default_values("advanced_technical_analysis")

        assert "indicators" in result
        assert "confluence_zones" in result
        assert "support_resistance" in result

    def test_should_return_chart_defaults(self):
        """Test default values for chart analysis."""
        result = get_default_values("chart_analysis")

        assert result["chart_url"] is None
        assert result["pattern_insights"] == []

    def test_should_return_perplexity_defaults(self):
        """Test default values for perplexity research."""
        result = get_default_values("perplexity_research")

        assert result["status"] == "disabled"
        assert result["source"] == "fallback"

    def test_should_return_empty_dict_for_unknown(self):
        """Test returns empty dict for unknown flag."""
        result = get_default_values("unknown_flag")

        assert result == {}
