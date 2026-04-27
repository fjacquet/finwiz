from pathlib import Path
from typing import Any

import pytest
from pydantic import BaseModel

from finwiz.analysis.stages._ledger import RunLedger
from finwiz.analysis.stages._resilience import StageContext, stage
from finwiz.schemas.stage_contract import (
    StageOutcome,
    StageResult,
)


class _Payload(BaseModel):
    value: int


def _ctx(tmp_path: Path) -> StageContext:
    return StageContext(ticker="AAPL", run_id="r1", ledger=RunLedger(run_id="r1", artifact_dir=tmp_path))


@stage(name="collect", timeout_s=5, retries=0)
def _collect_ok(ctx: StageContext) -> _Payload:
    return _Payload(value=42)


@stage(name="quantify", timeout_s=5, retries=0)
def _quantify_raises(ctx: StageContext, prev: _Payload) -> _Payload:
    raise RuntimeError("boom")


def test_stage_wraps_return_in_stage_result_ok(tmp_path: Path) -> None:
    ctx = _ctx(tmp_path)
    result = _collect_ok(ctx)
    assert isinstance(result, StageResult)
    assert result.provenance.stage == "collect"
    assert result.provenance.outcome == StageOutcome.OK
    assert result.payload is not None and result.payload.value == 42


def test_stage_records_ledger_entry_on_ok(tmp_path: Path) -> None:
    ctx = _ctx(tmp_path)
    _collect_ok(ctx)
    assert len(ctx.ledger.entries) == 1
    assert ctx.ledger.entries[0].outcome == StageOutcome.OK


def test_stage_captures_exception_as_failed(tmp_path: Path) -> None:
    ctx = _ctx(tmp_path)
    result = _quantify_raises(ctx, _Payload(value=1))
    assert result.payload is None
    assert result.provenance.outcome == StageOutcome.FAILED
    assert "boom" in (result.provenance.reason or "")


def test_stage_records_ledger_entry_on_failure(tmp_path: Path) -> None:
    ctx = _ctx(tmp_path)
    _quantify_raises(ctx, _Payload(value=1))
    assert ctx.ledger.entries[-1].outcome == StageOutcome.FAILED


def test_stage_allow_degrade_outside_qualify_raises_at_decoration() -> None:
    with pytest.raises(ValueError) as excinfo:

        @stage(name="collect", timeout_s=5, retries=0, allow_degrade=True)
        def _bad(ctx: StageContext) -> _Payload:
            return _Payload(value=1)

    assert "allow_degrade" in str(excinfo.value)
    assert "qualify" in str(excinfo.value)


def test_stage_validation_error_not_retried(tmp_path: Path, mocker: Any) -> None:
    from pydantic import ValidationError

    calls = {"n": 0}

    @stage(name="quantify", timeout_s=5, retries=3)
    def _validate(ctx: StageContext) -> _Payload:
        calls["n"] += 1
        # Force a validation error from pydantic
        _Payload(value="not-an-int")  # type: ignore[arg-type]
        return _Payload(value=1)

    ctx = _ctx(tmp_path)
    with pytest.raises(ValidationError):
        _validate(ctx)
    assert calls["n"] == 1  # no retry on ValidationError
