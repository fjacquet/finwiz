# Implementation Plan - FinWiz Codebase Modernization

**Last Updated**: 2025-01-18

## Overview

This plan focuses on completing the remaining modernization work for the FinWiz codebase.

**Current Status**:

- ✅ Phases 1, 2, 2A, 2B, 2C, 5 - **COMPLETE**
- ⏳ Phase 3 - **IN PROGRESS** (5/22 files split)
- ❌ Phase 4 - **NOT STARTED** (20 files to split)
- ❌ Phase 6 - **NOT STARTED** (Test failure resolution)
- ❌ Phase 7 - **NOT STARTED** (Final validation)

**Key Metrics**:

- Test Pass Rate: 82.2% (2,614/3,181 tests passing)
- Test Failures: 569 failures to fix
- Files >600 lines: 17 remaining (started with 27)
- Files >500 lines: 20 remaining
- Files >400 lines: 27 remaining

---

## Phase 3: Split Large Files (>600 lines) - IN PROGRESS

**Status**: 5 of 22 files complete

- [ ] 3. Split large files exceeding 600 lines
  - [x] 3.1 Split main.py (764 lines) ✓
  - [x] 3.2 Split integration/manager.py (722 lines) ✓
  - [x] 3.3 Split integration/validation_error_recovery.py (704 lines) ✓
  - [x] 3.4 Split quantitative/optimization.py (689 lines) ✓
  - [x] 3.5 Split integration/log_config.py (671 lines) ✓

  - [x] 3.6 Split quantitative/config.py (670 lines)
    - Extract validators to quantitative/config_validators.py
    - Extract builders to quantitative/config_builders.py
    - Extract defaults to quantitative/config_defaults.py
    - Run config tests after split
    - _Requirements: 1_

  - [x] 3.7 Split quantitative/cost_analyzer.py (663 lines)
    - Extract cost calculators to quantitative/cost_calculators.py
    - Extract analysis logic to quantitative/cost_analysis.py
    - Run cost analysis tests after split
    - _Requirements: 1_

  - [x] 3.8 Split integration/health_checker.py (653 lines)
    - Extract health checks to integration/health_checks.py
    - Extract monitoring to integration/health_monitoring.py
    - Run health check tests after split
    - _Requirements: 1_

  - [x] 3.9 Split tools/a_plus_scoring_tool.py (649 lines)
    - Extract scoring algorithms to tools/scoring/scoring_algorithms.py
    - Extract criteria evaluators to tools/scoring/scoring_criteria.py
    - Run scoring tests after split
    - _Requirements: 1_

  - [x] 3.10 Split orchestrators/portfolio_review.py (645 lines)
    - Extract review logic to orchestrators/review_engine.py
    - Extract decision makers to orchestrators/review_decisions.py
    - Run portfolio review tests after split
    - _Requirements: 1_

  - [x] 3.11 Split tools/rebalancing_templates.py (641 lines)
    - Extract template builders to tools/rebalancing/template_builders.py
    - Extract template renderers to tools/rebalancing/template_renderers.py
    - Run rebalancing tests after split
    - _Requirements: 1_

  - [x] 3.12 Split tools/sentiment_analyzer.py (639 lines)
    - Extract sentiment calculators to tools/sentiment/sentiment_calculators.py
    - Extract aggregators to tools/sentiment/sentiment_aggregators.py
    - Run sentiment tests after split
    - _Requirements: 1_

  - [x] 3.13 Split quantitative/derivatives.py (637 lines)
    - Extract pricing models to quantitative/derivative_pricing.py
    - Extract risk calculations to quantitative/derivative_risk.py
    - Run derivatives tests after split
    - _Requirements: 1_

    - [x] 3.14 Split quantitativeortfolio_monitor.py (631 lines)
    - Extract monitoring logic to quantitative/monitoring_engine.py
    - Extract alert generation to quantitative/monitoring_alerts.py
    - Run portfolio monitor tests after split
    - _Requirements: 1_

  - [x] 3.15 Split tools/html_report_generator.py (629 lines)
    - Extract report sections to tools/reporting/report_sections.py
    - Extract formatting logic to tools/reporting/report_formatters.py
    - Run report generator tests after split
    - _Requirements: 1_

  - [x] 3.16 Split utils/session_persistence.py (625 lines)
    - Extract persistence strategies to utils/persistence_strategies.py
    - Extract session storage to utils/session_storage.py
    - Run session tests after split
    - _Requirements: 1_

  - [x] 3.17 Split integration/aplus_extractor.py (616 lines)
    - Extract extraction logic to integration/extraction_engine.py
    - Extract data parsers to integration/extraction_parsers.py
    - Run extraction tests after split
    - _Requirements: 1_

  - [x] 3.18 Split quantitative/risk_manager.py (615 lines)
    - Extract risk calculations to quantitative/risk_calculations.py
    - Extract risk metrics to quantitative/risk_metrics.py
    - Run risk manager tests after split
    - _Requirements: 1_

  - [x] 3.19 Split tools/holding_analyzer_orchestrator.py (607 lines)
    - Extract analysis coordination to tools/analysis/analysis_coordinator.py
    - Extract holding processors to tools/analysis/holding_processors.py
    - Run holding analyzer tests after split
    - _Requirements: 1_

  - [x] 3.20 Split tools/enhanced_etf_tool.py (607 lines)
    - Extract ETF data fetchers to tools/etf/etf_data_fetchers.py
    - Extract ETF analyzers to tools/etf/etf_analyzers.py
    - Run ETF tool tests after split
    - _Requirements: 1_

  - [x] 3.21 Split utils/feature_flags.py (605 lines)
    - Extract flag definitions to utils/flags/flag_definitions.py
    - Extract flag evaluators to utils/flags/flag_evaluators.py
    - Run feature flag tests after split
    - _Requirements: 1_

  - [x] 3.22 Verify Phase 3 completion
    - Run: `find src/finwiz -name "*.py" -exec wc -l {} + | awk '$1 > 600' | wc -l` (expect: 0)
    - Run full test suite: `uv run pytest`
    - Run linting: `ruff check . && ruff format .`
    - **Phase 3 Complete: All files >600 lines split ✓**
    - _Requirements: 1_1_

