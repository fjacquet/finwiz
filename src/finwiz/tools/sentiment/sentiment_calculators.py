"""
Sentiment calculation utilities for multi-source sentiment analysis.

This module provides core sentiment calculation functions including keyword-based
sentiment scoring, weighted sentiment aggregation, and confidence calculations.
"""

from __future__ import annotations

from typing import Any

from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class SentimentCalculators:
    """Utilities for calculating sentiment scores from various data sources."""

    def __init__(self, bullish_keywords: list[str], bearish_keywords: list[str]) -> None:
        """
        Initialize sentiment calculators with keyword lists.

        Args:
            bullish_keywords: List of keywords indicating positive sentiment
            bearish_keywords: List of keywords indicating negative sentiment
        """
        self.bullish_keywords = bullish_keywords
        self.bearish_keywords = bearish_keywords

    def calculate_keyword_sentiment(self, text: str) -> float:
        """
        Calculate sentiment score using keyword analysis.

        Args:
            text: Text to analyze for sentiment

        Returns:
            Sentiment score between -1.0 (very negative) and 1.0 (very positive)
        """
        text_lower = text.lower()

        bullish_count = sum(1 for keyword in self.bullish_keywords if keyword in text_lower)
        bearish_count = sum(1 for keyword in self.bearish_keywords if keyword in text_lower)

        if bullish_count == 0 and bearish_count == 0:
            return 0.0

        # Calculate sentiment score
        total_keywords = bullish_count + bearish_count
        sentiment_strength = abs(bullish_count - bearish_count) / total_keywords

        if bullish_count > bearish_count:
            return min(0.8, sentiment_strength)
        elif bearish_count > bullish_count:
            return max(-0.8, -sentiment_strength)
        else:
            return 0.0

    def calculate_weighted_sentiment(self, sources: list[dict[str, Any]]) -> float:
        """
        Calculate weighted average sentiment across multiple sources.

        Args:
            sources: List of source dictionaries with sentiment_score, confidence, and weight

        Returns:
            Weighted sentiment score between -1.0 and 1.0
        """
        if not sources:
            return 0.0

        weighted_sum = 0.0
        total_weight = 0.0

        for source in sources:
            weight = source["weight"] * source["confidence"]
            weighted_sum += source["sentiment_score"] * weight
            total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else 0.0

    def calculate_confidence(self, sources: list[dict[str, Any]], total_articles: int) -> float:
        """
        Calculate overall confidence in the sentiment analysis.

        Args:
            sources: List of source dictionaries with confidence values
            total_articles: Total number of articles analyzed

        Returns:
            Confidence score between 0.0 and 1.0
        """
        if not sources:
            return 0.0

        # Base confidence on number of sources and articles
        source_confidence = len(sources) / 3.0  # Max 3 sources
        article_confidence = min(1.0, total_articles / 30.0)  # Optimal around 30 articles

        # Weight by individual source confidences
        avg_source_confidence = sum(s["confidence"] for s in sources) / len(sources)

        return source_confidence * 0.3 + article_confidence * 0.3 + avg_source_confidence * 0.4
