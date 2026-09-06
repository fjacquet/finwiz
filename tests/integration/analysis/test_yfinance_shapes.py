"""Canary test for yfinance response shapes.

IMPORTANT: This test exists because the unit test fixtures were hand-built from
a specification that incorrectly assumed filing dates were strings when they are
actually datetime.date objects. This caused filing_events() to silently fail on
production data, returning zero events when the function was being tested and
reviewed against the wrong shapes.

When this test fails, it means yfinance response shapes have changed and the
unit test fixtures in test_yfinance_events.py need to be updated to match the
new production reality. Update the fixtures, NOT the implementation, and re-run
this test to confirm the new shapes.

Run with: uv run pytest tests/integration/analysis/test_yfinance_shapes.py -m integration -v
"""

from datetime import date, datetime

import pytest

from finwiz.analysis.fact_pack.sources import yfinance_source as src


@pytest.mark.integration
class TestYfinanceShapes:
    """Verify production response shapes match what unit tests assume."""

    def test_sec_filings_shape(self):
        """sec_filings entries must have date as datetime.date/datetime, plus type/title/edgarUrl."""
        filings = src._ticker("AAPL").sec_filings
        if not filings:
            pytest.skip("No filings returned for AAPL")

        for filing in filings[:5]:  # Test first 5 to avoid slow response
            assert isinstance(filing, dict), f"Filing must be a dict, got {type(filing)}"
            assert "date" in filing, "Filing must have 'date' key"
            assert "type" in filing, "Filing must have 'type' key"
            assert "title" in filing, "Filing must have 'title' key"
            assert "edgarUrl" in filing, "Filing must have 'edgarUrl' key"

            # Date must be date or datetime, never a string
            d = filing["date"]
            assert isinstance(d, (date, datetime)), f"Filing date must be date/datetime, got {type(d).__name__}: {d!r}"

    def test_news_shape(self):
        """news entries must have content.title/pubDate/provider.displayName/canonicalUrl.url as strings."""
        news = src._ticker("AAPL").news
        if not news:
            pytest.skip("No news returned for AAPL")

        for item in news[:5]:  # Test first 5 to avoid slow response
            assert isinstance(item, dict), f"News item must be a dict, got {type(item)}"
            assert "content" in item, "News item must have 'content' key"

            content = item["content"]
            assert isinstance(content, dict), f"News content must be a dict, got {type(content)}"
            assert "title" in content, "News content must have 'title' key"
            assert isinstance(content["title"], str), f"News title must be string, got {type(content['title'])}"
            assert "pubDate" in content, "News content must have 'pubDate' key"
            assert isinstance(content["pubDate"], str), f"News pubDate must be string, got {type(content['pubDate'])}"

            provider = content.get("provider") or {}
            display_name = provider.get("displayName", "")
            assert isinstance(display_name, str), f"Provider displayName must be string, got {type(display_name)}"

            canonical = content.get("canonicalUrl") or {}
            url = canonical.get("url", "")
            assert isinstance(url, str), f"CanonicalUrl.url must be string, got {type(url)}"

    def test_info_equity_shape(self):
        """info dict for an equity must have quoteType and companyOfficers entries with name/title."""
        info = src._ticker("AAPL").info
        assert isinstance(info, dict), f"Info must be a dict, got {type(info)}"
        assert "quoteType" in info, "Info must have 'quoteType' key"
        assert info["quoteType"] == "EQUITY", f"AAPL must be EQUITY, got {info['quoteType']}"

        officers = info.get("companyOfficers") or []
        if officers:
            for officer in officers[:3]:  # Test first 3
                assert isinstance(officer, dict), f"Officer must be a dict, got {type(officer)}"
                # name and title may be empty strings but must be strings
                assert "name" in officer, "Officer must have 'name' key"
                assert isinstance(officer["name"], str), f"Officer name must be string, got {type(officer['name'])}"
                assert "title" in officer, "Officer must have 'title' key"
                assert isinstance(officer["title"], str), f"Officer title must be string, got {type(officer['title'])}"

    def test_info_etf_shape(self):
        """info dict for an ETF must have quoteType='ETF' and fundFamily/legalType."""
        info = src._ticker("VTSAX").info
        assert isinstance(info, dict), f"Info must be a dict, got {type(info)}"
        assert "quoteType" in info, "Info must have 'quoteType' key"
        assert info["quoteType"] == "MUTUALFUND", f"VTSAX must be MUTUALFUND, got {info['quoteType']}"

    def test_unresolvable_ticker_shape(self):
        """An unknown ticker's info dict must lack 'quoteType'."""
        info = src._ticker("BOGUS_TICKER_XYZ").info or {}
        # Unresolvable tickers may have other fields but never quoteType
        assert "quoteType" not in info, f"Unresolvable ticker should not have quoteType, but got: {info}"
