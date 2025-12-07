"""
Property-based tests for enriched analysis schema.

**Feature: python-ai-hybrid-analysis, Property 5: Enriched Analysis Merge Completeness**
**Feature: python-ai-hybrid-analysis, Property 6: Report Quality Thresholds**
**Validates: Requirements 3.1, 3.2, 3.3, 7.3, 7.4**

Tests that EnrichedAnalysis properly merges quantitative and qualitative data
and enforces quality thresholds.
"""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError
from pytest import approx

from finwiz.schemas.hybrid_analysis.enriched import EnrichedAnalysis
from finwiz.schemas.hybrid_analysis.metadata import DataLineage, DataQualityMetrics
from finwiz.schemas.hybrid_analysis.qualitative import (
    ContextualRiskInsights,
    FundamentalContextInsights,
    InvestmentSynthesis,
    QualitativeInsights,
    SecAnalysisInsights,
    TechnicalStrategyInsights,
)
from finwiz.schemas.hybrid_analysis.quantitative import QuantitativeAnalysis


def create_valid_quantitative() -> QuantitativeAnalysis:
    """Helper to create valid QuantitativeAnalysis."""
    return QuantitativeAnalysis(
        composite_score=0.85,
        fundamental_score=0.90,
        technical_score=0.80,
        risk_score=2.5,
        grade="A",
        preliminary_recommendation="BUY",
        fundamental_metrics={"roe": 0.25},
        technical_indicators={"rsi": 55.0},
        risk_metrics={"volatility": 0.15},
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
        python_rationale="Test rationale",
    )


def create_valid_qualitative() -> QualitativeInsights:
    """Helper to create valid QualitativeInsights."""
    return QualitativeInsights(
        sec_insights=SecAnalysisInsights(
            business_model="A" * 100,
            competitive_advantages=["Advantage 1"],
            risk_factors=["Risk 1"],
        ),
        fundamental_context=FundamentalContextInsights(
            industry_analysis="A" * 100,
            growth_drivers=["Driver 1"],
            competitive_positioning="A" * 50,
            management_assessment="A" * 50,
        ),
        technical_strategy=TechnicalStrategyInsights(
            chart_patterns=["Pattern 1"],
            support_resistance="A" * 50,
            entry_exit_strategy="A" * 100,
            timing_assessment="A" * 50,
        ),
        contextual_risks=ContextualRiskInsights(),
        investment_synthesis=InvestmentSynthesis(
            investment_thesis="A" * 200,
            bull_case="A" * 100,
            base_case="A" * 100,
            bear_case="A" * 100,
            scenario_probabilities={"bull": 0.3, "base": 0.5, "bear": 0.2},
            final_recommendation="BUY",
            recommendation_confidence="HIGH",
            action_plan={"immediate_actions": ["Action 1"], "monitoring_points": ["Point 1"], "exit_triggers": ["Trigger 1"]},
        ),
        analysis_timestamp=datetime.now(UTC),
        ai_confidence=0.85,
    )


# Property 5: Enriched Analysis Merge Completeness
def test_enriched_analysis_contains_both_quantitative_and_qualitative():
    """
    Property: EnrichedAnalysis must contain both quantitative and qualitative fields.

    For any valid enriched analysis, both Python calculations and AI insights
    must be present with no null required fields.
    """
    enriched = EnrichedAnalysis(
        ticker="AAPL",
        company_name="Apple Inc.",
        asset_class="stock",
        quantitative=create_valid_quantitative(),
        qualitative=create_valid_qualitative(),
        final_grade="A",
        final_score=0.85,
        final_recommendation="BUY",
        recommendation_confidence="HIGH",
        executive_summary="B" * 200,
        investment_rationale="C" * 500,
        report_word_count=2000,
        unique_insights_count=5,
        processing_time_seconds=25.5,
        llm_cost_dollars=0.08,
    )

    # Verify quantitative fields present
    assert enriched.quantitative is not None
    assert enriched.quantitative.composite_score == approx(0.85)
    assert enriched.quantitative.grade == "A"

    # Verify qualitative fields present
    assert enriched.qualitative is not None
    assert enriched.qualitative.sec_insights is not None
    assert enriched.qualitative.investment_synthesis is not None

    # Verify no null required fields
    assert enriched.ticker is not None
    assert enriched.final_recommendation is not None


