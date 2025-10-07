"""
Unit tests for Report Crew Data Availability Tracker integration.

Tests that the DataAvailabilityTracker is properly integrated into the report crew
and tracks all data sources as they are accessed during report generation.
"""


import pytest

from finwiz.crews.report_crew.report_crew import ReportCrew


class TestReportCrewAvailabilityTracker:
    """Test suite for Report Crew availability tracker integration."""

    @pytest.fixture
    def mock_data_accessor(self, mocker):
        """Create mock data accessor with availability report."""
        mock = mocker.Mock()

        # Mock availability report
        availability_report = mocker.Mock()
        availability_report.stock_available = True
        availability_report.stock_age_hours = 2.0
        availability_report.etf_available = True
        availability_report.etf_age_hours = 3.0
        availability_report.crypto_available = False
        availability_report.portfolio_available = True
        availability_report.portfolio_age_hours = 1.0
        availability_report.missing_data = ["crypto"]
        availability_report.stale_data = []

        mock.check_data_availability.return_value = availability_report
        mock.get_stale_data_warnings.return_value = []

        # Mock consolidated reporter input
        mock.get_consolidated_reporter_input.return_value = {
            "stock_analysis_data": [{"ticker": "AAPL"}],
            "etf_analysis_data": [{"ticker": "SPY"}],
            "crypto_analysis_data": [],
            "portfolio_review": {"holdings": [{"ticker": "AAPL"}]}
        }

        return mock

    @pytest.fixture
    def mock_discovery_accessor(self, mocker):
        """Create mock discovery accessor."""
        mock = mocker.Mock()
        mock.has_discovery_results.return_value = True
        mock.load_discovery_results.return_value = {
            "opportunities": [{"ticker": "MSFT", "grade": "A+"}]
        }
        mock.get_opportunities_summary.return_value = "1 A+ opportunity found"
        return mock

    @pytest.fixture
    def mock_backtesting_extractor(self, mocker):
        """Create mock backtesting extractor."""
        mock = mocker.Mock()
        return mock

    @pytest.fixture
    def report_crew(self, mocker, mock_data_accessor, mock_discovery_accessor, mock_backtesting_extractor):
        """Create report crew instance with mocked dependencies."""
        # Mock the initialization to avoid file I/O
        mocker.patch("finwiz.crews.report_crew.report_crew.Path")
        mocker.patch("builtins.open", mocker.mock_open(read_data="{}"))
        mocker.patch("yaml.safe_load", return_value={})

        # Create crew instance
        crew = ReportCrew()

        # Replace with mocks
        crew.data_accessor = mock_data_accessor
        crew.discovery_accessor = mock_discovery_accessor
        crew.backtesting_extractor = mock_backtesting_extractor

        return crew

    def test_should_initialize_availability_tracker(self, report_crew):
        """Test that availability tracker is initialized."""
        assert hasattr(report_crew, "availability_tracker")
        assert report_crew.availability_tracker is not None
        assert report_crew.availability_tracker.stale_threshold_hours == 168.0

    def test_should_track_stock_crew_data_when_available(self, report_crew):
        """Test tracking of available stock crew data."""
        # Act
        context = report_crew.get_integrated_data_context(max_age_hours=24)

        # Assert
        stock_status = report_crew.availability_tracker.get_source_status("stock_crew")
        assert stock_status is not None
        assert stock_status.status == "available"
        assert stock_status.age_hours == 2.0
        assert stock_status.record_count == 1

    def test_should_track_etf_crew_data_when_available(self, report_crew):
        """Test tracking of available ETF crew data."""
        # Act
        context = report_crew.get_integrated_data_context(max_age_hours=24)

        # Assert
        etf_status = report_crew.availability_tracker.get_source_status("etf_crew")
        assert etf_status is not None
        assert etf_status.status == "available"
        assert etf_status.age_hours == 3.0
        assert etf_status.record_count == 1

    def test_should_track_crypto_crew_data_when_unavailable(self, report_crew):
        """Test tracking of unavailable crypto crew data."""
        # Act
        context = report_crew.get_integrated_data_context(max_age_hours=24)

        # Assert
        crypto_status = report_crew.availability_tracker.get_source_status("crypto_crew")
        assert crypto_status is not None
        assert crypto_status.status == "unavailable"
        assert crypto_status.error_message == "Crypto crew data not found"

    def test_should_track_portfolio_data_when_available(self, report_crew):
        """Test tracking of available portfolio data."""
        # Act
        context = report_crew.get_integrated_data_context(max_age_hours=24)

        # Assert
        portfolio_status = report_crew.availability_tracker.get_source_status("portfolio_review")
        assert portfolio_status is not None
        assert portfolio_status.status == "available"
        assert portfolio_status.age_hours == 1.0
        assert portfolio_status.record_count == 1

    def test_should_track_discovery_data_when_available(self, report_crew):
        """Test tracking of available discovery data."""
        # Act
        context = report_crew.get_integrated_data_context(max_age_hours=24)

        # Assert
        discovery_status = report_crew.availability_tracker.get_source_status("aplus_discovery")
        assert discovery_status is not None
        assert discovery_status.status == "available"
        assert discovery_status.record_count == 1

    def test_should_track_discovery_data_when_unavailable(self, report_crew):
        """Test tracking of unavailable discovery data."""
        # Arrange
        report_crew.discovery_accessor.has_discovery_results.return_value = False

        # Act
        context = report_crew.get_integrated_data_context(max_age_hours=24)

        # Assert
        discovery_status = report_crew.availability_tracker.get_source_status("aplus_discovery")
        assert discovery_status is not None
        assert discovery_status.status == "unavailable"
        assert "not run" in discovery_status.error_message.lower()

    def test_should_track_backtesting_data_when_available(self, report_crew, mocker):
        """Test tracking of available backtesting data."""
        # Arrange
        mocker.patch.object(
            report_crew,
            "_extract_backtesting_data",
            return_value={
                "has_backtesting_data": True,
                "message": "Backtesting data available",
                "status": "available",
                "backtesting_by_candidate": {"MSFT": {}},
                "total_candidates": 1
            }
        )

        # Act
        context = report_crew.get_integrated_data_context(max_age_hours=24)

        # Assert
        backtesting_status = report_crew.availability_tracker.get_source_status("backtesting")
        assert backtesting_status is not None
        assert backtesting_status.status == "available"
        assert backtesting_status.record_count == 1

    def test_should_track_backtesting_data_when_unavailable(self, report_crew, mocker):
        """Test tracking of unavailable backtesting data."""
        # Arrange
        mocker.patch.object(
            report_crew,
            "_extract_backtesting_data",
            return_value={
                "has_backtesting_data": False,
                "message": "Backtesting data not available - discovery not run",
                "status": "not_available"
            }
        )

        # Act
        context = report_crew.get_integrated_data_context(max_age_hours=24)

        # Assert
        backtesting_status = report_crew.availability_tracker.get_source_status("backtesting")
        assert backtesting_status is not None
        assert backtesting_status.status == "unavailable"
        assert "not available" in backtesting_status.error_message.lower()

    def test_should_include_availability_summary_in_context(self, report_crew):
        """Test that availability summary is included in integrated context."""
        # Act
        context = report_crew.get_integrated_data_context(max_age_hours=24)

        # Assert
        assert "data_availability_summary" in context
        assert "data_availability_summary_formatted" in context

        summary = context["data_availability_summary"]
        assert "total_sources" in summary
        assert "available_sources" in summary
        assert "unavailable_sources" in summary
        assert "stale_sources" in summary
        assert "source_details" in summary

    def test_should_generate_correct_availability_counts(self, report_crew):
        """Test that availability summary has correct counts."""
        # Act
        context = report_crew.get_integrated_data_context(max_age_hours=24)

        # Assert
        summary = context["data_availability_summary"]
        assert summary["total_sources"] == 6  # stock, etf, crypto, portfolio, discovery, backtesting
        assert summary["available_sources"] >= 4  # stock, etf, portfolio, discovery
        assert summary["unavailable_sources"] >= 1  # crypto

    def test_should_include_formatted_summary(self, report_crew):
        """Test that formatted summary is included."""
        # Act
        context = report_crew.get_integrated_data_context(max_age_hours=24)

        # Assert
        formatted = context["data_availability_summary_formatted"]
        assert isinstance(formatted, str)
        assert "Data Availability Summary" in formatted
        assert "Total Data Sources:" in formatted
        assert "Available:" in formatted
        assert "Unavailable:" in formatted

    def test_should_clear_tracker_before_new_context(self, report_crew):
        """Test that tracker is cleared before generating new context."""
        # Arrange - First call
        context1 = report_crew.get_integrated_data_context(max_age_hours=24)
        initial_sources = report_crew.availability_tracker.get_tracked_source_names()

        # Act - Second call
        context2 = report_crew.get_integrated_data_context(max_age_hours=24)
        final_sources = report_crew.availability_tracker.get_tracked_source_names()

        # Assert - Should have same sources (cleared and re-tracked)
        assert len(initial_sources) == len(final_sources)

    def test_should_track_error_in_availability_tracker_on_exception(self, report_crew, mocker):
        """Test that errors are tracked in availability tracker."""
        # Arrange
        mocker.patch.object(
            report_crew.data_accessor,
            "get_consolidated_reporter_input",
            side_effect=Exception("Test error")
        )

        # Act
        context = report_crew.get_integrated_data_context(max_age_hours=24)

        # Assert
        assert "error" in context
        assert "data_availability_summary" in context

        error_status = report_crew.availability_tracker.get_source_status("data_integration")
        assert error_status is not None
        assert error_status.status == "unavailable"
        assert "Test error" in error_status.error_message

    def test_should_include_freshness_warnings_in_summary(self, report_crew, mocker):
        """Test that freshness warnings are included in summary."""
        # Arrange - Mock stale data
        availability_report = mocker.Mock()
        availability_report.stock_available = True
        availability_report.stock_age_hours = 200.0  # > 168 hours (7 days)
        availability_report.etf_available = True
        availability_report.etf_age_hours = 3.0
        availability_report.crypto_available = False
        availability_report.portfolio_available = True
        availability_report.portfolio_age_hours = 1.0
        availability_report.missing_data = ["crypto"]
        availability_report.stale_data = ["stock"]

        report_crew.data_accessor.check_data_availability.return_value = availability_report

        # Act
        context = report_crew.get_integrated_data_context(max_age_hours=24)

        # Assert
        summary = context["data_availability_summary"]
        assert summary["stale_sources"] >= 1
        assert len(summary["freshness_warnings"]) >= 1

        # Check that stock crew is marked as stale
        stock_status = report_crew.availability_tracker.get_source_status("stock_crew")
        assert stock_status.status == "stale"

    def test_should_log_availability_summary_info(self, report_crew, mocker):
        """Test that availability summary is logged."""
        # Arrange
        mock_logger = mocker.patch("finwiz.crews.report_crew.report_crew.logger")

        # Act
        context = report_crew.get_integrated_data_context(max_age_hours=24)

        # Assert - Check that info was logged with summary counts
        mock_logger.info.assert_called()
        # Find the call with the summary message
        calls = [call for call in mock_logger.info.call_args_list 
                 if "Integrated data context prepared" in str(call)]
        assert len(calls) > 0, "Expected log message about integrated data context"

    def test_should_handle_missing_discovery_results_gracefully(self, report_crew):
        """Test handling when discovery results exist but can't be loaded."""
        # Arrange
        report_crew.discovery_accessor.has_discovery_results.return_value = True
        report_crew.discovery_accessor.load_discovery_results.return_value = None

        # Act
        context = report_crew.get_integrated_data_context(max_age_hours=24)

        # Assert
        discovery_status = report_crew.availability_tracker.get_source_status("aplus_discovery")
        assert discovery_status is not None
        assert discovery_status.status == "available"
        assert discovery_status.record_count == 0

    def test_should_track_all_expected_sources(self, report_crew, mocker):
        """Test that all expected data sources are tracked."""
        # Arrange
        mocker.patch.object(
            report_crew,
            "_extract_backtesting_data",
            return_value={
                "has_backtesting_data": True,
                "message": "Available",
                "status": "available",
                "backtesting_by_candidate": {},
                "total_candidates": 0
            }
        )

        # Act
        context = report_crew.get_integrated_data_context(max_age_hours=24)

        # Assert
        tracked_sources = report_crew.availability_tracker.get_tracked_source_names()
        expected_sources = [
            "stock_crew",
            "etf_crew",
            "crypto_crew",
            "portfolio_review",
            "aplus_discovery",
            "backtesting"
        ]

        for source in expected_sources:
            assert source in tracked_sources, f"Expected source {source} not tracked"

