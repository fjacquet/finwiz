"""Tests for sentiment section rendering in HTML report."""

from finwiz.reporting.section_generators import generate_sentiment_section

SAMPLE_SENTIMENT = {
    "AAPL": {
        "score": 0.65,
        "confidence": 0.82,
        "article_count": 15,
        "bullish_count": 10,
        "bearish_count": 3,
        "neutral_count": 2,
        "top_headlines": [
            {"title": "Apple lance un nouveau produit", "source": "Reuters", "sentiment_label": "bullish"},
            {"title": "Resultats trimestriels solides", "source": "Bloomberg", "sentiment_label": "bullish"},
        ],
    }
}

BEARISH_SENTIMENT = {
    "TSLA": {
        "score": -0.45,
        "confidence": 0.70,
        "article_count": 8,
        "bullish_count": 1,
        "bearish_count": 6,
        "neutral_count": 1,
        "top_headlines": [
            {"title": "Tesla rappelle des vehicules", "source": "CNBC", "sentiment_label": "bearish"},
        ],
    }
}


class TestSentimentSectionEmptyWhenNoData:
    """Verify section returns empty string when no data."""

    def test_returns_empty_when_none(self):
        assert generate_sentiment_section(None) == ""

    def test_returns_empty_when_empty_dict(self):
        assert generate_sentiment_section({}) == ""


class TestSentimentSectionRendersWithData:
    """Verify sentiment section renders correctly with data."""

    def test_contains_section_header(self):
        html = generate_sentiment_section(SAMPLE_SENTIMENT)
        assert "Sentiment de Marche" in html

    def test_contains_ticker_sentiment(self):
        html = generate_sentiment_section(SAMPLE_SENTIMENT)
        assert "AAPL" in html
        assert "+0.65" in html

    def test_contains_headlines(self):
        html = generate_sentiment_section(SAMPLE_SENTIMENT)
        assert "Apple lance un nouveau produit" in html
        assert "Resultats trimestriels solides" in html

    def test_contains_confidence(self):
        html = generate_sentiment_section(SAMPLE_SENTIMENT)
        assert "82%" in html

    def test_contains_article_count(self):
        html = generate_sentiment_section(SAMPLE_SENTIMENT)
        assert "15" in html

    def test_contains_french_labels(self):
        html = generate_sentiment_section(SAMPLE_SENTIMENT)
        assert "Score de Sentiment" in html
        assert "Confiance" in html
        assert "Articles" in html
        assert "Titres Recents" in html

    def test_color_codes_bullish(self):
        """Score > 0.2 should use green color."""
        html = generate_sentiment_section(SAMPLE_SENTIMENT)
        assert "22c55e" in html

    def test_color_codes_bearish(self):
        """Score < -0.2 should use red color."""
        html = generate_sentiment_section(BEARISH_SENTIMENT)
        assert "ef4444" in html

    def test_handles_missing_headlines(self):
        """Sentiment without top_headlines key should render without error."""
        data = {"MSFT": {"score": 0.10, "confidence": 0.50, "article_count": 3}}
        html = generate_sentiment_section(data)
        assert "MSFT" in html
        assert "Titres Recents" not in html
