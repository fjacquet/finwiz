---
phase: 2
plan: "02-01"
subsystem: discovery
tags: [pydantic, schemas, yfinance, etf-mining, universe-provider]
dependency-graph:
  requires: []
  provides: [newcomer-schemas, discovery-package, universe-provider]
  affects: [02-02, 03-01, 03-02]
tech-stack:
  added: []
  patterns: [etf-holdings-mining, static-fallback]
key-files:
  created:
    - src/finwiz/discovery/__init__.py
    - src/finwiz/discovery/universe_provider.py
  modified:
    - src/finwiz/schemas/newcomer_discovery.py
    - src/finwiz/schemas/__init__.py
decisions:
  - Keep Literal["stock","etf","crypto"] instead of AssetClass enum (simpler, matches existing pattern)
  - Crypto goes straight to static fallback (no yfinance ETF holdings for crypto)
  - Per-ETF error isolation (individual fetch failures skip, not abort entire mining)
metrics:
  duration: "2m 40s"
  completed: "2026-02-08"
---

# Phase 2 Plan 01: Discovery Schemas and Universe Provider Summary

JWT-style ticker universe mining via yfinance ETF holdings with ScreeningUtils fallback, plus screener fields on NewcomerCandidate schema.

## Tasks Completed

| Task | Description | Commit | Key Changes |
|------|-------------|--------|-------------|
| 1 | Extend newcomer discovery schemas | 6225aad | Added market_cap, sector, discovery_date to NewcomerCandidate; sources_used, top_picks to NewcomerDiscoveryResult |
| 2 | Register schemas in package init | b11e062 | Import/export 3 newcomer schemas from finwiz.schemas |
| 3 | Create discovery package __init__ | 76aef86 | New finwiz.discovery package exporting DynamicUniverseProvider |
| 4 | Implement DynamicUniverseProvider | 08c8ed5 | ETF holdings mining via yfinance, static fallback, per-ETF error isolation |

## Decisions Made

1. **Literal over Enum**: Kept `Literal["stock", "etf", "crypto"]` on schemas instead of switching to `AssetClass` enum -- simpler and matches existing file pattern.
2. **Crypto static-only**: Crypto universe goes directly to static fallback because yfinance does not expose crypto ETF holdings.
3. **Per-ETF isolation**: Individual ETF fetch failures log a warning and skip; only if ALL ETFs fail does the full fallback trigger.

## Deviations from Plan

None -- plan executed exactly as written.

## Verification Results

All 6 verification checks passed:
- Schema field defaults (market_cap=None, discovery_date=now, sources_used=[], top_picks=[])
- Package-level imports from finwiz.schemas
- Discovery package import of DynamicUniverseProvider
- Provider instantiation without network calls
- JSON serialization round-trip
- Ruff lint clean

## Next Phase Readiness

- **02-02** can now import `DynamicUniverseProvider` from `finwiz.discovery`
- **02-02** will add IPOScreener, BreakoutDetector, MomentumScanner, CandidateScorer
- Phase 3 lazy imports for discovery modules will resolve once 02-02 completes
