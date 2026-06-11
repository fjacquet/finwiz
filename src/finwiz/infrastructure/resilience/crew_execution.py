"""Crew execution wrapper with timeout and circuit breaker protection.

Wraps all crew.kickoff() calls with:
- asyncio.wait_for() timeout (configurable via FINWIZ_CREW_TIMEOUT)
- Circuit breaker that opens after FAILURE_THRESHOLD consecutive failures
- ThreadPoolExecutor wrapping since crew.kickoff() is synchronous
"""

import asyncio
import atexit
import os
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from pydantic import ValidationError

from finwiz.tools.logger import get_logger

logger = get_logger(__name__)

# Per-crew-attempt timeout — loaded from FINWIZ_CREW_TIMEOUT.
#
# History:
#   2026-04-29: Default bumped 600 → 900 s after DELL succeeded at 1488 s
#               (asyncio.wait_for cannot interrupt sync crew.kickoff() inside a
#               ThreadPoolExecutor; long-tail successes need budget).
#   2026-06-11: Split from FINWIZ_HOLDING_TIMEOUT into its own var so the
#               per-holding outer timeout can guarantee retry headroom.  The
#               holding budget (FINWIZ_HOLDING_TIMEOUT, default 900 s) is now
#               auto-raised to CREW_TIMEOUT + 300 s when set below that floor,
#               giving the @stage retry at least 300 s to complete after an
#               inner-attempt timeout fires.  Both vars are independent:
#                 FINWIZ_CREW_TIMEOUT  — budget per crew attempt (default 600 s)
#                 FINWIZ_HOLDING_TIMEOUT — outer per-holding budget (default 900 s)
CREW_TIMEOUT = int(os.getenv("FINWIZ_CREW_TIMEOUT", "600"))


def _get_failure_threshold() -> int:
    from finwiz.config.resilience_config import get_resilience_config

    return get_resilience_config().circuit_breaker_threshold


def _get_recovery_timeout() -> float:
    from finwiz.config.resilience_config import get_resilience_config

    return get_resilience_config().circuit_breaker_recovery


# Module-level state
_executor = ThreadPoolExecutor(max_workers=4)
_crew_failures: dict[str, int] = {}
_crew_circuit_open: dict[str, float] = {}


def shutdown_executor() -> None:
    """Shut down the thread pool executor so the process can exit cleanly."""
    _executor.shutdown(wait=False, cancel_futures=True)
    logger.debug("Crew executor shut down")


atexit.register(shutdown_executor)


class CircuitBreakerOpenError(RuntimeError):
    """Raised when a crew's circuit breaker is open due to repeated failures."""


def _record_crew_usage(crew_name: str, result: Any) -> None:
    """Record this kickoff's CrewAI token usage into the cost monitor.

    Source of truth for the (honest) end-of-run cost summary: CrewAI's
    ``CrewOutput.token_usage`` is populated directly and survives the thread
    boundaries that prevent the litellm callback from firing. Best-effort —
    never let cost accounting break crew execution.
    """
    try:
        token_usage = getattr(result, "token_usage", None)
        if token_usage is None:
            return
        from finwiz.crews.helpers.llm_config import get_crew_model_string
        from finwiz.infrastructure.monitoring.litellm_callback import get_token_monitor

        monitor = get_token_monitor()
        if monitor is not None:
            monitor.record_usage(crew_name, token_usage, model=get_crew_model_string())
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug(f"Cost tracking skipped for {crew_name}: {exc}")


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

    recovery_timeout = _get_recovery_timeout()
    failure_threshold = _get_failure_threshold()

    # --- Circuit breaker check ---
    if crew_name in _crew_circuit_open:
        elapsed = time.time() - _crew_circuit_open[crew_name]
        if elapsed < recovery_timeout:
            logger.warning(f"Circuit breaker OPEN for {crew_name} ({elapsed:.0f}s < {recovery_timeout}s)")
            raise CircuitBreakerOpenError(f"Circuit breaker open for {crew_name}")
        # Half-open: recovery timeout passed, allow retry
        logger.info(f"Circuit breaker half-open for {crew_name}, allowing retry")
        del _crew_circuit_open[crew_name]

    # --- Execute with timeout ---
    from finwiz.infrastructure.monitoring.litellm_callback import clear_crew_context, set_crew_context

    loop = asyncio.get_running_loop()
    try:
        set_crew_context(crew_name)
        result = await asyncio.wait_for(
            loop.run_in_executor(_executor, lambda: crew_instance.kickoff(inputs=inputs)),
            timeout=effective_timeout,
        )
        # Success: reset failure counter
        _crew_failures[crew_name] = 0
        logger.info(f"Crew {crew_name} completed successfully")
        _record_crew_usage(crew_name, result)
        return result

    except ValidationError:
        # Deterministic schema failure — backoff doesn't help (the LLM's next
        # output will fail the same validator). Re-raise without incrementing
        # the breaker counter so a thrashing schema mismatch doesn't trip the
        # breaker on healthy upstream providers. The 2026-04-28 ETF cascade
        # was driven by exactly this confounder.
        raise

    except (TimeoutError, Exception) as exc:
        # Track failure
        _crew_failures[crew_name] = _crew_failures.get(crew_name, 0) + 1
        failure_count = _crew_failures[crew_name]
        logger.warning(f"Crew {crew_name} failed ({failure_count}/{failure_threshold}): {exc}")

        # Open circuit breaker if threshold reached
        if failure_count >= failure_threshold:
            _crew_circuit_open[crew_name] = time.time()
            logger.error(f"Circuit breaker OPEN for {crew_name} after {failure_count} consecutive failures")

        raise

    finally:
        clear_crew_context()


def reset_circuit_breakers() -> None:
    """Reset all circuit breaker state. Used for testing."""
    _crew_failures.clear()
    _crew_circuit_open.clear()
    logger.info("Circuit breakers reset")
