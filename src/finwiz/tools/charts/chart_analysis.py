"""
Chart analysis and pattern recognition utilities.

This module provides LLM-based chart analysis for pattern recognition,
trend analysis, and visual insights.
"""

import re
from typing import Any

from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class PatternExtractor:
    """Extracts chart patterns from analysis text."""

    # Pattern definitions
    CHART_PATTERNS = {
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

    @staticmethod
    def extract_patterns(analysis_text: str) -> list[dict[str, Any]]:
        """
        Extract chart patterns from LLM analysis.

        Args:
            analysis_text: Analysis text from LLM

        Returns:
            List of identified patterns

        """
        patterns = []
        analysis_lower = analysis_text.lower()

        for pattern_name, pattern_info in PatternExtractor.CHART_PATTERNS.items():
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
                    {
                        "pattern_name": pattern_name.replace("_", " ").title(),
                        "pattern_type": pattern_info["type"],
                        "confidence": confidence,
                        "description": pattern_info["description"],
                        "timeframe": "medium-term",
                        "completion_status": completion_status,
                    }
                )

        return patterns


class SupportResistanceExtractor:
    """Extracts support and resistance levels from analysis."""

    @staticmethod
    def extract_levels(analysis_text: str) -> list[dict[str, Any]]:
        """
        Extract support and resistance levels from analysis.

        Args:
            analysis_text: Analysis text from LLM

        Returns:
            List of support/resistance levels

        """
        lines = []

        # Look for price levels mentioned in analysis
        price_pattern = r"\$(\d+(?:\.\d+)?)"
        prices = re.findall(price_pattern, analysis_text)

        for price_str in prices:
            price = float(price_str)

            # Determine if it's support or resistance based on context
            price_context = SupportResistanceExtractor._get_price_context(analysis_text, price_str)

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
                {
                    "line_type": line_type,
                    "price_level": price,
                    "strength": strength,
                    "touches": 2,  # Default assumption
                    "slope": slope,
                    "description": f"{line_type.title()} level at ${price}",
                }
            )

        return lines

    @staticmethod
    def _get_price_context(text: str, price: str) -> str:
        """Get context around a price mention for classification."""
        # Find the sentence containing the price
        # Use regex to split on sentence boundaries while preserving decimal points in prices
        sentences = re.split(r"\.(?!\d)", text)  # Split on periods not followed by digits
        for sentence in sentences:
            if f"${price}" in sentence:
                return sentence.strip()
        return ""


class VolumeAnalyzer:
    """Analyzes volume patterns from chart analysis."""

    @staticmethod
    def analyze_volume(analysis_text: str) -> dict[str, Any]:
        """
        Extract volume analysis from LLM response.

        Args:
            analysis_text: Analysis text from LLM

        Returns:
            Volume analysis dictionary

        """
        analysis_lower = analysis_text.lower()

        # Determine volume trend
        if "increasing volume" in analysis_lower or "rising volume" in analysis_lower:
            volume_trend = "increasing"
        elif "decreasing volume" in analysis_lower or "declining volume" in analysis_lower:
            volume_trend = "decreasing"
        else:
            volume_trend = "stable"

        # Check volume confirmation
        volume_confirmation = "volume confirmation" in analysis_lower or "confirmed by volume" in analysis_lower or "strong volume" in analysis_lower

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

        return {
            "volume_trend": volume_trend,
            "volume_confirmation": volume_confirmation,
            "unusual_volume_periods": unusual_periods,
            "volume_pattern": volume_pattern,
        }


class TrendAnalyzer:
    """Analyzes trend patterns from chart analysis."""

    @staticmethod
    def analyze_trend(analysis_text: str) -> dict[str, Any]:
        """
        Extract trend analysis from LLM response.

        Args:
            analysis_text: Analysis text from LLM

        Returns:
            Trend analysis dictionary

        """
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

        return {
            "primary_trend": primary_trend,
            "trend_strength": trend_strength,
            "trend_duration": trend_duration,
            "trend_channels": trend_channels,
            "breakout_potential": breakout_potential,
        }


class SignalDeterminer:
    """Determines overall chart signal from analysis components."""

    @staticmethod
    def determine_signal(
        patterns: list[dict[str, Any]],
        sr_lines: list[dict[str, Any]],
        volume_analysis: dict[str, Any],
        trend_analysis: dict[str, Any],
    ) -> tuple[str, float]:
        """
        Determine overall signal from chart analysis components.

        Args:
            patterns: List of identified patterns
            sr_lines: List of support/resistance lines
            volume_analysis: Volume analysis dictionary
            trend_analysis: Trend analysis dictionary

        Returns:
            Tuple of (signal, confidence)

        """
        bullish_signals = 0.0
        bearish_signals = 0.0
        total_weight = 0.0

        # Weight pattern signals
        for pattern in patterns:
            weight = pattern.get("confidence", 0.5)
            if pattern.get("pattern_type") == "bullish":
                bullish_signals += weight
            elif pattern.get("pattern_type") == "bearish":
                bearish_signals += weight
            total_weight += weight

        # Weight trend analysis
        trend_weight = trend_analysis.get("trend_strength", 0.5)
        if trend_analysis.get("primary_trend") == "uptrend":
            bullish_signals += trend_weight
        elif trend_analysis.get("primary_trend") == "downtrend":
            bearish_signals += trend_weight
        total_weight += trend_weight

        # Weight volume confirmation
        if volume_analysis.get("volume_confirmation"):
            if trend_analysis.get("primary_trend") == "uptrend":
                bullish_signals += 0.3
            elif trend_analysis.get("primary_trend") == "downtrend":
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


class InsightExtractor:
    """Extracts insights and risk factors from analysis."""

    @staticmethod
    def extract_key_insights(analysis_text: str) -> list[str]:
        """
        Extract key insights from analysis.

        Args:
            analysis_text: Analysis text from LLM

        Returns:
            List of key insights

        """
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

    @staticmethod
    def extract_risk_factors(analysis_text: str) -> list[str]:
        """
        Extract risk factors from analysis.

        Args:
            analysis_text: Analysis text from LLM

        Returns:
            List of risk factors

        """
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
