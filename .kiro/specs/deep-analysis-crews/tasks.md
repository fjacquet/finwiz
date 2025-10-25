# Implementation Plan: Unified Deep Analysis Crew

## Overview

This implementation plan creates ONE unified deep analysis crew (`DeepAnalysisCrew`) that handles all asset classes (Stock, ETF, Crypto) through dynamic tool routing. This eliminates code duplication and provides a single source of truth for deep analysis logic.

**Benefits:**

- No code duplication across asset classes
- Single crew to maintain and test
- Dynamic tool selection based on asset_class parameter
- Clean separation: discovery crews vs deep analysis crew

**Current Status:**

- ✅ Tool factories exist (`get_stock_crew_tools`, `get_etf_crew_tools`, `get_crypto_crew_tools`)
- ✅ `DeepAnalysisResult` schema exists in `flow_state.py`
- ✅ `@final_reporter` decorator exists in `agent_validators.py`
- ✅ Flow orchestrator has `analyze_holdings_deep()` method with direct crew instantiation pattern
- ❌ No deep analysis crew implementations exist yet
- ❌ Flow sequence is incorrect (discovery BEFORE portfolio analysis)
- ❌ Flow methods are not consolidated (3 separate methods instead of 1 atomic operation)

**Critical Implementation Note:**

Task 3 MUST be completed before Task 4. Task 3 creates the `analyze_and_update_portfolio()` method, and Task 4 updates the `@listen` decorators to reference it. Attempting Task 4 before Task 3 will result in broken flow execution.

## Task List

- [x] 1. Create DeepAnalysisCrew structure and configuration
  - Create directory structure `src/finwiz/crews/deep_analysis/`
  - Create `config/agents.yaml` with 3 agents (asset_analyst, risk_assessor, investment_reporter)
  - Create `config/tasks.yaml` with 4 tasks (deep_analysis, technical_analysis, risk_assessment, final_report)
  - Ensure task descriptions explicitly state "SINGLE TICKER MODE" and "analyze the provided ticker: {ticker}"
  - Task descriptions should adapt based on {asset_class} parameter using template variables
  - Final reporter agent MUST have empty tools list (`tools=[]`)
  - _Requirements: 1.1-1.5, 9.1-9.7, 10.1-10.2_

- [x] 1.1 Implement DeepAnalysisCrew Python class with dynamic tool routing
  - Create `deep_analysis.py` with `@CrewBase` decorator following existing crew pattern
  - Implement `__init__` to load agent and task configs from YAML files
  - Implement `get_tools_for_asset_class(asset_class)` method for dynamic tool routing
  - Implement 3 agents with `@agent` decorator (asset_analyst, risk_assessor, investment_reporter)
  - Use `@final_reporter` decorator on investment_reporter to enforce empty tools
  - Implement 4 tasks with `@task` decorator (async for first 3, sync for final)
  - Implement `@crew` method with sequential process, max_rpm=20, respect_context_window=True
  - Enable `reasoning=True` on all agents and tasks
  - Use `get_configured_llm()` for LLM configuration
  - _Requirements: 5.1-5.6, 9.1-9.7_

- [x] 1.2 Implement dynamic tool routing logic
  - Create `get_tools_for_asset_class(asset_class)` method in DeepAnalysisCrew class
  - Route to `get_stock_crew_tools(include_rag=True, include_quantitative=True, collection_suffix="stock_deep")` when asset_class="stock"
  - Route to `get_etf_crew_tools(include_rag=True, include_quantitative=True, collection_suffix="etf_deep")` when asset_class="etf"
  - Route to `get_crypto_crew_tools(include_rag=True, include_quantitative=True, collection_suffix="crypto_deep")` when asset_class="crypto"
  - Raise ValueError with clear message for invalid asset_class
  - Apply `make_tools_robust()` wrapper to tools for error handling
  - _Requirements: 6.1-6.4, 11.1-11.5_

