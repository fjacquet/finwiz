"""
Feature flag evaluation logic and circuit breaker management.

This module contains the core evaluation logic for different feature flag strategies
and circuit breaker pattern implementation.
"""

import random
import time
from typing import Any

from finwiz.config.features.definitions import (
    CircuitBreakerState,
    FeatureFlagConfig,
    FeatureFlagStrategy,
)
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


def evaluate_flag(
    config: FeatureFlagConfig,
    user_id: str | None,
    context: dict[str, Any] | None,
    circuit_breakers: dict[str, CircuitBreakerState],
) -> bool:
    """
    Evaluate feature flag based on its strategy.

    Args:
        config: Feature flag configuration
        user_id: Optional user identifier
        context: Optional context for evaluation
        circuit_breakers: Circuit breaker states dictionary

    Returns:
        True if feature is enabled, False otherwise

    """
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
        return evaluate_circuit_breaker(config, circuit_breakers)

    return False


def evaluate_circuit_breaker(config: FeatureFlagConfig, circuit_breakers: dict[str, CircuitBreakerState]) -> bool:
    """
    Evaluate circuit breaker state for feature flag.

    Args:
        config: Feature flag configuration
        circuit_breakers: Circuit breaker states dictionary

    Returns:
        True if circuit is closed or half-open, False if open

    """
    breaker = circuit_breakers.get(config.name)
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


def record_success(flag_name: str, circuit_breakers: dict[str, CircuitBreakerState]) -> None:
    """
    Record successful operation for circuit breaker.

    Args:
        flag_name: Name of the feature flag
        circuit_breakers: Circuit breaker states dictionary

    """
    if flag_name in circuit_breakers:
        breaker = circuit_breakers[flag_name]
        breaker.failure_count = 0
        breaker.last_success_time = time.time()
        if breaker.is_open:
            breaker.is_open = False
            logger.info(f"Circuit breaker for {flag_name} closed after successful operation")


def record_failure(flag_name: str, flags: dict[str, FeatureFlagConfig], circuit_breakers: dict[str, CircuitBreakerState]) -> None:
    """
    Record failed operation for circuit breaker.

    Args:
        flag_name: Name of the feature flag
        flags: Feature flags dictionary
        circuit_breakers: Circuit breaker states dictionary

    """
    if flag_name not in circuit_breakers:
        return

    config = flags.get(flag_name)
    if not config or config.strategy != FeatureFlagStrategy.CIRCUIT_BREAKER:
        return

    breaker = circuit_breakers[flag_name]
    breaker.failure_count += 1
    breaker.last_failure_time = time.time()

    if breaker.failure_count >= config.circuit_breaker_threshold:
        breaker.is_open = True
        logger.warning(f"Circuit breaker for {flag_name} opened after {breaker.failure_count} failures")


def get_default_values(flag_name: str) -> Any:
    """
    Get default values for specific features.

    Args:
        flag_name: Name of the feature flag

    Returns:
        Default values for the feature or empty dict

    """
    defaults = {
        "enhanced_sentiment_analysis": {"sentiment_score": 0.0, "article_count": 0, "trending_topics": [], "source": "default"},
        "chart_analysis": {"chart_url": None, "pattern_insights": [], "visual_analysis": "Chart analysis unavailable"},
        "perplexity_research": {
            "sonar_articles": [],
            "search_results": [],
            "total_results": 0,
            "source": "fallback",
            "status": "disabled",
        },
        "finnhub_news": {
            "articles": [],
            "aggregate_sentiment": 0.0,
            "article_count": 0,
            "source": "default",
        },
        "fred_macro": {
            "fed_rate": None,
            "cpi_yoy": None,
            "unemployment_rate": None,
            "gdp_growth": None,
            "vix": None,
            "source": "default",
        },
        "fear_greed_index": {
            "value": None,
            "label": None,
            "source": "default",
        },
        "sentiment_scoring": {"weight": 0.0, "source": "disabled"},
        "macro_scoring": {"weight": 0.0, "source": "disabled"},
    }
    result = defaults.get(flag_name, {})
    if result:
        logger.info(f"Using default values for {flag_name}")
    return result
