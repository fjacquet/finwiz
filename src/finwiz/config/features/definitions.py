"""
Feature flag definitions and configuration models.

This module defines all feature flag enums, strategies, and configuration dataclasses
used throughout the FinWiz system.
"""

import os
from dataclasses import dataclass, field
from enum import Enum

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


def get_env_bool(key: str, default: bool = False) -> bool:
    """Get boolean value from environment variable."""
    value = os.getenv(key, str(default)).lower()
    return value in {"true", "1", "yes", "on", "enabled"}


def get_env_float(key: str, default: float = 0.0) -> float:
    """Get float value from environment variable."""
    try:
        return float(os.getenv(key, str(default)))
    except (ValueError, TypeError):
        logger.warning(f"Invalid float value for {key}, using default: {default}")
        return default


def get_env_int(key: str, default: int = 0) -> int:
    """Get integer value from environment variable."""
    try:
        return int(os.getenv(key, str(default)))
    except (ValueError, TypeError):
        logger.warning(f"Invalid integer value for {key}, using default: {default}")
        return default


def create_default_flags() -> dict[str, FeatureFlagConfig]:
    """Create default feature flag configurations from environment variables."""
    return {
        "enhanced_sentiment_analysis": FeatureFlagConfig(
            name="enhanced_sentiment_analysis",
            enabled=get_env_bool("FF_ENHANCED_SENTIMENT", True),
            strategy=FeatureFlagStrategy.PERCENTAGE,
            rollout_percentage=get_env_float("FF_ENHANCED_SENTIMENT_ROLLOUT", 100.0),
            fallback_strategy=FallbackStrategy.CACHED_ONLY,
            description="Multi-source sentiment analysis with trending topics",
        ),
        "advanced_technical_analysis": FeatureFlagConfig(
            name="advanced_technical_analysis",
            enabled=get_env_bool("FF_ADVANCED_TECHNICAL", True),
            strategy=FeatureFlagStrategy.PERCENTAGE,
            rollout_percentage=get_env_float("FF_ADVANCED_TECHNICAL_ROLLOUT", 100.0),
            fallback_strategy=FallbackStrategy.REDUCED_FUNCTIONALITY,
            description="Advanced technical indicators and confluence detection",
        ),
        "chart_analysis": FeatureFlagConfig(
            name="chart_analysis",
            enabled=get_env_bool("FF_CHART_ANALYSIS", True),
            strategy=FeatureFlagStrategy.CIRCUIT_BREAKER,
            circuit_breaker_threshold=get_env_int("FF_CHART_BREAKER_THRESHOLD", 3),
            circuit_breaker_timeout=get_env_int("FF_CHART_BREAKER_TIMEOUT", 300),
            fallback_strategy=FallbackStrategy.DISABLE,
            description="Chart-img API integration for visual analysis",
        ),
        "twelve_data_integration": FeatureFlagConfig(
            name="twelve_data_integration",
            enabled=get_env_bool("FF_TWELVE_DATA", True),
            strategy=FeatureFlagStrategy.CIRCUIT_BREAKER,
            circuit_breaker_threshold=get_env_int("FF_TWELVE_DATA_BREAKER_THRESHOLD", 5),
            circuit_breaker_timeout=get_env_int("FF_TWELVE_DATA_BREAKER_TIMEOUT", 600),
            fallback_strategy=FallbackStrategy.CACHED_ONLY,
            description="Twelve Data API for technical indicators",
        ),
        "strict_validation": FeatureFlagConfig(
            name="strict_validation",
            enabled=get_env_bool("FF_STRICT_VALIDATION", True),
            strategy=FeatureFlagStrategy.PERCENTAGE,
            rollout_percentage=get_env_float("FF_STRICT_VALIDATION_ROLLOUT", 100.0),
            fallback_strategy=FallbackStrategy.REDUCED_FUNCTIONALITY,
            description="Strict Pydantic validation enforcement",
        ),
        "async_execution": FeatureFlagConfig(
            name="async_execution",
            enabled=get_env_bool("FF_ASYNC_EXECUTION", True),
            strategy=FeatureFlagStrategy.BOOLEAN,
            fallback_strategy=FallbackStrategy.REDUCED_FUNCTIONALITY,
            description="Asynchronous task execution for I/O operations",
        ),
        "intelligent_caching": FeatureFlagConfig(
            name="intelligent_caching",
            enabled=get_env_bool("FF_INTELLIGENT_CACHING", True),
            strategy=FeatureFlagStrategy.BOOLEAN,
            fallback_strategy=FallbackStrategy.DISABLE,
            description="Advanced caching with TTL and invalidation strategies",
        ),
        "portfolio_review": FeatureFlagConfig(
            name="portfolio_review",
            enabled=get_env_bool("FF_PORTFOLIO_REVIEW", True),
            strategy=FeatureFlagStrategy.BOOLEAN,
            fallback_strategy=FallbackStrategy.DISABLE,
            description="Portfolio keep-or-sell review functionality",
        ),
        "quantitative_analysis": FeatureFlagConfig(
            name="quantitative_analysis",
            enabled=get_env_bool("FF_QUANTITATIVE_ANALYSIS", True),
            strategy=FeatureFlagStrategy.PERCENTAGE,
            rollout_percentage=get_env_float("FF_QUANTITATIVE_ANALYSIS_ROLLOUT", 0.0),
            fallback_strategy=FallbackStrategy.DISABLE,
            description="Quantitative analysis and backtesting framework",
        ),
        "quantitative_backtesting": FeatureFlagConfig(
            name="quantitative_backtesting",
            enabled=get_env_bool("FF_QUANTITATIVE_BACKTESTING", True),
            strategy=FeatureFlagStrategy.CIRCUIT_BREAKER,
            circuit_breaker_threshold=get_env_int("FF_BACKTEST_BREAKER_THRESHOLD", 3),
            circuit_breaker_timeout=get_env_int("FF_BACKTEST_BREAKER_TIMEOUT", 600),
            fallback_strategy=FallbackStrategy.DISABLE,
            description="Strategy backtesting with professional frameworks",
        ),
        "stock_screening": FeatureFlagConfig(
            name="stock_screening",
            enabled=get_env_bool("FF_STOCK_SCREENING", True),
            strategy=FeatureFlagStrategy.BOOLEAN,
            fallback_strategy=FallbackStrategy.REDUCED_FUNCTIONALITY,
            description="Fundamental analysis stock screening",
        ),
        "portfolio_optimization": FeatureFlagConfig(
            name="portfolio_optimization",
            enabled=get_env_bool("FF_PORTFOLIO_OPTIMIZATION", True),
            strategy=FeatureFlagStrategy.BOOLEAN,
            fallback_strategy=FallbackStrategy.DISABLE,
            description="Modern portfolio theory optimization",
        ),
        "derivatives_pricing": FeatureFlagConfig(
            name="derivatives_pricing",
            enabled=get_env_bool("FF_DERIVATIVES_PRICING", True),
            strategy=FeatureFlagStrategy.BOOLEAN,
            fallback_strategy=FallbackStrategy.DISABLE,
            description="QuantLib derivatives pricing capabilities",
        ),
        "portfolio_rebalancing": FeatureFlagConfig(
            name="portfolio_rebalancing",
            enabled=get_env_bool("FF_PORTFOLIO_REBALANCING", True),
            strategy=FeatureFlagStrategy.PERCENTAGE,
            rollout_percentage=get_env_float("FF_PORTFOLIO_REBALANCING_ROLLOUT", 0.0),
            fallback_strategy=FallbackStrategy.DISABLE,
            description="Portfolio rebalancing with optimization algorithms",
        ),
        "rebalancing_monitoring": FeatureFlagConfig(
            name="rebalancing_monitoring",
            enabled=get_env_bool("FF_REBALANCING_MONITORING", True),
            strategy=FeatureFlagStrategy.CIRCUIT_BREAKER,
            circuit_breaker_threshold=get_env_int("FF_REBALANCING_BREAKER_THRESHOLD", 3),
            circuit_breaker_timeout=get_env_int("FF_REBALANCING_BREAKER_TIMEOUT", 300),
            fallback_strategy=FallbackStrategy.DISABLE,
            description="Real-time portfolio monitoring and alerts",
        ),
        "rebalancing_api": FeatureFlagConfig(
            name="rebalancing_api",
            enabled=get_env_bool("FF_REBALANCING_API", True),
            strategy=FeatureFlagStrategy.BOOLEAN,
            fallback_strategy=FallbackStrategy.DISABLE,
            description="REST API endpoints for portfolio rebalancing",
        ),
        "monitoring": FeatureFlagConfig(
            name="monitoring",
            enabled=get_env_bool("FF_MONITORING", True),
            strategy=FeatureFlagStrategy.BOOLEAN,
            fallback_strategy=FallbackStrategy.DISABLE,
            description="Performance monitoring and metrics collection",
        ),
        "investment_discovery": FeatureFlagConfig(
            name="investment_discovery",
            enabled=get_env_bool("FF_INVESTMENT_DISCOVERY", True),
            strategy=FeatureFlagStrategy.PERCENTAGE,
            rollout_percentage=get_env_float("FF_INVESTMENT_DISCOVERY_ROLLOUT", 100.0),
            fallback_strategy=FallbackStrategy.DISABLE,
            description="A+ grade investment discovery agents for proactive opportunity identification",
        ),
        "newcomer_discovery": FeatureFlagConfig(
            name="newcomer_discovery",
            enabled=get_env_bool("FF_NEWCOMER_DISCOVERY", False),
            strategy=FeatureFlagStrategy.BOOLEAN,
            fallback_strategy=FallbackStrategy.DEFAULT_VALUES,
            description="Route stock/etf/crypto analyzers through NewcomerDiscoveryPipeline instead of legacy mocked data",
        ),
        "stock_analysis": FeatureFlagConfig(
            name="stock_analysis",
            enabled=get_env_bool("FF_STOCK_ANALYSIS", True),
            strategy=FeatureFlagStrategy.BOOLEAN,
            fallback_strategy=FallbackStrategy.DISABLE,
            description="Stock market analysis crew for equity research and recommendations",
        ),
        "etf_analysis": FeatureFlagConfig(
            name="etf_analysis",
            enabled=get_env_bool("FF_ETF_ANALYSIS", True),
            strategy=FeatureFlagStrategy.BOOLEAN,
            fallback_strategy=FallbackStrategy.DISABLE,
            description="ETF analysis crew for exchange-traded fund research and recommendations",
        ),
        "crypto_analysis": FeatureFlagConfig(
            name="crypto_analysis",
            enabled=get_env_bool("FF_CRYPTO_ANALYSIS", True),
            strategy=FeatureFlagStrategy.BOOLEAN,
            fallback_strategy=FallbackStrategy.DISABLE,
            description="Cryptocurrency analysis crew for digital asset research and recommendations",
        ),
        "perplexity_research": FeatureFlagConfig(
            name="perplexity_research",
            enabled=get_env_bool("FF_PERPLEXITY_RESEARCH", True),
            strategy=FeatureFlagStrategy.CIRCUIT_BREAKER,
            circuit_breaker_threshold=get_env_int("FF_PERPLEXITY_BREAKER_THRESHOLD", 5),
            circuit_breaker_timeout=get_env_int("FF_PERPLEXITY_BREAKER_TIMEOUT", 300),
            fallback_strategy=FallbackStrategy.DISABLE,
            description=("Perplexity Sonar Search integration for enhanced research capabilities across sentiment, technical, and fundamental analysis"),
        ),
    }
