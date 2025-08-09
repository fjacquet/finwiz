from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from .common import RiskAssessmentStandardized


class ETFTopHolding(BaseModel):
    """A single ETF top holding with weight and provenance."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    ticker: str = Field(min_length=1, max_length=15)
    weight_pct: float = Field(ge=0.0, le=100.0)
    source_url: HttpUrl
    as_of: date


class ETFFactsheet(BaseModel):
    """
    ETF factsheet highlights and metadata.

    Include commonly available numbers to aid the final reporter and risk synthesis.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    schema_version: int = 1

    ticker: str = Field(min_length=1, max_length=15)
    issuer: str
    expense_ratio: float = Field(ge=0.0, le=5.0, description="Total expense ratio (%)")
    tracking_diff: float | None = Field(
        default=None,
        ge=-10.0,
        le=10.0,
        description="Annualized tracking difference vs benchmark in %",
    )
    replication_method: Literal["physical", "synthetic", "optimized", "other"] = "other"

    factsheet_url: HttpUrl
    as_of: date

    factsheet_highlights: list[str] = Field(default_factory=list, max_length=20)
    top_holdings: list[ETFTopHolding] = Field(default_factory=list)

    # standardized risk lives separately
    risk: RiskAssessmentStandardized | None = None
