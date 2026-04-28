"""Pydantic models for the analysis cache.

Extracted from analysis_cache_manager.py to keep that file under the
project's 300-line cap; behavior is unchanged.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CrewAnalysisResult(BaseModel):
    """Result from crew analysis."""

    ticker: str
    asset_class: str
    crew_name: str
    analyzed_at: datetime

    fundamental_score: float | None = None
    technical_score: float | None = None
    quality_score: float | None = None
    risk_score: float | None = None
    composite_score: float

    grade: str

    metrics: dict[str, Any] = Field(default_factory=dict)
    raw_output: dict[str, Any] = Field(default_factory=dict)


class CachedAnalysis(BaseModel):
    """Cached crew analysis result with metadata."""

    ticker: str
    asset_class: str
    cached_at: datetime
    analysis: CrewAnalysisResult

    def is_fresh(self, ttl_hours: int) -> bool:
        """Check if cached data is within TTL."""
        age = datetime.now() - self.cached_at
        return age.total_seconds() < (ttl_hours * 3600)

    @property
    def age_hours(self) -> float:
        """Age of cached data in hours."""
        age = datetime.now() - self.cached_at
        return age.total_seconds() / 3600
