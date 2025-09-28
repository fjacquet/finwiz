"""
Validation error recovery system for crew data integration.

This module provides comprehensive validation error analysis, data repair suggestions,
and recovery recommendations for the crew data integration system.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger(__name__)


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


class DataRepairSuggestion(BaseModel):
    """Suggestion for repairing invalid data."""

    repair_type: str = Field(description="Type of repair (e.g., 'set_default', 'convert_type', 'remove_field')")
    field_path: str = Field(description="Path to the field to repair")
    current_value: Any = Field(description="Current invalid value")
    suggested_value: Any = Field(description="Suggested replacement value")
    repair_description: str = Field(description="Human-readable description of the repair")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in this repair suggestion")
    side_effects: list[str] = Field(default_factory=list, description="Potential side effects of applying this repair")
    validation_after_repair: bool = Field(default=True, description="Whether validation should be re-run after this repair")


class ValidationErrorReport(BaseModel):
    """Comprehensive report on validation errors and recovery options."""

    total_errors: int = Field(description="Total number of validation errors")
    error_analyses: list[ValidationErrorAnalysis] = Field(default_factory=list, description="Detailed analysis of each error")
    repair_suggestions: list[DataRepairSuggestion] = Field(default_factory=list, description="Suggestions for repairing the data")
    recovery_recommendations: list[str] = Field(default_factory=list, description="High-level recovery recommendations")
    repairable_errors_count: int = Field(description="Number of errors that can be automatically repaired")
    critical_errors_count: int = Field(description="Number of critical errors")
    report_timestamp: datetime = Field(description="When this report was generated")
    overall_repairability: str = Field(
        description="Overall assessment: 'fully_repairable', 'partially_repairable', 'not_repairable'"
    )


class ValidationErrorRecovery:
    """
    Handles validation error analysis, data repair suggestions, and recovery recommendations.

    This class provides comprehensive validation error recovery for the crew data
    integration system, including error categorization, automatic repair suggestions,
    and detailed recovery reporting.
    """

    def __init__(self) -> None:
        """Initialize the validation error recovery system."""
        self._initialize_error_patterns()
        self._initialize_repair_strategies()

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

    def _initialize_repair_strategies(self) -> None:
        """Initialize repair strategies for different error types."""
        self.repair_strategies = {
            "missing_field": {
                "strategy": "set_default",
                "confidence": 0.8,
                "description": "Set missing field to appropriate default value",
            },
            "type_mismatch": {
                "strategy": "convert_type",
                "confidence": 0.7,
                "description": "Convert value to expected type if possible",
            },
            "format_error": {
                "strategy": "format_correction",
                "confidence": 0.6,
                "description": "Correct format to match expected pattern",
            },
            "constraint_error": {"strategy": "adjust_value", "confidence": 0.7, "description": "Adjust value to meet constraints"},
            "enum_error": {"strategy": "map_to_valid", "confidence": 0.5, "description": "Map to closest valid enumeration value"},
            "schema_error": {"strategy": "remove_extra", "confidence": 0.9, "description": "Remove extra fields not in schema"},
        }

        # Default values for common field types
        self.default_values = {
            "str": "",
            "int": 0,
            "float": 0.0,
            "bool": False,
            "list": [],
            "dict": {},
            "datetime": datetime.now().isoformat(),
            "optional_str": None,
            "optional_int": None,
            "optional_float": None,
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

        # Check if repairable
        is_repairable, repair_confidence = self._assess_repairability(error_type, error_info)

        # Generate suggested fix
        suggested_fix = self._generate_suggested_fix(error_type, error_info, data_context)

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

        if error_type in ["constraint_error"] and any(
            high_priority in field_path.lower() for high_priority in high_priority_fields
        ):
            return "high"

        if error_type in ["type_mismatch", "constraint_error"]:
            return "medium"

        if error_type in ["format_error", "enum_error"]:
            return "low"

        return "medium"

    def _assess_repairability(self, error_type: str, error_info: dict) -> tuple[bool, float]:
        """Assess whether an error can be automatically repaired."""
        if error_type not in self.repair_strategies:
            return False, 0.0

        strategy = self.repair_strategies[error_type]
        base_confidence = strategy["confidence"]

        # Adjust confidence based on specific error details
        if error_type == "missing_field":
            # Missing fields are usually repairable with defaults
            return True, base_confidence

        if error_type == "type_mismatch":
            # Type mismatches depend on the specific types involved
            input_type = error_info.get("input", None)
            if input_type is not None:
                # Can often convert strings to numbers, etc.
                return True, base_confidence * 0.8
            return True, base_confidence * 0.5

        if error_type == "schema_error":
            # Extra fields can usually be removed safely
            return True, base_confidence

        if error_type in ["format_error", "constraint_error", "enum_error"]:
            # These require more careful handling
            return True, base_confidence * 0.6

        return False, 0.0

    def _generate_suggested_fix(self, error_type: str, error_info: dict, data_context: dict | None) -> str | None:
        """Generate a suggested fix for the validation error."""
        if error_type not in self.repair_strategies:
            return None

        strategy = self.repair_strategies[error_type]
        field_path = ".".join(str(loc) for loc in error_info.get("loc", []))

        if error_type == "missing_field":
            return f"Add missing field '{field_path}' with appropriate default value"

        if error_type == "type_mismatch":
            expected_type = self._extract_expected_type(error_info.get("msg", ""))
            current_value = error_info.get("input", "unknown")
            return f"Convert '{current_value}' to {expected_type} type"

        if error_type == "schema_error":
            return f"Remove extra field '{field_path}' not allowed in schema"

        if error_type == "format_error":
            return f"Correct format of field '{field_path}' to match expected pattern"

        if error_type == "constraint_error":
            return f"Adjust value of field '{field_path}' to meet constraints"

        if error_type == "enum_error":
            return f"Change value of field '{field_path}' to valid enumeration member"

        return strategy["description"]

    def _extract_expected_type(self, error_message: str) -> str:
        """Extract expected type from error message."""
        type_patterns = {
            r"str type expected": "string",
            r"int type expected": "integer",
            r"float type expected": "float",
            r"bool type expected": "boolean",
            r"list type expected": "list",
            r"dict type expected": "dictionary",
        }

        for pattern, type_name in type_patterns.items():
            if re.search(pattern, error_message):
                return type_name

        return "unknown"

    def suggest_data_repairs(
        self, error_analyses: list[ValidationErrorAnalysis], original_data: dict
    ) -> list[DataRepairSuggestion]:
        """
        Generate data repair suggestions based on error analyses.

        Args:
            error_analyses: List of validation error analyses
            original_data: The original data that failed validation

        Returns:
            List of data repair suggestions

        """
        repair_suggestions = []

        for analysis in error_analyses:
            if not analysis.is_repairable:
                continue

            suggestion = self._create_repair_suggestion(analysis, original_data)
            if suggestion:
                repair_suggestions.append(suggestion)

        # Sort by confidence (highest first)
        repair_suggestions.sort(key=lambda x: x.confidence, reverse=True)

        return repair_suggestions

    def _create_repair_suggestion(self, analysis: ValidationErrorAnalysis, original_data: dict) -> DataRepairSuggestion | None:
        """Create a specific repair suggestion for a validation error."""
        field_path = analysis.field_path
        error_type = analysis.error_type

        # Get current value from original data
        current_value = self._get_nested_value(original_data, field_path)

        if error_type == "missing_field":
            suggested_value = self._get_default_value_for_field(field_path)
            return DataRepairSuggestion(
                repair_type="set_default",
                field_path=field_path,
                current_value=None,
                suggested_value=suggested_value,
                repair_description=f"Set missing field '{field_path}' to default value",
                confidence=analysis.repair_confidence,
                side_effects=[],
                validation_after_repair=True,
            )

        if error_type == "type_mismatch":
            suggested_value = self._convert_value_type(current_value, analysis.error_message)
            return DataRepairSuggestion(
                repair_type="convert_type",
                field_path=field_path,
                current_value=current_value,
                suggested_value=suggested_value,
                repair_description=f"Convert '{current_value}' to expected type",
                confidence=analysis.repair_confidence,
                side_effects=["May lose precision in type conversion"],
                validation_after_repair=True,
            )

        if error_type == "schema_error":
            return DataRepairSuggestion(
                repair_type="remove_field",
                field_path=field_path,
                current_value=current_value,
                suggested_value=None,
                repair_description=f"Remove extra field '{field_path}'",
                confidence=analysis.repair_confidence,
                side_effects=["Data will be permanently removed"],
                validation_after_repair=True,
            )

        if error_type == "constraint_error":
            suggested_value = self._adjust_value_for_constraints(current_value, analysis.error_message)
            return DataRepairSuggestion(
                repair_type="adjust_value",
                field_path=field_path,
                current_value=current_value,
                suggested_value=suggested_value,
                repair_description=f"Adjust '{current_value}' to meet constraints",
                confidence=analysis.repair_confidence * 0.7,  # Lower confidence for constraint adjustments
                side_effects=["Original value will be modified"],
                validation_after_repair=True,
            )

        return None

    def _get_nested_value(self, data: dict, field_path: str) -> Any:
        """Get a nested value from a dictionary using dot notation."""
        if not field_path:
            return data

        keys = field_path.split(".")
        current = data

        try:
            for key in keys:
                if isinstance(current, dict):
                    current = current.get(key)
                elif isinstance(current, list) and key.isdigit():
                    current = current[int(key)]
                else:
                    return None
            return current
        except (KeyError, IndexError, TypeError):
            return None

    def _get_default_value_for_field(self, field_path: str) -> Any:
        """Get an appropriate default value for a field based on its name."""
        field_name = field_path.split(".")[-1].lower()

        # Specific field defaults
        field_defaults = {
            "crew_name": "unknown",
            "execution_timestamp": datetime.now().isoformat(),
            "schema_version": 1,
            "is_valid": False,
            "validation_timestamp": datetime.now().isoformat(),
            "validation_errors": [],
            "validation_warnings": [],
            "data_sources": [],
            "dependencies_met": False,
            "is_fresh": False,
            "age_hours": 999.0,
            "max_age_hours": 24,
            "refresh_recommended": True,
            "last_updated": datetime.now().isoformat(),
        }

        if field_name in field_defaults:
            return field_defaults[field_name]

        # Generic defaults based on field name patterns
        if "timestamp" in field_name or "date" in field_name:
            return datetime.now().isoformat()

        if "count" in field_name or "score" in field_name:
            return 0

        if "status" in field_name:
            return "unknown"

        if "list" in field_name or field_name.endswith("s"):
            return []

        if "url" in field_name:
            return ""

        return ""

    def _convert_value_type(self, current_value: Any, error_message: str) -> Any:
        """Convert a value to the expected type based on error message."""
        if "str type expected" in error_message:
            return str(current_value) if current_value is not None else ""

        if "int type expected" in error_message:
            try:
                if isinstance(current_value, str):
                    return int(float(current_value))  # Handle "123.0" strings
                return int(current_value)
            except (ValueError, TypeError):
                return 0

        if "float type expected" in error_message:
            try:
                return float(current_value)
            except (ValueError, TypeError):
                return 0.0

        if "bool type expected" in error_message:
            if isinstance(current_value, str):
                return current_value.lower() in ("true", "1", "yes", "on")
            return bool(current_value)

        if "list type expected" in error_message:
            if current_value is None:
                return []
            if not isinstance(current_value, list):
                return [current_value]
            return current_value

        if "dict type expected" in error_message:
            if current_value is None:
                return {}
            if isinstance(current_value, str):
                try:
                    return json.loads(current_value)
                except json.JSONDecodeError:
                    return {}
            return dict(current_value) if hasattr(current_value, "__dict__") else {}

        return current_value

    def _adjust_value_for_constraints(self, current_value: Any, error_message: str) -> Any:
        """Adjust a value to meet constraints based on error message."""
        if "greater than" in error_message:
            # Extract minimum value from error message
            match = re.search(r"greater than (\d+(?:\.\d+)?)", error_message)
            if match and isinstance(current_value, (int, float)):
                min_val = float(match.group(1))
                return max(current_value, min_val + 0.1)

        if "less than" in error_message:
            # Extract maximum value from error message
            match = re.search(r"less than (\d+(?:\.\d+)?)", error_message)
            if match and isinstance(current_value, (int, float)):
                max_val = float(match.group(1))
                return min(current_value, max_val - 0.1)

        if "at least" in error_message and isinstance(current_value, str):
            # String length constraint
            match = re.search(r"at least (\d+)", error_message)
            if match:
                min_length = int(match.group(1))
                if len(current_value) < min_length:
                    return current_value + "x" * (min_length - len(current_value))

        if "at most" in error_message and isinstance(current_value, str):
            # String length constraint
            match = re.search(r"at most (\d+)", error_message)
            if match:
                max_length = int(match.group(1))
                return current_value[:max_length]

        return current_value

    def generate_error_report(self, validation_errors: list[ValidationError], original_data: dict) -> ValidationErrorReport:
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

        # Generate repair suggestions
        repair_suggestions = self.suggest_data_repairs(error_analyses, original_data)

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

    def _generate_recovery_recommendations(
        self, error_analyses: list[ValidationErrorAnalysis], repair_suggestions: list[DataRepairSuggestion]
    ) -> list[str]:
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

    def attempt_data_repair(self, corrupted_data: dict, repair_suggestions: list[DataRepairSuggestion]) -> dict | None:
        """
        Attempt to repair corrupted data using repair suggestions.

        Args:
            corrupted_data: The data that failed validation
            repair_suggestions: List of repair suggestions to apply

        Returns:
            Repaired data if successful, None if repair failed

        """
        try:
            repaired_data = corrupted_data.copy()

            # Apply repairs in order of confidence (highest first)
            for suggestion in sorted(repair_suggestions, key=lambda x: x.confidence, reverse=True):
                if suggestion.confidence < 0.5:
                    # Skip low-confidence repairs
                    logger.warning(f"Skipping low-confidence repair for {suggestion.field_path}")
                    continue

                repaired_data = self._apply_repair_suggestion(repaired_data, suggestion)

                logger.info(f"Applied repair: {suggestion.repair_type} to {suggestion.field_path}")

            return repaired_data

        except Exception as e:
            logger.error(f"Failed to repair data: {e}")
            return None

    def _apply_repair_suggestion(self, data: dict, suggestion: DataRepairSuggestion) -> dict:
        """Apply a single repair suggestion to the data."""
        field_path = suggestion.field_path
        keys = field_path.split(".")

        if suggestion.repair_type == "set_default":
            self._set_nested_value(data, keys, suggestion.suggested_value)

        elif suggestion.repair_type == "convert_type":
            self._set_nested_value(data, keys, suggestion.suggested_value)

        elif suggestion.repair_type == "remove_field":
            self._remove_nested_field(data, keys)

        elif suggestion.repair_type == "adjust_value":
            self._set_nested_value(data, keys, suggestion.suggested_value)

        return data

    def _set_nested_value(self, data: dict, keys: list[str], value: Any) -> None:
        """Set a nested value in a dictionary using a list of keys."""
        current = data

        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value

    def _remove_nested_field(self, data: dict, keys: list[str]) -> None:
        """Remove a nested field from a dictionary using a list of keys."""
        current = data

        try:
            for key in keys[:-1]:
                current = current[key]

            if keys[-1] in current:
                del current[keys[-1]]
        except (KeyError, TypeError):
            # Field doesn't exist, nothing to remove
            pass
