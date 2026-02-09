"""Tests for sentiment summary persistence in enriched JSON and macro_snapshot on FinwizState.

Verifies that enriched JSON includes sentiment_summary with correct fields,
and that FinwizState.macro_snapshot is set during analysis.
"""

from __future__ import annotations

from typing import Any

import pytest

from finwiz.analysis.deep_analysis_pipeline import _build_sentiment_summary
from finwiz.flow_state_models import FinwizState


class TestBuildSentimentSummary:
    """Test _build_sentiment_summary helper function."""

    def test_sentiment_summary_with_articles(self):
        """When news_sentiment has articles, sentiment_summary includes correct fields."""
        raw_data: dict[str, Any] = {
            "news_sentiment": {
                "ticker": "AAPL",
                "aggregate_sentiment": 0.35,
                "article_count": 8,
                "bullish_count": 5,
                "bearish_count": 1,
                "neutral_count": 2,
                "articles": [
                    {"title": "Apple beats earnings", "source": "finnhub", "sentiment_label": "bullish"},
                    {"title": "iPhone sales strong", "source": "gnews", "sentiment_label": "bullish"},
                    {"title": "Market rally continues", "source": "rss", "sentiment_label": "neutral"},
                    {"title": "Tech sector update", "source": "finnhub", "sentiment_label": "bullish"},
                    {"title": "AAPL price target raised", "source": "gnews", "sentiment_label": "bullish"},
                    {"title": "Supply chain concerns", "source": "rss", "sentiment_label": "bearish"},
                    {"title": "Analyst upgrades Apple", "source": "finnhub", "sentiment_label": "bullish"},
                ],
            }
        }

        result = _build_sentiment_summary(raw_data)

        assert result is not None
        assert result["score"] == 0.35
        assert result["article_count"] == 8
        assert result["bullish_count"] == 5
        assert result["bearish_count"] == 1
        assert result["neutral_count"] == 2
        assert result["confidence"] == pytest.approx(0.8)  # min(1.0, 8/10)
        assert len(result["top_headlines"]) == 5  # Limited to 5

    def test_sentiment_summary_none_when_no_news(self):
        """When news_sentiment is None, sentiment_summary is None."""
        raw_data: dict[str, Any] = {"news_sentiment": None}
        result = _build_sentiment_summary(raw_data)
        assert result is None

    def test_sentiment_summary_none_when_key_missing(self):
        """When news_sentiment key is absent, sentiment_summary is None."""
        raw_data: dict[str, Any] = {}
        result = _build_sentiment_summary(raw_data)
        assert result is None

    def test_sentiment_summary_top_headlines_limited_to_5(self):
        """Top headlines are limited to 5 entries even with more articles."""
        articles = [{"title": f"Article {i}", "source": "finnhub", "sentiment_label": "bullish"} for i in range(10)]
        raw_data: dict[str, Any] = {
            "news_sentiment": {
                "aggregate_sentiment": 0.5,
                "article_count": 10,
                "bullish_count": 10,
                "bearish_count": 0,
                "neutral_count": 0,
                "articles": articles,
            }
        }

        result = _build_sentiment_summary(raw_data)

        assert result is not None
        assert len(result["top_headlines"]) == 5
        assert result["top_headlines"][0]["title"] == "Article 0"
        assert result["top_headlines"][4]["title"] == "Article 4"

    def test_sentiment_summary_confidence_capped_at_1(self):
        """Confidence is capped at 1.0 even with many articles."""
        raw_data: dict[str, Any] = {
            "news_sentiment": {
                "aggregate_sentiment": 0.2,
                "article_count": 50,
                "bullish_count": 30,
                "bearish_count": 10,
                "neutral_count": 10,
                "articles": [],
            }
        }

        result = _build_sentiment_summary(raw_data)

        assert result is not None
        assert result["confidence"] == 1.0

    def test_sentiment_summary_zero_articles(self):
        """Zero articles result in zero confidence."""
        raw_data: dict[str, Any] = {
            "news_sentiment": {
                "aggregate_sentiment": 0.0,
                "article_count": 0,
                "bullish_count": 0,
                "bearish_count": 0,
                "neutral_count": 0,
                "articles": [],
            }
        }

        result = _build_sentiment_summary(raw_data)

        assert result is not None
        assert result["confidence"] == 0.0
        assert result["top_headlines"] == []

    def test_sentiment_summary_with_object_articles(self):
        """Handle NewsSentimentResult-like objects (not dicts) for articles."""
        from types import SimpleNamespace

        articles = [
            SimpleNamespace(title="Article A", source="finnhub", sentiment_label="bullish"),
            SimpleNamespace(title="Article B", source="gnews", sentiment_label="bearish"),
        ]
        ns = SimpleNamespace(
            aggregate_sentiment=0.1,
            article_count=2,
            bullish_count=1,
            bearish_count=1,
            neutral_count=0,
            articles=articles,
        )
        raw_data: dict[str, Any] = {"news_sentiment": ns}

        result = _build_sentiment_summary(raw_data)

        assert result is not None
        assert result["score"] == 0.1
        assert len(result["top_headlines"]) == 2
        assert result["top_headlines"][0]["title"] == "Article A"
        assert result["top_headlines"][1]["sentiment_label"] == "bearish"


