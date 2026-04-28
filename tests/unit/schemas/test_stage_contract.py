# tests/unit/schemas/test_stage_contract.py
import pytest
from pydantic import BaseModel as _PBM
from pydantic import ValidationError

from finwiz.schemas.stage_contract import StageOutcome, StageProvenance, StageResult


def test_stage_outcome_has_three_values() -> None:
    assert {o.value for o in StageOutcome} == {"ok", "degraded", "failed"}


def test_stage_outcome_is_str_enum() -> None:
    assert StageOutcome.OK == "ok"
    assert StageOutcome.DEGRADED == "degraded"
    assert StageOutcome.FAILED == "failed"


def test_provenance_ok_for_collect_is_valid() -> None:
    p = StageProvenance(stage="collect", outcome=StageOutcome.OK, duration_ms=12)
    assert p.outcome == StageOutcome.OK


def test_provenance_failed_with_reason_is_valid() -> None:
    p = StageProvenance(
        stage="quantify",
        outcome=StageOutcome.FAILED,
        reason="scorer raised",
        duration_ms=5,
    )
    assert p.outcome == StageOutcome.FAILED


def test_provenance_degraded_outside_qualify_raises() -> None:
    with pytest.raises(ValidationError) as excinfo:
        StageProvenance(stage="collect", outcome=StageOutcome.DEGRADED, duration_ms=1)
    assert "DEGRADED" in str(excinfo.value)


def test_provenance_degraded_in_qualify_is_valid() -> None:
    p = StageProvenance(
        stage="qualify",
        outcome=StageOutcome.DEGRADED,
        fallback_used="python_proxy_qualitative",
        reason="AI null",
        duration_ms=3000,
    )
    assert p.outcome == StageOutcome.DEGRADED


def test_provenance_fallback_without_degraded_raises() -> None:
    with pytest.raises(ValidationError) as excinfo:
        StageProvenance(
            stage="qualify",
            outcome=StageOutcome.OK,
            fallback_used="python_proxy_qualitative",
            duration_ms=1,
        )
    assert "fallback_used" in str(excinfo.value)


def test_provenance_extra_fields_forbidden() -> None:
    with pytest.raises(ValidationError):
        StageProvenance(
            stage="collect",
            outcome=StageOutcome.OK,
            duration_ms=1,
            unknown_field="boom",
        )


class _Payload(_PBM):
    value: int


def test_result_ok_with_payload_is_valid() -> None:
    r = StageResult[_Payload](
        payload=_Payload(value=42),
        provenance=StageProvenance(stage="collect", outcome=StageOutcome.OK, duration_ms=1),
    )
    assert r.payload is not None and r.payload.value == 42


def test_result_failed_with_payload_raises() -> None:
    with pytest.raises(ValidationError) as excinfo:
        StageResult[_Payload](
            payload=_Payload(value=1),
            provenance=StageProvenance(stage="collect", outcome=StageOutcome.FAILED, duration_ms=1, reason="boom"),
        )
    assert "FAILED" in str(excinfo.value)


def test_result_ok_without_payload_raises() -> None:
    with pytest.raises(ValidationError) as excinfo:
        StageResult[_Payload](
            payload=None,
            provenance=StageProvenance(stage="collect", outcome=StageOutcome.OK, duration_ms=1),
        )
    assert "payload" in str(excinfo.value)


def test_result_failed_without_payload_is_valid() -> None:
    r = StageResult[_Payload](
        payload=None,
        provenance=StageProvenance(stage="collect", outcome=StageOutcome.FAILED, duration_ms=1, reason="boom"),
    )
    assert r.payload is None
