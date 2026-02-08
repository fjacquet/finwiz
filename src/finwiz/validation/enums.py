"""Validation enums and constants."""

from enum import StrEnum
from typing import Literal


class ValidationMode(StrEnum):
    """Validation strictness modes."""

    OFF = "off"
    WARN = "warn"
    ERROR = "error"


# Type alias for backward compatibility
Strictness = Literal["off", "warn", "error"]
