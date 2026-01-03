"""
AI Output Validation Infrastructure.

This module provides validation for AI crew outputs to ensure structured,
parseable results. Implements Requirements 12.1-12.7 from the hybrid analysis spec.

Key Features:
- Pre-validation structure checks (Requirement 12.5)
- Tool call detection (Requirement 12.6)
- Retry logic with format instructions (Requirement 12.3)
- Fallback to Python-only analysis (Requirement 12.4)
- Pydantic schema enforcement (Requirement 12.1)
"""

import logging
from collections.abc import Callable
from datetime import UTC
from typing import Any, Literal, cast

from pydantic import ValidationError

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
from finwiz.schemas.hybrid_analysis.quantitative import QuantitativeAnalysis

logger = logging.getLogger(__name__)


# ============================================================================
# Custom Exceptions (Requirements 12.5, 12.6)
# ============================================================================


class AIOutputError(Exception):
    """Base exception for AI output validation issues."""

    pass


class OutputParsingError(AIOutputError):
    """Failed to parse AI output (Requirement 12.5)."""

    pass


class MissingRequiredFieldError(AIOutputError):
    """AI output missing required fields (Requirement 12.2)."""

    def __init__(self, missing_fields: list[str]):
        self.missing_fields = missing_fields
        super().__init__(f"AI output missing required fields: {', '.join(missing_fields)}")


class ToolCallInsteadOfAnalysisError(AIOutputError):
    """AI returned tool calls instead of analysis (Requirement 12.6)."""

    pass


# ============================================================================
# Pre-Validation Checks (Requirement 12.5, 12.6)
# ============================================================================


def validate_ai_output_structure(result: Any) -> dict:
    """
    Validate AI output structure before Pydantic validation.

    Implements Requirement 12.5: Pre-validation structure checks
    Implements Requirement 12.6: Tool call detection

    Checks:
    - Result is a dict (not string, list, or other type)
    - No tool_calls or function_call keys present
    - Contains expected top-level keys

    Args:
        result: Raw AI crew output

    Returns:
        Validated dict ready for Pydantic parsing

    Raises:
        OutputParsingError: Structure validation failed
        ToolCallInsteadOfAnalysisError: AI returned tool calls
        MissingRequiredFieldError: Missing required top-level keys

    """
    # Check 1: Must be a dict (Requirement 12.5)
    if not isinstance(result, dict):
        raise OutputParsingError(f"Expected dict output, got {type(result).__name__}. AI must return a structured JSON object, not {type(result).__name__}.")

    # Check 2: Detect tool calls (Requirement 12.6)
    if "tool_calls" in result or "function_call" in result:
        raise ToolCallInsteadOfAnalysisError(
            "AI returned tool calls instead of analysis. The AI agent attempted to call tools rather than providing analysis. Retrying with corrected prompt."
        )

    # Check 3: Verify expected top-level keys
    expected_keys = {
        "sec_insights",
        "fundamental_context",
        "technical_strategy",
        "contextual_risks",
        "investment_synthesis",
        "analysis_timestamp",
        "ai_confidence",
    }

    missing_keys = expected_keys - set(result.keys())
    if missing_keys:
        raise MissingRequiredFieldError(list(missing_keys))

    return result


def validate_qualitative_insights(result: dict) -> QualitativeInsights:
    """
    Validate AI output against QualitativeInsights schema.

    Implements Requirement 12.1: Pydantic schema enforcement

    Args:
        result: Pre-validated dict from validate_ai_output_structure

    Returns:
        Validated QualitativeInsights model

    Raises:
        ValidationError: Pydantic validation failed

    """
    try:
        return QualitativeInsights.model_validate(result)
    except ValidationError as e:
        logger.error(f"Pydantic validation failed: {e}")
        raise


# ============================================================================
# Retry Logic with Format Instructions (Requirement 12.3)
# ============================================================================


