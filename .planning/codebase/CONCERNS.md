# Codebase Concerns

**Analysis Date:** 2026-02-07

## Tech Debt

**File Size Violations (300 line limit):**

- Issue: CLAUDE.md explicitly states "Max 300 lines per file", but 150+ files exceed this limit
- Files: `src/finwiz/analysis/deep_analysis_pipeline.py` (784 lines), `src/finwiz/orchestrators/reporting_orchestrator.py` (723 lines), `src/finwiz/tools/portfolio_holdings_html_generator.py` (617 lines), `src/finwiz/tools/perplexity_analysis_integration.py` (617 lines), `src/finwiz/tools/standardized_sentiment_tool.py` (612 lines), `src/finwiz/tools/notification_service.py` (610 lines), `src/finwiz/orchestrators/portfolio_review_orchestrator.py` (601 lines), `src/finwiz/quantitative/rebalancing_history_tracker.py` (599 lines), plus 142 more files
- Impact: Violates stated project standards, reduces maintainability, makes testing harder, increases cognitive load
- Fix approach: Refactor large files into focused modules. For example, split `deep_analysis_pipeline.py` into separate modules for data collection, scoring, synthesis, and AI generation. Extract HTML generation logic from orchestrators to `reporting/` module. Create sub-modules in `quantitative/` for each major concern.

**Broad Exception Handlers:**

- Issue: 44+ instances of bare `except Exception:` handlers that may hide bugs or swallow important errors
- Files: `src/finwiz/validation/report.py:335`, `src/finwiz/validation/sec_citation.py:495`, `src/finwiz/validation/scripts.py:169,206,217`, `src/finwiz/infrastructure/logging/enhanced.py:472`, `src/finwiz/tools/sec_tool.py:125`, `src/finwiz/tools/screening_ranking.py:87,105`, `src/finwiz/integration/cache.py:360`, `src/finwiz/orchestrators/portfolio_review_orchestrator.py:67,73`, `src/finwiz/tools/yahoo_finance_company_info_tool.py:41`, `src/finwiz/orchestrators/portfolio_rebalancing.py:336,398`, `src/finwiz/quantitative/performance_benchmarks.py:247`, plus 30 more
- Impact: Makes debugging difficult, can hide root causes, may mask data quality issues, violates fail-fast principle
- Fix approach: Replace with specific exception types (e.g., `except (ValueError, KeyError, APIError)`). Add proper error context logging before catch. Use custom exceptions for domain errors. Only use broad handlers at system boundaries with explicit logging and re-raising.

**json.dumps Missing default=str:**

- Issue: 40+ calls to `json.dumps()` but only ~15 use `default=str` parameter, risking serialization failures for datetime, Decimal, and custom types
- Files: Throughout codebase, particularly in `src/finwiz/tools/`, `src/finwiz/orchestrators/`, `src/finwiz/infrastructure/logging/`
- Impact: Runtime TypeError when serializing non-JSON types (datetime, Decimal, Enum), inconsistent serialization behavior, fragile crew output handling
- Fix approach: Enforce `json.dumps(data, default=str, indent=2)` as standard pattern. Add ruff rule to detect missing `default=` parameter. Create utility function `to_json(data)` that always includes proper defaults. Update all existing calls systematically.

**CrewAI Output Handling Anti-Pattern:**

- Issue: Inconsistent crew result handling - sometimes `str(result.raw)`, sometimes `str(result)`, sometimes direct access, leading to fragile parsing
- Files: `src/finwiz/crew_factory.py:61,86,134,182`, crew execution paths throughout
- Impact: Breaks when CrewAI changes output format, inconsistent error handling, difficult to test, parsing failures may be silent
- Fix approach: Standardize on single pattern using Pydantic schemas. All crew tasks should use `output_pydantic` in tasks.yaml. Create `CrewOutputParser` utility to centralize parsing logic with validation. Never use `str(result)` - always access structured fields.

**Duplicate Portfolio Review Implementations:**

- Issue: Multiple implementations of portfolio review logic scattered across 10+ files
- Files: `src/finwiz/reporting/python_report_generator.py`, `src/finwiz/reporting/section_generators.py`, `src/finwiz/reporting/portfolio_review_html.py`, `src/finwiz/tools/portfolio_holdings_html_generator.py`, `src/finwiz/orchestrators/portfolio_review_orchestrator.py`, `src/finwiz/validation/report_data.py`, plus others
- Impact: Inconsistent calculations, duplicated logic is hard to maintain, bug fixes may not propagate to all copies, violates DRY principle
- Fix approach: Consolidate into single authoritative implementation in `finwiz.quantitative.portfolio_analyzer`. HTML generation goes to `finwiz.reporting.portfolio_review_html`. Orchestrator delegates to these modules. Remove duplicates systematically.

