"""Event fragments: filings preferred, news filtered.

Yahoo's news feed mixes wire copy with opinion pieces ("Prediction: Amazon Will
Join..."). The project rule is to filter noise out, not emit it with a low
grade, so these tests pin exclusion rather than down-weighting.
"""

from datetime import UTC, date, datetime

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
    # Production shape: date is datetime.date object; kept one string case for tolerance
    return [
        {"date": date(2026, 9, 1), "type": "8-K", "title": "Corporate Changes & Voting Matters", "edgarUrl": "https://example.com/edgar/1"},
        {"date": date(2026, 6, 15), "type": "10-Q", "title": "Quarterly Report", "edgarUrl": "https://example.com/edgar/2"},
        {"date": date(2019, 1, 2), "type": "8-K", "title": "Ancient Event", "edgarUrl": "https://example.com/edgar/old"},
        {"date": date(2026, 8, 1), "type": "CORRESP", "title": "Correspondence", "edgarUrl": "https://example.com/edgar/3"},
        {"date": "2026-07-15", "type": "8-K", "title": "String Date (Fallback)", "edgarUrl": "https://example.com/edgar/str"},
    ]


class TestFilingEvents:
    def test_material_filings_inside_the_window_become_events(self, mocker, filings):
        mocker.patch.object(src, "_ticker", return_value=_FakeTicker(sec_filings=filings))

        fragment = src.filing_events("AAPL", now=NOW)

        # Should have 3 material filings: 8-K (date obj), 10-Q (date obj), 8-K (string date)
        assert len(fragment.recent_events) == 3
        assert "2026-09-01 8-K: Corporate Changes & Voting Matters" in fragment.recent_events
        assert "2026-06-15 10-Q: Quarterly Report" in fragment.recent_events
        assert "2026-07-15 8-K: String Date (Fallback)" in fragment.recent_events
        assert fragment.events_from_filings is True

    def test_filings_older_than_twelve_months_are_dropped(self, mocker, filings):
        mocker.patch.object(src, "_ticker", return_value=_FakeTicker(sec_filings=filings))
        assert not any("Ancient" in e for e in src.filing_events("AAPL", now=NOW).recent_events)

    def test_immaterial_filing_types_are_dropped(self, mocker, filings):
        mocker.patch.object(src, "_ticker", return_value=_FakeTicker(sec_filings=filings))
        assert not any("Correspondence" in e for e in src.filing_events("AAPL", now=NOW).recent_events)

    def test_edgar_urls_become_citations(self, mocker, filings):
        mocker.patch.object(src, "_ticker", return_value=_FakeTicker(sec_filings=filings))
        citations = src.filing_events("AAPL", now=NOW).citations
        # Should have 3 citations from the material filings
        assert len(citations) == 3
        assert "https://example.com/edgar/1" in citations
        assert "https://example.com/edgar/2" in citations
        assert "https://example.com/edgar/str" in citations

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

    def test_news_raising_exception_degrades_the_field_and_does_not_raise(self, mocker):
        mocker.patch.object(src, "_ticker", return_value=_FakeTicker(news=RuntimeError("HTTP Error 404")))
        assert src.news_events("AMZN", now=NOW) == FactPackFragment()


class TestEventCaps:
    @staticmethod
    def _filing(date, type_, title):
        return {"date": date, "type": type_, "title": title, "edgarUrl": "https://example.com/edgar/1"}

    @staticmethod
    def _news_item(title, provider):
        return {"content": {"title": title, "pubDate": "2026-09-05T19:40:00Z", "provider": {"displayName": provider}, "canonicalUrl": {"url": "https://example.com/news"}}}

    def test_filing_events_cap_at_ten_items(self, mocker):
        filings = [self._filing("2026-09-01", "8-K", f"Event {i}") for i in range(15)]
        mocker.patch.object(src, "_ticker", return_value=_FakeTicker(sec_filings=filings))
        assert len(src.filing_events("AAPL", now=NOW).recent_events) == 10

    def test_news_events_cap_at_ten_items(self, mocker):
        news = [self._news_item(f"News {i}", "Reuters") for i in range(15)]
        mocker.patch.object(src, "_ticker", return_value=_FakeTicker(news=news))
        assert len(src.news_events("AAPL", now=NOW).recent_events) == 10


