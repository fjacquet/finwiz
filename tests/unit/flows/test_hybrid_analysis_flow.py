"""
Property-based tests for HybridAnalysisFlow.

Tests the flow execution sequence and state management for the hybrid
Python/AI analysis architecture.
"""

import logging
import time
from datetime import datetime

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from pytest import approx

from finwiz.flows.hybrid_analysis_flow import HybridAnalysisFlow
from finwiz.schemas.hybrid_analysis import EnrichedAnalysis
from finwiz.schemas.hybrid_analysis.metadata import DataLineage, DataQualityMetrics


def create_valid_quantitative_data(
    composite_score: float = 0.5,
    fundamental_score: float = 0.5,
    technical_score: float = 0.5,
    risk_score: float = 2.5,  # Must be <= 5.0
    grade: str = "B",
    recommendation: str = "HOLD",
) -> dict:
    """Create valid quantitative analysis data with all required fields."""
    return {
        "composite_score": composite_score,
        "fundamental_score": fundamental_score,
        "technical_score": technical_score,
        "risk_score": min(risk_score, 5.0),  # Ensure max 5.0
        "grade": grade,
        "preliminary_recommendation": recommendation,
        "fundamental_metrics": {"roe": 0.25, "debt_to_equity": 0.5},
        "technical_indicators": {"rsi": 55.0, "macd": 1.2},
        "risk_metrics": {"volatility": 0.15, "beta": 1.1},
        "calculation_timestamp": datetime.now().isoformat(),
        "data_quality": DataQualityMetrics(
            completeness_score=0.95,
            freshness_score=1.0,
            accuracy_confidence=0.90,
            source_reliability=0.85,
            missing_fields=[],
        ).model_dump(),
        "data_lineage": DataLineage(
            primary_sources=["yfinance"],
            collection_timestamp=datetime.now(),
            transformation_steps=["normalize"],
            cache_status="fresh",
        ).model_dump(),
        "confidence_level": 0.90,
        "python_rationale": "Template-generated analysis based on quantitative metrics",
    }


