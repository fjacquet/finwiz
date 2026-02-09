# Project Milestones: FinWiz

## v1 Hardening & Discovery (Shipped: 2026-02-08)

**Delivered:** Real newcomer detection replaces mocked discovery data, while production-risk code quality issues have been eliminated.

**Phases completed:** 1-5 (13 plans total)

**Key accomplishments:**

- Replaced 50+ bare `except Exception:` handlers with specific exception types and added `default=str` to all json.dumps calls
- Built complete newcomer discovery pipeline: universe provider, IPO screener, breakout detector, momentum scanner, candidate scorer
- Integrated discovery pipeline end-to-end with feature flag routing (FF_NEWCOMER_DISCOVERY) and Perplexity enrichment
- Implemented token bucket rate limiting (aiolimiter), crew execution timeouts with circuit breaker, and event-driven cache cleanup
- Added 75+ tests covering orchestrator state mutations, crew output parsing, adapter fallback scenarios, and HTML validation

**Stats:**

- 106,813 lines of Python
- 5 phases, 13 plans, 22 requirements
- 4387 tests passing, 65.78% coverage
- 2 days from start to ship (2026-02-07 to 2026-02-08)

**Audit:** Passed (22/22 requirements, 23/23 integration connections, 3/3 E2E flows)

**Archive:** `milestones/v1-ROADMAP.md`, `milestones/v1-REQUIREMENTS.md`, `milestones/v1-MILESTONE-AUDIT.md`

---

## v2 Security & Structural Quality (Shipped: 2026-02-08)

**Delivered:** Security hardening, structural debt elimination, and automated code quality enforcement across the entire codebase.

**Phases completed:** 6-8 (6 plans total)

**Key accomplishments:**

- Fail-fast API key validation across 9 tool classes — no silent degradation on missing keys
- Centralized log sanitization with 3 handlers filtering sensitive data before output
- All 13 API endpoint URLs consolidated into `config/endpoints.py` (zero hardcoded URLs remain)
- Portfolio review logic consolidated from 10+ duplicate sites into single `decisions.py` module
- Orchestrator registry pattern eliminates circular import risk with lazy loading
- Pre-commit hooks + CI pipeline enforce ruff, file size limits, and unittest.mock ban on every commit

**Stats:**

- 83 files changed, +1801/-1182 lines
- 106,718 lines of Python
- 3 phases, 6 plans, 7 requirements
- 4416 tests passing, 66% coverage
- 1 day (2026-02-08)

**Audit:** Passed (7/7 requirements, 3/3 phases, 5/5 integration, 5/5 E2E flows)

**Archive:** `milestones/v2-ROADMAP.md`, `milestones/v2-REQUIREMENTS.md`, `milestones/v2-MILESTONE-AUDIT.md`

---

## v3 Performance & Risk Analysis (Shipped: 2026-02-08)

**Delivered:** Full async parallelism, smart caching with observability, LLM cost tracking, and portfolio risk stress testing with HTML report integration.

**Phases completed:** 9-12 (7 plans total)

**Key accomplishments:**

- Full async data collection with batch prefetching and configurable parallelism (DEEP_ANALYSIS_BATCH_SIZE env-configurable)
- Smart tiered cache eviction (hot/warm/cold) with type-aware TTLs (market:15min, fundamentals:24h, static:7d)
- LLM cost tracking per crew using litellm.completion_cost() with crew attribution via contextvars
- Portfolio stress testing engine: market crash, interest rate shock, and sector-specific shock scenarios
- Stress test results rendered in production HTML report with color-coded impact tables and sensitivity labels
- Resolved all Pyright errors in reporting pipeline (dead code removal, missing state fields, signature fixes)

**Stats:**

- 233 files changed, +7553/-2551 lines
- 107,586 lines of Python
- 4 phases, 7 plans, 13 requirements
- 4,516 tests passing, 66.85% coverage
- 1 day (2026-02-08)

**Audit:** Passed (13/13 requirements, 4/4 phases, 30/30 integration, 1/1 E2E flow)

**Archive:** `milestones/v3-ROADMAP.md`, `milestones/v3-REQUIREMENTS.md`, `milestones/v3-MILESTONE-AUDIT.md`

---

## v4 Data Intelligence & Smart Scoring (Shipped: 2026-02-09)

**Delivered:** News sentiment, macroeconomic indicators, and smart scoring overlays enriching the composite analysis pipeline with market context beyond technicals and fundamentals.

**Phases completed:** 13-16 (17 plans total)

**Key accomplishments:**

- Built data foundation with Finnhub news adapter (waterfall fallback), FRED macro adapter (session-cached), Fear & Greed adapter, and 5 feature flags with circuit breakers
- Created SentimentScorer with temporal decay weighting, source reliability, and 40/30/30 confidence metric -- explicit None for no-news holdings
- Created MacroScorer using real VIX, yield curve spread, and Fed rate from FRED -- per-asset-class sensitivity (stock=1.0, etf=0.7, crypto=0.3)
- Wired both overlays as additive adjustments in composite scorer with identical 4-gate safety (flag, weight, data, confidence) preserving 40/30/30 base weights
- Added 3 HTML report sections: per-holding sentiment cards, macro dashboard with traffic-light indicators and Fear & Greed gauge, economic calendar with FOMC/CPI/earnings dates
- EconomicCalendarAdapter from Finnhub with session caching, sentiment_summary persistence in enriched JSON, macro_snapshot on FinwizState for report-time access

**Stats:**

- 106 files changed, +11,784 / -1,282 lines
- ~110,000 lines of Python
- 4 phases, 17 plans, 30 requirements
- 4,795 tests passing, 67.41% coverage
- 2 days (2026-02-08 to 2026-02-09)

**Audit:** Passed (30/30 requirements, 28/29 integration connections, 3/3 E2E flows)

**Archive:** `milestones/v4-ROADMAP.md`, `milestones/v4-REQUIREMENTS.md`, `milestones/v4-MILESTONE-AUDIT.md`

---
