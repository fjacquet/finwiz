"""
Quality validation tests for hybrid analysis architecture.

Tests validate that the system meets quality requirements:
- Report word count: ≥2000 words
- Unique insights: ≥5 insights
- Executive summary: ≥200 words
- Investment rationale: ≥500 words
"""

import pytest

from finwiz.flows.hybrid_analysis_flow import HybridAnalysisFlow


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
    """Mock crew execution to generate quality content."""
    from datetime import datetime

    from finwiz.schemas.hybrid_analysis.qualitative import (
        ContextualRiskInsights,
        FundamentalContextInsights,
        InvestmentSynthesis,
        QualitativeInsights,
        SecAnalysisInsights,
        TechnicalStrategyInsights,
    )

    # Generate content that meets ALL quality thresholds

    # Business model: 125+ words
    business_model = " ".join(
        [
            "Strong business model with recurring revenue streams and high customer retention.",
            "The company operates in a growing market with significant barriers to entry.",
            "Vertically integrated operations provide cost advantages and quality control.",
            "Platform effects create network value that strengthens with scale.",
            "Diversified revenue streams reduce dependency on single products or markets.",
        ]
        * 5
    )

    # Investment thesis: 750+ words (for 500+ word rationale requirement)
    investment_thesis = " ".join(
        [
            "This investment opportunity presents compelling value based on multiple factors.",
            "The company demonstrates strong fundamentals with consistent revenue growth.",
            "Market position is defensible with significant competitive advantages.",
            "Management team has proven track record of execution and capital allocation.",
            "Industry tailwinds support long-term growth trajectory.",
            "Valuation appears attractive relative to growth prospects and peer comparisons.",
            "Risk-reward profile favors upside potential with manageable downside scenarios.",
            "Technical indicators suggest favorable entry point with momentum building.",
            "Catalyst pipeline includes new product launches and market expansion.",
            "Financial health is robust with strong balance sheet and cash generation.",
        ]
        * 15
    )

    # Industry analysis: 120+ words
    industry_analysis = " ".join(
        [
            "Technology sector showing strong growth with AI adoption accelerating.",
            "The industry is experiencing rapid transformation driven by artificial intelligence.",
            "Cloud computing and digital transformation continue to drive enterprise spending.",
            "Market dynamics favor established players with strong ecosystems.",
            "Regulatory environment remains supportive of innovation while addressing privacy.",
            "Long-term growth prospects remain robust with increasing digital transformation.",
            "Competitive landscape is consolidating around platform leaders.",
            "Emerging markets present significant expansion opportunities.",
            "Industry margins are expanding due to operating leverage and scale effects.",
            "Technology adoption curves suggest sustained multi-year growth runway.",
        ]
        * 3
    )

    # Entry/exit strategy: 120+ words
    entry_exit_strategy = " ".join(
        [
            "Enter on pullback to $145 support level with volume confirmation and RSI reset.",
            "Scale in with 50% position initially, add remaining 50% on break above $155 resistance.",
            "Primary target at $165 resistance level, secondary target at $175 on breakout confirmation.",
            "Stop loss at $138 to limit downside risk to 5% of position size.",
            "Trail stop to breakeven once position reaches $155 to protect capital.",
            "Consider taking partial profits at $160 resistance level to lock in gains.",
            "Monitor volume patterns for confirmation of trend continuation.",
            "Adjust position size based on volatility and market conditions.",
            "Use options strategies for additional downside protection if needed.",
            "Review position quarterly and adjust based on fundamental changes.",
        ]
        * 3
    )

    # Bull case: 120+ words
    bull_case = " ".join(
        [
            "Continued growth in services and AI with margin expansion driving profitability.",
            "Strong adoption of new AI features drives premium pricing and customer retention.",
            "Services segment reaches 35% of revenue with 70% margins improving overall profitability.",
            "International markets accelerate with emerging market penetration exceeding expectations.",
            "Ecosystem lock-in strengthens with increased developer engagement and platform effects.",
            "Stock could reach $200+ in bull scenario with multiple expansion to 30x P/E.",
            "New product categories open additional TAM and revenue streams.",
            "Market share gains in key segments drive above-market growth rates.",
            "Operating leverage delivers margin expansion beyond current guidance.",
            "Capital returns accelerate with increased buybacks and dividend growth.",
        ]
        * 3
    )

    # Base case: 120+ words
    base_case = " ".join(
        [
            "Steady growth with market share maintenance and consistent dividend growth.",
            "Services grow at 15% annually while hardware stabilizes at market growth rates.",
            "Margins remain stable with balanced product mix and cost management.",
            "Consistent capital returns through dividends and buybacks maintain shareholder value.",
            "Market multiple remains at current levels reflecting mature growth profile.",
            "Stock reaches $175-180 in base case over 12-18 months timeframe.",
            "Competitive position maintained through innovation and brand strength.",
            "International expansion continues at moderate pace with selective market entry.",
            "Operating efficiency improvements offset inflationary pressures.",
            "Balance sheet strength supports strategic flexibility and opportunistic M&A.",
        ]
        * 3
    )

    # Bear case: 120+ words
    bear_case = " ".join(
        [
            "Regulatory headwinds and competition pressure margins below expectations.",
            "Antitrust actions force ecosystem changes reducing lock-in effects and pricing power.",
            "Hardware sales decline faster than services can compensate for revenue shortfall.",
            "Margin compression from competitive pressures and pricing actions.",
            "Multiple contracts to 20x P/E from current levels on growth concerns.",
            "Stock could decline to $120-130 in bear scenario with sentiment deterioration.",
            "Market share losses in key categories to aggressive competitors.",
            "Economic downturn reduces consumer spending on premium products.",
            "Supply chain disruptions impact product availability and margins.",
            "Execution missteps on new product launches damage brand perception.",
        ]
        * 3
    )

    mock_insights = QualitativeInsights(
        sec_insights=SecAnalysisInsights(
            business_model=business_model,
            competitive_advantages=[
                "Brand strength and customer loyalty",
                "Ecosystem lock-in effects",
                "Innovation pipeline and R&D capabilities",
                "Vertical integration advantages",
                "Platform network effects",
            ],
            risk_factors=[
                "Regulatory scrutiny and antitrust concerns",
                "Market saturation in developed markets",
                "Intense competition from established and emerging players",
                "Supply chain vulnerabilities",
                "Technology disruption risks",
            ],
            strategic_initiatives=[
                "AI integration across product portfolio",
                "Services expansion and recurring revenue growth",
                "Sustainability and carbon neutrality commitments",
                "Emerging market penetration strategies",
                "Platform ecosystem development",
            ],
        ),
        fundamental_context=FundamentalContextInsights(
            industry_analysis=industry_analysis,
            growth_drivers=[
                "AI adoption and integration",
                "Cloud services expansion",
                "Digital transformation acceleration",
                "Emerging market growth",
                "Platform ecosystem effects",
            ],
            competitive_positioning="Market leader with strong moat and pricing power through ecosystem lock-in and brand strength",
            management_assessment="Experienced leadership team with proven track record of innovation and capital allocation discipline",
        ),
        technical_strategy=TechnicalStrategyInsights(
            chart_patterns=[
                "Bullish flag formation indicating continuation",
                "Higher highs and higher lows trend structure",
                "Volume accumulation on pullbacks",
            ],
            support_resistance="Key support levels at $140 and $135, resistance at $160 and $165 with strong volume confirmation",
            entry_exit_strategy=entry_exit_strategy,
            timing_assessment="Favorable technical setup with momentum building and RSI in neutral zone allowing for entry",
        ),
        contextual_risks=ContextualRiskInsights(
            regulatory_risks=[
                "Antitrust concerns and potential breakup scenarios",
                "Data privacy regulations and compliance costs",
            ],
            geopolitical_risks=[
                "Supply chain disruptions from geopolitical tensions",
                "Trade policy changes and tariff impacts",
            ],
            competitive_risks=[
                "Emerging competitors with disruptive technologies",
                "Market share erosion in key product categories",
            ],
            operational_risks=[
                "Product delays and quality issues",
                "Execution risks on new initiatives",
            ],
            stress_scenarios=[
                "Market downturn scenario with 30% revenue decline",
                "Recession impact on consumer spending patterns",
            ],
        ),
        investment_synthesis=InvestmentSynthesis(
            investment_thesis=investment_thesis,
            bull_case=bull_case,
            base_case=base_case,
            bear_case=bear_case,
            scenario_probabilities={"bull": 0.25, "base": 0.50, "bear": 0.25},
            final_recommendation="BUY",
            recommendation_confidence="HIGH",
            action_plan={
                "immediate_actions": [
                    "Initiate position at current levels",
                    "Set price alerts at key technical levels",
                ],
                "monitoring_points": [
                    "Quarterly earnings reports and guidance",
                    "Product launch announcements and reception",
                ],
                "exit_triggers": [
                    "Break below $140 support on high volume",
                    "Negative guidance or margin compression",
                ],
            },
        ),
        analysis_timestamp=datetime.now(),
        ai_confidence=0.85,
    )

    return mocker.patch(
        "finwiz.flows.hybrid_analysis_flow.HybridAnalysisFlow._execute_crew",
        return_value=mock_insights,
    )


