"""Unit tests for the synthesize stage (D4 contract)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from finwiz.analysis.stages._ledger import RunLedger
from finwiz.analysis.stages._resilience import StageContext
from finwiz.analysis.stages.synthesize import synthesize
from finwiz.schemas.hybrid_analysis import EnrichedAnalysis, QualitativeInsights, QuantitativeAnalysis
from finwiz.schemas.stage_contract import StageOutcome


def _make_ctx(tmp_path: Path, mocker: Any) -> StageContext:
    return StageContext(
        ticker="AAPL",
        run_id="r1",
        ledger=RunLedger(run_id="r1", artifact_dir=tmp_path),
        extras={"analysis_ctx": mocker.MagicMock(), "partial_result": mocker.MagicMock()},
    )


def test_synthesize_returns_ok(tmp_path: Path, mocker: Any) -> None:
    fake = EnrichedAnalysis.model_construct()
    mocker.patch(
        "finwiz.analysis.stages.synthesize._synthesize_inner",
        return_value=fake,
    )
    ctx = _make_ctx(tmp_path, mocker)
    result = synthesize(ctx, QuantitativeAnalysis.model_construct(), QualitativeInsights.model_construct(), {})
    assert result.provenance.outcome == StageOutcome.OK
    assert result.payload is fake


def test_synthesize_records_ledger_entry(tmp_path: Path, mocker: Any) -> None:
    mocker.patch(
        "finwiz.analysis.stages.synthesize._synthesize_inner",
        return_value=EnrichedAnalysis.model_construct(),
    )
    ctx = _make_ctx(tmp_path, mocker)
    synthesize(ctx, QuantitativeAnalysis.model_construct(), QualitativeInsights.model_construct(), {})
    assert any(e.stage == "synthesize" for e in ctx.ledger.entries)


def test_synthesize_failure_becomes_failed(tmp_path: Path, mocker: Any) -> None:
    mocker.patch(
        "finwiz.analysis.stages.synthesize._synthesize_inner",
        side_effect=ValueError("synth error"),
    )
    ctx = _make_ctx(tmp_path, mocker)
    result = synthesize(ctx, QuantitativeAnalysis.model_construct(), QualitativeInsights.model_construct(), {})
    assert result.payload is None
    assert result.provenance.outcome == StageOutcome.FAILED
