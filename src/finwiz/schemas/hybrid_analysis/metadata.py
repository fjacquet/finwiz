"""
Metadata schemas for hybrid analysis data quality and lineage tracking.

This module provides Pydantic models for tracking data quality metrics and
data lineage throughout the hybrid Python/AI analysis pipeline.
"""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class DataQualityMetrics(BaseModel):
    """
    Data quality assessment for quantitative analysis.

    Tracks completeness, freshness, accuracy, and source reliability
    to ensure high-quality analysis inputs.

    Examples:
        >>> metrics = DataQualityMetrics(completeness_score=0.95, freshness_score=1.0, accuracy_confidence=0.90, source_reliability=0.85, missing_fields=["beta"])
        >>> assert 0 <= metrics.completeness_score <= 1

    """

    completeness_score: float = Field(..., ge=0.0, le=1.0, description="Percentage of required data points available (0.0-1.0)")
    freshness_score: float = Field(..., ge=0.0, le=1.0, description="How recent the data is (1.0 = today, 0.0 = very old)")
    accuracy_confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in data accuracy (0.0-1.0)")
    source_reliability: float = Field(..., ge=0.0, le=1.0, description="Reliability of data sources (0.0-1.0)")
    missing_fields: list[str] = Field(default_factory=list, description="List of missing critical fields")

    model_config = {
        "str_strip_whitespace": True,
        "validate_default": True,
        "json_schema_extra": {
            "examples": [{"completeness_score": 0.95, "freshness_score": 1.0, "accuracy_confidence": 0.90, "source_reliability": 0.85, "missing_fields": ["beta"]}]
        },
    }


class DataLineage(BaseModel):
    """
    Track data sources and transformations for audit trail.

    Maintains complete lineage of data from source through transformations
    to ensure reproducibility and debugging capability.

    Examples:
        >>> lineage = DataLineage(
        ...     primary_sources=["yfinance", "alpha_vantage"], collection_timestamp=datetime.now(), transformation_steps=["normalize", "calculate_metrics"], cache_status="fresh"
        ... )
        >>> assert len(lineage.primary_sources) > 0

    """

    primary_sources: list[str] = Field(..., min_length=1, description="Primary data sources (e.g., 'yfinance', 'sec_api')")
    collection_timestamp: datetime = Field(..., description="When data was collected (UTC)")
    transformation_steps: list[str] = Field(default_factory=list, description="Data transformation steps applied")
    cache_status: str = Field(..., description="Whether data was cached or fresh")

    model_config = {
        "str_strip_whitespace": True,
        "json_schema_extra": {
            "examples": [
                {
                    "primary_sources": ["yfinance", "alpha_vantage"],
                    "collection_timestamp": "2025-11-21T10:30:00Z",
                    "transformation_steps": ["normalize", "calculate_metrics"],
                    "cache_status": "fresh",
                }
            ]
        },
    }

    @field_validator("primary_sources")
    @classmethod
    def validate_primary_sources(cls, v: list[str]) -> list[str]:
        """Ensure primary_sources is non-empty."""
        if not v:
            raise ValueError("primary_sources must contain at least one source")
        return v
