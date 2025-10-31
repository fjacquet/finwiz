"""
Unit tests for the feature flag system.

Tests feature flag evaluation, circuit breaker patterns, fallback strategies,
and graceful degradation logic.
"""

import os
import time

from finwiz.utils.feature_flags import (
    FallbackStrategy,
    FeatureFlagConfig,
    FeatureFlags,
    FeatureFlagStrategy,
    execute_with_feature_flag,
    is_feature_enabled,
)


class TestFeatureFlags:
    """Test suite for FeatureFlags class."""

    def setup_method(self):
        """Set up test environment."""
        # Clear environment variables
        env_vars_to_clear = [
            "FF_ENHANCED_SENTIMENT",
            "FF_ENHANCED_SENTIMENT_ROLLOUT",
            "FF_ADVANCED_TECHNICAL",
            "FF_ADVANCED_TECHNICAL_ROLLOUT",
            "FF_CHART_ANALYSIS",
            "FF_CHART_BREAKER_THRESHOLD",
            "FF_TWELVE_DATA",
            "FF_STRICT_VALIDATION",
            "FF_PERPLEXITY_RESEARCH",
            "FF_PERPLEXITY_BREAKER_THRESHOLD",
            "FF_PERPLEXITY_BREAKER_TIMEOUT",
        ]
        for var in env_vars_to_clear:
            if var in os.environ:
                del os.environ[var]

    def test_should_initialize_with_default_flags(self):
        """Test that FeatureFlags initializes with expected default flags."""
        # Arrange & Act
        flags = FeatureFlags()

        # Assert
        assert len(flags.flags) > 0
        assert "enhanced_sentiment_analysis" in flags.flags
        assert "advanced_technical_analysis" in flags.flags
        assert "chart_analysis" in flags.flags
        assert "twelve_data_integration" in flags.flags
        assert "strict_validation" in flags.flags
        assert "perplexity_research" in flags.flags

    def test_should_load_boolean_flag_from_environment(self, mocker):
        """Test loading boolean feature flags from environment variables."""
        # Arrange
        mocker.patch.dict(os.environ, {"FF_ENHANCED_SENTIMENT": "true"})

        # Act
        flags = FeatureFlags()

        # Assert
        config = flags.flags["enhanced_sentiment_analysis"]
        assert config.enabled is True

    def test_should_load_percentage_rollout_from_environment(self, mocker):
        """Test loading percentage rollout values from environment."""
        # Arrange
        mocker.patch.dict(os.environ, {"FF_ENHANCED_SENTIMENT_ROLLOUT": "75.5"})

        # Act
        flags = FeatureFlags()

        # Assert
        config = flags.flags["enhanced_sentiment_analysis"]
        assert config.rollout_percentage == 75.5

    def test_should_handle_invalid_environment_values_gracefully(self, mocker):
        """Test graceful handling of invalid environment variable values."""
        # Arrange
        mocker.patch.dict(os.environ, {"FF_ENHANCED_SENTIMENT_ROLLOUT": "invalid_number", "FF_CHART_BREAKER_THRESHOLD": "not_an_int"})

        # Act & Assert - Should not raise exception
        flags = FeatureFlags()

        # Should use defaults for invalid values
        config = flags.flags["enhanced_sentiment_analysis"]
        assert config.rollout_percentage == 100.0  # Default value

    def test_should_evaluate_boolean_strategy_correctly(self):
        """Test boolean strategy evaluation."""
        # Arrange
        flags = FeatureFlags()
        flags.flags["test_flag"] = FeatureFlagConfig(name="test_flag", enabled=True, strategy=FeatureFlagStrategy.BOOLEAN)

        # Act & Assert
        assert flags.is_enabled("test_flag") is True

        # Disable flag
        flags.flags["test_flag"].enabled = False
        assert flags.is_enabled("test_flag") is False

    def test_should_evaluate_percentage_strategy_with_user_id(self):
        """Test percentage strategy with deterministic user ID."""
        # Arrange
        flags = FeatureFlags()
        flags.flags["test_flag"] = FeatureFlagConfig(name="test_flag", enabled=True, strategy=FeatureFlagStrategy.PERCENTAGE, rollout_percentage=50.0)

        # Act - Test with specific user IDs that should have consistent results
        user_enabled = flags.is_enabled("test_flag", user_id="user123")
        user_enabled_again = flags.is_enabled("test_flag", user_id="user123")

        # Assert - Same user should get consistent results
        assert user_enabled == user_enabled_again

    def test_should_evaluate_percentage_strategy_without_user_id(self):
        """Test percentage strategy without user ID (random)."""
        # Arrange
        flags = FeatureFlags()
        flags.flags["test_flag"] = FeatureFlagConfig(
            name="test_flag",
            enabled=True,
            strategy=FeatureFlagStrategy.PERCENTAGE,
            rollout_percentage=0.0,  # 0% rollout should always be False
        )

        # Act & Assert
        assert flags.is_enabled("test_flag") is False

        # 100% rollout should always be True
        flags.flags["test_flag"].rollout_percentage = 100.0
        assert flags.is_enabled("test_flag") is True

    def test_should_evaluate_user_list_strategy(self):
        """Test user list strategy evaluation."""
        # Arrange
        flags = FeatureFlags()
        flags.flags["test_flag"] = FeatureFlagConfig(name="test_flag", enabled=True, strategy=FeatureFlagStrategy.USER_LIST, allowed_users={"user1", "user2", "admin"})

        # Act & Assert
        assert flags.is_enabled("test_flag", user_id="user1") is True
        assert flags.is_enabled("test_flag", user_id="user3") is False
        assert flags.is_enabled("test_flag", user_id=None) is False

    def test_should_evaluate_time_window_strategy(self):
        """Test time window strategy evaluation."""
        # Arrange
        current_time = time.time()
        flags = FeatureFlags()
        flags.flags["test_flag"] = FeatureFlagConfig(
            name="test_flag",
            enabled=True,
            strategy=FeatureFlagStrategy.TIME_WINDOW,
            start_time=current_time - 3600,  # Started 1 hour ago
            end_time=current_time + 3600,  # Ends in 1 hour
        )

        # Act & Assert
        assert flags.is_enabled("test_flag") is True

        # Test future start time
        flags.flags["test_flag"].start_time = current_time + 3600
        assert flags.is_enabled("test_flag") is False

        # Test past end time
        flags.flags["test_flag"].start_time = current_time - 7200
        flags.flags["test_flag"].end_time = current_time - 3600
        assert flags.is_enabled("test_flag") is False

    def test_should_handle_circuit_breaker_pattern(self):
        """Test circuit breaker pattern functionality."""
        # Arrange
        flags = FeatureFlags()
        flags.flags["test_flag"] = FeatureFlagConfig(
            name="test_flag",
            enabled=True,
            strategy=FeatureFlagStrategy.CIRCUIT_BREAKER,
            circuit_breaker_threshold=3,
            circuit_breaker_timeout=1,  # 1 second for testing
        )

        # Initialize circuit breaker state for test flag
        from finwiz.utils.feature_flags import CircuitBreakerState

        flags.circuit_breakers["test_flag"] = CircuitBreakerState()

        # Act & Assert - Initially should be enabled
        assert flags.is_enabled("test_flag") is True

        # Record failures to trip circuit breaker
        for _ in range(3):
            flags.record_failure("test_flag")

        # Circuit should now be open
        assert flags.is_enabled("test_flag") is False

        # Manually reset circuit breaker state to simulate timeout
        flags.circuit_breakers["test_flag"]["last_failure_time"] = time.time() - 2.0  # Simulate timeout passed
        assert flags.is_enabled("test_flag") is True  # Should be in half-open state

        # Record success to close circuit
        flags.record_success("test_flag")
        assert flags.is_enabled("test_flag") is True

    def test_should_execute_primary_function_when_flag_enabled(self):
        """Test execution of primary function when feature flag is enabled."""
        # Arrange
        flags = FeatureFlags()
        flags.flags["test_flag"] = FeatureFlagConfig(name="test_flag", enabled=True, strategy=FeatureFlagStrategy.BOOLEAN)

        def primary_func(value):
            return f"primary_{value}"

        def fallback_func(value):
            return f"fallback_{value}"

        # Act
        result = flags.execute_with_fallback("test_flag", primary_func, fallback_func, value="test")

        # Assert
        assert result == "primary_test"

    def test_should_execute_fallback_function_when_flag_disabled(self):
        """Test execution of fallback function when feature flag is disabled."""
        # Arrange
        flags = FeatureFlags()
        flags.flags["test_flag"] = FeatureFlagConfig(
            name="test_flag",
            enabled=False,
            strategy=FeatureFlagStrategy.BOOLEAN,
            fallback_strategy=FallbackStrategy.REDUCED_FUNCTIONALITY,
        )

        def primary_func(value):
            return f"primary_{value}"

        def fallback_func(value):
            return f"fallback_{value}"

        # Act
        result = flags.execute_with_fallback("test_flag", primary_func, fallback_func, value="test")

        # Assert
        assert result == "fallback_test"

    def test_should_execute_fallback_when_primary_function_fails(self):
        """Test fallback execution when primary function raises exception."""
        # Arrange
        flags = FeatureFlags()
        flags.flags["test_flag"] = FeatureFlagConfig(
            name="test_flag",
            enabled=True,
            strategy=FeatureFlagStrategy.BOOLEAN,
            fallback_strategy=FallbackStrategy.REDUCED_FUNCTIONALITY,
        )

        def primary_func(value):
            raise ValueError("Primary function failed")

        def fallback_func(value):
            return f"fallback_{value}"

        # Act
        result = flags.execute_with_fallback("test_flag", primary_func, fallback_func, value="test")

        # Assert
        assert result == "fallback_test"

    def test_should_return_default_values_for_disable_strategy(self):
        """Test default values fallback strategy."""
        # Arrange
        flags = FeatureFlags()
        flags.flags["enhanced_sentiment_analysis"] = FeatureFlagConfig(
            name="enhanced_sentiment_analysis",
            enabled=False,
            strategy=FeatureFlagStrategy.BOOLEAN,
            fallback_strategy=FallbackStrategy.DEFAULT_VALUES,
        )

        def primary_func():
            return {"sentiment_score": 0.8, "article_count": 10}

        # Act
        result = flags.execute_with_fallback("enhanced_sentiment_analysis", primary_func)

        # Assert
        assert result is not None
        assert "sentiment_score" in result
        assert result["sentiment_score"] == 0.0  # Default value

    def test_should_return_none_for_disable_fallback_strategy(self):
        """Test disable fallback strategy returns None."""
        # Arrange
        flags = FeatureFlags()
        flags.flags["test_flag"] = FeatureFlagConfig(name="test_flag", enabled=False, strategy=FeatureFlagStrategy.BOOLEAN, fallback_strategy=FallbackStrategy.DISABLE)

        def primary_func():
            return "primary_result"

        # Act
        result = flags.execute_with_fallback("test_flag", primary_func)

        # Assert
        assert result is None

    def test_should_get_flag_status_with_comprehensive_info(self):
        """Test getting comprehensive flag status information."""
        # Arrange
        flags = FeatureFlags()

        # Act
        status = flags.get_flag_status("enhanced_sentiment_analysis")

        # Assert
        assert "name" in status
        assert "enabled" in status
        assert "strategy" in status
        assert "fallback_strategy" in status
        assert "description" in status
        assert status["name"] == "enhanced_sentiment_analysis"

    def test_should_list_all_flags_with_status(self):
        """Test listing all feature flags with their status."""
        # Arrange
        flags = FeatureFlags()

        # Act
        all_flags = flags.list_all_flags()

        # Assert
        assert isinstance(all_flags, dict)
        assert len(all_flags) > 0
        assert "enhanced_sentiment_analysis" in all_flags
        assert "advanced_technical_analysis" in all_flags

    def test_should_update_flag_configuration_at_runtime(self):
        """Test updating feature flag configuration at runtime."""
        # Arrange
        flags = FeatureFlags()
        original_enabled = flags.flags["enhanced_sentiment_analysis"].enabled

        # Act
        success = flags.update_flag("enhanced_sentiment_analysis", enabled=not original_enabled)

        # Assert
        assert success is True
        assert flags.flags["enhanced_sentiment_analysis"].enabled != original_enabled

    def test_should_handle_unknown_flag_gracefully(self):
        """Test graceful handling of unknown feature flags."""
        # Arrange
        flags = FeatureFlags()

        # Act & Assert
        assert flags.is_enabled("unknown_flag") is False

        status = flags.get_flag_status("unknown_flag")
        assert "error" in status

        success = flags.update_flag("unknown_flag", enabled=True)
        assert success is False

    def test_should_configure_perplexity_research_flag_correctly(self):
        """Test that perplexity_research flag is configured with circuit breaker strategy."""
        # Arrange & Act
        flags = FeatureFlags()

        # Assert
        config = flags.flags["perplexity_research"]
        assert config.name == "perplexity_research"
        assert config.enabled is False  # Default disabled
        assert config.strategy == FeatureFlagStrategy.CIRCUIT_BREAKER
        assert config.fallback_strategy == FallbackStrategy.CACHED_ONLY
        assert config.circuit_breaker_threshold == 5  # Default threshold
        assert config.circuit_breaker_timeout == 300  # Default timeout
        assert "Perplexity Sonar Search integration" in config.description

    def test_should_load_perplexity_research_flag_from_environment(self, mocker):
        """Test loading perplexity_research flag configuration from environment variables."""
        # Arrange
        mocker.patch.dict(
            os.environ,
            {
                "FF_PERPLEXITY_RESEARCH": "true",
                "FF_PERPLEXITY_BREAKER_THRESHOLD": "3",
                "FF_PERPLEXITY_BREAKER_TIMEOUT": "600",
            },
        )

        # Act
        flags = FeatureFlags()

        # Assert
        config = flags.flags["perplexity_research"]
        assert config.enabled is True
        assert config.circuit_breaker_threshold == 3
        assert config.circuit_breaker_timeout == 600

    def test_should_return_perplexity_default_values_when_disabled(self):
        """Test that perplexity_research returns appropriate default values when disabled."""
        # Arrange
        flags = FeatureFlags()

        def primary_func():
            return {"sonar_articles": [{"title": "Test"}], "total_results": 1}

        # Act
        result = flags.execute_with_fallback("perplexity_research", primary_func)

        # Assert - Should return default values since flag is disabled by default
        assert result is not None
        assert "sonar_articles" in result
        assert result["sonar_articles"] == []
        assert result["total_results"] == 0
        assert result["source"] == "fallback"
        assert result["status"] == "disabled"


