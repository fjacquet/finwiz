from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .common import RiskAssessmentStandardized


class CryptoThesis(BaseModel):
    """Crypto investment thesis bullets with optional citations."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    schema_version: int = 1

    symbol: str = Field(min_length=2, max_length=10, description="Crypto symbol, e.g., BTC")
    thesis_bullets: list[str] = Field(default_factory=list, max_length=20)
    references: list[str] = Field(default_factory=list, description="List of reference URLs")

    @field_validator("references")
    @classmethod
    def validate_references(cls, v: list[str]) -> list[str]:
        """Validate that references are valid URLs."""
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

        for url in v:
            if not url_pattern.match(url):
                raise ValueError(f"Invalid URL format: {url}")
        return v


# Alias via type for clarity in exports
CryptoRisk = RiskAssessmentStandardized
