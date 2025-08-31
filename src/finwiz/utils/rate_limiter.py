"""
Rate limiting and throttling utilities for external API calls.

This module provides comprehensive rate limiting, throttling, and retry strategies
for all external API integrations to prevent rate limit violations and ensure
reliable operation.
"""

import asyncio
import time
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class APIProvider(str, Enum):
    """Supported API providers with their rate limits."""

    ALPHA_VANTAGE = "alpha_vantage"
    YAHOO_FINANCE = "yahoo_finance"
    TWELVE_DATA = "twelve_data"
    CHART_IMG = "chart_img"
    COINMARKETCAP = "coinmarketcap"
    KRAKEN = "kraken"
    SEC_EDGAR = "sec_edgar"


@dataclass
class RateLimitConfig:
    """Configuration for API rate limiting."""

    requests_per_minute: int
    requests_per_hour: int = 0
    requests_per_day: int = 0
    burst_limit: int = 5
    cooldown_seconds: float = 1.0
    max_retries: int = 3
    base_backoff: float = 1.0
    max_backoff: float = 60.0
    jitter: bool = True


# Default rate limit configurations for each API provider
DEFAULT_RATE_LIMITS: dict[APIProvider, RateLimitConfig] = {
    APIProvider.ALPHA_VANTAGE: RateLimitConfig(
        requests_per_minute=5,
        requests_per_hour=500,
        requests_per_day=500,
        burst_limit=2,
        cooldown_seconds=12.0,  # 5 requests per minute = 12 seconds between requests
        max_retries=3,
        base_backoff=2.0,
        max_backoff=120.0,
    ),
    APIProvider.YAHOO_FINANCE: RateLimitConfig(
        requests_per_minute=60,
        requests_per_hour=2000,
        burst_limit=10,
        cooldown_seconds=1.0,
        max_retries=3,
        base_backoff=1.0,
        max_backoff=30.0,
    ),
    APIProvider.TWELVE_DATA: RateLimitConfig(
        requests_per_minute=8,
        requests_per_hour=800,
        requests_per_day=800,
        burst_limit=3,
        cooldown_seconds=7.5,  # 8 requests per minute
        max_retries=3,
        base_backoff=2.0,
        max_backoff=60.0,
    ),
    APIProvider.CHART_IMG: RateLimitConfig(
        requests_per_minute=30,
        requests_per_hour=1000,
        burst_limit=5,
        cooldown_seconds=2.0,
        max_retries=3,
        base_backoff=1.0,
        max_backoff=30.0,
    ),
    APIProvider.COINMARKETCAP: RateLimitConfig(
        requests_per_minute=30,
        requests_per_hour=1000,
        requests_per_day=10000,
        burst_limit=5,
        cooldown_seconds=2.0,
        max_retries=3,
        base_backoff=1.0,
        max_backoff=60.0,
    ),
    APIProvider.KRAKEN: RateLimitConfig(
        requests_per_minute=60,
        requests_per_hour=1000,
        burst_limit=10,
        cooldown_seconds=1.0,
        max_retries=3,
        base_backoff=1.0,
        max_backoff=30.0,
    ),
    APIProvider.SEC_EDGAR: RateLimitConfig(
        requests_per_minute=10,
        requests_per_hour=600,
        burst_limit=3,
        cooldown_seconds=6.0,  # 10 requests per minute
        max_retries=3,
        base_backoff=2.0,
        max_backoff=60.0,
    ),
}


@dataclass
class RequestRecord:
    """Record of an API request for rate limiting tracking."""

    timestamp: float
    endpoint: str
    success: bool = True