class TestMacroSnapshotOnFinwizState:
    """Test macro_snapshot field on FinwizState."""

    def test_macro_snapshot_default_none(self):
        """FinwizState.macro_snapshot defaults to None."""
        state = FinwizState()
        assert state.macro_snapshot is None

    def test_macro_snapshot_can_be_set(self):
        """FinwizState.macro_snapshot can be set to a dict."""
        state = FinwizState()
        state.macro_snapshot = {
            "fed_rate": 5.25,
            "vix": 18.5,
            "fear_greed_index": 65,
        }
        assert state.macro_snapshot is not None
        assert state.macro_snapshot["fed_rate"] == 5.25
        assert state.macro_snapshot["vix"] == 18.5

    def test_macro_snapshot_survives_serialization(self):
        """FinwizState.macro_snapshot survives model_dump/model_validate round-trip."""
        state = FinwizState()
        state.macro_snapshot = {
            "fed_rate": 5.25,
            "yield_curve_spread": -0.15,
            "fetched_at": "2026-02-09T10:00:00",
        }
        dumped = state.model_dump()
        restored = FinwizState.model_validate(dumped)
        assert restored.macro_snapshot == state.macro_snapshot


class TestEnsureMacroSnapshotOnState:
    """Test _ensure_macro_snapshot_on_state in DeepAnalysisOrchestrator."""

    def test_macro_snapshot_set_when_available(self, mocker):
        """Macro snapshot is set on state when collect_macro returns data."""
        from finwiz.schemas.macro import MacroSnapshot

        mock_snapshot = MacroSnapshot(
            fed_rate=5.25,
            vix=18.5,
            fear_greed_index=65,
            fear_greed_label="Greed",
        )

        mock_collector_cls = mocker.MagicMock()
        mock_collector_instance = mock_collector_cls.return_value
        mock_collector_instance.collect_macro.return_value = mock_snapshot

        # Patch where the lazy import resolves (the source module)
        mocker.patch("finwiz.data.sentiment_collector.SentimentMacroCollector", mock_collector_cls)

        from finwiz.orchestrators.deep_analysis_orchestrator import DeepAnalysisOrchestrator

        state = FinwizState()
        orch = DeepAnalysisOrchestrator(state=state)
        orch._ensure_macro_snapshot_on_state()

        assert state.macro_snapshot is not None
        assert state.macro_snapshot["fed_rate"] == 5.25

    def test_macro_snapshot_not_overwritten_if_already_set(self, mocker):
        """Macro snapshot is NOT overwritten if already set."""
        from finwiz.orchestrators.deep_analysis_orchestrator import DeepAnalysisOrchestrator

        state = FinwizState()
        state.macro_snapshot = {"fed_rate": 4.0}

        orch = DeepAnalysisOrchestrator(state=state)
        orch._ensure_macro_snapshot_on_state()

        # macro_snapshot should not have changed since it was already set
        assert state.macro_snapshot == {"fed_rate": 4.0}

    def test_macro_snapshot_none_when_collection_fails(self, mocker):
        """Macro snapshot stays None when collection fails gracefully."""
        mock_collector_cls = mocker.MagicMock()
        mock_collector_instance = mock_collector_cls.return_value
        mock_collector_instance.collect_macro.return_value = None

        mocker.patch("finwiz.data.sentiment_collector.SentimentMacroCollector", mock_collector_cls)

        from finwiz.orchestrators.deep_analysis_orchestrator import DeepAnalysisOrchestrator

        state = FinwizState()
        orch = DeepAnalysisOrchestrator(state=state)
        orch._ensure_macro_snapshot_on_state()

        assert state.macro_snapshot is None


class TestCollectEconomicCalendar:
    """Test SentimentMacroCollector.collect_economic_calendar()."""

    def test_returns_none_when_feature_disabled(self, mocker):
        """Returns None when economic_calendar feature flag is off."""
        mocker.patch("finwiz.data.sentiment_collector.is_feature_enabled", return_value=False)
        from finwiz.data.sentiment_collector import SentimentMacroCollector

        collector = SentimentMacroCollector()
        result = collector.collect_economic_calendar()
        assert result is None

    def test_returns_none_when_adapter_unavailable(self, mocker):
        """Returns None when Finnhub key is missing."""
        mocker.patch("finwiz.data.sentiment_collector.is_feature_enabled", return_value=True)
        mocker.patch("finwiz.data.adapters.economic_calendar_adapter.EconomicCalendarAdapter.is_available", return_value=False)
        from finwiz.data.sentiment_collector import SentimentMacroCollector

        collector = SentimentMacroCollector()
        result = collector.collect_economic_calendar()
        assert result is None

    def test_returns_calendar_data_when_enabled(self, mocker):
        """Returns calendar dict when feature enabled and adapter available."""
        mocker.patch("finwiz.data.sentiment_collector.is_feature_enabled", return_value=True)

        from finwiz.schemas.economic_calendar import EconomicCalendar, EconomicEvent

        mock_calendar = EconomicCalendar(
            economic_events=[
                EconomicEvent(event="FOMC Meeting", country="US", date="2026-02-15"),
            ],
        )

        mock_adapter = mocker.MagicMock()
        mock_adapter.is_available.return_value = True
        mock_adapter.get_economic_calendar.return_value = mock_calendar

        # Patch at the source module where the lazy import resolves
        mocker.patch(
            "finwiz.data.adapters.economic_calendar_adapter.EconomicCalendarAdapter",
            return_value=mock_adapter,
        )

        from finwiz.data.sentiment_collector import SentimentMacroCollector

        collector = SentimentMacroCollector()
        result = collector.collect_economic_calendar()

        assert result is not None
        assert len(result["economic_events"]) == 1
        assert result["economic_events"][0]["event"] == "FOMC Meeting"
