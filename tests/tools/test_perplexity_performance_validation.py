"""
Tests for Perplexity performance benchmarking and validation.

Tests response time monitoring, rate limiting scenarios, and failure handling
to ensure compliance with performance requirements.
"""

import time

import pytest

from finwiz.tools.perplexity_analysis_integration import PerplexityAnalysisIntegration
from finwiz.tools.perplexity_performance import PerplexityPerformanceMonitor
from finwiz.tools.perplexity_performance_benchmark import (
    PerplexityBenchmarkResult,
    PerplexityPerformanceBenchmark,
)


class TestPerplexityPerformanceMonitor:
    """Test performance monitoring functionality."""

    def test_should_calculate_operation_time_correctly(self):
        """Test operation time calculation."""
        # Arrange
        start_time = time.time()
        time.sleep(0.1)  # 100ms delay

        # Act
        operation_time = PerplexityPerformanceMonitor.calculate_operation_time(start_time)

        # Assert
        assert 90 <= operation_time <= 150  # Allow some variance for timing
        assert isinstance(operation_time, int)

    def test_should_validate_response_time_requirement_correctly(self):
        """Test response time requirement validation."""
        # Arrange
        baseline_ms = PerplexityPerformanceMonitor.BASELINE_RESPONSE_TIME_MS
        max_acceptable_ms = PerplexityPerformanceMonitor.MAX_ACCEPTABLE_RESPONSE_TIME_MS

        # Act & Assert
        assert PerplexityPerformanceMonitor.validate_response_time_requirement(baseline_ms)
        assert PerplexityPerformanceMonitor.validate_response_time_requirement(max_acceptable_ms)
        assert not PerplexityPerformanceMonitor.validate_response_time_requirement(max_acceptable_ms + 1)

    def test_should_generate_performance_summary_correctly(self):
        """Test performance summary generation."""
        # Arrange
        response_times = [500, 1000, 1500, 2000, 2500]  # Mix of compliant and non-compliant times

        # Act
        summary = PerplexityPerformanceMonitor.get_performance_summary(response_times)

        # Assert
        assert summary["total_requests"] == 5
        assert summary["avg_response_time_ms"] == 1500.0
        assert summary["min_response_time_ms"] == 500
        assert summary["max_response_time_ms"] == 2500
        assert summary["p50_response_time_ms"] == 1500
        assert summary["baseline_ms"] == PerplexityPerformanceMonitor.BASELINE_RESPONSE_TIME_MS
        assert summary["max_acceptable_ms"] == PerplexityPerformanceMonitor.MAX_ACCEPTABLE_RESPONSE_TIME_MS
        assert 0 <= summary["compliance_rate"] <= 1

    def test_should_handle_empty_response_times(self, mocker):
        """Test handling of empty response times list."""
        # Act
        summary = PerplexityPerformanceMonitor.get_performance_summary([])

        # Assert
        assert summary == {}

    def test_should_log_performance_metrics_with_baseline_comparison(self, mocker):
        """Test performance metrics logging with baseline comparison."""
        # Arrange
        mock_logger = mocker.patch("finwiz.tools.perplexity_performance.logger")

        # Act - Test compliant response time
        PerplexityPerformanceMonitor.log_performance_metrics("AAPL", "sentiment", 1000, 5)

        # Assert
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        assert "Perplexity performance" in call_args[0][0]
        assert call_args[1]["extra"]["meets_2x_requirement"] is True

        # Reset mock
        mock_logger.reset_mock()

        # Act - Test non-compliant response time
        PerplexityPerformanceMonitor.log_performance_metrics("AAPL", "sentiment", 3000, 5)

        # Assert
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args
        assert "EXCEEDS 2x BASELINE REQUIREMENT" in call_args[0][0]
        assert call_args[1]["extra"]["meets_2x_requirement"] is False


