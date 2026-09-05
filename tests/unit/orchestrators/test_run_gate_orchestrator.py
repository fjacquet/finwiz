"""The orchestrator collects from state, evaluates, writes, logs -- and never raises.

Every fixture here is producer output, not prose. The portfolio review goes
through ``save_review_json`` and back exactly as the flow writes and reads it,
discovery through ``DiscoveryOrchestrator.check_investment_discovery``, coverage
through a real ``RunLedger``, freshness through ``summarize_fact_pack_freshness``,
cost through a real ``TokenMonitorCallback``, and the state is a real
``FinwizState``. Hand-invented shapes -- ``SimpleNamespace(holdings=...)``,
``{"opportunities": [...]}`` -- are what let a gate that could never pass survive
seven reviews: the fixture asserted a contract the collector satisfied and the
flow did not.
"""

from __future__ import annotations

import json
import logging
import os
import time
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from finwiz.analysis.fact_pack_freshness import summarize_fact_pack_freshness
from finwiz.analysis.run_gate import exit_code_for
from finwiz.analysis.stages._ledger import RunLedger
from finwiz.config.settings import RunGateSettings
from finwiz.flow_state import FinwizState
from finwiz.infrastructure.monitoring.litellm_callback import TokenMonitorCallback
from finwiz.orchestrators.discovery_orchestrator import DiscoveryOrchestrator
from finwiz.orchestrators.portfolio_review_orchestrator import save_review_json
from finwiz.orchestrators.run_gate_orchestrator import (
    RunGateOrchestrator,
    cost_from,
    coverage_from,
    fact_pack_from,
    phases_from,
    valuation_from,
)
from finwiz.schemas.common import RiskAssessmentStandardized
from finwiz.schemas.newcomer_discovery import PortfolioGapProfile, UnderperformerSlot
from finwiz.schemas.portfolio_review import HoldingDecision, PortfolioReview
from finwiz.schemas.run_ledger import RunLedgerEntry
from finwiz.schemas.run_summary import RunSummary, Verdict
from finwiz.schemas.stage_contract import StageOutcome

MOMENT = datetime(2026, 9, 5, 9, 0, tzinfo=UTC)


# ---------------------------------------------------------------------------
# Fixtures built by the code that builds them in a run
# ---------------------------------------------------------------------------


def _holding(ticker: str, weight: float | None) -> HoldingDecision:
    return HoldingDecision(
        ticker=ticker,
        name=f"{ticker} Inc.",
        asset_class="stock",
        currency="USD",
        decision="KEEP",
        composite_score=0.8,
        grade="A",
        grade_description="Grade A holding",
        recommended_action="HOLD",
        risk=RiskAssessmentStandardized(score=2.5, level="Medium"),
        weight=weight,
    )


def _review(tmp_path: Path, weights: Sequence[float | None]) -> dict[str, Any]:
    """The exact dict the flow puts on ``state.portfolio_review``.

    ``save_review_json`` writes the review file and ``validation_orchestrator``
    reads it back with ``json.loads``; doing both here means the fixture cannot
    drift from the shape production produces.
    """
    review = PortfolioReview(
        as_of=MOMENT,
        holdings=[_holding(f"T{i}", w) for i, w in enumerate(weights)],
        total_value_eur=100.0,
    )
    path = tmp_path / "portfolio_review.json"
    save_review_json(review, path)
    return json.loads(path.read_text(encoding="utf-8"))


def _ledger(tmp_path: Path, analyzed: int = 3, total: int = 3, run_id: str = "run-abc") -> RunLedger:
    """A real ledger with `analyzed` holdings carried through to the terminal stage."""
    ledger = RunLedger(run_id=run_id, artifact_dir=tmp_path / "ledger", total=total)
    for i in range(analyzed):
        for stage in ("collect", "quantify", "qualify", "synthesize", "emit"):
            ledger.record(RunLedgerEntry(run_id=run_id, ticker=f"T{i}", started_at=MOMENT, finished_at=MOMENT, stage=stage, outcome=StageOutcome.OK))
    return ledger


def _enriched(freshness: str | None) -> SimpleNamespace:
    """What ``summarize_fact_pack_freshness`` reads off one enriched analysis."""
    if freshness is None:
        return SimpleNamespace(qualitative=None)
    return SimpleNamespace(qualitative=SimpleNamespace(fact_pack=SimpleNamespace(freshness=freshness, fetched_at=datetime(2026, 8, 17, tzinfo=UTC))))


