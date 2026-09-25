# ADR-015: Cache web-research results on disk

**Status:** Accepted
**Date:** 2026-09-25
**Supersedes:** nothing. Complements ADR-012 (research provider) and ADR-010 (fact-pack cache).

## Context

On the 67-holding run of 2026-09-21, web research cost $4.58 of $5.57 (82%):
`research_news` $1.81 (134 calls), `research_swot` $1.43 (67), `research_porter`
$1.31 (67). The deep-analysis crew was $1.00.

Every research call pays OpenRouter's Exa search fee ($0.007 per request) plus
prompt tokens for about 3 000 tokens of injected search results. Provider prompt
caching cannot help: the date, ticker, facts and search results come first in
each prompt, and the only stable prefix (the system prompt) is below the
provider's minimum cacheable size. Nothing reused the *answers* either, so a
second run on the same day paid the full $4.58 again, although SWOT and Porter
answers barely change in days and the news window is a week.

## Decision

`research_with_retry` takes an optional `cache_key`. When it is set and the
call's `kind` has a TTL, a stored answer younger than the TTL is returned with
no request; otherwise the call runs as before and a successful answer is stored.

- Store: `ResearchCache` (`src/finwiz/cache/research_cache.py`), one JSON file
  per answer at `cache/research/<kind>/<sha256(key)>.json`, holding the
  validated data, the citations and `fetched_at`. Writes are atomic.
- TTLs, in `research_retry._CACHE_TTL`: `swot` and `porter` 72 h (the fact
  pack's "fresh" band), `news` 24 h. `posture` (one portfolio-level call) and
  `factpack` (already behind `FactPackCache`) are not cached.
- Keys: SWOT and Porter use `ticker|asset_class`; news uses
  `ticker|asset_type|analysis_type|max_results|query`.
- A miss is anything absent, older than the TTL, unreadable, or no longer valid
  against the caller's schema. A failed call (`None`) is never stored.
- A hit records no cost. The cost summary counts hits on its own line
  (`cache hits (no request, $0): research_swot 67, ...`).

Delete `cache/research/` to force fresh research.

## Consequences

### Positive

- A same-day re-run pays nothing for SWOT, Porter and news; a re-run within
  three days pays only for news.
- `run_summary.json` cost stays the real spend of the run.

### Negative

- Editing a prompt template does not invalidate stored answers; for up to 72 h
  a re-run shows answers written under the old wording. A schema change does
  invalidate them.
- An answer's age is logged but not shown in the report.

### Risks

- A stale answer outlives a material event inside the TTL (e.g. an
  acquisition announced yesterday). News, the channel for such events, has the
  shortest TTL; delete the cache before a run where this matters.

## References

- `src/finwiz/cache/research_cache.py`
- `src/finwiz/infrastructure/resilience/research_retry.py`
- ADR-012 (OpenRouter research provider), ADR-010 (fact-pack cache)
