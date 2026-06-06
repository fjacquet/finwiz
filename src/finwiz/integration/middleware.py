"""
Crew Integration Middleware.

Provides pre and post-execution hooks for crew coordination, dependency validation,
and data storage management.
"""

import logging
from collections.abc import Callable
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

        # NOTE: integration_dir removed per storage cleanup
        # self.integration_dir = self.output_dir / "integration"

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
            extra={"output_dir": str(self.output_dir)},
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
            error_msg = f"Coordinated execution failed: {e!s}"
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
            self.logger.error(f"Dependency validation failed: {e!s}", exc_info=True)
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
            error_msg = f"Output validation failed: {e!s}"
            self.logger.error(error_msg, exc_info=True)

            return ValidationStatus(
                is_valid=False,
                validation_timestamp=datetime.now(),
                validation_errors=[error_msg],
                validation_warnings=[],
                schema_version=1,
            )

    async def _store_crew_output(self, context: CrewExecutionContext, crew_output: dict[str, Any], execution_duration: float | None) -> dict[str, Any]:
        """
        Store crew output in the integration directory.

        NOTE: Filesystem storage has been removed per cleanup.
        This method is now a no-op that returns success.
        """
        # No-op: Storage removed per cleanup
        self.logger.debug(f"_store_crew_output called for {context.crew_name} (no-op, storage disabled)")
        return {"success": True, "errors": []}

    async def _store_execution_metadata(
        self,
        context: CrewExecutionContext,
        crew_output: dict[str, Any],
        validation_result: ValidationStatus,
        execution_duration: float | None,
    ) -> dict[str, Any]:
        """
        Store execution metadata.

        NOTE: Filesystem storage has been removed per cleanup.
        This method is now a no-op that returns success.
        """
        # No-op: Storage removed per cleanup
        self.logger.debug(f"_store_execution_metadata called for {context.execution_id} (no-op, storage disabled)")
        return {"success": True, "errors": []}

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
                    f"Hook execution failed: {e!s}",
                    extra={"hook_type": hook_type, "hook_function": hook.__name__, "execution_id": context.execution_id},
                    exc_info=True,
                )
