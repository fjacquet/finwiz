"""
Data storage operations for registry management.

Functions for storing crew output data with validation and metadata.
"""

import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


def store_crew_output(
    output_dir: Path,
    metadata_dir: Path,
    crew_name: str,
    crew_output: Any,
    logger: logging.Logger,
) -> bool:
    """Store crew output to the integration system."""
    try:
        from .schema_manager import SchemaManager
        from .validation_manager import ValidationManager

        schema_manager = SchemaManager(logger)
        validation_manager = ValidationManager(metadata_dir, logger)

        logger.info(f"Storing output for crew: {crew_name}")

        # Create crew output directory
        crew_output_dir = output_dir / crew_name
        crew_output_dir.mkdir(parents=True, exist_ok=True)

        # Convert crew output to dictionary
        output_data = _convert_crew_output_to_dict(crew_output, schema_manager)

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

        # Create/update latest symlink
        latest_file = crew_output_dir / f"{crew_name}_latest.json"
        _create_latest_symlink(output_file, latest_file)

        # Validate the stored output
        validation_result = validation_manager.validate_crew_output(crew_name, output_data)

        if validation_result.is_valid:
            logger.info(
                f"Successfully stored output for crew {crew_name}",
                extra={
                    "output_file": str(output_file),
                    "data_size": len(str(output_data)),
                    "has_tasks": len(output_data.get("tasks_output", [])),
                },
            )
        else:
            logger.warning(
                f"Stored output for crew {crew_name} with validation warnings",
                extra={
                    "validation_errors": validation_result.errors,
                    "validation_warnings": validation_result.warnings,
                },
            )

        return True

    except Exception as e:
        error_msg = f"Failed to store output for crew {crew_name}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return False


def _convert_crew_output_to_dict(
    crew_output: Any,
    schema_manager: Any,
) -> dict[str, Any]:
    """Convert crew output object to dictionary format."""
    if hasattr(crew_output, "raw"):
        # CrewAI CrewOutput object
        return {
            "raw_output": str(crew_output.raw),
            "json_dict": (crew_output.json_dict if hasattr(crew_output, "json_dict") else {}),
            "pydantic": (crew_output.pydantic.model_dump() if hasattr(crew_output, "pydantic") and crew_output.pydantic else {}),
            "tasks_output": _extract_tasks_output(crew_output),
            "token_usage": (crew_output.token_usage if hasattr(crew_output, "token_usage") else {}),
            "usage_metrics": (schema_manager.serialize_usage_metrics(crew_output.usage_metrics) if hasattr(crew_output, "usage_metrics") else {}),
        }
    elif isinstance(crew_output, dict):
        return crew_output
    else:
        return {"raw_output": str(crew_output)}


def _extract_tasks_output(crew_output: Any) -> list[dict[str, Any]]:
    """Extract tasks output from crew output object."""
    if not hasattr(crew_output, "tasks_output"):
        return []

    return [
        {
            "description": (task.description if hasattr(task, "description") else str(task)),
            "summary": task.summary if hasattr(task, "summary") else "",
            "raw": str(task.raw) if hasattr(task, "raw") else str(task),
            "json_dict": task.json_dict if hasattr(task, "json_dict") else {},
            "pydantic": (task.pydantic.model_dump() if hasattr(task, "pydantic") and task.pydantic else {}),
        }
        for task in crew_output.tasks_output
    ]


def _create_latest_symlink(output_file: Path, latest_file: Path) -> None:
    """Create or update symlink to latest output file."""
    if latest_file.exists():
        latest_file.unlink()

    try:
        latest_file.symlink_to(output_file.name)
    except (OSError, NotImplementedError):
        # Fallback: copy file if symlinks not supported
        shutil.copy2(output_file, latest_file)
