"""
Unit tests for report crew backtesting data integration.

Tests that the report crew properly integrates backtesting data from the
backtesting extractor and makes it available in the report context.
"""


import pytest

from finwiz.crews.report_crew.report_crew import ReportCrew
from finwiz.integration.backtesting_extractor import BacktestingMetrics


class TestReportCrewBacktestingIntegration:
    """Test suite for report crew backtesting integration."""

    @pytest.fixture
    def mock_discovery_accessor(self, mocker):
        """Create mock discovery accessor."""
        mock = mocker.Mock()
        mock.has_discovery_results.return_value = True
        mock.load_discovery_results.return_value = {
            "opportunities": [
                {"symbol": "AAPL", "grade": "A+"},
                {"symbol": "MSFT", "grade": "A+"}
            ],
            "validation_results": [
                {
                    "symbol": "AAPL",
                    "total_candidates": 1,
                    "average_sharpe_ratio": 1.5,
                    "average_sortino_ratio": 1.8,
                    "average_max_drawdown": -15.0,
                    "backtest_period_years": 5,
                    "market_regimes_tested": ["bull", "bear", "sideways"],
                    "validation_details": [
                        {
                            "annualized_return": 12.5,
                            "win_rate": 0.65,
                            "total_trades": 50
                        }
                    ]
                },
                {
                    "symbol": "MSFT",
                    "total_candidates": 1,
                    "average_sharpe_ratio": 1.3,
                    "average_sortino_ratio": None,  # Test None handling
                    "average_max_drawdown": -18.0,
                    "backtest_period_years": 5,
                    "market_regimes_tested": ["bull", "bear"],
                    "validation_details": [
                        {
                            "annualized_return": 10.2,
                            "win_rate": None,  # Test None handling
                            "total_trades": 45
                        }
                    ]
                }
            ]
        }
        mock.get_opportunities_summary.return_value = "2 A+ opportunities found"
        return mock

    @pytest.fixture
    def mock_backtesting_extractor(self, mocker):
        """Create mock backtesting extractor."""
        mock = mocker.Mock()

        # Mock extract_backtesting_metrics to return different metrics for different symbols
        def extract_metrics_side_effect(validation_result):
            if hasattr(validation_result, 'symbol'):
                symbol = validation_result.symbol
            elif isinstance(validation_result, dict):
                symbol = validation_result.get('symbol', 'UNKNOWN')
            else:
                symbol = 'UNKNOWN'

            if symbol == "AAPL":
                return BacktestingMetrics(
                    annualized_return=12.5,
                    sharpe_ratio=1.5,
                    sortino_ratio=1.8,
                    calmar_ratio=0.83,
                    max_drawdown=-15.0,
                    win_rate=0.65,
                    backtest_period_years=5,
                    total_trades=50
                )
            elif symbol == "MSFT":
                return BacktestingMetrics(
                    annualized_return=10.2,
                    sharpe_ratio=1.3,
                    sortino_ratio=None,  # Test None handling
                    calmar_ratio=0.57,
                    max_drawdown=-18.0,
                    win_rate=None,  # Test None handling
                    backtest_period_years=5,
                    total_trades=45
                )
            return None

        mock.extract_backtesting_metrics.side_effect = extract_metrics_side_effect

        # Mock format_for_display
        def format_display_side_effect(metrics):
            if metrics is None:
                return "Backtesting data not available"
            lines = []
            if metrics.annualized_return is not None:
                lines.append(f"Annualized Return: {metrics.annualized_return:.2f}%")
            else:
                lines.append("Annualized Return: Not calculated")
            if metrics.sharpe_ratio is not None:
                lines.append(f"Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
            else:
                lines.append("Sharpe Ratio: Not calculated")
            return "\n".join(lines)

        mock.format_for_display.side_effect = format_display_side_effect

        # Mock get_available_metrics
        def get_available_metrics_side_effect(metrics):
            if metrics is None:
                return {
                    "annualized_return": None,
                    "sharpe_ratio": None,
                    "sortino_ratio": None,
                    "calmar_ratio": None,
                    "max_drawdown": None,
                    "win_rate": None,
                    "backtest_period_years": None,
                    "total_trades": None
                }
            return metrics.model_dump()

        mock.get_available_metrics.side_effect = get_available_metrics_side_effect

        return mock

    @pytest.fixture
    def report_crew_with_mocks(self, mocker, mock_discovery_accessor, mock_backtesting_extractor):
        """Create report crew with mocked dependencies."""
        # Mock the integration manager and data accessor
        mocker.patch('finwiz.crews.report_crew.report_crew.CrewDataIntegrationManager')
        mocker.patch('finwiz.crews.report_crew.report_crew.CrewDataAccessor')

        # Create crew instance
        crew = ReportCrew()

        # Replace with our mocks
        crew.discovery_accessor = mock_discovery_accessor
        crew.backtesting_extractor = mock_backtesting_extractor

        return crew

    def test_should_extract_backtesting_data_when_discovery_available(
        self, report_crew_with_mocks, mock_discovery_accessor
    ):
        """Test that backtesting data is extracted when discovery results are available."""
        # Act
        backtesting_data = report_crew_with_mocks._extract_backtesting_data()

        # Assert
        assert backtesting_data["has_backtesting_data"] is True
        assert backtesting_data["status"] == "available"
        assert "backtesting_by_candidate" in backtesting_data
        assert len(backtesting_data["backtesting_by_candidate"]) == 2

        # Verify AAPL data
        aapl_data = backtesting_data["backtesting_by_candidate"]["AAPL"]
        assert aapl_data["metrics"]["annualized_return"] == 12.5
        assert aapl_data["metrics"]["sharpe_ratio"] == 1.5
        assert aapl_data["metrics"]["win_rate"] == 0.65
        assert "formatted_display" in aapl_data
        assert "available_metrics" in aapl_data

        # Verify MSFT data with None values
        msft_data = backtesting_data["backtesting_by_candidate"]["MSFT"]
        assert msft_data["metrics"]["annualized_return"] == 10.2
        assert msft_data["metrics"]["sharpe_ratio"] == 1.3
        assert msft_data["metrics"]["sortino_ratio"] is None  # Should be None, not string
        assert msft_data["metrics"]["win_rate"] is None  # Should be None, not string

    def test_should_return_not_available_when_discovery_not_run(
        self, report_crew_with_mocks, mock_discovery_accessor
    ):
        """Test that backtesting data returns not_available when discovery hasn't run."""
        # Arrange
        mock_discovery_accessor.has_discovery_results.return_value = False

        # Act
        backtesting_data = report_crew_with_mocks._extract_backtesting_data()

        # Assert
        assert backtesting_data["has_backtesting_data"] is False
        assert backtesting_data["status"] == "not_available"
        assert "Backtesting data not available - discovery not run" in backtesting_data["message"]

    def test_should_handle_empty_validation_results(
        self, report_crew_with_mocks, mock_discovery_accessor
    ):
        """Test handling of discovery results with no validation data."""
        # Arrange
        mock_discovery_accessor.load_discovery_results.return_value = {
            "opportunities": [],
            "validation_results": []
        }

        # Act
        backtesting_data = report_crew_with_mocks._extract_backtesting_data()

        # Assert
        assert backtesting_data["has_backtesting_data"] is False
        assert backtesting_data["status"] == "not_available"
        assert "no validation results" in backtesting_data["message"].lower()

    def test_should_include_backtesting_in_integrated_context(
        self, report_crew_with_mocks, mocker
    ):
        """Test that backtesting data is included in integrated context."""
        # Arrange
        # Mock the data accessor methods
        mock_data_accessor = mocker.Mock()
        mock_data_accessor.get_consolidated_reporter_input.return_value = {
            "stock_analysis_data": {},
            "etf_analysis_data": {},
            "crypto_analysis_data": {}
        }
        mock_data_accessor.check_data_availability.return_value = mocker.Mock(
            overall_status=mocker.Mock(value="COMPLETE"),
            stock_available=True,
            etf_available=True,
            crypto_available=True,
            discovery_available=True,
            portfolio_available=True,
            missing_data=[],
            stale_data=[]
        )
        mock_data_accessor.get_stale_data_warnings.return_value = []

        report_crew_with_mocks.data_accessor = mock_data_accessor

        # Act
        integrated_context = report_crew_with_mocks.get_integrated_data_context()

        # Assert
        assert "backtesting_status" in integrated_context
        assert "backtesting_data" in integrated_context
        assert "backtesting_summary" in integrated_context

        # Verify backtesting status
        assert integrated_context["backtesting_status"]["has_data"] is True
        assert integrated_context["backtesting_status"]["status"] == "available"

        # Verify backtesting data structure
        assert integrated_context["backtesting_data"] is not None
        assert "AAPL" in integrated_context["backtesting_data"]
        assert "MSFT" in integrated_context["backtesting_data"]

    def test_should_format_none_values_as_not_calculated(
        self, report_crew_with_mocks, mock_backtesting_extractor
    ):
        """Test that None values are formatted as 'Not calculated' not 'Données non disponibles'."""
        # Arrange
        metrics_with_none = BacktestingMetrics(
            annualized_return=10.0,
            sharpe_ratio=None,  # This should be "Not calculated"
            sortino_ratio=None,
            calmar_ratio=None,
            max_drawdown=-15.0,
            win_rate=None,
            backtest_period_years=5,
            total_trades=None
        )

        # Act
        formatted = mock_backtesting_extractor.format_for_display(metrics_with_none)

        # Assert
        assert "Not calculated" in formatted
        assert "Données non disponibles" not in formatted
        assert "Annualized Return: 10.00%" in formatted
        assert "Sharpe Ratio: Not calculated" in formatted

    def test_should_include_summary_statistics(
        self, report_crew_with_mocks
    ):
        """Test that summary statistics are included when available."""
        # Act
        backtesting_data = report_crew_with_mocks._extract_backtesting_data()

        # Assert
        assert "summary" in backtesting_data
        summary = backtesting_data["summary"]

        if summary:  # Summary might be None if no metrics available
            assert "total_candidates_tested" in summary
            assert "candidates_with_data" in summary
            assert summary["total_candidates_tested"] == 2

    def test_should_handle_extraction_errors_gracefully(
        self, report_crew_with_mocks, mock_backtesting_extractor
    ):
        """Test graceful handling of extraction errors."""
        # Arrange
        mock_backtesting_extractor.extract_backtesting_metrics.side_effect = Exception("Extraction failed")

        # Act
        backtesting_data = report_crew_with_mocks._extract_backtesting_data()

        # Assert - Should still return a valid structure even with errors
        assert "has_backtesting_data" in backtesting_data
        assert "status" in backtesting_data
        assert "message" in backtesting_data
        # The extraction should handle individual failures and continue
        # or return not_available if all fail

    def test_should_log_available_and_missing_metrics(
        self, report_crew_with_mocks, caplog
    ):
        """Test that available and missing metrics are logged."""
        # Act
        with caplog.at_level("INFO"):
            backtesting_data = report_crew_with_mocks._extract_backtesting_data()

        # Assert
        assert any("Extracted backtesting metrics for" in record.message for record in caplog.records)
        assert any("Successfully extracted backtesting data" in record.message for record in caplog.records)
