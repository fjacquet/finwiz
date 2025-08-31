"""
Feature flag system for gradual rollout and graceful degradation.

This module provides a comprehensive feature flag system that allows for:
- Environment variable-based configuration
- Gradual rollout capabilities with percentage-based rollouts
- Graceful degradation logic for API failures and rate limits
- Feature flag evaluation with fallback strategies
"""

import os
import random
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class FeatureFlagStrategy(str, Enum):
    """Feature flag evaluation strategies."""

    BOOLEAN = "boolean"  # Simple on/off
    PERCENTAGE = "percentage"  # Percentage-based rollout
    USER_LIST = "user_list"  # Specific user allowlist
    TIME_WINDOW = "time_window"  # Time-based activation
    CIRCUIT_BREAKER = "circuit_breaker"  # Circuit breaker pattern


class FallbackStrategy(str, Enum):
    """Fallback strategies for degraded functionality."""

    DISABLE = "disable"  # Disable feature completely
    CACHED_ONLY = "cached_only"  # Use cached data only
    REDUCED_FUNCTIONALITY = "reduced_functionality"  # Limited feature set
    DEFAULT_VALUES = "default_values"  # Use default/mock values
    RETRY_WITH_BACKOFF = "retry_with_backoff"  # Retry with exponential backoff