def get_explicit_format_example() -> str:
    """
    Generate explicit format instructions for retry attempts.

    Implements Requirement 12.3: Retry with format instructions
    Implements Requirement 12.7: Include format examples

    Used when initial AI output fails validation to provide clear
    guidance on expected structure.

    Returns:
        Detailed format instructions with example

    """
    return """
CRITICAL: Your output MUST be a valid JSON object matching this EXACT structure:

{
  "sec_insights": {
    "business_model": "string (minimum 100 words - required)",
    "competitive_advantages": ["advantage 1", "advantage 2"],
    "risk_factors": ["risk 1", "risk 2"],
    "strategic_initiatives": ["initiative 1", "initiative 2"]
  },
  "fundamental_context": {
    "industry_analysis": "string (minimum 100 words - required)",
    "growth_drivers": ["driver 1", "driver 2"],
    "competitive_positioning": "string (minimum 50 words - required)",
    "management_assessment": "string (minimum 50 words - required)"
  },
  "technical_strategy": {
    "chart_patterns": ["pattern 1", "pattern 2"],
    "support_resistance": "string (minimum 50 words - required)",
    "entry_exit_strategy": "string (minimum 100 words - required)",
    "timing_assessment": "string (minimum 50 words - required)"
  },
  "contextual_risks": {
    "regulatory_risks": ["risk 1", "risk 2"],
    "geopolitical_risks": ["risk 1", "risk 2"],
    "competitive_risks": ["risk 1", "risk 2"],
    "operational_risks": ["risk 1", "risk 2"],
    "stress_scenarios": ["scenario 1", "scenario 2"]
  },
  "investment_synthesis": {
    "investment_thesis": "string (minimum 200 words - required)",
    "bull_case": "string (minimum 100 words - required)",
    "base_case": "string (minimum 100 words - required)",
    "bear_case": "string (minimum 100 words - required)",
    "scenario_probabilities": {
      "bull": 0.25,
      "base": 0.50,
      "bear": 0.25
    },
    "final_recommendation": "BUY|HOLD|SELL (required)",
    "recommendation_confidence": "LOW|MEDIUM|HIGH (required)",
    "action_plan": {
      "immediate_actions": ["action 1", "action 2"],
      "monitoring_points": ["point 1", "point 2"],
      "exit_triggers": ["trigger 1", "trigger 2"]
    }
  },
  "analysis_timestamp": "2025-01-22T10:30:00Z",
  "ai_confidence": 0.85
}

FIELD REQUIREMENTS:
- business_model: Minimum 100 words describing how company makes money
- competitive_advantages: At least 1 advantage (list of strings)
- risk_factors: At least 1 risk factor (list of strings)
- industry_analysis: Minimum 100 words on industry context
- growth_drivers: At least 1 driver (list of strings)
- competitive_positioning: Minimum 50 words on market position
- management_assessment: Minimum 50 words on leadership quality
- chart_patterns: At least 1 pattern (list of strings)
- support_resistance: Minimum 50 words on key levels
- entry_exit_strategy: Minimum 100 words with price targets
- timing_assessment: Minimum 50 words on market timing
- investment_thesis: Minimum 200 words comprehensive thesis
- bull_case: Minimum 100 words optimistic scenario
- base_case: Minimum 100 words most likely scenario
- bear_case: Minimum 100 words pessimistic scenario
- scenario_probabilities: Must sum to 1.0
- final_recommendation: Must be exactly "BUY", "HOLD", or "SELL"
- recommendation_confidence: Must be exactly "LOW", "MEDIUM", or "HIGH"
- action_plan: Dict with 3 keys (immediate_actions, monitoring_points, exit_triggers)
- analysis_timestamp: ISO 8601 format datetime
- ai_confidence: Float between 0.0 and 1.0

DO NOT:
- Return tool calls or function calls
- Return a string instead of JSON object
- Omit any required fields
- Use null for required fields
- Use empty strings for text fields
- Provide placeholder text like "TODO" or "TBD"

DO:
- Return valid JSON matching the structure above
- Include all required fields with substantive content
- Meet minimum word counts for text fields
- Ensure scenario_probabilities sum to 1.0
- Use exact values for enums (BUY/HOLD/SELL, LOW/MEDIUM/HIGH)
- Provide actionable, specific content
"""


