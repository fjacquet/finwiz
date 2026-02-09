"""Unit tests for news deduplication and source reliability utilities."""

from datetime import datetime

from finwiz.data.news_utils import (
    calculate_weighted_sentiment,
    deduplicate_articles,
    get_source_reliability,
    jaccard_similarity,
)
from finwiz.schemas.sentiment import NewsArticle


def _make_article(title: str = "Test headline", source: str = "finnhub", **kwargs) -> NewsArticle:
    defaults = {
        "title": title,
        "url": "https://example.com",
        "source": source,
        "published_at": datetime(2026, 1, 15),
        "ticker": "AAPL",
    }
    defaults.update(kwargs)
    return NewsArticle(**defaults)


class TestJaccardSimilarity:
    """Tests for Jaccard similarity calculation."""

    def test_identical_texts(self):
        assert jaccard_similarity("hello world", "hello world") == 1.0

    def test_completely_different(self):
        assert jaccard_similarity("hello world", "foo bar baz") == 0.0

    def test_partial_overlap(self):
        sim = jaccard_similarity("apple beats earnings", "apple misses earnings")
        assert 0.3 < sim < 0.8

    def test_empty_text(self):
        assert jaccard_similarity("", "hello") == 0.0
        assert jaccard_similarity("hello", "") == 0.0
        assert jaccard_similarity("", "") == 0.0

    def test_case_insensitive(self):
        assert jaccard_similarity("Hello World", "hello world") == 1.0

    def test_single_word(self):
        assert jaccard_similarity("hello", "hello") == 1.0


class TestDeduplicateArticles:
    """Tests for article deduplication."""

    def test_no_duplicates(self):
        articles = [
            _make_article("Apple beats earnings expectations"),
            _make_article("Tesla announces new factory"),
        ]
        result = deduplicate_articles(articles)
        assert len(result) == 2

    def test_exact_duplicates_removed(self):
        articles = [
            _make_article("Apple beats earnings expectations", source="finnhub", source_reliability=0.8),
            _make_article("Apple beats earnings expectations", source="gnews", source_reliability=0.6),
        ]
        result = deduplicate_articles(articles)
        assert len(result) == 1
        assert result[0].source == "finnhub"  # higher reliability kept

    def test_similar_duplicates_removed(self):
        articles = [
            _make_article("Apple beats Q4 earnings expectations today", source="reuters", source_reliability=0.95),
            _make_article("Apple beats Q4 earnings expectations in latest report", source="gnews", source_reliability=0.65),
        ]
        result = deduplicate_articles(articles, threshold=0.5)
        assert len(result) == 1
        assert result[0].source == "reuters"

    def test_keeps_higher_reliability(self):
        articles = [
            _make_article("Apple beats earnings", source="rss", source_reliability=0.5),
            _make_article("Apple beats earnings", source="reuters", source_reliability=0.95),
        ]
        result = deduplicate_articles(articles)
        assert len(result) == 1
        assert result[0].source == "reuters"

    def test_empty_list(self):
        assert deduplicate_articles([]) == []

    def test_single_article(self):
        articles = [_make_article("Single article")]
        result = deduplicate_articles(articles)
        assert len(result) == 1

    def test_custom_threshold(self):
        articles = [
            _make_article("Apple Q4 earnings beat"),
            _make_article("Apple Q4 earnings miss"),
        ]
        # Very high threshold: should keep both
        result = deduplicate_articles(articles, threshold=0.99)
        assert len(result) == 2


class TestGetSourceReliability:
    """Tests for source reliability lookup."""

    def test_known_sources(self):
        assert get_source_reliability("reuters") == 0.95
        assert get_source_reliability("bloomberg") == 0.95
        assert get_source_reliability("finnhub") == 0.80
        assert get_source_reliability("gnews") == 0.65
        assert get_source_reliability("rss") == 0.50

    def test_unknown_source(self):
        assert get_source_reliability("random_blog") == 0.40

    def test_case_insensitive(self):
        assert get_source_reliability("Reuters") == 0.95
        assert get_source_reliability("BLOOMBERG") == 0.95

    def test_normalizes_separators(self):
        assert get_source_reliability("Financial Times") == 0.90
        assert get_source_reliability("financial-times") == 0.90
        assert get_source_reliability("Wall Street Journal") == 0.90


class TestCalculateWeightedSentiment:
    """Tests for reliability-weighted sentiment calculation."""

    def test_single_article(self):
        articles = [_make_article(sentiment_score=0.8, source_reliability=0.9)]
        assert calculate_weighted_sentiment(articles) == 0.8

    def test_weighted_average(self):
        articles = [
            _make_article(sentiment_score=0.8, source_reliability=0.9),
            _make_article(title="Other", sentiment_score=-0.4, source_reliability=0.5),
        ]
        expected = (0.8 * 0.9 + (-0.4) * 0.5) / (0.9 + 0.5)
        assert abs(calculate_weighted_sentiment(articles) - expected) < 1e-10

    def test_no_articles(self):
        assert calculate_weighted_sentiment([]) == 0.0

    def test_articles_without_sentiment_excluded(self):
        articles = [
            _make_article(sentiment_score=0.5, source_reliability=0.8),
            _make_article(title="No score", sentiment_score=None, source_reliability=0.9),
        ]
        assert calculate_weighted_sentiment(articles) == 0.5

    def test_all_articles_without_sentiment(self):
        articles = [
            _make_article(sentiment_score=None),
            _make_article(title="Also none", sentiment_score=None),
        ]
        assert calculate_weighted_sentiment(articles) == 0.0
