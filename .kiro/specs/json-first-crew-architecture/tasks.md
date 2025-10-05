# Implementation Plan: JSON-First Crew Architecture

## Overview

This implementation plan focuses on migrating crew task outputs from markdown to JSON with Pydantic validation.

**Current Status:**

- ✅ All schemas use modern Python 3.12+ syntax (`Type | None`, `list`, `dict`)
- ✅ All crew schemas exist and are comprehensive
- ✅ Schema registry is complete and up-to-date
- ❌ No crew task configurations use `output_pydantic` yet
- ❌ No JSON error handlers exist
- ❌ No migration documentation exists

**Remaining Work:**

- Phase 1: Task Config

- `[ ]` = Not started
- `[x]` = Completed
- `[ ]*` = Optional testing task

## Phase 1: Task Configuration Updates (Week 1)

All schemas are ready. Now we need to update crew task configurations to use them.

- [x] 1. Update all crew task configurations for JSON output
  - Update task YAML files for all 6 crews to use `output_pydantic` and JSON output
  - **Stock Crew** (`src/finwiz/crews/stock_crew/config/tasks.yaml`):
    - Add `output_pydantic: MarketTrend` to `market_technical_analysis_task`
    - Add `output_pydantic: StockScreeningResult` to `stock_screening_task`
    - Add `output_pydantic: StockTechnicalAnalysis` to `technical_detail_task`
    - Change `output_file` to `.json` extension for intermediate tasks
    - Keep final tasks (risk assessment, translation) as HTML
  - **ETF Crew** (`src/finwiz/crews/etf_crew/config/tasks.yaml`):
    - Add `output_pydantic: ETFMarketTrend` to `etf_market_trends_task`
    - Add `output_pydantic: ETFScreeningResult` to `etf_screening_task`
    - Add `output_pydantic: ETFTechnicalAnalysis` to `etf_technical_detail_task`
    - Change `output_file` to `.json` extension for intermediate tasks
    - Keep final tasks (risk assessment, investment strategy, translation) as HTML
  - **Crypto Crew** (`src/finwiz/crews/crypto_crew/config/tasks.yaml`):
    - Add `output_pydantic: CryptoMarketAnalysis` to `market_analysis_task`
    - Add `output_pydantic: CryptoTechnicalAnalysis` to `technical_analysis_task`
    - Add `output_pydantic: CryptoRiskProfile` to `risk_assessment_task`
    - Add `output_pydantic: CryptoInvestmentStrategy` to `investment_strategy_task`
    - Change `output_file` to `.json` extension for intermediate tasks
    - Keep final tasks (final report, translation) as HTML
  - **Investment Discovery Crew** (`src/finwiz/crews/investment_discovery_crew/config/tasks.yaml`):
    - Add `output_pydantic: APlusDiscoveryResult` to `etf_discovery_task`
    - Add `output_pydantic: APlusDiscoveryResult` to `stock_discovery_task`
    - Add `output_pydantic: APlusDiscoveryResult` to `crypto_discovery_task`
    - Add `output_pydantic: ValidationResult` to `validation_task`
    - Add `output_pydantic: OptimizationResult` to `optimization_task`
    - Change `output_file` to `.json` extension for intermediate tasks
    - Keep final tasks (report generation, feedback learning) as HTML/markdown
  - **Portfolio Rebalancing Crew** (`src/finwiz/crews/portfolio_rebalancing_crew/config/tasks.yaml`):
    - Add `output_pydantic: HoldingDecision` to `analyze_holding_task`
    - Add `output_pydantic: PriceTargets` to `calculate_price_targets_task`
    - Add `output_pydantic: Alternative` to `find_alternatives_task`
    - Add `output_pydantic: PortfolioAnalysis` to `portfolio_analysis_task`
    - Add `output_pydantic: RebalancingRecommendation` to `rebalancing_optimization_task`
    - Change `output_file` to `.json` extension for intermediate tasks
    - Keep final tasks (risk validation, translation) as HTML
  - **Report Crew** (`src/finwiz/crews/report_crew/config/tasks.yaml`):
    - Add `output_pydantic: ReporterInput` to `comprehensive_financial_integration_task`
    - Add `output_pydantic: PortfolioConfiguration` to `optimal_portfolio_allocation_task`
    - Add `output_pydantic: RiskAssessmentStandardized` to `risk_assessment_mitigation_task`
    - Change `output_file` to `.json` extension for intermediate tasks
    - Keep final tasks (comprehensive report, translation) as HTML
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 7.1, 7.2_

## Phase 2: Error Handling & Documentation (Week 2)

- [x] 2. Error Handling & Documentation

- [x] 2.1 Implement JSON error handling utilities
  - Create `src/finwiz/utils/json_error_handlers.py`
  - Implement JSON parsing error handler with file path and line number
  - Implement schema validation error handler with field-level details
  - Add sanitized logging (no sensitive data)
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 9.4_

- [x] 2.2 Create schema documentation
  - Create `docs/schemas/README.md` with overview
  - Document each schema with field descriptions
  - Include JSON examples for each schema
  - Add usage guidelines
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 2.3 Create JSON migration guide
  - Create `docs/JSON_MIGRATION_GUIDE.md`
  - Document migration process step-by-step
  - Include before/after examples
  - Add troubleshooting section
  - Document common validation errors
  - _Requirements: 5.1, 5.2, 5.3, 5.5, 8.3, 8.4_

## Phase 3: Testing & Validation (Week 3)

