"""
Consolidated Technical Analysis Models and Enums.

This module contains all Pydantic models and enums related to technical analysis,
providing a single source of truth for technical analysis data structures.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, validator

# ============================================================================
# ENUMS
# ============================================================================


class SignalType(str, Enum):
    """Types of technical analysis signals."""

    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    STRONG_BUY = "STRONG_BUY"
    STRONG_SELL = "STRONG_SELL"


class SignalStrength(str, Enum):
    """Signal strength levels."""

    VERY_WEAK = "very_weak"
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    VERY_STRONG = "very_strong"


class ZoneType(str, Enum):
    """Types of technical analysis zones."""

    SUPPORT = "support"
    RESISTANCE = "resistance"
    REVERSAL = "reversal"
    CONFLUENCE = "confluence"


class TrendDirection(str, Enum):
    """Market trend directions."""

    UPTREND = "uptrend"
    DOWNTREND = "downtrend"
    SIDEWAYS = "sideways"
    UNKNOWN = "unknown"


# ============================================================================
# CORE MODELS
# ============================================================================


class TechnicalSignal(BaseModel):
    """Represents a technical analysis signal."""

    indicator: str = Field(..., description="Name of the technical indicator")
    signal_type: SignalType = Field(..., description="Type of signal generated")
    strength: SignalStrength = Field(..., description="Strength of the signal")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence level (0.0 to 1.0)")
    price_level: float = Field(..., gt=0, description="Price level where signal was generated")
    timestamp: datetime = Field(default_factory=datetime.now, description="When signal was generated")
    description: str = Field(..., description="Human-readable description of the signal")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional signal metadata")


class IndicatorSignal(BaseModel):
    """Individual technical indicator signal (legacy compatibility)."""

    model_config = ConfigDict(extra="forbid")

    indicator_name: str = Field(..., description="Name of the technical indicator")
    signal_type: str = Field(..., description="buy, sell, or neutral")
    strength: float = Field(..., ge=0.0, le=1.0, description="Signal strength (0-1)")
    value: float = Field(..., description="Current indicator value")
    threshold: float | None = Field(None, description="Threshold value if applicable")
    description: str = Field(..., description="Human-readable signal description")


class ConfluenceZone(BaseModel):
    """Represents a confluence zone where multiple indicators align."""

    price_level: float = Field(..., gt=0, description="Price level of confluence")
    signal_type: SignalType = Field(..., description="Overall signal type for the zone")
    strength: SignalStrength = Field(..., description="Combined strength of confluent signals")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in confluence zone")
    contributing_signals: list[TechnicalSignal] = Field(..., description="Signals contributing to confluence")
    zone_range: tuple[float, float] = Field(..., description="Price range of confluence zone")
    timestamp: datetime = Field(default_factory=datetime.now, description="When confluence was detected")

    @validator("zone_range")
    def validate_zone_range(cls, v: tuple[float, float]) -> tuple[float, float]:
        """Validate that zone range is properly ordered."""
        if v[0] > v[1]:
            raise ValueError("Zone range lower bound must be less than upper bound")
        return v


class LegacyConfluenceZone(BaseModel):
    """Legacy confluence zone model for backward compatibility."""

    model_config = ConfigDict(extra="forbid")

    price_range: tuple[float, float] = Field(..., description="Price range of confluence zone")
    zone_type: str = Field(..., description="support, resistance, or reversal")
    confluence_score: float = Field(..., ge=0.0, le=1.0, description="Strength of confluence (0-1)")
    contributing_indicators: list[str] = Field(default_factory=list, description="Indicators in confluence")
    fibonacci_level: float | None = Field(None, description="Fibonacci level if present")
    support_resistance_level: float | None = Field(None, description="S/R level if present")
    signal_strength: float = Field(..., ge=0.0, le=1.0, description="Overall signal strength")


# ============================================================================
# FIBONACCI MODELS
# ============================================================================


class FibonacciLevels(BaseModel):
    """Fibonacci retracement and extension levels."""

    model_config = ConfigDict(extra="forbid")

    swing_high: float = Field(..., description="Swing high price")
    swing_low: float = Field(..., description="Swing low price")
    trend_direction: str = Field(..., description="uptrend or downtrend")
    retracement_levels: dict[str, float] = Field(..., description="Fibonacci retracement levels")
    extension_levels: dict[str, float] = Field(..., description="Fibonacci extension levels")
    current_price: float = Field(..., description="Current price for context")
    nearest_support: float | None = Field(None, description="Nearest Fibonacci support level")
    nearest_resistance: float | None = Field(None, description="Nearest Fibonacci resistance level")


# ============================================================================
# SUPPORT/RESISTANCE MODELS
# ============================================================================


class SupportResistance(BaseModel):
    """Support and resistance levels analysis."""

    model_config = ConfigDict(extra="forbid")

    support_levels: list[float] = Field(default_factory=list, description="Identified support levels")
    resistance_levels: list[float] = Field(default_factory=list, description="Identified resistance levels")
    current_price: float = Field(..., description="Current price for context")
    nearest_support: float | None = Field(None, description="Nearest support level")
    nearest_resistance: float | None = Field(None, description="Nearest resistance level")
    support_resistance_ratio: float = Field(..., description="Ratio of support to resistance levels")


# ============================================================================
# INDICATOR VALUE MODELS
# ============================================================================


class TechnicalIndicatorValue(BaseModel):
    """Individual technical indicator data point."""

    timestamp: datetime = Field(..., description="Data point timestamp")
    value: float = Field(..., description="Indicator value")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class TechnicalIndicatorSummary(BaseModel):
    """Summary of all technical indicators for a symbol."""

    symbol: str = Field(..., description="Symbol being analyzed")
    timestamp: datetime = Field(default_factory=datetime.now, description="Analysis timestamp")
    indicators: dict[str, TechnicalIndicatorValue] = Field(default_factory=dict, description="Dictionary of indicator values")
    overall_trend: TrendDirection = Field(default=TrendDirection.UNKNOWN, description="Overall trend direction")
    trend_strength: float = Field(default=0.0, ge=0.0, le=1.0, description="Trend strength (0-1)")


# ============================================================================
# RESULT MODELS
# ============================================================================


class TechnicalIndicatorResult(BaseModel):
    """Result from a technical indicator calculation."""

    indicator_name: str = Field(..., description="Name of the technical indicator")
    signals: list[TechnicalSignal] = Field(default_factory=list, description="Generated signals")
    raw_values: dict[str, Any] = Field(default_factory=dict, description="Raw indicator values")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    calculation_timestamp: datetime = Field(default_factory=datetime.now, description="When calculation was performed")


class TechnicalAnalysisResult(BaseModel):
    """Comprehensive technical analysis result."""

    symbol: str = Field(..., description="Symbol analyzed")
    timeframe: str = Field(..., description="Timeframe of analysis")
    analysis_timestamp: datetime = Field(default_factory=datetime.now, description="When analysis was performed")

    # Individual indicator results
    indicator_results: dict[str, TechnicalIndicatorResult] = Field(default_factory=dict, description="Results from individual indicators")

    # Overall analysis
    overall_signal: SignalType = Field(..., description="Overall signal recommendation")
    overall_confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence level")
    signal_strength: SignalStrength = Field(..., description="Overall signal strength")

    # Advanced analysis
    confluence_zones: list[ConfluenceZone] = Field(default_factory=list, description="Detected confluence zones")

    # Summary statistics
    total_signals: int = Field(default=0, ge=0, description="Total number of signals generated")
    bullish_signals: int = Field(default=0, ge=0, description="Number of bullish signals")
    bearish_signals: int = Field(default=0, ge=0, description="Number of bearish signals")
    neutral_signals: int = Field(default=0, ge=0, description="Number of neutral signals")

    # Metadata
    data_quality_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Quality score of input data")
    analysis_duration_ms: float = Field(default=0.0, ge=0.0, description="Analysis duration in milliseconds")


class LegacyTechnicalAnalysisResult(BaseModel):
    """Legacy technical analysis result for backward compatibility."""

    model_config = ConfigDict(extra="forbid")

    ticker: str = Field(..., description="Analyzed ticker symbol")
    analysis_date: datetime = Field(default_factory=datetime.now)
    fibonacci_levels: FibonacciLevels
    support_resistance: SupportResistance
    indicator_signals: list[IndicatorSignal] = Field(default_factory=list)
    confluence_zones: list[LegacyConfluenceZone] = Field(default_factory=list)
    overall_signal: str = Field(..., description="buy, sell, or neutral")
    signal_confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence")


# ============================================================================
# INPUT MODELS
# ============================================================================


class TechnicalAnalysisInput(BaseModel):
    """Input schema for technical analysis."""

    model_config = ConfigDict(extra="forbid")

    symbol: str = Field(..., description="Symbol to analyze")
    timeframe: str = Field(default="1D", description="Timeframe for analysis")
    indicators: list[str] = Field(default_factory=list, description="Specific indicators to calculate")
    lookback_period: int = Field(default=100, ge=20, le=500, description="Number of periods to analyze")
    include_confluence: bool = Field(default=True, description="Whether to detect confluence zones")


class EnhancedTechnicalAnalysisInput(BaseModel):
    """Enhanced input schema for technical analysis with additional options."""

    model_config = ConfigDict(extra="forbid")

    symbol: str = Field(..., description="Symbol to analyze")
    timeframe: str = Field(default="1D", description="Timeframe for analysis")
    analysis_type: str = Field(default="comprehensive", description="Type of analysis to perform")
    include_news_sentiment: bool = Field(default=False, description="Include news sentiment analysis")
    risk_tolerance: str = Field(default="moderate", description="Risk tolerance level")


# ============================================================================
# PRICE DATA MODELS
# ============================================================================


class PriceData(BaseModel):
    """Price data structure for technical analysis."""

    model_config = ConfigDict(extra="forbid")

    dates: list[datetime] = Field(..., description="List of dates")
    opens: list[float] = Field(..., description="Opening prices")
    highs: list[float] = Field(..., description="High prices")
    lows: list[float] = Field(..., description="Low prices")
    closes: list[float] = Field(..., description="Closing prices")
    volumes: list[int] = Field(..., description="Volume data")

    @validator("opens", "highs", "lows", "closes")
    def validate_price_lists_length(cls, v: list[float], values: dict[str, Any]) -> list[float]:
        """Validate that all price lists have the same length."""
        if "dates" in values and len(v) != len(values["dates"]):
            raise ValueError("All price data lists must have the same length as dates")
        return v

    @property
    def length(self) -> int:
        """Get the number of data points."""
        return len(self.dates)


# ============================================================================
# CONFIGURATION MODELS
# ============================================================================


class IndicatorConfig(BaseModel):
    """Configuration for technical indicators."""

    model_config = ConfigDict(extra="forbid")

    indicator: str = Field(..., description="Indicator type")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Indicator parameters")
    enabled: bool = Field(default=True, description="Whether indicator is enabled")
    weight: float = Field(default=1.0, ge=0.0, le=2.0, description="Weight in overall analysis")


class TechnicalAnalysisConfig(BaseModel):
    """Configuration for technical analysis engine."""

    model_config = ConfigDict(extra="forbid")

    indicators: list[IndicatorConfig] = Field(default_factory=list, description="Indicator configurations")
    confluence_threshold: int = Field(default=2, ge=2, le=5, description="Minimum signals for confluence")
    confidence_threshold: float = Field(default=0.6, ge=0.0, le=1.0, description="Minimum confidence for signals")
    enable_fibonacci: bool = Field(default=True, description="Enable Fibonacci analysis")
    enable_support_resistance: bool = Field(default=True, description="Enable support/resistance analysis")
    lookback_period: int = Field(default=100, ge=20, le=500, description="Default lookback period")
