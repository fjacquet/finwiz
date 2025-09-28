"""
Crew Data Integration Manager.

Central manager for crew data integration and coordination.
Handles data flow between crews and ensures proper data accessibility.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from .freshness_checker import DataFreshnessChecker


class ExecutionResult(BaseModel):
    """Result of crew execution coordination."""

    success: bool
    executed_crews: list[str] = Field(default_factory=list)
    failed_crews: list[str] = Field(default_factory=list)
    execution_time: float
    errors: list[str] = Field(default_factory=list)


class ValidationResult(BaseModel):
    """Result of data validation."""

    is_valid: bool
    validation_timestamp: datetime
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class FreshnessReport(BaseModel):
    """Report on data freshness across crews."""

    fresh_data: list[str] = Field(default_factory=list)
    stale_data: list[str] = Field(default_factory=list)
    missing_data: list[str] = Field(default_factory=list)
    overall_status: str = Field(default="UNKNOWN")
    check_timestamp: datetime


class CrewConfig(BaseModel):
    """Configuration for crew execution."""

    name: str
    dependencies: list[str] = Field(default_factory=list)
    output_schema: str | None = None
    max_age_hours: int = 24


class UpstreamDataCollection(BaseModel):
    """Collection of upstream data available to a crew."""

    available_data: dict[str, Any] = Field(default_factory=dict)
    missing_data: list[str] = Field(default_factory=list)
    stale_data: list[str] = Field(default_factory=list)


class CrewDataIntegrationManager:
    """
    Central manager for crew data integration and coordination.

    This class orchestrates data flow between crews, validates outputs,
    and ensures proper data accessibility for downstream crews.
    """

    def __init__(self, output_dir: Path = Path("output"), config_path: Path | None = None) -> None:
        """
        Initialize the integration manager.

        Args:
            output_dir: Base directory for all crew outputs
            config_path: Path to configuration file (optional)

        """
        # Load configuration
        from .config import load_integration_config

        self.config = load_integration_config(config_path)

        # Use configured output directory if not explicitly provided
        if output_dir == Path("output") and self.config.output_dir != Path("output"):
            self.output_dir = self.config.output_dir
        else:
            self.output_dir = Path(output_dir)

        self.integration_dir = self.output_dir / self.config.integration_dir_name
        self.metadata_dir = self.integration_dir / self.config.metadata_dir_name
        self.contracts_dir = self.integration_dir / self.config.contracts_dir_name
        self.consolidated_dir = self.integration_dir / self.config.consolidated_dir_name

        # Set up logging
        self.logger = self._setup_logging()

        # Ensure directories exist
        self._ensure_directories()

        # Initialize freshness checker
        self.freshness_checker = DataFreshnessChecker(output_dir=self.output_dir, logger=self.logger)

        # Initialize execution tracking
        self.execution_log_path = self.metadata_dir / "crew_execution_log.json"
        self.data_lineage_path = self.metadata_dir / "data_lineage.json"
        self.validation_status_path = self.metadata_dir / "validation_status.json"

        self.logger.info(
            "CrewDataIntegrationManager initialized",
            extra={
                "output_dir": str(self.output_dir),
                "integration_dir": str(self.integration_dir),
                "config_loaded": config_path is not None,
                "strict_validation": self.config.strict_validation,
            },
        )

    def _setup_logging(self) -> logging.Logger:
        """Set up structured logging for integration operations."""
        logger = logging.getLogger("finwiz.integration")

        if not logger.handlers:
            # Create handler if it doesn't exist
            handler = logging.StreamHandler()

            # Use configured log format
            formatter = logging.Formatter(self.config.log_format)
            handler.setFormatter(formatter)
            logger.addHandler(handler)

            # Set configured log level
            log_level = getattr(logging, self.config.log_level.upper(), logging.INFO)
            logger.setLevel(log_level)

        return logger

    def _ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        directories = [self.integration_dir, self.metadata_dir, self.contracts_dir, self.consolidated_dir]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"Ensured directory exists: {directory}")

    async def coordinate_crew_execution(self, crews: list[CrewConfig]) -> ExecutionResult:
        """
        Coordinate execution of multiple crews based on dependencies.

        Args:
            crews: List of crew configurations to execute

        Returns:
            ExecutionResult with success status and execution details

        """
        start_time = datetime.now()
        executed_crews = []
        failed_crews = []
        errors = []

        self.logger.info(
            "Starting crew execution coordination", extra={"crew_count": len(crews), "crews": [crew.name for crew in crews]}
        )

        try:
            # Sort crews by dependencies (simplified - would need topological sort for complex deps)
            sorted_crews = self._sort_crews_by_dependencies(crews)

            for crew in sorted_crews:
                try:
                    self.logger.info(f"Coordinating execution for crew: {crew.name}")

                    # Check dependencies
                    deps_result = self._check_dependencies(crew)
                    if not deps_result:
                        error_msg = f"Dependencies not met for crew {crew.name}"
                        errors.append(error_msg)
                        failed_crews.append(crew.name)
                        self.logger.error(error_msg)
                        continue

                    # Log execution start
                    self._log_crew_execution_start(crew.name)
                    executed_crews.append(crew.name)

                except Exception as e:
                    error_msg = f"Failed to coordinate crew {crew.name}: {str(e)}"
                    errors.append(error_msg)
                    failed_crews.append(crew.name)
                    self.logger.error(error_msg, exc_info=True)

            execution_time = (datetime.now() - start_time).total_seconds()
            success = len(failed_crews) == 0

            result = ExecutionResult(
                success=success,
                executed_crews=executed_crews,
                failed_crews=failed_crews,
                execution_time=execution_time,
                errors=errors,
            )

            self.logger.info(
                "Crew execution coordination completed",
                extra={
                    "success": success,
                    "executed_count": len(executed_crews),
                    "failed_count": len(failed_crews),
                    "execution_time": execution_time,
                },
            )

            return result

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            error_msg = f"Crew coordination failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)

            return ExecutionResult(
                success=False,
                executed_crews=executed_crews,
                failed_crews=failed_crews,
                execution_time=execution_time,
                errors=[error_msg],
            )

    def store_crew_output(self, crew_name: str, crew_output: Any) -> bool:
        """
        Store crew output to the integration system.

        Args:
            crew_name: Name of the crew (e.g., 'stock', 'etf', 'crypto')
            crew_output: The crew output object (CrewOutput or similar)

        Returns:
            True if storage was successful, False otherwise

        """
        try:
            self.logger.info(f"Storing output for crew: {crew_name}")

            # Create crew output directory
            crew_output_dir = self.output_dir / crew_name
            crew_output_dir.mkdir(parents=True, exist_ok=True)

            # Convert crew output to dictionary
            if hasattr(crew_output, "raw"):
                # CrewAI CrewOutput object
                output_data = {
                    "raw_output": str(crew_output.raw),
                    "json_dict": crew_output.json_dict if hasattr(crew_output, "json_dict") else {},
                    "pydantic": crew_output.pydantic.model_dump()
                    if hasattr(crew_output, "pydantic") and crew_output.pydantic
                    else {},
                    "tasks_output": [
                        {
                            "description": task.description if hasattr(task, "description") else str(task),
                            "summary": task.summary if hasattr(task, "summary") else "",
                            "raw": str(task.raw) if hasattr(task, "raw") else str(task),
                            "json_dict": task.json_dict if hasattr(task, "json_dict") else {},
                            "pydantic": task.pydantic.model_dump() if hasattr(task, "pydantic") and task.pydantic else {},
                        }
                        for task in (crew_output.tasks_output if hasattr(crew_output, "tasks_output") else [])
                    ],
                    "token_usage": crew_output.token_usage if hasattr(crew_output, "token_usage") else {},
                    "usage_metrics": crew_output.usage_metrics if hasattr(crew_output, "usage_metrics") else {},
                }
            elif isinstance(crew_output, dict):
                output_data = crew_output
            else:
                # Fallback for other types
                output_data = {"raw_output": str(crew_output)}

            # Add metadata
            output_data["metadata"] = {
                "crew_name": crew_name,
                "storage_timestamp": datetime.now().isoformat(),
                "integration_version": "1.0",
                "data_freshness": {
                    "stored_at": datetime.now().isoformat(),
                    "is_fresh": True,
                    "age_hours": 0.0,
                },
            }

            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = crew_output_dir / f"{crew_name}_output_{timestamp}.json"

            # Save to JSON file
            self._save_json_file(output_file, output_data)

            # Create/update latest symlink for easy access
            latest_file = crew_output_dir / f"{crew_name}_latest.json"
            if latest_file.exists():
                latest_file.unlink()

            # Create symlink to latest file (cross-platform compatible)
            try:
                latest_file.symlink_to(output_file.name)
            except (OSError, NotImplementedError):
                # Fallback: copy file if symlinks not supported
                import shutil

                shutil.copy2(output_file, latest_file)

            # Validate the stored output
            validation_result = self.validate_crew_output(crew_name, output_data)

            if validation_result.is_valid:
                self.logger.info(
                    f"Successfully stored output for crew {crew_name}",
                    extra={
                        "output_file": str(output_file),
                        "data_size": len(str(output_data)),
                        "has_tasks": len(output_data.get("tasks_output", [])),
                    },
                )
            else:
                self.logger.warning(
                    f"Stored output for crew {crew_name} with validation warnings",
                    extra={
                        "validation_errors": validation_result.errors,
                        "validation_warnings": validation_result.warnings,
                    },
                )

            return True

        except Exception as e:
            error_msg = f"Failed to store output for crew {crew_name}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return False

    def get_cached_crew_output(self, crew_name: str) -> dict[str, Any] | None:
        """
        Get cached crew output if available.

        Args:
            crew_name: Name of the crew

        Returns:
            Cached crew output data, or None if not available

        """
        try:
            crew_output_dir = self.output_dir / crew_name
            latest_file = crew_output_dir / f"{crew_name}_latest.json"

            if latest_file.exists():
                return self._load_json_file(latest_file, {})

            # Fallback: find most recent file
            output_files = list(crew_output_dir.glob(f"{crew_name}_output_*.json"))
            if output_files:
                newest_file = max(output_files, key=lambda f: f.stat().st_mtime)
                return self._load_json_file(newest_file, {})

            return None

        except Exception as e:
            self.logger.error(f"Failed to get cached output for crew {crew_name}: {str(e)}")
            return None

    def validate_crew_output(self, crew_name: str, output_data: dict) -> ValidationResult:
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

    def get_upstream_data(self, requesting_crew: str, max_age_hours: int = 24) -> UpstreamDataCollection:
        """
        Get available upstream data for a requesting crew with freshness validation.

        Args:
            requesting_crew: Name of the crew requesting data
            max_age_hours: Maximum acceptable age in hours for data freshness

        Returns:
            UpstreamDataCollection with available, missing, and stale data

        """
        self.logger.info(f"Getting upstream data for crew: {requesting_crew}")

        try:
            available_data = {}
            missing_data = []
            stale_data = []

            # Check each crew output directory
            crew_dirs = ["stock", "etf", "crypto", "discovery", "portfolio"]

            for crew_dir in crew_dirs:
                if crew_dir == requesting_crew:
                    continue  # Skip self

                crew_output_dir = self.output_dir / crew_dir
                if crew_output_dir.exists():
                    # Check for output files
                    output_files = list(crew_output_dir.glob("*.json"))
                    if output_files:
                        # Check freshness of the newest file
                        max(output_files, key=lambda f: f.stat().st_mtime)
                        freshness_result = self.freshness_checker.check_data_freshness_for_crew(crew_dir, max_age_hours)

                        if freshness_result and freshness_result.freshness_status.is_fresh:
                            available_data[crew_dir] = [str(f) for f in output_files]
                        else:
                            stale_data.append(crew_dir)
                            # Still include in available data but mark as stale
                            available_data[crew_dir] = [str(f) for f in output_files]

                            # Log stale data warning
                            age_hours = freshness_result.freshness_status.age_hours if freshness_result else float("inf")
                            self.logger.warning(
                                f"Stale data detected for {crew_dir} crew (age: {age_hours:.1f}h > {max_age_hours}h)"
                            )
                    else:
                        missing_data.append(crew_dir)
                else:
                    missing_data.append(crew_dir)

            result = UpstreamDataCollection(available_data=available_data, missing_data=missing_data, stale_data=stale_data)

            self.logger.info(
                f"Upstream data collection completed for {requesting_crew}",
                extra={"available_crews": len(available_data), "missing_crews": len(missing_data), "stale_crews": len(stale_data)},
            )

            return result

        except Exception as e:
            error_msg = f"Failed to get upstream data for {requesting_crew}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)

            return UpstreamDataCollection(available_data={}, missing_data=crew_dirs, stale_data=[])

    def get_crew_data_with_freshness_check(
        self, crew_name: str, max_age_hours: int = 24, warn_on_stale: bool = True
    ) -> dict | None:
        """
        Get crew data with automatic freshness validation and warnings.

        Args:
            crew_name: Name of the crew whose data to retrieve
            max_age_hours: Maximum acceptable age in hours
            warn_on_stale: Whether to log warnings for stale data

        Returns:
            Dictionary containing crew data, or None if not available

        """
        try:
            crew_output_dir = self.output_dir / crew_name

            if not crew_output_dir.exists():
                self.logger.warning(f"No output directory found for {crew_name} crew")
                return None

            # Find JSON files in crew directory
            output_files = list(crew_output_dir.glob("*.json"))
            if not output_files:
                self.logger.warning(f"No output files found for {crew_name} crew")
                return None

            # Get the newest file
            newest_file = max(output_files, key=lambda f: f.stat().st_mtime)

            # Check freshness
            freshness_result = self.freshness_checker.check_data_freshness_for_crew(crew_name, max_age_hours)

            if freshness_result:
                if not freshness_result.freshness_status.is_fresh and warn_on_stale:
                    age_hours = freshness_result.freshness_status.age_hours
                    self.logger.warning(
                        f"Using stale data for {crew_name} crew",
                        extra={
                            "crew_name": crew_name,
                            "age_hours": age_hours,
                            "max_age_hours": max_age_hours,
                            "file_path": str(newest_file),
                        },
                    )
                elif freshness_result.freshness_status.refresh_recommended and warn_on_stale:
                    age_hours = freshness_result.freshness_status.age_hours
                    self.logger.info(
                        f"Data refresh recommended for {crew_name} crew",
                        extra={"crew_name": crew_name, "age_hours": age_hours, "max_age_hours": max_age_hours},
                    )

            # Load and return the data
            with open(newest_file, encoding="utf-8") as f:
                data = json.load(f)

            self.logger.debug(f"Successfully loaded data for {crew_name} crew from {newest_file}")
            return data

        except Exception as e:
            error_msg = f"Failed to get data for {crew_name} crew: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return None

    def get_refresh_recommendations(self, max_age_hours: int = 24) -> list[str]:
        """
        Get list of crews that should be refreshed based on data staleness.

        Args:
            max_age_hours: Maximum acceptable age in hours

        Returns:
            List of crew names in recommended refresh order

        """
        try:
            return self.freshness_checker.recommend_refresh_order(max_age_hours)
        except Exception as e:
            self.logger.error(f"Failed to get refresh recommendations: {str(e)}", exc_info=True)
            return []

    def check_data_freshness(self, max_age_hours: int = 24) -> list[dict[str, Any]]:
        """
        Check freshness of all crew data using the DataFreshnessChecker.

        Args:
            max_age_hours: Maximum age in hours before data is considered stale

        Returns:
            FreshnessReport with freshness status

        """
        self.logger.info(f"Checking data freshness with max age: {max_age_hours} hours")

        try:
            return self.freshness_checker.generate_freshness_report(max_age_hours)
        except Exception as e:
            error_msg = f"Data freshness check failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)

            # Import here to avoid circular imports
            from .freshness_checker import FreshnessReport

            return FreshnessReport(
                fresh_data=[],
                stale_data=[],
                missing_data=["stock", "etf", "crypto", "discovery", "portfolio"],
                overall_status="ERROR",
                check_timestamp=datetime.now(),
                recommendations=["Fix data freshness checker and retry"],
            )

    def _sort_crews_by_dependencies(self, crews: list[CrewConfig]) -> list[CrewConfig]:
        """Sort crews by their dependencies (simplified implementation)."""
        # Simple sorting - crews with no dependencies first
        no_deps = [crew for crew in crews if not crew.dependencies]
        with_deps = [crew for crew in crews if crew.dependencies]
        return no_deps + with_deps

    def _check_dependencies(self, crew: CrewConfig) -> bool:
        """Check if crew dependencies are satisfied."""
        if not crew.dependencies:
            return True

        # Check if dependency outputs exist
        for dep in crew.dependencies:
            dep_dir = self.output_dir / dep
            if not dep_dir.exists() or not list(dep_dir.glob("*.json")):
                return False

        return True

    def _log_crew_execution_start(self, crew_name: str) -> None:
        """Log the start of crew execution."""
        try:
            execution_log = self._load_json_file(self.execution_log_path, {})

            if "executions" not in execution_log:
                execution_log["executions"] = []

            execution_log["executions"].append(
                {"crew_name": crew_name, "start_time": datetime.now().isoformat(), "status": "STARTED"}
            )

            self._save_json_file(self.execution_log_path, execution_log)

        except Exception as e:
            self.logger.warning(f"Failed to log execution start for {crew_name}: {str(e)}")

    def _store_validation_result(self, crew_name: str, result: ValidationResult) -> None:
        """Store validation result to metadata."""
        try:
            validation_status = self._load_json_file(self.validation_status_path, {})

            validation_status[crew_name] = {
                "is_valid": result.is_valid,
                "validation_timestamp": result.validation_timestamp.isoformat(),
                "errors": result.errors,
                "warnings": result.warnings,
            }

            self._save_json_file(self.validation_status_path, validation_status)

        except Exception as e:
            self.logger.warning(f"Failed to store validation result for {crew_name}: {str(e)}")

    def _load_json_file(self, file_path: Path, default: dict) -> dict:
        """Load JSON file with default fallback."""
        try:
            if file_path.exists():
                with open(file_path, encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning(f"Failed to load JSON file {file_path}: {str(e)}")

        return default

    def _save_json_file(self, file_path: Path, data: dict) -> None:
        """Save data to JSON file."""
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
