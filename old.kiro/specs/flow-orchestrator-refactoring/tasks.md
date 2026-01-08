# Implementation Plan

## Phase 1: Foundation Setup

- [x] 1. Create orchestrators directory structure
  - Create `src/finwiz/orchestrators/` directory
  - Create `__init__.py` with module exports
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 2. Implement ErrorHandlingOrchestrator
  - Create `src/finwiz/orchestrators/error_handling_orchestrator.py`
  - Implement `execute_crew_with_error_handling()` method
  - Implement `generate_error_summary()` method
  - Implement `generate_error_report()` method
  - Ensure file size < 400 lines
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

    - [x] 2.1 Write unit tests for ErrorHandlingOrchestrator
    - Test error handling for crew failures
    - Test error aggregation
    - Test error report generation
    - Test successful result pass-through
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

    - [x] 2.2 Write property test for error handling
    - **Property 4: Error Handling Graceful Degradation**
    - **Validates: Requirements 2.1**

    - [x] 2.3 Write property test for error aggregation
    - **Property 5: Error Aggregation Completeness**
    - **Validates: Requirements 2.2**

- [x] 3. Implement ProgressTrackingOrchestrator
  - Create `src/finwiz/orchestrators/progress_tracking_orchestrator.py`
  - Implement `update_progress()` method
  - Implement `save_batch_metrics_to_file()` method
  - Ensure file size < 400 lines
  - _Requirements: 8.1, 8.2, 8.3, 8.4_

    - [x] 3.1 Write unit tests for ProgressTrackingOrchestrator
    - Test progress calculation
    - Test metrics file saving
    - Test progress logging
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

    - [x] 3.2 Write property test for progress calculation
    - **Property 21: Progress Calculation Accuracy**
    - **Validates: Requirements 8.3**


- [x] 4. Implement UtilityOrchestrator
  - Create `src/finwiz/orchestrators/utility_orchestrator.py`
  - Implement `parse_crew_output_for_holding()` method
  - Implement `calculate_grade_distribution()` method
  - Implement `extract_sec_filing_urls()` method
  - Implement `validate_and_fix_sec_urls()` method
  - Ensure file size < 400 lines
  - _Requirements: 9.1, 9.2, 9.3, 9.4_

    - [x] 4.1 Write unit tests for UtilityOrchestrator
    - Test crew output parsing
    - Test grade distribution calculation
    - Test SEC URL extraction
    - Test SEC URL validation and fixing
    - _Requirements: 9.1, 9.2, 9.3, 9.4_

    - [x] 4.2 Write property test for grade distribution
    - **Property 22: Grade Distribution Aggregation**
    - **Validates: Requirements 9.2**

    - [x] 4.3 Write property test for URL validation
    - **Property 24: URL Validation and Correction**
    - **Validates: Requirements 9.4**

## Phase 2: Core Business Logic Orchestrators

- [x] 5. Implement DeepAnalysisOrchestrator
  - Create `src/finwiz/orchestrators/deep_analysis_orchestrator.py`
  - Implement `run_deep_analysis_on_holdings()` method
  - Implement `create_deep_analysis_result_from_crew_output()` method
  - Implement `execute_deep_analysis_with_prefetch()` method
  - Implement `save_batch_metrics_to_file()` method
  - Ensure file size < 400 lines
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

    - [x] 5.1 Write unit tests for DeepAnalysisOrchestrator
    - Test deep analysis execution
    - Test result creation from crew output
    - Test batch prefetch optimization
    - Test metrics file saving
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

    - [x] 5.2 Write property test for deep analysis completeness
    - **Property 8: Deep Analysis Completeness**
    - **Validates: Requirements 3.1**

    - [x] 5.3 Write property test for result structure validation
    - **Property 9: Deep Analysis Result Structure**
    - **Validates: Requirements 3.2**

    - [x] 5.4 Write property test for parsing correctness
    - **Property 10: Deep Analysis Parsing Correctness**
    - **Validates: Requirements 3.5**


- [x] 6. Implement AlternativesMatchingOrchestrator
  - Create `src/finwiz/orchestrators/alternatives_matching_orchestrator.py`
  - Implement `match_alternatives_for_holdings()` method
  - Implement `match_alternatives_after_discovery()` method
  - Ensure file size < 400 lines (196 lines ✓)
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

    - [x] 6.1 Write unit tests for AlternativesMatchingOrchestrator
    - Test alternative matching for underperforming holdings
    - Test alternative matching from discovery results
    - Test alternative structure validation
    - Test empty result for high-grade holdings
    - All tests passing with pytest-mock (unittest.mock banned)
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

    - [x] 6.2 Write property test for conditional matching
    - **Property 11: Alternative Matching Conditional**
    - **Validates: Requirements 4.1**

    - [x] 6.3 Write property test for alternative structure
    - **Property 12: Alternative Structure Validation**
    - **Validates: Requirements 4.3**

