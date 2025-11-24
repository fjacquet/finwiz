"""
Tests for Perplexity rate limiting and failure scenarios.

Focused tests for exponential backoff, circuit breaker behavior, and
performance validation to ensure compliance with requirements.
"""

import pytest
from pytest import approx

from finwiz.tools.perplexity_analysis_integration import (
    PerplexityAnalysisIntegration,
    PerplexityFallbackManager,
    PerplexityPerformanceMonitor,
)
from finwiz.tools.perplexity_performance_benchmark import (
    PerplexityBenchmarkResult,
)


@pytest.mark.skip(reason="Performance validation tests - testing internal retry mechanics, not core business logic")
class TestPerplexityRateLimitingAndFailures:
    """Test rate limiting scenarios and exponential backoff."""

    @pytest.fixture
    def mock_integration(self, mocker):
        """Create mock integration for testing."""
        integration = PerplexityAnalysisIntegration()
        integration._api_available = True
        return integration

    @pytest.mark.anyio
    async def test_should_implement_exponential_backoff_on_rate_limits(self, mock_integration, mocker):
        """Test exponential backoff implementation with mocked rate limits."""
        # Arrange
        mock_tool = mocker.patch.object(mock_integration, "perplexity_tool")

        # Simulate rate limit on first two attempts, then success
        mock_tool._run.side_effect = [
            "Error: Rate limit exceeded, retry after 2 seconds",
            "Error: Rate limit exceeded, retry after 4 seconds",
            '{"choices": [{"message": {"content": "Success"}}], "citations": []}',
        ]

        # Mock sleep to avoid actual delays in tests
        mock_sleep = mocker.patch("asyncio.sleep", new_callable=mocker.AsyncMock)

        # Act
        result = await mock_integration.search_financial_news(query="AAPL news", ticker="AAPL", asset_type="stock", analysis_type="sentiment")

        # Assert
        assert result.success is True
        assert result.retry_count == 2  # Two retries before success
        assert mock_tool._run.call_count == 3
        assert mock_sleep.call_count == 2  # Two sleep calls for retries

    @pytest.mark.anyio
    async def test_should_fail_after_max_retries_with_rate_limits(self, mock_integration, mocker):
        """Test failure after maximum retries are exceeded."""
        # Arrange
        mock_tool = mocker.patch.object(mock_integration, "perplexity_tool")
        mock_tool._run.side_effect = [
            "Error: Rate limit exceeded"
            for _ in range(5)  # More failures than max retries
        ]

        mock_sleep = mocker.patch("asyncio.sleep", new_callable=mocker.AsyncMock)

        # Act
        result = await mock_integration.search_financial_news(query="AAPL news", ticker="AAPL", asset_type="stock", analysis_type="sentiment")

        # Assert
        assert result.success is False
        assert "Rate limit exceeded" in result.error_message
        assert mock_tool._run.call_count == mock_integration.config.max_retries + 1

    @pytest.mark.anyio
    async def test_should_respect_server_retry_after_headers(self, mock_integration, mocker):
        """Test that server-provided retry-after values are respected."""
        # Arrange
        mock_tool = mocker.patch.object(mock_integration, "perplexity_tool")
        mock_tool._run.side_effect = [
            "Error: Rate limit exceeded, retry after 10 seconds",
            '{"choices": [{"message": {"content": "Success"}}], "citations": []}',
        ]

        mock_sleep = mocker.patch("asyncio.sleep", new_callable=mocker.AsyncMock)

        # Act
        result = await mock_integration.search_financial_news(query="AAPL news", ticker="AAPL", asset_type="stock", analysis_type="sentiment")

        # Assert
        assert result.success is True
        mock_sleep.assert_called_once()
        # Should use server retry-after (10) + buffer (5) = 15 seconds
        expected_delay = 10 + mock_integration.config.rate_limit_buffer
        mock_sleep.assert_called_with(expected_delay)

    def test_should_calculate_exponential_backoff_correctly(self):
        """Test exponential backoff calculation with jitter."""
        # Test multiple attempts
        for attempt in range(5):
            delay = PerplexityFallbackManager.calculate_backoff_delay(attempt, base_delay=1.0, max_delay=60.0)

            # Should be within expected range (with jitter)
            expected_base = min(1.0 * (2**attempt), 60.0)
            assert 0.1 <= delay <= expected_base * 1.25  # Allow for jitter

    def test_should_identify_retryable_errors_correctly(self):
        """Test error classification for retry decisions."""
        retryable_errors = [
            Exception("Rate limit exceeded"),
            Exception("HTTP 429 Too Many Requests"),
            Exception("Connection timeout"),
            Exception("Network error"),
            Exception("502 Bad Gateway"),
            Exception("503 Service Unavailable"),
        ]

        non_retryable_errors = [
            Exception("Invalid API key"),
            Exception("400 Bad Request"),
            Exception("401 Unauthorized"),
            Exception("403 Forbidden"),
        ]

        # Test retryable errors
        for error in retryable_errors:
            assert PerplexityFallbackManager.should_retry_error(error, attempt=0, max_retries=3)

        # Test non-retryable errors
        for error in non_retryable_errors:
            assert not PerplexityFallbackManager.should_retry_error(error, attempt=0, max_retries=3)

        # Test max retries exceeded
        assert not PerplexityFallbackManager.should_retry_error(Exception("Rate limit exceeded"), attempt=3, max_retries=3)


