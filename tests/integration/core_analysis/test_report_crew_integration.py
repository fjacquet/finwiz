"""Test Report Crew integration with data integration system."""

from pathlib import Path

from finwiz.crews.report_crew.report_crew import ReportCrew
from finwiz.schemas.integration import DataAvailabilityReport, DataAvailabilityStatus


class TestReportCrewIntegration:
    """Test Report Crew integration with data integration system."""

    def test_should_initialize_with_data_integration_components(self, mocker):
        """Test that ReportCrew initializes with data integration components."""
        # Arrange
        mock_integration_manager = mocker.patch("finwiz.crews.report_crew.report_crew.CrewDataIntegrationManager")
        mock_data_accessor = mocker.patch("finwiz.crews.report_crew.report_crew.CrewDataAccessor")

        # Act
        crew = ReportCrew()

        # Assert
        assert crew.integration_manager is not None
        assert crew.data_accessor is not None
        mock_integration_manager.assert_called_once_with(Path("output"))
        mock_data_accessor.assert_called_once()

    def test_should_check_data_availability_during_initialization(self, mocker):
        """Test that ReportCrew checks data availability during tool initialization."""
        # Arrange
        mock_availability_report = DataAvailabilityReport(
            stock_available=True,
            etf_available=True,
            crypto_available=False,
            discovery_available=True,
            portfolio_available=False,
            missing_data=["crypto", "portfolio"],
            stale_data=[],
            integration_errors=[],
            overall_status=DataAvailabilityStatus.PARTIAL,
            report_timestamp=mocker.MagicMock(),
            data_freshness_summary={},
            recommendations=[],
        )

        mock_data_accessor = mocker.MagicMock()
        mock_data_accessor.check_data_availability.return_value = mock_availability_report
        mock_data_accessor.get_stale_data_warnings.return_value = []

        mocker.patch("finwiz.crews.report_crew.report_crew.CrewDataIntegrationManager")
        mocker.patch("finwiz.crews.report_crew.report_crew.CrewDataAccessor", return_value=mock_data_accessor)

        # Act
        crew = ReportCrew()

        # Assert
        mock_data_accessor.check_data_availability.assert_called_once()
        assert len(crew.tools) > 0  # Should have some tools initialized

    def test_should_prepare_integrated_context_successfully(self, mocker):
        """Test that crew prepares integrated context with all required data."""
        # Arrange
        mock_integrated_data = {
            "stock": {"validated_tickers": ["AAPL", "MSFT"]},
            "etf": {"validated_etfs": ["SPY", "QQQ"]},
            "market_sentiment": {
                "aggregated_scores": {"positive": 0.6, "neutral": 0.3, "negative": 0.1},
                "top_sources": [{"url": "test.com", "date": "2024-01-01"}],
            },
            "aplus_opportunities": {"stock_opportunities": ["NVDA"], "confidence_score": 0.85},
        }

        mock_data_accessor = mocker.MagicMock()
        mock_data_accessor.check_data_availability.return_value = mocker.MagicMock()
        mock_data_accessor.get_stale_data_warnings.return_value = []
        mock_data_accessor.get_consolidated_reporter_input.return_value = mock_integrated_data

        mocker.patch("finwiz.crews.report_crew.report_crew.CrewDataIntegrationManager")
        mocker.patch("finwiz.crews.report_crew.report_crew.CrewDataAccessor", return_value=mock_data_accessor)

        crew = ReportCrew()

        # Act
        context = crew.get_integrated_data_context()

        # Assert
        assert "stock" in context
        assert "market_sentiment" in context
        assert "aplus_opportunities" in context
        mock_data_accessor.get_consolidated_reporter_input.assert_called_once_with(24)

    def test_should_handle_data_integration_failure_gracefully(self, mocker):
        """Test graceful degradation when data integration fails."""
        # Arrange
        mock_data_accessor = mocker.MagicMock()
        mock_data_accessor.check_data_availability.side_effect = Exception("Integration failed")
        mock_data_accessor.get_stale_data_warnings.return_value = []

        mocker.patch("finwiz.crews.report_crew.report_crew.CrewDataIntegrationManager")
        mocker.patch("finwiz.crews.report_crew.report_crew.CrewDataAccessor", return_value=mock_data_accessor)

        # Act
        crew = ReportCrew()
        context = crew.get_integrated_data_context()

        # Assert
        assert "error" in context
        assert context["fallback_mode"] is True
        assert len(crew.tools) > 0  # Should still have fallback tools

    def test_should_prepare_crew_context_with_metadata(self, mocker):
        """Test that crew context includes execution metadata."""
        # Arrange
        mock_data_accessor = mocker.MagicMock()
        mock_data_accessor.check_data_availability.return_value = mocker.MagicMock()
        mock_data_accessor.get_stale_data_warnings.return_value = []
        mock_data_accessor.get_consolidated_reporter_input.return_value = {"test": "data"}

        mocker.patch("finwiz.crews.report_crew.report_crew.CrewDataIntegrationManager")
        mocker.patch("finwiz.crews.report_crew.report_crew.CrewDataAccessor", return_value=mock_data_accessor)

        crew = ReportCrew()

        # Act
        context = crew.prepare_crew_context(max_age_hours=12)

        # Assert
        assert "execution_metadata" in context
        metadata = context["execution_metadata"]
        assert metadata["max_age_hours"] == 12
        assert metadata["integration_manager_initialized"] is True
        assert metadata["data_accessor_initialized"] is True
        assert "tools_count" in metadata

    def test_should_validate_reporter_input_with_integrated_context(self, mocker):
        """Test that reporter input validation works with integrated context."""
        # Arrange
        mock_validator = mocker.MagicMock()
        mock_data_accessor = mocker.MagicMock()
        mock_data_accessor.check_data_availability.return_value = mocker.MagicMock()
        mock_data_accessor.get_stale_data_warnings.return_value = []
        mock_data_accessor.get_consolidated_reporter_input.return_value = {"valid": "data"}

        mocker.patch("finwiz.crews.report_crew.report_crew.CrewDataIntegrationManager")
        mocker.patch("finwiz.crews.report_crew.report_crew.CrewDataAccessor", return_value=mock_data_accessor)
        mocker.patch("finwiz.crews.report_crew.report_crew.ReporterInputValidator", return_value=mock_validator)

        crew = ReportCrew()

        # Act
        crew.prepare_crew_context()

        # Assert
        mock_validator.validate_reporter_context.assert_called_once()

    def test_should_log_data_availability_warnings(self, mocker, caplog):
        """Test that data availability warnings are properly logged."""
        # Arrange
        mock_availability_report = DataAvailabilityReport(
            stock_available=False,
            etf_available=True,
            crypto_available=False,
            discovery_available=True,
            portfolio_available=False,
            missing_data=["stock", "crypto", "portfolio"],
            stale_data=["etf"],
            integration_errors=[],
            overall_status=DataAvailabilityStatus.INSUFFICIENT,
            report_timestamp=mocker.MagicMock(),
            data_freshness_summary={},
            recommendations=[],
        )

        mock_data_accessor = mocker.MagicMock()
        mock_data_accessor.check_data_availability.return_value = mock_availability_report
        mock_data_accessor.get_stale_data_warnings.return_value = ["ETF data is 25 hours old"]

        mocker.patch("finwiz.crews.report_crew.report_crew.CrewDataIntegrationManager")
        mocker.patch("finwiz.crews.report_crew.report_crew.CrewDataAccessor", return_value=mock_data_accessor)

        # Act
        with caplog.at_level("WARNING"):
            ReportCrew()

        # Assert
        assert "Missing data for crews: stock, crypto, portfolio" in caplog.text
        assert "ETF data is 25 hours old" in caplog.text
