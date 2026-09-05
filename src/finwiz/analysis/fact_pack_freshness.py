"""One line per run on how fresh the fact packs were.

`FactPack.freshness` is Python-derived from `fetched_at` and already rendered
per holding in the report. What was missing is the aggregate: the 2026-09-05
run served 18 of 64 fact packs from a 2026-08-17 cache, and finding that out
took three greps over the log. This module turns the per-holding results into
one number and one sentence, for the log now and for the run gate later.

Pure: reads `enriched.qualitative.fact_pack.{freshness, fetched_at}` and
nothing else, so a test needs no FactPack, no network and no flow.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

_BUCKETS = ("fresh", "recent", "stale")


@dataclass(frozen=True)
class FactPackFreshnessSummary:
    """Counts by freshness bucket, plus the age of the oldest stale pack."""

    total: int
    fresh: int
    recent: int
    stale: int
    missing: int
    oldest_stale_fetched_at: datetime | None

    @property
    def stale_ratio(self) -> float:
        return self.stale / self.total if self.total else 0.0

    def line(self, now: datetime | None = None) -> str:
        """The sentence to log. `now` is injectable so the age is testable."""
        oldest = ""
        if self.oldest_stale_fetched_at is not None:
            # Calendar days, not truncated elapsed time: a pack fetched on the 17th read
            # on the 5th is "19 days ago" to a reader, even 22 hours short of 19x24h.
            age_days = ((now or datetime.now(UTC)).date() - _as_utc(self.oldest_stale_fetched_at).date()).days
            oldest = f" (oldest {self.oldest_stale_fetched_at.date()}, {age_days} days ago)"
        return f"fact_pack freshness: {self.fresh} fresh, {self.recent} recent, {self.stale} stale{oldest}, {self.missing} missing — {self.total} holdings"


def summarize_fact_pack_freshness(enriched_by_ticker: Mapping[str, Any]) -> FactPackFreshnessSummary:
    """Aggregate per-holding fact-pack freshness for one run.

    A holding is *missing* when the analysis, its qualitative stage or its
    fact_pack stage produced nothing — or when freshness carries a value that is
    not one of the three buckets, which must never be counted as fresh.
    """
    counts = dict.fromkeys(_BUCKETS, 0)
    missing = 0
    oldest_stale: datetime | None = None

    for enriched in enriched_by_ticker.values():
        fact_pack = getattr(getattr(enriched, "qualitative", None), "fact_pack", None)
        freshness = getattr(fact_pack, "freshness", None)
        if freshness not in counts:
            missing += 1
            continue
        counts[freshness] += 1
        fetched_at = getattr(fact_pack, "fetched_at", None)
        if freshness == "stale" and fetched_at is not None and (oldest_stale is None or _as_utc(fetched_at) < _as_utc(oldest_stale)):
            oldest_stale = fetched_at

    return FactPackFreshnessSummary(
        total=len(enriched_by_ticker),
        fresh=counts["fresh"],
        recent=counts["recent"],
        stale=counts["stale"],
        missing=missing,
        oldest_stale_fetched_at=oldest_stale,
    )


def _as_utc(dt: datetime) -> datetime:
    """A naive `fetched_at` is treated as UTC rather than left incomparable."""
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)
