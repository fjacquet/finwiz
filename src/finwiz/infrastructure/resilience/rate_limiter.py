"""
Rate limiting and throttling utilities for external API calls.

This module provides token-bucket rate limiting using aiolimiter, retry strategies
with exponential backoff, and monitoring for all external API integrations.
"""

import asyncio
import time
from collections import defaultdict, deque
from collections.abc import Callable
from typing import Any

from aiolimiter import AsyncLimiter

from finwiz.infrastructure.resilience.rate_limiter_config import (
    DEFAULT_RATE_LIMITS,
    APIProvider,
    RateLimitConfig,
    RequestRecord,
)
from finwiz.tools.logger import get_logger

# Re-export for backward compatibility
__all__ = [
    "DEFAULT_RATE_LIMITS",
    "APIProvider",
    "RateLimitConfig",
    "RateLimiter",
    "RequestRecord",
    "get_rate_limiter",
    "with_rate_limit",
]

logger = get_logger(__name__)


class RateLimiter:
    """
    Token-bucket rate limiter using aiolimiter with monitoring and retry support.

    Each API provider gets its own AsyncLimiter instance configured from
    DEFAULT_RATE_LIMITS. The token bucket handles synchronization internally,
    eliminating the need for an external asyncio.Lock.
    """

    def __init__(self, config: dict[APIProvider, RateLimitConfig] | None = None) -> None:
        """Initialize rate limiter with per-provider token buckets."""
        self.config = config or DEFAULT_RATE_LIMITS

        # Create a token-bucket limiter per provider
        self._limiters: dict[APIProvider, AsyncLimiter] = {}
        for provider, cfg in self.config.items():
            # max_rate = burst capacity, time_period = window that achieves correct per-minute rate
            time_period = 60.0 / cfg.requests_per_minute * cfg.burst_limit
            self._limiters[provider] = AsyncLimiter(max_rate=cfg.burst_limit, time_period=time_period)

        # Monitoring / stats (kept for observability)
        self.request_history: dict[APIProvider, deque] = defaultdict(deque)
        self.last_request_time: dict[APIProvider, float] = {}
        self.retry_counts: dict[str, int] = defaultdict(int)

    async def acquire(self, provider: APIProvider, endpoint: str = "") -> bool:
        """
        Acquire permission to make an API request via the token bucket.

        Args:
            provider: API provider to check limits for
            endpoint: Specific endpoint being called

        Returns:
            True once a token has been acquired (waits if necessary)

        """
        limiter = self._limiters.get(provider)
        if not limiter:
            logger.warning(f"No rate limit config for provider {provider}")
            return True

        # Wait for a token (aiolimiter handles queuing internally)
        await limiter.acquire()

        # Record the request for monitoring
        now = time.time()
        history = self.request_history[provider]
        self._clean_old_requests(history, now)
        history.append(RequestRecord(timestamp=now, endpoint=endpoint))
        self.last_request_time[provider] = now

        return True

    async def wait_for_availability(self, provider: APIProvider, endpoint: str = "") -> None:
        """Wait until a request can be made for the given provider."""
        try:
            await asyncio.wait_for(self.acquire(provider, endpoint), timeout=300)
        except TimeoutError:
            logger.error(f"Timeout waiting for rate limit availability for {provider}")
            raise TimeoutError(f"Rate limit timeout for {provider}")

    def _clean_old_requests(self, history: deque, now: float) -> None:
        """Remove requests older than 1 hour from history."""
        while history and now - history[0].timestamp > 3600:
            history.popleft()

    def get_retry_delay(self, provider: APIProvider, attempt: int) -> float:
        """Calculate exponential backoff delay for retry attempts."""
        config = self.config.get(provider)
        if not config:
            return 1.0

        # Exponential backoff with jitter
        delay = min(config.base_backoff * (2**attempt), config.max_backoff)

        if config.jitter:
            import random

            delay *= 0.5 + random.random() * 0.5  # Add 0-50% jitter

        return float(delay)

    def should_retry(self, provider: APIProvider, attempt: int, error: Exception) -> bool:
        """Determine if a request should be retried based on error and attempt count."""
        config = self.config.get(provider)
        if not config or attempt >= config.max_retries:
            return False

        # Retry on rate limit errors, timeouts, and connection errors
        error_str = str(error).lower()
        retryable_errors = [
            "rate limit",
            "too many requests",
            "429",
            "503",
            "502",
            "504",
            "timeout",
            "connection",
            "network",
            "temporary",
        ]

        return any(err in error_str for err in retryable_errors)

    def record_failure(self, provider: APIProvider, endpoint: str, error: Exception) -> None:
        """Record a failed request for monitoring and adjustment."""
        logger.warning(f"Rate limit failure recorded for {provider} {endpoint}: {error}")

        # Update retry count
        key = f"{provider}:{endpoint}"
        self.retry_counts[key] += 1

        # Log retry count if it's getting high
        if self.retry_counts[key] >= 3:
            logger.warning(f"High retry count for {provider} {endpoint}: {self.retry_counts[key]} failures")

    def get_stats(self, provider: APIProvider) -> dict[str, Any]:
        """Get rate limiting statistics for a provider."""
        history = self.request_history[provider]
        now = time.time()

        minute_count = sum(1 for r in history if now - r.timestamp <= 60)
        hour_count = sum(1 for r in history if now - r.timestamp <= 3600)

        config = self.config.get(provider, RateLimitConfig(requests_per_minute=0))

        return {
            "provider": provider.value,
            "requests_last_minute": minute_count,
            "requests_last_hour": hour_count,
            "limit_per_minute": config.requests_per_minute,
            "limit_per_hour": config.requests_per_hour,
            "last_request": self.last_request_time.get(provider, 0),
            "total_requests": len(history),
        }


