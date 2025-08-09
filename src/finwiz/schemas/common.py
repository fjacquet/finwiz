from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

RiskLevel = Literal["Low", "Medium", "High", "Very High"]


class RiskAssessmentStandardized(BaseModel):
    """
    Standardized risk assessment across Stock/ETF/Crypto on a 0-5 scale.

    - score: 0 (lowest) .. 5 (highest)
    - level: human-friendly label mapped from score
    - risk_factors: up to 10 concise reasons
    - scale: reserved for future alternate encodings
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    scale: Literal["0_5", "L_M_H", "L_M_H_VH"] = "0_5"
    score: float = Field(ge=0.0, le=5.0)
    level: RiskLevel
    risk_factors: list[str] = Field(default_factory=list, max_length=10)
