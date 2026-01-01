"""
Recovery strategies for validation error handling.

This module provides strategies for determining how to repair different types
of validation errors in the crew data integration system.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from typing import TYPE_CHECKING, Any, cast

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from finwiz.integration.error_handlers import ValidationErrorAnalysis


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


class RecoveryStrategies:
    """
    Provides strategies for recovering from validation errors.

    This class contains the logic for determining how to repair different types
    of validation errors and generating appropriate repair suggestions.
    """

    def __init__(self) -> None:
        """Initialize recovery strategies."""
        self._initialize_repair_strategies()
        self._initialize_default_values()

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

    def _initialize_default_values(self) -> None:
        """Initialize default values for common field types."""
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

    def assess_repairability(self, error_type: str, error_info: dict[str, Any]) -> tuple[bool, float]:
        """Assess whether an error can be automatically repaired."""
        if error_type not in self.repair_strategies:
            return False, 0.0

        strategy = self.repair_strategies[error_type]
        base_confidence = cast(float, strategy["confidence"])

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

    def generate_suggested_fix(self, error_type: str, error_info: dict, data_context: dict | None) -> str | None:
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

        return str(strategy["description"])

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

    def create_repair_suggestion(self, error_analysis: ValidationErrorAnalysis, original_data: dict[str, Any]) -> DataRepairSuggestion | None:
        """Create a specific repair suggestion for a validation error."""
        field_path = error_analysis.field_path
        error_type = error_analysis.error_type

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
                confidence=error_analysis.repair_confidence,
                side_effects=[],
                validation_after_repair=True,
            )

        if error_type == "type_mismatch":
            suggested_value = self._convert_value_type(current_value, error_analysis.error_message)
            return DataRepairSuggestion(
                repair_type="convert_type",
                field_path=field_path,
                current_value=current_value,
                suggested_value=suggested_value,
                repair_description=f"Convert '{current_value}' to expected type",
                confidence=error_analysis.repair_confidence,
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
                confidence=error_analysis.repair_confidence,
                side_effects=["Data will be permanently removed"],
                validation_after_repair=True,
            )

        if error_type == "constraint_error":
            suggested_value = self._adjust_value_for_constraints(current_value, error_analysis.error_message)
            return DataRepairSuggestion(
                repair_type="adjust_value",
                field_path=field_path,
                current_value=current_value,
                suggested_value=suggested_value,
                repair_description=f"Adjust '{current_value}' to meet constraints",
                confidence=error_analysis.repair_confidence * 0.7,  # Lower confidence for constraint adjustments
                side_effects=["Original value will be modified"],
                validation_after_repair=True,
            )

        return None

    def _get_nested_value(self, data: dict, field_path: str) -> Any:
        """Get a nested value from a dictionary using dot notation."""
        if not field_path:
            return data

        keys = field_path.split(".")
        current: Any = data

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