---

## Phase 4: Split Medium Files (500-600 lines)

**Status**: 0 of 20 files complete

- [ ] 4. Split medium files (500-600 lines)

  - [ ] 4.1 Split quantitative/screening.py (600 lines)
    - Extract screening criteria to quantitative/screening_criteria.py
    - Extract screening filters to quantitative/screening_filters.py
    - _Requirements: 1_

  - [ ] 4.2 Split crews/report_crew/report_crew.py (594 lines)
    - Extract agent definitions if needed (maintain @CrewBase patterns)
    - Keep YAML configs in config/ directory
    - _Requirements: 1, 2_

  - [ ] 4.3 Split tools/chart_analyzer.py (588 lines)
    - Extract chart generation to tools/charts/chart_generator.py
    - Extract chart analysis to tools/charts/chart_analysis.py
    - _Requirements: 1_

  - [ ] 4.4 Split tools/twelve_data_transformers.py (584 lines)
    - Extract data transformers to tools/twelve_data/transformers.py
    - Extract data validators to tools/twelve_data/validators.py
    - _Requirements: 1_

  - [ ] 4.5 Split tools/enhanced_crypto_tool.py (583 lines)
    - Extract crypto data fetchers to tools/crypto/crypto_data_fetchers.py
    - Extract crypto analyzers to tools/crypto/crypto_analyzers.py
    - _Requirements: 1_

  - [ ] 4.6 Split integration/storage.py (583 lines)
    - Extract storage backends to integration/storage_backends.py
    - Extract storage operations to integration/storage_operations.py
    - _Requirements: 1_

  - [ ] 4.7 Split tools/backtesting_tool.py (581 lines)
    - Extract backtesting strategies to tools/backtesting/strategies.py
    - Extract backtesting metrics to tools/backtesting/metrics.py
    - _Requirements: 1_

  - [ ] 4.8 Split quantitative/rebalancing_history_tracker.py (580 lines)
    - Extract history storage to quantitative/rebalancing_history_storage.py
    - Extract history analysis to quantitative/rebalancing_history_analysis.py
    - _Requirements: 1_

  - [ ] 4.9 Split integration/sec_citation_validator.py (572 lines)
    - Extract citation validators to integration/citation_validators.py
    - Extract citation parsers to integration/citation_parsers.py
    - _Requirements: 1_

  - [ ] 4.10 Split tools/perplexity_analysis_integration.py (570 lines)
    - Extract Perplexity client to tools/perplexity/perplexity_client.py
    - Extract analysis logic to tools/perplexity/perplexity_analyzer.py
    - _Requirements: 1_

  - [ ] 4.11 Split integration/missing_data_handler.py (566 lines)
    - Extract data recovery strategies
    - Extract fallback handlers
    - _Requirements: 1_

  - [ ] 4.12 Split integration/validation_scripts.py (560 lines)
    - Extract validation rules
    - Extract validation executors
    - _Requirements: 1_

  - [ ] 4.13 Split utils/cache_manager.py (556 lines)
    - Extract cache strategies
    - Extract cache storage
    - _Requirements: 1_

  - [ ] 4.14 Split tools/screening_utils.py (555 lines)
    - Extract screening helpers
    - Extract screening formatters
    - _Requirements: 1_

  - [ ] 4.15 Split integration/middleware.py (544 lines)
    - Extract middleware components
    - Extract middleware handlers
    - _Requirements: 1_

  - [ ] 4.16 Split tools/standardized_sentiment_tool.py (536 lines)
    - Extract sentiment analyzers
    - Extract sentiment aggregators
    - _Requirements: 1_

  - [ ] 4.17 Split tools/risk_assessment_tool.py (536 lines)
    - Extract risk calculators
    - Extract risk evaluators
    - _Requirements: 1_

  - [ ] 4.18 Split tools/notification_service.py (530 lines)
    - Extract notification builders
    - Extract notification senders
    - _Requirements: 1_

  - [ ] 4.19 Split quantitative/portfolio_analyzer.py (526 lines)
    - Extract analysis engines
    - Extract metric calculators
    - _Requirements: 1_

  - [ ] 4.20 Split tools/enhanced_sec_tool.py (507 lines)
    - Extract SEC data fetchers
    - Extract SEC analyzers
    - _Requirements: 1_

  - [ ] 4.21 Verify Phase 4 completion
    - Run: `find src/finwiz -name "*.py" -exec wc -l {} + | awk '$1 > 500' | wc -l` (expect: <10)
    - Run full test suite: `uv run pytest`
    - Run linting: `ruff check . && ruff format .`
    - **Phase 4 Complete: Most files >500 lines split ✓**
    - _Requirements: 1_

