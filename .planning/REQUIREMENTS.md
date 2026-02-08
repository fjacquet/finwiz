# Requirements: FinWiz v3

**Defined:** 2026-02-08
**Core Value:** Hybrid financial analysis with real newcomer detection — now faster, cheaper to observe, and with risk scenario analysis.

## v3 Requirements

Requirements for the Performance & Risk Analysis milestone. Each maps to roadmap phases.

### PERF — Parallel Execution

- [ ] **PERF-01**: Data adapters support async execution (DataSourceOrchestrator fully async)
- [ ] **PERF-02**: Deep analysis runs holdings concurrently with configurable parallel limit (default raised from 3)
- [ ] **PERF-03**: BatchDataPreFetcher is integrated into the main analysis flow (not just demo/standalone)
- [ ] **PERF-04**: All data collection paths use batch API calls where the provider supports it

### CACHE — Cache Optimization

- [ ] **CACHE-01**: Cache uses tiered eviction (hot/warm/cold based on access frequency)
- [ ] **CACHE-02**: TTL is data-type-aware (market data: 15min, fundamentals: 24h, static: 7d)
- [ ] **CACHE-03**: Cache hit/miss metrics are logged for observability

### COST — Cost Tracking

- [ ] **COST-01**: LiteLLM callback tracks actual token costs using provider pricing
- [ ] **COST-02**: Per-crew and total costs are reported in analysis output

### RISK — Risk Stress Testing

- [ ] **RISK-01**: User can run market crash scenario (-20% broad market) against portfolio
- [ ] **RISK-02**: User can run interest rate shock scenario against portfolio
- [ ] **RISK-03**: User can run sector-specific shock scenario against portfolio
- [ ] **RISK-04**: Stress test results are included in the HTML report output

## Future Requirements

Deferred to future releases.

### Observability

- **OBS-01**: OpenTelemetry tracing spans for end-to-end profiling
- **OBS-02**: Performance regression tests with pytest-benchmark baselines

### Infrastructure

- **INFRA-01**: HTTP connection pooling / session reuse across API calls
- **INFRA-02**: Persistent result cache across runs (skip re-analysis of unchanged holdings)
- **INFRA-03**: Progressive/streaming results (surface holdings as they complete)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Real-time data streaming | Architectural change, different milestone |
| Multi-user support | Requires auth, sessions, DB — separate effort |
| i18n framework | Not performance-related |
| File size refactoring (300-line splits) | Enforce for new code only, not bulk refactor |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| PERF-01 | — | Pending |
| PERF-02 | — | Pending |
| PERF-03 | — | Pending |
| PERF-04 | — | Pending |
| CACHE-01 | — | Pending |
| CACHE-02 | — | Pending |
| CACHE-03 | — | Pending |
| COST-01 | — | Pending |
| COST-02 | — | Pending |
| RISK-01 | — | Pending |
| RISK-02 | — | Pending |
| RISK-03 | — | Pending |
| RISK-04 | — | Pending |

**Coverage:**
- v3 requirements: 13 total
- Mapped to phases: 0
- Unmapped: 13

---
*Requirements defined: 2026-02-08*
*Last updated: 2026-02-08 after initial definition*
