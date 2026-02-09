"""Unit tests for sentiment schemas (NewsArticle, NewsSentimentResult)."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from finwiz.schemas.sentiment import NewsArticle, NewsSentimentResult


class TestNewsArticle:
    """Tests for NewsArticle schema validation."""

    def _make_article(self, **overrides) -> NewsArticle:
        defaults = {
            "title": "Apple beats earnings expectations",
            "url": "https://example.com/article",
            "source": "finnhub",
            "published_at": datetime(2026, 1, 15, 10, 30),
            "ticker": "AAPL",
        }
        defaults.update(overrides)
        return NewsArticle(**defaults)

    def test_valid_article(self):
        a = self._make_article()
        assert a.title == "Apple beats earnings expectations"
        assert a.ticker == "AAPL"
        assert a.source_reliability == 1.0
        assert a.sentiment_score is None
        assert a.sentiment_label is None

    def test_ticker_uppercased(self):
        a = self._make_article(ticker="aapl")
        assert a.ticker == "AAPL"

    def test_sentiment_score_boundaries(self):
        a = self._make_article(sentiment_score=-1.0)
        assert a.sentiment_score == -1.0
        a = self._make_article(sentiment_score=1.0)
        assert a.sentiment_score == 1.0

    def test_sentiment_score_out_of_range(self):
        with pytest.raises(ValidationError):
            self._make_article(sentiment_score=1.5)
        with pytest.raises(ValidationError):
            self._make_article(sentiment_score=-1.1)

    def test_source_reliability_boundaries(self):
        a = self._make_article(source_reliability=0.0)
        assert a.source_reliability == 0.0
        a = self._make_article(source_reliability=1.0)
        assert a.source_reliability == 1.0

    def test_source_reliability_out_of_range(self):
        with pytest.raises(ValidationError):
            self._make_article(source_reliability=1.5)
        with pytest.raises(ValidationError):
            self._make_article(source_reliability=-0.1)

    def test_empty_title_rejected(self):
        with pytest.raises(ValidationError):
            self._make_article(title="")

    def test_extra_fields_forbidden(self):
        with pytest.raises(ValidationError):
            self._make_article(unknown_field="bad")

    def test_sentiment_label_valid_values(self):
        for label in ("bullish", "bearish", "neutral"):
            a = self._make_article(sentiment_label=label)
            assert a.sentiment_label == label

    def test_sentiment_label_invalid_value(self):
        with pytest.raises(ValidationError):
            self._make_article(sentiment_label="very_bullish")

    def test_serialization_roundtrip(self):
        a = self._make_article(sentiment_score=0.5, sentiment_label="bullish")
        json_str = a.model_dump_json()
        assert "AAPL" in json_str
        restored = NewsArticle.model_validate_json(json_str)
        assert restored.ticker == a.ticker
        assert restored.sentiment_score == a.sentiment_score

    def test_whitespace_stripped(self):
        a = self._make_article(title="  Headline with spaces  ")
        assert a.title == "Headline with spaces"


class TestNewsSentimentResult:
    """Tests for NewsSentimentResult schema validation."""

    def test_empty_result(self):
        r = NewsSentimentResult(ticker="AAPL")
        assert r.ticker == "AAPL"
        assert r.articles == []
        assert r.aggregate_sentiment == 0.0
        assert r.weighted_sentiment == 0.0
        assert r.article_count == 0
        assert r.source_breakdown == {}

    def test_ticker_uppercased(self):
        r = NewsSentimentResult(ticker="msft")
        assert r.ticker == "MSFT"

    def test_sentiment_range_validation(self):
        with pytest.raises(ValidationError):
            NewsSentimentResult(ticker="X", aggregate_sentiment=1.5)
        with pytest.raises(ValidationError):
            NewsSentimentResult(ticker="X", weighted_sentiment=-1.5)

    def test_negative_counts_rejected(self):
        with pytest.raises(ValidationError):
            NewsSentimentResult(ticker="X", article_count=-1)
        with pytest.raises(ValidationError):
            NewsSentimentResult(ticker="X", bullish_count=-1)

    def test_with_articles(self):
        article = NewsArticle(
            title="Test",
            url="https://example.com",
            source="finnhub",
            published_at=datetime(2026, 1, 15),
            ticker="AAPL",
            sentiment_score=0.8,
            sentiment_label="bullish",
        )
        r = NewsSentimentResult(
            ticker="AAPL",
            articles=[article],
            article_count=1,
            bullish_count=1,
            aggregate_sentiment=0.8,
            weighted_sentiment=0.8,
        )
        assert len(r.articles) == 1
        assert r.bullish_count == 1

    def test_extra_fields_forbidden(self):
        with pytest.raises(ValidationError):
            NewsSentimentResult(ticker="X", unknown="bad")

    def test_source_breakdown(self):
        r = NewsSentimentResult(
            ticker="AAPL",
            source_breakdown={"finnhub": 3, "gnews": 2, "rss": 1},
        )
        assert r.source_breakdown["finnhub"] == 3