**Lazy-Loaded Orchestrators with Circular Import Risk:**

- Issue: Flow uses lazy-loaded orchestrator properties to avoid circular imports, but pattern is fragile and error-prone
- Files: `src/finwiz/flows/orchestrator.py` - properties for `deep_analysis_orch`, `validation_orch`, etc.
- Impact: Initialization errors happen late at runtime, difficult to test, violates fail-fast principle, coupling is hidden
- Fix approach: Use dependency injection container (OrchestratorDependencies already exists). Instantiate all orchestrators in `__init__` with proper dependency order. If circular imports exist, refactor module boundaries - orchestrators should not import from flows.

**Migration Utilities in Production Code:**

- Issue: Schema migration utilities (`migrate_portfolio_review_if_needed()`) embedded in production code path
- Files: `src/finwiz/schemas/migration.py`
- Impact: Runtime overhead for every request, makes code harder to understand, migrations should be one-time operations
- Fix approach: Move migrations to CLI scripts in `scripts/migrations/`. Run as explicit migration step during deployment. Remove migration calls from hot paths. Add version tracking to prevent re-running migrations.

## Known Bugs

**TODO: Cost Calculation Not Implemented:**

- Symptoms: Comment states "TODO: Implement actual cost calculation based on LLM usage" but feature is advertised
- Files: `src/finwiz/flows/hybrid_analysis_synthesizer.py:269`
- Trigger: Any deep analysis flow - cost is always $0.00 in reports
- Workaround: None - feature is incomplete
- Fix: Implement LiteLLM callback to track actual token usage and costs, aggregate by holding, include in EnrichedAnalysis metadata

**TODO: Async Adapter Migration Incomplete:**

- Symptoms: Comment "TODO: Migrate remaining adapters to async interface" indicates incomplete migration
- Files: `src/finwiz/data/data_source_orchestrator.py:123`
- Trigger: Using data adapters that haven't been migrated to async
- Workaround: Mixed sync/async code with blocking calls
- Fix: Complete async migration for all data adapters (yfinance, alpha_vantage, etc.). Use asyncio.to_thread for sync-only libraries. Standardize on fully async data pipeline.

## Security Considerations

**API Key Management:**

- Risk: 15+ API keys required, managed via environment variables with no rotation support
- Files: `src/finwiz/config/manager.py:52-90`, `.env.example` (318 lines)
- Current mitigation: Keys stored in `.env` (gitignored), validation on startup, format checking
- Recommendations: Implement API key rotation (FF_ENABLE_API_KEY_ROTATION exists but not implemented), use secret management service (AWS Secrets Manager, HashiCorp Vault), add key expiry warnings, implement per-environment key isolation, add audit logging for key usage

**API Key Validation Bypassed in Tools:**

- Risk: Some tools silently return empty results when API keys are missing instead of failing fast
- Files: `src/finwiz/tools/twelve_data_multi_indicator_tool.py:153-155`, `src/finwiz/tools/chart_img_tool.py:50-52`, `src/finwiz/tools/alpha_vantage_news_tool.py:39-41`
- Current mitigation: Partial - startup validation exists but tools can be instantiated without validation
- Recommendations: Fail fast at tool instantiation if required key is missing. Use factory pattern strictly (already exists in `tool_factories.py`). Add runtime assertion that validates keys before any API call. Never return "Error: API_KEY not set" strings - raise exceptions.

**Hardcoded API Endpoints:**

- Risk: API endpoints hardcoded throughout tools, no centralized configuration
- Files: Throughout `src/finwiz/tools/` - each tool has its own endpoint strings
- Current mitigation: None
- Recommendations: Centralize all API endpoints in `config/api_endpoints.py` with environment override support. Add endpoint validation on startup. Support custom endpoints for enterprise/self-hosted services. Version API endpoints to handle breaking changes gracefully.

**Sensitive Data in Logs:**

- Risk: JSON dumps of data structures may include API keys or sensitive portfolio information
- Files: `src/finwiz/infrastructure/logging/enhanced.py:95,102,141,146,192` - extensive json.dumps of context
- Current mitigation: Some sanitization in logging (line 95 mentions "sanitized_inputs")
- Recommendations: Implement comprehensive sanitization for all logged data. Create allowlist of safe fields to log. Mask API keys, account numbers, personal information. Add structured logging with field-level controls. Never log raw API responses.

**CORS Configuration:**

