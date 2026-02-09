"""Unit tests for SentimentMacroCollector."""

from finwiz.data.sentiment_collector import SentimentMacroCollector
from finwiz.schemas.macro import MacroSnapshot
from finwiz.schemas.sentiment import NewsSentimentResult


class TestSentimentCollection:
    """Tests for sentiment data collection."""

    def test_returns_none_when_flag_disabled(self, mocker):
        mocker.patch("finwiz.data.sentiment_collector.is_feature_enabled", return_value=False)
        collector = SentimentMacroCollector()
        assert collector.collect_sentiment("AAPL") is None

    def test_returns_result_when_flag_enabled(self, mocker):
        mocker.patch("finwiz.data.sentiment_collector.is_feature_enabled", return_value=True)
        mock_adapter_cls = mocker.patch("finwiz.data.adapters.finnhub_news_adapter.FinnhubNewsAdapter")
        mock_adapter = mock_adapter_cls.return_value
        mock_adapter.get_news_sentiment.return_value = NewsSentimentResult(ticker="AAPL", article_count=5)

        collector = SentimentMacroCollector()
        result = collector.collect_sentiment("AAPL")
        assert result is not None
        assert result.ticker == "AAPL"
        assert result.article_count == 5

    def test_returns_none_on_failure(self, mocker):
        mocker.patch("finwiz.data.sentiment_collector.is_feature_enabled", return_value=True)
        mock_adapter_cls = mocker.patch("finwiz.data.adapters.finnhub_news_adapter.FinnhubNewsAdapter")
        mock_adapter_cls.return_value.get_news_sentiment.side_effect = ConnectionError("API down")

        collector = SentimentMacroCollector()
        assert collector.collect_sentiment("AAPL") is None


class TestMacroCollection:
    """Tests for macro data collection."""

    def test_returns_none_when_flag_disabled(self, mocker):
        mocker.patch("finwiz.data.sentiment_collector.is_feature_enabled", return_value=False)
        collector = SentimentMacroCollector()
        assert collector.collect_macro() is None

    def test_returns_snapshot_when_flag_enabled(self, mocker):
        mocker.patch("finwiz.data.sentiment_collector.is_feature_enabled", return_value=True)

        snapshot = MacroSnapshot(fed_rate=5.25, vix=22.5)
        mock_adapter_cls = mocker.patch("finwiz.data.adapters.fred_adapter.FREDAdapter")
        mock_adapter = mock_adapter_cls.return_value
        mock_adapter.is_available.return_value = True
        mock_adapter.get_macro_snapshot.return_value = snapshot

        # Mock Fear & Greed
        mock_fg_cls = mocker.patch("finwiz.data.adapters.fear_greed_adapter.FearGreedAdapter")
        mock_fg_cls.return_value.get_fear_greed.return_value = (42, "Fear")

        collector = SentimentMacroCollector()
        result = collector.collect_macro()
        assert result is not None
        assert result.fed_rate == 5.25
        assert result.fear_greed_index == 42

    def test_session_level_caching(self, mocker):
        mocker.patch("finwiz.data.sentiment_collector.is_feature_enabled", return_value=True)

        snapshot = MacroSnapshot(fed_rate=5.25)
        mock_adapter_cls = mocker.patch("finwiz.data.adapters.fred_adapter.FREDAdapter")
        mock_adapter = mock_adapter_cls.return_value
        mock_adapter.is_available.return_value = True
        mock_adapter.get_macro_snapshot.return_value = snapshot

        mocker.patch("finwiz.data.adapters.fear_greed_adapter.FearGreedAdapter")

        collector = SentimentMacroCollector()
        result1 = collector.collect_macro()
        result2 = collector.collect_macro()
        assert result1 is result2
        # FRED constructor called only once
        assert mock_adapter_cls.call_count == 1

    def test_returns_none_when_fred_unavailable(self, mocker):
        mocker.patch("finwiz.data.sentiment_collector.is_feature_enabled", return_value=True)

        mock_adapter_cls = mocker.patch("finwiz.data.adapters.fred_adapter.FREDAdapter")
        mock_adapter_cls.return_value.is_available.return_value = False

        collector = SentimentMacroCollector()
        assert collector.collect_macro() is None

    def test_returns_none_on_failure(self, mocker):
        mocker.patch("finwiz.data.sentiment_collector.is_feature_enabled", return_value=True)

        mock_adapter_cls = mocker.patch("finwiz.data.adapters.fred_adapter.FREDAdapter")
        mock_adapter_cls.return_value.is_available.return_value = True
        mock_adapter_cls.return_value.get_macro_snapshot.side_effect = ConnectionError("down")

        collector = SentimentMacroCollector()
        assert collector.collect_macro() is None

    def test_fear_greed_failure_does_not_break_macro(self, mocker):
        mocker.patch("finwiz.data.sentiment_collector.is_feature_enabled", return_value=True)

        snapshot = MacroSnapshot(fed_rate=5.25)
        mock_adapter_cls = mocker.patch("finwiz.data.adapters.fred_adapter.FREDAdapter")
        mock_adapter = mock_adapter_cls.return_value
        mock_adapter.is_available.return_value = True
        mock_adapter.get_macro_snapshot.return_value = snapshot

        mock_fg_cls = mocker.patch("finwiz.data.adapters.fear_greed_adapter.FearGreedAdapter")
        mock_fg_cls.return_value.get_fear_greed.side_effect = ConnectionError("failed")

        collector = SentimentMacroCollector()
        result = collector.collect_macro()
        assert result is not None
        assert result.fed_rate == 5.25
        assert result.fear_greed_index is None  # Gracefully degraded