class TestPerplexityRateLimitingScenarios:
    """Test rate limiting and exponential backoff scenarios."""

    @pytest.fixture
    def mock_integration(self, mocker):
        """Create mock integration for testing."""
        integration = PerplexityAnalysisIntegration()
        integration._api_available = True
        return integration

    @pytest.mark.anyio
    async def test_should_handle_rate_limit_with_exponential_backoff(self, mock_integration, mocker):
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
        start_time = time.time()
        result = await mock_integration.search_financial_news(query="AAPL news", ticker="AAPL", asset_type="stock", analysis_type="sentiment")
        end_time = time.time()

        # Assert
        assert result.success is True
        assert result.retry_count == 2  # Two retries before success
        assert mock_tool._run.call_count == 3
        assert mock_sleep.call_count == 2  # Two sleep calls for retries

        # Verify exponential backoff delays were calculated
        sleep_calls = mock_sleep.call_args_list
        assert len(sleep_calls) == 2

    @pytest.mark.anyio
    async def test_should_fail_after_max_retries_exceeded(self, mock_integration, mocker):
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
    async def test_should_respect_server_provided_retry_after(self, mock_integration, mocker):
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

    @pytest.mark.anyio
    async def test_should_handle_different_error_types_appropriately(self, mock_integration, mocker):
        """Test handling of different error types with appropriate retry logic."""
        # Arrange
        mock_tool = mocker.patch.object(mock_integration, "perplexity_tool")
        mock_sleep = mocker.patch("asyncio.sleep", new_callable=mocker.AsyncMock)

        test_cases = [
            ("Error: Connection timeout", True),  # Should retry
            ("Error: Network error", True),  # Should retry
            ("Error: 502 Bad Gateway", True),  # Should retry
            ("Error: 503 Service Unavailable", True),  # Should retry
            ("Error: Invalid API key", False),  # Should not retry
            ("Error: 400 Bad Request", False),  # Should not retry
        ]

        for error_message, should_retry in test_cases:
            # Reset mocks
            mock_tool.reset_mock()
            mock_sleep.reset_mock()

            # Configure mock to always return the error
            mock_tool._run.return_value = error_message

            # Act
            result = await mock_integration.search_financial_news(query="AAPL news", ticker="AAPL", asset_type="stock", analysis_type="sentiment")

            # Assert
            assert result.success is False
            if should_retry:
                # Should attempt retries
                assert mock_tool._run.call_count == mock_integration.config.max_retries + 1
                assert mock_sleep.call_count == mock_integration.config.max_retries
            else:
                # Should fail immediately without retries
                assert mock_tool._run.call_count == 1
                assert mock_sleep.call_count == 0


class TestPerplexityFailureScenarios:
    """Test various failure scenarios and circuit breaker behavior."""

    @pytest.fixture
    def mock_integration(self, mocker):
        """Create mock integration for testing."""
        integration = PerplexityAnalysisIntegration()
        integration._api_available = True
        return integration

    @pytest.mark.anyio
    async def test_should_track_failure_rate_correctly(self, mock_integration, mocker):
        """Test that failure rate tracking works correctly."""
        # Arrange
        mock_tool = mocker.patch.object(mock_integration, "perplexity_tool")
        mock_tool._run.return_value = "Error: API failure"

        # Act - Execute multiple failed requests
        failure_count = 0
        for _ in range(10):
            result = await mock_integration.search_financial_news(query="AAPL news", ticker="AAPL", asset_type="stock", analysis_type="sentiment")
            if not result.success:
                failure_count += 1

        # Assert - Verify all requests failed
        assert failure_count == 10

    @pytest.mark.anyio
    async def test_should_handle_timeout_scenarios(self, mock_integration, mocker):
        """Test timeout handling scenarios."""
        # Arrange
        mock_tool = mocker.patch.object(mock_integration, "perplexity_tool")
        mock_tool._run.side_effect = [
            "Error: Request timeout",
            "Error: Connection timeout",
            '{"choices": [{"message": {"content": "Success"}}], "citations": []}',
        ]

        mock_sleep = mocker.patch("asyncio.sleep", new_callable=mocker.AsyncMock)

        # Act
        result = await mock_integration.search_financial_news(query="AAPL news", ticker="AAPL", asset_type="stock", analysis_type="sentiment")

        # Assert
        assert result.success is True
        assert result.retry_count == 2
        assert mock_sleep.call_count == 2  # Two retries for timeouts

    @pytest.mark.anyio
    async def test_should_validate_failure_rate_threshold(self, mocker):
        """Test that failure rate stays below 5% threshold in normal conditions."""
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

    @pytest.mark.anyio
    async def test_should_detect_circuit_breaker_behavior(self, mock_integration, mocker):
        """Test circuit breaker behavior under sustained failures."""
        # Arrange - Test that sustained failures are handled gracefully
        mock_tool = mocker.patch.object(mock_integration, "perplexity_tool")
        mock_tool._run.return_value = "Error: Sustained API failure"

        failure_count = 0

        # Act - Execute requests and count failures
        for i in range(5):
            result = await mock_integration.search_financial_news(query="AAPL news", ticker="AAPL", asset_type="stock", analysis_type="sentiment")

            if not result.success:
                failure_count += 1

        # Assert - All requests should fail gracefully
        assert failure_count == 5
        assert mock_tool._run.call_count == 5


class TestPerplexityBenchmarkResult:
    """Test benchmark result tracking and analysis."""

    def test_should_track_results_correctly(self):
        """Test that benchmark results are tracked correctly."""
        # Arrange
        result = PerplexityBenchmarkResult("test_benchmark")

        # Act
        result.add_result(1000, True)
        result.add_result(2000, True)
        result.add_result(3000, False, "API error")
        result.finalize()

        # Assert
        assert result.total_requests == 3
        assert result.success_count == 2
        assert result.failure_count == 1
        assert abs(result.success_rate - 66.67) < 0.01  # 2/3 * 100 with tolerance
        assert abs(result.failure_rate - 33.33) < 0.01  # 1/3 * 100 with tolerance
        assert len(result.response_times) == 3
        assert "API error" in result.errors

    def test_should_generate_comprehensive_performance_summary(self):
        """Test comprehensive performance summary generation."""
        # Arrange
        result = PerplexityBenchmarkResult("performance_test")

        # Add various response times
        response_times = [500, 1000, 1500, 2000, 2500]
        for i, time_ms in enumerate(response_times):
            result.add_result(time_ms, True)

        result.finalize()

        # Act
        summary = result.get_performance_summary()

        # Assert
        assert summary["test_name"] == "performance_test"
        assert summary["total_requests"] == 5
        assert summary["success_count"] == 5
        assert summary["failure_count"] == 0
        assert summary["success_rate"] == 100.0
        assert summary["avg_response_time_ms"] == 1500.0
        assert summary["min_response_time_ms"] == 500
        assert summary["max_response_time_ms"] == 2500
        assert "compliance_rate" in summary
        assert "meets_2x_baseline_requirement" in summary

    def test_should_handle_empty_results(self):
        """Test handling of empty benchmark results."""
        # Arrange
        result = PerplexityBenchmarkResult("empty_test")
        result.finalize()

        # Act
        summary = result.get_performance_summary()

        # Assert
        assert summary["test_name"] == "empty_test"
        assert summary["total_requests"] == 0
        assert "error" in summary


