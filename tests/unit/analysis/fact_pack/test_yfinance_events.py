"""Event fragments: filings preferred, news filtered.

Yahoo's news feed mixes wire copy with opinion pieces ("Prediction: Amazon Will
Join..."). The project rule is to filter noise out, not emit it with a low
grade, so these tests pin exclusion rather than down-weighting.
"""

from datetime import UTC, datetime

import pytest

from finwiz.analysis.fact_pack.fragment import FactPackFragment
from finwiz.analysis.fact_pack.sources import yfinance_source as src

NOW = datetime(2026, 9, 6, tzinfo=UTC)


class _FakeTicker:
    def __init__(self, sec_filings=None, news=None):
        self._sec_filings = sec_filings
        self._news = news

    @property
    def sec_filings(self):
        if isinstance(self._sec_filings, Exception):
            raise self._sec_filings
        return self._sec_filings

    @property
    def news(self):
        if isinstance(self._news, Exception):
            raise self._news
        return self._news


@pytest.fixture
def filings():
    return [
        {"date": "2026-09-01", "type": "8-K", "title": "Corporate Changes & Voting Matters", "edgarUrl": "https://example.com/edgar/1"},
        {"date": "2026-06-15", "type": "10-Q", "title": "Quarterly Report", "edgarUrl": "https://example.com/edgar/2"},
        {"date": "2019-01-02", "type": "8-K", "title": "Ancient Event", "edgarUrl": "https://example.com/edgar/old"},
        {"date": "2026-08-01", "type": "CORRESP", "title": "Correspondence", "edgarUrl": "https://example.com/edgar/3"},
    ]


class TestFilingEvents:
    def test_material_filings_inside_the_window_become_events(self, mocker, filings):
        mocker.patch.object(src, "_ticker", return_value=_FakeTicker(sec_filings=filings))

        fragment = src.filing_events("AAPL", now=NOW)

        assert fragment.recent_events == (
            "2026-09-01 8-K: Corporate Changes & Voting Matters",
            "2026-06-15 10-Q: Quarterly Report",
        )
        assert fragment.events_from_filings is True

    def test_filings_older_than_twelve_months_are_dropped(self, mocker, filings):
        mocker.patch.object(src, "_ticker", return_value=_FakeTicker(sec_filings=filings))
        assert not any("Ancient" in e for e in src.filing_events("AAPL", now=NOW).recent_events)

    def test_immaterial_filing_types_are_dropped(self, mocker, filings):
        mocker.patch.object(src, "_ticker", return_value=_FakeTicker(sec_filings=filings))
        assert not any("Correspondence" in e for e in src.filing_events("AAPL", now=NOW).recent_events)

    def test_edgar_urls_become_citations(self, mocker, filings):
        mocker.patch.object(src, "_ticker", return_value=_FakeTicker(sec_filings=filings))
        assert src.filing_events("AAPL", now=NOW).citations == ("https://example.com/edgar/1", "https://example.com/edgar/2")

    def test_a_european_listing_with_no_filings_yields_an_empty_fragment(self, mocker):
        mocker.patch.object(src, "_ticker", return_value=_FakeTicker(sec_filings=[]))
        assert src.filing_events("AIR.PA", now=NOW).recent_events == ()

    def test_an_internal_404_degrades_the_field_and_does_not_raise(self, mocker):
        # yfinance raises internally for non-US tickers; that must cost events only.
        mocker.patch.object(src, "_ticker", return_value=_FakeTicker(sec_filings=RuntimeError("HTTP Error 404")))
        assert src.filing_events("NESN.SW", now=NOW) == FactPackFragment()


class TestNewsEvents:
    @staticmethod
    def _item(title, provider, url, pub_date="2026-09-05T19:40:00Z"):
        return {"content": {"title": title, "pubDate": pub_date, "provider": {"displayName": provider}, "canonicalUrl": {"url": url}}}

    def test_allowlisted_providers_become_events(self, mocker):
        news = [self._item("Airbus wins 40-jet order", "Reuters", "https://example.com/reuters/1")]
        mocker.patch.object(src, "_ticker", return_value=_FakeTicker(news=news))

        fragment = src.news_events("AIR.PA", now=NOW)

        assert fragment.recent_events == ("2026-09-05 Airbus wins 40-jet order",)
        assert fragment.citations == ("https://example.com/reuters/1",)
        assert fragment.events_from_filings is False

    def test_opinion_providers_are_excluded_entirely(self, mocker):
        news = [self._item("Prediction: Amazon Will Join Nvidia", "Motley Fool", "https://example.com/fool/1")]
        mocker.patch.object(src, "_ticker", return_value=_FakeTicker(news=news))
        assert src.news_events("AMZN", now=NOW).recent_events == ()

    def test_items_older_than_twelve_months_are_dropped(self, mocker):
        news = [self._item("Old wire story", "Reuters", "https://example.com/r/old", pub_date="2024-01-01T00:00:00Z")]
        mocker.patch.object(src, "_ticker", return_value=_FakeTicker(news=news))
        assert src.news_events("AAPL", now=NOW).recent_events == ()

    def test_event_text_is_truncated_to_two_hundred_chars(self, mocker):
        news = [self._item("x" * 400, "Reuters", "https://example.com/r/long")]
        mocker.patch.object(src, "_ticker", return_value=_FakeTicker(news=news))
        assert all(len(e) <= 200 for e in src.news_events("AAPL", now=NOW).recent_events)