# Global rate limiter instance
_rate_limiter: RateLimiter | None = None


def get_rate_limiter(use_premium_tiers: bool = False) -> RateLimiter:
    """
    Get the global rate limiter instance.

    Args:
        use_premium_tiers: If True, use premium tier rate limits for supported providers

    Returns:
        Configured RateLimiter instance

    """
    global _rate_limiter
    if _rate_limiter is None:
        config = DEFAULT_RATE_LIMITS.copy()

        # Check environment variables for premium tier configuration
        import os

        if use_premium_tiers or os.getenv("ALPHA_VANTAGE_PREMIUM", "false").lower() == "true":
            logger.info("Using Alpha Vantage premium tier rate limits (75 calls/minute)")
            config[APIProvider.ALPHA_VANTAGE] = config[APIProvider.ALPHA_VANTAGE_PREMIUM]

        if use_premium_tiers or os.getenv("TWELVE_DATA_PREMIUM", "false").lower() == "true":
            logger.info("Using Twelve Data premium tier rate limits (800 calls/minute)")
            config[APIProvider.TWELVE_DATA] = config[APIProvider.TWELVE_DATA_PREMIUM]

        _rate_limiter = RateLimiter(config)
    return _rate_limiter


async def with_rate_limit(provider: APIProvider, func: Callable, *args: Any, endpoint: str = "", **kwargs: Any) -> Any:
    """
    Execute a function with rate limiting and retry logic.

    Args:
        provider: API provider for rate limiting
        func: Function to execute (can be sync or async)
        endpoint: Specific API endpoint being called
        *args: Positional arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function

    Returns:
        Result of the function call

    Raises:
        Exception: If all retry attempts fail

    """
    limiter = get_rate_limiter()
    config = limiter.config.get(provider)
    max_retries = config.max_retries if config else 3

    for attempt in range(max_retries + 1):
        try:
            # Wait for rate limit availability
            await limiter.wait_for_availability(provider, endpoint)

            # Execute the function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            # Reset retry count on success
            key = f"{provider}:{endpoint}"
            limiter.retry_counts[key] = 0

            return result

        except Exception as e:
            limiter.record_failure(provider, endpoint, e)

            if not limiter.should_retry(provider, attempt, e):
                logger.error(f"Rate limit retry exhausted for {provider} {endpoint} - Failed after {attempt} attempts: {e}")
                raise

            if attempt < max_retries:
                delay = limiter.get_retry_delay(provider, attempt)
                logger.info(f"Rate limit retry for {provider} {endpoint} - Attempt {attempt + 1}/{max_retries}, waiting {delay:.2f}s before retry")
                await asyncio.sleep(delay)

    raise RuntimeError(f"All retry attempts failed for {provider} {endpoint}")
