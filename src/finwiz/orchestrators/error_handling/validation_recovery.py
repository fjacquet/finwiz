"""
Validation error recovery system for crew data integration.

This module provides comprehensive validation error analysis, data repair suggestions,
and recovery recommendations for the crew data integration system.
"""

from __future__ import annotations

import logging
from typing import Any

from pydantic import ValidationError

from .error_handlers import ErrorHandlers, ValidationErrorAnalysis, ValidationErrorReport
from .fallback_handlers import FallbackHandlers
from .recovery_strategies import DataRepairSuggestion, RecoveryStrategies

logger = logging.getLogger(__name__)

# Re-export classes for backward compatibility
__all__ = [
    "ValidationErrorAnalysis",
    "DataRepairSuggestion",
    "ValidationErrorReport",
    "ValidationErrorRecovery",
]


class ValidationErrorRecovery:
    """
    Handles validation error analysis, data repair suggestions, and recovery recommendations.

    This class provides comprehensive validation error recovery for the crew data
    integration system, including error categorization, automatic repair suggestions,
    and detailed recovery reporting.

    This class now delegates to specialized handlers for better maintainability.
    """

    def __init__(self) -> None:
        """Initialize the validation error recovery system."""
        self.error_handlers = ErrorHandlers()
        self.recovery_strategies = RecoveryStrategies()
        self.fallback_handlers = FallbackHandlers()

    # Backward compatibility properties
    @property
    def error_patterns(self) -> dict[str, Any]:
        """Backward compatibility property for error patterns."""
        return self.error_handlers.error_patterns

    @property
    def repair_strategies(self) -> dict[str, Any]:
        """Backward compatibility property for repair strategies."""
        return self.recovery_strategies.repair_strategies

    @property
    def default_values(self) -> dict[str, Any]:
        """Backward compatibility property for default values."""
        return self.recovery_strategies.default_values

    def analyze_validation_error(self, error: ValidationError, data_context: dict | None = None) -> ValidationErrorAnalysis:
        """
        Analyze a single validation error and categorize it.

        Args:
            error: The Pydantic ValidationError to analyze
            data_context: Optional context about the data being validated

        Returns:
            Detailed analysis of the validation error

        """
        return self.error_handlers.analyze_validation_error(error, data_context)

    def suggest_data_repairs(self, error_analyses: list[ValidationErrorAnalysis], original_data: dict[str, Any]) -> list[DataRepairSuggestion]:
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

            suggestion = self.recovery_strategies.create_repair_suggestion(analysis, original_data)
            if suggestion:
                repair_suggestions.append(suggestion)

        # Sort by confidence (highest first)
        repair_suggestions.sort(key=lambda x: x.confidence, reverse=True)

        return repair_suggestions

    def generate_error_report(self, validation_errors: list[ValidationError], original_data: dict[str, Any]) -> ValidationErrorReport:
        """
        Generate a comprehensive validation error report.

        Args:
            validation_errors: List of validation errors
            original_data: The original data that failed validation

        Returns:
            Comprehensive validation error report

        """
        return self.error_handlers.generate_error_report(validation_errors, original_data)

    def attempt_data_repair(self, corrupted_data: dict, repair_suggestions: list[DataRepairSuggestion]) -> dict | None:
        """
        Attempt to repair corrupted data using repair suggestions.

        Args:
            corrupted_data: The data that failed validation
            repair_suggestions: List of repair suggestions to apply

        Returns:
            Repaired data if successful, None if repair failed

        """
        return self.fallback_handlers.attempt_data_repair(corrupted_data, repair_suggestions)

    # Backward compatibility methods - delegate to appropriate handlers
    def _categorize_error(self, error_message: str) -> str:
        """Backward compatibility method."""
        return self.error_handlers._categorize_error(error_message)

    def _determine_error_severity(self, error_type: str, field_path: str, error_message: str) -> str:
        """Backward compatibility method."""
        return self.error_handlers._determine_error_severity(error_type, field_path, error_message)

    def _assess_repairability(self, error_type: str, error_info: dict[str, Any]) -> tuple[bool, float]:
        """Backward compatibility method."""
        return self.recovery_strategies.assess_repairability(error_type, error_info)

    def _generate_suggested_fix(self, error_type: str, error_info: dict, data_context: dict | None) -> str | None:
        """Backward compatibility method."""
        return self.recovery_strategies.generate_suggested_fix(error_type, error_info, data_context)

    def _get_nested_value(self, data: dict, field_path: str) -> Any:
        """Backward compatibility method."""
        return self.recovery_strategies._get_nested_value(data, field_path)

    def _get_default_value_for_field(self, field_path: str) -> Any:
        """Backward compatibility method."""
        return self.recovery_strategies._get_default_value_for_field(field_path)

    def _convert_value_type(self, current_value: Any, error_message: str) -> Any:
        """Backward compatibility method."""
        return self.recovery_strategies._convert_value_type(current_value, error_message)

    def _adjust_value_for_constraints(self, current_value: Any, error_message: str) -> Any:
        """Backward compatibility method."""
        return self.recovery_strategies._adjust_value_for_constraints(current_value, error_message)

    def _create_repair_suggestion(self, analysis: ValidationErrorAnalysis, original_data: dict[str, Any]) -> DataRepairSuggestion | None:
        """Backward compatibility method."""
        return self.recovery_strategies.create_repair_suggestion(analysis, original_data)

    def _generate_recovery_recommendations(self, error_analyses: list[ValidationErrorAnalysis], repair_suggestions: list[DataRepairSuggestion]) -> list[str]:
        """Backward compatibility method."""
        return self.error_handlers._generate_recovery_recommendations(error_analyses, repair_suggestions)

    def _set_nested_value(self, data: dict, keys: list[str], value: Any) -> None:
        """Backward compatibility method."""
        return self.fallback_handlers._set_nested_value(data, keys, value)

    def _remove_nested_field(self, data: dict, keys: list[str]) -> None:
        """Backward compatibility method."""
        return self.fallback_handlers._remove_nested_field(data, keys)

    def _apply_repair_suggestion(self, data: dict, suggestion: DataRepairSuggestion) -> dict[str, Any]:
        """Backward compatibility method."""
        return self.fallback_handlers._apply_repair_suggestion(data, suggestion)
