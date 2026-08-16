"""Retry-with-backoff and concurrency control for Perplexity structured calls.

The vendored ``perplexity_structured`` client swallows every failure *except a
missing API key* into a bare ``None`` return (see
``crewai_custom_tools/tools/web/perplexity_structured.py``), so a 429, a
timeout, and an unparseable body are all indistinguishable from each other. A
missing key is different: ``require_api_key`` raises ``ValueError`` before the
client's own ``try``/``except`` even starts, so that one failure mode escapes
as an exception rather than a ``None``. This wrapper pre-empts that specific,
known case up front via ``_has_api_key()`` (checking the same two env-var
names), so a misconfiguration fails fast instead of burning the whole attempt
budget -- and also catches any other exception the call might raise (e.g. if
the vendored client's accepted key names or internal handling ever changes),
treating it exactly like a ``None`` result. The whole call is therefore
retried **by outcome**, not by status code, delegating the actual backoff math
to ``PerplexityFallbackManager.calculate_backoff_delay`` -- the
exponential-backoff-with-jitter helper already used by
``perplexity_analysis_integration.py`` -- instead of reimplementing it.
"""

from __future__ import annotations

import asyncio
import os
import threading
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from crewai_custom_tools import perplexity_structured
from pydantic import BaseModel

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

from finwiz.tools.logger import get_logger
from finwiz.tools.perplexity_errors import PerplexityFallbackManager

logger = get_logger(__name__)

# Perplexity rate-limits aggressively; a full portfolio fans out far wider than
# the account allows. This caps in-flight requests process-wide.
#
# Floored at 1: an unfloored 0 would make ``BoundedSemaphore(0).acquire(blocking=False)``
# always return False, so ``_throttle_slot()``'s poll loop would spin forever with
# no timeout -- a config typo hanging the whole run instead of failing loudly. A
# negative value would raise ``ValueError`` out of ``BoundedSemaphore``'s own
# constructor, which ``perplexity_with_retry``'s broad ``except Exception`` would
# launder into four generic per-holding failures, hiding the real cause.
PERPLEXITY_CONCURRENCY = max(1, int(os.getenv("PERPLEXITY_CONCURRENCY", "4")))

# Ceiling for the exponential backoff, matching the default already used by
# PerplexityFallbackManager.calculate_backoff_delay elsewhere in the codebase.
_MAX_BACKOFF_DELAY = 60.0

# How long a coroutine waits between attempts to claim a throttle slot. Slots are
# held for the duration of a network call (seconds), so a 10ms poll adds latency
# that is invisible next to it while keeping the event loop free -- see
# _throttle_slot() for why the wait cannot simply block.
_SLOT_POLL_INTERVAL = 0.01

_throttle: threading.BoundedSemaphore | None = None
# Guards _throttle's lazy init below -- see the race note in get_perplexity_semaphore().
_throttle_init_lock = threading.Lock()


def get_perplexity_semaphore() -> threading.BoundedSemaphore:
    """Return the process-wide Perplexity concurrency throttle.

    Deliberately a ``threading`` primitive, not an ``asyncio`` one. Production
    runs one holding per ThreadPoolExecutor worker, and a worker has no running
    loop, so ``fetch_fact_pack_sync`` calls ``asyncio.run`` -- a *fresh event
    loop per holding, per thread*. An ``asyncio.Semaphore`` binds to the first
    loop that contends on it and raises ``RuntimeError`` on every other one, so
    it throttled nothing and instead failed most of the fleet (and could park a
    thread forever on a future owned by a dead loop). A threading semaphore
    belongs to no loop, so the cap is genuinely process-wide however the callers
    are scheduled.

    A per-loop semaphore keyed by the running loop would silence the
    ``RuntimeError`` but deliver no throttle at all here: each holding owns its
    own loop, so a per-loop cap of 4 admits 4 x (number of loops) concurrent
    calls -- precisely the self-inflicted 429 storm the cap exists to prevent.

    The lazy init is double-checked-locked rather than a bare check-then-assign.
    Production drives this from a ThreadPoolExecutor (default 10 workers), so
    without the lock, two threads racing the cold start could both observe
    ``_throttle is None``, each construct their own ``BoundedSemaphore``, and
    each hand its own instance to a caller -- two semaphores each capping
    ``PERPLEXITY_CONCURRENCY`` concurrent calls is exactly the doubled-cap 429
    storm this throttle exists to prevent.
    """
    global _throttle
    if _throttle is None:
        with _throttle_init_lock:
            if _throttle is None:
                _throttle = threading.BoundedSemaphore(PERPLEXITY_CONCURRENCY)
    return _throttle


