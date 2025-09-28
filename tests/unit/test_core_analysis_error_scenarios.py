"""
Unit tests for Core Analysis Error Scenarios.

Tests error handling, graceful degradation, and recovery mechanisms
for core analysis functionality.
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from finwiz.main import FinwizFlow


class TestCoreAnalysisErrorScenarios:
    """Test cases for Core Analysis Error Scenarios."""

    @pytest.fixture
    def mock_flow_inputs(self):
        """Create mock inputs for error scenario testing."""
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
    def finwiz_flow(self):
        """Create a FinwizFlow instance for error testing."""
        return FinwizFlow()

    @pytest.fixture
    def error_handler(self, finwiz_flow):
        """Create an error handler for testing."""
        return finwiz_flow.error_handler

    def test_should_handle_crew_initialization_failure(self, finwiz_flow):
        """Test handling of crew initialization failures."""
        with patch("finwiz.main.is_feature_enabled", return_value=True):
            with patch("finwiz.main.StockCrew") as mock_stock_crew_class:
                # Mock crew initialization failure
                mock_stock_crew_class.side_effect = Exception("Crew initialization failed")

                # Execute should handle the error gracefully
                finwiz_flow.check_stock()

                # Verify error was handled
                assert finwiz_flow.inputs.get("stock_analysis_success") is False
                assert "stock_analysis_error" in finwiz_flow.inputs

    def test_should_handle_crew_kickoff_failure(self, finwiz_flow):
        """Test handling of crew kickoff failures."""
        with patch("finwiz.main.is_feature_enabled", return_value=True):
            with patch("finwiz.main.StockCrew") as mock_stock_crew_class:
                # Mock crew that fails during kickoff
                mock_stock_crew = MagicMock()
                mock_stock_crew.crew().kickoff.side_effect = Exception("Crew execution failed")
                mock_stock_crew_class.return_value = mock_stock_crew

                # Execute should handle the error gracefully
                finwiz_flow.check_stock()

                # Verify error was handled
                assert finwiz_flow.inputs["stock_analysis_success"] is False
                assert finwiz_flow.inputs["stock_analysis_fallback"] is True
                assert "stock_analysis_error" in finwiz_flow.inputs

    def test_should_handle_api_connection_failures(self, finwiz_flow):
        """Test handling of API connection failures."""
        with patch("finwiz.main.is_feature_enabled", return_value=True):
            with patch("finwiz.main.CryptoCrew") as mock_crypto_crew_class:
                # Mock API connection failure
                mock_crypto_crew = MagicMock()
                mock_crypto_crew.crew().kickoff.side_effect = ConnectionError("API connection failed")
                mock_crypto_crew_class.return_value = mock_crypto_crew

                # Mock error handler response
                mock_fallback_response = MagicMock()
                mock_fallback_response.success = False
                mock_fallback_response.message = "API connection failed, no fallback available"
                mock_fallback_response.fallback_strategy = "skip"
                mock_fallback_response.degraded_functionality = ["no_crypto_data"]
                finwiz_flow.error_handler.handle_crew_failure.return_value = mock_fallback_response

                # Execute should handle the error gracefully
                finwiz_flow.check_crypto()

                # Verify error was handled
                assert finwiz_flow.inputs["crypto_analysis_success"] is False
                assert finwiz_flow.inputs["crypto_fallback_strategy"] == "skip"
                assert finwiz_flow.inputs["crypto_degraded_functionality"] == ["no_crypto_data"]

    def test_should_handle_timeout_errors(self, finwiz_flow):
        """Test handling of timeout errors."""
        with patch("finwiz.main.is_feature_enabled", return_value=True):
            with patch("finwiz.main.EtfCrew") as mock_etf_crew_class:
                # Mock timeout error
                mock_etf_crew = MagicMock()
                mock_etf_crew.crew().kickoff.side_effect = TimeoutError("Crew execution timed out")
                mock_etf_crew_class.return_value = mock_etf_crew

                # Execute should handle the error gracefully
                finwiz_flow.check_etf()

                # Verify error was handled
                assert finwiz_flow.inputs["etf_analysis_success"] is False
                assert "etf_analysis_error" in finwiz_flow.inputs
                assert "timed out" in str(finwiz_flow.inputs["etf_analysis_error"])

    def test_should_handle_memory_errors(self, finwiz_flow):
        """Test handling of memory errors."""
        with patch("finwiz.main.is_feature_enabled", return_value=True):
            with patch("finwiz.main.StockCrew") as mock_stock_crew_class:
                # Mock memory error
                mock_stock_crew = MagicMock()
                mock_stock_crew.crew().kickoff.side_effect = MemoryError("Insufficient memory")
                mock_stock_crew_class.return_value = mock_stock_crew

                # Execute should handle the error gracefully
                finwiz_flow.check_stock()

                # Verify error was handled
                assert finwiz_flow.inputs["stock_analysis_success"] is False
                assert "stock_analysis_error" in finwiz_flow.inputs

    def test_should_handle_data_validation_errors(self, finwiz_flow):
        """Test handling of data validation errors."""
        with patch("finwiz.main.is_feature_enabled", return_value=True):
            with patch("finwiz.main.CryptoCrew") as mock_crypto_crew_class:
                # Mock data validation error
                mock_crypto_crew = MagicMock()
                mock_crypto_crew.crew().kickoff.side_effect = ValueError("Invalid data format")
                mock_crypto_crew_class.return_value = mock_crypto_crew

                # Execute should handle the error gracefully
                finwiz_flow.check_crypto()

                # Verify error was handled
                assert finwiz_flow.inputs["crypto_analysis_success"] is False
                assert "crypto_analysis_error" in finwiz_flow.inputs

    def test_should_use_cached_data_as_fallback(self, finwiz_flow):
        """Test that cached data is used as fallback when available."""
        with patch("finwiz.main.is_feature_enabled", return_value=True):
            with patch("finwiz.main.StockCrew") as mock_stock_crew_class:
                # Mock crew failure
                mock_stock_crew = MagicMock()
                mock_stock_crew.crew().kickoff.side_effect = Exception("API failed")
                mock_stock_crew_class.return_value = mock_stock_crew

                # Mock successful fallback with cached data
                cached_data = {
                    "analysis": "Cached stock analysis",
                    "recommendation": "HOLD",
                    "risk_score": 5,
                    "confidence": 0.7,
                    "timestamp": "2025-01-14T10:00:00",
                    "source": "cache",
                }
                mock_fallback_response = MagicMock()
                mock_fallback_response.success = True
                mock_fallback_response.data = cached_data
                mock_fallback_response.message = "Using cached data from yesterday"
                mock_fallback_response.fallback_strategy = "cached_data"
                mock_fallback_response.degraded_functionality = ["stale_data"]
                finwiz_flow.error_handler.handle_crew_failure.return_value = mock_fallback_response

                # Execute should use fallback data
                finwiz_flow.check_stock()

                # Verify fallback data was used
                assert finwiz_flow.inputs["stock_analysis_success"] is False
                assert finwiz_flow.inputs["stock_analysis_fallback"] is True
                assert finwiz_flow.inputs["stock_fallback_strategy"] == "cached_data"
                assert "stock_analysis_result" in finwiz_flow.inputs

    def test_should_handle_partial_crew_failures(self, finwiz_flow):
        """Test handling when some crews succeed and others fail."""
        with patch("finwiz.main.is_feature_enabled", return_value=True):
            with (
                patch("finwiz.main.StockCrew") as mock_stock_crew_class,
                patch("finwiz.main.EtfCrew") as mock_etf_crew_class,
                patch("finwiz.main.CryptoCrew") as mock_crypto_crew_class,
            ):
                # Mock successful stock crew
                mock_stock_crew = MagicMock()
                mock_stock_result = MagicMock()
                mock_stock_result.raw = "Successful stock analysis"
                mock_stock_crew.crew().kickoff.return_value = mock_stock_result
                mock_stock_crew_class.return_value = mock_stock_crew

                # Mock successful ETF crew
                mock_etf_crew = MagicMock()
                mock_etf_result = MagicMock()
                mock_etf_result.raw = "Successful ETF analysis"
                mock_etf_crew.crew().kickoff.return_value = mock_etf_result
                mock_etf_crew_class.return_value = mock_etf_crew

                # Mock failing crypto crew
                mock_crypto_crew = MagicMock()
                mock_crypto_crew.crew().kickoff.side_effect = Exception("Crypto API failed")
                mock_crypto_crew_class.return_value = mock_crypto_crew

                # Mock error handler for crypto failure
                mock_fallback_response = MagicMock()
                mock_fallback_response.success = False
                mock_fallback_response.message = "Crypto analysis failed"
                finwiz_flow.error_handler.handle_crew_failure.return_value = mock_fallback_response

                # Execute all crews
                finwiz_flow.check_stock()
                finwiz_flow.check_etf()
                finwiz_flow.check_crypto()

                # Verify partial success
                assert finwiz_flow.inputs["stock_analysis_success"] is True
                assert finwiz_flow.inputs["etf_analysis_success"] is True
                assert finwiz_flow.inputs["crypto_analysis_success"] is False

                # Verify successful results are available
                assert "stock_analysis_result" in finwiz_flow.inputs
                assert "etf_analysis_result" in finwiz_flow.inputs

    def test_should_handle_integration_system_failures(self, finwiz_flow):
        """Test handling of data integration system failures."""
        with patch("finwiz.main.is_feature_enabled", return_value=True):
            with patch("finwiz.main.StockCrew") as mock_stock_crew_class:
                # Mock successful crew
                mock_stock_crew = MagicMock()
                mock_stock_result = MagicMock()
                mock_stock_result.raw = "Stock analysis completed"
                mock_stock_crew.crew().kickoff.return_value = mock_stock_result
                mock_stock_crew_class.return_value = mock_stock_crew

                # Mock integration system failure
                finwiz_flow.integration_manager.store_crew_output.side_effect = Exception("Storage failed")

                # Execute should handle integration failure gracefully
                finwiz_flow.check_stock()

                # Verify crew executed successfully despite integration failure
                assert finwiz_flow.inputs["stock_analysis_success"] is True
                assert "stock_analysis_result" in finwiz_flow.inputs

    def test_should_handle_error_handler_failures(self, finwiz_flow):
        """Test handling when error handler itself fails."""
        with patch("finwiz.main.is_feature_enabled", return_value=True):
            with patch("finwiz.main.CryptoCrew") as mock_crypto_crew_class:
                # Mock crew failure
                mock_crypto_crew = MagicMock()
                mock_crypto_crew.crew().kickoff.side_effect = Exception("Crypto failed")
                mock_crypto_crew_class.return_value = mock_crypto_crew

                # Mock error handler failure
                finwiz_flow.error_handler.handle_crew_failure.side_effect = Exception("Error handler failed")

                # Execute should handle error handler failure gracefully
                finwiz_flow.check_crypto()

                # Verify basic error handling still works
                assert finwiz_flow.inputs["crypto_analysis_success"] is False
                assert "crypto_analysis_error" in finwiz_flow.inputs

    def test_should_handle_invalid_crew_results(self, finwiz_flow):
        """Test handling of invalid crew results."""
        with patch("finwiz.main.is_feature_enabled", return_value=True):
            with patch("finwiz.main.EtfCrew") as mock_etf_crew_class:
                # Mock crew that returns invalid result
                mock_etf_crew = MagicMock()
                mock_invalid_result = None  # Invalid result
                mock_etf_crew.crew().kickoff.return_value = mock_invalid_result
                mock_etf_crew_class.return_value = mock_etf_crew

                # Execute should handle invalid result gracefully
                finwiz_flow.check_etf()

                # Verify handling of invalid result
                assert finwiz_flow.inputs["etf_analysis_success"] is True  # Crew executed
                assert "etf_analysis_result" in finwiz_flow.inputs

    def test_should_provide_detailed_error_information(self, finwiz_flow):
        """Test that detailed error information is provided for debugging."""
        with patch("finwiz.main.is_feature_enabled", return_value=True):
            with patch("finwiz.main.StockCrew") as mock_stock_crew_class:
                # Mock specific error
                error_message = "Yahoo Finance API rate limit exceeded"
                mock_stock_crew = MagicMock()
                mock_stock_crew.crew().kickoff.side_effect = Exception(error_message)
                mock_stock_crew_class.return_value = mock_stock_crew

                # Execute should capture detailed error information
                finwiz_flow.check_stock()

                # Verify detailed error information is available
                assert finwiz_flow.inputs["stock_analysis_success"] is False
                assert "stock_analysis_error" in finwiz_flow.inputs
                assert error_message in str(finwiz_flow.inputs["stock_analysis_error"])

    def test_should_handle_multiple_consecutive_failures(self, finwiz_flow):
        """Test handling of multiple consecutive failures."""
        with patch("finwiz.main.is_feature_enabled", return_value=True):
            with patch("finwiz.main.CryptoCrew") as mock_crypto_crew_class:
                # Mock crew that always fails
                mock_crypto_crew = MagicMock()
                mock_crypto_crew.crew().kickoff.side_effect = Exception("Persistent failure")
                mock_crypto_crew_class.return_value = mock_crypto_crew

                # Mock error handler with no fallback
                mock_fallback_response = MagicMock()
                mock_fallback_response.success = False
                mock_fallback_response.message = "No fallback available"
                finwiz_flow.error_handler.handle_crew_failure.return_value = mock_fallback_response

                # Execute multiple times
                for i in range(3):
                    finwiz_flow.check_crypto()

                    # Verify each failure is handled
                    assert finwiz_flow.inputs["crypto_analysis_success"] is False
                    assert "crypto_analysis_error" in finwiz_flow.inputs

    def test_should_maintain_system_stability_during_errors(self, finwiz_flow):
        """Test that system maintains stability during various error conditions."""
        error_scenarios = [
            Exception("Generic error"),
            ConnectionError("Network error"),
            TimeoutError("Timeout error"),
            ValueError("Validation error"),
            MemoryError("Memory error"),
        ]

        with patch("finwiz.main.is_feature_enabled", return_value=True):
            for i, error in enumerate(error_scenarios):
                with patch("finwiz.main.StockCrew") as mock_stock_crew_class:
                    # Mock crew with specific error
                    mock_stock_crew = MagicMock()
                    mock_stock_crew.crew().kickoff.side_effect = error
                    mock_stock_crew_class.return_value = mock_stock_crew

                    # Execute should handle each error type gracefully
                    finwiz_flow.check_stock()

                    # Verify system remains stable
                    assert finwiz_flow.inputs["stock_analysis_success"] is False
                    assert "stock_analysis_error" in finwiz_flow.inputs

                    # System should still be functional for next iteration
                    assert finwiz_flow.integration_manager is not None
                    assert finwiz_flow.error_handler is not None

    def test_should_handle_data_integration_validation_failures(self, finwiz_flow):
        """Test handling of data integration validation failures."""
        # Mock data accessor failure
        finwiz_flow.data_accessor.check_data_availability.side_effect = Exception("Data validation failed")

        # Execute validation should handle failure gracefully
        finwiz_flow.validate_data_integration()

        # System should continue to function despite validation failure
        assert finwiz_flow.integration_manager is not None
        assert finwiz_flow.data_accessor is not None
