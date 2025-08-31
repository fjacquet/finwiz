"""Validation enums and constants."""

from enum import Enum
from typing import Literal


class ValidationMode(str, Enum):
    """Validation strictness modes."""

    OFF = "off"
    WARN = "warn"
    ERROR = "error"


# Type alias for backward compatibility
Strictness = Literal["off", "warn", "error"]
