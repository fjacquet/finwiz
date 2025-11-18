"""
Chart Analysis Tool with Visual Pattern Recognition.

This module provides comprehensive chart analysis by integrating Chart-img API
for chart generation and LLM-based pattern analysis for automated technical
pattern recognition and visual analysis.

This is the main entry point that re-exports from specialized modules:
- chart_generator: Chart image generation
- chart_analysis: Pattern recognition and analysis
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from finwiz.tools.charts.chart_analysis import (
    InsightExtractor,
    PatternExtractor,
    SignalDeterminer,
    SupportResistanceExtractor,
    TrendAnalyzer,
    VolumeAnalyzer,
)
from finwiz.tools.charts.chart_generator import ChartGenerator
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class ChartPattern(BaseModel):
    """Identified chart pattern from visual analysis."""

    model_config = ConfigDict(extra="forbid")

    pattern_name: str = Field(..., description="Name of the identified pattern")
    pattern_type: str = Field(..., description="bullish, bearish, or neutral")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in pattern identification")
    description: str = Field(..., description="Detailed description of the pattern")
    price_target: float | None = Field(None, description="Potential price target if applicable")
    timeframe: str = Field(..., description="Timeframe of the pattern")
    completion_status: str = Field(..., description="forming, completed, or broken")


class SupportResistanceLine(BaseModel):
    """Visual support or resistance line identified from chart."""

    model_config = ConfigDict(extra="forbid")

    line_type: str = Field(..., description="support or resistance")
    price_level: float = Field(..., description="Price level of the line")
    strength: float = Field(..., ge=0.0, le=1.0, description="Strength of the line")
    touches: int = Field(..., ge=1, description="Number of times price touched the line")
    slope: str = Field(..., description="horizontal, ascending, or descending")
    description: str = Field(..., description="Description of the line significance")


class VolumeAnalysis(BaseModel):
    """Volume analysis from chart visualization."""

    model_config = ConfigDict(extra="forbid")

    volume_trend: str = Field(..., description="increasing, decreasing, or stable")
    volume_confirmation: bool = Field(..., description="Whether volume confirms price action")
    unusual_volume_periods: list[str] = Field(default_factory=list, description="Periods with unusual volume")
    volume_pattern: str = Field(..., description="Description of volume pattern")


class TrendAnalysis(BaseModel):
    """Trend analysis from visual chart inspection."""

    model_config = ConfigDict(extra="forbid")

    primary_trend: str = Field(..., description="uptrend, downtrend, or sideways")
    trend_strength: float = Field(..., ge=0.0, le=1.0, description="Strength of the trend")
    trend_duration: str = Field(..., description="short-term, medium-term, or long-term")
    trend_channels: list[str] = Field(default_factory=list, description="Identified trend channels")
    breakout_potential: float = Field(..., ge=0.0, le=1.0, description="Potential for trend breakout")


class ChartAnalysisResult(BaseModel):
    """Complete chart analysis result with visual insights."""

    model_config = ConfigDict(extra="forbid")

    ticker: str = Field(..., description="Analyzed ticker symbol")
    timeframe: str = Field(..., description="Chart timeframe analyzed")
    analysis_timestamp: datetime = Field(default_factory=datetime.now)
    chart_url: str = Field(..., description="URL or data URL of the analyzed chart")

    # Visual analysis components
    identified_patterns: list[ChartPattern] = Field(default_factory=list)
    support_resistance_lines: list[SupportResistanceLine] = Field(default_factory=list)
    volume_analysis: VolumeAnalysis
    trend_analysis: TrendAnalysis

    # Overall assessment
    overall_signal: str = Field(..., description="buy, sell, or neutral")
    signal_confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in the signal")
    key_insights: list[str] = Field(default_factory=list, description="Key visual insights")
    risk_factors: list[str] = Field(default_factory=list, description="Identified risk factors")


class ChartAnalyzer:
    """
    Advanced chart analyzer with visual pattern recognition.

    Integrates Chart-img API for chart generation and uses LLM-based analysis
    for automated pattern recognition, trend analysis, and visual insights.
    """

    # Pattern definitions for backward compatibility
    chart_patterns = PatternExtractor.CHART_PATTERNS

    # Default chart parameters
    default_width = 1200
    default_height = 800
    default_theme = "light"

    def __init__(self) -> None:
        """Initialize the chart analyzer."""
        self.chart_generator = ChartGenerator()

    def analyze_chart(
        self,
        ticker: str,
        timeframe: str = "6mo",
        interval: str = "1day",
        width: int | None = None,
        height: int | None = None,
    ) -> ChartAnalysisResult:
        """
        Perform comprehensive chart analysis with visual pattern recognition.

        Args:
            ticker: The ticker symbol to analyze
            timeframe: Time range for the chart (1mo, 3mo, 6mo, 1y, 5y, max)
            interval: Bar interval (1min, 5min, 1h, 1day)
            width: Chart width in pixels
            height: Chart height in pixels

        Returns:
            Complete chart analysis result

        """
        logger.info(f"Starting chart analysis for {ticker} ({timeframe})")

        # Generate chart image
        chart_url = self._generate_chart(
            ticker,
            timeframe,
            interval,
            width or self.default_width,
            height or self.default_height,
        )

        if chart_url.startswith("Error"):
            raise RuntimeError(f"Failed to generate chart: {chart_url}")

        # Perform visual analysis using LLM
        visual_analysis = self._analyze_chart_visually(ticker, chart_url, timeframe)

        # Extract patterns from analysis
        patterns = self._extract_patterns(visual_analysis)

        # Extract support/resistance lines
        sr_lines = self._extract_support_resistance(visual_analysis)

        # Analyze volume
        volume_analysis = self._analyze_volume(visual_analysis)

        # Analyze trend
        trend_analysis = self._analyze_trend(visual_analysis)

        # Determine overall signal
        overall_signal, confidence = self._determine_chart_signal(patterns, sr_lines, volume_analysis, trend_analysis)

        # Extract key insights and risks
        key_insights = self._extract_key_insights(visual_analysis)
        risk_factors = self._extract_risk_factors(visual_analysis)

        return ChartAnalysisResult(
            ticker=ticker,
            timeframe=timeframe,
            chart_url=chart_url,
            identified_patterns=patterns,
            support_resistance_lines=sr_lines,
            volume_analysis=volume_analysis,
            trend_analysis=trend_analysis,
            overall_signal=overall_signal,
            signal_confidence=confidence,
            key_insights=key_insights,
            risk_factors=risk_factors,
        )

    def _generate_chart(self, symbol: str, timeframe: str, interval: str, width: int, height: int) -> str:
        """Generate chart image using Chart-img API."""
        return self.chart_generator.generate_chart(symbol, timeframe, interval, width, height)

    def _analyze_chart_visually(self, ticker: str, chart_url: str, timeframe: str) -> str:
        """
        Analyze chart using LLM for pattern recognition.

        This is a placeholder for LLM integration. In a real implementation,
        this would send the chart image to an LLM with vision capabilities
        for detailed visual analysis.
        """
        # Simulated LLM analysis response for testing
        # In production, this would integrate with OpenAI GPT-4V or similar

        mock_analysis = f"""
        Chart Analysis for {ticker} ({timeframe}):

        TREND ANALYSIS:
        - Primary trend: The chart shows a clear uptrend over the analyzed period
        - Trend strength: Strong upward momentum with higher highs and higher lows
        - Trend duration: Medium-term uptrend lasting several months
        - Breakout potential: High potential for continued upward movement

        PATTERN IDENTIFICATION:
        - Cup and handle pattern forming in recent months with bullish implications
        - Triangle consolidation pattern visible in mid-period, successfully broken to upside
        - Flag continuation pattern after major price advance

        SUPPORT AND RESISTANCE:
        - Strong horizontal support at previous resistance level around $150
        - Ascending trendline support connecting recent lows
        - Resistance at psychological $200 level with multiple touches
        - Dynamic resistance from 50-day moving average

        VOLUME ANALYSIS:
        - Volume trend: Increasing volume on up moves, decreasing on pullbacks
        - Volume confirmation: Strong volume confirmation on breakouts
        - Unusual volume: Significant volume spike during recent breakout
        - Volume pattern: Healthy volume distribution supporting price action

        KEY INSIGHTS:
        - Bullish momentum remains intact with strong institutional support
        - Recent consolidation suggests preparation for next leg higher
        - Volume profile supports continued upward movement
        - Technical indicators align with bullish price action

        RISK FACTORS:
        - Potential resistance at psychological $200 level
        - Overbought conditions on shorter timeframes
        - Market volatility could impact momentum
        - Gap areas below current price may act as support/resistance
        """

        return mock_analysis

    def _extract_patterns(self, analysis_text: str) -> list[ChartPattern]:
        """Extract chart patterns from LLM analysis."""
        patterns_data = PatternExtractor.extract_patterns(analysis_text)
        return [ChartPattern(**p) for p in patterns_data]

    def _extract_support_resistance(self, analysis_text: str) -> list[SupportResistanceLine]:
        """Extract support and resistance levels from analysis."""
        sr_data = SupportResistanceExtractor.extract_levels(analysis_text)
        return [SupportResistanceLine(**s) for s in sr_data]

    def _analyze_volume(self, analysis_text: str) -> VolumeAnalysis:
        """Extract volume analysis from LLM response."""
        volume_data = VolumeAnalyzer.analyze_volume(analysis_text)
        return VolumeAnalysis(**volume_data)

    def _analyze_trend(self, analysis_text: str) -> TrendAnalysis:
        """Extract trend analysis from LLM response."""
        trend_data = TrendAnalyzer.analyze_trend(analysis_text)
        return TrendAnalysis(**trend_data)

    def _determine_chart_signal(
        self,
        patterns: list[ChartPattern],
        sr_lines: list[SupportResistanceLine],
        volume_analysis: VolumeAnalysis,
        trend_analysis: TrendAnalysis,
    ) -> tuple[str, float]:
        """Determine overall signal from chart analysis components."""
        # Convert Pydantic models to dicts for SignalDeterminer
        patterns_data = [
            {
                "pattern_name": p.pattern_name,
                "pattern_type": p.pattern_type,
                "confidence": p.confidence,
                "description": p.description,
            }
            for p in patterns
        ]

        sr_data = [
            {
                "line_type": s.line_type,
                "price_level": s.price_level,
                "strength": s.strength,
            }
            for s in sr_lines
        ]

        volume_data = {
            "volume_trend": volume_analysis.volume_trend,
            "volume_confirmation": volume_analysis.volume_confirmation,
        }

        trend_data = {
            "primary_trend": trend_analysis.primary_trend,
            "trend_strength": trend_analysis.trend_strength,
        }

        return SignalDeterminer.determine_signal(patterns_data, sr_data, volume_data, trend_data)

    def _extract_key_insights(self, analysis_text: str) -> list[str]:
        """Extract key insights from analysis."""
        return InsightExtractor.extract_key_insights(analysis_text)

    def _extract_risk_factors(self, analysis_text: str) -> list[str]:
        """Extract risk factors from analysis."""
        return InsightExtractor.extract_risk_factors(analysis_text)

    def _get_price_context(self, text: str, price: str) -> str:
        """Get context around a price mention for classification."""
        return SupportResistanceExtractor._get_price_context(text, price)

    def generate_chart_url(
        self,
        symbol: str,
        timeframe: str = "6mo",
        interval: str = "1day",
        width: int = 900,
        height: int = 500,
        theme: str = "light",
    ) -> str:
        """
        Generate a chart image URL for embedding.

        This is a convenience method that just generates the chart without analysis.
        """
        return self._generate_chart(symbol, timeframe, interval, width, height)
