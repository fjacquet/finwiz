"""Unit tests for the quantify stage StageResult contract."""

from pathlib import Path
from typing import Any

from finwiz.analysis.stages._ledger import RunLedger
from finwiz.analysis.stages._resilience import StageContext
from finwiz.analysis.stages.quantify import quantify
from finwiz.schemas.hybrid_analysis.metadata import DataQualityMetrics
from finwiz.schemas.hybrid_analysis.quantitative import QuantitativeAnalysis
from finwiz.schemas.stage_contract import StageOutcome


def _build_quant() -> QuantitativeAnalysis:
    """Build a minimal valid QuantitativeAnalysis for testing."""
    from datetime import datetime

    return QuantitativeAnalysis(
        composite_score=0.75,
        fundamental_score=0.80,
        technical_score=0.70,
        risk_score=2.0,
        grade="B",
        preliminary_recommendation="BUY",
        fundamental_metrics={"roe": 0.15},
        technical_indicators={"rsi": 55.0},
        risk_metrics={"volatility": 0.18},
        calculation_timestamp=datetime.now(),
        data_quality=DataQualityMetrics(
            completeness_score=0.9,
            freshness_score=1.0,
            accuracy_confidence=0.85,
            source_reliability=0.85,
            missing_fields=[],
        ),
        confidence_level=0.85,
        python_rationale="Solid fundamentals with stable technical signals",
    )


def test_quantify_returns_ok(tmp_path: Path, mocker: Any) -> None:
    fake_quant = _build_quant()
    fake_partial = mocker.MagicMock()
    mocker.patch(
        "finwiz.analysis.stages.quantify._calculate_quantitative_inner",
        return_value=(fake_partial, fake_quant),
    )
    ctx = StageContext(
        ticker="AAPL",
        run_id="r1",
        ledger=RunLedger(run_id="r1", artifact_dir=tmp_path),
        extras={"analysis_ctx": mocker.MagicMock()},
    )
    result = quantify(ctx, {"price_history": [1, 2, 3]})
    assert result.provenance.outcome == StageOutcome.OK
    assert result.payload is fake_quant
    # Partial result should have been stashed for downstream stages
    assert ctx.extras["partial_result"] is fake_partial


def test_quantify_records_ledger_entry(tmp_path: Path, mocker: Any) -> None:
    mocker.patch(
        "finwiz.analysis.stages.quantify._calculate_quantitative_inner",
        return_value=(mocker.MagicMock(), _build_quant()),
    )
    ctx = StageContext(
        ticker="AAPL",
        run_id="r1",
        ledger=RunLedger(run_id="r1", artifact_dir=tmp_path),
        extras={"analysis_ctx": mocker.MagicMock()},
    )
    quantify(ctx, {})
    assert any(e.stage == "quantify" for e in ctx.ledger.entries)


def test_quantify_failure_becomes_failed(tmp_path: Path, mocker: Any) -> None:
    mocker.patch(
        "finwiz.analysis.stages.quantify._calculate_quantitative_inner",
        side_effect=ValueError("scorer error"),
    )
    ctx = StageContext(
        ticker="AAPL",
        run_id="r1",
        ledger=RunLedger(run_id="r1", artifact_dir=tmp_path),
        extras={"analysis_ctx": mocker.MagicMock()},
    )
    result = quantify(ctx, {})
    assert result.payload is None
    assert result.provenance.outcome == StageOutcome.FAILED
    assert "scorer error" in (result.provenance.reason or "")
