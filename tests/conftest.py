"""
Pytest configuration and shared fixtures.

Makes test fixtures available to all test modules.
"""

from datetime import datetime
from typing import Any

import pytest
from faker import Faker

# Import all fixtures to make them available
from tests.fixtures import (
    create_crypto_data,
    create_deep_analysis_result,
    create_etf_data,
    create_market_context,
    create_portfolio_review,
    create_price_history,
    create_risk_assessment,
    create_stock_data,
)


# Make fixtures available as pytest fixtures
@pytest.fixture
def stock_data():
    """Fixture providing sample stock data."""
    return create_stock_data()


@pytest.fixture
def etf_data():
    """Fixture providing sample ETF data."""
    return create_etf_data()


@pytest.fixture
def crypto_data():
    """Fixture providing sample crypto data."""
    return create_crypto_data()


@pytest.fixture
def market_context():
    """Fixture providing sample market context."""
    return create_market_context()


@pytest.fixture
def price_history():
    """Fixture providing sample price history."""
    return create_price_history()


@pytest.fixture
def risk_assessment():
    """Fixture providing sample risk assessment."""
    return create_risk_assessment()


@pytest.fixture
def deep_analysis_result():
    """Fixture providing sample deep analysis result."""
    return create_deep_analysis_result()


@pytest.fixture
def portfolio_review():
    """Fixture providing sample portfolio review."""
    return create_portfolio_review()


# ===== Faker-based fixtures =====


@pytest.fixture(scope="session")
def fake():
    """Faker instance for generating test data."""
    return Faker()


@pytest.fixture
def fake_client_profile(fake: Faker) -> dict[str, Any]:
    """Fixture providing realistic client profile data."""
    return {
        "name": fake.name(),
        "email": fake.email(),
        "phone": fake.phone_number(),
        "address": fake.address(),
        "city": fake.city(),
        "country": fake.country(),
        "date_of_birth": fake.date_of_birth(minimum_age=25, maximum_age=70).isoformat(),
        "risk_tolerance": fake.random_element(elements=("conservative", "moderate", "aggressive")),
        "investment_goals": fake.sentence(nb_words=10),
        "annual_income": fake.random_int(min=30000, max=500000),
        "net_worth": fake.random_int(min=50000, max=5000000),
    }


@pytest.fixture
def fake_timestamps(fake: Faker) -> dict[str, Any]:
    """Fixture providing realistic timestamp data."""
    return {
        "created_at": fake.past_datetime(start_date="-30d").isoformat(),
        "updated_at": fake.date_time_between(start_date="-7d", end_date="now").isoformat(),
        "last_analysis": fake.date_time_between(start_date="-3d", end_date="now").isoformat(),
    }


@pytest.fixture
def fake_portfolio_holdings(fake: Faker) -> list[dict[str, Any]]:
    """Fixture providing realistic portfolio holdings data."""
    holdings = []
    tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "JPM", "V", "JNJ"]
    for ticker in fake.random_elements(elements=tickers, length=5, unique=True):
        holdings.append(
            {
                "ticker": ticker,
                "shares": fake.random_int(min=1, max=1000),
                "purchase_price": round(fake.random.uniform(10.0, 500.0), 2),
                "current_price": round(fake.random.uniform(10.0, 500.0), 2),
                "purchase_date": fake.past_date(start_date="-2y").isoformat(),
            }
        )
    return holdings


@pytest.fixture
def fake_investment_recommendations(fake: Faker) -> list[dict[str, Any]]:
    """Fixture providing realistic investment recommendations."""
    recommendations = []
    for _ in range(3):
        recommendations.append(
            {
                "ticker": fake.random_element(elements=("AAPL", "MSFT", "GOOGL", "AMZN", "TSLA")),
                "action": fake.random_element(elements=("BUY", "HOLD", "SELL")),
                "target_price": round(fake.random.uniform(100.0, 500.0), 2),
                "confidence": fake.random.uniform(0.6, 0.95),
                "rationale": fake.sentence(nb_words=15),
            }
        )
    return recommendations


@pytest.fixture
def fake_financial_data(fake: Faker) -> dict[str, Any]:
    """Fixture providing realistic financial data."""
    return {
        "revenue": fake.random_int(min=1000000, max=100000000),
        "net_income": fake.random_int(min=100000, max=10000000),
        "total_assets": fake.random_int(min=5000000, max=500000000),
        "total_liabilities": fake.random_int(min=2000000, max=200000000),
        "eps": round(fake.random.uniform(1.0, 50.0), 2),
        "pe_ratio": round(fake.random.uniform(10.0, 40.0), 2),
        "dividend_yield": round(fake.random.uniform(0.0, 5.0), 2),
    }