- [x] 1.3 Update crew to dynamically assign tools based on kickoff inputs
  - Modify `@crew` method to accept asset_class from kickoff inputs
  - Dynamically call `get_tools_for_asset_class()` and assign tools to agents before execution
  - Ensure tools are assigned to asset_analyst and risk_assessor agents
  - Ensure investment_reporter has empty tools list (enforced by @final_reporter)
  - _Requirements: 6.1-6.4, 9.8_

- [x] 1.4 Write unit tests for DeepAnalysisCrew
  - Create `tests/unit/crews/test_deep_analysis_crew.py`
  - Test `get_tools_for_asset_class()` returns correct tools for each asset_class (stock, etf, crypto)
  - Test ValueError raised for invalid asset_class
  - Test crew class instantiation succeeds without errors
  - Test YAML configuration files load correctly (agents.yaml, tasks.yaml)
  - Test investment_reporter agent config has empty tools list in YAML
  - Test tool routing returns expected tool types (e.g., EnhancedSECAnalysisTool for stock)
  - Mock all external dependencies using pytest-mock (never unittest.mock)
  - DO NOT test agent behavior, LLM calls, or crew execution (not testable)
  - _Requirements: 1.1-1.5, 5.1-5.6_

- [x] 2. Update Flow Orchestrator routing
  - Update `src/finwiz/flows/flow_orchestrator.py` in `analyze_holdings_deep()` method
  - Import DeepAnalysisCrew: `from finwiz.crews.deep_analysis.deep_analysis import DeepAnalysisCrew`
  - Replace asset_class-based if/elif routing with unified crew instantiation: `crew = DeepAnalysisCrew()`
  - Pass both ticker AND asset_class in inputs: `{"ticker": ticker, "asset_class": asset_class, ...}`
  - Keep existing `_parse_crew_output_for_holding()` method integration (no changes needed)
  - Keep existing cache manager integration (no changes needed)
  - _Requirements: 4.1-4.7_

- [x] 3. Consolidate Flow methods into single atomic operation
  - Rename `analyze_holdings_deep()` to `analyze_and_update_portfolio()` in `src/finwiz/flows/flow_orchestrator.py`
  - Update `@listen` decorator from `"check_portfolio"` to `"check_portfolio"` (no change, but verify)
  - Extract helper method `_run_deep_analysis_on_holdings()` containing deep analysis logic from current method
  - Extract helper method `_match_alternatives_for_holdings(deep_results)` containing alternative matching logic
  - Extract helper method `_update_portfolio_review_with_enriched_data()` containing portfolio update logic
  - Update `analyze_and_update_portfolio()` to call all three helpers sequentially in one atomic operation
  - Return consolidated results: `{"deep_analysis_complete": True, "analysis_results": ..., "alternatives_data": ..., "portfolio_updated": ...}`
  - Update Flow state: `self.state.deep_analysis_results = deep_results`, `self.state.portfolio_alternatives = alternatives`
  - Remove separate `match_alternatives()` method (logic moved to `_match_alternatives_for_holdings` helper)
  - Remove separate `update_portfolio_review_with_deep_analysis()` method (logic moved to `_update_portfolio_review_with_enriched_data` helper)
  - Update `check_portfolio` to generate initial portfolio review WITHOUT deep analysis (pass `flow_state=None` to portfolio builder)
  - Ensure portfolio review is only regenerated ONCE (in `_update_portfolio_review_with_enriched_data()` helper)
  - Add error handling: wrap each helper in try/except, continue with degraded functionality on failure
  - Add logging: log analysis count, alternatives count, update status at each step
  - _Requirements: 4.1-4.8, 4.17-4.20, 8.1-8.6_