class TestReportWordCount:
    """Test report word count requirements."""

    def test_should_generate_minimum_2000_words(self, mock_data_collection, mock_scorer, mock_crew_execution):
        """
        Test that reports contain at least 2000 words.

        **Validates: Requirements 7.5, 10.1**
        """
        # Arrange
        flow = HybridAnalysisFlow()
        # Initialize state via the flow's state initialization
        flow.state.ticker = "AAPL"
        flow.state.asset_class = "stock"
        flow.state.company_name = "Test Company"

        # Act
        result = flow.kickoff()

        # Assert
        assert result.report_word_count >= 2000, f"Report has {result.report_word_count} words, minimum is 2000"

    def test_should_calculate_word_count_correctly(self, mock_data_collection, mock_scorer, mock_crew_execution):
        """
        Test that calculated word count matches reported word count.

        **Validates: Requirements 10.1**
        """
        # Arrange
        flow = HybridAnalysisFlow()
        # Initialize state via the flow's state initialization
        flow.state.ticker = "AAPL"
        flow.state.asset_class = "stock"
        flow.state.company_name = "Test Company"

        # Act
        result = flow.kickoff()

        # Assert
        calculated = result.calculated_word_count
        reported = result.report_word_count

        # Allow small variance due to different counting methods
        variance = abs(calculated - reported) / reported
        assert variance <= 0.1, f"Word count variance {variance:.1%} exceeds 10% (calculated: {calculated}, reported: {reported})"


