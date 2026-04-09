"""
Core validation infrastructure for FinWiz.

This module provides centralized validation management, schema registry,
and structured error handling for all data validation needs.
"""

from .contract import ContractValidator
from .enums import ValidationMode
from .manager import ValidationManager
from .registry import SchemaRegistry
from .result import ValidationError, ValidationResult, ValidationWarning
from .template import (
    ConfigurationError,
    TemplateVariableValidator,
    validate_template_variables_at_startup,
)

__all__ = [
    "ConfigurationError",
    "ContractValidator",
    "SchemaRegistry",
    "TemplateVariableValidator",
    "ValidationError",
    "ValidationManager",
    "ValidationMode",
    "ValidationResult",
    "ValidationWarning",
    "validate_template_variables_at_startup",
]
