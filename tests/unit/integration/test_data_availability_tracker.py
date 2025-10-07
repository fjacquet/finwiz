"""
Unit tests for DataAvailabilityTracker.

Tests the data availability tracking functionality including source tracking,
freshness warnings, and summary generation.
"""

from datetime import datetime, timedelta

import pytest

from finwiz.integration.data_availability_tracker import (
    DataAvailabilitySummary,
    DataAvailabilityTracker,
)


class TestDataAvailabilityTracker:
    """Test suite for DataAvailabilityTracker."""

    @pytest.fixture
    def tracker(self):
        """Create a tracker instance for testing."""
        return DataAvailabilityTracker(stale_threshold_hours=168.0)

    @pytest.fixture
    def sample_timestamp(self):
        """Create a sample timestamp for testing."""
        return datetime.now() - timedelta(hours=48)

    def test_should_initialize_with_default_threshold(self):
        """Test that tracker initializes with default stale threshold."""
        # Act
        tracker = DataAvailabilityTracker()

        # Assert
        assert tracker.stale_threshold_hours == 168.0
        assert len(tracker._tracked_sources) == 0

    def test_should_initialize_with_custom_threshold(self):
        """Test that tracker initializes with custom stale threshold."""
        # Act
        tracker = DataAvailabilityTracker(stale_threshold_hours=24.0)

        # Assert
        assert tracker.stale_threshold_hours == 24.0

    def test_should_track_available_data_source(self, tracker, sample_timestamp):
        """Test tracking an available data source."""
        # Act
        tracker.track_data_source(
            source="sentiment",
            status="available",
            age_hours=48.0,
            last_updated=sample_timestamp,
            record_count=100,
        )

        # Assert
        assert "sentiment" in tracker._tracked_sources
        source_status = tracker.get_source_status("sentiment")
        assert source_status is not None
        assert source_status.source_name == "sentiment"
        assert source_status.status == "available"
        assert source_status.age_hours == 48.0
        assert source_status.record_count == 100

    def test_should_track_unavailable_data_source(self, tracker):
        """Test tracking an unavailable data source."""
        # Act
        tracker.track_data_source(
            source="sec_filings",
            status="unavailable",
            error_message="API timeout",
        )

        # Assert
        source_status = tracker.get_source_status("sec_filings")
        assert source_status is not None
        assert source_status.status == "unavailable"
        assert source_status.error_message == "API timeout"

    def test_should_calculate_age_from_last_updated(self, tracker):
        """Test that age_hours is calculated from last_updated if not provided."""
        # Arrange
        last_updated = datetime.now() - timedelta(hours=72)

        # Act
        tracker.track_data_source(
            source="portfolio",
            status="available",
            last_updated=last_updated,
        )

        # Assert
        source_status = tracker.get_source_status("portfolio")
        assert source_status is not None
        assert source_status.age_hours is not None
        # Should be approximately 72 hours (allow small variance)
        assert 71.0 < source_status.age_hours < 73.0

    def test_should_mark_old_data_as_stale(self, tracker):
        """Test that data older than threshold is marked as stale."""
        # Arrange
        old_timestamp = datetime.now() - timedelta(hours=200)

        # Act
        tracker.track_data_source(
            source="discovery",
            status="available",
            last_updated=old_timestamp,
        )

        # Assert
        source_status = tracker.get_source_status("discovery")
        assert source_status is not None
        assert source_status.status == "stale"

    def test_should_generate_availability_summary(self, tracker):
        """Test generating availability summary with multiple sources."""
        # Arrange
        tracker.track_data_source("sentiment", "available", age_hours=24.0)
        tracker.track_data_source("sec_filings", "unavailable", error_message="Not found")
        tracker.track_data_source("portfolio", "available", age_hours=48.0)
        tracker.track_data_source("discovery", "stale", age_hours=200.0)

        # Act
        summary = tracker.get_availability_summary()

        # Assert
        assert isinstance(summary, DataAvailabilitySummary)
        assert summary.total_sources == 4
        assert summary.available_sources == 2
        assert summary.unavailable_sources == 1
        assert summary.stale_sources == 1
        assert len(summary.source_details) == 4

    def test_should_generate_freshness_warnings_for_stale_data(self, tracker):
        """Test that freshness warnings are generated for stale data."""
        # Arrange
        tracker.track_data_source("discovery", "stale", age_hours=200.0)
        tracker.track_data_source("backtesting", "stale", age_hours=300.0)

        # Act
        warnings = tracker.get_freshness_warnings()

        # Assert
        assert len(warnings) == 2
        assert any("discovery" in w for w in warnings)
        assert any("backtesting" in w for w in warnings)
        assert any("8.3 days" in w or "8.4 days" in w for w in warnings)

    def test_should_generate_freshness_warnings_for_unavailable_data(self, tracker):
        """Test that freshness warnings are generated for unavailable data."""
        # Arrange
        tracker.track_data_source(
            "sec_filings",
            "unavailable",
            error_message="API timeout",
        )

        # Act
        warnings = tracker.get_freshness_warnings()

        # Assert
        assert len(warnings) == 1
        assert "sec_filings" in warnings[0]
        assert "not available" in warnings[0].lower()
        assert "API timeout" in warnings[0]

    def test_should_return_none_for_untracked_source(self, tracker):
        """Test that get_source_status returns None for untracked source."""
        # Act
        source_status = tracker.get_source_status("nonexistent")

        # Assert
        assert source_status is None

    def test_should_check_if_source_is_available(self, tracker):
        """Test checking if a source is available."""
        # Arrange
        tracker.track_data_source("sentiment", "available", age_hours=24.0)
        tracker.track_data_source("sec_filings", "unavailable")

        # Act & Assert
        assert tracker.is_source_available("sentiment") is True
        assert tracker.is_source_available("sec_filings") is False
        assert tracker.is_source_available("nonexistent") is False

    def test_should_check_if_source_is_stale(self, tracker):
        """Test checking if a source is stale."""
        # Arrange
        tracker.track_data_source("discovery", "stale", age_hours=200.0)
        tracker.track_data_source("sentiment", "available", age_hours=24.0)

        # Act & Assert
        assert tracker.is_source_stale("discovery") is True
        assert tracker.is_source_stale("sentiment") is False
        assert tracker.is_source_stale("nonexistent") is False

    def test_should_clear_tracked_sources(self, tracker):
        """Test clearing all tracked sources."""
        # Arrange
        tracker.track_data_source("sentiment", "available", age_hours=24.0)
        tracker.track_data_source("sec_filings", "available", age_hours=48.0)
        assert len(tracker._tracked_sources) == 2

        # Act
        tracker.clear_tracked_sources()

        # Assert
        assert len(tracker._tracked_sources) == 0

    def test_should_get_tracked_source_names(self, tracker):
        """Test getting list of tracked source names."""
        # Arrange
        tracker.track_data_source("sentiment", "available", age_hours=24.0)
        tracker.track_data_source("sec_filings", "available", age_hours=48.0)
        tracker.track_data_source("portfolio", "unavailable")

        # Act
        source_names = tracker.get_tracked_source_names()

        # Assert
        assert len(source_names) == 3
        assert "sentiment" in source_names
        assert "sec_filings" in source_names
        assert "portfolio" in source_names

    def test_should_format_summary_for_report(self, tracker):
        """Test formatting availability summary for report display."""
        # Arrange
        tracker.track_data_source("sentiment", "available", age_hours=24.0, record_count=50)
        tracker.track_data_source("sec_filings", "unavailable", error_message="Not found")
        tracker.track_data_source("discovery", "stale", age_hours=200.0)

        # Act
        formatted = tracker.format_summary_for_report()

        # Assert
        assert "Data Availability Summary" in formatted
        assert "Total Data Sources: 3" in formatted
        assert "Available: 1" in formatted
        assert "Unavailable: 1" in formatted
        assert "Stale (>7 days): 1" in formatted
        assert "sentiment" in formatted
        assert "sec_filings" in formatted
        assert "discovery" in formatted
        assert "✅" in formatted  # Available icon
        assert "❌" in formatted  # Unavailable icon
        assert "⚠️" in formatted  # Stale icon

    def test_should_handle_empty_tracker_in_summary(self, tracker):
        """Test generating summary when no sources are tracked."""
        # Act
        summary = tracker.get_availability_summary()

        # Assert
        assert summary.total_sources == 0
        assert summary.available_sources == 0
        assert summary.unavailable_sources == 0
        assert summary.stale_sources == 0
        assert len(summary.freshness_warnings) == 0

    def test_should_handle_error_in_track_data_source(self, tracker, mocker):
        """Test that errors in track_data_source are handled gracefully."""
        # Arrange
        mock_logger = mocker.patch.object(tracker, "logger")

        # Act - Pass invalid data that might cause an error
        tracker.track_data_source(
            source="test",
            status="available",
            age_hours="invalid",  # Invalid type
        )

        # Assert - Should log error
        assert mock_logger.error.called

    def test_should_include_record_count_in_status(self, tracker):
        """Test that record count is included in source status."""
        # Act
        tracker.track_data_source(
            source="sentiment",
            status="available",
            age_hours=24.0,
            record_count=150,
        )

        # Assert
        source_status = tracker.get_source_status("sentiment")
        assert source_status is not None
        assert source_status.record_count == 150

    def test_should_track_multiple_sources_independently(self, tracker):
        """Test that multiple sources are tracked independently."""
        # Act
        tracker.track_data_source("sentiment", "available", age_hours=24.0)
        tracker.track_data_source("sec_filings", "unavailable")
        tracker.track_data_source("portfolio", "stale", age_hours=200.0)
        tracker.track_data_source("discovery", "available", age_hours=48.0)
        tracker.track_data_source("backtesting", "available", age_hours=72.0)

        # Assert
        assert len(tracker._tracked_sources) == 5
        assert tracker.is_source_available("sentiment")
        assert not tracker.is_source_available("sec_filings")
        assert tracker.is_source_stale("portfolio")
        assert tracker.is_source_available("discovery")
        assert tracker.is_source_available("backtesting")

    def test_should_update_existing_source_status(self, tracker):
        """Test that tracking the same source twice updates its status."""
        # Arrange
        tracker.track_data_source("sentiment", "available", age_hours=24.0)

        # Act - Update the same source
        tracker.track_data_source("sentiment", "stale", age_hours=200.0)

        # Assert
        source_status = tracker.get_source_status("sentiment")
        assert source_status is not None
        assert source_status.status == "stale"
        assert source_status.age_hours == 200.0

    def test_should_generate_summary_with_freshness_warnings(self, tracker):
        """Test that summary includes freshness warnings."""
        # Arrange
        tracker.track_data_source("discovery", "stale", age_hours=200.0)
        tracker.track_data_source("sec_filings", "unavailable", error_message="API error")

        # Act
        summary = tracker.get_availability_summary()

        # Assert
        assert len(summary.freshness_warnings) == 2
        assert any("discovery" in w for w in summary.freshness_warnings)
        assert any("sec_filings" in w for w in summary.freshness_warnings)

    def test_should_format_report_with_no_warnings(self, tracker):
        """Test formatting report when all sources are available and fresh."""
        # Arrange
        tracker.track_data_source("sentiment", "available", age_hours=24.0)
        tracker.track_data_source("sec_filings", "available", age_hours=48.0)

        # Act
        formatted = tracker.format_summary_for_report()

        # Assert
        assert "Data Availability Summary" in formatted
        assert "Freshness Warnings:" not in formatted  # No warnings section

    def test_should_handle_none_age_hours(self, tracker):
        """Test handling sources with no age information."""
        # Act
        tracker.track_data_source(
            source="sentiment",
            status="available",
            age_hours=None,
        )

        # Assert
        source_status = tracker.get_source_status("sentiment")
        assert source_status is not None
        assert source_status.age_hours is None
        assert source_status.status == "available"

    def test_should_handle_none_last_updated(self, tracker):
        """Test handling sources with no last_updated timestamp."""
        # Act
        tracker.track_data_source(
            source="sentiment",
            status="available",
            last_updated=None,
        )

        # Assert
        source_status = tracker.get_source_status("sentiment")
        assert source_status is not None
        assert source_status.last_updated is None
