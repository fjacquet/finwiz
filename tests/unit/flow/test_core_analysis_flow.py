"""
Unit tests for Core Analysis Flow Integration.

Tests the main flow orchestration for core analysis crews including
stock, ETF, and crypto analysis integration.
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from finwiz.main import FinwizFlow


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
    def mock_crew_results(self):
        """Create mock crew results."""
        return {
            "stock": MagicMock(raw="Stock analysis: BUY recommendation for AAPL"),
            "etf": MagicMock(raw="ETF analysis: BUY recommendation for SPY"),
            "crypto": MagicMock(raw="Crypto analysis: HOLD recommendation for BTC"),
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
        assert hasattr(finwiz_flow, "inputs")

    def test_should_have_proper_flow_inputs(self, finwiz_flow):
        """Test that flow inputs are properly initialized."""
        inputs = finwiz_flow.inputs

        required_keys = [
            "current_date",
            "full_date",
            "timestamp",
            "report_language",
            "has_existing_session",
            "session_id",
            "analysis_count",
        ]

        for key in required_keys:
            assert key in inputs, f"Missing required input: {key}"

    @patch("finwiz.main.is_feature_enabled")
    @patch("finwiz.main.CryptoCrew")
    def test_should_execute_crypto_crew_when_enabled(
        self, mock_crypto_crew_class, mock_feature_enabled, finwiz_flow, mock_crew_results
    ):
        """Test that crypto crew executes when feature is enabled."""
        # Mock feature flag
        mock_feature_enabled.return_value = True

        # Mock crew instance and result
        mock_crypto_crew = MagicMock()
        mock_crypto_crew.crew().kickoff.return_value = mock_crew_results["crypto"]
        mock_crypto_crew_class.return_value = mock_crypto_crew

        # Execute crypto analysis
        finwiz_flow.check_crypto()

        # Verify crew was created and executed
        mock_crypto_crew_class.assert_called_once()
        mock_crypto_crew.crew().kickoff.assert_called_once_with(inputs=finwiz_flow.inputs)

        # Verify results were stored
        assert "crypto_analysis_result" in finwiz_flow.inputs
        assert finwiz_flow.inputs["crypto_analysis_success"] is True
        assert finwiz_flow.inputs["core_analysis_completed"] is True

    @patch("finwiz.main.is_feature_enabled")
    def test_should_skip_crypto_crew_when_disabled(self, mock_feature_enabled, finwiz_flow):
        """Test that crypto crew is skipped when feature is disabled."""
        # Mock feature flag
        mock_feature_enabled.return_value = False

        # Execute crypto analysis
        finwiz_flow.check_crypto()

        # Verify crew was skipped
        assert finwiz_flow.inputs.get("crypto_analysis_disabled") is True
        assert "crypto_analysis_result" not in finwiz_flow.inputs

    @patch("finwiz.main.is_feature_enabled")
    @patch("finwiz.main.StockCrew")
    def test_should_execute_stock_crew_when_enabled(
        self, mock_stock_crew_class, mock_feature_enabled, finwiz_flow, mock_crew_results
    ):
        """Test that stock crew executes when feature is enabled."""
        # Mock feature flag
        mock_feature_enabled.return_value = True

        # Mock crew instance and result
        mock_stock_crew = MagicMock()
        mock_stock_crew.crew().kickoff.return_value = mock_crew_results["stock"]
        mock_stock_crew_class.return_value = mock_stock_crew

        # Execute stock analysis
        finwiz_flow.check_stock()

        # Verify crew was created and executed
        mock_stock_crew_class.assert_called_once()
        mock_stock_crew.crew().kickoff.assert_called_once_with(inputs=finwiz_flow.inputs)

        # Verify results were stored
        assert "stock_analysis_result" in finwiz_flow.inputs
        assert finwiz_flow.inputs["stock_analysis_success"] is True
        assert finwiz_flow.inputs["core_analysis_completed"] is True

    @patch("finwiz.main.is_feature_enabled")
    @patch("finwiz.main.EtfCrew")
    def test_should_execute_etf_crew_when_enabled(self, mock_etf_crew_class, mock_feature_enabled, finwiz_flow, mock_crew_results):
        """Test that ETF crew executes when feature is enabled."""
        # Mock feature flag
        mock_feature_enabled.return_value = True

        # Mock crew instance and result
        mock_etf_crew = MagicMock()
        mock_etf_crew.crew().kickoff.return_value = mock_crew_results["etf"]
        mock_etf_crew_class.return_value = mock_etf_crew

        # Execute ETF analysis
        finwiz_flow.check_etf()

        # Verify crew was created and executed
        mock_etf_crew_class.assert_called_once()
        mock_etf_crew.crew().kickoff.assert_called_once_with(inputs=finwiz_flow.inputs)

        # Verify results were stored
        assert "etf_analysis_result" in finwiz_flow.inputs
        assert finwiz_flow.inputs["etf_analysis_success"] is True
        assert finwiz_flow.inputs["core_analysis_completed"] is True

    @patch("finwiz.main.is_feature_enabled")
    @patch("finwiz.main.CryptoCrew")
    def test_should_handle_crypto_crew_failure_gracefully(self, mock_crypto_crew_class, mock_feature_enabled, finwiz_flow):
        """Test that crypto crew failures are handled gracefully."""
        # Mock feature flag
        mock_feature_enabled.return_value = True

        # Mock crew failure
        mock_crypto_crew = MagicMock()
        mock_crypto_crew.crew().kickoff.side_effect = Exception("Crypto API failed")
        mock_crypto_crew_class.return_value = mock_crypto_crew

        # Mock error handler
        mock_fallback_response = MagicMock()
        mock_fallback_response.success = False
        mock_fallback_response.message = "Crypto analysis failed"
        mock_fallback_response.fallback_strategy = "skip"
        mock_fallback_response.degraded_functionality = ["no_crypto_data"]
        finwiz_flow.error_handler.handle_crew_failure.return_value = mock_fallback_response

        # Execute crypto analysis (should not raise exception)
        finwiz_flow.check_crypto()

        # Verify error handling
        assert finwiz_flow.inputs["crypto_analysis_success"] is False
        assert finwiz_flow.inputs["crypto_analysis_fallback"] is True
        assert "crypto_analysis_error" in finwiz_flow.inputs
        assert finwiz_flow.inputs["crypto_analysis_result"] is None

    @patch("finwiz.main.is_feature_enabled")
    @patch("finwiz.main.CryptoCrew")
    def test_should_use_fallback_data_when_available(self, mock_crypto_crew_class, mock_feature_enabled, finwiz_flow):
        """Test that fallback data is used when crew fails but fallback succeeds."""
        # Mock feature flag
        mock_feature_enabled.return_value = True

        # Mock crew failure
        mock_crypto_crew = MagicMock()
        mock_crypto_crew.crew().kickoff.side_effect = Exception("Crypto API failed")
        mock_crypto_crew_class.return_value = mock_crypto_crew

        # Mock successful fallback
        fallback_data = {"analysis": "Cached crypto analysis", "recommendation": "HOLD"}
        mock_fallback_response = MagicMock()
        mock_fallback_response.success = True
        mock_fallback_response.data = fallback_data
        mock_fallback_response.message = "Using cached data"
        mock_fallback_response.fallback_strategy = "cached_data"
        mock_fallback_response.degraded_functionality = ["stale_data"]
        finwiz_flow.error_handler.handle_crew_failure.return_value = mock_fallback_response

        # Execute crypto analysis
        finwiz_flow.check_crypto()

        # Verify fallback data is used
        assert finwiz_flow.inputs["crypto_analysis_success"] is False
        assert finwiz_flow.inputs["crypto_analysis_fallback"] is True
        assert finwiz_flow.inputs["crypto_fallback_strategy"] == "cached_data"
        assert "crypto_analysis_result" in finwiz_flow.inputs

    def test_should_validate_data_integration_system(self, finwiz_flow):
        """Test that data integration system is validated before crew execution."""
        # Mock data accessor
        mock_availability_report = {
            "data_sources_available": ["yahoo_finance", "alpha_vantage"],
            "data_freshness_status": "acceptable",
            "integration_health": "healthy",
        }
        finwiz_flow.data_accessor.check_data_availability.return_value = mock_availability_report

        # Execute validation
        finwiz_flow.validate_data_integration()

        # Verify validation was performed
        finwiz_flow.data_accessor.check_data_availability.assert_called_once()

    @patch("finwiz.main.is_feature_enabled")
    @patch("finwiz.main.CryptoCrew")
    @patch("finwiz.main.StockCrew")
    @patch("finwiz.main.EtfCrew")
    def test_should_store_all_crew_results_in_integration_system(
        self,
        mock_etf_crew_class,
        mock_stock_crew_class,
        mock_crypto_crew_class,
        mock_feature_enabled,
        finwiz_flow,
        mock_crew_results,
    ):
        """Test that all crew results are stored in the integration system."""
        # Mock feature flags
        mock_feature_enabled.return_value = True

        # Mock crew instances
        mock_crypto_crew = MagicMock()
        mock_crypto_crew.crew().kickoff.return_value = mock_crew_results["crypto"]
        mock_crypto_crew_class.return_value = mock_crypto_crew

        mock_stock_crew = MagicMock()
        mock_stock_crew.crew().kickoff.return_value = mock_crew_results["stock"]
        mock_stock_crew_class.return_value = mock_stock_crew

        mock_etf_crew = MagicMock()
        mock_etf_crew.crew().kickoff.return_value = mock_crew_results["etf"]
        mock_etf_crew_class.return_value = mock_etf_crew

        # Execute all crews
        finwiz_flow.check_crypto()
        finwiz_flow.check_stock()
        finwiz_flow.check_etf()

        # Verify all results were stored in integration system
        finwiz_flow.integration_manager.store_crew_output.assert_any_call("crypto", mock_crew_results["crypto"])
        finwiz_flow.integration_manager.store_crew_output.assert_any_call("stock", mock_crew_results["stock"])
        finwiz_flow.integration_manager.store_crew_output.assert_any_call("etf", mock_crew_results["etf"])

    def test_should_handle_session_information_properly(self, finwiz_flow):
        """Test that flow handles session information properly."""
        # Test without existing session
        assert finwiz_flow.inputs["has_existing_session"] is False
        assert finwiz_flow.inputs["session_id"] == ""
        assert finwiz_flow.inputs["analysis_count"] == 0

        # Test with existing session (via environment variables)
        with patch.dict(
            "os.environ",
            {"FINWIZ_HAS_EXISTING_SESSION": "true", "FINWIZ_SESSION_ID": "test-session-123", "FINWIZ_ANALYSIS_COUNT": "5"},
        ):
            flow_with_session = FinwizFlow()

            assert flow_with_session.inputs["has_existing_session"] is True
            assert flow_with_session.inputs["session_id"] == "test-session-123"
            assert flow_with_session.inputs["analysis_count"] == 5

    def test_should_support_multilingual_configuration(self, finwiz_flow):
        """Test that flow supports multilingual configuration."""
        # Default should be French
        assert finwiz_flow.inputs["report_language"] == "fr"

        # Test with different language
        finwiz_flow.inputs["report_language"] = "en"
        assert finwiz_flow.inputs["report_language"] == "en"

    @patch("finwiz.main.is_feature_enabled")
    def test_should_handle_all_crews_disabled(self, mock_feature_enabled, finwiz_flow):
        """Test that flow handles scenario where all crews are disabled."""
        # Mock all feature flags as disabled
        mock_feature_enabled.return_value = False

        # Execute all crew methods
        finwiz_flow.check_crypto()
        finwiz_flow.check_stock()
        finwiz_flow.check_etf()

        # Verify all crews were skipped
        assert finwiz_flow.inputs.get("crypto_analysis_disabled") is True
        assert finwiz_flow.inputs.get("stock_analysis_disabled") is True
        assert finwiz_flow.inputs.get("etf_analysis_disabled") is True

        # Verify no analysis results were created
        assert "crypto_analysis_result" not in finwiz_flow.inputs
        assert "stock_analysis_result" not in finwiz_flow.inputs
        assert "etf_analysis_result" not in finwiz_flow.inputs

    def test_should_maintain_proper_execution_timing(self, finwiz_flow):
        """Test that flow maintains proper execution timing information."""
        # Check that timestamp is properly formatted
        timestamp = finwiz_flow.inputs["timestamp"]
        assert isinstance(timestamp, str)
        assert len(timestamp) > 0

        # Verify date components
        assert isinstance(finwiz_flow.inputs["current_day"], int)
        assert isinstance(finwiz_flow.inputs["current_month"], int)
        assert isinstance(finwiz_flow.inputs["current_year"], int)
        assert isinstance(finwiz_flow.inputs["current_date"], str)
        assert isinstance(finwiz_flow.inputs["full_date"], str)

    @patch("finwiz.main.is_feature_enabled")
    @patch("finwiz.main.CryptoCrew")
    def test_should_handle_crew_result_formats(self, mock_crypto_crew_class, mock_feature_enabled, finwiz_flow):
        """Test that flow handles different crew result formats properly."""
        # Mock feature flag
        mock_feature_enabled.return_value = True

        # Test with result that has 'raw' attribute
        mock_crypto_crew = MagicMock()
        mock_result_with_raw = MagicMock()
        mock_result_with_raw.raw = "Crypto analysis with raw attribute"
        mock_crypto_crew.crew().kickoff.return_value = mock_result_with_raw
        mock_crypto_crew_class.return_value = mock_crypto_crew

        finwiz_flow.check_crypto()

        assert finwiz_flow.inputs["crypto_analysis_result"] == "Crypto analysis with raw attribute"

        # Test with result that doesn't have 'raw' attribute
        mock_result_without_raw = "Direct crypto analysis result"
        mock_crypto_crew.crew().kickoff.return_value = mock_result_without_raw

        finwiz_flow.check_crypto()

        assert finwiz_flow.inputs["crypto_analysis_result"] == "Direct crypto analysis result"
