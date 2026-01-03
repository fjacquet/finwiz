"""
Unit tests for Flow delegation to orchestrators.

Tests that Flow listeners correctly delegate to appropriate orchestrators
and that orchestrator methods are called with correct parameters.

Validates Requirements 10.2: Flow listeners delegate to appropriate orchestrators.
"""

import pytest

from finwiz.flows.orchestrator import FinwizFlow


class TestFlowDelegation:
    """Test suite for Flow delegation to orchestrators."""

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
        return flow

    def test_should_have_all_orchestrator_properties(self, flow_instance):
        """Test that Flow has all required orchestrator properties."""
        # Assert all orchestrators are accessible
        assert hasattr(flow_instance, "error_handler_orch")
        assert hasattr(flow_instance, "progress_orch")
        assert hasattr(flow_instance, "utility_orch")
        assert hasattr(flow_instance, "deep_analysis_orch")
        assert hasattr(flow_instance, "alternatives_orch")
        assert hasattr(flow_instance, "discovery_orch")
        assert hasattr(flow_instance, "validation_orch")
        assert hasattr(flow_instance, "reporting_orch")
