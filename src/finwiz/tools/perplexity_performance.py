"""
Performance monitoring utilities for Perplexity integration.

This module contains performance monitoring and metrics collection
for Perplexity API operations with baseline comparison.
"""

import time
from typing import Any

from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class PerplexityPerformanceMonitor:
    """Performance monitoring for Perplexity operations with baseline comparison."""

    # Baseline response time in milliseconds (configurable)
    BASELINE_RESPONSE_TIME_MS = 1000  # 1 second baseline
    MAX_ACCEPTABLE_RESPONSE_TIME_MS = BASELINE_RESPONSE_TIME_MS * 2  # 2x baseline requirement

    @staticmethod
    def start_operation_timer() -> float:
        """Start timing an operation and return start timestamp."""
        return time.time()

    @staticmethod
    def calculate_operation_time(start_time: float) -> int:
        """Calculate operation time in milliseconds."""
        return int((time.time() - start_time) * 1000)

    @staticmethod
    def log_performance_metrics(
        ticker: str, analysis_type: str, latency_ms: int, result_count: int, baseline_comparison: dict[str, Any] | None = None
    ) -> None:
        """Log performance metrics with baseline comparison."""
        performance_ratio = latency_ms / PerplexityPerformanceMonitor.BASELINE_RESPONSE_TIME_MS
        meets_requirement = latency_ms <= PerplexityPerformanceMonitor.MAX_ACCEPTABLE_RESPONSE_TIME_MS

        extra_data = {
            "operation": "perplexity_performance_metrics",
            "ticker": ticker,
            "analysis_type": analysis_type,
            "latency_ms": latency_ms,
            "result_count": result_count,
            "baseline_ms": PerplexityPerformanceMonitor.BASELINE_RESPONSE_TIME_MS,
            "performance_ratio": round(performance_ratio, 2),
            "meets_2x_requirement": meets_requirement,
            "timestamp": time.time(),
        }

        if baseline_comparison:
            extra_data.update(baseline_comparison)

        log_level = "info" if meets_requirement else "warning"
        message = f"Perplexity performance: {latency_ms}ms ({performance_ratio:.2f}x baseline)"

        if log_level == "info":
            logger.info(message, extra=extra_data)
        else:
            logger.warning(f"{message} - EXCEEDS 2x BASELINE REQUIREMENT", extra=extra_data)

    @staticmethod
    def validate_response_time_requirement(latency_ms: int) -> bool:
        """Validate that response time meets ≤2× baseline requirement."""
        return latency_ms <= PerplexityPerformanceMonitor.MAX_ACCEPTABLE_RESPONSE_TIME_MS

    @staticmethod
    def get_performance_summary(response_times: list[int]) -> dict[str, Any]:
        """Calculate performance summary statistics."""
        if not response_times:
            return {}

        avg_time = sum(response_times) / len(response_times)
        min_time = min(response_times)
        max_time = max(response_times)

        # Calculate percentiles
        sorted_times = sorted(response_times)
        n = len(sorted_times)
        p50 = sorted_times[n // 2]
        p95 = sorted_times[int(n * 0.95)] if n > 1 else sorted_times[0]
        p99 = sorted_times[int(n * 0.99)] if n > 1 else sorted_times[0]

        # Check compliance with requirements
        compliant_responses = sum(1 for t in response_times if t <= PerplexityPerformanceMonitor.MAX_ACCEPTABLE_RESPONSE_TIME_MS)
        compliance_rate = compliant_responses / len(response_times)

        return {
            "total_requests": len(response_times),
            "avg_response_time_ms": round(avg_time, 2),
            "min_response_time_ms": min_time,
            "max_response_time_ms": max_time,
            "p50_response_time_ms": p50,
            "p95_response_time_ms": p95,
            "p99_response_time_ms": p99,
            "baseline_ms": PerplexityPerformanceMonitor.BASELINE_RESPONSE_TIME_MS,
            "max_acceptable_ms": PerplexityPerformanceMonitor.MAX_ACCEPTABLE_RESPONSE_TIME_MS,
            "compliance_rate": round(compliance_rate, 4),
            "avg_performance_ratio": round(avg_time / PerplexityPerformanceMonitor.BASELINE_RESPONSE_TIME_MS, 2),
        }


class PerplexityFeatureFlagTracker:
    """Tracks feature flag success/failure for Perplexity operations with circuit breaker integration."""

    def __init__(self, failure_threshold: int = 5, recovery_threshold: int = 3):
        """
        Initialize feature flag tracker.

        Args:
            failure_threshold: Number of consecutive failures before disabling feature
            recovery_threshold: Number of consecutive successes needed to re-enable feature

        """
        self.failure_threshold = failure_threshold
        self.recovery_threshold = recovery_threshold
        self.consecutive_failures = 0
        self.consecutive_successes = 0
        self.feature_enabled = True
        self.last_failure_time = None
        self.total_requests = 0
        self.total_failures = 0

    def record_success(self) -> None:
        """Record a successful operation."""
        self.total_requests += 1
        self.consecutive_failures = 0
        self.consecutive_successes += 1

        # Re-enable feature if we have enough consecutive successes
        if not self.feature_enabled and self.consecutive_successes >= self.recovery_threshold:
            self.feature_enabled = True
            logger.info(
                f"Perplexity feature re-enabled after {self.consecutive_successes} consecutive successes",
                extra={
                    "operation": "perplexity_feature_recovery",
                    "consecutive_successes": self.consecutive_successes,
                    "recovery_threshold": self.recovery_threshold,
                },
            )

    def record_failure(self) -> None:
        """Record a failed operation."""
        self.total_requests += 1
        self.total_failures += 1
        self.consecutive_successes = 0
        self.consecutive_failures += 1
        self.last_failure_time = time.time()

        # Disable feature if we have too many consecutive failures
        if self.feature_enabled and self.consecutive_failures >= self.failure_threshold:
            self.feature_enabled = False
            logger.warning(
                f"Perplexity feature disabled after {self.consecutive_failures} consecutive failures",
                extra={
                    "operation": "perplexity_feature_disabled",
                    "consecutive_failures": self.consecutive_failures,
                    "failure_threshold": self.failure_threshold,
                    "failure_rate": self.get_failure_rate(),
                },
            )

    def is_feature_enabled(self) -> bool:
        """Check if the feature is currently enabled."""
        return self.feature_enabled

    def get_failure_rate(self) -> float:
        """Get the current failure rate."""
        if self.total_requests == 0:
            return 0.0
        return self.total_failures / self.total_requests

    def get_status_summary(self) -> dict[str, Any]:
        """Get a summary of the current feature flag status."""
        return {
            "feature_enabled": self.feature_enabled,
            "consecutive_failures": self.consecutive_failures,
            "consecutive_successes": self.consecutive_successes,
            "total_requests": self.total_requests,
            "total_failures": self.total_failures,
            "failure_rate": round(self.get_failure_rate(), 4),
            "failure_threshold": self.failure_threshold,
            "recovery_threshold": self.recovery_threshold,
            "last_failure_time": self.last_failure_time,
        }
