"""
Custom exceptions for FinWiz application.

This module provides domain-specific exceptions for better error handling
and debugging throughout the FinWiz codebase.
"""

from finwiz.exceptions.data_quality import (
    DataQualityError,
    GradeScoreMismatchError,
    MissingRequiredFieldError,
)
from finwiz.exceptions.orchestrator import (
    InsufficientPriceDataError,
    OptimizationFailedError,
    PortfolioRebalancingError,
)

__all__ = [
    # Data quality exceptions
    "DataQualityError",
    "MissingRequiredFieldError",
    "GradeScoreMismatchError",
    # Orchestrator exceptions
    "PortfolioRebalancingError",
    "InsufficientPriceDataError",
    "OptimizationFailedError",
]
