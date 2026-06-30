"""Unit tests for the refactored token-bucket RateLimiter."""

import pytest
from aiolimiter import AsyncLimiter

from finwiz.infrastructure.resilience.rate_limiter import (
    APIProvider,
    RateLimiter,
    get_rate_limiter,
)
from finwiz.infrastructure.resilience.rate_limiter_config import DEFAULT_RATE_LIMITS

# ---------------------------------------------------------------------------
# Construction tests
# ---------------------------------------------------------------------------


class TestRateLimiterInit:
    """Verify __init__ creates one AsyncLimiter per provider."""

    def test_creates_limiter_per_provider(self) -> None:
        limiter = RateLimiter()
        for provider in DEFAULT_RATE_LIMITS:
            assert provider in limiter._limiters, f"Missing limiter for {provider}"

    def test_custom_config_limits_providers(self) -> None:
        cfg = {APIProvider.YAHOO_FINANCE: DEFAULT_RATE_LIMITS[APIProvider.YAHOO_FINANCE]}
        limiter = RateLimiter(config=cfg)
        assert APIProvider.YAHOO_FINANCE in limiter._limiters
        assert APIProvider.ALPHA_VANTAGE not in limiter._limiters


# ---------------------------------------------------------------------------
# acquire() tests
# ---------------------------------------------------------------------------


class TestAcquire:
    """Token bucket acquire is called for known providers."""

    @pytest.mark.asyncio
    async def test_acquire_uses_token_bucket(self, mocker) -> None:
        # Patched on the class, not the instance: AsyncLimiter uses __slots__
        # (via contextlib.AbstractAsyncContextManager) and has no per-instance
        # __dict__, so instance-level attribute patching isn't possible.
        mock_acquire = mocker.patch.object(
            AsyncLimiter,
            "acquire",
            new_callable=mocker.AsyncMock,
        )
        limiter = RateLimiter()
        result = await limiter.acquire(APIProvider.YAHOO_FINANCE)
        assert result is True
        mock_acquire.assert_called_once()

    @pytest.mark.asyncio
    async def test_acquire_unknown_provider_returns_true(self) -> None:
        cfg = {APIProvider.YAHOO_FINANCE: DEFAULT_RATE_LIMITS[APIProvider.YAHOO_FINANCE]}
        limiter = RateLimiter(config=cfg)
        result = await limiter.acquire(APIProvider.ALPHA_VANTAGE)
        assert result is True

    @pytest.mark.asyncio
    async def test_acquire_records_request(self, mocker) -> None:
        mocker.patch.object(
            AsyncLimiter,
            "acquire",
            new_callable=mocker.AsyncMock,
        )
        limiter = RateLimiter()
        await limiter.acquire(APIProvider.YAHOO_FINANCE, endpoint="/quote")
        history = limiter.request_history[APIProvider.YAHOO_FINANCE]
        assert len(history) == 1
        assert history[0].endpoint == "/quote"


# ---------------------------------------------------------------------------
# wait_for_availability() tests
# ---------------------------------------------------------------------------


class TestWaitForAvailability:
    """wait_for_availability delegates to acquire."""

    @pytest.mark.asyncio
    async def test_delegates_to_acquire(self, mocker) -> None:
        limiter = RateLimiter()
        mock_acq = mocker.patch.object(limiter, "acquire", new_callable=mocker.AsyncMock, return_value=True)
        await limiter.wait_for_availability(APIProvider.YAHOO_FINANCE, endpoint="/test")
        mock_acq.assert_called_once_with(APIProvider.YAHOO_FINANCE, "/test")


# ---------------------------------------------------------------------------
# Stats / monitoring tests
# ---------------------------------------------------------------------------


class TestStats:
    """Stats methods work after token bucket refactor."""

    def test_get_stats_returns_expected_keys(self) -> None:
        limiter = RateLimiter()
        stats = limiter.get_stats(APIProvider.YAHOO_FINANCE)
        expected_keys = {
            "provider",
            "requests_last_minute",
            "requests_last_hour",
            "limit_per_minute",
            "limit_per_hour",
            "last_request",
            "total_requests",
        }
        assert set(stats.keys()) == expected_keys

    def test_get_stats_provider_value(self) -> None:
        limiter = RateLimiter()
        stats = limiter.get_stats(APIProvider.YAHOO_FINANCE)
        assert stats["provider"] == "yahoo_finance"


# ---------------------------------------------------------------------------
# Retry / backoff tests
# ---------------------------------------------------------------------------


class TestRetry:
    """Retry and backoff helpers remain functional."""

    def test_get_retry_delay_positive(self) -> None:
        limiter = RateLimiter()
        delay = limiter.get_retry_delay(APIProvider.YAHOO_FINANCE, attempt=0)
        assert delay > 0

    def test_should_retry_rate_limit_error(self) -> None:
        limiter = RateLimiter()
        assert limiter.should_retry(APIProvider.YAHOO_FINANCE, 0, RuntimeError("429 Too many requests"))

    def test_should_retry_exceeds_max(self) -> None:
        limiter = RateLimiter()
        assert not limiter.should_retry(APIProvider.YAHOO_FINANCE, 99, RuntimeError("429"))


# ---------------------------------------------------------------------------
# Config re-export tests
# ---------------------------------------------------------------------------


class TestConfigReExports:
    """Verify backward-compatible re-exports from rate_limiter.py."""

    def test_api_provider_importable_from_rate_limiter(self) -> None:
        from finwiz.infrastructure.resilience.rate_limiter import APIProvider as AP

        assert AP.YAHOO_FINANCE.value == "yahoo_finance"

    def test_default_rate_limits_importable(self) -> None:
        from finwiz.infrastructure.resilience.rate_limiter import DEFAULT_RATE_LIMITS as DRL

        assert APIProvider.YAHOO_FINANCE in DRL

    def test_request_record_importable(self) -> None:
        from finwiz.infrastructure.resilience.rate_limiter import RequestRecord as RR

        rec = RR(timestamp=1.0, endpoint="/test")
        assert rec.endpoint == "/test"


# ---------------------------------------------------------------------------
# get_rate_limiter singleton tests
# ---------------------------------------------------------------------------


class TestGetRateLimiter:
    """get_rate_limiter() returns a configured singleton."""

    def test_returns_rate_limiter_instance(self, mocker) -> None:
        # Reset the global so we get a fresh instance
        import finwiz.infrastructure.resilience.rate_limiter as mod

        mocker.patch.object(mod, "_rate_limiter", None)
        rl = get_rate_limiter()
        assert isinstance(rl, RateLimiter)
