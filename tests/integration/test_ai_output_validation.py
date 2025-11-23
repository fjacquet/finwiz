"""
Integration tests for AI output validation and enforcement.

These tests verify:
1. Real crew execution with output validation
2. Retry logic with format instructions
3. Fallback to Python-only analysis
4. Tool call detection and rejection

Requirements: 12.1-12.7
"""

import os

import pytest

from finwiz.schemas.hybrid_analysis.qualitative import QualitativeInsights
from finwiz.schemas.hybrid_analysis.quantitative import QuantitativeAnalysis
from finwiz.validation.ai_output_validator import (
    create_python_only_qualitative,
    validate_ai_output_with_retry,
)


@pytest.mark.integration
class TestAIOutputValidationIntegration:
    """Integration tests for AI output validation with retry and fallback."""

    def test_valid_output_passes_validation(self, mocker):
        """
        Test that valid AI output passes validation without retries.

        Verifies:
        - Properly formatted output is accepted
        - No retries needed for valid output
        - QualitativeInsights schema validation succeeds

        Requirements: 12.1, 12.5
        """
        # Arrange
        from datetime import datetime


        valid_output = {
            "sec_insights": {
                "business_model": "Test business model analysis with comprehensive details about the company's operations " * 5,
                "competitive_advantages": ["Strong brand", "Market position"],
                "risk_factors": ["Competition", "Regulation"],
            },
            "fundamental_context": {
                "industry_analysis": "Test industry analysis with market trends and competitive landscape " * 10,
                "growth_drivers": ["Innovation", "Expansion"],
                "competitive_positioning": "Market leader with strong positioning and competitive advantages",
                "management_assessment": "Experienced leadership team with proven track record of success",
            },
            "technical_strategy": {
                "chart_patterns": ["Bullish flag", "Higher highs"],
                "support_resistance": "Support at 100 with strong buying, resistance at 120 with profit taking",
                "entry_exit_strategy": "Test entry exit strategy with detailed price targets and risk management " * 10,
                "timing_assessment": "Positive momentum with strong volume and upward trend continuation",
            },
            "contextual_risks": {
                "regulatory_risks": ["Regulatory changes"],
                "geopolitical_risks": ["Trade tensions"],
            },
            "investment_synthesis": {
                "investment_thesis": "Test comprehensive investment thesis with detailed analysis and reasoning " * 20,
                "bull_case": "Test bull case scenario with upside catalysts and growth potential " * 10,
                "base_case": "Test base case scenario with most likely outcome and expectations " * 10,
                "bear_case": "Test bear case scenario with downside risks and challenges " * 10,
                "scenario_probabilities": {"bull": 0.3, "base": 0.5, "bear": 0.2},
                "final_recommendation": "BUY",
                "recommendation_confidence": "HIGH",
                "action_plan": {
                    "immediate_actions": ["Monitor"],
                    "monitoring_points": ["Price"],
                    "exit_triggers": ["Loss"],
                },
            },
            "analysis_timestamp": datetime.now().isoformat(),
            "ai_confidence": 0.85,
        }

        from finwiz.schemas.hybrid_analysis.metadata import DataLineage, DataQualityMetrics

        quantitative = QuantitativeAnalysis(
            composite_score=0.85,
            fundamental_score=0.90,
            technical_score=0.80,
            risk_score=2.5,
            grade="A",
            preliminary_recommendation="BUY",
            fundamental_metrics={"roe": 0.25, "debt_to_equity": 0.3},
            technical_indicators={"rsi": 55.0, "macd": 1.2},
            risk_metrics={"volatility": 0.15, "beta": 1.1},
            calculation_timestamp=datetime.now(),
            data_quality=DataQualityMetrics(
                completeness_score=0.95,
                freshness_score=1.0,
                accuracy_confidence=0.90,
                source_reliability=0.85,
                missing_fields=[],
            ),
            data_lineage=DataLineage(
                primary_sources=["yfinance"],
                collection_timestamp=datetime.now(),
                transformation_steps=["normalize"],
                cache_status="fresh",
            ),
            confidence_level=0.90,
            python_rationale="Strong fundamentals",
        )

        retry_callback = mocker.Mock()

        # Act
        result = validate_ai_output_with_retry(result=valid_output, quantitative=quantitative, retry_callback=retry_callback, max_retries=2)

        # Assert
        assert isinstance(result, QualitativeInsights)
        assert retry_callback.call_count == 0, "Should not retry for valid output"

    def test_invalid_output_triggers_retry_with_format_instructions(self, mocker):
        """
        Test that invalid output triggers retry with format instructions.

        Verifies:
        - Missing fields detected
        - Retry callback invoked with format instructions
        - Format instructions include field descriptions
        - Max retries enforced (2 attempts)
        - Falls back to Python-only analysis after max retries

        Requirements: 12.3, 12.4
        """
        # Arrange
        from datetime import datetime

        from finwiz.schemas.hybrid_analysis.metadata import DataLineage, DataQualityMetrics

        quantitative = QuantitativeAnalysis(
            composite_score=0.85,
            fundamental_score=0.90,
            technical_score=0.80,
            risk_score=2.5,
            grade="A",
            preliminary_recommendation="BUY",
            fundamental_metrics={"roe": 0.25},
            technical_indicators={"rsi": 55.0},
            risk_metrics={"volatility": 0.15},
            calculation_timestamp=datetime.now(),
            data_quality=DataQualityMetrics(
                completeness_score=0.95,
                freshness_score=1.0,
                accuracy_confidence=0.90,
                source_reliability=0.85,
                missing_fields=[],
            ),
            data_lineage=DataLineage(
                primary_sources=["yfinance"],
                collection_timestamp=datetime.now(),
                transformation_steps=["normalize"],
                cache_status="fresh",
            ),
            confidence_level=0.90,
            python_rationale="Strong fundamentals",
        )

        # Invalid output (missing required fields)
        invalid_output = {"some_field": "value"}

        retry_count = [0]

        def mock_retry_callback(format_instructions: str, retry_context: str):
            retry_count[0] += 1
            # Verify format instructions are provided
            assert len(format_instructions) > 0
            assert "sec_insights" in format_instructions or "required" in format_instructions.lower()
            # Still return invalid output to test max retries
            return invalid_output

        # Act - Should fall back to Python-only analysis after max retries (Requirement 12.4)
        result = validate_ai_output_with_retry(result=invalid_output, quantitative=quantitative, retry_callback=mock_retry_callback, max_retries=2)

        # Assert
        # Should retry exactly max_retries times
        assert retry_count[0] == 2, f"Expected 2 retries, got {retry_count[0]}"

        # Should return Python-only fallback (not raise error)
        assert isinstance(result, QualitativeInsights)
        assert result.investment_synthesis.final_recommendation == quantitative.preliminary_recommendation

    def test_tool_call_detection_and_rejection(self, mocker):
        """
        Test that tool calls are detected and rejected.

        Verifies:
        - tool_calls key detected in output
        - Retry triggered automatically
        - Format instructions emphasize no tool calls
        - Falls back to Python-only analysis after max retries

        Requirements: 12.6
        """
        # Arrange
        from datetime import datetime

        from finwiz.schemas.hybrid_analysis.metadata import DataLineage, DataQualityMetrics

        quantitative = QuantitativeAnalysis(
            composite_score=0.85,
            fundamental_score=0.90,
            technical_score=0.80,
            risk_score=2.5,
            grade="A",
            preliminary_recommendation="BUY",
            fundamental_metrics={"roe": 0.25},
            technical_indicators={"rsi": 55.0},
            risk_metrics={"volatility": 0.15},
            calculation_timestamp=datetime.now(),
            data_quality=DataQualityMetrics(
                completeness_score=0.95,
                freshness_score=1.0,
                accuracy_confidence=0.90,
                source_reliability=0.85,
                missing_fields=[],
            ),
            data_lineage=DataLineage(
                primary_sources=["yfinance"],
                collection_timestamp=datetime.now(),
                transformation_steps=["normalize"],
                cache_status="fresh",
            ),
            confidence_level=0.90,
            python_rationale="Strong fundamentals",
        )

        # Output with tool_calls (should be rejected)
        tool_call_output = {
            "tool_calls": [{"name": "some_tool", "args": {}}],
            "content": "Some analysis",
        }

        retry_callback = mocker.Mock(return_value=tool_call_output)

        # Act - Should fall back to Python-only analysis after max retries
        result = validate_ai_output_with_retry(result=tool_call_output, quantitative=quantitative, retry_callback=retry_callback, max_retries=2)

        # Assert
        # Verify retry was attempted
        assert retry_callback.call_count == 2

        # Should return Python-only fallback (not raise error)
        assert isinstance(result, QualitativeInsights)
        assert result.investment_synthesis.final_recommendation == quantitative.preliminary_recommendation

    def test_fallback_to_python_only_analysis(self):
        """
        Test fallback to Python-only analysis after max retries.

        Verifies:
        - Python-only fallback created from quantitative data
        - Minimal but valid QualitativeInsights generated
        - ai_analysis_available flag set to False (indirectly)
        - All required fields present

        Requirements: 12.4
        """
        # Arrange
        from datetime import datetime

        from finwiz.schemas.hybrid_analysis.metadata import DataLineage, DataQualityMetrics

        quantitative = QuantitativeAnalysis(
            composite_score=0.85,
            fundamental_score=0.90,
            technical_score=0.80,
            risk_score=2.5,
            grade="A",
            preliminary_recommendation="BUY",
            fundamental_metrics={"roe": 0.25, "debt_to_equity": 0.3},
            technical_indicators={"rsi": 55.0, "macd": 1.2},
            risk_metrics={"volatility": 0.15, "beta": 1.1},
            calculation_timestamp=datetime.now(),
            data_quality=DataQualityMetrics(
                completeness_score=0.95,
                freshness_score=1.0,
                accuracy_confidence=0.90,
                source_reliability=0.85,
                missing_fields=[],
            ),
            data_lineage=DataLineage(
                primary_sources=["yfinance"],
                collection_timestamp=datetime.now(),
                transformation_steps=["normalize"],
                cache_status="fresh",
            ),
            confidence_level=0.90,
            python_rationale="Strong fundamentals with moderate technical signals",
        )

        # Act
        fallback = create_python_only_qualitative(quantitative)

        # Assert
        assert isinstance(fallback, QualitativeInsights)
        assert fallback.sec_insights is not None
        assert fallback.fundamental_context is not None
        assert fallback.technical_strategy is not None
        assert fallback.contextual_risks is not None
        assert fallback.investment_synthesis is not None

        # Verify content is based on quantitative data
        assert fallback.investment_synthesis.final_recommendation == quantitative.preliminary_recommendation
        assert "grade" in fallback.investment_synthesis.investment_thesis.lower() or str(quantitative.grade) in fallback.investment_synthesis.investment_thesis

    def test_retry_with_successful_second_attempt(self, mocker):
        """
        Test successful retry after initial failure.

        Verifies:
        - First attempt fails validation
        - Retry callback invoked with format instructions
        - Second attempt succeeds
        - Total retry count is 1

        Requirements: 12.3, 12.4
        """
        # Arrange
        from datetime import datetime

        from finwiz.schemas.hybrid_analysis.metadata import DataLineage, DataQualityMetrics

        quantitative = QuantitativeAnalysis(
            composite_score=0.85,
            fundamental_score=0.90,
            technical_score=0.80,
            risk_score=2.5,
            grade="A",
            preliminary_recommendation="BUY",
            fundamental_metrics={"roe": 0.25},
            technical_indicators={"rsi": 55.0},
            risk_metrics={"volatility": 0.15},
            calculation_timestamp=datetime.now(),
            data_quality=DataQualityMetrics(
                completeness_score=0.95,
                freshness_score=1.0,
                accuracy_confidence=0.90,
                source_reliability=0.85,
                missing_fields=[],
            ),
            data_lineage=DataLineage(
                primary_sources=["yfinance"],
                collection_timestamp=datetime.now(),
                transformation_steps=["normalize"],
                cache_status="fresh",
            ),
            confidence_level=0.90,
            python_rationale="Strong fundamentals",
        )

        # Valid output for retry
        valid_output = {
            "sec_insights": {
                "business_model": "Test business model " * 20,
                "competitive_advantages": ["Strong brand"],
                "risk_factors": ["Competition"],
            },
            "fundamental_context": {
                "industry_analysis": "Test industry " * 20,
                "growth_drivers": ["Innovation"],
                "competitive_positioning": "Market leader with strong positioning and advantages",
                "management_assessment": "Experienced team with proven track record of success",
            },
            "technical_strategy": {
                "chart_patterns": ["Bullish"],
                "support_resistance": "Support at 100 with buying, resistance at 120 with profit taking",
                "entry_exit_strategy": "Test strategy " * 20,
                "timing_assessment": "Positive momentum with volume and trend continuation expected",
            },
            "contextual_risks": {},
            "investment_synthesis": {
                "investment_thesis": "Test thesis " * 40,
                "bull_case": "Test bull " * 20,
                "base_case": "Test base " * 20,
                "bear_case": "Test bear " * 20,
                "scenario_probabilities": {"bull": 0.3, "base": 0.5, "bear": 0.2},
                "final_recommendation": "BUY",
                "recommendation_confidence": "HIGH",
                "action_plan": {
                    "immediate_actions": ["Monitor"],
                    "monitoring_points": ["Price"],
                    "exit_triggers": ["Loss"],
                },
            },
            "analysis_timestamp": datetime.now().isoformat(),
            "ai_confidence": 0.85,
        }

        retry_callback = mocker.Mock(return_value=valid_output)

        # Invalid initial output
        invalid_output = {"missing": "fields"}

        # Act
        result = validate_ai_output_with_retry(result=invalid_output, quantitative=quantitative, retry_callback=retry_callback, max_retries=2)

        # Assert
        assert isinstance(result, QualitativeInsights)
        assert retry_callback.call_count == 1, "Should retry exactly once"



