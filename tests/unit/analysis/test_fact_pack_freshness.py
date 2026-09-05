"""Per-run fact-pack freshness summary.

The 2026-09-05 run served 18 of 64 fact packs from a 2026-08-17 cache. Finding
that out took three greps over the log. One line at the end of Phase 3 should
say it — and it is the freshness-ratio input the run gate (workstream A) needs.
"""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from finwiz.analysis.fact_pack_freshness import summarize_fact_pack_freshness

NOW = datetime(2026, 9, 5, 12, 0, tzinfo=UTC)


def _enriched(freshness: str | None, fetched_at: datetime | None = None) -> SimpleNamespace:
    """An EnrichedAnalysis stand-in: only .qualitative.fact_pack.{freshness,fetched_at} are read."""
    fact_pack = None if freshness is None else SimpleNamespace(freshness=freshness, fetched_at=fetched_at or NOW)
    return SimpleNamespace(qualitative=SimpleNamespace(fact_pack=fact_pack))


class TestSummarizeFactPackFreshness:
    def test_counts_every_bucket_and_every_way_of_being_missing(self) -> None:
        by_ticker = {
            "A": _enriched("fresh"),
            "B": _enriched("fresh"),
            "C": _enriched("recent"),
            "D": _enriched("stale", datetime(2026, 8, 23, tzinfo=UTC)),
            "E": _enriched("stale", datetime(2026, 8, 17, 13, 15, tzinfo=UTC)),
            "F": None,  # holding failed outright
            "G": SimpleNamespace(qualitative=None),  # qualitative stage failed
            "H": _enriched(None),  # fact_pack stage failed
        }
        s = summarize_fact_pack_freshness(by_ticker)
        assert (s.total, s.fresh, s.recent, s.stale, s.missing) == (8, 2, 1, 2, 3)
        assert s.oldest_stale_fetched_at == datetime(2026, 8, 17, 13, 15, tzinfo=UTC)
        assert s.stale_ratio == pytest.approx(0.25)

    def test_line_reads_like_the_thing_you_would_otherwise_grep_for(self) -> None:
        by_ticker = {"A": _enriched("fresh"), "E": _enriched("stale", datetime(2026, 8, 17, 13, 15, tzinfo=UTC)), "F": None}
        line = summarize_fact_pack_freshness(by_ticker).line(now=NOW)
        assert line == "fact_pack freshness: 1 fresh, 0 recent, 1 stale (oldest 2026-08-17, 19 days ago), 1 missing — 3 holdings"

    def test_no_stale_means_no_oldest_clause(self) -> None:
        line = summarize_fact_pack_freshness({"A": _enriched("fresh"), "B": _enriched("recent")}).line(now=NOW)
        assert "oldest" not in line
        assert line.endswith("0 missing — 2 holdings")

    def test_empty_run(self) -> None:
        s = summarize_fact_pack_freshness({})
        assert s.total == 0 and s.stale_ratio == 0.0
        assert s.line(now=NOW) == "fact_pack freshness: 0 fresh, 0 recent, 0 stale, 0 missing — 0 holdings"

    def test_naive_fetched_at_is_treated_as_utc(self) -> None:
        s = summarize_fact_pack_freshness({"E": _enriched("stale", datetime(2026, 8, 17, 13, 15))})
        assert "19 days ago" in s.line(now=NOW)

    def test_unknown_freshness_value_counts_as_missing_not_as_fresh(self) -> None:
        s = summarize_fact_pack_freshness({"X": _enriched("bogus")})
        assert (s.fresh, s.missing) == (0, 1)
