from __future__ import annotations

from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator


class TenKInsight(BaseModel):
    """
    Extracted 10-K insight with provenance.

    section: One of the most-cited sections to constrain prompts and allow
             downstream section-specific synthesis.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    schema_version: int = 1
    ticker: str = Field(min_length=1, max_length=10)
    filing_url: str = Field(description="URL to the SEC filing")
    filed_at: AwareDatetime
    section: Literal["Item 1", "Item 1A", "Item 7", "Item 7A", "Item 8"]
    excerpt: str = Field(min_length=20)
    sec_citation: str  # e.g., "10-K (2024), Item 1A, p. 17"

    @field_validator("filing_url")
    @classmethod
    def validate_filing_url(cls, v: str) -> str:
        """Validate that filing_url is a valid URL."""
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


class SentimentItem(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    headline: str
    url: str = Field(description="Article URL")
    date: AwareDatetime
    score: float = Field(ge=-1.0, le=1.0)

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate that url is a valid URL."""
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


class MarketSentiment(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    schema_version: int = 1
    ticker: str = Field(min_length=1, max_length=10)
    mean_score: float = Field(ge=-1.0, le=1.0)
    counts: dict[Literal["pos", "neu", "neg"], int]
    top_pos: list[SentimentItem] = Field(default_factory=list)
    top_neg: list[SentimentItem] = Field(default_factory=list)
