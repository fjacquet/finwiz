"""Fail-fast API key validation for tool classes.

Tools call `validate_api_key()` in `model_post_init` so that a missing key
raises `ValueError` immediately at instantiation — not at first API call.
"""

import os

from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


def validate_api_key(env_var: str, tool_name: str) -> str:
    """Return the API key value or raise ValueError if missing/empty.

    Args:
        env_var: Name of the environment variable (e.g. ``"PPLX_API_KEY"``).
        tool_name: Human-readable tool name for the error message.

    Returns:
        The non-empty API key string.

    Raises:
        ValueError: If the environment variable is unset or empty.

    """
    key = os.getenv(env_var)
    if not key:
        msg = f"{tool_name} requires {env_var} environment variable"
        logger.error(msg)
        raise ValueError(msg)
    return key
