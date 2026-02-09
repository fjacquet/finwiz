"""
Resilience configuration for FinWiz flow orchestrator.

Provides centralized configuration for retry logic, timeouts, checkpointing,
and parallelization settings.
"""

import os
from dataclasses import dataclass


@dataclass
class ResilienceConfig:
    """Configuration for flow resilience features."""

    # Retry configuration
    max_retries: int
    retry_base_delay: float
    retry_max_delay: float

    # Timeout configuration
    holding_timeout: int
    flow_timeout: int

    # Resume configuration
    auto_resume: bool
    state_max_age_hours: int

    # Parallelization configuration
    parallel_limit: int
    deep_analysis_parallel_limit: int

    # Circuit breaker configuration
    circuit_breaker_threshold: int
    circuit_breaker_recovery: float

    # State cleanup configuration
    cleanup_state_on_success: bool
    state_cleanup_max_age_days: int

    def validate(self) -> None:
        """
        Validate configuration values.

        Raises:
            ValueError: If configuration values are invalid

        """
        # Validate timeout relationship
        if self.holding_timeout >= self.flow_timeout:
            raise ValueError(f"holding_timeout ({self.holding_timeout}s) must be less than flow_timeout ({self.flow_timeout}s)")

        # Validate retry configuration
        if self.max_retries < 0:
            raise ValueError(f"max_retries must be non-negative, got {self.max_retries}")

        if self.retry_base_delay <= 0:
            raise ValueError(f"retry_base_delay must be positive, got {self.retry_base_delay}")

        if self.retry_max_delay <= self.retry_base_delay:
            raise ValueError(f"retry_max_delay ({self.retry_max_delay}) must be greater than retry_base_delay ({self.retry_base_delay})")

        # Validate state age
        if self.state_max_age_hours < 1:
            raise ValueError(f"state_max_age_hours must be at least 1, got {self.state_max_age_hours}")

        # Validate parallelization limits
        if self.parallel_limit < 1:
            raise ValueError(f"parallel_limit must be at least 1, got {self.parallel_limit}")

        if self.deep_analysis_parallel_limit < 1:
            raise ValueError(f"deep_analysis_parallel_limit must be at least 1, got {self.deep_analysis_parallel_limit}")

        # Validate circuit breaker configuration
        if self.circuit_breaker_threshold < 1:
            raise ValueError(f"circuit_breaker_threshold must be at least 1, got {self.circuit_breaker_threshold}")

        if self.circuit_breaker_recovery <= 0:
            raise ValueError(f"circuit_breaker_recovery must be positive, got {self.circuit_breaker_recovery}")

        # Validate state cleanup configuration
        if self.state_cleanup_max_age_days < 1:
            raise ValueError(f"state_cleanup_max_age_days must be at least 1, got {self.state_cleanup_max_age_days}")


# Singleton instance
_resilience_config: ResilienceConfig | None = None