@asynccontextmanager
async def _throttle_slot() -> AsyncIterator[None]:
    """Hold one throttle slot for the duration of the block.

    Acquires without blocking and yields to the event loop between tries.
    Blocking on ``acquire()`` inside a coroutine would stall the whole loop --
    and if several Perplexity coroutines were ever gathered on one loop, the
    slot holders would be tasks on that same stalled loop and could never
    release: a deadlock of exactly the kind this fix removes.

    The wait is unordered (a thread can in principle be passed over), which is
    acceptable for a fleet of a few dozen holdings against a cap of 4.
    """
    throttle = get_perplexity_semaphore()
    while not throttle.acquire(blocking=False):
        await asyncio.sleep(_SLOT_POLL_INTERVAL)
    try:
        yield
    finally:
        throttle.release()


def _has_api_key() -> bool:
    return bool(os.getenv("PERPLEXITY_API_KEY") or os.getenv("PPLX_API_KEY"))


async def perplexity_with_retry[T: BaseModel](
    *,
    prompt: str,
    schema: type[T],
    system: str,
    search_recency_filter: str | None = "month",
    timeout: float = 15.0,
    max_attempts: int = 4,
    base_delay: float = 1.0,
) -> T | None:
    """Call ``perplexity_structured`` with bounded retries and exponential backoff.

    Args:
        prompt: User prompt forwarded to Perplexity.
        schema: Pydantic model the response must validate against.
        system: System prompt forwarded to Perplexity.
        search_recency_filter: Perplexity recency window, or None to omit.
        timeout: Per-attempt httpx timeout in seconds.
        max_attempts: Total attempts, including the first. Must be >= 1.
        base_delay: Seconds before the second attempt; doubles each retry,
            jittered by +/-25% and capped at 60s by the delegated backoff helper.

    Returns:
        The validated model, or None when every attempt failed.
    """
    if not _has_api_key():
        logger.warning(f"Perplexity call for {schema.__name__} skipped: no PERPLEXITY_API_KEY/PPLX_API_KEY configured")
        return None

    for attempt in range(max_attempts):
        try:
            async with _throttle_slot():
                result = await perplexity_structured(
                    prompt=prompt,
                    schema=schema,
                    system=system,
                    search_recency_filter=search_recency_filter,
                    timeout=timeout,
                )
        except Exception as exc:
            logger.warning(f"Perplexity call for {schema.__name__} raised on attempt {attempt + 1}/{max_attempts}: {exc!r}")
            result = None

        if result is not None:
            if attempt > 0:
                logger.info(f"Perplexity call for {schema.__name__} succeeded on attempt {attempt + 1}/{max_attempts}")
            return result

        if attempt < max_attempts - 1:
            delay = PerplexityFallbackManager.calculate_backoff_delay(attempt, base_delay, _MAX_BACKOFF_DELAY)
            logger.warning(f"Perplexity call for {schema.__name__} returned no result (attempt {attempt + 1}/{max_attempts}); retrying in {delay:.1f}s")
            await asyncio.sleep(delay)

    logger.warning(f"Perplexity call for {schema.__name__} exhausted {max_attempts} attempts")
    return None