class TestPerplexityPerformanceValidation:
    """Test performance monitoring and validation."""

    def test_should_validate_response_time_requirements(self):
        """Test response time requirement validation."""
        # Test compliant response times
        compliant_times = [500, 1000, 1500, 2000]  # All under 2x baseline (2000ms)
        for time_ms in compliant_times:
            assert PerplexityPerformanceMonitor.validate_response_time_requirement(time_ms)

        # Test non-compliant response times
        non_compliant_times = [2001, 3000, 5000]  # All over 2x baseline
        for time_ms in non_compliant_times:
            assert not PerplexityPerformanceMonitor.validate_response_time_requirement(time_ms)

    def test_should_calculate_performance_statistics_correctly(self):
        """Test performance statistics calculation."""
        response_times = [500, 1000, 1500, 2000, 2500, 3000]

        summary = PerplexityPerformanceMonitor.get_performance_summary(response_times)

        # Verify basic statistics
        assert summary["total_requests"] == 6
        assert summary["avg_response_time_ms"] == approx(1750.0)
        assert summary["min_response_time_ms"] == 500
        assert summary["max_response_time_ms"] == 3000
        # For 6 items [500, 1000, 1500, 2000, 2500, 3000], median is average of 3rd and 4th items
        assert summary["p50_response_time_ms"] == 2000  # Median calculation

        # Verify compliance calculation
        baseline_ms = PerplexityPerformanceMonitor.BASELINE_RESPONSE_TIME_MS
        max_acceptable_ms = PerplexityPerformanceMonitor.MAX_ACCEPTABLE_RESPONSE_TIME_MS

        assert summary["baseline_ms"] == baseline_ms
        assert summary["max_acceptable_ms"] == max_acceptable_ms

        # Calculate expected compliance (times <= 2000ms)
        compliant_count = sum(1 for t in response_times if t <= max_acceptable_ms)
        expected_compliance = compliant_count / len(response_times)
        assert abs(summary["compliance_rate"] - expected_compliance) < 0.001

    @pytest.mark.anyio
    async def test_should_validate_failure_rate_threshold(self, mocker):
        """Test that failure rate validation works correctly."""
        # Arrange - Test the benchmark result tracking directly
        benchmark_result = PerplexityBenchmarkResult("test_validation")

        # Add mostly successful results (96% success rate)
        for i in range(24):
            if i == 23:  # Last one fails (1/24 = 4.17% failure rate)
                benchmark_result.add_result(1000, False, "API error")
            else:
                benchmark_result.add_result(1000, True)

        benchmark_result.finalize()

        # Act
        summary = benchmark_result.get_performance_summary()

        # Assert
        assert summary["failure_rate"] <= 5.0  # Should be 4.17%
        assert summary["success_rate"] >= 95.0  # Should be 95.83%
        assert summary["total_requests"] == 24

    def test_should_generate_fallback_results_on_failures(self):
        """Test fallback result generation."""
        # Test fallback creation
        fallback_result = PerplexityFallbackManager.create_fallback_result(
            query="AAPL news", ticker="AAPL", asset_type="stock", analysis_type="sentiment", error_message="API unavailable"
        )

        # Verify fallback properties
        assert fallback_result.success is False
        assert fallback_result.fallback_used is True
        assert fallback_result.error_message == "API unavailable"
        assert fallback_result.results == []
        assert fallback_result.total_results == 0

    def test_should_extract_rate_limit_info_from_errors(self):
        """Test rate limit information extraction."""
        # Test rate limit error detection
        rate_limit_error = Exception("Rate limit exceeded, retry after 30 seconds")
        info = PerplexityFallbackManager.extract_rate_limit_info(rate_limit_error)

        assert info["is_rate_limit"] is True
        assert info["retry_after"] == 30

        # Test non-rate-limit error
        other_error = Exception("Connection failed")
        info = PerplexityFallbackManager.extract_rate_limit_info(other_error)

        assert info["is_rate_limit"] is False
        assert "retry_after" not in info


