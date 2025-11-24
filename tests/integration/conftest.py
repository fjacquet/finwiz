"""
Shared fixtures for integration tests.
"""

from datetime import UTC, datetime

import pytest


@pytest.fixture
def mock_data_collection(mocker):
    """Mock data collection to avoid external API calls."""
    mock_data = {
        "ticker": "AAPL",
        "price": 150.0,
        "volume": 1000000,
        "market_cap": 2500000000000,
    }
    return mocker.patch(
        "finwiz.flows.hybrid_analysis_flow.HybridAnalysisFlow._collect_raw_data",
        return_value=mock_data,
    )


@pytest.fixture
def mock_scorer(mocker):
    """Mock DeepAnalysisScorer to avoid expensive calculations."""
    from finwiz.flow_state import DeepAnalysisResult

    mock_result = DeepAnalysisResult(
        ticker="AAPL",
        asset_class="stock",
        crew_name="deep_analysis",
        composite_score=0.85,
        fundamental_score=0.90,
        technical_score=0.80,
        risk_score=2.5,
        grade="A",
        recommendation="BUY",
        rationale="Strong fundamentals with good technical indicators and manageable risk",
        fundamental_details={"roe": 0.25, "debt_to_equity": 0.5, "revenue_growth": 0.15},
        technical_details={"rsi": 55.0, "macd": 1.2, "trend_strength": 0.75},
        risk_details={"volatility": 0.15, "beta": 1.1, "max_drawdown": 0.20},
        data_freshness_hours=1.0,
        confidence_level=0.90,
        warnings=[],
        data_quality={
            "completeness_score": 0.95,
            "quality_level": "high",
        },
    )

    return mocker.patch(
        "finwiz.flows.hybrid_analysis_flow.DeepAnalysisScorer.calculate_composite_score",
        return_value=mock_result,
    )


@pytest.fixture
def mock_crew_execution(mocker):
    """Mock crew execution to generate quality content that meets all validation requirements."""
    from finwiz.schemas.hybrid_analysis.qualitative import (
        ContextualRiskInsights,
        FundamentalContextInsights,
        InvestmentSynthesis,
        QualitativeInsights,
        SecAnalysisInsights,
        TechnicalStrategyInsights,
    )

    # Generate content that meets minimum length requirements
    business_model = " ".join(
        [
            "Strong business model with recurring revenue streams and ecosystem lock-in.",
            "The company benefits from vertical integration and platform effects.",
            "High switching costs and network effects create sustainable competitive advantages.",
        ]
    )  # ~100+ chars

    industry_analysis = " ".join(
        [
            "Technology sector showing strong growth with AI adoption driving innovation.",
            "Market dynamics favor established players with scale and resources.",
            "Regulatory environment creating barriers to entry for new competitors.",
        ]
    )  # ~100+ chars

    competitive_positioning = " ".join(
        [
            "Market leader with strong moat and pricing power in core segments.",
            "Differentiated product offering and brand strength.",
        ]
    )  # ~50+ chars

    management_assessment = " ".join(
        [
            "Experienced leadership team with proven track record of execution.",
            "Strong capital allocation and strategic vision.",
        ]
    )  # ~50+ chars

    support_resistance = " ".join(
        [
            "Key support at $140 with strong buying interest.",
            "Resistance at $160 represents previous highs.",
        ]
    )  # ~50+ chars

    entry_exit_strategy = " ".join(
        [
            "Enter on pullback to $145 support level with confirmation.",
            "Target $165 resistance with stop loss at $138.",
            "Scale in gradually to manage risk and optimize entry price.",
        ]
    )  # ~100+ chars

    timing_assessment = " ".join(
        [
            "Favorable technical setup with momentum building.",
            "Volume confirmation supports bullish thesis.",
        ]
    )  # ~50+ chars

    investment_thesis = " ".join(
        [
            "Comprehensive investment thesis based on strong fundamentals and favorable technicals.",
            "The company demonstrates consistent revenue growth and margin expansion.",
            "Market position provides pricing power and competitive advantages.",
            "Technical indicators suggest favorable entry point with upside potential.",
            "Risk-reward profile attractive at current valuation levels.",
        ]
        * 10
    )  # ~200+ words

    bull_case = " ".join(
        [
            "Continued growth in services and AI with margin expansion.",
            "New product categories drive incremental revenue streams.",
            "Market share gains in key segments accelerate growth.",
        ]
        * 2
    )  # ~100+ words

    base_case = " ".join(
        [
            "Steady growth with market share maintenance and dividend growth.",
            "Margins remain stable with operational efficiency improvements.",
            "Share buybacks continue to support earnings per share growth.",
        ]
        * 2
    )  # ~100+ words

    bear_case = " ".join(
        [
            "Regulatory headwinds and competition pressure margins significantly.",
            "Market saturation limits growth opportunities in core markets.",
            "Economic downturn reduces consumer spending on premium products.",
        ]
        * 2
    )  # ~100+ words

    mock_insights = QualitativeInsights(
        sec_insights=SecAnalysisInsights(
            business_model=business_model,
            competitive_advantages=["Brand strength", "Ecosystem lock-in"],
            risk_factors=["Regulatory scrutiny", "Market saturation"],
            strategic_initiatives=["AI integration", "Services expansion"],
        ),
        fundamental_context=FundamentalContextInsights(
            industry_analysis=industry_analysis,
            growth_drivers=["AI adoption", "Cloud services"],
            competitive_positioning=competitive_positioning,
            management_assessment=management_assessment,
        ),
        technical_strategy=TechnicalStrategyInsights(
            chart_patterns=["Bullish flag formation"],
            support_resistance=support_resistance,
            entry_exit_strategy=entry_exit_strategy,
            timing_assessment=timing_assessment,
        ),
        contextual_risks=ContextualRiskInsights(
            regulatory_risks=["Antitrust concerns"],
            geopolitical_risks=["Supply chain disruptions"],
            competitive_risks=["Emerging competitors"],
            operational_risks=["Product delays"],
            stress_scenarios=["Market downturn scenario"],
        ),
        investment_synthesis=InvestmentSynthesis(
            investment_thesis=investment_thesis,
            bull_case=bull_case,
            base_case=base_case,
            bear_case=bear_case,
            scenario_probabilities={"bull": 0.30, "base": 0.50, "bear": 0.20},
            final_recommendation="BUY",
            recommendation_confidence="HIGH",
            action_plan={
                "immediate_actions": ["Initiate position"],
                "monitoring_points": ["Quarterly earnings"],
                "exit_triggers": ["Break below $140"],
            },
        ),
        analysis_timestamp=datetime.now(UTC),
        ai_confidence=0.85,
    )

    # Mock the crew execution by patching analyze_qualitative_insights
    # which is the flow method that executes crews and converts output
    async def mock_analyze_qualitative(holding_data):
        return mock_insights

    return mocker.patch(
        "finwiz.flows.hybrid_analysis_flow.HybridAnalysisFlow.analyze_qualitative_insights",
        side_effect=mock_analyze_qualitative,
    )
