# Requirements: FinWiz Hardening & Discovery

**Defined:** 2026-02-07
**Core Value:** Replace mocked discovery with real newcomer detection while eliminating production-risk code quality issues

## v1 Requirements

### Error Handling

- [ ] **ERRH-01**: Replace all bare `except Exception:` handlers with specific exception types (ValueError, KeyError, APIError, etc.) across 44+ locations
- [ ] **ERRH-02**: Add `default=str` parameter to all `json.dumps()` calls missing it across 40+ locations
- [ ] **ERRH-03**: Standardize CrewAI output handling via Pydantic `output_pydantic` schemas instead of inconsistent `str(result.raw)` / `str(result)` patterns

### Performance

- [ ] **PERF-01**: Implement batch API calls in data collection instead of sequential per-holding fetches using `asyncio.gather()` with semaphore
- [ ] **PERF-02**: Replace 14+ blocking `asyncio.sleep()` rate limiters with token bucket algorithm (per-API quotas with burst capacity)
- [ ] **PERF-03**: Wrap all `crew.kickoff()` calls with `asyncio.wait_for()` using `FINWIZ_HOLDING_TIMEOUT`, with circuit breaker for repeatedly failing crews
- [ ] **PERF-04**: Replace blocking cache cleanup (`asyncio.sleep(3600)`) with event-driven LRU eviction and incremental cleanup

### Test Coverage

- [ ] **TEST-01**: Add orchestrator integration tests with real `FinwizState` mutations, concurrent execution, and error propagation
- [ ] **TEST-02**: Add crew output parsing tests covering malformed JSON, schema validation failures, and CrewAI output format variations
- [ ] **TEST-03**: Add data adapter fallback tests covering complete failure scenarios, fallback chain exhaustion, and partial data degradation
- [ ] **TEST-04**: Add HTML output validation tests for generated HTML validity, XSS prevention, and character encoding

### Discovery Pipeline

- [ ] **DISC-01**: Create Pydantic schemas for discovery candidates (`NewcomerCandidate`, `EnrichmentResult`, `NewcomerDiscoveryResult`) in `schemas/newcomer_discovery.py`
- [ ] **DISC-02**: Create `DynamicUniverseProvider` that mines ETF holdings via yfinance with fallback to existing screening_utils universe lists
- [ ] **DISC-03**: Create `IPOScreener` that queries SEC EDGAR EFTS API for recent S-1/S-1A filings and extracts ticker fundamentals
- [ ] **DISC-04**: Create `BreakoutDetector` for price/volume breakout signals on small/mid-cap stocks ($200M-$50B market cap)
- [ ] **DISC-05**: Create `MomentumScanner` for volume anomaly + RSI + momentum signals
- [ ] **DISC-06**: Create `CandidateScorer` reusing existing `ScreeningCriteria` and `score_to_grade()` for scoring and grading
- [ ] **DISC-07**: Create `NewcomerDiscoveryPipeline` orchestrating all discovery components with portfolio exclusion and legacy format output
- [ ] **DISC-08**: Add Perplexity enrichment for top candidates (score >= 0.80), gated by `perplexity_research` feature flag
- [ ] **DISC-09**: Add `newcomer_discovery` feature flag in `config/features/definitions.py` with routing in `scoring/{stock,etf,crypto}_analyzer.py`
- [ ] **DISC-10**: Save newcomer discovery results to `output/discovery/newcomer_{asset_class}.json` via discovery orchestrator
- [ ] **DISC-11**: Create unit tests for all discovery modules (universe provider, IPO screener, breakout detector, momentum scanner, candidate scorer, pipeline, schemas)

## v2 Requirements

### Security Hardening

- **SEC-01**: Implement API key rotation support
- **SEC-02**: Centralize hardcoded API endpoints
- **SEC-03**: Add comprehensive log sanitization for sensitive data
- **SEC-04**: Fail fast at tool instantiation when required API keys are missing

### Structural Refactoring

- **REFAC-01**: Consolidate duplicate portfolio review logic across 10+ files
- **REFAC-02**: Redesign lazy-loaded orchestrators to eliminate circular import risk
- **REFAC-03**: Move schema migration utilities from production code to CLI scripts
- **REFAC-04**: Enforce 300-line file size limit across 150+ violating files

## Out of Scope

| Feature | Reason |
|---------|--------|
| File size limit enforcement | 150+ files affected, massive effort, low immediate payoff |
| Multi-user support | Architectural change requiring database, auth, user context |
| Real-time data / streaming | Future milestone, requires WebSocket architecture |
| i18n framework | TARGETLANG=fr exists but proper gettext is a separate effort |
| Duplicate portfolio review consolidation | 10+ files, big refactor not blocking |
| Lazy-loaded orchestrator redesign | Works today, circular imports are architectural |
| Migration utilities relocation | Low immediate impact |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| ERRH-01 | TBD | Pending |
| ERRH-02 | TBD | Pending |
| ERRH-03 | TBD | Pending |
| PERF-01 | TBD | Pending |
| PERF-02 | TBD | Pending |
| PERF-03 | TBD | Pending |
| PERF-04 | TBD | Pending |
| TEST-01 | TBD | Pending |
| TEST-02 | TBD | Pending |
| TEST-03 | TBD | Pending |
| TEST-04 | TBD | Pending |
| DISC-01 | TBD | Pending |
| DISC-02 | TBD | Pending |
| DISC-03 | TBD | Pending |
| DISC-04 | TBD | Pending |
| DISC-05 | TBD | Pending |
| DISC-06 | TBD | Pending |
| DISC-07 | TBD | Pending |
| DISC-08 | TBD | Pending |
| DISC-09 | TBD | Pending |
| DISC-10 | TBD | Pending |
| DISC-11 | TBD | Pending |

**Coverage:**
- v1 requirements: 22 total
- Mapped to phases: 0
- Unmapped: 22

---
*Requirements defined: 2026-02-07*
*Last updated: 2026-02-07 after initial definition*