def _freshness(fresh: int = 0, recent: int = 0, stale: int = 0, missing: int = 0) -> dict[str, Any]:
    """The dict Phase 3 persists: the real summariser, dumped as ``_record_fact_pack_freshness`` dumps it."""
    enriched: dict[str, Any] = {}
    for bucket, count in (("fresh", fresh), ("recent", recent), ("stale", stale)):
        for i in range(count):
            enriched[f"{bucket}{i}"] = _enriched(bucket)
    for i in range(missing):
        enriched[f"missing{i}"] = _enriched(None)
    return asdict(summarize_fact_pack_freshness(enriched))


def _cost(*, priced: bool = True, crew: str = "deep_analysis_stock") -> dict[str, Any]:
    """The dict ``_log_post_flow_summaries`` puts on state: a real monitor's own summary."""
    monitor = TokenMonitorCallback()
    monitor.record_usage(crew, SimpleNamespace(prompt_tokens=200, completion_tokens=100, successful_requests=3), model="openai/gpt-4o-mini" if priced else None)
    return monitor.get_cost_summary()


def _gap_profile(underperformers: int) -> dict[str, Any]:
    """The dict ``GapProfileOrchestrator`` puts on state: ``PortfolioGapProfile.model_dump()``."""
    profile = PortfolioGapProfile(
        session_id="s",
        underperformer_slots=[UnderperformerSlot(ticker=f"BAD{i}", grade="D") for i in range(underperformers)],
        is_empty=False,
    )
    return profile.model_dump()


def _discover(state: FinwizState, tmp_path: Path, count: int) -> None:
    """Put discovery on state through the orchestrator that puts it there in a run."""
    state.stock_opportunities = [{"ticker": f"OPP{i}", "composite_score": 0.9} for i in range(count)]
    previous = Path.cwd()
    os.chdir(tmp_path)
    try:
        DiscoveryOrchestrator(state).check_investment_discovery()
    finally:
        os.chdir(previous)


def _state(tmp_path: Path, *, discovered: int = 2, **overrides: Any) -> FinwizState:
    """A real ``FinwizState`` carrying what a real run leaves on it. Nominal case: 1/3 stale."""
    state = FinwizState()
    state.run_ledger = _ledger(tmp_path)
    state.portfolio_review = _review(tmp_path, [0.5, 0.3, 0.2])
    state.fact_pack_freshness = _freshness(fresh=2, stale=1)
    state.alternatives_count = 0
    state.portfolio_gap_profile = _gap_profile(underperformers=3)
    state.stress_test_count = 6
    state.llm_cost_summary = _cost()
    _discover(state, tmp_path, discovered)
    for key, value in overrides.items():
        setattr(state, key, value)
    return state


def _healthy(tmp_path: Path, **overrides: Any) -> FinwizState:
    """A run with nothing wrong with it: every check green, verdict PASS."""
    healthy: dict[str, Any] = {
        "fact_pack_freshness": _freshness(fresh=3),
        "alternatives_count": 2,
        "portfolio_gap_profile": _gap_profile(underperformers=1),
    }
    return _state(tmp_path, **(healthy | overrides))


@contextmanager
def _local_timezone(name: str) -> Iterator[None]:
    """``FinwizState.timestamp`` is naive LOCAL wall-clock; the gate's clock is UTC."""
    previous = os.environ.get("TZ")
    os.environ["TZ"] = name
    time.tzset()
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop("TZ", None)
        else:
            os.environ["TZ"] = previous
        time.tzset()


# ---------------------------------------------------------------------------
# Collectors
# ---------------------------------------------------------------------------


