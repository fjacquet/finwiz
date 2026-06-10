"""Shared JSON envelope helpers for tool _run methods that return JSON strings."""

import json
from typing import Any


def json_ok(payload: dict[str, Any]) -> str:
    """Serialize a tool success payload (handles datetimes and other non-JSON types)."""
    return json.dumps(payload, indent=2, default=str)


def json_error(exc: Exception, **context: Any) -> str:
    """Serialize a tool failure envelope with the exception type and optional context fields; context cannot override the envelope keys."""
    payload: dict[str, Any] = {**context, "success": False, "error": str(exc), "error_type": type(exc).__name__}
    return json.dumps(payload, indent=2, default=str)
