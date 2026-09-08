"""Tests for Perplexity backoff, error classification and fallback behaviour.

These cover the pure helpers on ``PerplexityFallbackManager`` and
``PerplexityPerformanceMonitor``. The end-to-end retry tests that used to live
here were deleted: they drove a real ``PerplexityAnalysisIntegration``, which
now refuses to construct without an API key, so they had been failing at
fixture setup behind a class-level skip rather than testing anything.
"""

from pytest import approx

from finwiz.tools.perplexity_analysis_integration import (
    PerplexityFallbackManager,
    PerplexityPerformanceMonitor,
)


class TestPerplexityFallbackManager:
    """Backoff calculation and retry classification — pure functions, no API client."""

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


class TestPerplexityCircuitBreakerBehavior:
    """Degradation behaviour when the circuit breaker is open."""

    def test_should_provide_graceful_degradation(self):
        """Test graceful degradation when circuit breaker is open."""
        # Test that fallback results are provided
        fallback = PerplexityFallbackManager.create_fallback_result("test query", "AAPL", "stock", "sentiment", "Circuit breaker open")

        # Should provide empty but valid result
        assert fallback.success is False
        assert fallback.fallback_used is True
        assert len(fallback.results) == 0
        assert fallback.error_message == "Circuit breaker open"