@pytest.fixture
def fake_stock_data(fake: Faker) -> dict[str, Any]:
    """Fixture providing realistic stock data."""
    return {
        "ticker": fake.random_element(elements=("AAPL", "MSFT", "GOOGL", "AMZN", "TSLA")),
        "company_name": fake.company(),
        "sector": fake.random_element(elements=("Technology", "Finance", "Healthcare", "Energy")),
        "market_cap": fake.random_int(min=1000000000, max=3000000000000),
        "price": round(fake.random.uniform(10.0, 500.0), 2),
        "volume": fake.random_int(min=1000000, max=100000000),
        "change_percent": round(fake.random.uniform(-10.0, 10.0), 2),
    }


@pytest.fixture
def fake_data_generator(fake: Faker):
    """Fixture providing a data generator function."""

    def generate(data_type: str, count: int = 1):
        if data_type == "stock":
            return [fake_stock_data.__wrapped__(fake) for _ in range(count)]
        elif data_type == "client":
            return [fake_client_profile.__wrapped__(fake) for _ in range(count)]
        else:
            return []

    return generate


@pytest.fixture
def sample_output() -> dict[str, Any]:
    """Fixture providing sample crew output data."""
    return {
        "crew_name": "stock_crew",
        "timestamp": datetime.now().isoformat(),
        "status": "success",
        "raw_output": "Comprehensive stock analysis completed successfully.",
        "pydantic": {
            "ticker": "AAPL",
            "composite_score": 0.85,
            "grade": "A-",
            "recommendation": "BUY",
        },
        "tasks_output": [
            {
                "name": "analysis_task",
                "description": "Analyze stock fundamentals",
                "raw": "Apple Inc. shows strong fundamentals with consistent revenue growth.",
            }
        ],
    }


# ===== Hybrid Analysis Flow Fixtures =====


