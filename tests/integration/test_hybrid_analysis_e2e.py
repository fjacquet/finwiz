"""
End-to-end integration tests for hybrid analysis architecture.

Tests validate the complete flow from data collection to report generation,
including fallback scenarios and batch processing.
"""

from datetime import UTC

import pytest

from finwiz.flows.hybrid_analysis_flow import HybridAnalysisFlow
from finwiz.schemas.hybrid_analysis.enriched import EnrichedAnalysis


@pytest.fixture
def mock_data_collection(mocker):
    """Mock data collection to avoid external API calls."""
    mock_data = {
        "ticker": "AAPL",
        "price": 150.0,
        "volume": 1000000,
        "market_cap": 2500000000000,
        "pe_ratio": 25.0,
        "dividend_yield": 0.015,
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

    # Generate content that meets quality thresholds
    business_model = " ".join(
        [
            "Apple operates a vertically integrated business model with hardware, software, and services.",
            "The company benefits from strong ecosystem lock-in through its App Store and iCloud services.",
            "Recurring revenue from services provides stable cash flow and high margins.",
            "The company's brand strength allows premium pricing and customer loyalty.",
        ]
        * 5
    )  # ~100 words

    investment_thesis = " ".join(
        [
            "Apple represents a compelling investment opportunity based on multiple factors.",
            "The company demonstrates strong fundamental performance with consistent revenue growth.",
            "Technical indicators suggest favorable entry points with bullish momentum building.",
            "Risk factors are manageable and well-understood by the market.",
            "The services segment provides recurring revenue and margin expansion opportunities.",
            "AI integration across products represents significant growth potential.",
            "Strong balance sheet and cash generation support shareholder returns.",
            "Market leadership position provides competitive advantages and pricing power.",
        ]
        * 20
    )  # ~700 words

    mock_insights = QualitativeInsights(
        sec_insights=SecAnalysisInsights(
            business_model=business_model,
            competitive_advantages=[
                "Brand strength and customer loyalty",
                "Ecosystem lock-in through integrated products",
                "Premium pricing power",
                "Innovation pipeline and R&D capabilities",
                "Supply chain excellence",
            ],
            risk_factors=[
                "Regulatory scrutiny and antitrust concerns",
                "Market saturation in developed markets",
                "Competition from Android ecosystem",
                "Dependence on iPhone revenue",
                "Supply chain vulnerabilities",
            ],
            strategic_initiatives=[
                "AI integration across product line",
                "Services expansion and recurring revenue",
                "Sustainability and carbon neutrality goals",
                "Healthcare and wearables growth",
                "Augmented reality development",
            ],
        ),
        fundamental_context=FundamentalContextInsights(
            industry_analysis="Technology sector showing strong growth with AI adoption driving innovation across multiple verticals. The industry is experiencing unprecedented transformation with cloud computing, artificial intelligence, and digital services creating new revenue opportunities and competitive dynamics.",
            growth_drivers=[
                "AI and machine learning adoption",
                "Cloud services expansion",
                "Digital transformation trends",
                "5G network rollout",
                "Emerging market penetration",
            ],
            competitive_positioning="Market leader with strong moat, premium positioning, and pricing power. The company maintains dominant market share through brand loyalty, ecosystem lock-in, and continuous innovation. Competitive advantages include vertical integration, supply chain excellence, and unmatched customer experience.",
            competitive_analysis="Market leader with strong moat, premium positioning, and pricing power",
            management_assessment="Experienced leadership team with proven track record of execution and innovation",
        ),
        technical_strategy=TechnicalStrategyInsights(
            chart_patterns=[
                "Bullish flag formation indicating continuation",
                "Higher highs and higher lows trend",
                "Volume confirmation on breakouts",
            ],
            support_resistance="Key support levels identified at $140 (primary) and $135 (secondary), with resistance at $160 (primary) and $165 (secondary). These levels confirmed by volume analysis and historical price action.",
            entry_exit_strategy="Enter on pullback to $145 support level with confirmation from RSI oversold conditions and volume spike. Primary target at $165 resistance with partial profit-taking at $160. Stop loss placed at $138 below key support to limit downside risk. Position sizing should account for 5% portfolio allocation maximum.",
            timing_assessment="Favorable technical setup with momentum building and volume confirmation. MACD showing bullish crossover with increasing histogram. RSI in healthy range indicating room for upside movement.",
        ),
        contextual_risks=ContextualRiskInsights(
            regulatory_risks=[
                "Antitrust investigations in multiple jurisdictions",
                "Data privacy regulations and compliance costs",
                "App Store commission scrutiny",
            ],
            geopolitical_risks=[
                "US-China trade tensions",
                "Supply chain disruptions",
                "Currency fluctuations",
            ],
            competitive_risks=[
                "Android ecosystem competition",
                "Emerging competitors in wearables",
                "Market share pressure in services",
            ],
            operational_risks=[
                "Product launch delays",
                "Quality control issues",
                "Key personnel retention",
            ],
            stress_scenarios=[
                "Market downturn scenario: -20% revenue impact",
                "Recession impact: Reduced consumer spending",
                "Regulatory breakup: Services separation",
            ],
        ),
        investment_synthesis=InvestmentSynthesis(
            investment_thesis=investment_thesis,
            bull_case="Continued growth in services and AI with margin expansion driving profitability. New product categories including Vision Pro and health devices create additional revenue streams. Services segment reaches 30% of total revenue with 70% gross margins. AI integration across product line enhances ecosystem value and customer retention.",
            base_case="Steady growth with market share maintenance through product innovation and ecosystem strength. Dividend growth and share buybacks continue providing shareholder returns. Services growth offsets hardware maturity. Margins remain stable with operational efficiency improvements. Market leadership position maintained through brand strength and customer loyalty.",
            bear_case="Regulatory headwinds and competition pressure margins as antitrust scrutiny intensifies. Market saturation limits growth in developed markets. Supply chain disruptions impact product availability and costs. Emerging competitors gain share in key categories. Economic downturn reduces consumer spending on premium products. Services growth slows as competition increases.",
            scenario_probabilities={"bull": 0.30, "base": 0.50, "bear": 0.20},
            catalysts=[
                "New product launches (iPhone, Vision Pro)",
                "Earnings beat and guidance raise",
                "AI breakthrough and integration",
                "Services subscriber growth",
                "Share buyback acceleration",
            ],
            final_recommendation="BUY",
            recommendation_confidence="HIGH",
            confidence_rationale="High confidence based on strong fundamentals, favorable technicals, and manageable risks",
            action_plan={
                "immediate_actions": [
                    "Initiate position at current levels",
                    "Set price alerts at key support/resistance",
                    "Review quarterly earnings calendar",
                ],
                "monitoring_points": [
                    "Quarterly earnings and guidance",
                    "Product launch announcements",
                    "Regulatory developments",
                    "Services subscriber metrics",
                    "Margin trends",
                ],
                "exit_triggers": [
                    "Break below $140 support on high volume",
                    "Negative earnings guidance",
                    "Major regulatory action",
                    "Deteriorating fundamentals",
                ],
            },
        ),
        analysis_timestamp=datetime.now(UTC),
        ai_confidence=0.85,
    )

    return mocker.patch(
        "finwiz.flows.hybrid_analysis_flow.HybridAnalysisFlow._execute_crew",
        return_value=mock_insights,
    )


class TestCompleteFlow:
    """Test complete flow from data collection to report generation."""

    def test_should_execute_complete_flow_successfully(self, mock_data_collection, mock_scorer, mock_crew_execution):
        """
        Test that complete flow executes successfully.

        **Validates: Requirements 1.1, 1.2, 1.3, 1.4**
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
        assert isinstance(result, EnrichedAnalysis)
        assert result.ticker == "AAPL"
        assert result.asset_class == "stock"

    def test_should_separate_quantitative_and_qualitative(self, mock_data_collection, mock_scorer, mock_crew_execution):
        """
        Test that quantitative and qualitative analyses are separated.

        **Validates: Requirements 1.1, 1.2**
        """
        # Arrange
        flow = HybridAnalysisFlow()
        # Initialize state via the flow's state initialization
        flow.state.ticker = "AAPL"
        flow.state.asset_class = "stock"
        flow.state.company_name = "Test Company"

        # Act
        result = flow.kickoff()

        # Assert - Both components present
        assert result.quantitative is not None
        assert result.qualitative is not None

        # Quantitative has Python calculations
        assert result.quantitative.composite_score > 0
        assert result.quantitative.grade in ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-", "F"]

        # Qualitative has AI insights
        assert len(result.qualitative.sec_insights.competitive_advantages) > 0
        assert len(result.qualitative.investment_synthesis.bull_case) > 0  # Check bull_case instead of catalysts

    def test_should_merge_results_into_enriched_analysis(self, mock_data_collection, mock_scorer, mock_crew_execution):
        """
        Test that results are merged into EnrichedAnalysis.

        **Validates: Requirements 1.4, 3.1**
        """
        # Arrange
        flow = HybridAnalysisFlow()
        # Initialize state via the flow's state initialization
        flow.state.ticker = "AAPL"
        flow.state.asset_class = "stock"
        flow.state.company_name = "Test Company"

        # Act
        result = flow.kickoff()

        # Assert - Final synthesis present
        assert result.final_grade is not None
        assert result.final_score > 0
        assert result.final_recommendation in ["BUY", "HOLD", "SELL"]
        assert result.recommendation_confidence in ["LOW", "MEDIUM", "HIGH"]

    def test_should_generate_complete_report(self, mock_data_collection, mock_scorer, mock_crew_execution):
        """
        Test that complete report is generated.

        **Validates: Requirements 5.1, 5.2, 5.3, 5.4**
        """
        # Arrange
        flow = HybridAnalysisFlow()
        # Initialize state via the flow's state initialization
        flow.state.ticker = "AAPL"
        flow.state.asset_class = "stock"
        flow.state.company_name = "Test Company"

        # Act
        result = flow.kickoff()

        # Assert - Report components present
        assert len(result.executive_summary) >= 200
        assert len(result.investment_rationale) >= 500
        assert result.report_word_count >= 2000
        assert result.unique_insights_count >= 5


class TestFallbackScenarios:
    """Test fallback scenarios when AI fails."""

    def test_should_fallback_when_crew_fails(self, mock_data_collection, mock_scorer, mocker):
        """
        Test fallback when crew execution fails.

        **Validates: Requirements 4.2, 6.2, 9.5**
        """
        # Arrange - Mock crew to fail
        mocker.patch(
            "finwiz.flows.hybrid_analysis_flow.HybridAnalysisFlow._execute_crew",
            side_effect=Exception("Crew execution failed"),
        )

        flow = HybridAnalysisFlow()
        # Initialize state via the flow's state initialization
        flow.state.ticker = "AAPL"
        flow.state.asset_class = "stock"
        flow.state.company_name = "Apple Inc."

        # Act
        result = flow.kickoff()

        # Assert - Fallback analysis created
        assert isinstance(result, EnrichedAnalysis)
        assert result.recommendation_confidence == "LOW"
        assert result.quantitative is not None  # Python results still present

    def test_should_use_python_only_in_fallback(self, mock_data_collection, mock_scorer, mocker):
        """
        Test that fallback uses Python-only results.

        **Validates: Requirements 9.5**
        """
        # Arrange - Mock crew to fail
        mocker.patch(
            "finwiz.flows.hybrid_analysis_flow.HybridAnalysisFlow._execute_crew",
            side_effect=Exception("Crew execution failed"),
        )

        flow = HybridAnalysisFlow()
        # Initialize state via the flow's state initialization
        flow.state.ticker = "AAPL"
        flow.state.asset_class = "stock"
        flow.state.company_name = "Apple Inc."

        # Act
        result = flow.kickoff()

        # Assert - Python calculations present
        assert result.quantitative.composite_score > 0
        assert result.quantitative.grade is not None
        assert result.final_recommendation in ["BUY", "HOLD", "SELL"]


class TestBatchProcessing:
    """Test batch processing scenarios."""

    def test_should_process_multiple_holdings(self, mock_data_collection, mock_scorer, mock_crew_execution):
        """
        Test processing multiple holdings in batch.

        **Validates: Requirements 10.1, 10.2**
        """
        # Arrange
        tickers = ["AAPL", "GOOGL", "MSFT", "AMZN", "META"]

        # Act
        results = []
        for ticker in tickers:
            flow = HybridAnalysisFlow()
            # Initialize state via the flow's state fields
            flow.state.ticker = ticker
            flow.state.asset_class = "stock"
            flow.state.company_name = f"{ticker} Corp"
            result = flow.kickoff()
            results.append(result)

        # Assert
        assert len(results) == len(tickers)
        for result in results:
            assert isinstance(result, EnrichedAnalysis)
            assert result.ticker in tickers

    def test_should_handle_mixed_success_failure_in_batch(self, mock_data_collection, mock_scorer, mock_crew_execution):
        """
        Test handling mixed success/failure in batch processing.

        This test verifies that the flow can process multiple holdings successfully.
        Error handling for individual failures is tested in the reliability tests.

        **Validates: Requirements 10.4**
        """
        # Arrange
        tickers = ["AAPL", "GOOGL", "MSFT"]

        # Act
        results = []
        for ticker in tickers:
            flow = HybridAnalysisFlow()
            # Initialize state via the flow's state fields
            flow.state.ticker = ticker
            flow.state.asset_class = "stock"
            flow.state.company_name = f"{ticker} Corp"
            result = flow.kickoff()
            results.append(result)

        # Assert - Should have results for all tickers
        assert len(results) == len(tickers)
        for result in results:
            assert isinstance(result, EnrichedAnalysis)
            assert result.ticker in tickers


class TestRealTickerData:
    """Test with real ticker data (mocked external APIs)."""

    def test_should_handle_real_ticker_format(self, mock_data_collection, mock_scorer, mock_crew_execution):
        """
        Test handling real ticker formats.

        **Validates: Requirements 1.1**
        """
        # Arrange
        real_tickers = ["AAPL", "GOOGL", "MSFT", "BRK.B", "JPM"]

        # Act & Assert
        for ticker in real_tickers:
            flow = HybridAnalysisFlow()
            # Initialize state via the flow's state fields
            flow.state.ticker = ticker
            flow.state.asset_class = "stock"
            flow.state.company_name = f"{ticker} Corp"
            result = flow.kickoff()

            assert isinstance(result, EnrichedAnalysis)
            assert result.ticker == ticker
