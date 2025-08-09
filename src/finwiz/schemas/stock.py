from __future__ import annotations

from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, HttpUrl


class TenKInsight(BaseModel):
    """
    Extracted 10-K insight with provenance.

    section: One of the most-cited sections to constrain prompts and allow
             downstream section-specific synthesis.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    schema_version: int = 1
    ticker: str = Field(min_length=1, max_length=10)
    filing_url: HttpUrl
    filed_at: AwareDatetime
    section: Literal["Item 1", "Item 1A", "Item 7", "Item 7A", "Item 8"]
    excerpt: str = Field(min_length=20)
    sec_citation: str  # e.g., "10-K (2024), Item 1A, p. 17"


class SentimentItem(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    headline: str
    url: HttpUrl
    date: AwareDatetime
    score: float = Field(ge=-1.0, le=1.0)


class MarketSentiment(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    schema_version: int = 1
    ticker: str = Field(min_length=1, max_length=10)
    mean_score: float = Field(ge=-1.0, le=1.0)
    counts: dict[Literal["pos", "neu", "neg"], int]
    top_pos: list[SentimentItem] = Field(default_factory=list)
    top_neg: list[SentimentItem] = Field(default_factory=list)
