# FinWiz — AI-Powered Financial Analysis Platform

## What This Is

FinWiz is an AI-powered financial analysis platform built with CrewAI that analyzes portfolios of stocks, ETFs, and crypto using hybrid Python scoring + AI crews. It features real investment discovery, comprehensive portfolio analysis with quantitative backtesting and rebalancing, portfolio stress testing against market scenarios, async-parallel data collection with smart caching, and smart scoring enriched with news sentiment and macroeconomic context. Security hardening, structural quality, and automated enforcement are built in.

## Core Value

Hybrid financial analysis enriched with news sentiment and macroeconomic context for smarter scoring: deterministic Python scoring ($0, <100ms) for quantitative rigor, AI crews for qualitative reasoning, with real newcomer detection for investment discovery.

## Current State

Shipped v4 (2026-02-09): Data Intelligence & Smart Scoring milestone complete.

- ~110,000 LOC Python, 4,795 tests passing, 67.41% coverage
- Tech stack: Python 3.12, CrewAI >=1.5.0, uv, aiolimiter, TA-Lib, LiteLLM, finnhub-python, fredapi
- Scoring: 40/30/30 base (fundamental/technical/risk) + additive sentiment + macro overlays with 4-gate safety
- Data: Finnhub news, FRED macro indicators, Fear & Greed Index, Economic Calendar -- all feature-flagged
- Reports: Per-holding sentiment cards, macro dashboard with traffic-light indicators, Fear & Greed gauge, economic calendar
- Async: Full async data collection, batch prefetching, configurable parallel analysis
- Caching: Tiered eviction (hot/warm/cold), type-aware TTLs, metrics logging
- Cost: LLM cost tracking per crew with real provider pricing
- Risk: Portfolio stress testing (market crash, rate shock, sector shock) with HTML report
- Security: fail-fast API key validation, log sanitization, centralized endpoints
- Quality: pre-commit hooks + CI pipeline enforce ruff, file size, unittest.mock ban

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
- ✓ Fail-fast on missing API keys at tool instantiation — v2
- ✓ Log sanitization for sensitive data (API keys, tokens) — v2
- ✓ Centralize hardcoded API endpoint URLs — v2
- ✓ Consolidate duplicate portfolio review logic across 10+ files — v2
- ✓ Redesign lazy-loaded orchestrators to eliminate circular import risk — v2
- ✓ Automated quality enforcement (pre-commit hooks, CI checks, file size linting) — v2
- ✓ Complete async migration for all data adapters — v3
- ✓ Configurable parallel limit for concurrent holdings analysis — v3
- ✓ Batch data prefetcher integrated into main analysis flow — v3
- ✓ Batch API calls for providers supporting multi-ticker — v3
- ✓ Tiered cache eviction (hot/warm/cold) with type-aware TTLs — v3
- ✓ Cache hit/miss metrics logging for observability — v3
- ✓ LLM cost tracking per crew using real provider pricing — v3
- ✓ Per-crew and total costs reported in analysis output — v3
- ✓ Market crash scenario stress testing — v3
- ✓ Interest rate shock scenario stress testing — v3
- ✓ Sector-specific shock scenario stress testing — v3
- ✓ Stress test results in HTML report with color-coded impact tables — v3
- ✓ Finnhub news adapter with waterfall fallback — v4
- ✓ FRED macro adapter (Fed rate, CPI, VIX, yields) with session caching — v4
- ✓ Fear & Greed Index adapter with library + HTTP fallback — v4
- ✓ News deduplication and source reliability weighting — v4
- ✓ Feature flags for sentiment and macro pipelines with circuit breakers — v4
- ✓ SentimentScorer with temporal decay, reliability weighting, confidence metric — v4
- ✓ No-news = None (not neutral 0.0) explicit handling — v4
- ✓ Sentiment as additive overlay with 4-gate safety (flag, weight, data, confidence) — v4
- ✓ MacroScorer with VIX, yield curve, Fed rate, per-asset-class sensitivity — v4
- ✓ Macro as additive overlay with 4-gate safety preserving 40/30/30 base — v4
- ✓ Real VIX replacing hardcoded 20.0 in market regime assessment — v4
- ✓ Real Fed rate replacing hardcoded estimates — v4
- ✓ Per-holding sentiment section in HTML reports — v4
- ✓ Macro dashboard with traffic-light indicators and Fear & Greed gauge — v4
- ✓ Economic calendar with FOMC, CPI releases, and earnings dates — v4
- ✓ Discovery pipeline returns real screened candidates — v4

### Active

