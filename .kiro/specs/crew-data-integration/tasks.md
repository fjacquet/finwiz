# Implementation Plan

- [x] 1. Set up core data integration infrastructure
  - Create directory structure for centralized data storage
  - Implement base CrewDataIntegrationManager class with initialization
  - Set up logging and configuration for integration system
  - _Requirements: 4.1, 4.2, 7.1_

- [x] 2. Implement enhanced data schemas with metadata
  - [x] 2.1 Create CrewOutputMetadata base schema
    - Write Pydantic model for crew output metadata including timestamps and validation status
    - Add data source tracking and freshness status fields
    - Create unit tests for metadata schema validation with mocked data (no external calls)
    - _Requirements: 4.2, 6.1, 6.2_

  - [x] 2.2 Enhance existing crew output schemas
    - Extend StockCrewOutput, ETFCrewOutput, CryptoCrewOutput with metadata fields
    - Add SEC citation models with full provenance tracking
    - Add validated ticker models with validation metadata
    - Create unit tests for enhanced schemas
    - _Requirements: 1.1, 1.2, 3.1, 3.2_

  - [x] 2.3 Create discovery and integration-specific schemas
    - Implement APlusOpportunityCollection schema for A+ opportunities
    - Create DataAvailabilityReport and IntegrationError schemas
    - Add FreshnessStatus and ValidationStatus models
    - Write comprehensive unit tests for all new schemas
    - _Requirements: 5.1, 5.2, 6.1, 7.1_

- [x] 3. Implement data freshness monitoring system
  - [x] 3.1 Create DataFreshnessChecker class
    - Write file timestamp checking logic with configurable age thresholds
    - Implement stale data detection across all crew output directories
    - Add freshness report generation with detailed status information
    - Create unit tests with fully mocked file system operations (no real file I/O)
    - _Requirements: 6.1, 6.2, 6.3_

  - [x] 3.2 Integrate freshness checking into data access
    - Add freshness validation to data retrieval methods
    - Implement automatic warnings for stale data (>24 hours)
    - Create refresh recommendation logic based on data dependencies
    - Write integration tests for freshness checking workflow
    - _Requirements: 6.2, 6.3, 6.4_

- [x] 4. Create centralized data validation pipeline
  - [x] 4.1 Implement ValidationPipeline class
    - Write schema validation logic using Pydantic models
    - Add cross-crew data consistency checking
    - Implement validation error collection and reporting
    - Create unit tests for validation scenarios
    - _Requirements: 3.1, 3.2, 3.3, 4.1_

  - [x] 4.2 Add SEC citation validation and integration
    - Implement SEC/EDGAR citation extraction and validation
    - Add filing date and URL verification logic
    - Create citation consolidation for report integration
    - Write tests for SEC citation handling
    - _Requirements: 1.1, 1.2, 1.3_

- [x] 5. Implement CrewDataAccessor for unified data access
  - [x] 5.1 Create base data accessor with error handling
    - Write methods for retrieving stock, ETF, crypto, and discovery data
    - Implement graceful degradation when data is unavailable
    - Add detailed error reporting with specific file paths
    - Create unit tests with fully mocked data scenarios (no file system access)
    - _Requirements: 4.3, 7.2, 7.3_

  - [x] 5.2 Add market sentiment data consolidation
    - Implement sentiment data aggregation across crews
    - Add Top 3 sentiment sources with URLs and dates
    - Create Positive/Neutral/Negative distribution calculation
    - Write tests for sentiment data integration
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 5.3 Implement ticker validation consolidation
    - Create validated ticker collection from all crews
    - Add validation status tracking and error reporting
    - Implement alternative ticker suggestions for failed validations
    - Write comprehensive tests for ticker validation workflow
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 6. Create A+ opportunity integration system
  - [x] 6.1 Implement A+ data extraction from discovery outputs
    - Write logic to parse A+ opportunities from discovery crew files
    - Add allocation recommendation and replacement note extraction
    - Create A+ opportunity validation and scoring
    - Write unit tests for A+ data extraction
    - _Requirements: 5.1, 5.2, 5.3_

  - [x] 6.2 Integrate A+ opportunities into report data
    - Add A+ opportunity consolidation to reporter input
    - Implement portfolio allocation updates based on A+ discoveries
    - Create A+ availability status tracking
    - Write integration tests for A+ data flow
    - _Requirements: 5.3, 5.4, 5.5_

