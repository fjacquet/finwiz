# Implementation Plan

- [x] 1. Restore core analysis crews in main.py flow
  - Uncomment and restore the existing @start() methods for check_crypto(), check_stock(), and check_etf() in FinwizFlow
  - Import existing StockCrew, EtfCrew, and CryptoCrew classes that are already implemented
  - Add simple feature flag checks using existing feature flag system
  - Test that crews execute and store results in flow inputs
  - _Requirements: 1.1, 1.2, 1.3_

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

- [x] 4. Implement improved flow layout with optimized phases
  - Restore core analysis crews (stock, etf, crypto) to execute in parallel after data validation using @start() decorator
  - Update check_portfolio() to use @listen() decorator waiting for all three core analysis crews completion
  - Update check_portfolio_rebalancing() to use @listen() decorator waiting for all three core analysis crews completion  
  - Keep check_investment_discovery() listening to both portfolio methods for comprehensive analysis
  - Test the new 5-phase flow layout improves performance and maintains proper data dependencies
  - _Requirements: 3.1, 3.2, 7.1, 7.2_

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

- [x] 8. Test backward compatibility with existing features
  - Run existing portfolio review functionality to ensure it still works
  - Test existing investment discovery with enhanced core analysis data
  - Verify existing report generation includes core analysis insights
  - Test existing quantitative backtesting integration continues to work
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7_

- [x] 9. Reorganize and improve test structure following best practices
  - Move scattered root-level tests to proper organized directories
  - Create tests/unit/crews/ subdirectories for stock_crew, etf_crew, crypto_crew tests
  - Create tests/unit/flow/ for main flow and orchestration tests
  - Create tests/integration/core_analysis/ for core analysis integration tests
  - Update pytest configuration to use the new organized structure
  - _Requirements: 13.1, 13.2, 13.7_

- [x] 10. Write comprehensive tests for restored core analysis functionality
  - Write unit tests for each restored crew in tests/unit/crews/{crew_name}/
  - Write flow integration tests in tests/integration/core_analysis/
  - Write performance tests in tests/performance/core_analysis/
  - Test error scenarios, feature flags, and backward compatibility
  - _Requirements: 13.3, 13.4, 13.5, 13.6, 13.7_
