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

MIXED_SENTIMENT = {
    **SAMPLE_SENTIMENT,
    **BEARISH_SENTIMENT,
    "VAHN.SW": {"score": 0.0, "confidence": 0.0, "article_count": 0},
    "SCMN.SW": {"score": 0.0, "confidence": 0.0, "article_count": 0},
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

    def test_contains_headlines_folded_per_row(self):
        html = generate_sentiment_section(SAMPLE_SENTIMENT)
        assert "Apple lance un nouveau produit" in html
        assert "Resultats trimestriels solides" in html
        assert "<details><summary>Titres Recents (2)</summary>" in html

    def test_contains_confidence(self):
        html = generate_sentiment_section(SAMPLE_SENTIMENT)
        assert "82%" in html

    def test_contains_article_count(self):
        html = generate_sentiment_section(SAMPLE_SENTIMENT)
        assert ">15<" in html

    def test_contains_french_labels(self):
        html = generate_sentiment_section(SAMPLE_SENTIMENT)
        assert "Score de Sentiment" in html
        assert "Confiance" in html
        assert "Articles" in html
        assert "Titres Recents" in html

    def test_renders_table_not_cards(self):
        html = generate_sentiment_section(SAMPLE_SENTIMENT)
        assert "<table" in html
        assert "stat-card" not in html

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


class TestSentimentSummaryAndOrdering:
    """Portfolio-wide digest line, bearish-first ordering, no-news collapse."""

    def test_summary_line_counts_labels_and_no_news(self):
        html = generate_sentiment_section(MIXED_SENTIMENT)
        # Mean over tickers with news only: (0.65 - 0.45) / 2 = +0.10
        assert "Sentiment moyen +0.10" in html
        assert "1 haussier" in html
        assert "1 baissier" in html
        assert "2 positions sans actualités" in html

    def test_rows_sorted_bearish_first(self):
        html = generate_sentiment_section(MIXED_SENTIMENT)
        table = html[html.index("<table") :]
        assert table.index("TSLA") < table.index("AAPL")

    def test_no_news_tickers_collapsed_to_one_line_outside_table(self):
        html = generate_sentiment_section(MIXED_SENTIMENT)
        table = html[html.index("<table") : html.index("</table>")]
        assert "VAHN.SW" not in table
        assert "Sans actualités (2) : SCMN.SW, VAHN.SW" in html

    def test_only_no_news_tickers_renders_no_table(self):
        data = {"VAHN.SW": {"score": 0.0, "confidence": 0.0, "article_count": 0}}
        html = generate_sentiment_section(data)
        assert "<table" not in html
        assert "Sans actualités (1) : VAHN.SW" in html
