# FinWiz — AI-Powered Financial Analysis Platform

## What This Is

FinWiz is an AI-powered financial analysis platform built with CrewAI that analyzes portfolios of stocks, ETFs, and crypto using hybrid Python scoring + AI crews. It features a real investment discovery pipeline (IPOs, breakouts, momentum) alongside comprehensive portfolio analysis with quantitative backtesting and rebalancing.

## Core Value

Hybrid financial analysis: deterministic Python scoring ($0, <100ms) for quantitative rigor, AI crews for qualitative reasoning, with real newcomer detection for investment discovery.

## Current State

Shipped v1 (2026-02-08): Hardening & Discovery milestone complete.

- 106,813 LOC Python, 4387 tests passing, 65.78% coverage
- Tech stack: Python 3.12, CrewAI >=1.5.0, uv, aiolimiter, TA-Lib
- Codebase mapped in `.planning/codebase/` (7 documents)

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
- ✓ Specific exception types replacing bare except Exception: handlers — v1
- ✓ json.dumps with default=str across all serialization — v1
- ✓ Standardized CrewAI output via Pydantic access cascade — v1
- ✓ Token bucket rate limiting with per-API quotas (aiolimiter) — v1
- ✓ Crew execution timeouts with circuit breaker — v1
- ✓ Event-driven cache cleanup (no blocking sleep) — v1
- ✓ Batch API calls with asyncio.gather() + semaphore — v1
- ✓ Newcomer discovery pipeline (IPO screener, breakout detector, momentum scanner) — v1
- ✓ Discovery feature flag routing (FF_NEWCOMER_DISCOVERY) with legacy fallback — v1
- ✓ Perplexity enrichment for top discovery candidates — v1
- ✓ Orchestrator integration tests with real state mutations — v1
- ✓ Crew output parsing and adapter fallback tests — v1
- ✓ HTML output validation with XSS prevention — v1

### Active

(No active requirements — define with `/gsd:new-milestone`)

### Out of Scope

- File size violations (300-line limit) — 150+ files, tracked as REFAC-04
- Duplicate portfolio review consolidation — big refactor across 10+ files
- Lazy-loaded orchestrator redesign — circular import restructuring
- Security hardening (API key rotation, endpoint centralization) — separate effort
- Multi-user support — architectural change
- Real-time data / streaming — future milestone
- i18n framework — future milestone

## Constraints

- **Testing**: unittest.mock is BANNED — use pytest-mock only (`mocker.patch()`)
- **Serialization**: `json.dumps` always with `default=str`
- **Schemas**: Pydantic models go in `schemas/`, not domain folders
- **Discovery**: Discovered candidates MUST exclude tickers already in portfolio
- **Feature flags**: New discovery gated by `FF_NEWCOMER_DISCOVERY` flag, legacy mocks remain as fallback
- **Line length**: 180 characters (ruff configured)
- **Coverage**: 65% minimum threshold
- **AI Minimalism**: Python for deterministic tasks, AI only for qualitative reasoning

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Skip 300-line file size limit | 150+ files affected, massive effort with low immediate payoff | ✓ Good — deferred to v2 |
| Interleave concerns with discovery | Fix related issues as we build new code, not as separate tracks | ✓ Good — clean patterns in new code |
| Skip duplicate portfolio review consolidation | Big refactor across 10+ files, not blocking | ✓ Good — deferred to v2 |
| Skip lazy-loaded orchestrator redesign | Works today, fixing circular imports is architectural | ✓ Good — no issues encountered |
| Feature-flag discovery pipeline | Legacy mocks remain as fallback for safety | ✓ Good — clean migration path |
| Token bucket over fixed sleep | aiolimiter handles burst + rate limiting natively | ✓ Good — cleaner than manual sleep |
| Circuit breaker for crew timeouts | Prevent cascade failures from repeatedly failing crews | ✓ Good — auto-recovery after 60s |
| Lazy imports in discovery pipeline | Forward-compatible: Phase 3 can be built before Phase 2 | ✓ Good — flexible dev order |

---
*Last updated: 2026-02-08 after v1 milestone*
