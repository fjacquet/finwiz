# Roadmap: FinWiz

## Milestones

- [x] **v1 Hardening & Discovery** - Phases 1-5 (shipped 2026-02-08)
- [x] **v2 Security & Structural Quality** - Phases 6-8 (shipped 2026-02-08)
- [x] **v3 Performance & Risk Analysis** - Phases 9-11 (shipped 2026-02-08)

## Phases

<details>
<summary>v1 Hardening & Discovery (Phases 1-5) - SHIPPED 2026-02-08</summary>

See: milestones/v1-ROADMAP.md for full phase details.

Phases completed: 1-5 (13 plans total)

</details>

<details>
<summary>v2 Security & Structural Quality (Phases 6-8) - SHIPPED 2026-02-08</summary>

See: milestones/v2-ROADMAP.md for full phase details.

Phases completed: 6-8 (6 plans total)

</details>

### v3 Performance & Risk Analysis

**Milestone Goal:** Make FinWiz significantly faster through async parallelism, batch prefetching, and smart caching -- and add portfolio risk stress testing as a new analytical capability. Cost tracking provides LLM spend visibility.

- [x] **Phase 9: Async & Batch Performance** - Full async data collection with batch prefetching and configurable parallel analysis (shipped 2026-02-08)
- [x] **Phase 10: Cache & Cost Observability** - Smart tiered caching with type-aware TTLs and LLM cost tracking (shipped 2026-02-08)
- [x] **Phase 11: Risk Stress Testing** - Portfolio scenario analysis with market crash, rate shock, and sector shock simulations (shipped 2026-02-08)

## Phase Details

### Phase 9: Async & Batch Performance

**Goal**: All data collection and deep analysis runs fully async with batch prefetching and configurable parallelism
**Depends on**: Phase 8 (v2 complete)
**Requirements**: PERF-01, PERF-02, PERF-03, PERF-04
**Success Criteria** (what must be TRUE):

  1. Running `crewai flow kickoff` uses async data adapters throughout -- no synchronous API calls remain in the data collection path
  2. Deep analysis processes multiple holdings concurrently, and the parallel limit is configurable via environment variable (not hardcoded to 3)
  3. BatchDataPreFetcher loads data for all holdings before deep analysis begins as part of the normal flow (not a standalone demo script)
  4. Data providers that support batch endpoints (e.g., yfinance multi-ticker) use a single batch call instead of N sequential calls per holding
**Plans**: TBD

Plans:

- [x] 09-01: Batch Prefetch Integration (PERF-03, PERF-04)
- [x] 09-02: Async Adapters + Concurrency Tuning (PERF-01, PERF-02)

### Phase 10: Cache & Cost Observability

**Goal**: The platform manages cache intelligently with tiered eviction and type-aware TTLs, and provides full visibility into LLM token costs per crew and overall
**Depends on**: Phase 9 (async data paths established, cache layer exercised by new batch flows)
**Requirements**: CACHE-01, CACHE-02, CACHE-03, COST-01, COST-02
**Success Criteria** (what must be TRUE):

  1. Cache evicts cold entries first, preserving frequently-accessed hot data -- observable via log output showing tier assignments during eviction
  2. Market data entries expire in ~15 minutes, fundamentals in ~24 hours, and static reference data in ~7 days (verified by TTL behavior in logs or tests)
  3. Cache hit/miss rates are visible in log output after each analysis run
  4. After a flow run completes, the output shows actual LLM token costs per crew and a total cost summary using real provider pricing

Plans:

- [x] 10-01: Tiered Cache Eviction & Type-Aware TTLs (CACHE-01, CACHE-02, CACHE-03)
- [x] 10-02: LLM Cost Tracking & Reporting (COST-01, COST-02)

### Phase 11: Risk Stress Testing

**Goal**: Users can stress test their portfolio against realistic market scenarios and see projected impact in the HTML report
**Depends on**: Phase 9 (analysis pipeline stable with async infrastructure)
**Requirements**: RISK-01, RISK-02, RISK-03, RISK-04
**Success Criteria** (what must be TRUE):

  1. User can run a market crash scenario (-20% broad market) and see projected per-holding and total portfolio impact
  2. User can run an interest rate shock scenario and see which holdings are most and least affected
  3. User can run a sector-specific shock scenario and see differential impact across portfolio sectors
  4. The HTML report includes a stress testing section with scenario results presented alongside existing analysis output

Plans:

- [x] 11-01: Stress Test Engine & Scenarios (RISK-01, RISK-02, RISK-03)
- [x] 11-02: Stress Test Integration & HTML Report (RISK-04)

## Progress

**Execution Order:** 9 -> 10 -> 11

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1-5 | v1 | 13/13 | Shipped | 2026-02-08 |
| 6-8 | v2 | 6/6 | Shipped | 2026-02-08 |
| 9. Async & Batch Performance | v3 | 2/2 | Complete | 2026-02-08 |
| 10. Cache & Cost Observability | v3 | 2/2 | Complete | 2026-02-08 |
| 11. Risk Stress Testing | v3 | 2/2 | Complete | 2026-02-08 |

---
*Roadmap created: 2026-02-08*
*Last updated: 2026-02-08*
