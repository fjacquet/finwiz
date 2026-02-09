# Roadmap: FinWiz

## Milestones

- [x] **v1 Hardening & Discovery** - Phases 1-5 (shipped 2026-02-08)
- [x] **v2 Security & Structural Quality** - Phases 6-8 (shipped 2026-02-08)
- [x] **v3 Performance & Risk Analysis** - Phases 9-12 (shipped 2026-02-08)
- [ ] **v4 Data Intelligence & Smart Scoring** - Phases 13-16 (in progress)

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

<details>
<summary>v3 Performance & Risk Analysis (Phases 9-12) - SHIPPED 2026-02-08</summary>

See: milestones/v3-ROADMAP.md for full phase details.

Phases completed: 9-12 (7 plans total)

- Phase 9: Async & Batch Performance (2 plans)
- Phase 10: Cache & Cost Observability (2 plans)
- Phase 11: Risk Stress Testing (2 plans)
- Phase 12: Wire Stress Test Report (1 plan, gap closure)

</details>

### v4 Data Intelligence & Smart Scoring (In Progress)

**Milestone Goal:** Enrich the analysis pipeline with news sentiment, macroeconomic indicators, and additional data providers so that composite scores factor in market context -- not just technicals and fundamentals.

**Phase Numbering:**
- Integer phases (13, 14, 15, 16): Planned milestone work
- Decimal phases (13.1, 13.2): Urgent insertions if needed (marked with INSERTED)

- [x] **Phase 13: Data Foundation** - Adapters, schemas, feature flags, and infrastructure for news and macro data
- [x] **Phase 14: Sentiment Scoring** - Per-holding sentiment computation and composite score integration
- [x] **Phase 15: Macro Context** - Real macro data replaces hardcoded values, dynamic risk adjustment
- [ ] **Phase 16: Report Enrichment** - New HTML sections for sentiment, macro dashboard, and economic calendar

## Phase Details

### Phase 13: Data Foundation
**Goal**: Data adapters and schemas exist to collect news, sentiment, macro, and Fear & Greed data from external APIs
**Depends on**: Nothing (builds on existing adapter patterns from v1-v3)
**Requirements**: DATA-01, DATA-02, DATA-03, DATA-04, DATA-05, DATA-06, DATA-07, DATA-08, DATA-09, DISC-01
**Success Criteria** (what must be TRUE):
  1. Running the analysis with FF_NEWS_SENTIMENT=true fetches real company news articles for each holding from Finnhub
  2. Running the analysis with FF_MACRO_INDICATORS=true fetches real macro indicators (Fed rate, CPI, VIX, yields) from FRED
  3. Duplicate news articles from multiple sources are deduplicated before processing
  4. Discovery pipeline returns real screened candidates instead of hardcoded mock data
  5. Disabling feature flags (default) results in no new API calls and existing behavior is unchanged
**Plans**: 10/10 complete

Plans:
- [x] 13-01: Pydantic schemas (sentiment.py, macro.py)
- [x] 13-02: Endpoints & APIProvider
- [x] 13-03: Feature flags (5 new flags)
- [x] 13-04: News utilities (dedup, reliability, weighted sentiment)
- [x] 13-05: Finnhub news adapter (waterfall fallback)
- [x] 13-06: FRED macro adapter (session-cached)
- [x] 13-07: Fear & Greed adapter (library + HTTP fallback)
- [x] 13-08: Dependencies (6 new packages)
- [x] 13-09: Discovery pipeline fix (newcomer_discovery → True)
- [x] 13-10: Integration wiring (SentimentMacroCollector + pipeline)

