# Roadmap: FinWiz Hardening & Discovery

## Overview

This milestone hardens the FinWiz codebase (error handling, performance, test coverage) while building a real investment discovery pipeline to replace mocked data. The journey starts with error handling cleanup to establish clean patterns, builds discovery components bottom-up (schemas and modules, then integration), optimizes performance bottlenecks, and fills critical test gaps. Every v1 requirement maps to exactly one of 5 phases.

## Phases

**Phase Numbering:**

- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Error Handling Cleanup** - Replace bare exceptions, fix json.dumps, standardize crew output handling
- [x] **Phase 2: Discovery Core** - Pydantic schemas and individual discovery modules (universe, screeners, scorer)
- [x] **Phase 3: Discovery Integration** - Pipeline orchestrator, enrichment, feature flags, output, and unit tests
- [x] **Phase 4: Performance** - Batch API calls, token bucket rate limiting, crew timeouts, cache cleanup
- [ ] **Phase 5: Test Coverage** - Orchestrator, crew output, fallback, and HTML validation tests

## Phase Details

### Phase 1: Error Handling Cleanup

**Goal**: All error handling follows project standards so new code builds on clean patterns
**Depends on**: Nothing (first phase)
**Requirements**: ERRH-01, ERRH-02, ERRH-03
**Success Criteria** (what must be TRUE):

  1. No bare `except Exception:` handlers remain -- every catch uses specific exception types (ValueError, KeyError, APIError, etc.) with proper error context logging
  2. All `json.dumps()` calls use `default=str`, preventing TypeError on datetime/Decimal serialization
  3. All crew tasks that produce structured data use `output_pydantic` schemas, and crew results are accessed via Pydantic model fields instead of `str(result)` or `str(result.raw)` patterns
**Plans**: 4 plans

Plans:

- [x] 01-01-PLAN.md -- Replace ~22 bare except Exception: handlers in tools/ files (ERRH-01)
- [x] 01-02-PLAN.md -- Replace ~21 bare except Exception: handlers in non-tools/ files (ERRH-01)
- [x] 01-03-PLAN.md -- Add default=str to ~37 json.dumps calls across 18 files (ERRH-02)
- [x] 01-04-PLAN.md -- Standardize 5 CrewAI output patterns via result.pydantic cascade + fix flow state types (ERRH-03)

### Phase 2: Discovery Core

**Goal**: All discovery components exist and can independently find and score newcomer candidates
**Depends on**: Phase 1
**Requirements**: DISC-01, DISC-02, DISC-03, DISC-04, DISC-05, DISC-06
**Success Criteria** (what must be TRUE):

  1. Pydantic schemas (NewcomerCandidate, EnrichmentResult, NewcomerDiscoveryResult) validate and serialize correctly in `schemas/newcomer_discovery.py`
  2. DynamicUniverseProvider returns candidate tickers from ETF holdings via yfinance, with fallback to static screening_utils lists when yfinance fails
  3. IPOScreener, BreakoutDetector, and MomentumScanner each return scored candidates from their respective data sources (SEC EDGAR, price/volume data, RSI/momentum)
  4. CandidateScorer assigns grades (A+ to F) to candidates using existing ScreeningCriteria and score_to_grade() functions
**Plans**: 2 plans

Plans:

- [x] 02-01-PLAN.md -- Discovery schemas and universe provider (DISC-01, DISC-02)
- [x] 02-02-PLAN.md -- Screeners, detectors, and scorer (DISC-03, DISC-04, DISC-05, DISC-06)

### Phase 3: Discovery Integration

**Goal**: Discovery pipeline runs end-to-end within the existing flow, gated by feature flag, with full test coverage
**Depends on**: Phase 2
**Requirements**: DISC-07, DISC-08, DISC-09, DISC-10, DISC-11
**Success Criteria** (what must be TRUE):

  1. NewcomerDiscoveryPipeline orchestrates all discovery components and excludes tickers already in the user's portfolio
  2. Top candidates (score >= 0.80) receive Perplexity enrichment when `perplexity_research` feature flag is enabled; others skip enrichment gracefully
  3. Setting `FF_NEWCOMER_DISCOVERY=true` routes stock/etf/crypto analyzers through the new pipeline; `false` falls back to legacy mocked data with no behavior change
  4. Discovery results are persisted to `output/discovery/newcomer_{asset_class}.json` with valid NewcomerDiscoveryResult schema
  5. All discovery modules have passing unit tests covering happy path and error scenarios
**Plans**: 2 plans

Plans:

- [x] 03-01-PLAN.md -- Pipeline orchestrator with portfolio exclusion and output persistence (DISC-07, DISC-10)
- [x] 03-02-PLAN.md -- Perplexity enrichment, feature flag routing, and unit tests (DISC-08, DISC-09, DISC-11)

### Phase 4: Performance

**Goal**: Portfolio analysis runs faster without sequential bottlenecks or hanging crews
**Depends on**: Phase 1
**Requirements**: PERF-01, PERF-02, PERF-03, PERF-04
**Success Criteria** (what must be TRUE):

  1. Data collection fetches multiple holdings concurrently using asyncio.gather() with semaphore-based concurrency control
  2. Rate limiting uses token bucket algorithm with per-API quotas and burst capacity, replacing all blocking asyncio.sleep() calls
  3. Every crew.kickoff() call is wrapped with asyncio.wait_for() using FINWIZ_HOLDING_TIMEOUT, and repeatedly failing crews trigger a circuit breaker
  4. Cache cleanup uses event-driven LRU eviction with incremental cleanup instead of blocking synchronous sleep
**Plans**: 3 plans

Plans:

- [x] 04-01-PLAN.md -- Token bucket rate limiter (aiolimiter) + replace blocking sleeps in data collection (PERF-01, PERF-02)
- [x] 04-02-PLAN.md -- Crew execution timeouts with asyncio.wait_for() and circuit breaker (PERF-03)
- [x] 04-03-PLAN.md -- Event-driven cache cleanup replacing blocking asyncio.sleep(3600) loop (PERF-04)

### Phase 5: Test Coverage

**Goal**: Critical test gaps are filled, building confidence in the hardened and newly built code
**Depends on**: Phases 1, 3
**Requirements**: TEST-01, TEST-02, TEST-03, TEST-04
**Success Criteria** (what must be TRUE):

  1. Orchestrator integration tests verify real FinwizState mutations, concurrent execution paths, and error propagation across orchestrator boundaries
  2. Crew output parsing tests cover malformed JSON, Pydantic schema validation failures, and CrewAI output format variations (raw, pydantic, json_dict)
  3. Data adapter fallback tests cover complete adapter failure, fallback chain exhaustion, and partial data degradation scenarios
  4. HTML output validation tests confirm generated HTML is well-formed, free of XSS vectors, and uses correct character encoding
**Plans**: 2 plans

Plans:

- [ ] 05-01-PLAN.md -- Orchestrator integration tests with real FinwizState mutations + crew output parsing tests (TEST-01, TEST-02)
- [ ] 05-02-PLAN.md -- Data adapter fallback scenarios + HTML output validation tests (TEST-03, TEST-04)

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5

Note: Phases 4 and 5 depend on Phase 1 but not on each other. However, running Phase 5 last ensures tests validate all prior work.

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Error Handling Cleanup | 4/4 | Complete | 2026-02-07 |
| 2. Discovery Core | 2/2 | Complete | 2026-02-08 |
| 3. Discovery Integration | 2/2 | Complete | 2026-02-08 |
| 4. Performance | 3/3 | Complete | 2026-02-08 |
| 5. Test Coverage | 0/2 | Not started | - |
