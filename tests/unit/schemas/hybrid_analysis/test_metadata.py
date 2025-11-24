"""
Property-based tests for metadata schemas.

**Feature: python-ai-hybrid-analysis, Property 2: Data Quality Metadata Completeness**
**Validates: Requirements 1.2, 1.3**

Tests that DataQualityMetrics and DataLineage schemas properly validate
data quality scores, timestamps, and source tracking.
"""

from datetime import UTC, datetime

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from finwiz.schemas.hybrid_analysis.metadata import (
    DataLineage,
    DataQualityMetrics,
)


# Property 2: Data Quality Metadata Completeness
@given(
    completeness=st.floats(min_value=0.0, max_value=1.0),
    freshness=st.floats(min_value=0.0, max_value=1.0),
    accuracy=st.floats(min_value=0.0, max_value=1.0),
    reliability=st.floats(min_value=0.0, max_value=1.0),
    missing_fields=st.lists(
        st.text(
            min_size=1,
            max_size=20,
            alphabet=st.characters(min_codepoint=32, max_codepoint=126),  # Printable ASCII
        ),
        max_size=10,
    ),
)
def test_data_quality_metrics_scores_in_valid_range(
    completeness: float,
    freshness: float,
    accuracy: float,
    reliability: float,
    missing_fields: list[str],
):
    """
    Property: All quality scores must be in [0,1] range.

    For any valid quality scores in [0,1], DataQualityMetrics should
    accept them and store them correctly.
    """
    metrics = DataQualityMetrics(
        completeness_score=completeness,
        freshness_score=freshness,
        accuracy_confidence=accuracy,
        source_reliability=reliability,
        missing_fields=missing_fields,
    )

    # All scores should be in valid range
    assert 0.0 <= metrics.completeness_score <= 1.0
    assert 0.0 <= metrics.freshness_score <= 1.0
    assert 0.0 <= metrics.accuracy_confidence <= 1.0
    assert 0.0 <= metrics.source_reliability <= 1.0

    # Missing fields should be preserved (after whitespace stripping)
    expected_fields = [f.strip() for f in missing_fields]
    assert metrics.missing_fields == expected_fields


@given(
    score=st.one_of(
        st.floats(min_value=-1000.0, max_value=-0.01),
        st.floats(min_value=1.01, max_value=1000.0),
    )
)
def test_data_quality_metrics_rejects_invalid_scores(score: float):
    """
    Property: Scores outside [0,1] must be rejected.

    For any score outside the [0,1] range, DataQualityMetrics should
    raise a ValidationError.
    """
    with pytest.raises(ValidationError):
        DataQualityMetrics(
            completeness_score=score,
            freshness_score=0.5,
            accuracy_confidence=0.5,
            source_reliability=0.5,
        )


@given(
    sources=st.lists(
        st.text(
            min_size=1,
            max_size=50,
            alphabet=st.characters(min_codepoint=32, max_codepoint=126),  # Printable ASCII
        ),
        min_size=1,
        max_size=10,
    ),
    cache_status=st.sampled_from(["fresh", "cached", "stale"]),
    transformation_steps=st.lists(
        st.text(
            min_size=1,
            max_size=50,
            alphabet=st.characters(min_codepoint=32, max_codepoint=126),  # Printable ASCII
        ),
        max_size=10,
    ),
)
def test_data_lineage_requires_non_empty_sources(
    sources: list[str],
    cache_status: str,
    transformation_steps: list[str],
):
    """
    Property: primary_sources must be non-empty.

    For any non-empty list of sources, DataLineage should accept them
    and store them correctly.
    """
    lineage = DataLineage(
        primary_sources=sources,
        collection_timestamp=datetime.now(UTC),
        transformation_steps=transformation_steps,
        cache_status=cache_status,
    )

    # Sources must be non-empty
    assert len(lineage.primary_sources) > 0
    # After whitespace stripping, sources should match
    expected_sources = [s.strip() for s in sources]
    assert lineage.primary_sources == expected_sources

    # Timestamp should be valid
    assert isinstance(lineage.collection_timestamp, datetime)

    # Cache status and transformations should be preserved
    assert lineage.cache_status == cache_status
    expected_steps = [s.strip() for s in transformation_steps]
    assert lineage.transformation_steps == expected_steps


def test_data_lineage_rejects_empty_sources():
    """
    Property: Empty primary_sources must be rejected.

    DataLineage should raise ValidationError when primary_sources is empty.
    """
    with pytest.raises(ValidationError) as exc_info:
        DataLineage(
            primary_sources=[],
            collection_timestamp=datetime.now(UTC),
            cache_status="fresh",
        )

    # Verify the error is about primary_sources
    assert "primary_sources" in str(exc_info.value).lower()


@given(
    timestamp=st.datetimes(
        min_value=datetime(2020, 1, 1),
        max_value=datetime(2030, 12, 31),
    )
)
def test_data_lineage_timestamp_validation(timestamp: datetime):
    """
    Property: Timestamps must be valid datetime objects.

    For any valid datetime, DataLineage should accept and store it correctly.
    """
    # Add timezone if not present
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=UTC)

    lineage = DataLineage(
        primary_sources=["test_source"],
        collection_timestamp=timestamp,
        cache_status="fresh",
    )

    assert isinstance(lineage.collection_timestamp, datetime)
    assert lineage.collection_timestamp == timestamp


# Example-based tests for edge cases
def test_data_quality_metrics_boundary_values():
    """Test boundary values for quality scores."""
    # Minimum values
    metrics_min = DataQualityMetrics(
        completeness_score=0.0,
        freshness_score=0.0,
        accuracy_confidence=0.0,
        source_reliability=0.0,
    )
    assert metrics_min.completeness_score == 0.0

    # Maximum values
    metrics_max = DataQualityMetrics(
        completeness_score=1.0,
        freshness_score=1.0,
        accuracy_confidence=1.0,
        source_reliability=1.0,
    )
    assert metrics_max.completeness_score == 1.0


def test_data_lineage_with_empty_transformations():
    """Test DataLineage with no transformation steps."""
    lineage = DataLineage(
        primary_sources=["yfinance"],
        collection_timestamp=datetime.now(UTC),
        cache_status="fresh",
    )

    assert lineage.transformation_steps == []
    assert len(lineage.primary_sources) == 1