- Risk: CORS_ORIGINS in `.env.example` only shows localhost, production config unclear
- Files: `.env.example:279` - `FINWIZ_CORS_ORIGINS=http://localhost:3000`
- Current mitigation: Environment-based configuration exists
- Recommendations: Document production CORS setup. Implement strict origin validation. Never use wildcard (*) in production. Add pre-flight request logging. Support multiple origins with validation.

## Performance Bottlenecks

**Sequential API Calls in Data Collection:**

- Problem: Data collection makes sequential API calls for each holding instead of batching
- Files: `src/finwiz/analysis/deep_analysis_pipeline.py:collect_raw_data()`, data adapter pattern in `src/finwiz/data/adapters/`
- Cause: No batch API support in adapter interface, each ticker fetched individually
- Improvement path: Implement batch_fetch() in BaseDataAdapter. Use asyncio.gather() for concurrent fetches. Respect rate limits with semaphore. Pre-fetch common data (market indices, sector averages) once. Already partially implemented in `batch_data_prefetcher.py` - expand coverage.

**Synchronous Rate Limiting:**

- Problem: 14+ asyncio.sleep() calls for rate limiting block entire async event loop
- Files: `src/finwiz/infrastructure/caching/manager.py:135`, `src/finwiz/infrastructure/resilience/rate_limiter.py:219,269,429`, `src/finwiz/integration/batch_data_prefetcher.py:464`, `src/finwiz/tools/portfolio_price_service.py:254,309`, `src/finwiz/quantitative/portfolio_monitor.py:247,257,267`
- Cause: Simple sleep-based rate limiting instead of token bucket or sliding window
- Improvement path: Implement token bucket rate limiter (leaky bucket algorithm). Use per-API quotas with separate buckets. Track rate limits dynamically from API headers. Allow burst capacity for batch operations. Consider aiometer or aiolimiter libraries.

**Large Files (600+ lines) with Mixed Concerns:**

- Problem: 7 files exceed 600 lines, indicating complex modules with multiple responsibilities
- Files: `deep_analysis_pipeline.py` (784), `reporting_orchestrator.py` (723), `portfolio_holdings_html_generator.py` (617), `perplexity_analysis_integration.py` (617), `standardized_sentiment_tool.py` (612), `notification_service.py` (610), `portfolio_review_orchestrator.py` (601)
- Cause: Gradual accumulation of features, insufficient refactoring, unclear boundaries
- Improvement path: Extract classes/functions into focused modules. Apply Single Responsibility Principle strictly. Use composition over inheritance. Create sub-packages for complex domains. Target 150-250 lines per file as optimal.

**Cache Cleanup Blocking:**

- Problem: Cache cleanup runs synchronously with 3600s (1 hour) sleep, blocking cleanup of stale data
- Files: `src/finwiz/infrastructure/caching/manager.py:135` - `await asyncio.sleep(self.config.cleanup_interval)`
- Cause: Simple periodic cleanup instead of event-driven
- Improvement path: Use background task scheduler (APScheduler). Implement LRU/LFU eviction on memory pressure. Add TTL-based automatic expiry. Make cleanup incremental (batch of N items per cycle). Monitor cache hit rate and adjust policy dynamically.

**Crew Execution Without Timeouts:**

- Problem: Individual crew executions may hang indefinitely if LLM API stalls
- Files: `src/finwiz/crew_factory.py:57` - `crypto_crew.crew().kickoff(inputs=inputs)` has no timeout wrapper
- Cause: Timeouts configured at flow level but not enforced per-crew
- Improvement path: Wrap all crew.kickoff() with asyncio.wait_for(). Use FINWIZ_HOLDING_TIMEOUT per holding. Add circuit breaker for repeatedly failing crews. Log timeout occurrences for monitoring. Allow graceful degradation on timeout.

## Fragile Areas

**CrewAI Version Coupling:**

- Files: All crew implementations in `src/finwiz/crews/`
- Why fragile: Tight coupling to CrewAI framework, breaking changes in CrewAI updates affect entire codebase
- Test coverage: Limited integration tests for crew execution paths
- Safe modification: Pin CrewAI version strictly in pyproject.toml. Test all crews after any CrewAI upgrade. Use feature flags for new CrewAI features. Abstract crew execution behind facade to isolate framework changes. Maintain compatibility layer for version transitions.

**Pydantic Schema Evolution:**

- Files: All schemas in `src/finwiz/schemas/` - 30+ Pydantic models
- Why fragile: Schema changes break stored JSON data, no migration strategy for field additions/removals
- Test coverage: Schema validation tests exist but no migration tests
- Safe modification: Never remove required fields (add Optional instead). Use Field(default=...) for new fields. Version schemas explicitly (v1, v2). Implement schema migration utilities. Test with old JSON fixtures. Use Pydantic's model_validate() with from_attributes for flexibility.

