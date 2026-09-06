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


class TestSchemaGuards:
    """FactPack's own Field(max_length=...) caps must never surface as a raise.

    NTNX's real longBusinessSummary was 2212 chars against a 2000-char cap on
    2026-09-06 -- this is not a hypothetical edge case.
    """

    def test_a_business_summary_over_the_schema_cap_is_truncated_not_rejected(self, mocker):
        long_summary = "A" * 2500
        mocker.patch.object(composer.yfinance_source, "resolve", return_value={"quoteType": "EQUITY", "longBusinessSummary": long_summary})
        mocker.patch.object(composer.yfinance_source, "equity_fragment", return_value=FactPackFragment(corporate_structure=long_summary))
        mocker.patch.object(composer.yfinance_source, "filing_events", return_value=FactPackFragment())
        mocker.patch.object(composer.yfinance_source, "news_events", return_value=FactPackFragment())

        pack = composer.compose_fact_pack("NTNX", "Nutanix", None, None, "stock")

        assert len(pack.corporate_structure) == 2000

    def test_citations_over_the_schema_cap_are_truncated_not_rejected(self, mocker):
        """An ETF's quote-page citation plus a full 10 filings + 10 news is 21."""
        mocker.patch.object(composer.yfinance_source, "resolve", return_value={"quoteType": "ETF", "fundFamily": "iShares"})
        mocker.patch.object(
            composer.yfinance_source,
            "etf_fragment",
            return_value=FactPackFragment(corporate_structure="iShares World ETF.", citations=("https://finance.yahoo.com/quote/2B7K.DE",), sources=("yfinance.info",)),
        )
        mocker.patch.object(
            composer.yfinance_source,
            "filing_events",
            return_value=FactPackFragment(
                recent_events=("2026-09-01 8-K: Changes",),
                citations=tuple(f"https://filing/{i}" for i in range(10)),
                events_from_filings=True,
                sources=("yfinance.sec_filings",),
            ),
        )
        mocker.patch.object(
            composer.yfinance_source,
            "news_events",
            return_value=FactPackFragment(citations=tuple(f"https://news/{i}" for i in range(10)), sources=("yfinance.news",)),
        )

        pack = composer.compose_fact_pack("2B7K.DE", "iShares World", None, None, "etf")

        assert len(pack.source_citations) == 20

    def test_an_unexpected_construction_failure_falls_back_to_a_minimal_pack(self, mocker, caplog):
        """The clamps above cover every constraint this module knows about; this

        is the backstop for one it doesn't -- the composer's contract is that
        nothing reaches the caller as an exception.
        """
        mocker.patch.object(composer.yfinance_source, "resolve", return_value={"quoteType": "EQUITY", "longBusinessSummary": "Designs phones."})
        mocker.patch.object(composer.yfinance_source, "filing_events", return_value=FactPackFragment())
        mocker.patch.object(composer.yfinance_source, "news_events", return_value=FactPackFragment())

        original_init = composer.FactPack.__init__
        calls = {"n": 0}

        def _flaky_init(self, *args, **kwargs):
            calls["n"] += 1
            if calls["n"] == 1:
                raise ValueError("simulated schema failure")
            original_init(self, *args, **kwargs)

        mocker.patch.object(composer.FactPack, "__init__", _flaky_init)

        with caplog.at_level("ERROR"):
            pack = composer.compose_fact_pack("AAPL", "Apple Inc.", None, None, "stock")

        assert pack is not None
        assert pack.corporate_structure == PLACEHOLDER
        assert pack.leadership == PLACEHOLDER
        assert pack.confidence == 0.0
        assert any(r.levelname == "ERROR" and "AAPL" in r.message for r in caplog.records)
        # A fallback pack is otherwise byte-identical to a legitimately
        # data-free holding; the marker is the only way to tell them apart
        # once this log line has scrolled off (packs are cached to disk).
        assert "composer.schema_fallback" in pack.sources_used


class TestSymbolNormalization:
    """yfinance's own `BTC` is a Grayscale trust ETF, not the coin.

    Domain-model tickers stay bare (BTC, AAVE); only the yfinance query needs
    the `-USD` suffix. Without normalization, two crypto holdings fetch facts
    about the wrong instrument and a third (SOL) resolves to nothing at all.
    """

    def test_a_crypto_ticker_is_queried_with_the_usd_suffix(self, mocker):
        resolve = mocker.patch.object(composer.yfinance_source, "resolve", return_value={"quoteType": "CRYPTOCURRENCY", "longName": "Bitcoin USD"})
        mocker.patch.object(composer.yfinance_source, "filing_events", return_value=FactPackFragment())
        mocker.patch.object(composer.yfinance_source, "news_events", return_value=FactPackFragment())

        composer.compose_fact_pack("BTC", "Bitcoin", None, None, "crypto")

        resolve.assert_called_once_with("BTC-USD")

    def test_a_stock_ticker_is_queried_unchanged(self, mocker):
        resolve = mocker.patch.object(composer.yfinance_source, "resolve", return_value={"quoteType": "EQUITY", "longBusinessSummary": "Designs phones."})
        mocker.patch.object(composer.yfinance_source, "filing_events", return_value=FactPackFragment())
        mocker.patch.object(composer.yfinance_source, "news_events", return_value=FactPackFragment())

        composer.compose_fact_pack("AAPL", "Apple Inc.", None, None, "stock")

        resolve.assert_called_once_with("AAPL")

    def test_an_etf_ticker_is_queried_unchanged(self, mocker):
        resolve = mocker.patch.object(composer.yfinance_source, "resolve", return_value={"quoteType": "ETF", "fundFamily": "iShares"})
        mocker.patch.object(composer.yfinance_source, "filing_events", return_value=FactPackFragment())
        mocker.patch.object(composer.yfinance_source, "news_events", return_value=FactPackFragment())

        composer.compose_fact_pack("2B7K.DE", "iShares World", None, None, "etf")

        resolve.assert_called_once_with("2B7K.DE")

    def test_the_etf_citation_url_uses_the_query_symbol_not_the_bare_ticker(self, mocker):
        """BRK.B is renamed to BRK-B at the yfinance boundary (ticker_hygiene);

        a citation built from the bare ticker would point at a page Yahoo 404s.
        Uses the real etf_fragment (not mocked) so the citation URL reflects
        whatever symbol the composer actually threads through.
        """
        mocker.patch.object(
            composer.yfinance_source,
            "resolve",
            return_value={"quoteType": "ETF", "longName": "Test Fund", "fundFamily": "Test Manager", "legalType": "Exchange Traded Fund", "fundInceptionDate": 1602460800},
        )
        mocker.patch.object(composer.yfinance_source, "filing_events", return_value=FactPackFragment())
        mocker.patch.object(composer.yfinance_source, "news_events", return_value=FactPackFragment())

        pack = composer.compose_fact_pack("BRK.B", "Test Fund", None, None, "etf")

        assert pack.source_citations == ["https://finance.yahoo.com/quote/BRK-B"]
