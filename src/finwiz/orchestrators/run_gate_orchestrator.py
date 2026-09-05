"""Orchestrator for the run gate -- the flow's last act.

Collects what the run already knows about itself from state, evaluates it
through ``analysis/run_gate.py``, writes ``output/run_summary.json`` and a
dated copy beside the ledger, logs one line per check, and leaves the verdict
on state for ``core/app_initializer.py`` to turn into an exit code.

Never raises. The report was written before this ran; a failure here is
recorded as verdict ERROR (exit 2), with its traceback, and the run ends.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from finwiz.analysis.run_gate import evaluate, format_block, verdict
from finwiz.config.settings import RunGateSettings, get_settings
from finwiz.infrastructure.time.datetime_utils import assume_local_aware
from finwiz.schemas.run_summary import CostInput, CoverageInput, FactPackInput, PhasesInput, RunSummary, ValuationInput, Verdict
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)

_STATE_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"  # FinwizState.timestamp


def coverage_from(ledger: Any) -> CoverageInput:
    """Read coverage off the run ledger. ``None`` -- no ledger -- is unavailable, not zero."""
    if ledger is None:
        return CoverageInput()
    c = ledger.coverage()
    return CoverageInput(available=True, analyzed=c.analyzed, degraded=c.degraded, failed=c.failed, total=c.total)


def valuation_from(portfolio_review: Any) -> ValuationInput:
    """Priced = ``weight is not None`` -- the same set the allocation hero counts.

    ``state.portfolio_review`` is a plain dict: ``validation_orchestrator`` sets it
    to ``json.loads`` of the review file. A validated ``PortfolioReview`` is read
    too, because ``reporting/`` hands both shapes around.
    """
    holdings = _field(portfolio_review, "holdings")
    if not isinstance(holdings, list):
        return ValuationInput()
    return ValuationInput(available=True, priced=sum(1 for h in holdings if _field(h, "weight") is not None), total=len(holdings))


def _field(obj: Any, name: str) -> Any:
    """Read one field off either shape the review reaches state in."""
    return obj.get(name) if isinstance(obj, dict) else getattr(obj, name, None)


def fact_pack_from(freshness: dict[str, Any] | None) -> FactPackInput:
    """Read the persisted freshness summary. Missing or empty is unavailable, not zero."""
    if not freshness:
        return FactPackInput()
    return FactPackInput(
        available=True,
        **{k: freshness.get(k, 0) for k in ("fresh", "recent", "stale", "missing", "total")},
        oldest_stale_fetched_at=freshness.get("oldest_stale_fetched_at"),
    )


def phases_from(state: Any) -> PhasesInput:
    """Read the phase-outcome counts the roadmap tracks as known gaps. An absent phase result is honestly a zero."""
    # discovery_orchestrator.py consolidates every asset class onto
    # `all_discovery_opportunities`; `investment_discovery_result` is declared on
    # the state model but has no writer anywhere under src/, so reading it counted
    # a healthy discovery as zero and WARNed on it forever.
    opportunities = getattr(state, "all_discovery_opportunities", None)
    gap_profile = getattr(state, "portfolio_gap_profile", None) or {}
    return PhasesInput(
        discovery_candidates=len(opportunities) if isinstance(opportunities, list) else 0,
        alternatives_found=int(getattr(state, "alternatives_count", 0) or 0),
        underperformers=len(gap_profile.get("underperformer_slots") or []),
        stress_scenarios=int(getattr(state, "stress_test_count", 0) or 0),
        optimal_allocation=getattr(state, "optimal_allocation", None) is not None,
    )


def cost_from(summary: dict[str, Any] | None) -> CostInput:
    """Read the cost monitor's summary. Any crew missing ``cost_known`` makes the whole total untrusted.

    ``get_cost_summary()`` returns a populated dict even when it recorded
    nothing, and a run that measured nothing is not proof of zero usage --
    ``log_cost_summary`` refuses to claim "No LLM calls made" for exactly this
    reason. The two are indistinguishable from the callback's data, so an
    unmeasured run is unavailable, and its check FAILs as "not measured". A
    false FAIL is recoverable; "$0.00 over 0 calls -- PASS" is the defect this
    gate exists to catch.
    """
    if not summary:
        return CostInput()
    per_crew = summary.get("per_crew") or {}
    if not per_crew and not int(summary.get("call_count") or 0):
        return CostInput()
    unpriced = sorted(name for name, entry in per_crew.items() if not entry.get("cost_known", True))
    return CostInput(
        available=True,
        total_usd=float(summary.get("total_cost") or 0.0),
        call_count=int(summary.get("call_count") or 0),
        cost_known=not unpriced,
        unpriced_crews=unpriced,
    )


class RunGateOrchestrator:
    """Evaluates the finished run and records the verdict. See module docstring."""

    def __init__(
        self,
        state: Any,
        output_dir: Path = Path("output"),
        thresholds: RunGateSettings | None = None,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self.state = state
        self.output_dir = output_dir
        self.thresholds = thresholds
        self._now = now or (lambda: datetime.now(UTC))

    def run(self) -> RunSummary | None:
        try:
            summary = self._evaluate()
            self._write(summary)
            for line in format_block(summary.checks, summary.verdict, str(self.output_dir / "run_summary.json")):
                logger.info(line)
            self.state.run_summary = summary.model_dump(mode="json")
            self.state.gate_verdict = summary.verdict.value
            return summary
        except Exception:
            # The report is already written. Record that we could not judge it --
            # with the traceback, or the next person cannot either.
            logger.exception("run gate could not evaluate this run; verdict ERROR")
            self.state.gate_verdict = Verdict.ERROR.value
            return None

    def _evaluate(self) -> RunSummary:
        thresholds = self.thresholds or get_settings().gate
        coverage = coverage_from(getattr(self.state, "run_ledger", None))
        valuation = valuation_from(getattr(self.state, "portfolio_review", None))
        fact_pack = fact_pack_from(getattr(self.state, "fact_pack_freshness", None))
        phases = phases_from(self.state)
        cost = cost_from(getattr(self.state, "llm_cost_summary", None))
        checks = evaluate(coverage, valuation, fact_pack, phases, cost, thresholds)

        finished = assume_local_aware(self._now())
        started = self._started_at()
        ledger = getattr(self.state, "run_ledger", None)
        return RunSummary(
            run_id=getattr(ledger, "run_id", None) or str(getattr(self.state, "id", "unknown")),
            started_at=started,
            finished_at=finished,
            duration_seconds=self._duration(started, finished),
            coverage=coverage,
            valuation=valuation,
            fact_pack=fact_pack,
            phases=phases,
            cost=cost,
            checks=checks,
            verdict=verdict(checks),
        )

    def _started_at(self) -> datetime | None:
        """``state.timestamp`` is naive LOCAL wall-clock (``flow_state_models.py`` stamps it with ``datetime.now()``)."""
        raw = getattr(self.state, "timestamp", None)
        try:
            return assume_local_aware(datetime.strptime(raw, _STATE_TIMESTAMP_FORMAT)) if raw else None
        except ValueError:
            return None

    def _duration(self, started: datetime | None, finished: datetime) -> float | None:
        """Elapsed seconds between two instants, or ``None`` when there is no honest answer.

        Both ends are timezone-aware by the time they get here, so a negative
        result means the clock itself moved (an NTP step, a hand-edited
        timestamp). Duration is informational -- no check reads it -- so an
        impossible one is recorded as unknown rather than allowed to fail
        ``RunSummary``'s ``ge=0.0`` and take the whole summary down with it.
        """
        if started is None:
            return None
        elapsed = (finished - started).total_seconds()
        if elapsed < 0:
            # Not prefixed "run gate: " -- that prefix belongs to the verdict block, one line per check.
            logger.warning(f"run gate could not measure duration: {elapsed:.1f}s between {started.isoformat()} and {finished.isoformat()}; recorded as unknown")
            return None
        return elapsed

    def _write(self, summary: RunSummary) -> None:
        payload = summary.model_dump_json(indent=2)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "run_summary.json").write_text(payload)
        dated = self.output_dir / "run_ledger"
        dated.mkdir(parents=True, exist_ok=True)
        (dated / f"{summary.run_id}.summary.json").write_text(payload)