class TestMalformedData:
    def test_filing_events_skips_non_dict_entries(self, mocker):
        filings = [
            {"date": "2026-09-01", "type": "8-K", "title": "Good", "edgarUrl": "https://example.com/edgar/1"},
            None,
            "not a dict",
            {"date": "2026-09-02", "type": "8-K", "title": "Also good", "edgarUrl": "https://example.com/edgar/2"},
        ]
        mocker.patch.object(src, "_ticker", return_value=_FakeTicker(sec_filings=filings))
        fragment = src.filing_events("AAPL", now=NOW)
        assert len(fragment.recent_events) == 2
        assert "Good" in fragment.recent_events[0]
        assert "Also good" in fragment.recent_events[1]

    def test_filing_events_skips_non_string_dates(self, mocker):
        filings = [
            {"date": "2026-09-01", "type": "8-K", "title": "Good", "edgarUrl": "https://example.com/edgar/1"},
            {"date": 12345, "type": "8-K", "title": "Bad date", "edgarUrl": "https://example.com/edgar/2"},
            {"date": None, "type": "8-K", "title": "Null date", "edgarUrl": "https://example.com/edgar/3"},
        ]
        mocker.patch.object(src, "_ticker", return_value=_FakeTicker(sec_filings=filings))
        fragment = src.filing_events("AAPL", now=NOW)
        assert len(fragment.recent_events) == 1
        assert "Good" in fragment.recent_events[0]

    def test_news_events_skips_non_dict_entries(self, mocker):
        news = [
            {"content": {"title": "Good", "pubDate": "2026-09-05T19:40:00Z", "provider": {"displayName": "Reuters"}, "canonicalUrl": {"url": "https://example.com/1"}}},
            None,
            "not a dict",
            {"content": {"title": "Also good", "pubDate": "2026-09-05T19:40:00Z", "provider": {"displayName": "Reuters"}, "canonicalUrl": {"url": "https://example.com/2"}}},
        ]
        mocker.patch.object(src, "_ticker", return_value=_FakeTicker(news=news))
        fragment = src.news_events("AAPL", now=NOW)
        assert len(fragment.recent_events) == 2
        assert "Good" in fragment.recent_events[0]
        assert "Also good" in fragment.recent_events[1]


class TestPerItemContainment:
    """A malformed *field* inside an otherwise dict-shaped item is different
    from the non-dict-item case above: `_extract_filing_event`/
    `_extract_news_event`'s own `isinstance` guard doesn't help, because the
    item passes it. Before per-item containment in the loop, an exception
    raised partway through extracting one item escaped to the function's
    outer `except Exception` and discarded every sibling event and citation
    gathered before it -- not just the bad one.
    """

    def test_a_filing_with_a_non_string_title_does_not_cost_its_siblings(self, mocker):
        """Regression, not a probe of the loop-level containment itself:
        a non-string filing title is fixed at the source by `_safe_str`
        (an empty title, not a raise), so this filing degrades to an event
        with a blank title rather than ever reaching the containment
        try/except. The news case below is the one that actually exercises
        it -- `_safe_str` alone doesn't cover `.replace()` on a non-string.
        """
        filings = [
            {"date": "2026-09-01", "type": "8-K", "title": 12345, "edgarUrl": "https://example.com/edgar/bad"},
            {"date": "2026-09-02", "type": "8-K", "title": "Good filing", "edgarUrl": "https://example.com/edgar/good"},
        ]
        mocker.patch.object(src, "_ticker", return_value=_FakeTicker(sec_filings=filings))
        fragment = src.filing_events("AAPL", now=NOW)
        assert len(fragment.recent_events) == 2
        assert "Good filing" in fragment.recent_events[1]
        assert fragment.citations == ("https://example.com/edgar/bad", "https://example.com/edgar/good")

    def test_a_news_item_with_a_non_dict_provider_does_not_cost_its_siblings(self, mocker):
        """The sharpest bite check. `_safe_str` guards the *value* a `.get()`
        call returns, not the container it's called on: `provider` here is
        a bare string, not a dict, so `(content.get("provider") or {})`
        evaluates to that truthy string and `.get("displayName")` raises
        `AttributeError` -- `_safe_str` never gets a chance to run. Before
        per-item containment, this escaped `_extract_news_event` entirely
        and `news_events`'s outer handler discarded every good headline
        gathered before it, returning zero events instead of the survivor.
        """
        news = [
            {"content": {"title": "Bad", "pubDate": "2026-09-05T19:40:00Z", "provider": "Reuters", "canonicalUrl": {"url": "https://example.com/bad"}}},
            {"content": {"title": "Good headline", "pubDate": "2026-09-05T19:40:00Z", "provider": {"displayName": "Reuters"}, "canonicalUrl": {"url": "https://example.com/good"}}},
        ]
        mocker.patch.object(src, "_ticker", return_value=_FakeTicker(news=news))
        fragment = src.news_events("AAPL", now=NOW)
        assert fragment.recent_events == ("2026-09-05 Good headline",)
        assert fragment.citations == ("https://example.com/good",)
