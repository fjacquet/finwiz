"""
Unit tests for progress tracking helper method in FinwizFlow.

Tests the _update_progress() method that calculates and updates progress metrics.
"""

from datetime import datetime, timedelta

import pytest
from pytest import approx

from finwiz.flows.orchestrator import FinwizFlow


class TestProgressTracking:
    """Test suite for progress tracking functionality."""

    @pytest.fixture
    def flow_instance(self, mocker):
        """Create a FinwizFlow instance with mocked dependencies."""
        # Mock all external dependencies
        mocker.patch("finwiz.flows.orchestrator.CrewDataIntegrationManager")
        mocker.patch("finwiz.flows.orchestrator.CrewDataAccessor")
        mocker.patch("finwiz.flows.orchestrator.CoreAnalysisErrorHandler")
        mocker.patch("finwiz.flows.orchestrator.FlowStateManager")
        mocker.patch("finwiz.flows.orchestrator.CrewFactory")
        mocker.patch("finwiz.flows.orchestrator.DataAvailabilityTracker")
        mocker.patch("finwiz.flows.orchestrator.get_resilience_config")
        mocker.patch("finwiz.flows.orchestrator.create_retry_decorator")

        # Create flow instance
        flow = FinwizFlow()

        # Access the state (managed by Flow framework) and update fields
        # Note: state is read-only property, but we can modify its fields
        flow.state.total_holdings = 10
        flow.state.holdings_processed = 0
        flow.state.holdings_remaining = 10
        flow.state.failed_holdings = []
        flow.state.timeout_holdings = []
        flow.state.flow_start_time = (datetime.now() - timedelta(seconds=100)).isoformat()

        return flow

    def test_should_calculate_progress_percentage_when_holdings_processed(self, flow_instance):
        """Test that progress percentage is calculated correctly."""
        # Arrange
        flow_instance.state.holdings_processed = 5
        flow_instance.state.holdings_remaining = 5

        # Act
        flow_instance._update_progress()

        # Assert
        assert flow_instance.state.progress_percentage == approx(50.0)

    def test_should_calculate_zero_progress_when_no_holdings_processed(self, flow_instance):
        """Test that progress is 0% when no holdings processed."""
        # Arrange
        flow_instance.state.holdings_processed = 0
        flow_instance.state.holdings_remaining = 10

        # Act
        flow_instance._update_progress()

        # Assert
        assert flow_instance.state.progress_percentage == approx(0.0)

    def test_should_calculate_full_progress_when_all_holdings_processed(self, flow_instance):
        """Test that progress is 100% when all holdings processed."""
        # Arrange
        flow_instance.state.holdings_processed = 10
        flow_instance.state.holdings_remaining = 0

        # Act
        flow_instance._update_progress()

        # Assert
        assert flow_instance.state.progress_percentage == approx(100.0)

    def test_should_calculate_estimated_time_remaining_when_holdings_processed(self, flow_instance):
        """Test that estimated time remaining is calculated based on average time."""
        # Arrange
        # 100 seconds elapsed, 5 holdings processed = 20 seconds per holding
        # 5 holdings remaining = 100 seconds estimated
        flow_instance.state.holdings_processed = 5
        flow_instance.state.holdings_remaining = 5

        # Act
        flow_instance._update_progress()

        # Assert
        # Should be approximately 100 seconds (5 remaining * 20 sec/holding)
        assert 95 <= flow_instance.state.estimated_time_remaining <= 105

    def test_should_set_zero_estimated_time_when_no_holdings_remaining(self, flow_instance):
        """Test that estimated time is 0 when no holdings remain."""
        # Arrange
        flow_instance.state.holdings_processed = 10
        flow_instance.state.holdings_remaining = 0

        # Act
        flow_instance._update_progress()

        # Assert
        assert flow_instance.state.estimated_time_remaining == approx(0.0)

    def test_should_set_zero_estimated_time_when_no_holdings_processed(self, flow_instance):
        """Test that estimated time is 0 when no holdings processed yet."""
        # Arrange
        flow_instance.state.holdings_processed = 0
        flow_instance.state.holdings_remaining = 10

        # Act
        flow_instance._update_progress()

        # Assert
        assert flow_instance.state.estimated_time_remaining == approx(0.0)

    def test_should_update_last_checkpoint_time_when_called(self, flow_instance):
        """Test that last checkpoint time is updated to current time."""
        # Arrange
        old_checkpoint = (datetime.now() - timedelta(minutes=5)).isoformat()
        flow_instance.state.last_checkpoint_time = old_checkpoint
        flow_instance.state.holdings_processed = 5
        flow_instance.state.holdings_remaining = 5

        # Act
        before_call = datetime.now()
        flow_instance._update_progress()
        after_call = datetime.now()

        # Assert
        assert flow_instance.state.last_checkpoint_time is not None
        # Parse ISO format string back to datetime for comparison
        checkpoint_dt = datetime.fromisoformat(flow_instance.state.last_checkpoint_time)
        assert before_call <= checkpoint_dt <= after_call
        assert checkpoint_dt > datetime.fromisoformat(old_checkpoint)

    def test_should_handle_zero_total_holdings_gracefully(self, flow_instance):
        """Test that method handles edge case of zero total holdings."""
        # Arrange
        flow_instance.state.total_holdings = 0
        flow_instance.state.holdings_processed = 0
        flow_instance.state.holdings_remaining = 0

        # Act
        flow_instance._update_progress()

        # Assert
        assert flow_instance.state.progress_percentage == approx(0.0)
        assert flow_instance.state.estimated_time_remaining == approx(0.0)
        assert flow_instance.state.last_checkpoint_time is not None

    def test_should_update_state_fields_when_progress_updated(self, flow_instance):
        """Test that state fields are updated correctly when progress is updated."""
        # Arrange
        flow_instance.state.holdings_processed = 5
        flow_instance.state.holdings_remaining = 5
        flow_instance.state.failed_holdings = ["AAPL"]
        flow_instance.state.timeout_holdings = ["TSLA"]

        # Act
        flow_instance._update_progress()

        # Assert - Verify state fields are updated
        assert flow_instance.state.holdings_processed == 5
        assert flow_instance.state.holdings_remaining == 5
        assert flow_instance.state.progress_percentage == approx(50.0)
        assert flow_instance.state.total_holdings == 10
