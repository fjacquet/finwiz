"""`make gate` re-evaluates an existing run_summary.json against current thresholds."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "scripts"))

from run_gate import main

from finwiz.config.settings import reset_settings

REPO_SCRIPT = Path(__file__).parent.parent.parent.parent / "scripts" / "run_gate.py"


@pytest.fixture(autouse=True)
def _fresh_settings():
    reset_settings()
    yield
    reset_settings()


def _summary_json(stale: int = 18) -> dict:
    return {
        "run_id": "run-abc",
        "started_at": "2026-09-05T09:04:46",
        "finished_at": "2026-09-05T09:28:09",
        "duration_seconds": 1403.0,
        "coverage": {"available": True, "analyzed": 64, "degraded": 0, "failed": 0, "total": 64},
        "valuation": {"available": True, "priced": 63, "total": 64},
        "fact_pack": {"available": True, "fresh": 64 - stale, "recent": 0, "stale": stale, "missing": 0, "total": 64, "oldest_stale_fetched_at": None},
        "phases": {"discovery_candidates": 3, "alternatives_found": 2, "underperformers": 17, "stress_scenarios": 6, "optimal_allocation": False},
        "cost": {"available": True, "total_usd": 0.51, "call_count": 68, "cost_known": True, "unpriced_crews": []},
        "checks": [],
        "verdict": "PASS",  # deliberately wrong: the script must re-evaluate, not trust this
    }


class TestRunGateScript:
    def test_reevaluates_rather_than_trusting_the_stored_verdict(self, tmp_path, capsys) -> None:
        p = tmp_path / "run_summary.json"
        p.write_text(json.dumps(_summary_json(stale=18)))

        code = main([str(p)])

        out = capsys.readouterr().out
        assert code == 1
        assert "run gate: verdict FAIL" in out

    def test_a_changed_threshold_changes_the_verdict(self, tmp_path, monkeypatch) -> None:
        p = tmp_path / "run_summary.json"
        p.write_text(json.dumps(_summary_json(stale=18)))
        monkeypatch.setenv("FINWIZ_GATE__MAX_STALE_RATIO", "0.30")
        reset_settings()

        assert main([str(p)]) == 0

    def test_missing_file_is_exit_2(self, tmp_path) -> None:
        assert main([str(tmp_path / "nope.json")]) == 2

    def test_script_never_imports_the_flow(self) -> None:
        source = REPO_SCRIPT.read_text()
        assert "finwiz.flows" not in source
        assert "finwiz.orchestrators" not in source


class TestABadThresholdIsCouldNotEvaluate:
    """`make gate` exists so a threshold can be changed and the effect seen. The typo it invites must not read as FAIL."""

    def test_an_out_of_range_threshold_exits_2(self, tmp_path, monkeypatch, capsys) -> None:
        p = tmp_path / "run_summary.json"
        p.write_text(json.dumps(_summary_json(stale=0)))
        monkeypatch.setenv("FINWIZ_GATE__MAX_STALE_RATIO", "1.5")
        reset_settings()

        code = main([str(p)])

        assert code == 2
        assert "run gate" in capsys.readouterr().err

    def test_an_unparseable_threshold_exits_2(self, tmp_path, monkeypatch) -> None:
        p = tmp_path / "run_summary.json"
        p.write_text(json.dumps(_summary_json(stale=0)))
        monkeypatch.setenv("FINWIZ_GATE__MIN_COVERAGE_RATIO", "not-a-number")
        reset_settings()

        assert main([str(p)]) == 2
