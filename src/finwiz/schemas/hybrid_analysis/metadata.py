"""
Metadata schemas for hybrid analysis data quality tracking.

This module provides Pydantic models for tracking data quality metrics
throughout the hybrid Python/AI analysis pipeline.
"""

from pydantic import BaseModel, Field


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
