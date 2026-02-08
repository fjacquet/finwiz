# Milestone v1: FinWiz Hardening & Discovery

**Status:** SHIPPED 2026-02-08
**Phases:** 1-5
**Total Plans:** 13

## Overview

This milestone hardens the FinWiz codebase (error handling, performance, test coverage) while building a real investment discovery pipeline to replace mocked data. The journey starts with error handling cleanup to establish clean patterns, builds discovery components bottom-up (schemas and modules, then integration), optimizes performance bottlenecks, and fills critical test gaps. Every v1 requirement maps to exactly one of 5 phases.

## Phases

### Phase 1: Error Handling Cleanup

**Goal**: All error handling follows project standards so new code builds on clean patterns
**Depends on**: Nothing (first phase)
**Requirements**: ERRH-01, ERRH-02, ERRH-03
**Success Criteria**:

  1. No bare `except Exception:` handlers remain
  2. All `json.dumps()` calls use `default=str`
  3. All crew tasks use `output_pydantic` schemas with Pydantic access cascade

**Plans**: 4 plans

- [x] 01-01-PLAN.md -- Replace ~22 bare except Exception: handlers in tools/ files (ERRH-01)
- [x] 01-02-PLAN.md -- Replace ~21 bare except Exception: handlers in non-tools/ files (ERRH-01)
- [x] 01-03-PLAN.md -- Add default=str to ~37 json.dumps calls across 18 files (ERRH-02)
- [x] 01-04-PLAN.md -- Standardize 5 CrewAI output patterns via result.pydantic cascade + fix flow state types (ERRH-03)

### Phase 2: Discovery Core

**Goal**: All discovery components exist and can independently find and score newcomer candidates
**Depends on**: Phase 1
**Requirements**: DISC-01, DISC-02, DISC-03, DISC-04, DISC-05, DISC-06
**Success Criteria**:

  1. Pydantic schemas validate and serialize correctly
  2. DynamicUniverseProvider returns tickers from ETF holdings with fallback
  3. IPOScreener, BreakoutDetector, MomentumScanner each return scored candidates
  4. CandidateScorer assigns grades using existing scoring infrastructure

**Plans**: 2 plans

- [x] 02-01-PLAN.md -- Discovery schemas and universe provider (DISC-01, DISC-02)
- [x] 02-02-PLAN.md -- Screeners, detectors, and scorer (DISC-03, DISC-04, DISC-05, DISC-06)

### Phase 3: Discovery Integration

**Goal**: Discovery pipeline runs end-to-end within the existing flow, gated by feature flag, with full test coverage
**Depends on**: Phase 2
**Requirements**: DISC-07, DISC-08, DISC-09, DISC-10, DISC-11
**Success Criteria**:

  1. Pipeline orchestrates all components with portfolio exclusion
  2. Top candidates (score >= 0.80) receive Perplexity enrichment
  3. Feature flag routes analyzers through new pipeline or legacy fallback
  4. Results persisted to output/discovery/newcomer_{asset_class}.json
  5. All discovery modules have passing unit tests

**Plans**: 2 plans

- [x] 03-01-PLAN.md -- Pipeline orchestrator with portfolio exclusion and output persistence (DISC-07, DISC-10)
- [x] 03-02-PLAN.md -- Perplexity enrichment, feature flag routing, and unit tests (DISC-08, DISC-09, DISC-11)

### Phase 4: Performance

**Goal**: Portfolio analysis runs faster without sequential bottlenecks or hanging crews
**Depends on**: Phase 1
**Requirements**: PERF-01, PERF-02, PERF-03, PERF-04
**Success Criteria**:

  1. Concurrent data collection with asyncio.gather() + semaphore
  2. Token bucket rate limiting with per-API quotas
  3. All crew.kickoff() wrapped with asyncio.wait_for() + circuit breaker
  4. Event-driven cache cleanup replacing blocking sleep

**Plans**: 3 plans

- [x] 04-01-PLAN.md -- Token bucket rate limiter (aiolimiter) + replace blocking sleeps (PERF-01, PERF-02)
- [x] 04-02-PLAN.md -- Crew execution timeouts with asyncio.wait_for() and circuit breaker (PERF-03)
- [x] 04-03-PLAN.md -- Event-driven cache cleanup replacing blocking asyncio.sleep(3600) loop (PERF-04)

### Phase 5: Test Coverage

**Goal**: Critical test gaps are filled, building confidence in the hardened and newly built code
**Depends on**: Phases 1, 3
**Requirements**: TEST-01, TEST-02, TEST-03, TEST-04
**Success Criteria**:

  1. Orchestrator integration tests with real FinwizState mutations
  2. Crew output parsing tests covering all output format variations
  3. Data adapter fallback tests covering failure and degradation scenarios
  4. HTML output validation with XSS prevention and encoding checks

**Plans**: 2 plans

- [x] 05-01-PLAN.md -- Orchestrator integration tests + crew output parsing tests (TEST-01, TEST-02)
- [x] 05-02-PLAN.md -- Data adapter fallback scenarios + HTML output validation tests (TEST-03, TEST-04)

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Error Handling Cleanup | 4/4 | Complete | 2026-02-07 |
| 2. Discovery Core | 2/2 | Complete | 2026-02-08 |
| 3. Discovery Integration | 2/2 | Complete | 2026-02-08 |
| 4. Performance | 3/3 | Complete | 2026-02-08 |
| 5. Test Coverage | 2/2 | Complete | 2026-02-08 |

## Milestone Summary

**Key Decisions:**

- Exception types chosen by matching operations inside try blocks (decision matrix)
- Import fallbacks use ImportError instead of generic Exception
- Wrap raw fallback in {"raw_output": ...} dict for type consistency
- Literal over Enum for newcomer schemas (simpler, matches existing pattern)
- Crypto universe goes straight to static fallback (no yfinance ETF holdings)
- Per-ETF error isolation (individual failures skip, not abort)
- IPO screener uses SEC EDGAR EFTS search-index API with 0.15s delay
- Breakout detector filters to $200M-$50B market cap
- Momentum scanner uses TA-Lib RSI + ROC (40% RSI, 30% volume, 30% momentum)
- CandidateScorer blends source score (40%) with screening infrastructure score (60%)
- Extracted rate_limiter_config.py to keep files under 300 lines
- crew.kickoff() is sync -- must use run_in_executor() to avoid event loop blocking
- FINWIZ_HOLDING_TIMEOUT env var controls timeout (default 300s)
- Kept CacheConfig.auto_cleanup field for API compatibility
- Incremental cleanup every 100 insertions, batch size 10

**Issues Resolved:**

- 50+ bare except Exception: handlers replaced with specific types
- 37+ json.dumps calls missing default=str fixed
- 5 str(result.raw) patterns replaced with Pydantic cascade
- 56 UP042 lint warnings (str+Enum to StrEnum) migrated
- 8 bare exceptions reintroduced in discovery code fixed
- CandidateScorer market_cap metadata fallback added

**Issues Deferred (v2):**

- 150+ files exceed 300-line limit (REFAC-04)
- Duplicate portfolio review consolidation (REFAC-01)
- Lazy-loaded orchestrator redesign (REFAC-02)
- Security hardening: API key rotation, endpoint centralization (SEC-01 through SEC-04)

**Technical Debt:**

- Phase 1 missing VERIFICATION.md (executed before verifier workflow was added)

---
*Archived: 2026-02-08 as part of v1 milestone completion*
*For current project status, see .planning/ROADMAP.md*
