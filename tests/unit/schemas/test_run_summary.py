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

    def test_phases_have_no_availability_flag_because_absence_is_a_zero(self) -> None:
        assert PhasesInput().discovery_candidates == 0
        assert PhasesInput().optimal_allocation is False


class TestRunSummaryRoundTrip:
    def test_json_round_trip_preserves_everything(self) -> None:
        summary = RunSummary(
            run_id="abc123",
            started_at=datetime(2026, 9, 5, 9, 4, 46, tzinfo=UTC),
            finished_at=datetime(2026, 9, 5, 9, 28, 9, tzinfo=UTC),
            duration_seconds=1403.0,
            coverage=CoverageInput(available=True, analyzed=64, degraded=0, failed=0, total=64),
            valuation=ValuationInput(available=True, priced=63, total=64),
            fact_pack=FactPackInput(available=True, fresh=40, recent=6, stale=18, missing=0, total=64, oldest_stale_fetched_at=datetime(2026, 8, 17, tzinfo=UTC)),
            phases=PhasesInput(discovery_candidates=0, alternatives_found=0, underperformers=17, stress_scenarios=6, optimal_allocation=False),
            cost=CostInput(available=True, total_usd=0.0, call_count=2080, cost_known=False, unpriced_crews=["deep_analysis_etf"]),
            checks=[GateCheck(name="coverage", severity=Severity.FAIL, passed=True, observed="64/64", threshold="min 95%", detail="")],
            verdict=Verdict.FAIL,
        )
        again = RunSummary.model_validate_json(summary.model_dump_json())
        assert again == summary
        assert again.verdict is Verdict.FAIL
        assert again.cost.unpriced_crews == ["deep_analysis_etf"]
