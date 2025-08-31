"""Validation result classes for structured error handling."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ValidationError(BaseModel):
    """Represents a validation error with context."""

    model_config = ConfigDict(extra="forbid")

    field_path: str = Field(..., description="Dot-separated path to the field that failed validation")
    error_type: str = Field(..., description="Type of validation error")
    message: str = Field(..., description="Human-readable error message")
    input_value: Any = Field(default=None, description="The value that caused the error")
    context: dict[str, Any] = Field(default_factory=dict, description="Additional error context")


class ValidationWarning(BaseModel):
    """Represents a validation warning."""

    model_config = ConfigDict(extra="forbid")

    field_path: str = Field(..., description="Dot-separated path to the field")
    message: str = Field(..., description="Human-readable warning message")
    input_value: Any = Field(default=None, description="The value that triggered the warning")
    context: dict[str, Any] = Field(default_factory=dict, description="Additional warning context")


class ValidationResult(BaseModel):
    """Result of a validation operation."""

    model_config = ConfigDict(extra="forbid")

    is_valid: bool = Field(..., description="Whether validation passed")
    errors: list[ValidationError] = Field(default_factory=list, description="Validation errors")
    warnings: list[ValidationWarning] = Field(default_factory=list, description="Validation warnings")
    sanitized_data: dict[str, Any] | None = Field(default=None, description="Cleaned/sanitized data if validation passed")

    @property
    def has_errors(self) -> bool:
        """Check if there are any validation errors."""
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        """Check if there are any validation warnings."""
        return len(self.warnings) > 0

    def add_error(
        self,
        field_path: str,
        error_type: str,
        message: str,
        input_value: Any = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Add a validation error."""
        error = ValidationError(
            field_path=field_path,
            error_type=error_type,
            message=message,
            input_value=input_value,
            context=context or {},
        )
        self.errors.append(error)
        self.is_valid = False

    def add_warning(self, field_path: str, message: str, input_value: Any = None, context: dict[str, Any] | None = None) -> None:
        """Add a validation warning."""
        warning = ValidationWarning(field_path=field_path, message=message, input_value=input_value, context=context or {})
        self.warnings.append(warning)
