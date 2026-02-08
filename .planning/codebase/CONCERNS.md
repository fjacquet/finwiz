# Codebase Concerns

**Analysis Date:** 2026-02-08 (updated after v2 milestone)

## Tech Debt

**File Size Violations (300 line limit):**

- Issue: 150+ existing files exceed the 300-line limit
- Impact: Reduced maintainability, increased cognitive load
- Mitigation (v2): Pre-commit hook enforces limit for NEW files only. CI pipeline fails on new violations.
- Fix approach: Gradually split files during feature work. Not planned as standalone effort.

**Migration Utilities in Production Code:**

- Issue: Schema migration utilities (`migrate_portfolio_review_if_needed()`) embedded in production code path
- Files: `src/finwiz/schemas/migration.py`
- Impact: Runtime overhead for every request
- Fix approach: Move migrations to CLI scripts in `scripts/migrations/`. Run as explicit migration step.

## Resolved in v2

The following concerns from the original audit were resolved:

- **API Key Validation Bypassed in Tools** → SEC-01: Fail-fast `ValueError` at `__init__` across 9 tool classes
- **Hardcoded API Endpoints** → SEC-03: All 13 endpoints consolidated in `config/endpoints.py`
- **Sensitive Data in Logs** → SEC-02: Centralized `infrastructure/logging/sanitizer.py` with 3 handlers
- **Duplicate Portfolio Review Implementations** → REFAC-01: Single source in `portfolio_review/decisions.py`
- **Lazy-Loaded Orchestrators with Circular Import Risk** → REFAC-02: Registry pattern in `flows/orchestrator_registry.py`

## Resolved in v1

- **Broad Exception Handlers** → Replaced 50+ bare `except Exception:` with specific types
- **json.dumps Missing default=str** → Added `default=str` across all serialization calls
- **CrewAI Output Handling Anti-Pattern** → Standardized on Pydantic access cascade
- **Synchronous Rate Limiting** → Token bucket rate limiting via aiolimiter
- **Cache Cleanup Blocking** → Event-driven cache cleanup (no blocking sleep)
- **Crew Execution Without Timeouts** → Circuit breaker + timeout for all crew.kickoff() calls

## Known Bugs

**TODO: Cost Calculation Not Implemented:**

- Symptoms: Cost is always $0.00 in reports
- Files: `src/finwiz/flows/hybrid_analysis_synthesizer.py:269`
- Fix: Implement LiteLLM callback to track actual token usage and costs

**TODO: Async Adapter Migration Incomplete:**

- Symptoms: Mixed sync/async code with blocking calls
- Files: `src/finwiz/data/data_source_orchestrator.py:123`
- Fix: Complete async migration for all data adapters

## Security Considerations

**API Key Management:**

- Risk: 15+ API keys via environment variables with no rotation support
- Current mitigation: Keys in `.env` (gitignored), fail-fast validation at tool init (v2), log sanitization (v2)
- Remaining: Implement key rotation, use secret management service

**CORS Configuration:**

- Risk: CORS_ORIGINS only configured for localhost
- Current mitigation: Environment-based configuration exists
- Remaining: Document production CORS setup

## Performance Bottlenecks

**Sequential API Calls in Data Collection:**

- Problem: Each ticker fetched individually
- Partial fix: `batch_data_prefetcher.py` exists, asyncio.gather() with semaphore added in v1
- Remaining: Expand batch coverage

**Large Files (600+ lines) with Mixed Concerns:**

- Problem: 7+ files exceed 600 lines
- Mitigation: Pre-commit enforces 300-line limit for new files (v2)
- Remaining: Gradual splits during feature work

## Fragile Areas

**CrewAI Version Coupling:**

- Risk: Young framework, breaking changes in updates affect entire codebase
- Mitigation: Pinned version in pyproject.toml

**Pydantic Schema Evolution:**

- Risk: Schema changes break stored JSON data, no migration strategy
- Mitigation: `migration.py` exists but embedded in production code

**HTML Template String Concatenation:**

- Risk: Manual HTML with f-strings risks XSS, hard to maintain
- Mitigation: HTML output validation tests added in v1

**Feature Flag Dependencies:**

- Risk: 30+ flags, untested combinations, string literal references
- Mitigation: Enum-based flag names would reduce typo risk

## Scaling Limits

**LLM Token Limits:** ~500 holdings before context overflow
**Concurrent Crew Execution:** Conservative FINWIZ_DEEP_ANALYSIS_PARALLEL_LIMIT=2
**In-Memory Caching:** 10000 items max, no tiered eviction
**File-Based Storage:** Individual JSON/HTML files, no database

## Dependencies at Risk

- **CrewAI** — Young framework, core dependency
- **yfinance** — Unofficial API, primary data source (has fallback chain)
- **OpenRouter** — Single LLM proxy (has multi-provider fallback via LiteLLM)
- **Backtrader** — Maintenance mode, Python 3.12 compatibility concerns

## Missing Critical Features

- **Multi-User Support** — Single-user design with global state
- **Real-Time Data Updates** — Snapshot-based only, no streaming
- **Internationalization (i18n)** — Hardcoded French strings, no framework

## Test Coverage Gaps

**Feature Flag Combinations:**

- What's not tested: Interactions between 30+ flags
- Priority: Medium — identify critical dependencies, test common combinations

**Performance Regression:**

- What's not tested: Execution time, memory usage, API call counts
- Priority: Medium — add pytest-benchmark tests, set performance budgets

## Resolved Test Gaps (v1)

- Orchestrator integration tests — added with real state mutations
- Crew output parsing — Pydantic access cascade tested
- Data adapter fallbacks — fallback scenario tests added
- HTML output validation — XSS prevention tests added

---

*Concerns audit: 2026-02-08 (updated after v2 milestone)*
