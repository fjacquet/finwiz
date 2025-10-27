"""
Unit tests for DataQualityMetrics class.

Tests the data quality metrics tracking functionality to ensure
proper recording and calculation of quality scores.
"""

import json

import pytest

from finwiz.utils.data_quality_metrics import DataQualityMetrics


class TestDataQualityMetrics:
    """Test suite for DataQualityMetrics."""

    @pytest.fixture
    def metrics(self):
        """Create a fresh metrics instance for each test."""
        return DataQualityMetrics(flow_execution_id="test-flow-123")

    def test_should_initialize_with_zero_counts(self, metrics):
        """Test that metrics initialize with zero counts."""
        # Assert
        assert metrics.fallback_grades_count == 0
        assert metrics.placeholder_urls_count == 0
        assert metrics.missing_data_count == 0
        assert metrics.successful_merges_count == 0
        assert metrics.failed_merges_count == 0
        assert metrics.fallback_tickers == []
        assert metrics.placeholder_url_locations == []
        assert metrics.missing_data_fields == []

    def test_should_record_fallback_grade(self, metrics):
        """Test recording fallback grade usage."""
        # Act
        metrics.record_fallback_grade("AAPL")
        metrics.record_fallback_grade("GOOGL")

        # Assert
        assert metrics.fallback_grades_count == 2
        assert "AAPL" in metrics.fallback_tickers
        assert "GOOGL" in metrics.fallback_tickers

    def test_should_not_duplicate_fallback_tickers(self, metrics):
        """Test that duplicate ticker recordings don't create duplicates in list."""
        # Act
        metrics.record_fallback_grade("AAPL")
        metrics.record_fallback_grade("AAPL")
        metrics.record_fallback_grade("AAPL")

        # Assert
        assert metrics.fallback_grades_count == 3
        assert metrics.fallback_tickers.count("AAPL") == 1

    def test_should_record_placeholder_url(self, metrics):
        """Test recording placeholder URL detection."""
        # Act
        metrics.record_placeholder_url("sec_filing")
        metrics.record_placeholder_url("company_website")

        # Assert
        assert metrics.placeholder_urls_count == 2
        assert "sec_filing" in metrics.placeholder_url_locations
        assert "company_website" in metrics.placeholder_url_locations

    def test_should_record_missing_data(self, metrics):
        """Test recording missing data fields."""
        # Act
        metrics.record_missing_data("deep_analysis_AAPL")
        metrics.record_missing_data("alternatives_GOOGL")

        # Assert
        assert metrics.missing_data_count == 2
        assert "deep_analysis_AAPL" in metrics.missing_data_fields
        assert "alternatives_GOOGL" in metrics.missing_data_fields

    def test_should_record_successful_merge(self, metrics):
        """Test recording successful merge operations."""
        # Act
        metrics.record_successful_merge("AAPL")
        metrics.record_successful_merge("GOOGL")
        metrics.record_successful_merge("MSFT")

        # Assert
        assert metrics.successful_merges_count == 3

    def test_should_record_failed_merge(self, metrics):
        """Test recording failed merge operations."""
        # Act
        metrics.record_failed_merge("AAPL", "Verification failed")
        metrics.record_failed_merge("GOOGL", "Missing data")

        # Assert
        assert metrics.failed_merges_count == 2

    def test_should_calculate_quality_score_perfect(self, metrics):
        """Test quality score calculation with perfect quality."""
        # Arrange - All successful, no issues
        metrics.record_successful_merge("AAPL")
        metrics.record_successful_merge("GOOGL")
        metrics.record_successful_merge("MSFT")

        # Act
        score = metrics.calculate_quality_score()

        # Assert
        assert score == 1.0

    def test_should_calculate_quality_score_with_penalties(self, metrics):
        """Test quality score calculation with penalties."""
        # Arrange
        metrics.record_successful_merge("AAPL")
        metrics.record_successful_merge("GOOGL")
        metrics.record_fallback_grade("IBM")  # 1 penalty
        metrics.record_placeholder_url("sec_filing")  # 1 penalty

        # Act
        score = metrics.calculate_quality_score()

        # Assert
        # 2 successful operations, 2 penalties
        # penalty_ratio = 2 / 2 = 1.0
        # score = max(0.0, 1.0 - 1.0) = 0.0
        assert score == 0.0

    def test_should_calculate_quality_score_with_failed_merges(self, metrics):
        """Test that failed merges count double in penalties."""
        # Arrange
        metrics.record_successful_merge("AAPL")
        metrics.record_successful_merge("GOOGL")
        metrics.record_failed_merge("IBM", "Verification failed")  # 2 penalties

        # Act
        score = metrics.calculate_quality_score()

        # Assert
        # 3 total operations (2 successful + 1 failed)
        # 2 penalties (failed merge counts as 2)
        # penalty_ratio = 2 / 3 = 0.667
        # score = max(0.0, 1.0 - 0.667) = 0.333
        assert score == pytest.approx(0.333, abs=0.01)

    def test_should_return_neutral_score_with_no_operations(self, metrics):
        """Test quality score returns 0.5 when no operations recorded."""
        # Act
        score = metrics.calculate_quality_score()

        # Assert
        assert score == 0.5

    def test_should_get_quality_grade_a_plus(self, metrics):
        """Test quality grade A+ for score >= 0.95."""
        # Arrange
        for i in range(20):
            metrics.record_successful_merge(f"TICKER{i}")

        # Act
        score = metrics.calculate_quality_score()
        grade = metrics._get_quality_grade(score)

        # Assert
        assert score >= 0.95
        assert grade == "A+"

    def test_should_get_quality_grade_f(self, metrics):
        """Test quality grade F for score < 0.60."""
        # Arrange
        metrics.record_successful_merge("AAPL")
        metrics.record_fallback_grade("IBM")
        metrics.record_fallback_grade("GE")
        metrics.record_placeholder_url("url1")
        metrics.record_placeholder_url("url2")

        # Act
        score = metrics.calculate_quality_score()
        grade = metrics._get_quality_grade(score)

        # Assert
        assert score < 0.60
        assert grade == "F"

    def test_should_get_summary(self, metrics):
        """Test getting metrics summary."""
        # Arrange
        metrics.record_successful_merge("AAPL")
        metrics.record_fallback_grade("IBM")
        metrics.record_placeholder_url("sec_filing")

        # Act
        summary = metrics.get_summary()

        # Assert
        assert "quality_score" in summary
        assert "quality_grade" in summary
        assert "metrics" in summary
        assert "details" in summary
        assert summary["metrics"]["successful_merges"] == 1
        assert summary["metrics"]["fallback_grades"] == 1
        assert summary["metrics"]["placeholder_urls"] == 1
        assert "IBM" in summary["details"]["fallback_tickers"]

    def test_should_export_to_file(self, metrics, tmp_path):
        """Test exporting metrics to JSON file."""
        # Arrange
        metrics.record_successful_merge("AAPL")
        metrics.record_fallback_grade("IBM")

        # Act
        filepath = metrics.export_to_file(tmp_path)

        # Assert
        assert filepath.exists()
        assert filepath.suffix == ".json"

        # Verify file contents
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

        assert data["quality_score"] is not None
        assert data["metrics"]["successful_merges"] == 1
        assert data["metrics"]["fallback_grades"] == 1

    def test_should_reset_metrics(self, metrics):
        """Test resetting all metrics to zero."""
        # Arrange
        metrics.record_successful_merge("AAPL")
        metrics.record_fallback_grade("IBM")
        metrics.record_placeholder_url("url")

        # Act
        metrics.reset()

        # Assert
        assert metrics.fallback_grades_count == 0
        assert metrics.placeholder_urls_count == 0
        assert metrics.missing_data_count == 0
        assert metrics.successful_merges_count == 0
        assert metrics.failed_merges_count == 0
        assert metrics.fallback_tickers == []
        assert metrics.placeholder_url_locations == []
        assert metrics.missing_data_fields == []

    def test_should_include_flow_execution_id(self, metrics):
        """Test that flow execution ID is included in summary."""
        # Act
        summary = metrics.get_summary()

        # Assert
        assert summary["flow_execution_id"] == "test-flow-123"

    def test_should_have_timestamp(self, metrics):
        """Test that metrics include timestamp."""
        # Act
        summary = metrics.get_summary()

        # Assert
        assert "timestamp" in summary
        assert summary["timestamp"] is not None