- [x] 7. Implement DiscoveryOrchestrator
  - Create `src/finwiz/orchestrators/discovery_orchestrator.py`
  - Implement `check_crypto()` method
  - Implement `check_stock()` method
  - Implement `check_etf()` method
  - Implement `check_investment_discovery()` method
  - Ensure file size < 400 lines
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

    - [x] 7.1 Write unit tests for DiscoveryOrchestrator
    - Test crypto discovery execution
    - Test stock discovery execution
    - Test ETF discovery execution
    - Test discovery result consolidation
    - Test error handling for failed discoveries
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

    - [x] 7.2 Write property test for result consolidation
    - **Property 16: Discovery Result Consolidation**
    - **Validates: Requirements 6.4**

    - [x] 7.3 Write property test for error handling
    - **Property 17: Discovery Error Handling**
    - **Validates: Requirements 6.5**


- [x] 8. Implement ValidationOrchestrator
  - Create `src/finwiz/orchestrators/validation_orchestrator.py`
  - Implement `pre_validate_reporter_input()` method
  - Implement `check_core_analysis_availability()` method
  - Implement `extract_market_conditions()` method
  - Implement `extract_market_context_from_core_analysis()` method
  - Ensure file size < 400 lines
  - _Requirements: 7.1, 7.2, 7.3, 7.4_

    - [x] 8.1 Write unit tests for ValidationOrchestrator
    - Test reporter input validation
    - Test core analysis availability checking
    - Test market conditions extraction
    - Test market context extraction
    - _Requirements: 7.1, 7.2, 7.3, 7.4_

    - [x] 8.2 Write property test for data availability check
    - **Property 18: Validation Data Availability Check**
    - **Validates: Requirements 7.1**

    - [x] 8.3 Write property test for core analysis verification
    - **Property 19: Core Analysis Verification**
    - **Validates: Requirements 7.2**

    - [x] 8.4 Write property test for market context structure
    - **Property 20: Market Context Structure**
    - **Validates: Requirements 7.4**

## Phase 3: Reporting Orchestrator

- [x] 9. Implement ReportingOrchestrator
  - Create `src/finwiz/orchestrators/reporting_orchestrator.py`
  - Implement `report()` method
  - Implement `consolidate_reports()` method
  - Implement `generate_final_report()` method
  - Implement `generate_html_from_export()` method
  - Implement `store_crew_export_paths()` method
  - Implement `get_crew_export_path()` method
  - Ensure file size < 400 lines (169 lines ✓)
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

    - [x] 9.1 Write unit tests for ReportingOrchestrator
    - Test report consolidation
    - Test final report generation
    - Test HTML generation with Jinja2
    - Test export path calculation
    - Test export path storage
    - All tests passing with pytest-mock (unittest.mock banned)
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

    - [x] 9.2 Write property test for report consolidation
    - **Property 13: Report Consolidation Completeness**
    - **Validates: Requirements 5.1**
    - Tests crew export path management and consolidation

    - [x] 9.3 Write property test for HTML generation
    - **Property 14: HTML Report Generation**
    - **Validates: Requirements 5.2**
    - Tests HTML generation from export data with Jinja2

    - [x] 9.4 Write property test for export path correctness
    - **Property 15: Export Path Correctness**
    - **Validates: Requirements 5.4**
    - Tests export path calculation and session ID inclusion


## Phase 4: Flow Refactoring

- [x] 10. Refactor FinwizFlow to use orchestrators
  - Create orchestrator initialization in `__init__`
  - Implement lazy loading properties for all orchestrators
  - Create `OrchestratorDependencies` dataclass
  - Implement `_initialize_dependencies()` method
  - Ensure refactored Flow < 400 lines
  - _Requirements: 1.1, 10.2_

