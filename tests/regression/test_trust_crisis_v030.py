"""Regression test for the v0.3.0 silent-success bug.

Original symptom: AI returned null for 62 of 63 holdings, yet the report rendered
"✅ FinWiz analysis workflow completed successfully" with placeholder grade='D'
and composite_score=0.6 indistinguishable from a real verdict.

Under v5.1, the same scenario must produce DEGRADED outcomes with the amber
"Insight IA indisponible" badge and a red trust banner — never a silent OK.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from finwiz.analysis.stages._ledger import RunLedger
from finwiz.analysis.stages._resilience import StageContext
from finwiz.analysis.stages.qualify import qualify
from finwiz.schemas.hybrid_analysis import QualitativeInsights, QuantitativeAnalysis
from finwiz.schemas.run_ledger import RunLedgerEntry
from finwiz.schemas.stage_contract import StageOutcome

pytestmark = pytest.mark.regression


def test_ai_null_never_emits_silent_ok(tmp_path: Path, mocker: Any) -> None:
    """v0.3.0 regression: when AI returns null, qualify must produce DEGRADED, never silent OK."""
    mocker.patch("finwiz.analysis.stages.qualify._try_ai_qualify", return_value=None)
    mocker.patch(
        "finwiz.analysis.stages.qualify._python_proxy_qualify",
        return_value=QualitativeInsights.model_construct(),
    )
    ctx = StageContext(
        ticker="DELL",
        run_id="r1",
        ledger=RunLedger(run_id="r1", artifact_dir=tmp_path),
        extras={"analysis_ctx": mocker.MagicMock()},
    )
    result = qualify(ctx, QuantitativeAnalysis.model_construct(), {})
    assert result.provenance.outcome == StageOutcome.DEGRADED, f"v0.3.0 regression: AI null must NEVER produce a silent OK — got {result.provenance.outcome}"
    assert result.provenance.fallback_used == "python_proxy_qualitative"


def test_red_banner_when_majority_fail(tmp_path: Path) -> None:
    """A run where 62/63 holdings fail must render a red 'do not decide' banner."""
    ledger = RunLedger(run_id="r1", artifact_dir=tmp_path, total=63)
    now = datetime(2026, 4, 27, tzinfo=UTC)

    def _entry(ticker: str, stage: str, outcome: StageOutcome) -> RunLedgerEntry:
        return RunLedgerEntry(
            run_id="r1",
            ticker=ticker,
            started_at=now,
            finished_at=now,
            stage=stage,  # type: ignore[arg-type]
            outcome=outcome,
        )

    # 1 successful pipeline (AAPL completes through emit)
    for s in ("collect", "quantify", "qualify", "synthesize", "emit"):
        ledger.record(_entry("AAPL", s, StageOutcome.OK))
    # 62 failures at qualify
    for ticker in (f"FAIL{i}" for i in range(62)):
        ledger.record(_entry(ticker, "qualify", StageOutcome.FAILED))

    banner = ledger.to_banner()
    assert banner.state == "red"
    assert banner.block_decisions is True
    assert "NE PAS" in banner.message
