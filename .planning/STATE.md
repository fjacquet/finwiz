# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-07)

**Core value:** Replace mocked discovery with real newcomer detection while eliminating production-risk code quality issues
**Current focus:** Phase 2 plan 1 complete -- next: 02-02 (screeners and scorer)

## Current Position

Phase: 2 of 5 (Discovery Core)
Plan: 1 of 2 in current phase
Status: In progress. Phases 1 and 3 done. Phase 2 plan 1 done, plan 2 pending.
Last activity: 2026-02-08 -- Completed 02-01-PLAN.md (discovery schemas and universe provider)

Progress: [███████░░░] ~70%

## Performance Metrics

**Velocity:**

- Total plans completed: 7
- Average duration: ~4.8 min
- Total execution time: ~34 min

**By Phase:**

| Phase | Plans | Completed | Avg/Plan |
|-------|-------|-----------|----------|
| 1 - Error Handling | 4 | 4 | ~6 min |
| 2 - Discovery Core | 2 | 1 | ~3 min |
| 3 - Discovery Integration | 2 | 2 | ~4.5 min |

**Recent Trend:**

- Last 5 plans: 01-03 (~5 min), 03-01 (~3 min), 03-02 (~6 min), 02-01 (~3 min)
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

### Pending Todos

None yet.

### Blockers/Concerns

- 56 pre-existing UP042 lint warnings (str+Enum inheritance) across codebase -- not blocking, but will need cleanup eventually
- 2 pre-existing test failures in test_notification_service.py -- not related to current changes
- Phase 2 plan 2 (screeners + scorer) still needed before FF_NEWCOMER_DISCOVERY=true works end-to-end

## Session Continuity

Last session: 2026-02-08
Stopped at: Completed 02-01-PLAN.md
Resume file: None
