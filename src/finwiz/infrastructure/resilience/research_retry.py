"""Retry, throttle, cost recording and fallback for web-grounded research calls.

Primary provider is :func:`openrouter_structured`; :func:`perplexity_with_retry`
is the fallback, tried once when every OpenRouter attempt failed and a
Perplexity key is configured. Both providers return ``None`` for any failure
after the request was made and raise only for a missing key, so the loop
retries **by outcome** and treats a raise like a ``None``. Backoff is delegated
to ``PerplexityFallbackManager.calculate_backoff_delay`` -- the same
exponential-with-jitter helper ``perplexity_retry`` uses.

Each successful OpenRouter call records its exact ``usage.cost`` under
``research_{kind}`` in the run's cost summary; a fallback answer is recorded
as one call with unknown cost, so the summary shows ``cost n/a`` rather than a
false zero.

A caller that passes ``cache_key`` gets a recent answer from
:class:`~finwiz.cache.research_cache.ResearchCache` without a request, when its
``kind`` has a TTL in ``_CACHE_TTL``. A hit records no cost, only a hit count.
"""

from __future__ import annotations

import asyncio
import os
import threading
from contextlib import asynccontextmanager
from datetime import timedelta
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from finwiz.cache.research_cache import ResearchCache
from finwiz.infrastructure.research.openrouter_structured import ResearchResult, SearchOptions, openrouter_structured
from finwiz.infrastructure.resilience.perplexity_retry import perplexity_with_retry
from finwiz.tools.logger import get_logger
from finwiz.tools.perplexity_errors import PerplexityFallbackManager

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

logger = get_logger(__name__)

# Process-wide cap on in-flight OpenRouter research calls. Floored at 1 for the
# same reason as PERPLEXITY_CONCURRENCY: a 0 would spin _throttle_slot() forever
# and a negative value would raise out of BoundedSemaphore's constructor.
RESEARCH_CONCURRENCY = max(1, int(os.getenv("RESEARCH_CONCURRENCY", "6")))

_MAX_BACKOFF_DELAY = 60.0
_SLOT_POLL_INTERVAL = 0.01

# How long a research answer is reused, per kind. A kind absent here is never
# cached: posture is one portfolio-level call; factpack has its own FactPackCache.
# SWOT/Porter match the fact pack's 3-day "fresh" band; news asks for last week's
# headlines, so a day-old answer is the most we reuse.
_CACHE_TTL: dict[str, timedelta] = {
    "swot": timedelta(hours=72),
    "porter": timedelta(hours=72),
    "news": timedelta(hours=24),
}

_research_cache: ResearchCache | None = None

_throttle: threading.BoundedSemaphore | None = None
_throttle_init_lock = threading.Lock()


def get_research_semaphore() -> threading.BoundedSemaphore:
    """Return the process-wide research throttle.

    A ``threading`` primitive, not an ``asyncio`` one: production runs one
    holding per ThreadPoolExecutor worker, each on its own fresh event loop
    (``asyncio.run`` inside ``_run_coroutine_sync``), and an ``asyncio.Semaphore``
    binds to the first loop that contends on it and raises on every other one.
    See ``perplexity_retry.get_perplexity_semaphore`` for the full account,
    including why the lazy init is double-checked-locked.
    """
    global _throttle
    if _throttle is None:
        with _throttle_init_lock:
            if _throttle is None:
                _throttle = threading.BoundedSemaphore(RESEARCH_CONCURRENCY)
    return _throttle


@asynccontextmanager
async def _throttle_slot() -> AsyncIterator[None]:
    """Hold one slot; poll without blocking so the loop stays free."""
    throttle = get_research_semaphore()
    while not throttle.acquire(blocking=False):
        await asyncio.sleep(_SLOT_POLL_INTERVAL)
    try:
        yield
    finally:
        throttle.release()


def _get_research_cache() -> ResearchCache:
    """Process-wide research cache (test seam)."""
    global _research_cache
    if _research_cache is None:
        _research_cache = ResearchCache()
    return _research_cache


def has_openrouter_key() -> bool:
    """Whether OPENROUTER_API_KEY is configured.

    Public: callers that only need to know whether research can run at all
    (e.g. the sentiment wrapper's availability check) use this instead of
    constructing a client/tool just to probe for a key.
    """
    return bool(os.getenv("OPENROUTER_API_KEY"))


def has_perplexity_key() -> bool:
    """Whether a Perplexity key (either env var) is configured. See :func:`has_openrouter_key`."""
    return bool(os.getenv("PERPLEXITY_API_KEY") or os.getenv("PPLX_API_KEY"))


def _record_cost(kind: str, result: ResearchResult[Any]) -> None:
    """Attribute one research call to ``research_{kind}``; never raises."""
    try:
        from finwiz.infrastructure.monitoring.litellm_callback import get_token_monitor

        monitor = get_token_monitor()
        if monitor is None:
            return
        usage = SimpleNamespace(prompt_tokens=result.prompt_tokens, completion_tokens=result.completion_tokens, successful_requests=1)
        monitor.record_usage(f"research_{kind}", usage, model=None, cost_usd=result.cost_usd)
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug(f"Cost tracking skipped for research_{kind}: {exc}")


