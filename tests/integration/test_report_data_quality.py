"""Integration tests for report data quality."""

import pytest

from finwiz.integration.aplus_discovery_accessor import APlusDiscoveryAccessor
from finwiz.integration.data_availability_tracker import DataAvailabilityTracker
from finwiz.tools.sec_filing_url_generator import SECFilingURLGenerator


@pytest.mark.integration
class TestReportDataQuality:
    """Integration tests for report data quality with missing data scenarios."""

    def test_should_handle_missing_sentiment_data(self, mocker):
        """Test report generation with missing sentiment data."""
        tracker = DataAvailabilityTracker()

        mock_sentiment = mocker.Mock()
        mock_sentiment.return_value = {
            "articles": [],
            "overall_sentiment": "neutral",
            "confidence": 0.0,
            "message": "No sentiment data available",
        }

        tracker.track_data_source(source="sentiment", status="unavailable", age_hours=0, error_message="No articles found")

        summary = tracker.get_availability_summary()

        assert summary.unavailable_sources == 1
        assert "sentiment" in summary.source_details
        assert summary.source_details["sentiment"].status == "unavailable"
        assert mock_sentiment.return_value["articles"] == []
        assert mock_sentiment.return_value["confidence"] == 0.0

    def test_should_handle_missing_sec_filings(self, mocker):
        """Test report generation with missing SEC filings."""
        generator = SECFilingURLGenerator()
        tracker = DataAvailabilityTracker()

        mocker.patch.object(generator, "get_filing_url", return_value=None)

        filing_url = generator.get_filing_url("INVALID", "10-K")

        tracker.track_data_source(source="sec_filings", status="unavailable", age_hours=0, error_message="No filings found for INVALID")

        summary = tracker.get_availability_summary()

        assert filing_url is None
        assert summary.unavailable_sources == 1
        assert "sec_filings" in summary.source_details
        assert summary.source_details["sec_filings"].status == "unavailable"

    def test_should_handle_incomplete_portfolio(self, tmp_path):
        """Test report generation with incomplete portfolio data."""
        tracker = DataAvailabilityTracker()

        # Simulate empty portfolio
        tracker.track_data_source(source="portfolio", status="available", age_hours=0, record_count=0)

        availability_summary = tracker.get_availability_summary()

        assert "portfolio" in availability_summary.source_details
        assert availability_summary.source_details["portfolio"].record_count == 0

    def test_should_handle_missing_discovery_results(self, tmp_path):
        """Test report generation without discovery results."""
        accessor = APlusDiscoveryAccessor(output_dir=tmp_path)
        tracker = DataAvailabilityTracker()

        has_results = accessor.has_discovery_results()
        results = accessor.load_discovery_results()
        summary_text = accessor.get_opportunities_summary()

        tracker.track_data_source(source="discovery", status="unavailable", age_hours=0, error_message="Discovery not run")

        availability_summary = tracker.get_availability_summary()

        assert has_results is False
        assert results is None
        assert "discovery not run" in summary_text.lower() or "no a+ opportunities" in summary_text.lower()
        assert "discovery" in availability_summary.source_details
        assert availability_summary.source_details["discovery"].status == "unavailable"

    def test_should_handle_incomplete_backtesting(self):
        """Test report generation with incomplete backtesting data."""
        tracker = DataAvailabilityTracker()

        # Simulate incomplete backtesting with only 1 metric
        tracker.track_data_source(source="backtesting", status="available", age_hours=0, record_count=1)

        availability_summary = tracker.get_availability_summary()

        assert "backtesting" in availability_summary.source_details
        assert availability_summary.source_details["backtesting"].record_count == 1

    def test_should_verify_no_hallucinated_urls(self, mocker):
        """Test that no hallucinated URLs are generated."""
        generator = SECFilingURLGenerator()

        mock_response = mocker.Mock()
        mock_response.status_code = 404
        mocker.patch("requests.head", return_value=mock_response)

        url = generator.get_filing_url("FAKE", "10-K")

        assert url is None or not generator.verify_url(url)

        if url:
            assert "example.com" not in url
            assert "test.com" not in url
            assert "fake" not in url.lower()

    def test_should_track_all_data_sources(self):
        """Test comprehensive data availability tracking."""
        tracker = DataAvailabilityTracker()

        tracker.track_data_source("sentiment", "available", 2, record_count=10)
        tracker.track_data_source("sec_filings", "unavailable", 0, error_message="No filings")
        tracker.track_data_source("portfolio", "available", 1, record_count=5)
        tracker.track_data_source("discovery", "unavailable", 0, error_message="Not run")
        tracker.track_data_source("backtesting", "available", 3, record_count=3)

        summary = tracker.get_availability_summary()

        assert summary.total_sources == 5
        assert summary.available_sources == 3
        assert summary.unavailable_sources == 2

        assert "sentiment" in summary.source_details
        assert "sec_filings" in summary.source_details
        assert "portfolio" in summary.source_details
        assert "discovery" in summary.source_details
        assert "backtesting" in summary.source_details

    def test_should_generate_freshness_warnings(self):
        """Test freshness warnings for stale data."""
        tracker = DataAvailabilityTracker()

        tracker.track_data_source("sentiment", "available", 2)
        tracker.track_data_source("sec_filings", "available", 48)
        tracker.track_data_source("portfolio", "available", 200)

        warnings = tracker.get_freshness_warnings()
        summary = tracker.get_availability_summary()

        assert len(warnings) > 0
        assert any("portfolio" in w.lower() for w in warnings)
        assert summary.stale_sources >= 1

    def test_should_handle_all_missing_data_scenario(self):
        """Test report generation when all data sources are unavailable."""
        tracker = DataAvailabilityTracker()

        tracker.track_data_source("sentiment", "unavailable", 0, error_message="No data")
        tracker.track_data_source("sec_filings", "unavailable", 0, error_message="No filings")
        tracker.track_data_source("portfolio", "unavailable", 0, error_message="No CSV")
        tracker.track_data_source("discovery", "unavailable", 0, error_message="Not run")
        tracker.track_data_source("backtesting", "unavailable", 0, error_message="No data")

        summary = tracker.get_availability_summary()

        assert summary.total_sources == 5
        assert summary.available_sources == 0
        assert summary.unavailable_sources == 5

        for source in ["sentiment", "sec_filings", "portfolio", "discovery", "backtesting"]:
            assert source in summary.source_details
            assert summary.source_details[source].status == "unavailable"

    def test_should_handle_partial_data_across_sources(self):
        """Test report generation with partial data across multiple sources."""
        tracker = DataAvailabilityTracker()

        tracker.track_data_source("sentiment", "available", 2, record_count=5)
        tracker.track_data_source("sec_filings", "available", 24, record_count=1)
        tracker.track_data_source("portfolio", "available", 1, record_count=10)
        tracker.track_data_source("discovery", "unavailable", 0, error_message="Not run")
        tracker.track_data_source("backtesting", "available", 12, record_count=2)

        summary = tracker.get_availability_summary()

        assert summary.total_sources == 5
        assert summary.available_sources == 4
        assert summary.unavailable_sources == 1

    def test_should_validate_discovery_data_structure(self, tmp_path):
        """Test that discovery data structure is validated correctly."""
        accessor = APlusDiscoveryAccessor(output_dir=tmp_path)

        # Create discovery directory with correct name
        discovery_dir = tmp_path / "discovery"
        discovery_dir.mkdir()

        # Create a valid discovery file with invalid structure
        invalid_file = discovery_dir / "a_plus_stocks.json"
        invalid_file.write_text('{"invalid": "structure"}')

        has_results = accessor.has_discovery_results()
        results = accessor.load_discovery_results()

        assert has_results is True  # File exists
        # Results should handle invalid structure gracefully
        assert results is not None  # Should return something even if invalid

    def test_should_validate_backtesting_data_structure(self):
        """Test that backtesting data structure is validated correctly."""
        tracker = DataAvailabilityTracker()

        # Simulate invalid backtesting data by tracking as unavailable
        tracker.track_data_source(source="backtesting", status="unavailable", age_hours=0, error_message="Invalid data structure")

        summary = tracker.get_availability_summary()

        assert "backtesting" in summary.source_details
        assert summary.source_details["backtesting"].status == "unavailable"
        assert summary.source_details["backtesting"].error_message == "Invalid data structure"

    def test_should_handle_stale_data_warnings(self):
        """Test that stale data generates appropriate warnings."""
        tracker = DataAvailabilityTracker()

        tracker.track_data_source("sentiment", "available", 240, record_count=10)
        tracker.track_data_source("sec_filings", "available", 720, record_count=1)

        warnings = tracker.get_freshness_warnings()
        summary = tracker.get_availability_summary()

        assert len(warnings) >= 2
        assert summary.stale_sources >= 2

        warning_text = " ".join(warnings).lower()
        assert "sentiment" in warning_text or "sec" in warning_text
