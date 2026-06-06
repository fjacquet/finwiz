"""
Fallback handlers for applying data repairs and recovery operations.

This module provides fallback logic for applying repair suggestions and
handling data recovery operations in the crew data integration system.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from finwiz.orchestrators.error_handling.recovery import DataRepairSuggestion

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

    def attempt_data_repair(self, corrupted_data: dict, repair_suggestions: list[Any]) -> dict | None:
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

    def _apply_repair_suggestion(self, data: dict, suggestion: DataRepairSuggestion) -> dict[str, Any]:
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

    def _sanitize_data_section(self, data_section: dict[str, Any]) -> dict[str, Any]:
        """
        Sanitize a data section to remove problematic fields.

        Args:
            data_section: The data section to sanitize

        Returns:
            Sanitized data section

        """
        sanitized: dict[str, Any] = {}

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
