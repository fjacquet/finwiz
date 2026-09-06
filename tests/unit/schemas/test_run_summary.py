"""Unit tests for the run-summary contract."""

from __future__ import annotations

from datetime import UTC, datetime

from finwiz.schemas.run_summary import (
    CostInput,
    CoverageInput,
    FactPackInput,
    GateCheck,
    PhasesInput,
    RunSummary,
    Severity,
    ValuationInput,
    Verdict,
)


class TestInputsDefaultToNotMeasured:
    def test_every_measured_input_starts_unavailable(self) -> None:
        assert CoverageInput().available is False
        assert ValuationInput().available is False
        assert FactPackInput().available is False
        assert CostInput().available is False

    def test_phases_carry_one_flag_for_the_count_whose_zero_is_ambiguous(self) -> None:
        """A phase that never ran honestly delivered zero candidates -- but zero underperformers
        is also what Phase 3.6's fail-soft empty gap profile looks like, and it is the value that
        passes the ``alternatives`` check.
        """
        assert PhasesInput().discovery_candidates == 0
        assert PhasesInput().stress_scenarios == 0
        assert PhasesInput().underperformers_available is False

    def test_the_contract_carries_no_field_no_check_reads(self) -> None:
        """``failed`` is ``total - analyzed - degraded``; nothing under ``src/`` writes ``state.optimal_allocation``."""
        assert "failed" not in CoverageInput.model_fields
        assert "optimal_allocation" not in PhasesInput.model_fields


class TestRunSummaryRoundTrip:
    def test_json_round_trip_preserves_everything(self) -> None:
        summary = RunSummary(
            run_id="abc123",
            started_at=datetime(2026, 9, 5, 9, 4, 46, tzinfo=UTC),
            finished_at=datetime(2026, 9, 5, 9, 28, 9, tzinfo=UTC),
            duration_seconds=1403.0,
            coverage=CoverageInput(available=True, analyzed=60, degraded=4, total=64),
            valuation=ValuationInput(available=True, priced=63, total=64),
            fact_pack=FactPackInput(available=True, fresh=40, recent=6, stale=18, missing=0, total=64, oldest_stale_fetched_at=datetime(2026, 8, 17, tzinfo=UTC)),
            phases=PhasesInput(discovery_candidates=0, alternatives_found=0, underperformers=17, underperformers_available=True, stress_scenarios=6),
            cost=CostInput(available=True, total_usd=0.0, call_count=2080, cost_known=False, unpriced_crews=["deep_analysis_etf"]),
            checks=[
                GateCheck(
                    name="coverage", severity=Severity.FAIL, passed=True, observed="64/64 analysed = 100.0% (60 clean + 4 degraded, 0 failed)", threshold="min 95.0%", detail=""
                )
            ],
            verdict=Verdict.FAIL,
        )
        again = RunSummary.model_validate_json(summary.model_dump_json())
        assert again == summary
        assert again.verdict is Verdict.FAIL
        assert again.cost.unpriced_crews == ["deep_analysis_etf"]
