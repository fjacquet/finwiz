"""The run gate, as a pure function.

Five measured inputs and a set of thresholds go in; eight checks and a verdict
come out. Nothing here reads state, touches the disk or consults a clock, so a
test needs five small models and nothing else.

Severity is decided here, in code. FAIL means the report is not trustworthy --
coverage, valuation, cost visibility, fact-pack freshness. WARN means a gap the
roadmap already tracks is still a gap -- discovery, alternatives, stress tests.
A gate that FAILs on the known gaps is red from its first run until they are
closed, and a gate that is always red is the mechanism by which Requirement 9.2
became noise.

A check whose input is unavailable FAILs as "not measured". It is never
skipped: a gate that skips a check when the data is missing is a gate that is
passed by breaking the data.
"""

from __future__ import annotations

from finwiz.config.settings import RunGateSettings
from finwiz.schemas.run_summary import CostInput, CoverageInput, FactPackInput, GateCheck, PhasesInput, Severity, ValuationInput, Verdict

NOT_MEASURED = "not measured"

_EXIT_CODES: dict[Verdict, int] = {Verdict.PASS: 0, Verdict.WARN: 0, Verdict.FAIL: 1, Verdict.ERROR: 2}


def evaluate(
    coverage: CoverageInput,
    valuation: ValuationInput,
    fact_pack: FactPackInput,
    phases: PhasesInput,
    cost: CostInput,
    thresholds: RunGateSettings,
) -> list[GateCheck]:
    """Return the eight checks, always all of them, always in this order."""
    return [
        _ratio_at_least("coverage", coverage.available, coverage.analyzed, coverage.total, thresholds.min_coverage_ratio, "analysed"),
        _ratio_at_least("valuation", valuation.available, valuation.priced, valuation.total, thresholds.min_priced_ratio, "priced"),
        _cost_known(cost),
        _ratio_at_most("fact_pack_stale", fact_pack.available, fact_pack.stale, fact_pack.total, thresholds.max_stale_ratio, "stale"),
        GateCheck(
            name="discovery",
            severity=Severity.WARN,
            passed=phases.discovery_candidates > 0,
            observed=f"{phases.discovery_candidates} candidates",
            threshold="> 0",
        ),
        GateCheck(
            name="alternatives",
            severity=Severity.WARN,
            passed=phases.alternatives_found > 0 or phases.underperformers == 0,
            observed=f"{phases.alternatives_found} found for {phases.underperformers} underperformers",
            threshold="> 0 when there are underperformers",
        ),
        GateCheck(
            name="stress_tests",
            severity=Severity.WARN,
            passed=phases.stress_scenarios > 0,
            observed=f"{phases.stress_scenarios} scenarios",
            threshold="> 0",
        ),
        GateCheck(
            name="fact_pack_missing",
            severity=Severity.WARN,
            passed=fact_pack.available and fact_pack.missing == 0,
            observed=f"{fact_pack.missing} missing" if fact_pack.available else NOT_MEASURED,
            threshold="= 0",
            detail="" if fact_pack.available else NOT_MEASURED,
        ),
    ]


def verdict(checks: list[GateCheck]) -> Verdict:
    """Any failed FAIL → FAIL; else any failed WARN → WARN; else PASS. WARNs never escalate."""
    failed = [c for c in checks if not c.passed]
    if any(c.severity is Severity.FAIL for c in failed):
        return Verdict.FAIL
    if failed:
        return Verdict.WARN
    return Verdict.PASS


def exit_code_for(v: Verdict | str | None) -> int:
    """PASS/WARN → 0, FAIL → 1, anything else -- ERROR, None, unknown -- → 2.

    None means the gate never ran. "Nothing to report" and "I did not look" must
    never share an exit code.
    """
    try:
        return _EXIT_CODES[Verdict(v)] if v is not None else 2
    except ValueError:
        return 2


def format_block(checks: list[GateCheck], v: Verdict, summary_path: str) -> list[str]:
    """One grep-able line per check, the verdict last."""
    width = max(len(c.name) for c in checks) if checks else 0
    lines = [f"run gate: {c.name:<{width}} {'PASS' if c.passed else c.severity.value:<5} {c.observed} ({c.threshold})" for c in checks]
    lines.append(f"run gate: verdict {v.value} — {summary_path}")
    return lines


def _ratio_at_least(name: str, available: bool, part: int, total: int, minimum: float, noun: str) -> GateCheck:
    if not available or total == 0:
        return GateCheck(name=name, severity=Severity.FAIL, passed=False, observed=NOT_MEASURED, threshold=f"min {minimum:.0%}", detail=NOT_MEASURED)
    return GateCheck(name=name, severity=Severity.FAIL, passed=part / total >= minimum, observed=f"{part}/{total} {noun}", threshold=f"min {minimum:.0%}")


def _ratio_at_most(name: str, available: bool, part: int, total: int, maximum: float, noun: str) -> GateCheck:
    if not available or total == 0:
        return GateCheck(name=name, severity=Severity.FAIL, passed=False, observed=NOT_MEASURED, threshold=f"max {maximum:.0%}", detail=NOT_MEASURED)
    return GateCheck(name=name, severity=Severity.FAIL, passed=part / total <= maximum, observed=f"{part}/{total} {noun} = {part / total:.0%}", threshold=f"max {maximum:.0%}")


def _cost_known(cost: CostInput) -> GateCheck:
    if not cost.available:
        return GateCheck(name="cost_known", severity=Severity.FAIL, passed=False, observed=NOT_MEASURED, threshold="every crew priced", detail=NOT_MEASURED)
    if cost.unpriced_crews:
        n = len(cost.unpriced_crews)
        return GateCheck(
            name="cost_known",
            severity=Severity.FAIL,
            passed=False,
            observed=f"{n} crew{'s' if n > 1 else ''} unpriced: {', '.join(cost.unpriced_crews)}",
            threshold="every crew priced",
        )
    return GateCheck(name="cost_known", severity=Severity.FAIL, passed=True, observed=f"${cost.total_usd:.2f} over {cost.call_count} calls", threshold="every crew priced")
