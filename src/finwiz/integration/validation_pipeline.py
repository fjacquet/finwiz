"""
Centralized Data Validation Pipeline.

This module provides comprehensive validation for crew data integration,
including schema validation, cross-crew consistency checking, and error reporting.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field
from pydantic import ValidationError as PydanticValidationError

from ..schemas.integration import (
    CrewOutputMetadata,
    CryptoCrewOutput,
    DiscoveryCrewOutput,
    ETFCrewOutput,
    IntegrationError,
    IntegrationErrorType,
    StockCrewOutput,
)
from ..validation.enums import ValidationMode
from ..validation.manager import ValidationManager, get_validation_manager
from ..validation.result import ValidationResult as BaseValidationResult
from .sec_citation_validator import SECCitationValidator


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

        # Initialize SEC citation validator
        self.sec_citation_validator = SECCitationValidator(logger=self.logger)

        # Schema mapping for crew outputs
        self.crew_schema_mapping = {
            "stock": StockCrewOutput,
            "etf": ETFCrewOutput,
            "crypto": CryptoCrewOutput,
            "discovery": DiscoveryCrewOutput,
        }

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
        self.logger.info(
            "Starting comprehensive crew output validation", extra={"max_age_hours": max_age_hours, "strict_mode": strict_mode}
        )

        # Set validation mode
        original_mode = self.validation_manager.get_strictness_mode()
        if strict_mode:
            self.validation_manager.set_strictness_mode(ValidationMode.ERROR)

        try:
            result = ValidationPipelineResult(
                overall_valid=True,
                validation_timestamp=start_time,
                cross_crew_validation=CrossCrewValidationResult(is_consistent=True, validation_timestamp=start_time),
            )

            # Step 1: Validate individual crew outputs
            crew_data = {}
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
                    schema_result = self._validate_crew_schema(crew_name, data)
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

            # Step 2: Cross-crew consistency validation
            if len(crew_data) > 1:
                self.logger.info("Performing cross-crew consistency validation")
                cross_crew_result = self._validate_cross_crew_consistency(crew_data)
                result.cross_crew_validation = cross_crew_result

                if not cross_crew_result.is_consistent:
                    result.overall_valid = False
                    result.total_errors += len(cross_crew_result.consistency_errors)
                    result.total_warnings += len(cross_crew_result.consistency_warnings)

            # Step 3: SEC citation validation
            if crew_data:
                self.logger.info("Performing SEC citation validation")
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

            # Step 4: Generate summary
            execution_time = (datetime.now() - start_time).total_seconds()
            self.logger.info(
                "Validation pipeline completed",
                extra={
                    "overall_valid": result.overall_valid,
                    "validated_crews": len(result.validated_crews),
                    "failed_crews": len(result.failed_crews),
                    "total_errors": result.total_errors,
                    "total_warnings": result.total_warnings,
                    "execution_time": execution_time,
                },
            )

            return result

        finally:
            # Restore original validation mode
            self.validation_manager.set_strictness_mode(original_mode)

    def validate_crew_output(
        self, crew_name: str, output_data: dict[str, Any], validate_metadata: bool = True
    ) -> BaseValidationResult:
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
            result = self._validate_with_pydantic_schema(output_data, schema_class)

            # Additional metadata validation if requested
            if validate_metadata and result.is_valid and result.sanitized_data:
                metadata_result = self._validate_crew_metadata(result.sanitized_data.get("metadata"))
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

    def validate_cross_crew_consistency(self, crew_outputs: dict[str, dict[str, Any]]) -> CrossCrewValidationResult:
        """
        Validate consistency across multiple crew outputs.

        Args:
            crew_outputs: Dictionary mapping crew names to their output data

        Returns:
            CrossCrewValidationResult with consistency validation results

        """
        self.logger.info(
            "Validating cross-crew data consistency", extra={"crew_count": len(crew_outputs), "crews": list(crew_outputs.keys())}
        )

        return self._validate_cross_crew_consistency(crew_outputs)

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

    def _validate_crew_schema(self, crew_name: str, data: dict[str, Any]) -> BaseValidationResult:
        """Validate crew data against its schema."""
        schema_class = self.crew_schema_mapping.get(crew_name)
        if not schema_class:
            result = BaseValidationResult(is_valid=False)
            result.add_error(field_path="schema", error_type="schema_not_found", message=f"No schema found for crew: {crew_name}")
            return result

        return self._validate_with_pydantic_schema(data, schema_class)

    def _validate_with_pydantic_schema(self, data: dict[str, Any], schema_class: type[BaseModel]) -> BaseValidationResult:
        """Validate data against a Pydantic schema."""
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

    def _validate_crew_metadata(self, metadata: dict[str, Any] | None) -> BaseValidationResult:
        """Validate crew output metadata."""
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

    def _validate_cross_crew_consistency(self, crew_outputs: dict[str, dict[str, Any]]) -> CrossCrewValidationResult:
        """Validate consistency across crew outputs."""
        result = CrossCrewValidationResult(is_consistent=True, validation_timestamp=datetime.now())

        try:
            # Extract validated tickers from all crews
            all_tickers = self._extract_all_validated_tickers(crew_outputs)

            # Check for ticker validation conflicts
            ticker_conflicts = self._find_ticker_validation_conflicts(all_tickers)
            if ticker_conflicts:
                result.ticker_conflicts = ticker_conflicts
                result.is_consistent = False
                for conflict in ticker_conflicts:
                    result.consistency_errors.append(
                        f"Ticker validation conflict for {conflict['ticker']}: {conflict['conflict_description']}"
                    )

            # Check for data value conflicts (e.g., different risk scores for same ticker)
            data_conflicts = self._find_data_value_conflicts(crew_outputs)
            if data_conflicts:
                result.data_conflicts = data_conflicts
                result.is_consistent = False
                for conflict in data_conflicts:
                    result.consistency_errors.append(f"Data conflict: {conflict['description']}")

            # Check metadata consistency
            metadata_issues = self._check_metadata_consistency(crew_outputs)
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

    def _extract_all_validated_tickers(self, crew_outputs: dict[str, dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        """Extract all validated tickers from crew outputs."""
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

    def _find_ticker_validation_conflicts(self, all_tickers: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
        """Find conflicts in ticker validation across crews."""
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

    def _find_data_value_conflicts(self, crew_outputs: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
        """Find conflicts in data values across crews."""
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

    def _check_metadata_consistency(self, crew_outputs: dict[str, dict[str, Any]]) -> list[str]:
        """Check for metadata consistency issues."""
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
                "error_count": len(schema_result.errors),
                "warning_count": len(schema_result.warnings),
                "errors": [
                    {
                        "field_path": error.field_path,
                        "error_type": error.error_type,
                        "message": error.message,
                        "context": error.context,
                    }
                    for error in schema_result.errors
                ],
                "warnings": [
                    {"field_path": warning.field_path, "message": warning.message, "context": warning.context}
                    for warning in schema_result.warnings
                ],
            }

        # Save report if path provided
        if output_path:
            try:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(report, f, indent=2, ensure_ascii=False, default=str)

                self.logger.info(f"Validation report saved to {output_path}")

            except Exception as e:
                self.logger.error(f"Failed to save validation report: {str(e)}", exc_info=True)

        return report
