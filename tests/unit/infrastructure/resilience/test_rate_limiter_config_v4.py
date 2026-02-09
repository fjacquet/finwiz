"""Unit tests for v4 APIProvider enum entries and rate limit configs."""

from finwiz.infrastructure.resilience.rate_limiter_config import (
    DEFAULT_RATE_LIMITS,
    APIProvider,
)


class TestV4APIProviders:
    """Verify new APIProvider enum members exist."""

    def test_finnhub_provider(self):
        assert APIProvider.FINNHUB == "finnhub"

    def test_fred_provider(self):
        assert APIProvider.FRED == "fred"

    def test_fear_greed_provider(self):
        assert APIProvider.FEAR_GREED == "fear_greed"

    def test_gnews_provider(self):
        assert APIProvider.GNEWS == "gnews"


class TestV4RateLimits:
    """Verify rate limit configs for new providers."""

    def test_finnhub_rate_limits(self):
        config = DEFAULT_RATE_LIMITS[APIProvider.FINNHUB]
        assert config.requests_per_minute == 60
        assert config.burst_limit == 10

    def test_fred_rate_limits(self):
        config = DEFAULT_RATE_LIMITS[APIProvider.FRED]
        assert config.requests_per_minute == 120
        assert config.burst_limit == 20

    def test_fear_greed_rate_limits(self):
        config = DEFAULT_RATE_LIMITS[APIProvider.FEAR_GREED]
        assert config.requests_per_minute == 10
        assert config.max_retries == 2

    def test_gnews_rate_limits(self):
        config = DEFAULT_RATE_LIMITS[APIProvider.GNEWS]
        assert config.requests_per_minute == 10
        assert config.requests_per_day == 100
        assert config.max_retries == 2

    def test_all_new_providers_have_configs(self):
        new_providers = [APIProvider.FINNHUB, APIProvider.FRED, APIProvider.FEAR_GREED, APIProvider.GNEWS]
        for provider in new_providers:
            assert provider in DEFAULT_RATE_LIMITS, f"Missing rate limit config for {provider}"
