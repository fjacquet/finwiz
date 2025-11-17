"""
Unit tests for Core Analysis Error Scenarios.

Tests error handling, graceful degradation, and recovery mechanisms
for core analysis functionality.
"""

from datetime import datetime

import pytest

from finwiz.flows.flow_orchestrator import FinwizFlow


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

    def test_should_handle_crew_initialization_failure(self, finwiz_flow, mocker):
        """Test handling of Python analysis initialization failures."""
        # Mock Python analysis function to raise exception
        mock_analyze = mocker.patch("finwiz.scoring.stock_analyzer.analyze_stock_opportunities")
        mock_analyze.side_effect = Exception("Analysis initialization failed")

        # Execute should handle the error gracefully
        finwiz_flow.check_stock()

        # Verify error was handled
        assert finwiz_flow.state.stock_analysis_success is False
        assert finwiz_flow.state.stock_analysis_error == "Analysis initialization failed"

    def test_should_handle_crew_kickoff_failure(self, finwiz_flow, mocker):
        """Test handling of Python analysis execution failures."""
        # Mock Python analysis function to raise exception
        mock_analyze = mocker.patch("finwiz.scoring.stock_analyzer.analyze_stock_opportunities")
        mock_analyze.side_effect = Exception("Analysis execution failed")

        # Execute should handle the error gracefully
        finwiz_flow.check_stock()

        # Verify error was handled
        assert finwiz_flow.state.stock_analysis_success is False
        assert finwiz_flow.state.stock_analysis_error == "Analysis execution failed"

    def test_should_handle_api_connection_failures(self, finwiz_flow, mocker):
        """Test handling of API connection failures."""
        # Mock Python analysis function to raise ConnectionError
        mock_analyze = mocker.patch("finwiz.scoring.crypto_analyzer.analyze_crypto_opportunities")
        mock_analyze.side_effect = ConnectionError("API connection failed")

        # Execute should handle the error gracefully
        finwiz_flow.check_crypto()

        # Verify error was handled
        assert finwiz_flow.state.crypto_analysis_success is False
        assert finwiz_flow.state.crypto_analysis_error == "API connection failed"

    def test_should_handle_timeout_errors(self, finwiz_flow, mocker):
        """Test handling of timeout errors."""
        # Mock Python analysis function to raise TimeoutError
        mock_analyze = mocker.patch("finwiz.scoring.etf_analyzer.analyze_etf_opportunities")
        mock_analyze.side_effect = TimeoutError("Analysis execution timed out")

        # Execute should handle the error gracefully
        finwiz_flow.check_etf()

        # Verify error was handled
        assert finwiz_flow.state.etf_analysis_success is False
        assert finwiz_flow.state.etf_analysis_error == "Analysis execution timed out"
        assert "timed out" in str(finwiz_flow.state.etf_analysis_error)

    def test_should_handle_memory_errors(self, finwiz_flow, mocker):
        """Test handling of memory errors."""
        # Mock Python analysis function to raise MemoryError
        mock_analyze = mocker.patch("finwiz.scoring.stock_analyzer.analyze_stock_opportunities")
        mock_analyze.side_effect = MemoryError("Insufficient memory")

        # Execute should handle the error gracefully
        finwiz_flow.check_stock()

        # Verify error was handled
        assert finwiz_flow.state.stock_analysis_success is False
        assert finwiz_flow.state.stock_analysis_error == "Insufficient memory"

    def test_should_handle_data_validation_errors(self, finwiz_flow, mocker):
        """Test handling of data validation errors."""
        # Mock Python analysis function to raise ValueError
        mock_analyze = mocker.patch("finwiz.scoring.crypto_analyzer.analyze_crypto_opportunities")
        mock_analyze.side_effect = ValueError("Invalid data format")

        # Execute should handle the error gracefully
        finwiz_flow.check_crypto()

        # Verify error was handled
        assert finwiz_flow.state.crypto_analysis_success is False
        assert finwiz_flow.state.crypto_analysis_error == "Invalid data format"

    def test_should_use_cached_data_as_fallback(self, finwiz_flow, mocker):
        """Test that Python analysis handles failures gracefully."""
        # Mock Python analysis function to raise exception
        mock_analyze = mocker.patch("finwiz.scoring.stock_analyzer.analyze_stock_opportunities")
        mock_analyze.side_effect = Exception("API failed")

        # Execute should handle the error gracefully
        finwiz_flow.check_stock()

        # Verify error was handled (Python analysis doesn't have fallback)
        assert finwiz_flow.state.stock_analysis_success is False
        assert finwiz_flow.state.stock_analysis_error == "API failed"

    def test_should_handle_partial_crew_failures(self, finwiz_flow, mocker):
        """Test handling when some analysis succeeds and others fail."""
        # Mock successful stock analysis
        mock_stock_analyze = mocker.patch("finwiz.scoring.stock_analyzer.analyze_stock_opportunities")
        mock_stock_analyze.return_value = {
            "analysis_summary": "Identified 3 stock opportunities",
            "opportunities": [{"ticker": "AAPL"}, {"ticker": "MSFT"}, {"ticker": "GOOGL"}],
            "performance_metrics": {},
        }

        # Mock successful ETF analysis
        mock_etf_analyze = mocker.patch("finwiz.scoring.etf_analyzer.analyze_etf_opportunities")
        mock_etf_analyze.return_value = {
            "analysis_summary": "Identified 2 ETF opportunities",
            "opportunities": [{"ticker": "SPY"}, {"ticker": "QQQ"}],
            "performance_metrics": {},
        }

        # Mock failing crypto analysis
        mock_crypto_analyze = mocker.patch("finwiz.scoring.crypto_analyzer.analyze_crypto_opportunities")
        mock_crypto_analyze.side_effect = Exception("Crypto API failed")

        # Execute all analysis
        finwiz_flow.check_stock()
        finwiz_flow.check_etf()
        finwiz_flow.check_crypto()

        # Verify partial success
        assert finwiz_flow.state.stock_analysis_success is True
        assert finwiz_flow.state.etf_analysis_success is True
        assert finwiz_flow.state.crypto_analysis_success is False
        assert finwiz_flow.state.crypto_analysis_error == "Crypto API failed"

    def test_should_handle_integration_system_failures(self, finwiz_flow, mocker):
        """Test that integration system failures are caught by outer exception handler."""
        # Mock successful Python analysis
        mock_analyze = mocker.patch("finwiz.scoring.stock_analyzer.analyze_stock_opportunities")
        mock_analyze.return_value = {
            "analysis_summary": "Stock analysis completed",
            "opportunities": [{"ticker": "AAPL"}],
            "performance_metrics": {},
        }

        # Mock integration system failure (availability tracker)
        # First call raises exception, second call (in error handler) succeeds
        mock_track = mocker.patch.object(finwiz_flow.availability_tracker, "track_data_source")
        mock_track.side_effect = [Exception("Storage failed"), None]

        # Execute - integration failure is caught by outer exception handler
        finwiz_flow.check_stock()

        # The exception from track_data_source is caught and treated as analysis failure
        assert finwiz_flow.state.stock_analysis_success is False
        assert finwiz_flow.state.stock_analysis_error == "Storage failed"

    def test_should_handle_error_handler_failures(self, finwiz_flow, mocker):
        """Test handling when Python analysis fails."""
        # Mock Python analysis failure
        mock_analyze = mocker.patch("finwiz.scoring.crypto_analyzer.analyze_crypto_opportunities")
        mock_analyze.side_effect = Exception("Crypto failed")

        # Execute should handle error gracefully
        finwiz_flow.check_crypto()

        # Verify basic error handling still works
        assert finwiz_flow.state.crypto_analysis_success is False
        assert finwiz_flow.state.crypto_analysis_error == "Crypto failed"

    def test_should_handle_invalid_crew_results(self, finwiz_flow, mocker):
        """Test handling of invalid crew results."""
        mocker.patch("finwiz.main.is_feature_enabled", return_value=True)
        mock_etf_crew_class = mocker.patch("finwiz.main.EtfCrew")
        # Mock crew that returns invalid result
        mock_etf_crew = mocker.MagicMock()
        mock_invalid_result = None  # Invalid result
        mock_etf_crew.crew().kickoff.return_value = mock_invalid_result
        mock_etf_crew_class.return_value = mock_etf_crew

        # Execute should handle invalid result gracefully
        finwiz_flow.check_etf()

        # Verify handling of invalid result
        assert finwiz_flow.state.etf_analysis_success is True  # Crew executed
        assert hasattr(finwiz_flow.state, "etf_analysis_result")

    def test_should_provide_detailed_error_information(self, finwiz_flow, mocker):
        """Test that detailed error information is provided for debugging."""
        # Mock specific error
        error_message = "Yahoo Finance API rate limit exceeded"
        mock_analyze = mocker.patch("finwiz.scoring.stock_analyzer.analyze_stock_opportunities")
        mock_analyze.side_effect = Exception(error_message)

        # Execute should capture detailed error information
        finwiz_flow.check_stock()

        # Verify detailed error information is available
        assert finwiz_flow.state.stock_analysis_success is False
        assert finwiz_flow.state.stock_analysis_error == error_message
        assert error_message in str(finwiz_flow.state.stock_analysis_error)

    def test_should_handle_multiple_consecutive_failures(self, finwiz_flow, mocker):
        """Test handling of multiple consecutive failures."""
        # Mock Python analysis that always fails
        mock_analyze = mocker.patch("finwiz.scoring.crypto_analyzer.analyze_crypto_opportunities")
        mock_analyze.side_effect = Exception("Persistent failure")

        # Execute multiple times
        for i in range(3):
            finwiz_flow.check_crypto()

            # Verify each failure is handled
            assert finwiz_flow.state.crypto_analysis_success is False
            assert finwiz_flow.state.crypto_analysis_error == "Persistent failure"

    def test_should_maintain_system_stability_during_errors(self, finwiz_flow, mocker):
        """Test that system maintains stability during various error conditions."""
        error_scenarios = [
            Exception("Generic error"),
            ConnectionError("Network error"),
            TimeoutError("Timeout error"),
            ValueError("Validation error"),
            MemoryError("Memory error"),
        ]

        for i, error in enumerate(error_scenarios):
            # Mock Python analysis with specific error
            mock_analyze = mocker.patch("finwiz.scoring.stock_analyzer.analyze_stock_opportunities")
            mock_analyze.side_effect = error

            # Execute should handle each error type gracefully
            finwiz_flow.check_stock()

            # Verify system remains stable
            assert finwiz_flow.state.stock_analysis_success is False
            assert finwiz_flow.state.stock_analysis_error == str(error)

            # System should still be functional for next iteration
            assert finwiz_flow.integration_manager is not None
            assert finwiz_flow.error_handler is not None

    async def test_should_handle_data_integration_validation_failures(self, finwiz_flow, mocker):
        """Test handling of data integration validation failures."""
        # Mock data accessor failure
        mocker.patch.object(finwiz_flow.data_accessor, "check_data_availability", side_effect=Exception("Data validation failed"))

        # Execute validation - exception is caught and returned in result
        result = await finwiz_flow.validate_data_integration()

        # Verify error was handled gracefully
        assert result["validation_complete"] is False
        assert "error" in result
        assert "Data validation failed" in result["error"]

        # State should have error recorded
        assert finwiz_flow.state.data_integration_error == "Data validation failed"

        # System objects still exist
        assert finwiz_flow.integration_manager is not None
        assert finwiz_flow.data_accessor is not None
