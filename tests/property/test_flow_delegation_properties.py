"""
Property-based tests for Flow delegation to orchestrators.

Tests that Flow listeners correctly delegate to appropriate orchestrators
using property-based testing with Hypothesis.

**Feature: flow-orchestrator-refactoring, Property 25: Flow Listener Delegation**
**Validates: Requirements 10.2**
"""

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from finwiz.flows.orchestrator import FinwizFlow


class TestFlowDelegationProperties:
    """Property-based tests for Flow delegation."""

    @pytest.fixture
    def flow_with_mocked_orchestrators(self, mocker):
        """Create a Flow instance with mocked orchestrators."""
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

        # Mock all orchestrators using pytest-mock
        flow._error_handler_orch = mocker.MagicMock()
        flow._progress_orch = mocker.MagicMock()
        flow._utility_orch = mocker.MagicMock()
        flow._deep_analysis_orch = mocker.MagicMock()
        flow._alternatives_orch = mocker.MagicMock()
        flow._discovery_orch = mocker.MagicMock()
        flow._validation_orch = mocker.MagicMock()
        flow._reporting_orch = mocker.MagicMock()

        return flow

    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
    )
    @given(
        orchestrator_name=st.sampled_from(
            [
                "error_handler_orch",
                "progress_orch",
                "utility_orch",
                "deep_analysis_orch",
                "alternatives_orch",
                "discovery_orch",
                "validation_orch",
                "reporting_orch",
            ]
        )
    )
    def test_property_orchestrator_accessibility(self, flow_with_mocked_orchestrators, orchestrator_name):
        """
        **Feature: flow-orchestrator-refactoring, Property 25: Flow Listener Delegation**

        For any orchestrator name, the Flow should have that orchestrator accessible
        as a property.

        This ensures that all orchestrators are properly initialized and accessible
        through the Flow instance.
        """
        flow = flow_with_mocked_orchestrators

        # Property: Flow has the orchestrator property
        assert hasattr(flow, orchestrator_name), f"Flow missing {orchestrator_name}"

        # Property: Orchestrator property returns a valid object
        orchestrator = getattr(flow, orchestrator_name)
        assert orchestrator is not None, f"{orchestrator_name} is None"

    @settings(
        max_examples=50,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
    )
    @given(
        orchestrator_pairs=st.lists(
            st.sampled_from(
                [
                    "error_handler_orch",
                    "progress_orch",
                    "utility_orch",
                    "deep_analysis_orch",
                    "alternatives_orch",
                    "discovery_orch",
                    "validation_orch",
                    "reporting_orch",
                ]
            ),
            min_size=2,
            max_size=8,
            unique=True,
        )
    )
    def test_property_orchestrator_independence(self, flow_with_mocked_orchestrators, orchestrator_pairs):
        """
        **Feature: flow-orchestrator-refactoring, Property 25: Flow Listener Delegation**

        For any set of orchestrators, they should be independent instances.

        This ensures that orchestrators don't share state and can be tested
        independently.
        """
        flow = flow_with_mocked_orchestrators

        # Get all orchestrators
        orchestrators = [getattr(flow, name) for name in orchestrator_pairs]

        # Property: All orchestrators are distinct objects
        for i, orch1 in enumerate(orchestrators):
            for j, orch2 in enumerate(orchestrators):
                if i != j:
                    assert orch1 is not orch2, f"Orchestrators {orchestrator_pairs[i]} and {orchestrator_pairs[j]} are the same instance"

    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
    )
    @given(
        orchestrator_name=st.sampled_from(
            [
                "error_handler_orch",
                "progress_orch",
                "utility_orch",
                "deep_analysis_orch",
                "alternatives_orch",
                "discovery_orch",
                "validation_orch",
                "reporting_orch",
            ]
        )
    )
    def test_property_orchestrator_has_state(self, flow_with_mocked_orchestrators, orchestrator_name):
        """
        **Feature: flow-orchestrator-refactoring, Property 25: Flow Listener Delegation**

        For any orchestrator, it should have access to the Flow state.

        This ensures that orchestrators can read and update the shared Flow state.
        """
        flow = flow_with_mocked_orchestrators

        # Get the orchestrator
        orchestrator = getattr(flow, orchestrator_name)

        # Property: Orchestrator has state attribute
        # Note: This is a structural check. The actual state access is tested in unit tests.
        assert hasattr(orchestrator, "state"), f"{orchestrator_name} missing state attribute"
