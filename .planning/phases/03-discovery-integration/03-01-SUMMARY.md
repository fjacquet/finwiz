---
phase: 03-discovery-integration
plan: 01
subsystem: scoring
tags: [discovery, pipeline, portfolio-exclusion, json-persistence, lazy-imports]

# Dependency graph
requires:
  - phase: 02-discovery-core
    provides: "Phase 2 discovery modules (universe provider, screeners, scorer, schemas) -- imported lazily"
provides:
  - "NewcomerDiscoveryPipeline class in scoring.discovery.pipeline"
  - "Package-level export from scoring.discovery"
  - "Portfolio ticker exclusion with Yahoo: prefix and crypto -USD normalization"
  - "JSON output persistence to output/discovery/newcomer_{asset_class}.json"
  - "Legacy format conversion for DiscoveryOrchestrator backward compatibility"
affects:
  - "03-02 (Perplexity enrichment, feature flag routing, unit tests)"
  - "02-discovery-core (Phase 2 modules define the API that pipeline calls)"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Lazy imports for Phase 2 modules inside method bodies (graceful ImportError handling)"
    - "TYPE_CHECKING guard + from __future__ import annotations for deferred type evaluation"
    - "Dual crypto ticker normalization (BTC and BTC-USD both in exclusion set)"

key-files:
  created:
    - "src/finwiz/scoring/discovery/pipeline.py"
    - "src/finwiz/scoring/discovery/__init__.py"
  modified: []

key-decisions:
  - "Lazy imports for all Phase 2 modules so pipeline can be imported before Phase 2 is built"
  - "Portfolio exclusion loads ALL 3 CSVs (stock, etf, crypto) regardless of current asset_class"
  - "Crypto tickers stored in both BTC and BTC-USD forms for cross-format matching"
  - "Each screener/scanner wrapped in independent try/except so one failure does not block others"

patterns-established:
  - "Lazy import with ImportError fallback: try/except ImportError pattern for Phase 2 modules"
  - "Deduplication by ticker via seen set in _gather_candidates()"
  - "Legacy format bridge: _to_legacy_format() converts new schemas to existing dict format"

# Metrics
duration: 3min
completed: 2026-02-08
---

# Phase 3 Plan 01: Discovery Pipeline Summary

**NewcomerDiscoveryPipeline orchestrating 4 screeners with CSV-based portfolio exclusion and JSON persistence, using lazy Phase 2 imports for forward compatibility**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-08T03:24:40Z
- **Completed:** 2026-02-08T03:28:17Z
- **Tasks:** 2/2
- **Files created:** 2

## Accomplishments

- Created NewcomerDiscoveryPipeline class with 6 methods: discover(), _load_portfolio_tickers(), _gather_candidates(), _score_candidates(), _persist_result(), _to_legacy_format()
- Portfolio exclusion reads all 3 CSV files (stock.csv, etf.csv, crypto.csv) with Yahoo: prefix stripping and crypto -USD dual-form normalization
- All Phase 2 module imports are lazy (inside method bodies) so pipeline module imports cleanly before Phase 2 is built
- Package-level export: `from finwiz.scoring.discovery import NewcomerDiscoveryPipeline`

## Task Commits

Each task was committed atomically:

1. **Task 1: Create NewcomerDiscoveryPipeline** - `7a33fd5` (feat)
2. **Task 2: Update __init__.py with pipeline export** - `cc12bbe` (feat)

## Files Created/Modified

- `src/finwiz/scoring/discovery/pipeline.py` - NewcomerDiscoveryPipeline class (254 lines)
- `src/finwiz/scoring/discovery/__init__.py` - Package exports with NewcomerDiscoveryPipeline

## Decisions Made

- **Lazy imports for Phase 2 modules:** Since Phase 2 (discovery core) has not been executed yet, all Phase 2 component imports (DynamicUniverseProvider, IPOScreener, BreakoutDetector, MomentumScanner, CandidateScorer, NewcomerDiscoveryResult) use lazy imports inside method bodies with ImportError fallback. This allows the pipeline module to be imported and linted now while actual execution waits for Phase 2.
- **Dual crypto ticker forms:** Both "BTC" and "BTC-USD" are added to the portfolio exclusion set when processing crypto.csv, ensuring cross-format matching regardless of how discovery candidates report crypto tickers.
- **Independent screener error handling:** Each of the 4 screeners (universe, IPO, breakout, momentum) has its own try/except block so a failure in one does not prevent others from contributing candidates.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Pipeline structure is ready for Phase 2 modules to be plugged in (lazy imports will resolve once modules exist)
- Plan 03-02 (Perplexity enrichment, feature flag routing, unit tests) can build on this pipeline
- Phase 2 must be completed before the pipeline can produce actual candidates at runtime

---
*Phase: 03-discovery-integration*
*Completed: 2026-02-08*