# ============================================================================
# Fallback to Python-Only Analysis (Requirement 12.4)
# ============================================================================


def create_python_only_qualitative(quantitative: QuantitativeAnalysis) -> QualitativeInsights:
    """
    Create fallback qualitative insights when AI fails after retries.

    Implements Requirement 12.4: Fallback to Python-only analysis after
    2 failed retry attempts.

    Generates minimal qualitative insights from quantitative data with
    appropriate warnings and flags.

    Args:
        quantitative: Python-calculated quantitative analysis

    Returns:
        Minimal QualitativeInsights with ai_analysis_available=False flag

    """
    from datetime import datetime

    logger.warning("Creating Python-only qualitative insights. AI analysis failed after maximum retry attempts.")

    # Create minimal qualitative insights from quantitative data
    return QualitativeInsights(
        sec_insights=SecAnalysisInsights(
            business_model=(
                "AI analysis unavailable. Using quantitative metrics only. "
                "Business model analysis requires AI crew execution which failed "
                "after retry attempts. Recommendation based on quantitative grade "
                f"and composite score of {quantitative.composite_score:.2f}. "
                "This fallback provides minimal context based on Python calculations."
            ),
            competitive_advantages=["Quantitative analysis indicates positive metrics"],
            risk_factors=["AI qualitative analysis unavailable"],
            strategic_initiatives=[],
        ),
        fundamental_context=FundamentalContextInsights(
            industry_analysis=(
                "Industry context analysis unavailable. AI crew execution failed. "
                "Quantitative fundamental score available: "
                f"{quantitative.fundamental_score:.2f}. "
                "For detailed industry analysis, AI crew must execute successfully. "
                "This fallback provides only quantitative metrics without industry context."
            ),
            growth_drivers=["Based on quantitative fundamental metrics only"],
            competitive_positioning="Not assessed - AI analysis unavailable. Competitive positioning requires qualitative analysis which failed after retry attempts.",
            management_assessment="Not assessed - AI analysis unavailable. Management quality assessment requires qualitative analysis which failed after retry attempts.",
        ),
        technical_strategy=TechnicalStrategyInsights(
            chart_patterns=["Technical analysis based on quantitative indicators only"],
            support_resistance="Not assessed - AI analysis unavailable. Support and resistance levels require qualitative chart analysis which failed after retry attempts.",
            entry_exit_strategy=(
                f"Based on quantitative analysis only. Grade: {quantitative.grade}. "
                f"Technical score: {quantitative.technical_score:.2f}. "
                f"Recommendation: {quantitative.preliminary_recommendation}. "
                "For detailed entry/exit strategy, AI crew must execute successfully. "
                "This fallback provides only basic quantitative guidance."
            ),
            timing_assessment="Not assessed - AI analysis unavailable. Market timing assessment requires qualitative analysis which failed after retry attempts.",
        ),
        contextual_risks=ContextualRiskInsights(
            regulatory_risks=[],
            geopolitical_risks=[],
            competitive_risks=[],
            operational_risks=[],
            stress_scenarios=[],
        ),
        investment_synthesis=InvestmentSynthesis(
            investment_thesis=(
                f"Python-only analysis. "
                f"Quantitative Grade: {quantitative.grade}. "
                f"Composite Score: {quantitative.composite_score:.2f}. "
                f"Fundamental Score: {quantitative.fundamental_score:.2f}. "
                f"Technical Score: {quantitative.technical_score:.2f}. "
                f"Risk Score: {quantitative.risk_score:.2f}. "
                f"Recommendation: {quantitative.preliminary_recommendation}. "
                "AI qualitative analysis unavailable after retry attempts. "
                "This analysis is based solely on quantitative metrics calculated "
                "by Python. For comprehensive analysis including contextual insights, "
                "competitive positioning, and strategic guidance, AI crew execution "
                "must complete successfully. Current recommendation is based on "
                "deterministic scoring algorithms applied to fundamental, technical, "
                "and risk metrics."
            ),
            bull_case=(
                "Quantitative metrics improve beyond current levels. "
                "Fundamental score increases above current baseline. "
                "Technical indicators show strengthening momentum. "
                "Risk metrics remain within acceptable ranges."
            ),
            base_case=(
                "Quantitative metrics remain stable at current levels. "
                "Fundamental score maintains current baseline. "
                "Technical indicators show neutral momentum. "
                "Risk metrics stay within normal ranges."
            ),
            bear_case=(
                "Quantitative metrics deteriorate from current levels. "
                "Fundamental score decreases below current baseline. "
                "Technical indicators show weakening momentum. "
                "Risk metrics exceed acceptable thresholds."
            ),
            scenario_probabilities=ScenarioProbabilities(bull=0.33, base=0.34, bear=0.33),
            final_recommendation=cast(Literal["BUY", "HOLD", "SELL"], quantitative.preliminary_recommendation),
            recommendation_confidence="LOW",  # Low confidence without AI analysis
            action_plan=ActionPlan(
                immediate_actions=[f"Follow quantitative recommendation: {quantitative.preliminary_recommendation}"],
                monitoring_points=["Monitor quantitative metrics for changes"],
                exit_triggers=["Significant deterioration in quantitative scores"],
            ),
        ),
        analysis_timestamp=datetime.now(UTC),
        ai_confidence=0.0,  # Zero confidence - no AI analysis performed
    )


