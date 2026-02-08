# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-07)

**Core value:** Replace mocked discovery with real newcomer detection while eliminating production-risk code quality issues
**Current focus:** Phases 1, 2, 3 complete -- next: Phase 4 (Performance) or Phase 5 (Test Coverage)

## Current Position

Phase: 3 of 5 complete (Discovery Integration)
Plan: All plans complete for Phases 1, 2, 3
Status: Phases 1, 2, 3 done. Phases 4, 5 remaining.
Last activity: 2026-02-08 -- Completed Phase 2 (02-02-PLAN.md: screeners, detectors, and scorer)

Progress: [████████░░] ~80%

## Performance Metrics

**Velocity:**

- Total plans completed: 8
- Average duration: ~4.6 min
- Total execution time: ~37 min

**By Phase:**

| Phase | Plans | Completed | Avg/Plan |
|-------|-------|-----------|----------|
| 1 - Error Handling | 4 | 4 | ~6 min |
| 2 - Discovery Core | 2 | 2 | ~4 min |
| 3 - Discovery Integration | 2 | 2 | ~4.5 min |

**Recent Trend:**

- Last 5 plans: 03-01 (~3 min), 03-02 (~6 min), 02-01 (~3 min), 02-02 (~5 min)
- Trend: Stable ~4 min/plan

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Roadmap: 5-phase structure (error handling -> discovery core -> discovery integration -> performance -> tests)
- Roadmap: ERRH cleanup first so new discovery code builds on clean patterns
- Roadmap: Discovery split into core (schemas+modules) and integration (pipeline+flags+tests) phases
- 01-01: Exception types chosen by matching operations inside try blocks (decision matrix)
- 01-01: Import fallbacks use ImportError instead of generic Exception
- 01-04: Wrap raw fallback in {"raw_output": ...} dict to ensure dict type consistency with state fields
- 01-04: Use isinstance check on fallback_response.data for defensive type handling
- 01-02: Exception types chosen by matching operations inside try blocks (decision matrix pattern)
- 01-03: All json.dumps calls use default=str (verified via AST scan)
- 03-01: Lazy imports for Phase 2 modules so pipeline can be imported before Phase 2 is built
- 03-01: Portfolio exclusion loads ALL 3 CSVs regardless of current asset_class
- 03-01: Crypto tickers stored in both BTC and BTC-USD forms for cross-format matching
- 03-02: Schema with extra='forbid' for strict validation matching project Pydantic standards
- 03-02: Enrichment uses asyncio.run() with running-loop detection for sync/async boundary
- 03-02: _gather_candidates refactored to data-driven screener list with importlib for compactness
- 03-02: Contract tests mock sys.modules since Phase 2 modules do not exist yet
- 02-01: Literal over Enum on newcomer schemas (simpler, matches existing pattern)
- 02-01: Crypto universe goes straight to static fallback (no yfinance ETF holdings)
- 02-01: Per-ETF error isolation (individual failures skip, not abort)
- 02-02: IPO screener uses SEC EDGAR EFTS search-index API with 0.15s delay
- 02-02: Breakout detector filters to $200M-$50B market cap, requires composite >= 0.3
- 02-02: Momentum scanner uses TA-Lib RSI + ROC (40% RSI, 30% volume, 30% momentum)
- 02-02: CandidateScorer blends source score (40%) with screening infrastructure score (60%)

### Pending Todos

None yet.

### Blockers/Concerns

- 56 pre-existing UP042 lint warnings (str+Enum inheritance) across codebase -- not blocking, but will need cleanup eventually
- 2 pre-existing test failures in test_notification_service.py -- not related to current changes

## Session Continuity

Last session: 2026-02-08
Stopped at: Completed Phase 2 (Discovery Core)
Resume file: None
