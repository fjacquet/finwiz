"""
Tests for Core Analysis Error Handler.

Tests the error handling and graceful degradation functionality
for core analysis crews.
"""

from datetime import datetime, timedelta

import pytest
from pytest import approx

from finwiz.integration.manager import CrewDataIntegrationManager
from finwiz.orchestrators.error_handling.core_analysis_error_handler import CoreAnalysisErrorHandler, CrewErrorContext, CrewFailureType


class TestCoreAnalysisErrorHandler:
    """Test suite for CoreAnalysisErrorHandler."""

    @pytest.fixture
    def mock_integration_manager(self, mocker):
        """Create a mock integration manager."""
        manager = mocker.Mock(spec=CrewDataIntegrationManager)
        manager.get_cached_crew_output.return_value = None
        return manager

    @pytest.fixture
    def error_handler(self, mock_integration_manager):
        """Create an error handler instance."""
        return CoreAnalysisErrorHandler(mock_integration_manager)

    def test_should_initialize_error_handler_when_created(self, error_handler):
        """Test error handler initialization."""
        assert error_handler is not None
        assert hasattr(error_handler, "integration_manager")
        assert hasattr(error_handler, "feature_flags")
        assert hasattr(error_handler, "fallback_strategies")
        assert hasattr(error_handler, "error_history")

    def test_should_classify_timeout_error_when_timeout_in_message(self, error_handler):
        """Test error classification for timeout errors."""
        timeout_error = Exception("Request timed out after 30 seconds")
        error_type = error_handler._classify_error(timeout_error)
        assert error_type == CrewFailureType.TIMEOUT_ERROR

    def test_should_classify_api_error_when_api_in_message(self, error_handler):
        """Test error classification for API errors."""
        api_error = Exception("HTTP 500 API request failed")
        error_type = error_handler._classify_error(api_error)
        assert error_type == CrewFailureType.API_ERROR

    def test_should_classify_validation_error_when_validation_in_message(self, error_handler):
        """Test error classification for validation errors."""
        validation_error = Exception("Schema validation failed")
        error_type = error_handler._classify_error(validation_error)
        assert error_type == CrewFailureType.VALIDATION_ERROR

    def test_should_record_error_when_handle_crew_failure_called(self, error_handler):
        """Test error recording functionality."""
        test_error = Exception("Test error")
        test_inputs = {"test": "data"}

        # Handle the failure
        error_handler.handle_crew_failure("stock", test_error, test_inputs, 5.0)

        # Check error was recorded
        assert "stock" in error_handler.error_history
        assert len(error_handler.error_history["stock"]) == 1

        error_context = error_handler.error_history["stock"][0]
        assert error_context.crew_name == "stock"
        assert error_context.error_message == "Test error"
        assert error_context.execution_time == approx(5.0)

    def test_should_return_cached_data_fallback_when_cache_available(self, mocker, error_handler, mock_integration_manager):
        """Test cached data fallback strategy."""
        # Setup cached data
        cached_data = {
            "metadata": {"storage_timestamp": datetime.now().isoformat(), "crew_name": "stock"},
            "raw_output": "Cached stock analysis",
            "tasks_output": [],
        }
        mock_integration_manager.get_cached_crew_output.return_value = cached_data

        # Mock feature flags to return cached_only strategy
        mock_strategy = mocker.patch.object(error_handler.feature_flags, "get_fallback_strategy", return_value="cached_only")

        test_error = Exception("Test error")
        response = error_handler.handle_crew_failure("stock", test_error, {}, 1.0)

        assert response.success is True
        assert response.cache_used is True
        assert response.fallback_strategy == "cached_data"
        assert response.data is not None

    def test_should_return_reduced_functionality_when_no_cache_available(self, mocker, error_handler, mock_integration_manager):
        """Test reduced functionality fallback strategy."""
        # No cached data available
        mock_integration_manager.get_cached_crew_output.return_value = None

        # Mock feature flags to return cached_only strategy (will fallback to reduced)
        mock_strategy = mocker.patch.object(error_handler.feature_flags, "get_fallback_strategy", return_value="cached_only")

        test_error = Exception("Test error")
        response = error_handler.handle_crew_failure("stock", test_error, {}, 1.0)

        assert response.success is True
        assert response.cache_used is False
        assert response.fallback_strategy == "reduced_functionality"
        assert "limited_analysis" in response.degraded_functionality

    def test_should_return_default_values_when_reduced_functionality_fails(self, mocker, error_handler, mock_integration_manager):
        """Test default values fallback strategy."""
        # No cached data available
        mock_integration_manager.get_cached_crew_output.return_value = None

        # Mock feature flags to return default_values strategy
        mock_strategy = mocker.patch.object(error_handler.feature_flags, "get_fallback_strategy", return_value="default_values")

        test_error = Exception("Test error")
        response = error_handler.handle_crew_failure("stock", test_error, {}, 1.0)

        assert response.success is True
        assert response.fallback_strategy == "default_values"
        assert response.data["ai_recommendation"] == "HOLD"
        assert response.data["confidence_score"] == approx(0.1)

    def test_should_reject_stale_cache_when_too_old(self, mocker, error_handler, mock_integration_manager):
        """Test cache rejection when data is too old."""
        # Setup very old cached data
        old_timestamp = (datetime.now() - timedelta(days=5)).isoformat()
        cached_data = {
            "metadata": {"storage_timestamp": old_timestamp, "crew_name": "stock"},
            "raw_output": "Very old stock analysis",
        }
        mock_integration_manager.get_cached_crew_output.return_value = cached_data

        # Mock feature flags to return cached_only strategy
        mock_strategy = mocker.patch.object(error_handler.feature_flags, "get_fallback_strategy", return_value="cached_only")

        test_error = Exception("Test error")
        response = error_handler.handle_crew_failure("stock", test_error, {}, 1.0)

        # Should fallback to reduced functionality since cache is too old
        assert response.fallback_strategy == "reduced_functionality"

    def test_should_get_error_summary_when_errors_recorded(self, error_handler):
        """Test error summary generation."""
        # Record some errors
        test_error1 = Exception("API timeout")
        test_error2 = Exception("Validation failed")

        error_handler.handle_crew_failure("stock", test_error1, {}, 1.0)
        error_handler.handle_crew_failure("stock", test_error2, {}, 2.0)

        summary = error_handler.get_error_summary("stock")

        assert summary["crew_name"] == "stock"
        assert summary["error_count"] == 2
        assert len(summary["recent_errors"]) == 2
        assert summary["error_rate"] == 2 / 24.0  # 2 errors in 24 hours

    def test_should_get_system_health_status_when_multiple_crews_have_errors(self, error_handler):
        """Test system health status with multiple crew errors."""
        # Record errors for multiple crews
        for i in range(15):  # More than 10 errors to trigger degraded status
            error_handler.handle_crew_failure("stock", Exception(f"Error {i}"), {}, 1.0)

        for i in range(5):  # Fewer errors for ETF
            error_handler.handle_crew_failure("etf", Exception(f"Error {i}"), {}, 1.0)

        health_status = error_handler.get_system_health_status()

        assert health_status["overall_status"] == "degraded"
        assert "stock" in health_status["degraded_crews"]
        assert health_status["crew_status"]["stock"]["status"] == "degraded"
        assert health_status["crew_status"]["etf"]["status"] == "healthy"
        assert health_status["total_errors_24h"] == 20

    def test_should_enhance_cached_data_with_fallback_metadata(self, error_handler):
        """Test cached data enhancement with fallback metadata."""
        cached_data = {"raw_output": "Original analysis", "metadata": {"original": "data"}}

        error_context = CrewErrorContext(crew_name="stock", error_type="api_error", error_message="API failed", execution_time=5.0)

        enhanced_data = error_handler._enhance_cached_data(cached_data, error_context)

        assert enhanced_data["metadata"]["fallback_mode"] is True
        assert enhanced_data["metadata"]["original_error"] == "API failed"
        assert enhanced_data["metadata"]["error_type"] == "api_error"
        assert "[FALLBACK MODE]" in enhanced_data["raw_output"]

    def test_should_handle_missing_cache_gracefully(self, mocker, error_handler, mock_integration_manager):
        """Test graceful handling when cache is completely missing."""
        # No cached data available
        mock_integration_manager.get_cached_crew_output.return_value = None

        # Mock feature flags to return disable strategy
        mock_strategy = mocker.patch.object(error_handler.feature_flags, "get_fallback_strategy", return_value="disable")

        test_error = Exception("Test error")
        response = error_handler.handle_crew_failure("stock", test_error, {}, 1.0)

        assert response.success is False
        assert response.fallback_strategy == "disable"
        assert "crew_disabled" in response.degraded_functionality

    def test_should_clean_old_errors_from_history(self, error_handler):
        """Test that old errors are cleaned from history."""
        # Record an error
        test_error = Exception("Test error")
        error_handler.handle_crew_failure("stock", test_error, {}, 1.0)

        # Manually set an old timestamp
        old_error = error_handler.error_history["stock"][0]
        old_error.timestamp = datetime.now() - timedelta(days=2)

        # Record a new error (this should trigger cleanup)
        error_handler.handle_crew_failure("stock", Exception("New error"), {}, 1.0)

        # Old error should be cleaned up
        assert len(error_handler.error_history["stock"]) == 1
        assert error_handler.error_history["stock"][0].error_message == "New error"
