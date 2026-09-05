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
    """Priced = ``weight is not None`` -- the same set the allocation hero counts."""
    holdings = getattr(portfolio_review, "holdings", None)
    if holdings is None:
        return ValuationInput()
    return ValuationInput(available=True, priced=sum(1 for h in holdings if getattr(h, "weight", None) is not None), total=len(holdings))


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
    discovery = getattr(state, "investment_discovery_result", None) or {}
    opportunities = discovery.get("opportunities") if isinstance(discovery, dict) else None
    gap_profile = getattr(state, "portfolio_gap_profile", None) or {}
    return PhasesInput(
        discovery_candidates=len(opportunities) if isinstance(opportunities, list) else 0,
        alternatives_found=int(getattr(state, "alternatives_count", 0) or 0),
        underperformers=len(gap_profile.get("underperformer_slots") or []),
        stress_scenarios=int(getattr(state, "stress_test_count", 0) or 0),
        optimal_allocation=getattr(state, "optimal_allocation", None) is not None,
    )


def cost_from(summary: dict[str, Any] | None) -> CostInput:
    """Read the cost monitor's summary. Any crew missing ``cost_known`` makes the whole total untrusted."""
    if not summary:
        return CostInput()
    per_crew = summary.get("per_crew") or {}
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

        finished = self._now()
        started = self._started_at()
        ledger = getattr(self.state, "run_ledger", None)
        return RunSummary(
            run_id=getattr(ledger, "run_id", None) or str(getattr(self.state, "id", "unknown")),
            started_at=started,
            finished_at=finished,
            duration_seconds=(finished.replace(tzinfo=None) - started).total_seconds() if started else None,
            coverage=coverage,
            valuation=valuation,
            fact_pack=fact_pack,
            phases=phases,
            cost=cost,
            checks=checks,
            verdict=verdict(checks),
        )

    def _started_at(self) -> datetime | None:
        raw = getattr(self.state, "timestamp", None)
        try:
            return datetime.strptime(raw, _STATE_TIMESTAMP_FORMAT) if raw else None
        except ValueError:
            return None

    def _write(self, summary: RunSummary) -> None:
        payload = summary.model_dump_json(indent=2)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "run_summary.json").write_text(payload)
        dated = self.output_dir / "run_ledger"
        dated.mkdir(parents=True, exist_ok=True)
        (dated / f"{summary.run_id}.summary.json").write_text(payload)