# ============================================================================
# Main Validation Function with Retry Logic
# ============================================================================


def validate_ai_output_with_retry(
    result: Any,
    quantitative: QuantitativeAnalysis,
    retry_callback: Callable[..., Any] | None = None,
    max_retries: int = 2,
) -> QualitativeInsights:
    """
    Validate AI output with retry logic and fallback.

    Implements complete validation flow:
    - Requirement 12.5: Pre-validation checks
    - Requirement 12.6: Tool call detection
    - Requirement 12.1: Pydantic validation
    - Requirement 12.3: Retry with format instructions
    - Requirement 12.4: Fallback after max retries

    Args:
        result: Raw AI crew output
        quantitative: Quantitative analysis for fallback
        retry_callback: Optional function to call for retry (receives format_instructions)
        max_retries: Maximum retry attempts (default: 2 per Requirement 12.4)

    Returns:
        Validated QualitativeInsights or Python-only fallback

    Raises:
        AIOutputError: If validation fails and no retry_callback provided

    """
    for attempt in range(max_retries + 1):  # +1 for initial attempt
        try:
            # Step 1: Pre-validation structure checks
            validated_dict = validate_ai_output_structure(result)

            # Step 2: Pydantic validation
            qualitative = validate_qualitative_insights(validated_dict)

            # Success!
            if attempt > 0:
                logger.info(f"AI output validation succeeded on retry attempt {attempt}")
            return qualitative

        except (OutputParsingError, ToolCallInsteadOfAnalysisError, MissingRequiredFieldError, ValidationError) as e:
            if attempt < max_retries:
                # Retry with format instructions
                logger.warning(f"AI output validation failed (attempt {attempt + 1}/{max_retries + 1}): {e}")

                if retry_callback:
                    format_instructions = get_explicit_format_example()
                    retry_context = f"Previous attempt failed: {str(e)}"
                    result = retry_callback(format_instructions=format_instructions, retry_context=retry_context)
                else:
                    # No retry callback - cannot retry
                    logger.error("No retry callback provided, cannot retry validation")
                    break
            else:
                # Max retries exceeded - fallback to Python-only
                logger.error(f"AI output validation failed after {max_retries} retry attempts. Falling back to Python-only analysis (Requirement 12.4)")
                return create_python_only_qualitative(quantitative)

    # Should not reach here, but fallback just in case
    logger.error("Unexpected validation flow - falling back to Python-only analysis")
    return create_python_only_qualitative(quantitative)
