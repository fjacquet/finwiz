"""
Property-based tests for quantitative analysis schemas.

**Feature: python-ai-hybrid-analysis, Property 1: Python Quantitative Output Structure**
**Validates: Requirements 1.1**

Tests that QuantitativeAnalysis schema properly validates scores, grades,
and recommendations from Python calculations.
"""

from datetime import UTC, datetime

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError
from pytest import approx

from finwiz.schemas.hybrid_analysis.metadata import (
    DataLineage,
    DataQualityMetrics,
)
from finwiz.schemas.hybrid_analysis.quantitative import QuantitativeAnalysis


# Helper strategy for creating valid DataQualityMetrics
@st.composite
def data_quality_metrics_strategy(draw):
    """Generate valid DataQualityMetrics instances."""
    return DataQualityMetrics(
        completeness_score=draw(st.floats(min_value=0.0, max_value=1.0)),
        freshness_score=draw(st.floats(min_value=0.0, max_value=1.0)),
        accuracy_confidence=draw(st.floats(min_value=0.0, max_value=1.0)),
        source_reliability=draw(st.floats(min_value=0.0, max_value=1.0)),
        missing_fields=draw(st.lists(st.text(min_size=1, max_size=20, alphabet=st.characters(min_codepoint=32, max_codepoint=126)), max_size=5)),
    )


# Helper strategy for creating valid DataLineage
@st.composite
def data_lineage_strategy(draw):
    """Generate valid DataLineage instances."""
    timestamp = draw(st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2030, 12, 31)))
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=UTC)

    return DataLineage(
        primary_sources=draw(st.lists(st.text(min_size=1, max_size=20, alphabet=st.characters(min_codepoint=32, max_codepoint=126)), min_size=1, max_size=5)),
        collection_timestamp=timestamp,
        transformation_steps=draw(st.lists(st.text(min_size=1, max_size=20, alphabet=st.characters(min_codepoint=32, max_codepoint=126)), max_size=5)),
        cache_status=draw(st.sampled_from(["fresh", "cached", "stale"])),
    )


# Property 1: Python Quantitative Output Structure
@given(
    composite_score=st.floats(min_value=0.0, max_value=1.0),
    fundamental_score=st.floats(min_value=0.0, max_value=1.0),
    technical_score=st.floats(min_value=0.0, max_value=1.0),
    risk_score=st.floats(min_value=0.0, max_value=5.0),
    grade=st.sampled_from(["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-", "F"]),
    recommendation=st.sampled_from(["BUY", "HOLD", "SELL"]),
    confidence=st.floats(min_value=0.0, max_value=1.0),
    data_quality=data_quality_metrics_strategy(),
    data_lineage=data_lineage_strategy(),
)
def test_quantitative_analysis_valid_structure(
    composite_score: float,
    fundamental_score: float,
    technical_score: float,
    risk_score: float,
    grade: str,
    recommendation: str,
    confidence: float,
    data_quality: DataQualityMetrics,
    data_lineage: DataLineage,
):
    """
    Property: QuantitativeAnalysis accepts valid scores, grades, and recommendations.

    For any valid quantitative metrics, QuantitativeAnalysis should accept
    them and store them correctly.
    """
    analysis = QuantitativeAnalysis(
        composite_score=composite_score,
        fundamental_score=fundamental_score,
        technical_score=technical_score,
        risk_score=risk_score,
        grade=grade,
        preliminary_recommendation=recommendation,
        fundamental_metrics={"roe": 0.25, "debt_to_equity": 0.3},
        technical_indicators={"rsi": 55.0, "macd": 1.2},
        risk_metrics={"volatility": 0.15, "max_drawdown": 0.10},
        calculation_timestamp=datetime.now(UTC),
        data_quality=data_quality,
        data_lineage=data_lineage,
        confidence_level=confidence,
        python_rationale="Test rationale",
    )

    # Verify composite_score in [0,1]
    assert 0.0 <= analysis.composite_score <= 1.0
    assert analysis.composite_score == composite_score

    # Verify valid grade pattern
    assert analysis.grade in ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-", "F"]
    assert analysis.grade == grade

    # Verify valid recommendation values
    assert analysis.preliminary_recommendation in ["BUY", "HOLD", "SELL"]
    assert analysis.preliminary_recommendation == recommendation

    # Verify other scores in valid ranges
    assert 0.0 <= analysis.fundamental_score <= 1.0
    assert 0.0 <= analysis.technical_score <= 1.0
    assert 0.0 <= analysis.risk_score <= 5.0
    assert 0.0 <= analysis.confidence_level <= 1.0


