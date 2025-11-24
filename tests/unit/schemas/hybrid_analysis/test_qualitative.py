"""
Property-based tests for qualitative insights schemas.

**Feature: python-ai-hybrid-analysis, Property 4: AI Output Schema Compliance**
**Validates: Requirements 2.2, 2.3, 2.4, 2.5, 2.6**

Tests that QualitativeInsights and sub-schemas properly validate AI-generated
contextual analysis with required fields and constraints.
"""

from datetime import UTC, datetime

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from finwiz.schemas.hybrid_analysis.qualitative import (
    ContextualRiskInsights,
    FundamentalContextInsights,
    InvestmentSynthesis,
    QualitativeInsights,
    SecAnalysisInsights,
    TechnicalStrategyInsights,
)


# Helper strategies for generating valid text
def text_strategy(min_length: int, max_length: int = None):
    """Generate printable ASCII text of specified length (accounts for Pydantic stripping)."""
    if max_length is None:
        max_length = min_length + 100
    # Use 33-126 to exclude space (32) at boundaries, preventing strip issues
    # This ensures stripped length still meets minimum after Pydantic validation
    return st.text(
        min_size=min_length,
        max_size=max_length,
        alphabet=st.characters(min_codepoint=33, max_codepoint=126)
    ).filter(lambda x: len(x.strip()) >= min_length)


# Property 4: AI Output Schema Compliance
@given(
    business_model=text_strategy(100, 200),
    competitive_advantages=st.lists(text_strategy(10, 50), min_size=1, max_size=5),
    risk_factors=st.lists(text_strategy(10, 50), min_size=1, max_size=5),
)
def test_sec_analysis_insights_validates_correctly(
    business_model: str,
    competitive_advantages: list[str],
    risk_factors: list[str],
):
    """
    Property: SecAnalysisInsights validates with required fields.

    For any valid SEC analysis data, the schema should accept and validate it.
    """
    insights = SecAnalysisInsights(
        business_model=business_model,
        competitive_advantages=competitive_advantages,
        risk_factors=risk_factors,
    )

    assert len(insights.business_model) >= 100
    assert len(insights.competitive_advantages) >= 1
    assert len(insights.risk_factors) >= 1


@given(
    industry_analysis=text_strategy(100, 200),
    growth_drivers=st.lists(text_strategy(10, 50), min_size=1, max_size=5),
    competitive_positioning=text_strategy(50, 100),
    management_assessment=text_strategy(50, 100),
)
def test_fundamental_context_insights_validates_correctly(
    industry_analysis: str,
    growth_drivers: list[str],
    competitive_positioning: str,
    management_assessment: str,
):
    """
    Property: FundamentalContextInsights validates with required fields.

    For any valid fundamental context data, the schema should accept it.
    """
    insights = FundamentalContextInsights(
        industry_analysis=industry_analysis,
        growth_drivers=growth_drivers,
        competitive_positioning=competitive_positioning,
        management_assessment=management_assessment,
    )

    assert len(insights.industry_analysis) >= 100
    assert len(insights.growth_drivers) >= 1
    assert len(insights.competitive_positioning) >= 50
    assert len(insights.management_assessment) >= 50


@given(
    chart_patterns=st.lists(text_strategy(10, 50), min_size=1, max_size=5),
    support_resistance=text_strategy(50, 100),
    entry_exit_strategy=text_strategy(100, 200),
    timing_assessment=text_strategy(50, 100),
)
def test_technical_strategy_insights_validates_correctly(
    chart_patterns: list[str],
    support_resistance: str,
    entry_exit_strategy: str,
    timing_assessment: str,
):
    """
    Property: TechnicalStrategyInsights validates with required fields.

    For any valid technical strategy data, the schema should accept it.
    """
    insights = TechnicalStrategyInsights(
        chart_patterns=chart_patterns,
        support_resistance=support_resistance,
        entry_exit_strategy=entry_exit_strategy,
        timing_assessment=timing_assessment,
    )

    assert len(insights.chart_patterns) >= 1
    assert len(insights.support_resistance) >= 50
    assert len(insights.entry_exit_strategy) >= 100
    assert len(insights.timing_assessment) >= 50


def test_contextual_risk_insights_validates_with_empty_lists():
    """
    Property: ContextualRiskInsights accepts empty risk lists.

    All risk fields are optional (default_factory=list).
    """
    insights = ContextualRiskInsights()

    assert insights.regulatory_risks == []
    assert insights.geopolitical_risks == []
    assert insights.competitive_risks == []
    assert insights.operational_risks == []
    assert insights.stress_scenarios == []


@given(
    investment_thesis=text_strategy(200, 300),
    bull_case=text_strategy(100, 150),
    base_case=text_strategy(100, 150),
    bear_case=text_strategy(100, 150),
    recommendation=st.sampled_from(["BUY", "HOLD", "SELL"]),
    confidence=st.sampled_from(["LOW", "MEDIUM", "HIGH"]),
)
def test_investment_synthesis_validates_correctly(
    investment_thesis: str,
    bull_case: str,
    base_case: str,
    bear_case: str,
    recommendation: str,
    confidence: str,
):
    """
    Property: InvestmentSynthesis validates with required fields.

    For any valid investment synthesis data, the schema should accept it.
    """
    synthesis = InvestmentSynthesis(
        investment_thesis=investment_thesis,
        bull_case=bull_case,
        base_case=base_case,
        bear_case=bear_case,
        scenario_probabilities={"bull": 0.3, "base": 0.5, "bear": 0.2},
        final_recommendation=recommendation,
        recommendation_confidence=confidence,
        action_plan={"immediate_actions": ["Action 1"], "monitoring_points": ["Point 1"], "exit_triggers": ["Trigger 1"]},
    )

    assert len(synthesis.investment_thesis) >= 200
    assert len(synthesis.bull_case) >= 100
    assert synthesis.final_recommendation in ["BUY", "HOLD", "SELL"]
    assert synthesis.recommendation_confidence in ["LOW", "MEDIUM", "HIGH"]


def test_qualitative_insights_complete_structure():
    """
    Property: QualitativeInsights requires all sub-schemas.

    All five sub-schemas must be present for a complete qualitative analysis.
    """
    insights = QualitativeInsights(
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

    # Verify all sub-schemas are present
    assert insights.sec_insights is not None
    assert insights.fundamental_context is not None
    assert insights.technical_strategy is not None
    assert insights.contextual_risks is not None
    assert insights.investment_synthesis is not None
    assert 0.0 <= insights.ai_confidence <= 1.0


# Test field constraints
def test_sec_analysis_rejects_short_business_model():
    """Property: business_model must be at least 100 characters."""
    with pytest.raises(ValidationError):
        SecAnalysisInsights(
            business_model="Too short",
            competitive_advantages=["Advantage 1"],
            risk_factors=["Risk 1"],
        )


def test_investment_synthesis_rejects_invalid_recommendation():
    """Property: final_recommendation must be BUY/HOLD/SELL."""
    with pytest.raises(ValidationError):
        InvestmentSynthesis(
            investment_thesis="A" * 200,
            bull_case="A" * 100,
            base_case="A" * 100,
            bear_case="A" * 100,
            scenario_probabilities={"bull": 0.3, "base": 0.5, "bear": 0.2},
            final_recommendation="MAYBE",  # Invalid
            recommendation_confidence="HIGH",
            action_plan={"immediate_actions": ["Action 1"], "monitoring_points": ["Point 1"], "exit_triggers": ["Trigger 1"]},
        )