- [x] 11. Update Flow listeners to delegate to orchestrators
  - Update `validate_data_integration()` to delegate to ValidationOrchestrator
  - Update `check_portfolio()` to delegate to ValidationOrchestrator
  - Update `analyze_holdings_deep()` to delegate to DeepAnalysisOrchestrator
  - Update `match_alternatives()` to delegate to AlternativesMatchingOrchestrator
  - Update `check_crypto()` to delegate to DiscoveryOrchestrator
  - Update `check_stock()` to delegate to DiscoveryOrchestrator
  - Update `check_etf()` to delegate to DiscoveryOrchestrator
  - Update `check_investment_discovery()` to delegate to DiscoveryOrchestrator
  - Update `report()` to delegate to ReportingOrchestrator
  - _Requirements: 10.2_

- [x] 12. Create re-export layer for backward compatibility
  - Add re-exports for all orchestrators in `flow_orchestrator.py`
  - Add re-exports for state classes
  - Update `__all__` to include all exports
  - _Requirements: 1.4, 10.1_

    - [x] 12.1 Write unit tests for Flow delegation
    - Test that Flow listeners delegate to correct orchestrators
    - Test that orchestrator methods are called with correct parameters
    - _Requirements: 10.2_

    - [x] 12.2 Write property test for listener delegation
    - **Property 25: Flow Listener Delegation**
    - **Validates: Requirements 10.2**

## Phase 5: Testing and Validation

- [x] 13. Run existing test suite
  - Run all tests in `tests/unit/flows/test_flow_orchestrator.py`
  - Verify all tests pass without modification
  - _Requirements: 1.5, 10.4_

- [x] 14. Update test mock paths if needed
  - Identify tests that mock Flow methods
  - Update mock paths to point to orchestrator methods
  - Verify tests still pass
  - _Requirements: 1.5, 10.4_

<!-- 
- [ ] 15. Run integration tests
  - Create integration test for full Flow execution
  - Test orchestrator interactions
  - Test error propagation between orchestrators
  - _Requirements: 10.3_

- [ ] 15.1 Write property test for behavioral equivalence
  - **Property 26: Behavioral Equivalence**
  - **Validates: Requirements 10.3** -->

- [x] 16. Run backward compatibility tests
  - Test all existing import paths
  - Test public API compatibility
  - Verify no breaking changes
  - _Requirements: 1.4, 10.1, 10.5_

    - [x] 16.1 Write property test for import compatibility
    - **Property 3: Import Backward Compatibility**
    - **Validates: Requirements 1.4, 10.1**

    - [x] 16.2 Write property test for API compatibility
    - **Property 27: API Compatibility**
    - **Validates: Requirements 10.5**

- [x] 17. Verify file size constraints
  - Check line count for `flow_orchestrator.py` (< 300 lines)
  - Check line count for all orchestrator files (< 300 lines each)
  - _Requirements: 1.1, 1.2_

    - [x] 17.1 Write property test for file size constraint
    - **Property 1: File Size Constraint**
    - **Validates: Requirements 1.1, 1.2**

    - [x] 17.2 Write property test for single responsibility
    - **Property 2: Single Responsibility**
    - **Validates: Requirements 1.3**

- [x] 18. Verify code coverage
  - Run coverage report for all orchestrators
  - Ensure coverage ≥ 80% for all modules
  - Ensure coverage ≥ 90% for ErrorHandling and DeepAnalysis
  - _Requirements: All_

- [x] 19. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Phase 6: Documentation and Cleanup

- [x] 20. Update orchestrator docstrings
  - Add comprehensive docstrings to all orchestrator classes
  - Add docstrings to all orchestrator methods
  - Include parameter descriptions and return types
  - _Requirements: All_

- [x] 21. Update Flow docstrings
  - Update FinwizFlow class docstring to reference orchestrators
  - Update Flow listener docstrings to indicate delegation
  - _Requirements: All_


- [x] 22. Create migration guide
  - Document the refactoring changes
  - Provide examples of using orchestrators directly
  - Document backward compatibility guarantees
  - Include troubleshooting section
  - _Requirements: 10.1, 10.5_

- [x] 23. Update architecture documentation
  - Update system architecture diagrams
  - Document orchestrator responsibilities
  - Document orchestrator interactions
  - Update developer onboarding guide
  - _Requirements: All_

- [x] 24. Remove dead code
  - Identify and remove any unused methods
  - Remove commented-out code
  - Clean up imports
  - _Requirements: All_

- [x] 25. Final code review
  - Review all orchestrator implementations
  - Review Flow refactoring
  - Review test coverage
  - Review documentation
  - _Requirements: All_

- [x] 26. Final checkpoint - Verify completion
  - Ensure all tests pass, ask the user if questions arise.