@given(
    score=st.one_of(
        st.floats(min_value=-1000.0, max_value=-0.01),
        st.floats(min_value=1.01, max_value=1000.0),
    )
)
def test_quantitative_analysis_rejects_invalid_composite_score(score: float):
    """
    Property: composite_score outside [0,1] must be rejected.

    For any score outside the [0,1] range, QuantitativeAnalysis should
    raise a ValidationError.
    """
    with pytest.raises(ValidationError):
        QuantitativeAnalysis(
            composite_score=score,
            fundamental_score=0.5,
            technical_score=0.5,
            risk_score=2.5,
            grade="B",
            preliminary_recommendation="HOLD",
            fundamental_metrics={},
            technical_indicators={},
            risk_metrics={},
            calculation_timestamp=datetime.now(UTC),
            data_quality=DataQualityMetrics(
                completeness_score=0.9,
                freshness_score=0.9,
                accuracy_confidence=0.9,
                source_reliability=0.9,
            ),
            data_lineage=DataLineage(
                primary_sources=["test"],
                collection_timestamp=datetime.now(UTC),
                cache_status="fresh",
            ),
            confidence_level=0.9,
            python_rationale="Test",
        )


@given(invalid_grade=st.text(min_size=1, max_size=10).filter(lambda x: x not in ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-", "F"]))
def test_quantitative_analysis_rejects_invalid_grade(invalid_grade: str):
    """
    Property: Invalid grade patterns must be rejected.

    For any grade not matching the A+ to F pattern, QuantitativeAnalysis
    should raise a ValidationError.
    """
    with pytest.raises(ValidationError):
        QuantitativeAnalysis(
            composite_score=0.5,
            fundamental_score=0.5,
            technical_score=0.5,
            risk_score=2.5,
            grade=invalid_grade,
            preliminary_recommendation="HOLD",
            fundamental_metrics={},
            technical_indicators={},
            risk_metrics={},
            calculation_timestamp=datetime.now(UTC),
            data_quality=DataQualityMetrics(
                completeness_score=0.9,
                freshness_score=0.9,
                accuracy_confidence=0.9,
                source_reliability=0.9,
            ),
            data_lineage=DataLineage(
                primary_sources=["test"],
                collection_timestamp=datetime.now(UTC),
                cache_status="fresh",
            ),
            confidence_level=0.9,
            python_rationale="Test",
        )


@given(invalid_recommendation=st.text(min_size=1, max_size=10).filter(lambda x: x not in ["BUY", "HOLD", "SELL"]))
def test_quantitative_analysis_rejects_invalid_recommendation(invalid_recommendation: str):
    """
    Property: Invalid recommendations must be rejected.

    For any recommendation not in {BUY, HOLD, SELL}, QuantitativeAnalysis
    should raise a ValidationError.
    """
    with pytest.raises(ValidationError):
        QuantitativeAnalysis(
            composite_score=0.5,
            fundamental_score=0.5,
            technical_score=0.5,
            risk_score=2.5,
            grade="B",
            preliminary_recommendation=invalid_recommendation,
            fundamental_metrics={},
            technical_indicators={},
            risk_metrics={},
            calculation_timestamp=datetime.now(UTC),
            data_quality=DataQualityMetrics(
                completeness_score=0.9,
                freshness_score=0.9,
                accuracy_confidence=0.9,
                source_reliability=0.9,
            ),
            data_lineage=DataLineage(
                primary_sources=["test"],
                collection_timestamp=datetime.now(UTC),
                cache_status="fresh",
            ),
            confidence_level=0.9,
            python_rationale="Test",
        )


# Example-based tests for edge cases
def test_quantitative_analysis_boundary_values():
    """Test boundary values for all scores."""
    # Minimum values
    analysis_min = QuantitativeAnalysis(
        composite_score=0.0,
        fundamental_score=0.0,
        technical_score=0.0,
        risk_score=0.0,
        grade="F",
        preliminary_recommendation="SELL",
        fundamental_metrics={},
        technical_indicators={},
        risk_metrics={},
        calculation_timestamp=datetime.now(UTC),
        data_quality=DataQualityMetrics(
            completeness_score=0.0,
            freshness_score=0.0,
            accuracy_confidence=0.0,
            source_reliability=0.0,
        ),
        data_lineage=DataLineage(
            primary_sources=["test"],
            collection_timestamp=datetime.now(UTC),
            cache_status="fresh",
        ),
        confidence_level=0.0,
        python_rationale="Minimum values",
    )
    assert analysis_min.composite_score == approx(0.0)
    assert analysis_min.grade == "F"

    # Maximum values
    analysis_max = QuantitativeAnalysis(
        composite_score=1.0,
        fundamental_score=1.0,
        technical_score=1.0,
        risk_score=5.0,
        grade="A+",
        preliminary_recommendation="BUY",
        fundamental_metrics={},
        technical_indicators={},
        risk_metrics={},
        calculation_timestamp=datetime.now(UTC),
        data_quality=DataQualityMetrics(
            completeness_score=1.0,
            freshness_score=1.0,
            accuracy_confidence=1.0,
            source_reliability=1.0,
        ),
        data_lineage=DataLineage(
            primary_sources=["test"],
            collection_timestamp=datetime.now(UTC),
            cache_status="fresh",
        ),
        confidence_level=1.0,
        python_rationale="Maximum values",
    )
    assert analysis_max.composite_score == approx(1.0)
    assert analysis_max.grade == "A+"
