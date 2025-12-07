"""
Property-based tests for qualitative insights schemas.

**Feature: python-ai-hybrid-analysis, Property 4: AI Output Schema Compliance**
**Validates: Requirements 2.2, 2.3, 2.4, 2.5, 2.6**

Tests that QualitativeInsights and sub-schemas properly validate AI-generated
contextual analysis with required fields and constraints.
"""

from datetime import UTC, datetime

from hypothesis import given
from hypothesis import strategies as st

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
    return st.text(min_size=min_length, max_size=max_length, alphabet=st.characters(min_codepoint=33, max_codepoint=126)).filter(lambda x: len(x.strip()) >= min_length)


# Property 4: AI Output Schema Compliance
# Use printable characters to avoid whitespace-only strings that get stripped
printable_text = st.text(alphabet=st.characters(min_codepoint=33, max_codepoint=126), min_size=0, max_size=50)


@given(
    business_model=printable_text,
    competitive_advantages=st.lists(printable_text, min_size=0, max_size=5),
    risk_factors=st.lists(printable_text, min_size=0, max_size=5),
)
def test_sec_analysis_insights_validates_correctly(
    business_model: str,
    competitive_advantages: list[str],
    risk_factors: list[str],
):
    """
    Property: SecAnalysisInsights validates with any fields (relaxed validation).

    For any SEC analysis data, the schema should accept it with relaxed validation.
    """
    insights = SecAnalysisInsights(
        business_model=business_model,
        competitive_advantages=competitive_advantages,
        risk_factors=risk_factors,
    )

    # Relaxed: just verify schema creation succeeds
    assert insights is not None
    assert isinstance(insights.business_model, str)
    assert isinstance(insights.competitive_advantages, list)
    assert isinstance(insights.risk_factors, list)


@given(
    industry_analysis=printable_text,
    growth_drivers=st.lists(printable_text, min_size=0, max_size=5),
    competitive_positioning=printable_text,
    management_assessment=printable_text,
)
def test_fundamental_context_insights_validates_correctly(
    industry_analysis: str,
    growth_drivers: list[str],
    competitive_positioning: str,
    management_assessment: str,
):
    """
    Property: FundamentalContextInsights validates with any fields (relaxed validation).

    For any fundamental context data, the schema should accept it.
    """
    insights = FundamentalContextInsights(
        industry_analysis=industry_analysis,
        growth_drivers=growth_drivers,
        competitive_positioning=competitive_positioning,
        management_assessment=management_assessment,
    )

    # Relaxed: just verify schema creation succeeds
    assert insights is not None
    assert isinstance(insights.industry_analysis, str)
    assert isinstance(insights.growth_drivers, list)
    assert isinstance(insights.competitive_positioning, str)
    assert isinstance(insights.management_assessment, str)


@given(
    chart_patterns=st.lists(printable_text, min_size=0, max_size=5),
    support_resistance=printable_text,
    entry_exit_strategy=printable_text,
    timing_assessment=printable_text,
)
def test_technical_strategy_insights_validates_correctly(
    chart_patterns: list[str],
    support_resistance: str,
    entry_exit_strategy: str,
    timing_assessment: str,
):
    """
    Property: TechnicalStrategyInsights validates with any fields (relaxed validation).

    For any technical strategy data, the schema should accept it.
    """
    insights = TechnicalStrategyInsights(
        chart_patterns=chart_patterns,
        support_resistance=support_resistance,
        entry_exit_strategy=entry_exit_strategy,
        timing_assessment=timing_assessment,
    )

    # Relaxed: just verify schema creation succeeds
    assert insights is not None
    assert isinstance(insights.chart_patterns, list)
    assert isinstance(insights.support_resistance, str)
    assert isinstance(insights.entry_exit_strategy, str)
    assert isinstance(insights.timing_assessment, str)


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
    investment_thesis=printable_text,
    bull_case=printable_text,
    base_case=printable_text,
    bear_case=printable_text,
    recommendation=printable_text,
    confidence=printable_text,
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
    Property: InvestmentSynthesis validates with any fields (relaxed validation).

    For any investment synthesis data, the schema should accept it.
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

    # Relaxed: just verify schema creation succeeds
    assert synthesis is not None
    assert isinstance(synthesis.investment_thesis, str)
    assert isinstance(synthesis.bull_case, str)
    assert isinstance(synthesis.final_recommendation, str)
    assert isinstance(synthesis.recommendation_confidence, str)


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
def test_sec_analysis_accepts_short_business_model():
    """Property: business_model accepts any string (relaxed validation for CrewAI)."""
    # Relaxed validation to support CrewAI structured output
    insights = SecAnalysisInsights(
        business_model="Too short",
        competitive_advantages=["Advantage 1"],
        risk_factors=["Risk 1"],
    )
    assert insights.business_model == "Too short"


def test_investment_synthesis_accepts_any_recommendation():
    """Property: final_recommendation accepts any string (relaxed validation for CrewAI)."""
    # Relaxed validation to support CrewAI structured output
    synthesis = InvestmentSynthesis(
        investment_thesis="A" * 200,
        bull_case="A" * 100,
        base_case="A" * 100,
        bear_case="A" * 100,
        scenario_probabilities={"bull": 0.3, "base": 0.5, "bear": 0.2},
        final_recommendation="MAYBE",  # Previously invalid, now accepted
        recommendation_confidence="HIGH",
        action_plan={"immediate_actions": ["Action 1"], "monitoring_points": ["Point 1"], "exit_triggers": ["Trigger 1"]},
    )
    assert synthesis.final_recommendation == "MAYBE"
