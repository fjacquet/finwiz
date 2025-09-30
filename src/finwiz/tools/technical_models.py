"""
Technical Analysis Data Models.

This module contains all Pydantic models used for technical analysis
including Fibonacci levels, support/resistance, and analysis results.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field


@dataclass
class PriceData:
    """Price data structure for technical analysis."""

    dates: list[datetime]
    opens: list[float]
    highs: list[float]
    lows: list[float]
    closes: list[float]
    volumes: list[int]

    def __post_init__(self) -> None:
        """Validate that all lists have the same length."""
        lengths = [
            len(self.dates),
            len(self.opens),
            len(self.highs),
            len(self.lows),
            len(self.closes),
            len(self.volumes),
        ]
        if len(set(lengths)) != 1:
            raise ValueError("All price data lists must have the same length")

    @property
    def length(self) -> int:
        """Get the number of data points."""
        return len(self.dates)

    def to_dataframe(self) -> pd.DataFrame:
        """Convert to pandas DataFrame for easier analysis."""
        return pd.DataFrame(
            {
                "date": self.dates,
                "open": self.opens,
                "high": self.highs,
                "low": self.lows,
                "close": self.closes,
                "volume": self.volumes,
            }
        )


class FibonacciLevel(BaseModel):
    """Individual Fibonacci retracement level."""

    model_config = ConfigDict(extra="forbid")

    ratio: float = Field(..., description="Fibonacci ratio (e.g., 0.382, 0.618)")
    price: float = Field(..., description="Price level for this ratio")
    percentage: float = Field(..., description="Percentage retracement")
    level_type: str = Field(..., description="Type: retracement or extension")


class FibonacciLevels(BaseModel):
    """Complete Fibonacci analysis result."""

    model_config = ConfigDict(extra="forbid")

    swing_high: float = Field(..., description="Swing high price used for calculation")
    swing_low: float = Field(..., description="Swing low price used for calculation")
    swing_high_date: datetime = Field(..., description="Date of swing high")
    swing_low_date: datetime = Field(..., description="Date of swing low")
    trend_direction: str = Field(..., description="uptrend or downtrend")
    levels: list[FibonacciLevel] = Field(default_factory=list, description="Fibonacci levels")
    current_price: float = Field(..., description="Current price for reference")
    nearest_support: float | None = Field(None, description="Nearest Fibonacci support level")
    nearest_resistance: float | None = Field(None, description="Nearest Fibonacci resistance level")


class SupportResistanceLevel(BaseModel):
    """Individual support or resistance level."""

    model_config = ConfigDict(extra="forbid")

    price: float = Field(..., description="Price level")
    level_type: str = Field(..., description="support or resistance")
    strength: float = Field(..., ge=0.0, le=1.0, description="Strength of the level (0-1)")
    touch_count: int = Field(..., ge=1, description="Number of times price touched this level")
    last_touch_date: datetime = Field(..., description="Date of last touch")
    volume_confirmation: bool = Field(default=False, description="Whether volume confirms the level")


class SupportResistance(BaseModel):
    """Complete support and resistance analysis."""

    model_config = ConfigDict(extra="forbid")

    support_levels: list[SupportResistanceLevel] = Field(default_factory=list)
    resistance_levels: list[SupportResistanceLevel] = Field(default_factory=list)
    current_price: float = Field(..., description="Current price for reference")
    nearest_support: float | None = Field(None, description="Nearest support level")
    nearest_resistance: float | None = Field(None, description="Nearest resistance level")
    support_resistance_ratio: float = Field(..., description="Ratio of support to resistance levels")


class IndicatorSignal(BaseModel):
    """Individual technical indicator signal."""

    model_config = ConfigDict(extra="forbid")

    indicator_name: str = Field(..., description="Name of the technical indicator")
    signal_type: str = Field(..., description="buy, sell, or neutral")
    strength: float = Field(..., ge=0.0, le=1.0, description="Signal strength (0-1)")
    value: float = Field(..., description="Current indicator value")
    threshold: float | None = Field(None, description="Threshold value if applicable")
    description: str = Field(..., description="Human-readable signal description")


class ConfluenceZone(BaseModel):
    """Zone where multiple technical indicators align."""

    model_config = ConfigDict(extra="forbid")

    price_range: tuple[float, float] = Field(..., description="Price range of confluence zone")
    zone_type: str = Field(..., description="support, resistance, or reversal")
    confluence_score: float = Field(..., ge=0.0, le=1.0, description="Strength of confluence (0-1)")
    contributing_indicators: list[str] = Field(default_factory=list, description="Indicators in confluence")
    fibonacci_level: float | None = Field(None, description="Fibonacci level if present")
    support_resistance_level: float | None = Field(None, description="S/R level if present")
    signal_strength: float = Field(..., ge=0.0, le=1.0, description="Overall signal strength")


class TechnicalAnalysisResult(BaseModel):
    """Complete technical analysis result."""

    model_config = ConfigDict(extra="forbid")

    ticker: str = Field(..., description="Analyzed ticker symbol")
    analysis_date: datetime = Field(default_factory=datetime.now)
    fibonacci_levels: FibonacciLevels
    support_resistance: SupportResistance
    indicator_signals: list[IndicatorSignal] = Field(default_factory=list)
    confluence_zones: list[ConfluenceZone] = Field(default_factory=list)
    overall_signal: str = Field(..., description="buy, sell, or neutral")
    signal_confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence")
