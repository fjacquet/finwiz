"""Behavior tests for the one pipeline FinwizFlow actually runs.

`run_sequential_workflow` is the only `@start()` method that can fire on
`FinwizFlow`, and it drives all six phases by calling orchestrator methods
directly. These tests assert that call sequence. They replace the property
tests that asserted the (now deleted) `@listen` methods existed by name --
`hasattr` assertions that passed whether or not the pipeline could run.
"""

import pytest

from finwiz.flows.orchestrator import FinwizFlow

PHASE_CALLS = [
    ("validation_orch", "validate_data_integration"),
    ("validation_orch", "check_portfolio"),
    ("deep_analysis_orch", "analyze_and_update_portfolio"),
    ("gap_profile_orch", "build_gap_profile"),
    ("discovery_orch", "check_crypto"),
    ("discovery_orch", "check_stock"),
    ("discovery_orch", "check_etf"),
    ("discovery_orch", "check_investment_discovery"),
    ("alternatives_orch", "match_alternatives_after_discovery"),
    ("validation_orch", "pre_validate_reporter_input"),
    ("reporting_orch", "report"),
]


@pytest.fixture
def flow_with_recording_orchestrators(mocker):
    """A flow whose orchestrators are mocks attached to one recording parent.

    Attaching every orchestrator to a single parent mock makes
    ``parent.mock_calls`` a global, ordered record of the pipeline, which is
    what lets the order assertion below be meaningful.
    """
    for name in (
        "CrewDataIntegrationManager",
        "CrewDataAccessor",
        "CoreAnalysisErrorHandler",
        "FlowStateManager",
        "DataAvailabilityTracker",
        "get_resilience_config",
        "create_retry_decorator",
    ):
        mocker.patch(f"finwiz.flows.orchestrator.{name}")

    # Phase 3.5 and the run gate import their orchestrators inside the
    # function body, so they are patched at their definition sites.
    mocker.patch("finwiz.orchestrators.stress_test_orchestrator.StressTestOrchestrator")
    mocker.patch("finwiz.orchestrators.run_gate_orchestrator.RunGateOrchestrator")

    flow = FinwizFlow()
    parent = mocker.MagicMock()

    # Orchestrators are cached in `flow._orchestrators`, keyed by the short
    # registry names `_get_orch()` uses -- there are no `_<name>_orch`
    # attributes. Seeding that dict is what makes the properties return mocks
    # instead of building real orchestrators.
    for registry_name in (
        "error_handler",
        "progress",
        "utility",
        "deep_analysis",
        "alternatives",
        "discovery",
        "gap_profile",
        "validation",
        "reporting",
    ):
        child = mocker.MagicMock()
        parent.attach_mock(child, f"{registry_name}_orch")
        flow._orchestrators[registry_name] = child

    # Phases 1, 2 and 3 are awaited, so those three need AsyncMock. They are
    # attached rather than assigned: attach_mock keeps them in the parent's
    # call record, which a bare assignment would break.
    for registry_name, method in (
        ("validation", "validate_data_integration"),
        ("validation", "check_portfolio"),
        ("deep_analysis", "analyze_and_update_portfolio"),
    ):
        flow._orchestrators[registry_name].attach_mock(mocker.AsyncMock(), method)

    # check_investment_discovery's return value is passed to alternatives
    # matching; a MagicMock would flow through, but a dict keeps the assertion
    # about what phase 5 receives honest.
    flow.discovery_orch.check_investment_discovery.return_value = {"candidates": []}

    return flow, parent


class TestRunSequentialWorkflowPhases:
    """The six phases run, in order, through the orchestrators."""

    @pytest.mark.asyncio
    async def test_every_phase_is_invoked(self, flow_with_recording_orchestrators):
        flow, _parent = flow_with_recording_orchestrators

        result = await flow.run_sequential_workflow()

        assert result == {"status": "completed"}
        for orch_attr, method in PHASE_CALLS:
            orch = getattr(flow, orch_attr)
            assert getattr(orch, method).called, f"{orch_attr}.{method} was never called"

    @pytest.mark.asyncio
    async def test_phases_run_in_pipeline_order(self, flow_with_recording_orchestrators):
        """Deep analysis cannot precede validation, discovery cannot precede
        the gap profile, and reporting is last. Asserting the order is the
        point: a reordering that breaks the pipeline is exactly what the
        deleted hasattr tests could not see."""
        flow, parent = flow_with_recording_orchestrators

        await flow.run_sequential_workflow()

        observed = [name for name, _args, _kwargs in parent.mock_calls]
        expected = [f"{orch}.{method}" for orch, method in PHASE_CALLS]
        pipeline = [call for call in observed if call in expected]

        assert pipeline == expected

    @pytest.mark.asyncio
    async def test_discovery_result_reaches_alternatives_matching(self, flow_with_recording_orchestrators):
        """Phase 5 consumes what phase 4 produced."""
        flow, _parent = flow_with_recording_orchestrators

        await flow.run_sequential_workflow()

        flow.alternatives_orch.match_alternatives_after_discovery.assert_called_once_with({"candidates": []})

    @pytest.mark.asyncio
    async def test_discovery_none_result_becomes_empty_dict(self, flow_with_recording_orchestrators):
        """`check_investment_discovery() or {}` -- phase 5 must never see None."""
        flow, _parent = flow_with_recording_orchestrators
        flow.discovery_orch.check_investment_discovery.return_value = None

        await flow.run_sequential_workflow()

        flow.alternatives_orch.match_alternatives_after_discovery.assert_called_once_with({})

    @pytest.mark.asyncio
    async def test_deep_analysis_failure_still_logs_cost_summaries(self, flow_with_recording_orchestrators, mocker):
        """Phase 3 is the largest LLM spend; its cost attribution must survive
        the failure path."""
        flow, _parent = flow_with_recording_orchestrators
        flow.deep_analysis_orch.analyze_and_update_portfolio.side_effect = RuntimeError("no analyses produced")
        log_summaries = mocker.patch.object(flow, "_log_post_flow_summaries")

        with pytest.raises(RuntimeError, match="no analyses produced"):
            await flow.run_sequential_workflow()

        log_summaries.assert_called_once()
        assert not flow.reporting_orch.report.called
