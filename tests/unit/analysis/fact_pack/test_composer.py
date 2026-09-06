"""Routing, merge order and FactPack construction."""

import pytest

from finwiz.analysis.fact_pack import composer
from finwiz.analysis.fact_pack.fragment import PLACEHOLDER, FactPackFragment
from finwiz.schemas.hybrid_analysis.fact_pack import CryptoFacts, FundFacts, FundHolding


@pytest.fixture(autouse=True)
def _no_gap_fill(mocker):
    """Deterministic path only; test_gap_fill.py exercises the Perplexity hook.

    Without this, an equity fixture with no recent_events would fall through
    to a real `is_feature_enabled("perplexity_research")` check (default: on)
    and attempt a live Perplexity call from these otherwise network-free tests.
    """
    mocker.patch.object(composer, "is_feature_enabled", return_value=False)


class TestRouting:
    def test_asset_class_comes_from_the_caller_never_from_the_symbol(self, mocker):
        """ASML.AS is 7 characters; a symbol-shape heuristic once called that crypto.

        Routing reads the declared class and nothing else. Asserts against the
        seams routing actually uses (fund_source/crypto_source) rather than the
        now-uncalled yfinance_source.crypto_fragment -- a stock must never
        reach the fund or crypto builder.
        """
        mocker.patch.object(composer.yfinance_source, "resolve", return_value={"quoteType": "EQUITY", "longBusinessSummary": "Chip lithography."})
        equity = mocker.patch.object(composer.yfinance_source, "equity_fragment", return_value=FactPackFragment(corporate_structure="Chip lithography."))
        fund_facts = mocker.patch.object(composer.fund_source, "fund_facts")
        crypto_facts = mocker.patch.object(composer.crypto_source, "crypto_facts")
        mocker.patch.object(composer.yfinance_source, "filing_events", return_value=FactPackFragment())
        mocker.patch.object(composer.yfinance_source, "news_events", return_value=FactPackFragment())

        pack = composer.compose_fact_pack("ASML.AS", "ASML Holding", None, None, "stock")

        equity.assert_called_once()
        fund_facts.assert_not_called()
        crypto_facts.assert_not_called()
        assert pack.details.kind == "equity"

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

        assert pack.details.recent_events == ["2026-09-01 8-K: Changes"]
        assert "yfinance.sec_filings" in pack.sources_used

    def test_empty_fields_become_the_placeholder_not_an_empty_string(self, mocker):
        mocker.patch.object(composer.yfinance_source, "resolve", return_value={"quoteType": "CRYPTOCURRENCY", "longName": "Bitcoin USD"})

        pack = composer.compose_fact_pack("BTC-USD", "Bitcoin", None, None, "crypto")

        # CryptoFacts.description requires min_length=1; the placeholder
        # satisfies the schema without asserting a fact nobody has -- there is
        # no `description` in `info` here, so crypto_source.crypto_facts
        # declines to build facts at all.
        assert pack.details.description == PLACEHOLDER
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

        assert len(pack.details.business_summary) == 2000

    def test_citations_over_the_schema_cap_are_truncated_not_rejected(self, mocker):
        """A fund whose builder somehow returns 21 citations must still fit the 20-URL cap."""
        mocker.patch.object(composer.yfinance_source, "resolve", return_value={"quoteType": "ETF", "fundFamily": "iShares"})
        mocker.patch.object(
            composer.fund_source,
            "fund_facts",
            return_value=(
                FundFacts(issuer="iShares"),
                tuple(f"https://example.com/citation/{i}" for i in range(21)),
                ("yfinance.info", "yfinance.funds_data"),
            ),
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
        assert pack.details.business_summary == PLACEHOLDER
        assert pack.details.leadership == PLACEHOLDER
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
        mocker.patch.object(composer.fund_source, "fund_facts", return_value=(None, (), ()))

        composer.compose_fact_pack("2B7K.DE", "iShares World", None, None, "etf")

        resolve.assert_called_once_with("2B7K.DE")

    def test_the_etf_citation_url_uses_the_query_symbol_not_the_bare_ticker(self, mocker):
        """BRK.B is renamed to BRK-B at the yfinance boundary (ticker_hygiene);

        a citation built from the bare ticker would point at a page Yahoo 404s.
        Uses the real fund_source.fund_facts (not mocked) so the citation URL
        reflects whatever symbol the composer actually threads through --
        only the network seam (`_ticker`) is mocked, so funds_data resolves
        to nothing without touching the network.
        """
        mocker.patch.object(
            composer.yfinance_source,
            "resolve",
            return_value={"quoteType": "ETF", "longName": "Test Fund", "fundFamily": "Test Manager", "legalType": "Exchange Traded Fund", "fundInceptionDate": 1602460800},
        )
        mocker.patch.object(composer.yfinance_source, "_ticker", return_value=mocker.Mock(funds_data=None))

        pack = composer.compose_fact_pack("BRK.B", "Test Fund", None, None, "etf")

        assert pack.source_citations == ["https://finance.yahoo.com/quote/BRK-B"]


class TestPerClassComposition:
    def test_a_fund_gets_fund_facts_and_never_an_equity_shape(self, mocker):
        mocker.patch.object(composer.yfinance_source, "resolve", return_value={"quoteType": "ETF", "fundFamily": "iShares"})
        mocker.patch.object(
            composer.fund_source,
            "fund_facts",
            return_value=(
                FundFacts(issuer="iShares", expense_ratio=0.002, asset_mix={"stockPosition": 1.0}, top_holdings=[FundHolding(symbol="NVDA", name="NVIDIA Corp", weight=0.07)]),
                ("https://finance.yahoo.com/quote/2B7K.DE",),
                ("yfinance.info", "yfinance.funds_data"),
            ),
        )

        pack = composer.compose_fact_pack("2B7K.DE", "iShares World", None, None, "etf")

        assert pack.asset_class == "etf"
        assert pack.details.kind == "fund"
        assert pack.confidence == 1.0

    def test_a_crypto_holding_gets_crypto_facts(self, mocker):
        mocker.patch.object(composer.yfinance_source, "resolve", return_value={"quoteType": "CRYPTOCURRENCY", "description": "Bitcoin is..."})
        mocker.patch.object(
            composer.crypto_source,
            "crypto_facts",
            return_value=(
                CryptoFacts(description="Bitcoin is...", launched_year=2010, circulating_supply=20080456.0, max_supply=21000000.0, supply_is_capped=True, market_cap=1.6e12),
                ("https://coinmarketcap.com/currencies/bitcoin/",),
            ),
        )

        pack = composer.compose_fact_pack("BTC", "Bitcoin", None, None, "crypto")

        assert pack.asset_class == "crypto"
        assert pack.details.kind == "crypto"
        assert pack.details.supply_is_capped is True

    def test_a_fund_whose_builder_returns_none_still_yields_a_pack(self, mocker):
        """A fund with no issuer is thin, not fatal -- only an unresolvable ticker is fatal."""
        mocker.patch.object(composer.yfinance_source, "resolve", return_value={"quoteType": "ETF"})
        mocker.patch.object(composer.fund_source, "fund_facts", return_value=(None, (), ()))

        pack = composer.compose_fact_pack("XXXX.DE", "Unknown fund", None, None, "etf")

        assert pack is not None
        assert pack.details.kind == "fund"
        assert pack.confidence == 0.0

    def test_an_unresolvable_ticker_still_returns_none(self, mocker):
        mocker.patch.object(composer.yfinance_source, "resolve", return_value={"trailingPegRatio": None})
        assert composer.compose_fact_pack("ZZZZNOTREAL", "Nothing", None, None, "stock") is None

    def test_a_substituted_expense_ratio_is_visible_in_provenance(self, mocker):
        """fund_source's third tuple element names the curated-table substitution.

        The composer must propagate whatever `sources` fund_facts returns
        rather than hardcoding it -- a hardcoded tuple here would silently
        launder a curated data/etf_expense_ratios.yaml value as a live
        yfinance reading, which is exactly what fund_facts's real 3-tuple
        return exists to make visible.
        """
        mocker.patch.object(composer.yfinance_source, "resolve", return_value={"quoteType": "ETF", "fundFamily": "iShares"})
        mocker.patch.object(
            composer.fund_source,
            "fund_facts",
            return_value=(
                FundFacts(issuer="iShares", expense_ratio=0.0019),
                ("https://finance.yahoo.com/quote/2B7K.DE",),
                ("yfinance.info", "yfinance.funds_data", "etf_expense_ratios.yaml"),
            ),
        )

        pack = composer.compose_fact_pack("2B7K.DE", "iShares World", None, None, "etf")

        assert "etf_expense_ratios.yaml" in pack.sources_used


class TestUnknownAssetClass:
    """An unenumerated asset_class must degrade to a labelled 'stock' pack, never kill the holding.

    Before the entry-point normalisation, an unknown value reached the
    backstop's _FALLBACK_DETAILS[asset_class] lookup unnormalised: the main
    FactPack(...) call correctly rejected it (Literal validation), the except
    caught that, and then the fallback line raised KeyError -- uncaught,
    inside the one code path whose entire purpose is that a holding never
    dies.
    """

    def test_an_unknown_asset_class_degrades_to_stock_with_a_warning(self, mocker, caplog):
        mocker.patch.object(composer.yfinance_source, "resolve", return_value={"quoteType": "EQUITY", "longBusinessSummary": "Designs phones."})
        mocker.patch.object(composer.yfinance_source, "filing_events", return_value=FactPackFragment())
        mocker.patch.object(composer.yfinance_source, "news_events", return_value=FactPackFragment())

        with caplog.at_level("WARNING"):
            pack = composer.compose_fact_pack("AAPL", "Apple Inc.", None, None, "bond")

        assert pack is not None
        assert pack.asset_class == "stock"
        assert pack.details.kind == "equity"
        assert any("unknown asset_class='bond'" in r.message for r in caplog.records)

    @pytest.mark.parametrize("asset_class", ["stock", "etf", "crypto"])
    def test_the_backstop_still_returns_a_valid_pack_for_each_real_class(self, mocker, asset_class):
        """The normalisation must not weaken the backstop for the three real classes."""
        info_by_class = {
            "stock": {"quoteType": "EQUITY", "longBusinessSummary": "Designs phones."},
            "etf": {"quoteType": "ETF", "fundFamily": "iShares"},
            "crypto": {"quoteType": "CRYPTOCURRENCY", "description": "Bitcoin is..."},
        }
        mocker.patch.object(composer.yfinance_source, "resolve", return_value=info_by_class[asset_class])
        mocker.patch.object(composer.yfinance_source, "filing_events", return_value=FactPackFragment())
        mocker.patch.object(composer.yfinance_source, "news_events", return_value=FactPackFragment())
        mocker.patch.object(composer.fund_source, "fund_facts", return_value=(FundFacts(issuer="iShares"), (), ()))
        mocker.patch.object(composer.crypto_source, "crypto_facts", return_value=(CryptoFacts(description="Bitcoin is..."), ()))

        original_init = composer.FactPack.__init__
        calls = {"n": 0}

        def _flaky_init(self, *args, **kwargs):
            calls["n"] += 1
            if calls["n"] == 1:
                raise ValueError("simulated schema failure")
            original_init(self, *args, **kwargs)

        mocker.patch.object(composer.FactPack, "__init__", _flaky_init)

        pack = composer.compose_fact_pack("TICKER", "Some Holding", None, None, asset_class)

        assert pack is not None
        assert pack.asset_class == asset_class
        assert pack.confidence == 0.0
        assert "composer.schema_fallback" in pack.sources_used