### Phase 14: Sentiment Scoring
**Goal**: Each holding receives a sentiment score derived from news headlines, integrated into the composite score as an additive overlay
**Depends on**: Phase 13 (requires news data adapters and sentiment schemas)
**Requirements**: SENT-01, SENT-02, SENT-03, SENT-04, SENT-05, SCORE-01, SCORE-02
**Success Criteria** (what must be TRUE):
  1. Each holding shows a sentiment score (positive/negative/neutral) computed from aggregated news headlines with source-reliability weighting
  2. Sentiment confidence reflects article count, source diversity, and recency -- holdings with few or stale articles show low confidence
  3. Holdings with no news coverage show sentiment as "unavailable" (None), not neutral (0.0)
  4. Composite score includes sentiment as an additive adjustment that defaults to zero impact (weight=0.0, feature-flagged off)
  5. Enabling sentiment scoring with a non-zero weight does not change the existing 40/30/30 fundamental/technical/risk weight distribution
**Plans**: 2/2 complete

Plans:
- [x] 14-01-PLAN.md — SentimentScorer: schema, utilities, and scorer class
- [x] 14-02-PLAN.md — Composite score integration: overlay wiring and regression tests

### Phase 15: Macro Context
**Goal**: Real macroeconomic data replaces hardcoded values and adjusts risk scoring dynamically based on market regime
**Depends on**: Phase 13 (requires FRED adapter and macro schemas), Phase 14 (uses scorer extension pattern)
**Requirements**: MACRO-01, MACRO-02, MACRO-03, MACRO-04, MACRO-05, MACRO-06, MACRO-07, SCORE-03, SCORE-04
**Success Criteria** (what must be TRUE):
  1. Market regime assessment uses real VIX data instead of hardcoded 20.0 and real yield curve data instead of estimated thresholds
  2. Macro indicators (Fed rate, CPI, GDP, yields) are fetched once per analysis run and shared across all holdings
  3. Yield curve spread (10Y-2Y) is computed and classified into regime (inverted/flat/normal/steep)
  4. Risk scoring weights adjust dynamically based on detected market regime -- high-volatility regimes increase risk weight
  5. Stocks, ETFs, and crypto respond to macro indicators with different sensitivity coefficients
**Plans**: 2 plans

Plans:
- [x] 15-01-PLAN.md — MacroScorer component: schema, thresholds, scorer class, and test suite
- [x] 15-02-PLAN.md — Composite wiring: macro overlay, hardcoded value replacement, and regression tests

### Phase 16: Report Enrichment
**Goal**: HTML report visualizes sentiment scores, macroeconomic context, and upcoming economic events for each holding and the portfolio
**Depends on**: Phase 14 (sentiment data), Phase 15 (macro data)
**Requirements**: REPORT-01, REPORT-02, REPORT-03, REPORT-04
**Success Criteria** (what must be TRUE):
  1. Each holding's report section includes sentiment score, confidence level, article count, and top headlines
  2. Portfolio-level macro dashboard shows VIX, yield curve, GDP, CPI, and Fed rate with traffic-light color coding (green/yellow/red)
  3. Fear & Greed Index gauge is displayed in the macro dashboard section
  4. Economic calendar section shows upcoming FOMC meetings, CPI releases, and earnings dates
**Plans**: 3 plans

Plans:
- [ ] 16-01-PLAN.md -- Data plumbing: EconomicCalendar schemas/adapter, sentiment summary persistence, macro_snapshot on FinwizState
- [ ] 16-02-PLAN.md -- Consolidated report sections: sentiment summary, macro dashboard with F&G gauge, economic calendar + CSS
- [ ] 16-03-PLAN.md -- Per-holding template enrichment: sentiment sections in enriched and deep analysis reports

## Progress

**Execution Order:**
Phases execute in numeric order: 13 -> 14 -> 15 -> 16

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1-5 | v1 | 13/13 | Shipped | 2026-02-08 |
| 6-8 | v2 | 6/6 | Shipped | 2026-02-08 |
| 9-12 | v3 | 7/7 | Shipped | 2026-02-08 |
| 13. Data Foundation | v4 | 10/10 | Complete | 2026-02-09 |
| 14. Sentiment Scoring | v4 | 2/2 | Complete | 2026-02-09 |
| 15. Macro Context | v4 | 2/2 | Complete | 2026-02-09 |
| 16. Report Enrichment | v4 | 0/3 | Planning complete | - |

---
*Roadmap created: 2026-02-08*
*Last updated: 2026-02-09 after Phase 16 planning*
