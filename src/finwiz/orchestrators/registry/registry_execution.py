"""
Crew execution coordination for registry management.

Functions for coordinating crew execution, dependency management, and logging.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from .registry_models import CrewConfig, ExecutionResult

if TYPE_CHECKING:
    pass


def sort_crews_by_dependencies(crews: list[CrewConfig]) -> list[CrewConfig]:
    """Sort crews by their dependencies (simplified implementation)."""
    no_deps = [crew for crew in crews if not crew.dependencies]
    with_deps = [crew for crew in crews if crew.dependencies]
    return no_deps + with_deps


def check_dependencies(crew: CrewConfig, output_dir: Path) -> bool:
    """Check if crew dependencies are satisfied."""
    if not crew.dependencies:
        return True

    for dep in crew.dependencies:
        dep_dir = output_dir / dep
        if not dep_dir.exists() or not list(dep_dir.glob("*.json")):
            return False
    return True


def log_crew_execution_start(
    crew_name: str,
    execution_log_path: Path,
    logger: logging.Logger,
) -> None:
    """Log the start of crew execution."""
    try:
        from finwiz.integration.schema import SchemaManager

        schema_manager = SchemaManager(logger)
        execution_log = schema_manager.load_json_file(execution_log_path, {})

        if "executions" not in execution_log:
            execution_log["executions"] = []

        execution_log["executions"].append(
            {
                "crew_name": crew_name,
                "start_time": datetime.now().isoformat(),
                "status": "STARTED",
            }
        )

        schema_manager.save_json_file(execution_log_path, execution_log)

    except Exception as e:
        logger.warning(f"Failed to log execution start for {crew_name}: {str(e)}")


async def coordinate_crew_execution(
    crews: list[CrewConfig],
    output_dir: Path,
    execution_log_path: Path,
    logger: logging.Logger,
) -> ExecutionResult:
    """Coordinate execution of multiple crews based on dependencies."""
    start_time = datetime.now()
    executed_crews: list[str] = []
    failed_crews: list[str] = []
    errors: list[str] = []

    logger.info(
        "Starting crew execution coordination",
        extra={"crew_count": len(crews), "crews": [crew.name for crew in crews]},
    )

    try:
        sorted_crews = sort_crews_by_dependencies(crews)

        for crew in sorted_crews:
            try:
                logger.info(f"Coordinating execution for crew: {crew.name}")

                deps_result = check_dependencies(crew, output_dir)
                if not deps_result:
                    error_msg = f"Dependencies not met for crew {crew.name}"
                    errors.append(error_msg)
                    failed_crews.append(crew.name)
                    logger.error(error_msg)
                    continue

                log_crew_execution_start(crew.name, execution_log_path, logger)
                executed_crews.append(crew.name)

            except Exception as e:
                error_msg = f"Failed to coordinate crew {crew.name}: {str(e)}"
                errors.append(error_msg)
                failed_crews.append(crew.name)
                logger.error(error_msg, exc_info=True)

        execution_time = (datetime.now() - start_time).total_seconds()
        success = len(failed_crews) == 0

        result = ExecutionResult(
            success=success,
            executed_crews=executed_crews,
            failed_crews=failed_crews,
            execution_time=execution_time,
            errors=errors,
        )

        logger.info(
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
        logger.error(error_msg, exc_info=True)

        return ExecutionResult(
            success=False,
            executed_crews=executed_crews,
            failed_crews=failed_crews,
            execution_time=execution_time,
            errors=[error_msg],
        )
