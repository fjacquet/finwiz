"""
Schema management for crew data integration.

Handles data serialization, deserialization, and schema-related operations.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel


class SchemaManager:
    """
    Manager for data schemas and serialization.

    Handles JSON serialization/deserialization with support for datetime and Pydantic models.
    """

    def __init__(self, logger: logging.Logger) -> None:
        """
        Initialize the schema manager.

        Args:
            logger: Logger instance for schema operations

        """
        self.logger = logger

    def serialize_usage_metrics(self, usage_metrics: Any) -> dict:
        """
        Convert UsageMetrics object to JSON-serializable dictionary.

        Args:
            usage_metrics: UsageMetrics object from CrewAI

        Returns:
            Dictionary representation of usage metrics

        """
        if usage_metrics is None:
            return {}

        try:
            # If it's already a dict, return as-is
            if isinstance(usage_metrics, dict):
                return usage_metrics

            # Try to convert Pydantic model to dict
            if hasattr(usage_metrics, "model_dump"):
                return usage_metrics.model_dump()

            # Try to convert using dict() for dataclasses or similar
            if hasattr(usage_metrics, "__dict__"):
                return {
                    key: value for key, value in usage_metrics.__dict__.items() if not key.startswith("_") and not callable(value)
                }

            # Fallback: convert to string representation
            return {"raw_usage_metrics": str(usage_metrics)}

        except Exception as e:
            self.logger.warning(f"Failed to serialize usage_metrics: {str(e)}")
            return {"serialization_error": str(e), "raw_usage_metrics": str(usage_metrics)}

    def save_json_file(self, file_path: Path, data: dict) -> None:
        """Save data to JSON file with custom serialization for datetime and Pydantic models."""

        def json_serializer(obj: Any) -> str:
            """Serialize datetime and Pydantic objects to JSON."""
            if isinstance(obj, datetime):
                return obj.isoformat()
            if isinstance(obj, BaseModel):
                return obj.model_dump()
            if hasattr(obj, "__dict__"):
                return obj.__dict__
            return str(obj)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=json_serializer)

    def load_json_file(self, file_path: Path, default: dict) -> dict:
        """Load JSON file with default fallback."""
        try:
            if file_path.exists():
                with open(file_path, encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning(f"Failed to load JSON file {file_path}: {str(e)}")

        return default