class TestCollectors:
    def test_coverage_from_ledger(self, tmp_path) -> None:
        c = coverage_from(_ledger(tmp_path, analyzed=2, total=3))
        assert (c.available, c.analyzed, c.failed, c.total) == (True, 2, 1, 3)

    def test_coverage_from_none_is_unavailable(self) -> None:
        assert coverage_from(None).available is False

    def test_valuation_reads_the_dict_the_flow_puts_on_state(self, tmp_path) -> None:
        """`state.portfolio_review` is a plain dict, not an object with attributes."""
        v = valuation_from(_review(tmp_path, [0.4, 0.6, None]))
        assert (v.available, v.priced, v.total) == (True, 2, 3)

    def test_valuation_uses_the_heros_denominator(self, tmp_path) -> None:
        """Unpriced holdings leave `priced`, never `total` -- the 5.14.1 lesson."""
        v = valuation_from(_review(tmp_path, [0.4, None, None]))
        assert (v.priced, v.total) == (1, 3)

    def test_valuation_accepts_the_model_too(self) -> None:
        """`reporting/` hands both the dict and a validated `PortfolioReview` around."""
        review = PortfolioReview(as_of=MOMENT, holdings=[_holding("A", 0.5), _holding("B", None)])
        v = valuation_from(review)
        assert (v.available, v.priced, v.total) == (True, 1, 2)

    def test_valuation_from_none_is_unavailable(self) -> None:
        assert valuation_from(None).available is False

    def test_fact_pack_from_the_summariser_output(self) -> None:
        f = fact_pack_from(_freshness(fresh=40, recent=6, stale=18))
        assert (f.available, f.stale, f.total) == (True, 18, 64)

    def test_fact_pack_from_none_is_unavailable(self) -> None:
        assert fact_pack_from(None).available is False

    def test_phases_read_the_field_discovery_actually_writes(self, tmp_path) -> None:
        """Discovery consolidates onto `all_discovery_opportunities`; nothing writes `investment_discovery_result`."""
        p = phases_from(_state(tmp_path, discovered=2))
        assert (p.discovery_candidates, p.alternatives_found, p.underperformers, p.stress_scenarios, p.optimal_allocation) == (2, 0, 3, 6, False)

    def test_phases_treat_a_discovery_that_never_ran_as_zero(self, tmp_path) -> None:
        state = _state(tmp_path, discovered=0)
        assert phases_from(state).discovery_candidates == 0
        assert phases_from(FinwizState()).discovery_candidates == 0

    def test_cost_lists_every_unpriced_crew(self) -> None:
        summary = _cost(priced=False, crew="deep_analysis_stock")
        summary["per_crew"].update(_cost(priced=False, crew="deep_analysis_etf")["per_crew"])
        summary["per_crew"].update(_cost(crew="deep_analysis_crypto")["per_crew"])
        c = cost_from(summary)
        assert (c.available, c.cost_known, c.unpriced_crews) == (True, False, ["deep_analysis_etf", "deep_analysis_stock"])

    def test_cost_from_none_is_unavailable(self) -> None:
        assert cost_from(None).available is False

    def test_cost_from_a_run_that_measured_nothing_is_unavailable(self) -> None:
        """`get_cost_summary()` returns a populated dict even when it recorded nothing.

        An unmeasured run is not proof of zero usage -- `log_cost_summary`'s own
        docstring says so -- and $0.00 over 0 calls must never read as fine.
        """
        nothing_measured = TokenMonitorCallback().get_cost_summary()
        assert nothing_measured == {"total_cost": 0.0, "call_count": 0, "per_crew": {}}
        assert cost_from(nothing_measured).available is False

    def test_cost_from_a_measured_run_is_available(self) -> None:
        c = cost_from(_cost())
        assert (c.available, c.cost_known, c.call_count) == (True, True, 3)
        assert c.total_usd > 0.0


# ---------------------------------------------------------------------------
# The run
# ---------------------------------------------------------------------------


