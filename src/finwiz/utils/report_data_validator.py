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

    def validate_report_inputs(self, inputs: dict[str, Any]) -> None:
        """
        Validate report crew inputs are complete and valid.

        Args:
            inputs: Report crew input data

        Raises:
            ReportValidationError: If inputs are incomplete or invalid

        """
        logger.info("=" * 80)
        logger.info("REPORT INPUT VALIDATION")
        logger.info("=" * 80)

        self.validation_errors = []

        # Define required fields (always required)
        required_fields = [
            "portfolio_review",
            "aplus_opportunities",
            "investment_discovery_structured",
            "data_availability_summary",
            "data_availability_summary_formatted",
        ]

        # Define optional fields (only required if discovery was successful)
        # These fields depend on discovery crews running successfully
        discovery_dependent_fields = [
            "validated_tickers_list",
            "discovery_status",
            "backtesting_status",
        ]

        # Check if discovery was available/successful
        discovery_available = inputs.get("investment_discovery_available", False)
        discovery_success = inputs.get("investment_discovery_success", False)

        # If discovery was successful, add discovery-dependent fields to required list
        if discovery_available and discovery_success:
            required_fields.extend(discovery_dependent_fields)
            logger.info("Discovery data available - validating discovery-dependent fields")
        else:
            logger.warning(
                f"Discovery data not available (available={discovery_available}, success={discovery_success}) - "
                f"skipping validation of discovery-dependent fields: {discovery_dependent_fields}"
            )

        missing_fields = []
        invalid_fields = []

        # Check each required field
        for field in required_fields:
            if field not in inputs:
                missing_fields.append(field)
                logger.error(f"❌ Missing required field: {field}")
                continue

            value = inputs[field]

            # Check for "NOT PROVIDED" placeholder
            if isinstance(value, str) and "NOT PROVIDED" in value:
                invalid_fields.append(field)
                logger.error(f"❌ Field {field} contains placeholder: {value}")
                continue

            # Check for None when data should exist
            if value is None and field in ["portfolio_review"]:
                invalid_fields.append(field)
                logger.error(f"❌ Field {field} is None but should have data")
                continue

            logger.info(f"✅ Field {field}: Valid")

        # FAIL-FAST: Refuse to generate report
        if missing_fields or invalid_fields:
            error_parts = []
            if missing_fields:
                error_parts.append(f"Missing fields: {missing_fields}")
            if invalid_fields:
                error_parts.append(f"Invalid fields: {invalid_fields}")

            error_message = "Cannot generate report with incomplete data. " + " ".join(error_parts) + "\n\nREFUSING to generate report with hallucinated data."

            logger.error("=" * 80)
            logger.error("REPORT INPUT VALIDATION FAILED")
            logger.error("=" * 80)

            raise ReportValidationError(error_message)

        logger.info("=" * 80)
        logger.info("✅ Report inputs validation passed")
        logger.info("=" * 80)

    def validate_portfolio_review_data(self, portfolio_review: dict[str, Any]) -> None:
        """
        Validate portfolio review contains actual analysis, not fallbacks.

        This method detects the fallback pattern:
        - Grade D
        - Composite score 0.6
        - "Validation rapide" in rationale

        Supports both nested and flat data structures for schema migration:
        - Nested (legacy): portfolio_review["portfolio_review"]["holdings"]
        - Flat (current): portfolio_review["holdings"]

        Args:
            portfolio_review: Portfolio review data

        Raises:
            ReportValidationError: If portfolio contains fallback data

        Requirements: 16.1-16.8 (Data Structure Validation with Migration Support)

        """
        logger.info("=" * 80)
        logger.info("PORTFOLIO REVIEW DATA VALIDATION")
        logger.info("=" * 80)

        # Extract holdings from portfolio review (handle both nested and flat structures)
        # Requirement 16.2: Try nested structure first (legacy format)
        holdings = portfolio_review.get("portfolio_review", {}).get("holdings", [])
        structure_type = "nested"

        # Requirement 16.3: Fall back to flat structure (current format)
        if not holdings:
            holdings = portfolio_review.get("holdings", [])
            structure_type = "flat"

        # Requirement 16.8: Log which structure format was found
        if holdings:
            logger.info(f"✅ Found holdings using {structure_type} structure format")
            logger.info(f"   Holdings count: {len(holdings)}")

        # Requirement 16.4-16.5: If neither structure contains holdings, provide diagnostic info
        if not holdings:
            # Requirement 16.4: Log available keys for debugging
            available_keys = list(portfolio_review.keys())
            logger.error("❌ No holdings found in portfolio review")
            logger.error(f"   Available top-level keys: {available_keys}")

            # Check if nested structure exists but is empty
            if "portfolio_review" in portfolio_review:
                nested_keys = list(portfolio_review["portfolio_review"].keys())
                logger.error(f"   Available nested keys in ['portfolio_review']: {nested_keys}")

            # Requirement 16.5: Raise error with diagnostic information
            error_message = (
                f"Portfolio review contains no holdings\n\n"
                f"Diagnostic Information:\n"
                f"  • Tried nested structure: portfolio_review['portfolio_review']['holdings'] - Not found\n"
                f"  • Tried flat structure: portfolio_review['holdings'] - Not found\n"
                f"  • Available top-level keys: {available_keys}\n\n"
                f"Possible Causes:\n"
                f"  1. Portfolio review was not generated correctly\n"
                f"  2. Data structure changed and migration logic needs update\n"
                f"  3. Holdings list is empty (no assets in portfolio)\n\n"
                f"Remediation:\n"
                f"  1. Check portfolio review generation in check_portfolio() method\n"
                f"  2. Verify portfolio CSV files contain holdings\n"
                f"  3. Check for errors in portfolio holdings processor\n"
            )
            logger.error(error_message)
            raise ReportValidationError(error_message)

        logger.info(f"Validating {len(holdings)} holdings...")

        fallback_count = 0
        fallback_tickers = []

        for holding in holdings:
            ticker = holding.get("ticker", "UNKNOWN")
            grade = holding.get("grade")
            composite_score = holding.get("composite_score")
            rationale_bullets = holding.get("rationale_bullets", [])

            # Check for fallback pattern
            is_fallback = grade == "D" and composite_score == 0.6 and any("Validation rapide" in str(bullet) for bullet in rationale_bullets)

            if is_fallback:
                fallback_count += 1
                fallback_tickers.append(ticker)
                logger.error(f"❌ Holding {ticker} has fallback data: Grade D, Score 0.6, 'Validation rapide'")
            else:
                logger.info(f"✅ Holding {ticker}: Grade {grade}, Score {composite_score:.2f}")

        if fallback_count > 0:
            error_message = f"Portfolio review contains {fallback_count} holdings with fallback data: {fallback_tickers}. REFUSING to generate report with fake grades."

            logger.error("=" * 80)
            logger.error("PORTFOLIO REVIEW VALIDATION FAILED")
            logger.error("=" * 80)

            raise ReportValidationError(error_message)

        logger.info("=" * 80)
        logger.info(f"✅ Portfolio review validation passed: {len(holdings)} holdings with actual analysis data")
        logger.info("=" * 80)

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
