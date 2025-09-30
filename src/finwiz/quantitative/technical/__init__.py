"""
Technical Analysis Package.

Modular technical analysis system with indicator calculators and analysis engine.
"""

# Import main classes for backward compatibility
from .engine import TechnicalAnalysisEngine, calculate_technical_indicators, detect_confluence_zones, get_confluence_signals
from .technical_indicators import TALibWrappers
from .technical_models import (
    ConfluenceZone,
    SignalStrength,
    SignalType,
    TechnicalAnalysisResult,
    TechnicalIndicatorResult,
    TechnicalSignal,
)

# Export all classes for backward compatibility
__all__ = [
    # Main engine
    "TechnicalAnalysisEngine",
    "calculate_technical_indicators",
    "detect_confluence_zones",
    "get_confluence_signals",  # Backward compatibility alias
    # Models
    "SignalType",
    "SignalStrength",
    "TechnicalSignal",
    "ConfluenceZone",
    "TechnicalIndicatorResult",
    "TechnicalAnalysisResult",
    # TA-Lib Wrappers
    "TALibWrappers",
]
