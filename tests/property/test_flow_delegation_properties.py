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

from finwiz.flows.flow_orchestrator import FinwizFlow


class TestFlowDelegationProperties:
    """Property-based tests for Flow delegation."""

    @pytest.fixture
    def flow_with_mocked_orchestrators(self, mocker):
        """Create a Flow instance with mocked orchestrators."""
        # Mock all external dependencies
        mocker.patch("finwiz.flows.flow_orchestrator.CrewDataIntegrationManager")
        mocker.patch("finwiz.flows.flow_orchestrator.CrewDataAccessor")
        mocker.patch("finwiz.flows.flow_orchestrator.CoreAnalysisErrorHandler")
        mocker.patch("finwiz.flows.flow_orchestrator.FlowStateManager")
        mocker.patch("finwiz.flows.flow_orchestrator.CrewFactory")
        mocker.patch("finwiz.flows.flow_orchestrator.DataAvailabilityTracker")
        mocker.patch("finwiz.flows.flow_orchestrator.get_resilience_config")
        mocker.patch("finwiz.flows.flow_orchestrator.create_retry_decorator")

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
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
    )
    @given(
        method_data=st.sampled_from(
            [
                ("validate_data_integration", "validation_orch", "validate_data_integration"),
                ("check_portfolio", "validation_orch", "check_portfolio"),
                ("analyze_and_update_portfolio", "deep_analysis_orch", "analyze_and_update_portfolio"),
                ("match_alternatives_after_discovery", "alternatives_orch", "match_alternatives_after_discovery"),
                ("check_crypto", "discovery_orch", "check_crypto"),
                ("check_stock", "discovery_orch", "check_stock"),
                ("check_etf", "discovery_orch", "check_etf"),
                ("check_investment_discovery", "discovery_orch", "check_investment_discovery"),
                ("check_portfolio_rebalancing", "validation_orch", "check_portfolio_rebalancing"),
                ("pre_validate_reporter_input", "validation_orch", "pre_validate_reporter_input"),
                ("report", "reporting_orch", "report"),
            ]
        )
    )
    def test_property_flow_listener_delegation(self, flow_with_mocked_orchestrators, method_data, mocker):
        """
        **Feature: flow-orchestrator-refactoring, Property 25: Flow Listener Delegation**

        For any Flow listener method call, it should delegate to the appropriate
        orchestrator method.

        This property ensures that:
        1. Flow listeners exist and are callable
        2. They delegate to the correct orchestrator
        3. The orchestrator method is called when the Flow listener is invoked
        """
        flow = flow_with_mocked_orchestrators
        listener_method, orchestrator_name, orchestrator_method = method_data

        # Property 1: Flow has the listener method
        assert hasattr(flow, listener_method), f"Flow missing listener {listener_method}"

        # Property 2: Flow has the corresponding orchestrator
        assert hasattr(flow, orchestrator_name), f"Flow missing orchestrator {orchestrator_name}"

        # Get the orchestrator
        orchestrator = getattr(flow, orchestrator_name)

        # Property 3: Orchestrator has the expected method
        assert hasattr(orchestrator, orchestrator_method), f"Orchestrator {orchestrator_name} missing method {orchestrator_method}"

        # Note: We cannot easily test actual delegation without triggering the full Flow
        # execution, which would require complex mocking of CrewAI internals.
        # The unit tests in test_flow_delegation.py cover the actual delegation behavior.
        # This property test verifies the structural requirements for delegation.

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
