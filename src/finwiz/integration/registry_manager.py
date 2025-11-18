"""
Registry management for crew data integration.

Handles crew coordination, data storage, retrieval, and dependency management.
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


class RegistryManager:
    """
    Manager for crew registry and data coordination.

    Handles crew execution coordination, data storage/retrieval, and dependency management.
    """

    def __init__(self, output_dir: Path, metadata_dir: Path, freshness_checker: DataFreshnessChecker, logger: logging.Logger) -> None:
        """
        Initialize the registry manager.

        Args:
            output_dir: Base directory for crew outputs
            metadata_dir: Directory for metadata storage
            freshness_checker: Data freshness checker instance
            logger: Logger instance for registry operations

        """
        self.output_dir = output_dir
        self.metadata_dir = metadata_dir
        self.freshness_checker = freshness_checker
        self.logger = logger

        # Initialize tracking paths
        self.execution_log_path = self.metadata_dir / "crew_execution_log.json"
        self.data_lineage_path = self.metadata_dir / "data_lineage.json"

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

        self.logger.info("Starting crew execution coordination", extra={"crew_count": len(crews), "crews": [crew.name for crew in crews]})

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
            from .schema_manager import SchemaManager
            from .validation_manager import ValidationManager

            schema_manager = SchemaManager(self.logger)
            validation_manager = ValidationManager(self.metadata_dir, self.logger)

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
                    "pydantic": crew_output.pydantic.model_dump() if hasattr(crew_output, "pydantic") and crew_output.pydantic else {},
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
                    "usage_metrics": schema_manager.serialize_usage_metrics(crew_output.usage_metrics) if hasattr(crew_output, "usage_metrics") else {},
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
            schema_manager.save_json_file(output_file, output_data)

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
            validation_result = validation_manager.validate_crew_output(crew_name, output_data)

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
            from .schema_manager import SchemaManager

            schema_manager = SchemaManager(self.logger)
            crew_output_dir = self.output_dir / crew_name
            latest_file = crew_output_dir / f"{crew_name}_latest.json"

            if latest_file.exists():
                return schema_manager.load_json_file(latest_file, {})

            # Fallback: find most recent file
            output_files = list(crew_output_dir.glob(f"{crew_name}_output_*.json"))
            if output_files:
                newest_file = max(output_files, key=lambda f: f.stat().st_mtime)
                return schema_manager.load_json_file(newest_file, {})

            return None

        except Exception as e:
            self.logger.error(f"Failed to get cached output for crew {crew_name}: {str(e)}")
            return None

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
                            self.logger.warning(f"Stale data detected for {crew_dir} crew (age: {age_hours:.1f}h > {max_age_hours}h)")
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

    def get_crew_data_with_freshness_check(self, crew_name: str, max_age_hours: int = 24, warn_on_stale: bool = True) -> dict | None:
        """
        Get crew data with automatic freshness validation and warnings.

        For crew types (stock, etf, crypto), consolidates individual ticker analyses
        into crew-level summaries. For specific files, returns the individual file.

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

            # Find JSON files in crew directory with proper filtering
            # For discovery crew, only look for discovery_output_*.json files
            if crew_name == "discovery":
                output_files = list(crew_output_dir.glob("discovery_output_*.json"))
            else:
                # For other crews, get all JSON files
                output_files = list(crew_output_dir.glob("*.json"))
            
            if not output_files:
                self.logger.warning(f"No output files found for {crew_name} crew")
                return None

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
                            "file_count": len(output_files),
                        },
                    )
                elif freshness_result.freshness_status.refresh_recommended and warn_on_stale:
                    age_hours = freshness_result.freshness_status.age_hours
                    self.logger.info(
                        f"Data refresh recommended for {crew_name} crew",
                        extra={"crew_name": crew_name, "age_hours": age_hours, "max_age_hours": max_age_hours},
                    )

            # For crew types (stock, etf, crypto), consolidate individual ticker files
            if crew_name in ["stock", "etf", "crypto"]:
                return self._consolidate_crew_ticker_files(crew_name, output_files)
            else:
                # For other crew types, return the newest single file
                newest_file = max(output_files, key=lambda f: f.stat().st_mtime)
                
                # Check if file is empty before trying to parse
                if newest_file.stat().st_size == 0:
                    self.logger.warning(f"Cache file for {crew_name} crew is empty: {newest_file}")
                    return None
                
                with open(newest_file, encoding="utf-8") as f:
                    content = f.read().strip()
                    if not content:
                        self.logger.warning(f"Cache file for {crew_name} crew has no content: {newest_file}")
                        return None
                    
                    try:
                        data = json.loads(content)
                        self.logger.debug(f"Successfully loaded data for {crew_name} crew from {newest_file}")
                        return data
                    except json.JSONDecodeError as e:
                        self.logger.error(f"Invalid JSON in cache file for {crew_name} crew: {newest_file} - {e}")
                        return None

        except Exception as e:
            error_msg = f"Failed to get data for {crew_name} crew: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return None

    def _consolidate_crew_ticker_files(self, crew_name: str, output_files: list[Any]) -> dict[str, Any]:
        """
        Consolidate individual ticker analysis files into crew-level summary.

        Args:
            crew_name: Name of the crew (stock, etf, crypto)
            output_files: List of JSON files to consolidate

        Returns:
            Dictionary containing consolidated crew data with metadata

        """
        from datetime import datetime

        consolidated_data = {
            "crew_name": crew_name,  # Top-level crew_name for validator compatibility
            "execution_id": f"consolidated-{crew_name}-{int(datetime.now().timestamp())}",
            "asset_class": crew_name,
            "analysis_timestamp": datetime.now().isoformat(),
            "metadata": {
                "crew_name": crew_name,
                "consolidation_timestamp": datetime.now().isoformat(),
                "total_tickers": len(output_files),
                "consolidation_method": "ticker_aggregation",
            },
            "ticker_analyses": {},
            "summary_statistics": {
                "total_analyses": 0,
                "grade_distribution": {},
                "average_composite_score": 0.0,
                "recommendations": {"BUY": 0, "HOLD": 0, "SELL": 0},
            },
        }

        total_score = 0.0
        valid_analyses = 0

        try:
            for file_path in output_files:
                try:
                    with open(file_path, encoding="utf-8") as f:
                        ticker_data = json.load(f)

                    ticker = ticker_data.get("ticker", file_path.stem.split("_")[0])
                    consolidated_data["ticker_analyses"][ticker] = ticker_data

                    # Update summary statistics
                    if "composite_score" in ticker_data:
                        total_score += float(ticker_data["composite_score"])
                        valid_analyses += 1

                    if "grade" in ticker_data:
                        grade = ticker_data["grade"]
                        consolidated_data["summary_statistics"]["grade_distribution"][grade] = consolidated_data["summary_statistics"]["grade_distribution"].get(grade, 0) + 1

                    if "recommendation" in ticker_data:
                        rec = ticker_data["recommendation"]
                        if rec in consolidated_data["summary_statistics"]["recommendations"]:
                            consolidated_data["summary_statistics"]["recommendations"][rec] += 1

                except Exception as e:
                    self.logger.warning(f"Failed to load ticker file {file_path}: {e}")
                    continue

            # Calculate averages
            consolidated_data["summary_statistics"]["total_analyses"] = valid_analyses
            if valid_analyses > 0:
                consolidated_data["summary_statistics"]["average_composite_score"] = total_score / valid_analyses

            self.logger.info(
                f"Consolidated {crew_name} crew data: {valid_analyses} ticker analyses, avg score: {consolidated_data['summary_statistics']['average_composite_score']:.3f}"
            )

            return consolidated_data

        except Exception as e:
            self.logger.error(f"Failed to consolidate {crew_name} crew data: {e}")
            # Return minimal valid structure
            return {
                "metadata": {
                    "crew_name": crew_name,
                    "consolidation_timestamp": datetime.now().isoformat(),
                    "total_tickers": 0,
                    "consolidation_error": str(e),
                },
                "ticker_analyses": {},
                "summary_statistics": {"total_analyses": 0},
            }

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
            from .schema_manager import SchemaManager

            schema_manager = SchemaManager(self.logger)
            execution_log = schema_manager.load_json_file(self.execution_log_path, {})

            if "executions" not in execution_log:
                execution_log["executions"] = []

            execution_log["executions"].append({"crew_name": crew_name, "start_time": datetime.now().isoformat(), "status": "STARTED"})

            schema_manager.save_json_file(self.execution_log_path, execution_log)

        except Exception as e:
            self.logger.warning(f"Failed to log execution start for {crew_name}: {str(e)}")
