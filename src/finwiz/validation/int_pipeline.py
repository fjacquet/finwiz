"""
Centralized Data Validation Pipeline.

This module provides comprehensive validation for crew data integration,
including schema validation, cross-crew consistency checking, and error reporting.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from pydantic import BaseModel

from finwiz.schemas.integration import CryptoCrewOutput, DiscoveryCrewOutput, ETFCrewOutput, StockCrewOutput
from finwiz.validation.enums import ValidationMode
from finwiz.validation.manager import ValidationManager, get_validation_manager
from finwiz.validation.result import ValidationResult as BaseValidationResult

from .pipeline_stages import PipelineStages, ValidationPipelineResult
from .rules import ValidationRules


class ValidationPipeline:
    """
    Centralized validation pipeline for crew data integration.

    This class provides comprehensive validation including:
    - Schema validation using Pydantic models
    - Cross-crew data consistency checking
    - Validation error collection and reporting
    - Integration with existing validation infrastructure
    """

    def __init__(
        self,
        output_dir: Path = Path("output"),
        validation_manager: ValidationManager | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """
        Initialize the validation pipeline.

        Args:
            output_dir: Base directory for crew outputs
            validation_manager: Optional validation manager instance
            logger: Optional logger instance

        """
        self.output_dir = Path(output_dir)
        self.validation_manager = validation_manager or get_validation_manager()
        self.logger = logger or self._setup_logging()

        # Schema mapping for crew outputs
        self.crew_schema_mapping = {
            "stock": StockCrewOutput,
            "etf": ETFCrewOutput,
            "crypto": CryptoCrewOutput,
            "discovery": DiscoveryCrewOutput,
        }

        # Initialize pipeline stages and validation rules
        self.pipeline_stages = PipelineStages(output_dir=self.output_dir, crew_schema_mapping=cast(dict[str, type[BaseModel]], self.crew_schema_mapping), logger=self.logger)
        self.validation_rules = ValidationRules(logger=self.logger)

        self.logger.info(
            "ValidationPipeline initialized",
            extra={"output_dir": str(self.output_dir), "available_schemas": list(self.crew_schema_mapping.keys())},
        )

    def _setup_logging(self) -> logging.Logger:
        """Set up structured logging for validation pipeline."""
        logger = logging.getLogger("finwiz.integration.validation")

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)

        return logger

    def validate_all_crew_outputs(self, max_age_hours: int = 24, strict_mode: bool = False) -> ValidationPipelineResult:
        """
        Validate all available crew outputs with comprehensive checking.

        Args:
            max_age_hours: Maximum acceptable age for data freshness
            strict_mode: Whether to use strict validation mode

        Returns:
            ValidationPipelineResult with comprehensive validation results

        """
        start_time = datetime.now()
        self.logger.info("Starting comprehensive crew output validation", extra={"max_age_hours": max_age_hours, "strict_mode": strict_mode})

        # Set validation mode
        original_mode = self.validation_manager.get_strictness_mode()
        if strict_mode:
            self.validation_manager.set_strictness_mode(ValidationMode.ERROR)

        try:
            from .pipeline_stages import CrossCrewValidationResult

            result = ValidationPipelineResult(
                overall_valid=True,
                validation_timestamp=start_time,
                cross_crew_validation=CrossCrewValidationResult(is_consistent=True, validation_timestamp=start_time),
            )

            # Execute pipeline stages
            crew_data = {}

            # Stage 1: Individual crew validation
            self.pipeline_stages.execute_individual_crew_validation(result, crew_data)

            # Stage 2: Cross-crew consistency validation
            self.pipeline_stages.execute_cross_crew_validation(result, crew_data)

            # Stage 3: SEC citation validation
            self.pipeline_stages.execute_sec_citation_validation(result, crew_data)

            # Stage 4: Generate summary
            self.pipeline_stages.execute_summary_generation(result, start_time)

            return result

        finally:
            # Restore original validation mode
            self.validation_manager.set_strictness_mode(original_mode)

    def validate_crew_output(self, crew_name: str, output_data: dict[str, Any], validate_metadata: bool = True) -> BaseValidationResult:
        """
        Validate a single crew's output against its schema.

        Args:
            crew_name: Name of the crew
            output_data: Output data to validate
            validate_metadata: Whether to validate metadata fields

        Returns:
            ValidationResult with validation status and details

        """
        self.logger.info(f"Validating output for {crew_name} crew")

        try:
            # Get appropriate schema
            schema_class = self.crew_schema_mapping.get(crew_name)
            if not schema_class:
                result = BaseValidationResult(is_valid=False)
                result.add_error(
                    field_path="schema",
                    error_type="schema_not_found",
                    message=f"No schema found for crew: {crew_name}",
                    context={"crew_name": crew_name, "available_schemas": list(self.crew_schema_mapping.keys())},
                )
                return result

            # Validate using the schema
            result = self.validation_rules.validate_with_pydantic_schema(output_data, cast(type[BaseModel], schema_class))

            # Additional metadata validation if requested
            if validate_metadata and result.is_valid and result.sanitized_data:
                metadata_result = self.validation_rules.validate_crew_metadata(result.sanitized_data.get("metadata"))
                if not metadata_result.is_valid:
                    result.errors.extend(metadata_result.errors)
                    result.warnings.extend(metadata_result.warnings)
                    result.is_valid = False

            self.logger.info(
                f"Validation completed for {crew_name} crew",
                extra={"is_valid": result.is_valid, "error_count": len(result.errors), "warning_count": len(result.warnings)},
            )

            return result

        except Exception as e:
            error_msg = f"Validation failed for {crew_name} crew: {str(e)}"
            self.logger.error(error_msg, exc_info=True)

            result = BaseValidationResult(is_valid=False)
            result.add_error(
                field_path="validation",
                error_type="unexpected_error",
                message=error_msg,
                context={"crew_name": crew_name, "exception_type": type(e).__name__},
            )
            return result

    def validate_cross_crew_consistency(self, crew_outputs: dict[str, dict[str, Any]]) -> Any:
        """
        Validate consistency across multiple crew outputs.

        Args:
            crew_outputs: Dictionary mapping crew names to their output data

        Returns:
            CrossCrewValidationResult with consistency validation results

        """
        self.logger.info("Validating cross-crew data consistency", extra={"crew_count": len(crew_outputs), "crews": list(crew_outputs.keys())})

        return self.pipeline_stages._validate_cross_crew_consistency(crew_outputs)

    def validate_sec_citations(self, crew_outputs: dict[str, dict[str, Any]], consolidate_for_report: bool = True) -> dict[str, Any]:
        """
        Validate SEC citations across all crew outputs.

        Args:
            crew_outputs: Dictionary mapping crew names to their output data
            consolidate_for_report: Whether to consolidate citations for report integration

        Returns:
            Dictionary containing SEC citation validation results

        """
        return self.pipeline_stages.validate_sec_citations(crew_outputs, consolidate_for_report)

    def generate_validation_report(self, validation_result: ValidationPipelineResult, output_path: Path | None = None) -> dict[str, Any]:
        """
        Generate a comprehensive validation report.

        Args:
            validation_result: Result from validation pipeline
            output_path: Optional path to save the report

        Returns:
            Dictionary containing the validation report

        """
        return self.pipeline_stages.generate_validation_report(validation_result, output_path)
