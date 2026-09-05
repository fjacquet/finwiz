"""The gate is a pure function: numbers in, checks and a verdict out."""

from __future__ import annotations

import pytest

from finwiz.analysis.run_gate import NOT_MEASURED, evaluate, exit_code_for, format_block, verdict
from finwiz.config.settings import RunGateSettings
from finwiz.schemas.run_summary import CostInput, CoverageInput, FactPackInput, GateCheck, PhasesInput, Severity, ValuationInput, Verdict

T = RunGateSettings()


def _run_2026_09_05() -> dict:
    """The measured values of the run that motivated the gate."""
    return {
        "coverage": CoverageInput(available=True, analyzed=64, degraded=0, failed=0, total=64),
        "valuation": ValuationInput(available=True, priced=63, total=64),
        "fact_pack": FactPackInput(available=True, fresh=40, recent=6, stale=18, missing=0, total=64),
        "phases": PhasesInput(discovery_candidates=0, alternatives_found=0, underperformers=17, stress_scenarios=6),
        "cost": CostInput(available=True, total_usd=0.0, call_count=2080, cost_known=False, unpriced_crews=["deep_analysis_crypto", "deep_analysis_etf", "deep_analysis_stock"]),
    }


def _by_name(checks: list[GateCheck]) -> dict[str, GateCheck]:
    return {c.name: c for c in checks}


class TestTheMotivatingRun:
    def test_verdict_is_fail_for_the_right_reasons(self) -> None:
        checks = evaluate(**_run_2026_09_05(), thresholds=T)
        by = _by_name(checks)
        assert by["coverage"].passed and by["valuation"].passed and by["stress_tests"].passed and by["fact_pack_missing"].passed
        assert not by["cost_known"].passed and by["cost_known"].severity is Severity.FAIL
        assert not by["fact_pack_stale"].passed and by["fact_pack_stale"].severity is Severity.FAIL
        assert not by["discovery"].passed and by["discovery"].severity is Severity.WARN
        assert not by["alternatives"].passed and by["alternatives"].severity is Severity.WARN
        assert verdict(checks) is Verdict.FAIL

    def test_eight_checks_always_present_in_stable_order(self) -> None:
        names = [c.name for c in evaluate(**_run_2026_09_05(), thresholds=T)]
        assert names == ["coverage", "valuation", "cost_known", "fact_pack_stale", "discovery", "alternatives", "stress_tests", "fact_pack_missing"]


class TestThresholdsBothSides:
    @pytest.mark.parametrize(("analyzed", "passed"), [(64, True), (61, True), (60, False)])  # 61/64 = 95.3%, 60/64 = 93.75%
    def test_coverage(self, analyzed: int, passed: bool) -> None:
        d = _run_2026_09_05() | {"coverage": CoverageInput(available=True, analyzed=analyzed, total=64)}
        assert _by_name(evaluate(**d, thresholds=T))["coverage"].passed is passed

    @pytest.mark.parametrize(("priced", "passed"), [(64, True), (61, True), (60, False)])
    def test_valuation(self, priced: int, passed: bool) -> None:
        d = _run_2026_09_05() | {"valuation": ValuationInput(available=True, priced=priced, total=64)}
        assert _by_name(evaluate(**d, thresholds=T))["valuation"].passed is passed

    @pytest.mark.parametrize(("stale", "passed"), [(0, True), (16, True), (17, False)])  # 16/64 = 25% exactly passes; 17/64 fails
    def test_stale_ratio_boundary_is_inclusive(self, stale: int, passed: bool) -> None:
        d = _run_2026_09_05() | {"fact_pack": FactPackInput(available=True, fresh=64 - stale, stale=stale, total=64)}
        assert _by_name(evaluate(**d, thresholds=T))["fact_pack_stale"].passed is passed

    def test_a_changed_threshold_changes_the_outcome(self) -> None:
        loose = RunGateSettings(max_stale_ratio=0.30)
        assert _by_name(evaluate(**_run_2026_09_05(), thresholds=loose))["fact_pack_stale"].passed is True

    def test_alternatives_pass_when_there_is_nobody_to_replace(self) -> None:
        d = _run_2026_09_05() | {"phases": PhasesInput(alternatives_found=0, underperformers=0, stress_scenarios=6)}
        assert _by_name(evaluate(**d, thresholds=T))["alternatives"].passed is True

    def test_cost_known_passes_only_with_no_unpriced_crew(self) -> None:
        d = _run_2026_09_05() | {"cost": CostInput(available=True, total_usd=0.51, call_count=68, cost_known=True, unpriced_crews=[])}
        assert _by_name(evaluate(**d, thresholds=T))["cost_known"].passed is True


class TestNotMeasuredIsAFailNotASkip:
    @pytest.mark.parametrize(
        ("field", "empty", "check"),
        [
            ("coverage", CoverageInput(), "coverage"),
            ("valuation", ValuationInput(), "valuation"),
            ("fact_pack", FactPackInput(), "fact_pack_stale"),
            ("cost", CostInput(), "cost_known"),
        ],
    )
    def test_unavailable_input_fails_its_check(self, field: str, empty, check: str) -> None:
        d = _run_2026_09_05() | {field: empty}
        c = _by_name(evaluate(**d, thresholds=T))[check]
        assert c.passed is False
        assert c.detail == NOT_MEASURED
        assert c.severity is Severity.FAIL

    def test_zero_total_is_not_measured_either(self) -> None:
        d = _run_2026_09_05() | {"coverage": CoverageInput(available=True, analyzed=0, total=0)}
        assert _by_name(evaluate(**d, thresholds=T))["coverage"].detail == NOT_MEASURED


class TestVerdictAndExitCode:
    def _check(self, sev: Severity, passed: bool) -> GateCheck:
        return GateCheck(name="x", severity=sev, passed=passed, observed="", threshold="")

    def test_fail_beats_warn_beats_pass(self) -> None:
        assert verdict([self._check(Severity.WARN, False), self._check(Severity.FAIL, False)]) is Verdict.FAIL
        assert verdict([self._check(Severity.WARN, False), self._check(Severity.FAIL, True)]) is Verdict.WARN
        assert verdict([self._check(Severity.WARN, True), self._check(Severity.FAIL, True)]) is Verdict.PASS

    def test_three_warns_stay_warn(self) -> None:
        assert verdict([self._check(Severity.WARN, False)] * 3) is Verdict.WARN

    def test_no_checks_is_pass(self) -> None:
        assert verdict([]) is Verdict.PASS

    @pytest.mark.parametrize(("v", "code"), [(Verdict.PASS, 0), (Verdict.WARN, 0), (Verdict.FAIL, 1), (Verdict.ERROR, 2), ("FAIL", 1), (None, 2), ("garbage", 2)])
    def test_exit_codes(self, v, code: int) -> None:
        assert exit_code_for(v) == code


class TestFormatBlock:
    def test_one_line_per_check_then_the_verdict(self) -> None:
        checks = evaluate(**_run_2026_09_05(), thresholds=T)
        lines = format_block(checks, verdict(checks), "output/run_summary.json")
        assert len(lines) == len(checks) + 1
        assert all(line.startswith("run gate: ") for line in lines)
        assert "run gate: fact_pack_stale   FAIL  18/64 stale = 28% (max 25%)" in lines  # name padded to the longest check name, fact_pack_missing
        assert lines[-1] == "run gate: verdict FAIL — output/run_summary.json"