- [x] 4. Correct Flow sequence to match logical business order
  - **CRITICAL:** This task depends on Task 3 completing first (method must exist before updating listeners)
  - Update `@listen` decorator on `check_portfolio` from `and_("check_stock", "check_etf", "check_crypto")` to `"validate_data_integration"`
  - Update `@listen` decorator on `check_crypto` from `"validate_data_integration"` to `"analyze_and_update_portfolio"`
  - Update `@listen` decorator on `check_stock` from `"validate_data_integration"` to `"analyze_and_update_portfolio"`
  - Update `@listen` decorator on `check_etf` from `"validate_data_integration"` to `"analyze_and_update_portfolio"`
  - Update `@listen` decorator on `check_investment_discovery` from `and_("match_alternatives", "check_portfolio_rebalancing")` to `and_("check_crypto", "check_stock", "check_etf")`
  - Update `@listen` decorator on `check_portfolio_rebalancing` from `and_("check_stock", "check_etf", "check_crypto")` to `"check_investment_discovery"`
  - Verify new flow order: validate → portfolio → analyze_and_update_portfolio → discovery (parallel) → investment_discovery → rebalancing → report
  - Test flow execution to ensure correct sequence (portfolio BEFORE discovery)
  - Update flow diagram in `crewai_flow.html` to reflect corrected 6-phase sequence
  - Add comments in code explaining why this order (analyze what you have → find alternatives → discover new opportunities)
  - _Requirements: 4.9-4.26_

- [x] 5. Integration testing and validation
  - Create `tests/integration/test_flow_sequence.py` for flow orchestrator testing
  - Test flow orchestrator listener decorators are correctly configured (verify @listen parameters)
  - Test flow execution order: validate → portfolio → analyze_and_update_portfolio → discovery → rebalancing → report
  - Test `get_tools_for_asset_class()` integration with tool factories (stock, etf, crypto)
  - Test `_parse_crew_output_for_holding()` correctly extracts scores from mock crew results
  - Test cache manager integration with mock analysis results
  - Test helper methods with mocked dependencies:
    - `_run_deep_analysis_on_holdings()` - Mock DeepAnalysisCrew execution
    - `_match_alternatives_for_holdings()` - Mock AlternativeFinder
    - `_update_portfolio_review_with_enriched_data()` - Mock portfolio builder
  - Verify Flow state updates correctly after each phase (check self.state fields)
  - Test error handling and graceful degradation:
    - Test deep analysis failure continues with empty results
    - Test alternative matching failure continues without alternatives
    - Test portfolio update failure retains original portfolio
  - Test that portfolio review is generated ONCE (not twice)
  - Test that discovery runs AFTER portfolio analysis (not before)
  - Mark tests with `@pytest.mark.integration` decorator
  - Mock all external dependencies (LLMs, APIs, crew executions) using pytest-mock
  - DO NOT test actual crew execution, agent behavior, or LLM calls (not testable)
  - _Requirements: 1.1-1.5, 4.1-4.26, 7.1-7.5, 8.1-8.6, 11.1-11.5_

- [x] 6. Implement API efficiency patterns in DeepAnalysisCrew
  - Update `config/tasks.yaml` to enable parallel execution:
    - Set `async_execution: true` for deep_analysis_task
    - Set `async_execution: true` for technical_analysis_task
    - Set `async_execution: true` for risk_assessment_task
    - Set `async_execution: false` for final_report_task (CrewAI requirement)
  - Implement smart batching in technical_analysis_task:
    - Use `TwelveDataIndicatorTool` with batch parameter for multiple indicators
    - Fetch RSI, MACD, Bollinger Bands in single API call instead of 3 separate calls
    - Example: `indicators = tool.fetch_multiple(ticker, ["RSI", "MACD", "BB"])`
  - Implement context sharing between tasks:
    - deep_analysis_task fetches price data and stores in context with timestamp
    - technical_analysis_task checks context for price data before re-fetching
    - Validate data freshness (max_age_minutes=5) before reusing from context
    - Re-fetch if stale: `if not is_fresh(cached_data["timestamp"], max_age=5): refetch()`
  - Add monitoring logging in crew execution:
    - Log API call count per ticker analysis
    - Log data freshness percentage (fresh vs cached)
    - Log execution time breakdown by task
    - Log optimization opportunities when detected
  - Document acceptable vs unacceptable patterns in code comments:
    - ✅ Acceptable: Batch indicators, share context, parallel I/O
    - ❌ Not acceptable: 24h cached prices, stale sentiment, skipping fetches for cost
  - _Requirements: 7.6-7.10, 11.1-11.20_

