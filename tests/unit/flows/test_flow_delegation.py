"""
Unit tests for FinwizFlow's orchestrator properties.

Asserts that `FinwizFlow` exposes each lazily-loaded orchestrator property
(`error_handler_orch`, `progress_orch`, etc.). It does not exercise delegation
between the flow and the orchestrators -- that is covered by
`tests/unit/flows/test_run_sequential_workflow.py`.
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
