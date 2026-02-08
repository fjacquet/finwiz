# FinWiz — Hardening & Discovery Milestone

## What This Is

FinWiz is an AI-powered financial analysis platform built with CrewAI that analyzes portfolios of stocks, ETFs, and crypto using hybrid Python scoring + AI crews. This milestone hardens the codebase (error handling, performance, test coverage) while building a real investment discovery pipeline to replace the current mocked data.

## Core Value

Replace mocked discovery with real newcomer detection (IPOs, breakouts, momentum) while eliminating production-risk code quality issues that hide bugs and degrade performance.

## Requirements

### Validated

- ✓ Hybrid analysis pipeline (Python scoring + AI crews) — existing
- ✓ Portfolio analysis for stocks, ETFs, crypto — existing
- ✓ Deep analysis with composite scoring (40% fundamental, 30% technical, 30% risk) — existing
- ✓ HTML report generation — existing
- ✓ Feature flag system with circuit breakers — existing
- ✓ CrewAI Flow orchestration with state management — existing
- ✓ Quantitative backtesting and rebalancing — existing
- ✓ Data adapter fallback chain (yfinance, Alpha Vantage, Tiingo) — existing
- ✓ Caching infrastructure with TTL — existing

### Active

**Error Handling:**

- [ ] Replace 44+ bare `except Exception:` with specific exception types
- [ ] Add `default=str` to 40+ `json.dumps()` calls missing it
- [ ] Standardize CrewAI output handling via Pydantic schemas

**Performance:**

- [ ] Batch API calls instead of sequential per-holding fetches
- [ ] Replace 14+ blocking `asyncio.sleep()` rate limiters with token bucket
- [ ] Add timeouts to crew execution (wrap `kickoff()` with `asyncio.wait_for()`)
- [ ] Fix cache cleanup blocking (event-driven instead of synchronous sleep)

**Test Coverage:**

- [ ] Orchestrator integration tests with real state mutations
- [ ] Crew output parsing tests (malformed JSON, schema validation)
- [ ] Data adapter fallback scenario tests
- [ ] HTML output validation tests

**Newcomer Discovery Pipeline:**

- [ ] Pydantic schemas for discovery candidates and enrichment
- [ ] Dynamic universe provider (mine ETF holdings via yfinance)
- [ ] IPO screener (SEC EDGAR EFTS for recent S-1 filings)
- [ ] Breakout detector (price/volume breakouts on small/mid-caps)
- [ ] Momentum scanner (volume anomaly + RSI + analyst changes)
- [ ] Candidate scorer (reuses existing ScreeningCriteria + score_to_grade)
- [ ] Perplexity enrichment for top candidates (gated by feature flag)
- [ ] Pipeline orchestrator with portfolio exclusion
- [ ] Feature flag routing in stock/etf/crypto analyzers
- [ ] Unit tests for all discovery modules

### Out of Scope

- File size violations (300-line limit) — 150+ files, too large for this milestone
- Duplicate portfolio review consolidation — big refactor across 10+ files
- Lazy-loaded orchestrator redesign — circular import restructuring
- Migration utilities in production code — low immediate impact
- Security hardening (API key rotation, endpoint centralization) — separate effort
- Multi-user support — architectural change
- Real-time data / streaming — future milestone
- i18n framework — future milestone

## Context

- Python 3.12, CrewAI >=1.5.0, uv package manager
- Discovery is currently mocked: `scoring/{stock,etf,crypto}_analyzer.py` return hardcoded tickers
- Portfolio CSVs are real holdings: 37 stocks, 29 ETFs, 4 crypto (70 total)
- Detailed discovery pipeline design exists in quokka plan (8 new files, 5 modifications, 7 test files)
- Codebase mapped in `.planning/codebase/` (7 documents, 2325 lines)
- AI Minimalism principle: Python for deterministic tasks, AI only for qualitative reasoning

## Constraints

- **Testing**: unittest.mock is BANNED — use pytest-mock only (`mocker.patch()`)
- **Serialization**: `json.dumps` always with `default=str`
- **Schemas**: Pydantic models go in `schemas/`, not domain folders
- **Discovery**: Discovered candidates MUST exclude tickers already in portfolio
- **Feature flags**: New discovery gated by `FF_NEWCOMER_DISCOVERY` flag, legacy mocks remain as fallback
- **Line length**: 180 characters (ruff configured)
- **Coverage**: 65% minimum threshold

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Skip 300-line file size limit | 150+ files affected, massive effort with low immediate payoff | -- Pending |
| Interleave concerns with discovery | Fix related issues as we build new code, not as separate tracks | -- Pending |
| Skip duplicate portfolio review consolidation | Big refactor across 10+ files, not blocking | -- Pending |
| Skip lazy-loaded orchestrator redesign | Works today, fixing circular imports is architectural | -- Pending |
| Feature-flag discovery pipeline | Legacy mocks remain as fallback for safety | -- Pending |

---
*Last updated: 2026-02-07 after initialization*