def create_complete_enriched_analysis(
    ticker: str = "AAPL",
    company_name: str = "Apple Inc.",
    asset_class: str = "stock",
    processing_time: float = 15.0,
    llm_cost: float = 0.05,
) -> Any:
    """
    Create a complete EnrichedAnalysis object for testing.

    This helper generates all required nested Pydantic models with realistic data.
    """
    from datetime import datetime

    from finwiz.schemas.hybrid_analysis.enriched import EnrichedAnalysis
    from finwiz.schemas.hybrid_analysis.metadata import DataQualityMetrics
    from finwiz.schemas.hybrid_analysis.qualitative import (
        ContextualRiskInsights,
        FundamentalContextInsights,
        InvestmentSynthesis,
        QualitativeInsights,
        SecAnalysisInsights,
        TechnicalStrategyInsights,
    )
    from finwiz.schemas.hybrid_analysis.quantitative import QuantitativeAnalysis

    # Create quantitative analysis (Python-calculated)
    quantitative = QuantitativeAnalysis(
        ticker=ticker,
        asset_class=asset_class,
        composite_score=0.85,
        fundamental_score=0.82,
        technical_score=0.88,
        risk_score=2.5,
        grade="A",
        preliminary_recommendation="BUY",
        fundamental_metrics={"roe": 0.25, "debt_to_equity": 0.5},
        technical_indicators={"rsi": 58.3, "macd": 2.1},
        risk_metrics={"volatility": 0.283, "beta": 1.25},
        calculation_timestamp=datetime.now(),
        data_quality=DataQualityMetrics(
            completeness_score=0.95,
            freshness_score=1.0,
            accuracy_confidence=0.90,
            source_reliability=0.85,
            missing_fields=[],
        ),
        confidence_level=0.90,
        python_rationale="Strong fundamentals with consistent revenue growth and robust profit margins",
    )

    # Create qualitative insights (AI-generated)
    qualitative = QualitativeInsights(
        sec_insights=SecAnalysisInsights(
            business_model=(
                f"{company_name} operates a diversified business model with multiple revenue streams "
                "across products and services. The company has established strong competitive moats "
                "through brand equity, ecosystem lock-in, and distribution advantages. Revenue model "
                "combines hardware sales with recurring services revenue, providing stability and growth "
                "potential. Management has demonstrated consistent execution and capital allocation discipline "
                "over multiple business cycles. The company maintains strong relationships with suppliers "
                "and distribution partners while managing regulatory compliance across global markets."
            ),
            competitive_advantages=[
                "Brand strength and customer loyalty create switching costs",
                "Ecosystem integration across products drives platform stickiness",
                "Scale advantages in manufacturing and supply chain",
                "Strong R&D capabilities support innovation pipeline",
            ],
            risk_factors=[
                "Regulatory risk: Antitrust investigations and compliance requirements",
                "Competition risk: Market share pressure from competitors",
                "Concentration risk: Revenue dependency on key products",
            ],
            strategic_initiatives=[
                "Services segment expansion targeting 15%+ annual growth",
                "New market expansion in emerging geographies",
                "Technology integration across product portfolio",
            ],
        ),
        fundamental_context=FundamentalContextInsights(
            industry_analysis=(
                "Technology sector demonstrates strong growth dynamics with increasing digitalization "
                "across industries. Market leadership positions provide pricing power and competitive advantages. "
                "Secular trends in services transition and ecosystem development support long-term growth. "
                "Industry consolidation creates opportunities for scale advantages and market share gains."
            ),
            growth_drivers=[
                "Services segment growing at 15%+ annually",
                "Product innovation cycle with sustained demand",
                "Market expansion in emerging geographies",
                "Adjacent market opportunities in financial services",
            ],
            competitive_positioning=(
                "Market leadership in premium segment with 50%+ margins. Strong competitive moats "
                "through brand equity and ecosystem lock-in. Distribution advantages and retail presence."
            ),
            management_assessment=(
                "Excellent management quality with consistent execution track record. Strong capital allocation discipline demonstrated through share buybacks and dividend growth."
            ),
        ),
        technical_strategy=TechnicalStrategyInsights(
            chart_patterns=[
                "Bullish momentum with RSI at 58.3",
                "MACD positive at 2.1 indicating uptrend",
                "Price above 50-day and 200-day moving averages",
            ],
            support_resistance=(
                "Key support at $150, resistance at $180. Strong volume at support levels indicates buying interest. Breakout above $180 could trigger momentum rally."
            ),
            entry_exit_strategy=(
                "Establish initial position at current levels with disciplined approach. Consider "
                "dollar-cost averaging over multiple months to reduce timing risk. Target allocation "
                "appropriate for risk tolerance. Exit on technical breakdown below $150 or fundamental "
                "deterioration. Take partial profits at $180 resistance level."
            ),
            timing_assessment=("Market timing favorable with bullish momentum indicators. Entry at current levels offers attractive risk-reward with defined support levels."),
        ),
        contextual_risks=ContextualRiskInsights(
            regulatory_risks=["Antitrust investigations ongoing", "Compliance requirements increasing"],
            geopolitical_risks=["Supply chain vulnerabilities", "Trade tensions affecting manufacturing"],
            competitive_risks=["Market share pressure from competitors", "Pricing power erosion"],
            operational_risks=["Revenue concentration on key products", "Execution risk on new initiatives"],
            stress_scenarios=[
                "Recession scenario: 20-30% revenue decline",
                "Regulatory action: 10-15% margin compression",
                "Competition: 5-10% market share loss",
            ],
        ),
        investment_synthesis=InvestmentSynthesis(
            investment_thesis=(
                f"Investment in {ticker} is supported by strong fundamental metrics, competitive positioning, "
                "and positive industry dynamics. The company has demonstrated consistent financial performance "
                "with sustainable growth drivers across multiple segments. Quantitative analysis shows favorable "
                "valuation relative to growth potential and risk profile. Qualitative factors including management "
                "quality, competitive advantages, and strategic execution support the investment case. Risk-reward "
                "profile is attractive at current valuation levels with multiple catalysts for value creation."
            ),
            bull_case=(
                "Strong ecosystem lock-in drives recurring revenue through services segment. "
                "Product innovation cycle continues with sustained demand. Market leadership in "
                "premium segment with 50%+ margins. Services growing at 15%+ annually providing "
                "stable cash flow. Strong balance sheet enables consistent capital returns."
            ),
            base_case=(
                "Sustained revenue growth at 8-10% annually driven by services and product innovation. "
                "Margins remain stable at 45-50% with operational efficiency improvements. Market share "
                "maintained in core segments with selective expansion in adjacent markets."
            ),
            bear_case=(
                "Regulatory scrutiny impacts revenue model and pricing power. Competition intensifies "
                "in core markets from established and emerging players. Revenue concentration creates "
                "dependency risk. Market saturation in developed regions limits growth potential."
            ),
            scenario_probabilities={"bull": 0.30, "base": 0.50, "bear": 0.20},
            final_recommendation="BUY",
            recommendation_confidence="HIGH",
            action_plan={
                "immediate_actions": [
                    "Establish position at current levels",
                    "Monitor upcoming earnings release",
                    "Review product launch pipeline",
                ],
                "monitoring_points": [
                    "Quarterly revenue and margin trends",
                    "Market share dynamics in key segments",
                    "Regulatory developments",
                ],
                "exit_triggers": [
                    "Price target $180 reached",
                    "Technical breakdown below $150",
                    "Fundamental deterioration",
                ],
            },
        ),
        analysis_timestamp=datetime.now(),
        ai_confidence=0.85,
    )

    # Create enriched analysis (combination)
    return EnrichedAnalysis(
        ticker=ticker,
        company_name=company_name,
        asset_class=asset_class,
        quantitative=quantitative,
        qualitative=qualitative,
        final_grade="A",
        final_score=0.85,
        final_recommendation="BUY",
        recommendation_confidence="HIGH",
        executive_summary=(
            f"{company_name} ({ticker}) demonstrates strong fundamentals with consistent revenue growth "
            "and robust profit margins. The company's ecosystem strategy and services segment "
            "provide sustainable competitive advantages. Technical indicators suggest bullish "
            "momentum with RSI at 58.3 indicating room for upside. Risk metrics show moderate "
            "volatility at 28.3%, typical for large-cap technology stocks. Overall investment "
            "outlook is positive with a BUY recommendation based on quantitative analysis showing "
            "an A grade composite score of 0.85. The company has established a strong market position "
            "with significant barriers to entry and demonstrates consistent execution across product lines. "
            "Management quality is excellent with proven track record. Investment thesis is supported by "
            "multiple growth catalysts and strong competitive positioning in premium market segments."
        ),
        investment_rationale=qualitative.investment_synthesis.investment_thesis,
        report_word_count=2500,
        unique_insights_count=7,
        processing_time_seconds=processing_time,
        llm_cost_dollars=llm_cost,
    )


