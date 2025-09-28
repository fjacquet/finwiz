"""
Test main flow integration with CrewDataIntegrationManager.

This module tests the integration of the CrewDataIntegrationManager
into the main FinwizFlow orchestration.
"""

from datetime import datetime

from finwiz.main import FinwizFlow
from finwiz.schemas.integration import DataAvailabilityReport, DataAvailabilityStatus


class TestMainFlowIntegration:
    """Test integration of CrewDataIntegrationManager into main flow."""

    def test_should_initialize_integration_system_when_flow_created(self, mocker):
        """Test that FinwizFlow initializes the integration system correctly."""
        # Arrange
        mock_integration_manager = mocker.patch("finwiz.main.CrewDataIntegrationManager")
        mock_data_accessor = mocker.patch("finwiz.main.CrewDataAccessor")

        # Act
        flow = FinwizFlow()

        # Assert
        mock_integration_manager.assert_called_once()
        mock_data_accessor.assert_called_once_with(mock_integration_manager.return_value)
        assert hasattr(flow, "integration_manager")
        assert hasattr(flow, "data_accessor")

    def test_should_validate_data_integration_on_start(self, mocker):
        """Test that data integration validation runs on flow start."""
        # Arrange
        mock_availability_report = DataAvailabilityReport(
            stock_available=True,
            etf_available=True,
            crypto_available=False,
            discovery_available=False,
            portfolio_available=True,
            missing_data=["crypto", "discovery"],
            stale_data=[],
            integration_errors=[],
            overall_status=DataAvailabilityStatus.PARTIAL,
            report_timestamp=datetime.now(),
            data_freshness_summary={},
            recommendations=["Run crypto and discovery crews"],
        )

        mock_integration_manager = mocker.MagicMock()
        mock_data_accessor = mocker.MagicMock()
        mock_data_accessor.check_data_availability.return_value = mock_availability_report
        mock_data_accessor.get_stale_data_warnings.return_value = []

        mocker.patch("finwiz.main.CrewDataIntegrationManager", return_value=mock_integration_manager)
        mocker.patch("finwiz.main.CrewDataAccessor", return_value=mock_data_accessor)

        flow = FinwizFlow()

        # Act
        flow.validate_data_integration()

        # Assert
        mock_data_accessor.check_data_availability.assert_called_once()
        assert flow.inputs["data_availability_report"]["overall_status"] == "PARTIAL"
        assert flow.inputs["data_availability_report"]["stock_available"] is True
        assert flow.inputs["data_availability_report"]["crypto_available"] is False

    def test_should_handle_stale_data_warnings_in_validation(self, mocker):
        """Test that stale data warnings are properly handled."""
        # Arrange
        mock_availability_report = DataAvailabilityReport(
            stock_available=True,
            etf_available=True,
            crypto_available=True,
            discovery_available=True,
            portfolio_available=True,
            missing_data=[],
            stale_data=["stock", "etf"],
            integration_errors=[],
            overall_status=DataAvailabilityStatus.PARTIAL,
            report_timestamp=datetime.now(),
            data_freshness_summary={},
            recommendations=["Refresh stale data"],
        )

        stale_warnings = [
            "Stale data warning: stock crew data is 25.5 hours old (threshold: 24 hours)",
            "Stale data warning: etf crew data is 30.2 hours old (threshold: 24 hours)",
        ]

        mock_integration_manager = mocker.MagicMock()
        mock_integration_manager.get_refresh_recommendations.return_value = ["stock", "etf", "crypto"]

        mock_data_accessor = mocker.MagicMock()
        mock_data_accessor.check_data_availability.return_value = mock_availability_report
        mock_data_accessor.get_stale_data_warnings.return_value = stale_warnings

        mocker.patch("finwiz.main.CrewDataIntegrationManager", return_value=mock_integration_manager)
        mocker.patch("finwiz.main.CrewDataAccessor", return_value=mock_data_accessor)

        flow = FinwizFlow()

        # Act
        flow.validate_data_integration()

        # Assert
        assert "stale_data_warnings" in flow.inputs
        assert len(flow.inputs["stale_data_warnings"]) == 2
        assert "refresh_recommendations" in flow.inputs
        assert flow.inputs["refresh_recommendations"] == ["stock", "etf", "crypto"]

    def test_should_use_upstream_data_in_investment_discovery(self, mocker):
        """Test that investment discovery uses upstream data from integration system."""
        # Arrange
        from finwiz.integration.manager import UpstreamDataCollection

        upstream_data = UpstreamDataCollection(
            available_data={"stock": ["stock_output.json"], "etf": ["etf_output.json"]},
            missing_data=["crypto"],
            stale_data=["portfolio"],
        )

        mock_integration_manager = mocker.MagicMock()
        mock_integration_manager.get_upstream_data.return_value = upstream_data

        mock_data_accessor = mocker.MagicMock()
        mock_aplus_opportunities = mocker.MagicMock()
        mock_aplus_opportunities.etf_opportunities = ["VWCE", "CSSPX"]
        mock_aplus_opportunities.stock_opportunities = ["MSFT", "AAPL"]
        mock_aplus_opportunities.crypto_opportunities = ["BTC", "ETH"]
        mock_aplus_opportunities.discovery_summary = "Test summary"
        mock_aplus_opportunities.confidence_score = 0.85
        mock_aplus_opportunities.allocation_recommendations = []
        mock_aplus_opportunities.replacement_notes = []
        mock_data_accessor.get_aplus_opportunities.return_value = mock_aplus_opportunities

        mocker.patch("finwiz.main.CrewDataIntegrationManager", return_value=mock_integration_manager)
        mocker.patch("finwiz.main.CrewDataAccessor", return_value=mock_data_accessor)

        # Mock feature flag and crew execution
        mocker.patch("finwiz.utils.feature_flags.is_feature_enabled", return_value=True)
        mock_crew = mocker.MagicMock()
        mock_crew_result = mocker.MagicMock()
        mock_crew_result.raw = "Discovery analysis completed"
        mock_crew.crew.return_value.kickoff.return_value = mock_crew_result
        mocker.patch("finwiz.main.InvestmentDiscoveryCrew", return_value=mock_crew)

        flow = FinwizFlow()
        flow.inputs["portfolio_review"] = {"test": "data"}

        # Act
        flow.check_investment_discovery()

        # Assert
        mock_integration_manager.get_upstream_data.assert_called_once_with("discovery")
        mock_data_accessor.get_aplus_opportunities.assert_called_once()

        # Check that upstream data info is passed to crew
        crew_inputs = mock_crew.crew.return_value.kickoff.call_args[1]["inputs"]
        assert "upstream_data_available" in crew_inputs
        assert crew_inputs["upstream_data_available"] == ["stock", "etf"]
        assert crew_inputs["upstream_data_stale"] == ["portfolio"]
        assert crew_inputs["upstream_data_missing"] == ["crypto"]

        # Check that A+ opportunities are extracted
        assert flow.inputs["investment_discovery_structured"]["has_a_plus_analysis"] is True
        assert len(flow.inputs["investment_discovery_structured"]["etf_opportunities"]) == 2

    def test_should_consolidate_data_for_reporter_input(self, mocker):
        """Test that reporter input uses consolidated data from integration system."""
        # Arrange
        consolidated_data = {
            "stock": {"test": "stock_data"},
            "etf": {"test": "etf_data"},
            "market_sentiment": {
                "aggregated_scores": {"positive": 0.6, "neutral": 0.3, "negative": 0.1},
                "data_quality": "HIGH",
            },
            "ticker_validation": {
                "validation_summary": {"validation_rate": 95.0},
            },
            "aplus_opportunities": {
                "stock_opportunities": ["MSFT", "AAPL"],
                "etf_opportunities": ["VWCE"],
                "crypto_opportunities": ["BTC"],
            },
            "portfolio_allocation_updates": [],
            "aplus_availability_status": "AVAILABLE",
        }

        mock_integration_manager = mocker.MagicMock()
        mock_data_accessor = mocker.MagicMock()
        mock_data_accessor.get_consolidated_reporter_input.return_value = consolidated_data

        mocker.patch("finwiz.main.CrewDataIntegrationManager", return_value=mock_integration_manager)
        mocker.patch("finwiz.main.CrewDataAccessor", return_value=mock_data_accessor)

        flow = FinwizFlow()

        # Act
        flow.pre_validate_reporter_input()

        # Assert
        mock_data_accessor.get_consolidated_reporter_input.assert_called_once()
        assert flow.inputs["consolidated_data"] == consolidated_data
        assert flow.inputs["integrated_data_available"] is True
        assert flow.inputs["market_sentiment"]["data_quality"] == "HIGH"
        assert flow.inputs["ticker_validation"]["validation_summary"]["validation_rate"] == 95.0
        assert flow.inputs["aplus_opportunities"]["stock_opportunities"] == ["MSFT", "AAPL"]

    def test_should_provide_data_accessor_to_report_crew(self, mocker):
        """Test that report crew receives data accessor and integration manager."""
        # Arrange
        mock_integration_manager = mocker.MagicMock()
        mock_data_accessor = mocker.MagicMock()

        mocker.patch("finwiz.main.CrewDataIntegrationManager", return_value=mock_integration_manager)
        mocker.patch("finwiz.main.CrewDataAccessor", return_value=mock_data_accessor)

        mock_report_crew = mocker.MagicMock()
        mock_report_crew.validate_reporter_input.return_value = None
        mock_report_crew.crew.return_value.kickoff.return_value = "Report generated"
        mocker.patch("finwiz.main.ReportCrew", return_value=mock_report_crew)

        flow = FinwizFlow()
        flow.inputs["integrated_data_available"] = True
        flow.inputs["market_sentiment"] = {"data_quality": "HIGH"}
        flow.inputs["ticker_validation"] = {"validation_summary": {"validation_rate": 95.0}}
        flow.inputs["aplus_opportunities"] = {"stock_opportunities": ["MSFT"]}

        # Act
        flow.report()

        # Assert
        assert flow.inputs["data_accessor"] == mock_data_accessor
        assert flow.inputs["integration_manager"] == mock_integration_manager
        mock_report_crew.crew.return_value.kickoff.assert_called_once()

    def test_should_handle_integration_system_errors_gracefully(self, mocker):
        """Test that integration system errors are handled gracefully."""
        # Arrange
        mock_integration_manager = mocker.MagicMock()
        mock_data_accessor = mocker.MagicMock()
        mock_data_accessor.check_data_availability.side_effect = Exception("Integration system error")

        mocker.patch("finwiz.main.CrewDataIntegrationManager", return_value=mock_integration_manager)
        mocker.patch("finwiz.main.CrewDataAccessor", return_value=mock_data_accessor)

        flow = FinwizFlow()

        # Act
        flow.validate_data_integration()

        # Assert
        assert "data_integration_error" in flow.inputs
        assert "Integration system error" in flow.inputs["data_integration_error"]

    def test_should_fallback_to_example_validation_when_no_crew_data(self, mocker):
        """Test fallback to example validation when no crew data is available."""
        # Arrange
        consolidated_data = {}  # No crew data

        mock_integration_manager = mocker.MagicMock()
        mock_data_accessor = mocker.MagicMock()
        mock_data_accessor.get_consolidated_reporter_input.return_value = consolidated_data

        mocker.patch("finwiz.main.CrewDataIntegrationManager", return_value=mock_integration_manager)
        mocker.patch("finwiz.main.CrewDataAccessor", return_value=mock_data_accessor)

        # Mock example file existence and validation
        mock_path = mocker.patch("finwiz.main.Path")
        mock_example_path = mock_path.return_value.resolve.return_value.parents.__getitem__.return_value.__truediv__.return_value
        mock_example_path.exists.return_value = True

        mock_validate = mocker.patch("finwiz.main.validate_reporter_input")
        mock_model = mocker.MagicMock()
        mock_model.model_dump.return_value = {"example": "data"}
        mock_validate.return_value = mock_model

        flow = FinwizFlow()

        # Act
        flow.pre_validate_reporter_input()

        # Assert
        mock_validate.assert_called_once()
        assert flow.inputs["reporter_input"] == {"example": "data"}
