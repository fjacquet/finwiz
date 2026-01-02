"""
JSON error handling utilities for FinWiz.

Provides comprehensive error handling for JSON parsing and schema validation
with sanitized logging that excludes sensitive data.
"""

import json
import logging
from pathlib import Path
from typing import Any

from pydantic import ValidationError

logger = logging.getLogger(__name__)


class JSONParsingError(Exception):
    """Raised when JSON parsing fails."""

    def __init__(self, file_path: str, line_number: int | None, column: int | None, message: str) -> None:
        """Initialize JSON parsing error with location details."""
        self.file_path = file_path
        self.line_number = line_number
        self.column = column
        self.message = message
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        """Format error message with file location details."""
        location = f"File: {self.file_path}"
        if self.line_number is not None:
            location += f", Line: {self.line_number}"
        if self.column is not None:
            location += f", Column: {self.column}"
        return f"JSON parsing failed - {location}\nError: {self.message}"


class SchemaValidationError(Exception):
    """Raised when schema validation fails."""

    def __init__(self, schema_name: str, errors: list[dict[str, Any]]) -> None:
        """Initialize schema validation error with field-level details."""
        self.schema_name = schema_name
        self.errors = errors
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        """Format error message with field-level validation details."""
        error_lines = [f"Schema validation failed for: {self.schema_name}"]
        error_lines.append(f"Total errors: {len(self.errors)}")
        error_lines.append("\nValidation errors:")

        for error in self.errors:
            field_path = " -> ".join(str(loc) for loc in error.get("loc", []))
            error_type = error.get("type", "unknown")
            message = error.get("msg", "No message provided")
            error_lines.append(f"  • Field: {field_path}")
            error_lines.append(f"    Type: {error_type}")
            error_lines.append(f"    Message: {message}")

        return "\n".join(error_lines)


def parse_json_file(file_path: str | Path) -> dict[str, Any]:
    """
    Parse JSON file with detailed error reporting.

    Args:
        file_path: Path to JSON file

    Returns:
        Parsed JSON data as dictionary

    Raises:
        JSONParsingError: If JSON parsing fails with file location details
        FileNotFoundError: If file does not exist

    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"JSON file not found: {file_path}")

    try:
        with open(file_path, encoding="utf-8") as f:
            result: dict[str, Any] = json.load(f)
            return result
    except json.JSONDecodeError as e:
        # Log sanitized error (no file contents)
        logger.error(
            "JSON parsing failed",
            extra={
                "file_path": str(file_path),
                "line_number": e.lineno,
                "column": e.colno,
                "error_type": type(e).__name__,
            },
        )
        raise JSONParsingError(
            file_path=str(file_path),
            line_number=e.lineno,
            column=e.colno,
            message=e.msg,
        ) from e
    except Exception as e:
        logger.error(
            "Unexpected error reading JSON file",
            extra={
                "file_path": str(file_path),
                "error_type": type(e).__name__,
            },
        )
        raise


def parse_json_string(json_str: str, source_name: str = "string") -> dict[str, Any]:
    """
    Parse JSON string with detailed error reporting.

    Args:
        json_str: JSON string to parse
        source_name: Name of source for error reporting

    Returns:
        Parsed JSON data as dictionary

    Raises:
        JSONParsingError: If JSON parsing fails with location details

    """
    try:
        result: dict[str, Any] = json.loads(json_str)
        return result
    except json.JSONDecodeError as e:
        # Log sanitized error (no JSON contents)
        logger.error(
            "JSON parsing failed",
            extra={
                "source": source_name,
                "line_number": e.lineno,
                "column": e.colno,
                "error_type": type(e).__name__,
            },
        )
        raise JSONParsingError(
            file_path=source_name,
            line_number=e.lineno,
            column=e.colno,
            message=e.msg,
        ) from e


def validate_schema(data: dict[str, Any], schema_class: type, schema_name: str | None = None) -> Any:
    """
    Validate data against Pydantic schema with detailed error reporting.

    Args:
        data: Data to validate
        schema_class: Pydantic model class
        schema_name: Optional schema name for error reporting

    Returns:
        Validated Pydantic model instance

    Raises:
        SchemaValidationError: If validation fails with field-level details

    """
    schema_name = schema_name or schema_class.__name__

    try:
        return schema_class.model_validate(data)
    except ValidationError as e:
        # Extract field-level errors and convert ErrorDetails to dict
        errors: list[dict[str, Any]] = [dict(err) for err in e.errors()]

        # Log sanitized error (no data values)
        logger.error(
            "Schema validation failed",
            extra={
                "schema": schema_name,
                "error_count": len(errors),
                "field_errors": [
                    {
                        "field": " -> ".join(str(loc) for loc in err.get("loc", [])),
                        "type": err.get("type", "unknown"),
                    }
                    for err in errors
                ],
            },
        )

        raise SchemaValidationError(schema_name=schema_name, errors=errors) from e


def handle_missing_fields(errors: list[dict[str, Any]]) -> list[str]:
    """
    Extract list of missing required fields from validation errors.

    Args:
        errors: List of validation error dictionaries

    Returns:
        List of missing field names

    """
    missing_fields = []
    for error in errors:
        if error.get("type") == "missing":
            field_path = " -> ".join(str(loc) for loc in error.get("loc", []))
            missing_fields.append(field_path)
    return missing_fields


def handle_type_mismatches(errors: list[dict[str, Any]]) -> list[dict[str, str]]:
    """
    Extract type mismatch information from validation errors.

    Args:
        errors: List of validation error dictionaries

    Returns:
        List of dictionaries with field, expected type, and error message

    """
    type_errors = []
    for error in errors:
        error_type = error.get("type", "")
        if "type" in error_type or error_type in ["int_parsing", "float_parsing", "bool_parsing"]:
            field_path = " -> ".join(str(loc) for loc in error.get("loc", []))
            type_errors.append(
                {
                    "field": field_path,
                    "error_type": error_type,
                    "message": error.get("msg", "Type mismatch"),
                }
            )
    return type_errors


def format_validation_summary(errors: list[dict[str, Any]]) -> str:
    """
    Format validation errors into human-readable summary.

    Args:
        errors: List of validation error dictionaries

    Returns:
        Formatted error summary string

    """
    missing = handle_missing_fields(errors)
    type_errors = handle_type_mismatches(errors)

    summary_lines = []

    if missing:
        summary_lines.append("Missing required fields:")
        for field in missing:
            summary_lines.append(f"  • {field}")

    if type_errors:
        if summary_lines:
            summary_lines.append("")
        summary_lines.append("Type mismatches:")
        for error in type_errors:
            summary_lines.append(f"  • {error['field']}: {error['message']}")

    other_errors = [e for e in errors if e.get("type") not in ["missing"] and "type" not in e.get("type", "")]
    if other_errors:
        if summary_lines:
            summary_lines.append("")
        summary_lines.append("Other validation errors:")
        for error in other_errors:
            field_path = " -> ".join(str(loc) for loc in error.get("loc", []))
            summary_lines.append(f"  • {field_path}: {error.get('msg', 'Validation failed')}")

    return "\n".join(summary_lines)