@pytest.fixture
def mock_hybrid_flow_complete(mocker):
    """
    Mock HybridAnalysisFlow.kickoff() to return complete EnrichedAnalysis.

    This fixture mocks the entire Flow execution to avoid actual data collection,
    Python scoring, and AI crew execution. Returns deterministic results for testing.
    """
    mock_result = create_complete_enriched_analysis()

    return mocker.patch("finwiz.flows.hybrid_analysis_flow.HybridAnalysisFlow.kickoff", return_value=mock_result)


@pytest.fixture
def mock_data_collection(mocker):
    """
    Mock data collection for HybridAnalysisFlow tests.

    Patches the data orchestrator to return realistic test data without external API calls.
    """
    from datetime import datetime

    from finwiz.data.data_source_orchestrator import OrchestrationResult

    mock_result = OrchestrationResult(
        ticker="AAPL",
        timestamp=datetime.now(),
        return_on_equity=0.25,
        debt_to_equity=0.5,
        revenue_growth=0.15,
        profit_margin=0.20,
        operating_margin=0.18,
        gross_margin=0.38,
        sources_succeeded=["YFinance"],
        confidence=1.0,
    )

    # Patch at the flow level to avoid actual data collection
    return mocker.patch(
        "finwiz.flows.hybrid_analysis_flow.HybridAnalysisFlow._collect_quantitative_data",
        return_value={
            "roe": 0.25,
            "debt_to_equity": 0.5,
            "revenue_growth": 0.15,
            "profit_margin": 0.20,
            "rsi": 58.3,
            "beta": 1.25,
            "volatility": 0.283,
        },
    )


@pytest.fixture
def mock_scorer(mocker):
    """
    Mock Python scorer for HybridAnalysisFlow tests.

    Returns deterministic scoring results without actual calculation.
    """
    from datetime import datetime

    from finwiz.schemas.hybrid_analysis.quantitative import QuantitativeAnalysis
    from finwiz.schemas.integration.models import DataQualityMetrics

    mock_result = QuantitativeAnalysis(
        ticker="AAPL",
        asset_class="stock",
        composite_score=0.85,
        fundamental_score=0.82,
        technical_score=0.88,
        risk_score=2.5,
        grade="A",
        preliminary_recommendation="BUY",
        fundamental_metrics={"roe": 0.25, "debt_to_equity": 0.5},
        technical_indicators={"rsi": 58.3, "macd": 2.1},
        risk_metrics={"volatility": 0.283, "beta": 1.25},
        calculation_timestamp=datetime.now(),
        data_quality=DataQualityMetrics(
            completeness_score=0.95,
            freshness_score=1.0,
            accuracy_confidence=0.90,
            source_reliability=0.85,
            missing_fields=[],
        ),
        confidence_level=0.90,
        python_rationale="Mock scoring result for testing",
    )

    return mocker.patch("finwiz.flows.hybrid_analysis_flow.HybridAnalysisFlow._calculate_python_scores", return_value=mock_result)


