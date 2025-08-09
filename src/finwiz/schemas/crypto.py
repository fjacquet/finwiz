from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from .common import RiskAssessmentStandardized


class CryptoThesis(BaseModel):
    """Crypto investment thesis bullets with optional citations."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    schema_version: int = 1

    symbol: str = Field(min_length=2, max_length=10, description="Crypto symbol, e.g., BTC")
    thesis_bullets: list[str] = Field(default_factory=list, max_length=20)
    references: list[HttpUrl] = Field(default_factory=list)


# Alias via type for clarity in exports
CryptoRisk = RiskAssessmentStandardized