@dataclass
class FeatureFlagConfig:
    """Configuration for a single feature flag."""

    name: str
    enabled: bool = False
    strategy: FeatureFlagStrategy = FeatureFlagStrategy.BOOLEAN
    rollout_percentage: float = 0.0  # 0-100
    allowed_users: set[str] = field(default_factory=set)
    start_time: float | None = None
    end_time: float | None = None
    fallback_strategy: FallbackStrategy = FallbackStrategy.DISABLE
    circuit_breaker_threshold: int = 5  # Failures before circuit opens
    circuit_breaker_timeout: int = 300  # Seconds before retry
    description: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class CircuitBreakerState:
    """State tracking for circuit breaker pattern."""

    failure_count: int = 0
    last_failure_time: float = 0.0
    is_open: bool = False
    last_success_time: float = 0.0


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
        # Define default feature flags for FinWiz
        default_flags = {
            "enhanced_sentiment_analysis": FeatureFlagConfig(
                name="enhanced_sentiment_analysis",
                enabled=self._get_env_bool("FF_ENHANCED_SENTIMENT", True),
                strategy=FeatureFlagStrategy.PERCENTAGE,
                rollout_percentage=self._get_env_float("FF_ENHANCED_SENTIMENT_ROLLOUT", 100.0),
                fallback_strategy=FallbackStrategy.CACHED_ONLY,
                description="Multi-source sentiment analysis with trending topics",
            ),
            "advanced_technical_analysis": FeatureFlagConfig(
                name="advanced_technical_analysis",
                enabled=self._get_env_bool("FF_ADVANCED_TECHNICAL", True),
                strategy=FeatureFlagStrategy.PERCENTAGE,
                rollout_percentage=self._get_env_float("FF_ADVANCED_TECHNICAL_ROLLOUT", 100.0),
                fallback_strategy=FallbackStrategy.REDUCED_FUNCTIONALITY,
                description="Advanced technical indicators and confluence detection",
            ),
            "chart_analysis": FeatureFlagConfig(
                name="chart_analysis",
                enabled=self._get_env_bool("FF_CHART_ANALYSIS", True),
                strategy=FeatureFlagStrategy.CIRCUIT_BREAKER,
                circuit_breaker_threshold=self._get_env_int("FF_CHART_BREAKER_THRESHOLD", 3),
                circuit_breaker_timeout=self._get_env_int("FF_CHART_BREAKER_TIMEOUT", 300),
                fallback_strategy=FallbackStrategy.DISABLE,
                description="Chart-img API integration for visual analysis",
            ),
            "twelve_data_integration": FeatureFlagConfig(
                name="twelve_data_integration",
                enabled=self._get_env_bool("FF_TWELVE_DATA", True),
                strategy=FeatureFlagStrategy.CIRCUIT_BREAKER,
                circuit_breaker_threshold=self._get_env_int("FF_TWELVE_DATA_BREAKER_THRESHOLD", 5),
                circuit_breaker_timeout=self._get_env_int("FF_TWELVE_DATA_BREAKER_TIMEOUT", 600),
                fallback_strategy=FallbackStrategy.CACHED_ONLY,
                description="Twelve Data API for technical indicators",
            ),
            "strict_validation": FeatureFlagConfig(
                name="strict_validation",
                enabled=self._get_env_bool("FF_STRICT_VALIDATION", True),
                strategy=FeatureFlagStrategy.PERCENTAGE,
                rollout_percentage=self._get_env_float("FF_STRICT_VALIDATION_ROLLOUT", 100.0),
                fallback_strategy=FallbackStrategy.REDUCED_FUNCTIONALITY,
                description="Strict Pydantic validation enforcement",
            ),
            "async_execution": FeatureFlagConfig(
                name="async_execution",
                enabled=self._get_env_bool("FF_ASYNC_EXECUTION", True),
                strategy=FeatureFlagStrategy.BOOLEAN,
                fallback_strategy=FallbackStrategy.REDUCED_FUNCTIONALITY,
                description="Asynchronous task execution for I/O operations",
            ),
            "intelligent_caching": FeatureFlagConfig(
                name="intelligent_caching",
                enabled=self._get_env_bool("FF_INTELLIGENT_CACHING", True),
                strategy=FeatureFlagStrategy.BOOLEAN,
                fallback_strategy=FallbackStrategy.DISABLE,
                description="Advanced caching with TTL and invalidation strategies",
            ),
            "portfolio_review": FeatureFlagConfig(
                name="portfolio_review",
                enabled=self._get_env_bool("FF_PORTFOLIO_REVIEW", True),
                strategy=FeatureFlagStrategy.BOOLEAN,
                fallback_strategy=FallbackStrategy.DISABLE,
                description="Portfolio keep-or-sell review functionality",
            ),
        }

        self.flags.update(default_flags)

        # Initialize circuit breaker states
        for flag_name, config in self.flags.items():
            if config.strategy == FeatureFlagStrategy.CIRCUIT_BREAKER:
                self.circuit_breakers[flag_name] = CircuitBreakerState()

    def _get_env_bool(self, key: str, default: bool = False) -> bool:
        """Get boolean value from environment variable."""
        value = os.getenv(key, str(default)).lower()
        return value in {"true", "1", "yes", "on", "enabled"}

    def _get_env_float(self, key: str, default: float = 0.0) -> float:
        """Get float value from environment variable."""
        try:
            return float(os.getenv(key, str(default)))
        except (ValueError, TypeError):
            logger.warning(f"Invalid float value for {key}, using default: {default}")
            return default

    def _get_env_int(self, key: str, default: int = 0) -> int:
        """Get integer value from environment variable."""
        try:
            return int(os.getenv(key, str(default)))
        except (ValueError, TypeError):
            logger.warning(f"Invalid integer value for {key}, using default: {default}")
            return default

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
            return self._evaluate_flag(config, user_id, context)
        except Exception as e:
            logger.error(f"Error evaluating feature flag {flag_name}: {e}")
            return False

    def _evaluate_flag(self, config: FeatureFlagConfig, user_id: str | None, context: dict[str, Any] | None) -> bool:
        """Evaluate feature flag based on its strategy."""
        if config.strategy == FeatureFlagStrategy.BOOLEAN:
            return config.enabled

        elif config.strategy == FeatureFlagStrategy.PERCENTAGE:
            # Use deterministic hash for consistent user experience
            if user_id:
                hash_value = hash(f"{config.name}:{user_id}") % 100
            else:
                hash_value = random.randint(0, 99)
            return hash_value < config.rollout_percentage

        elif config.strategy == FeatureFlagStrategy.USER_LIST:
            return user_id is not None and user_id in config.allowed_users

        elif config.strategy == FeatureFlagStrategy.TIME_WINDOW:
            current_time = time.time()
            if config.start_time and current_time < config.start_time:
                return False
            if config.end_time and current_time > config.end_time:
                return False
            return True

        elif config.strategy == FeatureFlagStrategy.CIRCUIT_BREAKER:
            return self._evaluate_circuit_breaker(config)

        return False

    def _evaluate_circuit_breaker(self, config: FeatureFlagConfig) -> bool:
        """Evaluate circuit breaker state for feature flag."""
        breaker = self.circuit_breakers.get(config.name)
        if not breaker:
            return True

        current_time = time.time()

        # If circuit is open, check if timeout has passed
        if breaker.is_open:
            if current_time - breaker.last_failure_time > config.circuit_breaker_timeout:
                # Try to close circuit (half-open state)
                breaker.is_open = False
                breaker.failure_count = 0
                logger.info(f"Circuit breaker for {config.name} moving to half-open state")
                return True
            return False

        # Circuit is closed or half-open
        return True

    def record_success(self, flag_name: str) -> None:
        """Record successful operation for circuit breaker."""
        if flag_name in self.circuit_breakers:
            breaker = self.circuit_breakers[flag_name]
            breaker.failure_count = 0
            breaker.last_success_time = time.time()
            if breaker.is_open:
                breaker.is_open = False
                logger.info(f"Circuit breaker for {flag_name} closed after successful operation")

    def record_failure(self, flag_name: str) -> None:
        """Record failed operation for circuit breaker."""
        if flag_name not in self.circuit_breakers:
            return

        config = self.flags.get(flag_name)
        if not config or config.strategy != FeatureFlagStrategy.CIRCUIT_BREAKER:
            return

        breaker = self.circuit_breakers[flag_name]
        breaker.failure_count += 1
        breaker.last_failure_time = time.time()

        if breaker.failure_count >= config.circuit_breaker_threshold:
            breaker.is_open = True
            logger.warning(f"Circuit breaker for {flag_name} opened after {breaker.failure_count} failures")

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
        *args,
        **kwargs,
    ) -> Any:
        """
        Execute function with feature flag and fallback logic.

        Args:
            flag_name: Name of the feature flag
            primary_func: Primary function to execute if flag is enabled
            fallback_func: Optional fallback function
            user_id: Optional user identifier
            context: Optional context for evaluation
            *args, **kwargs: Arguments for the functions

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

    def _execute_fallback(self, flag_name: str, fallback_func: Callable | None, *args, **kwargs) -> Any:
        """Execute fallback logic based on strategy."""
        strategy = self.get_fallback_strategy(flag_name)

        if strategy == FallbackStrategy.DISABLE:
            logger.info(f"Feature {flag_name} disabled, returning None")
            return None

        elif strategy == FallbackStrategy.DEFAULT_VALUES:
            logger.info(f"Feature {flag_name} using default values")
            return self._get_default_values(flag_name)

        elif fallback_func:
            try:
                return fallback_func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Fallback function failed for {flag_name}: {e}")
                return None

        else:
            logger.warning(f"No fallback available for {flag_name}")
            return None

    def _get_default_values(self, flag_name: str) -> Any:
        """Get default values for specific features."""
        defaults = {
            "enhanced_sentiment_analysis": {"sentiment_score": 0.0, "article_count": 0, "trending_topics": [], "source": "default"},
            "advanced_technical_analysis": {
                "indicators": {},
                "confluence_zones": [],
                "support_resistance": {"support": [], "resistance": []},
            },
            "chart_analysis": {"chart_url": None, "pattern_insights": [], "visual_analysis": "Chart analysis unavailable"},
        }
        return defaults.get(flag_name, {})

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

    def update_flag(self, flag_name: str, **updates) -> bool:
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
    """Convenience function to check if a feature is enabled."""
    return get_feature_flags().is_enabled(flag_name, user_id, context)


def execute_with_feature_flag(
    flag_name: str,
    primary_func: Callable,
    fallback_func: Callable | None = None,
    user_id: str | None = None,
    context: dict[str, Any] | None = None,
    *args,
    **kwargs,
) -> Any:
    """Convenience function to execute with feature flag and fallback."""
    return get_feature_flags().execute_with_fallback(flag_name, primary_func, fallback_func, user_id, context, *args, **kwargs)
