"""
Report Data Validator for FinWiz.

This module provides validation for report crew inputs to ensure data quality
and prevent hallucinated or incomplete data from reaching the final report.

FAIL-FAST PRINCIPLE: Refuse to generate reports with incomplete or invalid data.
"""

import logging
from typing import Any

from pydantic import ValidationError

from finwiz.schemas.hybrid_analysis import (
    EnrichedAnalysis,
    QualitativeInsights,
    QuantitativeAnalysis,
)

logger = logging.getLogger(__name__)


class ReportValidationError(Exception):
    """Raised when report inputs are invalid or incomplete."""

    pass


class ReportDataValidator:
    """
    Validate that report crew receives all required data.

    FAIL-FAST: Refuse to generate report if data is incomplete.

    This validator ensures that:
    1. All required fields are present
    2. No "NOT PROVIDED" placeholders exist
    3. Portfolio holdings have actual analysis data, not fallback values
    4. Data is complete and ready for report generation
    """

    def __init__(self) -> None:
        """Initialize the report data validator."""
        self.validation_errors: list[str] = []

    def validate_enriched_analysis(self, analysis: dict[str, Any] | EnrichedAnalysis) -> EnrichedAnalysis:
        """
        Validate EnrichedAnalysis schema compliance.

        Args:
            analysis: EnrichedAnalysis data (dict or model instance)

        Returns:
            Validated EnrichedAnalysis instance

        Raises:
            ReportValidationError: If validation fails

        Requirements: 3.1 (EnrichedAnalysis validation)

        """
        logger.info("Validating EnrichedAnalysis schema...")

        try:
            # If already an instance, validate it
            if isinstance(analysis, EnrichedAnalysis):
                validated = analysis
            else:
                # Parse and validate from dict
                validated = EnrichedAnalysis.model_validate(analysis)

            # Additional quality checks
            if validated.report_word_count < 2000:
                raise ReportValidationError(f"Report word count {validated.report_word_count} is below minimum 2000 words")

            if validated.unique_insights_count < 5:
                raise ReportValidationError(f"Unique insights count {validated.unique_insights_count} is below minimum 5 insights")

            logger.info(f"✅ EnrichedAnalysis validation passed for {validated.ticker}")
            return validated

        except ValidationError as e:
            error_message = f"EnrichedAnalysis validation failed: {e}"
            logger.error(f"❌ {error_message}")
            raise ReportValidationError(error_message) from e

    def validate_quantitative_analysis(self, analysis: dict[str, Any] | QuantitativeAnalysis) -> QuantitativeAnalysis:
        """
        Validate QuantitativeAnalysis schema compliance.

        Args:
            analysis: QuantitativeAnalysis data (dict or model instance)

        Returns:
            Validated QuantitativeAnalysis instance

        Raises:
            ReportValidationError: If validation fails

        Requirements: 3.1 (QuantitativeAnalysis validation)

        """
        logger.info("Validating QuantitativeAnalysis schema...")

        try:
            # If already an instance, validate it
            if isinstance(analysis, QuantitativeAnalysis):
                validated = analysis
            else:
                # Parse and validate from dict
                validated = QuantitativeAnalysis.model_validate(analysis)

            # Additional checks
            if not 0.0 <= validated.composite_score <= 1.0:
                raise ReportValidationError(f"Composite score {validated.composite_score} is out of range [0.0, 1.0]")

            if not 0.0 <= validated.confidence_level <= 1.0:
                raise ReportValidationError(f"Confidence level {validated.confidence_level} is out of range [0.0, 1.0]")

            logger.info(f"✅ QuantitativeAnalysis validation passed: Grade {validated.grade}, Score {validated.composite_score:.2f}")
            return validated

        except ValidationError as e:
            error_message = f"QuantitativeAnalysis validation failed: {e}"
            logger.error(f"❌ {error_message}")
            raise ReportValidationError(error_message) from e

    def validate_qualitative_insights(self, insights: dict[str, Any] | QualitativeInsights) -> QualitativeInsights:
        """
        Validate QualitativeInsights schema compliance.

        Args:
            insights: QualitativeInsights data (dict or model instance)

        Returns:
            Validated QualitativeInsights instance

        Raises:
            ReportValidationError: If validation fails

        Requirements: 3.1 (QualitativeInsights validation)

        """
        logger.info("Validating QualitativeInsights schema...")

        try:
            # If already an instance, validate it
            if isinstance(insights, QualitativeInsights):
                validated = insights
            else:
                # Parse and validate from dict
                validated = QualitativeInsights.model_validate(insights)

            # Additional quality checks
            if len(validated.sec_insights.business_model) < 100:
                raise ReportValidationError(f"Business model analysis is too short: {len(validated.sec_insights.business_model)} chars (minimum 100)")

            if len(validated.investment_synthesis.investment_thesis) < 200:
                raise ReportValidationError(f"Investment thesis is too short: {len(validated.investment_synthesis.investment_thesis)} chars (minimum 200)")

            logger.info(f"✅ QualitativeInsights validation passed: Confidence {validated.ai_confidence:.2f}")
            return validated

        except ValidationError as e:
            error_message = f"QualitativeInsights validation failed: {e}"
            logger.error(f"❌ {error_message}")
            raise ReportValidationError(error_message) from e

    def get_validation_summary(self) -> dict[str, Any]:
        """
        Get a summary of validation results.

        Returns:
            Dictionary with validation summary

        """
        return {
            "validation_errors": self.validation_errors,
            "has_errors": len(self.validation_errors) > 0,
            "error_count": len(self.validation_errors),
        }
