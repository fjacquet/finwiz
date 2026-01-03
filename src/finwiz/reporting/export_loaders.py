"""
Report export loading functions for report consolidation.

Extracted from report_consolidator.py for modularity.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import BaseModel, ValidationError

from finwiz.schemas.crew_exports import DeepAnalysisCrewExport
from finwiz.schemas.hybrid_analysis import EnrichedAnalysis
from finwiz.schemas.python_analysis import PythonDeepAnalysisResult
from finwiz.tools.logger import get_logger

if TYPE_CHECKING:
    pass

logger = get_logger(__name__)


def load_exports(
    file_paths: list[str],
    schema_class: type[BaseModel],
    crew_name: str,
    session_id: str,
    validation_errors: list[dict],
) -> list[BaseModel]:
    """
    Load and validate JSON export files with enhanced error recovery.

    This helper function reads JSON files from disk, validates them against
    the specified Pydantic schema, and returns a list of validated objects.
    It handles missing files and validation errors gracefully with detailed
    logging and error tracking.

    Args:
        file_paths: List of file paths to load
        schema_class: Pydantic schema class for validation
        crew_name: Name of crew for error tracking
        session_id: Session ID for defaults
        validation_errors: List to append validation errors to

    Returns:
        List of validated export objects (may be empty if all files fail)

    """
    exports: list[BaseModel] = []
    schema_name = schema_class.__name__

    logger.debug(f"Loading {len(file_paths)} files for schema {schema_name}")

    for path_str in file_paths:
        path = Path(path_str)

        if not path.exists():
            _handle_missing_file(path, crew_name, validation_errors)
            continue

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            filtered_data = _filter_to_schema_fields(data, schema_class)
            filtered_data = _add_discovery_defaults(filtered_data, schema_name, session_id, path)

            export = schema_class.model_validate(filtered_data)
            exports.append(export)
            logger.debug(f"Successfully validated {path} as {schema_name}")

        except ValidationError as e:
            _handle_validation_error(path, schema_name, crew_name, e, validation_errors)
        except json.JSONDecodeError as e:
            _handle_json_error(path, crew_name, e, validation_errors)
        except Exception as e:
            _handle_unexpected_error(path, crew_name, e, validation_errors)

    logger.info(f"Loaded {len(exports)}/{len(file_paths)} valid {schema_name} exports")

    if len(file_paths) > 0 and len(exports) == 0:
        logger.warning(f"No valid {schema_name} exports loaded from {len(file_paths)} files")

    return exports


def load_deep_analysis_exports(
    file_paths: list[str],
    validation_errors: list[dict],
) -> list[DeepAnalysisCrewExport | PythonDeepAnalysisResult | EnrichedAnalysis]:
    """
    Load deep analysis exports with automatic schema detection.

    Supports:
    - CrewAI deep analysis exports (legacy)
    - Python analyzer results (legacy)
    - EnrichedAnalysis (new hybrid analysis schema)

    Automatically detects which schema to use based on the crew_name field
    or presence of hybrid analysis fields.

    Args:
        file_paths: List of file paths to load
        validation_errors: List to append validation errors to

    Returns:
        List of validated export objects (mixed CrewAI, Python, and hybrid)

    """
    exports: list[DeepAnalysisCrewExport | PythonDeepAnalysisResult | EnrichedAnalysis] = []
    crew_name = "deep_analysis_crew"

    logger.debug(f"Loading {len(file_paths)} deep analysis files with auto-detection")

    for path_str in file_paths:
        path = Path(path_str)

        if not path.exists():
            _handle_missing_file(path, crew_name, validation_errors)
            continue

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            export, schema_name = _detect_and_validate_schema(data)
            exports.append(export)
            logger.debug(f"✅ Validated {path} as {schema_name}")

        except ValidationError as e:
            schema_name = _determine_schema_name(data)
            _handle_validation_error(path, schema_name, crew_name, e, validation_errors)
        except json.JSONDecodeError as e:
            _handle_json_error(path, crew_name, e, validation_errors)
        except Exception as e:
            _handle_unexpected_error(path, crew_name, e, validation_errors)

    logger.info(f"Loaded {len(exports)}/{len(file_paths)} valid deep analysis exports")

    if len(file_paths) > 0 and len(exports) == 0:
        logger.warning(f"No valid deep analysis exports loaded from {len(file_paths)} files")

    return exports


def _detect_and_validate_schema(
    data: dict,
) -> tuple[DeepAnalysisCrewExport | PythonDeepAnalysisResult | EnrichedAnalysis, str]:
    """Detect schema from data structure and validate."""
    crew_name = data.get("crew_name", "")

    if "quantitative" in data and "qualitative" in data:
        return EnrichedAnalysis.model_validate(data), "EnrichedAnalysis (hybrid)"
    elif crew_name == "PythonDeepAnalyzer":
        return PythonDeepAnalysisResult.model_validate(data), "PythonDeepAnalysisResult (legacy)"
    else:
        return DeepAnalysisCrewExport.model_validate(data), "DeepAnalysisCrewExport (legacy)"


def _determine_schema_name(data: dict) -> str:
    """Determine schema name from data for error reporting."""
    crew_name = data.get("crew_name", "")
    if "quantitative" in data and "qualitative" in data:
        return "EnrichedAnalysis"
    elif crew_name == "PythonDeepAnalyzer":
        return "PythonDeepAnalysisResult"
    return "DeepAnalysisCrewExport"


def _filter_to_schema_fields(data: dict, schema_class: type[BaseModel]) -> dict:
    """Filter data to only include fields defined in the schema."""
    schema_fields = schema_class.model_fields.keys()
    return {k: v for k, v in data.items() if k in schema_fields}


def _add_discovery_defaults(data: dict, schema_name: str, session_id: str, path: Path) -> dict:
    """Add default values for missing required fields in discovery exports."""
    if schema_name != "DiscoveryCrewExport":
        return data

    if "session_id" not in data:
        data["session_id"] = session_id
    if "market_context" not in data:
        data["market_context"] = "Market context not available from discovery crew export"
    if "report_html_path" not in data:
        data["report_html_path"] = str(path.parent / "discovery_latest.html")
    if "report_json_path" not in data:
        data["report_json_path"] = str(path)

    return data


def _handle_missing_file(path: Path, crew_name: str, validation_errors: list[dict]) -> None:
    """Handle missing file error."""
    error_msg = f"Export file not found: {path}"
    logger.warning(error_msg)
    validation_errors.append(
        {
            "crew": crew_name,
            "file": str(path),
            "error_type": "missing_file",
            "message": error_msg,
        }
    )


def _handle_validation_error(
    path: Path,
    schema_name: str,
    crew_name: str,
    error: ValidationError,
    validation_errors: list[dict],
) -> None:
    """Handle Pydantic validation error."""
    logger.error(f"Validation failed for {path} against {schema_name}:")
    validation_details = []
    for err in error.errors():
        field_path = " -> ".join(str(loc) for loc in err["loc"])
        error_detail = f"Field '{field_path}': {err['msg']}"
        logger.error(f"  {error_detail}")
        validation_details.append(error_detail)

    validation_errors.append(
        {
            "crew": crew_name,
            "file": str(path),
            "error_type": "validation_error",
            "schema": schema_name,
            "details": validation_details,
            "message": f"Validation failed: {len(validation_details)} field errors",
        }
    )
    logger.warning(f"Skipping invalid export {path} - continuing with valid exports")


def _handle_json_error(path: Path, crew_name: str, error: json.JSONDecodeError, validation_errors: list[dict]) -> None:
    """Handle JSON parsing error."""
    error_msg = f"Invalid JSON in {path}: {error}"
    logger.error(error_msg)
    validation_errors.append(
        {
            "crew": crew_name,
            "file": str(path),
            "error_type": "json_parse_error",
            "message": error_msg,
        }
    )


def _handle_unexpected_error(path: Path, crew_name: str, error: Exception, validation_errors: list[dict]) -> None:
    """Handle unexpected error."""
    error_msg = f"Failed to load {path}: {error}"
    logger.error(error_msg, exc_info=True)
    validation_errors.append(
        {
            "crew": crew_name,
            "file": str(path),
            "error_type": "unexpected_error",
            "message": error_msg,
        }
    )