class TestRun:
    def test_writes_json_logs_block_and_sets_state(self, tmp_path, caplog) -> None:
        state = _state(tmp_path)
        output = tmp_path / "output"
        with caplog.at_level(logging.INFO):
            summary = RunGateOrchestrator(state, output_dir=output, thresholds=RunGateSettings()).run()

        assert summary is not None and summary.verdict is Verdict.FAIL  # 1/3 stale = 33% > 25%
        assert state.gate_verdict == "FAIL"
        assert state.run_summary == summary.model_dump(mode="json")

        written = RunSummary.model_validate_json((output / "run_summary.json").read_text())
        assert written == summary
        assert (output / "run_ledger" / "run-abc.summary.json").exists()

        lines = [r.message for r in caplog.records if r.message.startswith("run gate: ")]
        assert len(lines) == 9
        assert lines[-1].startswith("run gate: verdict FAIL")

    def test_a_healthy_run_passes(self, tmp_path, caplog) -> None:
        """The case the branch never had: every check green, verdict PASS, exit 0."""
        state = _healthy(tmp_path)
        with caplog.at_level(logging.INFO):
            summary = RunGateOrchestrator(state, output_dir=tmp_path / "output", thresholds=RunGateSettings()).run()

        assert summary is not None
        assert [c.name for c in summary.checks if not c.passed] == []
        assert summary.verdict is Verdict.PASS
        assert state.gate_verdict == "PASS"
        assert exit_code_for(state.gate_verdict) == 0
        assert RunSummary.model_validate_json((tmp_path / "output" / "run_summary.json").read_text()) == summary
        assert [r.message for r in caplog.records if r.message.startswith("run gate: verdict")] == [f"run gate: verdict PASS — {tmp_path / 'output' / 'run_summary.json'}"]

    def test_a_known_gap_warns_and_still_exits_zero(self, tmp_path) -> None:
        """One failed WARN-severity check, every FAIL-severity check green."""
        summary = RunGateOrchestrator(_healthy(tmp_path, stress_test_count=0), output_dir=tmp_path / "output", thresholds=RunGateSettings()).run()

        assert summary is not None
        assert [c.name for c in summary.checks if not c.passed] == ["stress_tests"]
        assert summary.verdict is Verdict.WARN
        assert exit_code_for(summary.verdict) == 0

    def test_an_unpriced_crew_fails_the_otherwise_healthy_run(self, tmp_path) -> None:
        summary = RunGateOrchestrator(_healthy(tmp_path, llm_cost_summary=_cost(priced=False)), output_dir=tmp_path / "output", thresholds=RunGateSettings()).run()

        assert summary is not None
        assert [c.name for c in summary.checks if not c.passed] == ["cost_known"]
        assert summary.verdict is Verdict.FAIL
        assert exit_code_for(summary.verdict) == 1

    @pytest.mark.parametrize("tz", ["Europe/Paris", "UTC", "America/New_York", "Asia/Tokyo"])
    def test_duration_is_measured_on_one_clock(self, tmp_path, tz) -> None:
        """`state.timestamp` is naive local; `finished` is UTC. Subtracting them raw is negative east of UTC.

        A negative duration violates `RunSummary.duration_seconds` (ge=0.0), which
        means no summary file at all -- the gate destroyed by its own arithmetic.
        """
        with _local_timezone(tz):
            state = _healthy(tmp_path)  # FinwizState() stamps its timestamp in local time, like a real run
            summary = RunGateOrchestrator(state, output_dir=tmp_path / "output", thresholds=RunGateSettings()).run()

        assert summary is not None, f"the gate must produce a summary under TZ={tz}"
        assert summary.duration_seconds is not None
        assert 0 <= summary.duration_seconds < 600
        assert (tmp_path / "output" / "run_summary.json").exists()

    def test_an_impossible_duration_does_not_destroy_the_summary(self, tmp_path, caplog) -> None:
        """A clock that moved backwards makes duration unknown -- it does not cost us the verdict."""
        state = _healthy(tmp_path)
        with caplog.at_level(logging.WARNING):
            summary = RunGateOrchestrator(state, output_dir=tmp_path / "output", thresholds=RunGateSettings(), now=lambda: MOMENT - timedelta(days=365)).run()

        assert summary is not None and summary.verdict is Verdict.PASS
        assert summary.duration_seconds is None
        assert any("duration" in r.message for r in caplog.records if r.levelno >= logging.WARNING)

    def test_a_collector_raising_yields_error_not_an_exception(self, tmp_path, caplog, mocker) -> None:
        mocker.patch("finwiz.orchestrators.run_gate_orchestrator.coverage_from", side_effect=RuntimeError("ledger exploded"))
        state = _state(tmp_path)

        with caplog.at_level(logging.ERROR):
            result = RunGateOrchestrator(state, output_dir=tmp_path / "output").run()

        assert result is None
        assert state.gate_verdict == "ERROR"
        failures = [r for r in caplog.records if "run gate" in r.message.lower() and r.levelno >= logging.ERROR]
        assert failures and failures[0].exc_info is not None, "the gate's own failure must keep its traceback"

    def test_unavailable_inputs_still_produce_a_summary(self, tmp_path) -> None:
        state = _state(tmp_path, run_ledger=None, llm_cost_summary=None, fact_pack_freshness=None, portfolio_review=None)
        summary = RunGateOrchestrator(state, output_dir=tmp_path / "output").run()
        assert summary is not None and summary.verdict is Verdict.FAIL
        assert [c.name for c in summary.checks if c.detail == "not measured"] == ["coverage", "valuation", "cost_known", "fact_pack_stale", "fact_pack_missing"]
