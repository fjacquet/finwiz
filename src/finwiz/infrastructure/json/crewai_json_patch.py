"""
CrewAI JSON Repair Patch.

Monkey-patches Pydantic's model_validate_json to automatically repair
common JSON errors from LLM outputs (especially trailing commas).

This patch is applied at crew initialization to ensure all JSON outputs
are repaired before Pydantic validation.
"""

import json
import threading
from contextlib import contextmanager
from typing import Any

from pydantic import BaseModel, ValidationError

from finwiz.infrastructure.json.repair import repair_json
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)

# Store original method (get the underlying function, not the classmethod)
_original_model_validate_json = BaseModel.model_validate_json.__func__

# Thread-safe patch tracking
_patch_lock = threading.Lock()
_patch_applied = False


def _patched_model_validate_json(cls: type[BaseModel], json_data: str | bytes, **kwargs: Any) -> BaseModel:
    """
    Patched version of model_validate_json that repairs JSON before validation.

    Args:
        cls: Pydantic model class
        json_data: JSON string or bytes to validate
        **kwargs: Additional arguments for validation

    Returns:
        Validated Pydantic model instance

    """
    try:
        # Try original validation first
        result: BaseModel = _original_model_validate_json(cls, json_data, **kwargs)
        return result
    except (ValidationError, json.JSONDecodeError) as e:
        # If validation fails, try repairing the JSON
        logger.warning(f"Pydantic validation failed for {cls.__name__}, attempting JSON repair...")
        logger.debug(f"Original error: {e}")

        try:
            # Convert bytes to string if needed
            if isinstance(json_data, bytes):
                json_str = json_data.decode("utf-8")
            else:
                json_str = json_data

            # Repair the JSON
            repaired_json = repair_json(json_str)

            # Try validation again with repaired JSON
            repaired_result: BaseModel = _original_model_validate_json(cls, repaired_json, **kwargs)
            logger.info(f"✅ Successfully validated {cls.__name__} after JSON repair")
            return repaired_result

        except (ValidationError, json.JSONDecodeError, ValueError) as repair_error:
            logger.error(f"❌ JSON repair failed for {cls.__name__}: {repair_error}")
            # Re-raise original error
            raise e from repair_error


def apply_json_repair_patch() -> None:
    """
    Apply the JSON repair patch to Pydantic's model_validate_json.

    This should be called once at application startup or before crew execution.
    Thread-safe implementation using lock.
    """
    global _patch_applied

    with _patch_lock:
        if _patch_applied:
            logger.debug("JSON repair patch already applied")
            return

        logger.info("Applying JSON repair patch to Pydantic model_validate_json")
        BaseModel.model_validate_json = classmethod(_patched_model_validate_json)  # type: ignore[method-assign, assignment]
        _patch_applied = True
        logger.info("✅ JSON repair patch applied successfully")


def remove_json_repair_patch() -> None:
    """
    Remove the JSON repair patch and restore original Pydantic behavior.

    This is mainly for testing purposes.
    Thread-safe implementation using lock.
    """
    global _patch_applied

    with _patch_lock:
        if not _patch_applied:
            logger.debug("JSON repair patch not applied, nothing to remove")
            return

        logger.info("Removing JSON repair patch from Pydantic")
        BaseModel.model_validate_json = classmethod(_original_model_validate_json)  # type: ignore[method-assign, assignment]
        _patch_applied = False
        logger.info("✅ JSON repair patch removed")


@contextmanager
def json_repair_context():
    """
    Context manager for temporary JSON repair patch.

    Applies the patch on entry and removes it on exit.
    Useful for testing or isolated crew executions.

    Example:
        with json_repair_context():
            result = crew.kickoff()

    """
    apply_json_repair_patch()
    try:
        yield
    finally:
        remove_json_repair_patch()
