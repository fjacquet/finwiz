"""Unit tests for FinnhubNewsAdapter with waterfall fallback."""

from types import SimpleNamespace

from finwiz.data.adapters.finnhub_news_adapter import FinnhubNewsAdapter


class TestFinnhubNewsAdapter:
    """Tests for FinnhubNewsAdapter waterfall logic."""

    def test_is_available_always_true(self):
        adapter = FinnhubNewsAdapter()
        assert adapter.is_available() is True

    def test_finnhub_primary_source(self, mocker):
        """When Finnhub returns articles, they are used."""
        mocker.patch.dict("os.environ", {"FINNHUB_API_KEY": "test_key"})
        adapter = FinnhubNewsAdapter()

        mock_client_cls = mocker.patch("finnhub.Client")
        mock_client = mock_client_cls.return_value
        mock_client.company_news.return_value = [
            {"headline": f"Article {i}", "url": f"https://example.com/{i}", "summary": f"Summary {i}", "datetime": 1700000000 + i, "sentiment": 0.5} for i in range(6)
        ]

        result = adapter.get_news_sentiment("AAPL")
        assert result.ticker == "AAPL"
        assert result.article_count >= 5
        assert "finnhub" in result.source_breakdown

    def test_waterfall_to_rss_when_no_keys(self, mocker):
        """When no API keys are set, falls back to RSS."""
        mocker.patch.dict("os.environ", {}, clear=True)
        adapter = FinnhubNewsAdapter()
        adapter.finnhub_key = None
        adapter.gnews_key = None

        mock_feedparser = mocker.patch("feedparser.parse")
        mock_feedparser.return_value = SimpleNamespace(
            entries=[
                {"title": "Apple stock update", "link": "https://example.com/rss/1", "summary": "Latest news", "published": "Mon, 15 Jan 2026 10:00:00 GMT"},
            ]
        )

        mock_vader_cls = mocker.patch("vaderSentiment.vaderSentiment.SentimentIntensityAnalyzer")
        mock_vader = mock_vader_cls.return_value
        mock_vader.polarity_scores.return_value = {"compound": 0.2, "pos": 0.3, "neg": 0.1, "neu": 0.6}

        result = adapter.get_news_sentiment("AAPL")
        assert result.article_count >= 1
        assert "rss" in result.source_breakdown

    def test_vader_applied_to_articles_without_sentiment(self, mocker):
        """Articles without pre-computed sentiment get VADER scores."""
        mocker.patch.dict("os.environ", {}, clear=True)
        adapter = FinnhubNewsAdapter()
        adapter.finnhub_key = None
        adapter.gnews_key = None

        mock_feedparser = mocker.patch("feedparser.parse")
        mock_feedparser.return_value = SimpleNamespace(
            entries=[{"title": "Test article", "link": "https://test.com", "summary": "Good news", "published": "Mon, 15 Jan 2026 10:00:00 GMT"}]
        )

        mock_vader_cls = mocker.patch("vaderSentiment.vaderSentiment.SentimentIntensityAnalyzer")
        mock_vader = mock_vader_cls.return_value
        mock_vader.polarity_scores.return_value = {"compound": 0.6, "pos": 0.5, "neg": 0.0, "neu": 0.5}

        result = adapter.get_news_sentiment("AAPL")
        assert result.article_count >= 1
        for article in result.articles:
            assert article.sentiment_score is not None
            assert article.sentiment_label is not None

    def test_gnews_fallback_when_finnhub_insufficient(self, mocker):
        """When Finnhub returns < 5 articles, gnews is tried."""
        mocker.patch.dict("os.environ", {"FINNHUB_API_KEY": "test", "GNEWS_API_KEY": "test"})
        adapter = FinnhubNewsAdapter()

        mock_client_cls = mocker.patch("finnhub.Client")
        mock_client = mock_client_cls.return_value
        mock_client.company_news.return_value = [
            {"headline": "Article 1", "url": "https://a.com", "summary": "S1", "datetime": 1700000000, "sentiment": 0.5},
            {"headline": "Article 2", "url": "https://b.com", "summary": "S2", "datetime": 1700000001, "sentiment": 0.3},
        ]

        mock_gnews_cls = mocker.patch("gnews.GNews")
        mock_gnews = mock_gnews_cls.return_value
        mock_gnews.get_news.return_value = [
            {"title": "gnews Article", "url": "https://c.com", "description": "Extra news", "published date": "Mon, 15 Jan 2026 10:00:00 GMT"},
        ]

        mock_vader_cls = mocker.patch("vaderSentiment.vaderSentiment.SentimentIntensityAnalyzer")
        mock_vader = mock_vader_cls.return_value
        mock_vader.polarity_scores.return_value = {"compound": 0.4, "pos": 0.3, "neg": 0.1, "neu": 0.6}

        result = adapter.get_news_sentiment("AAPL")
        assert result.article_count >= 3
        assert "finnhub" in result.source_breakdown
        assert "gnews" in result.source_breakdown

    def test_finnhub_failure_cascades_gracefully(self, mocker):
        """When Finnhub raises an exception, adapter continues to RSS."""
        mocker.patch.dict("os.environ", {"FINNHUB_API_KEY": "test"})
        adapter = FinnhubNewsAdapter()
        adapter.gnews_key = None

        mock_client_cls = mocker.patch("finnhub.Client")
        mock_client = mock_client_cls.return_value
        mock_client.company_news.side_effect = ConnectionError("API down")

        mock_feedparser = mocker.patch("feedparser.parse")
        mock_feedparser.return_value = SimpleNamespace(
            entries=[{"title": "RSS fallback article", "link": "https://rss.com", "summary": "backup", "published": "Mon, 15 Jan 2026 10:00:00 GMT"}]
        )

        mock_vader_cls = mocker.patch("vaderSentiment.vaderSentiment.SentimentIntensityAnalyzer")
        mock_vader_cls.return_value.polarity_scores.return_value = {"compound": 0.0, "pos": 0.0, "neg": 0.0, "neu": 1.0}

        result = adapter.get_news_sentiment("AAPL")
        assert result.article_count >= 1

    def test_empty_result_when_all_fail(self, mocker):
        """When all sources fail, returns empty result."""
        mocker.patch.dict("os.environ", {"FINNHUB_API_KEY": "test"})
        adapter = FinnhubNewsAdapter()
        adapter.gnews_key = None

        mock_client_cls = mocker.patch("finnhub.Client")
        mock_client_cls.return_value.company_news.side_effect = ConnectionError("down")

        mock_feedparser = mocker.patch("feedparser.parse")
        mock_feedparser.return_value = SimpleNamespace(entries=[])

        result = adapter.get_news_sentiment("AAPL")
        assert result.article_count == 0
        assert result.aggregate_sentiment == 0.0

    def test_source_reliability_applied(self, mocker):
        """Source reliability weights are set on articles."""
        mocker.patch.dict("os.environ", {}, clear=True)
        adapter = FinnhubNewsAdapter()
        adapter.finnhub_key = None
        adapter.gnews_key = None

        mock_feedparser = mocker.patch("feedparser.parse")
        mock_feedparser.return_value = SimpleNamespace(
            entries=[{"title": "RSS article", "link": "https://test.com", "summary": "News", "published": "Mon, 15 Jan 2026 10:00:00 GMT"}]
        )
        mock_vader_cls = mocker.patch("vaderSentiment.vaderSentiment.SentimentIntensityAnalyzer")
        mock_vader_cls.return_value.polarity_scores.return_value = {"compound": 0.0, "pos": 0.0, "neg": 0.0, "neu": 1.0}

        result = adapter.get_news_sentiment("AAPL")
        for article in result.articles:
            assert article.source_reliability > 0
            assert article.source_reliability <= 1.0
