"""
Tests for API rate limiting and throttling functionality.

This module tests the rate limiting system, retry strategies, and API decorators
to ensure proper behavior under various conditions including rate limit violations,
network errors, and concurrent access patterns.
"""

import asyncio
import time

import pytest

from finwiz.utils.api_decorators import (
    APICallContext,
    api_error_handler,
    api_tool,
    rate_limited,
    safe_api_call,
    timeout_handler,
)
from finwiz.utils.rate_limiter import (
    APIProvider,
    RateLimitConfig,
    RateLimiter,
    get_rate_limiter,
    with_rate_limit,
)


class TestRateLimiter:
    """Test cases for the RateLimiter class."""

    def test_should_initialize_with_default_config(self):
        """Test rate limiter initialization with default configuration."""
        # Arrange & Act
        limiter = RateLimiter()

        # Assert
        assert APIProvider.ALPHA_VANTAGE in limiter.config
        assert limiter.config[APIProvider.ALPHA_VANTAGE].requests_per_minute == 5
        assert limiter.config[APIProvider.YAHOO_FINANCE].requests_per_minute == 600  # 10 requests per second

    def test_should_initialize_with_custom_config(self):
        """Test rate limiter initialization with custom configuration."""
        # Arrange
        custom_config = {APIProvider.ALPHA_VANTAGE: RateLimitConfig(requests_per_minute=10, requests_per_hour=1000)}

        # Act
        limiter = RateLimiter(custom_config)

        # Assert
        assert limiter.config[APIProvider.ALPHA_VANTAGE].requests_per_minute == 10
        assert limiter.config[APIProvider.ALPHA_VANTAGE].requests_per_hour == 1000

    def test_should_support_premium_tier_providers(self):
        """Test that premium tier providers are configured correctly."""
        # Arrange & Act
        limiter = RateLimiter()

        # Assert - Premium tiers should exist in config
        assert APIProvider.ALPHA_VANTAGE_PREMIUM in limiter.config
        assert limiter.config[APIProvider.ALPHA_VANTAGE_PREMIUM].requests_per_minute == 75
        assert APIProvider.TWELVE_DATA_PREMIUM in limiter.config
        assert limiter.config[APIProvider.TWELVE_DATA_PREMIUM].requests_per_minute == 800

    @pytest.mark.asyncio
    async def test_should_allow_request_within_limits(self):
        """Test that requests within rate limits are allowed."""
        # Arrange
        config = {APIProvider.ALPHA_VANTAGE: RateLimitConfig(requests_per_minute=10, cooldown_seconds=0.1)}
        limiter = RateLimiter(config)

        # Act
        result = await limiter.acquire(APIProvider.ALPHA_VANTAGE, "test_endpoint")

        # Assert
        assert result is True
        assert len(limiter.request_history[APIProvider.ALPHA_VANTAGE]) == 1

    @pytest.mark.asyncio
    async def test_should_enforce_cooldown_period(self):
        """Test that cooldown period is enforced between requests."""
        # Arrange
        config = {APIProvider.ALPHA_VANTAGE: RateLimitConfig(requests_per_minute=60, cooldown_seconds=0.5)}
        limiter = RateLimiter(config)

        # Act
        start_time = time.time()
        await limiter.acquire(APIProvider.ALPHA_VANTAGE, "test1")
        await limiter.acquire(APIProvider.ALPHA_VANTAGE, "test2")
        end_time = time.time()

        # Assert
        duration = end_time - start_time
        assert duration >= 0.5  # Should have waited for cooldown

    @pytest.mark.asyncio
    async def test_should_reject_request_exceeding_rate_limit(self):
        """Test that requests exceeding rate limits are rejected."""
        # Arrange
        config = {APIProvider.ALPHA_VANTAGE: RateLimitConfig(requests_per_minute=2, cooldown_seconds=0.0)}
        limiter = RateLimiter(config)

        # Act - Make requests up to the limit
        result1 = await limiter.acquire(APIProvider.ALPHA_VANTAGE, "test1")
        result2 = await limiter.acquire(APIProvider.ALPHA_VANTAGE, "test2")
        result3 = await limiter.acquire(APIProvider.ALPHA_VANTAGE, "test3")

        # Assert
        assert result1 is True
        assert result2 is True
        assert result3 is False  # Should be rejected

    def test_should_calculate_exponential_backoff_delay(self):
        """Test exponential backoff delay calculation."""
        # Arrange
        config = {APIProvider.ALPHA_VANTAGE: RateLimitConfig(requests_per_minute=5, base_backoff=2.0, max_backoff=60.0, jitter=False)}
        limiter = RateLimiter(config)

        # Act & Assert
        assert limiter.get_retry_delay(APIProvider.ALPHA_VANTAGE, 0) == 2.0
        assert limiter.get_retry_delay(APIProvider.ALPHA_VANTAGE, 1) == 4.0
        assert limiter.get_retry_delay(APIProvider.ALPHA_VANTAGE, 2) == 8.0
        assert limiter.get_retry_delay(APIProvider.ALPHA_VANTAGE, 10) == 60.0  # Capped at max

    def test_should_determine_retry_eligibility(self):
        """Test retry eligibility determination based on error types."""
        # Arrange
        config = {APIProvider.ALPHA_VANTAGE: RateLimitConfig(requests_per_minute=5, max_retries=3)}
        limiter = RateLimiter(config)

        # Act & Assert - Retryable errors
        assert limiter.should_retry(APIProvider.ALPHA_VANTAGE, 1, Exception("Rate limit exceeded"))
        assert limiter.should_retry(APIProvider.ALPHA_VANTAGE, 1, Exception("429 Too Many Requests"))
        assert limiter.should_retry(APIProvider.ALPHA_VANTAGE, 1, Exception("Connection timeout"))

        # Non-retryable conditions
        assert not limiter.should_retry(APIProvider.ALPHA_VANTAGE, 5, Exception("Rate limit"))  # Too many attempts
        assert not limiter.should_retry(APIProvider.ALPHA_VANTAGE, 1, Exception("Invalid API key"))  # Non-retryable error

    def test_should_provide_accurate_stats(self):
        """Test that rate limiter provides accurate statistics."""
        # Arrange
        limiter = RateLimiter()

        # Act - Simulate some requests
        asyncio.run(limiter.acquire(APIProvider.YAHOO_FINANCE, "test"))
        stats = limiter.get_stats(APIProvider.YAHOO_FINANCE)

        # Assert
        assert stats["provider"] == "yahoo_finance"
        assert stats["requests_last_minute"] == 1
        assert stats["total_requests"] == 1
        assert "limit_per_minute" in stats


