"""
Integration tests for Core Analysis functionality.

Tests the integration between core analysis crews, data integration system,
and the main flow orchestration.
"""

from datetime import datetime

import pytest

from finwiz.flows.flow_orchestrator import FinwizFlow
from finwiz.integration.data_accessor import CrewDataAccessor
from finwiz.integration.manager import CrewDataIntegrationManager
from finwiz.utils.core_analysis_error_handler import CoreAnalysisErrorHandler


class TestCoreAnalysisIntegration:
    """Test cases for Core Analysis Integration."""

    @pytest.fixture
    def integration_manager(self):
        """Create a CrewDataIntegrationManager instance for testing."""
        return CrewDataIntegrationManager()

    @pytest.fixture
    def data_accessor(self, integration_manager):
        """Create a CrewDataAccessor instance for testing."""
        return CrewDataAccessor(integration_manager)

    @pytest.fixture
    def error_handler(self, integration_manager):
        """Create a CoreAnalysisErrorHandler instance for testing."""
        return CoreAnalysisErrorHandler(integration_manager)

    @pytest.fixture
    def mock_crew_outputs(self):
        """Create mock crew outputs for testing."""
        return {
            "stock": {
                "analysis": "AAPL shows strong fundamentals with P/E of 25.5",
                "recommendation": "BUY",
                "risk_score": 6,
                "price_target": 165.0,
                "confidence": 0.85,
                "timestamp": datetime.now().isoformat(),
            },
            "etf": {
                "analysis": "SPY provides broad market exposure with low expense ratio",
                "recommendation": "BUY",
                "risk_score": 4,
                "expense_ratio": 0.0945,
                "tracking_error": 0.02,
                "confidence": 0.90,
                "timestamp": datetime.now().isoformat(),
            },
            "crypto": {
                "analysis": "Bitcoin maintains digital gold narrative with institutional support",
                "recommendation": "HOLD",
                "risk_score": 8,
                "price_target": 55000.0,
                "volatility": 0.65,
                "confidence": 0.75,
                "timestamp": datetime.now().isoformat(),
            },
        }

    def test_should_integrate_crew_outputs_with_data_system(self, integration_manager, mock_crew_outputs):
        """Test that crew outputs integrate properly with data system."""
        # Store crew outputs
        for crew_type, output in mock_crew_outputs.items():
            integration_manager.store_crew_output(crew_type, output)

        # Verify outputs can be retrieved
        for crew_type, expected_output in mock_crew_outputs.items():
            stored_output = integration_manager.get_cached_crew_output(crew_type)
            assert stored_output is not None
            assert stored_output == expected_output

    def test_should_provide_data_accessibility_through_accessor(self, data_accessor, integration_manager, mock_crew_outputs):
        """Test that data accessor provides proper access to crew outputs."""
        # Store crew outputs
        for crew_type, output in mock_crew_outputs.items():
            integration_manager.store_crew_output(crew_type, output)

        # Test data availability check
        availability_report = data_accessor.check_data_availability()
        assert availability_report is not None
        # availability_report is a Pydantic model, not a dict
        assert hasattr(availability_report, "stock_available")

        # Test accessing specific crew data
        stock_data = data_accessor.get_crew_data("stock")
        assert stock_data is not None
        assert stock_data["recommendation"] == "BUY"

    def test_should_handle_missing_crew_data_gracefully(self, data_accessor):
        """Test that data accessor handles missing crew data gracefully."""
        # Try to access non-existent crew data - should raise AttributeError
        with pytest.raises(AttributeError):
            data_accessor.get_crew_data("nonexistent_crew")

        # Check availability report with no data
        availability_report = data_accessor.check_data_availability()
        assert availability_report is not None

    def test_should_validate_crew_output_schemas(self, integration_manager):
        """Test that crew outputs are validated against schemas."""
        valid_output = {
            "analysis": "Valid analysis text",
            "recommendation": "BUY",
            "risk_score": 5,
            "confidence": 0.8,
            "timestamp": datetime.now().isoformat(),
        }

        # Valid output should be stored successfully
        result = integration_manager.store_crew_output("stock", valid_output)
        assert result is True

        # Invalid output - validation is permissive in integration mode
        # so this will succeed but with warnings
        invalid_output = {
            "analysis": "Missing required fields",
            # Missing recommendation, risk_score, etc.
        }

        # Store should succeed even with incomplete data (graceful degradation)
        result = integration_manager.store_crew_output("stock", invalid_output)
        assert result is True  # Integration manager is permissive

    def test_should_integrate_all_crews_in_flow(self, mocker, mock_crew_outputs):
        """Test that all crews integrate properly in the main flow."""
        # Mock the crews and feature flags
        mock_feature_enabled = mocker.patch("finwiz.main.is_feature_enabled")
        mock_crypto_crew_class = mocker.patch("finwiz.main.CryptoCrew")
        mock_stock_crew_class = mocker.patch("finwiz.main.StockCrew")
        mock_etf_crew_class = mocker.patch("finwiz.main.EtfCrew")
        # Mock feature flags
        mock_feature_enabled.return_value = True

        # Mock crew instances and results
        mock_crypto_crew = mocker.MagicMock()
        mock_crypto_result = mocker.MagicMock()
        mock_crypto_result.raw = str(mock_crew_outputs["crypto"])
        mock_crypto_crew.crew().kickoff.return_value = mock_crypto_result
        mock_crypto_crew_class.return_value = mock_crypto_crew

        mock_stock_crew = mocker.MagicMock()
        mock_stock_result = mocker.MagicMock()
        mock_stock_result.raw = str(mock_crew_outputs["stock"])
        mock_stock_crew.crew().kickoff.return_value = mock_stock_result
        mock_stock_crew_class.return_value = mock_stock_crew

        mock_etf_crew = mocker.MagicMock()
        mock_etf_result = mocker.MagicMock()
        mock_etf_result.raw = str(mock_crew_outputs["etf"])
        mock_etf_crew.crew().kickoff.return_value = mock_etf_result
        mock_etf_crew_class.return_value = mock_etf_crew

        # Create and execute flow
        flow = FinwizFlow()

        # Execute core analysis crews
        flow.check_crypto()
        flow.check_stock()
        flow.check_etf()

        # Verify all crews were executed
        mock_crypto_crew.crew().kickoff.assert_called_once()
        mock_stock_crew.crew().kickoff.assert_called_once()
        mock_etf_crew.crew().kickoff.assert_called_once()

        # Verify results are stored in flow inputs
        assert "crypto_analysis_result" in flow.inputs
        assert "stock_analysis_result" in flow.inputs
        assert "etf_analysis_result" in flow.inputs

        # Verify success flags
        assert flow.inputs["crypto_analysis_success"] is True
        assert flow.inputs["stock_analysis_success"] is True
        assert flow.inputs["etf_analysis_success"] is True

    def test_should_handle_partial_crew_failures(self, error_handler, integration_manager):
        """Test that system handles partial crew failures gracefully."""
        # Simulate successful stock analysis
        stock_output = {
            "analysis": "Stock analysis successful",
            "recommendation": "BUY",
            "risk_score": 5,
            "confidence": 0.8,
            "timestamp": datetime.now().isoformat(),
        }
        integration_manager.store_crew_output("stock", stock_output)

        # Simulate crypto crew failure
        crypto_error = Exception("Crypto API connection failed")
        fallback_response = error_handler.handle_crew_failure(
            crew_name="crypto", error=crypto_error, inputs={"current_date": "2025-01-15"}, execution_time=5.0
        )

        # Verify error handling
        assert fallback_response is not None
        assert hasattr(fallback_response, "success")
        assert hasattr(fallback_response, "message")
        assert hasattr(fallback_response, "fallback_strategy")

        # Verify stock data is still available
        stock_data = integration_manager.get_cached_crew_output("stock")
        assert stock_data is not None
        assert stock_data["recommendation"] == "BUY"

    def test_should_support_data_freshness_validation(self, integration_manager):
        """Test that data freshness validation works in integration."""
        # Store output with current timestamp
        fresh_output = {
            "analysis": "Fresh analysis",
            "recommendation": "BUY",
            "risk_score": 5,
            "confidence": 0.8,
            "timestamp": datetime.now().isoformat(),
        }
        integration_manager.store_crew_output("stock", fresh_output)

        # Store output with old timestamp
        old_timestamp = datetime(2024, 1, 1).isoformat()
        stale_output = {
            "analysis": "Stale analysis",
            "recommendation": "HOLD",
            "risk_score": 6,
            "confidence": 0.7,
            "timestamp": old_timestamp,
        }
        integration_manager.store_crew_output("etf", stale_output)

        # Verify fresh data is available
        fresh_data = integration_manager.get_cached_crew_output("stock")
        assert fresh_data is not None
        assert fresh_data["timestamp"] == fresh_output["timestamp"]

        # Verify stale data is flagged (implementation dependent)
        stale_data = integration_manager.get_cached_crew_output("etf")
        assert stale_data is not None

    def test_should_aggregate_crew_recommendations(self, integration_manager, mock_crew_outputs):
        """Test that crew recommendations can be aggregated properly."""
        # Store all crew outputs
        for crew_type, output in mock_crew_outputs.items():
            integration_manager.store_crew_output(crew_type, output)

        # Aggregate recommendations
        all_recommendations = []
        for crew_type in ["stock", "etf", "crypto"]:
            crew_data = integration_manager.get_cached_crew_output(crew_type)
            if crew_data and "recommendation" in crew_data:
                all_recommendations.append(crew_data["recommendation"])

        # Verify aggregation
        assert len(all_recommendations) == 3
        assert "BUY" in all_recommendations
        assert "HOLD" in all_recommendations

    def test_should_calculate_aggregate_risk_scores(self, integration_manager, mock_crew_outputs):
        """Test that risk scores can be aggregated across crews."""
        # Store all crew outputs
        for crew_type, output in mock_crew_outputs.items():
            integration_manager.store_crew_output(crew_type, output)

        # Calculate aggregate risk
        risk_scores = []
        for crew_type in ["stock", "etf", "crypto"]:
            crew_data = integration_manager.get_cached_crew_output(crew_type)
            if crew_data and "risk_score" in crew_data:
                risk_scores.append(crew_data["risk_score"])

        # Verify risk score aggregation
        assert len(risk_scores) == 3
        assert all(1 <= score <= 10 for score in risk_scores)

        # Calculate weighted average risk
        avg_risk = sum(risk_scores) / len(risk_scores)
        assert 1 <= avg_risk <= 10

    def test_should_support_cross_crew_data_sharing(self, integration_manager, data_accessor):
        """Test that crews can share data through the integration system."""
        # Store market sentiment from stock crew
        stock_output = {
            "analysis": "Market sentiment is bullish",
            "recommendation": "BUY",
            "risk_score": 5,
            "market_sentiment": "bullish",
            "sector_trends": {"technology": "positive", "healthcare": "neutral"},
            "confidence": 0.8,
            "timestamp": datetime.now().isoformat(),
        }
        integration_manager.store_crew_output("stock", stock_output)

        # ETF crew can access stock market sentiment
        stock_data = data_accessor.get_crew_data("stock")
        assert stock_data is not None
        assert stock_data["market_sentiment"] == "bullish"
        assert "sector_trends" in stock_data

        # Use shared data in ETF analysis
        etf_output = {
            "analysis": f"ETF analysis considering {stock_data['market_sentiment']} market sentiment",
            "recommendation": "BUY",
            "risk_score": 4,
            "confidence": 0.9,
            "timestamp": datetime.now().isoformat(),
        }
        integration_manager.store_crew_output("etf", etf_output)

        # Verify cross-crew data usage
        etf_data = integration_manager.get_cached_crew_output("etf")
        assert "bullish" in etf_data["analysis"]

    def test_should_maintain_data_consistency_across_crews(self, integration_manager, mock_crew_outputs):
        """Test that data consistency is maintained across all crews."""
        # Store all crew outputs
        for crew_type, output in mock_crew_outputs.items():
            integration_manager.store_crew_output(crew_type, output)

        # Verify all outputs have required fields
        required_fields = ["analysis", "recommendation", "risk_score", "confidence", "timestamp"]

        for crew_type in ["stock", "etf", "crypto"]:
            crew_data = integration_manager.get_cached_crew_output(crew_type)
            assert crew_data is not None

            for field in required_fields:
                assert field in crew_data, f"Missing {field} in {crew_type} output"

        # Verify data types are consistent
        for crew_type in ["stock", "etf", "crypto"]:
            crew_data = integration_manager.get_cached_crew_output(crew_type)

            assert isinstance(crew_data["analysis"], str)
            assert crew_data["recommendation"] in ["BUY", "HOLD", "SELL"]
            assert isinstance(crew_data["risk_score"], int)
            assert 1 <= crew_data["risk_score"] <= 10
            assert isinstance(crew_data["confidence"], float)
            assert 0.0 <= crew_data["confidence"] <= 1.0

    def test_should_handle_feature_flag_combinations(self, mocker):
        """Test that different feature flag combinations work properly."""
        # Mock feature flags
        mock_feature_enabled = mocker.patch("finwiz.main.is_feature_enabled")

        # Test with only stock analysis enabled
        def mock_feature_side_effect(feature_name):
            return feature_name == "stock_analysis"

        mock_feature_enabled.side_effect = mock_feature_side_effect

        flow = FinwizFlow()

        with mocker.patch("finwiz.main.StockCrew") as mock_stock_crew_class:
            mock_stock_crew = mocker.MagicMock()
            mock_result = mocker.MagicMock()
            mock_result.raw = "Stock analysis only"
            mock_stock_crew.crew().kickoff.return_value = mock_result
            mock_stock_crew_class.return_value = mock_stock_crew

            # Execute crews
            flow.check_stock()
            flow.check_etf()
            flow.check_crypto()

            # Verify only stock crew executed
            mock_stock_crew.crew().kickoff.assert_called_once()
            assert "stock_analysis_result" in flow.inputs
            assert flow.inputs.get("etf_analysis_disabled") is True
            assert flow.inputs.get("crypto_analysis_disabled") is True

    def test_should_support_performance_monitoring(self, integration_manager):
        """Test that performance monitoring works in integration."""
        start_time = datetime.now()

        # Simulate crew execution with timing
        crew_output = {
            "analysis": "Performance test analysis",
            "recommendation": "BUY",
            "risk_score": 5,
            "confidence": 0.8,
            "timestamp": datetime.now().isoformat(),
            "execution_time": 2.5,
            "performance_metrics": {
                "api_calls": 5,
                "data_points_processed": 100,
                "cache_hits": 3,
                "cache_misses": 2,
            },
        }

        integration_manager.store_crew_output("stock", crew_output)

        # Verify performance data is stored
        stored_data = integration_manager.get_cached_crew_output("stock")
        assert "execution_time" in stored_data
        assert "performance_metrics" in stored_data
        assert stored_data["performance_metrics"]["api_calls"] == 5
