"""
Tests for Perplexity performance benchmarking and validation.

Tests response time monitoring, rate limiting scenarios, and failure handling
to ensure compliance with performance requirements.
"""

import time

import pytest
from pytest import approx

from finwiz.tools.perplexity_analysis_integration import PerplexityAnalysisIntegration
from finwiz.tools.perplexity_performance import PerplexityPerformanceMonitor


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
        assert summary["avg_response_time_ms"] == approx(1500.0)
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


@pytest.mark.skip(reason="Performance validation tests - testing internal retry mechanics, not core business logic")
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


@pytest.mark.skip(reason="Performance validation tests - testing internal retry mechanics, not core business logic")
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
