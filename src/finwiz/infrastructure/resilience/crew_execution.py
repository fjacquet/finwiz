"""Crew execution wrapper with timeout and circuit breaker protection.

Wraps all crew.kickoff() calls with:
- asyncio.wait_for() timeout (configurable via FINWIZ_CREW_TIMEOUT)
- Circuit breaker that opens after FAILURE_THRESHOLD consecutive non-timeout
  failures, OR after TIMEOUT_FAILURE_THRESHOLD consecutive timeouts (separate
  counters -- see the module note below)
- ThreadPoolExecutor wrapping since crew.kickoff() is synchronous
"""

import asyncio
import atexit
import os
import threading
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


def _get_timeout_failure_threshold() -> int:
    """Consecutive TIMEOUTS (own counter, see module note) before the breaker opens.

    A single slow ticker must never trip the breaker (2026-08-16 cascade,
    Task 1's fix -- kept here). But a provider that hangs on *every* request
    must still be detected: excluding timeouts from the failure counter
    entirely means the breaker never opens for a hung upstream, and all 64
    holdings each burn a full CREW_TIMEOUT (default 600s) before giving up.

    Default 15, three times circuit_breaker_threshold's default of 5:
    high enough that the common case -- a couple of genuinely slow tickers
    among 64 -- never trips it, low enough to catch a systemic hang well
    before the whole batch has each independently paid the full timeout.
    """
    return int(os.getenv("FINWIZ_CIRCUIT_BREAKER_TIMEOUT_THRESHOLD", "15"))


# Module-level state
_executor = ThreadPoolExecutor(max_workers=4)
_crew_failures: dict[str, int] = {}
_crew_timeout_failures: dict[str, int] = {}
_crew_circuit_open: dict[str, float] = {}

# Guards the three dicts above. threading.Lock, not asyncio.Lock: every call
# site of execute_crew_with_timeout (qualify.py, crew_factory.py,
# flows/utils.py) runs each attempt via a *fresh* asyncio.run(...) -- either
# directly or via pool.submit(asyncio.run, ...) -- so concurrent holdings
# execute on independent OS threads, each with its own throwaway event loop.
# An asyncio.Lock is bound to the loop that created it and cannot be awaited
# safely from a different loop/thread; a threading.Lock has no such
# restriction. It is only ever held around plain dict reads/writes, never
# across an `await`, so it cannot serialize the cooldown waits below.
#
# On a shared wait primitive (e.g. asyncio.Event/Condition or a
# threading.Event all waiters block on): deliberately not used. Every
# concurrent waiter for the same crew_name computes
# `remaining = recovery_timeout - (now - open_ts)` from the SAME open_ts, so
# each one's wake target is `open_ts + recovery_timeout` regardless of when
# it snapshots -- they already converge on the identical wall-clock instant
# and already run in parallel (independent OS threads, see above). A shared
# primitive would add cross-loop plumbing (a plain asyncio.Event can't be
# awaited from a different thread's loop; a threading.Event would need
# run_in_executor to avoid blocking) for zero behavioural change. The actual
# defect in "every waiter sleeps independently" was never the independent
# sleep itself -- it was that an incorrectly-scoped lock could accidentally
# serialize them, which the never-across-an-await rule above already
# forecloses.
_state_lock = threading.Lock()


def shutdown_executor() -> None:
    """Shut down the thread pool executor so the process can exit cleanly."""
    _executor.shutdown(wait=False, cancel_futures=True)
    logger.debug("Crew executor shut down")


atexit.register(shutdown_executor)


async def _wait_out_open_breaker(crew_name: str, recovery_timeout: float) -> None:
    """If the breaker is open for `crew_name`, wait out the cooldown, then half-open.

    Split out of execute_crew_with_timeout to keep that function's cyclomatic
    complexity in check; see its docstring Note and the _state_lock comment
    above for the concurrency reasoning this implements.
    """
    with _state_lock:
        open_ts = _crew_circuit_open.get(crew_name)

    if open_ts is None:
        return

    elapsed = time.time() - open_ts
    remaining = recovery_timeout - elapsed
    if remaining > 0:
        # Wait the cooldown out rather than failing instantly. Holdings run
        # concurrently, so fail-fast here rejects every queued holding in the
        # same instant — the 31-holding cascade of 2026-08-16. Every
        # concurrent waiter for this crew_name already runs on its own OS
        # thread (see the _state_lock comment above) and computes the same
        # wake target (open_ts + recovery_timeout) from the same open_ts, so
        # independent sleeps here already run in parallel and already
        # converge on the same instant — no shared wait primitive changes
        # that; see the _state_lock comment for why one isn't used.
        logger.warning(f"Circuit breaker OPEN for {crew_name}; waiting {remaining:.0f}s for cooldown")
        await asyncio.sleep(remaining)

    with _state_lock:
        # Only clear the cooldown we actually waited out. `remaining` was
        # computed from a snapshot taken before the wait; a concurrent
        # holding may have failed again *during* our wait and opened a NEW
        # cooldown for this crew_name. Popping unconditionally here would
        # discard that fresh cooldown out from under it.
        if _crew_circuit_open.get(crew_name) == open_ts:
            _crew_circuit_open.pop(crew_name, None)
            # Reset both counters on the half-open transition. Without this,
            # the counter sits at the threshold forever, so the very next
            # failure (threshold + 1 >= threshold) reopens the breaker
            # instantly — a live-but-flaky provider becomes a loop where
            # every holding pays a full cooldown for one failure.
            _crew_failures[crew_name] = 0
            _crew_timeout_failures[crew_name] = 0
            logger.info(f"Circuit breaker half-open for {crew_name}, allowing retry")
        else:
            logger.info(f"Circuit breaker state for {crew_name} changed during cooldown wait; not clearing it")


