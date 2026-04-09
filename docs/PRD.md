# Product Requirements Document -- FinWiz

**Version:** 1.0
**Date:** 2026-04-09
**Status:** Active

## 1. Product Vision

FinWiz is an AI-powered financial analysis platform that provides comprehensive portfolio analysis, deep per-holding scoring, investment discovery, and actionable rebalancing recommendations -- all delivered as styled HTML reports. It uses a hybrid approach: deterministic Python scoring ($0, <100ms) for quantitative analysis, and CrewAI crews for qualitative insights only.

## 2. Target Users

Individual investors managing diversified multi-asset portfolios (stocks, ETFs, crypto) who want professional-grade analysis without paying for financial advisors. Technical users comfortable with CLI tools and CSV-based portfolio definitions.

## 3. User Stories

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| US-1 | As an investor, I want to run a complete portfolio analysis with a single command | `crewai flow kickoff` executes all 6 phases end-to-end |
| US-2 | As an investor, I want each holding graded A+ to F with a composite score | Composite = 40% fundamental + 30% technical + 30% risk |
| US-3 | As an investor, I want AI-generated qualitative insights alongside Python scores | SEC analysis, market narrative, risk assessment produced per holding |
| US-4 | As an investor, I want discovery of A+ investment opportunities I don't hold | Discovery crews screen stocks, ETFs, and crypto separately |
| US-5 | As an investor, I want rebalancing recommendations with specific trade instructions | Output includes buy/sell/hold actions with target allocations |
| US-6 | As an investor, I want all results as styled HTML reports | Reports viewable in any browser, one per phase |
| US-7 | As an investor, I want the system to work with my existing CSV portfolio files | Reads `data/stock.csv`, `data/etf.csv`, `data/crypto.csv` |

## 4. Functional Requirements

- **Data ingestion** -- Read portfolio holdings from CSV files (37 stocks, 29 ETFs, 4 crypto).
- **Input validation** -- Configurable strictness via `VALIDATION_STRICTNESS` (off / warn / error).
- **Deep analysis pipeline** -- 4-step per-holding process:
  1. `collect_raw_data()` -- Python tools fetch market data ($0)
  2. `calculate_quantitative()` -- Python scorer computes composite grade ($0)
  3. `generate_qualitative()` -- AI crew produces narrative insights (~$0.05)
  4. `synthesize()` -- Python merges quantitative and qualitative ($0)
- **Investment discovery** -- Separate AI crews screen stocks, ETFs, and crypto for A+ opportunities.
- **Alternative matching** -- Suggest replacements for underperforming holdings.
- **HTML reporting** -- Generate styled reports for portfolio review, deep analysis, discovery, and rebalancing.
- **Feature flags** -- Toggle optional capabilities: `DEEP_ANALYSIS_ENABLED`, `PERPLEXITY_RESEARCH_ENABLED`, batch prefetch.

## 5. Non-Functional Requirements

| Requirement | Target | Rationale |
|-------------|--------|-----------|
| Token budget | <100K tokens per crew run | LiteLLM alert threshold; prevents cost explosion |
| LLM response cap | max_tokens per model type (1024-4096) | Prevents unbounded output; configurable via `LLM_MAX_TOKENS` |
| Cost per ticker | <$0.10 for deep analysis | Python handles deterministic work for $0 |
| Execution time | 10-30s per deep analysis (Python); 5-10min per discovery crew (AI) | Acceptable for batch portfolio analysis |
| Test coverage | 65% minimum | Enforced by pytest-cov |
| Python version | >=3.12, <3.13 | Required by CrewAI and TA-Lib |
| Line length | 180 characters | Configured in ruff |
| File size | 300 lines max | Enforced by `make check-file-size` |

## 6. Architecture Principles

- **AI Minimalism (ADR-003)** -- Python for deterministic tasks, AI only for qualitative reasoning.
- **Sync-first pipeline (ADR-004)** -- Deterministic execution order for financial calculations.
- **Context scoping (ADR-006)** -- Send summarized metrics to AI, never raw data dumps.
- **Token optimization (ADR-007)** -- Deduplicate prompt boilerplate, cap LLM response lengths, guard against token overflow.
- **Python wins** -- When AI and Python scores disagree, Python takes precedence.

## 7. Scope Boundaries

| In Scope | Out of Scope |
|----------|-------------|
| Portfolio analysis and scoring | Automated trading / broker integration |
| AI-powered qualitative insights | Real-time streaming data |
| Investment discovery and screening | Mobile app / web UI (reports are static HTML) |
| Rebalancing recommendations | Multi-user / authentication |
| HTML report generation | Portfolio tracking over time (each run is independent) |
| Feature flag configuration | |

## 8. Data Sources

| Source | Usage | Required |
|--------|-------|----------|
| Yahoo Finance (yfinance) | Prices, fundamentals | Yes |
| SEC API | Company filings | Yes |
| Alpha Vantage | Additional market data | Optional |
| Twelve Data | Technical indicators | Optional |
| CoinMarketCap | Crypto data | Yes (for crypto) |
| Perplexity | Current market research | Optional (feature flag) |
| FRED | Macroeconomic data | Optional |

## 9. References

- `docs/explanations/ARCHITECTURE.md` -- System architecture
- `docs/adr/` -- Architecture Decision Records
- `CLAUDE.md` -- Development guide
- `CHANGELOG.md` -- Version history
