"""
Circuit breaker implementation for database operations.

Prevents cascading failures by automatically disabling database operations
after repeated failures and attempting recovery after a timeout period.
"""

import logging
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failures detected, skip operations
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreaker:
    """
    Circuit breaker for database operations.

    Implements three-state logic (CLOSED, OPEN, HALF_OPEN) to protect
    against cascading failures from database issues.

    Attributes:
        failure_threshold: Number of consecutive failures before opening circuit
        recovery_timeout: Seconds to wait before attempting recovery
        failure_count: Current count of consecutive failures
        last_failure_time: Timestamp of most recent failure
        state: Current circuit breaker state

    """

    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_timeout: int = 300,
    ) -> None:
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit (default: 3)
            recovery_timeout: Seconds before recovery attempt (default: 300)

        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time: datetime | None = None
        self.state = CircuitState.CLOSED

    def is_open(self) -> bool:
        """
        Check if circuit breaker is open.

        Automatically attempts recovery if timeout has elapsed.

        Returns:
            True if circuit is open and operations should be skipped

        """
        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if self.last_failure_time:
                elapsed = (datetime.now() - self.last_failure_time).total_seconds()
                if elapsed >= self.recovery_timeout:
                    self.state = CircuitState.HALF_OPEN
                    logger.info("Circuit breaker entering half-open state for recovery test")
                    return False
            return True
        return False

    def record_success(self) -> None:
        """
        Record successful operation.

        Resets failure count and closes circuit if in half-open state.
        """
        if self.state == CircuitState.HALF_OPEN:
            logger.info("Circuit breaker closing after successful recovery test")
            self.state = CircuitState.CLOSED
        self.failure_count = 0

    def record_failure(self) -> None:
        """
        Record failed operation.

        Increments failure count and opens circuit if threshold is reached.
        """
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.failure_count >= self.failure_threshold:
            if self.state != CircuitState.OPEN:
                logger.warning(f"Circuit breaker opening after {self.failure_count} consecutive failures")
                self.state = CircuitState.OPEN