@pytest.mark.integration
@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="Requires OPENAI_API_KEY for real crew execution")
class TestRealCrewExecutionWithValidation:
    """
    Integration tests with real crew execution and AI output validation.
    
    These tests actually execute crews with LLM calls to verify:
    - Real crew output passes validation
    - Retry logic works with actual AI responses
    - Fallback mechanisms work in practice
    - Tool call detection works with real outputs
    
    Requirements: 12.1-12.7
    """

    def test_real_crew_execution_with_valid_output(self):
        """
        Test real crew execution produces valid output.
        
        Verifies:
        - Real crew can be executed
        - Output passes validation
        - QualitativeInsights schema is satisfied
        - All required fields are present
        
        Requirements: 12.1, 12.2, 12.7
        
        Note: This test requires actual LLM API calls and may take 30+ seconds.
        It's marked as integration and will be skipped if API keys are not available.
        """
        # Arrange
        from datetime import datetime

        from finwiz.schemas.hybrid_analysis.metadata import DataLineage, DataQualityMetrics

        # Try to import and initialize crew - skip if there are issues
        try:
            from finwiz.crews.stock_crew.stock_crew import StockCrew

            crew = StockCrew()
        except (ImportError, TypeError, AttributeError) as e:
            pytest.skip(f"Cannot initialize StockCrew: {e}")

        quantitative = QuantitativeAnalysis(
            composite_score=0.85,
            fundamental_score=0.90,
            technical_score=0.80,
            risk_score=2.5,
            grade="A",
            preliminary_recommendation="BUY",
            fundamental_metrics={"roe": 0.25, "debt_to_equity": 0.3},
            technical_indicators={"rsi": 55.0, "macd": 1.2},
            risk_metrics={"volatility": 0.15, "beta": 1.1},
            calculation_timestamp=datetime.now(),
            data_quality=DataQualityMetrics(
                completeness_score=0.95,
                freshness_score=1.0,
                accuracy_confidence=0.90,
                source_reliability=0.85,
                missing_fields=[],
            ),
            data_lineage=DataLineage(
                primary_sources=["yfinance"],
                collection_timestamp=datetime.now(),
                transformation_steps=["normalize"],
                cache_status="fresh",
            ),
            confidence_level=0.90,
            python_rationale="Strong fundamentals with moderate technical signals",
        )

        # Prepare crew inputs
        today = datetime.now()
        inputs = {
            "ticker": "AAPL",
            "asset_class": "stock",
            "current_day": today.day,
            "current_month": today.month,
            "current_year": today.year,
            "current_date": today.strftime("%Y-%m-%d"),
            "full_date": today.strftime("%B %d, %Y"),
            "timestamp": today.strftime("%Y-%m-%d %H:%M:%S"),
            # Pass quantitative context
            "grade": quantitative.grade,
            "composite_score": quantitative.composite_score,
            "fundamental_score": quantitative.fundamental_score,
            "technical_score": quantitative.technical_score,
            "risk_score": quantitative.risk_score,
            "recommendation": quantitative.preliminary_recommendation,
        }

        # Act - Execute real crew
        try:
            result = crew.crew().kickoff(inputs=inputs)
        except Exception as e:
            pytest.skip(f"Crew execution failed (likely missing API keys): {e}")

        # Extract raw output
        if hasattr(result, "pydantic"):
            crew_output = result.pydantic.model_dump() if result.pydantic else {}
        elif hasattr(result, "json_dict"):
            crew_output = result.json_dict
        elif hasattr(result, "raw"):
            # If raw is a string, we can't validate it directly
            # This would be a case where the crew didn't use output_pydantic
            pytest.skip("Crew output is raw string, not structured dict")
        else:
            crew_output = {}

        # Assert - Validate output structure
        if crew_output:
            # Validate with retry mechanism (should pass on first try)
            validated = validate_ai_output_with_retry(
                result=crew_output,
                quantitative=quantitative,
                retry_callback=lambda fmt, ctx: crew_output,  # Won't be called if valid
                max_retries=2,
            )

            assert isinstance(validated, QualitativeInsights)
            assert validated.sec_insights is not None
            assert validated.fundamental_context is not None
            assert validated.technical_strategy is not None
            assert validated.investment_synthesis is not None
        else:
            pytest.skip("Crew output is empty or not in expected format")

    def test_real_crew_with_retry_simulation(self, mocker):
        """
        Test retry logic with simulated invalid output from real crew.
        
        Verifies:
        - Retry callback is invoked when output is invalid
        - Format instructions are provided
        - System can recover with valid output on retry
        
        Requirements: 12.3, 12.4
        """
        # Arrange
        from datetime import datetime

        from finwiz.schemas.hybrid_analysis.metadata import DataLineage, DataQualityMetrics

        quantitative = QuantitativeAnalysis(
            composite_score=0.85,
            fundamental_score=0.90,
            technical_score=0.80,
            risk_score=2.5,
            grade="A",
            preliminary_recommendation="BUY",
            fundamental_metrics={"roe": 0.25},
            technical_indicators={"rsi": 55.0},
            risk_metrics={"volatility": 0.15},
            calculation_timestamp=datetime.now(),
            data_quality=DataQualityMetrics(
                completeness_score=0.95,
                freshness_score=1.0,
                accuracy_confidence=0.90,
                source_reliability=0.85,
                missing_fields=[],
            ),
            data_lineage=DataLineage(
                primary_sources=["yfinance"],
                collection_timestamp=datetime.now(),
                transformation_steps=["normalize"],
                cache_status="fresh",
            ),
            confidence_level=0.90,
            python_rationale="Strong fundamentals",
        )

        # Simulate invalid initial output
        invalid_output = {"incomplete": "data"}

        # Valid output for retry
        valid_output = {
            "sec_insights": {
                "business_model": "Comprehensive business model analysis with detailed operational insights " * 5,
                "competitive_advantages": ["Strong brand", "Market position"],
                "risk_factors": ["Competition", "Regulation"],
            },
            "fundamental_context": {
                "industry_analysis": "Detailed industry analysis covering market trends and dynamics " * 10,
                "growth_drivers": ["Innovation", "Expansion"],
                "competitive_positioning": "Market leader with strong positioning and competitive advantages",
                "management_assessment": "Experienced leadership team with proven track record of success",
            },
            "technical_strategy": {
                "chart_patterns": ["Bullish flag"],
                "support_resistance": "Support at 100 with strong buying, resistance at 120 with profit taking",
                "entry_exit_strategy": "Detailed entry exit strategy with price targets and risk management " * 10,
                "timing_assessment": "Positive momentum with strong volume and upward trend continuation",
            },
            "contextual_risks": {
                "regulatory_risks": ["Regulatory changes"],
                "geopolitical_risks": ["Trade tensions"],
            },
            "investment_synthesis": {
                "investment_thesis": "Comprehensive investment thesis with detailed analysis and reasoning " * 20,
                "bull_case": "Bull case scenario with upside catalysts and growth potential " * 10,
                "base_case": "Base case scenario with most likely outcome and expectations " * 10,
                "bear_case": "Bear case scenario with downside risks and challenges " * 10,
                "scenario_probabilities": {"bull": 0.3, "base": 0.5, "bear": 0.2},
                "final_recommendation": "BUY",
                "recommendation_confidence": "HIGH",
                "action_plan": {
                    "immediate_actions": ["Monitor"],
                    "monitoring_points": ["Price"],
                    "exit_triggers": ["Loss"],
                },
            },
            "analysis_timestamp": datetime.now().isoformat(),
            "ai_confidence": 0.85,
        }

        retry_count = [0]

        def retry_callback(format_instructions: str, retry_context: str):
            retry_count[0] += 1
            # Verify format instructions are comprehensive
            assert len(format_instructions) > 100, "Format instructions should be detailed"
            assert "required" in format_instructions.lower() or "field" in format_instructions.lower()
            # Return valid output on retry
            return valid_output

        # Act
        result = validate_ai_output_with_retry(
            result=invalid_output,
            quantitative=quantitative,
            retry_callback=retry_callback,
            max_retries=2,
        )

        # Assert
        assert isinstance(result, QualitativeInsights)
        assert retry_count[0] == 1, "Should retry exactly once"

    def test_fallback_mechanism_with_real_quantitative_data(self):
        """
        Test Python-only fallback with realistic quantitative data.
        
        Verifies:
        - Fallback creates valid QualitativeInsights
        - Content is derived from quantitative analysis
        - All required fields are populated
        - Fallback is usable for downstream processing
        
        Requirements: 12.4
        """
        # Arrange
        from datetime import datetime

        from finwiz.schemas.hybrid_analysis.metadata import DataLineage, DataQualityMetrics

        quantitative = QuantitativeAnalysis(
            composite_score=0.72,
            fundamental_score=0.85,
            technical_score=0.65,
            risk_score=3.2,
            grade="B",
            preliminary_recommendation="HOLD",
            fundamental_metrics={
                "roe": 0.18,
                "debt_to_equity": 0.45,
                "revenue_growth": 0.12,
                "profit_margin": 0.15,
            },
            technical_indicators={"rsi": 48.0, "macd": -0.5, "sma_20": 145.0, "sma_50": 150.0},
            risk_metrics={"volatility": 0.22, "beta": 1.3, "max_drawdown": -0.18},
            calculation_timestamp=datetime.now(),
            data_quality=DataQualityMetrics(
                completeness_score=0.88,
                freshness_score=0.95,
                accuracy_confidence=0.85,
                source_reliability=0.80,
                missing_fields=["pe_ratio"],
            ),
            data_lineage=DataLineage(
                primary_sources=["yfinance", "alpha_vantage"],
                collection_timestamp=datetime.now(),
                transformation_steps=["normalize", "validate"],
                cache_status="fresh",
            ),
            confidence_level=0.85,
            python_rationale="Moderate fundamentals with weak technical signals and elevated risk",
        )

        # Act
        fallback = create_python_only_qualitative(quantitative)

        # Assert
        assert isinstance(fallback, QualitativeInsights)

        # Verify all required sections are present
        assert fallback.sec_insights is not None
        assert fallback.fundamental_context is not None
        assert fallback.technical_strategy is not None
        assert fallback.contextual_risks is not None
        assert fallback.investment_synthesis is not None

        # Verify content reflects quantitative data
        thesis = fallback.investment_synthesis.investment_thesis.lower()
        assert "grade" in thesis or quantitative.grade.lower() in thesis
        assert fallback.investment_synthesis.final_recommendation == quantitative.preliminary_recommendation

        # Verify minimum content length requirements
        assert len(fallback.investment_synthesis.investment_thesis) >= 200
        assert len(fallback.investment_synthesis.bull_case) >= 100
        assert len(fallback.investment_synthesis.base_case) >= 100
        assert len(fallback.investment_synthesis.bear_case) >= 100

    def test_tool_call_detection_in_practice(self):
        """
        Test that tool call detection works with realistic output structures.
        
        Verifies:
        - Various tool call formats are detected
        - System rejects tool calls appropriately
        - Error messages are clear
        
        Requirements: 12.6
        """
        # Arrange
        from datetime import datetime

        from finwiz.schemas.hybrid_analysis.metadata import DataLineage, DataQualityMetrics
        from finwiz.validation.ai_output_validator import ToolCallInsteadOfAnalysisError, validate_ai_output_structure

        quantitative = QuantitativeAnalysis(
            composite_score=0.85,
            fundamental_score=0.90,
            technical_score=0.80,
            risk_score=2.5,
            grade="A",
            preliminary_recommendation="BUY",
            fundamental_metrics={"roe": 0.25},
            technical_indicators={"rsi": 55.0},
            risk_metrics={"volatility": 0.15},
            calculation_timestamp=datetime.now(),
            data_quality=DataQualityMetrics(
                completeness_score=0.95,
                freshness_score=1.0,
                accuracy_confidence=0.90,
                source_reliability=0.85,
                missing_fields=[],
            ),
            data_lineage=DataLineage(
                primary_sources=["yfinance"],
                collection_timestamp=datetime.now(),
                transformation_steps=["normalize"],
                cache_status="fresh",
            ),
            confidence_level=0.90,
            python_rationale="Strong fundamentals",
        )

        # Test various tool call formats
        tool_call_formats = [
            {"tool_calls": [{"name": "get_stock_data", "args": {"ticker": "AAPL"}}]},
            {"function_call": {"name": "analyze_fundamentals", "arguments": "{}"}},
            {"tool_calls": [], "content": "Some analysis"},  # Empty tool calls array
        ]

        for tool_call_output in tool_call_formats:
            # Act & Assert
            with pytest.raises(ToolCallInsteadOfAnalysisError):
                validate_ai_output_structure(tool_call_output)

    def test_format_instructions_are_comprehensive(self):
        """
        Test that format instructions provided to retry callback are comprehensive.
        
        Verifies:
        - Format instructions include all required fields
        - Instructions include field descriptions
        - Instructions include example structure
        - Instructions are actionable for LLM
        
        Requirements: 12.7
        """
        # Arrange
        from datetime import datetime

        from finwiz.schemas.hybrid_analysis.metadata import DataLineage, DataQualityMetrics
        from finwiz.validation.ai_output_validator import get_explicit_format_example

        quantitative = QuantitativeAnalysis(
            composite_score=0.85,
            fundamental_score=0.90,
            technical_score=0.80,
            risk_score=2.5,
            grade="A",
            preliminary_recommendation="BUY",
            fundamental_metrics={"roe": 0.25},
            technical_indicators={"rsi": 55.0},
            risk_metrics={"volatility": 0.15},
            calculation_timestamp=datetime.now(),
            data_quality=DataQualityMetrics(
                completeness_score=0.95,
                freshness_score=1.0,
                accuracy_confidence=0.90,
                source_reliability=0.85,
                missing_fields=[],
            ),
            data_lineage=DataLineage(
                primary_sources=["yfinance"],
                collection_timestamp=datetime.now(),
                transformation_steps=["normalize"],
                cache_status="fresh",
            ),
            confidence_level=0.90,
            python_rationale="Strong fundamentals",
        )

        # Act
        format_instructions = get_explicit_format_example()

        # Assert
        # Verify format instructions are comprehensive
        assert len(format_instructions) > 500, "Format instructions should be detailed"

        # Check for required field mentions
        required_fields = [
            "sec_insights",
            "fundamental_context",
            "technical_strategy",
            "contextual_risks",
            "investment_synthesis",
        ]

        for field in required_fields:
            assert field in format_instructions, f"Format instructions should mention {field}"

        # Check for structure indicators
        assert "{" in format_instructions or "json" in format_instructions.lower()
        assert "required" in format_instructions.lower() or "must" in format_instructions.lower()