def get_resilience_config() -> ResilienceConfig:
    """
    Get validated resilience configuration (singleton pattern).

    Loads configuration from environment variables with sensible defaults.
    Configuration is validated on first access and cached for subsequent calls.

    Environment Variables:
        FINWIZ_MAX_RETRIES: Maximum retry attempts (default: 3)
        FINWIZ_RETRY_BASE_DELAY: Base delay in seconds (default: 2)
        FINWIZ_RETRY_MAX_DELAY: Maximum delay in seconds (default: 60)
        FINWIZ_HOLDING_TIMEOUT: Per-holding timeout in seconds (default: 600)
        FINWIZ_FLOW_TIMEOUT: Global flow timeout in seconds (default: 7200)
        FINWIZ_CIRCUIT_BREAKER_THRESHOLD: Consecutive failures to open breaker (default: 5)
        FINWIZ_CIRCUIT_BREAKER_RECOVERY: Seconds before half-open retry (default: 120)
        FINWIZ_AUTO_RESUME: Auto-resume from checkpoint (default: false)
        FINWIZ_STATE_MAX_AGE_HOURS: Max checkpoint age in hours (default: 24)
        FINWIZ_PARALLEL_LIMIT: Concurrent portfolio holdings (default: 10)
        FINWIZ_DEEP_ANALYSIS_PARALLEL_LIMIT: Concurrent deep analysis (default: 3)
        FINWIZ_CLEANUP_STATE_ON_SUCCESS: Cleanup state on success (default: false)
        FINWIZ_STATE_CLEANUP_MAX_AGE_DAYS: Max state age for cleanup in days (default: 7)

    Backward Compatibility:
        Falls back to PORTFOLIO_PARALLEL_LIMIT and DEEP_ANALYSIS_PARALLEL_LIMIT
        if FINWIZ_ prefixed versions are not set.

    Returns:
        ResilienceConfig: Validated configuration instance

    Raises:
        ValueError: If configuration validation fails

    """
    global _resilience_config

    if _resilience_config is None:
        # Load retry configuration
        max_retries = int(os.getenv("FINWIZ_MAX_RETRIES", "3"))
        retry_base_delay = float(os.getenv("FINWIZ_RETRY_BASE_DELAY", "2"))
        retry_max_delay = float(os.getenv("FINWIZ_RETRY_MAX_DELAY", "60"))

        # Load timeout configuration
        holding_timeout = int(os.getenv("FINWIZ_HOLDING_TIMEOUT", "600"))
        flow_timeout = int(os.getenv("FINWIZ_FLOW_TIMEOUT", "7200"))

        # Load resume configuration
        auto_resume = os.getenv("FINWIZ_AUTO_RESUME", "false").lower() == "true"
        state_max_age_hours = int(os.getenv("FINWIZ_STATE_MAX_AGE_HOURS", "24"))

        # Load parallelization configuration with fallback to old variable names
        parallel_limit = int(os.getenv("FINWIZ_PARALLEL_LIMIT", os.getenv("PORTFOLIO_PARALLEL_LIMIT", "10")))
        deep_analysis_parallel_limit = int(
            os.getenv(
                "FINWIZ_DEEP_ANALYSIS_PARALLEL_LIMIT",
                os.getenv("DEEP_ANALYSIS_PARALLEL_LIMIT", "3"),
            )
        )

        # Load circuit breaker configuration
        circuit_breaker_threshold = int(os.getenv("FINWIZ_CIRCUIT_BREAKER_THRESHOLD", "5"))
        circuit_breaker_recovery = float(os.getenv("FINWIZ_CIRCUIT_BREAKER_RECOVERY", "120"))

        # Load state cleanup configuration
        cleanup_state_on_success = os.getenv("FINWIZ_CLEANUP_STATE_ON_SUCCESS", "false").lower() == "true"
        state_cleanup_max_age_days = int(os.getenv("FINWIZ_STATE_CLEANUP_MAX_AGE_DAYS", "7"))

        # Create and validate configuration
        _resilience_config = ResilienceConfig(
            max_retries=max_retries,
            retry_base_delay=retry_base_delay,
            retry_max_delay=retry_max_delay,
            holding_timeout=holding_timeout,
            flow_timeout=flow_timeout,
            auto_resume=auto_resume,
            state_max_age_hours=state_max_age_hours,
            parallel_limit=parallel_limit,
            deep_analysis_parallel_limit=deep_analysis_parallel_limit,
            circuit_breaker_threshold=circuit_breaker_threshold,
            circuit_breaker_recovery=circuit_breaker_recovery,
            cleanup_state_on_success=cleanup_state_on_success,
            state_cleanup_max_age_days=state_cleanup_max_age_days,
        )

        # Validate configuration
        _resilience_config.validate()

    return _resilience_config


def reset_resilience_config() -> None:
    """
    Reset the singleton configuration instance.

    Useful for testing to force reloading configuration from environment variables.
    """
    global _resilience_config
    _resilience_config = None
