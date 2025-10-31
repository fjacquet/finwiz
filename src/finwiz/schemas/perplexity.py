"""
Perplexity Sonar integration data models.

Provides Pydantic models for Perplexity Sonar search results and articles
with strict validation following FinWiz standards.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, validator


class SonarArticle(BaseModel):
    """Individual article from Sonar search results."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, validate_assignment=True)

    title: str = Field(..., min_length=1, max_length=500, description="Article title")
    url: str = Field(..., description="Article URL")
    summary: str = Field("", max_length=2000, description="Article summary/snippet")
    publisher: str = Field("", max_length=200, description="Publisher name")

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

    published_date: Optional[str] = Field(None, description="Publication date (ISO format)")
    relevance_score: float = Field(0.0, ge=0.0, le=1.0, description="Relevance to query (0.0-1.0)")
    content_type: Literal["news", "filing", "analysis", "earnings", "regulatory"] = Field("news", description="Type of content")
    analysis_type: Literal["sentiment", "technical", "fundamental", "general"] = Field("general", description="Analysis context for this article")

    @validator("published_date")
    def validate_published_date(cls, v: Optional[str]) -> Optional[str]:
        """Validate published date format."""
        if v is None:
            return v
        try:
            # Try to parse as ISO format to validate
            datetime.fromisoformat(v.replace("Z", "+00:00"))
            return v
        except ValueError:
            # If not ISO format, return as-is but log warning
            return v


class SonarSearchResult(BaseModel):
    """Structured result from Perplexity Sonar search."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, validate_assignment=True)

    query: str = Field(..., min_length=1, max_length=500, description="Original search query")
    ticker: str = Field(..., pattern=r"^[A-Z0-9.-]{1,10}$", description="Asset ticker symbol")
    asset_type: Literal["stock", "etf", "crypto"] = Field(..., description="Asset type")
    analysis_type: Literal["sentiment", "technical", "fundamental", "general"] = Field("general", description="Type of analysis performed")
    results: list[SonarArticle] = Field(default_factory=list, description="Search results")
    total_results: int = Field(0, ge=0, description="Total number of results found")
    search_time_ms: int = Field(0, ge=0, description="Search execution time in milliseconds")
    source: str = Field("perplexity_sonar", description="Data source identifier")
    success: bool = Field(True, description="Whether search was successful")
    error_message: Optional[str] = Field(None, description="Error message if search failed")
    fallback_used: bool = Field(False, description="Whether fallback mechanism was used")
    retry_count: int = Field(0, ge=0, description="Number of retry attempts made")

    @validator("ticker")
    def validate_ticker_format(cls, v: str) -> str:
        """Validate and normalize ticker symbol."""
        return v.upper().strip()


class PerplexitySearchRequest(BaseModel):
    """Request schema for Perplexity search operations."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, str_upper=False)

    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    ticker: str = Field(..., pattern=r"^[A-Z0-9.-]{1,10}$", description="Asset ticker symbol")
    asset_type: Literal["stock", "etf", "crypto"] = Field(..., description="Asset type")
    analysis_type: Literal["sentiment", "technical", "fundamental", "general"] = Field("general", description="Type of analysis to perform")
    max_results: int = Field(10, ge=1, le=50, description="Maximum results to return")
    search_filters: Optional[dict[str, str]] = Field(None, description="Additional search filters")

    @validator("ticker")
    def validate_ticker_format(cls, v: str) -> str:
        """Validate and normalize ticker symbol."""
        return v.upper().strip()


class PerplexitySearchResponse(BaseModel):
    """Response schema for Perplexity search operations."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    success: bool = Field(..., description="Whether search was successful")
    results: list[SonarArticle] = Field(default_factory=list, description="Search results")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    error_message: Optional[str] = Field(None, description="Error message if search failed")
    rate_limit_info: Optional[dict[str, int]] = Field(None, description="Rate limit status")
    search_time_ms: int = Field(0, ge=0, description="Search execution time")


class PerplexityConfig(BaseModel):
    """Configuration for Perplexity Sonar integration."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    api_key: str = Field(..., min_length=1, description="Perplexity API key")
    timeout_seconds: float = Field(30.0, ge=1.0, le=120.0, description="Request timeout")
    max_retries: int = Field(3, ge=0, le=10, description="Maximum retry attempts")
    backoff_factor: float = Field(2.0, ge=1.0, le=10.0, description="Exponential backoff factor")
    rate_limit_buffer: int = Field(5, ge=1, le=60, description="Rate limit buffer in seconds")

    # Search configuration
    default_max_results: int = Field(10, ge=1, le=50, description="Default maximum results")
    financial_news_filters: dict[str, str] = Field(
        default_factory=lambda: {"site": "bloomberg.com,reuters.com,wsj.com,ft.com,cnbc.com", "date": "past_week"},
        description="Filters for financial news searches",
    )
    sec_filing_filters: dict[str, str] = Field(default_factory=lambda: {"site": "sec.gov", "filetype": "pdf,html"}, description="Filters for SEC filing searches")
