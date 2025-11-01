"""
Circuit breaker implementation for database operations.

Prevents cascading failures by automatically disabling database operations
after repeated failures and attempting recovery after a timeout period.
Includes state change monitoring and logging.
"""

import logging
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from finwiz.supabase.utils.monitoring import CircuitBreakerMonitor

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
        monitor: "CircuitBreakerMonitor | None" = None,
    ) -> None:
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit (default: 3)
            recovery_timeout: Seconds before recovery attempt (default: 300)
            monitor: Optional CircuitBreakerMonitor for state change tracking

        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time: datetime | None = None
        self.state = CircuitState.CLOSED
        self.monitor = monitor

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
                    self._transition_to_half_open()
                    return False
            return True
        return False

    def should_allow_request(self) -> bool:
        """
        Check if circuit breaker should allow a request.

        This is the main method to check before attempting an operation.
        Handles state transitions automatically.

        Returns:
            True if request should be allowed, False otherwise

        """
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.HALF_OPEN:
            # Allow one request to test recovery
            return True

        if self.state == CircuitState.OPEN:
            # Check if we should transition to half-open
            if self.last_failure_time:
                elapsed = (datetime.now() - self.last_failure_time).total_seconds()
                if elapsed >= self.recovery_timeout:
                    self._transition_to_half_open()
                    return True
            return False

        return False

    def _transition_to_half_open(self) -> None:
        """
        Transition circuit breaker to half-open state.

        Called when recovery timeout has elapsed and we want to test
        if the service has recovered.
        """
        old_state = self.state
        self.state = CircuitState.HALF_OPEN
        logger.info("🔄 Circuit breaker half-open - testing Supabase")

        # Record state change in monitor
        if self.monitor:
            self.monitor.record_state_change(old_state, self.state)

    def _transition_to_open(self) -> None:
        """
        Transition circuit breaker to open state.

        Called when failure threshold is reached.
        """
        old_state = self.state
        self.state = CircuitState.OPEN
        logger.warning(
            f"⚠️ Circuit breaker opened after {self.failure_count} failures"
        )
        logger.warning("⚠️ Supabase operations suspended - caching disabled")

        # Record state change in monitor
        if self.monitor:
            self.monitor.record_state_change(old_state, self.state)

    def _transition_to_closed(self) -> None:
        """
        Transition circuit breaker to closed state.

        Called when a successful operation occurs in half-open state.
        """
        old_state = self.state
        self.state = CircuitState.CLOSED
        logger.info("✅ Circuit breaker closed - Supabase recovered")

        # Record state change in monitor
        if self.monitor:
            self.monitor.record_state_change(old_state, self.state)

    def record_success(self) -> None:
        """
        Record successful operation.

        Resets failure count and closes circuit if in half-open state.
        """
        if self.state == CircuitState.HALF_OPEN:
            self._transition_to_closed()
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
                self._transition_to_open()