class TestHybridAnalysisFlowExecutionSequence:
    """
    Property 8: Flow Execution Sequence
    Validates: Requirements 4.1

    Test that flow steps execute in correct order:
    collect_data → calculate_quantitative_metrics → analyze_qualitative_insights → synthesize_enriched_analysis
    """

    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        ticker=st.text(min_size=1, max_size=5, alphabet=st.characters(whitelist_categories=("Lu",))),
        asset_class=st.sampled_from(["stock", "etf", "crypto"]),
    )
    def test_flow_execution_order(self, mocker, ticker: str, asset_class: str):
        """
        Property: Flow steps execute in correct order.

        For any valid ticker and asset_class, the flow should execute steps
        in the correct sequence with proper state updates at each step.
        """
        # Arrange
        flow = HybridAnalysisFlow()
        flow.state.ticker = ticker
        flow.state.asset_class = asset_class
        flow.state.company_name = f"{ticker} Corp"

        # Track execution order
        execution_order = []

        # Mock the data collection to track execution
        def mock_collect(ticker, asset_class, existing_data=None):
            execution_order.append("collect_data")
            return {"mock": "data"}

        flow.data_collector.collect_raw_data = mock_collect

        # Act - Execute collect_data
        result = flow.collect_data()

        # Assert - Verify execution order
        assert "collect_data" in execution_order
        assert execution_order[0] == "collect_data"

        # Assert - Verify state updates
        assert flow.state.ticker == ticker
        assert flow.state.asset_class == asset_class
        assert flow.state.raw_data == {"mock": "data"}
        assert flow.state.processing_start > 0

        # Assert - Verify return value for downstream listeners
        assert result["ticker"] == ticker
        assert result["asset_class"] == asset_class
        assert "raw_data" in result
        assert "collection_timestamp" in result

    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        ticker=st.text(min_size=1, max_size=5, alphabet=st.characters(whitelist_categories=("Lu",))),
        asset_class=st.sampled_from(["stock", "etf", "crypto"]),
        composite_score=st.floats(min_value=0.0, max_value=1.0),
    )
    def test_quantitative_calculation_receives_upstream_data(self, mocker, ticker: str, asset_class: str, composite_score: float):
        """
        Property: Quantitative calculation receives data from collect_data.

        For any valid inputs, the calculate_quantitative_metrics method
        should receive data from collect_data as a parameter and update state.
        """
        # Arrange
        flow = HybridAnalysisFlow()

        # Mock the scorer to return predictable results
        from finwiz.flow_state import DeepAnalysisResult

        mock_result = DeepAnalysisResult(
            ticker=ticker,
            asset_class=asset_class,
            crew_name="deep_analysis",
            composite_score=composite_score,
            fundamental_score=0.8,
            technical_score=0.7,
            risk_score=2.5,
            grade="A",
            recommendation="BUY",
            rationale="Test rationale",
            fundamental_details={},
            technical_details={},
            risk_details={},
            data_freshness_hours=1.0,
            confidence_level=0.9,
        )

        flow.scorer.calculate_composite_score = mocker.Mock(return_value=mock_result)

        # Prepare upstream data (as if from collect_data)
        upstream_data = {
            "ticker": ticker,
            "asset_class": asset_class,
            "company_name": f"{ticker} Corp",
            "raw_data": {"test": "data"},
            "collection_timestamp": "2025-01-01T00:00:00",
        }

        # Act
        result = flow.calculate_quantitative_metrics(upstream_data)

        # Assert - Verify scorer was called with correct parameters
        flow.scorer.calculate_composite_score.assert_called_once_with(ticker=ticker, asset_class=asset_class, data={"test": "data"})

        # Assert - Verify state was updated
        assert flow.state.quantitative_analysis is not None
        assert "composite_score" in flow.state.quantitative_analysis
        assert flow.state.quantitative_analysis["composite_score"] == composite_score

        # Assert - Verify return value includes upstream data
        assert result["ticker"] == ticker
        assert result["asset_class"] == asset_class
        assert "quantitative_analysis" in result
        assert "calculation_timestamp" in result

    def test_state_updates_at_each_step(self, mocker):
        """
        Property: State is updated at each flow step.

        For any flow execution, the state should be updated with relevant
        data at each step of the flow.
        """
        # Arrange
        flow = HybridAnalysisFlow()
        flow.state.ticker = "AAPL"
        flow.state.asset_class = "stock"
        flow.state.company_name = "Apple Inc"

        # Mock data collection
        flow.data_collector.collect_raw_data = mocker.Mock(return_value={"price": 150.0})

        # Act - Step 1: collect_data
        result1 = flow.collect_data()

        # Assert - State updated after step 1
        assert flow.state.raw_data == {"price": 150.0}
        assert flow.state.processing_start > 0

        # Mock scorer for step 2
        from finwiz.flow_state import DeepAnalysisResult

        mock_result = DeepAnalysisResult(
            ticker="AAPL",
            asset_class="stock",
            crew_name="deep_analysis",
            composite_score=0.85,
            fundamental_score=0.8,
            technical_score=0.7,
            risk_score=2.5,
            grade="A",
            recommendation="BUY",
            rationale="Test rationale for analysis",
            fundamental_details={},
            technical_details={},
            risk_details={},
            data_freshness_hours=1.0,
            confidence_level=0.9,
        )

        flow.scorer.calculate_composite_score = mocker.Mock(return_value=mock_result)

        # Act - Step 2: calculate_quantitative_metrics
        result2 = flow.calculate_quantitative_metrics(result1)

        # Assert - State updated after step 2
        assert flow.state.quantitative_analysis is not None
        assert "composite_score" in flow.state.quantitative_analysis
        assert flow.state.quantitative_analysis["composite_score"] == approx(0.85)

    def test_data_passing_between_steps(self, mocker):
        """
        Property: Data is correctly passed between flow steps.

        For any flow execution, data returned from one step should be
        available as input to the next step.
        """
        # Arrange
        flow = HybridAnalysisFlow()
        flow.state.ticker = "MSFT"
        flow.state.asset_class = "stock"
        flow.state.company_name = "Microsoft"

        # Mock data collection
        flow.data_collector.collect_raw_data = mocker.Mock(return_value={"volume": 1000000})

        # Act - Step 1
        step1_output = flow.collect_data()

        # Assert - Step 1 output contains expected data
        assert "ticker" in step1_output
        assert "asset_class" in step1_output
        assert "raw_data" in step1_output
        assert step1_output["raw_data"]["volume"] == 1000000

        # Mock scorer
        from finwiz.flow_state import DeepAnalysisResult

        mock_result = DeepAnalysisResult(
            ticker="MSFT",
            asset_class="stock",
            crew_name="deep_analysis",
            composite_score=0.75,
            fundamental_score=0.8,
            technical_score=0.7,
            risk_score=2.5,
            grade="B+",
            recommendation="HOLD",
            rationale="Test rationale for analysis",
            fundamental_details={},
            technical_details={},
            risk_details={},
            data_freshness_hours=1.0,
            confidence_level=0.9,
        )

        flow.scorer.calculate_composite_score = mocker.Mock(return_value=mock_result)

        # Act - Step 2 receives Step 1 output
        step2_output = flow.calculate_quantitative_metrics(step1_output)

        # Assert - Step 2 output includes Step 1 data
        assert step2_output["ticker"] == step1_output["ticker"]
        assert step2_output["asset_class"] == step1_output["asset_class"]
        assert step2_output["raw_data"] == step1_output["raw_data"]
        assert "quantitative_analysis" in step2_output


