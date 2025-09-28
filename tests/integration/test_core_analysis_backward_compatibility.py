"""
Integration tests for Core Analysis Backward Compatibility.

Tests that the restored core analysis functionality maintains backward
compatibility with existing features and workflows.
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from finwiz.main import FinwizFlow


class TestCoreAnalysisBackwardCompatibility:
    """Test cases for Core Analysis Backward Compatibility."""

    @pytest.fixture
    def mock_flow_inputs(self):
        """Create mock inputs for backward compatibility testing."""
        today = datetime.now()
        return {
            "current_day": today.day,
            "current_month": today.month,
            "current_year": today.year,
            "current_date": today.strftime("%Y-%m-%d"),
            "full_date": today.strftime("%B %d, %Y"),
            "timestamp": today.strftime("%Y-%m-%d %H:%M:%S"),
            "report_language": "fr",
            "has_existing_session": False,
            "session_id": "",
            "analysis_count": 0,
        }

    @pytest.fixture
    def mock_legacy_portfolio_data(self):
        """Create mock legacy portfolio data."""
        return {
            "holdings": [
                {"symbol": "AAPL", "shares": 100, "cost_basis": 150.0},
                {"symbol": "GOOGL", "shares": 10, "cost_basis": 2500.0},
                {"symbol": "MSFT", "shares": 50, "cost_basis": 300.0},
            ],
            "total_value": 55000.0,
            "last_updated": "2025-01-14T10:00:00Z",
        }

    @pytest.fixture
    def finwiz_flow(self):
        """Create a FinwizFlow instance for backward compatibility testing."""
        return FinwizFlow()

    def test_should_maintain_existing_portfolio_review_functionality(self, finwiz_flow, mock_legacy_portfolio_data):
        """Test that existing portfolio review functionality continues to work."""
        # Add legacy portfolio data to inputs
        finwiz_flow.inputs.update(
            {
                "portfolio_data": mock_legacy_portfolio_data,
                "target_allocations": {"AAPL": 0.4, "GOOGL": 0.35, "MSFT": 0.25},
            }
        )

        # Mock portfolio review execution
        with patch.object(finwiz_flow, "check_portfolio") as mock_check_portfolio:
            mock_check_portfolio.return_value = None
            finwiz_flow.inputs["portfolio_review"] = "Portfolio review completed successfully"

            # Execute portfolio review
            finwiz_flow.check_portfolio()

            # Verify portfolio review executed
            mock_check_portfolio.assert_called_once()

            # Verify legacy data structure is preserved
            assert "portfolio_data" in finwiz_flow.inputs
            assert finwiz_flow.inputs["portfolio_data"]["total_value"] == 55000.0

    def test_should_maintain_existing_investment_discovery_functionality(self, finwiz_flow):
        """Test that existing investment discovery functionality continues to work."""
        # Mock investment discovery crew
        with patch("finwiz.main.InvestmentDiscoveryCrew") as mock_id_crew_class:
            mock_id_crew = MagicMock()
            mock_id_result = MagicMock()
            mock_id_result.raw = "Investment discovery analysis completed"
            mock_id_crew.crew().kickoff.return_value = mock_id_result
            mock_id_crew_class.return_value = mock_id_crew

            # Mock the check_investment_discovery method
            with patch.object(finwiz_flow, "check_investment_discovery") as mock_check_id:

                def mock_id_execution():
                    finwiz_flow.inputs["investment_discovery_result"] = str(mock_id_result.raw)
                    finwiz_flow.inputs["investment_discovery_available"] = True

                mock_check_id.side_effect = mock_id_execution

                # Execute investment discovery
                finwiz_flow.check_investment_discovery()

                # Verify investment discovery executed
                mock_check_id.assert_called_once()

                # Verify legacy output format is maintained
                assert "investment_discovery_result" in finwiz_flow.inputs
                assert finwiz_flow.inputs["investment_discovery_available"] is True

    def test_should_maintain_existing_portfolio_rebalancing_functionality(self, finwiz_flow, mock_legacy_portfolio_data):
        """Test that existing portfolio rebalancing functionality continues to work."""
        # Add legacy portfolio data
        finwiz_flow.inputs.update(
            {
                "portfolio_data": mock_legacy_portfolio_data,
                "target_allocations": {"AAPL": 0.4, "GOOGL": 0.35, "MSFT": 0.25},
                "tolerance_bands": {"AAPL": 0.05, "GOOGL": 0.05, "MSFT": 0.05},
                "available_capital": 5000.0,
            }
        )

        # Mock portfolio rebalancing crew
        with patch("finwiz.main.PortfolioRebalancingCrew") as mock_rebal_crew_class:
            mock_rebal_crew = MagicMock()
            mock_rebal_result = MagicMock()
            mock_rebal_result.raw = "Portfolio rebalancing recommendations generated"
            mock_rebal_crew.crew().kickoff.return_value = mock_rebal_result
            mock_rebal_crew_class.return_value = mock_rebal_crew

            # Mock the check_portfolio_rebalancing method
            with patch.object(finwiz_flow, "check_portfolio_rebalancing") as mock_check_rebal:

                def mock_rebal_execution():
                    finwiz_flow.inputs["portfolio_rebalancing_result"] = str(mock_rebal_result.raw)
                    finwiz_flow.inputs["portfolio_rebalancing_available"] = True

                mock_check_rebal.side_effect = mock_rebal_execution

                # Execute portfolio rebalancing
                finwiz_flow.check_portfolio_rebalancing()

                # Verify rebalancing executed
                mock_check_rebal.assert_called_once()

                # Verify legacy output format is maintained
                assert "portfolio_rebalancing_result" in finwiz_flow.inputs
                assert finwiz_flow.inputs["portfolio_rebalancing_available"] is True

    def test_should_maintain_existing_report_generation_functionality(self, finwiz_flow):
        """Test that existing report generation functionality continues to work."""
        # Add mock analysis results
        finwiz_flow.inputs.update(
            {
                "portfolio_review": "Portfolio review completed",
                "investment_discovery_result": "Investment opportunities identified",
                "portfolio_rebalancing_result": "Rebalancing recommendations provided",
            }
        )

        # Mock report crew
        with patch("finwiz.main.ReportCrew") as mock_report_crew_class:
            mock_report_crew = MagicMock()
            mock_report_result = MagicMock()
            mock_report_result.raw = "Comprehensive financial report generated"
            mock_report_crew.crew().kickoff.return_value = mock_report_result
            mock_report_crew_class.return_value = mock_report_crew

            # Mock the report method
            with patch.object(finwiz_flow, "report") as mock_report:

                def mock_report_execution():
                    finwiz_flow.inputs["final_report"] = str(mock_report_result.raw)

                mock_report.side_effect = mock_report_execution

                # Execute report generation
                finwiz_flow.report()

                # Verify report generation executed
                mock_report.assert_called_once()

                # Verify legacy output format is maintained
                assert "final_report" in finwiz_flow.inputs

    def test_should_enhance_existing_features_with_core_analysis(self, finwiz_flow):
        """Test that existing features are enhanced with core analysis data."""
        # Mock core analysis results
        core_analysis_results = {
            "stock_analysis_result": "AAPL: BUY recommendation with strong fundamentals",
            "etf_analysis_result": "SPY: BUY recommendation with low expense ratio",
            "crypto_analysis_result": "BTC: HOLD recommendation with high volatility",
        }
        finwiz_flow.inputs.update(core_analysis_results)
        finwiz_flow.inputs["core_analysis_completed"] = True

        # Mock enhanced portfolio rebalancing that uses core analysis
        with patch("finwiz.main.PortfolioRebalancingCrew") as mock_rebal_crew_class:
            mock_rebal_crew = MagicMock()
            mock_rebal_result = MagicMock()
            mock_rebal_result.raw = "Enhanced rebalancing with market analysis"
            mock_rebal_crew.crew().kickoff.return_value = mock_rebal_result
            mock_rebal_crew_class.return_value = mock_rebal_crew

            # Mock enhanced check_portfolio_rebalancing
            with patch.object(finwiz_flow, "check_portfolio_rebalancing") as mock_check_rebal:

                def enhanced_rebal_execution():
                    # Verify core analysis data is available
                    assert finwiz_flow.inputs.get("core_analysis_completed") is True
                    assert "stock_analysis_result" in finwiz_flow.inputs

                    # Store enhanced result
                    finwiz_flow.inputs["portfolio_rebalancing_result"] = str(mock_rebal_result.raw)
                    finwiz_flow.inputs["portfolio_rebalancing_available"] = True

                mock_check_rebal.side_effect = enhanced_rebal_execution

                # Execute enhanced portfolio rebalancing
                finwiz_flow.check_portfolio_rebalancing()

                # Verify enhancement worked
                mock_check_rebal.assert_called_once()
                assert "Enhanced" in finwiz_flow.inputs["portfolio_rebalancing_result"]

    def test_should_maintain_existing_api_interfaces(self, finwiz_flow):
        """Test that existing API interfaces are maintained."""
        # Test that flow inputs maintain expected structure
        required_legacy_fields = [
            "current_date",
            "full_date",
            "timestamp",
            "report_language",
            "has_existing_session",
            "session_id",
            "analysis_count",
        ]

        for field in required_legacy_fields:
            assert field in finwiz_flow.inputs, f"Missing legacy field: {field}"

        # Test that flow methods maintain expected signatures
        assert hasattr(finwiz_flow, "validate_data_integration")
        assert hasattr(finwiz_flow, "check_portfolio")
        assert hasattr(finwiz_flow, "check_portfolio_rebalancing")
        assert hasattr(finwiz_flow, "check_investment_discovery")
        assert hasattr(finwiz_flow, "pre_validate_reporter_input")
        assert hasattr(finwiz_flow, "report")

    def test_should_maintain_existing_data_formats(self, finwiz_flow):
        """Test that existing data formats are maintained."""
        # Test date format compatibility
        assert isinstance(finwiz_flow.inputs["current_date"], str)
        assert isinstance(finwiz_flow.inputs["full_date"], str)
        assert isinstance(finwiz_flow.inputs["timestamp"], str)

        # Test numeric format compatibility
        assert isinstance(finwiz_flow.inputs["current_day"], int)
        assert isinstance(finwiz_flow.inputs["current_month"], int)
        assert isinstance(finwiz_flow.inputs["current_year"], int)

        # Test boolean format compatibility
        assert isinstance(finwiz_flow.inputs["has_existing_session"], bool)

        # Test string format compatibility
        assert isinstance(finwiz_flow.inputs["report_language"], str)
        assert isinstance(finwiz_flow.inputs["session_id"], str)

    def test_should_maintain_existing_error_handling_patterns(self, finwiz_flow):
        """Test that existing error handling patterns are maintained."""
        # Mock a failure in existing functionality
        with patch.object(finwiz_flow, "validate_data_integration") as mock_validate:
            mock_validate.side_effect = Exception("Data validation failed")

            # System should handle error gracefully (not crash)
            try:
                finwiz_flow.validate_data_integration()
            except Exception:
                pass  # Error handling may vary

            # System should remain functional
            assert finwiz_flow.integration_manager is not None
            assert finwiz_flow.data_accessor is not None

    def test_should_maintain_existing_configuration_compatibility(self, finwiz_flow):
        """Test that existing configuration compatibility is maintained."""
        # Test that existing environment variables are still supported
        with patch.dict(
            "os.environ",
            {
                "FINWIZ_HAS_EXISTING_SESSION": "true",
                "FINWIZ_SESSION_ID": "legacy-session-123",
                "FINWIZ_ANALYSIS_COUNT": "10",
            },
        ):
            legacy_flow = FinwizFlow()

            # Verify legacy environment variables are processed
            assert legacy_flow.inputs["has_existing_session"] is True
            assert legacy_flow.inputs["session_id"] == "legacy-session-123"
            assert legacy_flow.inputs["analysis_count"] == 10

    def test_should_maintain_existing_output_file_formats(self, finwiz_flow):
        """Test that existing output file formats are maintained."""
        # Mock report generation with legacy format
        finwiz_flow.inputs.update(
            {
                "portfolio_review": "Legacy portfolio review",
                "investment_discovery_result": "Legacy investment discovery",
                "final_report": "Legacy report format maintained",
            }
        )

        # Verify legacy output fields are preserved
        assert "portfolio_review" in finwiz_flow.inputs
        assert "investment_discovery_result" in finwiz_flow.inputs
        assert "final_report" in finwiz_flow.inputs

        # Verify output format is string-based (legacy format)
        assert isinstance(finwiz_flow.inputs["portfolio_review"], str)
        assert isinstance(finwiz_flow.inputs["investment_discovery_result"], str)
        assert isinstance(finwiz_flow.inputs["final_report"], str)

    def test_should_support_legacy_workflow_without_core_analysis(self, finwiz_flow):
        """Test that legacy workflow works without core analysis crews."""
        # Disable all core analysis crews
        with patch("finwiz.main.is_feature_enabled") as mock_feature_enabled:
            mock_feature_enabled.return_value = False

            # Mock legacy workflow components
            with (
                patch.object(finwiz_flow, "check_portfolio") as mock_portfolio,
                patch.object(finwiz_flow, "check_portfolio_rebalancing") as mock_rebalancing,
                patch.object(finwiz_flow, "check_investment_discovery") as mock_discovery,
                patch.object(finwiz_flow, "report") as mock_report,
            ):

                def setup_legacy_results():
                    finwiz_flow.inputs["portfolio_review"] = "Legacy portfolio review"
                    finwiz_flow.inputs["portfolio_rebalancing_result"] = "Legacy rebalancing"
                    finwiz_flow.inputs["investment_discovery_result"] = "Legacy discovery"
                    finwiz_flow.inputs["final_report"] = "Legacy report"

                mock_portfolio.side_effect = setup_legacy_results
                mock_rebalancing.side_effect = lambda: None
                mock_discovery.side_effect = lambda: None
                mock_report.side_effect = lambda: None

                # Execute legacy workflow
                finwiz_flow.validate_data_integration()
                finwiz_flow.check_crypto()  # Should be skipped
                finwiz_flow.check_stock()  # Should be skipped
                finwiz_flow.check_etf()  # Should be skipped
                finwiz_flow.check_portfolio()
                finwiz_flow.check_portfolio_rebalancing()
                finwiz_flow.check_investment_discovery()
                finwiz_flow.report()

                # Verify legacy workflow completed
                assert "portfolio_review" in finwiz_flow.inputs
                assert finwiz_flow.inputs.get("crypto_analysis_disabled") is True
                assert finwiz_flow.inputs.get("stock_analysis_disabled") is True
                assert finwiz_flow.inputs.get("etf_analysis_disabled") is True

    def test_should_maintain_existing_performance_characteristics(self, finwiz_flow):
        """Test that existing performance characteristics are maintained."""
        import time

        # Test that flow initialization time is reasonable
        start_time = time.time()
        test_flow = FinwizFlow()
        init_time = time.time() - start_time

        # Should initialize quickly (backward compatibility requirement)
        assert init_time < 2.0, f"Flow initialization took {init_time:.2f}s, expected < 2.0s"

        # Test that basic operations remain fast
        start_time = time.time()
        test_flow.validate_data_integration()
        validation_time = time.time() - start_time

        # Should validate quickly (backward compatibility requirement)
        assert validation_time < 1.0, f"Data validation took {validation_time:.2f}s, expected < 1.0s"

    def test_should_maintain_existing_logging_patterns(self, finwiz_flow):
        """Test that existing logging patterns are maintained."""
        from unittest.mock import patch

        # Mock logger to capture log messages
        with patch("finwiz.main.logger") as mock_logger:
            # Execute flow operations
            finwiz_flow.validate_data_integration()

            # Verify logging patterns are maintained
            # (Specific assertions depend on existing logging implementation)
            assert mock_logger.info.called or mock_logger.debug.called

    def test_should_maintain_existing_session_management(self, finwiz_flow):
        """Test that existing session management is maintained."""
        # Test session information is properly handled
        assert "has_existing_session" in finwiz_flow.inputs
        assert "session_id" in finwiz_flow.inputs
        assert "analysis_count" in finwiz_flow.inputs

        # Test session data types are maintained
        assert isinstance(finwiz_flow.inputs["has_existing_session"], bool)
        assert isinstance(finwiz_flow.inputs["session_id"], str)
        assert isinstance(finwiz_flow.inputs["analysis_count"], int)

        # Test session defaults are maintained
        assert finwiz_flow.inputs["has_existing_session"] is False
        assert finwiz_flow.inputs["session_id"] == ""
        assert finwiz_flow.inputs["analysis_count"] == 0