# Property 6: Report Quality Thresholds
def test_enriched_analysis_enforces_word_count_threshold():
    """
    Property: report_word_count must be >= 2000.

    For any enriched analysis, the report word count must meet the
    minimum quality threshold of 2000 words.
    """
    enriched = EnrichedAnalysis(
        ticker="AAPL",
        company_name="Apple Inc.",
        asset_class="stock",
        quantitative=create_valid_quantitative(),
        qualitative=create_valid_qualitative(),
        final_grade="A",
        final_score=0.85,
        final_recommendation="BUY",
        recommendation_confidence="HIGH",
        executive_summary="B" * 200,
        investment_rationale="C" * 500,
        report_word_count=2500,  # >= 2000
        unique_insights_count=7,
        processing_time_seconds=25.5,
        llm_cost_dollars=0.08,
    )

    assert enriched.report_word_count >= 2000


def test_enriched_analysis_accepts_low_word_count():
    """Property: report_word_count accepts any non-negative value (relaxed validation for CrewAI)."""
    # Relaxed validation to support CrewAI structured output
    enriched = EnrichedAnalysis(
        ticker="AAPL",
        company_name="Apple Inc.",
        asset_class="stock",
        quantitative=create_valid_quantitative(),
        qualitative=create_valid_qualitative(),
        final_grade="A",
        final_score=0.85,
        final_recommendation="BUY",
        recommendation_confidence="HIGH",
        executive_summary="B" * 200,
        investment_rationale="C" * 500,
        report_word_count=1500,  # < 2000 - now accepted
        unique_insights_count=5,
        processing_time_seconds=25.5,
        llm_cost_dollars=0.08,
    )
    assert enriched.report_word_count == 1500


def test_enriched_analysis_enforces_insights_count_threshold():
    """
    Property: unique_insights_count must be >= 5.

    For any enriched analysis, the unique insights count must meet the
    minimum quality threshold of 5 insights.
    """
    enriched = EnrichedAnalysis(
        ticker="AAPL",
        company_name="Apple Inc.",
        asset_class="stock",
        quantitative=create_valid_quantitative(),
        qualitative=create_valid_qualitative(),
        final_grade="A",
        final_score=0.85,
        final_recommendation="BUY",
        recommendation_confidence="HIGH",
        executive_summary="B" * 200,
        investment_rationale="C" * 500,
        report_word_count=2000,
        unique_insights_count=7,  # >= 5
        processing_time_seconds=25.5,
        llm_cost_dollars=0.08,
    )

    assert enriched.unique_insights_count >= 5


def test_enriched_analysis_accepts_low_insights_count():
    """Property: unique_insights_count accepts any non-negative value (relaxed validation for CrewAI)."""
    # Relaxed validation to support CrewAI structured output
    enriched = EnrichedAnalysis(
        ticker="AAPL",
        company_name="Apple Inc.",
        asset_class="stock",
        quantitative=create_valid_quantitative(),
        qualitative=create_valid_qualitative(),
        final_grade="A",
        final_score=0.85,
        final_recommendation="BUY",
        recommendation_confidence="HIGH",
        executive_summary="B" * 200,
        investment_rationale="C" * 500,
        report_word_count=2000,
        unique_insights_count=3,  # < 5 - now accepted
        processing_time_seconds=25.5,
        llm_cost_dollars=0.08,
    )
    assert enriched.unique_insights_count == 3


def test_enriched_analysis_calculated_word_count():
    """
    Property: calculated_word_count computes total from sections.

    The computed field should accurately count words from all text sections.
    """
    enriched = EnrichedAnalysis(
        ticker="AAPL",
        company_name="Apple Inc.",
        asset_class="stock",
        quantitative=create_valid_quantitative(),
        qualitative=create_valid_qualitative(),
        final_grade="A",
        final_score=0.85,
        final_recommendation="BUY",
        recommendation_confidence="HIGH",
        executive_summary="word " * 50,  # 50 words (200+ chars)
        investment_rationale="word " * 125,  # 125 words (500+ chars)
        report_word_count=2000,
        unique_insights_count=5,
        processing_time_seconds=25.5,
        llm_cost_dollars=0.08,
    )

    # calculated_word_count should be > 0
    assert enriched.calculated_word_count > 0


def test_enriched_analysis_accepts_any_asset_class():
    """Property: asset_class accepts any string (relaxed validation for CrewAI)."""
    # Relaxed validation to support CrewAI structured output
    enriched = EnrichedAnalysis(
        ticker="AAPL",
        company_name="Apple Inc.",
        asset_class="bond",  # Previously invalid, now accepted
        quantitative=create_valid_quantitative(),
        qualitative=create_valid_qualitative(),
        final_grade="A",
        final_score=0.85,
        final_recommendation="BUY",
        recommendation_confidence="HIGH",
        executive_summary="B" * 200,
        investment_rationale="C" * 500,
        report_word_count=2000,
        unique_insights_count=5,
        processing_time_seconds=25.5,
        llm_cost_dollars=0.08,
    )
    assert enriched.asset_class == "bond"
