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

    def save_json_file(self, file_path: Path, data: dict[str, Any]) -> None:
        """Save data to JSON file with custom serialization for datetime and Pydantic models."""

        def json_serializer(obj: Any) -> Any:
            """Serialize datetime and Pydantic objects to JSON."""
            if isinstance(obj, datetime):
                return obj.isoformat()
            if isinstance(obj, BaseModel):
                model_dict: dict[str, Any] = obj.model_dump()
                return model_dict
            if hasattr(obj, "__dict__"):
                obj_dict: dict[str, Any] = obj.__dict__
                return obj_dict
            return str(obj)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=json_serializer)

    def load_json_file(self, file_path: Path, default: dict[str, Any]) -> dict[str, Any]:
        """Load JSON file with default fallback."""
        try:
            if file_path.exists():
                with open(file_path, encoding="utf-8") as f:
                    loaded_data: dict[str, Any] = json.load(f)
                    return loaded_data
        except Exception as e:
            self.logger.warning(f"Failed to load JSON file {file_path}: {e!s}")

        return default