---

## Phase 6: Test Failure Resolution (569 failures)

**Status**: Based on TEST_FAILURE_REPORT.md - 0 of 569 failures fixed

- [ ] 6. Test Failure Resolution

  - [ ] 6.1 Fix

    - [ ] 6.1.1 Fix Flow state management (45 failures)
      - Replace `self.inputs` with `self.state` in all flow tests
      - Update test fixtures to use Pydantic state models
      - Use structured state access: `flow.state.field_name`
      - Files: `test_*_flow.py`, `test_metrics_export.py`, `test_progress_tracking.py`
      - _Requirements: 3_

    - [ ] 6.1.2 Fix core schema validation (50 failures)
      - Update `RebalancingNeed`, `PortfolioMetrics`, `DeepAnalysisResult` schemas
      - Add missing required fields to test fixtures
      - Rename fields to match new schemas (e.g., `estimated_cost` → `total_estimated_cost`)
      - Files: `test_portfolio_*.py`, `test_deep_analysis_scorer.py`
      - _Requirements: 3_
  
  - [ ] 6.2 Fix

    - [ ] 6.2.1 Refactor crew tests (33 failures)
      - Remove crew execution tests (`crew.kickoff()`)
      - Focus on configuration loading and tool routing
      - Test method existence, not execution
      - Follow `crewai-testing-standards.md` patterns
      - Files: `test_*_crew.py`
      - _Requirements: 2, 3_

    - [ ] 6.2.2 Fix tool integration (45 failures)
      - Update tool signatures and return formats
      - Fix import paths for moved modules
      - Update assertions to match new return formats
      - Files: `test_enhanced_*.py`, `test_market_screening_tool.py`
      - _Requirements: 3_

    - [ ] 6.2.3 Fix remaining schema issues (124 failures)
      - Update all remaining schema validations
      - Fix field name changes across all schemas
      - Add missing fields to test fixtures
      - Files: Various schema-related tests
      - _Requirements: 3_

  - [ ] 6.4 Fix

    - [ ] 6.4.1 Fix enum/constant changes (20 failures)
      - Update enum references to match new definitions
      - Convert string comparisons to enum comparisons
      - Add missing fields to test fixtures
      - Files: `test_portfolio_configuration_manager.py`, `test_scenario_analyzer.py`
      - _Requirements: 3_

    - [ ] 6.4.2 Fix async/coroutine issues (15 failures)
      - Add `async`/`await` to test functions
      - Use `pytest.mark.asyncio` decorator
      - Properly await coroutine results before assertions
      - Files: `test_portfolio_holdings_grading.py`, `test_portfolio_review.py`
      - _Requirements: 3_

    - [ ] 6.4.3 Fix Supabase issues (15 failures)
      - Update mock client to include all required attributes
      - Add `timeout` and `max_retries` to mock configurations
      - Match new client initialization patterns
      - Files: `test_client.py`, `test_*_repository.py`
      - _Requirements: 3_

  - [ ] 6.5 Fix

    - [ ] 6.5.1 Run full test suite validation
      - Run: `uv run pytest`
      - Verify pass rate >95% (target: 3,020+ of 3,181 tests)
      - Ensure test execution time <3 minutes
      - Check coverage improved to 65%+ (current: 57.84%)
      - Document remaining failures with justification
      - **Phase 6 Complete: Test suite restored to health ✓**
      - _Requirements: 3_

