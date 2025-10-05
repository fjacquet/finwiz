"""
Fallback handlers for applying data repairs and recovery operations.

This module provides fallback logic for applying repair suggestions and
handling data recovery operations in the crew data integration system.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from finwiz.integration.recovery_strategies import DataRepairSuggestion
    from finwiz.integration.validation_manager import ValidationResult

logger = logging.getLogger(__name__)


class FallbackHandlers:
    """
    Handles fallback operations for data repair and recovery.

    This class provides the logic for applying repair suggestions to corrupted
    data and managing fallback operations when validation fails.
    """

    def __init__(self) -> None:
        """Initialize fallback handlers."""
        pass

    def attempt_data_repair(self, corrupted_data: dict, repair_suggestions: list) -> dict | None:
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

    def create_fallback_data(self, original_data: dict, error_report: ValidationResult) -> dict:
        """
        Create fallback data when repair attempts fail.

        Args:
            original_data: The original data that failed validation
            error_report: The validation error report

        Returns:
            Fallback data structure with minimal valid content

        """
        from datetime import datetime

        fallback_data = {
            "metadata": {
                "crew_name": original_data.get("metadata", {}).get("crew_name", "unknown"),
                "execution_timestamp": datetime.now().isoformat(),
                "schema_version": 1,
                "fallback_mode": True,
                "original_errors": len(error_report.error_analyses),
            },
            "validation_status": {
                "is_valid": False,
                "validation_timestamp": datetime.now().isoformat(),
                "validation_errors": [analysis.error_message for analysis in error_report.error_analyses],
                "validation_warnings": [],
                "fallback_applied": True,
            },
            "data_sources": [],
            "freshness_status": {
                "dependencies_met": False,
                "is_fresh": False,
                "age_hours": 999.0,
                "max_age_hours": 24,
                "refresh_recommended": True,
                "last_updated": datetime.now().isoformat(),
            },
        }

        # Try to preserve any valid data from the original
        try:
            if "data" in original_data and isinstance(original_data["data"], dict):
                fallback_data["data"] = self._sanitize_data_section(original_data["data"])
        except Exception as e:
            logger.warning(f"Could not preserve original data: {e}")
            fallback_data["data"] = {}

        return fallback_data

    def _sanitize_data_section(self, data_section: dict) -> dict:
        """
        Sanitize a data section to remove problematic fields.

        Args:
            data_section: The data section to sanitize

        Returns:
            Sanitized data section

        """
        sanitized = {}

        for key, value in data_section.items():
            try:
                # Only include simple, safe data types
                if isinstance(value, (str, int, float, bool)):
                    sanitized[key] = value
                elif isinstance(value, list) and all(isinstance(item, (str, int, float, bool)) for item in value):
                    sanitized[key] = value
                elif isinstance(value, dict):
                    # Recursively sanitize nested dictionaries
                    nested_sanitized = self._sanitize_data_section(value)
                    if nested_sanitized:  # Only include if not empty
                        sanitized[key] = nested_sanitized
            except Exception as e:
                logger.debug(f"Skipping problematic field {key}: {e}")
                continue

        return sanitized

    def apply_emergency_fallback(self, crew_name: str) -> dict:
        """
        Apply emergency fallback when all other recovery attempts fail.

        Args:
            crew_name: Name of the crew that failed

        Returns:
            Minimal emergency fallback data structure

        """
        from datetime import datetime

        return {
            "metadata": {
                "crew_name": crew_name,
                "execution_timestamp": datetime.now().isoformat(),
                "schema_version": 1,
                "emergency_fallback": True,
            },
            "validation_status": {
                "is_valid": False,
                "validation_timestamp": datetime.now().isoformat(),
                "validation_errors": ["Emergency fallback applied - original data could not be recovered"],
                "validation_warnings": [],
                "emergency_mode": True,
            },
            "data_sources": [],
            "freshness_status": {
                "dependencies_met": False,
                "is_fresh": False,
                "age_hours": 999.0,
                "max_age_hours": 24,
                "refresh_recommended": True,
                "last_updated": datetime.now().isoformat(),
            },
            "data": {},
        }
