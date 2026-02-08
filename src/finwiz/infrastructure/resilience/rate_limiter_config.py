"""
Rate limiter configuration: enums, dataclasses, and default rate limits.

Extracted from rate_limiter.py to enforce the 300-line file limit while keeping
configuration constants separate from runtime logic.
"""

from dataclasses import dataclass
from enum import Enum


class APIProvider(str, Enum):
    """Supported API providers with their rate limits."""

    ALPHA_VANTAGE = "alpha_vantage"
    ALPHA_VANTAGE_PREMIUM = "alpha_vantage_premium"
    YAHOO_FINANCE = "yahoo_finance"
    TWELVE_DATA = "twelve_data"
    TWELVE_DATA_PREMIUM = "twelve_data_premium"
    CHART_IMG = "chart_img"
    COINMARKETCAP = "coinmarketcap"
    KRAKEN = "kraken"
    SEC_EDGAR = "sec_edgar"
    PERPLEXITY = "perplexity"


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
    APIProvider.ALPHA_VANTAGE_PREMIUM: RateLimitConfig(
        requests_per_minute=75,
        requests_per_hour=4500,
        requests_per_day=75000,
        burst_limit=10,
        cooldown_seconds=0.8,  # 75 requests per minute
        max_retries=3,
        base_backoff=1.0,
        max_backoff=60.0,
    ),
    APIProvider.YAHOO_FINANCE: RateLimitConfig(
        requests_per_minute=600,  # 10 requests per second
        requests_per_hour=36000,
        burst_limit=20,
        cooldown_seconds=0.1,  # 10 requests per second
        max_retries=3,
        base_backoff=1.0,
        max_backoff=30.0,
    ),
    APIProvider.TWELVE_DATA: RateLimitConfig(
        requests_per_minute=8,
        requests_per_hour=480,
        requests_per_day=800,
        burst_limit=3,
        cooldown_seconds=7.5,  # 8 requests per minute
        max_retries=3,
        base_backoff=2.0,
        max_backoff=60.0,
    ),
    APIProvider.TWELVE_DATA_PREMIUM: RateLimitConfig(
        requests_per_minute=800,
        requests_per_hour=48000,
        requests_per_day=800000,
        burst_limit=50,
        cooldown_seconds=0.075,  # 800 requests per minute
        max_retries=3,
        base_backoff=0.5,
        max_backoff=30.0,
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
    APIProvider.PERPLEXITY: RateLimitConfig(
        requests_per_minute=30,
        requests_per_hour=1200,
        burst_limit=5,
        cooldown_seconds=2.0,
        max_retries=3,
        base_backoff=1.0,
        max_backoff=30.0,
    ),
}


@dataclass
class RequestRecord:
    """Record of an API request for rate limiting tracking."""

    timestamp: float
    endpoint: str
    success: bool = True
