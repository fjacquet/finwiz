"""
Validation management for crew data integration.

Handles validation of crew outputs against expected schemas and stores validation results.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class ValidationResult(BaseModel):
    """Result of data validation."""

    is_valid: bool
    validation_timestamp: datetime
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ValidationManager:
    """
    Manager for crew output validation.

    Handles validation of crew outputs against expected schemas and stores validation results.
    """

    def __init__(self, metadata_dir: Path, logger: logging.Logger) -> None:
        """
        Initialize the validation manager.

        Args:
            metadata_dir: Directory for storing validation metadata
            logger: Logger instance for validation operations

        """
        self.metadata_dir = metadata_dir
        self.logger = logger
        self.validation_status_path = self.metadata_dir / "validation_status.json"

    def validate_crew_output(self, crew_name: str, output_data: dict[str, Any]) -> ValidationResult:
        """
        Validate crew output against expected schema.

        Args:
            crew_name: Name of the crew
            output_data: Output data to validate

        Returns:
            ValidationResult with validation status and details

        """
        self.logger.info(f"Validating output for crew: {crew_name}")

        try:
            # Basic validation - would be enhanced with actual schema validation
            errors = []
            warnings = []

            if not output_data:
                errors.append("Output data is empty")

            if not isinstance(output_data, dict):
                errors.append("Output data must be a dictionary")

            # Check for required metadata fields
            if "metadata" not in output_data:
                warnings.append("Missing metadata field")

            # Validate crew-specific requirements
            if crew_name in ["stock", "etf", "crypto"]:
                # Core analysis crews should have raw_output or analysis content
                if not output_data.get("raw_output") and not output_data.get("tasks_output"):
                    warnings.append(f"No analysis content found for {crew_name} crew")

            is_valid = len(errors) == 0

            result = ValidationResult(is_valid=is_valid, validation_timestamp=datetime.now(), errors=errors, warnings=warnings)

            # Store validation result
            self._store_validation_result(crew_name, result)

            self.logger.info(
                f"Validation completed for crew {crew_name}",
                extra={"is_valid": is_valid, "error_count": len(errors), "warning_count": len(warnings)},
            )

            return result

        except Exception as e:
            error_msg = f"Validation failed for crew {crew_name}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)

            return ValidationResult(is_valid=False, validation_timestamp=datetime.now(), errors=[error_msg], warnings=[])

    def _store_validation_result(self, crew_name: str, result: ValidationResult) -> None:
        """Store validation result to metadata."""
        try:
            from finwiz.integration.schema import SchemaManager

            schema_manager = SchemaManager(self.logger)
            validation_status = schema_manager.load_json_file(self.validation_status_path, {})

            validation_status[crew_name] = {
                "is_valid": result.is_valid,
                "validation_timestamp": result.validation_timestamp.isoformat(),
                "errors": result.errors,
                "warnings": result.warnings,
            }

            schema_manager.save_json_file(self.validation_status_path, validation_status)

        except Exception as e:
            self.logger.warning(f"Failed to store validation result for {crew_name}: {str(e)}")