class TestAIContextIsolation:
    """
    Property 3: AI Context Isolation
    Validates: Requirements 2.1, 5.1

    Test that quantitative data passed as context remains unmodified (READ-ONLY),
    and no financial metrics are recalculated by AI agents.
    """

    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        ticker=st.text(min_size=1, max_size=5, alphabet=st.characters(whitelist_categories=("Lu",))),
        asset_class=st.sampled_from(["stock", "etf", "crypto"]),
        composite_score=st.floats(min_value=0.0, max_value=1.0),
        fundamental_score=st.floats(min_value=0.0, max_value=1.0),
        technical_score=st.floats(min_value=0.0, max_value=1.0),
        risk_score=st.floats(min_value=0.0, max_value=10.0),
        grade=st.sampled_from(["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D", "F"]),
        recommendation=st.sampled_from(["BUY", "HOLD", "SELL"]),
    )
    def test_quantitative_data_passed_as_readonly_context(
        self,
        mocker,
        ticker: str,
        asset_class: str,
        composite_score: float,
        fundamental_score: float,
        technical_score: float,
        risk_score: float,
        grade: str,
        recommendation: str,
    ):
        """
        Property: Quantitative analysis is passed as READ-ONLY context to AI.

        For any valid quantitative analysis data, when passed to the AI crew,
        the original data should remain unmodified (immutable context).
        """
        # Arrange
        flow = HybridAnalysisFlow()

        # Create quantitative analysis data with generated values using helper
        quant_data = create_valid_quantitative_data(
            composite_score=composite_score,
            fundamental_score=fundamental_score,
            technical_score=technical_score,
            risk_score=risk_score,
            grade=grade,
            recommendation=recommendation,
        )

        # Create a deep copy to verify immutability
        import copy

        original_quant_data = copy.deepcopy(quant_data)

        upstream_data = {
            "ticker": ticker,
            "asset_class": asset_class,
            "company_name": f"{ticker} Corp",
            "quantitative_analysis": quant_data,
        }

        # Mock the crew execution to verify inputs
        crew_inputs_received = {}

        def mock_execute_crew(asset_class: str, inputs: dict):
            # Capture the inputs passed to crew
            crew_inputs_received.update(inputs)
            # Simulate AI trying to modify context (should not affect original)
            if "quantitative_analysis" in inputs:
                inputs["quantitative_analysis"]["composite_score"] = 0.99
            # Return mock result (simulating crew output)
            return mocker.Mock()

        mocker.patch.object(flow, "_execute_crew", side_effect=mock_execute_crew)
        mocker.patch.object(flow, "_extract_raw_output", return_value={})

        # Mock validate_ai_output_with_retry to return a QualitativeInsights object
        from datetime import datetime

        from finwiz.schemas.hybrid_analysis.qualitative import (
            ContextualRiskInsights,
            FundamentalContextInsights,
            InvestmentSynthesis,
            QualitativeInsights,
            SecAnalysisInsights,
            TechnicalStrategyInsights,
        )

        mock_insights = QualitativeInsights(
            sec_insights=SecAnalysisInsights(
                business_model="Test business model analysis " * 20,
                competitive_advantages=["Strong brand"],
                risk_factors=["Market competition"],
            ),
            fundamental_context=FundamentalContextInsights(
                industry_analysis="Test industry analysis " * 20,
                growth_drivers=["Innovation"],
                competitive_positioning="Market leader in segment with strong positioning and advantages",
                management_assessment="Experienced leadership team with proven track record of success",
            ),
            technical_strategy=TechnicalStrategyInsights(
                chart_patterns=["Bullish flag"],
                support_resistance="Support at 100 with strong buying interest, resistance at 120 with profit taking",
                entry_exit_strategy="Test entry exit strategy " * 20,
                timing_assessment="Positive momentum with strong volume and upward trend continuation expected",
            ),
            contextual_risks=ContextualRiskInsights(regulatory_risks=["Regulatory changes"], geopolitical_risks=["Trade tensions"]),
            investment_synthesis=InvestmentSynthesis(
                investment_thesis="Test investment thesis " * 40,
                bull_case="Test bull case " * 20,
                base_case="Test base case " * 20,
                bear_case="Test bear case " * 20,
                scenario_probabilities={"bull": 0.3, "base": 0.5, "bear": 0.2},
                final_recommendation="BUY",
                recommendation_confidence="HIGH",
                action_plan={
                    "immediate_actions": ["Monitor"],
                    "monitoring_points": ["Price"],
                    "exit_triggers": ["Loss"],
                },
            ),
            analysis_timestamp=datetime.now(),
            ai_confidence=0.85,
        )
        mocker.patch("finwiz.validation.ai_output_validator.validate_ai_output_with_retry", return_value=mock_insights)

        # Act
        flow.analyze_qualitative_insights(upstream_data)

        # Assert - Verify quantitative data was passed as context
        assert "quantitative_analysis" in crew_inputs_received
        assert crew_inputs_received["grade"] == grade
        assert crew_inputs_received["score"] == composite_score
        assert crew_inputs_received["preliminary_recommendation"] == recommendation

        # Assert - CRITICAL: Verify original data was NOT modified
        assert upstream_data["quantitative_analysis"]["composite_score"] == original_quant_data["composite_score"]
        assert upstream_data["quantitative_analysis"]["grade"] == original_quant_data["grade"]
        assert upstream_data["quantitative_analysis"]["preliminary_recommendation"] == original_quant_data["preliminary_recommendation"]

        # Assert - Verify all nested metrics remain unchanged
        assert upstream_data["quantitative_analysis"]["fundamental_metrics"] == original_quant_data["fundamental_metrics"]
        assert upstream_data["quantitative_analysis"]["technical_indicators"] == original_quant_data["technical_indicators"]
        assert upstream_data["quantitative_analysis"]["risk_metrics"] == original_quant_data["risk_metrics"]

    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        ticker=st.text(min_size=1, max_size=5, alphabet=st.characters(whitelist_categories=("Lu",))),
        asset_class=st.sampled_from(["stock", "etf", "crypto"]),
        composite_score=st.floats(min_value=0.0, max_value=1.0),
        grade=st.sampled_from(["A+", "A", "B+", "B", "C", "D", "F"]),
        recommendation=st.sampled_from(["BUY", "HOLD", "SELL"]),
    )
    def test_ai_receives_calculated_metrics_not_raw_data(
        self,
        mocker,
        ticker: str,
        asset_class: str,
        composite_score: float,
        grade: str,
        recommendation: str,
    ):
        """
        Property: AI crew receives pre-calculated metrics, not raw data for recalculation.

        For any AI crew execution, the crew should receive calculated scores
        and grades, not raw financial data that would require recalculation.
        This prevents AI from performing financial calculations.
        """
        # Arrange
        flow = HybridAnalysisFlow()

        upstream_data = {
            "ticker": ticker,
            "asset_class": asset_class,
            "company_name": f"{ticker} Corporation",
            "quantitative_analysis": create_valid_quantitative_data(
                composite_score=composite_score,
                grade=grade,
                recommendation=recommendation,
            ),
        }

        crew_inputs_received = {}

        def mock_execute_crew(asset_class: str, inputs: dict):
            crew_inputs_received.update(inputs)
            return mocker.Mock()

        mocker.patch.object(flow, "_execute_crew", side_effect=mock_execute_crew)
        mocker.patch.object(flow, "_extract_raw_output", return_value={})

        # Mock validate_ai_output_with_retry to return a QualitativeInsights object
        from datetime import datetime

        from finwiz.schemas.hybrid_analysis.qualitative import (
            ContextualRiskInsights,
            FundamentalContextInsights,
            InvestmentSynthesis,
            QualitativeInsights,
            SecAnalysisInsights,
            TechnicalStrategyInsights,
        )

        mock_insights = QualitativeInsights(
            sec_insights=SecAnalysisInsights(
                business_model="Test business model analysis " * 20,
                competitive_advantages=["Strong brand"],
                risk_factors=["Market competition"],
            ),
            fundamental_context=FundamentalContextInsights(
                industry_analysis="Test industry analysis " * 20,
                growth_drivers=["Innovation"],
                competitive_positioning="Market leader in segment with strong positioning and advantages",
                management_assessment="Experienced leadership team with proven track record of success",
            ),
            technical_strategy=TechnicalStrategyInsights(
                chart_patterns=["Bullish flag"],
                support_resistance="Support at 100 with strong buying interest, resistance at 120 with profit taking",
                entry_exit_strategy="Test entry exit strategy " * 20,
                timing_assessment="Positive momentum with strong volume and upward trend continuation expected",
            ),
            contextual_risks=ContextualRiskInsights(regulatory_risks=["Regulatory changes"], geopolitical_risks=["Trade tensions"]),
            investment_synthesis=InvestmentSynthesis(
                investment_thesis="Test investment thesis " * 40,
                bull_case="Test bull case " * 20,
                base_case="Test base case " * 20,
                bear_case="Test bear case " * 20,
                scenario_probabilities={"bull": 0.3, "base": 0.5, "bear": 0.2},
                final_recommendation="BUY",
                recommendation_confidence="HIGH",
                action_plan={
                    "immediate_actions": ["Monitor"],
                    "monitoring_points": ["Price"],
                    "exit_triggers": ["Loss"],
                },
            ),
            analysis_timestamp=datetime.now(),
            ai_confidence=0.85,
        )
        mocker.patch("finwiz.validation.ai_output_validator.validate_ai_output_with_retry", return_value=mock_insights)

        # Act
        try:
            flow.analyze_qualitative_insights(upstream_data)
        except Exception:
            pass

        # Assert - Verify crew receives CALCULATED metrics
        assert "grade" in crew_inputs_received
        assert "score" in crew_inputs_received
        assert "preliminary_recommendation" in crew_inputs_received

        # Assert - Verify values match the pre-calculated ones
        assert crew_inputs_received["grade"] == grade
        assert crew_inputs_received["score"] == composite_score
        assert crew_inputs_received["preliminary_recommendation"] == recommendation

        # Assert - Verify crew does NOT receive raw financial data
        # (Raw data would be things like price, revenue, earnings, etc.)
        assert "price" not in crew_inputs_received
        assert "revenue" not in crew_inputs_received
        assert "earnings" not in crew_inputs_received
        assert "raw_data" not in crew_inputs_received

    def test_quantitative_metrics_immutability_across_multiple_calls(self, mocker):
        """
        Property: Quantitative metrics remain immutable across multiple AI calls.

        For any sequence of AI crew executions, the quantitative analysis
        should remain unchanged, proving true READ-ONLY behavior.
        """
        # Arrange
        flow = HybridAnalysisFlow()

        original_quant = {
            "composite_score": 0.85,
            "fundamental_score": 0.80,
            "technical_score": 0.70,
            "risk_score": 2.5,
            "grade": "A",
            "preliminary_recommendation": "BUY",
            "fundamental_metrics": {"roe": 0.25},
            "technical_indicators": {"rsi": 55.0},
            "risk_metrics": {"volatility": 0.15},
        }

        upstream_data = {
            "ticker": "TEST",
            "asset_class": "stock",
            "company_name": "Test Corp",
            "quantitative_analysis": original_quant.copy(),
        }

        def mock_get_crew(ac):
            mock_crew_instance = mocker.Mock()
            mock_crew_obj = mocker.Mock()

            def mock_kickoff(inputs):
                # Simulate AI attempting to modify context
                if "quantitative_analysis" in inputs:
                    inputs["quantitative_analysis"]["composite_score"] = 0.99
                    inputs["quantitative_analysis"]["grade"] = "F"
                return mocker.Mock()

            mock_crew_obj.kickoff = mock_kickoff
            mock_crew_instance.crew = mocker.Mock(return_value=mock_crew_obj)
            return mock_crew_instance

        flow._get_analysis_crew = mock_get_crew
        flow._extract_raw_output = mocker.Mock(return_value={})

        # Mock validate_ai_output_with_retry to return a mock QualitativeInsights
        mock_insights = mocker.Mock(model_dump=mocker.Mock(return_value={}))
        mocker.patch(
            "finwiz.validation.ai_output_validator.validate_ai_output_with_retry",
            return_value=mock_insights
        )

        # Act - Call multiple times
        for _ in range(3):
            try:
                flow.analyze_qualitative_insights(upstream_data)
            except Exception:
                pass

        # Assert - Original data unchanged after multiple calls
        assert upstream_data["quantitative_analysis"]["composite_score"] == approx(0.85)
        assert upstream_data["quantitative_analysis"]["grade"] == "A"
        assert upstream_data["quantitative_analysis"]["preliminary_recommendation"] == "BUY"
        assert upstream_data["quantitative_analysis"]["fundamental_metrics"]["roe"] == approx(0.25)


