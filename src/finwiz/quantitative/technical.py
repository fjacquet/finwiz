"""
Technical analysis engine with TA-Lib integration for FinWiz.

This module provides comprehensive technical analysis capabilities including:
- TA-Lib wrapper functions for technical indicators
- Calculation methods for SMA, RSI, MACD, Bollinger Bands, and other indicators
- Confluence detection and signal generation capabilities
- Multi-timeframe analysis support
- Signal strength scoring and validation

DEPRECATED: This module has been refactored into a modular package.
Use: from finwiz.quantitative.technical import <ClassName>
"""

# Re-export all classes from the new modular structure for backward compatibility
from finwiz.quantitative.technical.engine import TechnicalAnalysisEngine
from finwiz.quantitative.technical.models import (
    ConfluenceZone,
    SignalStrength,
    SignalType,
    TechnicalAnalysisResult,
    TechnicalIndicatorResult,
    TechnicalSignal,
)
from finwiz.quantitative.technical.technical_indicators import (
    calculate_technical_indicators,
    detect_confluence_zones,
)

# Backward compatibility alias
get_confluence_signals = detect_confluence_zones

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
]
