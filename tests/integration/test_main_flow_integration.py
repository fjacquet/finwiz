"""
Test main flow integration with CrewDataIntegrationManager.

This module tests the integration of the CrewDataIntegrationManager
into the main FinwizFlow orchestration.
"""

from datetime import datetime

from finwiz.flows.flow_orchestrator import FinwizFlow
from finwiz.schemas.integration import DataAvailabilityReport, DataAvailabilityStatus


class TestMainFlowIntegration:
    """Test integration of CrewDataIntegrationManager into main flow."""

    def test_should_initialize_integration_system_when_flow_created(self, mocker):
        """Test that FinwizFlow initializes the integration system correctly."""
        # Arrange
        mock_integration_manager = mocker.patch("finwiz.flows.flow_orchestrator.CrewDataIntegrationManager")
        mock_data_accessor = mocker.patch("finwiz.flows.flow_orchestrator.CrewDataAccessor")

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

        mocker.patch("finwiz.flows.flow_orchestrator.CrewDataIntegrationManager", return_value=mock_integration_manager)
        mocker.patch("finwiz.flows.flow_orchestrator.CrewDataAccessor", return_value=mock_data_accessor)

        flow = FinwizFlow()

        # Act
        flow.validate_data_integration()

        # Assert
        mock_data_accessor.check_data_availability.assert_called_once()
        assert flow.state.data_availability_report.overall_status == DataAvailabilityStatus.PARTIAL
        assert flow.state.data_availability_report.stock_available is True
        assert flow.state.data_availability_report.crypto_available is False

    async def test_should_handle_stale_data_warnings_in_validation(self, mocker):
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

        mocker.patch("finwiz.flows.flow_orchestrator.CrewDataIntegrationManager", return_value=mock_integration_manager)
        mocker.patch("finwiz.flows.flow_orchestrator.CrewDataAccessor", return_value=mock_data_accessor)

        flow = FinwizFlow()

        # Act
        await flow.validate_data_integration()

        # Assert
        assert hasattr(flow.state, "stale_data_warnings")
        assert len(flow.state.stale_data_warnings) == 2
        assert hasattr(flow.state, "refresh_recommendations")
        assert flow.state.refresh_recommendations == ["stock", "etf", "crypto"]

    def test_should_use_upstream_data_in_investment_discovery(self, mocker):
        """Test that investment discovery uses Python-based analysis results."""
        # Arrange - Mock Python analyzers to provide discovery data
        mock_crypto_results = {
            "analysis_summary": "Crypto discovery completed",
            "opportunities": ["BTC", "ETH"],
            "performance_metrics": {"total_analyzed": 2, "a_plus_count": 2},
        }
        mock_stock_results = {
            "analysis_summary": "Stock discovery completed",
            "opportunities": ["MSFT", "AAPL"],
            "performance_metrics": {"total_analyzed": 2, "a_plus_count": 2},
        }
        mock_etf_results = {
            "analysis_summary": "ETF discovery completed",
            "opportunities": ["VWCE", "CSSPX"],
            "performance_metrics": {"total_analyzed": 2, "a_plus_count": 2},
        }

        mocker.patch("finwiz.scoring.crypto_analyzer.analyze_crypto_opportunities", return_value=mock_crypto_results)
        mocker.patch("finwiz.scoring.stock_analyzer.analyze_stock_opportunities", return_value=mock_stock_results)
        mocker.patch("finwiz.scoring.etf_analyzer.analyze_etf_opportunities", return_value=mock_etf_results)

        # Mock investment discovery crew
        mocker.patch("finwiz.utils.feature_flags.is_feature_enabled", return_value=True)
        mock_crew = mocker.MagicMock()
        mock_crew_result = mocker.MagicMock()
        mock_crew_result.raw = "Discovery analysis completed"
        mock_crew.crew.return_value.kickoff.return_value = mock_crew_result
        mocker.patch("finwiz.main.InvestmentDiscoveryCrew", return_value=mock_crew)

        # Mock data consolidation validator
        mock_validator = mocker.MagicMock()
        mock_validator.validate_and_report.return_value = None
        mocker.patch("finwiz.flows.flow_orchestrator.DataConsolidationValidator", return_value=mock_validator)

        flow = FinwizFlow()
        flow.state.portfolio_review = {"test": "data"}

        # Act - Run discovery flow (crypto, stock, etf first, then consolidation)
        flow.check_crypto()
        flow.check_stock()
        flow.check_etf()
        flow.check_investment_discovery()

        # Assert - Verify Python analyzers were used for discovery
        assert flow.state.crypto_analysis_success is True
        assert flow.state.stock_analysis_success is True
        assert flow.state.etf_analysis_success is True
        assert flow.state.crypto_result == "Crypto discovery completed"
        assert flow.state.stock_result == "Stock discovery completed"
        assert flow.state.etf_result == "ETF discovery completed"

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

        mocker.patch("finwiz.flows.flow_orchestrator.CrewDataIntegrationManager", return_value=mock_integration_manager)
        mocker.patch("finwiz.flows.flow_orchestrator.CrewDataAccessor", return_value=mock_data_accessor)

        flow = FinwizFlow()

        # Act
        flow.pre_validate_reporter_input()

        # Assert
        mock_data_accessor.get_consolidated_reporter_input.assert_called_once()
        assert flow.state.consolidated_data == consolidated_data
        assert flow.state.integrated_data_available is True
        assert flow.state.market_sentiment["data_quality"] == "HIGH"
        assert flow.state.ticker_validation["validation_summary"]["validation_rate"] == 95.0
        assert flow.state.aplus_opportunities["stock_opportunities"] == ["MSFT", "AAPL"]

    def test_should_provide_data_accessor_to_report_crew(self, mocker):
        """Test that report crew receives data accessor and integration manager."""
        # Arrange
        mock_integration_manager = mocker.MagicMock()
        mock_data_accessor = mocker.MagicMock()

        mocker.patch("finwiz.flows.flow_orchestrator.CrewDataIntegrationManager", return_value=mock_integration_manager)
        mocker.patch("finwiz.flows.flow_orchestrator.CrewDataAccessor", return_value=mock_data_accessor)

        mock_report_crew = mocker.MagicMock()
        mock_report_crew.validate_reporter_input.return_value = None
        mock_report_crew.crew.return_value.kickoff.return_value = "Report generated"
        mocker.patch("finwiz.main.ReportCrew", return_value=mock_report_crew)

        flow = FinwizFlow()
        flow.state.integrated_data_available = True
        flow.state.market_sentiment = {"data_quality": "HIGH"}
        flow.state.ticker_validation = {"validation_summary": {"validation_rate": 95.0}}
        flow.state.aplus_opportunities = {"stock_opportunities": ["MSFT"]}

        # Act
        flow.report()

        # Assert
        assert flow.state.data_accessor == mock_data_accessor
        assert flow.state.integration_manager == mock_integration_manager
        mock_report_crew.crew.return_value.kickoff.assert_called_once()

    async def test_should_handle_integration_system_errors_gracefully(self, mocker):
        """Test that integration system errors are handled gracefully."""
        # Arrange
        mock_integration_manager = mocker.MagicMock()
        mock_data_accessor = mocker.MagicMock()
        mock_data_accessor.check_data_availability.side_effect = Exception("Integration system error")

        mocker.patch("finwiz.flows.flow_orchestrator.CrewDataIntegrationManager", return_value=mock_integration_manager)
        mocker.patch("finwiz.flows.flow_orchestrator.CrewDataAccessor", return_value=mock_data_accessor)

        flow = FinwizFlow()

        # Act
        await flow.validate_data_integration()

        # Assert
        assert hasattr(flow.state, "data_integration_error")
        assert "Integration system error" in flow.state.data_integration_error

    def test_should_fallback_to_example_validation_when_no_crew_data(self, mocker):
        """Test fallback to example validation when no crew data is available."""
        # Arrange
        consolidated_data = {}  # No crew data

        mock_integration_manager = mocker.MagicMock()
        mock_data_accessor = mocker.MagicMock()
        mock_data_accessor.get_consolidated_reporter_input.return_value = consolidated_data

        mocker.patch("finwiz.flows.flow_orchestrator.CrewDataIntegrationManager", return_value=mock_integration_manager)
        mocker.patch("finwiz.flows.flow_orchestrator.CrewDataAccessor", return_value=mock_data_accessor)

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
        assert flow.state.reporter_input == {"example": "data"}
