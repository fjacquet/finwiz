# Requirements Archive: v1 Hardening & Discovery

**Archived:** 2026-02-08
**Status:** SHIPPED

This is the archived requirements specification for v1.
For current requirements, see `.planning/REQUIREMENTS.md` (created for next milestone).

---

## v1 Requirements

### Error Handling

- [x] **ERRH-01**: Replace all bare `except Exception:` handlers with specific exception types (ValueError, KeyError, APIError, etc.) across 44+ locations
- [x] **ERRH-02**: Add `default=str` parameter to all `json.dumps()` calls missing it across 40+ locations
- [x] **ERRH-03**: Standardize CrewAI output handling via Pydantic `output_pydantic` schemas instead of inconsistent `str(result.raw)` / `str(result)` patterns

### Performance

- [x] **PERF-01**: Implement batch API calls in data collection instead of sequential per-holding fetches using `asyncio.gather()` with semaphore
- [x] **PERF-02**: Replace 14+ blocking `asyncio.sleep()` rate limiters with token bucket algorithm (per-API quotas with burst capacity)
- [x] **PERF-03**: Wrap all `crew.kickoff()` calls with `asyncio.wait_for()` using `FINWIZ_HOLDING_TIMEOUT`, with circuit breaker for repeatedly failing crews
- [x] **PERF-04**: Replace blocking cache cleanup (`asyncio.sleep(3600)`) with event-driven LRU eviction and incremental cleanup

### Test Coverage

- [x] **TEST-01**: Add orchestrator integration tests with real `FinwizState` mutations, concurrent execution, and error propagation
- [x] **TEST-02**: Add crew output parsing tests covering malformed JSON, schema validation failures, and CrewAI output format variations
- [x] **TEST-03**: Add data adapter fallback tests covering complete failure scenarios, fallback chain exhaustion, and partial data degradation
- [x] **TEST-04**: Add HTML output validation tests for generated HTML validity, XSS prevention, and character encoding

### Discovery Pipeline

- [x] **DISC-01**: Create Pydantic schemas for discovery candidates (`NewcomerCandidate`, `EnrichmentResult`, `NewcomerDiscoveryResult`) in `schemas/newcomer_discovery.py`
- [x] **DISC-02**: Create `DynamicUniverseProvider` that mines ETF holdings via yfinance with fallback to existing screening_utils universe lists
- [x] **DISC-03**: Create `IPOScreener` that queries SEC EDGAR EFTS API for recent S-1/S-1A filings and extracts ticker fundamentals
- [x] **DISC-04**: Create `BreakoutDetector` for price/volume breakout signals on small/mid-cap stocks ($200M-$50B market cap)
- [x] **DISC-05**: Create `MomentumScanner` for volume anomaly + RSI + momentum signals
- [x] **DISC-06**: Create `CandidateScorer` reusing existing `ScreeningCriteria` and `score_to_grade()` for scoring and grading
- [x] **DISC-07**: Create `NewcomerDiscoveryPipeline` orchestrating all discovery components with portfolio exclusion and legacy format output
- [x] **DISC-08**: Add Perplexity enrichment for top candidates (score >= 0.80), gated by `perplexity_research` feature flag
- [x] **DISC-09**: Add `newcomer_discovery` feature flag in `config/features/definitions.py` with routing in `scoring/{stock,etf,crypto}_analyzer.py`
- [x] **DISC-10**: Save newcomer discovery results to `output/discovery/newcomer_{asset_class}.json` via discovery orchestrator
- [x] **DISC-11**: Create unit tests for all discovery modules (universe provider, IPO screener, breakout detector, momentum scanner, candidate scorer, pipeline, schemas)

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| ERRH-01 | 1 | Complete |
| ERRH-02 | 1 | Complete |
| ERRH-03 | 1 | Complete |
| PERF-01 | 4 | Complete |
| PERF-02 | 4 | Complete |
| PERF-03 | 4 | Complete |
| PERF-04 | 4 | Complete |
| TEST-01 | 5 | Complete |
| TEST-02 | 5 | Complete |
| TEST-03 | 5 | Complete |
| TEST-04 | 5 | Complete |
| DISC-01 | 2 | Complete |
| DISC-02 | 2 | Complete |
| DISC-03 | 2 | Complete |
| DISC-04 | 2 | Complete |
| DISC-05 | 2 | Complete |
| DISC-06 | 2 | Complete |
| DISC-07 | 3 | Complete |
| DISC-08 | 3 | Complete |
| DISC-09 | 3 | Complete |
| DISC-10 | 3 | Complete |
| DISC-11 | 3 | Complete |

## Milestone Summary

**Shipped:** 22 of 22 v1 requirements
**Adjusted:** None -- all requirements implemented as specified
**Dropped:** None

---
*Archived: 2026-02-08 as part of v1 milestone completion*
