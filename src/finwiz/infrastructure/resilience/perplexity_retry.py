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

from crewai_custom_tools import perplexity_structured
from pydantic import BaseModel

from finwiz.tools.logger import get_logger
from finwiz.tools.perplexity_errors import PerplexityFallbackManager

logger = get_logger(__name__)

# Perplexity rate-limits aggressively; a full portfolio fans out far wider than
# the account allows. This caps in-flight requests process-wide.
PERPLEXITY_CONCURRENCY = int(os.getenv("PERPLEXITY_CONCURRENCY", "4"))

# Ceiling for the exponential backoff, matching the default already used by
# PerplexityFallbackManager.calculate_backoff_delay elsewhere in the codebase.
_MAX_BACKOFF_DELAY = 60.0

_semaphore: asyncio.Semaphore | None = None


def get_perplexity_semaphore() -> asyncio.Semaphore:
    """Return the process-wide Perplexity concurrency semaphore."""
    global _semaphore
    if _semaphore is None:
        _semaphore = asyncio.Semaphore(PERPLEXITY_CONCURRENCY)
    return _semaphore


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
            async with get_perplexity_semaphore():
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
