"""
Newcomer discovery data models.

Pydantic schemas for the NewcomerDiscoveryPipeline: candidates,
enrichment results, and aggregated discovery results.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class EnrichmentResult(BaseModel):
    """Result of Perplexity enrichment for a single candidate."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    source: str = Field("perplexity_sonar", description="Enrichment data source")
    query: str = Field("", description="Search query used")
    articles_found: int = Field(0, ge=0, description="Number of articles retrieved")
    summary: str = Field("", description="AI-generated summary of findings")
    sentiment: Optional[str] = Field(None, description="Overall sentiment from articles")
    key_insights: list[str] = Field(default_factory=list, description="Key insights extracted")
    success: bool = Field(True, description="Whether enrichment succeeded")
    error_message: Optional[str] = Field(None, description="Error message if failed")


class NewcomerCandidate(BaseModel):
    """A single newcomer investment candidate discovered by the pipeline."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    ticker: str = Field(..., min_length=1, max_length=20, description="Ticker symbol")
    name: str = Field("", max_length=200, description="Company or asset name")
    asset_class: Literal["stock", "etf", "crypto"] = Field(..., description="Asset class")
    source: str = Field("", description="Discovery source (e.g. universe, ipo, breakout, momentum)")
    composite_score: float = Field(0.0, ge=0.0, le=1.0, description="Overall score (0-1)")
    grade: str = Field("", max_length=5, description="Letter grade (A+ to F)")
    recommendation: str = Field("REVIEW", description="Action recommendation")
    rationale: str = Field("", max_length=2000, description="Reasoning for the recommendation")

    # Screener-populated fields
    market_cap: float | None = Field(None, ge=0, description="Market capitalization in USD")
    sector: str | None = Field(None, max_length=100, description="Industry sector")
    discovery_date: datetime = Field(default_factory=datetime.utcnow, description="When this candidate was discovered")

    # Optional scoring breakdown
    fundamental_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Fundamental analysis score")
    technical_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Technical analysis score")
    momentum_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Momentum score")

    # Optional enrichment
    enrichment: Optional[EnrichmentResult] = Field(None, description="Perplexity enrichment data")

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class NewcomerDiscoveryResult(BaseModel):
    """Aggregated result of a newcomer discovery pipeline run."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    asset_class: str = Field(..., description="Asset class analyzed")
    session_id: str = Field(..., description="Session identifier")
    timestamp: str = Field(..., description="ISO-format timestamp of discovery run")
    candidates: list[NewcomerCandidate] = Field(default_factory=list, description="Discovered candidates")
    total_candidates: int = Field(0, ge=0, description="Total candidate count")
    summary: str = Field("", description="Human-readable summary")
    sources_used: list[str] = Field(default_factory=list, description="Discovery sources used in this run")
    top_picks: list[str] = Field(default_factory=list, description="Top N candidate tickers")
    pipeline_version: str = Field("1.0", description="Pipeline version")
    enrichment_attempted: int = Field(0, ge=0, description="Number of candidates enrichment was attempted for")
    enrichment_succeeded: int = Field(0, ge=0, description="Number of candidates successfully enriched")