(None — all requirements shipped through v4. Next milestone defines new requirements.)

### Out of Scope

- File size violations (300-line limit) — 150+ files, enforce for new code only
- API key rotation support — runtime key refresh too complex
- Multi-user support — architectural change
- Real-time data / streaming — future milestone
- i18n framework — future milestone
- OpenTelemetry tracing — future milestone
- Persistent cross-run cache — future milestone
- FinBERT sentiment model — v4 research deferred (SENT-F01)
- Sector-relative sentiment normalization — v4 research deferred (SENT-F02)
- Historical macro overlay charts — v4 research deferred (MACRO-F01)

## Constraints

- **Testing**: unittest.mock is BANNED — use pytest-mock only (`mocker.patch()`)
- **Serialization**: `json.dumps` always with `default=str`
- **Schemas**: Pydantic models go in `schemas/`, not domain folders
- **Discovery**: Discovered candidates MUST exclude tickers already in portfolio
- **Feature flags**: All new data pipelines gated by feature flags with safe defaults (off)
- **Line length**: 180 characters (ruff configured)
- **Coverage**: 65% minimum threshold
- **AI Minimalism**: Python for deterministic tasks, AI only for qualitative reasoning
- **Quality**: Pre-commit hooks enforce ruff, file size limits, unittest.mock ban
- **Scoring overlays**: Additive only, never redistribute base 40/30/30 weights
- **French localization**: All HTML report labels in French

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Skip 300-line file size limit | 150+ files affected, massive effort with low immediate payoff | ✓ Good — deferred, enforced for new code |
| Interleave concerns with discovery | Fix related issues as we build new code, not as separate tracks | ✓ Good — clean patterns in new code |
| Skip duplicate portfolio review consolidation (v1) | Big refactor across 10+ files, not blocking | ✓ Good — done in v2 |
| Skip lazy-loaded orchestrator redesign (v1) | Works today, fixing circular imports is architectural | ✓ Good — done in v2 |
| Feature-flag discovery pipeline | Legacy mocks remain as fallback for safety | ✓ Good — clean migration path |
| Token bucket over fixed sleep | aiolimiter handles burst + rate limiting natively | ✓ Good — cleaner than manual sleep |
| Circuit breaker for crew timeouts | Prevent cascade failures from repeatedly failing crews | ✓ Good — auto-recovery after 60s |
| Lazy imports in discovery pipeline | Forward-compatible: Phase 3 can be built before Phase 2 | ✓ Good — flexible dev order |
| Fail-fast API key validation | ValueError at __init__ catches config errors immediately | ✓ Good — 9 tool classes protected |
| Centralized log sanitizer | 3-handler approach covers all log output paths | ✓ Good — zero leaks in tests |
| Endpoint config module | Single source for all 13 API URLs | ✓ Good — no hardcoded URLs |
| Dead code deletion for duplicates | 5 divergent portfolio review copies → 1 shared module | ✓ Good — reduced maintenance burden |
| Registry pattern for orchestrators | Eliminates circular imports, enables lazy loading | ✓ Good — clean `__getattr__` approach |
| Pre-commit with `--check-all` for CI | Same hooks, different mode for CI vs local | ✓ Good — parity achieved |
| PythonReportGenerator for production | FinalReportGenerator (Jinja2) unused; production uses inline HTML | ✓ Good — Phase 12 targeted correct generator |
| Section generator delegation | HTML generation in section_generators.py, delegated from PythonReportGenerator | ✓ Good — consistent pattern across all sections |
| Inline CSS color coding for stress test | Red/orange/green for impact severity and sensitivity labels | ✓ Good — matches existing report styling |
| Additive overlays for sentiment/macro | 4-gate safety: flag, weight, data, confidence. Never redistribute base weights | ✓ Good — zero risk of score regression |
| Component scorer pattern | SentimentScorer/MacroScorer return (score_or_None, details_dict) | ✓ Good — consistent, testable, composable |
| Session-level macro data collection | Collect once per run, share across holdings via FinwizState | ✓ Good — avoids redundant API calls |
| Traffic-light CSS for macro indicators | Reuse existing risk-low/risk-medium/risk-high pattern | ✓ Good — consistent report styling |
| Fear & Greed as CSS-only gauge | Horizontal gradient bar with positioned marker, no JavaScript | ✓ Good — works in all report viewers |
| Sentiment persistence in enriched JSON | Store sentiment_summary during analysis for report-time access | ✓ Good — avoids re-fetching at report time |

---
*Last updated: 2026-02-09 after v4 milestone completion*
