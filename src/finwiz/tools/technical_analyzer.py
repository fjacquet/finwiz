"""
Advanced Technical Analysis Tools.

This module provides comprehensive technical analysis capabilities including
Fibonacci retracements, support/resistance levels, and multi-indicator confluence
zone detection for enhanced trading signal identification.
"""

from __future__ import annotations

from finwiz.tools.logger import get_logger
from finwiz.tools.technical_algorithms import TechnicalAlgorithms
from finwiz.tools.technical_models import PriceData, TechnicalAnalysisResult
from finwiz.tools.technical_patterns import TechnicalPatterns

logger = get_logger(__name__)


class TechnicalAnalyzer:
    """
    Advanced technical analysis engine.

    Provides comprehensive technical analysis including:
    - Fibonacci retracements and extensions
    - Dynamic support and resistance levels
    - Multi-indicator confluence zones
    - Signal strength assessment
    """

    def __init__(self) -> None:
        """Initialize the technical analyzer."""
        self.algorithms = TechnicalAlgorithms()
        self.patterns = TechnicalPatterns()

    def analyze(self, ticker: str, price_data: PriceData) -> TechnicalAnalysisResult:
        """
        Perform comprehensive technical analysis.

        Args:
            ticker: The ticker symbol being analyzed
            price_data: Historical price data

        Returns:
            Complete technical analysis result

        """
        logger.info(f"Starting technical analysis for {ticker}")

        if price_data.length < 20:
            raise ValueError("Insufficient data for technical analysis (minimum 20 periods required)")

        # Calculate Fibonacci levels using algorithms module
        fibonacci_levels = self.algorithms.calculate_fibonacci_levels(price_data)

        # Identify support and resistance levels using patterns module
        support_resistance = self.patterns.identify_support_resistance(price_data)

        # Calculate technical indicators using algorithms module
        indicator_signals = self.algorithms.calculate_indicator_signals(price_data)

        # Find confluence zones using patterns module
        confluence_zones = self.patterns.find_confluence_zones(fibonacci_levels, support_resistance, indicator_signals, price_data.closes[-1])

        # Determine overall signal using patterns module
        overall_signal, signal_confidence = self.patterns.determine_overall_signal(fibonacci_levels, support_resistance, indicator_signals, confluence_zones)

        return TechnicalAnalysisResult(
            ticker=ticker,
            fibonacci_levels=fibonacci_levels,
            support_resistance=support_resistance,
            indicator_signals=indicator_signals,
            confluence_zones=confluence_zones,
            overall_signal=overall_signal,
            signal_confidence=signal_confidence,
        )