def _record_cache_hit(kind: str) -> None:
    """Count one cache hit under ``research_{kind}``; never raises."""
    try:
        from finwiz.infrastructure.monitoring.litellm_callback import get_token_monitor

        monitor = get_token_monitor()
        if monitor is not None:
            monitor.record_cache_hit(f"research_{kind}")
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug(f"Cache hit tracking skipped for research_{kind}: {exc}")


async def _perplexity_fallback[T: BaseModel](
    *, prompt: str, schema: type[T], system: str, search_recency_filter: str | None, timeout: float, kind: str
) -> ResearchResult[T] | None:
    if not has_perplexity_key():
        return None
    data = await perplexity_with_retry(prompt=prompt, schema=schema, system=system, search_recency_filter=search_recency_filter, timeout=timeout, max_attempts=1)
    if data is None:
        return None
    logger.info(f"research_{kind}: {schema.__name__} answered by the Perplexity fallback")
    result: ResearchResult[T] = ResearchResult(data=data, citations=(), cost_usd=None, prompt_tokens=0, completion_tokens=0)
    _record_cost(kind, result)
    return result


async def research_with_retry[T: BaseModel](
    *,
    prompt: str,
    schema: type[T],
    system: str,
    search_recency_filter: str | None = "month",
    timeout: float = 15.0,
    max_attempts: int = 4,
    base_delay: float = 1.0,
    kind: str = "research",
    cache_key: str | None = None,
) -> ResearchResult[T] | None:
    """Call OpenRouter with bounded retries, then Perplexity once, then give up.

    Args:
        prompt: User prompt.
        schema: Pydantic model the reply must validate against.
        system: System prompt.
        search_recency_filter: ``"month"``, ``"week"`` or ``None``; becomes the
            OpenRouter recency hint and, on fallback, Perplexity's filter.
        timeout: Per-attempt timeout in seconds.
        max_attempts: OpenRouter attempts including the first. Must be >= 1.
        base_delay: Seconds before the second attempt; doubles each retry with
            jitter, capped at 60 s.
        kind: Cost attribution suffix (``swot``, ``porter``, ``posture``,
            ``factpack``, ``news``).
        cache_key: Identifies the question (e.g. ``"AAPL|stock"``). When set and
            ``kind`` has a TTL, a recent stored answer is returned without a
            request and a fresh answer is stored. ``None`` disables the cache.

    Returns:
        A :class:`ResearchResult` from whichever provider answered, or ``None``.
    """
    ttl = _CACHE_TTL.get(kind)
    if cache_key is None or ttl is None:
        return await _research_uncached(
            prompt=prompt, schema=schema, system=system, search_recency_filter=search_recency_filter, timeout=timeout, max_attempts=max_attempts, base_delay=base_delay, kind=kind
        )

    cache = _get_research_cache()
    cached = cache.get(kind, cache_key, schema, max_age=ttl)
    if cached is not None:
        _record_cache_hit(kind)
        return cached

    result = await _research_uncached(
        prompt=prompt, schema=schema, system=system, search_recency_filter=search_recency_filter, timeout=timeout, max_attempts=max_attempts, base_delay=base_delay, kind=kind
    )
    if result is not None:
        try:
            cache.put(kind, cache_key, result)
        except OSError as exc:
            logger.warning(f"research_{kind}: could not store result in cache: {type(exc).__name__}")
    return result


async def _research_uncached[T: BaseModel](
    *,
    prompt: str,
    schema: type[T],
    system: str,
    search_recency_filter: str | None,
    timeout: float,
    max_attempts: int,
    base_delay: float,
    kind: str,
) -> ResearchResult[T] | None:
    """The retry loop and fallback behind :func:`research_with_retry`, without the cache."""
    if not has_openrouter_key():
        logger.warning(f"research_{kind}: OPENROUTER_API_KEY not configured; trying the Perplexity fallback directly")
        return await _perplexity_fallback(prompt=prompt, schema=schema, system=system, search_recency_filter=search_recency_filter, timeout=timeout, kind=kind)

    search = SearchOptions(recency_hint=search_recency_filter)
    for attempt in range(max_attempts):
        try:
            async with _throttle_slot():
                result = await openrouter_structured(prompt=prompt, schema=schema, system=system, search=search, timeout=timeout)
        except Exception as exc:
            logger.warning(f"research_{kind}: {schema.__name__} raised on attempt {attempt + 1}/{max_attempts}: {type(exc).__name__}")
            result = None

        if result is not None:
            if attempt > 0:
                logger.info(f"research_{kind}: {schema.__name__} succeeded on attempt {attempt + 1}/{max_attempts}")
            _record_cost(kind, result)
            return result

        if attempt < max_attempts - 1:
            delay = PerplexityFallbackManager.calculate_backoff_delay(attempt, base_delay, _MAX_BACKOFF_DELAY)
            logger.warning(f"research_{kind}: {schema.__name__} returned no result (attempt {attempt + 1}/{max_attempts}); retrying in {delay:.1f}s")
            await asyncio.sleep(delay)

    logger.warning(f"research_{kind}: {schema.__name__} exhausted {max_attempts} OpenRouter attempts")
    return await _perplexity_fallback(prompt=prompt, schema=schema, system=system, search_recency_filter=search_recency_filter, timeout=timeout, kind=kind)
