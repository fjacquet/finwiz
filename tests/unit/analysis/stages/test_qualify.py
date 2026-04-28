"""Unit tests for the qualify stage StageResult contract."""

from pathlib import Path
from typing import Any

from finwiz.analysis.stages._ledger import RunLedger
from finwiz.analysis.stages._resilience import StageContext
from finwiz.analysis.stages.qualify import qualify
from finwiz.schemas.hybrid_analysis import QualitativeInsights, QuantitativeAnalysis
from finwiz.schemas.stage_contract import StageOutcome


def test_qualify_returns_ok(tmp_path: Path, mocker: Any) -> None:
    fake_qual = QualitativeInsights()
    mocker.patch(
        "finwiz.analysis.stages.qualify._try_ai_qualify",
        return_value=fake_qual,
    )
    ctx = StageContext(
        ticker="AAPL",
        run_id="r1",
        ledger=RunLedger(run_id="r1", artifact_dir=tmp_path),
        extras={"analysis_ctx": mocker.MagicMock()},
    )
    quant = QuantitativeAnalysis.model_construct()
    result = qualify(ctx, quant, {})
    assert result.provenance.outcome == StageOutcome.OK
    assert result.payload is fake_qual


def test_qualify_records_ledger_entry(tmp_path: Path, mocker: Any) -> None:
    mocker.patch(
        "finwiz.analysis.stages.qualify._try_ai_qualify",
        return_value=QualitativeInsights(),
    )
    ctx = StageContext(
        ticker="AAPL",
        run_id="r1",
        ledger=RunLedger(run_id="r1", artifact_dir=tmp_path),
        extras={"analysis_ctx": mocker.MagicMock()},
    )
    qualify(ctx, QuantitativeAnalysis.model_construct(), {})
    assert any(e.stage == "qualify" for e in ctx.ledger.entries)


def test_qualify_failure_becomes_failed(tmp_path: Path, mocker: Any) -> None:
    mocker.patch(
        "finwiz.analysis.stages.qualify._try_ai_qualify",
        side_effect=RuntimeError("crew error"),
    )
    ctx = StageContext(
        ticker="AAPL",
        run_id="r1",
        ledger=RunLedger(run_id="r1", artifact_dir=tmp_path),
        extras={"analysis_ctx": mocker.MagicMock()},
    )
    result = qualify(ctx, QuantitativeAnalysis.model_construct(), {})
    assert result.payload is None
    assert result.provenance.outcome == StageOutcome.FAILED


def test_qualify_degraded_when_ai_returns_none(tmp_path: Path, mocker: Any) -> None:
    """v0.3.0 regression: AI null must produce DEGRADED, not silent OK."""
    mocker.patch("finwiz.analysis.stages.qualify._try_ai_qualify", return_value=None)
    fake_proxy = QualitativeInsights.model_construct()
    mocker.patch(
        "finwiz.analysis.stages.qualify._python_proxy_qualify",
        return_value=fake_proxy,
    )
    ctx = StageContext(
        ticker="AAPL",
        run_id="r1",
        ledger=RunLedger(run_id="r1", artifact_dir=tmp_path),
        extras={"analysis_ctx": mocker.MagicMock()},
    )
    result = qualify(ctx, QuantitativeAnalysis.model_construct(), {})
    assert result.provenance.outcome == StageOutcome.DEGRADED
    assert result.provenance.fallback_used == "python_proxy_qualitative"
    assert result.payload is fake_proxy
