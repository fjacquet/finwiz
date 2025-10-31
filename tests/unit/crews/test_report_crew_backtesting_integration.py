"""
Unit tests for backtesting data integration in ReportCrew.

Tests that backtesting data is properly extracted from Flow state inputs
before falling back to file-based checking.
"""

import pytest

from finwiz.crews.report_crew.report_crew import ReportCrew


class TestReportCrewBacktestingIntegration:
    """Test suite for backtesting data integration."""

    @pytest.fixture
    def report_crew(self, tmp_path, mocker):
        """Create report crew instance with mocked dependencies."""
        # Mock the integration manager and data accessor
        mocker.patch("finwiz.crews.report_crew.report_crew.CrewDataIntegrationManager")
        mocker.patch("finwiz.crews.report_crew.report_crew.CrewDataAccessor")
        mocker.patch("finwiz.crews.report_crew.report_crew.APlusDiscoveryAccessor")
        mocker.patch("finwiz.crews.report_crew.report_crew.BacktestingDataExtractor")
        mocker.patch("finwiz.crews.report_crew.report_crew.DataAvailabilityTracker")

        # Create crew instance
        crew = ReportCrew()
        crew.output_dir = tmp_path

        return crew

    def test_should_extract_backtesting_from_flow_state_aplus_opportunities(self, report_crew, mocker):
        """Test that backtesting data is extracted from Flow state aplus_opportunities."""
        # Arrange
        mock_discovery_results = {
            "validation_results": [
                {
                    "symbol": "AAPL",
                    "average_sharpe_ratio": 1.5,
                    "average_sortino_ratio": 1.8,
                    "average_max_drawdown": -15.0,
                    "backtest_period_years": 5,
                    "validation_details": [{"annualized_return": 12.5, "win_rate": 0.65, "total_trades": 100}],
                }
            ]
        }

        inputs = {"aplus_opportunities": mock_discovery_results}

        # Mock the backtesting extractor
        mock_extractor = mocker.Mock()
        mock_metrics = mocker.Mock()
        mock_metrics.model_dump.return_value = {
            "annualized_return": 12.5,
            "sharpe_ratio": 1.5,
            "sortino_ratio": 1.8,
            "max_drawdown": -15.0,
            "win_rate": 0.65,
            "backtest_period_years": 5,
            "total_trades": 100,
        }
        mock_extractor.extract_backtesting_metrics.return_value = mock_metrics
        mock_extractor.format_for_display.return_value = "Formatted metrics"
        report_crew.backtesting_extractor = mock_extractor

        # Act
        result = report_crew._extract_backtesting_data(inputs)

        # Assert
        assert result["has_backtesting_data"] is True
        assert result["status"] == "available"
        assert "AAPL" in result["backtesting_by_candidate"]
        assert result["total_candidates"] == 1

    def test_should_extract_backtesting_from_flow_state_investment_discovery(self, report_crew, mocker):
        """Test that backtesting data is extracted from Flow state investment_discovery_structured."""
        # Arrange
        mock_discovery_results = {
            "validation_results": [
                {
                    "symbol": "MSFT",
                    "average_sharpe_ratio": 1.8,
                    "average_sortino_ratio": 2.0,
                    "average_max_drawdown": -12.0,
                    "backtest_period_years": 5,
                    "validation_details": [{"annualized_return": 15.0, "win_rate": 0.70, "total_trades": 120}],
                }
            ]
        }

        inputs = {"investment_discovery_structured": mock_discovery_results}

        # Mock the backtesting extractor
        mock_extractor = mocker.Mock()
        mock_metrics = mocker.Mock()
        mock_metrics.model_dump.return_value = {
            "annualized_return": 15.0,
            "sharpe_ratio": 1.8,
            "sortino_ratio": 2.0,
            "max_drawdown": -12.0,
            "win_rate": 0.70,
            "backtest_period_years": 5,
            "total_trades": 120,
        }
        mock_extractor.extract_backtesting_metrics.return_value = mock_metrics
        mock_extractor.format_for_display.return_value = "Formatted metrics"
        report_crew.backtesting_extractor = mock_extractor

        # Act
        result = report_crew._extract_backtesting_data(inputs)

        # Assert
        assert result["has_backtesting_data"] is True
        assert result["status"] == "available"
        assert "MSFT" in result["backtesting_by_candidate"]

    def test_should_fallback_to_file_based_when_no_inputs(self, report_crew, mocker):
        """Test that method falls back to file-based checking when no inputs provided."""
        # Arrange
        mock_discovery_accessor = mocker.Mock()
        mock_discovery_accessor.has_discovery_results.return_value = False
        report_crew.discovery_accessor = mock_discovery_accessor

        # Act
        result = report_crew._extract_backtesting_data(inputs=None)

        # Assert
        assert result["has_backtesting_data"] is False
        assert result["status"] == "not_available"
        assert "discovery not run" in result["message"]
        mock_discovery_accessor.has_discovery_results.assert_called_once()

    def test_should_fallback_to_file_based_when_inputs_empty(self, report_crew, mocker):
        """Test that method falls back to file-based checking when inputs are empty."""
        # Arrange
        mock_discovery_accessor = mocker.Mock()
        mock_discovery_accessor.has_discovery_results.return_value = False
        report_crew.discovery_accessor = mock_discovery_accessor

        # Act
        result = report_crew._extract_backtesting_data(inputs={})

        # Assert
        assert result["has_backtesting_data"] is False
        assert result["status"] == "not_available"
        mock_discovery_accessor.has_discovery_results.assert_called_once()

    def test_should_handle_missing_validation_results_gracefully(self, report_crew, mocker):
        """Test that method handles missing validation_results in discovery data."""
        # Arrange
        inputs = {"aplus_opportunities": {"stocks": [], "etfs": [], "crypto": []}}

        # Act
        result = report_crew._extract_backtesting_data(inputs)

        # Assert
        assert result["has_backtesting_data"] is False
        assert result["status"] == "not_available"

    def test_should_log_flow_state_usage(self, report_crew, mocker, caplog):
        """Test that method logs when using Flow state data."""
        # Arrange
        mock_discovery_results = {"validation_results": [{"symbol": "GOOGL", "average_sharpe_ratio": 1.6, "backtest_period_years": 5, "validation_details": []}]}

        inputs = {"aplus_opportunities": mock_discovery_results}

        # Mock the backtesting extractor
        mock_extractor = mocker.Mock()
        mock_metrics = mocker.Mock()
        mock_metrics.model_dump.return_value = {"sharpe_ratio": 1.6, "backtest_period_years": 5}
        mock_extractor.extract_backtesting_metrics.return_value = mock_metrics
        mock_extractor.format_for_display.return_value = "Formatted"
        report_crew.backtesting_extractor = mock_extractor

        # Act
        with caplog.at_level("INFO"):
            report_crew._extract_backtesting_data(inputs)

        # Assert
        assert "Using discovery results from Flow state" in caplog.text
        assert "for backtesting extraction" in caplog.text
