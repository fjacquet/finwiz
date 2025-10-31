"""ValidationManager for centralized validation orchestration."""

from __future__ import annotations

import logging
import os
from typing import Any

from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError

from .contract_validator import ContractValidator
from .enums import ValidationMode
from .registry import SchemaRegistry, get_registry
from .result import ValidationResult

logger = logging.getLogger(__name__)


class ValidationManager:
    """
    Central validation orchestrator for FinWiz.

    Manages validation modes, coordinates with schema registry,
    and provides structured error handling for all validation operations.
    """

    def __init__(self, registry: SchemaRegistry | None = None) -> None:
        """Initialize ValidationManager with optional registry."""
        self._registry = registry or get_registry()
        self._contract_validator = ContractValidator()
        self._mode = self._get_validation_mode()

    def validate_crew_output(self, data: dict[str, Any], crew_type: str, output_type: str = "analysis") -> ValidationResult:
        """
        Validate crew output data against registered schemas and contracts.

        Args:
            data: Data to validate
            crew_type: Type of crew (stock, etf, crypto, report)
            output_type: Type of output (analysis, sentiment, risk, etc.)

        Returns:
            ValidationResult with validation status and any errors/warnings

        """
        result = ValidationResult(is_valid=True)

        # First validate contract compliance
        contract_result = self._contract_validator.validate_crew_contract(data, crew_type)
        result.errors.extend(contract_result.errors)
        result.warnings.extend(contract_result.warnings)

        if contract_result.has_errors and self._mode == ValidationMode.ERROR:
            result.is_valid = False
            return result

        # Get appropriate schema
        schema_class = self._registry.get_crew_schema(crew_type, output_type)
        if not schema_class:
            result.add_warning(
                field_path="schema",
                message=f"No schema registered for {crew_type}.{output_type}",
                context={"crew_type": crew_type, "output_type": output_type},
            )
            # In warn/off mode, continue without validation
            if self._mode != ValidationMode.ERROR:
                result.sanitized_data = data
                return result
            else:
                result.add_error(
                    field_path="schema",
                    error_type="schema_not_found",
                    message=f"Required schema not found for {crew_type}.{output_type}",
                    context={"crew_type": crew_type, "output_type": output_type},
                )
                return result

        return self._validate_with_schema(data, schema_class, result)

    def validate_reporter_input(self, data: dict[str, Any]) -> ValidationResult:
        """
        Validate ReporterInput data with strict validation and contract compliance.

        Args:
            data: Data to validate against ReporterInput schema

        Returns:
            ValidationResult with validation status and any errors/warnings

        """
        result = ValidationResult(is_valid=True)

        # First validate reporter contract compliance
        contract_result = self._contract_validator.validate_reporter_contract(data)
        result.errors.extend(contract_result.errors)
        result.warnings.extend(contract_result.warnings)

        if contract_result.has_errors and self._mode == ValidationMode.ERROR:
            result.is_valid = False
            return result

        schema_class = self._registry.get_schema("ReporterInput")
        if not schema_class:
            result.add_error(
                field_path="schema",
                error_type="schema_not_found",
                message="ReporterInput schema not found in registry",
            )
            return result

        return self._validate_with_schema(data, schema_class, result)

    def validate_with_schema(self, data: dict[str, Any], schema_name: str) -> ValidationResult:
        """
        Validate data against a named schema.

        Args:
            data: Data to validate
            schema_name: Name of registered schema

        Returns:
            ValidationResult with validation status and any errors/warnings

        """
        result = ValidationResult(is_valid=True)

        schema_class = self._registry.get_schema(schema_name)
        if not schema_class:
            result.add_error(
                field_path="schema",
                error_type="schema_not_found",
                message=f"Schema '{schema_name}' not found in registry",
            )
            return result

        return self._validate_with_schema(data, schema_class, result)

    def set_strictness_mode(self, mode: ValidationMode) -> None:
        """
        Set validation strictness mode.

        Args:
            mode: Validation mode (off, warn, error)

        """
        self._mode = mode
        logger.info(f"Validation mode set to: {mode.value}")

    def get_strictness_mode(self) -> ValidationMode:
        """Get current validation strictness mode."""
        return self._mode

    def _validate_with_schema(self, data: dict[str, Any], schema_class: type[BaseModel], result: ValidationResult) -> ValidationResult:
        """
        Validate data against a Pydantic schema.

        Args:
            data: Data to validate
            schema_class: Pydantic model class
            result: ValidationResult to populate

        Returns:
            Updated ValidationResult

        """
        try:
            # Attempt validation with extra='forbid' to catch schema drift
            validated_model = schema_class.model_validate(data)
            result.sanitized_data = validated_model.model_dump()

            logger.debug(f"Validation successful for {schema_class.__name__}")

        except PydanticValidationError as e:
            # Convert Pydantic errors to our structured format
            for error in e.errors():
                field_path = ".".join(str(loc) for loc in error["loc"])
                result.add_error(
                    field_path=field_path,
                    error_type=error["type"],
                    message=error["msg"],
                    input_value=error.get("input"),
                    context={"schema": schema_class.__name__},
                )

            # Handle based on validation mode
            if self._mode == ValidationMode.OFF:
                # In off mode, ignore errors and return original data
                result.is_valid = True
                result.errors.clear()
                result.sanitized_data = data
                logger.debug(f"Validation errors ignored (mode: {self._mode.value})")

            elif self._mode == ValidationMode.WARN:
                # In warn mode, log warnings but continue
                for error in result.errors:
                    logger.warning(f"Validation warning: {error.message} at {error.field_path}")
                    result.add_warning(
                        field_path=error.field_path,
                        message=f"Validation issue: {error.message}",
                        input_value=error.input_value,
                        context=error.context,
                    )

                # Clear errors and allow processing to continue
                result.errors.clear()
                result.is_valid = True
                result.sanitized_data = data

            else:  # ERROR mode
                logger.error(f"Validation failed for {schema_class.__name__}: {len(result.errors)} errors")
                # Errors remain, is_valid stays False

        except Exception as e:
            # Handle unexpected validation errors
            result.add_error(
                field_path="validation",
                error_type="unexpected_error",
                message=f"Unexpected validation error: {str(e)}",
                context={"schema": schema_class.__name__, "exception_type": type(e).__name__},
            )
            logger.exception(f"Unexpected validation error for {schema_class.__name__}")

        return result

    def _get_validation_mode(self) -> ValidationMode:
        """Get validation mode from environment variable."""
        env_value = os.getenv("VALIDATION_STRICTNESS", "warn").strip().lower()

        try:
            return ValidationMode(env_value)
        except ValueError:
            logger.warning(f"Invalid VALIDATION_STRICTNESS value: {env_value}, defaulting to 'warn'")
            return ValidationMode.WARN


# Global validation manager instance
_manager: ValidationManager | None = None


def get_validation_manager() -> ValidationManager:
    """Get the global validation manager instance."""
    global _manager
    if _manager is None:
        _manager = ValidationManager()
    return _manager
