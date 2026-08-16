"""Unit tests for the emit stage (D5 contract)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from finwiz.analysis.stages._ledger import RunLedger
from finwiz.analysis.stages._resilience import StageContext
from finwiz.analysis.stages.emit import _emit_pending, _pending_enriched, emit
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


def test_pending_enriched_does_not_fabricate_a_hold(tmp_path: Path) -> None:
    """A refused holding must not be persisted as a middling hold.

    ``{TICKER}_enriched.json`` is what the report and every downstream consumer
    reads. The pending path used to write ``EnrichedAnalysis.model_construct()``
    with no arguments, which took the schema defaults — grade "C", score 0.5,
    recommendation "HOLD" — and wrote them to disk for a holding the pipeline had
    explicitly refused. Observed live on 2026-08-16: 24 holdings, every one
    persisted as C/0.5/HOLD with an empty ticker and both analysis sections null.
    """
    ctx = StageContext(
        ticker="AAPL",
        run_id="r1",
        ledger=RunLedger(run_id="r1", artifact_dir=tmp_path),
    )
    enriched = _pending_enriched(ctx, reason="no cache and Perplexity fetch failed")

    assert enriched.final_grade != "C"
    assert enriched.final_score != 0.5
    assert enriched.final_recommendation != "HOLD"

    # It must say what it is, and for which holding.
    assert enriched.ticker == "AAPL"
    assert enriched.final_grade == "N/A"
    assert enriched.final_score == 0.0
    assert enriched.final_recommendation == "WAIT"
    assert enriched.quantitative is None
    assert enriched.qualitative is None
    assert "no cache and Perplexity fetch failed" in enriched.investment_rationale


def test_enriched_analysis_defaults_are_a_refusal_not_a_hold() -> None:
    """The schema's own defaults must fail safe.

    These defaults are the root cause: any construction site that forgets the
    verdict fields silently produces a confident "C / HOLD". A forgotten field
    should read as "no answer", never as a recommendation someone might act on.
    """
    blank = EnrichedAnalysis.model_construct()

    assert blank.final_grade == "N/A"
    assert blank.final_score == 0.0
    assert blank.final_recommendation == "WAIT"


def test_emit_failure_becomes_failed(tmp_path: Path, mocker: Any) -> None:
    mocker.patch(
        "finwiz.analysis.stages.emit._build_verdict_inner",
        side_effect=RuntimeError("verdict error"),
    )
    ctx = _make_ctx(tmp_path, mocker)
    result = emit(ctx, EnrichedAnalysis.model_construct())
    assert result.payload is None
    assert result.provenance.outcome == StageOutcome.FAILED
