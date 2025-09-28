from __future__ import annotations

import pytest
from pydantic import ValidationError

from finwiz.schemas import RiskAssessmentStandardized


def test_risk_valid_bounds() -> None:
    r = RiskAssessmentStandardized(score=0.0, level="Low")
    assert r.score == 0.0
    r2 = RiskAssessmentStandardized(score=5.0, level="Very High")
    assert r2.score == 5.0


def test_risk_out_of_bounds() -> None:
    with pytest.raises(ValidationError):
        RiskAssessmentStandardized(score=-0.1, level="Low")
    with pytest.raises(ValidationError):
        RiskAssessmentStandardized(score=5.1, level="High")


def test_risk_extra_forbidden() -> None:
    payload = {"score": 3.0, "level": "Medium", "risk_factors": [], "x": 1}
    with pytest.raises(ValidationError):
        RiskAssessmentStandardized.model_validate(payload)
