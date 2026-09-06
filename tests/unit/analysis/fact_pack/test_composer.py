"""Routing, merge order and FactPack construction."""

import pytest

from finwiz.analysis.fact_pack import composer
from finwiz.analysis.fact_pack.fragment import PLACEHOLDER, FactPackFragment


@pytest.fixture(autouse=True)
def _no_gap_fill(mocker):
    """Deterministic path only; Task 5 wires and tests the Perplexity hook."""
    mocker.patch.object(composer, "_gap_fill", return_value=FactPackFragment())


class TestRouting:
    def test_asset_class_comes_from_the_caller_never_from_the_symbol(self, mocker):
        """ASML.AS is 7 characters; a symbol-shape heuristic once called that crypto.

        Routing reads the declared class and nothing else.
        """
        mocker.patch.object(composer.yfinance_source, "resolve", return_value={"quoteType": "EQUITY", "longBusinessSummary": "Chip lithography."})
        equity = mocker.patch.object(composer.yfinance_source, "equity_fragment", return_value=FactPackFragment(corporate_structure="Chip lithography."))
        crypto = mocker.patch.object(composer.yfinance_source, "crypto_fragment", return_value=FactPackFragment())
        mocker.patch.object(composer.yfinance_source, "filing_events", return_value=FactPackFragment())
        mocker.patch.object(composer.yfinance_source, "news_events", return_value=FactPackFragment())

        composer.compose_fact_pack("ASML.AS", "ASML Holding", None, None, "stock")

        equity.assert_called_once()
        crypto.assert_not_called()

    def test_a_declared_class_that_contradicts_quote_type_is_warned_about(self, mocker, caplog):
        mocker.patch.object(composer.yfinance_source, "resolve", return_value={"quoteType": "ETF", "fundFamily": "iShares"})
        mocker.patch.object(composer.yfinance_source, "filing_events", return_value=FactPackFragment())
        mocker.patch.object(composer.yfinance_source, "news_events", return_value=FactPackFragment())

        composer.compose_fact_pack("2B7K.DE", "iShares World", None, None, "stock")

        assert any("declared asset_class" in r.message for r in caplog.records)


class TestUnresolvable:
    def test_an_unresolvable_ticker_returns_none(self, mocker):
        mocker.patch.object(composer.yfinance_source, "resolve", return_value={"trailingPegRatio": None})
        assert composer.compose_fact_pack("ZZZZNOTREAL", "Nothing", None, None, "stock") is None


class TestPackConstruction:
    def test_filings_outrank_news_for_recent_events(self, mocker):
        mocker.patch.object(composer.yfinance_source, "resolve", return_value={"quoteType": "EQUITY", "longBusinessSummary": "Designs phones."})
        mocker.patch.object(
            composer.yfinance_source,
            "filing_events",
            return_value=FactPackFragment(recent_events=("2026-09-01 8-K: Changes",), events_from_filings=True, sources=("yfinance.sec_filings",)),
        )
        mocker.patch.object(composer.yfinance_source, "news_events", return_value=FactPackFragment(recent_events=("A headline",), sources=("yfinance.news",)))

        pack = composer.compose_fact_pack("AAPL", "Apple Inc.", None, None, "stock")

        assert pack.recent_events == ["2026-09-01 8-K: Changes"]
        assert "yfinance.sec_filings" in pack.sources_used

    def test_empty_fields_become_the_placeholder_not_an_empty_string(self, mocker):
        mocker.patch.object(composer.yfinance_source, "resolve", return_value={"quoteType": "CRYPTOCURRENCY", "longName": "Bitcoin USD"})
        mocker.patch.object(composer.yfinance_source, "filing_events", return_value=FactPackFragment())
        mocker.patch.object(composer.yfinance_source, "news_events", return_value=FactPackFragment())

        pack = composer.compose_fact_pack("BTC-USD", "Bitcoin", None, None, "crypto")

        # FactPack requires min_length=1 on both; the placeholder satisfies the
        # schema without asserting a fact nobody has.
        assert pack.corporate_structure == PLACEHOLDER
        assert pack.leadership == PLACEHOLDER
        assert pack.confidence == 0.0

    def test_freshness_stays_python_owned(self, mocker):
        mocker.patch.object(composer.yfinance_source, "resolve", return_value={"quoteType": "EQUITY", "longBusinessSummary": "Designs phones."})
        mocker.patch.object(composer.yfinance_source, "filing_events", return_value=FactPackFragment())
        mocker.patch.object(composer.yfinance_source, "news_events", return_value=FactPackFragment())

        pack = composer.compose_fact_pack("AAPL", "Apple Inc.", None, None, "stock")

        assert pack.freshness == "fresh"
