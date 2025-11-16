"""
Unit tests for Core Analysis Flow Integration.

Tests the main flow orchestration for core analysis crews including
stock, ETF, and crypto analysis integration.
"""

from datetime import datetime

import pytest

from finwiz.flows.flow_orchestrator import FinwizFlow


class TestCoreAnalysisFlow:
    """Test cases for Core Analysis Flow Integration."""

    @pytest.fixture
    def mock_flow_inputs(self):
        """Create mock inputs for flow testing."""
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
    def mock_crew_results(self, mocker):
        """Create mock crew results."""
        return {
            "stock": mocker.MagicMock(raw="Stock analysis: BUY recommendation for AAPL"),
            "etf": mocker.MagicMock(raw="ETF analysis: BUY recommendation for SPY"),
            "crypto": mocker.MagicMock(raw="Crypto analysis: HOLD recommendation for BTC"),
        }

    @pytest.fixture
    def finwiz_flow(self):
        """Create a FinwizFlow instance for testing."""
        return FinwizFlow()

    def test_should_initialize_flow_with_proper_components(self, finwiz_flow):
        """Test that FinwizFlow initializes with all required components."""
        assert finwiz_flow is not None
        assert hasattr(finwiz_flow, "integration_manager")
        assert hasattr(finwiz_flow, "data_accessor")
        assert hasattr(finwiz_flow, "error_handler")
        assert hasattr(finwiz_flow, "state")

    def test_should_have_proper_flow_inputs(self, finwiz_flow):
        """Test that flow inputs are properly initialized."""
        state = finwiz_flow.state

        required_attrs = [
            "current_date",
            "full_date",
            "timestamp",
            "report_language",
            "has_existing_session",
            "session_id",
            "analysis_count",
        ]

        for attr in required_attrs:
            assert hasattr(state, attr), f"Missing required attribute: {attr}"

    def test_should_execute_crypto_crew_when_enabled(self, mocker, finwiz_flow, mock_crew_results):
        """Test that crypto discovery uses Python analysis."""
        # Mock Python-based crypto analyzer
        mock_crypto_results = {
            "analysis_summary": "Crypto analysis: HOLD recommendation for BTC",
            "opportunities": ["BTC", "ETH"],
            "performance_metrics": {"total_analyzed": 2, "a_plus_count": 1},
        }
        mock_analyze_crypto = mocker.patch("finwiz.scoring.crypto_analyzer.analyze_crypto_opportunities")
        mock_analyze_crypto.return_value = mock_crypto_results

        # Execute crypto analysis
        result = finwiz_flow.check_crypto()

        # Verify Python analyzer was called
        mock_analyze_crypto.assert_called_once()

        # Verify results were stored in state and returned
        assert finwiz_flow.state.crypto_analysis_success is True
        assert finwiz_flow.state.crypto_result == "Crypto analysis: HOLD recommendation for BTC"
        assert result["crypto_analysis_complete"] is True

    def test_should_skip_crypto_crew_when_disabled(self, mocker, finwiz_flow):
        """Test that crypto analysis handles errors gracefully."""
        # Mock Python analyzer to raise an exception
        mock_analyze_crypto = mocker.patch("finwiz.scoring.crypto_analyzer.analyze_crypto_opportunities")
        mock_analyze_crypto.side_effect = Exception("Crypto API failed")

        # Execute crypto analysis (should not raise exception)
        result = finwiz_flow.check_crypto()

        # Verify error was handled gracefully
        assert result["crypto_analysis_complete"] is True
        assert finwiz_flow.state.crypto_analysis_success is False

    def test_should_execute_stock_crew_when_enabled(self, mocker, finwiz_flow, mock_crew_results):
        """Test that stock discovery uses Python analysis."""
        # Mock Python-based stock analyzer
        mock_stock_results = {
            "analysis_summary": "Stock analysis: BUY recommendation for AAPL",
            "opportunities": ["AAPL", "MSFT"],
            "performance_metrics": {"total_analyzed": 2, "a_plus_count": 2},
        }
        mock_analyze_stock = mocker.patch("finwiz.scoring.stock_analyzer.analyze_stock_opportunities")
        mock_analyze_stock.return_value = mock_stock_results

        # Execute stock analysis
        result = finwiz_flow.check_stock()

        # Verify Python analyzer was called
        mock_analyze_stock.assert_called_once()

        # Verify results were stored in state and returned
        assert finwiz_flow.state.stock_analysis_success is True
        assert finwiz_flow.state.stock_result == "Stock analysis: BUY recommendation for AAPL"
        assert result["stock_analysis_complete"] is True

    def test_should_execute_etf_crew_when_enabled(self, mocker, finwiz_flow, mock_crew_results):
        """Test that ETF discovery uses Python analysis."""
        # Mock Python-based ETF analyzer
        mock_etf_results = {
            "analysis_summary": "ETF analysis: BUY recommendation for SPY",
            "opportunities": ["SPY", "VWCE"],
            "performance_metrics": {"total_analyzed": 2, "a_plus_count": 1},
        }
        mock_analyze_etf = mocker.patch("finwiz.scoring.etf_analyzer.analyze_etf_opportunities")
        mock_analyze_etf.return_value = mock_etf_results

        # Execute ETF analysis
        result = finwiz_flow.check_etf()

        # Verify Python analyzer was called
        mock_analyze_etf.assert_called_once()

        # Verify results were stored in state and returned
        assert finwiz_flow.state.etf_analysis_success is True
        assert finwiz_flow.state.etf_result == "ETF analysis: BUY recommendation for SPY"
        assert result["etf_analysis_complete"] is True

    def test_should_handle_crypto_crew_failure_gracefully(self, mocker, finwiz_flow):
        """Test that crypto analysis failures are handled gracefully."""
        # Mock Python analyzer failure
        mock_analyze_crypto = mocker.patch("finwiz.scoring.crypto_analyzer.analyze_crypto_opportunities")
        mock_analyze_crypto.side_effect = Exception("Crypto API failed")

        # Execute crypto analysis (should not raise exception)
        result = finwiz_flow.check_crypto()

        # Verify error handling
        assert result["crypto_analysis_complete"] is True
        assert finwiz_flow.state.crypto_analysis_success is False
        assert "Crypto API failed" in finwiz_flow.state.crypto_result

    def test_should_use_fallback_data_when_available(self, mocker, finwiz_flow):
        """Test that partial crypto data is handled gracefully."""
        # Mock Python analyzer returning partial results
        mock_crypto_results = {
            "analysis_summary": "Partial crypto analysis",
            "opportunities": ["BTC"],  # Only one opportunity
            "performance_metrics": {"total_analyzed": 1, "a_plus_count": 0},
        }
        mock_analyze_crypto = mocker.patch("finwiz.scoring.crypto_analyzer.analyze_crypto_opportunities")
        mock_analyze_crypto.return_value = mock_crypto_results

        # Execute crypto analysis
        result = finwiz_flow.check_crypto()

        # Verify partial data is accepted
        assert result["crypto_analysis_complete"] is True
        assert finwiz_flow.state.crypto_analysis_success is True
        assert finwiz_flow.state.crypto_result == "Partial crypto analysis"

    async def test_should_validate_data_integration_system(self, mocker, finwiz_flow):
        """Test that data integration system is validated before crew execution."""
        from datetime import datetime

        from finwiz.schemas.integration import DataAvailabilityReport, DataAvailabilityStatus

        # Mock data accessor method with proper Pydantic model
        mock_availability_report = DataAvailabilityReport(
            stock_available=True,
            etf_available=True,
            crypto_available=False,
            discovery_available=False,
            portfolio_available=True,
            missing_data=["crypto"],
            stale_data=[],
            integration_errors=[],
            overall_status=DataAvailabilityStatus.PARTIAL,
            report_timestamp=datetime.now(),
            data_freshness_summary={},
            recommendations=[],
        )
        mock_check = mocker.patch.object(
            finwiz_flow.data_accessor, "check_data_availability", return_value=mock_availability_report
        )

        # Execute validation (async)
        await finwiz_flow.validate_data_integration()

        # Verify validation was performed
        mock_check.assert_called_once()

    def test_should_store_all_crew_results_in_integration_system(
        self,
        mocker,
        finwiz_flow,
        mock_crew_results,
    ):
        """Test that all Python analysis results are tracked in availability system."""
        # Mock Python analyzers
        mock_crypto_results = {
            "analysis_summary": "Crypto analysis completed",
            "opportunities": ["BTC", "ETH"],
            "performance_metrics": {"total_analyzed": 2},
        }
        mock_stock_results = {
            "analysis_summary": "Stock analysis completed",
            "opportunities": ["AAPL", "MSFT"],
            "performance_metrics": {"total_analyzed": 2},
        }
        mock_etf_results = {
            "analysis_summary": "ETF analysis completed",
            "opportunities": ["SPY", "VWCE"],
            "performance_metrics": {"total_analyzed": 2},
        }

        mocker.patch("finwiz.scoring.crypto_analyzer.analyze_crypto_opportunities", return_value=mock_crypto_results)
        mocker.patch("finwiz.scoring.stock_analyzer.analyze_stock_opportunities", return_value=mock_stock_results)
        mocker.patch("finwiz.scoring.etf_analyzer.analyze_etf_opportunities", return_value=mock_etf_results)

        # Execute all analyses
        finwiz_flow.check_crypto()
        finwiz_flow.check_stock()
        finwiz_flow.check_etf()

        # Verify all results were stored in state
        assert finwiz_flow.state.crypto_analysis_success is True
        assert finwiz_flow.state.stock_analysis_success is True
        assert finwiz_flow.state.etf_analysis_success is True
        assert finwiz_flow.state.crypto_result == "Crypto analysis completed"
        assert finwiz_flow.state.stock_result == "Stock analysis completed"
        assert finwiz_flow.state.etf_result == "ETF analysis completed"

    def test_should_handle_session_information_properly(self, mocker, finwiz_flow):
        """Test that flow handles session information properly."""
        import os

        # Test without existing session
        assert finwiz_flow.state.has_existing_session is False
        assert finwiz_flow.state.session_id == ""
        assert finwiz_flow.state.analysis_count == 0

        # Test with existing session (via environment variables - must patch BEFORE creating flow)
        # Use mocker.patch.dict directly (without context manager)
        patch = mocker.patch.dict(
            os.environ,
            {"FINWIZ_HAS_EXISTING_SESSION": "true", "FINWIZ_SESSION_ID": "test-session-123", "FINWIZ_ANALYSIS_COUNT": "5"},
            clear=False,
        )
        patch.start()
        try:
            flow_with_session = FinwizFlow()
            assert flow_with_session.state.has_existing_session is True
            assert flow_with_session.state.session_id == "test-session-123"
            assert flow_with_session.state.analysis_count == 5
        finally:
            patch.stop()

    def test_should_support_multilingual_configuration(self, finwiz_flow):
        """Test that flow supports multilingual configuration."""
        # Default should be French
        assert finwiz_flow.state.report_language == "fr"

        # Test with different language
        finwiz_flow.state.report_language = "en"
        assert finwiz_flow.state.report_language == "en"

    def test_should_handle_all_crews_disabled(self, mocker, finwiz_flow):
        """Test that flow handles scenario where all Python analyzers fail."""
        # Mock all analyzers to raise exceptions
        mocker.patch(
            "finwiz.scoring.crypto_analyzer.analyze_crypto_opportunities", side_effect=Exception("Crypto failed")
        )
        mocker.patch("finwiz.scoring.stock_analyzer.analyze_stock_opportunities", side_effect=Exception("Stock failed"))
        mocker.patch("finwiz.scoring.etf_analyzer.analyze_etf_opportunities", side_effect=Exception("ETF failed"))

        # Execute all analyses
        finwiz_flow.check_crypto()
        finwiz_flow.check_stock()
        finwiz_flow.check_etf()

        # Verify all analyses failed gracefully
        assert finwiz_flow.state.crypto_analysis_success is False
        assert finwiz_flow.state.stock_analysis_success is False
        assert finwiz_flow.state.etf_analysis_success is False

    def test_should_maintain_proper_execution_timing(self, finwiz_flow):
        """Test that flow maintains proper execution timing information."""
        # Check that timestamp is properly formatted
        timestamp = finwiz_flow.state.timestamp
        assert isinstance(timestamp, str)
        assert len(timestamp) > 0

        # Verify date components
        assert isinstance(finwiz_flow.state.current_day, int)
        assert isinstance(finwiz_flow.state.current_month, int)
        assert isinstance(finwiz_flow.state.current_year, int)
        assert isinstance(finwiz_flow.state.current_date, str)
        assert isinstance(finwiz_flow.state.full_date, str)

    def test_should_handle_crew_result_formats(self, mocker, finwiz_flow):
        """Test that flow handles different Python analyzer result formats properly."""
        # Test with complete result structure
        mock_crypto_results_complete = {
            "analysis_summary": "Complete crypto analysis",
            "opportunities": ["BTC", "ETH"],
            "performance_metrics": {"total_analyzed": 2, "a_plus_count": 1},
        }
        mock_analyze_crypto = mocker.patch("finwiz.scoring.crypto_analyzer.analyze_crypto_opportunities")
        mock_analyze_crypto.return_value = mock_crypto_results_complete

        finwiz_flow.check_crypto()
        assert finwiz_flow.state.crypto_result == "Complete crypto analysis"

        # Test with minimal result structure
        mock_crypto_results_minimal = {
            "analysis_summary": "Minimal crypto analysis",
            "opportunities": [],
            "performance_metrics": {},
        }
        mock_analyze_crypto.return_value = mock_crypto_results_minimal

        finwiz_flow.check_crypto()
        assert finwiz_flow.state.crypto_result == "Minimal crypto analysis"
