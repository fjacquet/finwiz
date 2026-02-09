"""News and sentiment analysis schemas for v4 Data Intelligence."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class NewsArticle(BaseModel):
    """A single news article with optional sentiment scoring."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str = Field(..., min_length=1, max_length=500, description="Article headline")
    url: str = Field(..., min_length=1, description="Article URL")
    source: str = Field(..., min_length=1, description="Source identifier (e.g. 'finnhub', 'gnews', 'rss')")
    published_at: datetime = Field(..., description="Publication timestamp")
    summary: str = Field("", max_length=2000, description="Article summary or snippet")
    ticker: str = Field(..., min_length=1, max_length=10, description="Related ticker symbol")
    sentiment_score: float | None = Field(None, ge=-1.0, le=1.0, description="Sentiment score: -1 (bearish) to +1 (bullish)")
    sentiment_label: Literal["bullish", "bearish", "neutral"] | None = Field(None, description="Human-readable sentiment label")
    source_reliability: float = Field(1.0, ge=0.0, le=1.0, description="Source reliability weight for weighted averaging")
    content_hash: str = Field("", description="Hash of title+summary for deduplication")

    @field_validator("ticker")
    @classmethod
    def uppercase_ticker(cls, v: str) -> str:
        return v.upper()


class NewsSentimentResult(BaseModel):
    """Aggregated news sentiment for a single ticker."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    ticker: str = Field(..., min_length=1, max_length=10, description="Ticker symbol")
    articles: list[NewsArticle] = Field(default_factory=list, description="Collected articles")
    aggregate_sentiment: float = Field(0.0, ge=-1.0, le=1.0, description="Simple average sentiment")
    weighted_sentiment: float = Field(0.0, ge=-1.0, le=1.0, description="Reliability-weighted sentiment")
    article_count: int = Field(0, ge=0, description="Total articles collected")
    bullish_count: int = Field(0, ge=0, description="Articles with bullish sentiment")
    bearish_count: int = Field(0, ge=0, description="Articles with bearish sentiment")
    neutral_count: int = Field(0, ge=0, description="Articles with neutral sentiment")
    source_breakdown: dict[str, int] = Field(default_factory=dict, description="Article count per source")
    data_freshness_hours: float = Field(0.0, ge=0.0, description="Hours since newest article")
    fetched_at: datetime = Field(default_factory=datetime.now, description="When sentiment was collected")

    @field_validator("ticker")
    @classmethod
    def uppercase_ticker(cls, v: str) -> str:
        return v.upper()


class SentimentScore(BaseModel):
    """Phase 14 sentiment scoring output for a single holding."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    ticker: str = Field(..., min_length=1, max_length=10, description="Ticker symbol")
    score: float | None = Field(None, ge=-1.0, le=1.0, description="Aggregate sentiment score (-1 bearish to +1 bullish). None = no news data.")
    confidence: float | None = Field(None, ge=0.0, le=1.0, description="Confidence in the sentiment score. None = no news data.")
    article_count: int = Field(0, ge=0, description="Number of articles used in scoring")
    source_count: int = Field(0, ge=0, description="Number of unique sources")
    temporal_decay_applied: bool = Field(False, description="Whether temporal decay weighting was applied")
    data_freshness_hours: float = Field(0.0, ge=0.0, description="Hours since newest article")
    details: dict[str, Any] = Field(default_factory=dict, description="Scoring breakdown details")

    @field_validator("ticker")
    @classmethod
    def uppercase_ticker(cls, v: str) -> str:
        return v.upper()
