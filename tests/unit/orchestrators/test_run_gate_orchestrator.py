"""The orchestrator collects from state, evaluates, writes, logs -- and never raises."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from finwiz.config.settings import RunGateSettings
from finwiz.orchestrators.run_gate_orchestrator import (
    RunGateOrchestrator,
    cost_from,
    coverage_from,
    fact_pack_from,
    phases_from,
    valuation_from,
)
from finwiz.schemas.run_summary import RunSummary, Verdict

NOW = datetime(2026, 9, 5, 9, 28, 9, tzinfo=UTC)


def _holding(weight: float | None) -> SimpleNamespace:
    return SimpleNamespace(weight=weight)


def _ledger(analyzed: int = 64, total: int = 64) -> SimpleNamespace:
    return SimpleNamespace(run_id="run-abc", coverage=lambda: SimpleNamespace(analyzed=analyzed, degraded=0, failed=total - analyzed, total=total))


def _state(**overrides) -> SimpleNamespace:
    base = {
        "id": "state-id",
        "timestamp": "2026-09-05 09:04:46",
        "run_ledger": _ledger(),
        "portfolio_review": SimpleNamespace(holdings=[_holding(0.5), _holding(0.5), _holding(None)]),
        "fact_pack_freshness": {"total": 3, "fresh": 2, "recent": 0, "stale": 1, "missing": 0, "oldest_stale_fetched_at": datetime(2026, 8, 17, tzinfo=UTC)},
        "investment_discovery_result": {"opportunities": [{"ticker": "X"}, {"ticker": "Y"}]},
        "alternatives_count": 0,
        "portfolio_gap_profile": {"underperformer_slots": [{}, {}, {}]},
        "stress_test_count": 6,
        "optimal_allocation": None,
        "llm_cost_summary": {"total_cost": 0.51, "call_count": 68, "per_crew": {"deep_analysis_stock": {"cost": 0.51, "calls": 68, "cost_known": True}}},
        "run_summary": None,
        "gate_verdict": None,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


class TestCollectors:
    def test_coverage_from_ledger(self) -> None:
        c = coverage_from(_ledger(analyzed=60, total=64))
        assert (c.available, c.analyzed, c.failed, c.total) == (True, 60, 4, 64)

    def test_coverage_from_none_is_unavailable(self) -> None:
        assert coverage_from(None).available is False

    def test_valuation_uses_the_heros_denominator(self) -> None:
        """Unpriced holdings leave `priced`, never `total` -- the 5.14.1 lesson."""
        v = valuation_from(SimpleNamespace(holdings=[_holding(0.4), _holding(0.6), _holding(None)]))
        assert (v.available, v.priced, v.total) == (True, 2, 3)

    def test_valuation_from_none_is_unavailable(self) -> None:
        assert valuation_from(None).available is False

    def test_fact_pack_from_dict(self) -> None:
        f = fact_pack_from({"total": 64, "fresh": 40, "recent": 6, "stale": 18, "missing": 0, "oldest_stale_fetched_at": None})
        assert (f.available, f.stale, f.total) == (True, 18, 64)

    def test_fact_pack_from_none_is_unavailable(self) -> None:
        assert fact_pack_from(None).available is False

    def test_phases_read_the_named_state_fields(self) -> None:
        p = phases_from(_state())
        assert (p.discovery_candidates, p.alternatives_found, p.underperformers, p.stress_scenarios, p.optimal_allocation) == (2, 0, 3, 6, False)

    def test_phases_treat_none_discovery_and_raw_output_as_zero(self) -> None:
        assert phases_from(_state(investment_discovery_result=None)).discovery_candidates == 0
        assert phases_from(_state(investment_discovery_result={"raw_output": "text"})).discovery_candidates == 0

    def test_cost_lists_every_unpriced_crew(self) -> None:
        c = cost_from({"total_cost": 0.0, "call_count": 10, "per_crew": {"a": {"cost_known": False}, "b": {"cost_known": True}, "c": {"cost_known": False}}})
        assert (c.available, c.cost_known, c.unpriced_crews) == (True, False, ["a", "c"])

    def test_cost_from_none_is_unavailable(self) -> None:
        assert cost_from(None).available is False


class TestRun:
    def test_writes_json_logs_block_and_sets_state(self, tmp_path, caplog) -> None:
        state = _state()
        with caplog.at_level(logging.INFO):
            summary = RunGateOrchestrator(state, output_dir=tmp_path, thresholds=RunGateSettings(), now=lambda: NOW).run()

        assert summary is not None and summary.verdict is Verdict.FAIL  # 1/3 stale = 33% > 25%
        assert state.gate_verdict == "FAIL"
        assert state.run_summary == summary.model_dump(mode="json")

        written = RunSummary.model_validate_json((tmp_path / "run_summary.json").read_text())
        assert written == summary
        assert (tmp_path / "run_ledger" / "run-abc.summary.json").exists()

        lines = [r.message for r in caplog.records if r.message.startswith("run gate: ")]
        assert len(lines) == 9
        assert lines[-1].startswith("run gate: verdict FAIL")

    def test_duration_is_computed_from_state_timestamp(self, tmp_path) -> None:
        summary = RunGateOrchestrator(_state(), output_dir=tmp_path, now=lambda: NOW).run()
        assert summary is not None
        assert summary.duration_seconds == pytest.approx((NOW.replace(tzinfo=None) - datetime(2026, 9, 5, 9, 4, 46)).total_seconds())

    def test_a_collector_raising_yields_error_not_an_exception(self, tmp_path, caplog, mocker) -> None:
        mocker.patch("finwiz.orchestrators.run_gate_orchestrator.coverage_from", side_effect=RuntimeError("ledger exploded"))
        state = _state()

        with caplog.at_level(logging.ERROR):
            result = RunGateOrchestrator(state, output_dir=tmp_path).run()

        assert result is None
        assert state.gate_verdict == "ERROR"
        failures = [r for r in caplog.records if "run gate" in r.message.lower() and r.levelno >= logging.ERROR]
        assert failures and failures[0].exc_info is not None, "the gate's own failure must keep its traceback"

    def test_unavailable_inputs_still_produce_a_summary(self, tmp_path) -> None:
        state = _state(run_ledger=None, llm_cost_summary=None, fact_pack_freshness=None)
        summary = RunGateOrchestrator(state, output_dir=tmp_path, now=lambda: NOW).run()
        assert summary is not None and summary.verdict is Verdict.FAIL
        assert [c.name for c in summary.checks if c.detail == "not measured"] == ["coverage", "cost_known", "fact_pack_stale", "fact_pack_missing"]
