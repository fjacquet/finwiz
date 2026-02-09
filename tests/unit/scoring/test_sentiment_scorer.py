"""Tests for SentimentScorer (Phase 14 - SENT-01 through SENT-05)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from finwiz.schemas.sentiment import NewsArticle, NewsSentimentResult, SentimentScore
from finwiz.scoring.sentiment_scorer import SentimentScorer
from finwiz.scoring.thresholds import ScoringThresholds


@pytest.fixture
def scorer() -> SentimentScorer:
    return SentimentScorer()


@pytest.fixture
def custom_scorer() -> SentimentScorer:
    return SentimentScorer(thresholds=ScoringThresholds(sentiment_half_life_hours=24.0))


def _make_article(
    title: str = "Test headline",
    source: str = "finnhub",
    sentiment_score: float | None = 0.5,
    hours_ago: float = 0.0,
    reliability: float = 0.8,
    ticker: str = "AAPL",
) -> NewsArticle:
    published = datetime.now(tz=UTC) - timedelta(hours=hours_ago)
    return NewsArticle(
        title=title,
        url="https://example.com/article",
        source=source,
        published_at=published,
        ticker=ticker,
        sentiment_score=sentiment_score,
        sentiment_label="bullish" if (sentiment_score or 0) > 0.05 else ("bearish" if (sentiment_score or 0) < -0.05 else "neutral"),
        source_reliability=reliability,
    )


def _make_sentiment_data(articles: list[NewsArticle], ticker: str = "AAPL") -> dict[str, Any]:
    sources: dict[str, int] = {}
    for a in articles:
        sources[a.source] = sources.get(a.source, 0) + 1
    result = NewsSentimentResult(
        ticker=ticker,
        articles=articles,
        aggregate_sentiment=0.0,
        weighted_sentiment=0.0,
        article_count=len(articles),
        source_breakdown=sources,
        data_freshness_hours=0.5,
    )
    return {"news_sentiment": result.model_dump(mode="json")}


# --- SENT-05: No-news handling ---


class TestNoNewsHandling:
    def test_no_sentiment_key(self, scorer: SentimentScorer):
        score, details = scorer.calculate_sentiment_score({})
        assert score is None
        assert details["reason"] == "no_news_data"

    def test_sentiment_is_none(self, scorer: SentimentScorer):
        score, details = scorer.calculate_sentiment_score({"news_sentiment": None})
        assert score is None
        assert details["reason"] == "no_news_data"

    def test_zero_articles(self, scorer: SentimentScorer):
        data = _make_sentiment_data([])
        score, details = scorer.calculate_sentiment_score(data)
        assert score is None
        assert details["reason"] == "no_articles"

    def test_build_sentiment_score_no_news(self, scorer: SentimentScorer):
        result = scorer.build_sentiment_score("AAPL", {})
        assert isinstance(result, SentimentScore)
        assert result.score is None
        assert result.confidence is None
        assert result.article_count == 0


# --- SENT-01/SENT-02: Sentiment scoring ---


class TestSentimentScoring:
    def test_positive_sentiment(self, scorer: SentimentScorer):
        articles = [_make_article(sentiment_score=0.8), _make_article(sentiment_score=0.6)]
        data = _make_sentiment_data(articles)
        score, details = scorer.calculate_sentiment_score(data)
        assert score is not None
        assert 0.5 < score <= 1.0

    def test_negative_sentiment(self, scorer: SentimentScorer):
        articles = [_make_article(sentiment_score=-0.7), _make_article(sentiment_score=-0.5)]
        data = _make_sentiment_data(articles)
        score, details = scorer.calculate_sentiment_score(data)
        assert score is not None
        assert -1.0 <= score < -0.3

    def test_mixed_sentiment(self, scorer: SentimentScorer):
        articles = [_make_article(sentiment_score=0.8), _make_article(sentiment_score=-0.8)]
        data = _make_sentiment_data(articles)
        score, details = scorer.calculate_sentiment_score(data)
        assert score is not None
        assert -0.2 <= score <= 0.2  # Near neutral

    def test_score_clamped_to_range(self, scorer: SentimentScorer):
        articles = [_make_article(sentiment_score=1.0)]
        data = _make_sentiment_data(articles)
        score, _ = scorer.calculate_sentiment_score(data)
        assert score is not None
        assert -1.0 <= score <= 1.0

    def test_articles_without_sentiment_score_excluded(self, scorer: SentimentScorer):
        articles = [_make_article(sentiment_score=None), _make_article(sentiment_score=0.7)]
        data = _make_sentiment_data(articles)
        score, details = scorer.calculate_sentiment_score(data)
        assert score is not None
        assert score == pytest.approx(0.7, abs=0.1)


# --- SENT-04: Temporal decay ---


class TestTemporalDecay:
    def test_recent_article_weighted_more(self, scorer: SentimentScorer):
        recent = _make_article(sentiment_score=0.8, hours_ago=1)
        old = _make_article(sentiment_score=-0.8, hours_ago=96)
        data = _make_sentiment_data([recent, old])
        score, details = scorer.calculate_sentiment_score(data)
        assert score is not None
        assert score > 0  # Recent positive should dominate

    def test_decay_applied_flag(self, scorer: SentimentScorer):
        articles = [_make_article(sentiment_score=0.5)]
        data = _make_sentiment_data(articles)
        _, details = scorer.calculate_sentiment_score(data)
        assert details.get("temporal_decay_applied") is True

    def test_custom_half_life(self, custom_scorer: SentimentScorer):
        articles = [_make_article(sentiment_score=0.5, hours_ago=24)]
        data = _make_sentiment_data(articles)

        # Default scorer uses 48h half-life
        scorer_default = SentimentScorer()
        _, details_default = scorer_default.calculate_sentiment_score(data)
        assert details_default.get("half_life_hours") == 48.0

        _, details_custom = custom_scorer.calculate_sentiment_score(data)
        assert details_custom.get("half_life_hours") == 24.0


# --- SENT-03: Confidence metric ---


class TestConfidenceMetric:
    def test_high_confidence_many_articles(self, scorer: SentimentScorer):
        articles = [_make_article(sentiment_score=0.5, source=f"source_{i}") for i in range(10)]
        data = _make_sentiment_data(articles)
        _, details = scorer.calculate_sentiment_score(data)
        assert details["confidence"] > 0.7

    def test_low_confidence_few_articles(self, scorer: SentimentScorer):
        articles = [_make_article(sentiment_score=0.5)]
        data = _make_sentiment_data(articles)
        _, details = scorer.calculate_sentiment_score(data)
        assert details["confidence"] < 0.7

    def test_confidence_in_valid_range(self, scorer: SentimentScorer):
        articles = [_make_article(sentiment_score=0.5)]
        data = _make_sentiment_data(articles)
        _, details = scorer.calculate_sentiment_score(data)
        assert 0.0 <= details["confidence"] <= 1.0


# --- Source reliability weighting (SENT-02) ---


class TestSourceReliabilityWeighting:
    def test_reliable_source_weighted_more(self, scorer: SentimentScorer):
        reliable = _make_article(sentiment_score=0.8, reliability=0.95, source="reuters")
        unreliable = _make_article(sentiment_score=-0.8, reliability=0.40, source="unknown")
        data = _make_sentiment_data([reliable, unreliable])
        score, _ = scorer.calculate_sentiment_score(data)
        assert score is not None
        assert score > 0  # Reliable positive should dominate


# --- build_sentiment_score convenience method ---


class TestBuildSentimentScore:
    def test_returns_pydantic_model(self, scorer: SentimentScorer):
        articles = [_make_article(sentiment_score=0.5)]
        data = _make_sentiment_data(articles)
        result = scorer.build_sentiment_score("AAPL", data)
        assert isinstance(result, SentimentScore)
        assert result.ticker == "AAPL"
        assert result.score is not None
        assert result.confidence is not None
        assert result.article_count >= 1

    def test_invalid_data_type_handled(self, scorer: SentimentScorer):
        score, details = scorer.calculate_sentiment_score({"news_sentiment": 12345})
        assert score is None
        assert details["reason"] == "invalid_news_data_type"