- [x] 7. Implement comprehensive error handling and recovery
  - [x] 7.1 Create MissingDataHandler class
    - Write missing data detection logic across all crew outputs
    - Implement fallback data provision for common missing scenarios
    - Add recovery action suggestions with specific next steps
    - Create unit tests for missing data scenarios
    - _Requirements: 7.1, 7.2, 7.4_

  - [x] 7.2 Add validation error recovery system
    - Implement ValidationErrorRecovery class with error analysis
    - Add data repair suggestions for common validation failures
    - Create detailed error reporting with recovery recommendations
    - Write tests for validation error handling
    - _Requirements: 7.1, 7.4, 7.5_

- [x] 8. Create integration middleware for crew coordination
  - [x] 8.1 Implement CrewIntegrationMiddleware
    - Write pre-execution hooks for dependency validation
    - Add post-execution hooks for data storage and validation
    - Implement crew execution coordination based on data dependencies
    - Create unit tests for middleware functionality
    - _Requirements: 4.1, 4.4, 6.4_

  - [x] 8.2 Add crew output storage and retrieval
    - Implement standardized crew output storage in integration directory
    - Add metadata persistence for all crew executions
    - Create data lineage tracking across crew executions
    - Write integration tests for storage and retrieval workflow
    - _Requirements: 4.2, 4.5, 7.5_

- [x] 9. Update Report crew to use integrated data system
  - [x] 9.1 Modify ReportCrew to use CrewDataAccessor
    - Replace direct file reading with CrewDataAccessor methods
    - Add data availability checking before report generation
    - Implement graceful degradation for missing upstream data
    - Update crew configuration to use new data access patterns
    - _Requirements: 1.3, 2.4, 4.3, 5.5_

  - [x] 9.2 Enhance report generation with integrated data
    - Add SEC/EDGAR citations with proper formatting and dates
    - Include market sentiment analysis with source attribution
    - Add A+ opportunity sections with allocation recommendations
    - Update report templates to handle integrated data structure
    - _Requirements: 1.1, 1.2, 2.1, 2.2, 5.1, 5.2_

- [x] 10. Add logging and basic monitoring for single-user system
  - [x] 10.1 Implement integration system logging
    - Add structured logging for all data integration operations
    - Create data lineage logging with crew execution tracking
    - Implement error logging with detailed context information
    - Write simple log analysis utilities for debugging integration issues
    - _Requirements: 7.3, 7.5_

  - [x] 10.2 Create basic health checking for single-user workflow
    - Add simple health checks for data integration pipeline
    - Implement basic data freshness and availability status reporting
    - Create simple error reporting for integration failures and data staleness
    - Write basic validation scripts for single-user debugging
    - _Requirements: 6.2, 6.5, 7.3_

- [ ] 11. Create comprehensive test suite with proper mocking
  - [ ] 11.1 Write unit tests for all integration components with full mocking
    - Test CrewDataIntegrationManager with mocked file system and crew outputs
    - Test all enhanced schemas with mocked data (no external API calls)
    - Test data freshness checking with mocked file timestamps
    - Test error handling with mocked failure scenarios (no real crew execution)
    - Mock all external dependencies to avoid API costs and ensure fast execution
    - _Requirements: All requirements - validation through testing_

  - [ ] 11.2 Create integration tests with mocked crew outputs
    - Test complete data integration pipeline with pre-generated mock crew outputs
    - Test report generation with mocked integrated data from all crews
    - Test error recovery scenarios with mocked missing and stale data files
    - Mock all crew executions and external API calls to control costs
    - Focus on data flow validation rather than performance testing
    - _Requirements: All requirements - end-to-end validation_

- [x] 12. Update main flow orchestration
  - [x] 12.1 Integrate CrewDataIntegrationManager into main flow
    - Modify FinwizFlow to use CrewDataIntegrationManager for coordination
    - Add data integration validation before crew execution
    - Update flow inputs to include integrated data access
    - Test flow execution with new integration system
    - _Requirements: 4.1, 4.4, 6.4_

  - [x] 12.2 Add integration system configuration and deployment
    - Create configuration files for integration system settings
    - Add environment variable support for integration parameters
    - Update deployment scripts to include integration system setup
    - Create documentation for integration system configuration
    - _Requirements: 7.1, 7.4_