- [ ] 7. Fix

  - [ ] 7.1 Complete test suite validation
    - Run full test suite: `uv run pytest`
    - Verify all pytest-mock conversions work correctly
    - Ensure no unittest.mock imports remain: `grep -r "unittest.mock" . --exclude-dir=.git`
    - Validate test performance (< 5 seconds per suite)
    - Check test coverage is maintained or improved (target: 65%+)
    - _Requirements: 3_

  - [ ] 7.2 Code quality and standards validation
    - Run complete linting: `ruff check . && ruff format .`
    - Ensure no ruff complaints remain
    - Confirm all target files are under 400 lines: `find src/finwiz -name "*.py" -exec wc -l {} + | awk '$1 > 400' | wc -l`
    - Verify no functionality regressions with integration tests
    - Test all CrewAI crews function correctly
    - _Requirements: 1, 2_

  - [ ] 7.3 Final documentation and cleanup
    - Update development guidelines with new patterns
    - Document new file organization structure
    - Create examples of proper pytest-mock usage
    - Remove any unused imports or dead code
    - Verify all files have proper docstrings and type hints
    - _Requirements: 1, 2, 3_

  - [ ] 7.4 Performance and functionality validation (smoke tests)
    - Test application starts without errors: `uv run python src/finwiz/main.py --help`
    - Run existing integration tests: `uv run pytest tests/integration/ -v`
    - Verify no regressions in core functionality
    - Test sample crew executions (stock, ETF, crypto)
    - _Requirements: 1, 2, 3, 4_

  - [ ] 7.5 Final completion audit
    - Run all verification commands from design document
    - Verify 0 files >600 lines
    - Verify <30 files >400 lines
    - Verify 0% unittest.mock usage
    - Verify 100% CrewAI decorator compliance
    - Verify 0% HTML string concatenation
    - Generate final completion report
    - **Phase 7 Complete: Full modernization achieved ✓**
    - _Requirements: 1, 2, 3, 4_

---

## Completed Phases (Archive)

### ✅ Phase 1: Testing Modernization - COMPLETE

- All 61 test files converted from unittest.mock to pytest-mock
- unittest.mock enforcement mechanisms installed (4 layers)
- Integration and performance tests fully converted

### ✅ Phase 2: HTML Generation Migration - COMPLETE

- beautifulsoup4 dependency added
- All 6 HTML generation files migrated to bs4
- No HTML string concatenation remaining

### ✅ Phase 2A: High-Priority Refactoring - COMPLETE

- DeepAnalysisScorer split from 1,301 to ~400 lines
- Strategy pattern implemented for asset-specific logic
- Scoring thresholds extracted to configuration
- APlusExtractor duplicate code eliminated
- Template method pattern applied

### ✅ Phase 2B: Medium-Priority Refactoring - COMPLETE

- Long methods broken down
- Repeated scoring patterns extracted
- Base class created for async feedback tools
- Error handling standardized
- Nested conditionals extracted to guard clauses

### ✅ Phase 2C: Low-Priority Improvements - COMPLETE

- Timezone handling improved
- Regex patterns extracted to constants
- Missing type hints added

### ✅ Phase 5: CrewAI Compliance - COMPLETE

- All 6 crews verified to use @CrewBase decorator
- All crews have YAML configuration files
- Tool injection patterns verified

---

## Success Metrics

**Target**: 100% Completion Across All Areas

- **File Decomposition**: 0 files >600 lines, <30 files >400 lines
- **Testing Modernization**: 0% unittest.mock usage, 100% pytest-mock ✓
- **Test Health**: >95% pass rate, 65%+ coverage
- **CrewAI Compliance**: 100% decorator patterns ✓
- **HTML Security**: 100% bs4 usage ✓

**Current Progress**:

- File Decomposition: ~23% complete (5/22 files >600 lines split)
- Test Health: 82.2% pass rate (need to fix 569 failures)
- Overall: ~60% complete

---

## Quick Commands

```bash
# Check file sizes
find src/finwiz -name "*.py" -exec wc -l {} + | awk '$1 > 600' | wc -l
find src/finwiz -name "*.py" -exec wc -l {} + | awk '$1 > 400' | wc -l

# Run tests
uv run pytest
uv run pytest --cov=src/finwiz --cov-report=html

# Check code quality
ruff check . && ruff format .
make check-unittest-mock

# Verify no HTML string concatenation
grep -r "f\"<\|\"<.*>\".*+\|'<.*>'.*+" src/finwiz --include="*.py" | wc -l
```
