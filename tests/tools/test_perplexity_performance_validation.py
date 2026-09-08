"""Tests for PerplexityPerformanceMonitor.

Covers operation timing, the 2x-baseline response-time requirement, the
summary statistics, and the warning logged when a call breaches the baseline.
"""

import time

from pytest import approx

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
