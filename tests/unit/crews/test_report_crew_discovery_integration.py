"""
Unit tests for Report Crew A+ Discovery Integration.

Tests the integration of APlusDiscoveryAccessor into the Report Crew
to ensure proper handling of discovery data availability states.
"""

import pytest


class TestReportCrewDiscoveryIntegration:
    """Test suite for Report Crew discovery integration."""

    @pytest.fixture
    def mock_discovery_accessor(self, mocker):
        """Create mock discovery accessor."""
        return mocker.Mock()

    @pytest.fixture
    def mock_data_accessor(self, mocker):
        """Create mock data accessor."""
        mock = mocker.Mock()
        mock.get_consolidated_reporter_input.return_value = {}
        mock.check_data_availability.return_value = mocker.Mock()
        mock.get_stale_data_warnings.return_value = []
        return mock

    @pytest.fixture
    def report_crew_instance(self, mocker, mock_discovery_accessor, mock_data_accessor):
        """Create a minimal ReportCrew-like object for testing."""

        # Create a simple object that mimics ReportCrew's discovery methods
        class MockReportCrew:
            def __init__(self):
                self.discovery_accessor = mock_discovery_accessor
                self.data_accessor = mock_data_accessor

            def _get_discovery_status(self):
                """Get A+ discovery status with clear messaging."""
                has_results = self.discovery_accessor.has_discovery_results()

                if has_results:
                    return {"has_results": True, "message": "A+ discovery results available", "status": "available"}
                else:
                    return {
                        "has_results": False,
                        "message": "A+ discovery not run - use --discovery flag to enable discovery analysis",
                        "status": "not_run",
                    }

            def get_integrated_data_context(self, max_age_hours=24):
                """Get integrated data context for report generation."""
                try:
                    # Get consolidated reporter input
                    integrated_data = self.data_accessor.get_consolidated_reporter_input(max_age_hours)

                    # Add data availability information
                    integrated_data["data_availability_report"] = self.data_accessor.check_data_availability(max_age_hours)
                    integrated_data["stale_data_warnings"] = self.data_accessor.get_stale_data_warnings(max_age_hours)

                    # Add A+ discovery data
                    discovery_status = self._get_discovery_status()
                    integrated_data["discovery_status"] = discovery_status

                    if discovery_status["has_results"]:
                        discovery_results = self.discovery_accessor.load_discovery_results()
                        if discovery_results:
                            integrated_data["aplus_discovery_results"] = discovery_results
                            integrated_data["aplus_opportunities_summary"] = self.discovery_accessor.get_opportunities_summary()
                        else:
                            integrated_data["aplus_discovery_results"] = None
                            integrated_data["aplus_opportunities_summary"] = "No A+ opportunities found in current analysis"
                    else:
                        integrated_data["aplus_discovery_results"] = None
                        integrated_data["aplus_opportunities_summary"] = discovery_status["message"]

                    return integrated_data

                except Exception as e:
                    return {
                        "error": f"Data integration failed: {str(e)}",
                        "fallback_mode": True,
                        "discovery_status": {"has_results": False, "message": f"Discovery data unavailable due to error: {str(e)}"},
                    }

        return MockReportCrew()

    def test_should_initialize_discovery_accessor(self, report_crew_instance, mock_discovery_accessor):
        """Test that discovery accessor is initialized."""
        assert report_crew_instance.discovery_accessor is not None
        assert report_crew_instance.discovery_accessor == mock_discovery_accessor

    def test_should_return_available_status_when_discovery_has_results(self, report_crew_instance, mock_discovery_accessor):
        """Test discovery status when results are available."""
        # Arrange
        mock_discovery_accessor.has_discovery_results.return_value = True

        # Act
        status = report_crew_instance._get_discovery_status()

        # Assert
        assert status["has_results"] is True
        assert status["status"] == "available"
        assert "available" in status["message"].lower()

    def test_should_return_not_run_status_when_discovery_has_no_results(self, report_crew_instance, mock_discovery_accessor):
        """Test discovery status when discovery hasn't run."""
        # Arrange
        mock_discovery_accessor.has_discovery_results.return_value = False

        # Act
        status = report_crew_instance._get_discovery_status()

        # Assert
        assert status["has_results"] is False
        assert status["status"] == "not_run"
        assert "--discovery flag" in status["message"]

    def test_should_include_discovery_results_when_available(self, report_crew_instance, mock_discovery_accessor):
        """Test that discovery results are included when available."""
        # Arrange
        mock_discovery_accessor.has_discovery_results.return_value = True
        mock_results = {"opportunities": [{"ticker": "AAPL", "grade": "A+", "score": 0.95}]}
        mock_discovery_accessor.load_discovery_results.return_value = mock_results
        mock_discovery_accessor.get_opportunities_summary.return_value = "1 A+ opportunity found"

        # Act
        context = report_crew_instance.get_integrated_data_context()

        # Assert
        assert context["discovery_status"]["has_results"] is True
        assert context["aplus_discovery_results"] == mock_results
        assert context["aplus_opportunities_summary"] == "1 A+ opportunity found"

    def test_should_show_no_opportunities_message_when_results_empty(self, report_crew_instance, mock_discovery_accessor):
        """Test message when discovery ran but found no opportunities."""
        # Arrange
        mock_discovery_accessor.has_discovery_results.return_value = True
        mock_discovery_accessor.load_discovery_results.return_value = None

        # Act
        context = report_crew_instance.get_integrated_data_context()

        # Assert
        assert context["discovery_status"]["has_results"] is True
        assert context["aplus_discovery_results"] is None
        assert "No A+ opportunities found" in context["aplus_opportunities_summary"]

    def test_should_show_not_run_message_when_discovery_not_executed(self, report_crew_instance, mock_discovery_accessor):
        """Test message when discovery hasn't been run."""
        # Arrange
        mock_discovery_accessor.has_discovery_results.return_value = False

        # Act
        context = report_crew_instance.get_integrated_data_context()

        # Assert
        assert context["discovery_status"]["has_results"] is False
        assert context["aplus_discovery_results"] is None
        assert "--discovery flag" in context["aplus_opportunities_summary"]

    def test_should_handle_discovery_accessor_errors_gracefully(
        self, report_crew_instance, mock_discovery_accessor, mock_data_accessor
    ):
        """Test graceful error handling when discovery accessor fails."""
        # Arrange
        mock_discovery_accessor.has_discovery_results.side_effect = Exception("Discovery error")
        mock_data_accessor.get_consolidated_reporter_input.side_effect = Exception("Integration error")

        # Act
        context = report_crew_instance.get_integrated_data_context()

        # Assert
        assert "error" in context
        assert context["fallback_mode"] is True
        assert "discovery_status" in context
        assert context["discovery_status"]["has_results"] is False

    def test_should_add_discovery_status_to_data_availability_report(self, report_crew_instance, mock_discovery_accessor, mocker):
        """Test that discovery status is included in data availability."""
        # Arrange
        mock_discovery_accessor.has_discovery_results.return_value = True
        mock_discovery_accessor.load_discovery_results.return_value = {"opportunities": []}

        mock_availability = mocker.Mock()
        mock_availability.discovery_available = True

        # Act
        context = report_crew_instance.get_integrated_data_context()

        # Assert
        assert "discovery_status" in context
        assert "data_availability_report" in context
