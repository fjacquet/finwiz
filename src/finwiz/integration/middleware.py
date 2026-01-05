"""
Crew Integration Middleware.

Provides pre and post-execution hooks for crew coordination, dependency validation,
and data storage management.
"""

import json
import logging
from collections.abc import Awaitable, Callable
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from finwiz.schemas.integration import ValidationStatus
from finwiz.validation.int_pipeline import ValidationPipeline

from .accessor import CrewDataAccessor
from .manager import CrewConfig, CrewDataIntegrationManager, ExecutionResult


class PreExecutionResult(BaseModel):
    """Result of pre-execution validation and preparation."""

    can_proceed: bool = Field(description="Whether crew execution can proceed")
    dependencies_met: bool = Field(description="Whether all dependencies are satisfied")
    missing_dependencies: list[str] = Field(default_factory=list)
    stale_dependencies: list[str] = Field(default_factory=list)
    upstream_data: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class PostExecutionResult(BaseModel):
    """Result of post-execution processing."""

    storage_success: bool = Field(description="Whether data was stored successfully")
    validation_success: bool = Field(description="Whether validation passed")
    metadata_stored: bool = Field(description="Whether metadata was persisted")
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class CrewExecutionContext(BaseModel):
    """Context information for crew execution."""

    crew_name: str = Field(description="Name of the crew being executed")
    execution_id: str = Field(description="Unique execution identifier")
    start_time: datetime = Field(description="Execution start time")
    dependencies: list[str] = Field(default_factory=list)
    max_age_hours: int = Field(default=24, description="Maximum acceptable data age")
    upstream_data: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CrewIntegrationMiddleware:
    """
    Middleware for crew execution coordination and data integration.

    Provides pre and post-execution hooks for:
    - Dependency validation
    - Data storage and retrieval
    - Metadata persistence
    - Data lineage tracking
    """

    def __init__(
        self,
        output_dir: Path = Path("output"),
        integration_manager: CrewDataIntegrationManager | None = None,
        data_accessor: CrewDataAccessor | None = None,
        validation_pipeline: ValidationPipeline | None = None,
    ) -> None:
        """
        Initialize the middleware.

        Args:
            output_dir: Base directory for crew outputs
            integration_manager: Optional integration manager instance
            data_accessor: Optional data accessor instance
            validation_pipeline: Optional validation pipeline instance

        """
        self.output_dir = Path(output_dir)
        self.integration_dir = self.output_dir / "integration"

        # Initialize components
        self.integration_manager = integration_manager or CrewDataIntegrationManager(output_dir)
        self.data_accessor = data_accessor or CrewDataAccessor(self.integration_manager)
        self.validation_pipeline = validation_pipeline or ValidationPipeline()

        # Set up logging
        self.logger = self._setup_logging()

        # Execution tracking
        self.active_executions: dict[str, CrewExecutionContext] = {}
        self.execution_hooks: dict[str, list[Callable]] = {"pre_execution": [], "post_execution": [], "on_error": []}

        self.logger.info(
            "CrewIntegrationMiddleware initialized",
            extra={"output_dir": str(self.output_dir), "integration_dir": str(self.integration_dir)},
        )

    def _setup_logging(self) -> logging.Logger:
        """Set up structured logging for middleware operations."""
        logger = logging.getLogger("finwiz.integration.middleware")

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)

        return logger

    def register_hook(self, hook_type: str, hook_function: Callable[[CrewExecutionContext], Awaitable[None]]) -> None:
        """
        Register a custom hook function.

        Args:
            hook_type: Type of hook ('pre_execution', 'post_execution', 'on_error')
            hook_function: Async function to call

        """
        if hook_type not in self.execution_hooks:
            raise ValueError(f"Invalid hook type: {hook_type}")

        self.execution_hooks[hook_type].append(hook_function)
        self.logger.info(f"Registered {hook_type} hook", extra={"hook_function": hook_function.__name__})

    async def pre_execution_hook(self, crew_name: str, dependencies: list[str], max_age_hours: int = 24, execution_id: str | None = None) -> PreExecutionResult:
        """
        Pre-execution hook for dependency validation and data preparation.

        Args:
            crew_name: Name of the crew to execute
            dependencies: List of crew dependencies
            max_age_hours: Maximum acceptable data age in hours
            execution_id: Optional execution identifier

        Returns:
            PreExecutionResult with validation status and upstream data

        """
        if not execution_id:
            execution_id = f"{crew_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        self.logger.info(
            f"Starting pre-execution hook for {crew_name}",
            extra={"execution_id": execution_id, "dependencies": dependencies, "max_age_hours": max_age_hours},
        )

        try:
            # Create execution context
            context = CrewExecutionContext(
                crew_name=crew_name,
                execution_id=execution_id,
                start_time=datetime.now(),
                dependencies=dependencies,
                max_age_hours=max_age_hours,
            )

            # Store active execution
            self.active_executions[execution_id] = context

            # Initialize result
            result = PreExecutionResult(can_proceed=True, dependencies_met=True)

            # Validate dependencies
            dependency_result = await self._validate_dependencies(crew_name, dependencies, max_age_hours)

            result.dependencies_met = dependency_result["all_met"]
            result.missing_dependencies = dependency_result["missing"]
            result.stale_dependencies = dependency_result["stale"]
            result.upstream_data = dependency_result["data"]

            # Add warnings for stale data
            if result.stale_dependencies:
                result.warnings.append(f"Stale dependencies detected: {', '.join(result.stale_dependencies)}")

            # Determine if execution can proceed
            if result.missing_dependencies:
                result.can_proceed = False
                result.errors.append(f"Missing required dependencies: {', '.join(result.missing_dependencies)}")

            # Update context with upstream data
            context.upstream_data = result.upstream_data

            # Execute custom pre-execution hooks
            await self._execute_hooks("pre_execution", context)

            self.logger.info(
                f"Pre-execution hook completed for {crew_name}",
                extra={
                    "execution_id": execution_id,
                    "can_proceed": result.can_proceed,
                    "dependencies_met": result.dependencies_met,
                    "missing_count": len(result.missing_dependencies),
                    "stale_count": len(result.stale_dependencies),
                },
            )

            return result

        except Exception as e:
            error_msg = f"Pre-execution hook failed for {crew_name}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)

            return PreExecutionResult(can_proceed=False, dependencies_met=False, errors=[error_msg])

    async def post_execution_hook(self, execution_id: str, crew_output: dict[str, Any], execution_duration: float | None = None) -> PostExecutionResult:
        """
        Post-execution hook for data storage, validation, and metadata persistence.

        Args:
            execution_id: Execution identifier from pre-execution hook
            crew_output: Output data from crew execution
            execution_duration: Optional execution duration in seconds

        Returns:
            PostExecutionResult with storage and validation status

        """
        self.logger.info("Starting post-execution hook", extra={"execution_id": execution_id})

        try:
            # Get execution context
            context = self.active_executions.get(execution_id)
            if not context:
                raise ValueError(f"No execution context found for ID: {execution_id}")

            # Initialize result
            result = PostExecutionResult(storage_success=False, validation_success=False, metadata_stored=False)

            # Validate crew output
            validation_result = await self._validate_crew_output(context.crew_name, crew_output)
            result.validation_success = validation_result.is_valid

            if not validation_result.is_valid:
                result.errors.extend(validation_result.validation_errors)
                result.warnings.extend(validation_result.validation_warnings)

            # Store crew output
            storage_result = await self._store_crew_output(context, crew_output, execution_duration)
            result.storage_success = storage_result["success"]

            if not storage_result["success"]:
                result.errors.extend(storage_result["errors"])

            # Store metadata
            metadata_result = await self._store_execution_metadata(context, crew_output, validation_result, execution_duration)
            result.metadata_stored = metadata_result["success"]

            if not metadata_result["success"]:
                result.errors.extend(metadata_result["errors"])

            # Execute custom post-execution hooks
            await self._execute_hooks("post_execution", context)

            # Clean up execution context
            if execution_id in self.active_executions:
                del self.active_executions[execution_id]

            self.logger.info(
                "Post-execution hook completed",
                extra={
                    "execution_id": execution_id,
                    "crew_name": context.crew_name,
                    "storage_success": result.storage_success,
                    "validation_success": result.validation_success,
                    "metadata_stored": result.metadata_stored,
                },
            )

            return result

        except Exception as e:
            error_msg = f"Post-execution hook failed for {execution_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)

            # Execute error hooks
            if execution_id in self.active_executions:
                try:
                    await self._execute_hooks("on_error", self.active_executions[execution_id])
                except Exception as hook_error:
                    self.logger.error(f"Error hook failed: {str(hook_error)}")

            return PostExecutionResult(storage_success=False, validation_success=False, metadata_stored=False, errors=[error_msg])

    async def coordinate_crew_execution(self, crew_configs: list[CrewConfig]) -> ExecutionResult:
        """
        Coordinate execution of multiple crews with middleware hooks.

        Args:
            crew_configs: List of crew configurations to execute

        Returns:
            ExecutionResult with coordination status

        """
        self.logger.info(
            "Starting coordinated crew execution",
            extra={"crew_count": len(crew_configs), "crews": [config.name for config in crew_configs]},
        )

        try:
            # Use the integration manager's coordination with middleware hooks
            return await self.integration_manager.coordinate_crew_execution(crew_configs)

        except Exception as e:
            error_msg = f"Coordinated execution failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)

            return ExecutionResult(
                success=False,
                executed_crews=[],
                failed_crews=[config.name for config in crew_configs],
                execution_time=0.0,
                errors=[error_msg],
            )

    async def _validate_dependencies(self, crew_name: str, dependencies: list[str], max_age_hours: int) -> dict[str, Any]:
        """Validate crew dependencies and collect upstream data."""
        try:
            missing = []
            stale = []
            data = {}

            for dep in dependencies:
                # Check if dependency data exists
                dep_data = self.integration_manager.get_crew_data_with_freshness_check(dep, max_age_hours, warn_on_stale=False)

                if dep_data is None:
                    missing.append(dep)
                else:
                    data[dep] = dep_data

                    # Check freshness
                    freshness_result = self.integration_manager.freshness_checker.check_data_freshness_for_crew(dep, max_age_hours)

                    if freshness_result and not freshness_result.freshness_status.is_fresh:
                        stale.append(dep)

            return {"all_met": len(missing) == 0, "missing": missing, "stale": stale, "data": data}

        except Exception as e:
            self.logger.error(f"Dependency validation failed: {str(e)}", exc_info=True)
            return {"all_met": False, "missing": dependencies, "stale": [], "data": {}}

    async def _validate_crew_output(self, crew_name: str, crew_output: dict[str, Any]) -> ValidationStatus:
        """Validate crew output using the validation pipeline."""
        try:
            # Use the validation pipeline for comprehensive validation
            validation_result = self.validation_pipeline.validate_crew_output(crew_name, crew_output)

            return ValidationStatus(
                is_valid=validation_result.is_valid,
                validation_timestamp=datetime.now(),
                validation_errors=[e.message for e in validation_result.errors],
                validation_warnings=[w.message for w in validation_result.warnings],
                schema_version=1,
            )

        except Exception as e:
            error_msg = f"Output validation failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)

            return ValidationStatus(
                is_valid=False,
                validation_timestamp=datetime.now(),
                validation_errors=[error_msg],
                validation_warnings=[],
                schema_version=1,
            )

    async def _store_crew_output(self, context: CrewExecutionContext, crew_output: dict[str, Any], execution_duration: float | None) -> dict[str, Any]:
        """Store crew output in the integration directory."""
        try:
            # Create crew-specific output directory
            crew_output_dir = self.integration_dir / context.crew_name
            crew_output_dir.mkdir(parents=True, exist_ok=True)

            # Generate output filename with timestamp
            timestamp = context.start_time.strftime("%Y%m%d_%H%M%S")
            output_file = crew_output_dir / f"{context.crew_name}_output_{timestamp}.json"

            # Add execution metadata to output
            enhanced_output = {
                "execution_id": context.execution_id,
                "crew_name": context.crew_name,
                "execution_timestamp": context.start_time.isoformat(),
                "execution_duration_seconds": execution_duration,
                "data": crew_output,
            }

            # Save to file
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(enhanced_output, f, indent=2, ensure_ascii=False, default=str)

            self.logger.info(
                "Stored crew output",
                extra={"crew_name": context.crew_name, "execution_id": context.execution_id, "output_file": str(output_file)},
            )

            return {"success": True, "errors": []}

        except Exception as e:
            error_msg = f"Failed to store crew output: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return {"success": False, "errors": [error_msg]}

    async def _store_execution_metadata(
        self,
        context: CrewExecutionContext,
        crew_output: dict[str, Any],
        validation_result: ValidationStatus,
        execution_duration: float | None,
    ) -> dict[str, Any]:
        """Store execution metadata."""
        try:
            metadata_file = self.integration_dir / "metadata" / f"{context.execution_id}_metadata.json"
            metadata_file.parent.mkdir(parents=True, exist_ok=True)

            metadata = {
                "execution_id": context.execution_id,
                "crew_name": context.crew_name,
                "execution_timestamp": context.start_time.isoformat(),
                "execution_duration_seconds": execution_duration,
                "dependencies": context.dependencies,
                "max_age_hours": context.max_age_hours,
                "validation_status": {
                    "is_valid": validation_result.is_valid,
                    "validation_timestamp": validation_result.validation_timestamp.isoformat(),
                    "validation_errors": validation_result.validation_errors,
                    "validation_warnings": validation_result.validation_warnings,
                    "schema_version": validation_result.schema_version,
                },
                "upstream_data_sources": list(context.upstream_data.keys()),
                "output_size_bytes": len(json.dumps(crew_output, default=str)),
            }

            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

            return {"success": True, "errors": []}

        except Exception as e:
            error_msg = f"Failed to store metadata: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return {"success": False, "errors": [error_msg]}

    async def _execute_hooks(self, hook_type: str, context: CrewExecutionContext) -> None:
        """Execute registered hooks of the specified type."""
        hooks = self.execution_hooks.get(hook_type, [])
        if not hooks:
            return

        self.logger.debug(
            f"Executing {len(hooks)} {hook_type} hooks",
            extra={"execution_id": context.execution_id, "crew_name": context.crew_name},
        )

        for hook in hooks:
            try:
                await hook(context)
            except Exception as e:
                self.logger.error(
                    f"Hook execution failed: {str(e)}",
                    extra={"hook_type": hook_type, "hook_function": hook.__name__, "execution_id": context.execution_id},
                    exc_info=True,
                )

    def get_active_executions(self) -> dict[str, CrewExecutionContext]:
        """Get currently active executions."""
        return self.active_executions.copy()

    def get_execution_context(self, execution_id: str) -> CrewExecutionContext | None:
        """Get execution context by ID."""
        return self.active_executions.get(execution_id)