class TestRecommendationSynthesis:
    """
    Property 7: Recommendation Discrepancy Logging.

    Validates: Requirements 3.4

    Test that when recommendations differ, a warning log is created with reasoning.
    """

    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        recommendation=st.sampled_from(["BUY", "HOLD", "SELL"]),
        confidence_rationale=st.text(min_size=10, max_size=100),
    )
    def test_matching_recommendations_no_warning(self, mocker, caplog, recommendation: str, confidence_rationale: str):
        """
        Property: When recommendations match, no discrepancy warning is logged.

        For any case where Python and AI recommendations agree,
        no warning should be logged.
        """
        # Arrange
        flow = HybridAnalysisFlow()

        quant = mocker.Mock()
        quant.preliminary_recommendation = recommendation

        qual = mocker.Mock()
        qual.investment_synthesis.final_recommendation = recommendation
        qual.investment_synthesis.confidence_rationale = confidence_rationale

        # Act
        with caplog.at_level(logging.WARNING):
            result = flow.synthesizer._synthesize_recommendation(quant, qual)

        # Assert - Recommendation matches
        assert result == recommendation

        # Assert - No discrepancy warning logged
        assert "discrepancy" not in caplog.text.lower()

    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        python_rec=st.sampled_from(["BUY", "HOLD", "SELL"]),
        ai_rec=st.sampled_from(["BUY", "HOLD", "SELL"]),
        confidence_rationale=st.text(min_size=10, max_size=100),
    )
    def test_differing_recommendations_logs_warning(self, mocker, caplog, python_rec: str, ai_rec: str, confidence_rationale: str):
        """
        Property: When recommendations differ, a warning is logged with reasoning.

        For any case where Python and AI recommendations disagree,
        a warning log entry should be created with the reasoning.
        """
        # Skip if recommendations match (not testing discrepancy case)
        if python_rec == ai_rec:
            return

        # Arrange
        flow = HybridAnalysisFlow()

        quant = mocker.Mock()
        quant.preliminary_recommendation = python_rec

        qual = mocker.Mock()
        qual.investment_synthesis.final_recommendation = ai_rec
        qual.investment_synthesis.confidence_rationale = confidence_rationale

        # Act
        with caplog.at_level(logging.WARNING):
            result = flow.synthesizer._synthesize_recommendation(quant, qual)

        # Assert - Python recommendation is used
        assert result == python_rec

        # Assert - Warning was logged with both recommendations
        assert "discrepancy" in caplog.text.lower()
        assert f"Python={python_rec}" in caplog.text
        assert f"AI={ai_rec}" in caplog.text

        # Assert - Reasoning is captured in log
        assert confidence_rationale in caplog.text

    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        python_rec=st.sampled_from(["BUY", "HOLD", "SELL"]),
        ai_rec=st.sampled_from(["BUY", "HOLD", "SELL"]),
        confidence_rationale=st.text(min_size=10, max_size=100),
    )
    def test_final_recommendation_uses_python_on_disagreement(self, mocker, python_rec: str, ai_rec: str, confidence_rationale: str):
        """
        Property: When recommendations differ, Python recommendation is used.

        For any disagreement, the final recommendation should be the
        Python-calculated preliminary recommendation.
        """
        # Skip if recommendations match (not testing discrepancy case)
        if python_rec == ai_rec:
            return

        # Arrange
        flow = HybridAnalysisFlow()

        quant = mocker.Mock()
        quant.preliminary_recommendation = python_rec

        qual = mocker.Mock()
        qual.investment_synthesis.final_recommendation = ai_rec
        qual.investment_synthesis.confidence_rationale = confidence_rationale

        # Act
        result = flow.synthesizer._synthesize_recommendation(quant, qual)

        # Assert - Python recommendation always wins on disagreement
        assert result == python_rec
        assert result != ai_rec  # Verify it's not using AI recommendation


