"""
Unit tests for AI output validation infrastructure.

Tests Requirements 12.1-12.7 from the hybrid analysis spec.
"""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError
from pytest import approx

from finwiz.schemas.hybrid_analysis.qualitative import QualitativeInsights
from finwiz.schemas.hybrid_analysis.quantitative import QuantitativeAnalysis
from finwiz.validation.ai_output import (
    MissingRequiredFieldError,
    OutputParsingError,
    ToolCallInsteadOfAnalysisError,
    create_python_only_qualitative,
    get_explicit_format_example,
    validate_ai_output_structure,
    validate_ai_output_with_retry,
    validate_qualitative_insights,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def valid_qualitative_dict():
    """Valid QualitativeInsights dict for testing."""
    return {
        "sec_insights": {
            "business_model": "A" * 100,  # 100 chars minimum
            "competitive_advantages": ["Advantage 1", "Advantage 2"],
            "risk_factors": ["Risk 1", "Risk 2"],
            "strategic_initiatives": ["Initiative 1"],
        },
        "fundamental_context": {
            "industry_analysis": "B" * 100,  # 100 chars minimum
            "growth_drivers": ["Driver 1", "Driver 2"],
            "competitive_positioning": "C" * 50,  # 50 chars minimum
            "management_assessment": "D" * 50,  # 50 chars minimum
        },
        "technical_strategy": {
            "chart_patterns": ["Pattern 1", "Pattern 2"],
            "support_resistance": "E" * 50,  # 50 chars minimum
            "entry_exit_strategy": "F" * 100,  # 100 chars minimum
            "timing_assessment": "G" * 50,  # 50 chars minimum
        },
        "contextual_risks": {
            "regulatory_risks": ["Risk 1"],
            "geopolitical_risks": ["Risk 2"],
            "competitive_risks": ["Risk 3"],
            "operational_risks": ["Risk 4"],
            "stress_scenarios": ["Scenario 1"],
        },
        "investment_synthesis": {
            "investment_thesis": "H" * 200,  # 200 chars minimum
            "bull_case": "I" * 100,  # 100 chars minimum
            "base_case": "J" * 100,  # 100 chars minimum
            "bear_case": "K" * 100,  # 100 chars minimum
            "scenario_probabilities": {"bull": 0.25, "base": 0.50, "bear": 0.25},
            "final_recommendation": "BUY",
            "recommendation_confidence": "HIGH",
            "action_plan": {
                "immediate_actions": ["Action 1", "Action 2"],
                "monitoring_points": ["Point 1", "Point 2"],
                "exit_triggers": ["Trigger 1", "Trigger 2"],
            },
        },
        "analysis_timestamp": datetime.now(UTC).isoformat(),
        "ai_confidence": 0.85,
    }


@pytest.fixture
def sample_quantitative():
    """Sample QuantitativeAnalysis for fallback testing."""
    from finwiz.schemas.hybrid_analysis.metadata import DataQualityMetrics

    return QuantitativeAnalysis(
        composite_score=0.85,
        fundamental_score=0.90,
        technical_score=0.80,
        risk_score=2.5,
        grade="A+",
        preliminary_recommendation="BUY",
        fundamental_metrics={"roe": 0.25, "debt_to_equity": 0.3, "revenue_growth": 0.15},
        technical_indicators={"rsi": 55.0, "macd": 1.2, "trend_strength": 0.75},
        risk_metrics={"volatility": 0.15, "max_drawdown": 0.10, "beta": 1.1},
        calculation_timestamp=datetime.now(UTC),
        data_quality=DataQualityMetrics(
            completeness_score=0.95,
            freshness_score=1.0,
            accuracy_confidence=0.90,
            source_reliability=0.85,
            missing_fields=[],
        ),
        confidence_level=1.0,
        python_rationale="Strong fundamentals with moderate technical signals",
    )


# ============================================================================
# Test Pre-Validation Checks (Requirement 12.5)
# ============================================================================


def test_should_pass_validation_with_valid_dict(valid_qualitative_dict):
    """Test pre-validation passes with valid output (Requirement 12.5)."""
    result = validate_ai_output_structure(valid_qualitative_dict)
    assert result == valid_qualitative_dict
    assert isinstance(result, dict)


def test_should_reject_non_dict_types():
    """Test rejection of non-dict types (Requirement 12.5)."""
    # Test string
    with pytest.raises(OutputParsingError) as exc_info:
        validate_ai_output_structure("This is a string")
    assert "Expected dict output, got str" in str(exc_info.value)

    # Test list
    with pytest.raises(OutputParsingError) as exc_info:
        validate_ai_output_structure(["item1", "item2"])
    assert "Expected dict output, got list" in str(exc_info.value)

    # Test None
    with pytest.raises(OutputParsingError) as exc_info:
        validate_ai_output_structure(None)
    assert "Expected dict output, got NoneType" in str(exc_info.value)


def test_should_detect_tool_calls(valid_qualitative_dict):
    """Test detection of tool_calls key (Requirement 12.6)."""
    # Test tool_calls key
    invalid_dict = valid_qualitative_dict.copy()
    invalid_dict["tool_calls"] = [{"name": "some_tool", "args": {}}]

    with pytest.raises(ToolCallInsteadOfAnalysisError) as exc_info:
        validate_ai_output_structure(invalid_dict)
    assert "tool calls instead of analysis" in str(exc_info.value)


def test_should_detect_function_call(valid_qualitative_dict):
    """Test detection of function_call key (Requirement 12.6)."""
    invalid_dict = valid_qualitative_dict.copy()
    invalid_dict["function_call"] = {"name": "some_function", "arguments": "{}"}

    with pytest.raises(ToolCallInsteadOfAnalysisError) as exc_info:
        validate_ai_output_structure(invalid_dict)
    assert "tool calls instead of analysis" in str(exc_info.value)


def test_should_detect_missing_required_fields():
    """Test detection of missing required fields (Requirement 12.2)."""
    incomplete_dict = {
        "sec_insights": {},
        "fundamental_context": {},
        # Missing: technical_strategy, contextual_risks, investment_synthesis, etc.
    }

    with pytest.raises(MissingRequiredFieldError) as exc_info:
        validate_ai_output_structure(incomplete_dict)

    error = exc_info.value
    assert "technical_strategy" in error.missing_fields
    assert "contextual_risks" in error.missing_fields
    assert "investment_synthesis" in error.missing_fields
    assert "analysis_timestamp" in error.missing_fields
    assert "ai_confidence" in error.missing_fields


# ============================================================================
# Test Pydantic Validation (Requirement 12.1)
# ============================================================================


def test_should_validate_with_pydantic(valid_qualitative_dict):
    """Test Pydantic validation enforcement (Requirement 12.1)."""
    result = validate_qualitative_insights(valid_qualitative_dict)
    assert isinstance(result, QualitativeInsights)
    assert result.sec_insights.business_model == valid_qualitative_dict["sec_insights"]["business_model"]
    assert result.investment_synthesis.final_recommendation == "BUY"


def test_should_reject_invalid_pydantic_data():
    """Test Pydantic validation rejects invalid data (Requirement 12.1)."""
    invalid_dict = {
        "sec_insights": {
            "business_model": "Too short",  # Less than 100 chars
            "competitive_advantages": [],  # Empty list (needs at least 1)
            "risk_factors": [],  # Empty list (needs at least 1)
            "strategic_initiatives": [],
        },
        "fundamental_context": {
            "industry_analysis": "Too short",  # Less than 100 chars
            "growth_drivers": [],  # Empty list
            "competitive_positioning": "Short",  # Less than 50 chars
            "management_assessment": "Short",  # Less than 50 chars
        },
        "technical_strategy": {
            "chart_patterns": [],  # Empty list
            "support_resistance": "Short",  # Less than 50 chars
            "entry_exit_strategy": "Short",  # Less than 100 chars
            "timing_assessment": "Short",  # Less than 50 chars
        },
        "contextual_risks": {},
        "investment_synthesis": {
            "investment_thesis": "Short",  # Less than 200 chars
            "bull_case": "Short",  # Less than 100 chars
            "base_case": "Short",  # Less than 100 chars
            "bear_case": "Short",  # Less than 100 chars
            "scenario_probabilities": {"bull": 0.5, "base": 0.5, "bear": 0.5},  # Doesn't sum to 1.0
            "final_recommendation": "INVALID",  # Not BUY/HOLD/SELL
            "recommendation_confidence": "INVALID",  # Not LOW/MEDIUM/HIGH
            "action_plan": {},
        },
        "analysis_timestamp": datetime.now(UTC).isoformat(),
        "ai_confidence": 1.5,  # > 1.0
    }

    with pytest.raises(ValidationError):
        validate_qualitative_insights(invalid_dict)


# ============================================================================
# Test Format Instructions (Requirement 12.3, 12.7)
# ============================================================================


def test_should_generate_format_instructions():
    """Test generation of explicit format instructions (Requirement 12.3, 12.7)."""
    instructions = get_explicit_format_example()

    # Check key elements are present
    assert "CRITICAL" in instructions
    assert "JSON object" in instructions
    assert "sec_insights" in instructions
    assert "fundamental_context" in instructions
    assert "technical_strategy" in instructions
    assert "contextual_risks" in instructions
    assert "investment_synthesis" in instructions
    assert "minimum 100 words" in instructions
    assert "minimum 200 words" in instructions
    assert "BUY|HOLD|SELL" in instructions
    assert "LOW|MEDIUM|HIGH" in instructions
    assert "DO NOT" in instructions
    assert "DO:" in instructions


# ============================================================================
# Test Fallback to Python-Only Analysis (Requirement 12.4)
# ============================================================================


def test_should_create_python_only_fallback(sample_quantitative):
    """Test fallback to Python-only analysis (Requirement 12.4)."""
    result = create_python_only_qualitative(sample_quantitative)

    # Verify it's a valid QualitativeInsights
    assert isinstance(result, QualitativeInsights)

    # Verify it uses quantitative data
    assert sample_quantitative.grade in result.investment_synthesis.investment_thesis
    assert str(sample_quantitative.composite_score) in result.investment_synthesis.investment_thesis

    # Verify AI confidence is zero
    assert result.ai_confidence == approx(0.0)

    # Verify recommendation matches quantitative
    assert result.investment_synthesis.final_recommendation == sample_quantitative.preliminary_recommendation

    # Verify confidence is LOW (no AI analysis)
    assert result.investment_synthesis.recommendation_confidence == "LOW"

    # Verify warning indicators
    assert "AI analysis unavailable" in result.sec_insights.business_model
    assert "AI crew execution failed" in result.fundamental_context.industry_analysis


def test_should_log_warning_for_python_only_fallback(sample_quantitative, caplog):
    """Test that fallback logs warning (Requirement 12.4)."""
    import logging

    caplog.set_level(logging.WARNING)

    create_python_only_qualitative(sample_quantitative)

    # Verify warning was logged
    assert any("Python-only qualitative insights" in record.message for record in caplog.records)
    assert any("AI analysis failed" in record.message for record in caplog.records)


# ============================================================================
# Test Retry Logic (Requirement 12.3)
# ============================================================================


def test_should_succeed_on_first_attempt(valid_qualitative_dict, sample_quantitative):
    """Test validation succeeds on first attempt without retry."""
    result = validate_ai_output_with_retry(valid_qualitative_dict, sample_quantitative)

    assert isinstance(result, QualitativeInsights)
    assert result.investment_synthesis.final_recommendation == "BUY"


def test_should_retry_with_format_instructions(sample_quantitative):
    """Test retry logic with format instructions (Requirement 12.3)."""
    retry_count = 0
    format_instructions_received = None
    retry_context_received = None

    def mock_retry_callback(format_instructions, retry_context):
        nonlocal retry_count, format_instructions_received, retry_context_received
        retry_count += 1
        format_instructions_received = format_instructions
        retry_context_received = retry_context

        # Return valid data on second retry
        if retry_count >= 2:
            return {
                "sec_insights": {
                    "business_model": "A" * 100,
                    "competitive_advantages": ["Advantage 1"],
                    "risk_factors": ["Risk 1"],
                    "strategic_initiatives": [],
                },
                "fundamental_context": {
                    "industry_analysis": "B" * 100,
                    "growth_drivers": ["Driver 1"],
                    "competitive_positioning": "C" * 50,
                    "management_assessment": "D" * 50,
                },
                "technical_strategy": {
                    "chart_patterns": ["Pattern 1"],
                    "support_resistance": "E" * 50,
                    "entry_exit_strategy": "F" * 100,
                    "timing_assessment": "G" * 50,
                },
                "contextual_risks": {},
                "investment_synthesis": {
                    "investment_thesis": "H" * 200,
                    "bull_case": "I" * 100,
                    "base_case": "J" * 100,
                    "bear_case": "K" * 100,
                    "scenario_probabilities": {"bull": 0.33, "base": 0.34, "bear": 0.33},
                    "final_recommendation": "BUY",
                    "recommendation_confidence": "HIGH",
                    "action_plan": {
                        "immediate_actions": ["Action 1"],
                        "monitoring_points": ["Point 1"],
                        "exit_triggers": ["Trigger 1"],
                    },
                },
                "analysis_timestamp": datetime.now(UTC).isoformat(),
                "ai_confidence": 0.85,
            }
        else:
            # Return invalid data to trigger retry
            return "Invalid string output"

    # Start with invalid output
    result = validate_ai_output_with_retry("Invalid string output", sample_quantitative, retry_callback=mock_retry_callback, max_retries=2)

    # Verify retry was called
    assert retry_count == 2

    # Verify format instructions were provided
    assert format_instructions_received is not None
    assert "CRITICAL" in format_instructions_received

    # Verify retry context was provided
    assert retry_context_received is not None
    assert "Previous attempt failed" in retry_context_received

    # Verify final result is valid
    assert isinstance(result, QualitativeInsights)


def test_should_fallback_after_max_retries(sample_quantitative):
    """Test fallback after max retries (Requirement 12.4)."""

    def mock_retry_callback(format_instructions, retry_context):
        # Always return invalid data
        return "Still invalid"

    # Start with invalid output
    result = validate_ai_output_with_retry("Invalid string output", sample_quantitative, retry_callback=mock_retry_callback, max_retries=2)

    # Verify fallback was used
    assert isinstance(result, QualitativeInsights)
    assert result.ai_confidence == approx(0.0)  # Python-only fallback
    assert "AI analysis unavailable" in result.sec_insights.business_model


def test_should_limit_retries_to_two(sample_quantitative):
    """Test retry limit of 2 attempts (Requirement 12.4)."""
    retry_count = 0

    def mock_retry_callback(format_instructions, retry_context):
        nonlocal retry_count
        retry_count += 1
        return "Still invalid"

    validate_ai_output_with_retry("Invalid string output", sample_quantitative, retry_callback=mock_retry_callback, max_retries=2)

    # Verify exactly 2 retries (not more)
    assert retry_count == 2


# ============================================================================
# Test Complete Validation Flow
# ============================================================================


def test_should_handle_complete_validation_flow(valid_qualitative_dict, sample_quantitative):
    """Test complete validation flow from raw output to validated model."""
    # Simulate complete flow
    validated_dict = validate_ai_output_structure(valid_qualitative_dict)
    validated_model = validate_qualitative_insights(validated_dict)

    assert isinstance(validated_model, QualitativeInsights)
    assert validated_model.sec_insights.business_model == valid_qualitative_dict["sec_insights"]["business_model"]
    assert validated_model.investment_synthesis.final_recommendation == "BUY"


def test_should_handle_tool_call_error_in_retry_flow(sample_quantitative):
    """Test handling of tool call error in retry flow."""
    retry_count = 0

    def mock_retry_callback(format_instructions, retry_context):
        nonlocal retry_count
        retry_count += 1

        if retry_count == 1:
            # First retry: return dict with tool_calls
            return {"tool_calls": [{"name": "some_tool"}], "sec_insights": {}}
        else:
            # Second retry: return valid data
            return {
                "sec_insights": {
                    "business_model": "A" * 100,
                    "competitive_advantages": ["Advantage 1"],
                    "risk_factors": ["Risk 1"],
                    "strategic_initiatives": [],
                },
                "fundamental_context": {
                    "industry_analysis": "B" * 100,
                    "growth_drivers": ["Driver 1"],
                    "competitive_positioning": "C" * 50,
                    "management_assessment": "D" * 50,
                },
                "technical_strategy": {
                    "chart_patterns": ["Pattern 1"],
                    "support_resistance": "E" * 50,
                    "entry_exit_strategy": "F" * 100,
                    "timing_assessment": "G" * 50,
                },
                "contextual_risks": {},
                "investment_synthesis": {
                    "investment_thesis": "H" * 200,
                    "bull_case": "I" * 100,
                    "base_case": "J" * 100,
                    "bear_case": "K" * 100,
                    "scenario_probabilities": {"bull": 0.33, "base": 0.34, "bear": 0.33},
                    "final_recommendation": "BUY",
                    "recommendation_confidence": "HIGH",
                    "action_plan": {
                        "immediate_actions": ["Action 1"],
                        "monitoring_points": ["Point 1"],
                        "exit_triggers": ["Trigger 1"],
                    },
                },
                "analysis_timestamp": datetime.now(UTC).isoformat(),
                "ai_confidence": 0.85,
            }

    result = validate_ai_output_with_retry({"tool_calls": [{"name": "initial_tool"}]}, sample_quantitative, retry_callback=mock_retry_callback, max_retries=2)

    # Verify retry was triggered by tool call error
    assert retry_count == 2
    assert isinstance(result, QualitativeInsights)