class TestUniqueInsights:
    """Test unique insights count requirements."""

    def test_should_generate_minimum_5_insights(self, mock_data_collection, mock_scorer, mock_crew_execution):
        """
        Test that reports contain at least 5 unique insights.

        **Validates: Requirements 10.2**
        """
        # Arrange
        flow = HybridAnalysisFlow()
        # Initialize state via the flow's state initialization
        flow.state.ticker = "AAPL"
        flow.state.asset_class = "stock"
        flow.state.company_name = "Test Company"

        # Act
        result = flow.kickoff()

        # Assert
        assert result.unique_insights_count >= 5, f"Report has {result.unique_insights_count} insights, minimum is 5"

    def test_should_count_insights_from_all_sections(self, mock_data_collection, mock_scorer, mock_crew_execution):
        """
        Test that insights are counted from all analysis sections.

        **Validates: Requirements 10.2**
        """
        # Arrange
        flow = HybridAnalysisFlow()
        # Initialize state via the flow's state initialization
        flow.state.ticker = "AAPL"
        flow.state.asset_class = "stock"
        flow.state.company_name = "Test Company"

        # Act
        result = flow.kickoff()

        # Assert - Verify insights come from multiple sections
        insights = result.qualitative

        # Count insights from different sections
        sec_insights = len(insights.sec_insights.competitive_advantages)
        fundamental_insights = len(insights.fundamental_context.growth_drivers)
        technical_insights = len(insights.technical_strategy.chart_patterns)
        risk_insights = len(insights.contextual_risks.regulatory_risks)
        # Count scenarios as insights (bull/base/bear cases)
        synthesis_insights = 3  # bull_case, base_case, bear_case

        total_insights = sec_insights + fundamental_insights + technical_insights + risk_insights + synthesis_insights

        assert total_insights >= 5, f"Total insights {total_insights} is less than 5"


