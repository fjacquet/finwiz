---
phase: 03-discovery-integration
plan: 02
subsystem: scoring
tags: [discovery, feature-flags, perplexity, enrichment, pipeline, unit-tests, schemas]

# Dependency graph
requires:
  - phase: 03-01
    provides: "NewcomerDiscoveryPipeline class with portfolio exclusion and lazy Phase 2 imports"
  - phase: 02-discovery-core
    provides: "Phase 2 discovery modules (universe provider, screeners, scorer) -- imported lazily"
provides:
  - "newcomer_discovery feature flag (FF_NEWCOMER_DISCOVERY) in definitions.py"
  - "Feature-flag routing in stock_analyzer, etf_analyzer, crypto_analyzer"
  - "Perplexity enrichment for top candidates (score >= 0.80) in pipeline"
  - "NewcomerCandidate, EnrichmentResult, NewcomerDiscoveryResult schemas"
  - "51 unit tests across 7 test files covering all discovery modules"
affects:
  - "02-discovery-core (Phase 2 modules define the API that tests mock)"
  - "04-performance (pipeline needs perf tuning once Phase 2 modules exist)"
  - "05-tests (additional test coverage for integration scenarios)"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Feature flag routing: check is_feature_enabled() then try/except pipeline with legacy fallback"
    - "Perplexity enrichment as optional pipeline step with graceful degradation"
    - "Phase 2 contract tests: mock sys.modules to test pipeline interaction with non-existent modules"

key-files:
  created:
    - "src/finwiz/schemas/newcomer_discovery.py"
    - "tests/unit/scoring/discovery/__init__.py"
    - "tests/unit/scoring/discovery/test_pipeline.py"
    - "tests/unit/scoring/discovery/test_universe_provider.py"
    - "tests/unit/scoring/discovery/test_ipo_screener.py"
    - "tests/unit/scoring/discovery/test_breakout_detector.py"
    - "tests/unit/scoring/discovery/test_momentum_scanner.py"
    - "tests/unit/scoring/discovery/test_candidate_scorer.py"
    - "tests/unit/schemas/test_newcomer_discovery.py"
  modified:
    - "src/finwiz/config/features/definitions.py"
    - "src/finwiz/scoring/discovery/pipeline.py"
    - "src/finwiz/scoring/stock_analyzer.py"
    - "src/finwiz/scoring/etf_analyzer.py"
    - "src/finwiz/scoring/crypto_analyzer.py"

key-decisions:
  - "Schema created with extra='forbid' for strict validation matching project Pydantic standards"
  - "Enrichment uses asyncio.run() with running-loop detection to handle sync/async boundary"
  - "Pipeline _gather_candidates refactored to data-driven screener list with importlib for compactness"
  - "Contract tests mock sys.modules since Phase 2 modules do not exist yet"

patterns-established:
  - "Feature flag routing pattern: is_feature_enabled() -> try pipeline -> except fall through to legacy"
  - "Perplexity enrichment pattern: initialize_perplexity_integration -> is_perplexity_enabled -> search_financial_news"
  - "Contract testing pattern: mock Phase 2 module interfaces via sys.modules patching"

# Metrics
duration: 6min
completed: 2026-02-08
---

# Phase 3 Plan 02: Discovery Integration Summary

**Feature-flag routing in all 3 analyzers, Perplexity enrichment for top candidates, NewcomerDiscovery schemas, and 51 unit tests covering pipeline, screeners, scorer, and schema validation**

## Performance

- **Duration:** 6 min
- **Started:** 2026-02-08T03:32:43Z
- **Completed:** 2026-02-08T03:39:00Z
- **Tasks:** 3/3
- **Files created:** 10
- **Files modified:** 5

## Accomplishments

- Registered `newcomer_discovery` feature flag (FF_NEWCOMER_DISCOVERY, default False) with DEFAULT_VALUES fallback strategy
- All 3 analyzers (stock, etf, crypto) check the flag and route through NewcomerDiscoveryPipeline when enabled, falling back to legacy mocked data when disabled or on failure
- Added `_enrich_top_candidates()` to pipeline: enriches candidates with score >= 0.80 (max 10) via Perplexity when `perplexity_research` flag is enabled, with full graceful degradation
- Created `schemas/newcomer_discovery.py` with `NewcomerCandidate`, `EnrichmentResult`, and `NewcomerDiscoveryResult` Pydantic models
- Created 51 unit tests across 7 test files with zero unittest.mock usage

## Task Commits

Each task was committed atomically:

1. **Task 1: Register feature flag and add Perplexity enrichment** - `60fbefd` (feat)
2. **Task 2: Wire feature flag routing in all three analyzers** - `cd457ae` (feat)
3. **Task 3: Create unit tests for all discovery modules** - `cb36082` (test)

