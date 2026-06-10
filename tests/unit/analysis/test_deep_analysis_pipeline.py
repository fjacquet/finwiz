"""Unit tests for the deep analysis pipeline.

Tests the functional pipeline for per-holding analysis.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest
from faker import Faker

from finwiz.analysis import AnalysisContext
from finwiz.analysis.deep_analysis_pipeline import (
    _extract_qualitative,
    _generate_executive_summary,
    _get_analysis_crew,
    _result_to_quantitative,
    analyze_holding,
    calculate_quantitative,
    collect_raw_data,
    generate_qualitative,
    synthesize_enriched_analysis,
)
from finwiz.flow_state_models import DeepAnalysisResult
from finwiz.schemas.hybrid_analysis import (
    QualitativeInsights,
    QuantitativeAnalysis,
)
from finwiz.schemas.hybrid_analysis.metadata import DataQualityMetrics

fake = Faker()


@pytest.fixture
def analysis_context() -> AnalysisContext:
    """Create a sample analysis context."""
    return AnalysisContext(
        ticker="AAPL",
        asset_class="stock",
        company_name="Apple Inc.",
    )


@pytest.fixture
def mock_raw_data() -> dict[str, Any]:
    """Create mock raw data from data collector."""
    return {
        "ticker": "AAPL",
        "asset_class": "stock",
        "price_data": {"current_price": 150.0, "52_week_high": 180.0, "52_week_low": 120.0},
        "fundamental_data": {"pe_ratio": 25.0, "roe": 0.30, "debt_to_equity": 0.5},
        "technical_data": {"rsi": 55.0, "macd": 1.2, "moving_avg_50": 145.0},
    }


@pytest.fixture
def mock_deep_analysis_result() -> DeepAnalysisResult:
    """Create a mock DeepAnalysisResult."""
    return DeepAnalysisResult(
        ticker="AAPL",
        asset_class="stock",
        crew_name="DeepAnalysisCrew",
        grade="A",
        composite_score=0.82,
        fundamental_score=0.85,
        technical_score=0.78,
        risk_score=0.80,
        recommendation="BUY",
        rationale="Strong fundamentals with solid growth potential.",
        fundamental_details={"pe_ratio": 25.0, "roe": 0.30},
        technical_details={"rsi": 55.0, "macd": 1.2},
        risk_details={"volatility": 0.15, "beta": 1.1},
        data_freshness_hours=0.5,
        confidence_level=0.85,
    )


@pytest.fixture
def mock_data_quality() -> DataQualityMetrics:
    """Create mock DataQualityMetrics."""
    return DataQualityMetrics(
        completeness_score=0.95,
        freshness_score=1.0,
        accuracy_confidence=0.90,
        source_reliability=0.85,
        missing_fields=[],
    )


@pytest.fixture
def mock_quantitative_analysis(mock_data_quality: DataQualityMetrics) -> QuantitativeAnalysis:
    """Create a mock QuantitativeAnalysis."""
    return QuantitativeAnalysis(
        composite_score=0.82,
        fundamental_score=0.85,
        technical_score=0.78,
        risk_score=0.80,
        grade="A",
        preliminary_recommendation="BUY",
        fundamental_metrics={"pe_ratio": 25.0, "roe": 0.30},
        technical_indicators={"rsi": 55.0, "macd": 1.2},
        risk_metrics={"volatility": 0.15, "beta": 1.1},
        calculation_timestamp=datetime.now(),
        data_quality=mock_data_quality,
        confidence_level=0.85,
        python_rationale="Strong fundamentals with solid growth potential.",
    )


@pytest.fixture
def mock_qualitative_insights(mocker) -> QualitativeInsights:
    """Create a mock QualitativeInsights."""
    from finwiz.schemas.hybrid_analysis.qualitative import (
        ActionPlan,
        ContextualRiskInsights,
        FundamentalContextInsights,
        InvestmentSynthesis,
        ScenarioProbabilities,
        SecAnalysisInsights,
        TechnicalStrategyInsights,
    )

    return QualitativeInsights(
        sec_insights=SecAnalysisInsights(
            business_model="Apple designs and sells consumer electronics and software. " * 10,
            competitive_advantages=["Strong brand", "Ecosystem lock-in", "Innovation"],
            risk_factors=["Supply chain risks", "Competition", "Regulatory"],
            strategic_initiatives=["AI/ML investment", "Services expansion"],
        ),
        fundamental_context=FundamentalContextInsights(
            industry_analysis="Technology sector remains strong with growth opportunities. " * 5,
            growth_drivers=["iPhone sales", "Services revenue", "Wearables"],
            competitive_positioning="Market leader in premium devices. " * 5,
            management_assessment="Experienced leadership team with proven track record. " * 5,
        ),
        technical_strategy=TechnicalStrategyInsights(
            chart_patterns=["Cup and handle", "Ascending triangle"],
            support_resistance="Support at $140, resistance at $180. " * 5,
            entry_exit_strategy="Buy on pullbacks to $145-150 range. " * 5,
            timing_assessment="Neutral to bullish in short term. " * 5,
        ),
        contextual_risks=ContextualRiskInsights(
            regulatory_risks=["Antitrust scrutiny"],
            geopolitical_risks=["China tensions"],
            competitive_risks=["Android competition"],
            operational_risks=["Supply chain disruptions"],
            stress_scenarios=["Economic recession"],
        ),
        investment_synthesis=InvestmentSynthesis(
            investment_thesis="Apple remains a strong long-term investment. " * 10,
            bull_case="New product categories drive growth. " * 10,
            base_case="Steady growth from services. " * 10,
            bear_case="Market saturation limits upside. " * 10,
            scenario_probabilities=ScenarioProbabilities(bull=0.3, base=0.5, bear=0.2),
            final_recommendation="BUY",
            recommendation_confidence="HIGH",
            confidence_rationale="Strong fundamentals support the recommendation.",
            action_plan=ActionPlan(
                immediate_actions=["Initiate position"],
                monitoring_points=["Q4 earnings"],
                exit_triggers=["Significant margin decline"],
            ),
        ),
        analysis_timestamp=datetime.now(),
        ai_confidence=0.85,
    )


class TestAnalysisContext:
    """Tests for AnalysisContext dataclass."""

    def test_context_creation(self):
        """Test context creation with all fields."""
        ctx = AnalysisContext(
            ticker="MSFT",
            asset_class="stock",
            company_name="Microsoft Corporation",
        )
        assert ctx.ticker == "MSFT"
        assert ctx.asset_class == "stock"
        assert ctx.company_name == "Microsoft Corporation"

    def test_context_default_company_name(self):
        """Test context with default company name."""
        ctx = AnalysisContext(ticker="GOOGL", asset_class="stock")
        assert ctx.ticker == "GOOGL"
        assert ctx.company_name == ""

    def test_context_immutable(self):
        """Test that context is immutable (frozen dataclass)."""
        ctx = AnalysisContext(ticker="AAPL", asset_class="stock")
        with pytest.raises(AttributeError):
            ctx.ticker = "MSFT"  # type: ignore


class TestCollectRawData:
    """Tests for collect_raw_data function."""

    @pytest.fixture(autouse=True)
    def _mock_sentiment_macro(self, mocker):
        """Mock the v4 sentiment/macro collector — its FRED/news fetches are remote.

        Without this, collect_raw_data reaches the FRED API (blocked by the
        network guard) and tenacity retries with sleeps add ~22s per test.
        """
        mock_v4 = mocker.MagicMock()
        mock_v4.collect_sentiment.return_value = None
        mock_v4.collect_macro.return_value = None
        mocker.patch(
            "finwiz.data.sentiment_collector.SentimentMacroCollector",
            return_value=mock_v4,
        )

    def test_collect_raw_data_calls_collector(self, mocker, analysis_context, mock_raw_data):
        """Test that collect_raw_data uses DeepAnalysisDataCollector."""
        mock_collector = mocker.MagicMock()
        mock_collector.collect_data.return_value = mock_raw_data

        mocker.patch(
            "finwiz.orchestrators.deep_analysis_data_collector.DeepAnalysisDataCollector",
            return_value=mock_collector,
        )

        result = collect_raw_data(analysis_context)

        mock_collector.collect_data.assert_called_once_with("AAPL", "stock", batch_enabled=False, prefetched_data=None)
        assert result == mock_raw_data

    def test_collect_raw_data_with_etf(self, mocker):
        """Test data collection for ETF asset class."""
        ctx = AnalysisContext(ticker="SPY", asset_class="etf")
        mock_collector = mocker.MagicMock()
        mock_collector.collect_data.return_value = {"ticker": "SPY"}

        mocker.patch(
            "finwiz.orchestrators.deep_analysis_data_collector.DeepAnalysisDataCollector",
            return_value=mock_collector,
        )

        result = collect_raw_data(ctx)

        mock_collector.collect_data.assert_called_once_with("SPY", "etf", batch_enabled=False, prefetched_data=None)


class TestCalculateQuantitative:
    """Tests for calculate_quantitative function."""

    def test_calculate_quantitative_returns_result_and_quant(self, mocker, analysis_context, mock_raw_data, mock_deep_analysis_result):
        """Test that calculate_quantitative returns both result and quant."""
        mock_scorer = mocker.MagicMock()
        mock_scorer.calculate_composite_score.return_value = mock_deep_analysis_result

        mocker.patch(
            "finwiz.scoring.deep_analysis_scorer.DeepAnalysisScorer",
            return_value=mock_scorer,
        )

        result, quant = calculate_quantitative(analysis_context, mock_raw_data)

        assert result == mock_deep_analysis_result
        assert isinstance(quant, QuantitativeAnalysis)
        assert quant.composite_score == 0.82
        assert quant.grade == "A"

    def test_calculate_quantitative_converts_to_quantitative_analysis(self, mocker, analysis_context, mock_raw_data):
        """Test conversion to QuantitativeAnalysis schema."""
        result = DeepAnalysisResult(
            ticker="AAPL",
            asset_class="stock",
            crew_name="DeepAnalysisCrew",
            grade="B+",
            composite_score=0.75,
            fundamental_score=0.70,
            technical_score=0.80,
            risk_score=0.72,
            recommendation="HOLD",
            rationale="Moderate growth with some risks.",
            fundamental_details={},
            technical_details={},
            risk_details={},
            data_freshness_hours=0.5,
            confidence_level=0.65,
        )

        mock_scorer = mocker.MagicMock()
        mock_scorer.calculate_composite_score.return_value = result

        mocker.patch(
            "finwiz.scoring.deep_analysis_scorer.DeepAnalysisScorer",
            return_value=mock_scorer,
        )

        _, quant = calculate_quantitative(analysis_context, mock_raw_data)

        assert quant.grade == "B+"
        assert quant.composite_score == 0.75
        assert quant.preliminary_recommendation == "HOLD"


class TestGenerateQualitative:
    """Tests for generate_qualitative function."""

    def test_generate_qualitative_calls_crew(self, mocker, analysis_context, mock_quantitative_analysis, mock_qualitative_insights):
        """Test that generate_qualitative calls the appropriate crew."""
        # Disable MAXIMUM_SPEED mode to test AI crew path
        mocker.patch(
            "finwiz.config.performance.performance_config.is_maximum_speed_mode",
            return_value=False,
        )

        mock_crew_instance = mocker.MagicMock()
        mock_crew_result = mocker.MagicMock()
        mock_crew_result.pydantic = mock_qualitative_insights
        # The pipeline calls crew.kickoff() directly (wrapper's kickoff method)
        mock_crew_instance.kickoff.return_value = mock_crew_result

        mocker.patch(
            "finwiz.analysis.stages.qualify._get_analysis_crew",
            return_value=mock_crew_instance,
        )

        result = generate_qualitative(analysis_context, mock_quantitative_analysis)

        mock_crew_instance.kickoff.assert_called_once()
        assert result == mock_qualitative_insights

    def test_generate_qualitative_passes_correct_inputs(self, mocker, analysis_context, mock_quantitative_analysis):
        """Test that correct inputs are passed to crew."""
        # Disable MAXIMUM_SPEED mode to test AI crew path
        mocker.patch(
            "finwiz.config.performance.performance_config.is_maximum_speed_mode",
            return_value=False,
        )

        mock_crew_instance = mocker.MagicMock()
        mock_crew_result = mocker.MagicMock()
        mock_crew_result.pydantic = None
        mock_crew_result.raw = "{}"

        # The pipeline calls crew.kickoff() directly (wrapper's kickoff method)
        mock_crew_instance.kickoff.return_value = mock_crew_result

        mocker.patch(
            "finwiz.analysis.stages.qualify._get_analysis_crew",
            return_value=mock_crew_instance,
        )
        mocker.patch(
            "finwiz.analysis.stages.qualify._extract_qualitative",
            return_value=mocker.MagicMock(),
        )

        generate_qualitative(analysis_context, mock_quantitative_analysis)

        call_args = mock_crew_instance.kickoff.call_args
        inputs = call_args.kwargs["inputs"]

        assert inputs["ticker"] == "AAPL"
        assert inputs["asset_class"] == "stock"
        assert inputs["company_name"] == "Apple Inc."
        assert inputs["grade"] == "A"
        assert inputs["composite_score"] == 0.82

    def test_generate_qualitative_maximum_speed_mode_skips_crew(self, mocker, analysis_context, mock_quantitative_analysis):
        """Test that MAXIMUM_SPEED mode skips AI crew and uses Python qualitative."""
        # Enable MAXIMUM_SPEED mode
        mocker.patch(
            "finwiz.config.performance.performance_config.is_maximum_speed_mode",
            return_value=True,
        )

        mock_crew_instance = mocker.MagicMock()
        mocker.patch(
            "finwiz.analysis.deep_analysis_pipeline._get_analysis_crew",
            return_value=mock_crew_instance,
        )

        result = generate_qualitative(analysis_context, mock_quantitative_analysis)

        # Crew should NOT be called in MAXIMUM_SPEED mode
        mock_crew_instance.kickoff.assert_not_called()

        # Should return a valid QualitativeInsights object
        from finwiz.schemas.hybrid_analysis import QualitativeInsights

        assert isinstance(result, QualitativeInsights)
        # Verify it contains Python-generated content (not empty)
        assert result.sec_insights is not None
        assert result.investment_synthesis is not None


class TestSynthesizeEnrichedAnalysis:
    """Tests for synthesize_enriched_analysis function."""

    def test_synthesize_creates_enriched_analysis(self, analysis_context, mock_quantitative_analysis, mock_qualitative_insights):
        """Test that synthesis creates EnrichedAnalysis with correct fields."""
        enriched = synthesize_enriched_analysis(
            analysis_context,
            mock_quantitative_analysis,
            mock_qualitative_insights,
            processing_time=5.0,
        )

        assert enriched.ticker == "AAPL"
        assert enriched.asset_class == "stock"
        assert enriched.final_grade == "A"
        assert enriched.final_score == 0.82
        assert enriched.final_recommendation == "BUY"
        assert enriched.processing_time_seconds == 5.0

    def test_synthesize_python_wins_on_recommendation_conflict(self, analysis_context, mock_quantitative_analysis, mock_qualitative_insights):
        """Test that Python recommendation wins when AI disagrees."""
        # Modify quant to have different recommendation
        mock_quantitative_analysis.preliminary_recommendation = "HOLD"

        enriched = synthesize_enriched_analysis(
            analysis_context,
            mock_quantitative_analysis,
            mock_qualitative_insights,
            processing_time=1.0,
        )

        # Python wins
        assert enriched.final_recommendation == "HOLD"

    def test_synthesize_generates_executive_summary(self, analysis_context, mock_quantitative_analysis, mock_qualitative_insights):
        """Test that executive summary is generated."""
        enriched = synthesize_enriched_analysis(
            analysis_context,
            mock_quantitative_analysis,
            mock_qualitative_insights,
            processing_time=1.0,
        )

        assert len(enriched.executive_summary) > 0
        assert "A" in enriched.executive_summary  # Grade should be mentioned


class TestAnalyzeHolding:
    """Tests for the main analyze_holding function."""

    def test_analyze_holding_composes_pipeline(self, mocker, mock_raw_data, mock_deep_analysis_result, mock_qualitative_insights):
        """Test that analyze_holding composes all pipeline steps."""
        mock_quant = QuantitativeAnalysis(
            composite_score=0.82,
            fundamental_score=0.85,
            technical_score=0.78,
            risk_score=0.80,
            grade="A",
            preliminary_recommendation="BUY",
            fundamental_metrics={},
            technical_indicators={},
            risk_metrics={},
            calculation_timestamp=datetime.now(),
            data_quality=DataQualityMetrics(
                completeness_score=0.95,
                freshness_score=1.0,
                accuracy_confidence=0.90,
                source_reliability=0.85,
            ),
            confidence_level=0.85,
            python_rationale="Strong fundamentals.",
        )

        from finwiz.schemas.hybrid_analysis.fact_pack import FactPack

        _now = datetime.now(UTC)
        _fake_fp = FactPack(
            corporate_structure="Apple Inc. — independent public company",
            recent_events=[],
            leadership="Tim Cook (CEO)",
            fetched_at=_now,
            freshness=FactPack.derive_freshness(_now),
            confidence=0.9,
            source_citations=[],
        )

        mocker.patch(
            "finwiz.analysis.stages.collect._collect_raw_data_inner",
            return_value=mock_raw_data,
        )
        mocker.patch(
            "finwiz.analysis.stages.quantify._calculate_quantitative_inner",
            return_value=(mock_deep_analysis_result, mock_quant),
        )
        mocker.patch(
            "finwiz.analysis.stages._compute_options_probabilities",
            return_value=None,
        )
        mocker.patch(
            "finwiz.analysis.stages.fact_pack._fact_pack_inner",
            return_value=_fake_fp,
        )
        mocker.patch(
            "finwiz.analysis.stages.qualify._try_ai_qualify",
            return_value=mock_qualitative_insights,
        )
        mocker.patch(
            "finwiz.analysis.stages.qualify._safe_strategic",
            return_value=None,
        )

        result, enriched = analyze_holding("AAPL", "stock", "Apple Inc.")

        # emit copies fact_pack from enriched.qualitative onto the result via
        # model_copy, so equality must compare against the fact-pack-augmented
        # expected. Compare on the canonical core fields instead of full ==.
        assert result.ticker == mock_deep_analysis_result.ticker
        assert result.grade == mock_deep_analysis_result.grade
        assert result.composite_score == mock_deep_analysis_result.composite_score
        assert result.recommendation == mock_deep_analysis_result.recommendation
        # fact_pack must propagate end-to-end (qualify attaches → emit copies)
        assert result.fact_pack is not None
        assert result.fact_pack.corporate_structure == _fake_fp.corporate_structure
        assert enriched.ticker == "AAPL"
        assert enriched.final_grade == "A"

    def test_analyze_holding_returns_both_outputs(self, mocker, mock_qualitative_insights):
        """Test that analyze_holding returns both DeepAnalysisResult and EnrichedAnalysis."""
        mock_result = DeepAnalysisResult(
            ticker="MSFT",
            asset_class="stock",
            crew_name="DeepAnalysisCrew",
            grade="A-",
            composite_score=0.78,
            fundamental_score=0.80,
            technical_score=0.75,
            risk_score=0.78,
            recommendation="BUY",
            rationale="Solid performer.",
            fundamental_details={},
            technical_details={},
            risk_details={},
            data_freshness_hours=0.5,
            confidence_level=0.85,
        )

        mock_quant = QuantitativeAnalysis(
            composite_score=0.78,
            fundamental_score=0.80,
            technical_score=0.75,
            risk_score=0.78,
            grade="A-",
            preliminary_recommendation="BUY",
            fundamental_metrics={},
            technical_indicators={},
            risk_metrics={},
            calculation_timestamp=datetime.now(),
            data_quality=DataQualityMetrics(
                completeness_score=0.95,
                freshness_score=1.0,
                accuracy_confidence=0.90,
                source_reliability=0.85,
            ),
            confidence_level=0.85,
            python_rationale="Solid performer.",
        )

        mocker.patch(
            "finwiz.analysis.stages.collect_raw_data",
            return_value={},
        )
        mocker.patch(
            "finwiz.analysis.stages.calculate_quantitative",
            return_value=(mock_result, mock_quant),
        )
        mocker.patch(
            "finwiz.analysis.stages._compute_options_probabilities",
            return_value=None,
        )
        mocker.patch(
            "finwiz.analysis.stages.qualify.generate_qualitative",
            return_value=mock_qualitative_insights,
        )
        mocker.patch(
            "finwiz.analysis.stages.qualify._safe_strategic",
            return_value=None,
        )

        result, enriched = analyze_holding("MSFT", "stock", "Microsoft")

        assert isinstance(result, DeepAnalysisResult)
        assert result.ticker == "MSFT"


class TestGetAnalysisCrew:
    """Tests for _get_analysis_crew factory function."""

    def test_get_deep_analysis_crew_for_stock(self, mocker):
        """Test that stock asset class returns DeepAnalysisCrew."""
        mock_crew = mocker.MagicMock()
        mocker.patch(
            "finwiz.crews.deep_analysis.deep_analysis.DeepAnalysisCrew",
            return_value=mock_crew,
        )

        result = _get_analysis_crew("stock")
        assert result == mock_crew

    def test_get_deep_analysis_crew_for_etf(self, mocker):
        """Test that etf asset class returns DeepAnalysisCrew."""
        mock_crew = mocker.MagicMock()
        mocker.patch(
            "finwiz.crews.deep_analysis.deep_analysis.DeepAnalysisCrew",
            return_value=mock_crew,
        )

        result = _get_analysis_crew("etf")
        assert result == mock_crew

    def test_get_deep_analysis_crew_for_crypto(self, mocker):
        """Test that crypto asset class returns DeepAnalysisCrew."""
        mock_crew = mocker.MagicMock()
        mocker.patch(
            "finwiz.crews.deep_analysis.deep_analysis.DeepAnalysisCrew",
            return_value=mock_crew,
        )

        result = _get_analysis_crew("crypto")
        assert result == mock_crew

    def test_all_asset_classes_use_same_crew(self, mocker):
        """Test that all asset classes use DeepAnalysisCrew."""
        mock_crew = mocker.MagicMock()
        mocker.patch(
            "finwiz.crews.deep_analysis.deep_analysis.DeepAnalysisCrew",
            return_value=mock_crew,
        )

        for asset_class in ["stock", "etf", "crypto", "bond", "commodity"]:
            result = _get_analysis_crew(asset_class)
            assert result == mock_crew


class TestResultToQuantitative:
    """Tests for _result_to_quantitative helper."""

    def test_converts_all_fields(self, mock_deep_analysis_result):
        """Test that all fields are correctly converted."""
        quant = _result_to_quantitative(mock_deep_analysis_result)

        assert quant.composite_score == 0.82
        assert quant.fundamental_score == 0.85
        assert quant.technical_score == 0.78
        assert quant.risk_score == 0.80
        assert quant.grade == "A"
        assert quant.preliminary_recommendation == "BUY"
        assert quant.confidence_level == 0.85

    def test_handles_none_scores(self):
        """Test that None scores are converted to 0.0."""
        result = DeepAnalysisResult(
            ticker="TEST",
            asset_class="stock",
            crew_name="DeepAnalysisCrew",
            grade="C",
            composite_score=0.5,
            fundamental_score=None,
            technical_score=None,
            risk_score=None,
            recommendation="HOLD",
            rationale="Test rationale with at least 10 characters.",
            fundamental_details={},
            technical_details={},
            risk_details={},
            data_freshness_hours=0.5,
            confidence_level=0.35,
        )

        quant = _result_to_quantitative(result)

        assert quant.fundamental_score == 0.0
        assert quant.technical_score == 0.0
        assert quant.risk_score == 0.0


class TestGenerateExecutiveSummary:
    """Tests for _generate_executive_summary helper."""

    def test_includes_grade_and_score(self, mock_quantitative_analysis, mock_qualitative_insights):
        """Test that summary includes grade and score."""
        summary = _generate_executive_summary(mock_quantitative_analysis, mock_qualitative_insights)

        assert "A" in summary
        assert "0.82" in summary

    def test_includes_recommendation(self, mock_quantitative_analysis, mock_qualitative_insights):
        """Test that summary includes recommendation."""
        summary = _generate_executive_summary(mock_quantitative_analysis, mock_qualitative_insights)

        assert "BUY" in summary or "recommendation" in summary.lower()


class TestExtractQualitative:
    """Tests for _extract_qualitative helper."""

    def test_extracts_pydantic_model_if_available(self, mocker, mock_qualitative_insights):
        """Test that pydantic model is extracted when available."""
        crew_result = mocker.MagicMock()
        crew_result.pydantic = mock_qualitative_insights

        result = _extract_qualitative(crew_result, mocker.MagicMock())

        assert result == mock_qualitative_insights

    def test_falls_back_to_validation_if_no_pydantic(self, mocker, mock_qualitative_insights):
        """Test that validation is used when all extraction methods fail."""
        crew_result = mocker.MagicMock()
        crew_result.pydantic = None  # No pydantic model
        crew_result.raw = "not valid json at all {"  # Invalid JSON that won't parse
        crew_result.tasks_output = []  # Empty tasks output

        mock_validate = mocker.patch(
            "finwiz.validation.ai_output.validate_ai_output_with_retry",
            return_value=mock_qualitative_insights,
        )

        result = _extract_qualitative(crew_result, mocker.MagicMock())

        mock_validate.assert_called_once()
        assert result == mock_qualitative_insights
