# tests/unit/schemas/test_stage_contract.py
from finwiz.schemas.stage_contract import StageOutcome


def test_stage_outcome_has_three_values() -> None:
    assert {o.value for o in StageOutcome} == {"ok", "degraded", "failed"}


def test_stage_outcome_is_str_enum() -> None:
    assert StageOutcome.OK == "ok"
    assert StageOutcome.DEGRADED == "degraded"
    assert StageOutcome.FAILED == "failed"
