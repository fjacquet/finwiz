"""Fragment merge and confidence derivation."""

from finwiz.analysis.fact_pack.fragment import FactPackFragment, derive_confidence, merge_fragments


class TestMergeFragments:
    def test_first_non_empty_wins_and_nothing_overwrites(self):
        first = FactPackFragment(corporate_structure="Independent entity.", sources=("yfinance.equity",))
        second = FactPackFragment(corporate_structure="A later, weaker guess.", leadership="Jane Doe, CEO", sources=("perplexity",))

        merged = merge_fragments(first, second)

        assert merged.corporate_structure == "Independent entity."
        assert merged.leadership == "Jane Doe, CEO"
        assert merged.sources == ("yfinance.equity", "perplexity")

    def test_citations_concatenate_and_deduplicate_preserving_order(self):
        first = FactPackFragment(citations=("https://a.example", "https://b.example"))
        second = FactPackFragment(citations=("https://b.example", "https://c.example"))

        assert merge_fragments(first, second).citations == ("https://a.example", "https://b.example", "https://c.example")

    def test_events_from_filings_survives_a_later_news_fragment(self):
        filings = FactPackFragment(recent_events=("2026-09-01 8-K: Corporate Changes",), events_from_filings=True)
        news = FactPackFragment(recent_events=("Some headline",))

        merged = merge_fragments(filings, news)

        # recent_events is first-non-empty like every other field, so the filing
        # events win outright and the flag must still describe what was kept.
        assert merged.recent_events == ("2026-09-01 8-K: Corporate Changes",)
        assert merged.events_from_filings is True


class TestDeriveConfidence:
    def test_us_stock_with_filings_scores_one(self):
        fragment = FactPackFragment(
            corporate_structure="Apple Inc. designs...",
            leadership="Tim Cook, CEO",
            recent_events=("2026-09-01 8-K: Corporate Changes",),
            citations=("https://example.com/edgar",),
            events_from_filings=True,
        )
        assert derive_confidence(fragment) == 1.0

    def test_european_stock_with_news_events_scores_0_85(self):
        fragment = FactPackFragment(
            corporate_structure="Airbus SE manufactures...",
            leadership="Guillaume Faury, CEO",
            recent_events=("Airbus wins order",),
            citations=("https://example.com/news",),
        )
        assert derive_confidence(fragment) == 0.85

    def test_typical_etf_scores_0_70(self):
        fragment = FactPackFragment(
            corporate_structure="UCITS ETF issued by BlackRock...",
            leadership="BlackRock Asset Management Ireland - ETF",
            citations=("https://finance.yahoo.com/quote/2B7K.DE",),
        )
        assert derive_confidence(fragment) == 0.70

    def test_crypto_with_news_only_scores_0_25(self):
        fragment = FactPackFragment(recent_events=("Bitcoin headline",), citations=("https://example.com/news",))
        assert derive_confidence(fragment) == 0.25

    def test_placeholder_text_does_not_count_as_populated(self):
        fragment = FactPackFragment(corporate_structure="Information indisponible", leadership="Information indisponible")
        assert derive_confidence(fragment) == 0.0
