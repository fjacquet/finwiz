"""
Error handlers for validation error analysis and categorization.

This module provides comprehensive validation error analysis, categorization,
and severity assessment for the crew data integration system.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, ValidationError


class ValidationErrorAnalysis(BaseModel):
    """Analysis of a validation error with categorization and severity."""

    error_type: str = Field(description="Type of validation error (e.g., 'missing_field', 'type_mismatch')")
    field_path: str = Field(description="Path to the field that caused the error")
    error_message: str = Field(description="Original error message")
    severity: str = Field(description="Severity level: 'critical', 'high', 'medium', 'low'")
    is_repairable: bool = Field(description="Whether this error can be automatically repaired")
    repair_confidence: float = Field(ge=0.0, le=1.0, description="Confidence level for automatic repair (0.0 to 1.0)")
    suggested_fix: str | None = Field(default=None, description="Suggested fix for the validation error")
    context: dict[str, Any] = Field(default_factory=dict, description="Additional context about the error")


class ValidationErrorReport(BaseModel):
    """Comprehensive report on validation errors and recovery options."""

    total_errors: int = Field(description="Total number of validation errors")
    error_analyses: list[ValidationErrorAnalysis] = Field(default_factory=list, description="Detailed analysis of each error")
    repair_suggestions: list = Field(default_factory=list, description="Suggestions for repairing the data")
    recovery_recommendations: list[str] = Field(default_factory=list, description="High-level recovery recommendations")
    repairable_errors_count: int = Field(description="Number of errors that can be automatically repaired")
    critical_errors_count: int = Field(description="Number of critical errors")
    report_timestamp: datetime = Field(description="When this report was generated")
    overall_repairability: str = Field(description="Overall assessment: 'fully_repairable', 'partially_repairable', 'not_repairable'")


class ErrorHandlers:
    """
    Handles validation error analysis and categorization.

    This class provides comprehensive validation error analysis including
    error categorization, severity assessment, and detailed reporting.
    """

    def __init__(self) -> None:
        """Initialize error handlers."""
        self._initialize_error_patterns()

    def _initialize_error_patterns(self) -> None:
        """Initialize patterns for categorizing validation errors."""
        self.error_patterns = {
            # Missing field errors
            "missing_field": [r"field required", r"missing.*required", r"none is not an allowed value", r"field.*is required"],
            # Type mismatch errors
            "type_mismatch": [
                r"value is not a valid.*",
                r"str type expected",
                r"int type expected",
                r"float type expected",
                r"bool type expected",
                r"list type expected",
                r"dict type expected",
                r"input should be a valid.*",
                r"unable to interpret input",
            ],
            # Format/pattern errors
            "format_error": [
                r"string does not match expected pattern",
                r"invalid.*format",
                r"does not match regex",
                r"invalid url",
                r"invalid email",
                r"invalid datetime",
                r"invalid character in",
            ],
            # Range/constraint errors
            "constraint_error": [
                r"ensure this value is greater than",
                r"ensure this value is less than",
                r"ensure this value has at least",
                r"ensure this value has at most",
                r"string too short",
                r"string too long",
                r"should have at least",
                r"should have at most",
                r"should be greater than",
                r"should be less than",
                r"input should be greater than or equal to",
                r"input should be less than or equal to",
            ],
            # Enum/choice errors
            "enum_error": [r"value is not a valid enumeration member", r"unexpected value.*expected", r"not an allowed value"],
            # Schema/structure errors
            "schema_error": [r"extra fields not permitted", r"unknown field", r"unexpected keyword argument"],
        }

    def analyze_validation_error(self, error: ValidationError, data_context: dict | None = None) -> ValidationErrorAnalysis:
        """
        Analyze a single validation error and categorize it.

        Args:
            error: The Pydantic ValidationError to analyze
            data_context: Optional context about the data being validated

        Returns:
            Detailed analysis of the validation error

        """
        error_info = error.errors()[0] if error.errors() else {}
        error_message = str(error_info.get("msg", str(error)))
        field_path = ".".join(str(loc) for loc in error_info.get("loc", []))

        # Categorize the error
        error_type = self._categorize_error(error_message)

        # Determine severity
        severity = self._determine_error_severity(error_type, field_path, error_message)

        # Import here to avoid circular imports
        from .recovery_strategies import RecoveryStrategies

        recovery_strategies = RecoveryStrategies()

        # Check if repairable
        is_repairable, repair_confidence = recovery_strategies.assess_repairability(error_type, error_info)

        # Generate suggested fix
        suggested_fix = recovery_strategies.generate_suggested_fix(error_type, error_info, data_context)

        return ValidationErrorAnalysis(
            error_type=error_type,
            field_path=field_path,
            error_message=error_message,
            severity=severity,
            is_repairable=is_repairable,
            repair_confidence=repair_confidence,
            suggested_fix=suggested_fix,
            context={"error_info": error_info, "data_context": data_context or {}},
        )

    def _categorize_error(self, error_message: str) -> str:
        """Categorize an error message based on patterns."""
        error_message_lower = error_message.lower()

        for error_type, patterns in self.error_patterns.items():
            for pattern in patterns:
                if re.search(pattern, error_message_lower):
                    return error_type

        return "unknown_error"

    def _determine_error_severity(self, error_type: str, field_path: str, error_message: str) -> str:
        """Determine the severity of a validation error."""
        # Critical fields that must be present
        critical_fields = ["metadata", "crew_name", "execution_timestamp", "validation_status"]

        # High priority fields
        high_priority_fields = ["schema_version", "data_sources", "freshness_status", "validation_status"]

        field_path.split(".")[-1] if field_path else ""

        # Check if it's a critical field
        if any(critical in field_path.lower() for critical in critical_fields):
            return "critical"

        # Check error type severity
        if error_type in ["missing_field", "schema_error"]:
            if any(high_priority in field_path.lower() for high_priority in high_priority_fields):
                return "high"
            return "medium"

        if error_type in ["constraint_error"] and any(high_priority in field_path.lower() for high_priority in high_priority_fields):
            return "high"

        if error_type in ["type_mismatch", "constraint_error"]:
            return "medium"

        if error_type in ["format_error", "enum_error"]:
            return "low"

        return "medium"

    def generate_error_report(self, validation_errors: list[ValidationError], original_data: dict[str, Any]) -> ValidationErrorReport:
        """
        Generate a comprehensive validation error report.

        Args:
            validation_errors: List of validation errors
            original_data: The original data that failed validation

        Returns:
            Comprehensive validation error report

        """
        error_analyses = []

        # Analyze each validation error
        for error in validation_errors:
            analysis = self.analyze_validation_error(error, {"original_data": original_data})
            error_analyses.append(analysis)

        # Import here to avoid circular imports
        from .recovery_strategies import RecoveryStrategies

        recovery_strategies = RecoveryStrategies()

        # Generate repair suggestions
        repair_suggestions = []
        for analysis in error_analyses:
            if analysis.is_repairable:
                suggestion = recovery_strategies.create_repair_suggestion(analysis, original_data)
                if suggestion:
                    repair_suggestions.append(suggestion)

        # Sort by confidence (highest first)
        repair_suggestions.sort(key=lambda x: x.confidence, reverse=True)

        # Count different types of errors
        repairable_count = sum(1 for analysis in error_analyses if analysis.is_repairable)
        critical_count = sum(1 for analysis in error_analyses if analysis.severity == "critical")

        # Generate recovery recommendations
        recovery_recommendations = self._generate_recovery_recommendations(error_analyses, repair_suggestions)

        # Determine overall repairability
        if repairable_count == len(error_analyses):
            overall_repairability = "fully_repairable"
        elif repairable_count > 0:
            overall_repairability = "partially_repairable"
        else:
            overall_repairability = "not_repairable"

        return ValidationErrorReport(
            total_errors=len(error_analyses),
            error_analyses=error_analyses,
            repair_suggestions=repair_suggestions,
            recovery_recommendations=recovery_recommendations,
            repairable_errors_count=repairable_count,
            critical_errors_count=critical_count,
            report_timestamp=datetime.now(),
            overall_repairability=overall_repairability,
        )

    def _generate_recovery_recommendations(self, error_analyses: list[ValidationErrorAnalysis], repair_suggestions: list[Any]) -> list[str]:
        """Generate high-level recovery recommendations."""
        recommendations = []

        critical_errors = [a for a in error_analyses if a.severity == "critical"]
        if critical_errors:
            recommendations.append(f"Address {len(critical_errors)} critical validation errors immediately")

        high_confidence_repairs = [r for r in repair_suggestions if r.confidence > 0.8]
        if high_confidence_repairs:
            recommendations.append(f"Apply {len(high_confidence_repairs)} high-confidence automatic repairs")

        manual_repairs = [r for r in repair_suggestions if r.confidence < 0.6]
        if manual_repairs:
            recommendations.append(f"Review {len(manual_repairs)} low-confidence repairs manually")

        schema_errors = [a for a in error_analyses if a.error_type == "schema_error"]
        if schema_errors:
            recommendations.append("Update data structure to match expected schema")

        missing_fields = [a for a in error_analyses if a.error_type == "missing_field"]
        if missing_fields:
            recommendations.append(f"Provide values for {len(missing_fields)} missing required fields")

        if not recommendations:
            recommendations.append("No specific recovery actions identified")

        return recommendations
