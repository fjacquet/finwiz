from __future__ import annotations

from datetime import date
from typing import Literal, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .common import RiskAssessmentStandardized


class ETFTopHolding(BaseModel):
    """A single ETF top holding with weight and provenance."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    ticker: str = Field(min_length=1, max_length=15)
    weight_pct: float = Field(ge=0.0, le=100.0)
    source_url: str = Field(description="Source URL for the holding data")
    as_of: date

    @field_validator("source_url")
    @classmethod
    def validate_source_url(cls, v: str) -> str:
        """Validate that source_url is a valid URL."""
        import re

        url_pattern = re.compile(
            r"^https?://"  # http:// or https://
            r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain...
            r"localhost|"  # localhost...
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
            r"(?::\d+)?"  # optional port
            r"(?:/?|[/?]\S+)$",
            re.IGNORECASE,
        )

        if not url_pattern.match(v):
            raise ValueError(f"Invalid URL format: {v}")
        return v


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
    tracking_diff: Union[float, None] = Field(
        default=None,
        ge=-10.0,
        le=10.0,
        description="Annualized tracking difference vs benchmark in %",
    )
    replication_method: Literal["physical", "synthetic", "optimized", "other"] = "other"

    factsheet_url: str = Field(description="URL to the ETF factsheet")
    as_of: date

    factsheet_highlights: list[str] = Field(default_factory=list, max_length=20)
    top_holdings: list[ETFTopHolding] = Field(default_factory=list)

    @field_validator("factsheet_url")
    @classmethod
    def validate_factsheet_url(cls, v: str) -> str:
        """Validate that factsheet_url is a valid URL."""
        import re

        url_pattern = re.compile(
            r"^https?://"  # http:// or https://
            r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain...
            r"localhost|"  # localhost...
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
            r"(?::\d+)?"  # optional port
            r"(?:/?|[/?]\S+)$",
            re.IGNORECASE,
        )

        if not url_pattern.match(v):
            raise ValueError(f"Invalid URL format: {v}")
        return v

    # standardized risk lives separately
    risk: Union[RiskAssessmentStandardized, None] = None
