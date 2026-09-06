"""Fragment merge order and precedence."""

from finwiz.analysis.fact_pack.fragment import FactPackFragment, merge_fragments


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