## Files Created/Modified

- `src/finwiz/schemas/newcomer_discovery.py` - NewcomerCandidate, EnrichmentResult, NewcomerDiscoveryResult schemas (69 lines)
- `src/finwiz/config/features/definitions.py` - Added newcomer_discovery flag with FF_NEWCOMER_DISCOVERY env var
- `src/finwiz/scoring/discovery/pipeline.py` - Added _enrich_top_candidates() with Perplexity integration (278 lines)
- `src/finwiz/scoring/stock_analyzer.py` - Feature flag routing to pipeline or legacy (102 lines)
- `src/finwiz/scoring/etf_analyzer.py` - Feature flag routing to pipeline or legacy (102 lines)
- `src/finwiz/scoring/crypto_analyzer.py` - Feature flag routing to pipeline or legacy (94 lines)
- `tests/unit/scoring/discovery/test_pipeline.py` - 13 pipeline tests (245 lines)
- `tests/unit/scoring/discovery/test_universe_provider.py` - 4 universe provider contract tests
- `tests/unit/scoring/discovery/test_ipo_screener.py` - 4 IPO screener contract tests
- `tests/unit/scoring/discovery/test_breakout_detector.py` - 4 breakout detector contract tests
- `tests/unit/scoring/discovery/test_momentum_scanner.py` - 4 momentum scanner contract tests
- `tests/unit/scoring/discovery/test_candidate_scorer.py` - 5 candidate scorer contract tests
- `tests/unit/schemas/test_newcomer_discovery.py` - 17 schema validation tests

## Decisions Made

- **Schema with extra='forbid':** All discovery Pydantic models use strict validation (extra="forbid") consistent with project-wide Pydantic standards in schemas/ directory
- **Enrichment async bridge:** Used `asyncio.run()` with `get_running_loop()` detection to handle the sync pipeline calling async Perplexity API, with a fallback skip when an event loop is already running
- **Data-driven screener list:** Refactored `_gather_candidates()` from 4 repeated try/except blocks to a data-driven list of `(module, class, method)` tuples with `importlib.import_module()` for compactness and maintainability
- **Contract tests via sys.modules:** Since Phase 2 modules don't exist yet, tests mock their interfaces via `sys.modules` patching to verify the pipeline's expected API contract

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Created schemas/newcomer_discovery.py**
- **Found during:** Task 1 (before starting feature flag work)
- **Issue:** Pipeline imports `NewcomerCandidate` and `NewcomerDiscoveryResult` from `finwiz.schemas.newcomer_discovery`, but this file did not exist
- **Fix:** Created the schema file with all 3 Pydantic models (NewcomerCandidate, EnrichmentResult, NewcomerDiscoveryResult)
- **Files modified:** src/finwiz/schemas/newcomer_discovery.py
- **Verification:** `uv run python -c "from finwiz.schemas.newcomer_discovery import NewcomerCandidate"` succeeds
- **Committed in:** 60fbefd (Task 1 commit)

**2. [Rule 1 - Bug] Refactored _gather_candidates to data-driven pattern**
- **Found during:** Task 1 (pipeline was 359 lines, exceeding 300-line limit)
- **Issue:** Adding enrichment pushed pipeline over the 300-line file size limit
- **Fix:** Refactored 4 repeated try/except blocks into a data-driven screener list, reducing file from 359 to 278 lines
- **Files modified:** src/finwiz/scoring/discovery/pipeline.py
- **Committed in:** 60fbefd (Task 1 commit)

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 file-size compliance)
**Impact on plan:** Both fixes necessary for correctness and project rules compliance. No scope creep.

## Issues Encountered

- Three test failures on initial run due to patching lazy imports at wrong module path. Fixed by patching at `finwiz.tools.perplexity_feature_utils` (source module) instead of `finwiz.scoring.discovery.pipeline` (consumer module) for enrichment utils, and patching `importlib.import_module` directly for screener mocking.

## User Setup Required

None - no external service configuration required. The `newcomer_discovery` flag defaults to False (disabled).

## Next Phase Readiness

- Phase 3 (Discovery Integration) is now complete: pipeline built (03-01) and wired with flags, enrichment, and tests (03-02)
- Phase 2 (Discovery Core) modules still need to be built for the pipeline to produce real candidates at runtime
- Setting `FF_NEWCOMER_DISCOVERY=true` will activate the pipeline path; until Phase 2 modules exist, it will fall back to legacy data via ImportError handling
- All 51 tests pass, providing regression safety for future Phase 2 and Phase 4 work

---
*Phase: 03-discovery-integration*
*Completed: 2026-02-08*
