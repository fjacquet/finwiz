"""
Metrics tracking for Supabase client operations.

Provides response time tracking, success/failure counting,
and metrics logging for monitoring database operations.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ClientMetrics:
    """
    Tracks operation metrics for Supabase client.

    Attributes:
        total_operations: Total number of operations
        successful_operations: Number of successful operations
        failed_operations: Number of failed operations
        timeout_count: Number of operations that timed out
        response_times: Rolling window of recent response times (ms)
        max_response_times: Maximum response times to keep

    """

    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    timeout_count: int = 0
    response_times: list[float] = field(default_factory=list)
    max_response_times: int = 100

    def record_response_time(self, response_time_ms: float) -> None:
        """
        Record response time for metrics calculation.

        Maintains a rolling window of recent response times for calculating
        average response time.

        Args:
            response_time_ms: Response time in milliseconds

        """
        self.response_times.append(response_time_ms)
        # Keep only the most recent response times
        if len(self.response_times) > self.max_response_times:
            self.response_times.pop(0)

    def record_success(self) -> None:
        """Record a successful operation."""
        self.total_operations += 1
        self.successful_operations += 1

    def record_failure(self) -> None:
        """Record a failed operation."""
        self.total_operations += 1
        self.failed_operations += 1

    def record_timeout(self) -> None:
        """Record a timed out operation."""
        self.total_operations += 1
        self.failed_operations += 1
        self.timeout_count += 1

    def get_success_rate(self) -> float:
        """
        Calculate operation success rate.

        Returns:
            Success rate as float between 0.0 and 1.0

        """
        if self.total_operations == 0:
            return 0.0
        return self.successful_operations / self.total_operations

    def get_avg_response_time(self) -> float:
        """
        Calculate average response time.

        Returns:
            Average response time in milliseconds

        """
        if not self.response_times:
            return 0.0
        return sum(self.response_times) / len(self.response_times)

    def reset(self) -> None:
        """
        Reset operation metrics.

        Useful for testing or periodic metric resets.
        """
        self.total_operations = 0
        self.successful_operations = 0
        self.failed_operations = 0
        self.timeout_count = 0
        self.response_times = []
        logger.debug("Supabase client metrics reset")

    def should_log(self, interval: int = 100) -> bool:
        """
        Check if metrics should be logged (every N operations).

        Args:
            interval: Number of operations between logs

        Returns:
            True if metrics should be logged, False otherwise

        """
        return self.total_operations > 0 and self.total_operations % interval == 0

    def log(self, is_available: bool, circuit_breaker_open: bool) -> None:
        """
        Log current metrics at INFO level.

        Args:
            is_available: Whether Supabase is currently available
            circuit_breaker_open: Whether circuit breaker is open

        """
        logger.info(
            f"Supabase Metrics: "
            f"Available={is_available}, "
            f"Success Rate={self.get_success_rate():.1%}, "
            f"Avg Response Time={self.get_avg_response_time():.1f}ms, "
            f"Circuit Breaker={'OPEN' if circuit_breaker_open else 'CLOSED'}, "
            f"Total Ops={self.total_operations}, "
            f"Successful={self.successful_operations}, "
            f"Failed={self.failed_operations}, "
            f"Timeouts={self.timeout_count}"
        )

    def to_health_status_dict(self) -> dict:
        """
        Convert metrics to a dictionary for SupabaseHealthStatus.

        Returns:
            Dictionary with metrics values

        """
        return {
            "success_rate": self.get_success_rate(),
            "avg_response_time": self.get_avg_response_time(),
            "timeout_count": self.timeout_count,
            "total_operations": self.total_operations,
            "successful_operations": self.successful_operations,
            "failed_operations": self.failed_operations,
            "last_check_timestamp": datetime.now(),
        }
