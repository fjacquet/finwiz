"""Sentiment scoring engine for Phase 14.

Computes a normalized sentiment score from NewsSentimentResult data
with temporal decay weighting and confidence metrics.
"""

from __future__ import annotations

import logging
from typing import Any

from finwiz.data.news_utils import (
    calculate_sentiment_confidence,
    temporal_decay_weight,
)
from finwiz.schemas.sentiment import NewsSentimentResult, SentimentScore
from finwiz.scoring.thresholds import ScoringThresholds, get_thresholds

logger = logging.getLogger(__name__)


class SentimentScorer:
    """Score sentiment from aggregated news data.

    Follows the component scorer pattern (FundamentalScorer, TechnicalScorer, RiskScorer).
    Receives raw data dict containing news_sentiment, returns (score_or_None, details_dict).

    Key behaviors:
    - No news data -> returns (None, {"reason": "no_news_data"})
    - Zero articles -> returns (None, {"reason": "no_articles"})
    - Has articles -> computes temporal-decay-weighted sentiment + confidence
    """

    def __init__(self, thresholds: ScoringThresholds | None = None) -> None:
        self.thresholds = thresholds or get_thresholds()

    def calculate_sentiment_score(self, data: dict[str, Any]) -> tuple[float | None, dict[str, Any]]:
        """Calculate sentiment score from raw analysis data.

        Args:
            data: Raw data dict. Expects data["news_sentiment"] to be either:
                  - A dict (from NewsSentimentResult.model_dump())
                  - None (no sentiment data collected)

        Returns:
            Tuple of (score_or_None, details_dict).
            score is in [-1.0, +1.0] or None if no data.
            details contains scoring breakdown.
        """
        details: dict[str, Any] = {}

        # Extract news sentiment data
        news_sentiment_raw = data.get("news_sentiment")
        if news_sentiment_raw is None:
            details["reason"] = "no_news_data"
            logger.debug("No news sentiment data available")
            return None, details

        # Parse into NewsSentimentResult if it's a dict
        try:
            if isinstance(news_sentiment_raw, dict):
                sentiment_result = NewsSentimentResult(**news_sentiment_raw)
            elif isinstance(news_sentiment_raw, NewsSentimentResult):
                sentiment_result = news_sentiment_raw
            else:
                details["reason"] = "invalid_news_data_type"
                details["type"] = type(news_sentiment_raw).__name__
                logger.warning("Unexpected news_sentiment type: %s", type(news_sentiment_raw))
                return None, details
        except Exception as e:
            details["reason"] = "parse_error"
            details["error"] = str(e)
            logger.warning("Failed to parse news sentiment: %s", e)
            return None, details

        # No articles = no sentiment (SENT-05: None, not 0.0)
        if sentiment_result.article_count == 0 or not sentiment_result.articles:
            details["reason"] = "no_articles"
            details["article_count"] = 0
            logger.debug("No articles available for sentiment scoring")
            return None, details

        # Compute temporal-decay-weighted sentiment (SENT-04)
        score, decay_details = self._compute_decay_weighted_sentiment(sentiment_result)
        details.update(decay_details)

        # Compute confidence (SENT-03)
        source_count = len(sentiment_result.source_breakdown)
        confidence = calculate_sentiment_confidence(
            article_count=sentiment_result.article_count,
            source_count=source_count,
            data_freshness_hours=sentiment_result.data_freshness_hours,
            min_articles_for_high_confidence=self.thresholds.sentiment_min_articles_for_high_confidence,
            min_sources_for_max_diversity=self.thresholds.sentiment_min_sources_for_max_diversity,
            max_freshness_hours=self.thresholds.sentiment_max_freshness_hours,
        )

        details["confidence"] = confidence
        details["source_count"] = source_count
        details["article_count"] = sentiment_result.article_count
        details["data_freshness_hours"] = sentiment_result.data_freshness_hours

        logger.info(
            "Sentiment score for %s: score=%.4f, confidence=%.4f, articles=%d, sources=%d",
            sentiment_result.ticker,
            score,
            confidence,
            sentiment_result.article_count,
            source_count,
        )

        return score, details

    def _compute_decay_weighted_sentiment(self, sentiment_result: NewsSentimentResult) -> tuple[float, dict[str, Any]]:
        """Compute temporal-decay-weighted sentiment score.

        Each article's sentiment is weighted by:
        1. Source reliability (from Phase 13)
        2. Temporal decay (exponential, configurable half-life)

        Args:
            sentiment_result: Aggregated news sentiment data

        Returns:
            Tuple of (weighted_score, details_dict)
        """
        details: dict[str, Any] = {"temporal_decay_applied": True}
        half_life = self.thresholds.sentiment_half_life_hours

        total_weight = 0.0
        weighted_sum = 0.0
        decay_weights: list[float] = []

        for article in sentiment_result.articles:
            if article.sentiment_score is None:
                continue

            decay = temporal_decay_weight(article.published_at, half_life)
            combined_weight = article.source_reliability * decay
            weighted_sum += article.sentiment_score * combined_weight
            total_weight += combined_weight
            decay_weights.append(decay)

        if total_weight == 0:
            details["reason"] = "no_scored_articles"
            details["temporal_decay_applied"] = False
            return 0.0, details

        score = weighted_sum / total_weight
        # Clamp to [-1, 1] for safety
        score = max(-1.0, min(1.0, score))

        details["half_life_hours"] = half_life
        details["avg_decay_weight"] = sum(decay_weights) / len(decay_weights) if decay_weights else 0.0
        details["scored_article_count"] = len(decay_weights)

        return score, details

    def build_sentiment_score(self, ticker: str, data: dict[str, Any]) -> SentimentScore:
        """Build a complete SentimentScore object from raw data.

        Convenience method that wraps calculate_sentiment_score() and returns
        a validated SentimentScore Pydantic model.

        Args:
            ticker: Ticker symbol
            data: Raw data dict with news_sentiment

        Returns:
            SentimentScore with score, confidence, and details
        """
        score, details = self.calculate_sentiment_score(data)

        return SentimentScore(
            ticker=ticker,
            score=score,
            confidence=details.get("confidence"),
            article_count=details.get("article_count", 0),
            source_count=details.get("source_count", 0),
            temporal_decay_applied=details.get("temporal_decay_applied", False),
            data_freshness_hours=details.get("data_freshness_hours", 0.0),
            details=details,
        )