@pytest.fixture
def mock_crew_execution(mocker):
    """
    Mock CrewAI execution for HybridAnalysisFlow tests.

    Returns realistic qualitative insights without LLM API calls.
    """
    from finwiz.schemas.hybrid_analysis.qualitative import (
        ActionPlan,
        InvestmentThesis,
        QualitativeInsights,
        RiskAssessment,
    )

    mock_insights = QualitativeInsights(
        executive_summary=(
            "Apple Inc. (AAPL) demonstrates strong fundamentals with consistent revenue growth "
            "and robust profit margins. The company's ecosystem strategy and services segment "
            "provide sustainable competitive advantages. Technical indicators suggest bullish "
            "momentum with RSI at 58.3 indicating room for upside. Risk metrics show moderate "
            "volatility at 28.3%, typical for large-cap technology stocks. Overall investment "
            "outlook is positive with a BUY recommendation based on quantitative analysis showing "
            "an A grade composite score of 0.85."
        ),
        investment_thesis=InvestmentThesis(
            bull_case=(
                "Strong ecosystem lock-in drives recurring revenue through services segment. "
                "Product innovation cycle continues with iPhone, Mac, and wearables. Market "
                "leadership in premium smartphone segment with 50%+ margins. Services growing "
                "at 15%+ annually providing stable cash flow. Strong balance sheet enables "
                "consistent share buybacks and dividend growth."
            ),
            bear_case=(
                "Regulatory scrutiny in EU and US could impact App Store revenue model. "
                "Competition intensifying in smartphone market from Samsung and Chinese manufacturers. "
                "Dependence on iPhone for 50%+ of revenue creates concentration risk. "
                "Saturation in developed markets limits growth potential. Supply chain vulnerabilities "
                "exposed during recent global disruptions."
            ),
            key_catalysts=(
                "Q4 earnings expected to show 8% revenue growth driven by iPhone 15 cycle. "
                "Vision Pro launch in 2024 opens new product category with AR/VR potential. "
                "Services segment targeting $100B annual run rate by 2025. Expansion into "
                "financial services with Apple Pay and Apple Card. AI integration across "
                "product portfolio following industry trends."
            ),
            confidence_level=0.85,
        ),
        risk_assessment=RiskAssessment(
            key_risks=[
                "Regulatory risk: App Store antitrust investigations in EU/US",
                "Competition risk: Android ecosystem and Chinese manufacturers",
                "Concentration risk: iPhone revenue dependency",
                "Supply chain risk: Geopolitical tensions affecting Asian manufacturing",
            ],
            mitigation_strategies=[
                "Diversify revenue streams through services and wearables growth",
                "Expand geographic presence in India and Southeast Asia",
                "Strengthen supplier relationships and dual-sourcing critical components",
                "Invest in regulatory compliance and government relations",
            ],
            risk_rating="MODERATE",
        ),
        action_plan=ActionPlan(
            entry_strategy=(
                "Establish initial position at current levels around $175-180. "
                "Consider dollar-cost averaging over 3-6 months to reduce timing risk. "
                "Target allocation of 3-5% of equity portfolio for diversified investors."
            ),
            exit_conditions=[
                "Price target reached: $210-220 (12-month horizon)",
                "Fundamental deterioration: Services growth <5% or margin compression >200bps",
                "Technical breakdown: Sustained break below $160 support with volume",
                "Regulatory adverse ruling: Material App Store revenue impact >$10B annually",
            ],
            monitoring_metrics=[
                "Quarterly iPhone unit sales and ASP trends",
                "Services revenue growth and attach rate",
                "Operating margin and gross margin trends",
                "Capital return program pace (buybacks + dividends)",
                "Market share in key segments and geographies",
            ],
        ),
        data_quality_assessment=(
            "Data quality is excellent with 95% completeness from primary YFinance source. "
            "All critical financial metrics available and recently updated. Technical indicators "
            "calculated from reliable price history. No significant data gaps or quality concerns."
        ),
        confidence_rationale=(
            "High confidence (85%) based on: (1) Strong quantitative scores across fundamental, "
            "technical, and risk dimensions, (2) Comprehensive data availability from reliable sources, "
            "(3) Consistent historical performance patterns, (4) Clear investment thesis supported "
            "by multiple catalysts, (5) Well-defined risk mitigation strategies."
        ),
    )

    return mocker.patch("finwiz.flows.hybrid_analysis_flow.HybridAnalysisFlow._execute_crew", return_value=mock_insights)
