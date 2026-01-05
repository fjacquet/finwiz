"""Unit tests for DeepAnalysisOrchestrator.

Tests the orchestrator using the functional pipeline from finwiz.analysis.
"""

from datetime import datetime

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from finwiz.flow_state import FinwizState
from finwiz.flow_state_models import DeepAnalysisResult
from finwiz.orchestrators.deep_analysis_orchestrator import DeepAnalysisOrchestrator
from finwiz.schemas.hybrid_analysis import EnrichedAnalysis, QuantitativeAnalysis
from finwiz.schemas.hybrid_analysis.metadata import DataQualityMetrics


class TestDeepAnalysisOrchestrator:
    """Test suite for DeepAnalysisOrchestrator."""

    @pytest.fixture
    def state(self):
        """Create test state."""
        return FinwizState(
            session_id="test_session",
            current_day=17,
            current_month=11,
            current_year=2025,
            current_date="2025-11-17",
            full_date="November 17, 2025",
            timestamp="2025-11-17T10:00:00",
            report_language="en",
        )

    @pytest.fixture
    def batch_config(self, mocker):
        """Create test batch config."""
        config = mocker.Mock()
        config.enabled = True
        config.min_holdings_for_batch = 3
        config.alpha_vantage_rate_limit = 5
        return config

    @pytest.fixture
    def orchestrator(self, state, batch_config):
        """Create orchestrator instance."""
        return DeepAnalysisOrchestrator(state, batch_prefetch_config=batch_config, cache_service=None, cache_enabled=False)

    @pytest.fixture
    def mock_deep_analysis_result(self) -> DeepAnalysisResult:
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
    def mock_enriched_analysis(self, mocker) -> EnrichedAnalysis:
        """Create a mock EnrichedAnalysis."""
        from finwiz.schemas.hybrid_analysis.qualitative import (
            ActionPlan,
            ContextualRiskInsights,
            FundamentalContextInsights,
            InvestmentSynthesis,
            QualitativeInsights,
            ScenarioProbabilities,
            SecAnalysisInsights,
            TechnicalStrategyInsights,
        )

        quant = QuantitativeAnalysis(
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

        qual = QualitativeInsights(
            sec_insights=SecAnalysisInsights(
                business_model="Apple designs and sells consumer electronics. " * 10,
                competitive_advantages=["Strong brand"],
                risk_factors=["Supply chain risks"],
                strategic_initiatives=["AI investment"],
            ),
            fundamental_context=FundamentalContextInsights(
                industry_analysis="Tech sector strong. " * 10,
                growth_drivers=["iPhone sales"],
                competitive_positioning="Market leader. " * 10,
                management_assessment="Experienced team. " * 10,
            ),
            technical_strategy=TechnicalStrategyInsights(
                chart_patterns=["Cup and handle"],
                support_resistance="Support at $140. " * 10,
                entry_exit_strategy="Buy on pullbacks. " * 10,
                timing_assessment="Neutral to bullish. " * 10,
            ),
            contextual_risks=ContextualRiskInsights(
                regulatory_risks=["Antitrust"],
                geopolitical_risks=["China"],
                competitive_risks=["Android"],
                operational_risks=["Supply chain"],
                stress_scenarios=["Recession"],
            ),
            investment_synthesis=InvestmentSynthesis(
                investment_thesis="Strong long-term investment. " * 10,
                bull_case="New products drive growth. " * 10,
                base_case="Steady services growth. " * 10,
                bear_case="Market saturation. " * 10,
                scenario_probabilities=ScenarioProbabilities(bull=0.3, base=0.5, bear=0.2),
                final_recommendation="BUY",
                recommendation_confidence="HIGH",
                confidence_rationale="Strong fundamentals support recommendation.",
                action_plan=ActionPlan(
                    immediate_actions=["Initiate position"],
                    monitoring_points=["Q4 earnings"],
                    exit_triggers=["Margin decline"],
                ),
            ),
            analysis_timestamp=datetime.now(),
            ai_confidence=0.85,
        )

        return EnrichedAnalysis(
            ticker="AAPL",
            company_name="Apple Inc.",
            asset_class="stock",
            quantitative=quant,
            qualitative=qual,
            final_grade="A",
            final_score=0.82,
            final_recommendation="BUY",
            recommendation_confidence="HIGH",
            executive_summary="Investment Grade: A with score 0.82. Recommendation: BUY.",
            investment_rationale="Strong long-term investment thesis.",
            processing_time_seconds=5.0,
        )

    def test_should_return_empty_dict_when_no_holdings(self, orchestrator):
        """Test deep analysis with no holdings."""
        result = orchestrator.run_deep_analysis_on_holdings([])
        assert result == {}

    def test_should_analyze_single_holding(self, mocker, orchestrator, mock_deep_analysis_result, mock_enriched_analysis):
        """Test analysis of a single holding using functional pipeline."""
        # Mock the functional pipeline at the import location
        mocker.patch(
            "finwiz.analysis.analyze_holding",
            return_value=(mock_deep_analysis_result, mock_enriched_analysis),
        )

        holdings = [{"ticker": "AAPL", "asset_class": "stock", "company_name": "Apple Inc."}]

        result = orchestrator.run_deep_analysis_on_holdings(holdings)

        assert len(result) == 1
        assert "AAPL" in result
        assert isinstance(result["AAPL"], DeepAnalysisResult)
        assert result["AAPL"].grade == "A"
        assert result["AAPL"].composite_score == 0.82

    def test_should_analyze_multiple_holdings(self, mocker, orchestrator, mock_deep_analysis_result, mock_enriched_analysis):
        """Test analysis of multiple holdings."""

        def create_result(ticker, asset_class, company_name=""):
            result = DeepAnalysisResult(
                ticker=ticker,
                asset_class=asset_class,
                crew_name="DeepAnalysisCrew",
                grade="A" if ticker == "AAPL" else "B+",
                composite_score=0.82 if ticker == "AAPL" else 0.75,
                fundamental_score=0.85,
                technical_score=0.78,
                risk_score=0.80,
                recommendation="BUY",
                rationale="Test rationale for analysis.",
                fundamental_details={},
                technical_details={},
                risk_details={},
                data_freshness_hours=0.5,
                confidence_level=0.85,
            )
            # Return enriched as well (mock)
            enriched = mocker.MagicMock()
            enriched.ticker = ticker
            return result, enriched

        mocker.patch(
            "finwiz.analysis.analyze_holding",
            side_effect=create_result,
        )

        holdings = [
            {"ticker": "AAPL", "asset_class": "stock"},
            {"ticker": "GOOGL", "asset_class": "stock"},
        ]

        result = orchestrator.run_deep_analysis_on_holdings(holdings)

        assert len(result) == 2
        assert "AAPL" in result
        assert "GOOGL" in result

    def test_should_handle_analysis_failure_gracefully(self, mocker, orchestrator):
        """Test that analysis failures are handled gracefully."""

        def failing_analysis(ticker, asset_class, company_name=""):
            raise RuntimeError("Analysis failed")

        mocker.patch(
            "finwiz.analysis.analyze_holding",
            side_effect=failing_analysis,
        )

        holdings = [{"ticker": "FAIL", "asset_class": "stock"}]

        result = orchestrator.run_deep_analysis_on_holdings(holdings)

        # Should return empty dict on failure (graceful degradation)
        assert result == {}

    def test_should_skip_invalid_holdings(self, mocker, orchestrator, mock_deep_analysis_result, mock_enriched_analysis):
        """Test that holdings without ticker or asset_class are skipped."""
        mocker.patch(
            "finwiz.analysis.analyze_holding",
            return_value=(mock_deep_analysis_result, mock_enriched_analysis),
        )

        holdings = [
            {"ticker": "AAPL", "asset_class": "stock"},
            {"asset_class": "stock"},  # Missing ticker
            {"ticker": "GOOGL"},  # Missing asset_class
            {},  # Empty
        ]

        result = orchestrator.run_deep_analysis_on_holdings(holdings)

        # Only AAPL should be processed
        assert len(result) == 1
        assert "AAPL" in result

    def test_should_store_enriched_analysis(self, mocker, orchestrator, mock_deep_analysis_result, mock_enriched_analysis, tmp_path):
        """Test that enriched analysis is stored for HTML generation."""
        mocker.patch(
            "finwiz.analysis.analyze_holding",
            return_value=(mock_deep_analysis_result, mock_enriched_analysis),
        )

        # Override state output path
        orchestrator.state.output_dir = str(tmp_path)

        holdings = [{"ticker": "AAPL", "asset_class": "stock"}]

        result = orchestrator.run_deep_analysis_on_holdings(holdings)

        assert len(result) == 1

        # Verify enriched analysis can be retrieved
        enriched = orchestrator.get_enriched_analysis("AAPL")
        assert enriched is not None
        assert enriched.ticker == "AAPL"

    @pytest.mark.parametrize(
        "holdings",
        [
            [{"ticker": "AAPL", "asset_class": "stock"}],
            [{"ticker": "AAPL", "asset_class": "stock"}, {"ticker": "GOOGL", "asset_class": "stock"}],
            [
                {"ticker": "AAPL", "asset_class": "stock"},
                {"ticker": "SPY", "asset_class": "etf"},
                {"ticker": "BTC", "asset_class": "crypto"},
            ],
        ],
    )
    def test_property_deep_analysis_completeness(self, mocker, holdings):
        """
        **Feature: flow-orchestrator-refactoring, Property 8: Deep Analysis Completeness**

        For any portfolio with N holdings, the DeepAnalysisOrchestrator
        should execute analysis on all N holdings.

        **Validates: Requirements 3.1**
        """
        # Arrange
        state = FinwizState(
            session_id="test_session",
            current_day=17,
            current_month=11,
            current_year=2025,
            current_date="2025-11-17",
            full_date="November 17, 2025",
            timestamp="2025-11-17T10:00:00",
            report_language="en",
        )

        batch_config = mocker.Mock()
        batch_config.enabled = False
        batch_config.min_holdings_for_batch = 100

        orchestrator = DeepAnalysisOrchestrator(state, batch_prefetch_config=batch_config, cache_service=None, cache_enabled=False)

        def create_result(ticker, asset_class, company_name=""):
            result = DeepAnalysisResult(
                ticker=ticker,
                asset_class=asset_class,
                crew_name="DeepAnalysisCrew",
                grade="A",
                composite_score=0.82,
                fundamental_score=0.85,
                technical_score=0.78,
                risk_score=0.80,
                recommendation="BUY",
                rationale="Test analysis rationale for the holding.",
                fundamental_details={},
                technical_details={},
                risk_details={},
                data_freshness_hours=0.5,
                confidence_level=0.85,
            )
            enriched = mocker.MagicMock()
            enriched.ticker = ticker
            return result, enriched

        mocker.patch(
            "finwiz.analysis.analyze_holding",
            side_effect=create_result,
        )

        # Act
        results = orchestrator.run_deep_analysis_on_holdings(holdings)

        # Assert - Property 8: Completeness
        assert len(results) == len(holdings), f"Expected {len(holdings)} results but got {len(results)}. All holdings should be analyzed."

        for holding in holdings:
            ticker = holding["ticker"]
            assert ticker in results, f"Ticker {ticker} not found in results."

            result = results[ticker]
            assert isinstance(result, DeepAnalysisResult), f"Result for {ticker} is not DeepAnalysisResult"
            assert result.ticker == ticker
            assert result.asset_class == holding["asset_class"]

    @given(
        ticker=st.text(alphabet=st.characters(whitelist_categories=("Lu",)), min_size=1, max_size=5),
        asset_class=st.sampled_from(["stock", "etf", "crypto"]),
        grade=st.sampled_from(["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D", "F"]),
        composite_score=st.floats(min_value=0.0, max_value=1.0),
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_result_structure_validation(self, mocker, ticker, asset_class, grade, composite_score):
        """
        **Feature: flow-orchestrator-refactoring, Property 9: Deep Analysis Result Structure**

        For any deep analysis result, it should conform to the DeepAnalysisResult Pydantic schema.

        **Validates: Requirements 3.2**
        """
        from pydantic import ValidationError

        # Arrange
        state = FinwizState(
            session_id="test_session",
            current_day=17,
            current_month=11,
            current_year=2025,
            current_date="2025-11-17",
            full_date="November 17, 2025",
            timestamp="2025-11-17T10:00:00",
            report_language="en",
        )

        batch_config = mocker.Mock()
        batch_config.enabled = False
        batch_config.min_holdings_for_batch = 100

        orchestrator = DeepAnalysisOrchestrator(state, batch_prefetch_config=batch_config, cache_service=None, cache_enabled=False)

        def create_result(ticker_arg, asset_class_arg, company_name=""):
            result = DeepAnalysisResult(
                ticker=ticker_arg,
                asset_class=asset_class_arg,
                crew_name="DeepAnalysisCrew",
                grade=grade,
                composite_score=composite_score,
                fundamental_score=0.85,
                technical_score=0.78,
                risk_score=0.80,
                recommendation="BUY",
                rationale="Property test analysis rationale.",
                fundamental_details={},
                technical_details={},
                risk_details={},
                data_freshness_hours=0.5,
                confidence_level=0.85,
            )
            enriched = mocker.MagicMock()
            enriched.ticker = ticker_arg
            return result, enriched

        mocker.patch(
            "finwiz.analysis.analyze_holding",
            side_effect=create_result,
        )

        holdings = [{"ticker": ticker, "asset_class": asset_class}]

        # Act
        results = orchestrator.run_deep_analysis_on_holdings(holdings)

        # Assert
        assert len(results) == 1
        result = results[ticker]

        # Property 9: Result Structure Validation
        assert isinstance(result, DeepAnalysisResult)
        assert isinstance(result.ticker, str)
        assert isinstance(result.asset_class, str)
        assert isinstance(result.grade, str)
        assert isinstance(result.composite_score, float)
        assert 0.0 <= result.composite_score <= 1.0

        # Verify Pydantic validation
        try:
            result_dict = result.model_dump()
            DeepAnalysisResult.model_validate(result_dict)
        except ValidationError as e:
            pytest.fail(f"Result failed Pydantic validation: {e}")

    @given(
        ticker=st.text(alphabet=st.characters(whitelist_categories=("Lu",)), min_size=1, max_size=5),
        asset_class=st.sampled_from(["stock", "etf", "crypto"]),
    )
    @settings(max_examples=30, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_pipeline_integration(self, mocker, ticker, asset_class):
        """
        **Feature: deep-analysis-pipeline, Property: Pipeline Integration**

        Verify that the orchestrator correctly integrates with the functional pipeline.
        """
        # Arrange
        state = FinwizState(
            session_id="test_session",
            current_day=17,
            current_month=11,
            current_year=2025,
            current_date="2025-11-17",
            full_date="November 17, 2025",
            timestamp="2025-11-17T10:00:00",
            report_language="en",
        )

        batch_config = mocker.Mock()
        batch_config.enabled = False
        batch_config.min_holdings_for_batch = 100

        orchestrator = DeepAnalysisOrchestrator(state, batch_prefetch_config=batch_config, cache_service=None, cache_enabled=False)

        # Track calls to analyze_holding
        call_count = 0

        def track_calls(ticker_arg, asset_class_arg, company_name=""):
            nonlocal call_count
            call_count += 1
            result = DeepAnalysisResult(
                ticker=ticker_arg,
                asset_class=asset_class_arg,
                crew_name="DeepAnalysisCrew",
                grade="A",
                composite_score=0.82,
                fundamental_score=0.85,
                technical_score=0.78,
                risk_score=0.80,
                recommendation="BUY",
                rationale="Pipeline integration test rationale.",
                fundamental_details={},
                technical_details={},
                risk_details={},
                data_freshness_hours=0.5,
                confidence_level=0.85,
            )
            enriched = mocker.MagicMock()
            enriched.ticker = ticker_arg
            return result, enriched

        mocker.patch(
            "finwiz.analysis.analyze_holding",
            side_effect=track_calls,
        )

        holdings = [{"ticker": ticker, "asset_class": asset_class}]

        # Act
        results = orchestrator.run_deep_analysis_on_holdings(holdings)

        # Assert - Pipeline was called exactly once per holding
        assert call_count == 1, f"analyze_holding should be called exactly once, was called {call_count} times"
        assert ticker in results
