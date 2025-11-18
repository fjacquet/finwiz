"""
Unit tests for ProgressTrackingOrchestrator.

Tests progress calculation, metrics file saving, and progress logging.
"""

import json
from datetime import datetime

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from finwiz.flow_state import FinwizState
from finwiz.orchestrators.progress_tracking_orchestrator import ProgressTrackingOrchestrator


class TestProgressTrackingOrchestrator:
    """Test suite for ProgressTrackingOrchestrator."""

    @pytest.fixture
    def state(self):
        """Create a FinwizState instance for testing."""
        state = FinwizState()
        state.flow_start_time = datetime.now().isoformat()
        return state

    @pytest.fixture
    def orchestrator(self, state):
        """Create a ProgressTrackingOrchestrator instance for testing."""
        return ProgressTrackingOrchestrator(state)

    def test_update_progress_basic(self, orchestrator):
        """Test basic progress update functionality."""
        # Act
        orchestrator.update_progress(holdings_processed=5, total_holdings=10)

        # Assert
        assert orchestrator.state.holdings_processed == 5
        assert orchestrator.state.total_holdings == 10
        assert orchestrator.state.holdings_remaining == 5
        assert orchestrator.state.progress_percentage == 50.0

    def test_update_progress_zero_total(self, orchestrator):
        """Test progress update with zero total holdings."""
        # Act
        orchestrator.update_progress(holdings_processed=0, total_holdings=0)

        # Assert
        assert orchestrator.state.holdings_processed == 0
        assert orchestrator.state.total_holdings == 0
        assert orchestrator.state.holdings_remaining == 0
        assert orchestrator.state.progress_percentage == 0.0

    def test_update_progress_complete(self, orchestrator):
        """Test progress update when all holdings are processed."""
        # Act
        orchestrator.update_progress(holdings_processed=10, total_holdings=10)

        # Assert
        assert orchestrator.state.holdings_processed == 10
        assert orchestrator.state.total_holdings == 10
        assert orchestrator.state.holdings_remaining == 0
        assert orchestrator.state.progress_percentage == 100.0

    def test_update_progress_calculates_estimated_time(self, orchestrator):
        """Test that progress update calculates estimated time remaining."""
        # Arrange - set flow start time to 10 seconds ago
        from datetime import timedelta

        flow_start = datetime.now() - timedelta(seconds=10)
        orchestrator.state.flow_start_time = flow_start.isoformat()

        # Act - 2 out of 10 holdings processed
        orchestrator.update_progress(holdings_processed=2, total_holdings=10)

        # Assert
        # Average time per holding = 10s / 2 = 5s
        # Remaining holdings = 8
        # Estimated remaining = 5s * 8 = 40s
        assert orchestrator.state.estimated_time_remaining > 0
        # Allow some tolerance for execution time
        assert 35 <= orchestrator.state.estimated_time_remaining <= 45

    def test_update_progress_no_start_time(self, orchestrator):
        """Test progress update when flow start time is not set."""
        # Arrange
        orchestrator.state.flow_start_time = None

        # Act
        orchestrator.update_progress(holdings_processed=5, total_holdings=10)

        # Assert
        assert orchestrator.state.progress_percentage == 50.0
        assert orchestrator.state.estimated_time_remaining == 0.0

    def test_update_progress_updates_checkpoint_time(self, orchestrator):
        """Test that progress update sets last checkpoint time."""
        # Arrange
        before_update = datetime.now().isoformat()

        # Act
        orchestrator.update_progress(holdings_processed=5, total_holdings=10)

        # Assert
        assert orchestrator.state.last_checkpoint_time is not None
        assert orchestrator.state.last_checkpoint_time >= before_update

    def test_save_batch_metrics_to_file_basic(self, orchestrator, tmp_path):
        """Test saving batch metrics to file."""
        # Arrange
        metrics = {
            "total_holdings": 10,
            "holdings_processed": 10,
            "success_count": 8,
            "failed_count": 2,
            "execution_time_seconds": 120.5,
        }
        output_path = tmp_path / "metrics" / "batch_metrics.json"

        # Act
        orchestrator.save_batch_metrics_to_file(metrics, str(output_path))

        # Assert
        assert output_path.exists()
        with open(output_path) as f:
            saved_metrics = json.load(f)

        assert saved_metrics["total_holdings"] == 10
        assert saved_metrics["holdings_processed"] == 10
        assert saved_metrics["success_count"] == 8
        assert saved_metrics["failed_count"] == 2
        assert saved_metrics["execution_time_seconds"] == 120.5

    def test_save_batch_metrics_creates_directory(self, orchestrator, tmp_path):
        """Test that save_batch_metrics creates output directory if it doesn't exist."""
        # Arrange
        metrics = {"test": "data"}
        output_path = tmp_path / "nested" / "dir" / "metrics.json"

        # Act
        orchestrator.save_batch_metrics_to_file(metrics, str(output_path))

        # Assert
        assert output_path.exists()
        assert output_path.parent.exists()

    def test_save_batch_metrics_empty_metrics(self, orchestrator, mocker):
        """Test that save_batch_metrics handles empty metrics gracefully."""
        # Arrange
        mock_logger = mocker.patch.object(orchestrator, "logger")

        # Act
        orchestrator.save_batch_metrics_to_file({})

        # Assert - warning should be logged
        mock_logger.warning.assert_called_once()
        assert "No batch metrics to save" in str(mock_logger.warning.call_args)

    def test_save_batch_metrics_handles_error_gracefully(self, orchestrator, mocker):
        """Test that save_batch_metrics handles errors without raising."""
        # Arrange
        metrics = {"test": "data"}
        invalid_path = "/invalid/path/that/cannot/be/created/metrics.json"

        # Mock logger to verify error is logged
        mock_logger = mocker.patch.object(orchestrator, "logger")

        # Act - should not raise exception
        orchestrator.save_batch_metrics_to_file(metrics, invalid_path)

        # Assert - error should be logged
        mock_logger.error.assert_called_once()
        assert "Failed to save batch metrics" in str(mock_logger.error.call_args)

    def test_log_progress_called_on_update(self, orchestrator, mocker):
        """Test that _log_progress is called when update_progress is called."""
        # Arrange
        mock_log_progress = mocker.patch.object(orchestrator, "_log_progress")

        # Act
        orchestrator.update_progress(holdings_processed=5, total_holdings=10)

        # Assert
        mock_log_progress.assert_called_once()

    def test_log_progress_formats_message_correctly(self, orchestrator, mocker):
        """Test that _log_progress formats the message correctly."""
        # Arrange
        from datetime import timedelta

        flow_start = datetime.now() - timedelta(seconds=65)  # 1m 5s ago
        orchestrator.state.flow_start_time = flow_start.isoformat()
        orchestrator.state.holdings_processed = 5
        orchestrator.state.total_holdings = 10
        orchestrator.state.progress_percentage = 50.0
        orchestrator.state.estimated_time_remaining = 65.0  # 1m 5s remaining

        mock_logger = mocker.patch.object(orchestrator, "logger")

        # Act
        orchestrator._log_progress()

        # Assert
        mock_logger.info.assert_called_once()
        log_message = str(mock_logger.info.call_args[0][0])

        assert "Progress Update:" in log_message
        assert "5/10" in log_message
        assert "50.0%" in log_message
        assert "Elapsed:" in log_message
        assert "Remaining:" in log_message

    def test_update_progress_percentage_calculation(self, orchestrator):
        """Test progress percentage calculation for various scenarios."""
        # Test 0%
        orchestrator.update_progress(holdings_processed=0, total_holdings=100)
        assert orchestrator.state.progress_percentage == 0.0

        # Test 25%
        orchestrator.update_progress(holdings_processed=25, total_holdings=100)
        assert orchestrator.state.progress_percentage == 25.0

        # Test 50%
        orchestrator.update_progress(holdings_processed=50, total_holdings=100)
        assert orchestrator.state.progress_percentage == 50.0

        # Test 75%
        orchestrator.update_progress(holdings_processed=75, total_holdings=100)
        assert orchestrator.state.progress_percentage == 75.0

        # Test 100%
        orchestrator.update_progress(holdings_processed=100, total_holdings=100)
        assert orchestrator.state.progress_percentage == 100.0

    def test_update_progress_with_datetime_object(self, orchestrator):
        """Test progress update when flow_start_time is a datetime object."""
        # Arrange
        from datetime import timedelta

        flow_start = datetime.now() - timedelta(seconds=10)
        orchestrator.state.flow_start_time = flow_start  # datetime object, not string

        # Act
        orchestrator.update_progress(holdings_processed=2, total_holdings=10)

        # Assert
        assert orchestrator.state.estimated_time_remaining > 0

    def test_save_batch_metrics_with_complex_data(self, orchestrator, tmp_path):
        """Test saving batch metrics with complex nested data structures."""
        # Arrange
        metrics = {
            "total_holdings": 10,
            "ticker_execution_times": {"AAPL": 12.5, "GOOGL": 15.3, "MSFT": 11.2},
            "failed_holdings": ["INVALID1", "INVALID2"],
            "retry_counts": {"AAPL": 0, "GOOGL": 1, "MSFT": 0},
            "nested": {"level1": {"level2": {"value": 42}}},
        }
        output_path = tmp_path / "complex_metrics.json"

        # Act
        orchestrator.save_batch_metrics_to_file(metrics, str(output_path))

        # Assert
        with open(output_path) as f:
            saved_metrics = json.load(f)

        assert saved_metrics["ticker_execution_times"]["AAPL"] == 12.5
        assert saved_metrics["failed_holdings"] == ["INVALID1", "INVALID2"]
        assert saved_metrics["nested"]["level1"]["level2"]["value"] == 42


class TestProgressTrackingOrchestratorProperties:
    """Property-based tests for ProgressTrackingOrchestrator."""

    @given(
        processed=st.integers(min_value=0, max_value=100),
        total=st.integers(min_value=1, max_value=100),
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_progress_calculation_accuracy(self, mocker, processed, total):
        """
        **Feature: flow-orchestrator-refactoring, Property 21: Progress Calculation Accuracy**

        For any progress update with N processed out of M total holdings,
        the percentage should equal (N/M) * 100.

        **Validates: Requirements 8.3**
        """
        # Arrange
        state = FinwizState()
        state.flow_start_time = datetime.now().isoformat()
        orchestrator = ProgressTrackingOrchestrator(state)

        # Ensure processed <= total
        processed = min(processed, total)

        # Act
        orchestrator.update_progress(holdings_processed=processed, total_holdings=total)

        # Assert
        expected_percentage = (processed / total) * 100
        assert abs(state.progress_percentage - expected_percentage) < 0.01

        # Additional assertions
        assert state.holdings_processed == processed
        assert state.total_holdings == total
        assert state.holdings_remaining == total - processed