**HTML Template String Concatenation:**

- Files: `src/finwiz/tools/portfolio_holdings_html_generator.py`, `src/finwiz/reporting/portfolio_review_html.py`
- Why fragile: Manual HTML construction with f-strings risks XSS, breaks on special characters, hard to maintain
- Test coverage: Limited - no HTML validation tests
- Safe modification: Migrate to Jinja2 templates (template infrastructure exists). Escape all user input. Use BeautifulSoup for programmatic HTML generation (already used in some files). Validate HTML output with html5lib. Add snapshot tests for HTML output. Never concatenate raw user data into HTML.

**State Management Across Orchestrators:**

- Files: `src/finwiz/flows/orchestrator.py`, all orchestrator files in `src/finwiz/orchestrators/`
- Why fragile: State (FinwizState) mutated by multiple orchestrators, hard to track data flow, race conditions in concurrent execution
- Test coverage: Limited integration tests for state mutations
- Safe modification: Make state immutable where possible. Return new state from orchestrator methods instead of mutating. Use copy-on-write semantics. Add state validation after each phase. Log state transitions. Consider using state machine pattern for workflow phases.

**Feature Flag Dependencies:**

- Files: `src/finwiz/config/features/flags.py`, 30+ feature flag checks throughout codebase
- Why fragile: Untested flag combinations, flags referenced by string literals (typo risk), circular dependencies possible
- Test coverage: Individual flag tests exist but not combination testing
- Safe modification: Use enum for flag names (type-safe). Test all flag combinations with parameterized tests. Document flag dependencies (e.g., "rebalancing requires portfolio_review"). Implement flag validation at startup. Add deprecation warnings for old flags. Use feature flag service for dynamic updates.

**Data Adapter Fallback Chain:**

- Files: `src/finwiz/data/data_source_orchestrator.py:fetch_with_fallback()`, all adapters in `src/finwiz/data/adapters/`
- Why fragile: Fallback order hardcoded, no circuit breaker for failing sources, may retry endlessly
- Test coverage: Limited fallback scenario tests
- Safe modification: Implement circuit breaker per adapter. Track adapter health metrics (success rate, latency). Make fallback order configurable. Add max retries across all sources. Log which adapter succeeded for debugging. Allow adapter priority override per ticker/asset class. Test failure scenarios explicitly.

## Scaling Limits

**LLM Token Limits:**

- Current capacity: Grok-4.1-fast (2M context), Gemini-3-flash (1M context), but portfolio context grows O(n) with holdings
- Limit: ~500 holdings before context overflow (estimated based on 2000 tokens per holding)
- Scaling path: Implement chunking strategy for large portfolios. Process holdings in batches. Use MapReduce pattern for aggregation. Store intermediate results. Switch to streaming LLM APIs for incremental processing. Consider separate analysis per holding group.

**Concurrent Crew Execution:**

- Current capacity: FINWIZ_DEEP_ANALYSIS_PARALLEL_LIMIT=2 (very conservative)
- Limit: Rate limits from external APIs (Alpha Vantage: 5/min free tier, OpenAI: varies by tier)
- Scaling path: Increase parallelism with paid API tiers. Implement intelligent scheduling (priority queue). Use batch APIs where available. Cache aggressively to reduce API calls. Consider rate limit pooling across multiple API keys.

**In-Memory Caching:**

- Current capacity: CACHE_MAX_MEMORY_ITEMS=10000 items
- Limit: Estimated ~500MB-1GB memory usage at capacity, no automatic eviction on memory pressure
- Scaling path: Implement tiered caching (memory → Redis → disk). Add memory pressure monitoring. Use LRU eviction. Compress cached data. Store only essential fields. Consider distributed cache for multi-instance deployment.

**File-Based Storage:**

- Current capacity: All crew exports, enriched analysis, and reports stored as individual JSON/HTML files
- Limit: Filesystem limits (~1M files per directory on ext4), slow iteration over 10k+ files
- Scaling path: Migrate to database (SQLite for single-user, PostgreSQL for production). Use blob storage (S3) for large reports. Implement data retention policy. Add archival strategy for old analyses. Use partitioning by date/asset_class. Index by ticker for fast lookup.

## Dependencies at Risk

**CrewAI (crewai):**

- Risk: Young framework (frequent breaking changes), not production-battle-tested, limited enterprise support
- Impact: Core functionality - entire application unusable if CrewAI breaks
- Migration plan: Abstract crew execution behind adapter pattern. Maintain compatibility layer. Consider LangChain migration path (more mature). Contribute to CrewAI to influence stability. Pin version strictly and test upgrades thoroughly.