class TestAPIDecorators:
    """Test cases for API decorators and utilities."""

    @pytest.mark.asyncio
    async def test_rate_limited_decorator_async_function(self):
        """Test rate_limited decorator with async function."""

        # Arrange
        @rate_limited(APIProvider.YAHOO_FINANCE, "test_endpoint")
        async def mock_api_call(value: str) -> str:
            return f"result_{value}"

        # Act
        result = await mock_api_call("test")

        # Assert
        assert result == "result_test"

    def test_rate_limited_decorator_sync_function(self):
        """Test rate_limited decorator with sync function."""

        # Arrange
        @rate_limited(APIProvider.YAHOO_FINANCE, "test_endpoint")
        def mock_api_call(value: str) -> str:
            return f"result_{value}"

        # Act
        result = mock_api_call("test")

        # Assert
        assert result == "result_test"

    @pytest.mark.asyncio
    async def test_api_error_handler_with_default_return(self):
        """Test api_error_handler decorator with default return value."""

        # Arrange
        @api_error_handler(default_return="error_occurred", reraise=False)
        async def failing_function():
            raise ValueError("Test error")

        # Act
        result = await failing_function()

        # Assert
        assert result == "error_occurred"

    @pytest.mark.asyncio
    async def test_api_error_handler_with_reraise(self):
        """Test api_error_handler decorator with reraise option."""

        # Arrange
        @api_error_handler(reraise=True)
        async def failing_function():
            raise ValueError("Test error")

        # Act & Assert
        with pytest.raises(ValueError, match="Test error"):
            await failing_function()

    @pytest.mark.asyncio
    async def test_timeout_handler_decorator(self):
        """Test timeout_handler decorator."""

        # Arrange
        @timeout_handler(timeout_seconds=0.1)
        async def slow_function():
            await asyncio.sleep(0.2)
            return "completed"

        # Act & Assert
        with pytest.raises(TimeoutError):
            await slow_function()

    @pytest.mark.asyncio
    async def test_api_tool_comprehensive_decorator(self):
        """Test comprehensive api_tool decorator."""
        # Arrange
        call_count = 0

        @api_tool(provider=APIProvider.YAHOO_FINANCE, endpoint="test", timeout=1.0, default_return="fallback")
        async def mock_api_function(should_fail: bool = False):
            nonlocal call_count
            call_count += 1
            if should_fail:
                raise ValueError("API error")
            return "success"

        # Act
        success_result = await mock_api_function(should_fail=False)

        # Assert
        assert success_result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_api_call_context_manager(self):
        """Test APICallContext context manager."""
        # Arrange & Act
        async with APICallContext(APIProvider.YAHOO_FINANCE, "test_endpoint") as ctx:
            assert ctx.provider == APIProvider.YAHOO_FINANCE
            assert ctx.endpoint == "test_endpoint"

        # Context should exit cleanly

    @pytest.mark.asyncio
    async def test_safe_api_call_utility(self):
        """Test safe_api_call utility function."""

        # Arrange
        async def mock_successful_call(value: str) -> str:
            return f"processed_{value}"

        async def mock_failing_call():
            raise ConnectionError("Network error")

        # Act
        success_result = await safe_api_call(APIProvider.YAHOO_FINANCE, mock_successful_call, "test_data", endpoint="test")

        failure_result = await safe_api_call(APIProvider.YAHOO_FINANCE, mock_failing_call, endpoint="test", default_return="fallback_value")

        # Assert
        assert success_result == "processed_test_data"
        assert failure_result == "fallback_value"


