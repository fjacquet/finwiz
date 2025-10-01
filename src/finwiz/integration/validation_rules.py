"""
Validation Rules for Crew Data Integration.

This module contains validation logic and rules for validating crew outputs,
including schema validation, cross-crew consistency checking, and metadata validation.
"""

import logging
from typing import Any

from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError

from ..schemas.integration import CrewOutputMetadata
from ..validation.result import ValidationResult as BaseValidationResult


class ValidationRules:
    """
    Validation rules and logic for crew data integration.

    This class contains all the validation logic that can be applied
    to crew outputs, including schema validation, metadata validation,
    and cross-crew consistency checks.
    """

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """
        Initialize validation rules.

        Args:
            logger: Optional logger instance

        """
        self.logger = logger or logging.getLogger("finwiz.integration.validation_rules")

    def validate_with_pydantic_schema(self, data: dict[str, Any], schema_class: type[BaseModel]) -> BaseValidationResult:
        """
        Validate data against a Pydantic schema.

        Args:
            data: Data to validate
            schema_class: Pydantic model class to validate against

        Returns:
            ValidationResult with validation status and details

        """
        result = BaseValidationResult(is_valid=True)

        try:
            # Attempt validation
            validated_model = schema_class.model_validate(data)
            result.sanitized_data = validated_model.model_dump()

            self.logger.debug(f"Schema validation successful for {schema_class.__name__}")

        except PydanticValidationError as e:
            # Convert Pydantic errors to our format
            for error in e.errors():
                field_path = ".".join(str(loc) for loc in error["loc"])
                result.add_error(
                    field_path=field_path,
                    error_type=error["type"],
                    message=error["msg"],
                    input_value=error.get("input"),
                    context={"schema": schema_class.__name__},
                )

            self.logger.error(f"Schema validation failed for {schema_class.__name__}", extra={"error_count": len(result.errors)})

        except Exception as e:
            result.add_error(
                field_path="validation",
                error_type="unexpected_error",
                message=f"Unexpected validation error: {str(e)}",
                context={"schema": schema_class.__name__, "exception_type": type(e).__name__},
            )
            self.logger.exception(f"Unexpected validation error for {schema_class.__name__}")

        return result

    def validate_crew_metadata(self, metadata: dict[str, Any] | None) -> BaseValidationResult:
        """
        Validate crew output metadata.

        Args:
            metadata: Metadata dictionary to validate

        Returns:
            ValidationResult with validation status and details

        """
        result = BaseValidationResult(is_valid=True)

        if not metadata:
            result.add_error(field_path="metadata", error_type="missing_field", message="Metadata is required but not provided")
            return result

        try:
            # Validate metadata against CrewOutputMetadata schema
            CrewOutputMetadata.model_validate(metadata)

        except PydanticValidationError as e:
            for error in e.errors():
                field_path = f"metadata.{'.'.join(str(loc) for loc in error['loc'])}"
                result.add_error(
                    field_path=field_path, error_type=error["type"], message=error["msg"], input_value=error.get("input")
                )

        return result

    def extract_all_validated_tickers(self, crew_outputs: dict[str, dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        """
        Extract all validated tickers from crew outputs.

        Args:
            crew_outputs: Dictionary mapping crew names to their output data

        Returns:
            Dictionary mapping crew names to their validated tickers

        """
        all_tickers = {}

        for crew_name, output in crew_outputs.items():
            tickers = []

            # Extract tickers based on crew type
            if crew_name == "stock" and "validated_tickers" in output:
                tickers = output["validated_tickers"]
            elif crew_name == "etf" and "validated_etfs" in output:
                tickers = output["validated_etfs"]
            elif crew_name == "crypto" and "validated_symbols" in output:
                tickers = output["validated_symbols"]

            if tickers:
                all_tickers[crew_name] = tickers

        return all_tickers

    def find_ticker_validation_conflicts(self, all_tickers: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
        """
        Find conflicts in ticker validation across crews.

        Args:
            all_tickers: Dictionary mapping crew names to their validated tickers

        Returns:
            List of ticker validation conflicts

        """
        conflicts = []

        # Build a map of ticker -> validation results
        ticker_validations = {}

        for crew_name, tickers in all_tickers.items():
            for ticker_data in tickers:
                symbol = ticker_data.get("symbol", "").upper()
                if not symbol:
                    continue

                if symbol not in ticker_validations:
                    ticker_validations[symbol] = []

                ticker_validations[symbol].append(
                    {
                        "crew": crew_name,
                        "is_valid": ticker_data.get("is_valid", False),
                        "validation_source": ticker_data.get("validation_source", "unknown"),
                        "validation_timestamp": ticker_data.get("validation_timestamp"),
                        "validation_errors": ticker_data.get("validation_errors", []),
                    }
                )

        # Check for conflicts
        for symbol, validations in ticker_validations.items():
            if len(validations) > 1:
                # Check if there are conflicting validation results
                valid_results = [v["is_valid"] for v in validations]
                if not all(valid_results) and any(valid_results):
                    # Some crews say valid, others say invalid
                    conflicts.append(
                        {
                            "ticker": symbol,
                            "conflict_type": "validation_disagreement",
                            "conflict_description": "Crews disagree on validation status",
                            "validations": validations,
                        }
                    )

        return conflicts

    def find_data_value_conflicts(self, crew_outputs: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Find conflicts in data values across crews.

        Args:
            crew_outputs: Dictionary mapping crew names to their output data

        Returns:
            List of data value conflicts

        """
        conflicts = []

        # This is a simplified implementation - could be expanded
        # to check for specific data conflicts like risk scores, etc.

        # Check for timestamp consistency
        timestamps = {}
        for crew_name, output in crew_outputs.items():
            metadata = output.get("metadata", {})
            execution_timestamp = metadata.get("execution_timestamp")
            if execution_timestamp:
                timestamps[crew_name] = execution_timestamp

        if len(timestamps) > 1:
            # Check if timestamps are significantly different (more than 1 hour)
            list(timestamps.values())
            # This would need proper datetime parsing and comparison
            # For now, just log the information
            pass

        return conflicts

    def check_metadata_consistency(self, crew_outputs: dict[str, dict[str, Any]]) -> list[str]:
        """
        Check for metadata consistency issues.

        Args:
            crew_outputs: Dictionary mapping crew names to their output data

        Returns:
            List of consistency issues found

        """
        issues = []

        # Check schema versions
        schema_versions = {}
        for crew_name, output in crew_outputs.items():
            metadata = output.get("metadata", {})
            schema_version = metadata.get("schema_version", 1)
            schema_versions[crew_name] = schema_version

        if len(set(schema_versions.values())) > 1:
            issues.append(f"Schema version mismatch across crews: {schema_versions}")

        # Check for missing dependencies
        for crew_name, output in crew_outputs.items():
            metadata = output.get("metadata", {})
            dependencies_met = metadata.get("dependencies_met", True)
            if not dependencies_met:
                issues.append(f"Crew {crew_name} reports unmet dependencies")

        return issues

    def validate_crew_schema(
        self, crew_name: str, data: dict[str, Any], crew_schema_mapping: dict[str, type[BaseModel]]
    ) -> BaseValidationResult:
        """
        Validate crew data against its schema.

        Args:
            crew_name: Name of the crew
            data: Data to validate
            crew_schema_mapping: Mapping of crew names to schema classes

        Returns:
            ValidationResult with validation status and details

        """
        schema_class = crew_schema_mapping.get(crew_name)
        if not schema_class:
            result = BaseValidationResult(is_valid=False)
            result.add_error(field_path="schema", error_type="schema_not_found", message=f"No schema found for crew: {crew_name}")
            return result

        return self.validate_with_pydantic_schema(data, schema_class)
