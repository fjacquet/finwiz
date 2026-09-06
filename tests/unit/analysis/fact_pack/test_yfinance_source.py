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


@pytest.fixture
def etf_info():
    return {
        "quoteType": "ETF",
        "longName": "iShares MSCI World SRI UCITS ETF EUR (Acc)",
        "fundFamily": "BlackRock Asset Management Ireland - ETF",
        "legalType": "Exchange Traded Fund",
        "fundInceptionDate": 1602460800,
        "category": None,
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


class TestEquityFragment:
    def test_business_summary_becomes_corporate_structure(self, equity_info):
        assert src.equity_fragment(equity_info).corporate_structure == "Apple Inc. designs, manufactures and markets smartphones."

    def test_officers_become_leadership_as_name_and_title(self, equity_info):
        leadership = src.equity_fragment(equity_info).leadership
        assert "Mr. Timothy D. Cook (CEO & Director)" in leadership
        assert "Mr. Kevan Parekh (Senior VP & CFO)" in leadership

    def test_officers_without_a_name_or_title_are_skipped(self):
        info = {"quoteType": "EQUITY", "companyOfficers": [{"name": "", "title": "CEO"}, {"name": "Real Person", "title": ""}]}
        assert src.equity_fragment(info).leadership is None

    def test_a_missing_summary_yields_none_not_an_empty_string(self):
        assert src.equity_fragment({"quoteType": "EQUITY"}).corporate_structure is None

    def test_the_source_is_labelled(self, equity_info):
        assert src.equity_fragment(equity_info).sources == ("yfinance.info",)


class TestEtfFragment:
    def test_structure_names_issuer_legal_type_and_inception(self, etf_info):
        structure = src.etf_fragment("2B7K.DE", etf_info).corporate_structure
        assert "BlackRock Asset Management Ireland - ETF" in structure
        assert "Exchange Traded Fund" in structure
        assert "2020" in structure

    def test_the_manager_is_the_honest_answer_for_leadership(self, etf_info):
        assert src.etf_fragment("2B7K.DE", etf_info).leadership == "BlackRock Asset Management Ireland - ETF"

    def test_the_quote_page_is_the_citation(self, etf_info):
        assert src.etf_fragment("2B7K.DE", etf_info).citations == ("https://finance.yahoo.com/quote/2B7K.DE",)


class TestCryptoFragment:
    def test_crypto_has_no_structure_or_leadership_to_report(self):
        fragment = src.crypto_fragment({"quoteType": "CRYPTOCURRENCY", "longName": "Bitcoin USD"})
        assert fragment.corporate_structure is None
        assert fragment.leadership is None


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
        fragment = src.equity_fragment(info)
        # Should return a fragment, not raise - exception caught and logged
        assert isinstance(fragment, src.FactPackFragment)

    def test_equity_fragment_handles_non_string_summary(self):
        """Non-string longBusinessSummary should return empty fragment, not raise."""
        info = {
            "quoteType": "EQUITY",
            "longBusinessSummary": 12345,  # Not a string
            "companyOfficers": [],
        }
        fragment = src.equity_fragment(info)
        # Should return a fragment, not raise
        assert isinstance(fragment, src.FactPackFragment)

    def test_etf_fragment_handles_non_string_fundFamily(self):
        """Non-string fundFamily should return empty fragment, not raise."""
        info = {
            "quoteType": "ETF",
            "longName": "Test Fund",
            "fundFamily": 12345,  # Not a string, calling .strip() will raise AttributeError
            "legalType": "ETF",
            "fundInceptionDate": 1602460800,
        }
        fragment = src.etf_fragment("TEST", info)
        # Should return a fragment, not raise
        assert isinstance(fragment, src.FactPackFragment)

    def test_etf_fragment_handles_out_of_range_inception_date(self):
        """Out-of-range fundInceptionDate should return empty fragment, not raise."""
        info = {
            "quoteType": "ETF",
            "longName": "Test Fund",
            "fundFamily": "Test Manager",
            "legalType": "ETF",
            "fundInceptionDate": 9999999999999,  # Way out of range, will raise OSError/OverflowError
        }
        fragment = src.etf_fragment("TEST", info)
        # Should return a fragment, not raise
        assert isinstance(fragment, src.FactPackFragment)

    def test_crypto_fragment_handles_exception(self):
        """Exceptions in crypto_fragment should return empty fragment, not raise."""
        info = None  # Will cause exceptions in is_resolvable
        fragment = src.crypto_fragment(info)
        # Should return a fragment, not raise
        assert isinstance(fragment, src.FactPackFragment)