class TestWithRateLimit:
    """Test cases for the with_rate_limit function."""

    @pytest.mark.asyncio
    async def test_should_execute_function_with_rate_limiting(self):
        """Test that with_rate_limit executes function with proper rate limiting."""

        # Arrange
        async def mock_api_function(value: str) -> str:
            return f"api_result_{value}"

        # Act
        result = await with_rate_limit(APIProvider.YAHOO_FINANCE, mock_api_function, "test_input", endpoint="test_endpoint")

        # Assert
        assert result == "api_result_test_input"

    @pytest.mark.asyncio
    async def test_should_retry_on_retryable_errors(self, mocker):
        """Test retry behavior on retryable errors."""
        # Arrange
        call_count = 0

        async def mock_failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Rate limit exceeded")
            return "success_after_retries"

        # Mock the sleep to speed up test
        mocker.patch("asyncio.sleep", new_callable=mocker.AsyncMock)

        # Act
        result = await with_rate_limit(APIProvider.YAHOO_FINANCE, mock_failing_function, endpoint="test")

        # Assert
        assert result == "success_after_retries"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_should_fail_after_max_retries(self, mocker):
        """Test that function fails after maximum retry attempts."""

        # Arrange
        async def always_failing_function():
            raise ConnectionError("Persistent network error")

        # Mock the sleep to speed up test
        mocker.patch("asyncio.sleep", new_callable=mocker.AsyncMock)

        # Act & Assert
        with pytest.raises(ConnectionError, match="Persistent network error"):
            await with_rate_limit(APIProvider.YAHOO_FINANCE, always_failing_function, endpoint="test")


class TestRateLimitIntegration:
    """Integration tests for rate limiting system."""

    @pytest.mark.asyncio
    async def test_concurrent_requests_respect_rate_limits(self):
        """Test that concurrent requests properly respect rate limits."""
        # Arrange
        config = {APIProvider.ALPHA_VANTAGE: RateLimitConfig(requests_per_minute=3, cooldown_seconds=0.1)}
        limiter = RateLimiter(config)

        async def mock_request(request_id: int):
            await limiter.acquire(APIProvider.ALPHA_VANTAGE, f"request_{request_id}")
            return f"completed_{request_id}"

        # Act - Launch concurrent requests
        start_time = time.time()
        tasks = [mock_request(i) for i in range(5)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()

        # Assert
        successful_results = [r for r in results if isinstance(r, str)]
        assert len(successful_results) >= 3  # At least the allowed requests should succeed

        # Should take some time due to rate limiting
        duration = end_time - start_time
        assert duration >= 0.1  # At least one cooldown period

    def test_global_rate_limiter_singleton(self):
        """Test that get_rate_limiter returns the same instance."""
        # Act
        limiter1 = get_rate_limiter()
        limiter2 = get_rate_limiter()

        # Assert
        assert limiter1 is limiter2

    @pytest.mark.asyncio
    async def test_rate_limiter_cleans_old_requests(self):
        """Test that rate limiter properly cleans old request history."""
        # Arrange
        limiter = RateLimiter()

        # Act - Add some old requests manually
        import time

        old_time = time.time() - 7200  # 2 hours ago

        from finwiz.utils.rate_limiter import RequestRecord

        limiter.request_history[APIProvider.YAHOO_FINANCE].append(RequestRecord(timestamp=old_time, endpoint="old_request"))

        # Make a new request to trigger cleanup
        await limiter.acquire(APIProvider.YAHOO_FINANCE, "new_request")

        # Assert - Old request should be cleaned up
        history = limiter.request_history[APIProvider.YAHOO_FINANCE]
        assert len(history) == 1
        assert history[0].endpoint == "new_request"


@pytest.fixture
def mock_rate_limiter(mocker):
    """Fixture providing a mocked rate limiter for testing."""
    mock_limiter = mocker.Mock()
    mock_limiter.acquire = mocker.AsyncMock(return_value=True)
    mock_limiter.wait_for_availability = mocker.AsyncMock()
    mock_limiter.get_retry_delay = mocker.Mock(return_value=0.1)
    mock_limiter.should_retry = mocker.Mock(return_value=True)
    mock_limiter.record_failure = mocker.Mock()

    mocker.patch("finwiz.utils.rate_limiter.get_rate_limiter", return_value=mock_limiter)
    return mock_limiter