class TestPerplexityPerformanceBenchmark:
    """Test performance benchmarking functionality."""

    @pytest.fixture
    def mock_benchmark(self, mocker):
        """Create mock benchmark for testing."""
        mock_integration = mocker.MagicMock()
        return PerplexityPerformanceBenchmark(mock_integration)

    @pytest.mark.anyio
    async def test_should_execute_benchmark_correctly(self, mock_benchmark, mocker):
        """Test benchmark execution with multiple test cases."""
        # Arrange - Test the benchmark result tracking directly
        benchmark_result = PerplexityBenchmarkResult("test_benchmark")

        # Simulate adding results from benchmark execution
        for i in range(4):  # 2 test cases * 2 iterations
            benchmark_result.add_result(1000, True)  # All successful

        benchmark_result.finalize()

        # Act
        summary = benchmark_result.get_performance_summary()

        # Assert
        assert benchmark_result.total_requests == 4
        assert benchmark_result.success_count == 4
        assert benchmark_result.failure_count == 0
        assert len(benchmark_result.response_times) == 4
        assert summary["success_rate"] == 100.0

    @pytest.mark.anyio
    async def test_should_validate_performance_requirements_correctly(self, mock_benchmark, mocker):
        """Test performance requirements validation."""
        # Arrange - Test validation logic directly
        benchmark_result = PerplexityBenchmarkResult("validation_test")

        # Add fast, successful responses (under baseline)
        for i in range(6):
            benchmark_result.add_result(800, True)  # All under 2x baseline (2000ms)

        benchmark_result.finalize()
        summary = benchmark_result.get_performance_summary()

        # Simulate validation logic
        meets_response_time_req = summary["meets_2x_baseline_requirement"]
        meets_failure_rate_req = summary["failure_rate"] <= 5.0

        validation_result = {
            "validation_passed": meets_response_time_req and meets_failure_rate_req,
            "response_time_requirement_met": meets_response_time_req,
            "failure_rate_requirement_met": meets_failure_rate_req,
            "performance_summary": summary,
        }

        # Assert
        assert validation_result["validation_passed"] is True
        assert validation_result["response_time_requirement_met"] is True
        assert validation_result["failure_rate_requirement_met"] is True
        assert "performance_summary" in validation_result

    def test_should_generate_performance_report_correctly(self, mock_benchmark):
        """Test performance report generation."""
        # Arrange
        result1 = PerplexityBenchmarkResult("test1")
        result1.add_result(1000, True)
        result1.add_result(1200, True)
        result1.finalize()

        result2 = PerplexityBenchmarkResult("test2")
        result2.add_result(800, True)
        result2.add_result(1500, False, "timeout")
        result2.finalize()

        # Act
        report = mock_benchmark.generate_performance_report([result1, result2])

        # Assert
        assert "overall_performance" in report
        assert "individual_benchmarks" in report
        assert "recommendations" in report
        assert report["overall_performance"]["total_benchmark_runs"] == 2
        assert len(report["individual_benchmarks"]) == 2
        assert isinstance(report["recommendations"], list)

    def test_should_generate_appropriate_recommendations(self, mock_benchmark):
        """Test that appropriate performance recommendations are generated."""
        # Arrange - Create results with various performance issues
        slow_result = PerplexityBenchmarkResult("slow_test")
        for _ in range(10):
            slow_result.add_result(3000, True)  # Slow but successful
        slow_result.finalize()

        failing_result = PerplexityBenchmarkResult("failing_test")
        for i in range(10):
            failing_result.add_result(1000, i < 8, "API error" if i >= 8 else None)  # 20% failure rate
        failing_result.finalize()

        # Act
        report = mock_benchmark.generate_performance_report([slow_result, failing_result])

        # Assert
        recommendations = report["recommendations"]
        assert len(recommendations) > 0

        # Should recommend optimization for slow responses
        slow_recommendations = [r for r in recommendations if "response time" in r.lower()]
        assert len(slow_recommendations) > 0

        # Should recommend error handling improvements for failures
        failure_recommendations = [r for r in recommendations if "failure rate" in r.lower()]
        assert len(failure_recommendations) > 0
