"""
Chart Analysis Tool with Visual Pattern Recognition.

This module provides comprehensive chart analysis by integrating Chart-img API
for chart generation and LLM-based pattern analysis for automated technical
pattern recognition and visual analysis.
"""

from __future__ import annotations

import base64
import os
import re
from datetime import datetime

import requests
from pydantic import BaseModel, ConfigDict, Field

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

    def __init__(self) -> None:
        """Initialize the chart analyzer."""
        self.api_key = os.getenv("CHART_IMG_API_KEY")
        self.base_url = os.getenv("CHART_IMG_BASE_URL", "https://api.chart-img.com/v1/stock")

        # Chart generation parameters
        self.default_width = 1200
        self.default_height = 800
        self.default_theme = "light"

        # Pattern recognition keywords and descriptions
        self.chart_patterns = {
            "head_and_shoulders": {
                "type": "bearish",
                "description": "Head and shoulders reversal pattern",
                "keywords": ["head", "shoulders", "neckline", "reversal"],
            },
            "inverse_head_and_shoulders": {
                "type": "bullish",
                "description": "Inverse head and shoulders reversal pattern",
                "keywords": ["inverse", "head", "shoulders", "bullish", "reversal"],
            },
            "double_top": {
                "type": "bearish",
                "description": "Double top reversal pattern",
                "keywords": ["double", "top", "peak", "resistance", "reversal"],
            },
            "double_bottom": {
                "type": "bullish",
                "description": "Double bottom reversal pattern",
                "keywords": ["double", "bottom", "support", "bullish", "reversal"],
            },
            "triangle": {
                "type": "neutral",
                "description": "Triangle consolidation pattern",
                "keywords": ["triangle", "consolidation", "breakout", "convergence"],
            },
            "flag": {
                "type": "continuation",
                "description": "Flag continuation pattern",
                "keywords": ["flag", "continuation", "pole", "consolidation"],
            },
            "wedge": {
                "type": "reversal",
                "description": "Wedge pattern",
                "keywords": ["wedge", "converging", "trendlines"],
            },
            "cup_and_handle": {
                "type": "bullish",
                "description": "Cup and handle bullish pattern",
                "keywords": ["cup", "handle", "rounded", "bottom", "bullish"],
            },
        }

    def analyze_chart(
        self,
        ticker: str,
        timeframe: str = "6mo",
        interval: str = "1day",
        width: int = None,
        height: int = None,
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

        if not self.api_key:
            raise ValueError("CHART_IMG_API_KEY environment variable not set")

        # Generate chart image
        chart_url = self._generate_chart(ticker, timeframe, interval, width or self.default_width, height or self.default_height)

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
        headers = {"x-api-key": self.api_key}
        params = {
            "symbol": symbol,
            "interval": interval,
            "range": timeframe,
            "width": width,
            "height": height,
            "theme": self.default_theme,
        }

        try:
            response = requests.get(self.base_url, headers=headers, params=params, timeout=30)
            response.raise_for_status()

            content_type = response.headers.get("Content-Type", "image/png")
            b64_content = base64.b64encode(response.content).decode("ascii")
            return f"data:{content_type};base64,{b64_content}"

        except Exception as e:
            logger.error(f"Error generating chart for {symbol}: {e}")
            return f"Error generating chart image for {symbol}: {e}"

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
        patterns = []
        analysis_lower = analysis_text.lower()

        for pattern_name, pattern_info in self.chart_patterns.items():
            # Check if pattern keywords are mentioned in analysis
            keyword_matches = sum(1 for keyword in pattern_info["keywords"] if keyword in analysis_lower)

            if keyword_matches >= 2:  # Require at least 2 keyword matches
                # Extract confidence based on context
                confidence = min(0.9, 0.5 + (keyword_matches * 0.1))

                # Determine completion status
                completion_status = "forming"
                if "completed" in analysis_lower or "broken" in analysis_lower:
                    completion_status = "completed"
                elif "breaking" in analysis_lower:
                    completion_status = "broken"

                patterns.append(
                    ChartPattern(
                        pattern_name=pattern_name.replace("_", " ").title(),
                        pattern_type=pattern_info["type"],
                        confidence=confidence,
                        description=pattern_info["description"],
                        timeframe="medium-term",
                        completion_status=completion_status,
                    )
                )

        return patterns

    def _extract_support_resistance(self, analysis_text: str) -> list[SupportResistanceLine]:
        """Extract support and resistance levels from analysis."""
        lines = []

        # Look for price levels mentioned in analysis
        price_pattern = r"\$(\d+(?:\.\d+)?)"
        prices = re.findall(price_pattern, analysis_text)

        analysis_text.lower()

        for price_str in prices:
            price = float(price_str)

            # Determine if it's support or resistance based on context
            price_context = self._get_price_context(analysis_text, price_str)

            if "support" in price_context.lower():
                line_type = "support"
                strength = 0.7 if "strong" in price_context.lower() else 0.5
            elif "resistance" in price_context.lower():
                line_type = "resistance"
                strength = 0.7 if "strong" in price_context.lower() else 0.5
            else:
                continue  # Skip if not clearly support or resistance

            # Determine slope
            slope = "horizontal"
            if "ascending" in price_context.lower() or "rising" in price_context.lower():
                slope = "ascending"
            elif "descending" in price_context.lower() or "falling" in price_context.lower():
                slope = "descending"

            lines.append(
                SupportResistanceLine(
                    line_type=line_type,
                    price_level=price,
                    strength=strength,
                    touches=2,  # Default assumption
                    slope=slope,
                    description=f"{line_type.title()} level at ${price}",
                )
            )

        return lines

    def _analyze_volume(self, analysis_text: str) -> VolumeAnalysis:
        """Extract volume analysis from LLM response."""
        analysis_lower = analysis_text.lower()

        # Determine volume trend
        if "increasing volume" in analysis_lower or "rising volume" in analysis_lower:
            volume_trend = "increasing"
        elif "decreasing volume" in analysis_lower or "declining volume" in analysis_lower:
            volume_trend = "decreasing"
        else:
            volume_trend = "stable"

        # Check volume confirmation
        volume_confirmation = (
            "volume confirmation" in analysis_lower or "confirmed by volume" in analysis_lower or "strong volume" in analysis_lower
        )

        # Extract unusual volume periods
        unusual_periods = []
        if "volume spike" in analysis_lower:
            unusual_periods.append("Recent volume spike identified")
        if "unusual volume" in analysis_lower:
            unusual_periods.append("Unusual volume activity detected")

        # Extract volume pattern description
        volume_pattern = "Normal volume distribution"
        if "healthy volume" in analysis_lower:
            volume_pattern = "Healthy volume distribution supporting price action"
        elif "weak volume" in analysis_lower:
            volume_pattern = "Weak volume raises concerns about sustainability"

        return VolumeAnalysis(
            volume_trend=volume_trend,
            volume_confirmation=volume_confirmation,
            unusual_volume_periods=unusual_periods,
            volume_pattern=volume_pattern,
        )

    def _analyze_trend(self, analysis_text: str) -> TrendAnalysis:
        """Extract trend analysis from LLM response."""
        analysis_lower = analysis_text.lower()

        # Determine primary trend
        if "uptrend" in analysis_lower or "bullish" in analysis_lower:
            primary_trend = "uptrend"
        elif "downtrend" in analysis_lower or "bearish" in analysis_lower:
            primary_trend = "downtrend"
        else:
            primary_trend = "sideways"

        # Determine trend strength
        if "strong" in analysis_lower and primary_trend != "sideways":
            trend_strength = 0.8
        elif "weak" in analysis_lower:
            trend_strength = 0.3
        else:
            trend_strength = 0.6

        # Determine trend duration
        if "long-term" in analysis_lower:
            trend_duration = "long-term"
        elif "short-term" in analysis_lower:
            trend_duration = "short-term"
        else:
            trend_duration = "medium-term"

        # Extract trend channels
        trend_channels = []
        if "trendline" in analysis_lower:
            trend_channels.append("Trendline channel identified")
        if "channel" in analysis_lower:
            trend_channels.append("Price channel formation")

        # Determine breakout potential
        breakout_potential = 0.5  # Default
        if "breakout potential" in analysis_lower:
            if "high" in analysis_lower:
                breakout_potential = 0.8
            elif "low" in analysis_lower:
                breakout_potential = 0.2

        return TrendAnalysis(
            primary_trend=primary_trend,
            trend_strength=trend_strength,
            trend_duration=trend_duration,
            trend_channels=trend_channels,
            breakout_potential=breakout_potential,
        )

    def _determine_chart_signal(
        self,
        patterns: list[ChartPattern],
        sr_lines: list[SupportResistanceLine],
        volume_analysis: VolumeAnalysis,
        trend_analysis: TrendAnalysis,
    ) -> tuple[str, float]:
        """Determine overall signal from chart analysis components."""
        bullish_signals = 0
        bearish_signals = 0
        total_weight = 0

        # Weight pattern signals
        for pattern in patterns:
            weight = pattern.confidence
            if pattern.pattern_type == "bullish":
                bullish_signals += weight
            elif pattern.pattern_type == "bearish":
                bearish_signals += weight
            total_weight += weight

        # Weight trend analysis
        trend_weight = trend_analysis.trend_strength
        if trend_analysis.primary_trend == "uptrend":
            bullish_signals += trend_weight
        elif trend_analysis.primary_trend == "downtrend":
            bearish_signals += trend_weight
        total_weight += trend_weight

        # Weight volume confirmation
        if volume_analysis.volume_confirmation:
            if trend_analysis.primary_trend == "uptrend":
                bullish_signals += 0.3
            elif trend_analysis.primary_trend == "downtrend":
                bearish_signals += 0.3
            total_weight += 0.3

        # Determine signal
        if total_weight == 0:
            return "neutral", 0.0

        signal_ratio = (bullish_signals - bearish_signals) / total_weight
        confidence = min(1.0, total_weight / 2.0)

        if signal_ratio > 0.3:
            return "buy", confidence
        elif signal_ratio < -0.3:
            return "sell", confidence
        else:
            return "neutral", confidence * 0.7

    def _extract_key_insights(self, analysis_text: str) -> list[str]:
        """Extract key insights from analysis."""
        insights = []

        # Look for insights section
        lines = analysis_text.split("\n")
        in_insights_section = False

        for line in lines:
            line = line.strip()
            if "key insights" in line.lower():
                in_insights_section = True
                continue
            elif in_insights_section and line.startswith("-"):
                insights.append(line[1:].strip())
            elif in_insights_section and line and not line.startswith("-"):
                break  # End of insights section

        return insights[:5]  # Limit to top 5 insights

    def _extract_risk_factors(self, analysis_text: str) -> list[str]:
        """Extract risk factors from analysis."""
        risks = []

        # Look for risk factors section
        lines = analysis_text.split("\n")
        in_risk_section = False

        for line in lines:
            line = line.strip()
            if "risk factors" in line.lower():
                in_risk_section = True
                continue
            elif in_risk_section and line.startswith("-"):
                risks.append(line[1:].strip())
            elif in_risk_section and line and not line.startswith("-"):
                break  # End of risk section

        return risks[:5]  # Limit to top 5 risks

    def _get_price_context(self, text: str, price: str) -> str:
        """Get context around a price mention for classification."""
        # Find the sentence containing the price
        # Use regex to split on sentence boundaries while preserving decimal points in prices
        import re

        sentences = re.split(r"\.(?!\d)", text)  # Split on periods not followed by digits
        for sentence in sentences:
            if f"${price}" in sentence:
                return sentence.strip()
        return ""

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