class TestFallbackCreation:
    """
    Property 9: Fallback Analysis Creation
    Validates: Requirements 4.2, 6.2

    Test that fallback analysis is created on AI failure using Python-only results
    with confidence set to "LOW".
    """

    def test_fallback_created_on_ai_failure(self):
        """
        Property: Fallback analysis is created when AI analysis fails.

        For any AI failure, the system should create a fallback
        EnrichedAnalysis using Python-only results.
        """
        # Arrange
        flow = HybridAnalysisFlow()

        data = {
            "ticker": "AAPL",
            "company_name": "Apple Inc",
            "asset_class": "stock",
            "quantitative_analysis": {
                "composite_score": 0.85,
                "fundamental_score": 0.8,
                "technical_score": 0.7,
                "risk_score": 2.5,
                "grade": "A",
                "preliminary_recommendation": "BUY",
                "fundamental_metrics": {},
                "technical_indicators": {},
                "risk_metrics": {},
                "calculation_timestamp": datetime.now(),
                "data_quality": {
                    "completeness_score": 0.9,
                    "freshness_score": 0.95,
                    "accuracy_confidence": 0.85,
                    "source_reliability": 0.9,
                    "missing_fields": [],
                },
                "data_lineage": {
                    "primary_sources": ["test"],
                    "collection_timestamp": datetime.now(),
                    "transformation_steps": [],
                    "cache_status": "fresh",
                },
                "confidence_level": 0.85,
                "python_rationale": "Test rationale for fallback analysis",
            },
        }

        flow.state.processing_start = time.time()

        # Act
        result = flow.synthesizer.create_fallback_analysis(data, flow.state)

        # Assert - Fallback analysis created
        assert result is not None
        assert isinstance(result, EnrichedAnalysis)

    def test_fallback_uses_python_only_results(self):
        """
        Property: Fallback analysis uses only Python-calculated results.

        For any fallback, the analysis should be based solely on
        quantitative metrics, not AI insights.
        """
        # Arrange
        flow = HybridAnalysisFlow()

        data = {
            "ticker": "MSFT",
            "company_name": "Microsoft",
            "asset_class": "stock",
            "quantitative_analysis": {
                "composite_score": 0.75,
                "fundamental_score": 0.8,
                "technical_score": 0.7,
                "risk_score": 2.5,
                "grade": "B+",
                "preliminary_recommendation": "HOLD",
                "fundamental_metrics": {},
                "technical_indicators": {},
                "risk_metrics": {},
                "calculation_timestamp": datetime.now(),
                "data_quality": {
                    "completeness_score": 0.9,
                    "freshness_score": 0.95,
                    "accuracy_confidence": 0.85,
                    "source_reliability": 0.9,
                    "missing_fields": [],
                },
                "data_lineage": {
                    "primary_sources": ["test"],
                    "collection_timestamp": datetime.now(),
                    "transformation_steps": [],
                    "cache_status": "fresh",
                },
                "confidence_level": 0.85,
                "python_rationale": "Test rationale for fallback analysis",
            },
        }

        flow.state.processing_start = time.time()

        # Act
        result = flow.synthesizer.create_fallback_analysis(data, flow.state)

        # Assert - Uses Python results
        assert result.final_grade == "B+"
        assert result.final_score == approx(0.75)
        assert result.final_recommendation == "HOLD"

        # Assert - Qualitative insights are minimal/placeholder
        assert "unavailable" in result.qualitative.sec_insights.business_model.lower()

    def test_fallback_confidence_set_to_low(self):
        """
        Property: Fallback analysis has confidence set to "LOW".

        For any fallback analysis, the recommendation_confidence
        should be set to "LOW" to indicate degraded quality.
        """
        # Arrange
        flow = HybridAnalysisFlow()

        data = {
            "ticker": "GOOGL",
            "company_name": "Google",
            "asset_class": "stock",
            "quantitative_analysis": {
                "composite_score": 0.90,
                "fundamental_score": 0.8,
                "technical_score": 0.7,
                "risk_score": 2.5,
                "grade": "A+",
                "preliminary_recommendation": "BUY",
                "fundamental_metrics": {},
                "technical_indicators": {},
                "risk_metrics": {},
                "calculation_timestamp": datetime.now(),
                "data_quality": {
                    "completeness_score": 0.9,
                    "freshness_score": 0.95,
                    "accuracy_confidence": 0.85,
                    "source_reliability": 0.9,
                    "missing_fields": [],
                },
                "data_lineage": {
                    "primary_sources": ["test"],
                    "collection_timestamp": datetime.now(),
                    "transformation_steps": [],
                    "cache_status": "fresh",
                },
                "confidence_level": 0.85,
                "python_rationale": "Test rationale for fallback analysis",
            },
        }

        flow.state.processing_start = time.time()

        # Act
        result = flow.synthesizer.create_fallback_analysis(data, flow.state)

        # Assert - Confidence is LOW
        assert result.recommendation_confidence == "LOW"

        # Assert - LLM cost is zero (no AI used)
        assert result.llm_cost_dollars == approx(0.0)
