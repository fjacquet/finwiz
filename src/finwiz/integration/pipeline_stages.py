"""
Pipeline Stages for Validation Pipeline.

This module contains the pipeline execution stages for validating crew outputs,
including individual crew validation, cross-crew consistency validation,
and SEC citation validation.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from finwiz.schemas.integration import IntegrationError, IntegrationErrorType
from finwiz.validation.result import ValidationResult as BaseValidationResult

from .sec_citation_validator import SECCitationValidator
from .validation_rules import ValidationRules


class CrossCrewValidationResult(BaseModel):
    """Result of cross-crew data consistency validation."""

    is_consistent: bool = Field(description="Whether data is consistent across crews")
    validation_timestamp: datetime = Field(description="When validation was performed")
    consistency_errors: list[str] = Field(default_factory=list, description="List of consistency errors found")
    consistency_warnings: list[str] = Field(default_factory=list, description="List of consistency warnings")
    ticker_conflicts: list[dict[str, Any]] = Field(default_factory=list, description="Ticker validation conflicts between crews")
    data_conflicts: list[dict[str, Any]] = Field(default_factory=list, description="Data value conflicts between crews")


class ValidationPipelineResult(BaseModel):
    """Comprehensive result of validation pipeline execution."""

    overall_valid: bool = Field(description="Whether all validations passed")
    validation_timestamp: datetime = Field(description="When pipeline validation was performed")

    # Schema validation results per crew
    schema_validation_results: dict[str, BaseValidationResult] = Field(
        default_factory=dict, description="Schema validation results for each crew"
    )

    # Cross-crew consistency validation
    cross_crew_validation: CrossCrewValidationResult = Field(description="Cross-crew data consistency validation results")

    # Integration errors
    integration_errors: list[IntegrationError] = Field(default_factory=list, description="List of integration errors encountered")

    # Summary statistics
    total_errors: int = Field(default=0, description="Total number of errors")
    total_warnings: int = Field(default=0, description="Total number of warnings")
    validated_crews: list[str] = Field(default_factory=list, description="List of crews that were validated")
    failed_crews: list[str] = Field(default_factory=list, description="List of crews that failed validation")


class PipelineStages:
    """
    Pipeline execution stages for validation pipeline.

    This class contains the different stages of the validation pipeline,
    including individual crew validation, cross-crew consistency validation,
    and SEC citation validation.
    """

    def __init__(
        self,
        output_dir: Path = Path("output"),
        crew_schema_mapping: dict[str, type[BaseModel]] | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """
        Initialize pipeline stages.

        Args:
            output_dir: Base directory for crew outputs
            crew_schema_mapping: Mapping of crew names to schema classes
            logger: Optional logger instance

        """
        self.output_dir = Path(output_dir)
        self.crew_schema_mapping = crew_schema_mapping or {}
        self.logger = logger or logging.getLogger("finwiz.integration.pipeline_stages")

        # Initialize validation rules and SEC citation validator
        self.validation_rules = ValidationRules(logger=self.logger)
        self.sec_citation_validator = SECCitationValidator(logger=self.logger)

    def execute_individual_crew_validation(self, result: ValidationPipelineResult, crew_data: dict[str, dict[str, Any]]) -> None:
        """
        Execute Stage 1: Validate individual crew outputs.

        Args:
            result: ValidationPipelineResult to update
            crew_data: Dictionary to populate with loaded crew data

        """
        self.logger.info("Stage 1: Validating individual crew outputs")

        for crew_name in self.crew_schema_mapping.keys():
            try:
                self.logger.info(f"Validating {crew_name} crew output")

                # Load crew data
                data = self._load_crew_data(crew_name)
                if data is None:
                    self.logger.warning(f"No data found for {crew_name} crew")
                    result.failed_crews.append(crew_name)
                    continue

                crew_data[crew_name] = data

                # Validate schema
                schema_result = self.validation_rules.validate_crew_schema(crew_name, data, self.crew_schema_mapping)
                result.schema_validation_results[crew_name] = schema_result

                if schema_result.is_valid:
                    result.validated_crews.append(crew_name)
                    self.logger.info(f"Schema validation passed for {crew_name} crew")
                else:
                    result.failed_crews.append(crew_name)
                    result.overall_valid = False
                    self.logger.error(
                        f"Schema validation failed for {crew_name} crew",
                        extra={"error_count": len(schema_result.errors), "warning_count": len(schema_result.warnings)},
                    )

                # Collect errors and warnings
                result.total_errors += len(schema_result.errors)
                result.total_warnings += len(schema_result.warnings)

            except Exception as e:
                error_msg = f"Failed to validate {crew_name} crew: {str(e)}"
                self.logger.error(error_msg, exc_info=True)

                integration_error = IntegrationError(
                    error_type=IntegrationErrorType.VALIDATION_ERROR,
                    crew_name=crew_name,
                    error_message=error_msg,
                    timestamp=datetime.now(),
                    context={"exception_type": type(e).__name__},
                )
                result.integration_errors.append(integration_error)
                result.failed_crews.append(crew_name)
                result.overall_valid = False

    def execute_cross_crew_validation(self, result: ValidationPipelineResult, crew_data: dict[str, dict[str, Any]]) -> None:
        """
        Execute Stage 2: Cross-crew consistency validation.

        Args:
            result: ValidationPipelineResult to update
            crew_data: Dictionary containing loaded crew data

        """
        if len(crew_data) <= 1:
            self.logger.info("Skipping cross-crew validation - insufficient crew data")
            return

        self.logger.info("Stage 2: Performing cross-crew consistency validation")
        cross_crew_result = self._validate_cross_crew_consistency(crew_data)
        result.cross_crew_validation = cross_crew_result

        if not cross_crew_result.is_consistent:
            result.overall_valid = False
            result.total_errors += len(cross_crew_result.consistency_errors)
            result.total_warnings += len(cross_crew_result.consistency_warnings)

    def execute_sec_citation_validation(self, result: ValidationPipelineResult, crew_data: dict[str, dict[str, Any]]) -> None:
        """
        Execute Stage 3: SEC citation validation.

        Args:
            result: ValidationPipelineResult to update
            crew_data: Dictionary containing loaded crew data

        """
        if not crew_data:
            self.logger.info("Skipping SEC citation validation - no crew data")
            return

        self.logger.info("Stage 3: Performing SEC citation validation")
        sec_citation_results = self.validate_sec_citations(crew_data, consolidate_for_report=True)

        # Add SEC citation validation to integration errors if there are issues
        if "error" in sec_citation_results.get("validation_summary", {}):
            integration_error = IntegrationError(
                error_type=IntegrationErrorType.VALIDATION_ERROR,
                crew_name="sec_citation_validator",
                error_message=sec_citation_results["validation_summary"]["error"],
                timestamp=datetime.now(),
                context={"validation_type": "sec_citations"},
            )
            result.integration_errors.append(integration_error)

    def execute_summary_generation(self, result: ValidationPipelineResult, start_time: datetime) -> None:
        """
        Execute Stage 4: Generate summary.

        Args:
            result: ValidationPipelineResult to update
            start_time: When the validation pipeline started

        """
        execution_time = (datetime.now() - start_time).total_seconds()
        self.logger.info(
            "Stage 4: Validation pipeline completed",
            extra={
                "overall_valid": result.overall_valid,
                "validated_crews": len(result.validated_crews),
                "failed_crews": len(result.failed_crews),
                "total_errors": result.total_errors,
                "total_warnings": result.total_warnings,
                "execution_time": execution_time,
            },
        )

    def validate_sec_citations(
        self, crew_outputs: dict[str, dict[str, Any]], consolidate_for_report: bool = True
    ) -> dict[str, Any]:
        """
        Validate SEC citations across all crew outputs.

        Args:
            crew_outputs: Dictionary mapping crew names to their output data
            consolidate_for_report: Whether to consolidate citations for report integration

        Returns:
            Dictionary containing SEC citation validation results

        """
        self.logger.info(
            "Validating SEC citations across crew outputs",
            extra={"crew_count": len(crew_outputs), "consolidate_for_report": consolidate_for_report},
        )

        try:
            # Extract citations from crew outputs
            crew_citations = self.sec_citation_validator.extract_citations_from_crew_outputs(crew_outputs)

            # Validate all citations
            validation_results = {}
            for crew_name, citations in crew_citations.items():
                if citations:
                    crew_validation = self.sec_citation_validator.validate_multiple_citations(citations)
                    validation_results[crew_name] = crew_validation

            # Consolidate citations if requested
            consolidated_citations = None
            if consolidate_for_report and crew_citations:
                consolidated_citations = self.sec_citation_validator.consolidate_citations_for_report(
                    crew_citations, deduplicate=True
                )

            # Create summary
            total_citations = sum(len(citations) for citations in crew_citations.values())
            valid_citations = 0
            for crew_results in validation_results.values():
                valid_citations += sum(1 for result in crew_results.values() if result.is_valid)

            result = {
                "validation_summary": {
                    "total_citations": total_citations,
                    "valid_citations": valid_citations,
                    "invalid_citations": total_citations - valid_citations,
                    "crews_with_citations": len(crew_citations),
                    "validation_timestamp": datetime.now().isoformat(),
                },
                "crew_citations": crew_citations,
                "validation_results": validation_results,
                "consolidated_citations": consolidated_citations,
            }

            self.logger.info(
                "SEC citation validation completed",
                extra={
                    "total_citations": total_citations,
                    "valid_citations": valid_citations,
                    "crews_with_citations": len(crew_citations),
                },
            )

            return result

        except Exception as e:
            error_msg = f"SEC citation validation failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)

            return {
                "validation_summary": {
                    "error": error_msg,
                    "total_citations": 0,
                    "valid_citations": 0,
                    "validation_timestamp": datetime.now().isoformat(),
                },
                "crew_citations": {},
                "validation_results": {},
                "consolidated_citations": None,
            }

    def generate_validation_report(
        self, validation_result: ValidationPipelineResult, output_path: Path | None = None
    ) -> dict[str, Any]:
        """
        Generate a comprehensive validation report.

        Args:
            validation_result: Result from validation pipeline
            output_path: Optional path to save the report

        Returns:
            Dictionary containing the validation report

        """
        report = {
            "validation_summary": {
                "overall_valid": validation_result.overall_valid,
                "validation_timestamp": validation_result.validation_timestamp.isoformat(),
                "total_errors": validation_result.total_errors,
                "total_warnings": validation_result.total_warnings,
                "validated_crews": validation_result.validated_crews,
                "failed_crews": validation_result.failed_crews,
            },
            "schema_validation": {},
            "cross_crew_validation": {
                "is_consistent": validation_result.cross_crew_validation.is_consistent,
                "consistency_errors": validation_result.cross_crew_validation.consistency_errors,
                "consistency_warnings": validation_result.cross_crew_validation.consistency_warnings,
                "ticker_conflicts": validation_result.cross_crew_validation.ticker_conflicts,
                "data_conflicts": validation_result.cross_crew_validation.data_conflicts,
            },
            "integration_errors": [
                {
                    "error_type": error.error_type,
                    "crew_name": error.crew_name,
                    "error_message": error.error_message,
                    "timestamp": error.timestamp.isoformat(),
                    "context": error.context,
                }
                for error in validation_result.integration_errors
            ],
        }

        # Add schema validation details
        for crew_name, schema_result in validation_result.schema_validation_results.items():
            report["schema_validation"][crew_name] = {
                "is_valid": schema_result.is_valid,
                "errors": [
                    {
                        "field_path": error.field_path,
                        "error_type": error.error_type,
                        "message": error.message,
                        "input_value": error.input_value,
                        "context": error.context,
                    }
                    for error in schema_result.errors
                ],
                "warnings": [
                    {
                        "field_path": warning.field_path,
                        "error_type": warning.error_type,
                        "message": warning.message,
                        "input_value": warning.input_value,
                        "context": warning.context,
                    }
                    for warning in schema_result.warnings
                ],
            }

        # Save report if output path provided
        if output_path:
            try:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(report, f, indent=2, default=str)
                self.logger.info(f"Validation report saved to {output_path}")
            except Exception as e:
                self.logger.error(f"Failed to save validation report: {str(e)}", exc_info=True)

        return report

    def _validate_cross_crew_consistency(self, crew_outputs: dict[str, dict[str, Any]]) -> CrossCrewValidationResult:
        """Validate consistency across crew outputs."""
        result = CrossCrewValidationResult(is_consistent=True, validation_timestamp=datetime.now())

        try:
            # Extract validated tickers from all crews
            all_tickers = self.validation_rules.extract_all_validated_tickers(crew_outputs)

            # Check for ticker validation conflicts
            ticker_conflicts = self.validation_rules.find_ticker_validation_conflicts(all_tickers)
            if ticker_conflicts:
                result.ticker_conflicts = ticker_conflicts
                result.is_consistent = False
                for conflict in ticker_conflicts:
                    result.consistency_errors.append(
                        f"Ticker validation conflict for {conflict['ticker']}: {conflict['conflict_description']}"
                    )

            # Check for data value conflicts (e.g., different risk scores for same ticker)
            data_conflicts = self.validation_rules.find_data_value_conflicts(crew_outputs)
            if data_conflicts:
                result.data_conflicts = data_conflicts
                result.is_consistent = False
                for conflict in data_conflicts:
                    result.consistency_errors.append(f"Data conflict: {conflict['description']}")

            # Check metadata consistency
            metadata_issues = self.validation_rules.check_metadata_consistency(crew_outputs)
            if metadata_issues:
                result.consistency_warnings.extend(metadata_issues)

            self.logger.info(
                "Cross-crew consistency validation completed",
                extra={
                    "is_consistent": result.is_consistent,
                    "ticker_conflicts": len(result.ticker_conflicts),
                    "data_conflicts": len(result.data_conflicts),
                    "consistency_errors": len(result.consistency_errors),
                    "consistency_warnings": len(result.consistency_warnings),
                },
            )

        except Exception as e:
            error_msg = f"Cross-crew consistency validation failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            result.consistency_errors.append(error_msg)
            result.is_consistent = False

        return result

    def _load_crew_data(self, crew_name: str) -> dict[str, Any] | None:
        """Load crew data from output directory."""
        try:
            crew_output_dir = self.output_dir / crew_name

            if not crew_output_dir.exists():
                self.logger.debug(f"No output directory found for {crew_name} crew")
                return None

            # Find JSON files in crew directory
            output_files = list(crew_output_dir.glob("*.json"))
            if not output_files:
                self.logger.debug(f"No output files found for {crew_name} crew")
                return None

            # Get the newest file
            newest_file = max(output_files, key=lambda f: f.stat().st_mtime)

            # Load and return the data
            with open(newest_file, encoding="utf-8") as f:
                data = json.load(f)

            self.logger.debug(f"Successfully loaded data for {crew_name} crew from {newest_file}")
            return data

        except Exception as e:
            self.logger.error(f"Failed to load data for {crew_name} crew: {str(e)}", exc_info=True)
            return None