- [x] 5. Write unit tests for schema validation
  - Create `tests/unit/schemas/test_schema_validation.py`
  - Test each schema with valid data
  - Test each schema with invalid data
  - Test field constraints (min/max, patterns)
  - _Requirements: 2.1, 2.2, 6.2, 6.3, 6.4_

- [ ]* 6. Write CrewAI compatibility tests
  - Create `tests/unit/schemas/test_crewai_compatibility.py`
  - Test each schema with CrewAI's `convert_to_model` function
  - Verify no `AttributeError` from modern union types
  - _Requirements: 9.3, 9.4_

- [ ]* 7. Write unit tests for error handlers
  - Create `tests/unit/utils/test_json_error_handlers.py`
  - Test JSON parsing error handling
  - Test schema validation error handling
  - Verify sanitized logging
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ]* 8. Write integration tests for Stock Crew
  - Create `tests/integration/crews/test_stock_crew_json.py`
  - Test end-to-end execution with JSON outputs
  - Verify schema validation
  - _Requirements: 1.1, 1.2, 4.1, 4.2, 4.4, 7.3_

- [ ]* 9. Write integration tests for ETF Crew
  - Create `tests/integration/crews/test_etf_crew_json.py`
  - Test end-to-end execution with JSON outputs
  - _Requirements: 1.1, 1.2, 4.1, 4.2, 4.4, 7.3_

- [ ]* 10. Write integration tests for Crypto Crew
  - Create `tests/integration/crews/test_crypto_crew_json.py`
  - Test end-to-end execution with JSON outputs
  - _Requirements: 1.1, 1.2, 4.1, 4.2, 4.4, 7.3_

- [ ]* 11. Write integration tests for Investment Discovery Crew
  - Create `tests/integration/crews/test_investment_discovery_crew_json.py`
  - Test all 6 intermediate JSON outputs
  - _Requirements: 1.1, 1.2, 4.1, 4.2, 4.4, 7.3_

- [ ]* 12. Write integration tests for Portfolio Rebalancing Crew
  - Create `tests/integration/crews/test_portfolio_rebalancing_crew_json.py`
  - Test end-to-end execution with JSON outputs
  - _Requirements: 1.1, 1.2, 4.1, 4.2, 4.4, 7.3_

- [ ]* 13. Write integration tests for Report Crew
  - Create `tests/integration/crews/test_report_crew_json.py`
  - Test intermediate JSON outputs and final HTML
  - _Requirements: 1.1, 1.2, 4.1, 4.2, 4.4, 7.1, 7.2, 7.3_

- [ ] 14. Run manual migration tests
  - Execute Stock Crew with test ticker
  - Execute ETF Crew with test ticker
  - Execute Crypto Crew with test symbol
  - Execute Investment Discovery Crew
  - Execute Portfolio Rebalancing Crew with test portfolio
  - Execute Report Crew with test data
  - Verify all JSON outputs validate against schemas
  - Check for validation errors
  - _Requirements: 1.1, 1.2, 4.1, 4.2, 7.1, 7.2, 7.3_

- [ ] 15. Performance benchmarking
  - Create performance test script
  - Benchmark JSON parsing vs markdown parsing
  - Verify ≥2x improvement in parsing speed
  - Document results
  - _Requirements: 1.1, 1.2, 4.1, 4.2_

- [ ] 16. Update main flow orchestration (if needed)
  - Review orchestration code in `src/finwiz/main.py`
  - Update for JSON handling if necessary
  - Ensure context passing works with JSON
  - _Requirements: 4.1, 4.2, 4.4_

- [ ] 17. Final integration testing
  - Run full test suite: `uv run pytest`
  - Execute all crews end-to-end with real data
  - Verify all success criteria met
  - Document any issues
  - _Requirements: 1.1, 1.2, 4.1, 4.2, 4.4, 7.1, 7.2, 7.3_

- [ ] 18. Update project documentation
  - Update README.md with JSON-first architecture
  - Add links to schema documentation
  - Update developer guide
  - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [ ] 19. Production deployment preparation
  - Create deployment checklist
  - Prepare rollback plan
  - Set up monitoring for JSON validation errors
  - Document deployment process
  - _Requirements: 5.1, 5.2, 5.5_

## Success Verification

Before marking the spec as complete, verify:

- [x] ✅ All schemas use modern Python 3.12+ type annotations
- [x] ✅ All crew schemas exist and are comprehensive
- [x] ✅ Schema registry is complete and up-to-date
- [ ] ✅ All intermediate tasks output JSON with Pydantic validation
- [ ] ✅ All JSON outputs pass schema validation
- [ ] ✅ Final reports remain in HTML format
- [ ] ✅ Context passing works between all tasks
- [ ] ✅ Error handlers implemented with sanitized logging
- [ ] ✅ Schema documentation complete with examples
- [ ] ✅ Migration guide created with troubleshooting
- [ ] ✅ All tests pass (unit and integration)
- [ ] ✅ Performance benchmarks meet targets (≥2x faster JSON parsing)
- [ ] ✅ Project documentation updated

## Notes

- Schemas are already using modern Python 3.12+ syntax - no reversion needed
- All crew schemas exist and are properly exported in the registry
- Focus is now on updating task configurations to use `output_pydantic`
- Final tasks (reports, translations) should remain HTML format
- Intermediate tasks should output JSON with schema validation

---

**Version**: 3.0
**Last Updated**: 2025-05-10
**Status**: Refreshed based on current codebase state - schemas complete, task configs pending
