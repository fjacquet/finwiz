"""
Technical Analysis Models and Enums (Legacy Compatibility).

DEPRECATED: This module provides backward compatibility imports.
Use: from finwiz.quantitative.technical.technical_models import <ClassName>
"""

# Re-export all models from the new consolidated technical_models module
from .technical_models import (
    ConfluenceZone,
    SignalStrength,
    SignalType,
    TechnicalAnalysisResult,
    TechnicalIndicatorResult,
    TechnicalSignal,
)

__all__ = [
    "ConfluenceZone",
    "SignalStrength",
    "SignalType",
    "TechnicalAnalysisResult",
    "TechnicalIndicatorResult",
    "TechnicalSignal",
]