- [x] 7. Add clarifying documentation to discovery crews
  - Add header comment to `src/finwiz/crews/stock_crew/config/tasks.yaml`
  - Add header comment to `src/finwiz/crews/etf_crew/config/tasks.yaml`
  - Add header comment to `src/finwiz/crews/crypto_crew/config/tasks.yaml`
  - Comments should state: "# DISCOVERY CREW - Designed to screen and identify top 10 assets"
  - Comments should state: "# For single-ticker deep analysis, use DeepAnalysisCrew instead"
  - Comments should state: "# Runs AFTER portfolio analysis to find NEW opportunities"
  - Update crew docstrings in Python files to clarify discovery-only purpose
  - Verify task descriptions clearly state "top 10" throughout
  - _Requirements: 10.3-10.5_

- [x] 8. Documentation and monitoring
  - Create `docs/DEEP_ANALYSIS_CREW.md` with comprehensive documentation:
    - Usage examples for each asset_class (stock, etf, crypto)
    - Dynamic tool routing logic explanation
    - Input parameters (ticker, asset_class) with examples
    - Output schema (DeepAnalysisResult) with field descriptions
    - Error handling patterns and graceful degradation
    - Performance expectations (<5 minutes per ticker)
  - Document corrected flow sequence with detailed rationale:
    - Phase 1: Validation (check data systems)
    - Phase 2: Portfolio Analysis (analyze what you have)
    - Phase 3: Deep Analysis & Update (grade holdings, match alternatives, update portfolio - ATOMIC)
    - Phase 4: Discovery (find A+ opportunities for identified needs)
    - Phase 5: Rebalancing (optimize with complete data)
    - Phase 6: Reporting (consolidate and present)
    - Explain why portfolio BEFORE discovery (logical business order)
    - Explain why consolidated atomic operation (efficiency, no race conditions)
  - Document API efficiency patterns:
    - Smart batching examples (batch indicator fetches)
    - Context sharing examples (pass data between tasks)
    - Parallel execution configuration (async_execution: true)
    - Monitoring metrics (API calls, freshness, execution time)
  - Add logging for monitoring (implement in crew code):
    - Log data freshness metrics: `logger.info(f"Data freshness: {fresh_count}/{total_count} fresh")`
    - Log API call counts: `logger.info(f"API calls for {ticker}: {api_call_count}")`
    - Log execution time breakdown: `logger.info(f"Task times: deep={t1:.2f}s, technical={t2:.2f}s")`
  - Update `docs/USER_GUIDE.md` with DeepAnalysisCrew usage section
  - Document routing logic: when to use discovery crews vs deep analysis crew
  - Update `crewai_flow.html` diagram to reflect corrected 6-phase sequence
  - Add troubleshooting section for common issues (reasoning loops, stale data, API failures)
  - _Requirements: 4.9-4.26, 7.1-7.15, 8.1-8.6, 11.16-11.20_