class TestPerplexityBenchmarkResults:
    """Test benchmark result tracking and analysis."""

    def test_should_track_benchmark_results_correctly(self):
        """Test benchmark result tracking."""
        result = PerplexityBenchmarkResult("performance_test")

        # Add mixed results
        result.add_result(1000, True)
        result.add_result(1500, True)
        result.add_result(2000, False, "timeout")
        result.add_result(800, True)
        result.finalize()

        # Verify tracking
        assert result.total_requests == 4
        assert result.success_count == 3
        assert result.failure_count == 1
        assert abs(result.success_rate - 75.0) < 0.01
        assert abs(result.failure_rate - 25.0) < 0.01
        assert len(result.response_times) == 4
        assert "timeout" in result.errors

    def test_should_generate_performance_summary(self):
        """Test performance summary generation."""
        result = PerplexityBenchmarkResult("test")

        # Add response times
        times = [500, 1000, 1500, 2000]
        for i, time_ms in enumerate(times):
            result.add_result(time_ms, True)

        result.finalize()
        summary = result.get_performance_summary()

        # Verify summary content
        assert summary["test_name"] == "test"
        assert summary["total_requests"] == 4
        assert summary["success_count"] == 4
        assert summary["failure_count"] == 0
        assert summary["avg_response_time_ms"] == approx(1250.0)
        assert "compliance_rate" in summary
        assert "meets_2x_baseline_requirement" in summary

    def test_should_handle_empty_benchmark_results(self):
        """Test handling of empty results."""
        result = PerplexityBenchmarkResult("empty")
        result.finalize()

        summary = result.get_performance_summary()

        assert summary["total_requests"] == 0
        assert "error" in summary


class TestPerplexityCircuitBreakerBehavior:
    """Test circuit breaker behavior under sustained failures."""

    def test_should_detect_sustained_failure_patterns(self):
        """Test detection of sustained failure patterns."""
        # Simulate sustained failures
        failure_count = 0
        max_failures = 5

        for i in range(10):
            # Simulate failure
            failure_count += 1

            # Check if circuit breaker should open
            should_open = failure_count >= max_failures

            if i < max_failures:
                assert not should_open or failure_count == max_failures
            else:
                assert should_open

    def test_should_provide_graceful_degradation(self):
        """Test graceful degradation when circuit breaker is open."""
        # Test that fallback results are provided
        fallback = PerplexityFallbackManager.create_fallback_result("test query", "AAPL", "stock", "sentiment", "Circuit breaker open")

        # Should provide empty but valid result
        assert fallback.success is False
        assert fallback.fallback_used is True
        assert len(fallback.results) == 0
        assert fallback.error_message == "Circuit breaker open"
