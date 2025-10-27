"""
Unit tests for ReportCrew context preservation.

Tests that prepare_crew_context properly preserves all Flow state inputs
to prevent template variable errors and ensure discovery results are passed through.
"""

import pytest


class TestReportCrewContextPreservation:
    """Test suite for ReportCrew context preservation."""

    @pytest.fixture
    def mock_report_crew(self, mocker):
        """Create a mock ReportCrew instance."""
        # Mock the imports and dependencies
        mocker.patch("finwiz.crews.report_crew.report_crew.CrewDataIntegrationManager")
        mocker.patch("finwiz.crews.report_crew.report_crew.CrewDataAccessor")
        mocker.patch("finwiz.crews.report_crew.report_crew.APlusDiscoveryAccessor")
        mocker.patch("finwiz.crews.report_crew.report_crew.BacktestingDataExtractor")
        mocker.patch("finwiz.crews.report_crew.report_crew.DataAvailabilityTracker")
        mocker.patch("finwiz.crews.report_crew.report_crew.get_rag_tools", return_value=[])
        mocker.patch("finwiz.crews.report_crew.report_crew.make_tools_robust", return_value=[])

        # Import after mocking
        from finwiz.crews.report_crew.report_crew import ReportCrew

        # Create instance
        crew = ReportCrew()

        # Mock the get_integrated_data_context method to return minimal data
        crew.get_integrated_data_context = mocker.Mock(
            return_value={
                "data_availability_report": {"overall_status": "available"},
                "stale_data_warnings": [],
            }
        )

        # Mock the validate_reporter_input method
        crew.validate_reporter_input = mocker.Mock()

        return crew

    def test_should_preserve_portfolio_review_from_inputs(self, mock_report_crew):
        """Test that portfolio_review is preserved from Flow state inputs."""
        # Arrange
        flow_inputs = {
            "portfolio_review": {
                "portfolio_review": {
                    "holdings": [
                        {"ticker": "AAPL", "asset_class": "stock"},
                        {"ticker": "GOOGL", "asset_class": "stock"},
                    ]
                }
            },
            "current_date": "2025-01-18",
            "report_language": "fr",
        }

        # Act
        result = mock_report_crew.prepare_crew_context(max_age_hours=24, inputs=flow_inputs)

        # Assert
        assert "portfolio_review" in result, "portfolio_review should be preserved"
        assert result["portfolio_review"] == flow_inputs["portfolio_review"]

    def test_should_preserve_discovery_results_from_inputs(self, mock_report_crew):
        """Test that discovery results are preserved from Flow state inputs."""
        # Arrange
        flow_inputs = {
            "aplus_opportunities": {
                "stocks": {"a_plus_candidates": [{"ticker": "NVDA"}]},
                "etfs": {"a_plus_candidates": []},
                "crypto": {"a_plus_candidates": []},
            },
            "investment_discovery_structured": {
                "has_a_plus_analysis": True,
                "validation_results": [],
            },
            "investment_discovery_result": "Discovery completed successfully",
            "investment_discovery_available": True,
            "current_date": "2025-01-18",
            "report_language": "fr",
        }

        # Act
        result = mock_report_crew.prepare_crew_context(max_age_hours=24, inputs=flow_inputs)

        # Assert
        assert "aplus_opportunities" in result, "aplus_opportunities should be preserved"
        assert "investment_discovery_structured" in result, "investment_discovery_structured should be preserved"
        assert "investment_discovery_result" in result, "investment_discovery_result should be preserved"
        assert result["aplus_opportunities"] == flow_inputs["aplus_opportunities"]

    def test_should_construct_validated_tickers_list_from_portfolio(self, mock_report_crew):
        """Test that validated_tickers_list is constructed from portfolio_review."""
        # Arrange
        flow_inputs = {
            "portfolio_review": {
                "portfolio_review": {
                    "holdings": [
                        {"ticker": "AAPL", "asset_class": "stock"},
                        {"ticker": "GOOGL", "asset_class": "stock"},
                        {"ticker": "BTC-USD", "asset_class": "crypto"},
                    ]
                }
            },
            "current_date": "2025-01-18",
            "report_language": "fr",
        }

        # Act
        result = mock_report_crew.prepare_crew_context(max_age_hours=24, inputs=flow_inputs)

        # Assert
        assert "validated_tickers_list" in result, "validated_tickers_list should be constructed"
        assert isinstance(result["validated_tickers_list"], list)
        assert "AAPL" in result["validated_tickers_list"]
        assert "GOOGL" in result["validated_tickers_list"]
        assert "BTC-USD" in result["validated_tickers_list"]

    def test_should_construct_discovery_status_when_discovery_run(self, mock_report_crew):
        """Test that discovery_status is constructed when discovery was run."""
        # Arrange
        flow_inputs = {
            "investment_discovery_available": True,
            "aplus_opportunities": {
                "stocks": {"a_plus_candidates": [{"ticker": "NVDA"}]},
            },
            "current_date": "2025-01-18",
            "report_language": "fr",
        }

        # Act
        result = mock_report_crew.prepare_crew_context(max_age_hours=24, inputs=flow_inputs)

        # Assert
        assert "discovery_status" in result, "discovery_status should be constructed"
        assert result["discovery_status"]["has_results"] is True
        assert result["discovery_status"]["status"] == "available"

    def test_should_construct_discovery_status_when_discovery_not_run(self, mock_report_crew):
        """Test that discovery_status indicates not run when discovery was not executed."""
        # Arrange
        flow_inputs = {
            "investment_discovery_available": False,
            "current_date": "2025-01-18",
            "report_language": "fr",
        }

        # Act
        result = mock_report_crew.prepare_crew_context(max_age_hours=24, inputs=flow_inputs)

        # Assert
        assert "discovery_status" in result, "discovery_status should be constructed"
        assert result["discovery_status"]["has_results"] is False
        assert result["discovery_status"]["status"] == "not_run"
        assert "use --discovery flag" in result["discovery_status"]["message"]

    def test_should_construct_backtesting_status_when_available(self, mock_report_crew):
        """Test that backtesting_status is constructed when backtesting data is available."""
        # Arrange
        flow_inputs = {
            "investment_discovery_structured": {
                "validation_results": [
                    {"ticker": "NVDA", "sharpe_ratio": 1.5},
                    {"ticker": "AMD", "sharpe_ratio": 1.3},
                ]
            },
            "current_date": "2025-01-18",
            "report_language": "fr",
        }

        # Act
        result = mock_report_crew.prepare_crew_context(max_age_hours=24, inputs=flow_inputs)

        # Assert
        assert "backtesting_status" in result, "backtesting_status should be constructed"
        assert result["backtesting_status"]["has_data"] is True
        assert result["backtesting_status"]["status"] == "available"

    def test_should_construct_backtesting_status_when_not_available(self, mock_report_crew):
        """Test that backtesting_status indicates not available when no data."""
        # Arrange
        flow_inputs = {
            "current_date": "2025-01-18",
            "report_language": "fr",
        }

        # Act
        result = mock_report_crew.prepare_crew_context(max_age_hours=24, inputs=flow_inputs)

        # Assert
        assert "backtesting_status" in result, "backtesting_status should be constructed"
        assert result["backtesting_status"]["has_data"] is False
        assert result["backtesting_status"]["status"] == "not_available"

    def test_should_preserve_all_required_metadata_fields(self, mock_report_crew):
        """Test that all required metadata fields are preserved."""
        # Arrange
        flow_inputs = {
            "current_day": "18",
            "current_month": "January",
            "current_year": "2025",
            "current_date": "2025-01-18",
            "full_date": "January 18, 2025",
            "timestamp": "2025-01-18T10:30:00",
            "report_language": "fr",
        }

        # Act
        result = mock_report_crew.prepare_crew_context(max_age_hours=24, inputs=flow_inputs)

        # Assert
        for key in ["current_day", "current_month", "current_year", "current_date", "full_date", "timestamp", "report_language"]:
            assert key in result, f"{key} should be preserved"
            assert result[key] == flow_inputs[key]

    def test_should_preserve_data_availability_summary_formatted(self, mock_report_crew):
        """Test that data_availability_summary_formatted is preserved."""
        # Arrange
        flow_inputs = {
            "data_availability_summary_formatted": "All data sources available",
            "current_date": "2025-01-18",
            "report_language": "fr",
        }

        # Act
        result = mock_report_crew.prepare_crew_context(max_age_hours=24, inputs=flow_inputs)

        # Assert
        assert "data_availability_summary_formatted" in result
        assert result["data_availability_summary_formatted"] == flow_inputs["data_availability_summary_formatted"]

    def test_should_handle_missing_inputs_gracefully(self, mock_report_crew):
        """Test that missing inputs are handled gracefully without errors."""
        # Arrange - no inputs provided

        # Act
        result = mock_report_crew.prepare_crew_context(max_age_hours=24, inputs=None)

        # Assert - should not raise exception
        assert isinstance(result, dict)
        assert "data_availability_report" in result  # From get_integrated_data_context

    def test_should_preserve_rebalancing_results(self, mock_report_crew):
        """Test that portfolio rebalancing results are preserved."""
        # Arrange
        flow_inputs = {
            "portfolio_rebalancing_result": "Rebalancing completed",
            "portfolio_rebalancing_available": True,
            "current_date": "2025-01-18",
            "report_language": "fr",
        }

        # Act
        result = mock_report_crew.prepare_crew_context(max_age_hours=24, inputs=flow_inputs)

        # Assert
        assert "portfolio_rebalancing_result" in result
        assert "portfolio_rebalancing_available" in result
        assert result["portfolio_rebalancing_available"] is True

    def test_should_preserve_deep_analysis_results(self, mock_report_crew):
        """Test that deep analysis results are preserved."""
        # Arrange
        flow_inputs = {
            "deep_analysis_results": {
                "AAPL": {"grade": "A+", "composite_score": 0.95},
                "GOOGL": {"grade": "A", "composite_score": 0.88},
            },
            "deep_analysis_success": True,
            "current_date": "2025-01-18",
            "report_language": "fr",
        }

        # Act
        result = mock_report_crew.prepare_crew_context(max_age_hours=24, inputs=flow_inputs)

        # Assert
        assert "deep_analysis_results" in result
        assert "deep_analysis_success" in result
        assert result["deep_analysis_success"] is True
        assert "AAPL" in result["deep_analysis_results"]
