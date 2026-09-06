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
    # Both fact-pack checks read one denominator, so they cannot disagree about
    # whether there were any fact packs to look at.
    fact_pack_measured = fact_pack.available and fact_pack.total > 0
    return [
        _coverage(coverage, thresholds.min_coverage_ratio),
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
        _alternatives(phases),
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
            passed=fact_pack_measured and fact_pack.missing == 0,
            observed=f"{fact_pack.missing} missing" if fact_pack_measured else NOT_MEASURED,
            threshold="= 0",
            detail="" if fact_pack_measured else NOT_MEASURED,
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


def _coverage(coverage: CoverageInput, minimum: float) -> GateCheck:
    """Every holding that produced a verdict counts, degraded ones included.

    ``CoverageInput.analyzed`` is the ledger's ``analyzed_clean``: degraded
    holdings are subtracted from it by construction (``stages/_ledger.py``).
    Dividing by it alone FAILed runs in which every holding produced a verdict
    -- the always-red gate the design forbids -- and reported ``failed: 0``
    beside the failure. A degraded holding is amber, not absent; it counts.

    ``failed`` is shown derived rather than read, so the summary cannot carry
    two spellings of one fact.
    """
    threshold = f"min {minimum:.1%}"
    if not coverage.available or coverage.total == 0:
        return GateCheck(name="coverage", severity=Severity.FAIL, passed=False, observed=NOT_MEASURED, threshold=threshold, detail=NOT_MEASURED)
    with_verdict = coverage.analyzed + coverage.degraded
    composition = f"{coverage.analyzed} clean + {coverage.degraded} degraded, {coverage.total - with_verdict} failed"
    return GateCheck(
        name="coverage",
        severity=Severity.FAIL,
        passed=with_verdict / coverage.total >= minimum,
        observed=f"{with_verdict}/{coverage.total} analysed = {with_verdict / coverage.total:.1%} ({composition})",
        threshold=threshold,
    )


def _alternatives(phases: PhasesInput) -> GateCheck:
    """Two different facts: nobody needs replacing, and the gap profile was never built.

    Phase 3.6 fail-softs to an empty profile, which reads as zero
    underperformers -- and zero underperformers satisfies this check whether or
    not matching ran. A gate that skips a check when the data is missing is a
    gate that is passed by breaking the data.
    """
    threshold = "> 0 when there are underperformers"
    if not phases.underperformers_available:
        return GateCheck(name="alternatives", severity=Severity.WARN, passed=False, observed=NOT_MEASURED, threshold=threshold, detail=NOT_MEASURED)
    return GateCheck(
        name="alternatives",
        severity=Severity.WARN,
        passed=phases.alternatives_found > 0 or phases.underperformers == 0,
        observed=f"{phases.alternatives_found} found for {phases.underperformers} underperformers",
        threshold=threshold,
    )


def _ratio_at_least(name: str, available: bool, part: int, total: int, minimum: float, noun: str) -> GateCheck:
    threshold = f"min {minimum:.1%}"
    if not available or total == 0:
        return GateCheck(name=name, severity=Severity.FAIL, passed=False, observed=NOT_MEASURED, threshold=threshold, detail=NOT_MEASURED)
    return GateCheck(name=name, severity=Severity.FAIL, passed=part / total >= minimum, observed=f"{part}/{total} {noun} = {part / total:.1%}", threshold=threshold)


def _ratio_at_most(name: str, available: bool, part: int, total: int, maximum: float, noun: str) -> GateCheck:
    """One decimal, both directions: at ``:.0%`` a failing 25.2 % logged as "= 25% (max 25%)"."""
    threshold = f"max {maximum:.1%}"
    if not available or total == 0:
        return GateCheck(name=name, severity=Severity.FAIL, passed=False, observed=NOT_MEASURED, threshold=threshold, detail=NOT_MEASURED)
    return GateCheck(name=name, severity=Severity.FAIL, passed=part / total <= maximum, observed=f"{part}/{total} {noun} = {part / total:.1%}", threshold=threshold)


def _cost_known(cost: CostInput) -> GateCheck:
    """``cost_known`` is read, not inferred from ``unpriced_crews``.

    Live runs derive one from the other, so they agree. ``make gate`` re-judges
    stored files, where they need not: a summary carrying ``cost_known: false``
    with an empty crew list used to pass as "$0.00 over 5 calls".
    """
    threshold = "every crew priced"
    if not cost.available:
        return GateCheck(name="cost_known", severity=Severity.FAIL, passed=False, observed=NOT_MEASURED, threshold=threshold, detail=NOT_MEASURED)
    if cost.unpriced_crews:
        n = len(cost.unpriced_crews)
        return GateCheck(
            name="cost_known",
            severity=Severity.FAIL,
            passed=False,
            observed=f"{n} crew{'s' if n > 1 else ''} unpriced: {', '.join(cost.unpriced_crews)}",
            threshold=threshold,
        )
    if not cost.cost_known:
        return GateCheck(
            name="cost_known",
            severity=Severity.FAIL,
            passed=False,
            observed=f"total untrusted over {cost.call_count} calls, no crew named",
            threshold=threshold,
            detail="the summary reports its own total as unknown",
        )
    return GateCheck(name="cost_known", severity=Severity.FAIL, passed=True, observed=f"${cost.total_usd:.2f} over {cost.call_count} calls", threshold=threshold)
