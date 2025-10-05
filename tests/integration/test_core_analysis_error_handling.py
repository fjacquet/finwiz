"""
Integration tests for core analysis error handling.

Tests the error handling and graceful degradation functionality
in the main FinWiz flow.
"""

import pytest

from finwiz.flows.flow_orchestrator import FinwizFlow


class TestCoreAnalysisErrorHandlingIntegration:
    """Integration test suite for core analysis error handling."""

    @pytest.fixture
    def mock_crew_classes(self, mocker):
        """Mock the crew classes to simulate failures."""
        with (
            mocker.patch("finwiz.main.StockCrew") as mock_stock,
            mocker.patch("finwiz.main.EtfCrew") as mock_etf,
            mocker.patch("finwiz.main.CryptoCrew") as mock_crypto,
        ):
            # Configure mocks to raise exceptions
            mock_stock_instance = mocker.Mock()
            mock_stock_instance.crew.return_value.kickoff.side_effect = Exception("Stock API timeout")
            mock_stock.return_value = mock_stock_instance

            mock_etf_instance = mocker.Mock()
            mock_etf_instance.crew.return_value.kickoff.side_effect = Exception("ETF validation error")
            mock_etf.return_value = mock_etf_instance

            mock_crypto_instance = mocker.Mock()
            mock_crypto_instance.crew.return_value.kickoff.return_value = mocker.Mock(raw="Crypto analysis successful")
            mock_crypto.return_value = mock_crypto_instance

            yield {"stock": mock_stock, "etf": mock_etf, "crypto": mock_crypto}

    @pytest.fixture
    def mock_feature_flags(self, mocker):
        """Mock feature flags to enable all analysis crews."""
        with mocker.patch("finwiz.main.is_feature_enabled") as mock_flags:
            mock_flags.return_value = True
            yield mock_flags

    def test_should_continue_execution_when_individual_crews_fail(self, mocker, mock_crew_classes, mock_feature_flags):
        """Test that the system continues when individual crews fail."""
        # Create flow instance
        flow = FinwizFlow()

        # Mock the integration manager to avoid file system operations
        flow.integration_manager.store_crew_output = mocker.Mock(return_value=True)

        # Execute core analysis methods
        flow.check_stock()
        flow.check_etf()
        flow.check_crypto()

        # Verify that errors were handled gracefully
        assert flow.inputs.get("stock_analysis_error") is not None
        assert flow.inputs.get("etf_analysis_error") is not None
        assert flow.inputs.get("crypto_analysis_error") is None  # This one succeeded

        # Verify fallback information is stored
        assert flow.inputs.get("stock_analysis_fallback") is True
        assert flow.inputs.get("etf_analysis_fallback") is True
        assert flow.inputs.get("crypto_analysis_fallback") is None

        # Verify that successful crew results are still stored
        assert flow.inputs.get("crypto_analysis_result") is not None

    def test_should_provide_core_analysis_status_when_crews_fail(self, mocker, mock_crew_classes, mock_feature_flags):
        """Test that core analysis status is properly tracked."""
        # Create flow instance
        flow = FinwizFlow()

        # Mock the integration manager
        flow.integration_manager.store_crew_output = mocker.Mock(return_value=True)

        # Execute core analysis methods
        flow.check_stock()
        flow.check_etf()
        flow.check_crypto()

        # Check core analysis availability
        status = flow._check_core_analysis_availability()

        # Verify status tracking
        assert status["any_available"] is True  # Crypto succeeded
        assert status["stock_available"] is False  # Stock failed
        assert status["etf_available"] is False  # ETF failed
        assert status["crypto_available"] is True  # Crypto succeeded

        assert "stock" in status["failed_crews"]
        assert "etf" in status["failed_crews"]
        assert "crypto" not in status["failed_crews"]

        assert status["total_available"] == 1
        assert status["total_failed"] == 2

    def test_should_handle_complete_core_analysis_failure(self, mocker, mock_feature_flags):
        """Test handling when all core analysis crews fail."""
        with (
            mocker.patch("finwiz.main.StockCrew") as mock_stock,
            mocker.patch("finwiz.main.EtfCrew") as mock_etf,
            mocker.patch("finwiz.main.CryptoCrew") as mock_crypto,
        ):
            # Configure all mocks to fail
            for mock_crew in [mock_stock, mock_etf, mock_crypto]:
                mock_instance = mocker.Mock()
                mock_instance.crew.return_value.kickoff.side_effect = Exception("Complete failure")
                mock_crew.return_value = mock_instance

            # Create flow instance
            flow = FinwizFlow()
            flow.integration_manager.store_crew_output = mocker.Mock(return_value=True)

            # Execute core analysis methods
            flow.check_stock()
            flow.check_etf()
            flow.check_crypto()

            # Check core analysis availability
            status = flow._check_core_analysis_availability()

            # Verify complete failure is handled
            assert status["any_available"] is False
            assert status["total_available"] == 0
            assert status["total_failed"] == 3

            # Verify all crews have error information
            assert flow.inputs.get("stock_analysis_error") is not None
            assert flow.inputs.get("etf_analysis_error") is not None
            assert flow.inputs.get("crypto_analysis_error") is not None

    def test_should_use_error_handler_for_fallback_strategies(self, mocker, mock_crew_classes, mock_feature_flags):
        """Test that the error handler is used for fallback strategies."""
        # Create flow instance
        flow = FinwizFlow()

        # Mock the error handler
        mock_fallback_response = mocker.Mock()
        mock_fallback_response.success = True
        mock_fallback_response.data = {"fallback": "data"}
        mock_fallback_response.fallback_strategy = "cached_data"
        mock_fallback_response.degraded_functionality = ["stale_data"]

        flow.error_handler.handle_crew_failure = mocker.Mock(return_value=mock_fallback_response)
        flow.integration_manager.store_crew_output = mocker.Mock(return_value=True)

        # Execute stock analysis (which will fail)
        flow.check_stock()

        # Verify error handler was called
        flow.error_handler.handle_crew_failure.assert_called_once()
        call_args = flow.error_handler.handle_crew_failure.call_args

        assert call_args[1]["crew_name"] == "stock"
        assert isinstance(call_args[1]["error"], Exception)
        assert call_args[1]["inputs"] == flow.inputs

        # Verify fallback data was used
        assert flow.inputs.get("stock_fallback_strategy") == "cached_data"
        assert flow.inputs.get("stock_degraded_functionality") == ["stale_data"]

    def test_should_provide_system_health_information(self, mocker, mock_crew_classes, mock_feature_flags):
        """Test that system health information is available."""
        # Create flow instance
        flow = FinwizFlow()
        flow.integration_manager.store_crew_output = mocker.Mock(return_value=True)

        # Execute core analysis methods
        flow.check_stock()
        flow.check_etf()
        flow.check_crypto()

        # Get system health status
        health_status = flow.error_handler.get_system_health_status()

        # Verify health status structure
        assert "overall_status" in health_status
        assert "crew_status" in health_status
        assert "total_errors_24h" in health_status
        assert "degraded_crews" in health_status

        # Verify crew-specific status
        assert "stock" in health_status["crew_status"]
        assert "etf" in health_status["crew_status"]
        assert "crypto" in health_status["crew_status"]

    def test_should_handle_disabled_crews_gracefully(self, mocker):
        """Test handling of disabled crews via feature flags."""
        with mocker.patch("finwiz.main.is_feature_enabled") as mock_flags:
            # Disable stock analysis
            def feature_enabled(flag_name):
                return flag_name != "stock_analysis"

            mock_flags.side_effect = feature_enabled

            # Create flow instance
            flow = FinwizFlow()

            # Execute core analysis methods
            flow.check_stock()  # Should be disabled
            flow.check_etf()  # Should be enabled
            flow.check_crypto()  # Should be enabled

            # Verify disabled crew is marked correctly
            assert flow.inputs.get("stock_analysis_disabled") is True
            assert flow.inputs.get("etf_analysis_disabled") is None
            assert flow.inputs.get("crypto_analysis_disabled") is None

            # Check status
            status = flow._check_core_analysis_availability()
            assert "stock" in status["disabled_crews"]
            assert "etf" not in status["disabled_crews"]
            assert "crypto" not in status["disabled_crews"]
