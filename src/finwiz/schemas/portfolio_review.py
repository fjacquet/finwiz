from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .common import RiskAssessmentStandardized

Decision = Literal["KEEP", "SELL"]
AssetClass = Literal["stock", "etf"]
Grade = Literal["A+", "A", "B+", "B", "C+", "C", "D", "F"]


class Alternative(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    ticker: str
    name: str
    asset_class: AssetClass
    composite_score: float = Field(ge=0.0, le=1.0)
    grade: Grade = Field(description="Letter grade (A+ to F)")
    grade_description: str = Field(description="Human-readable grade description")
    recommended_action: str = Field(description="Recommended action based on grade")
    risk_score_standardized: float = Field(ge=0.0, le=5.0)
    key_metrics: dict = Field(default_factory=dict)
    thesis_bullets: list[str] = Field(default_factory=list, max_length=10)
    citations: list[str] = Field(default_factory=list, max_length=10)


class HoldingDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    asset_class: AssetClass
    name: str
    ticker: str
    currency: str
    decision: Decision
    composite_score: float = Field(ge=0.0, le=1.0)
    grade: Grade = Field(description="Letter grade (A+ to F)")
    grade_description: str = Field(description="Human-readable grade description")
    recommended_action: str = Field(description="Recommended action based on grade")
    risk: RiskAssessmentStandardized
    rationale_bullets: list[str] = Field(default_factory=list, max_length=10)
    citations: list[str] = Field(default_factory=list, max_length=10)
    alternatives: list[Alternative] = Field(default_factory=list, max_length=3)


class PortfolioReview(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    as_of: datetime
    base_currency: str = "CHF"
    holdings: list[HoldingDecision] = Field(default_factory=list)
