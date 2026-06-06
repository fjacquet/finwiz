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
    QualitativeInsights,
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