class TestFeatureFlagConvenienceFunctions:
    """Test suite for convenience functions."""

    def test_should_check_feature_enabled_via_convenience_function(self):
        """Test is_feature_enabled convenience function."""
        # Arrange & Act
        result = is_feature_enabled("enhanced_sentiment_analysis")

        # Assert
        assert isinstance(result, bool)

    def test_should_execute_with_feature_flag_via_convenience_function(self):
        """Test execute_with_feature_flag convenience function."""

        # Arrange
        def primary_func(value):
            return f"primary_{value}"

        def fallback_func(value):
            return f"fallback_{value}"

        # Act
        result = execute_with_feature_flag("enhanced_sentiment_analysis", primary_func, fallback_func, value="test")

        # Assert
        assert result is not None
        assert isinstance(result, str)


class TestFeatureFlagIntegration:
    """Integration tests for feature flag system."""

    def test_should_integrate_with_environment_variables(self, mocker):
        """Test integration with environment variable configuration."""
        # Arrange & Act
        mocker.patch.dict(os.environ, {"FF_ENHANCED_SENTIMENT": "false", "FF_ADVANCED_TECHNICAL": "true", "FF_CHART_ANALYSIS": "false"})

        flags = FeatureFlags()

        # Assert
        assert flags.is_enabled("enhanced_sentiment_analysis") is False
        assert flags.is_enabled("advanced_technical_analysis") is True
        assert flags.is_enabled("chart_analysis") is False

    def test_should_handle_circuit_breaker_recovery_scenario(self):
        """Test complete circuit breaker recovery scenario."""
        # Arrange
        flags = FeatureFlags()
        flags.flags["test_service"] = FeatureFlagConfig(
            name="test_service",
            enabled=True,
            strategy=FeatureFlagStrategy.CIRCUIT_BREAKER,
            circuit_breaker_threshold=2,
            circuit_breaker_timeout=0.5,
            fallback_strategy=FallbackStrategy.CACHED_ONLY,
        )

        def failing_service():
            raise ConnectionError("Service unavailable")

        def cached_fallback():
            return {"cached": True, "data": "fallback_data"}

        # Act & Assert - Initial calls should fail and trip circuit
        result1 = flags.execute_with_fallback("test_service", failing_service, cached_fallback)
        result2 = flags.execute_with_fallback("test_service", failing_service, cached_fallback)

        # Circuit should be open now, fallback should be used immediately
        result3 = flags.execute_with_fallback("test_service", failing_service, cached_fallback)

        # All results should be from fallback
        assert result1 == {"cached": True, "data": "fallback_data"}
        assert result2 == {"cached": True, "data": "fallback_data"}
        assert result3 == {"cached": True, "data": "fallback_data"}

        # Manually reset circuit breaker to simulate timeout
        flags.circuit_breakers["test_service"]["last_failure_time"] = time.time() - 1.0

        # Define a working service for recovery
        def working_service():
            return {"success": True, "data": "real_data"}

        # Circuit should try to close
        result4 = flags.execute_with_fallback("test_service", working_service, cached_fallback)

        assert result4 == {"success": True, "data": "real_data"}