- [x] 9. Parallelize portfolio holdings processing for massive performance gains
  - **Problem**: Sequential processing of 66 holdings takes ~66 seconds (1 second each), deep analysis would take hours
  - **Solution**: Use asyncio.gather() to process holdings in parallel
  - Update `src/finwiz/orchestrators/portfolio_holdings_processor.py`:
    - Convert `process_holdings()` to async method
    - Convert `_process_single_holding()` to async method
    - Replace sequential `for` loop with `asyncio.gather(*[_process_single_holding(h) for h in holdings])`
    - Add concurrency limit (e.g., 10 concurrent holdings) to avoid overwhelming APIs
    - Keep progress logging but update to show parallel processing
    - Maintain error handling and graceful degradation per holding
  - Update `src/finwiz/flows/flow_orchestrator.py` in `_run_deep_analysis_on_holdings()`:
    - Convert method to async
    - Replace sequential `for` loop with `asyncio.gather()` for parallel crew execution
    - Add concurrency limit (e.g., 3-5 concurrent deep analyses) to avoid rate limits
    - Keep cache checking logic (check all caches first, then run parallel analysis on non-cached)
    - Maintain progress logging with parallel execution indicators
    - Keep error handling per holding (one failure doesn't stop others)
  - Update callers to use `await` for async methods:
    - `analyze_and_update_portfolio()` method in flow orchestrator
    - Portfolio review orchestrator if it calls processor directly
  - Add configuration via environment variables:
    - `PORTFOLIO_PARALLEL_LIMIT` (default: 10) - max concurrent portfolio holdings
    - `DEEP_ANALYSIS_PARALLEL_LIMIT` (default: 3) - max concurrent deep analyses
  - Add performance logging:
    - Log total time before/after parallelization
    - Log speedup factor (e.g., "66 holdings processed in 2.5s (26x speedup)")
    - Log concurrency stats (e.g., "Processed 10 batches of 6-7 holdings each")
  - Write unit tests for parallel processing:
    - Test concurrent execution with mocked holdings
    - Test concurrency limit enforcement
    - Test error handling (one failure doesn't stop others)
    - Test progress logging with parallel execution
    - Mock asyncio.gather() and verify correct usage
  - **Expected Performance Gains**:
    - Portfolio processing: 66 seconds → ~2-5 seconds (13-33x speedup)
    - Deep analysis (10 holdings): 50-100 minutes → 15-30 minutes (3-4x speedup with limit of 3)
    - Total flow execution: Hours → Minutes
  - _Requirements: Performance optimization, scalability, user experience_

---

## Implementation Strategy

**Phase 1: Create Unified Crew (Tasks 1-2)** ✅ COMPLETE

- Create ONE unified DeepAnalysisCrew that handles all asset classes through dynamic tool routing
- Eliminates code duplication across stock/ETF/crypto implementations
- Integrates with existing flow orchestrator using direct crew instantiation pattern

**Phase 2: Fix Flow Architecture (Tasks 3-4)** 🔄 IN PROGRESS

- **Task 3 (FIRST):** Consolidate 3 separate Flow methods into 1 atomic operation
  - Creates `analyze_and_update_portfolio()` method
  - Eliminates redundant portfolio generation (runs once instead of twice)
  - Provides atomic semantics (all-or-nothing)
- **Task 4 (SECOND):** Correct flow sequence to match logical business order
  - Updates `@listen` decorators to reference new consolidated method
  - Fixes backwards flow (portfolio BEFORE discovery, not after)
  - Implements 6-phase flow: validate → portfolio → deep_analysis → discovery → rebalancing → report

**Phase 3: Optimize & Document (Tasks 5-8)**

- Implement API efficiency patterns (smart batching, context sharing, parallel execution)
- Add comprehensive testing (integration tests with mocked dependencies)
- Document discovery crew purposes (clarify "top 10" vs single-ticker analysis)
- Create comprehensive documentation with flow rationale and troubleshooting

**Critical Dependencies:**

- Task 4 depends on Task 3 (method must exist before updating listeners)
- Task 5 depends on Tasks 3-4 (tests verify corrected flow sequence)
- Task 8 depends on all previous tasks (documents complete implementation)

**Success Criteria:**

- ✅ Single unified crew for all asset classes (no duplication)
- ✅ Correct flow sequence (portfolio → discovery, not discovery → portfolio)
- ✅ Atomic operation (deep analysis + alternatives + update in one method)
- ✅ Portfolio generated ONCE (not twice)
- ✅ API efficiency patterns implemented (batching, context sharing, parallel execution)
- ✅ Comprehensive testing and documentation
