"""Unit tests for the emit stage (D5 contract)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from finwiz.analysis.stages._ledger import RunLedger
from finwiz.analysis.stages._resilience import StageContext
from finwiz.analysis.stages.emit import _emit_pending, emit
from finwiz.flow_state_models import DeepAnalysisResult
from finwiz.schemas.hybrid_analysis import EnrichedAnalysis
from finwiz.schemas.stage_contract import StageOutcome


def _make_fake_result(ticker: str = "AAPL", grade: str = "A", score: float = 0.9, rec: str = "BUY") -> DeepAnalysisResult:
    return DeepAnalysisResult.model_construct(
        ticker=ticker,
        asset_class="stock",
        crew_name="deep_analysis",
        composite_score=score,
        grade=grade,
        recommendation=rec,
        rationale="test rationale",
        risk_details={},
        fundamental_score=None,
        technical_score=None,
        risk_score=None,
        fundamental_details={},
        technical_details={},
        data_freshness_hours=1.0,
        confidence_level=0.8,
        warnings=[],
        data_quality=None,
        lineage=None,
        cached=False,
        sentiment_score=None,
        sentiment_confidence=None,
        macro_score=None,
        macro_regime=None,
    )


def _make_ctx(tmp_path: Path, mocker: Any, ticker: str = "AAPL") -> StageContext:
    return StageContext(
        ticker=ticker,
        run_id="r1",
        ledger=RunLedger(run_id="r1", artifact_dir=tmp_path),
        extras={
            "analysis_ctx": mocker.MagicMock(),
            "partial_result": _make_fake_result(ticker=ticker),
            "strategic": None,
            "processing_time": 1.5,
        },
    )


def test_emit_returns_ok(tmp_path: Path, mocker: Any) -> None:
    fake_result = _make_fake_result()
    fake_enriched = EnrichedAnalysis.model_construct()
    mocker.patch(
        "finwiz.analysis.stages.emit._build_verdict_inner",
        return_value=(fake_result, fake_enriched),
    )
    ctx = _make_ctx(tmp_path, mocker)
    result = emit(ctx, EnrichedAnalysis.model_construct())
    assert result.provenance.outcome == StageOutcome.OK
    assert result.payload is fake_result


def test_emit_records_ledger_entry(tmp_path: Path, mocker: Any) -> None:
    fake_result = _make_fake_result(ticker="X", grade="B", score=0.7, rec="HOLD")
    mocker.patch(
        "finwiz.analysis.stages.emit._build_verdict_inner",
        return_value=(fake_result, EnrichedAnalysis.model_construct()),
    )
    ctx = _make_ctx(tmp_path, mocker, ticker="X")
    emit(ctx, EnrichedAnalysis.model_construct())
    assert any(e.stage == "emit" for e in ctx.ledger.entries)


def test_emit_pending_returns_na_grade(tmp_path: Path) -> None:
    ctx = StageContext(
        ticker="AAPL",
        run_id="r1",
        ledger=RunLedger(run_id="r1", artifact_dir=tmp_path),
    )
    pending = _emit_pending(ctx, reason="upstream collect failure")
    assert pending.grade == "N/A"
    assert pending.composite_score == 0.0
    assert "Analyse en attente" in pending.rationale


def test_emit_failure_becomes_failed(tmp_path: Path, mocker: Any) -> None:
    mocker.patch(
        "finwiz.analysis.stages.emit._build_verdict_inner",
        side_effect=RuntimeError("verdict error"),
    )
    ctx = _make_ctx(tmp_path, mocker)
    result = emit(ctx, EnrichedAnalysis.model_construct())
    assert result.payload is None
    assert result.provenance.outcome == StageOutcome.FAILED
