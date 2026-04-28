"""FactPack schema for grounded qualitative analysis (v5.2).

Verified corporate facts fetched from Perplexity, cached for 7 days, injected
into the qualitative prompt as ground truth. The qualitative crew must NOT
contradict the fact pack — anti-hallucination becomes structural.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

_FRESHNESS_VALUES = ("fresh", "recent", "stale")
Freshness = Literal["fresh", "recent", "stale"]


class FactPack(BaseModel):
    """Verified corporate facts for one holding.

    Lifecycle: fetched once per holding via Perplexity, cached 7 days. The
    `freshness` field is Python-derived from `fetched_at` — AI cannot lie
    about it (cross-checked by model_validator).
    """

    corporate_structure: str = Field(min_length=1, max_length=2000, description="Current entity / parent / subsidiaries / recent divestitures")
    recent_events: list[str] = Field(default_factory=list, max_length=10, description="Material events in last 12 months")
    leadership: str = Field(min_length=1, max_length=1000, description="Current CEO/CFO and recent changes")
    fetched_at: datetime
    freshness: Freshness
    confidence: float = Field(ge=0.0, le=1.0, description="AI-rated 0.0-1.0")
    source_citations: list[str] = Field(default_factory=list, max_length=20, description="Perplexity citation URLs")

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @classmethod
    def derive_freshness(cls, fetched_at: datetime) -> Freshness:
        """Python owns freshness derivation; AI may not lie about it.

        <3d -> fresh, 3-7d -> recent, 7-14d -> stale, >14d -> raises (cache must have evicted).
        """
        if fetched_at.tzinfo is None:
            fetched_at = fetched_at.replace(tzinfo=UTC)
        now = datetime.now(UTC)
        age = now - fetched_at
        if age < timedelta(days=3):
            return "fresh"
        if age < timedelta(days=7):
            return "recent"
        if age < timedelta(days=15):
            return "stale"
        raise ValueError(f"FactPack older than 14 days (age={age}); cache should have evicted")

    @model_validator(mode="after")
    def _check_freshness_matches_fetched_at(self) -> FactPack:
        """AI may not lie about freshness — Python is authoritative."""
        expected = self.derive_freshness(self.fetched_at)
        if self.freshness != expected:
            raise ValueError(f"freshness={self.freshness!r} contradicts fetched_at={self.fetched_at} (Python derived: {expected!r})")
        return self
