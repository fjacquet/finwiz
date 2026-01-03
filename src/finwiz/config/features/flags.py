"""
Feature flag system for gradual rollout and graceful degradation.

This module provides a comprehensive feature flag system that allows for:
- Environment variable-based configuration
- Gradual rollout capabilities with percentage-based rollouts
- Graceful degradation logic for API failures and rate limits
- Feature flag evaluation with fallback strategies
"""

from collections.abc import Callable
from typing import Any

from finwiz.config.features.definitions import (
    CircuitBreakerState,
    FallbackStrategy,
    FeatureFlagConfig,
    FeatureFlagStrategy,
    create_default_flags,
)
from finwiz.config.features.evaluators import (
    evaluate_flag,
    get_default_values,
    record_failure,
    record_success,
)
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class FeatureFlags:
    """
    Feature flag manager with environment variable-based configuration.

    Supports multiple evaluation strategies and graceful degradation patterns
    for robust system behavior during failures or gradual rollouts.
    """

    def __init__(self) -> None:
        """Initialize feature flag manager."""
        self.flags: dict[str, FeatureFlagConfig] = {}
        self.circuit_breakers: dict[str, CircuitBreakerState] = {}
        self._load_from_environment()
        logger.info(f"Feature flags initialized with {len(self.flags)} flags")

    def _load_from_environment(self) -> None:
        """Load feature flag configurations from environment variables."""
        # Load default flags from definitions module
        default_flags = create_default_flags()
        self.flags.update(default_flags)

        # Initialize circuit breaker states
        for flag_name, config in self.flags.items():
            if config.strategy == FeatureFlagStrategy.CIRCUIT_BREAKER:
                self.circuit_breakers[flag_name] = CircuitBreakerState()

    def is_enabled(self, flag_name: str, user_id: str | None = None, context: dict[str, Any] | None = None) -> bool:
        """
        Check if a feature flag is enabled for the given context.

        Args:
            flag_name: Name of the feature flag
            user_id: Optional user identifier for user-based rollouts
            context: Optional context for evaluation

        Returns:
            True if feature is enabled, False otherwise

        """
        if flag_name not in self.flags:
            logger.warning(f"Unknown feature flag: {flag_name}")
            return False

        config = self.flags[flag_name]

        # Check if flag is globally disabled
        if not config.enabled:
            return False

        # Evaluate based on strategy
        try:
            return evaluate_flag(config, user_id, context, self.circuit_breakers)
        except Exception as e:
            logger.error(f"Error evaluating feature flag {flag_name}: {e}")
            return False

    def record_success(self, flag_name: str) -> None:
        """Record successful operation for circuit breaker."""
        record_success(flag_name, self.circuit_breakers)

    def record_failure(self, flag_name: str) -> None:
        """Record failed operation for circuit breaker."""
        record_failure(flag_name, self.flags, self.circuit_breakers)

    def get_fallback_strategy(self, flag_name: str) -> FallbackStrategy:
        """Get fallback strategy for a feature flag."""
        if flag_name not in self.flags:
            return FallbackStrategy.DISABLE
        return self.flags[flag_name].fallback_strategy

    def execute_with_fallback(
        self,
        flag_name: str,
        primary_func: Callable,
        fallback_func: Callable | None = None,
        user_id: str | None = None,
        context: dict[str, Any] | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Execute function with feature flag and fallback logic.

        Args:
            flag_name: Name of the feature flag
            primary_func: Primary function to execute if flag is enabled
            fallback_func: Optional fallback function
            user_id: Optional user identifier
            context: Optional context for evaluation
            *args: Positional arguments for the functions
            **kwargs: Keyword arguments for the functions

        Returns:
            Result from primary or fallback function

        """
        if self.is_enabled(flag_name, user_id, context):
            try:
                result = primary_func(*args, **kwargs)
                self.record_success(flag_name)
                return result
            except Exception as e:
                logger.warning(f"Primary function failed for {flag_name}: {e}")
                self.record_failure(flag_name)
                return self._execute_fallback(flag_name, fallback_func, *args, **kwargs)
        else:
            logger.debug(f"Feature flag {flag_name} disabled, using fallback")
            return self._execute_fallback(flag_name, fallback_func, *args, **kwargs)

    def _execute_fallback(self, flag_name: str, fallback_func: Callable | None, *args: Any, **kwargs: Any) -> Any:
        """Execute fallback logic based on strategy."""
        strategy = self.get_fallback_strategy(flag_name)

        if strategy == FallbackStrategy.DEFAULT_VALUES:
            logger.info(f"Feature {flag_name} using default values")
            return get_default_values(flag_name)

        elif strategy == FallbackStrategy.CACHED_ONLY:
            # For cached_only strategy, return default values if no cache available
            logger.info(f"Feature {flag_name} using cached fallback (default values)")
            return get_default_values(flag_name)

        elif fallback_func:
            try:
                return fallback_func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Fallback function failed for {flag_name}: {e}")
                # Try default values as last resort
                default_values = get_default_values(flag_name)
                if default_values:
                    return default_values
                return None

        elif strategy == FallbackStrategy.DISABLE:
            logger.info(f"Feature {flag_name} disabled, returning None")
            return None

        else:
            # Try default values as fallback
            default_values = get_default_values(flag_name)
            if default_values:
                logger.info(f"Using default values as fallback for {flag_name}")
                return default_values

            logger.warning(f"No fallback available for {flag_name}")
            return None

    def get_flag_status(self, flag_name: str) -> dict[str, Any]:
        """Get comprehensive status of a feature flag."""
        if flag_name not in self.flags:
            return {"error": f"Flag {flag_name} not found"}

        config = self.flags[flag_name]
        status = {
            "name": config.name,
            "enabled": config.enabled,
            "strategy": config.strategy.value,
            "fallback_strategy": config.fallback_strategy.value,
            "description": config.description,
        }

        if config.strategy == FeatureFlagStrategy.PERCENTAGE:
            status["rollout_percentage"] = config.rollout_percentage

        if config.strategy == FeatureFlagStrategy.CIRCUIT_BREAKER:
            breaker = self.circuit_breakers.get(flag_name)
            if breaker:
                status["circuit_breaker"] = {
                    "is_open": breaker.is_open,
                    "failure_count": breaker.failure_count,
                    "last_failure_time": breaker.last_failure_time,
                    "threshold": config.circuit_breaker_threshold,
                }

        return status

    def list_all_flags(self) -> dict[str, dict[str, Any]]:
        """List all feature flags and their current status."""
        return {name: self.get_flag_status(name) for name in self.flags.keys()}

    def get_enabled_flags(self) -> list[str]:
        """Get list of enabled feature flag names."""
        enabled_flags = []
        for flag_name in self.flags.keys():
            if self.is_enabled(flag_name):
                enabled_flags.append(flag_name)
        return enabled_flags

    def update_flag(self, flag_name: str, **updates: Any) -> bool:
        """
        Update feature flag configuration at runtime.

        Args:
            flag_name: Name of the flag to update
            **updates: Configuration updates

        Returns:
            True if update was successful, False otherwise

        """
        if flag_name not in self.flags:
            logger.error(f"Cannot update unknown flag: {flag_name}")
            return False

        try:
            config = self.flags[flag_name]
            for key, value in updates.items():
                if hasattr(config, key):
                    setattr(config, key, value)
                    logger.info(f"Updated {flag_name}.{key} to {value}")
                else:
                    logger.warning(f"Unknown config key for {flag_name}: {key}")
            return True
        except Exception as e:
            logger.error(f"Error updating flag {flag_name}: {e}")
            return False


# Global feature flags instance
_feature_flags: FeatureFlags | None = None


def get_feature_flags() -> FeatureFlags:
    """Get the global feature flags instance."""
    global _feature_flags
    if _feature_flags is None:
        _feature_flags = FeatureFlags()
    return _feature_flags


def is_feature_enabled(flag_name: str, user_id: str | None = None, context: dict[str, Any] | None = None) -> bool:
    """Check if a feature is enabled."""
    return get_feature_flags().is_enabled(flag_name, user_id, context)


def execute_with_feature_flag(
    flag_name: str,
    primary_func: Callable,
    fallback_func: Callable | None = None,
    user_id: str | None = None,
    context: dict[str, Any] | None = None,
    *args: Any,
    **kwargs: Any,
) -> Any:
    """Execute with feature flag and fallback."""
    return get_feature_flags().execute_with_fallback(flag_name, primary_func, fallback_func, user_id, context, *args, **kwargs)