- [x] 13. Implement backtesting data extraction system
  - [x] 13.1 Create BacktestingDataExtractor class
    - Write extraction logic for ValidationResult backtesting metrics
    - Implement methods to extract annualized_return, sharpe_ratio, max_drawdown, win_rate
    - Add regime-specific performance extraction from market_regimes_tested
    - Create risk-adjusted metrics extraction (Sharpe, Sortino, Calmar ratios)
    - Write unit tests with fully mocked ValidationResult data (no external calls)
    - _Requirements: 8.1, 8.2_

  - [x] 13.2 Implement regime performance analysis
    - Create RegimePerformance model for bull/bear/sideways market analysis
    - Extract performance metrics for each market regime from validation results
    - Calculate regime consistency scores showing performance stability
    - Generate performance comparison tables across regimes
    - Write tests for regime-specific performance extraction
    - _Requirements: 8.2, 8.4_

  - [x] 13.3 Add backtesting summary generation
    - Implement BacktestingSummary aggregation across all A+ candidates
    - Calculate average metrics across all validated candidates
    - Identify best and worst performers by backtesting metrics
    - Create structured output for report integration
    - Write integration tests for summary generation
    - _Requirements: 8.3, 8.4_

- [x] 14. Implement market context extraction system
  - [x] 14.1 Create MarketContextExtractor class
    - Write extraction logic for MarketRegime from APlusDiscoveryResult
    - Implement methods to extract regime_type, vix_level, inflation_rate, interest_rate_trend
    - Add market_stress_level extraction and assessment
    - Create VIXIndicators extraction with percentile calculations
    - Write unit tests with fully mocked APlusDiscoveryResult data
    - _Requirements: 9.1, 9.2_

  - [x] 14.2 Implement macro indicators extraction
    - Create MacroIndicators model for economic context
    - Extract inflation_rate and interest_rate_trend from market context
    - Add GDP growth and unemployment rate extraction (when available)
    - Calculate risk environment assessment (favorable/neutral/challenging)
    - Write tests for macro indicators extraction
    - _Requirements: 9.1, 9.2_

  - [x] 14.3 Add market context summary for reporting
    - Implement MarketContextSummary aggregation
    - Generate allocation implications based on current market context
    - Create structured output explaining how context influences recommendations
    - Add conservative assumptions handling for missing context data
    - Write integration tests for context summary generation
    - _Requirements: 9.3, 9.4, 9.5_

- [x] 15. Implement discovery methodology extraction system
  - [x] 15.1 Create DiscoveryMethodologyExtractor class
    - Write extraction logic for APlusCriteria from APlusDiscoveryResult
    - Implement methods to extract ROE thresholds, debt ratios, market cap minimums
    - Add revenue growth requirements and expense ratio thresholds extraction
    - Extract regime adjustment information and rationale
    - Write unit tests with fully mocked APlusDiscoveryResult data
    - _Requirements: 10.1, 10.2_

  - [x] 15.2 Implement validation statistics extraction
    - Create ValidationStatistics model for screening metrics
    - Extract total_screened, candidates_found, passed_validation, failed_validation
    - Calculate validation_rate and screening_efficiency percentages
    - Add validation success rates and failure analysis
    - Write tests for validation statistics extraction
    - _Requirements: 10.2, 10.5_

  - [x] 15.3 Add fundamental and technical score extraction
    - Implement ScoreBreakdown extraction for each A+ candidate
    - Extract fundamental_score, technical_score, quality_score, risk_score
    - Create composite_score and grade mapping
    - Generate methodology summary with score breakdowns
    - Write integration tests for score extraction
    - _Requirements: 10.4_

  - [x] 15.4 Create methodology summary for reporting
    - Implement MethodologySummary aggregation
    - Include screening criteria, validation statistics, and score breakdowns
    - Add methodology notes explaining discovery process
    - List data sources used for discovery
    - Write tests for methodology summary generation
    - _Requirements: 10.3, 10.4_

- [x] 16. Implement performance metrics aggregation system
  - [x] 16.1 Create PerformanceMetricsAggregator class
    - Write aggregation logic using BacktestingDataExtractor
    - Implement aggregate_by_asset_type for ETF/stock/crypto breakdown
    - Add aggregate_by_regime for bull/bear/sideways analysis
    - Calculate portfolio-level impact metrics
    - Write unit tests with mocked backtesting data
    - _Requirements: 8.3, 8.4_

  - [x] 16.2 Implement portfolio impact calculation
    - Create PortfolioImpactMetrics model
    - Calculate expected_grade_improvement from A+ opportunities
    - Assess risk_impact and diversification_impact
    - Determine implementation_complexity
    - Write tests for portfolio impact calculations
    - _Requirements: 8.4, 10.5_

  - [x] 16.3 Generate comprehensive performance report
    - Implement PerformanceReport generation
    - Aggregate metrics by asset type and regime
    - Include portfolio impact assessment
    - Identify top 5 opportunities by composite score
    - Write integration tests for report generation
    - _Requirements: 8.3, 8.4, 8.5_