def _record_timeout_and_maybe_open(crew_name: str, timeout_failure_threshold: int) -> tuple[int, bool]:
    """Increment the timeout counter; open the breaker if its own threshold is hit.

    Timeouts get a counter separate from _crew_failures/failure_threshold: a
    timeout is a per-holding event, not necessarily an upstream failure, so
    counting it against the failure threshold opens the breaker after just a
    few slow tickers among 64 healthy ones. But excluding timeouts entirely
    (the previous fix) means a provider that hangs on *every* request never
    trips the breaker, and every holding burns the full CREW_TIMEOUT before
    giving up. See _get_timeout_failure_threshold for the threshold choice.
    """
    with _state_lock:
        _crew_timeout_failures[crew_name] = _crew_timeout_failures.get(crew_name, 0) + 1
        timeout_count = _crew_timeout_failures[crew_name]
        opened = timeout_count >= timeout_failure_threshold
        if opened:
            _crew_circuit_open[crew_name] = time.time()
    return timeout_count, opened


def _record_failure_and_maybe_open(crew_name: str, failure_threshold: int) -> tuple[int, bool]:
    """Increment the non-timeout failure counter; open the breaker if threshold is hit."""
    with _state_lock:
        _crew_failures[crew_name] = _crew_failures.get(crew_name, 0) + 1
        failure_count = _crew_failures[crew_name]
        opened = failure_count >= failure_threshold
        if opened:
            _crew_circuit_open[crew_name] = time.time()
    return failure_count, opened


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
        TimeoutError: If the crew exceeds the timeout
        Exception: Any exception from crew.kickoff() is re-raised after tracking

    Note:
        An open circuit breaker no longer fails instantly. Holdings run
        concurrently across independent OS threads (each call site --
        qualify.py, crew_factory.py, flows/utils.py -- invokes this function
        via its own fresh asyncio.run()), so an instant failure here rejects
        every queued holding in the same moment (the 31-holding cascade of
        2026-08-16). Instead, this call waits out the remaining recovery
        cooldown and then retries — a holding pays for the breaker with time,
        not by losing its in-flight analysis.

        This wait is NOT bounded by FINWIZ_HOLDING_TIMEOUT. `qualify` is a
        sync stage invoked at the orchestrator level via
        `asyncio.wait_for(loop.run_in_executor(executor, sync_fn), timeout=...)`.
        Once that executor thread has started running, `run_in_executor`'s
        future cannot be cancelled: when the outer holding timeout fires, this
        coroutine's underlying thread keeps running regardless, finishes its
        cooldown wait, and calls crew.kickoff() anyway — orphaned, after the
        holding has already been reported pending by the orchestrator. That
        orphaned-thread problem is a known, separate defect and is not fixed
        here.

        CircuitBreakerOpenError has been removed: nothing raised it any more
        once fail-fast was replaced by wait-then-retry.

    """
    effective_timeout = timeout if timeout is not None else CREW_TIMEOUT

    failure_threshold = _get_failure_threshold()
    timeout_failure_threshold = _get_timeout_failure_threshold()

    await _wait_out_open_breaker(crew_name, _get_recovery_timeout())

    # --- Execute with timeout ---
    from finwiz.infrastructure.monitoring.litellm_callback import clear_crew_context, set_crew_context

    loop = asyncio.get_running_loop()
    try:
        set_crew_context(crew_name)
        result = await asyncio.wait_for(
            loop.run_in_executor(_executor, lambda: crew_instance.kickoff(inputs=inputs)),
            timeout=effective_timeout,
        )
        # Success: reset both failure counters
        with _state_lock:
            _crew_failures[crew_name] = 0
            _crew_timeout_failures[crew_name] = 0
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

    except TimeoutError:
        timeout_count, opened = _record_timeout_and_maybe_open(crew_name, timeout_failure_threshold)
        logger.warning(f"Crew {crew_name} timed out after {effective_timeout}s ({timeout_count}/{timeout_failure_threshold} timeouts; non-timeout failure counter unchanged)")
        if opened:
            logger.error(f"Circuit breaker OPEN for {crew_name} after {timeout_count} consecutive timeouts (provider appears hung)")
        raise

    except Exception as exc:
        failure_count, opened = _record_failure_and_maybe_open(crew_name, failure_threshold)
        # {exc!r} not {exc}: TimeoutError() stringifies to empty, which is why the
        # 2026-08-16 run logged "Crew deep_analysis_stock failed (5/5):" with no
        # reason. repr always shows the type. (This branch no longer sees
        # TimeoutError, but keep repr for any other exception with an empty str().)
        logger.warning(f"Crew {crew_name} failed ({failure_count}/{failure_threshold}): {exc!r}")
        if opened:
            logger.error(f"Circuit breaker OPEN for {crew_name} after {failure_count} consecutive failures")

        raise

    finally:
        clear_crew_context()


def reset_circuit_breakers() -> None:
    """Reset all circuit breaker state. Used for testing."""
    with _state_lock:
        _crew_failures.clear()
        _crew_timeout_failures.clear()
        _crew_circuit_open.clear()
    logger.info("Circuit breakers reset")