class RateLimiter:
    """
    Thread-safe rate limiter with sliding window and exponential backoff.

    Tracks requests per provider and endpoint, implements throttling,
    and provides retry strategies with exponential backoff.
    """

    def __init__(self, config: dict[APIProvider, RateLimitConfig] | None = None) -> None:
        """Initialize rate limiter with configuration."""
        self.config = config or DEFAULT_RATE_LIMITS
        self.request_history: dict[APIProvider, deque] = defaultdict(deque)
        self.last_request_time: dict[APIProvider, float] = {}
        self.retry_counts: dict[str, int] = defaultdict(int)
        self._lock = asyncio.Lock()

    async def acquire(self, provider: APIProvider, endpoint: str = "") -> bool:
        """
        Acquire permission to make an API request.

        Args:
            provider: API provider to check limits for
            endpoint: Specific endpoint being called

        Returns:
            True if request is allowed, False if rate limited

        """
        async with self._lock:
            config = self.config.get(provider)
            if not config:
                logger.warning(f"No rate limit config for provider {provider}")
                return True

            now = time.time()
            history = self.request_history[provider]

            # Clean old requests from sliding window
            self._clean_old_requests(history, now)

            # Check if we're within rate limits
            if not self._check_rate_limits(history, config, now):
                logger.warning(f"Rate limit exceeded for {provider}")
                return False

            # Check cooldown period
            last_request = self.last_request_time.get(provider, 0)
            time_since_last = now - last_request

            if time_since_last < config.cooldown_seconds:
                sleep_time = config.cooldown_seconds - time_since_last
                logger.info(f"Throttling {provider} request, sleeping {sleep_time:.2f}s")
                await asyncio.sleep(sleep_time)

            # Record the request
            history.append(RequestRecord(timestamp=now, endpoint=endpoint))
            self.last_request_time[provider] = now

            return True

    def _clean_old_requests(self, history: deque, now: float) -> None:
        """Remove requests older than 1 hour from history."""
        while history and now - history[0].timestamp > 3600:
            history.popleft()

    def _check_rate_limits(self, history: deque, config: RateLimitConfig, now: float) -> bool:
        """Check if current request count is within limits."""
        # Count requests in different time windows
        minute_count = sum(1 for r in history if now - r.timestamp <= 60)
        hour_count = sum(1 for r in history if now - r.timestamp <= 3600)
        day_count = sum(1 for r in history if now - r.timestamp <= 86400)

        # Check against limits
        if minute_count >= config.requests_per_minute:
            return False

        if config.requests_per_hour > 0 and hour_count >= config.requests_per_hour:
            return False

        if config.requests_per_day > 0 and day_count >= config.requests_per_day:
            return False

        return True

    async def wait_for_availability(self, provider: APIProvider, endpoint: str = "") -> None:
        """Wait until a request can be made for the given provider."""
        config = self.config.get(provider)
        if not config:
            return

        max_wait_time = 300  # 5 minutes maximum wait
        start_time = time.time()

        while time.time() - start_time < max_wait_time:
            if await self.acquire(provider, endpoint):
                return

            # Wait before checking again
            await asyncio.sleep(config.cooldown_seconds)

        logger.error(f"Timeout waiting for rate limit availability for {provider}")
        raise TimeoutError(f"Rate limit timeout for {provider}")

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

        return delay

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
        logger.warning(f"API request failed for {provider} {endpoint}: {error}")

        # Update retry count
        key = f"{provider}:{endpoint}"
        self.retry_counts[key] += 1

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


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


async def with_rate_limit(provider: APIProvider, func: Callable, *args, endpoint: str = "", **kwargs) -> Any:
    """
    Execute a function with rate limiting and retry logic.

    Args:
        provider: API provider for rate limiting
        func: Function to execute (can be sync or async)
        endpoint: Specific API endpoint being called
        *args, **kwargs: Arguments to pass to the function

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
                logger.error(f"Final failure for {provider} {endpoint} after {attempt} attempts: {e}")
                raise

            if attempt < max_retries:
                delay = limiter.get_retry_delay(provider, attempt)
                logger.info(f"Retrying {provider} {endpoint} in {delay:.2f}s (attempt {attempt + 1})")
                await asyncio.sleep(delay)

    raise RuntimeError(f"All retry attempts failed for {provider} {endpoint}")