**yfinance (unofficial Yahoo Finance API):**

- Risk: Unofficial API, Yahoo may change response format or block access without notice
- Impact: Primary data source - blocks 80% of analysis if it fails
- Migration plan: Already has fallback chain (Alpha Vantage, Tiingo, EOD). Prioritize moving to official APIs. Implement aggressive caching. Monitor API health. Add alerts for API changes. Consider Bloomberg/Refinitiv for enterprise use.

**OpenRouter (LLM proxy):**

- Risk: Single point of failure for all LLM calls, pricing changes, service outages
- Impact: All AI analysis stops without LLM access
- Migration plan: Support multiple LLM providers (already configured: OpenAI direct, Anthropic direct). Implement automatic fallback to backup provider. Use LiteLLM abstraction (already in use). Cache LLM responses aggressively. Consider self-hosted models for fallback.

**Backtrader (backtesting library):**

- Risk: Maintenance mode (low activity), Python 3.12 compatibility issues
- Impact: Quantitative backtesting features broken on newer Python
- Migration plan: Fork and maintain if needed. Evaluate vectorbt or backtesting.py alternatives. Migrate to pandas_ta + custom backtest logic. Most analysis doesn't require full backtest framework.

## Missing Critical Features

**Comprehensive Error Recovery:**

- Problem: Partial error handling exists but no system-wide recovery strategy
- Blocks: Production deployment - unhandled errors crash entire analysis
- Priority: High - implement error boundaries at orchestrator level, store partial results, allow resume from checkpoint

**Multi-User Support:**

- Problem: Single-user design with global state and file-based storage
- Blocks: SaaS deployment, concurrent user sessions
- Priority: Medium - add user context to all operations, implement proper database, add authentication/authorization

**Real-Time Data Updates:**

- Problem: All data is snapshot-based, no streaming or real-time updates
- Blocks: Live trading features, real-time alerts, monitoring
- Priority: Low - implement WebSocket data feeds, incremental analysis updates, event-driven architecture for alerts

**Internationalization (i18n):**

- Problem: Hardcoded French strings throughout, no i18n framework
- Blocks: English/other language support
- Priority: Low - already has TARGETLANG=fr env var but not fully implemented. Use gettext or fluent for proper i18n.

## Test Coverage Gaps

**Orchestrator Integration Tests:**

- What's not tested: End-to-end orchestrator workflows with real state mutations, concurrent execution, error propagation
- Files: `src/finwiz/orchestrators/` - minimal integration tests
- Risk: Orchestrator changes may break flow execution undetected
- Priority: High - add integration tests for each orchestrator with real FinwizState, test failure scenarios, validate state transitions

**Crew Output Parsing:**

- What's not tested: CrewAI output format variations, malformed JSON from LLMs, schema validation failures
- Files: `src/finwiz/crew_factory.py`, all crew implementations
- Risk: Production failures when LLM returns unexpected format
- Priority: High - add property-based tests with hypothesis, test all Pydantic schemas with invalid data, mock various CrewAI output formats

**Feature Flag Combinations:**

- What's not tested: Interactions between feature flags (30+ flags, 2^30 combinations)
- Files: `src/finwiz/config/features/flags.py`
- Risk: Untested flag combinations may cause runtime errors or inconsistent behavior
- Priority: Medium - identify critical flag dependencies, test common combinations, add validation for incompatible flags

**Data Adapter Fallbacks:**

- What's not tested: Complete adapter failure scenarios, fallback chain exhaustion, partial data degradation
- Files: `src/finwiz/data/data_source_orchestrator.py`, `src/finwiz/data/adapters/`
- Risk: Unknown behavior when all data sources fail
- Priority: High - mock adapter failures systematically, test fallback order, validate graceful degradation

**HTML Output Validation:**

- What's not tested: Generated HTML validity, XSS prevention, character encoding, rendering across browsers
- Files: `src/finwiz/reporting/`, `src/finwiz/tools/portfolio_holdings_html_generator.py`
- Risk: Broken reports, security vulnerabilities, rendering issues
- Priority: Medium - validate HTML with html5lib, test XSS scenarios, add snapshot tests for visual regression

**Performance Regression:**

- What's not tested: Execution time, memory usage, API call counts over time
- Files: Entire codebase - no performance benchmarks
- Risk: Gradual performance degradation undetected
- Priority: Medium - add pytest-benchmark tests, track metrics in CI, set performance budgets (30s per holding), monitor LLM costs

---

*Concerns audit: 2026-02-07*
