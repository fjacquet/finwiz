"""Gap-fill may add events to an equity. It may never overwrite, and never fail a pack."""

from finwiz.analysis.fact_pack import composer
from finwiz.analysis.fact_pack.sources import perplexity_source


class TestGapFillScope:
    def test_an_equity_without_events_asks_perplexity(self, mocker):
        mocker.patch.object(
            composer.yfinance_source,
            "resolve",
            return_value={"quoteType": "EQUITY", "longBusinessSummary": "Builds planes.", "companyOfficers": [{"name": "G. Faury", "title": "CEO"}]},
        )
        mocker.patch.object(composer.yfinance_source, "filing_events", return_value=composer.FactPackFragment())
        mocker.patch.object(composer.yfinance_source, "news_events", return_value=composer.FactPackFragment())
        mocker.patch.object(composer, "is_feature_enabled", return_value=True)
        fetch = mocker.patch.object(perplexity_source, "fetch_missing_events", return_value=("Airbus wins order",))

        pack = composer.compose_fact_pack("AIR.PA", "Airbus SE", None, None, "stock")

        fetch.assert_called_once()
        assert pack.details.recent_events == ["Airbus wins order"]
        assert pack.details.events_from_filings is False

    def test_an_equity_with_filing_events_never_asks(self, mocker):
        mocker.patch.object(
            composer.yfinance_source,
            "resolve",
            return_value={"quoteType": "EQUITY", "longBusinessSummary": "Designs phones.", "companyOfficers": [{"name": "T. Cook", "title": "CEO"}]},
        )
        mocker.patch.object(
            composer.yfinance_source,
            "filing_events",
            return_value=composer.FactPackFragment(recent_events=("2026-09-01 8-K: Changes",), events_from_filings=True, sources=("yfinance.sec_filings",)),
        )
        mocker.patch.object(composer.yfinance_source, "news_events", return_value=composer.FactPackFragment())
        mocker.patch.object(composer, "is_feature_enabled", return_value=True)
        fetch = mocker.patch.object(perplexity_source, "fetch_missing_events")

        composer.compose_fact_pack("AAPL", "Apple Inc.", None, None, "stock")

        fetch.assert_not_called()

    def test_a_fund_never_asks_however_thin_it_is(self, mocker):
        """Funds are complete from deterministic sources; there is nothing to buy."""
        mocker.patch.object(composer.yfinance_source, "resolve", return_value={"quoteType": "ETF"})
        # NOTE: the brief's Step 1 verbatim gives `(None, ())` here, a 2-tuple.
        # composer.py's fund branch unpacks `fund_source.fund_facts(...)` into
        # three values (facts, citations, sources) -- see every fixture in
        # test_composer.py's TestPerClassComposition -- so a 2-tuple raises
        # ValueError before this test's assertions ever run. Fixed to the
        # real 3-tuple shape; flagged in the Task 8 report as a brief defect.
        mocker.patch.object(composer.fund_source, "fund_facts", return_value=(None, (), ()))
        mocker.patch.object(composer, "is_feature_enabled", return_value=True)
        fetch = mocker.patch.object(perplexity_source, "fetch_missing_events")

        composer.compose_fact_pack("XXXX.DE", "Unknown fund", None, None, "etf")

        fetch.assert_not_called()

    def test_the_feature_flag_switches_it_off(self, mocker):
        mocker.patch.object(
            composer.yfinance_source,
            "resolve",
            return_value={"quoteType": "EQUITY", "longBusinessSummary": "Builds planes.", "companyOfficers": [{"name": "G. Faury", "title": "CEO"}]},
        )
        mocker.patch.object(composer.yfinance_source, "filing_events", return_value=composer.FactPackFragment())
        mocker.patch.object(composer.yfinance_source, "news_events", return_value=composer.FactPackFragment())
        mocker.patch.object(composer, "is_feature_enabled", return_value=False)
        fetch = mocker.patch.object(perplexity_source, "fetch_missing_events")

        composer.compose_fact_pack("AIR.PA", "Airbus SE", None, None, "stock")

        fetch.assert_not_called()

    def test_a_quota_401_leaves_the_deterministic_pack_intact(self, mocker):
        """The 2026-09-06 outage in one assertion."""
        mocker.patch.object(
            composer.yfinance_source,
            "resolve",
            return_value={"quoteType": "EQUITY", "longBusinessSummary": "Builds planes.", "companyOfficers": [{"name": "G. Faury", "title": "CEO"}]},
        )
        mocker.patch.object(composer.yfinance_source, "filing_events", return_value=composer.FactPackFragment())
        mocker.patch.object(composer.yfinance_source, "news_events", return_value=composer.FactPackFragment())
        mocker.patch.object(composer, "is_feature_enabled", return_value=True)
        mocker.patch.object(perplexity_source, "fetch_missing_events", side_effect=RuntimeError("Perplexity HTTP 401 insufficient_quota"))

        pack = composer.compose_fact_pack("AIR.PA", "Airbus SE", None, None, "stock")

        assert pack is not None
        assert pack.details.business_summary == "Builds planes."
        assert pack.details.recent_events == []