- [x] 17. Update Report crew task descriptions for enhanced data extraction
  - [x] 17.1 Update comprehensive_financial_integration_task description
    - Add explicit instructions to extract backtesting results from discovery crew
    - Include market context extraction (VIX, inflation, rates, regime type)
    - Add discovery criteria thresholds extraction instructions
    - Include fundamental_score and technical_score extraction
    - Update expected_output to include new data elements
    - _Requirements: 8.1, 8.2, 9.1, 9.2, 10.1, 10.4_

  - [x] 17.2 Update optimal_portfolio_allocation_task description
    - Add instructions to use backtesting Sharpe ratios for allocation weighting
    - Include regime consistency scores for asset selection
    - Add market context usage for defensive vs growth allocation adjustments
    - Include technical scores for entry timing recommendations
    - Update expected_output to reference backtesting and context data
    - _Requirements: 8.2, 8.3, 9.3, 9.4_

  - [x] 17.3 Update risk_assessment_mitigation_task description
    - Add instructions to extract max_drawdown from backtesting for downside risk
    - Include VIX levels and market_stress_level for risk environment assessment
    - Add regime-specific risks extraction (bull/bear/sideways variations)
    - Include validation report failure rates and alternatives
    - Update expected_output to include backtesting and context risk data
    - _Requirements: 8.1, 8.2, 9.1, 9.2, 9.5_

  - [x] 17.4 Update comprehensive_investment_report_task description
    - Add "Backtesting Performance Analysis" section with metrics tables
    - Include "Market Context & Regime Analysis" section with VIX and macro indicators
    - Add "Discovery Methodology" section with criteria and validation statistics
    - Include "Optimization Insights" section with validation and improvement data
    - Update expected_output to include all new report sections
    - _Requirements: 8.3, 8.4, 9.3, 9.4, 10.3, 10.5_

- [x] 18. Integrate enhanced extractors with CrewDataAccessor
  - [x] 18.1 Add extractor initialization to CrewDataAccessor
    - Initialize BacktestingDataExtractor in CrewDataAccessor.__init__
    - Initialize MarketContextExtractor in CrewDataAccessor.__init__
    - Initialize DiscoveryMethodologyExtractor in CrewDataAccessor.__init__
    - Initialize PerformanceMetricsAggregator in CrewDataAccessor.__init__
    - Write unit tests for extractor initialization
    - _Requirements: 8.1, 9.1, 10.1_

  - [x] 18.2 Add extractor methods to CrewDataAccessor
    - Implement get_backtesting_metrics() method
    - Implement get_market_context() method
    - Implement get_discovery_methodology() method
    - Implement get_performance_report() method
    - Write tests for all new accessor methods
    - _Requirements: 8.3, 9.3, 10.3_

  - [x] 18.3 Update get_consolidated_reporter_input to include enhanced data
    - Add backtesting_summary to consolidated reporter input
    - Add market_context_summary to consolidated reporter input
    - Add methodology_summary to consolidated reporter input
    - Add performance_report to consolidated reporter input
    - Write integration tests for enhanced consolidated input
    - _Requirements: 8.3, 8.4, 9.3, 9.4, 10.3_

- [x] 19. Create comprehensive test suite for enhanced extractors
  - [x] 19.1 Write unit tests for all extractor classes
    - Test BacktestingDataExtractor with mocked ValidationResult data
    - Test MarketContextExtractor with mocked APlusDiscoveryResult data
    - Test DiscoveryMethodologyExtractor with mocked discovery data
    - Test PerformanceMetricsAggregator with mocked metrics
    - Mock all external dependencies to ensure fast execution
    - _Requirements: 8.1, 8.2, 9.1, 9.2, 10.1, 10.2_

  - [x] 19.2 Create integration tests for end-to-end data flow
    - Test complete extraction pipeline from discovery outputs to report input
    - Test graceful degradation when backtesting data is unavailable
    - Test conservative assumptions when market context is missing
    - Test methodology extraction with partial validation data
    - Mock all crew executions and use pre-generated test data
    - _Requirements: 8.5, 9.5, 10.5_

- [x] 20. Update documentation and examples
  - [x] 20.1 Create documentation for enhanced data extraction
    - Document BacktestingDataExtractor usage and methods
    - Document MarketContextExtractor usage and methods
    - Document DiscoveryMethodologyExtractor usage and methods
    - Document PerformanceMetricsAggregator usage and methods
    - Include code examples for each extractor
    - _Requirements: 8.1, 9.1, 10.1_

  - [x] 20.2 Add examples for report crew enhanced data usage
    - Create example showing backtesting metrics in reports
    - Create example showing market context in risk assessment
    - Create example showing discovery methodology in reports
    - Create example showing performance aggregation
    - Update report crew documentation with new sections
    - _Requirements: 8.3, 8.4, 9.3, 9.4, 10.3_
