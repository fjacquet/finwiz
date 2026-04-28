"""Unit tests for the collect stage StageResult contract."""

from pathlib import Path
from typing import Any

from finwiz.analysis.stages._ledger import RunLedger
from finwiz.analysis.stages._resilience import StageContext
from finwiz.analysis.stages.collect import collect
from finwiz.schemas.hybrid_analysis.collected import CollectedData
from finwiz.schemas.stage_contract import StageOutcome, StageResult


def test_collect_returns_stage_result(tmp_path: Path, mocker: Any) -> None:
    mocker.patch(
        "finwiz.analysis.stages.collect._collect_raw_data_inner",
        return_value={"price_history": [1, 2, 3]},
    )
    ctx = StageContext(ticker="AAPL", run_id="r1", ledger=RunLedger(run_id="r1", artifact_dir=tmp_path))
    result = collect(ctx)
    assert isinstance(result, StageResult)
    assert result.provenance.outcome == StageOutcome.OK
    assert isinstance(result.payload, CollectedData)
    assert result.payload.data == {"price_history": [1, 2, 3]}


def test_collect_records_ledger_entry(tmp_path: Path, mocker: Any) -> None:
    mocker.patch(
        "finwiz.analysis.stages.collect._collect_raw_data_inner",
        return_value={},
    )
    ctx = StageContext(ticker="AAPL", run_id="r1", ledger=RunLedger(run_id="r1", artifact_dir=tmp_path))
    collect(ctx)
    assert any(e.stage == "collect" for e in ctx.ledger.entries)


def test_collect_failure_becomes_failed_outcome(tmp_path: Path, mocker: Any) -> None:
    mocker.patch(
        "finwiz.analysis.stages.collect._collect_raw_data_inner",
        side_effect=RuntimeError("data source down"),
    )
    ctx = StageContext(ticker="AAPL", run_id="r1", ledger=RunLedger(run_id="r1", artifact_dir=tmp_path))
    result = collect(ctx)
    assert result.payload is None
    assert result.provenance.outcome == StageOutcome.FAILED
    assert "data source down" in (result.provenance.reason or "")
