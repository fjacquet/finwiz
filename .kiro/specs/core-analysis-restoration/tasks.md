# Implementation Plan

## Completed Tasks

- [x] 1. Debug and fix data consolidation retrieval bug
  - Investigate why get_crew_data_with_freshness_check() returns None despite successful crew output storage
  - Verify that crew output files are stored in the expected directory structure and format
  - Debug the registry_manager.get_crew_data_with_freshness_check() method to identify retrieval failures
  - Test that stored crew outputs can be successfully retrieved by the data consolidation system
  - Fix any file path, permission, or JSON parsing issues preventing data retrieval
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 13.1, 13.2_

- [x] 2. Add data freshness validation to existing tools
  - Create simple DataFreshnessValidator class that checks if data timestamps are within 24 hours
  - Add timestamp validation to existing Yahoo Finance and Alpha Vantage tools
  - Log warnings when data is stale but continue processing (graceful degradation)
  - Write unit tests for freshness validation logic
  - _Requirements: 11.1, 11.2, 11.3, 11.6_

- [x] 3. Integrate core analysis with existing data integration system
  - Modify existing CrewDataIntegrationManager to collect outputs from restored crews
  - Update existing check_investment_discovery() to use core analysis results
  - Enhance existing pre_validate_reporter_input() to include core analysis data
  - Test that data flows properly from crews to report generation
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 4. Verify current flow architecture matches design requirements
  - Current flow has check_stock, check_etf, check_crypto as discovery crews (finding "top 10")
  - Design document specifies these should be core analysis crews (analyzing market conditions)
  - Verify if separate core analysis execution phase is needed before portfolio analysis
  - Determine if current discovery crews should be renamed or if new core analysis crews are needed
  - Document the actual vs. intended architecture and decide on implementation approach
  - _Requirements: 2.1, 2.2, 2.3, 3.1, 3.2, 4.1, 4.2, 4.3_

- [x] 5. Enhance error handling and graceful degradation
  - Add try-catch blocks around crew execution in main.py flow methods
  - Log errors and continue with existing functionality when crews fail
  - Update existing error handling to include core analysis failures
  - Test that system continues working when individual crews fail
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [x] 6. Add feature flags for core analysis crews
  - Extend existing FeatureFlags class with stock_analysis, etf_analysis, crypto_analysis flags
  - Add feature flag checks to crew execution methods in main.py
  - Default all core analysis flags to True to restore full functionality
  - Test feature flag control of individual crews
  - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [x] 7. Ensure AI agents drive analysis (not just Python logic)
  - Verify existing crew configurations use AI agents with proper LLM settings
  - Check that existing tools provide data to AI agents for reasoning and decision-making
  - Ensure existing task configurations capture AI reasoning in outputs
  - Test that crew outputs contain AI-generated insights and recommendations
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7_

- [x] 9. Reorganize and improve test structure following best practices
  - Move scattered root-level tests to proper organized directories
  - Create tests/unit/crews/ subdirectories for stock_crew, etf_crew, crypto_crew tests
  - Create tests/unit/flow/ for main flow and orchestration tests
  - Create tests/integration/core_analysis/ for core analysis integration tests
  - Update pytest configuration to use the new organized structure
  - _Requirements: 13.1, 13.2, 13.7_

## Remaining Tasks

- [ ] 8. Implement core analysis crews if needed based on architecture review
  - Task 4 determined that current discovery crews ARE the core analysis crews
  - No separate implementation needed - existing crews already perform market-wide analysis
  - Mark this task as NOT NEEDED based on architecture review findings
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.2, 5.3, 7.1, 7.2_
  - _Status: NOT NEEDED - Current architecture already implements required functionality_

- [x] 10. Verify data consolidation works correctly with current implementation
  - Test that integration_manager.store_crew_output() stores crew outputs correctly
  - Verify consolidated_data contains actual crew results from discovery crews in pre_validate_reporter_input()
  - Test that pre_validate_reporter_input() receives non-empty consolidated data
  - Ensure portfolio analysis can access crew data through integration system
  - Verify no "Core analysis data missing" warnings when crews execute successfully
  - Test the data flow from crew execution → storage → consolidation → report
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 13.1, 13.2, 13.3, 13.4_

- [x] 11. Test backward compatibility with current implementation
  - Run existing portfolio review functionality to ensure it works correctly
  - Test existing discovery crews (check_stock, check_etf, check_crypto) continue to work unchanged
  - Verify existing report generation includes properly consolidated crew data
  - Test existing quantitative backtesting integration continues to work
  - Verify no breaking changes to existing API endpoints or interfaces
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7, 12.8_

- [x] 12. Write comprehensive tests for data consolidation
  - Write unit tests for crew data storage and retrieval mechanisms
  - Write integration tests for data consolidation with discovery crews
  - Write tests verifying that stored crew data can be properly retrieved
  - Test error scenarios, file system issues, and data corruption handling
  - Write tests to prevent regression of data consolidation issues
  - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 14.7, 14.8_

- [x] 13. Fix discovery results integration with report generation
  - CRITICAL: Modify crew_factory.py execute_report_crew() to pass ALL Flow state fields to prepared_context
  - Current issue: execute_report_crew() calls prepare_crew_context() which may not preserve all state fields
  - Ensure portfolio_review from inputs is preserved in prepared_context (currently causing template variable errors)
  - Ensure aplus_opportunities from inputs is included in prepared_context
  - Ensure investment_discovery_structured from inputs is included in prepared_context
  - Ensure investment_discovery_result from inputs is included in prepared_context
  - Ensure validated_tickers_list is extracted and included in prepared_context
  - Ensure discovery_status is constructed and included in prepared_context
  - Ensure backtesting_status is constructed and included in prepared_context
  - Ensure data_availability_summary_formatted from inputs is included in prepared_context
  - Update ReportCrew.prepare_crew_context() to preserve all required input fields
  - Test that discovery results appear in the final report when discovery is run
  - Verify that "Discovery status not provided" message only appears when discovery is actually not run
  - Verify that report crew does NOT show "INSUFFICIENT / PARTIAL" errors for missing inputs
  - Verify that template variable errors for portfolio_review are resolved
  - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5, 15.6, 15.7, 15.8, 15.9, 15.10_