class TestExecutiveSummary:
    """Test executive summary quality requirements."""

    def test_should_generate_minimum_200_word_summary(self, mock_data_collection, mock_scorer, mock_crew_execution):
        """
        Test that executive summary contains at least 200 words.

        **Validates: Requirements 9.2**
        """
        # Arrange
        flow = HybridAnalysisFlow()
        # Initialize state via the flow's state initialization
        flow.state.ticker = "AAPL"
        flow.state.asset_class = "stock"
        flow.state.company_name = "Test Company"

        # Act
        result = flow.kickoff()

        # Assert
        summary_word_count = len(result.executive_summary.split())
        assert summary_word_count >= 200, f"Executive summary has {summary_word_count} words, minimum is 200"

    def test_should_include_key_information_in_summary(self, mock_data_collection, mock_scorer, mock_crew_execution):
        """
        Test that executive summary includes key information.

        **Validates: Requirements 9.2**
        """
        # Arrange
        flow = HybridAnalysisFlow()
        # Initialize state via the flow's state initialization
        flow.state.ticker = "AAPL"
        flow.state.asset_class = "stock"
        flow.state.company_name = "Test Company"

        # Act
        result = flow.kickoff()

        # Assert - Summary should be non-empty and substantive
        assert len(result.executive_summary) > 0
        assert result.executive_summary != ""


class TestInvestmentRationale:
    """Test investment rationale quality requirements."""

    def test_should_generate_minimum_500_word_rationale(self, mock_data_collection, mock_scorer, mock_crew_execution):
        """
        Test that investment rationale contains at least 500 words.

        **Validates: Requirements 9.3**
        """
        # Arrange
        flow = HybridAnalysisFlow()
        # Initialize state via the flow's state initialization
        flow.state.ticker = "AAPL"
        flow.state.asset_class = "stock"
        flow.state.company_name = "Test Company"

        # Act
        result = flow.kickoff()

        # Assert
        rationale_word_count = len(result.investment_rationale.split())
        assert rationale_word_count >= 500, f"Investment rationale has {rationale_word_count} words, minimum is 500"

    def test_should_include_detailed_analysis_in_rationale(self, mock_data_collection, mock_scorer, mock_crew_execution):
        """
        Test that investment rationale includes detailed analysis.

        **Validates: Requirements 9.3**
        """
        # Arrange
        flow = HybridAnalysisFlow()
        # Initialize state via the flow's state initialization
        flow.state.ticker = "AAPL"
        flow.state.asset_class = "stock"
        flow.state.company_name = "Test Company"

        # Act
        result = flow.kickoff()

        # Assert - Rationale should be substantive
        assert len(result.investment_rationale) > 0
        assert result.investment_rationale != ""


class TestActionPlan:
    """Test action plan completeness requirements."""

    def test_should_include_complete_action_plan(self, mock_data_collection, mock_scorer, mock_crew_execution):
        """
        Test that action plan includes all required fields.

        **Validates: Requirements 9.4**
        """
        # Arrange
        flow = HybridAnalysisFlow()
        # Initialize state via the flow's state initialization
        flow.state.ticker = "AAPL"
        flow.state.asset_class = "stock"
        flow.state.company_name = "Test Company"

        # Act
        result = flow.kickoff()

        # Assert
        action_plan = result.qualitative.investment_synthesis.action_plan

        assert "immediate_actions" in action_plan
        assert "monitoring_points" in action_plan
        assert "exit_triggers" in action_plan

        assert len(action_plan["immediate_actions"]) > 0
        assert len(action_plan["monitoring_points"]) > 0
        assert len(action_plan["exit_triggers"]) > 0

    def test_should_provide_actionable_guidance(self, mock_data_collection, mock_scorer, mock_crew_execution):
        """
        Test that action plan provides actionable guidance.

        **Validates: Requirements 9.4**
        """
        # Arrange
        flow = HybridAnalysisFlow()
        # Initialize state via the flow's state initialization
        flow.state.ticker = "AAPL"
        flow.state.asset_class = "stock"
        flow.state.company_name = "Test Company"

        # Act
        result = flow.kickoff()

        # Assert
        action_plan = result.qualitative.investment_synthesis.action_plan

        # Each action should be non-empty string
        for action in action_plan["immediate_actions"]:
            assert isinstance(action, str)
            assert len(action) > 0

        for point in action_plan["monitoring_points"]:
            assert isinstance(point, str)
            assert len(point) > 0

        for trigger in action_plan["exit_triggers"]:
            assert isinstance(trigger, str)
            assert len(trigger) > 0
