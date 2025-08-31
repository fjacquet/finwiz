"""
Core validation infrastructure for FinWiz.

This module provides centralized validation management, schema registry,
and structured error handling for all data validation needs.
"""

from .contract_validator import ContractValidator
from .enums import ValidationMode
from .manager import ValidationManager
from .registry import SchemaRegistry
from .result import ValidationError, ValidationResult, ValidationWarning

__all__ = [
    "ValidationManager",
    "SchemaRegistry",
    "ContractValidator",
    "ValidationResult",
    "ValidationError",
    "ValidationWarning",
    "ValidationMode",
]
