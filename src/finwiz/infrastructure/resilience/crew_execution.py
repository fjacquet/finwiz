"""Crew execution wrapper with timeout and circuit breaker protection.

Wraps all crew.kickoff() calls with:
- asyncio.wait_for() timeout (configurable via FINWIZ_HOLDING_TIMEOUT)
- Circuit breaker that opens after FAILURE_THRESHOLD consecutive failures
- ThreadPoolExecutor wrapping since crew.kickoff() is synchronous
"""

import asyncio
import os
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from finwiz.tools.logger import get_logger

logger = get_logger(__name__)

# Configuration
CREW_TIMEOUT = int(os.getenv("FINWIZ_HOLDING_TIMEOUT", "300"))
FAILURE_THRESHOLD = 3
RECOVERY_TIMEOUT = 60.0

# Module-level state
_executor = ThreadPoolExecutor(max_workers=4)
_crew_failures: dict[str, int] = {}
_crew_circuit_open: dict[str, float] = {}


class CircuitBreakerOpenError(RuntimeError):
    """Raised when a crew's circuit breaker is open due to repeated failures."""


async def execute_crew_with_timeout(
    crew_name: str,
    crew_instance: Any,
    inputs: dict[str, Any],
    timeout: int | None = None,
) -> Any:
    """Execute a crew with timeout and circuit breaker protection.

    crew.kickoff() is SYNCHRONOUS, so it is wrapped in run_in_executor()
    to prevent blocking the event loop.

    Args:
        crew_name: Identifier for circuit breaker tracking (e.g. "stock", "etf")
        crew_instance: CrewAI crew instance with a kickoff() method
        inputs: Dict of inputs to pass to crew.kickoff(inputs=...)
        timeout: Per-crew timeout in seconds (default: CREW_TIMEOUT env var)

    Returns:
        The crew result from kickoff()

    Raises:
        CircuitBreakerOpenError: If the crew's circuit breaker is open
        TimeoutError: If the crew exceeds the timeout
        Exception: Any exception from crew.kickoff() is re-raised after tracking

    """
    effective_timeout = timeout if timeout is not None else CREW_TIMEOUT

    # --- Circuit breaker check ---
    if crew_name in _crew_circuit_open:
        elapsed = time.time() - _crew_circuit_open[crew_name]
        if elapsed < RECOVERY_TIMEOUT:
            logger.warning(f"Circuit breaker OPEN for {crew_name} ({elapsed:.0f}s < {RECOVERY_TIMEOUT}s)")
            raise CircuitBreakerOpenError(f"Circuit breaker open for {crew_name}")
        # Half-open: recovery timeout passed, allow retry
        logger.info(f"Circuit breaker half-open for {crew_name}, allowing retry")
        del _crew_circuit_open[crew_name]

    # --- Execute with timeout ---
    loop = asyncio.get_running_loop()
    try:
        result = await asyncio.wait_for(
            loop.run_in_executor(_executor, lambda: crew_instance.kickoff(inputs=inputs)),
            timeout=effective_timeout,
        )
        # Success: reset failure counter
        _crew_failures[crew_name] = 0
        logger.info(f"Crew {crew_name} completed successfully")
        return result

    except (TimeoutError, Exception) as exc:
        # Track failure
        _crew_failures[crew_name] = _crew_failures.get(crew_name, 0) + 1
        failure_count = _crew_failures[crew_name]
        logger.warning(f"Crew {crew_name} failed ({failure_count}/{FAILURE_THRESHOLD}): {exc}")

        # Open circuit breaker if threshold reached
        if failure_count >= FAILURE_THRESHOLD:
            _crew_circuit_open[crew_name] = time.time()
            logger.error(f"Circuit breaker OPEN for {crew_name} after {failure_count} consecutive failures")

        raise


def reset_circuit_breakers() -> None:
    """Reset all circuit breaker state. Used for testing."""
    _crew_failures.clear()
    _crew_circuit_open.clear()
    logger.info("Circuit breakers reset")
