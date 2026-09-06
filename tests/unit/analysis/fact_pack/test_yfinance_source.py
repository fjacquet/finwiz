"""Identity fragments built from yfinance `info`.

Fixtures mirror real 2026-09-06 responses; the network seam is `_ticker`.
"""

import pytest

from finwiz.analysis.fact_pack.sources import yfinance_source as src


@pytest.fixture
def equity_info():
    return {
        "quoteType": "EQUITY",
        "longName": "Apple Inc.",
        "longBusinessSummary": "Apple Inc. designs, manufactures and markets smartphones.",
        "companyOfficers": [
            {"name": "Mr. Timothy D. Cook", "title": "CEO & Director"},
            {"name": "Mr. Kevan Parekh", "title": "Senior VP & CFO"},
            {"name": "Ms. Deirdre O'Brien", "title": "Senior VP of Retail"},
        ],
    }


class TestResolvability:
    def test_a_real_instrument_is_resolvable(self, equity_info):
        assert src.is_resolvable(equity_info) is True

    def test_an_unknown_ticker_is_not_resolvable(self):
        # A bogus symbol comes back as a single-key dict with no quoteType.
        assert src.is_resolvable({"trailingPegRatio": None}) is False

    def test_resolve_returns_an_empty_dict_when_yfinance_raises(self, mocker):
        mocker.patch.object(src, "_ticker", side_effect=RuntimeError("network is down"))
        assert src.resolve("AAPL") == {}

    def test_resolve_returns_populated_dict_on_success(self, mocker, equity_info):
        mocker.patch.object(src, "_ticker")
        mocker.patch.object(src._ticker.return_value, "info", equity_info)
        result = src.resolve("AAPL")
        assert result == equity_info
        assert result.get("quoteType") == "EQUITY"


class TestEquityFragment:
    def test_business_summary_becomes_corporate_structure(self, equity_info):
        assert src.equity_fragment("AAPL", equity_info).corporate_structure == "Apple Inc. designs, manufactures and markets smartphones."

    def test_officers_become_leadership_as_name_and_title(self, equity_info):
        leadership = src.equity_fragment("AAPL", equity_info).leadership
        assert "Mr. Timothy D. Cook (CEO & Director)" in leadership
        assert "Mr. Kevan Parekh (Senior VP & CFO)" in leadership

    def test_officers_without_a_name_or_title_are_skipped(self):
        info = {"quoteType": "EQUITY", "companyOfficers": [{"name": "", "title": "CEO"}, {"name": "Real Person", "title": ""}]}
        assert src.equity_fragment("AAPL", info).leadership is None

    def test_a_missing_summary_yields_none_not_an_empty_string(self):
        assert src.equity_fragment("AAPL", {"quoteType": "EQUITY"}).corporate_structure is None

    def test_the_source_is_labelled(self, equity_info):
        assert src.equity_fragment("AAPL", equity_info).sources == ("yfinance.info",)

    def test_more_than_six_officers_are_capped(self):
        """More than _MAX_OFFICERS should only return the first 6."""
        officers = [{"name": f"Officer {i}", "title": f"Title {i}"} for i in range(10)]
        info = {"quoteType": "EQUITY", "longBusinessSummary": "Test", "companyOfficers": officers}
        leadership = src.equity_fragment("AAPL", info).leadership
        # Should have exactly 6 officers listed
        officer_count = leadership.count(" (Title ")
        assert officer_count == 6
        assert "Officer 0" in leadership
        assert "Officer 5" in leadership
        assert "Officer 6" not in leadership


class TestExceptionHandling:
    """Verify all builders degrade gracefully without raising."""

    def test_equity_fragment_handles_non_dict_officer(self):
        """Officer entry that is not a dict should return empty fragment, not raise."""
        info = {
            "quoteType": "EQUITY",
            "longBusinessSummary": "Apple Inc.",
            "companyOfficers": [
                {"name": "Good Officer", "title": "CEO"},
                "not a dict",  # This will cause AttributeError if not handled
            ],
        }
        fragment = src.equity_fragment("AAPL", info)
        # Should return a fragment, not raise - exception caught and logged
        assert isinstance(fragment, src.FactPackFragment)

    def test_equity_fragment_handles_non_string_summary(self):
        """Non-string longBusinessSummary should return empty fragment, not raise."""
        info = {
            "quoteType": "EQUITY",
            "longBusinessSummary": 12345,  # Not a string
            "companyOfficers": [],
        }
        fragment = src.equity_fragment("AAPL", info)
        # Should return a fragment, not raise
        assert isinstance(fragment, src.FactPackFragment)
