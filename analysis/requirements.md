# Requirements Document: Add Enum Instructions to Task Configurations

## Introduction

This specification addresses the need to add comprehensive enum value instructions to all CrewAI task configuration files in FinWiz. Currently, only the stock and crypto crew task files have explicit enum instructions, while ETF, portfolio rebalancing, and investment discovery crews lack these critical guidelines. This inconsistency can lead to validation errors when agents generate outputs with incorrect enum values.

The goal is to ensure all task configurations explicitly document the exact enum values that must be used in their Pydantic schema outputs, preventing validation failures and improving agent output quality.

## Requirements

### Requirement 1: ETF Crew Enum Instructions

**User Story:** As a FinWiz developer, I want the ETF crew task configuration to include explicit enum instructions, so that agents generate outputs with correct enum values that pass Pydantic validation.

#### Acceptance Criteria

1. WHEN the ETF market trends task is executed THEN the task description SHALL include enum instructions for `market_sentiment` field
2. WHEN the ETF screening task is executed THEN the task description SHALL include enum instructions for any applicable enum fields in ETFScreeningResult schema
3. WHEN the ETF technical detail task is executed THEN the task description SHALL include enum instructions for `replication_method` and any other enum fields in ETFTechnicalAnalysis schema
4. WHEN the ETF risk assessment task is executed THEN the task description SHALL include enum instructions for risk level enums in RiskAssessmentStandardized schema
5. WHEN the ETF investment strategy task is executed THEN the task description SHALL include enum instructions for recommendation and time horizon enums

### Requirement 2: Portfolio Rebalancing Crew Enum Instructions

**User Story:** As a FinWiz developer, I want the portfolio rebalancing crew task configuration to include explicit enum instructions, so that agents generate portfolio decisions with correct enum values.

#### Acceptance Criteria

1. WHEN the analyze holding task is executed THEN the task description SHALL include enum instructions for `decision` field ("KEEP", "SELL")
2. WHEN the analyze holding task is executed THEN the task description SHALL include enum instructions for `asset_class` field ("stock", "etf", "crypto")
3. WHEN the analyze holding task is executed THEN the task description SHALL include enum instructions for `grade` field ("A+", "A", "B+", "B", "C+", "C", "D", "F")
4. WHEN the analyze holding task is executed THEN the task description SHALL include enum instructions for `data_freshness` field ("fresh", "recent", "stale")
5. WHEN the find alternatives task is executed THEN the task description SHALL include enum instructions for `swap_timing` field ("immediate", "gradual", "tax_optimized")
6. WHEN the portfolio analysis task is executed THEN the task description SHALL include enum instructions for `sizing_action` field ("add", "trim", "hold", "exit")
7. WHEN the rebalancing optimization task is executed THEN the task description SHALL include enum instructions for risk assessment scale and level enums

### Requirement 3: Investment Discovery Crew Enum Instructions

**User Story:** As a FinWiz developer, I want the investment discovery crew task configuration to include explicit enum instructions, so that agents generate A+ discovery results with correct enum values.

#### Acceptance Criteria

1. WHEN the ETF discovery task is executed THEN the task description SHALL include enum instructions for `asset_type` field ("etf", "stock", "crypto")
2. WHEN the ETF discovery task is executed THEN the task description SHALL include enum instructions for `grade` field ("A+", "A", "B+", "B", "C+", "C", "D", "F")
3. WHEN the stock discovery task is executed THEN the task description SHALL include enum instructions for market regime enums ("bull", "bear", "sideways", "volatile")
4. WHEN the stock discovery task is executed THEN the task description SHALL include enum instructions for interest rate trend enums ("rising", "falling", "stable")
5. WHEN the stock discovery task is executed THEN the task description SHALL include enum instructions for market stress level enums ("low", "medium", "high")
6. WHEN the crypto discovery task is executed THEN the task description SHALL include enum instructions for `improvement_type` field ("replacement", "addition", "rebalancing")
7. WHEN the crypto discovery task is executed THEN the task description SHALL include enum instructions for `implementation_priority` field ("high", "medium", "low")
8. WHEN the optimization task is executed THEN the task description SHALL include enum instructions for risk assessment enums

### Requirement 4: Consistent Enum Instruction Format

**User Story:** As a FinWiz developer, I want all enum instructions to follow a consistent format across all task files, so that the documentation is clear and maintainable.

#### Acceptance Criteria

1. WHEN enum instructions are added to any task THEN they SHALL be placed in a dedicated "REQUIRED ENUM VALUES" section
2. WHEN enum instructions are documented THEN they SHALL use the format: "field_name: MUST be one of: value1, value2, value3"
3. WHEN enum values are case-sensitive THEN the instruction SHALL explicitly state the case requirement (e.g., "uppercase", "lowercase", "capitalized")
4. WHEN enum instructions are added THEN they SHALL be placed after the main task description and before the OUTPUT section
5. WHEN multiple enum fields exist THEN each SHALL be documented on a separate line with clear field path notation

### Requirement 5: Schema Reference Documentation

**User Story:** As a FinWiz developer, I want task configurations to reference the relevant schema files, so that agents can understand the complete output structure.

#### Acceptance Criteria

1. WHEN a task uses a Pydantic output schema THEN the task description SHALL reference the schema file location (e.g., "docs/schemas/ETFMarketTrend.schema.json")
2. WHEN example files exist for a schema THEN the task description SHALL reference the example file location (e.g., "docs/schemas/examples/etf_market_trend.example.json")
3. WHEN schema references are added THEN they SHALL be placed at the beginning of the task description
4. WHEN schema references are added THEN they SHALL use the format: "FIRST: Read the schema files [path] to understand the exact output format required"
5. WHEN schema references are added THEN they SHALL be consistent with existing patterns in stock and crypto crew task files

### Requirement 6: Validation Error Prevention

**User Story:** As a FinWiz developer, I want enum instructions to prevent common validation errors, so that agent outputs pass Pydantic validation on the first attempt.

#### Acceptance Criteria

1. WHEN enum instructions are added THEN they SHALL cover all Literal type fields in the output schema
2. WHEN enum instructions are added THEN they SHALL explicitly state that no other values are allowed
3. WHEN enum instructions are added THEN they SHALL include examples of incorrect values to avoid (e.g., "NOT 'Bullish', 'Bearish', etc.")
4. WHEN enum instructions are added THEN they SHALL be placed prominently in the task description to ensure agent visibility
5. WHEN enum instructions are added THEN they SHALL use emphatic language (e.g., "MUST be", "EXACTLY these values", "no other values allowed")

---

**Version**: 1.0  
**Created**: 2025-05-10  
**Status**: Draft
# Requirements Document

## Introduction

This specification addresses the critical issue where the core financial analysis capabilities (cryptocurrency, stock,
and ETF analysis crews) were removed from the FinWiz main flow, significantly reducing the platform's functionality.
The goal is to restore these essential analysis features while integrating them with the existing data integration
system and ensuring they work harmoniously with the current portfolio review, rebalancing, and investment discovery
flows.

The restoration will maintain FinWiz's architectural principles while ensuring all analysis crews contribute their
specialized insights to create comprehensive investment recommendations across all major asset classes.

## Glossary

- **FinWiz System**: The AI-powered financial research platform using CrewAI agents for investment analysis
- **Core Analysis Crews**: The stock, ETF, and cryptocurrency analysis crews that perform market-wide analysis
- **Discovery Crews**: Specialized crews that screen and identify "top 10" investment opportunities
- **Data Integration System**: The CrewDataIntegrationManager and CrewDataAccessor components for crew data sharing
- **Flow Orchestration**: The CrewAI Flow-based execution sequence managing crew dependencies and data passing
- **Portfolio Review**: The analysis of existing portfolio holdings with keep/sell recommendations
- **Data Consolidation**: The process of gathering and merging crew outputs for downstream consumption
- **Freshness Validation**: The system ensuring market data is no older than 24 hours
- **Graceful Degradation**: The system's ability to continue operating with partial data when components fail
- **Feature Flags**: Configuration switches to enable/disable individual analysis crews

## Requirements

### Requirement 1: Data Consolidation Bug Fix

**User Story:** As a financial analyst, I want the data consolidation system to properly retrieve and include crew
analysis results that are successfully stored, so that portfolio analysis and reporting have access to actual market
analysis instead of empty data.

#### Acceptance Criteria

1. WHEN crews execute and store outputs successfully THEN the data consolidation system SHALL retrieve those outputs
2. WHEN get_crew_data_with_freshness_check() is called THEN it SHALL find and return stored crew data files
3. WHEN consolidated_data is populated THEN it SHALL contain actual crew results instead of empty dictionaries
4. WHEN the flow logs consolidation status THEN it SHALL accurately report the number of crews with available data
5. WHEN portfolio analysis accesses crew data THEN it SHALL receive actual analysis results instead of None
6. WHEN THE FinWiz System reports "Core analysis data missing" THEN it SHALL be because data is actually missing,
   not due to retrieval bugs
7. WHEN crew outputs are stored with correct metadata THEN the freshness checker SHALL properly validate and retrieve them

### Requirement 2: Data Integration System Compatibility

**User Story:** As a system architect, I want the restored analysis crews to work seamlessly with the existing data
integration system, so that all crews can share data and insights effectively.

#### Acceptance Criteria

1. WHEN Core Analysis Crews execute THEN they SHALL integrate with the Data Integration System for data sharing
2. WHEN Core Analysis Crews generate outputs THEN they SHALL be accessible via the CrewDataAccessor for downstream
   consumption
3. WHEN THE Data Integration System validates data THEN it SHALL include outputs from all restored analysis crews
4. WHEN Core Analysis Crews access shared data THEN they SHALL use the Data Integration System's standardized
   interfaces
5. IF upstream data is available THEN Core Analysis Crews SHALL incorporate it into their analysis workflows

### Requirement 3: Flow Orchestration Validation

**User Story:** As a system user, I want to verify that the current flow orchestration is working correctly and that
crew execution results are properly accessible to downstream processes, so that the logical business process is
maintained.

#### Acceptance Criteria

1. WHEN THE Flow Orchestration executes THEN crews SHALL run in the correct sequence: portfolio analysis before
   discovery
2. WHEN Core Analysis Crews complete execution THEN their stored outputs SHALL be accessible to subsequent flow
   methods
3. WHEN Portfolio Review runs THEN it SHALL have access to any previously stored crew analysis results
4. WHEN Discovery Crews execute THEN they SHALL continue their current "top 10" screening functionality unchanged
5. WHEN data flows between flow methods THEN THE Flow Orchestration SHALL follow CrewAI Flow best practices for data
   passing
6. WHEN THE Data Integration System stores crew outputs THEN subsequent retrieval SHALL work correctly
7. IF any crew fails THEN THE FinWiz System SHALL continue with Graceful Degradation and log appropriate warnings

### Requirement 4: Enhanced Analysis Capabilities

**User Story:** As a financial researcher, I want each analysis crew to provide deep, specialized insights using the
latest tools and data sources, so that investment recommendations are comprehensive and well-informed.

#### Acceptance Criteria

1. WHEN THE Core Analysis Crews analyze securities THEN they SHALL provide fundamental analysis, technical
   indicators, and SEC filing insights
2. WHEN THE Core Analysis Crews analyze funds THEN they SHALL provide expense analysis, holdings breakdown, and
   tracking performance
3. WHEN THE Core Analysis Crews analyze digital assets THEN they SHALL provide technical analysis, market dynamics,
   and risk assessment
4. WHEN any Core Analysis Crew performs analysis THEN it SHALL use multiple data sources for validation and
   completeness
5. WHEN Core Analysis Crews generate risk assessments THEN they SHALL use the standardized 1-10 risk scoring system

### Requirement 5: AI-Driven Analysis and Decision Making

**User Story:** As a financial analyst, I want the analysis to be driven by AI agents using CrewAI's intelligent
decision-making capabilities rather than just deterministic Python logic, so that insights are nuanced, adaptive, and
leverage the full power of large language models.

#### Acceptance Criteria

1. WHEN Core Analysis Crews analyze financial data THEN AI agents SHALL be the primary decision makers using LLM
   reasoning and financial tools
2. WHEN investment recommendations are generated THEN they SHALL result from AI agent analysis and reasoning, not just
   algorithmic calculations
3. WHEN Core Analysis Crews use financial tools THEN the tools SHALL provide data to AI agents who interpret and
   synthesize insights intelligently
4. WHEN market conditions change THEN AI agents SHALL adapt their analysis approach based on contextual understanding
5. WHEN conflicting data signals exist THEN AI agents SHALL weigh evidence and provide reasoned conclusions rather
   than simple rule-based outputs
6. WHEN generating narratives THEN AI agents SHALL create coherent, professional financial analysis that demonstrates
   understanding of market dynamics
7. IF Python logic is used THEN it SHALL serve as supporting infrastructure for data processing, while AI agents
   handle interpretation and decision-making

### Requirement 6: Output Standardization and Validation

**User Story:** As a system integrator, I want all crew outputs to follow standardized schemas and validation rules,
so that data flows reliably between system components.

#### Acceptance Criteria

1. WHEN Core Analysis Crews generate outputs THEN they SHALL conform to validated Pydantic schemas with strict
   validation
2. WHEN crew outputs are stored THEN they SHALL include standardized fields for risk scores, recommendations, and
   confidence levels
3. WHEN the report crew consumes data THEN it SHALL receive validated, structured data from all Core Analysis Crews
4. WHEN validation fails THEN THE FinWiz System SHALL log detailed errors and continue with Graceful Degradation
5. IF crew outputs are incomplete THEN THE FinWiz System SHALL identify missing data and provide appropriate
   fallbacks

### Requirement 7: Performance and Scalability

**User Story:** As a system operator, I want the restored analysis crews to execute efficiently without degrading
system performance, so that users receive timely results.

#### Acceptance Criteria

1. WHEN multiple Core Analysis Crews execute THEN they SHALL run in parallel where possible to minimize total
   execution time
2. WHEN Core Analysis Crews make external API calls THEN they SHALL implement proper rate limiting and caching
3. WHEN THE FinWiz System is under load THEN it SHALL maintain responsive performance through efficient resource
   management
4. WHEN external services are slow THEN Core Analysis Crews SHALL implement timeout handling and Graceful Degradation
5. IF system resources are constrained THEN THE Flow Orchestration SHALL prioritize critical analysis tasks

### Requirement 8: Configuration and Feature Management

**User Story:** As a system administrator, I want to control which analysis crews are enabled and how they behave, so
that I can optimize the system for different use cases and environments.

#### Acceptance Criteria

1. WHEN configuring THE FinWiz System THEN administrators SHALL be able to enable/disable individual Core Analysis
   Crews via Feature Flags
2. WHEN Core Analysis Crews are disabled THEN THE FinWiz System SHALL continue operating with remaining enabled crews
3. WHEN crew configurations change THEN THE FinWiz System SHALL apply changes without requiring full restart
4. WHEN debugging issues THEN administrators SHALL have access to detailed logging for each crew's execution
5. IF crew configurations are invalid THEN THE FinWiz System SHALL provide clear error messages and remediation
   guidance

### Requirement 9: Integration with Existing Features

**User Story:** As a financial planner, I want the restored analysis crews to enhance the existing portfolio review
and investment discovery features, so that I receive more comprehensive and actionable insights.

#### Acceptance Criteria

1. WHEN Portfolio Review executes THEN it SHALL have access to current market analysis from all Core Analysis Crews
2. WHEN investment discovery runs THEN it SHALL incorporate insights from stock, ETF, and crypto analysis
3. WHEN rebalancing recommendations are generated THEN they SHALL consider current market conditions from Core
   Analysis Crews
4. WHEN the final report is created THEN it SHALL integrate insights from all Core Analysis Crews into a cohesive
   narrative
5. IF Core Analysis Crews provide conflicting signals THEN THE FinWiz System SHALL highlight conflicts and provide
   balanced perspectives

### Requirement 10: Error Handling and Resilience

**User Story:** As a system user, I want the analysis system to be resilient to failures and provide meaningful
feedback when issues occur, so that I can understand system status and take appropriate action.

#### Acceptance Criteria

1. WHEN a Core Analysis Crew encounters an error THEN it SHALL log detailed error information and continue with
   available data
2. WHEN external APIs fail THEN Core Analysis Crews SHALL implement fallback strategies and cached data usage
3. WHEN data quality issues are detected THEN THE FinWiz System SHALL flag problematic data and adjust confidence
   scores
4. WHEN system recovery is needed THEN Core Analysis Crews SHALL implement retry logic with exponential backoff
5. IF critical failures occur THEN THE FinWiz System SHALL provide clear user feedback and suggested remediation
   steps

### Requirement 11: Data Freshness and Quality Assurance

**User Story:** As a financial analyst, I want to ensure that all market data used in analysis is no older than 1 day,
so that investment recommendations are based on current market conditions and remain relevant.

#### Acceptance Criteria

1. WHEN crews access market data THEN they SHALL validate that data timestamps are no older than 24 hours from current time
2. WHEN stale data is detected THEN the system SHALL attempt to refresh data from primary sources before proceeding
3. WHEN data cannot be refreshed THEN crews SHALL flag the analysis with data freshness warnings and reduced confidence scores
4. WHEN multiple data sources are available THEN the system SHALL prioritize the most recent data source
5. WHEN cached data is used THEN it SHALL be automatically invalidated after 24 hours regardless of cache TTL settings
6. IF real-time data is unavailable THEN the system SHALL clearly indicate the age of data used in analysis and adjust 
recommendations accordingly
7. WHEN market hours are considered THEN the system SHALL account for weekend and holiday periods when determining 
acceptable data age

### Requirement 12: Backward Compatibility and Data Integration Fix

**User Story:** As a system operator, I want the core market analysis restoration to fix the data integration bug
while maintaining full compatibility with existing features, so that the system works correctly without disrupting
current functionality.

#### Acceptance Criteria

1. WHEN core market analysis crews are added THEN existing portfolio review functionality SHALL continue to work with
 enhanced market context
2. WHEN the dual-crew architecture is implemented THEN existing discovery crews SHALL maintain their current "top 10" 
screening behavior unchanged
3. WHEN data consolidation is fixed THEN the system SHALL no longer log "Core analysis data missing" warnings
4. WHEN consolidated_data is populated THEN it SHALL contain both core analysis results and discovery results under 
appropriate keys
5. WHEN existing report generation runs THEN it SHALL produce consistent outputs with enhanced core analysis data
6. WHEN the flow orchestration is updated THEN existing API endpoints and interfaces SHALL remain stable and backward
 compatible
7. WHEN the data integration bug is fixed THEN portfolio holdings SHALL receive proper grades instead of fallback grade
 D values
8. IF any existing functionality is affected THEN changes SHALL be clearly documented with migration paths

### Requirement 13: Data Integration Bug Resolution

**User Story:** As a system architect, I want to fix the critical data integration bug where core analysis data is
 missing despite crews being marked as available, so that the data consolidation system works correctly and portfolio
  holdings receive proper analysis grades.

#### Acceptance Criteria

1. WHEN core market analysis crews execute THEN their outputs SHALL be stored with correct crew names for data
 consolidation retrieval
2. WHEN the data consolidation system queries for crew data THEN it SHALL find core analysis results under keys
 "stock", "etf", "crypto"
3. WHEN consolidated_data is populated THEN it SHALL contain actual crew results instead of empty dictionaries
4. WHEN the flow logs consolidation status THEN it SHALL report "Consolidated data from 3 crews (including 
3 core analysis crews)" instead of 0
5. WHEN portfolio holdings are analyzed THEN they SHALL receive proper grades based on actual analysis instead of fallback grade D
6. WHEN the system checks core analysis availability THEN the status SHALL accurately reflect actual data availability
7. WHEN the reporter input is prepared THEN it SHALL include core analysis data from the integration system
8. IF crew execution succeeds but data is not found THEN the system SHALL log detailed debugging information to identify
 the root cause

### Requirement 14: Testing and Quality Assurance

**User Story:** As a developer, I want comprehensive testing coverage for the restored analysis crews and data integration
 fix, so that system reliability is maintained and regressions are prevented.

#### Acceptance Criteria

1. WHEN crew code is modified THEN unit tests SHALL validate individual crew functionality with mocked dependencies
2. WHEN integration testing is performed THEN tests SHALL verify proper data flow between crews and integration systems
3. WHEN data integration testing is conducted THEN tests SHALL verify that core analysis data is properly stored and retrieved
4. WHEN regression testing is performed THEN tests SHALL ensure that restored functionality doesn't break existing features
5. WHEN test failures occur THEN they SHALL provide clear diagnostic information for rapid issue resolution
6. WHEN data freshness testing is performed THEN tests SHALL verify that stale data detection and refresh mechanisms 
work correctly
7. WHEN backward compatibility testing is conducted THEN tests SHALL verify that all existing features continue to work
 as expected
8. WHEN dual-crew architecture testing is performed THEN tests SHALL verify that both core analysis and Discovery
   Crews work correctly

### Requirement 15: Discovery Results Integration with Report Generation

**User Story:** As a financial analyst, I want the A+ investment discovery results to be properly integrated into the
final report, so that I can see the discovered opportunities and make informed investment decisions based on the
complete analysis.

#### Acceptance Criteria

1. WHEN investment discovery crews execute successfully THEN their results SHALL be passed to the report crew via Flow state
2. WHEN the report crew checks for discovery data THEN it SHALL find `aplus_opportunities`
 or `investment_discovery_structured` in the inputs
3. WHEN discovery results are available THEN the report SHALL display the "Opportunités A+ Découvertes" section with 
actual discovered opportunities
4. WHEN the report is generated THEN it SHALL NOT show "Discovery status not provided" messages if discovery was executed
5. WHEN discovery crews find A+ opportunities THEN the report SHALL list them by asset class (stocks, ETFs, crypto) with
 details
6. WHEN the Flow passes data to the report crew THEN it SHALL include all discovery-related state fields
 (aplus_opportunities, investment_discovery_structured, investment_discovery_result)
7. WHEN the report crew receives discovery data THEN it SHALL properly extract and format the opportunities for display
8. IF discovery was not run THEN the report SHALL clearly indicate "Discovery not run - use --discovery flag" instead 
of showing confusing status messages
9. WHEN the Flow passes data to the report crew THEN it SHALL include ALL required inputs (validated_tickers_list,
 discovery_status, backtesting_status, data_availability_summary_formatted)
10. WHEN the report crew validates inputs THEN it SHALL NOT show "INSUFFICIENT / PARTIAL" errors for missing required fields
# Requirements Document

## Introduction

The FinWiz reporting system currently suffers from communication breakdowns between different crews (Stock, ETF, Crypto, Discovery) and the final Report crew. This results in incomplete reports with missing SEC/EDGAR citations, unavailable market sentiment data, unvalidated tickers, and lack of upstream data integration. This feature will establish a robust data integration system that ensures all crew outputs are properly collected, validated, and made available to downstream crews, particularly the Report crew.

## Requirements

### Requirement 1

**User Story:** As a financial analyst using FinWiz, I want all reports to include complete SEC/EDGAR citations with filing dates and excerpts, so that I can verify the source data and comply with regulatory standards.

#### Acceptance Criteria

1. WHEN the Stock crew analyzes a ticker THEN it SHALL extract and store 10-K filing data including Business Overview, MD&A, Risk Factors, Liquidity, and Segments
2. WHEN the Stock crew processes SEC data THEN it SHALL include SEC/EDGAR citation URLs and filing dates for each extracted section
3. WHEN the Report crew generates a final report THEN it SHALL access and integrate all available SEC/EDGAR data with proper citations
4. WHEN SEC/EDGAR data is unavailable THEN the system SHALL clearly indicate the limitation and provide alternative data sources

### Requirement 2

**User Story:** As a financial analyst, I want market sentiment analysis to be consistently available in reports with aggregated scores and source attribution, so that I can understand market perception of recommended assets.

#### Acceptance Criteria

1. WHEN any crew performs sentiment analysis THEN it SHALL store results in a standardized format with aggregated scores
2. WHEN sentiment data is collected THEN it SHALL include Positive/Neutral/Negative distribution percentages
3. WHEN sentiment analysis is performed THEN it SHALL provide Top 3 sentiment sources with URLs and publication dates
4. WHEN the Report crew generates output THEN it SHALL access and integrate all available sentiment data
5. IF sentiment data is unavailable THEN the system SHALL indicate this clearly and explain the impact on analysis quality

### Requirement 3

**User Story:** As a financial analyst, I want all ticker symbols to be validated and verified across all crews, so that I can trust the accuracy of the analysis and avoid errors from invalid symbols.

#### Acceptance Criteria

1. WHEN any crew processes ticker symbols THEN it SHALL validate them against authoritative sources
2. WHEN validation is complete THEN each crew SHALL store validated_tickers[], validated_etfs[], and validated_symbols[] arrays
3. WHEN the Report crew accesses ticker data THEN it SHALL have access to all validation results from upstream crews
4. WHEN ticker validation fails THEN the system SHALL provide clear error messages and suggest alternatives
5. WHEN generating reports THEN all ticker symbols SHALL be marked with their validation status

### Requirement 4

**User Story:** As a system administrator, I want a centralized data integration system that ensures all crew outputs are accessible to downstream crews, so that no data is lost in the workflow and reports are complete.

#### Acceptance Criteria

1. WHEN any crew completes its analysis THEN it SHALL store outputs in a standardized, accessible format
2. WHEN crews store data THEN it SHALL include metadata about data source, timestamp, and validation status
3. WHEN the Report crew starts execution THEN it SHALL have access to all available upstream crew outputs
4. WHEN upstream data is missing THEN the system SHALL provide clear paths to the expected data locations
5. WHEN data integration fails THEN the system SHALL log specific error messages and provide recovery suggestions

### Requirement 5

**User Story:** As a financial analyst, I want A+ scoring opportunities to be consistently integrated into final reports, so that I can identify the highest-quality investment opportunities.

#### Acceptance Criteria

1. WHEN the Investment Discovery crew identifies A+ opportunities THEN it SHALL store them in a standardized format
2. WHEN A+ opportunities are available THEN they SHALL include allocation recommendations and replacement notes
3. WHEN the Report crew generates output THEN it SHALL integrate all available A+ opportunities
4. WHEN A+ data is integrated THEN it SHALL update portfolio allocation recommendations accordingly
5. IF A+ opportunities are unavailable THEN the system SHALL indicate this and provide standard recommendations

### Requirement 6

**User Story:** As a financial analyst, I want to ensure that all crew outputs are current and synchronized, so that final reports reflect the most recent analysis and avoid using stale data.

#### Acceptance Criteria

1. WHEN any crew generates output THEN it SHALL include timestamp metadata indicating when the analysis was performed
2. WHEN the Report crew accesses upstream data THEN it SHALL check file timestamps and warn about stale data (older than 24 hours)
3. WHEN stale data is detected THEN the system SHALL provide options to refresh upstream analysis or proceed with warnings
4. WHEN crews run in sequence THEN the system SHALL coordinate execution to ensure data freshness
5. WHEN generating final reports THEN all data sources SHALL be timestamped and their freshness status clearly indicated

### Requirement 7

**User Story:** As a developer maintaining the FinWiz system, I want clear error reporting and data flow visibility, so that I can quickly identify and resolve integration issues.

#### Acceptance Criteria

1. WHEN data integration fails THEN the system SHALL provide specific error messages with exact file paths
2. WHEN crews cannot access upstream data THEN the system SHALL list expected vs actual data locations
3. WHEN the Report crew starts THEN it SHALL log all available upstream data sources and any missing components
4. WHEN integration issues occur THEN the system SHALL provide concrete next steps for resolution
5. WHEN debugging data flow THEN developers SHALL have access to data lineage and transformation logs

### Requirement 8

**User Story:** As a financial analyst, I want reports to include comprehensive backtesting performance metrics from A+ opportunities, so that I can evaluate investment recommendations based on historical performance data.

#### Acceptance Criteria

1. WHEN the Discovery crew identifies A+ opportunities THEN it SHALL include backtesting results with annualized_return, sharpe_ratio, max_drawdown, and win_rate
2. WHEN backtesting data is available THEN it SHALL include regime consistency scores showing performance across bull/bear/sideways markets
3. WHEN the Report crew generates output THEN it SHALL extract and display backtesting performance metrics in a dedicated section
4. WHEN backtesting results are presented THEN they SHALL include performance comparison tables across different market regimes
5. IF backtesting data is unavailable THEN the system SHALL clearly indicate this limitation and its impact on recommendation confidence

### Requirement 9

**User Story:** As a financial analyst, I want reports to include current market context indicators (VIX, inflation, interest rates, regime type), so that I can understand the market environment influencing investment recommendations.

#### Acceptance Criteria

1. WHEN the Discovery crew performs analysis THEN it SHALL capture market context including regime_type, vix_level, inflation_rate, and interest_rate_trend
2. WHEN market context is available THEN it SHALL include market_stress_level assessment
3. WHEN the Report crew generates output THEN it SHALL extract and display market context indicators in risk assessment and allocation sections
4. WHEN market context is presented THEN it SHALL explain how current conditions influence allocation recommendations
5. IF market context data is unavailable THEN the system SHALL use conservative assumptions and document this limitation

### Requirement 10

**User Story:** As a financial analyst, I want reports to include the discovery methodology details (screening criteria, thresholds, validation statistics), so that I can understand how A+ opportunities were identified and validated.

#### Acceptance Criteria

1. WHEN the Discovery crew performs screening THEN it SHALL store discovery criteria including ROE thresholds, debt ratios, market cap minimums, and revenue growth requirements
2. WHEN discovery is complete THEN it SHALL include screening statistics showing total assets screened vs candidates found
3. WHEN the Report crew generates output THEN it SHALL extract and display discovery methodology in a dedicated section
4. WHEN methodology is presented THEN it SHALL include fundamental_score and technical_score breakdowns for each A+ candidate
5. WHEN validation results are available THEN the report SHALL include validation success rates and failure analysis with alternative suggestions
# Requirements Document

## Introduction

This specification defines practical enforcement of essential FinWiz features across CrewAI crews to ensure consistent analysis quality and proper tool utilization. The goal is to identify and fix gaps where crews are not using available tools that would improve their analysis quality, without over-engineering or adding unnecessary complexity.

Analysis of the current crew implementations shows that while FinWiz has many powerful tools available, some crews are not consistently using them. For example, some crews may skip quantitative analysis, others may not validate ticker symbols, or fail to generate proper schema-compliant outputs. This leads to inconsistent analysis quality across different asset classes.

This enhancement will focus on the essential features that directly impact analysis quality and user value, ensuring all crews use the minimum necessary set of tools to deliver comprehensive, reliable financial analysis while avoiding unnecessary complexity or "cool but unused" features.

## Requirements

### Requirement 1: Essential Tool Usage Audit

**User Story:** As a FinWiz user, I want all crews to use the essential analysis tools that are already implemented, so that I get consistent, high-quality analysis across all asset classes without gaps in coverage.

#### Acceptance Criteria

1. WHEN Stock crew analyzes securities THEN it SHALL use the Quantitative Analysis Tool and Enhanced SEC Analysis Tool that are already available
2. WHEN ETF crew analyzes funds THEN it SHALL use the Enhanced ETF Analysis Tool and factsheet extraction capabilities that exist
3. WHEN Crypto crew analyzes digital assets THEN it SHALL use the Enhanced Crypto Analysis Tool and CoinMarketCap integration that are implemented
4. WHEN any crew performs analysis THEN it SHALL validate ticker symbols using the existing Ticker Validation Tool
5. IF essential tools are not being used THEN the system SHALL identify and document the gaps for correction

### Requirement 2: Consistent Output Schema Compliance

**User Story:** As a data consumer, I want all crews to generate properly structured outputs that match FinWiz schemas, so that downstream processing and integration works reliably.

#### Acceptance Criteria

1. WHEN crews complete analysis THEN they SHALL generate machine-readable JSON appendices using existing FinWiz schemas (TenKInsight, MarketSentiment, RiskAssessmentStandardized, etc.)
2. WHEN schema objects are created THEN they SHALL include proper validation and error handling for malformed data
3. WHEN outputs are generated THEN they SHALL include required fields like timestamps, source references, and provenance information
4. WHEN schema validation fails THEN crews SHALL log the specific validation errors and attempt correction
5. IF schema compliance cannot be achieved THEN crews SHALL provide fallback structured output with clear documentation

### Requirement 3: Risk Assessment Standardization

**User Story:** As a risk manager, I want consistent risk scoring across all asset classes, so that I can compare and aggregate risks properly in portfolio decisions.

#### Acceptance Criteria

1. WHEN any crew assesses risk THEN it SHALL use the existing Standardized Risk Scoring methodology for consistent 0-5 scale scoring
2. WHEN risk objects are generated THEN they SHALL match the RiskAssessmentStandardized schema that is already defined
3. WHEN risk factors are identified THEN they SHALL be properly categorized using existing risk taxonomy
4. WHEN quantitative risk metrics are calculated THEN crews SHALL use the available Quantitative Analysis Tool for VaR and drawdown calculations
5. IF risk assessment tools fail THEN crews SHALL document the failure and use manual assessment with clear methodology

### Requirement 4: Report Crew Tool Restrictions

**User Story:** As a system architect, I want the Report crew to follow the established tool restriction policy, so that the final reporter maintains clean separation of concerns and only consumes upstream analysis.

#### Acceptance Criteria

1. WHEN the investment reporter agent executes THEN it SHALL have an empty tools list and make no external API calls
2. WHEN Report crew initializes THEN it SHALL use the existing ToolRestrictionValidator to ensure compliance
3. WHEN reporter processes data THEN it SHALL only consume validated upstream context from prior crew tasks
4. WHEN tool violations are detected THEN the system SHALL prevent execution and provide clear error messages
5. IF validation fails THEN the system SHALL provide specific guidance on how to fix tool restriction violations

### Requirement 5: Translation Task Implementation

**User Story:** As an international user, I want consistent translation capabilities across all crews, so that reports are available in French with proper formatting preservation.

#### Acceptance Criteria

1. WHEN crews generate final reports THEN they SHALL include translation tasks that are already configured in existing crews
2. WHEN translation agents execute THEN they SHALL have no tools and only consume upstream HTML context
3. WHEN translation is performed THEN it SHALL preserve exact HTML structure and CSS styling while translating text content
4. WHEN crews are missing translation tasks THEN they SHALL be updated to include the standard translation pattern
5. IF translation is not needed THEN crews SHALL clearly document why translation is skipped
# Requirements Document: Deep Analysis Crews for Single-Ticker Analysis

## Introduction

This spec defines the creation of **ONE unified CrewAI crew** (`DeepAnalysisCrew`) for in-depth analysis of single tickers across all asset classes: stocks, ETFs, and cryptocurrencies. This crew addresses the architectural mismatch where existing discovery crews (`StockCrew`, `EtfCrew`, `CryptoCrew`) are designed to screen and analyze 10 assets but are being incorrectly used for deep analysis of individual holdings in the portfolio analysis workflow.

**Design Philosophy:**

- **Unix Philosophy:** One task, one outcome - analyze a single ticker and return comprehensive analysis
- **No Duplication:** One crew handles all asset classes through dynamic tool routing
- **Accuracy First:** Fresh data for real money decisions
- **Smart API Usage:** Tool-level batching and context sharing minimize redundant calls

## Complete Crew Inventory & Roles

### Discovery Crews (Find Top 10 Candidates)

**1. StockCrew** - Screen and identify top 10 promising stocks
- **Purpose:** Discovery of new stock opportunities
- **Input:** Market screening criteria
- **Output:** Top 10 stocks with analysis
- **Use Case:** "Find me the best growth stocks"
- **NOT for:** Analyzing specific holdings you already own

**2. ETFCrew** - Screen and identify top 10 stable ETFs
- **Purpose:** Discovery of new ETF opportunities
- **Input:** ETF screening criteria (expense ratio, AUM, tracking error)
- **Output:** Top 10 ETFs with factsheet analysis
- **Use Case:** "Find me low-cost diversified ETFs"
- **NOT for:** Analyzing specific ETFs you already own

**3. CryptoCrew** - Identify top 10 promising cryptocurrencies
- **Purpose:** Discovery of new crypto opportunities
- **Input:** Crypto screening criteria (market cap, volume, adoption)
- **Output:** Top 10 cryptocurrencies with analysis
- **Use Case:** "Find me promising DeFi projects"
- **NOT for:** Analyzing specific crypto you already own

### Deep Analysis Crew (Analyze Single Ticker) ⭐ NEW

**4. DeepAnalysisCrew** - Comprehensive analysis of ONE specific ticker
- **Purpose:** Portfolio holdings evaluation
- **Input:** Single ticker + asset_class parameter
- **Output:** Grade (A+ to F), composite score, recommendation
- **Use Case:** "Analyze my AAPL holding - should I keep or sell?"
- **Dynamic Routing:** Routes to appropriate tools based on asset_class
- **Replaces:** Need for 3 separate deep analysis crews

### Portfolio Optimization Crews

**5. InvestmentDiscoveryCrew** - Find A+ opportunities to improve portfolio
- **Purpose:** Discover A+ grade opportunities across all asset classes
- **Input:** Portfolio context and improvement needs
- **Output:** A+ candidates with backtesting validation
- **Use Case:** "Find A+ alternatives for my underperforming holdings"
- **Runs:** AFTER portfolio analysis (knows what needs improvement)

**6. PortfolioRebalancingCrew** - Optimize existing portfolio
- **Purpose:** Analyze holdings and generate rebalancing recommendations
- **Input:** Portfolio holdings with grades
- **Output:** Trade recommendations, price targets, alternatives
- **Use Case:** "How should I rebalance my portfolio?"
- **Coordinates:** Uses HoldingAnalyzerOrchestrator for deep analysis

### Reporting Crew

**7. ReportCrew** - Consolidate all analysis into final report
- **Purpose:** Generate comprehensive investment report
- **Input:** All crew outputs (portfolio, discovery, rebalancing)
- **Output:** French-language HTML report
- **Use Case:** Final consolidated recommendations
- **No Tools:** Consumes context only (no external API calls)

## Problem Statement

### Issue 1: Architectural Mismatch (Crew Design)

Currently, when `analyze_holdings_deep()` in the flow orchestrator needs to analyze individual holdings, it calls the discovery crews with a single ticker. However, these crews are designed to:
- Screen and identify "top 10" assets (stocks/ETFs/cryptos)
- Perform comparative analysis across multiple assets
- Generate discovery-oriented recommendations

This architectural mismatch causes reasoning agents to enter infinite loops, asking for "10 tickers" when only 1 is provided, resulting in 3-6 hour hangs with `'ready': False` states.

**Evidence from logs:**
- ETF crew hung for 3+ hours on single ticker `L0CK.DE`
- Reasoning agent repeatedly asked for: "tickers list (<=10)", "KB auth", "compute_budget"
- Stock and crypto crews have identical "top 10" design and will fail the same way when cache expires

### Issue 2: Flow Sequence Logic Error (CRITICAL)

The current flow has **discovery BEFORE portfolio analysis**, which is backwards from the logical business process:

**Current (INCORRECT) Flow:**
```
1. validate_data_integration
2. check_crypto, check_stock, check_etf (discovery) ← WRONG: Before we know what we own
3. check_portfolio ← WRONG: Portfolio analysis AFTER discovery
4. analyze_holdings_deep
5. match_alternatives ← WRONG: Matching from empty discovery results
6. update_portfolio_review_with_deep_analysis
7. check_investment_discovery
8. check_portfolio_rebalancing
9. report
```

**Problems:**
1. ❌ **Discovery runs before portfolio analysis** - We discover assets before knowing what we own
2. ❌ **Can't find alternatives** - Alternative matching happens before discovery provides A+ candidates
3. ❌ **Wasted resources** - Discovery may find assets we already own
4. ❌ **Portfolio generated twice** - Once in check_portfolio, again in update_portfolio_review
5. ❌ **Rebalancing lacks context** - Runs in parallel with discovery, missing A+ opportunities

**Why This Is Wrong:**
- Discovery crews are designed to find "top 10" candidates
- We need to know what we own BEFORE finding alternatives
- Alternative matching identifies needs, discovery provides solutions
- Portfolio should be updated ONCE with complete data

**Correct Business Logic:**
1. **Analyze what you have** (portfolio analysis)
2. **Grade your holdings** (deep analysis)
3. **Identify needs** (match alternatives for underperformers)
4. **Find solutions** (discovery provides A+ candidates)
5. **Update portfolio** (merge deep analysis + A+ alternatives)
6. **Optimize allocations** (rebalancing with complete data)
7. **Present recommendations** (final report)

## Solution Overview

### Solution 1: Create Unified Deep Analysis Crew

Create **ONE unified deep analysis crew** that handles all asset classes through dynamic tool routing:

**New Unified Deep Analysis Crew:**

- **DeepAnalysisCrew** - Analyzes one ticker of ANY asset class (stock/ETF/crypto)
- Routes to appropriate tools based on `asset_class` parameter
- Single codebase, no duplication across asset classes
- Dynamic tool selection: `get_tools_for_asset_class(asset_class)`

**Existing Discovery Crews (Keep & Document):**

1. **StockCrew** - Screen and find top 10 stocks (discovery only)
2. **EtfCrew** - Screen and find top 10 ETFs (discovery only)
3. **CryptoCrew** - Screen and find top 10 cryptos (discovery only)

**Documentation Actions:**

- Add header comments to discovery crew task files clarifying purpose
- Document routing logic: discovery vs deep analysis use cases
- Update crew docstrings to explain discovery-only purpose

**Benefits:**

- Maximum code reuse (one crew for all asset classes)
- No duplication across stock/ETF/crypto implementations
- Separation of concerns (discovery vs deep analysis)
- Clean, maintainable codebase
- Simple routing: asset_class parameter determines tools
- Consistent structure across all asset types

### Solution 2: Fix Flow Sequence (CRITICAL)

Correct the flow to match logical business process:

**Optimized (CORRECT) Flow:**
```
Phase 1: Data Validation
├─ validate_data_integration (start)

Phase 2: Portfolio Analysis (Analyze What You Have)
├─ check_portfolio
│  └─ Generates initial portfolio review
│  └─ Identifies holdings that need deep analysis

Phase 3: Deep Analysis & Update (Evaluate & Merge)
├─ analyze_and_update_portfolio (consolidated atomic operation)
│  ├─ Deep analysis: DeepAnalysisCrew analyzes each holding
│  ├─ Match alternatives: Identifies holdings needing alternatives (grade < B)
│  └─ Update portfolio: Merges deep analysis + alternatives (ONCE)

Phase 4: Discovery (Find New Opportunities)
├─ check_crypto, check_stock, check_etf (parallel)
│  └─ Discovery crews find top 10 candidates
│  └─ Run AFTER we know what we need
├─ check_investment_discovery
│  └─ Consolidates discovery results
│  └─ Finds A+ opportunities
│  └─ Validates through backtesting

Phase 5: Rebalancing (Optimize Allocations)
├─ check_portfolio_rebalancing
│  └─ Generates trade recommendations
│  └─ Optimizes allocations with A+ opportunities

Phase 6: Reporting (Consolidate & Present)
├─ pre_validate_reporter_input → report
   └─ Generates final HTML report
```

**Key Improvements:**
1. ✅ Portfolio analysis BEFORE discovery (logical order)
2. ✅ Consolidated operation: deep analysis + alternatives + update (atomic)
3. ✅ Portfolio generated ONCE (not twice)
4. ✅ Discovery runs AFTER we know what needs improvement
5. ✅ Rebalancing has complete data (portfolio + discoveries)
6. ✅ Alternative matching identifies needs, discovery provides solutions

**Flow Rationale:**
- **Validate First:** Ensure data systems operational
- **Analyze Portfolio:** Understand what you own
- **Deep Analysis:** Grade each holding (A+ to F)
- **Discovery:** Find A+ alternatives for underperformers
- **Rebalancing:** Optimize with complete information
- **Report:** Present comprehensive recommendations

## Requirements

### Requirement 1: Single Ticker Analysis with Dynamic Asset Class Routing

**User Story:** As a portfolio analyst, I want to perform deep analysis on a single ticker of any asset class (stock/ETF/crypto), so that I can evaluate individual holdings without triggering discovery workflows.

#### Acceptance Criteria

1. WHEN DeepAnalysisCrew receives a single ticker input THEN it SHALL analyze only that ticker without requesting additional tickers
2. WHEN DeepAnalysisCrew is initialized THEN it SHALL accept both `ticker` and `asset_class` parameters
3. WHEN `asset_class` parameter is provided THEN the crew SHALL route to appropriate tools (stock/ETF/crypto)
4. WHEN reasoning is enabled THEN the agent SHALL recognize single-ticker mode and proceed with analysis
5. IF no ticker is provided THEN the crew SHALL raise a clear error indicating ticker is required
6. IF invalid asset_class is provided THEN the crew SHALL raise ValueError with valid options
7. WHEN the ticker parameter is provided THEN it SHALL be the primary input (not optional or discovery-based)

### Requirement 2: Comprehensive Asset-Specific Analysis

**User Story:** As a portfolio analyst, I want comprehensive analysis appropriate to each asset class, so that I can make informed keep/sell decisions.

#### Acceptance Criteria - Stock Analysis

1. WHEN analyzing a stock THEN the crew SHALL extract fundamental data (P/E ratio, EPS, revenue growth, debt levels)
2. WHEN analyzing a stock THEN the crew SHALL analyze 10-K/10-Q filings using SEC EDGAR data
3. WHEN analyzing a stock THEN the crew SHALL perform technical analysis (RSI, MACD, Bollinger Bands, support/resistance)
4. WHEN analyzing a stock THEN the crew SHALL calculate quantitative metrics (volatility, Sharpe ratio, beta)
5. WHEN analyzing a stock THEN the crew SHALL assess risk using standardized 0-5 scale

#### Acceptance Criteria - ETF Analysis

1. WHEN analyzing an ETF THEN the crew SHALL extract factsheet data (expense ratio, AUM, holdings, replication method)
2. WHEN analyzing an ETF THEN the crew SHALL calculate tracking error against benchmark
3. WHEN analyzing an ETF THEN the crew SHALL perform technical analysis (RSI, MACD, Bollinger Bands, support/resistance)
4. WHEN analyzing an ETF THEN the crew SHALL calculate quantitative metrics (tracking error, volatility, Sharpe ratio)
5. WHEN analyzing an ETF THEN the crew SHALL assess risk using standardized 0-5 scale

#### Acceptance Criteria - Crypto Analysis

1. WHEN analyzing a crypto THEN the crew SHALL extract on-chain metrics (active addresses, TVL, transaction volume)
2. WHEN analyzing a crypto THEN the crew SHALL analyze tokenomics (supply, inflation, staking rewards)
3. WHEN analyzing a crypto THEN the crew SHALL perform technical analysis (RSI, MACD, Bollinger Bands, support/resistance)
4. WHEN analyzing a crypto THEN the crew SHALL calculate quantitative metrics (volatility, correlation to BTC/ETH)
5. WHEN analyzing a crypto THEN the crew SHALL assess risk using standardized 0-5 scale

#### Acceptance Criteria - Common to All

1. WHEN analyzing any asset THEN the crew SHALL validate ticker existence on appropriate exchanges
2. WHEN analyzing any asset THEN the crew SHALL use `StandardizedSentimentTool` for market sentiment
3. WHEN analyzing any asset THEN the crew SHALL use `QuantitativeAnalysisTool` with appropriate asset_class parameter

### Requirement 3: Standardized Output Schema

**User Story:** As a system integrator, I want standardized output format across all asset classes, so that I can parse and cache analysis results consistently.

#### Acceptance Criteria

1. WHEN analysis completes THEN DeepAnalysisCrew SHALL return unified `DeepAnalysisResult` Pydantic model
2. WHEN returning results THEN the output SHALL include fundamental_score, technical_score, risk_score, composite_score
3. WHEN returning results THEN the output SHALL include grade (A+ to F) calculated from composite_score
4. WHEN returning results THEN the output SHALL include asset_class field to identify ticker type
5. WHEN returning results THEN the output SHALL conform to existing FinWiz schema standards
6. WHEN returning results THEN the output SHALL be cacheable by `analysis_cache_manager`
7. WHEN returning results THEN the output SHALL include ticker, asset_class, analyzed_at timestamp, crew_name
8. WHEN returning results THEN the output SHALL include data_freshness timestamps for transparency

### Requirement 4: Integration with Flow Orchestrator (Consolidated Architecture)

**User Story:** As a flow orchestrator, I want seamless integration with deep portfolio analysis in a single atomic operation, so that I can analyze holdings, match alternatives, and update portfolio review efficiently without redundant operations.

#### Acceptance Criteria - Consolidated Flow Method

1. WHEN `analyze_and_update_portfolio()` is called THEN it SHALL perform deep analysis, alternative matching, and portfolio update in one atomic operation
2. WHEN deep analysis is disabled THEN the method SHALL return early without processing
3. WHEN portfolio review data is unavailable THEN the method SHALL log warning and return empty result
4. WHEN any step fails THEN the method SHALL handle errors gracefully and continue with degraded functionality
5. WHEN all steps complete THEN the method SHALL return consolidated results including analysis count, alternatives count, and update status

#### Acceptance Criteria - Deep Analysis Integration

1. WHEN `analyze_and_update_portfolio()` calls DeepAnalysisCrew THEN it SHALL pass both ticker and asset_class parameters
2. WHEN DeepAnalysisCrew completes THEN it SHALL return results compatible with `_parse_crew_output_for_holding()`
3. WHEN DeepAnalysisCrew is instantiated THEN it SHALL use dynamic tool routing based on asset_class
4. WHEN DeepAnalysisCrew executes THEN it SHALL respect the same timeout and retry configurations
5. WHEN DeepAnalysisCrew fails THEN it SHALL raise exceptions that allow graceful degradation
6. WHEN flow orchestrator routes analysis THEN it SHALL use DeepAnalysisCrew for single-ticker analysis
7. WHEN flow orchestrator routes analysis THEN it SHALL use discovery crews for "top 10" screening
8. WHEN flow orchestrator instantiates crew THEN it SHALL use direct instantiation pattern (not factory)

#### Acceptance Criteria - Alternative Matching Integration

1. WHEN deep analysis completes THEN the method SHALL automatically match alternatives for underperforming holdings (grade C, D, or F)
2. WHEN matching alternatives THEN it SHALL use existing `AlternativeFinder` tool
3. WHEN alternatives are found THEN they SHALL be stored in structured Flow state
4. WHEN alternative matching fails THEN it SHALL log error and continue without alternatives

#### Acceptance Criteria - Portfolio Update Integration

1. WHEN deep analysis and alternatives are complete THEN the method SHALL regenerate portfolio review with enriched data
2. WHEN regenerating portfolio review THEN it SHALL pass Flow state containing deep analysis results and alternatives
3. WHEN portfolio review is updated THEN it SHALL reload the updated JSON into Flow state
4. WHEN portfolio update fails THEN it SHALL log error and retain original portfolio review

#### Acceptance Criteria - Flow Sequence Correction (CRITICAL - UPDATED)

**Logical Business Flow:** Analyze what you have → Grade holdings → Find better alternatives → Update portfolio → Optimize allocations → Report

1. WHEN `validate_data_integration` completes THEN it SHALL trigger `check_portfolio` (Phase 2: Portfolio Analysis)
2. WHEN `check_portfolio` completes THEN it SHALL trigger `analyze_and_update_portfolio` (Phase 3: Deep Analysis & Update)
3. WHEN `analyze_and_update_portfolio` completes THEN it SHALL trigger discovery crews (check_crypto, check_stock, check_etf) in parallel (Phase 4: Discovery)
4. WHEN all discovery crews complete THEN they SHALL trigger `check_investment_discovery` (Phase 4: Discovery Consolidation)
5. WHEN `check_investment_discovery` completes THEN it SHALL trigger `check_portfolio_rebalancing` (Phase 5: Rebalancing)
6. WHEN `check_portfolio_rebalancing` completes THEN it SHALL trigger `pre_validate_reporter_input` (Phase 6: Reporting)
7. WHEN `pre_validate_reporter_input` completes THEN it SHALL trigger `report` (Phase 6: Final Report)

**Critical Flow Corrections:**
- ✅ Portfolio analysis happens BEFORE discovery (not after)
- ✅ Discovery crews run AFTER we know what holdings need alternatives
- ✅ Rebalancing has access to BOTH portfolio analysis AND discovery results
- ✅ Portfolio review generated ONCE with complete data (not twice)
- ✅ Alternative matching happens BEFORE discovery (identifies needs)
- ✅ Discovery provides A+ candidates to match those needs
- ✅ Portfolio update happens AFTER discovery (merges A+ alternatives)

**Flow Phases:**
1. **Phase 1: Validation** - `validate_data_integration` (check data systems)
2. **Phase 2: Portfolio Analysis** - `check_portfolio` (analyze what you have)
3. **Phase 3: Deep Analysis & Update** - `analyze_and_update_portfolio` (grade holdings, match alternatives, update portfolio)
4. **Phase 4: Discovery** - `check_crypto/stock/etf` → `check_investment_discovery` (find A+ opportunities)
5. **Phase 5: Rebalancing** - `check_portfolio_rebalancing` (optimize allocations)
6. **Phase 6: Reporting** - `pre_validate_reporter_input` → `report` (consolidate & present)

**Why This Order:**
- Discovery crews are designed to find "top 10" candidates (not analyze single tickers)
- We need to know what we own BEFORE finding alternatives
- Alternative matching identifies needs, discovery provides solutions
- Portfolio update merges deep analysis + A+ discoveries in one operation
- Rebalancing optimizes with complete information (portfolio + discoveries)

### Requirement 5: Reasoning-Enabled Design

**User Story:** As a developer, I want reasoning enabled for quality analysis, so that agents can plan and validate their approach before execution.

#### Acceptance Criteria

1. WHEN reasoning is enabled THEN the agent SHALL create a plan for single-ticker analysis
2. WHEN the reasoning plan is created THEN it SHALL set `'ready': True` for single-ticker inputs
3. WHEN the reasoning plan is created THEN it SHALL NOT request additional tickers, KB auth, or compute_budget
4. WHEN the reasoning plan is created THEN it SHALL identify required tools and data sources for the specific ticker
5. WHEN reasoning completes THEN the agent SHALL proceed to execution without loops
6. WHEN task descriptions are written THEN they SHALL explicitly state "analyze the provided ticker" not "screen 10 assets"

### Requirement 6: Tool and Data Source Usage

**User Story:** As an analyst agent, I want access to appropriate tools for each asset class, so that I can gather comprehensive data for analysis.

#### Acceptance Criteria - Stock Tools

1. WHEN analyzing a stock THEN the crew SHALL use `EnhancedSECAnalysisTool` for 10-K/10-Q filings
2. WHEN analyzing a stock THEN the crew SHALL use `QuantitativeAnalysisTool(asset_class="stock")` for metrics
3. WHEN analyzing a stock THEN the crew SHALL use `TickerValidationTool` to verify ticker existence
4. WHEN analyzing a stock THEN the crew SHALL use `YahooFinanceNewsTool` for company news

#### Acceptance Criteria - ETF Tools

1. WHEN analyzing an ETF THEN the crew SHALL use `EnhancedETFAnalysisTool` for factsheet data
2. WHEN analyzing an ETF THEN the crew SHALL use `QuantitativeAnalysisTool(asset_class="etf")` for metrics
3. WHEN analyzing an ETF THEN the crew SHALL use `TickerValidationTool` to verify ticker existence
4. WHEN analyzing an ETF THEN the crew SHALL use `ETFTrackingAnalysisTool` for tracking error

#### Acceptance Criteria - Crypto Tools

1. WHEN analyzing a crypto THEN the crew SHALL use `EnhancedCryptoAnalysisTool` for on-chain metrics
2. WHEN analyzing a crypto THEN the crew SHALL use `QuantitativeAnalysisTool(asset_class="crypto")` for metrics
3. WHEN analyzing a crypto THEN the crew SHALL use `TickerValidationTool` to verify ticker existence on Coinbase
4. WHEN analyzing a crypto THEN the crew SHALL use `CoinMarketCapTool` for market data

#### Acceptance Criteria - Common Tools

1. WHEN analyzing any asset THEN the crew SHALL use `StandardizedSentimentTool` for sentiment analysis
2. WHEN analyzing any asset THEN the crew SHALL use `TwelveDataIndicatorTool` for technical indicators
3. WHEN analyzing any asset THEN the crew SHALL use RAG tools for knowledge base integration
4. WHEN analyzing any asset THEN the crew SHALL use `ChartImgGeneratorTool` for visualizations (optional)

### Requirement 7: Performance and Data Freshness

**User Story:** As an investor, I want accurate, up-to-date analysis based on current market conditions, so that I can make informed decisions with real money.

#### Acceptance Criteria - Data Freshness (CRITICAL)

1. WHEN analyzing any asset THEN the crew SHALL fetch current market data (not cached stale data)
2. WHEN market conditions change THEN analysis SHALL reflect current reality, not historical snapshots
3. WHEN tools provide timestamps THEN the crew SHALL validate data freshness and flag stale data
4. WHEN data is older than acceptable threshold THEN the crew SHALL re-fetch or flag as unreliable
5. WHEN returning analysis THEN the crew SHALL include data-as-of timestamps for transparency

#### Acceptance Criteria - Performance

1. WHEN any crew executes THEN it SHALL complete within 5 minutes for a single ticker
2. WHEN any crew executes THEN it SHALL use async tasks where appropriate to parallelize I/O
3. WHEN any crew executes THEN it SHALL respect rate limits (max_rpm=20)
4. WHEN multiple holdings are analyzed THEN crews SHALL be called sequentially to respect rate limits
5. WHEN performance degrades THEN the system SHALL log warnings for investigation

#### Acceptance Criteria - Caching Strategy (REVISED)

1. WHEN caching is used THEN it SHALL be for static data only (company info, historical filings)
2. WHEN caching is used THEN it SHALL NOT be for market prices, sentiment, or time-sensitive data
3. WHEN cached data is used THEN the crew SHALL clearly indicate which data is cached vs fresh
4. WHEN analysis is critical (real money decisions) THEN fresh data SHALL be prioritized over cache
5. WHEN cache is considered THEN TTL SHALL be asset-class appropriate (e.g., 1 hour for prices, 24h for filings)

### Requirement 11: API Efficiency Through Intelligent Tool Usage

**User Story:** As a cost-conscious operator, I want to minimize redundant API calls without sacrificing data accuracy, so that the system is both economical and reliable.

#### Acceptance Criteria - Smart Batching (Tool-Level)

1. WHEN tools support batch operations THEN crews SHALL use batch APIs when analyzing multiple related data points
2. WHEN fetching multiple indicators THEN crews SHALL use multi-indicator APIs (e.g., TwelveData batch) instead of individual calls
3. WHEN analyzing related tickers THEN crews SHALL consolidate API calls where tools support it
4. WHEN tools don't support batching THEN crews SHALL make individual calls (accuracy over cost)
5. WHEN batching is used THEN it SHALL NOT compromise data freshness or accuracy

#### Acceptance Criteria - Context Sharing (Crew-Level)

1. WHEN multiple tasks need the same data THEN crews SHALL pass data via context (not re-fetch)
2. WHEN a task fetches market data THEN subsequent tasks SHALL reuse that data from context
3. WHEN sharing data via context THEN crews SHALL include timestamps to ensure freshness
4. WHEN data in context is stale THEN tasks SHALL re-fetch rather than use outdated information
5. WHEN designing task sequences THEN minimize redundant tool calls through smart context passing

#### Acceptance Criteria - Parallel Execution

1. WHEN tasks are independent THEN crews SHALL use async_execution to parallelize I/O operations
2. WHEN fetching from multiple APIs THEN crews SHALL make concurrent requests where possible
3. WHEN parallelizing THEN crews SHALL respect rate limits and avoid overwhelming APIs
4. WHEN parallel execution fails THEN crews SHALL fall back to sequential execution
5. WHEN designing crews THEN identify opportunities for parallel data fetching

#### Acceptance Criteria - Monitoring and Optimization

1. WHEN crews execute THEN the system SHALL log API call counts per ticker
2. WHEN crews execute THEN the system SHALL log data freshness metrics (% fresh vs cached)
3. WHEN crews execute THEN the system SHALL identify opportunities for batching
4. WHEN crews execute THEN the system SHALL log execution time breakdown by task
5. WHEN inefficiencies are detected THEN the system SHALL log recommendations for optimization

#### Design Principles for API Efficiency

1. **Accuracy First**: Never sacrifice data freshness for cost savings
2. **Smart Batching**: Use tool-level batching when available (e.g., fetch RSI+MACD+BB in one call)
3. **Context Sharing**: Pass data between tasks to avoid re-fetching
4. **Parallel I/O**: Use async execution for independent data fetching
5. **Avoid Waste**: Don't call reasoning loops that waste tokens without adding value

#### Examples of Smart API Usage

**❌ Inefficient (Multiple Individual Calls):**
```python
rsi = fetch_indicator("AAPL", "RSI")
macd = fetch_indicator("AAPL", "MACD")
bb = fetch_indicator("AAPL", "BB")
# 3 API calls
```

**✅ Efficient (Batch Call):**
```python
indicators = fetch_indicators("AAPL", ["RSI", "MACD", "BB"])
# 1 API call
```

**❌ Inefficient (Re-fetching Same Data):**
```python
# Task 1
price_data = fetch_price("AAPL")
# Task 2
price_data = fetch_price("AAPL")  # Redundant!
```

**✅ Efficient (Context Sharing):**
```python
# Task 1
price_data = fetch_price("AAPL")
context["price_data"] = price_data
# Task 2
price_data = context["price_data"]  # Reuse!
```

#### Cost vs Accuracy Balance

**Priority 1: Accuracy** - Real money decisions require current data
**Priority 2: Efficiency** - Minimize redundant calls through smart design
**Priority 3: Cost** - Optimize where possible without compromising 1 & 2

**NOT Acceptable:**
- ❌ Using 24-hour cached prices for buy/sell decisions
- ❌ Using stale sentiment data for risk assessment
- ❌ Skipping data fetches to save costs

**Acceptable:**
- ✅ Caching company fundamentals (changes slowly)
- ✅ Batching indicator requests (same freshness, fewer calls)
- ✅ Sharing data between tasks via context (same execution)

### Requirement 8: Error Handling and Validation

**User Story:** As a system operator, I want clear error messages, so that I can diagnose and fix issues quickly.

#### Acceptance Criteria

1. WHEN ticker is invalid THEN the crew SHALL return clear error with ticker validation failure
2. WHEN data sources fail THEN the crew SHALL attempt fallback sources before failing
3. WHEN analysis is incomplete THEN the crew SHALL return partial results with confidence flags
4. WHEN any crew fails THEN it SHALL log detailed error information for debugging
5. WHEN any crew fails THEN it SHALL NOT enter infinite reasoning loops
6. WHEN ticker parameter is missing THEN the crew SHALL raise ValueError with clear message

### Requirement 9: Crew Structure and Organization

**User Story:** As a developer, I want consistent crew structure for the unified deep analysis crew, so that maintenance and updates are straightforward.

#### Acceptance Criteria

1. WHEN creating DeepAnalysisCrew THEN it SHALL follow standard CrewAI structure (deep_analysis/deep_analysis.py, config/agents.yaml, config/tasks.yaml)
2. WHEN creating DeepAnalysisCrew THEN it SHALL have 3 agents: asset_analyst, risk_assessor, investment_reporter
3. WHEN creating DeepAnalysisCrew THEN it SHALL have 4 tasks: deep_analysis, technical_analysis, risk_assessment, final_report
4. WHEN creating DeepAnalysisCrew THEN it SHALL use `@agent`, `@task`, `@crew` decorators
5. WHEN creating DeepAnalysisCrew THEN it SHALL use `get_configured_llm()` for LLM configuration
6. WHEN creating DeepAnalysisCrew THEN it SHALL enable `reasoning=True` on agents and tasks
7. WHEN creating DeepAnalysisCrew THEN task descriptions SHALL explicitly mention "analyze the provided {ticker} ticker"
8. WHEN creating DeepAnalysisCrew THEN it SHALL implement dynamic tool routing method `get_tools_for_asset_class()`
9. WHEN creating investment_reporter agent THEN it SHALL use `@final_reporter` decorator to enforce empty tools

## Success Criteria

### Core Functionality
1. **No Infinite Loops:** DeepAnalysisCrew completes or fails within 5 minutes, never hangs indefinitely
2. **Reasoning Works:** With `reasoning=True`, agents create valid plans and execute successfully
3. **Single Ticker Focus:** DeepAnalysisCrew analyzes exactly one ticker without requesting additional tickers
4. **Schema Compliance:** Outputs conform to unified `DeepAnalysisResult` schema
5. **Dynamic Routing:** Crew correctly routes to asset-specific tools based on `asset_class` parameter
6. **Integration Success:** `analyze_and_update_portfolio()` can call DeepAnalysisCrew with ticker and asset_class
7. **Performance:** Analysis completes in <5 minutes per ticker (vs 3-6 hours currently)
8. **No Duplication:** Single crew implementation handles all asset classes

### Crew Separation & Routing
9. **Clear Separation:** Task descriptions clearly distinguish discovery (top 10) from deep analysis (single ticker)
10. **Routing Logic:** Flow orchestrator correctly routes to discovery vs deep analysis crew
11. **Discovery Purpose:** StockCrew, ETFCrew, CryptoCrew are clearly documented as discovery-only (top 10 screening)
12. **Deep Analysis Purpose:** DeepAnalysisCrew is clearly documented for single-ticker portfolio evaluation

### Data Quality & Performance
13. **Data Freshness:** Analysis uses current market data, not stale cached data (accuracy over cost)
14. **API Efficiency:** Smart tool-level batching and context sharing minimize redundant calls without sacrificing accuracy
15. **Final Reporter Compliance:** Investment reporter has empty tools list and consolidates from context only

### Flow Architecture (CRITICAL)
16. **Consolidated Flow:** Single atomic operation performs deep analysis, alternative matching, and portfolio update
17. **Efficient Portfolio Generation:** Portfolio review generated only ONCE (not twice) with enriched data
18. **Correct Flow Sequence:** Portfolio analysis happens BEFORE discovery (logical business order)
19. **Atomic Operations:** Deep analysis, alternatives, and portfolio update succeed or fail together
20. **Discovery After Portfolio:** Discovery crews run AFTER portfolio is analyzed (not before)
21. **Rebalancing Has Full Context:** Rebalancing has access to both portfolio analysis AND discovery results

### Flow Sequence Validation
22. **Phase 1 Correct:** validate_data_integration triggers check_portfolio (not discovery crews)
23. **Phase 2 Correct:** check_portfolio triggers analyze_and_update_portfolio
24. **Phase 3 Correct:** analyze_and_update_portfolio triggers discovery crews (check_crypto/stock/etf)
25. **Phase 4 Correct:** Discovery crews trigger check_investment_discovery
26. **Phase 5 Correct:** check_investment_discovery triggers check_portfolio_rebalancing
27. **Phase 6 Correct:** check_portfolio_rebalancing triggers pre_validate_reporter_input → report

### Business Logic Validation
28. **Alternative Matching Logic:** Alternatives matched BEFORE discovery (identifies needs)
29. **Discovery Provides Solutions:** Discovery crews provide A+ candidates for identified needs
30. **Portfolio Update Timing:** Portfolio updated AFTER discovery (merges A+ alternatives)
31. **No Premature Discovery:** Discovery doesn't run before knowing what portfolio needs
32. **Complete Data for Rebalancing:** Rebalancing has both portfolio grades AND A+ opportunities

### Requirement 10: Clear Separation from Discovery Crews

**User Story:** As a developer, I want clear distinction between discovery and deep analysis crews, so that the reasoning agents understand their different purposes.

#### Acceptance Criteria

1. WHEN discovery crews are used THEN task descriptions SHALL explicitly state "screen and identify top 10 assets"
2. WHEN DeepAnalysisCrew is used THEN task descriptions SHALL explicitly state "analyze the provided {ticker} ticker"
3. WHEN updating existing crews THEN discovery crew task descriptions SHALL be reviewed for clarity
4. WHEN creating DeepAnalysisCrew THEN naming SHALL clearly indicate purpose (DeepAnalysisCrew vs StockCrew/EtfCrew/CryptoCrew)
5. WHEN flow orchestrator routes analysis THEN it SHALL use appropriate crew based on use case (discovery vs deep analysis)

#### Documentation Requirements

1. WHEN this spec is implemented THEN existing discovery crew task descriptions SHOULD be reviewed
2. WHEN reviewing discovery crews THEN ensure "top 10" language is clear and intentional
3. WHEN reviewing discovery crews THEN add header comments explaining they are for discovery, not single-ticker analysis
4. WHEN flow orchestrator is updated THEN document routing logic clearly
5. WHEN DeepAnalysisCrew is created THEN document dynamic tool routing based on asset_class

## Out of Scope

- Discovery/screening of multiple assets (handled by existing `StockCrew`, `EtfCrew`, `CryptoCrew`)
- Portfolio-level analysis (handled by portfolio crews)
- Comparative analysis across multiple assets
- Translation of reports to multiple languages
- PDF generation or report formatting
- **Code modifications to existing discovery crews** (documentation updates only - add header comments)
- Creating separate crews for each asset class (unified crew approach instead)

## Decision Matrix: When to Use Which Crew

### Use Discovery Crews (StockCrew, EtfCrew, CryptoCrew)

**Use Case:** Investment discovery, screening, finding opportunities

**Characteristics:**
- Need to find "top 10" best assets in a category
- Comparative analysis across multiple assets
- No specific tickers in mind
- Want to discover new investment opportunities
- Efficient for analyzing multiple assets in one execution

**Examples:**
- "Find the top 10 tech stocks for growth investing"
- "Screen for the best low-cost ETFs"
- "Identify promising DeFi cryptocurrencies"
- Monthly investment discovery workflow

**Data Freshness:** Always uses current market data (no stale cache)

### Use Deep Analysis Crews (StockDeepAnalysisCrew, EtfDeepAnalysisCrew, CryptoDeepAnalysisCrew)

**Use Case:** Portfolio evaluation, specific ticker analysis

**Characteristics:**
- Have specific ticker to analyze
- Need detailed analysis of existing holding
- Keep/sell decision for portfolio holdings
- Deep dive into single asset
- Focused, accurate analysis with current data

**Examples:**
- "Analyze my AAPL holding - should I keep or sell?"
- "Deep analysis of VOO ETF in my portfolio"
- "Evaluate BTC position for rebalancing"
- Portfolio review workflow (analyze each holding)

**Data Freshness:** Always uses current market data (accuracy over cache)

### API Efficiency Strategy (NOT Cost-Cutting)

**Principle:** Minimize redundant calls without sacrificing accuracy

**Scenario 1: Portfolio Review (66 holdings)**
- Each holding analyzed with fresh data
- Smart batching: Fetch multiple indicators per ticker in one call
- Context sharing: Pass data between tasks within same crew execution
- Parallel I/O: Fetch from multiple APIs concurrently
- Result: Accurate analysis with optimized API usage

**Scenario 2: Investment Discovery**
- Discovery crew: Analyze 10 assets in one execution
- Smart batching: Comparative analysis shares market context
- Result: Efficient discovery with current data

**Scenario 3: Tool-Level Batching**
- Instead of: 3 calls for RSI, MACD, BB
- Use: 1 call for all indicators
- Result: Same data freshness, fewer API calls

**What We DON'T Do:**
- ❌ Cache market prices for 24 hours (stale data = bad decisions)
- ❌ Skip data fetches to save money (accuracy matters more)
- ❌ Use old analysis for current decisions (market changes)

**What We DO:**
- ✅ Use tool-level batching when available (fetch multiple indicators at once)
- ✅ Share data between tasks via context (avoid re-fetching within same execution)
- ✅ Parallelize independent API calls (faster, not fewer calls)
- ✅ Cache static data only (company info, historical filings)

**Anti-Pattern to Avoid:**
- ❌ Using discovery crews for single-ticker analysis (architectural mismatch)
- ❌ Using deep analysis crews for screening/discovery (wrong tool for job)
- ❌ Sacrificing data freshness for cost savings (real money at stake)

## Dependencies

- **Existing schemas**: `TenKInsight`, `ETFFactsheet`, `CryptoThesis`, `RiskAssessmentStandardized`, `DeepAnalysisResult`
- **Tool factories**: `get_stock_crew_tools()`, `get_etf_crew_tools()`, `get_crypto_crew_tools()`
- **Flow orchestrator**: `analyze_holdings_deep()` method in `src/finwiz/flows/flow_orchestrator.py`
- **Cache manager**: `analysis_cache_manager`
- **Grading system**: `score_to_grade()` utility
- **LLM config**: `get_configured_llm()`
- **Agent validators**: `@final_reporter` decorator from `finwiz.utils.agent_validators`
- **CrewAI Flow**: Structured state management with Pydantic models

## Assumptions

- Single ticker analysis requires same data sources as multi-ticker discovery
- Reasoning can be enabled if task descriptions are clear about single-ticker mode
- Existing tools work for single tickers without modification
- Tool factories support dynamic routing based on asset_class parameter
- Flow orchestrator will be updated to pass both ticker and asset_class parameters
- Cache manager handles all asset classes uniformly
- Dynamic tool routing can be implemented within single crew class
- Task descriptions can adapt based on {asset_class} template variable

## Existing Crew Task Description Review

### Current State Analysis

All three existing discovery crews have "top 10" language embedded in their task descriptions:

**StockCrew (`src/finwiz/crews/stock_crew/config/tasks.yaml`):**
- `stock_screening_task`: "screen and identify the top 10 stable, blue-chip stocks"
- `technical_detail_task`: "perform detailed technical analysis on each of the 10 stocks"
- `stock_risk_assessment_task`: "evaluate risks for each of the 10 stocks"

**EtfCrew (`src/finwiz/crews/etf_crew/config/tasks.yaml`):**
- `etf_screening_task`: "Screen and identify the top 10 most stable and diversified ETFs"
- `etf_risk_assessment_task`: "Evaluate risks for each of the 10 ETFs identified"
- `etf_investment_strategy_task`: "Develop investment strategies for each of the 10 ETFs"

**CryptoCrew (`src/finwiz/crews/crypto_crew/config/tasks.yaml`):**
- `market_analysis_task`: "identify the top 10 promising cryptocurrencies"
- `technical_analysis_task`: "price trends for the top 10 projects"
- `risk_assessment_task`: "risks associated with the top 10 cryptocurrencies"

### Recommendation

**Do NOT modify existing discovery crews** - they are working correctly for their intended purpose (investment discovery). Instead:

1. Create new deep analysis crews with single-ticker task descriptions
2. Update flow orchestrator to route appropriately:
   - Discovery use case → Use existing crews (StockCrew, EtfCrew, CryptoCrew)
   - Deep analysis use case → Use new crews (StockDeepAnalysisCrew, etc.)
3. Add comments to existing crews clarifying they are for discovery/screening
4. Document the distinction in crew docstrings

### Optional Enhancement (Future)

Consider adding a comment header to existing discovery crew task files:

```yaml
# DISCOVERY CREW - Designed to screen and identify top 10 assets
# For single-ticker deep analysis, use StockDeepAnalysisCrew instead
# This crew is called by: check_stock() in flow orchestrator (discovery mode)
```

## Implementation Priority

1. **Phase 1:** Create unified `DeepAnalysisCrew` with dynamic tool routing (handles all asset classes)
2. **Phase 2:** Update flow orchestrator routing logic to use DeepAnalysisCrew with asset_class parameter
3. **Phase 3:** Integration testing with real tickers (stock, ETF, crypto)
4. **Phase 4:** Add clarifying header comments to existing discovery crew task files
5. **Phase 5:** Documentation and monitoring setup

---

**Version:** 1.0  
**Created:** 2025-01-11  
**Status:** Draft - Ready for Review and Design Phase
# Requirements Document

## Introduction

This feature enhances the FinWiz portfolio analysis system to provide deep, comprehensive analysis of 
portfolio holdings by integrating crew-based analysis and A+ alternative recommendations. Currently, 
the system only performs shallow ticker validation, resulting in all holdings receiving the same grade 
(D) and score (0.6), with no alternative recommendations despite A+ discovery data being available.

The enhanced system will:

- Run full crew analysis (stock/ETF/crypto) for each holding
- Calculate accurate composite scores based on fundamental, technical, and risk analysis
- Assign proper grades (A+, A, B, C, D, F) based on comprehensive evaluation
- Link A+ discovery candidates as alternatives for underperforming holdings
- Provide actionable swap recommendations with transition strategies

## Requirements

### Requirement 1: Deep Crew Analysis Flow Integration

**User Story:** As a portfolio manager, I want each holding to be analyzed by the appropriate crew 
(stock/ETF/crypto) through the CrewAI Flow system so that I receive accurate grades and scores based 
on comprehensive fundamental, technical, and risk analysis.

#### Acceptance Criteria

1. WHEN portfolio review completes THEN the Flow SHALL trigger a `@listen("check_portfolio")` 
   method for deep analysis
2. WHEN deep analysis Flow method executes THEN it SHALL check the `DEEP_PORTFOLIO_ANALYSIS` 
   environment variable
3. IF `DEEP_PORTFOLIO_ANALYSIS=true` THEN the Flow method SHALL iterate through holdings from 
   portfolio review output stored in `self.state`
4. WHEN processing each holding THEN the Flow SHALL instantiate and execute appropriate crew 
   (StockCrew for stocks, EtfCrew for ETFs, CryptoCrew for crypto) directly using `crew.kickoff()`
5. WHEN crew analysis completes THEN the Flow SHALL extract composite scores from crew outputs 
   including fundamental score, technical score, quality score, and risk score
6. WHEN composite scores are calculated THEN the Flow SHALL assign accurate letter grades 
   (A+, A, B, C, D, F) using the grading system
7. WHEN crew analysis is used THEN the Flow SHALL update structured Flow state (`self.state`) 
   with analysis results and return analysis data to downstream Flow methods
8. IF crew analysis fails for a holding THEN the Flow SHALL fall back to ticker validation with 
   appropriate warning flags
9. WHEN all holdings are processed THEN the Flow method SHALL return analysis results dict for 
   consumption by downstream `@listen()` methods
10. WHEN deep analysis completes THEN the Flow SHALL log statistics showing how many received 
    deep analysis vs. shallow validation

### Requirement 2: A+ Alternative Discovery Flow Integration

**User Story:** As a portfolio manager, I want underperforming holdings (graded C or below) to be 
matched with A+ alternative candidates through the Flow system so that I can make informed decisions 
about portfolio improvements.

#### Acceptance Criteria

1. WHEN deep analysis Flow method completes THEN the Flow SHALL trigger a 
   `@listen("analyze_holdings_deep")` method that receives analysis results as parameter
2. WHEN alternative matching Flow method executes THEN it SHALL check the 
   `PORTFOLIO_ENABLE_ALTERNATIVES` environment variable
3. IF alternatives are enabled THEN the Flow SHALL process holdings with grades C, D, or F from 
   the received analysis results parameter
4. WHEN searching for alternatives THEN the Flow SHALL use existing AlternativeFinder tool to 
   match by asset class
5. WHEN A+ alternatives are found THEN the Flow SHALL update structured Flow state (`self.state`) 
   with up to 5 top-ranked alternatives per holding
6. WHEN alternatives are provided THEN each alternative SHALL include ticker, name, grade, 
   composite score, and rationale for recommendation
7. WHEN no A+ alternatives exist for an asset class THEN the Flow SHALL log a warning and 
   continue processing
8. WHEN alternatives are populated THEN the Flow method SHALL return alternatives data dict for 
   consumption by downstream Flow methods

### Requirement 3: Alternative Finder Service

**User Story:** As a developer, I want a reusable AlternativeFinder service that can match 
underperforming holdings with A+ candidates so that the logic is centralized and testable.

#### Acceptance Criteria

1. WHEN AlternativeFinder is initialized THEN it SHALL load A+ discovery data from 
   `output/discovery/a_plus_*.json` files
2. WHEN finding alternatives for a holding THEN the system SHALL filter A+ candidates by 
   matching asset class
3. WHEN multiple alternatives exist THEN the system SHALL rank them by composite score 
   (highest first)
4. WHEN alternatives are found THEN the system SHALL return Alternative objects conforming to 
   the portfolio_review schema
5. IF discovery data is missing or stale THEN the system SHALL log appropriate warnings and 
   return empty alternatives list
6. WHEN alternatives are generated THEN each SHALL include a clear rationale explaining why 
   it's a better choice

### Requirement 4: Flow-Based Performance and Cost Management

**User Story:** As a system administrator, I want deep portfolio analysis to be optional and 
configurable through the Flow system so that I can balance analysis depth with API costs and 
execution time.

#### Acceptance Criteria

1. WHEN the Flow starts THEN it SHALL check for `DEEP_PORTFOLIO_ANALYSIS` environment variable 
   (default: false)
2. IF `DEEP_PORTFOLIO_ANALYSIS=true` THEN the Flow SHALL execute deep analysis Flow methods 
   after portfolio review
3. IF `DEEP_PORTFOLIO_ANALYSIS=false` THEN the Flow method SHALL return early without processing, 
   allowing Flow to continue to next listener
4. WHEN deep analysis Flow methods execute THEN they SHALL implement rate limiting to avoid 
   API throttling
5. WHEN deep analysis is enabled THEN the Flow SHALL provide progress logging showing X/Y 
   holdings analyzed
6. WHEN deep analysis completes THEN the Flow SHALL update structured state (`self.state`) with 
   execution metrics and return results to downstream methods

### Requirement 5: Flow-Integrated Caching and Incremental Updates

**User Story:** As a portfolio manager running daily analysis, I want the Flow system to cache 
crew analysis results so that unchanged holdings don't require re-analysis, reducing costs and 
execution time.

#### Acceptance Criteria

1. WHEN a holding is analyzed in the Flow THEN the deep analysis method SHALL cache the crew 
   analysis result with the ticker and analysis date
2. WHEN the Flow processes a holding THEN it SHALL check if cached analysis exists and is fresh 
   (< 24 hours)
3. IF cached analysis is fresh THEN the Flow SHALL use cached data instead of re-running crew 
   analysis
4. IF cached analysis is stale or missing THEN the Flow SHALL instantiate and execute crew 
   directly using `crew.kickoff()`
5. WHEN using cached data THEN the Flow SHALL log "Using cached analysis for {ticker} 
   (age: {hours}h)"
6. WHEN the cache is used THEN the Flow SHALL update structured state (`self.state`) with cache 
   metadata and include it in returned results

### Requirement 6: Enhanced Reporting and Transparency

**User Story:** As a portfolio manager, I want the final report to clearly show which holdings 
received deep analysis vs. shallow validation so that I understand the confidence level of each 
recommendation.

#### Acceptance Criteria

1. WHEN generating the portfolio review report THEN the system SHALL include a summary showing 
   deep vs. shallow analysis counts
2. WHEN displaying holdings in the report THEN each SHALL show an analysis depth indicator 
   (🔍 Deep Analysis or ⚡ Quick Validation)
3. WHEN a holding has A+ alternatives THEN the report SHALL display them in a dedicated 
   "Alternatives" column or expandable section
4. WHEN alternatives are shown THEN each SHALL include the grade badge, ticker, and brief 
   rationale
5. WHEN the report is generated THEN it SHALL include a "Portfolio Improvement Potential" 
   section summarizing possible upgrades
6. WHEN deep analysis was used THEN the report SHALL include aggregate statistics (average grade, 
   grade distribution, improvement opportunities)

### Requirement 7: Flow-Based Error Handling and Graceful Degradation

**User Story:** As a system operator, I want the Flow to continue even if some holdings fail deep 
analysis so that I still receive a complete report with partial data.

#### Acceptance Criteria

1. IF crew analysis fails for a holding in the Flow THEN the deep analysis method SHALL fall 
   back to ticker validation
2. WHEN falling back THEN the Flow SHALL log a warning with the error details
3. WHEN falling back THEN the Flow SHALL update structured state (`self.state`) with warning 
   flags and include them in returned results
4. IF A+ discovery data is missing THEN the alternative matching Flow method SHALL continue 
   without alternatives and log a warning
5. IF rate limiting occurs THEN the Flow SHALL implement exponential backoff and retry up to 
   3 times
6. WHEN errors occur THEN the Flow SHALL collect error statistics in structured state and return 
   them with analysis results for downstream Flow methods

### Requirement 8: CrewAI Flow State Management Compliance

**User Story:** As a developer, I want the deep portfolio analysis to follow proper CrewAI Flow 
patterns for state management and data passing so that the implementation is maintainable and 
follows framework best practices.

#### Acceptance Criteria

1. WHEN implementing Flow methods THEN they SHALL use structured Flow state (`self.state`) 
   instead of unstructured dictionaries
2. WHEN Flow methods complete THEN they SHALL return data that is automatically passed to 
   downstream `@listen()` methods as parameters
3. WHEN Flow methods need to store persistent data THEN they SHALL update `self.state` with 
   structured data models
4. WHEN instantiating crews THEN Flow methods SHALL use direct crew instantiation and 
   `crew.kickoff()` pattern from CrewAI documentation
5. WHEN Flow methods receive data from upstream methods THEN they SHALL accept it as method 
   parameters following CrewAI Flow listener patterns
6. WHEN Flow execution completes THEN the final Flow state SHALL contain all analysis results 
   accessible via `flow.state` after `flow.kickoff()`
7. WHEN implementing Flow listeners THEN they SHALL follow the exact patterns from CrewAI Flow 
   documentation for method signatures and data passing

### Requirement 9: Configuration and Feature Flags

**User Story:** As a system administrator, I want granular control over portfolio analysis features 
through environment variables so that I can optimize for different use cases (quick validation vs. 
comprehensive analysis).

#### Acceptance Criteria

1. WHEN the Flow starts THEN it SHALL support the following environment variables:
   - `DEEP_PORTFOLIO_ANALYSIS` (true/false, default: false)
   - `PORTFOLIO_ENABLE_ALTERNATIVES` (true/false, default: true)
   - `PORTFOLIO_CACHE_ENABLED` (true/false, default: true)
   - `PORTFOLIO_CACHE_TTL_HOURS` (integer, default: 24)
   - `PORTFOLIO_MAX_ALTERNATIVES` (integer, default: 5)
   - `PORTFOLIO_DEEP_ANALYSIS_BATCH_SIZE` (integer, default: 10)
2. WHEN configuration is loaded THEN the Flow SHALL validate all values and use defaults for invalid entries
3. WHEN configuration is loaded THEN the Flow SHALL log the active configuration settings
4. IF conflicting settings are detected THEN the Flow SHALL log warnings and use safe defaults
5. WHEN deep analysis is disabled THEN the Flow SHALL still attempt to link A+ alternatives if `PORTFOLIO_ENABLE_ALTERNATIVES=true`

### Requirement 11: Structured Flow State Migration

**User Story:** As a developer, I want the entire Flow orchestrator to use structured Pydantic 
state models instead of unstructured dictionaries so that the codebase follows CrewAI Flow best 
practices, provides type safety, and is easier to maintain.

#### Acceptance Criteria

1. WHEN the Flow is initialized THEN it SHALL use a comprehensive `FinwizState` Pydantic model 
   that includes ALL data currently stored in `self.inputs`
2. WHEN Flow methods need to store data THEN they SHALL update `self.state` fields instead of 
   `self.inputs` dictionary keys
3. WHEN Flow methods complete THEN they SHALL return structured data that is passed to downstream 
   listeners as typed parameters
4. WHEN accessing Flow data after execution THEN external code SHALL use `flow.state` with 
   type-safe field access instead of `flow.inputs` dictionary lookups
5. WHEN the `FinwizState` model is defined THEN it SHALL include properly typed fields for:
   - Core analysis results (stock_result, etf_result, crypto_result)
   - Portfolio review data (portfolio_review, portfolio_review_json)
   - Discovery results (investment_discovery_result, investment_discovery_structured)
   - Rebalancing data (portfolio_rebalancing_result, portfolio_rebalancing_available)
   - Data availability tracking (data_availability_report, stale_data_warnings)
   - Error tracking (error_summaries, system_health)
   - Consolidated data (consolidated_data, core_analysis_summary)
   - Session metadata (current_date, timestamp, report_language)
   - All other data currently in `self.inputs`
6. WHEN the migration is complete THEN ALL references to `self.inputs` SHALL be completely 
   removed from the entire codebase
7. WHEN the migration is complete THEN `self.inputs` SHALL NOT exist or be used anywhere in 
   the Flow orchestrator
8. WHEN Flow state is updated THEN it SHALL use Pydantic validation to ensure data integrity
9. WHEN Flow methods receive data from upstream THEN they SHALL use typed parameters matching 
   the Pydantic model fields
10. WHEN the Flow completes THEN the final state SHALL be fully accessible via `flow.state` 
    with IDE autocomplete support
11. WHEN the migration is implemented THEN it SHALL be done in ONE complete migration with NO 
    backward compatibility layer
12. WHEN any code references `self.inputs` after migration THEN it SHALL be considered a bug 
    and SHALL NOT compile or pass linting

### Requirement 10: Complete Data Integration and Report Synchronization

**User Story:** As a portfolio manager, I want all analysis data (crew outputs, discovery results, 
portfolio decisions) to be fully integrated into the final report so that no calculated data goes 
unused and all insights are presented in a unified view.

#### Acceptance Criteria

1. WHEN deep portfolio analysis completes THEN ALL crew analysis results SHALL be stored in 
   the integration system
2. WHEN A+ alternatives are found THEN they SHALL be included in BOTH the portfolio review JSON 
   AND the final HTML report
3. WHEN the final report is generated THEN it SHALL include ALL available data from:
   - Core crew analysis (stock, ETF, crypto)
   - Portfolio review with deep analysis scores
   - A+ discovery candidates
   - Alternative recommendations for each underperforming holding
   - Backtesting metrics (if available)
4. WHEN crew analysis produces metrics THEN those metrics SHALL be reflected in the portfolio 
   holdings table (not just stored in separate files)
5. IF any analysis data exists but is not displayed in the report THEN the system SHALL log a 
   warning indicating unused data
6. WHEN the report is generated THEN it SHALL include a "Data Completeness" section showing:
   - Which crews ran successfully
   - Which data sources were integrated
   - Any missing or unused data
   - Data freshness indicators
7. WHEN deep analysis is enabled THEN the portfolio review SHALL include detailed metrics from 
   crew analysis:
   - Fundamental scores (P/E, ROE, growth rates for stocks)
   - Technical indicators (RSI, MACD, trend direction)
   - Risk scores (0-5 scale with specific risk factors)
   - Sentiment scores (market sentiment analysis)
8. WHEN A+ alternatives are displayed THEN each SHALL show:
   - Current holding grade vs. alternative grade
   - Score improvement potential (e.g., "D → A+, +0.38 score improvement")
   - Key advantages of the alternative
   - Transition strategy recommendation
9. WHEN the report includes alternatives THEN it SHALL provide a "Portfolio Upgrade Summary" 
   showing:
   - Total number of holdings with alternatives
   - Potential portfolio grade improvement
   - Estimated risk reduction
   - Implementation priority ranking

---

## Success Metrics

- **Accuracy**: Holdings receive grades spanning A+ to F based on actual analysis (not all D)
- **Completeness**: 100% of holdings processed with either deep or shallow analysis
- **Alternative Coverage**: 80%+ of underperforming holdings (C or below) have A+ alternatives when available
- **Performance**: Deep analysis completes within 5 minutes for 50 holdings with caching
- **Cost Efficiency**: Cached analysis reduces API calls by 70%+ on subsequent runs
- **Transparency**: Reports clearly indicate analysis depth and data sources for each holding

---

## Out of Scope

- Real-time portfolio tracking and alerts
- Automated trade execution
- Portfolio optimization algorithms (handled by separate rebalancing crew)
- Historical performance backtesting for individual holdings
- Tax-loss harvesting strategies
- Multi-currency conversion and FX risk analysis
# Requirements Document

## Introduction

This specification defines a comprehensive modernization of the **entire FinWiz codebase** to address four core issues: overly complex classes, inconsistent testing with mocking, deviations from CrewAI framework patterns, and inconsistent HTML generation practices.

The modernization will systematically refactor all existing code to break down large classes into focused modules under 400 lines (with a stretch goal of 300 lines for critical files), convert all tests to use pytest-mock exclusively, ensure all CrewAI crews follow proper framework patterns, and migrate all HTML generation to use bs4 (BeautifulSoup). This will improve code maintainability, test consistency, and security posture across the entire codebase while preserving all existing functionality.

**Scope:** This is a codebase-wide optimization effort that applies to all existing Python files, tests, crews, and HTML generation code in the FinWiz project.

## Requirements

### Requirement 1: Break Down Large Classes Across Entire Codebase

**User Story:** As a developer, I want all large, complex classes in the existing codebase to be broken into smaller pieces, so that code is easier to read and maintain.

#### Acceptance Criteria

1. WHEN analyzing the codebase THEN all files exceeding 400 lines SHALL be identified and prioritized for refactoring
2. WHEN files exceed 500 lines THEN they SHALL be refactored with high priority
3. WHEN classes do multiple things THEN they SHALL be split by responsibility
4. WHEN utility functions exist in classes THEN they SHALL be moved to separate modules
5. WHEN classes are refactored THEN each SHALL have a clear, single purpose
6. IF a file cannot be reduced below 400 lines THEN it SHALL be documented why
7. WHEN refactoring is complete THEN no file in the codebase SHALL exceed 400 lines without documented justification (stretch goal: 300 lines for critical files)

### Requirement 2: Migrate All Crews to Follow CrewAI Patterns

**User Story:** As a CrewAI developer, I want all existing crews in the codebase to use proper framework patterns, so that code is consistent and maintainable.

#### Acceptance Criteria

1. WHEN analyzing the codebase THEN all existing crews SHALL be identified and audited for pattern compliance
2. WHEN defining crews THEN they SHALL use @agent, @task, and @crew decorators
3. WHEN configuring crews THEN they SHALL use agents.yaml and tasks.yaml files
4. WHEN defining agents THEN they SHALL use YAML for roles, goals, and backstories
5. WHEN creating tasks THEN they SHALL have proper expected_output definitions
6. WHEN assigning tools THEN they SHALL use CrewAI's tool injection patterns
7. WHEN migration is complete THEN all crews in the codebase SHALL follow the standard CrewAI structure

### Requirement 3: Convert All Tests to Use pytest-mock

**User Story:** As a developer, I want all existing tests in the codebase to use pytest-mock exclusively, so that mocking is consistent and simple.

#### Acceptance Criteria

1. WHEN analyzing the test suite THEN all tests using unittest.mock SHALL be identified for conversion
2. WHEN writing or modifying tests THEN they SHALL use pytest-mock, never unittest.mock
3. WHEN mocking external calls THEN they SHALL use the mocker fixture
4. WHEN testing async code THEN they SHALL use pytest-asyncio with async mocking
5. WHEN conversion is complete THEN no test file SHALL contain unittest.mock imports or usage
6. WHEN mocking APIs THEN they SHALL mock at the tool level, not HTTP level

### Requirement 4: Migrate All HTML Generation to Use bs4

**User Story:** As a developer, I want all existing HTML generation code in the codebase to use the bs4 package, so that we avoid security risks and enhance code readability.

#### Acceptance Criteria

1. WHEN analyzing the codebase THEN all Python files generating HTML SHALL be identified for migration
2. WHEN generating HTML THEN BeautifulSoup or Tag objects from bs4 SHALL be used exclusively
3. WHEN creating complex HTML structures THEN manual string concatenation (f-strings, +, str.format()) SHALL NOT be used
4. WHEN generating HTML output THEN secure UTF-8 encoding SHALL be used (.prettify(formatter="html") or .encode("utf-8"))
5. WHEN outputting HTML THEN the structure SHALL be correctly indented and well-formed using bs4's formatting methods
6. IF user-supplied data is inserted into HTML THEN bs4's internal escaping mechanisms SHALL be used to prevent XSS vulnerabilities
7. WHEN migration is complete THEN beautifulsoup4 SHALL be declared as a core dependency in pyproject.toml
8. WHEN migration is complete THEN no Python file SHALL use string concatenation for HTML generation
9. WHEN establishing coding standards THEN documentation SHALL explicitly mandate bs4 for HTML generation
# Requirements Document

## Introduction

This specification defines comprehensive enhancements to the FinWiz financial analysis platform based on analysis of the documentation in the `docs/` folder and identified improvement opportunities. The enhancements focus on strengthening data validation, expanding analytical capabilities, ensuring architectural compliance, and improving overall system reliability while maintaining the existing elegant, configuration-driven design principles.

The improvements address critical needs identified in change requests CR-2025-08-09-01, CR-2025-08-09-02, and CR-2025-08-10-01, while ensuring compliance with FinWiz's core design principles of being "light as a haiku" with strict separation of concerns and CrewAI Flow framework standards.

## Requirements

### Requirement 1: Schema Validation & Data Contracts

**User Story:** As a FinWiz developer, I want strict data validation between crews and the final reporter, so that schema drift is prevented and data integrity is maintained across the analysis pipeline.

#### Acceptance Criteria

1. WHEN crews output data THEN the system SHALL validate all outputs using Pydantic v2 models with `extra='forbid'`
2. WHEN the final reporter receives input THEN it SHALL only accept validated `ReporterInput` schema instances
3. WHEN schema validation fails THEN the system SHALL log detailed error information and continue processing with graceful degradation
4. WHEN cross-crew data is passed THEN it SHALL conform to standardized contract keys (`ten_k_insights`, `market_sentiment`, `risk_score_standardized`)
5. IF validation strictness is configured THEN the system SHALL support `off`, `warn`, and `error` modes for gradual rollout

### Requirement 2: Enhanced Financial Analysis Tools

**User Story:** As a financial analyst, I want advanced multi-source technical and sentiment analysis capabilities, so that I can generate more comprehensive and accurate investment recommendations.

#### Acceptance Criteria

1. WHEN analyzing any asset class THEN the system SHALL integrate sentiment analysis from multiple sources (Alpha Vantage, Yahoo Finance, CoinMarketCap)
2. WHEN performing technical analysis THEN the system SHALL calculate Fibonacci retracements, support/resistance levels, and multi-indicator confluence
3. WHEN generating charts THEN the system SHALL use Chart-img API for visual analysis and LLM-based pattern recognition
4. WHEN analyzing news THEN the system SHALL extract trending topics with relevance scoring and impact assessment
5. WHEN calculating technical indicators THEN the system SHALL use Twelve Data API for RSI, MACD, Bollinger Bands, and other advanced indicators
6. IF multiple indicators align THEN the system SHALL identify and score confluence zones for enhanced signal strength

### Requirement 3: Tool Architecture Compliance

**User Story:** As a FinWiz architect, I want to ensure the final reporter has no external tools and follows HTML-first output standards, so that the system maintains clean separation of concerns and consistent report quality.

#### Acceptance Criteria

1. WHEN the final reporter executes THEN it SHALL have an empty tools list and make no external API calls
2. WHEN generating reports THEN the system SHALL produce HTML-first output with proper UTF-8 encoding and emoji support
3. WHEN creating French reports THEN the system SHALL include required sections "Synthèse 10-K" and "Sentiment du Marché"
4. WHEN the reporter processes data THEN it SHALL only consume validated upstream context from prior crew tasks
5. IF the reporter attempts to use tools THEN the system SHALL prevent execution and log an error

### Requirement 4: Testing & Quality Assurance

**User Story:** As a FinWiz developer, I want comprehensive testing coverage for contracts, integrations, and output validation, so that system reliability is maintained as new features are added.

#### Acceptance Criteria

1. WHEN YAML configurations change THEN contract tests SHALL validate all required context keys are present
2. WHEN external APIs are called THEN integration tests SHALL verify proper error handling and response parsing
3. WHEN reports are generated THEN output validation tests SHALL ensure HTML formatting compliance
4. WHEN running tests THEN the system SHALL support markers for separating unit tests from integration tests
5. WHEN schema validation occurs THEN tests SHALL verify Pydantic model strictness and error handling

### Requirement 5: Configuration & Environment Management

**User Story:** As a FinWiz operator, I want standardized configuration management and caching capabilities, so that the system is easier to deploy and operates cost-effectively.

#### Acceptance Criteria

1. WHEN configuring API keys THEN the system SHALL use standardized environment variable names (e.g., `CHART_IMG_API_KEY`)
2. WHEN making repeated API calls THEN the system SHALL implement caching with configurable TTL (30-60 minutes default)
3. WHEN validation fails THEN the system SHALL provide clear error messages with remediation guidance
4. WHEN new features are deployed THEN the system SHALL support feature flags for gradual rollout
5. IF API rate limits are hit THEN the system SHALL implement graceful degradation and retry logic

### Requirement 6: Enhanced Crew Capabilities

**User Story:** As a financial research user, I want each crew (Stock, ETF, Crypto) to provide consistent analytical depth and quality, so that I can make informed investment decisions across all asset classes.

#### Acceptance Criteria

1. WHEN the Stock crew analyzes securities THEN it SHALL extract 10-K insights with SEC citations, filing dates, and section references
2. WHEN the ETF crew analyzes funds THEN it SHALL parse factsheets for expense ratios, tracking differences, and top holdings
3. WHEN the Crypto crew analyzes digital assets THEN it SHALL provide thesis bullets with risk assessments on the standardized 1-10 scale
4. WHEN any crew assesses risk THEN it SHALL output standardized risk scores with consistent factors and methodology
5. WHEN crews perform sentiment analysis THEN they SHALL provide weighted scores, article counts, and trending topics

### Requirement 7: Performance & Scalability

**User Story:** As a FinWiz user, I want fast and reliable analysis execution, so that I can receive timely investment insights without system delays or failures.

#### Acceptance Criteria

1. WHEN tasks are I/O-bound THEN they SHALL execute asynchronously with `async_execution=True`
2. WHEN the final task in a sequential crew executes THEN it SHALL remain synchronous per CrewAI framework requirements
3. WHEN API calls are made THEN the system SHALL implement request throttling and rate limit management
4. WHEN caching is enabled THEN repeated queries SHALL return cached results within the TTL window
5. IF external services are unavailable THEN the system SHALL continue processing with available data and log service outages

### Requirement 8: Documentation & Developer Experience

**User Story:** As a FinWiz contributor, I want clear documentation and examples for new tools and integrations, so that I can effectively extend and maintain the system.

#### Acceptance Criteria

1. WHEN new APIs are integrated THEN documentation SHALL include setup instructions and example usage
2. WHEN schemas evolve THEN versioning guidelines SHALL be provided with migration strategies
3. WHEN troubleshooting issues THEN guides SHALL be available for common API and configuration problems
4. WHEN developing new features THEN examples SHALL be provided in `docs/schemas/examples/`
5. IF breaking changes are introduced THEN rollback procedures SHALL be documented

### Requirement 9: Persistent Financial Planning Session

**User Story:** As a financial planner, I want the application to load my previous work, so that I can update an existing financial plan without starting over every time.

#### Acceptance Criteria

1. WHEN the application starts AND the file `report/finwiz_family_financial_plan.html` exists THEN the system SHALL read and parse the HTML content to initialize the financial plan object
2. WHEN the application starts AND the file `report/finwiz_family_financial_plan.html` does not exist THEN the system SHALL create a new, default financial plan object for a greenfield session
3. WHEN loading an existing report THEN the system SHALL log a message indicating successful loading of previous work
4. WHEN creating a new session THEN the system SHALL log a message indicating creation of a new financial plan
5. IF the existing report file is corrupted or unreadable THEN the system SHALL log an error and create a new default financial plan object

### Requirement 10: Use of Dynamic Test Data

**User Story:** As a developer, I want our tests to use realistic, dynamic data to improve test coverage and simulate various user scenarios without relying on static identifiers.

#### Acceptance Criteria

1. WHEN the development team writes a new test AND that test requires identifiers (names, emails, phone numbers) THEN the test SHALL use the Faker library to generate the data dynamically
2. WHEN an existing test that forges static identifiers is being refactored THEN the developer SHALL refactor it to use Faker to replace the static data
3. WHEN a test is written for a function that interacts with an external API THEN that test SHALL use pytest-mock to simulate the API's response, instead of the standard unittest.mock library
4. WHEN a test uses pytest-mock THEN it SHALL explicitly specify the expected behavior of the mock, including return values and side effects
5. WHEN the test suite is executed THEN all tests SHALL pass, using the data generated by Faker and the mock responses created with pytest-mock

### Requirement 11: Code Quality & Test Infrastructure

**User Story:** As a FinWiz developer, I want comprehensive code quality standards and robust test infrastructure, so that the codebase maintains high reliability and follows Python best practices.

#### Acceptance Criteria

1. WHEN writing tests THEN the system SHALL use pytest-mock exclusively instead of unittest.mock for all mocking operations
2. WHEN code is committed THEN it SHALL pass all ruff linting checks with 110 character line limit enforcement
3. WHEN test failures occur THEN the system SHALL provide clear error messages with stack traces for root cause analysis
4. WHEN tests are executed THEN they SHALL complete in under 5 seconds per test suite with no shared state dependencies
5. WHEN code quality issues are detected THEN the system SHALL provide actionable remediation guidance and correction plans

### Requirement 12: Quantitative Analysis & Backtesting Framework

**User Story:** As a quantitative analyst, I want to backtest trading strategies using professional-grade libraries, so that I can evaluate strategy profitability and risk metrics with industry-standard tools.

#### Acceptance Criteria

1. WHEN a user specifies a stock symbol and date range THEN the system SHALL download historical OHLCV data using yfinance or similar data provider
2. WHEN backtesting is initiated THEN the system SHALL use TA-Lib for technical indicator calculations (SMA, RSI, MACD, Bollinger Bands)
3. WHEN strategy signals are generated THEN the system SHALL execute simulated trades using Backtrader or Zipline framework
4. WHEN backtesting completes THEN the system SHALL generate performance reports with custom analytics including Sharpe ratio, maximum drawdown, and return analysis
5. WHEN portfolio optimization is required THEN the system SHALL use modern portfolio optimization libraries like cvxpy or scipy.optimize for efficient frontier calculations
6. IF advanced quantitative analysis is needed THEN the system SHALL integrate QuantLib for derivatives pricing and fixed-income analysis
7. WHEN backtesting results are generated THEN they SHALL be integrated into the existing HTML report format with proper visualization
8. WHEN quantitative analysis tools are used THEN they SHALL follow the same validation and error handling patterns as other FinWiz components
# Requirements Document: FinWiz Architectural Consolidation

## Introduction

This document provides a unified and consistent set of requirements for the FinWiz platform. It is the result of a comprehensive review of multiple requirement specifications, which were found to have critical contradictions in architectural approach and process flow.

This specification resolves these conflicts by adopting a single, robust architecture:

1. **A Unified `DeepAnalysisCrew`**: A new, single crew is established for the in-depth analysis of individual portfolio holdings (stocks, ETFs, or crypto). This replaces the problematic use of "discovery" crews for single-ticker analysis, which was identified as a root cause of system hangs and instability.

2. **A Corrected Business Logic Flow**: The main execution flow is re-sequenced to follow a logical business process: **Portfolio Analysis → Deep Analysis → Discovery → Rebalancing → Reporting**. This ensures that analysis of existing assets happens *before* discovering new ones.

All requirements from previous documents have been migrated and adapted to align with this clear architectural vision, creating a single source of truth for development.

## Glossary

- **FinWiz System**: The AI-powered financial research platform using CrewAI agents for investment analysis
- **Discovery Crews**: The `StockCrew`, `ETFCrew`, and `CryptoCrew` responsible for screening and identifying "top 10" new investment opportunities. **They are not used for analyzing existing portfolio holdings.**
- **Deep Analysis Crew**: The new, unified `DeepAnalysisCrew` responsible for comprehensive analysis of a **single ticker** from any asset class
- **Flow Orchestration**: The CrewAI Flow-based execution sequence managing crew dependencies and data passing
- **Data Integration System**: The components responsible for crew data sharing, consolidation, and freshness validation
- **Graceful Degradation**: The system's ability to continue operating with partial data when components fail
- **Feature Flags**: Configuration switches to enable/disable specific features, like deep analysis

## Requirements

### Requirement 1: Unified Deep Analysis Crew

**User Story:** As a FinWiz developer, I want a single unified crew for deep analysis of individual holdings, so that the system can analyze any ticker without entering infinite loops or requesting multiple tickers.

#### Acceptance Criteria

1. WHEN a ticker and asset_class are provided as input, THE DeepAnalysisCrew SHALL perform deep analysis on only that single asset
2. WHEN the asset_class parameter is "stock", THE DeepAnalysisCrew SHALL dynamically select and use stock-specific tools including SEC analysis
3. WHEN the asset_class parameter is "etf", THE DeepAnalysisCrew SHALL dynamically select and use ETF-specific tools including factsheet analysis
4. WHEN the asset_class parameter is "crypto", THE DeepAnalysisCrew SHALL dynamically select and use crypto-specific tools including on-chain metrics
5. WHEN deep analysis completes, THE DeepAnalysisCrew SHALL output a result conforming to the `DeepAnalysisResult` Pydantic schema with scores, grade, and timestamps
6. WHEN task descriptions are reviewed, THE StockCrew SHALL explicitly state its purpose is to "screen and identify top 10 stock assets"
7. WHEN task descriptions are reviewed, THE EtfCrew SHALL explicitly state its purpose is to "screen and identify top 10 ETF assets"
8. WHEN task descriptions are reviewed, THE CryptoCrew SHALL explicitly state its purpose is to "screen and identify top 10 crypto assets"

### Requirement 2: Corrected Flow Orchestration

**User Story:** As a FinWiz operator, I want the execution flow to follow the logical business sequence, so that portfolio analysis happens before discovery and all phases execute in the proper order.

#### Acceptance Criteria

1. WHEN the flow starts, THE FinwizFlow SHALL execute `validate_data_integration` as Phase 1
2. WHEN Phase 1 completes, THE FinwizFlow SHALL execute `check_portfolio` as Phase 2 to analyze existing holdings
3. WHEN Phase 2 completes, THE FinwizFlow SHALL execute `analyze_and_update_portfolio` as Phase 3 to grade holdings and identify needs
4. WHEN Phase 3 completes, THE FinwizFlow SHALL execute discovery crews (`check_stock`, `check_etf`, `check_crypto`) as Phase 4
5. WHEN all discovery crews complete, THE FinwizFlow SHALL execute `check_investment_discovery` to consolidate A+ opportunities
6. WHEN Phase 4 completes, THE FinwizFlow SHALL execute `check_portfolio_rebalancing` as Phase 5 to optimize allocations
7. WHEN Phase 5 completes, THE FinwizFlow SHALL execute `report` as Phase 6 to present final recommendations
8. WHEN `analyze_and_update_portfolio` executes, THE FinwizFlow SHALL perform deep analysis, match alternatives, and update portfolio review in one atomic operation
9. WHEN discovery crews are triggered, THE FinwizFlow SHALL ensure they run after portfolio analysis completes
10. WHEN rebalancing is triggered, THE FinwizFlow SHALL ensure it runs after discovery completes

### Requirement 3: Data Integration & Validation

**User Story:** As a FinWiz quality engineer, I want data to flow correctly between all system components with strict validation, so that the reporter receives complete and accurate data.

#### Acceptance Criteria

1. WHEN a crew completes execution, THE Data Integration System SHALL store crew outputs in `output/{crew_name}/` directories
2. WHEN downstream processes request crew data, THE Data Integration System SHALL retrieve all successfully stored crew outputs
3. WHEN data is passed between crews, THE Data Integration System SHALL validate data against strict Pydantic models with `extra='forbid'`
4. WHEN the ReportCrew receives input, THE Data Integration System SHALL validate input against the `ReporterInput` Pydantic schema
5. WHEN market data is retrieved, THE Data Integration System SHALL validate that timestamps are no older than 24 hours
6. IF market data is older than 24 hours, THEN THE Data Integration System SHALL flag the analysis with warnings and reduce confidence scores
7. WHEN a crew begins analysis, THE Data Integration System SHALL use `TickerValidationTool` to verify ticker symbols against authoritative sources

### Requirement 4: Analysis Capabilities & Tool Usage

**User Story:** As a FinWiz analyst, I want comprehensive analysis capabilities for all asset classes, so that investment decisions are based on complete information.

#### Acceptance Criteria

1. WHEN analyzing a stock ticker, THE DeepAnalysisCrew SHALL perform fundamental analysis including P/E ratio and EPS
2. WHEN analyzing a stock ticker, THE DeepAnalysisCrew SHALL perform 10-K and 10-Q SEC filing analysis
3. WHEN analyzing a stock ticker, THE DeepAnalysisCrew SHALL calculate technical indicators and quantitative metrics including beta and Sharpe ratio
4. WHEN analyzing an ETF ticker, THE DeepAnalysisCrew SHALL retrieve factsheet data including expense ratio and AUM
5. WHEN analyzing an ETF ticker, THE DeepAnalysisCrew SHALL calculate tracking error analysis
6. WHEN analyzing an ETF ticker, THE DeepAnalysisCrew SHALL analyze holdings breakdown
7. WHEN analyzing a crypto ticker, THE DeepAnalysisCrew SHALL retrieve on-chain metrics including TVL and active addresses
8. WHEN analyzing a crypto ticker, THE DeepAnalysisCrew SHALL analyze tokenomics
9. WHEN analyzing a crypto ticker, THE DeepAnalysisCrew SHALL calculate correlation to BTC and ETH
10. WHEN performing technical analysis, THE FinWiz System SHALL integrate Fibonacci retracements from the Twelve Data API
11. WHEN performing technical analysis, THE FinWiz System SHALL identify support and resistance levels
12. WHEN performing technical analysis, THE FinWiz System SHALL detect multi-indicator confluence zones
13. WHEN calculating risk scores, THE FinWiz System SHALL use a standardized 0-5 risk scoring methodology
14. WHEN analyzing sentiment, THE FinWiz System SHALL use a multi-source sentiment analysis tool
15. WHEN a holding has grade C or lower, THE AlternativeFinder SHALL match it with A+ opportunities from discovery crews
16. WHEN alternatives are matched, THE AlternativeFinder SHALL integrate alternatives into the portfolio review
17. WHEN alternatives are matched, THE AlternativeFinder SHALL integrate alternatives into the final report
18. WHEN task configuration files are created, THE FinWiz System SHALL include a "REQUIRED ENUM VALUES" section in all `tasks.yaml` files

### Requirement 5: Flow Resilience & Performance

**User Story:** As a FinWiz operator, I want the system to handle failures gracefully and perform efficiently, so that large portfolios can be analyzed reliably.

#### Acceptance Criteria

1. IF a crew execution fails due to transient network error, THEN THE FinwizFlow SHALL automatically retry the execution
2. IF a crew execution fails due to API error, THEN THE FinwizFlow SHALL automatically retry the execution
3. WHEN retrying failed executions, THE FinwizFlow SHALL use exponential backoff strategy with jitter
4. WHEN a holding is analyzed, THE FinwizFlow SHALL use the `@persist()` decorator to save progress
5. IF the flow is interrupted, THEN THE FinwizFlow SHALL resume from the last successful checkpoint
6. WHEN resuming from checkpoint, THE FinwizFlow SHALL skip already-completed work
7. IF a holding fails analysis after all retries, THEN THE FinwizFlow SHALL mark the holding as failed
8. IF a holding fails analysis after all retries, THEN THE FinwizFlow SHALL use fallback data if available
9. IF a holding fails analysis after all retries, THEN THE FinwizFlow SHALL continue processing remaining holdings
10. WHEN fetching multiple indicators, THE FinWiz System SHALL use tool-level batching to fetch data in one API call
11. WHEN tasks share data needs, THE FinWiz System SHALL share data via context to avoid redundant API fetches
12. WHEN executing I/O-bound tasks, THE FinWiz System SHALL use `async_execution=True` for parallel execution
13. WHEN executing parallel tasks, THE FinWiz System SHALL respect API rate limits

### Requirement 6: Code Quality, Testing & Modernization

**User Story:** As a FinWiz developer, I want the codebase to follow best practices and standards, so that the system is maintainable and secure.

#### Acceptance Criteria

1. WHEN a crew is created, THE FinWiz System SHALL use `@agent`, `@task`, and `@crew` decorators
2. WHEN a crew is configured, THE FinWiz System SHALL use YAML configuration files for agents and tasks
3. WHEN the ReportCrew is configured, THE FinWiz System SHALL set the tools list to empty
4. WHEN the ReportCrew is configured, THE FinWiz System SHALL use the `@final_reporter` decorator
5. WHEN the ReportCrew executes, THE FinWiz System SHALL only consolidate data from upstream crews
6. WHEN the ReportCrew executes, THE FinWiz System SHALL make no external API calls
7. WHEN test files are created, THE FinWiz System SHALL use `pytest-mock` exclusively
8. WHEN test files are created, THE FinWiz System SHALL not import `unittest.mock`
9. WHEN tests require fake data, THE FinWiz System SHALL use the `Faker` library
10. WHEN Python files are created, THE FinWiz System SHALL keep file length under 400 lines
11. IF a Python file exceeds 400 lines, THEN THE FinWiz System SHALL refactor it into smaller, single-responsibility modules
12. WHEN generating HTML, THE FinWiz System SHALL use the BeautifulSoup (bs4) library
13. WHEN generating HTML, THE FinWiz System SHALL not use manual string concatenation
14. WHEN the flow orchestrator manages state, THE FinWiz System SHALL use a structured Pydantic model via `self.state`
15. WHEN the flow orchestrator manages state, THE FinWiz System SHALL not use an unstructured dictionary via `self.inputs`

### Requirement 7: Configuration & Management

**User Story:** As a FinWiz administrator, I want configuration to be consistent and documented, so that the system can be properly configured for different environments.

#### Acceptance Criteria

1. WHERE deep portfolio analysis is a feature, THE FinWiz System SHALL provide an environment variable to enable or disable it
2. WHERE alternative matching is a feature, THE FinWiz System SHALL provide an environment variable to enable or disable it
3. WHEN environment variables are defined, THE FinWiz System SHALL use consistent, documented naming conventions
4. WHEN API keys are required, THE FinWiz System SHALL document all required API keys in `.env.example`
5. WHEN feature flags are configured, THE FinWiz System SHALL document their purpose and valid values

### Requirement 8: System Stability

**User Story:** As a FinWiz operator, I want the system to be stable and performant, so that I can analyze large portfolios reliably.

#### Acceptance Criteria

1. WHEN analyzing a portfolio with 50 or more holdings, THE FinWiz System SHALL complete analysis without hangs
2. WHEN analyzing a portfolio with 50 or more holdings, THE FinWiz System SHALL complete analysis without infinite loops
3. WHEN analyzing a portfolio with 50 or more holdings, THE FinWiz System SHALL complete analysis without crashes
4. WHEN performing deep analysis on a single ticker, THE FinWiz System SHALL complete analysis in under 5 minutes

### Requirement 9: System Correctness

**User Story:** As a FinWiz analyst, I want the system to execute correctly and produce accurate results, so that investment decisions are based on reliable analysis.

#### Acceptance Criteria

1. WHEN the flow executes, THE FinWiz System SHALL execute phases in the specified logical order
2. WHEN portfolio holdings are analyzed, THE FinWiz System SHALL assign accurate grades from A+ to F based on deep analysis
3. WHEN portfolio holdings are analyzed, THE FinWiz System SHALL assign nuanced grades reflecting actual performance

### Requirement 10: System Completeness

**User Story:** As a FinWiz stakeholder, I want final reports to integrate all analysis stages, so that I have complete information for decision-making.

#### Acceptance Criteria

1. WHEN the final report is generated, THE FinWiz System SHALL integrate data from deep analysis stage
2. WHEN the final report is generated, THE FinWiz System SHALL integrate A+ discovery alternatives
3. WHEN the final report is generated, THE FinWiz System SHALL integrate rebalancing recommendations

### Requirement 11: System Resilience

**User Story:** As a FinWiz operator, I want the system to recover from interruptions, so that I don't lose progress on long-running analyses.

#### Acceptance Criteria

1. IF the flow is interrupted, THEN THE FinWiz System SHALL successfully resume from the last persisted checkpoint
2. WHEN resuming from checkpoint, THE FinWiz System SHALL recover progress without data loss

### Requirement 12: System Maintainability

**User Story:** As a FinWiz developer, I want the codebase to be clean and maintainable, so that I can efficiently add features and fix bugs.

#### Acceptance Criteria

1. WHEN the codebase is reviewed, THE FinWiz System SHALL have modules under 400 lines
2. WHEN the codebase is reviewed, THE FinWiz System SHALL follow consistent testing patterns
3. WHEN the codebase is reviewed, THE FinWiz System SHALL adhere to CrewAI best practices

### Requirement 13: System Efficiency

**User Story:** As a FinWiz administrator, I want the system to be efficient with API calls and execution time, so that operational costs are minimized.

#### Acceptance Criteria

1. WHEN the system executes, THE FinWiz System SHALL optimize API call volume through smart batching
2. WHEN the system executes, THE FinWiz System SHALL optimize API call volume through context sharing
3. WHEN the system executes, THE FinWiz System SHALL reduce execution time through parallelization

### Requirement 14: Template Variable Validation

**User Story:** As a FinWiz developer, I want all template variables in task configurations to be validated at startup, so that missing variables are caught before crew execution.

**Rationale:** On October 18, 2025, all deep analysis executions failed immediately due to a missing `{url}` template variable in task descriptions. This caused 100% failure rate and wasted 20+ minutes before final validation caught the issue.

#### Acceptance Criteria

1. WHEN the system starts, THE FinWiz System SHALL scan all task configuration files for template variables (e.g., `{ticker}`, `{asset_class}`)
2. WHEN template variables are found, THE FinWiz System SHALL validate that all variables are provided in crew input schemas
3. IF a template variable is not in the crew input schema, THEN THE FinWiz System SHALL raise a `ConfigurationError` at startup
4. WHEN a crew is instantiated, THE FinWiz System SHALL validate that all required input variables are present before calling `kickoff()`
5. IF required input variables are missing, THEN THE FinWiz System SHALL raise a `ValueError` with a clear error message listing missing variables
6. WHEN task descriptions are written, THE FinWiz System SHALL document all required input variables in a comment block
7. WHEN task descriptions reference external data (e.g., URLs from tool outputs), THE FinWiz System SHALL use placeholder text like `URL_FROM_TOOL_OUTPUT` instead of template variables

### Requirement 15: Fail-Fast on Critical Failures

**User Story:** As a FinWiz operator, I want the system to fail immediately when critical components fail completely, so that I don't waste time and API calls on doomed executions.

**Rationale:** On October 18, 2025, when deep analysis failed for all 5 holdings (0% success rate), the flow continued for 20+ minutes executing discovery and rebalancing crews, wasting API calls and time before finally failing at report generation.

#### Acceptance Criteria

1. WHEN deep analysis completes with 0% success rate (0 successful analyses), THE FinwizFlow SHALL immediately raise a `RuntimeError` and halt execution
2. WHEN deep analysis completes with 0% success rate, THE FinwizFlow SHALL log a CRITICAL message explaining the failure
3. WHEN deep analysis completes with 0% success rate, THE FinwizFlow SHALL NOT continue to discovery phase
4. WHEN deep analysis completes with 0% success rate, THE FinwizFlow SHALL NOT continue to rebalancing phase
5. WHEN deep analysis completes with 0% success rate, THE FinwizFlow SHALL NOT continue to report generation phase
6. WHEN portfolio merge fails due to missing deep analysis results, THE FinwizFlow SHALL immediately raise a `RuntimeError` and halt execution
7. WHEN portfolio merge fails due to missing deep analysis results, THE FinwizFlow SHALL NOT return `deep_analysis_complete: True`
8. WHEN a critical failure occurs, THE FinwizFlow SHALL log the root cause with sufficient detail for debugging
9. WHEN a critical failure occurs, THE FinwizFlow SHALL include actionable remediation steps in the error message
10. WHEN deep analysis has a high failure rate (>50%), THE FinwizFlow SHALL log a CRITICAL alert and create a monitoring alert

### Requirement 16: Data Structure Validation

**User Story:** As a FinWiz developer, I want data validators to handle both legacy and current data structures, so that schema migrations don't break the system.

**Rationale:** On October 18, 2025, the report validator looked for nested structure `portfolio_review["portfolio_review"]["holdings"]` but the actual JSON had flat structure `portfolio_review["holdings"]`, causing "Portfolio review contains no holdings" error even though 5 holdings existed.

#### Acceptance Criteria

1. WHEN validating portfolio review data, THE ReportDataValidator SHALL check for holdings in both nested and flat structures
2. WHEN validating portfolio review data, THE ReportDataValidator SHALL first try nested structure `["portfolio_review"]["holdings"]`
3. WHEN nested structure is not found, THE ReportDataValidator SHALL try flat structure `["holdings"]`
4. IF neither structure contains holdings, THEN THE ReportDataValidator SHALL log the available keys for debugging
5. IF neither structure contains holdings, THEN THE ReportDataValidator SHALL raise a `ReportValidationError` with diagnostic information
6. WHEN data structure changes are made, THE FinWiz System SHALL update all validators to handle both old and new structures
7. WHEN data structure changes are made, THE FinWiz System SHALL document the migration path in code comments
8. WHEN validating data structures, THE FinWiz System SHALL log which structure format was found (nested vs flat)

### Requirement 17: Cache Reliability

**User Story:** As a FinWiz operator, I want the caching system to reliably save and retrieve analysis results, so that repeated analyses use cached data instead of making redundant API calls.

**Rationale:** On October 18, 2025, a previous successful run at 16:20 generated HTML reports, but the cache directories were empty at 18:22 (2 hours later). The cache was not used, causing redundant crew executions.

#### Acceptance Criteria

1. WHEN a crew execution completes successfully, THE AnalysisCacheManager SHALL save the result to disk
2. WHEN saving cache, THE AnalysisCacheManager SHALL log the cache file path and confirm successful write
3. WHEN saving cache fails, THE AnalysisCacheManager SHALL log an ERROR with the exception details
4. WHEN loading cache, THE AnalysisCacheManager SHALL log whether cache was found and its age
5. WHEN cache is not found, THE AnalysisCacheManager SHALL log the expected cache file path for debugging
6. WHEN cache is stale (older than TTL), THE AnalysisCacheManager SHALL log the age and TTL threshold
7. WHEN cache is used, THE AnalysisCacheManager SHALL log "Using cached analysis for {ticker} (age: {hours}h)"
8. WHEN cache is bypassed, THE AnalysisCacheManager SHALL log the reason (not found, stale, disabled)
9. WHEN the system starts, THE AnalysisCacheManager SHALL verify cache directory exists and is writable
10. IF cache directory is not writable, THEN THE AnalysisCacheManager SHALL log a WARNING and disable caching
11. WHEN cache key is generated, THE AnalysisCacheManager SHALL use consistent formatting for ticker and asset_class
12. WHEN cache key is generated, THE AnalysisCacheManager SHALL log the cache key for debugging
13. WHEN cache files are saved, THE AnalysisCacheManager SHALL include metadata (timestamp, ticker, asset_class, version)
14. WHEN cache files are loaded, THE AnalysisCacheManager SHALL validate metadata matches the request

### Requirement 18: Comprehensive Error Logging

**User Story:** As a FinWiz operator, I want comprehensive error logging at all critical points, so that I can quickly diagnose and fix issues.

**Rationale:** The October 18, 2025 failures could have been diagnosed faster with better logging at critical validation points.

#### Acceptance Criteria

1. WHEN a crew execution fails, THE FinWiz System SHALL log the crew name, ticker, asset_class, and full exception traceback
2. WHEN a crew execution fails, THE FinWiz System SHALL log the crew inputs that were provided
3. WHEN template variable interpolation fails, THE FinWiz System SHALL log the template string and available variables
4. WHEN data validation fails, THE FinWiz System SHALL log the validation errors with field paths
5. WHEN data validation fails, THE FinWiz System SHALL log a sample of the invalid data for debugging
6. WHEN portfolio merge fails, THE FinWiz System SHALL log the number of holdings before and after merge
7. WHEN portfolio merge fails, THE FinWiz System SHALL log the number of deep analysis results available
8. WHEN cache operations fail, THE FinWiz System SHALL log the cache file path and file system error
9. WHEN API calls fail, THE FinWiz System SHALL log the API endpoint, status code, and response body
10. WHEN the flow halts due to critical failure, THE FinWiz System SHALL log a summary of what succeeded and what failed

### Requirement 19: Crypto Portfolio Analysis

**User Story:** As a FinWiz user, I want to analyze my crypto holdings from data/crypto.csv just like stocks and ETFs,
so that I get comprehensive portfolio analysis across all asset classes.

**Rationale:** The system currently supports stock.csv and etf.csv for portfolio analysis, but crypto.csv is not being
loaded or analyzed. Users with crypto holdings need the same deep analysis capabilities.

#### Acceptance Criteria

1. WHEN the portfolio holdings processor loads data, THE FinWiz System SHALL load holdings from data/crypto.csv
2. WHEN loading crypto.csv, THE FinWiz System SHALL expect columns: Name, Ticker (and optionally Currency)
3. WHEN loading crypto.csv, THE FinWiz System SHALL normalize ticker symbols (e.g., "BTC" → "BTC-USD" for Yahoo Finance)
4. WHEN crypto holdings are loaded, THE FinWiz System SHALL set asset_class to "crypto"
5. WHEN crypto holdings are validated, THE FinWiz System SHALL use TickerValidationTool with asset_class="crypto"
6. WHEN deep analysis is enabled, THE FinWiz System SHALL execute DeepAnalysisCrew for each crypto holding
7. WHEN executing DeepAnalysisCrew for crypto, THE FinWiz System SHALL pass asset_class="crypto" to enable crypto-specific tools
8. WHEN crypto deep analysis executes, THE DeepAnalysisCrew SHALL use crypto-specific tools (CoinMarketCapTool, on-chain metrics)
9. WHEN crypto analysis completes, THE FinWiz System SHALL include crypto holdings in the portfolio review
10. WHEN crypto analysis completes, THE FinWiz System SHALL include crypto holdings in the final report
11. WHEN the portfolio review is generated, THE FinWiz System SHALL show crypto holdings with their grades and recommendations
12. WHEN alternatives are matched, THE AlternativeFinder SHALL match underperforming crypto with A+ crypto opportunities from CryptoCrew discovery
13. WHEN the flow orchestrator initializes, THE FinWiz System SHALL pass crypto_csv path to the portfolio holdings processor
14. WHEN crypto.csv is missing or empty, THE FinWiz System SHALL log a warning and continue with other asset classes
15. WHEN crypto.csv contains invalid tickers, THE FinWiz System SHALL log validation failures and continue with valid tickers

### Requirement 20: Report Data Completeness

**User Story:** As a FinWiz analyst, I want the final report to include all available data including data availability summary and discovery results, so that I have complete information for investment decisions.

**Rationale:** On October 19, 2025, the report was missing critical data: (1) `data_availability_summary` object was not being passed to the report crew, causing "NOT AVAILABLE" messages in the data availability section, and (2) Discovery results (A+ opportunities) were not appearing in the final report despite being generated successfully.

#### Acceptance Criteria

1. WHEN `data_availability_summary` is generated in Flow state, THE ReportCrew SHALL preserve it in `prepare_crew_context`
2. WHEN the report is generated, THE ReportCrew SHALL include `data_availability_summary` in the crew inputs
3. WHEN the report displays data availability, THE ReportCrew SHALL show total_sources, available_sources, unavailable_sources, and stale_sources from `data_availability_summary`
4. WHEN data sources are stale, THE ReportCrew SHALL display freshness warnings with age indicators from `data_availability_summary.freshness_warnings`
5. WHEN discovery analysis completes successfully, THE FinwizFlow SHALL preserve `aplus_opportunities` in Flow state
6. WHEN the report is generated, THE ReportCrew SHALL include `aplus_opportunities` in the crew inputs
7. WHEN A+ opportunities exist, THE ReportCrew SHALL display them in a dedicated "Opportunités A+" section
8. WHEN no A+ opportunities exist, THE ReportCrew SHALL indicate that discovery was not run or found no candidates
9. WHEN stock analysis includes SEC data, THE FinwizFlow SHALL preserve SEC filing URLs in Flow state
10. WHEN the report displays stock holdings, THE ReportCrew SHALL include clickable links to relevant SEC filings (10-K, 10-Q)
11. WHEN SEC data is unavailable, THE ReportCrew SHALL indicate "No SEC filings available"
12. WHEN `prepare_crew_context` merges Flow state inputs, THE ReportCrew SHALL include `data_availability_summary` in the `required_keys` list
13. WHEN `prepare_crew_context` merges Flow state inputs, THE ReportCrew SHALL log successful preservation of `data_availability_summary`
14. WHEN `data_availability_summary` is missing from Flow state, THE ReportCrew SHALL log a warning indicating the key was not found
# Requirements Document: Fix Hardcoding Issues

## Introduction

FinWiz currently suffers from pervasive hardcoding issues that compromise data integrity and analysis accuracy. Default values are used throughout the codebase when real data should be calculated, leading to grade inflation, identical risk profiles across different assets, and loss of user trust. This spec addresses the systematic removal of hardcoded defaults and implementation of proper data quality tracking.

## Glossary

- **System**: FinWiz financial analysis platform
- **Deep Analysis Scorer**: Python-based scoring engine that calculates composite scores and grades
- **Quantitative Analysis Tool**: Tool that calculates risk metrics (volatility, max drawdown, beta)
- **Alternative Finder**: Tool that recommends alternative investments for underperforming holdings
- **Data Quality Metrics**: Tracking system for calculated vs defaulted vs missing data fields
- **Grade Inflation**: Phenomenon where most assets receive A/A+ grades due to optimistic defaults
- **Composite Score**: Weighted score (0.0-1.0) combining fundamental, technical, and risk analysis
- **Risk Metrics**: Volatility, maximum drawdown, beta, and other risk measurements
- **Crew Output**: Structured data returned by CrewAI crews after analysis

## Requirements

### Requirement 1: Eliminate Risk Metrics Hardcoding

**User Story:** As a portfolio manager, I want each asset to display its actual calculated risk metrics, so that I can accurately assess and compare risk profiles across different investments.

#### Acceptance Criteria

1. WHEN the System calculates risk metrics for an asset, THE System SHALL use actual calculated values from historical price data
2. WHEN volatility data is unavailable, THE System SHALL log a warning and mark the field as "missing" rather than using a default value
3. WHEN max drawdown data is unavailable, THE System SHALL log a warning and mark the field as "missing" rather than using a default value
4. WHEN the Quantitative Analysis Tool returns risk metrics, THE System SHALL properly extract and pass volatility, max_drawdown, and beta to the Deep Analysis Scorer
5. WHEN displaying risk metrics in reports, THE System SHALL show actual calculated values with data quality indicators

### Requirement 2: Eliminate Grade Hardcoding

**User Story:** As an investor, I want to see realistic grade distributions across my portfolio and discovery recommendations, so that I can identify truly exceptional (A+) investments versus average (C) or poor (D/F) ones.

#### Acceptance Criteria

1. WHEN the Alternative Finder recommends alternatives, THE System SHALL calculate grades from composite scores rather than defaulting to "A+"
2. WHEN the Portfolio Review displays alternatives, THE System SHALL use calculated grades rather than defaulting to "A+"
3. WHEN the Template Renderer processes discovery data, THE System SHALL require explicit grades rather than defaulting to "A+"
4. WHEN the Investment Discovery Schema creates candidates, THE System SHALL validate that grades are explicitly calculated
5. WHEN the Feedback Tools record recommendations, THE System SHALL use actual recommendation grades rather than assuming "A+"

### Requirement 3: Eliminate Composite Score Hardcoding

**User Story:** As a financial analyst, I want composite scores to reflect actual analysis results, so that investment recommendations are based on real data rather than optimistic defaults.

#### Acceptance Criteria

1. WHEN the Flow Orchestrator processes crew results, THE System SHALL extract actual composite scores rather than defaulting to 0.7
2. WHEN the Alternative Finder evaluates alternatives, THE System SHALL use calculated composite scores rather than defaulting to 0.85
3. WHEN the A+ Extractor processes discovery candidates, THE System SHALL require explicit composite scores for stocks, ETFs, and crypto
4. WHEN composite scores are missing, THE System SHALL raise an error or mark the analysis as incomplete
5. WHEN displaying composite scores, THE System SHALL verify they match the calculated grade according to the grading scale

### Requirement 4: Implement Data Quality Tracking

**User Story:** As a system administrator, I want to track which data fields are calculated versus defaulted versus missing, so that I can monitor data quality and identify issues early.

#### Acceptance Criteria

1. WHEN the System calculates analysis results, THE System SHALL track which fields were calculated from real data
2. WHEN the System uses default values, THE System SHALL log warnings and record the field as "defaulted"
3. WHEN data is completely missing, THE System SHALL record the field as "missing" and include it in quality metrics
4. WHEN analysis completes, THE System SHALL calculate a data completeness score (0.0-1.0) based on calculated vs defaulted vs missing fields
5. WHEN data quality is low (completeness < 0.7), THE System SHALL mark the analysis with a quality warning

### Requirement 5: Add Data Quality Indicators to Reports

**User Story:** As an investor, I want to see data quality indicators in analysis reports, so that I can assess the reliability of recommendations before making investment decisions.

#### Acceptance Criteria

1. WHEN the System generates HTML reports, THE System SHALL display data quality level (high/medium/low) prominently
2. WHEN data quality is "low", THE System SHALL show a warning message: "⚠️ Limited data available - results may be less reliable"
3. WHEN data quality is "medium", THE System SHALL show an info message: "ℹ️ Some data estimated - verify before investing"
4. WHEN data quality is "high", THE System SHALL show a success message: "✅ High quality data - comprehensive analysis"
5. WHEN users hover over quality indicators, THE System SHALL display which specific fields were calculated vs defaulted vs missing

### Requirement 6: Standardize Default Handling

**User Story:** As a developer, I want consistent default handling across the codebase, so that behavior is predictable and maintainable.

#### Acceptance Criteria

1. WHEN the System encounters missing data, THE System SHALL follow a standardized default handling policy
2. WHEN critical fields are missing (grade, composite_score, volatility), THE System SHALL raise ValueError rather than using defaults
3. WHEN optional fields are missing, THE System SHALL use None rather than optimistic defaults
4. WHEN defaults must be used, THE System SHALL use consistent values across all modules
5. WHEN the System uses a default value, THE System SHALL log the event at WARNING level with context

### Requirement 7: Implement Fail-Loud Error Handling

**User Story:** As a system operator, I want the system to fail loudly when critical data is missing, so that I can identify and fix data collection issues rather than silently producing incorrect results.

#### Acceptance Criteria

1. WHEN grade data is missing from crew output, THE System SHALL raise ValueError with message "Missing grade for {ticker}"
2. WHEN composite score is missing from crew output, THE System SHALL raise ValueError with message "Missing composite_score for {ticker}"
3. WHEN risk metrics are missing from quantitative analysis, THE System SHALL raise ValueError with message "Missing risk metrics for {ticker}"
4. WHEN the System raises data validation errors, THE System SHALL include the ticker symbol and missing field names in the error message
5. WHEN validation errors occur, THE System SHALL log the full context (ticker, asset_class, attempted operation) for debugging

### Requirement 8: Validate Score-to-Grade Mapping

**User Story:** As a quality assurance engineer, I want to ensure that grades always match their corresponding composite scores, so that users see consistent and accurate information.

#### Acceptance Criteria

1. WHEN the System assigns a grade, THE System SHALL verify it matches the composite score according to the grading scale
2. WHEN composite_score >= 0.95, THE System SHALL assign grade "A+"
3. WHEN 0.85 <= composite_score < 0.95, THE System SHALL assign grade "A"
4. WHEN 0.75 <= composite_score < 0.85, THE System SHALL assign grade "B+"
5. WHEN grade and composite_score are inconsistent, THE System SHALL raise ValidationError with details

### Requirement 9: Track Grade Distribution Metrics

**User Story:** As a product manager, I want to monitor grade distribution across analyses, so that I can detect grade inflation and ensure realistic distributions.

#### Acceptance Criteria

1. WHEN the System completes portfolio analysis, THE System SHALL record the distribution of grades (A+, A, B, C, D, F)
2. WHEN grade distribution is unrealistic (>50% A+), THE System SHALL log a warning about potential grade inflation
3. WHEN the System generates discovery recommendations, THE System SHALL track the percentage of A+ candidates
4. WHEN monitoring grade distributions, THE System SHALL compare against expected realistic distributions
5. WHEN grade inflation is detected, THE System SHALL alert administrators via logging

### Requirement 10: Implement Data Quality Schema

**User Story:** As a developer, I want a standardized schema for tracking data quality, so that all components consistently report quality metrics.

#### Acceptance Criteria

1. WHEN the System creates analysis results, THE System SHALL include a DataQualityMetrics object
2. WHEN DataQualityMetrics is created, THE System SHALL populate fields_calculated list with all calculated field names
3. WHEN DataQualityMetrics is created, THE System SHALL populate fields_defaulted list with all defaulted field names
4. WHEN DataQualityMetrics is created, THE System SHALL populate fields_missing list with all missing field names
5. WHEN DataQualityMetrics is created, THE System SHALL calculate completeness_score as (calculated / total_fields)

### Requirement 11: Add Comprehensive Logging

**User Story:** As a system administrator, I want detailed logging of data quality issues, so that I can diagnose and fix problems quickly.

#### Acceptance Criteria

1. WHEN the System uses a default value, THE System SHALL log at WARNING level: "Using default {field}={value} for {ticker}"
2. WHEN the System encounters missing data, THE System SHALL log at ERROR level: "Missing required field {field} for {ticker}"
3. WHEN data quality is low, THE System SHALL log at WARNING level: "Low data quality ({score:.1%}) for {ticker}"
4. WHEN the System successfully calculates all fields, THE System SHALL log at INFO level: "High quality analysis for {ticker} ({score:.1%} complete)"
5. WHEN logging data quality events, THE System SHALL include ticker, asset_class, field names, and quality score

### Requirement 12: Implement Gradual Rollout

**User Story:** As a release manager, I want to roll out hardcoding fixes gradually, so that we can validate each change without breaking production.

#### Acceptance Criteria

1. WHEN deploying Phase 1 (risk metrics), THE System SHALL maintain backward compatibility with existing reports
2. WHEN deploying Phase 2 (grades), THE System SHALL add warnings before enforcing strict validation
3. WHEN deploying Phase 3 (UI indicators), THE System SHALL make quality indicators optional via feature flag
4. WHEN a phase fails validation, THE System SHALL allow rollback to previous behavior via configuration
5. WHEN all phases are deployed, THE System SHALL remove backward compatibility code and feature flags

### Requirement 13: Validate Against Real Data

**User Story:** As a QA engineer, I want to validate fixes against real market data, so that I can ensure the system produces accurate results for actual investments.

#### Acceptance Criteria

1. WHEN testing risk metrics fixes, THE System SHALL analyze 10 different stocks and verify unique volatility values
2. WHEN testing grade fixes, THE System SHALL analyze 20 different assets and verify realistic grade distribution
3. WHEN testing composite scores, THE System SHALL verify scores match calculated grades for 50 test cases
4. WHEN testing data quality tracking, THE System SHALL verify quality metrics are accurate for 100 analyses
5. WHEN validation tests pass, THE System SHALL produce a test report showing grade distribution and risk metric variance

### Requirement 14: Implement Complete Data Lineage Tracking

**User Story:** As a data scientist, I want complete data lineage for every calculation, so that I can trace where values came from, what transformations were applied, and reproduce results for validation and debugging.

#### Acceptance Criteria

1. WHEN the System calculates any metric, THE System SHALL record the data source (API, cache, calculation) with timestamp
2. WHEN the System applies transformations, THE System SHALL record the transformation type, input values, and output values
3. WHEN the System uses calculated values in scoring, THE System SHALL record which raw metrics contributed to each score component
4. WHEN the System generates final grades, THE System SHALL record the complete calculation chain from raw data to final grade
5. WHEN data scientists request lineage, THE System SHALL provide a complete audit trail showing: data sources → transformations → calculations → scores → grades

### Requirement 15: Provide Lineage Query Interface

**User Story:** As a data scientist, I want to query data lineage for specific tickers and metrics, so that I can understand and validate calculation logic without reading code.

#### Acceptance Criteria

1. WHEN querying lineage for a ticker, THE System SHALL return all data sources used in the analysis
2. WHEN querying lineage for a specific metric (e.g., volatility), THE System SHALL show: raw data points → calculation method → final value
3. WHEN querying lineage for composite scores, THE System SHALL show: component scores → weights → calculation → final score
4. WHEN querying lineage for grades, THE System SHALL show: composite score → grading scale → assigned grade
5. WHEN lineage data is incomplete, THE System SHALL clearly indicate which steps are missing or estimated

### Requirement 16: Export Lineage for Reproducibility

**User Story:** As a data scientist, I want to export complete lineage data, so that I can reproduce calculations independently and validate results in external tools (Python notebooks, R, Excel).

#### Acceptance Criteria

1. WHEN exporting lineage, THE System SHALL provide data in JSON format with all calculation steps
2. WHEN exporting lineage, THE System SHALL include raw input data, transformation formulas, and intermediate results
3. WHEN exporting lineage, THE System SHALL include timestamps for all data sources (to verify data freshness)
4. WHEN exporting lineage, THE System SHALL include version information (scorer version, formula version)
5. WHEN data scientists import lineage data, THE System SHALL provide example code (Python/R) to reproduce calculations

---

**Version**: 2.0  
**Created**: 2025-10-28  
**Updated**: 2025-10-29  
**Status**: Requirements Complete - Added Data Lineage Requirements (14-16)
# Requirements Document: Flow Resilience and Recovery

## Introduction

This feature adds comprehensive resilience, recovery, and checkpoint capabilities to the FinWiz flow orchestrator. Currently, when the flow encounters connection failures or errors during deep analysis of portfolio holdings, the entire process fails and must be restarted from scratch. This results in wasted API calls, lost progress, and poor user experience.

The flow resilience and recovery feature will enable the system to:
- Automatically retry failed operations with intelligent backoff strategies
- Save progress checkpoints to disk for recovery after failures
- Resume interrupted flows from the last successful checkpoint
- Handle partial failures gracefully without stopping the entire flow
- Provide detailed progress tracking and monitoring
- Implement timeout management to prevent indefinite hangs

This feature is critical for production reliability, especially when analyzing large portfolios (50+ holdings) where the probability of at least one failure approaches 100%.

## Requirements

### Requirement 1: Automatic Retry with Exponential Backoff

**User Story:** As a FinWiz user, I want the system to automatically retry failed operations so that transient network issues don't cause my entire analysis to fail.

#### Acceptance Criteria

1. WHEN a crew execution fails with a retryable error (connection timeout, rate limit, 5xx server error) THEN the system SHALL retry the operation with exponential backoff
2. WHEN retrying an operation THEN the system SHALL use exponential backoff with configurable base delay (default: 2 seconds), multiplier (default: 2), and maximum delay (default: 60 seconds)
3. WHEN retrying an operation THEN the system SHALL add jitter (random delay variation) to prevent thundering herd problems
4. WHEN the maximum retry count is reached (default: 3 attempts) THEN the system SHALL mark the operation as failed and continue with graceful degradation
5. IF an error is non-retryable (invalid ticker, authentication failure, validation error) THEN the system SHALL NOT retry and SHALL immediately mark as failed
6. WHEN retrying THEN the system SHALL log each retry attempt with attempt number, delay, and error details
7. WHEN all retries are exhausted THEN the system SHALL log a final error message with full context for debugging

### Requirement 2: Progress Checkpointing with CrewAI Flow State Persistence

**User Story:** As a FinWiz user, I want the system to save progress periodically using CrewAI's native state persistence so that if the analysis is interrupted, I don't lose all my work and API quota.

#### Acceptance Criteria

1. WHEN implementing checkpointing THEN the system SHALL use CrewAI's `@persist()` decorator for automatic state persistence
2. WHEN defining flow state THEN the system SHALL use a structured Pydantic model (not unstructured dict) for type safety and validation
3. WHEN a holding analysis completes successfully THEN the system SHALL persist the flow state containing: timestamp, ticker, asset_class, analysis result, holdings_processed count, holdings_remaining count, and error tracking
4. WHEN saving state THEN the system SHALL leverage CrewAI's built-in atomic file operations to prevent corruption
5. WHEN state is persisted THEN the system SHALL use CrewAI's default storage mechanism with the flow's unique UUID for identification
6. WHEN multiple flow executions exist THEN the system SHALL use CrewAI's state management to track each execution independently by UUID
7. WHEN state persistence fails THEN the system SHALL log the error but continue execution (persistence failure is not fatal)

### Requirement 3: Flow Resume Capability with CrewAI State Loading

**User Story:** As a FinWiz user, I want to resume an interrupted analysis from where it left off using CrewAI's state loading so that I don't waste time and API quota re-analyzing holdings that already succeeded.

#### Acceptance Criteria

1. WHEN starting the application THEN the system SHALL check for existing persisted flow states in the CrewAI storage directory
2. IF one or more persisted states exist THEN the system SHALL display a list of available sessions with: UUID, age, progress (holdings processed/total), and last update timestamp
3. IF valid persisted state exists and is less than 24 hours old THEN the system SHALL prompt the user with options: "Resume", "Start Fresh", or "Cancel"
4. WHEN the user selects "Resume" THEN the system SHALL load the selected flow state using CrewAI's state loading mechanism
5. WHEN resuming from persisted state THEN the system SHALL use conditional `@start()` methods to skip already-completed holdings based on state
6. WHEN resuming THEN the system SHALL log which holdings are being skipped (already completed) and which remain to be analyzed
7. WHEN the user selects "Start Fresh" THEN the system SHALL create a new flow instance with a new UUID and ignore existing state
8. IF persisted state is older than 24 hours THEN the system SHALL warn the user and recommend starting fresh but still allow resume
9. IF persisted state is incompatible or corrupted THEN the system SHALL log an error, display the issue to the user, and automatically start a fresh execution
10. WHEN resume is complete THEN the system SHALL merge persisted results with new results into a unified output
11. WHEN the flow completes successfully THEN the system SHALL optionally clean up the persisted state file (configurable via FINWIZ_CLEANUP_STATE_ON_SUCCESS)
12. WHEN the user provides a specific UUID via CLI argument (--resume-uuid) THEN the system SHALL attempt to resume that specific session without prompting

### Requirement 4: Graceful Degradation for Partial Failures

**User Story:** As a FinWiz user, I want the system to continue analyzing other holdings even if one holding fails, so that I get partial results rather than complete failure.

#### Acceptance Criteria

1. WHEN a holding analysis fails after all retries THEN the system SHALL mark that holding as failed and continue with remaining holdings
2. WHEN a holding fails THEN the system SHALL use baseline analysis data as a fallback if available
3. WHEN using fallback data THEN the system SHALL mark the result with a confidence flag indicating degraded quality
4. WHEN the flow completes THEN the system SHALL provide a summary showing: successful analyses, failed analyses, and fallback analyses
5. WHEN failures occur THEN the system SHALL include a detailed error report with ticker, error type, and suggested remediation
6. IF more than 50% of holdings fail THEN the system SHALL log a critical warning suggesting investigation of systemic issues
7. WHEN the flow completes with partial failures THEN the system SHALL still generate a portfolio review using available data

### Requirement 5: Timeout Management

**User Story:** As a FinWiz user, I want the system to enforce timeouts on long-running operations so that a single stuck analysis doesn't block the entire flow indefinitely.

#### Acceptance Criteria

1. WHEN analyzing a single holding THEN the system SHALL enforce a configurable timeout (default: 5 minutes)
2. IF a holding analysis exceeds the timeout THEN the system SHALL cancel the operation and mark it as failed
3. WHEN a timeout occurs THEN the system SHALL log the timeout with ticker, duration, and last known state
4. WHEN a timeout occurs THEN the system SHALL attempt graceful cancellation before forcing termination
5. WHEN the entire flow is running THEN the system SHALL enforce a global timeout (default: 2 hours)
6. IF the global timeout is reached THEN the system SHALL save a checkpoint and terminate gracefully
7. WHEN timeouts are configured THEN the system SHALL validate that per-holding timeout is less than global timeout

### Requirement 6: Progress Tracking and Monitoring

**User Story:** As a FinWiz user, I want to see real-time progress updates during analysis so that I know the system is working and can estimate completion time.

#### Acceptance Criteria

1. WHEN the flow starts THEN the system SHALL display total holdings count and estimated completion time
2. WHEN each holding completes THEN the system SHALL update progress with: holdings completed, holdings remaining, success rate, and estimated time remaining
3. WHEN progress updates are displayed THEN the system SHALL show: ticker, status (success/failed/timeout), execution time, and grade (if successful)
4. WHEN the flow is running THEN the system SHALL update progress at least every 10 seconds
5. WHEN failures occur THEN the system SHALL update the progress display to show failure count and types
6. WHEN the flow completes THEN the system SHALL display a final summary with: total time, success rate, failure breakdown, and performance metrics
7. WHEN progress is tracked THEN the system SHALL calculate and display: average time per holding, API calls per holding, and cache hit rate

### Requirement 7: Configuration Management (Leverage Existing Infrastructure)

**User Story:** As a FinWiz developer, I want to configure resilience parameters via environment variables using the existing configuration patterns so that I can tune behavior for different environments without code changes.

#### Acceptance Criteria

1. WHEN the system starts THEN the system SHALL load resilience configuration from environment variables using existing `os.getenv()` patterns with sensible defaults
2. WHEN configuring retry behavior THEN the system SHALL support: `FINWIZ_MAX_RETRIES` (default: 3), `FINWIZ_RETRY_BASE_DELAY` (default: 2), `FINWIZ_RETRY_MAX_DELAY` (default: 60)
3. WHEN configuring timeouts THEN the system SHALL support: `FINWIZ_HOLDING_TIMEOUT` (default: 300), `FINWIZ_FLOW_TIMEOUT` (default: 7200)
4. WHEN configuring resume behavior THEN the system SHALL support: `FINWIZ_AUTO_RESUME` (default: false), `FINWIZ_STATE_MAX_AGE_HOURS` (default: 24)
5. WHEN configuring state persistence THEN the system SHALL use CrewAI's default persistence location (no custom directory needed)
6. WHEN invalid configuration is provided THEN the system SHALL follow existing patterns (log warning, use defaults) as seen in `portfolio_review.py`
7. WHEN configuration is loaded THEN the system SHALL log all active resilience settings using existing logger infrastructure

### Requirement 8: Integration with Existing Parallelization and CrewAI Flow State

**User Story:** As a FinWiz developer, I want resilience features to work seamlessly with the existing parallel processing implementation and CrewAI Flow state management so that I get both speed and reliability.

#### Acceptance Criteria

1. WHEN parallel processing is enabled THEN retry logic SHALL apply to each parallel task independently
2. WHEN parallel processing is enabled THEN flow state SHALL be persisted using `@persist()` after each batch completes
3. WHEN resuming with parallel processing THEN the system SHALL use flow state to skip entire batches that completed successfully
4. WHEN a parallel batch has partial failures THEN the system SHALL track failures in flow state and retry only the failed holdings
5. WHEN parallel processing is enabled THEN timeout management SHALL apply to individual holdings, not the entire batch
6. WHEN parallel processing is enabled THEN progress tracking SHALL update flow state with per-batch and overall progress
7. WHEN parallel processing is enabled THEN the system SHALL respect concurrency limits while retrying failed operations
8. WHEN updating flow state from parallel tasks THEN the system SHALL use thread-safe operations to prevent race conditions

### Requirement 9: Error Classification and Reporting (Extend Existing ValidationError)

**User Story:** As a FinWiz user, I want clear error messages that explain what went wrong and what I can do about it, leveraging the existing ValidationError infrastructure.

#### Acceptance Criteria

1. WHEN an error occurs THEN the system SHALL classify it using existing `ValidationError` structure with `error_type` field: retryable (network, rate_limit, timeout), non-retryable (validation, authentication), or unknown
2. WHEN reporting errors THEN the system SHALL use `ValidationError.context` to include: ticker, timestamp, retry_count, and suggested remediation
3. WHEN multiple errors occur THEN the system SHALL use `ValidationResult` to collect and group errors by type in the final report
4. WHEN network errors occur THEN the system SHALL add remediation context suggesting checking connectivity and API status
5. WHEN rate limit errors occur THEN the system SHALL add remediation context suggesting reducing parallelism or increasing delays
6. WHEN authentication errors occur THEN the system SHALL add remediation context suggesting checking API keys
7. WHEN validation errors occur THEN the system SHALL add remediation context suggesting checking ticker symbols and input data

### Requirement 10: Monitoring and Observability (Integrate with Existing AlertManager)

**User Story:** As a FinWiz operator, I want detailed metrics and logs about flow execution integrated with the existing monitoring infrastructure so that I can monitor system health and diagnose issues.

#### Acceptance Criteria

1. WHEN the flow executes THEN the system SHALL track key metrics in flow state: total execution time, holdings processed, success rate, retry count, timeout count, persistence operations
2. WHEN the flow completes THEN the system SHALL calculate and log performance metrics from flow state: average time per holding, API calls per holding, cache hit rate, speedup from parallelization
3. WHEN errors occur THEN the system SHALL store structured error data in flow state using existing `ValidationError` format for consistency
4. WHEN critical failures occur (>50% failure rate) THEN the system SHALL integrate with existing `AlertManager` to send alerts via configured channels
5. WHEN retries occur THEN the system SHALL track retry metrics in flow state: total retries, retries per error type, average retry delay
6. WHEN the flow completes THEN the system SHALL export flow state metrics to a JSON file compatible with existing monitoring dashboards
7. WHEN monitoring is enabled THEN the system SHALL use existing `get_logger()` infrastructure for consistent logging across the codebase

---

**Version**: 1.0  
**Created**: 2025-01-11  
**Purpose**: Enable robust, production-ready flow execution with automatic recovery from failures
# Requirements - Agents de Recherche d'Investissements A+

## Introduction

Cette spec définit le développement d'agents IA spécialisés dans la découverte proactive d'investissements de grade A+ pour optimiser les portefeuilles FinWiz. L'objectif est de passer d'un système réactif (évaluation de l'existant) à un système proactif (découverte d'opportunités excellentes).

## Requirements

### Requirement 1 - Agent de Découverte d'ETFs A+

**User Story:** En tant qu'investisseur, je veux que le système identifie automatiquement les ETFs de grade A+ disponibles sur le marché, afin d'améliorer la qualité moyenne de mon portefeuille.

#### Acceptance Criteria

1. WHEN l'agent analyse le marché des ETFs THEN il SHALL identifier les ETFs avec un potentiel de grade A+ (score ≥ 0.95)
2. WHEN l'agent évalue un ETF THEN il SHALL analyser les critères suivants :
   - Frais de gestion ≤ 0.15% pour les ETFs larges, ≤ 0.25% pour les spécialisés
   - AUM ≥ 1 milliard USD pour la liquidité
   - Tracking error ≤ 0.20% sur 3 ans
   - Historique ≥ 3 ans de performance
   - Compatibilité UCITS pour les investisseurs suisses
3. WHEN l'agent trouve des ETFs A+ THEN il SHALL les comparer aux positions actuelles du portefeuille
4. WHEN des améliorations sont possibles THEN il SHALL générer des recommandations de remplacement avec justification

### Requirement 2 - Agent de Découverte d'Actions A+

**User Story:** En tant qu'investisseur, je veux que le système identifie les actions individuelles de grade A+ avec un potentiel de croissance exceptionnel, afin de maximiser les rendements de ma portion actions.

#### Acceptance Criteria

1. WHEN l'agent analyse les actions THEN il SHALL utiliser les critères A+ suivants :
   - ROE ≥ 20% sur 3 ans
   - Croissance du chiffre d'affaires ≥ 15% annuel sur 5 ans
   - Ratio dette/capitaux propres ≤ 0.3
   - Free Cash Flow positif et croissant
   - Position dominante dans un secteur en croissance
2. WHEN l'agent évalue une action THEN il SHALL vérifier la compatibilité avec les objectifs de l'investisseur
3. WHEN l'agent trouve des actions A+ THEN il SHALL évaluer leur corrélation avec le portefeuille existant
4. WHEN des opportunités sont identifiées THEN il SHALL proposer des allocations optimales

### Requirement 3 - Agent de Découverte Crypto A+

**User Story:** En tant qu'investisseur crypto, je veux que le système identifie les cryptomonnaies de grade A+ avec des fondamentaux solides, afin d'optimiser ma petite allocation crypto (5%).

#### Acceptance Criteria

1. WHEN l'agent analyse les cryptos THEN il SHALL évaluer les critères A+ suivants :
   - Capitalisation ≥ 10 milliards USD
   - Volume de trading quotidien ≥ 500 millions USD
   - Adoption institutionnelle croissante
   - Utilité réelle et cas d'usage prouvés
   - Équipe de développement active et transparente
2. WHEN l'agent évalue une crypto THEN il SHALL analyser les risques réglementaires par juridiction
3. WHEN des cryptos A+ sont identifiées THEN il SHALL recommander des stratégies d'acquisition (DCA, timing)
4. WHEN la limite de 5% est atteinte THEN il SHALL proposer des rééquilibrages internes

### Requirement 4 - Système de Scoring Dynamique A+

**User Story:** En tant qu'utilisateur du système, je veux que les critères de grade A+ évoluent avec les conditions de marché, afin que les recommandations restent pertinentes dans différents environnements économiques.

#### Acceptance Criteria

1. WHEN les conditions de marché changent THEN le système SHALL ajuster les seuils A+ automatiquement
2. WHEN l'inflation est élevée (>4%) THEN il SHALL privilégier les actifs réels et les actions avec pricing power
3. WHEN les taux montent rapidement THEN il SHALL ajuster les critères pour les REITs et utilities
4. WHEN la volatilité augmente (VIX >25) THEN il SHALL renforcer les critères de qualité et de stabilité

### Requirement 5 - Intégration avec le Système de Grading

**User Story:** En tant qu'utilisateur, je veux que les découvertes A+ soient intégrées dans mes rapports de portefeuille, afin de voir clairement les opportunités d'amélioration.

#### Acceptance Criteria

1. WHEN un rapport de portefeuille est généré THEN il SHALL inclure une section "Opportunités A+ Identifiées"
2. WHEN des améliorations A+ sont possibles THEN le rapport SHALL montrer l'impact sur la note moyenne du portefeuille
3. WHEN des remplacements sont suggérés THEN il SHALL afficher une comparaison avant/après avec les nouvelles notes
4. WHEN l'utilisateur accepte une recommandation THEN le système SHALL mettre à jour automatiquement les allocations cibles

### Requirement 6 - Validation et Backtesting

**User Story:** En tant qu'investisseur prudent, je veux que toutes les recommandations A+ soient validées par des données historiques, afin de m'assurer de leur qualité réelle.

#### Acceptance Criteria

1. WHEN un investissement A+ est recommandé THEN il SHALL avoir été backtesté sur au moins 5 ans
2. WHEN le backtesting est effectué THEN il SHALL inclure différents environnements de marché (bull, bear, sideways)
3. WHEN les résultats sont présentés THEN ils SHALL inclure les métriques de risque ajusté (Sharpe, Sortino, Max Drawdown)
4. WHEN un investissement ne passe pas la validation THEN il SHALL être exclu des recommandations A+

### Requirement 7 - Monitoring Continu

**User Story:** En tant qu'investisseur, je veux que le système surveille continuellement mes positions A+ pour s'assurer qu'elles maintiennent leur grade, afin d'éviter la dégradation silencieuse de la qualité.

#### Acceptance Criteria

1. WHEN une position A+ se dégrade THEN le système SHALL alerter l'utilisateur dans les 24h
2. WHEN les fondamentaux changent THEN il SHALL recalculer automatiquement le grade
3. WHEN un A+ devient B+ ou moins THEN il SHALL proposer des alternatives de remplacement
4. WHEN le monitoring détecte des tendances THEN il SHALL ajuster les critères de screening futurs

## Edge Cases et Considérations

### Gestion des Conflits

- Que faire si un investissement A+ ne correspond pas au profil de risque de l'utilisateur ?
- Comment gérer les investissements A+ avec des corrélations élevées ?

### Limites Réglementaires

- Respect des restrictions UCITS pour les investisseurs européens
- Gestion des limites de concentration par position

### Performance du Système

- Optimisation des requêtes de screening sur de grandes bases de données
- Mise en cache des résultats de scoring pour éviter les recalculs

### Personnalisation

- Adaptation des critères A+ selon le profil d'investisseur (conservateur, équilibré, agressif)
- Prise en compte des préférences ESG et d'impact

## Success Metrics

1. **Amélioration de la qualité du portefeuille** : Augmentation de la note moyenne de 10% minimum
2. **Taux de découverte** : Identification d'au moins 5 opportunités A+ par mois
3. **Précision des recommandations** : 80% des investissements A+ recommandés maintiennent leur grade sur 6 mois
4. **Adoption utilisateur** : 70% des recommandations A+ sont acceptées par les utilisateurs
5. **Performance relative** : Les positions A+ surperforment leur benchmark de 2% annualisé minimum
# Requirements Document: JSON-First Crew Architecture

## Introduction

This specification defines the migration of FinWiz crew task outputs from markdown-based to JSON-based structured data format. The goal is to improve data flow, validation, and integration between crews while maintaining human-readable final reports.

### Current State

Currently, FinWiz crews generate markdown (`.md`) files for intermediate analysis tasks and HTML files for final reports. This approach has several limitations:

- Markdown parsing required for data extraction
- No schema validation for intermediate outputs
- Inconsistent data structures between crews
- Difficult integration and data flow between tasks
- Error-prone data extraction from text

### Target State

All intermediate crew tasks will output validated JSON data conforming to Pydantic schemas, while final reports remain in HTML format for human readability. This enables:

- Automatic schema validation at task boundaries
- Type-safe data flow between tasks
- Consistent data structures across all crews
- Easier integration with external systems
- Improved debugging and error handling

## Requirements

### Requirement 1: Structured Data Output

**User Story:** As a FinWiz developer, I want intermediate crew tasks to output validated JSON data, so that data flows
cleanly between tasks with guaranteed schema compliance.

#### Acceptance Criteria

1. WHEN an intermediate analysis task completes THEN the system SHALL output a JSON file with Pydantic-validated structure
1. WHEN a task has `output_pydantic` defined THEN the output SHALL conform to the specified schema
1. WHEN schema validation fails THEN the system SHALL provide clear error messages with field-level details
1. WHEN JSON output is generated THEN it SHALL include all required fields as defined in the schema
1. IF a task is a final report task THEN it MAY output HTML format for human readability

### Requirement 2: Schema Design

**User Story:** As a FinWiz developer, I want comprehensive Pydantic schemas for all crew outputs, so that data
structures are well-defined and validated.

#### Acceptance Criteria

1. WHEN creating schemas THEN each crew SHALL have schemas for all intermediate task outputs
1. WHEN defining schemas THEN they SHALL use Pydantic v2 with `extra='forbid'` for strict validation
1. WHEN schemas reference other schemas THEN they SHALL use proper type hints and imports
1. WHEN a schema is created THEN it SHALL include docstrings and field descriptions
1. WHEN schemas are updated THEN backward compatibility SHALL be maintained or migration paths provided

### Requirement 3: Task Configuration

**User Story:** As a FinWiz developer, I want task configurations to specify output schemas, so that the system
knows what structure to validate against.

#### Acceptance Criteria

1. WHEN configuring an intermediate task THEN it SHALL specify `output_pydantic` with the schema class
1. WHEN configuring a final report task THEN it SHALL NOT specify `output_pydantic` (HTML output)
1. WHEN a task has `output_pydantic` THEN the `output_file` SHALL have `.json` extension
1. WHEN a task generates HTML THEN the `output_file` SHALL have `.html` extension
1. WHEN task configuration is invalid THEN the system SHALL fail fast with clear error messages

### Requirement 4: Data Flow Between Tasks

**User Story:** As a FinWiz developer, I want tasks to consume JSON outputs from previous tasks, so that data flows
seamlessly through the crew pipeline.

#### Acceptance Criteria

1. WHEN a task depends on another task THEN it SHALL be able to read the JSON output directly
1. WHEN reading JSON output THEN the system SHALL deserialize it into Pydantic models
1. WHEN data is missing or invalid THEN the system SHALL provide clear error messages
1. WHEN tasks run in sequence THEN JSON data SHALL be passed through the context
1. WHEN parallel tasks complete THEN their JSON outputs SHALL be aggregated for downstream tasks

### Requirement 5: Backward Compatibility

**User Story:** As a FinWiz user, I want existing functionality to continue working during migration, so that the
 system remains stable.

#### Acceptance Criteria

1. WHEN migrating tasks THEN existing markdown outputs SHALL be preserved until migration is complete
1. WHEN both formats exist THEN the system SHALL prefer JSON over markdown
1. WHEN reading outputs THEN the system SHALL support both JSON and markdown formats during transition
1. WHEN migration is complete THEN markdown support MAY be removed
1. WHEN errors occur THEN the system SHALL provide clear migration guidance

### Requirement 6: Error Handling

**User Story:** As a FinWiz developer, I want clear error messages when JSON validation fails, so that I can quickly
 identify and fix issues.

#### Acceptance Criteria

1. WHEN JSON parsing fails THEN the error SHALL include the file path and line number
1. WHEN schema validation fails THEN the error SHALL include field path and validation rule
1. WHEN required fields are missing THEN the error SHALL list all missing fields
1. WHEN type mismatches occur THEN the error SHALL show expected vs actual types
1. WHEN validation errors occur THEN the system SHALL log the full output for debugging

### Requirement 7: Final Report Generation

**User Story:** As a FinWiz user, I want final reports to remain in HTML format, so that they are human-readable and
visually appealing.

#### Acceptance Criteria

1. WHEN generating final reports THEN they SHALL be in HTML format
1. WHEN final reports are generated THEN they SHALL consume JSON data from intermediate tasks
1. WHEN HTML is generated THEN it SHALL include all data from upstream JSON outputs
1. WHEN reports are translated THEN the translation task SHALL consume HTML input
1. WHEN reports are complete THEN they SHALL be saved with `.html` extension

### Requirement 8: Schema Documentation

**User Story:** As a FinWiz developer, I want schema documentation, so that I understand the structure of each crew's outputs.

#### Acceptance Criteria

1. WHEN schemas are defined THEN they SHALL include comprehensive docstrings
1. WHEN fields are added THEN they SHALL include descriptions and examples
1. WHEN schemas are complex THEN they SHALL include usage examples
1. WHEN schemas change THEN the documentation SHALL be updated
1. WHEN viewing schemas THEN developers SHALL be able to generate JSON schema files

### Requirement 9: Modern Python 3.12 Type Annotations

**User Story:** As a FinWiz developer, I want schemas to use modern Python 3.12 type annotations, so that code is clean
and follows current best practices.

#### Acceptance Criteria

1. WHEN defining optional fields THEN they SHALL use `Type | None` syntax (Python 3.10+)
1. WHEN defining union types THEN they SHALL use `Type1 | Type2` syntax (Python 3.10+)
1. WHEN schemas are validated THEN they SHALL work correctly with CrewAI's JSON conversion
1. WHEN task output conversion fails THEN the error SHALL provide clear guidance on type annotation issues
1. WHEN migrating schemas THEN all legacy `Optional[Type]` and `Union[Type1, Type2]` syntax SHALL be converted to modern
union operators

## Affected Crews

The following crews will be migrated to JSON-first architecture:

1. **Stock Crew** - 4 intermediate tasks → JSON
2. **ETF Crew** - 4 intermediate tasks → JSON
3. **Crypto Crew** - 4 intermediate tasks → JSON
4. **Investment Discovery Crew** - 6 intermediate tasks → JSON
5. **Portfolio Rebalancing Crew** - 6 intermediate tasks → JSON
6. **Report Crew** - 3 intermediate tasks → JSON (final report remains HTML)

## Known Issues to Address

### Legacy Type Annotation Syntax in Schemas

**Current State**: Recent schema audit (SCHEMA_AUDIT_SUMMARY.md) converted schemas FROM modern Python 3.12 syntax TO
legacy `Optional`/`Union` syntax. This contradicts the project's Python 3.12+ standard documented in README.md and
PYTHON_312_UPGRADE_SUMMARY.md.

**Problem**: Schemas in `src/finwiz/schemas/` currently use:

- `Optional[Type]` instead of `Type | None`
- `Union[Type1, Type2]` instead of `Type1 | Type2`

**Root Cause**: The schema audit was performed under the mistaken belief that CrewAI required legacy syntax. However,
 the project standard is Python 3.12+, and we should use modern type annotations throughout.

**Target State**: All schemas use modern Python 3.12 union operator syntax, consistent with the rest of the codebase.

**Migration Required**: Revert recent schema changes and modernize to Python 3.12 syntax:

- Replace `Optional[Type]` with `Type | None`
- Replace `Union[Type1, Type2]` with `Type1 | Type2`
- Remove unnecessary `from typing import Optional, Union` imports

**Example**:

```python
# ❌ Legacy syntax (currently in schemas after audit)
from typing import Optional, Union

class MySchema(BaseModel):
    field1: Optional[str]
    field2: Union[int, float]

# ✅ Modern Python 3.12 syntax (project standard)
class MySchema(BaseModel):
    field1: str | None
    field2: int | float
```

**Affected Files** (from SCHEMA_AUDIT_SUMMARY.md):

- `src/finwiz/schemas/common.py`
- `src/finwiz/schemas/validation.py`
- `src/finwiz/schemas/portfolio_review.py`
- `src/finwiz/schemas/perplexity.py`
- `src/finwiz/schemas/investment_discovery.py`
- `src/finwiz/schemas/session.py`
- `src/finwiz/schemas/quantitative.py`
- `src/finwiz/schemas/rebalancing/trades.py`

## Out of Scope

The following are explicitly out of scope for this specification:

- Changes to agent behavior or prompts
- Modifications to tool implementations
- Updates to LLM configurations
- Changes to crew orchestration logic
- Database schema changes
- API endpoint modifications
- Performance optimization (separate effort)
- Schema versioning system (future enhancement)

## Success Metrics

1. **Schema Coverage**: 100% of intermediate tasks have Pydantic schemas
1. **Validation Rate**: 100% of JSON outputs pass schema validation
1. **Error Rate**: <1% of tasks fail due to JSON validation errors
1. **Performance**: JSON parsing is ≥2x faster than markdown parsing
1. **Data Quality**: Zero data loss during format conversion

## Dependencies

- Python 3.12+ (required for modern type annotations)
- Pydantic v2 (already in use)
- Existing crew infrastructure
- Current task configuration system
- Schema registry system (if exists)

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Schema design errors | High | Comprehensive testing and validation |
| Breaking changes | High | Phased migration with backward compatibility |
| Performance degradation | Medium | Benchmark before and after migration |
| Agent JSON generation issues | High | Clear prompts and validation feedback |
| Data loss during migration | High | Preserve markdown outputs during transition |
| Legacy type annotations in schemas | High | Revert recent schema audit changes; modernize to Python 3.12 syntax |
| CrewAI compatibility issues | High | Test all schemas with CrewAI converter before deployment |
| Inconsistent type annotation standards | Medium | Establish clear project-wide standard (Python 3.12 modern syntax) |

## Migration Strategy

1. **Phase 1**: Revert schema audit changes to modern Python 3.12 syntax
1. **Phase 2**: Design and implement schemas for all crews
1. **Phase 3**: Update task configurations to use `output_pydantic`
1. **Phase 4**: Test JSON generation with existing crews
1. **Phase 5**: Migrate one crew at a time, starting with simplest
1. **Phase 6**: Remove markdown support after all crews migrated
1. **Phase 7**: Performance optimization and monitoring

## Notes

- Final HTML reports remain unchanged for human readability
- Translation tasks continue to work with HTML inputs
- JSON outputs enable better integration with external systems
- Schema validation improves data quality and debugging
- This change aligns with modern data pipeline best practices
# Requirements Document

## Introduction

This specification defines the requirements for converting FinWiz's existing documentation structure into a professional MkDocs-powered documentation site with automated build and deployment processes via Makefile integration.

## Glossary

- **MkDocs**: Static site generator for project documentation using Markdown
- **Material Theme**: Modern, responsive theme for MkDocs with advanced features
- **Diátaxis Framework**: Documentation methodology organizing content into tutorials, how-to guides, reference, and explanations
- **Site Navigation**: Hierarchical menu structure for documentation organization
- **Build Pipeline**: Automated process for generating static documentation site
- **Hot Reload**: Automatic browser refresh during development when files change

## Requirements

### Requirement 1

**User Story:** As a developer, I want a professional documentation website, so that I can easily navigate and find information about FinWiz.

#### Acceptance Criteria

1. WHEN a developer visits the documentation site, THE Documentation_Site SHALL display a modern, responsive interface with clear navigation
2. WHEN a developer searches for content, THE Documentation_Site SHALL provide full-text search functionality across all documentation
3. WHEN a developer views code examples, THE Documentation_Site SHALL display syntax-highlighted code blocks with copy functionality
4. WHERE dark mode is preferred, THE Documentation_Site SHALL support automatic light/dark theme switching
5. WHILE browsing on mobile devices, THE Documentation_Site SHALL maintain full functionality and readability

### Requirement 2

**User Story:** As a developer, I want automated documentation builds, so that the site stays current with code changes.

#### Acceptance Criteria

1. WHEN documentation files are modified, THE Build_System SHALL automatically regenerate the site during development
2. WHEN running make commands, THE Build_System SHALL provide clear feedback on build status and errors
3. WHEN building for production, THE Build_System SHALL generate optimized static files for deployment
4. IF build errors occur, THEN THE Build_System SHALL display specific error messages with file locations
5. WHILE serving locally, THE Build_System SHALL enable hot reload for immediate preview of changes

### Requirement 3

**User Story:** As a content creator, I want organized documentation structure, so that I can maintain content following the Diátaxis framework.

#### Acceptance Criteria

1. WHEN organizing content, THE Documentation_Structure SHALL follow the four Diátaxis categories (tutorials, how-to, reference, explanations)
2. WHEN adding new documentation, THE Documentation_Structure SHALL provide clear templates and guidelines
3. WHEN cross-referencing content, THE Documentation_Structure SHALL support internal linking with validation
4. WHERE content exists in multiple formats, THE Documentation_Structure SHALL consolidate into single authoritative sources
5. WHILE maintaining backwards compatibility, THE Documentation_Structure SHALL preserve existing URLs where possible

### Requirement 4

**User Story:** As a developer, I want integrated schema documentation, so that I can understand data models and API contracts.

#### Acceptance Criteria

1. WHEN viewing schema documentation, THE Schema_Integration SHALL display JSON schemas with interactive examples
2. WHEN exploring data models, THE Schema_Integration SHALL show Pydantic model definitions with field descriptions
3. WHEN understanding API contracts, THE Schema_Integration SHALL provide request/response examples
4. WHERE schemas are updated, THE Schema_Integration SHALL automatically reflect changes in documentation
5. WHILE developing, THE Schema_Integration SHALL validate schema examples for accuracy

### Requirement 5

**User Story:** As a project maintainer, I want automated documentation deployment, so that updates are published without manual intervention.

#### Acceptance Criteria

1. WHEN documentation changes are committed, THE Deployment_System SHALL automatically build and deploy the updated site
2. WHEN deployment completes, THE Deployment_System SHALL provide confirmation and site URL
3. WHEN deployment fails, THE Deployment_System SHALL provide detailed error logs for troubleshooting
4. WHERE multiple environments exist, THE Deployment_System SHALL support staging and production deployments
5. WHILE maintaining site availability, THE Deployment_System SHALL perform zero-downtime deployments

### Requirement 6

**User Story:** As a developer, I want comprehensive navigation, so that I can quickly find relevant documentation sections.

#### Acceptance Criteria

1. WHEN browsing documentation, THE Navigation_System SHALL provide hierarchical menu structure matching content organization
2. WHEN searching for specific topics, THE Navigation_System SHALL highlight current page location in navigation tree
3. WHEN viewing long documents, THE Navigation_System SHALL provide table of contents with anchor links
4. WHERE related content exists, THE Navigation_System SHALL display "See Also" sections with relevant links
5. WHILE reading documentation, THE Navigation_System SHALL provide breadcrumb navigation for context

### Requirement 7

**User Story:** As a developer, I want development workflow integration, so that documentation tasks integrate seamlessly with existing development processes.

#### Acceptance Criteria

1. WHEN running development commands, THE Workflow_Integration SHALL provide documentation-specific make targets
2. WHEN setting up the development environment, THE Workflow_Integration SHALL install documentation dependencies automatically
3. WHEN validating documentation, THE Workflow_Integration SHALL check for broken links and formatting issues
4. WHERE documentation standards exist, THE Workflow_Integration SHALL enforce formatting and style guidelines
5. WHILE developing features, THE Workflow_Integration SHALL remind developers to update relevant documentation

### Requirement 8

**User Story:** As a user, I want fast site performance, so that I can access information quickly without delays.

#### Acceptance Criteria

1. WHEN loading pages, THE Performance_System SHALL achieve page load times under 2 seconds
2. WHEN searching content, THE Performance_System SHALL return results in under 500 milliseconds
3. WHEN navigating between pages, THE Performance_System SHALL provide instant navigation with prefetching
4. WHERE images are used, THE Performance_System SHALL optimize and lazy-load images for faster rendering
5. WHILE browsing offline, THE Performance_System SHALL provide cached content for previously visited pages# Requirements Document

## Introduction

This feature adds Perplexity Sonar Search as an optional supplementary research capability for FinWiz analyst crews (stocks, ETFs, crypto). A basic Perplexity search tool has already been implemented (`src/finwiz/tools/perplexity_search_tool.py`), but the integration needs to be completed by adding feature flag support, integrating with the enhanced sentiment tool, and implementing the full observability and error handling requirements. The goal is to validate whether Sonar can improve content quality, freshness, and factual grounding of analyst outputs without disrupting existing workflows.

## Requirements

### Requirement 1

**User Story:** As a FinWiz analyst crew (stock, ETF, crypto), I want to optionally access Perplexity Sonar Search results so that I can provide more comprehensive and up-to-date financial research insights across all analysis types.

#### Acceptance Criteria

1. WHEN the PERPLEXITY_RESEARCH feature flag is enabled THEN analyst tools SHALL include Sonar search results in their outputs
2. WHEN the PERPLEXITY_RESEARCH feature flag is disabled THEN all analyst tools SHALL behave exactly as they do today
3. WHEN Sonar search is performed THEN the system SHALL combine results with existing data sources seamlessly
4. WHEN Sonar results are included THEN they SHALL be normalized into each tool's standard output contract
5. WHEN the existing PerplexitySearchTool is used THEN it SHALL integrate with multiple analyst workflows (sentiment, technical, fundamental analysis)

### Requirement 2

**User Story:** As a system administrator, I want proper configuration management for Perplexity integration so that I can control access and monitor usage effectively.

#### Acceptance Criteria

1. WHEN setting up Perplexity integration THEN the system SHALL require PPLX_API_KEY environment variable (already implemented)
2. WHEN the API key is missing AND feature flag is enabled THEN the system SHALL log a warning and fallback to existing providers
3. WHEN configuring the integration THEN the system SHALL support async request flow for concurrency
4. WHEN making Sonar requests THEN the system SHALL apply appropriate filters for financial news and SEC filings
5. WHEN the PERPLEXITY_RESEARCH feature flag is added THEN it SHALL be integrated into the existing feature flags system

### Requirement 3

**User Story:** As a FinWiz operator, I want robust error handling and rate limiting so that Perplexity integration doesn't disrupt existing functionality.

#### Acceptance Criteria

1. WHEN Perplexity API returns HTTP 429 (rate limit) THEN the system SHALL implement exponential backoff
2. WHEN Perplexity API fails persistently THEN the system SHALL fallback to existing providers without degrading reporter flow
3. WHEN API requests timeout THEN the system SHALL handle gracefully and continue with available data
4. WHEN rate limits are hit THEN the system SHALL log warnings without exposing sensitive information

### Requirement 4

**User Story:** As a FinWiz developer, I want comprehensive observability so that I can monitor performance and troubleshoot issues effectively.

#### Acceptance Criteria

1. WHEN Sonar requests are made THEN the system SHALL log request latency, HTTP status, and result count
2. WHEN logging Sonar activity THEN the system SHALL redact content while preserving metadata
3. WHEN errors occur THEN the system SHALL emit appropriate warnings without exposing API keys
4. WHEN feature flag usage changes THEN the system SHALL track adoption metrics

### Requirement 5

**User Story:** As a FinWiz analyst, I want Sonar integration to improve research quality across all analysis types so that my reports contain fresher and more comprehensive information.

#### Acceptance Criteria

1. WHEN Sonar results are included THEN they SHALL increase freshness of financial articles for sentiment, technical, and fundamental analysis
2. WHEN Sonar provides citations THEN they SHALL be properly formatted in reporter HTML output
3. WHEN combining data sources THEN Sonar results SHALL enhance breadth of factual grounding for earnings analysis, regulatory updates, and market trends
4. WHEN generating reports THEN Sonar sources SHALL be cited following output formatting guidelines
5. WHEN performing technical analysis THEN Sonar SHALL provide recent analyst opinions and price target updates
6. WHEN analyzing fundamentals THEN Sonar SHALL surface recent earnings reports, SEC filings, and management commentary

### Requirement 6

**User Story:** As a FinWiz product owner, I want performance benchmarks so that I can evaluate the operational viability of Sonar integration.

#### Acceptance Criteria

1. WHEN measuring response times THEN average Sonar response time SHALL be ≤2× current provider baseline
2. WHEN handling rate limits THEN failure rate SHALL be <5%
3. WHEN projecting costs THEN daily spend SHALL remain under target budget
4. WHEN running benchmarks THEN system SHALL support manual comparison of flag on/off scenarios

### Requirement 7

**User Story:** As a FinWiz analyst crew, I want Perplexity integration available across multiple analysis tools so that I can leverage fresh research data for technical analysis, fundamental analysis, and market research beyond just sentiment.

#### Acceptance Criteria

1. WHEN performing technical analysis THEN Sonar SHALL provide recent analyst price targets and technical commentary
2. WHEN analyzing company fundamentals THEN Sonar SHALL surface recent earnings calls, SEC filings, and management guidance
3. WHEN researching market trends THEN Sonar SHALL provide sector analysis and macroeconomic insights
4. WHEN analyzing ETFs THEN Sonar SHALL provide fund performance updates and holdings changes
5. WHEN researching crypto assets THEN Sonar SHALL provide regulatory updates and adoption news

### Requirement 8

**User Story:** As a FinWiz maintainer, I want proper testing coverage so that I can ensure integration reliability and maintainability.

#### Acceptance Criteria

1. WHEN testing Sonar integration THEN unit tests SHALL mock HTTP responses for success, error, and timeout paths
2. WHEN running tests THEN they SHALL validate feature flag behavior in both enabled and disabled states
3. WHEN testing error handling THEN tests SHALL verify exponential backoff and fallback mechanisms
4. WHEN validating output THEN tests SHALL ensure Sonar results conform to existing schema contracts
# Requirements Document

## Introduction

The FinWiz platform currently generates generic portfolio reviews with placeholder
analysis for user holdings stored in `data/etf.csv` and `data/stock.csv`. The
current output in `output/portfolio/portfolio_review.json` contains only:

- Generic baseline scores (0.65 for ETFs, 0.6 for stocks)
- Placeholder risk factors ("Baseline placeholder")
- Generic rationale ("Ticker validated on Yahoo; baseline confidence")
- No specific buy/sell price targets
- No alternatives or improvement suggestions

Users need detailed, actionable analysis for each of their specific holdings
including:

- Deep fundamental analysis (for stocks and ETFs)
- Specific keep/sell/buy recommendations with price targets
- Alternative investment suggestions
- A+ grade improvement opportunities
- Risk-adjusted position sizing recommendations

This feature will enhance the portfolio review crew to provide comprehensive,
ticker-specific analysis that goes beyond validation to deliver actionable
investment intelligence for a portfolio of 28 ETFs and 37 stocks across multiple
exchanges (US, European, Swiss).

## Requirements

### Requirement 1: Individual Holding Deep Analysis

**User Story:** As an investor, I want detailed analysis of each holding in my
portfolio, so that I can make informed decisions about whether to keep, sell, or
add to each position.

#### Acceptance Criteria

1. WHEN a portfolio review is requested THEN the system SHALL analyze each
   validated ticker individually using the appropriate crew (stock/ETF/crypto)
2. WHEN analyzing a stock holding THEN the system SHALL retrieve and include
   SEC filing data, fundamental metrics, and competitive positioning
3. WHEN analyzing an ETF holding THEN the system SHALL include expense ratio
   analysis, tracking error, holdings composition, and benchmark comparison
4. WHEN analyzing a crypto holding THEN the system SHALL include technical
   analysis, volatility metrics, and market structure assessment
5. IF a holding has been analyzed by a crew THEN the system SHALL incorporate
   that crew's detailed output into the portfolio review
6. WHEN analysis is complete THEN the system SHALL replace generic "baseline"
   data with specific, ticker-relevant analysis

### Requirement 2: Actionable Buy/Sell Recommendations with Price Targets

**User Story:** As an investor, I want specific price targets for buying more or
selling my holdings, so that I can execute trades at optimal levels.

#### Acceptance Criteria

1. WHEN a holding receives a KEEP recommendation THEN the system SHALL provide:
   - Current price and fair value estimate
   - Buy-more price target (accumulation level)
   - Stop-loss or sell price target (risk management level)
   - Rationale for each price level
2. WHEN a holding receives a SELL recommendation THEN the system SHALL provide:
   - Target exit price range
   - Timeline for exit (immediate vs gradual)
   - Tax considerations if applicable
   - Specific reasons for the sell recommendation
3. WHEN a holding receives a BUY recommendation THEN the system SHALL provide:
   - Initial entry price target
   - Scale-in levels for dollar-cost averaging
   - Position sizing recommendation as % of portfolio
   - Risk/reward ratio at current levels
4. IF technical analysis is available THEN the system SHALL include
   support/resistance levels in price targets
5. WHEN price targets are provided THEN they SHALL be in the holding's native
   currency

### Requirement 3: Alternative Investment Suggestions

**User Story:** As an investor, I want to see better alternatives to my current
holdings, so that I can upgrade my portfolio quality over time.

#### Acceptance Criteria

1. WHEN a holding has a grade below B THEN the system SHALL suggest at least
   2-3 alternative investments
2. WHEN suggesting alternatives THEN the system SHALL match:
   - Similar asset class and risk profile
   - Similar or better expected returns
   - Lower fees (for ETFs)
   - Better fundamentals (for stocks)
   - Higher liquidity (for crypto)
3. WHEN alternatives are provided THEN each SHALL include:
   - Ticker symbol and name
   - Key advantage over current holding
   - Risk comparison
   - Transition strategy (swap timing and tax implications)
4. IF the current holding is in a tax-advantaged account THEN the system SHALL
   note tax-free swap opportunities
5. WHEN alternatives are A+ rated THEN they SHALL be clearly marked as premium
   opportunities

### Requirement 4: A+ Grade Improvement Path

**User Story:** As an investor, I want to understand how to improve my portfolio
to achieve more A+ rated holdings, so that I can systematically upgrade my
investment quality.

#### Acceptance Criteria

1. WHEN a portfolio contains holdings graded below A+ THEN the system SHALL
   provide an improvement roadmap
2. WHEN creating an improvement roadmap THEN the system SHALL:
   - Identify which holdings to exit first (prioritize D and F grades)
   - Suggest A+ replacements from the discovery crew output
   - Provide a phased transition plan (e.g., "Month 1-3: Exit X, Y; Month 4-6:
     Add A, B")
   - Calculate expected portfolio grade improvement
3. WHEN A+ opportunities exist THEN the system SHALL show:
   - Current portfolio A+ allocation percentage
   - Target A+ allocation percentage
   - Gap analysis and specific actions to close the gap
4. IF an A+ alternative exists for a current holding THEN it SHALL be
   highlighted in the holding's analysis
5. WHEN improvement suggestions are made THEN they SHALL respect the user's
   risk tolerance and investment constraints

### Requirement 5: Risk-Adjusted Position Sizing

**User Story:** As an investor, I want position sizing recommendations based on
each holding's risk profile, so that I can optimize my portfolio's risk/reward
balance.

#### Acceptance Criteria

1. WHEN analyzing each holding THEN the system SHALL calculate a recommended
   position size as % of total portfolio
2. WHEN calculating position size THEN the system SHALL consider:
   - Holding's risk score (0-10 scale)
   - Correlation with other portfolio holdings
   - User's overall risk tolerance
   - Concentration limits (e.g., max 10% in single stock)
3. WHEN current position size exceeds recommended size THEN the system SHALL
   flag it as "overweight" with trim recommendations
4. WHEN current position size is below recommended size THEN the system SHALL
   flag it as "underweight" with add recommendations
5. IF a holding is high-risk (score > 7) THEN the system SHALL recommend
   position size ≤ 3% of portfolio
6. WHEN position sizing recommendations are provided THEN they SHALL sum to
   100% across the entire portfolio

### Requirement 6: Data Freshness and Citation Requirements

**User Story:** As an investor, I want to know when the analysis data was last
updated and where it came from, so that I can trust the recommendations.

#### Acceptance Criteria

1. WHEN displaying analysis for any holding THEN the system SHALL include:
   - Data as-of date (timestamp)
   - Primary data sources with URLs
   - Freshness indicator (fresh < 7 days, stale > 30 days)
2. WHEN data is stale (> 30 days) THEN the system SHALL display a warning and
   reduce confidence scores by 20%
3. WHEN SEC filings are cited THEN the system SHALL include:
   - Filing type (10-K, 10-Q, 8-K)
   - Accession number
   - Filing date
   - Relevant excerpt or summary
4. WHEN market data is used THEN the system SHALL cite the specific API/source
   (Yahoo Finance, Alpha Vantage, etc.)
5. IF analysis cannot be completed due to missing data THEN the system SHALL
   clearly state what data is unavailable

### Requirement 7: Multi-Currency Support

**User Story:** As an international investor with holdings in multiple currencies,
I want analysis and price targets in each holding's native currency, so that I
can execute trades accurately.

#### Acceptance Criteria

1. WHEN a holding is denominated in a non-base currency THEN all price targets
   SHALL be in that currency
2. WHEN displaying portfolio-level metrics THEN they SHALL be converted to the
   user's base currency (CHF)
3. WHEN currency conversion is applied THEN the system SHALL:
   - Show the exchange rate used
   - Include the conversion timestamp
   - Note FX risk in the risk assessment
4. IF a holding trades on multiple exchanges THEN the system SHALL specify
   which exchange/listing is being analyzed
5. WHEN suggesting alternatives THEN the system SHALL prefer same-currency
   alternatives to minimize FX exposure

### Requirement 8: Integration with Existing Crews

**User Story:** As a system, I want to leverage existing crew analysis outputs,
so that portfolio reviews are comprehensive and avoid duplicate API calls.

#### Acceptance Criteria

1. WHEN a portfolio review is initiated THEN the system SHALL check if recent
   crew analysis exists for each ticker
2. IF crew analysis exists and is fresh (< 7 days) THEN the system SHALL reuse
   that analysis
3. IF crew analysis is missing or stale THEN the system SHALL trigger the
   appropriate crew (stock/ETF/crypto) to analyze the ticker
4. WHEN integrating crew outputs THEN the system SHALL map crew-specific fields
   to portfolio review schema:
   - Stock crew → fundamental_analysis, sec_citations, competitive_moat
   - ETF crew → expense_ratio, tracking_error, holdings_analysis
   - Crypto crew → technical_indicators, volatility_metrics, market_structure
5. WHEN all crew analyses are complete THEN the system SHALL consolidate them
   into a unified portfolio review output
6. IF a crew analysis fails THEN the system SHALL fall back to baseline
   analysis with a clear warning

### Requirement 9: French HTML Report Generation

**User Story:** As an investor, I want a professional French HTML report with
comprehensive portfolio analysis, so that I can review my holdings and make
informed decisions.

#### Acceptance Criteria

1. WHEN portfolio analysis is complete THEN the system SHALL generate a French
   HTML report at `output/portfolio/portfolio_review_fr.html`
2. WHEN generating HTML THEN the system SHALL use BeautifulSoup4 for proper
   HTML structure and validation
3. WHEN creating the report THEN it SHALL include:
   - Portfolio summary dashboard with grade distribution
   - Holdings analysis table (sortable/filterable)
   - Price targets section for each holding
   - Alternatives section for underperforming holdings
   - A+ improvement roadmap
   - Position sizing recommendations with visual charts
4. WHEN styling the report THEN it SHALL:
   - Use professional CSS with FinWiz branding
   - Be responsive and mobile-friendly
   - Include strategic emoji usage (📊 📈 📉 💰 ⚠️ ✅ ❌)
   - Use color-coded grades (green for A+/A, yellow for B/C, red for D/F)
   - Be print-friendly
5. WHEN displaying text THEN all content SHALL be in French with proper
   financial terminology
6. IF the report cannot be generated THEN the system SHALL log the error and
   fall back to JSON output only

## Success Criteria

- Portfolio reviews contain zero "baseline placeholder" entries for validated
  tickers
- Each holding has specific, actionable buy/sell price targets
- At least 80% of holdings below grade B have alternative suggestions
- Position sizing recommendations sum to 100% across portfolio
- All analysis includes data sources and freshness indicators
- User can execute trades directly from the recommendations without additional
  research
- French HTML report is generated successfully with professional formatting
- HTML is valid and well-formed (validated with BeautifulSoup4)
# Requirements Document

## Introduction

This specification defines a portfolio rebalancing system for the FinWiz financial analysis platform that provides intelligent buy/sell quantity recommendations based on target weightings, tolerance thresholds, and available capital. The system will help users maintain optimal portfolio allocations by suggesting specific actions to rebalance positions when they drift outside acceptable ranges.

The rebalancing engine will integrate with FinWiz's existing portfolio analysis capabilities while providing a new quantitative approach to portfolio management. Users will be able to define target allocations, set tolerance bands, and receive actionable recommendations for maintaining their desired portfolio structure.

## Requirements

### Requirement 1: Target Weighting Configuration

**User Story:** As a portfolio manager, I want to define target percentage weightings for each position in my portfolio, so that I can maintain my desired asset allocation strategy.

#### Acceptance Criteria

1. WHEN configuring portfolio targets THEN the system SHALL allow users to set target percentage weightings for each stock position
2. WHEN target weightings are entered THEN the system SHALL validate that all percentages sum to 100% or less (allowing for cash positions)
3. WHEN saving target allocations THEN the system SHALL persist the configuration for future rebalancing calculations
4. WHEN target weightings are modified THEN the system SHALL recalculate all rebalancing recommendations automatically
5. IF target weightings exceed 100% THEN the system SHALL display an error message and prevent saving until corrected

### Requirement 2: Tolerance Threshold Management

**User Story:** As an investor, I want to set tolerance bands around my target weightings, so that I only receive rebalancing recommendations when positions drift significantly from their targets.

#### Acceptance Criteria

1. WHEN setting tolerance thresholds THEN the system SHALL allow percentage-based tolerance bands (e.g., ±2%, ±5%) for each position
2. WHEN tolerance is configured THEN the system SHALL support both uniform tolerance (same for all positions) and individual position tolerances
3. WHEN calculating drift THEN the system SHALL compare current weightings against target weightings using the specified tolerance bands
4. WHEN positions are within tolerance THEN the system SHALL indicate "No Action Required" for those positions
5. IF tolerance values are negative or exceed 50% THEN the system SHALL validate inputs and provide appropriate error messages

### Requirement 3: Current Portfolio Analysis

**User Story:** As a portfolio analyst, I want the system to calculate current position weightings from my portfolio holdings, so that I can see how my actual allocations compare to my targets.

#### Acceptance Criteria

1. WHEN analyzing current portfolio THEN the system SHALL calculate current market values for each position using real-time or recent price data
2. WHEN computing weightings THEN the system SHALL calculate each position's percentage of total portfolio value
3. WHEN displaying current allocations THEN the system SHALL show both dollar amounts and percentage weightings for each position
4. WHEN portfolio values change THEN the system SHALL update weightings automatically based on current market prices
5. IF price data is unavailable THEN the system SHALL use the most recent available price and indicate the data age

### Requirement 4: Rebalancing Recommendations Engine

**User Story:** As an investor, I want specific buy/sell quantity recommendations for each position, so that I can execute trades to bring my portfolio back into alignment with my target allocations.

#### Acceptance Criteria

1. WHEN positions are outside tolerance bands THEN the system SHALL calculate exact share quantities needed to rebalance to target weightings
2. WHEN recommending purchases THEN the system SHALL suggest the number of shares to buy for under-weighted positions
3. WHEN recommending sales THEN the system SHALL suggest the number of shares to sell for over-weighted positions
4. WHEN calculating quantities THEN the system SHALL account for current share prices and round to whole shares
5. IF fractional shares are supported THEN the system SHALL provide precise fractional quantities with appropriate notation

### Requirement 5: Available Capital Integration

**User Story:** As an investor with limited capital, I want to specify how much money I have available to invest or need to withdraw, so that rebalancing recommendations fit within my financial constraints.

#### Acceptance Criteria

1. WHEN specifying available capital THEN the system SHALL accept positive amounts for new investments and negative amounts for withdrawals
2. WHEN capital is limited THEN the system SHALL prioritize rebalancing recommendations based on the largest deviations from target weightings
3. WHEN insufficient capital exists THEN the system SHALL provide partial rebalancing recommendations that maximize improvement within budget constraints
4. WHEN excess capital remains THEN the system SHALL suggest how to allocate remaining funds across under-weighted positions
5. IF capital requirements exceed available funds THEN the system SHALL indicate the shortfall and suggest alternative approaches

### Requirement 6: Optimization Algorithm

**User Story:** As a quantitative analyst, I want the rebalancing algorithm to optimize trade recommendations across all positions, so that I achieve the best possible portfolio alignment with minimal trading activity.

#### Acceptance Criteria

1. WHEN optimizing trades THEN the system SHALL minimize the number of transactions required to achieve target allocations
2. WHEN multiple positions need adjustment THEN the system SHALL coordinate buy/sell recommendations to use proceeds from sales to fund purchases
3. WHEN calculating optimal trades THEN the system SHALL consider transaction costs and suggest cost-effective rebalancing approaches
4. WHEN positions have different priorities THEN the system SHALL allow users to specify which positions are most important to rebalance first
5. IF perfect rebalancing is impossible THEN the system SHALL provide the closest achievable allocation and explain remaining deviations

### Requirement 7: Rebalancing Report Generation

**User Story:** As a portfolio manager, I want a comprehensive rebalancing report showing current vs. target allocations and recommended actions, so that I can review and execute the suggested trades.

#### Acceptance Criteria

1. WHEN generating rebalancing reports THEN the system SHALL display current weightings, target weightings, and deviations for each position
2. WHEN showing recommendations THEN the system SHALL provide clear buy/sell instructions with specific share quantities and estimated costs
3. WHEN calculating impact THEN the system SHALL show projected portfolio weightings after executing all recommended trades
4. WHEN presenting results THEN the system SHALL highlight positions requiring immediate attention and those within acceptable ranges
5. IF no rebalancing is needed THEN the system SHALL confirm that all positions are within tolerance and no action is required

### Requirement 8: Transaction Cost Analysis

**User Story:** As a cost-conscious investor, I want to understand the transaction costs associated with rebalancing recommendations, so that I can make informed decisions about when and how to rebalance.

#### Acceptance Criteria

1. WHEN calculating trade costs THEN the system SHALL estimate brokerage commissions, bid-ask spreads, and market impact for each recommended trade
2. WHEN showing recommendations THEN the system SHALL display estimated total transaction costs for the complete rebalancing
3. WHEN costs are high THEN the system SHALL suggest alternative approaches such as using new contributions to rebalance gradually
4. WHEN comparing options THEN the system SHALL show cost-benefit analysis of immediate rebalancing vs. gradual adjustment over time
5. IF transaction costs exceed benefits THEN the system SHALL recommend delaying rebalancing until deviations become larger

### Requirement 9: Historical Tracking and Analytics

**User Story:** As a portfolio analyst, I want to track rebalancing history and analyze the effectiveness of my allocation strategy, so that I can improve my portfolio management approach over time.

#### Acceptance Criteria

1. WHEN rebalancing is executed THEN the system SHALL record the date, positions adjusted, and quantities traded
2. WHEN analyzing performance THEN the system SHALL track how often each position requires rebalancing and the typical deviation amounts
3. WHEN reviewing history THEN the system SHALL show the impact of rebalancing on portfolio performance and risk metrics
4. WHEN evaluating strategy THEN the system SHALL provide analytics on whether current tolerance bands are appropriate
5. IF patterns emerge THEN the system SHALL suggest adjustments to target weightings or tolerance thresholds based on historical data

### Requirement 10: Integration with Existing FinWiz Architecture

**User Story:** As a FinWiz user, I want portfolio rebalancing to integrate seamlessly with existing portfolio analysis features, so that I can use rebalancing as part of my comprehensive investment workflow.

#### Acceptance Criteria

1. WHEN accessing rebalancing features THEN the system SHALL integrate with existing portfolio data structures and schemas
2. WHEN generating reports THEN the system SHALL maintain consistency with FinWiz HTML report formatting and styling
3. WHEN validating inputs THEN the system SHALL use existing Pydantic validation framework and error handling patterns
4. WHEN calculating market values THEN the system SHALL leverage existing price data APIs and caching infrastructure
5. IF rebalancing features are disabled THEN the system SHALL continue operating with existing portfolio functionality unaffected

### Requirement 11: Risk Management and Safeguards

**User Story:** As a risk-conscious investor, I want built-in safeguards to prevent excessive trading or dangerous portfolio concentrations, so that rebalancing recommendations support prudent risk management.

#### Acceptance Criteria

1. WHEN recommending large trades THEN the system SHALL warn users about positions that would exceed reasonable concentration limits (e.g., >20% in single stock)
2. WHEN calculating rebalancing THEN the system SHALL prevent recommendations that would create excessive turnover or trading activity
3. WHEN market volatility is high THEN the system SHALL suggest wider tolerance bands or delayed rebalancing to avoid whipsaw trading
4. WHEN positions have significant unrealized gains THEN the system SHALL consider tax implications and suggest tax-efficient rebalancing strategies
5. IF rebalancing would trigger significant tax events THEN the system SHALL highlight tax consequences and suggest alternatives

### Requirement 12: User Interface and Experience

**User Story:** As a portfolio manager, I want an intuitive interface for configuring targets and reviewing recommendations, so that I can efficiently manage my portfolio rebalancing process.

#### Acceptance Criteria

1. WHEN configuring portfolio targets THEN the system SHALL provide an easy-to-use interface for setting target weightings and tolerance bands
2. WHEN viewing recommendations THEN the system SHALL present information in a clear, actionable format with visual indicators for urgency
3. WHEN reviewing changes THEN the system SHALL show before/after portfolio compositions with clear highlighting of adjustments
4. WHEN exporting recommendations THEN the system SHALL support formats suitable for broker platforms or trading systems
5. IF errors occur THEN the system SHALL provide clear error messages with specific guidance on how to resolve issues
# Requirements Document

## Introduction

This specification defines a comprehensive quantitative analysis and backtesting framework for the FinWiz financial analysis platform. The framework will integrate professional-grade Python libraries including TA-Lib, Backtrade and  QuantLib to provide institutional-quality backtesting capabilities, portfolio optimization, and risk analysis.

The quantitative framework will enable users to backtest trading strategies, optimize portfolios, analyze performance metrics, and conduct advanced derivatives pricing analysis. This enhancement transforms FinWiz from a research-focused platform into a complete quantitative analysis suite suitable for both retail and institutional users.

## Requirements

### Requirement 1: Historical Data Management & Quality Assurance

**User Story:** As a quantitative analyst, I want reliable historical market data with quality validation, so that my backtesting results are based on accurate and complete datasets.

#### Acceptance Criteria

1. WHEN a user specifies a stock symbol and date range THEN the system SHALL download historical OHLCV data using yfinance with fallback to Alpha Vantage
2. WHEN historical data is retrieved THEN the system SHALL validate data completeness, checking for missing dates and price anomalies
3. WHEN data quality issues are detected THEN the system SHALL log warnings and attempt to fill gaps using interpolation or alternative sources
4. WHEN multiple data sources are available THEN the system SHALL cross-validate prices and flag significant discrepancies
5. IF data cannot be retrieved or validated THEN the system SHALL provide clear error messages with suggested alternatives

### Requirement 2: Technical Analysis Integration with TA-Lib

**User Story:** As a technical analyst, I want access to professional-grade technical indicators, so that I can build sophisticated trading strategies based on proven technical analysis methods.

#### Acceptance Criteria

1. WHEN calculating technical indicators THEN the system SHALL use TA-Lib for SMA, EMA, RSI, MACD, Bollinger Bands, and Stochastic oscillators
2. WHEN indicators are computed THEN the system SHALL handle edge cases like insufficient data periods and provide appropriate warnings
3. WHEN multiple indicators are requested THEN the system SHALL calculate them efficiently in batch operations
4. WHEN custom indicator parameters are specified THEN the system SHALL validate parameter ranges and provide sensible defaults
5. IF TA-Lib is not available THEN the system SHALL fall back to native Python implementations with performance warnings

### Requirement 3: Strategy Backtesting with Backtrader Framework

**User Story:** As a strategy developer, I want to backtest trading strategies using a professional framework, so that I can evaluate strategy performance with realistic trading conditions and costs.

#### Acceptance Criteria

1. WHEN backtesting is initiated THEN the system SHALL use Backtrader framework for strategy execution simulation
2. WHEN trades are executed THEN the system SHALL account for realistic transaction costs, slippage, and market impact
3. WHEN strategies generate signals THEN the system SHALL support multiple order types (market, limit, stop-loss, take-profit)
4. WHEN backtesting completes THEN the system SHALL provide detailed trade logs with entry/exit points and P&L calculations
5. IF strategy parameters are invalid THEN the system SHALL validate inputs and provide clear error messages with correction guidance

### Requirement 4: Performance Analysis with Pyfolio Integration

**User Story:** As a portfolio manager, I want comprehensive performance analysis and risk metrics, so that I can evaluate strategy effectiveness using industry-standard measures.

#### Acceptance Criteria

1. WHEN backtesting completes THEN the system SHALL generate Pyfolio tear sheets with returns analysis, risk metrics, and drawdown analysis
2. WHEN performance is analyzed THEN the system SHALL calculate Sharpe ratio, Sortino ratio, maximum drawdown, and Value at Risk (VaR)
3. WHEN benchmark comparison is requested THEN the system SHALL compare strategy performance against relevant market indices
4. WHEN risk analysis is performed THEN the system SHALL provide rolling volatility, beta analysis, and correlation metrics
5. IF insufficient data exists for analysis THEN the system SHALL indicate which metrics cannot be calculated and why

### Requirement 5: Portfolio Optimization with PyPortfolioOpt

**User Story:** As an investment manager, I want to optimize portfolio allocations using modern portfolio theory, so that I can construct efficient portfolios that maximize returns for given risk levels.

#### Acceptance Criteria

1. WHEN portfolio optimization is requested THEN the system SHALL use PyPortfolioOpt for efficient frontier calculations
2. WHEN optimizing allocations THEN the system SHALL support mean-variance optimization, Black-Litterman model, and risk parity approaches
3. WHEN constraints are specified THEN the system SHALL enforce position limits, sector constraints, and turnover restrictions
4. WHEN optimization completes THEN the system SHALL provide expected returns, volatility, and Sharpe ratio for optimal portfolios
5. IF optimization fails to converge THEN the system SHALL provide diagnostic information and suggest parameter adjustments

### Requirement 6: Advanced Derivatives Pricing with QuantLib

**User Story:** As a derivatives trader, I want to price complex financial instruments, so that I can evaluate options, bonds, and structured products with professional-grade models.

#### Acceptance Criteria

1. WHEN pricing options THEN the system SHALL use QuantLib for Black-Scholes, binomial, and Monte Carlo pricing models
2. WHEN analyzing bonds THEN the system SHALL calculate yield curves, duration, and convexity using QuantLib fixed-income tools
3. WHEN volatility surfaces are needed THEN the system SHALL construct and calibrate volatility models for options pricing
4. WHEN exotic derivatives are priced THEN the system SHALL support barrier options, Asian options, and other path-dependent instruments
5. IF market data is insufficient THEN the system SHALL indicate which pricing models cannot be used and suggest alternatives

### Requirement 7: Strategy Development Framework

**User Story:** As a quantitative researcher, I want a flexible framework for developing and testing custom trading strategies, so that I can rapidly prototype and evaluate new investment ideas.

#### Acceptance Criteria

1. WHEN creating strategies THEN the system SHALL provide base strategy classes with common functionality (signal generation, position sizing, risk management)
2. WHEN strategies are defined THEN the system SHALL support multiple asset classes (stocks, ETFs, cryptocurrencies, bonds)
3. WHEN backtesting strategies THEN the system SHALL enable parameter optimization using grid search and genetic algorithms
4. WHEN strategies are compared THEN the system SHALL provide side-by-side performance comparisons with statistical significance tests
5. IF strategy logic is invalid THEN the system SHALL validate strategy code and provide debugging assistance

### Requirement 8: Risk Management & Position Sizing

**User Story:** As a risk manager, I want sophisticated risk controls and position sizing algorithms, so that I can ensure strategies operate within acceptable risk parameters.

#### Acceptance Criteria

1. WHEN positions are sized THEN the system SHALL support Kelly criterion, fixed fractional, and volatility-based position sizing
2. WHEN risk limits are set THEN the system SHALL enforce maximum position sizes, sector exposure limits, and correlation constraints
3. WHEN drawdowns occur THEN the system SHALL implement dynamic position sizing adjustments and stop-loss mechanisms
4. WHEN portfolio risk is analyzed THEN the system SHALL calculate portfolio VaR, expected shortfall, and stress test scenarios
5. IF risk limits are breached THEN the system SHALL generate alerts and suggest position adjustments

### Requirement 9: Multi-Asset Class Support

**User Story:** As a multi-asset portfolio manager, I want to backtest strategies across different asset classes, so that I can build diversified portfolios and cross-asset strategies.

#### Acceptance Criteria

1. WHEN backtesting multi-asset strategies THEN the system SHALL support stocks, ETFs, bonds, commodities, and cryptocurrencies
2. WHEN calculating correlations THEN the system SHALL handle different trading schedules and time zones for global assets
3. WHEN rebalancing portfolios THEN the system SHALL account for different liquidity profiles and transaction costs across asset classes
4. WHEN analyzing performance THEN the system SHALL provide asset class attribution and contribution analysis
5. IF data is unavailable for certain assets THEN the system SHALL continue analysis with available assets and note limitations

### Requirement 10: Performance Optimization & Caching

**User Story:** As a quantitative analyst running large backtests, I want fast execution and intelligent caching, so that I can iterate quickly on strategy development without waiting for redundant calculations.

#### Acceptance Criteria

1. WHEN running backtests THEN the system SHALL cache historical data, indicator calculations, and intermediate results
2. WHEN parameters change slightly THEN the system SHALL reuse cached calculations where possible to minimize computation time
3. WHEN multiple strategies are tested THEN the system SHALL parallelize backtests across available CPU cores
4. WHEN large datasets are processed THEN the system SHALL use memory-efficient data structures and streaming calculations
5. IF memory limits are reached THEN the system SHALL implement data chunking and provide progress indicators

### Requirement 11: Reporting & Visualization

**User Story:** As a strategy analyst, I want comprehensive visual reports and interactive charts, so that I can communicate strategy performance and insights effectively to stakeholders.

#### Acceptance Criteria

1. WHEN generating reports THEN the system SHALL create HTML reports with interactive charts using Plotly or similar libraries
2. WHEN visualizing performance THEN the system SHALL include equity curves, drawdown charts, rolling metrics, and return distributions
3. WHEN comparing strategies THEN the system SHALL provide side-by-side visualizations with statistical comparison tables
4. WHEN exporting results THEN the system SHALL support PDF export, CSV data export, and JSON format for further analysis
5. IF visualization libraries are unavailable THEN the system SHALL fall back to static charts with reduced interactivity

### Requirement 12: Stock Screening & Fundamental Analysis

**User Story:** As a fundamental analyst, I want to screen stocks based on financial metrics and growth indicators, so that I can identify high-potential investment opportunities using quantitative criteria.

#### Acceptance Criteria

1. WHEN screening stocks THEN the system SHALL integrate with Yahoo Finance Stock Screener API to filter thousands of stocks by financial criteria
2. WHEN applying valuation filters THEN the system SHALL support P/S ratio (Price-to-Sales), P/E ratio (Price-to-Earnings), and PEG ratio (Price/Earnings to Growth) screening
3. WHEN filtering by growth metrics THEN the system SHALL screen for EPS growth (Earnings Per Share Growth) and revenue growth over quarterly and annual periods
4. WHEN combining criteria THEN the system SHALL allow multiple filter combinations (e.g., PEG < 1 AND revenue growth > 15% AND P/E < 25)
5. WHEN screening results are generated THEN the system SHALL rank stocks by composite scores and provide detailed fundamental metrics for each candidate
6. IF screening data is unavailable THEN the system SHALL fall back to alternative data sources and indicate data limitations

### Requirement 13: Advanced Fundamental Metrics Integration

**User Story:** As a value investor, I want access to comprehensive fundamental metrics and ratios, so that I can perform deep fundamental analysis alongside quantitative backtesting.

#### Acceptance Criteria

1. WHEN analyzing fundamentals THEN the system SHALL calculate and display debt-to-equity ratios, return on equity (ROE), and return on assets (ROA)
2. WHEN evaluating profitability THEN the system SHALL provide gross margin, operating margin, and net profit margin trends over multiple periods
3. WHEN assessing financial health THEN the system SHALL calculate current ratio, quick ratio, and interest coverage ratios
4. WHEN comparing companies THEN the system SHALL provide sector-relative metrics and percentile rankings within industry groups
5. IF fundamental data is incomplete THEN the system SHALL indicate missing metrics and suggest alternative analysis approaches

### Requirement 14: Integration with Existing FinWiz Architecture

**User Story:** As a FinWiz user, I want quantitative analysis to integrate seamlessly with existing research capabilities, so that I can combine fundamental analysis with quantitative backtesting in unified workflows.

#### Acceptance Criteria

1. WHEN running quantitative analysis THEN the system SHALL integrate with existing FinWiz crews for fundamental and sentiment analysis
2. WHEN strategies use multiple data sources THEN the system SHALL leverage existing API integrations and caching infrastructure
3. WHEN generating reports THEN the system SHALL maintain consistency with existing FinWiz HTML report formatting and styling
4. WHEN validating inputs THEN the system SHALL use existing Pydantic validation framework and error handling patterns
5. IF quantitative features are disabled THEN the system SHALL continue operating with existing functionality unaffected
# Requirements Document

## Introduction

This specification addresses the need for immediate, high-impact improvements to the FinWiz codebase that enhance code quality, maintainability, and CrewAI compliance. The Quick Wins Implementation focuses on five key areas: tool factory standardization, final reporter enforcement, async task decorators, type hint coverage, and standardized logging. These improvements are designed to be implemented quickly (2-3 days) while providing significant benefits to code consistency, developer experience, and system reliability.

The implementation follows FinWiz's core principles of modular architecture, strict validation, and CrewAI best practices. Each quick win is independent and can be implemented incrementally, allowing for continuous testing and validation.

## Requirements

### Requirement 1: Tool Factory Standardization

**User Story:** As a developer maintaining FinWiz crews, I want a standardized way to initialize tools across all crews, so that tool configuration is consistent, centralized, and easier to maintain.

#### Acceptance Criteria

1. WHEN a tool factory module is created THEN it SHALL provide factory functions for stock, crypto, and ETF crew tools
2. WHEN a factory function is called THEN it SHALL return a list of BaseTool instances configured for the specific crew type
3. WHEN factory functions are implemented THEN they SHALL accept optional parameters for RAG tools, quantitative tools, and collection suffixes
4. IF a crew needs tools THEN it SHALL use the appropriate factory function instead of manual tool initialization
5. WHEN tools are initialized via factory THEN they SHALL include core research tools, optional quantitative tools, optional RAG tools, and schema/contract tools
6. WHEN the tool factory is implemented THEN all existing crews (stock, crypto, ETF) SHALL be updated to use factory functions
7. WHEN factory functions are used THEN the system SHALL maintain backward compatibility with existing crew functionality
8. WHEN changes are complete THEN unit tests SHALL verify that crews receive correct tool sets

### Requirement 2: Final Reporter Enforcement

**User Story:** As a FinWiz architect, I want to enforce that final reporter agents never receive tools, so that the system maintains proper separation of concerns and prevents accidental violations of design principles.

#### Acceptance Criteria

1. WHEN a final reporter decorator is created THEN it SHALL validate that agents have no tools at initialization time
2. IF a final reporter agent is created with tools THEN the system SHALL raise a FinalReporterError with a clear message
3. WHEN a final reporter agent is created without tools THEN the decorator SHALL allow creation and log validation success
4. WHEN the decorator is implemented THEN it SHALL be applied to all final reporter agents (investment_reporter, translator)
5. WHEN the decorator is applied THEN it SHALL use functools.wraps to preserve function metadata
6. WHEN validation fails THEN the error message SHALL include the agent role and number of tools found
7. WHEN the enforcement is complete THEN unit tests SHALL verify both success and failure cases
8. WHEN tests run THEN they SHALL confirm that reporters with no tools pass and reporters with tools fail

### Requirement 3: Async Task Decorators

**User Story:** As a developer working with CrewAI tasks, I want explicit decorators to mark tasks as async or sync, so that execution patterns are consistent and final tasks are correctly configured as synchronous.

#### Acceptance Criteria

1. WHEN task decorator module is created THEN it SHALL provide both async_task and sync_task decorators
2. WHEN async_task decorator is applied THEN it SHALL set task.async_execution to True
3. WHEN sync_task decorator is applied THEN it SHALL set task.async_execution to False
4. WHEN decorators are applied THEN they SHALL log the configuration for debugging purposes
5. WHEN decorators are implemented THEN they SHALL be applied to all tasks across all crews (stock, crypto, ETF, report)
6. WHEN tasks are decorated THEN parallel tasks SHALL use async_task and final tasks SHALL use sync_task
7. WHEN decorators are used THEN they SHALL preserve function metadata using functools.wraps
8. WHEN implementation is complete THEN unit tests SHALL verify that decorators correctly set async_execution property

### Requirement 4: Type Hint Coverage

**User Story:** As a developer maintaining FinWiz code, I want comprehensive type hints on all public functions, so that I get better IDE support, catch errors early, and have self-documenting code.

#### Acceptance Criteria

1. WHEN mypy is configured THEN it SHALL enforce type hints on all public functions
2. WHEN mypy configuration is created THEN it SHALL set python_version to 3.10 and enable strict checking
3. WHEN mypy runs THEN it SHALL ignore missing imports for third-party libraries (crewai, crewai_tools, dotenv)
4. WHEN type hints are added THEN they SHALL use modern Python 3.10+ syntax (str | None instead of Optional[str])
5. WHEN functions are updated THEN return types SHALL be explicitly specified for all public functions
6. WHEN type hints are added THEN they SHALL include parameter types and return types
7. WHEN implementation is complete THEN mypy SHALL run without errors on updated modules
8. WHEN type hints are added THEN they SHALL improve IDE autocomplete and error detection

### Requirement 5: Standardized Logging

**User Story:** As a developer debugging FinWiz crews, I want consistent structured logging across all crews, so that I can easily track execution flow, measure performance, and diagnose issues.

#### Acceptance Criteria

1. WHEN logging helper module is created THEN it SHALL provide a CrewLogger class for standardized logging
2. WHEN CrewLogger is initialized THEN it SHALL accept a crew_name parameter and create a logger instance
3. WHEN log_start is called THEN it SHALL log crew execution start with crew name, input keys, and event type
4. WHEN log_complete is called THEN it SHALL log execution completion with duration in seconds
5. WHEN log_error is called THEN it SHALL log errors with crew name, error type, and full exception info
6. WHEN CrewLogger is implemented THEN all crews SHALL be updated to use it in their kickoff methods
7. WHEN crews use CrewLogger THEN they SHALL track execution time and log start, complete, or error events
8. WHEN logging is standardized THEN log entries SHALL include structured extra fields for parsing and analysis

## Success Criteria

The Quick Wins Implementation will be considered successful when:

1. All five quick wins are implemented and tested
2. Code consistency improves from 60% to 90%
3. Type coverage improves from 40% to 80%
4. All unit tests pass without regression
5. CrewAI compliance improves from 85% to 95%
6. Developer experience is enhanced through better tooling and consistency
7. Documentation is updated to reflect new patterns
8. The codebase is ready for larger refactoring efforts in subsequent phases
# Requirements Document

## Introduction

Critical regressions have been introduced after completing the core-analysis-restoration spec. Despite all tasks being marked complete, the system is producing severely degraded output with data corruption, missing information, and incorrect grades. 

**USER REQUIREMENT**: All data produced by the different crews must be consolidated in a proper report instead of producing hallucinations after costly operations. The system is currently running expensive AI analysis (crews generating detailed risk assessments, grades, and recommendations) but then ignoring this data and showing generic fallback values instead.

This specification addresses the urgent need to diagnose and fix these regressions to restore system functionality and ensure that expensive crew analysis is actually used in the final output.

## Glossary

- **Grade Corruption**: A+ quality tickers being incorrectly labeled as Grade D
- **URL Forgery**: Real SEC filing URLs being replaced with placeholder example.com URLs
- **Data Availability Report**: Section of report showing which data sources are available/missing
- **Alternative Recommendations**: Suggested replacement investments for underperforming holdings
- **Flow State**: CrewAI Flow's structured state containing all analysis results
- **Report Crew**: Final crew that consolidates all analysis into HTML report
- **Discovery Results**: A+ investment opportunities found by screening crews

## Requirements

### Requirement 1: Grade Corruption Diagnosis and Fix - USE ACTUAL CREW DATA

**User Story:** As a financial analyst, I need portfolio holdings to display their correct grades (A+, A, B, etc.) from the actual crew analysis instead of all showing fallback Grade D, so that I can make informed investment decisions based on the expensive AI analysis that was actually performed.

**CONTEXT**: The system is running costly crew analysis that generates proper grades and risk assessments (confirmed in output files), but then ignoring this data and showing generic Grade D fallback values. This is wasting computational resources and providing incorrect information to users.

#### Acceptance Criteria

1. WHEN portfolio holdings are analyzed THEN they SHALL display their actual computed grades (A+, A, B, C, D, F)
2. WHEN A+ quality holdings exist THEN they SHALL be labeled as Grade A+ not Grade D
3. WHEN grades are computed THEN the computation logic SHALL be verified to produce correct results
4. WHEN grades are passed through the data flow THEN they SHALL not be corrupted or overwritten with default values
5. WHEN the report displays grades THEN it SHALL show the grades from the actual analysis, not fallback values
6. IF grade computation fails THEN the system SHALL log detailed error information and use appropriate fallback logic
7. WHEN debugging grade issues THEN the system SHALL trace grade values through the entire data flow pipeline

### Requirement 2: URL Forgery Diagnosis and Fix - AUDIT TRAIL REQUIREMENT

**User Story:** As an auditor, I need real SEC filing URLs and data source citations in reports, not placeholder example.com URLs, so that I can fact-check the report by verifying data accuracy against original sources.

**AUDIT REQUIREMENT**: Every data point in the report must be traceable to its source through valid URLs. This is essential for compliance, due diligence, and verifying that AI analysis is based on real data, not hallucinations.

#### Acceptance Criteria

1. WHEN SEC filings are referenced THEN they SHALL include real SEC EDGAR URLs not example.com placeholders
2. WHEN data sources are cited THEN they SHALL include actual URLs to the data sources for audit verification
3. WHEN URL generation fails THEN the system SHALL log errors and omit the URL rather than forge a fake one
4. WHEN the report is generated THEN it SHALL only include URLs that have been successfully retrieved from tools
5. IF a URL is unavailable THEN the report SHALL indicate "URL not available" rather than showing example.com
6. WHEN debugging URL issues THEN the system SHALL trace URL values from tool output through to report generation
7. WHEN tools return URLs THEN those URLs SHALL be preserved through all data transformations
8. WHEN an auditor clicks a URL THEN it SHALL lead to the actual source document, not a placeholder or error page
9. WHEN data is cited THEN the citation SHALL include: source name, URL, and as-of date for full traceability
10. WHEN the system cannot obtain a valid URL THEN it SHALL NOT include that data point in the report (fail-safe for audit trail)

### Requirement 3: Missing Alternatives Diagnosis and Fix

**User Story:** As a portfolio manager, I need alternative investment recommendations for underperforming holdings, not "aucune alternative fournie" messages, so that I can make informed rebalancing decisions.

#### Acceptance Criteria

1. WHEN holdings are graded below B THEN the system SHALL provide alternative investment recommendations
2. WHEN alternatives are computed THEN they SHALL be included in the portfolio review data structure
3. WHEN alternatives are passed to the report THEN they SHALL be preserved and displayed correctly
4. WHEN no suitable alternatives exist THEN the system SHALL explicitly state "No suitable alternatives found" with reasoning
5. IF alternative finding fails THEN the system SHALL log detailed error information
6. WHEN the report displays holdings THEN it SHALL show alternatives for each underperforming holding
7. WHEN debugging alternative issues THEN the system SHALL trace alternative data through the entire pipeline

### Requirement 4: Data Availability Report Fix

**User Story:** As a system operator, I need the data availability report to accurately reflect which data sources are available, not show "NOT PROVIDED" for all fields, so that I can understand system health and data quality.

#### Acceptance Criteria

1. WHEN the report is generated THEN it SHALL include a complete data availability summary
2. WHEN data sources are queried THEN their availability status SHALL be tracked and reported
3. WHEN the data availability summary is constructed THEN it SHALL include counts of available/unavailable/stale sources
4. WHEN freshness warnings exist THEN they SHALL be included in the data availability report
5. WHEN discovery is not run THEN the report SHALL clearly state "Discovery not run - use --discovery flag"
6. WHEN discovery IS run THEN the report SHALL show actual discovery results and backtesting status
7. WHEN the report crew receives inputs THEN it SHALL have access to data_availability_summary and data_availability_summary_formatted

### Requirement 5: Root Cause Analysis - DATA CREATION vs CONSUMPTION GAP

**User Story:** As a developer, I need to understand exactly where and why these regressions were introduced, so that I can fix them properly and prevent similar issues in the future.

**CRITICAL FINDING**: Analysis crews ARE creating rich, detailed data with proper grades and risk assessments (confirmed in output/stock/stock_output_*.json files), but this data is NOT being consumed by the portfolio review. The portfolio review shows all holdings with fallback Grade D (composite_score 0.6) and generic "Validation rapide" messages, indicating the deep analysis results are not being merged.

#### Acceptance Criteria

1. WHEN analyzing the regression THEN the system SHALL confirm that crews ARE generating proper data (verified: stock_output shows detailed risk assessments with proper grades)
2. WHEN tracing data flow THEN the system SHALL identify where the disconnect occurs between data creation (crews) and data consumption (portfolio review)
3. WHEN examining the deep analysis merge THEN the system SHALL verify why cached deep analysis is not being applied to portfolio holdings
4. WHEN reviewing the portfolio_holdings_processor THEN the system SHALL identify why it's using fallback grades instead of deep analysis grades
5. WHEN examining the analyze_and_update_portfolio flow THEN the system SHALL verify the deep analysis results are being passed correctly
6. WHEN checking the merge logic THEN the system SHALL identify why "Deep analysis merge complete: 5 holdings with deep analysis" doesn't actually merge the grades
7. WHEN analyzing the issue THEN the system SHALL document that this is a DATA CONSUMPTION bug, not a data generation bug

### Requirement 6: Data Flow Integrity Verification

**User Story:** As a system architect, I need to verify that data flows correctly from crews through Flow state to the report, without corruption or loss, so that the system produces accurate outputs.

#### Acceptance Criteria

1. WHEN crews execute THEN their outputs SHALL be stored with complete and accurate data
2. WHEN Flow state is updated THEN all required fields SHALL be populated with actual data not defaults
3. WHEN data is passed between Flow methods THEN it SHALL be preserved without corruption
4. WHEN the report crew receives inputs THEN it SHALL have access to ALL required data from upstream
5. WHEN data transformations occur THEN they SHALL preserve data integrity and not introduce defaults
6. IF data is missing at any stage THEN the system SHALL log detailed diagnostic information
7. WHEN debugging data flow THEN the system SHALL provide tools to trace data through the entire pipeline

### Requirement 7: Test Coverage for Regressions

**User Story:** As a developer, I need comprehensive tests that would have caught these regressions, so that similar issues don't occur in the future.

#### Acceptance Criteria

1. WHEN tests are written THEN they SHALL verify correct grade assignment and preservation
2. WHEN tests are written THEN they SHALL verify real URLs are included not placeholders
3. WHEN tests are written THEN they SHALL verify alternatives are provided for underperforming holdings
4. WHEN tests are written THEN they SHALL verify data availability reports are complete
5. WHEN tests are written THEN they SHALL verify end-to-end data flow from crews to report
6. IF any regression test fails THEN it SHALL provide clear diagnostic information
7. WHEN tests run THEN they SHALL catch data corruption, missing data, and incorrect defaults

### Requirement 8: Emergency Rollback Plan

**User Story:** As a system operator, I need the ability to quickly rollback to a working state if the fix introduces new issues, so that users can continue using the system.

#### Acceptance Criteria

1. WHEN a rollback is needed THEN the system SHALL have a documented rollback procedure
2. WHEN rolling back THEN the system SHALL restore to the last known good state
3. WHEN rollback is complete THEN all functionality SHALL work as it did before the regression
4. IF rollback is not possible THEN the system SHALL have a hotfix procedure
5. WHEN rollback occurs THEN users SHALL be notified of the temporary state
6. WHEN the fix is ready THEN it SHALL be deployed with verification that regressions are resolved
7. WHEN deploying fixes THEN they SHALL be tested in a staging environment first

### Requirement 9: Immediate Diagnostic Logging

**User Story:** As a developer, I need detailed diagnostic logging added to the current system to understand exactly where data is being corrupted or lost, so that I can fix the issues quickly.

#### Acceptance Criteria

1. WHEN crews execute THEN they SHALL log the grades they compute with ticker symbols
2. WHEN Flow state is updated THEN it SHALL log what data is being stored
3. WHEN data is passed to the report crew THEN it SHALL log all input fields and their values
4. WHEN the report crew processes data THEN it SHALL log what it receives and how it transforms it
5. WHEN URLs are generated THEN the system SHALL log the actual URLs being created
6. WHEN alternatives are found THEN the system SHALL log the alternatives for each holding
7. WHEN data availability is checked THEN the system SHALL log the status of each data source

### Requirement 10: Data Consolidation - NO HALLUCINATIONS

**User Story:** As a user paying for expensive AI analysis, I need the final report to consolidate ALL actual data produced by crews, not generate hallucinations or use fallback values, so that I get value from the computational resources spent.

**CRITICAL**: The system must NEVER show generic/fallback data when actual crew analysis exists. Every piece of data in the final report must be traceable to actual crew outputs, not invented or defaulted.

#### Acceptance Criteria

1. WHEN crews generate analysis data THEN that data SHALL be used in the final report, not replaced with defaults
2. WHEN the report displays grades THEN they SHALL come from actual crew analysis, not fallback Grade D values
3. WHEN the report shows risk scores THEN they SHALL come from actual risk assessment tools, not baseline defaults
4. WHEN the report includes URLs THEN they SHALL be real URLs from tools, not example.com placeholders
5. WHEN alternatives are shown THEN they SHALL be from actual alternative finding logic, not empty lists
6. WHEN data availability is reported THEN it SHALL reflect actual data sources queried, not "NOT PROVIDED" messages
7. WHEN the system cannot find crew data THEN it SHALL log detailed errors and investigate why, not silently use defaults
8. WHEN consolidating data THEN the system SHALL verify each field comes from actual crew output before including it
9. IF crew data is missing THEN the system SHALL fail loudly with clear error messages, not silently degrade to hallucinations
10. WHEN users see analysis results THEN they SHALL be confident the data reflects actual analysis, not invented values

### Requirement 11: Audit Trail and Data Provenance

**User Story:** As an auditor, I need complete traceability from every data point in the report back to its original source, so that I can fact-check the analysis and verify data accuracy for compliance and due diligence.

**COMPLIANCE REQUIREMENT**: Financial reports must be auditable. Every claim, grade, risk score, and recommendation must be traceable to verifiable sources.

#### Acceptance Criteria

1. WHEN the report shows a grade THEN it SHALL include the source of that grade (crew name, analysis date, confidence level)
2. WHEN the report shows a risk score THEN it SHALL cite the tool and data sources used to compute it
3. WHEN the report references SEC filings THEN it SHALL include direct EDGAR URLs to the specific filing
4. WHEN the report shows market data THEN it SHALL cite the data provider (Yahoo Finance, Alpha Vantage, etc.) with as-of date
5. WHEN the report includes recommendations THEN it SHALL show the reasoning chain and data sources that led to that recommendation
6. WHEN an auditor needs to verify data THEN they SHALL be able to click through to original sources
7. WHEN data cannot be verified THEN it SHALL NOT be included in the report (no unverifiable claims)
8. WHEN the report is generated THEN it SHALL include a "Data Sources" section listing all sources with URLs
9. WHEN crew analysis is used THEN the report SHALL indicate which crew performed the analysis and when
10. WHEN the system uses cached data THEN the report SHALL indicate the cache age and original analysis date

### Requirement 12: End-to-End Data Flow Verification

**User Story:** As a senior data analyst, I need to verify that all crews are generating proper data AND that data is consumed properly to generate reports, so that I can ensure data integrity throughout the entire pipeline.

**DATA QUALITY ASSURANCE**: The system must provide verification at every stage: data generation, data storage, data retrieval, data consolidation, and report generation.

#### Acceptance Criteria

1. WHEN crews execute THEN the system SHALL log what data they generated (grades, scores, URLs, recommendations)
2. WHEN crew data is stored THEN the system SHALL verify the data was written correctly and is retrievable
3. WHEN data is retrieved THEN the system SHALL verify it matches what was stored (no corruption)
4. WHEN data is consolidated THEN the system SHALL log which crew data was included and which was missing
5. WHEN the report is generated THEN the system SHALL verify each data point came from actual crew output
6. WHEN data flow is complete THEN the system SHALL provide a verification report showing: crews run, data generated, data stored, data retrieved, data used in report
7. WHEN data is missing at any stage THEN the system SHALL log detailed diagnostics: what was expected, what was found, where the gap occurred
8. WHEN debugging data issues THEN analysts SHALL be able to trace data from crew output → storage → retrieval → consolidation → report
9. WHEN the system runs THEN it SHALL generate a data lineage report showing the complete flow for audit purposes
10. WHEN data quality issues are detected THEN the system SHALL alert immediately, not silently degrade

### Requirement 13: Fail-Fast Error Handling - NO SILENT DEGRADATION

**User Story:** As an expert on quality outcomes, I want the system to stop immediately if it detects errors, so that bad data never reaches the final report and users are never misled by degraded output.

**QUALITY PRINCIPLE**: It is better to fail loudly and stop execution than to silently degrade and produce misleading reports. Users must be able to trust that if they receive a report, it contains accurate data.

#### Acceptance Criteria

1. WHEN crew execution fails THEN the system SHALL stop immediately and report the error, not continue with fallback data
2. WHEN data retrieval fails THEN the system SHALL stop and investigate why, not silently use Grade D defaults
3. WHEN data consolidation finds missing data THEN the system SHALL stop and log detailed diagnostics, not proceed with partial data
4. WHEN URL generation fails THEN the system SHALL stop and report the issue, not forge example.com placeholders
5. WHEN alternative finding fails THEN the system SHALL stop and explain why, not show empty lists
6. WHEN data validation detects corruption THEN the system SHALL stop immediately, not attempt to fix or ignore it
7. WHEN the report crew receives incomplete inputs THEN it SHALL refuse to generate a report, not fill gaps with hallucinations
8. WHEN any data quality check fails THEN the system SHALL provide clear error messages with remediation steps
9. WHEN errors are detected THEN the system SHALL log: what failed, why it failed, what data was expected, what was found
10. WHEN the system stops due to errors THEN users SHALL receive actionable error messages, not generic failures

**EXCEPTION**: The system MAY continue with graceful degradation ONLY when explicitly configured to do so AND when it clearly marks degraded sections in the report with warnings.

### Requirement 14: CrewAI Task and Agent Configuration Validation

**User Story:** As a CrewAI expert, I need to ensure that all crew task descriptions are accurate and synchronized with our specifications and requirements, so that agents perform the correct analysis and produce the expected outputs.

**CONFIGURATION INTEGRITY**: Crew configurations (agents.yaml, tasks.yaml) must accurately reflect the system requirements. Misaligned configurations lead to agents performing wrong analysis or producing incorrect output formats.

#### Acceptance Criteria

1. WHEN crews are configured THEN their task descriptions SHALL match the requirements in this specification
2. WHEN agents are defined THEN their roles and goals SHALL align with the data they are expected to produce
3. WHEN tasks specify expected_output THEN it SHALL match the actual Pydantic schemas used for validation
4. WHEN tasks use output_pydantic THEN the schema SHALL exist and be correctly referenced
5. WHEN agents use tools THEN those tools SHALL be appropriate for the task and produce the expected data format
6. WHEN the report crew is configured THEN it SHALL have NO tools (tool-free reporter pattern)
7. WHEN discovery crews are configured THEN they SHALL be clearly marked as "top 10 screening" not "single ticker analysis"
8. WHEN deep analysis crews are configured THEN they SHALL be clearly marked as "single ticker deep dive"
9. WHEN task descriptions are updated THEN they SHALL be reviewed against requirements to ensure alignment
10. WHEN configuration drift is detected THEN the system SHALL alert and require manual review before proceeding

### Requirement 15: Pydantic Schema Enforcement for Data Transfer

**User Story:** As a data scientist, I need to ensure that Pydantic is always used to transfer data with high quality and semantic validation, so that data integrity is maintained throughout the system and type safety prevents errors.

**DATA TRANSFER STANDARD**: ALL data transfers between system components MUST use strict Pydantic v2 models with `extra='forbid'` to ensure type safety, semantic validation, and prevent data corruption.

#### Acceptance Criteria

1. WHEN crews generate outputs THEN they SHALL use Pydantic models with strict validation (`extra='forbid'`)
2. WHEN data is passed between Flow methods THEN it SHALL be validated against Pydantic schemas
3. WHEN the report crew receives inputs THEN all inputs SHALL be Pydantic-validated before processing
4. WHEN data is stored THEN it SHALL be serialized from validated Pydantic models
5. WHEN data is retrieved THEN it SHALL be deserialized into Pydantic models with validation
6. WHEN data transformations occur THEN input and output SHALL both be Pydantic-validated
7. WHEN validation fails THEN the system SHALL stop immediately with detailed field-level error messages
8. WHEN new data structures are added THEN they SHALL have corresponding Pydantic models defined
9. WHEN Pydantic models are updated THEN all usages SHALL be reviewed for compatibility
10. WHEN data is passed as dict THEN it SHALL be immediately converted to Pydantic model for validation

**BANNED PATTERNS:**
- ❌ Passing raw dicts between components without validation
- ❌ Using `extra='allow'` (allows unknown fields)
- ❌ Skipping validation for "performance"
- ❌ Manual dict construction instead of Pydantic models
- ❌ Type: ignore comments to bypass validation

**REQUIRED PATTERNS:**
- ✅ All crew outputs use `output_pydantic` with strict schemas
- ✅ All Flow state fields are Pydantic models
- ✅ All API boundaries validate with Pydantic
- ✅ All data storage/retrieval uses Pydantic serialization
- ✅ Validation errors include field paths and clear messages

### Requirement 16: Alignment with FinWiz Steering Standards

**User Story:** As a system architect, I need to ensure all requirements align with FinWiz steering standards, so that the fix maintains consistency with established patterns and doesn't introduce architectural drift.

**STEERING COMPLIANCE**: All fixes must comply with established FinWiz standards in `.kiro/steering/` directory.

#### Acceptance Criteria - Alignment Verification

1. **validation.md**: WHEN implementing fixes THEN they SHALL use strict Pydantic v2 models with `extra='forbid'` as specified
2. **crewai-standards.md**: WHEN configuring crews THEN they SHALL follow the required structure (agents.yaml, tasks.yaml, output_pydantic)
3. **crewai-flow-compliance.md**: WHEN using Flow state THEN it SHALL use structured Pydantic models, not unstructured dicts
4. **output-standards.md**: WHEN generating reports THEN they SHALL use proper HTML structure, French language, and emoji standards
5. **testing-standards.md**: WHEN writing tests THEN they SHALL use pytest-mock (unittest.mock is BANNED)
6. **quality.md**: WHEN handling errors THEN they SHALL implement graceful degradation with clear logging
7. **security.md**: WHEN handling data THEN they SHALL never log sensitive information or API keys
8. **tech.md**: WHEN writing code THEN it SHALL follow Ruff standards (110 char limit, type hints)
9. **finance.md**: WHEN providing analysis THEN it SHALL use standardized risk assessment (0-5 scale)
10. **agents.md**: WHEN configuring agents THEN they SHALL follow AI-driven analysis principles (not just Python logic)

**CRITICAL ALIGNMENTS:**
- ✅ Pydantic strict validation (validation.md)
- ✅ CrewAI Flow structured state (crewai-flow-compliance.md)
- ✅ Tool-free final reporter (crewai-standards.md)
- ✅ pytest-mock only (testing-standards.md, unittest-mock-ban.md)
- ✅ Fail-fast error handling (quality.md)
- ✅ French output standards (output-standards.md)
- ✅ Audit trail requirements (finance.md, security.md)

### Requirement 17: Validation of Recent Changes

**User Story:** As a code reviewer, I need to validate that recent changes to data passing and report generation are correct and haven't introduced bugs, so that the system works as designed.

#### Acceptance Criteria

1. WHEN reviewing Task 13 changes THEN they SHALL be verified to correctly pass all Flow state to report crew
2. WHEN reviewing data consolidation fixes THEN they SHALL be verified to not corrupt existing data
3. WHEN reviewing report crew changes THEN they SHALL be verified to correctly process all inputs
4. WHEN reviewing Flow state management THEN it SHALL be verified to preserve all data correctly
5. IF any recent change is found to be incorrect THEN it SHALL be reverted or fixed
6. WHEN validating changes THEN they SHALL be tested with real portfolio data
7. WHEN changes are validated THEN they SHALL be verified to not introduce new regressions
# Requirements Document

## Introduction

This specification defines a complete overhaul of the FinWiz architecture based on critical findings from the failed implementation attempt. The current implementation has fundamental architectural flaws that prevent it from delivering the promised outcomes:

1. **AI-based deep analysis is still being used** instead of pure Python scoring
2. **JSON exports are only cached, not properly output** to final directories
3. **A+ discovery system is not integrated** with deep analysis results
4. **Backtesting pipeline is disconnected** from discovery results
5. **Final reports are still AI-generated** instead of Python template-based
6. **Performance targets are not met** - no speed improvement achieved

This updated specification addresses these critical failures with a **PURE PYTHON FIRST** approach that eliminates AI where deterministic calculations are sufficient, ensuring 10-20x speed improvements and 100% cost reduction for calculations.

## Glossary

- **Pure Python Analysis**: Deterministic calculations using Python functions instead of AI agents for scoring, grading, and recommendations
- **DeepAnalysisScorer**: Python class that performs all deep analysis calculations without AI/LLM calls
- **Python Report Generator**: Jinja2-based HTML generation replacing AI-based report creation
- **Portfolio Deep Analyzer**: Pure Python system for analyzing multiple holdings concurrently
- **AI Minimalism**: Design principle - use AI only for tasks requiring reasoning, use Python for deterministic tasks
- **Crew**: An autonomous AI agent team (only used when AI reasoning is truly necessary)
- **Flow**: The CrewAI Flow orchestrator that manages execution sequence and calls Python functions
- **JSON Export**: Pydantic-validated data structure saved to output directory (not just cache)
- **Template-Based Reporting**: HTML generation using Jinja2 templates instead of AI agents






## Requirements

### Requirement 0: CRITICAL FIXES FOR IMPLEMENTATION FAILURES

**User Story:** As a FinWiz stakeholder, I want the fundamental architectural failures identified in the implementation analysis to be fixed immediately, so that the system delivers the promised 10-20x speed improvement and 100% cost reduction.

#### Acceptance Criteria - Replace AI Deep Analysis with Pure Python

1. THE System SHALL completely replace `DeepAnalysisCrew` AI-based analysis with pure Python `PortfolioDeepAnalyzer`
2. THE `PortfolioDeepAnalyzer` SHALL use the implemented `DeepAnalysisScorer` class for all calculations
3. THE Flow SHALL call `analyze_portfolio_with_python()` function instead of executing AI crews
4. THE Python analysis SHALL complete in seconds (not minutes) with 0 LLM calls for calculations
5. THE Python analysis SHALL generate deterministic, reproducible results
6. THE System SHALL eliminate the 5-task AI workflow: data_collection → technical_analysis → risk_assessment → final_report → export
7. THE System SHALL replace it with 2-step Python workflow: data_extraction → python_scoring

#### Acceptance Criteria - Fix JSON Export to Output Directory

8. THE System SHALL save JSON exports to `output/` directory structure, NOT just cache
9. THE JSON exports SHALL be saved to: `output/stock/`, `output/etf/`, `output/crypto/` directories
10. THE System SHALL create consolidated JSON export at: `output/deep_analysis_consolidated_{session_id}.json`
11. THE JSON files SHALL be accessible for backtesting and A+ discovery integration
12. THE System SHALL NOT rely on cache-only storage that is invisible to downstream processes

#### Acceptance Criteria - Integrate A+ Discovery with Deep Analysis Results

13. THE A+ discovery system SHALL read deep analysis JSON exports from output directory
14. THE System SHALL identify holdings with grades A+ and A from deep analysis results
15. THE `has_a_plus_analysis` field SHALL be set to `true` when A+ holdings are found
16. THE `total_opportunities_found` SHALL reflect actual count of A+ holdings from analysis
17. THE A+ discovery SHALL NOT show 0 opportunities when A+ holdings exist in the portfolio

#### Acceptance Criteria - Connect Backtesting Pipeline to Discovery Results

18. THE backtesting pipeline SHALL read A+ opportunities from discovery JSON exports
19. THE backtesting SHALL execute automatically when A+ candidates are available
20. THE backtesting results SHALL be included in the final report
21. THE System SHALL NOT show "Backtesting : Non exécuté / données non fournies" when candidates exist

#### Acceptance Criteria - Replace AI Report Generation with Python Templates

22. THE System SHALL use `PythonReportGenerator` class with Jinja2 templates for all HTML generation
23. THE final report SHALL be generated by `generate_python_report()` function, NOT AI crews
24. THE report generation SHALL complete in milliseconds using templates
25. THE final report SHALL contain actual analysis data, NOT placeholder content
26. THE System SHALL eliminate AI-based HTML generation that produces inconsistent results

#### Acceptance Criteria - Achieve Performance Targets

27. THE System SHALL achieve 10-20x speed improvement over current AI-based approach
28. THE System SHALL complete 66-holding portfolio analysis in 10-30 minutes (vs current 3-6 hours)
29. THE System SHALL achieve 100% cost reduction for calculations (0 LLM calls for scoring)
30. THE System SHALL demonstrate measurable performance improvements in execution logs

#### Acceptance Criteria - Integration Script for Validation

31. THE System SHALL include `scripts/run_python_analysis.py` to demonstrate pure Python approach
32. THE integration script SHALL load portfolio data, run Python analysis, and generate reports
33. THE integration script SHALL log performance metrics proving speed and cost improvements
34. THE integration script SHALL serve as validation that all components work together

#### Acceptance Criteria - Compliance with AI Minimalism

35. THE System SHALL follow AI Minimalism principle: use Python for deterministic tasks, AI only for reasoning
36. THE System SHALL eliminate AI usage for: calculations, HTML generation, data validation, data transformation
37. THE System SHALL use AI only for: complex synthesis requiring judgment (optional)
38. THE System SHALL be ruthless: if Python can do it, use Python

### Requirement 1: Pydantic-Validated Export Objects for All Crews

**User Story:** As a FinWiz developer, I want each crew to generate a Pydantic-validated export object saved to JSON, so that all crew outputs are type-safe and validated.

#### Acceptance Criteria

1. THE System SHALL define a dedicated Pydantic export schema for each crew (StockCrewExport, ETFCrewExport, CryptoCrewExport, DeepAnalysisCrewExport, DiscoveryCrewExport, RebalancingCrewExport)
2. WHEN a crew completes its analysis tasks, THE Crew SHALL have a final reporter task that creates a Pydantic-validated export object
3. THE reporter task SHALL validate all analysis data against the crew's Pydantic export schema
4. WHEN validation succeeds, THE reporter task SHALL save the Pydantic export object to a JSON file
5. THE JSON file SHALL include all analysis data (scores, grades, recommendations, risk assessments, metadata, file paths)
6. THE JSON file SHALL be saved to: `output/reports/{session_id}/{crew_name}/{crew_name}_export.json`
7. IF validation fails, THEN THE reporter task SHALL raise a clear error with validation failure details

### Requirement 2: HTML Report Generation with Python Templates (NO AI)

**User Story:** As a FinWiz developer, I want HTML reports generated using Python templates (Jinja2) from JSON exports, so that report generation is fast, testable, cheap, and deterministic.

#### Acceptance Criteria

1. THE System SHALL use Jinja2 templates for ALL HTML report generation (NO AI agents for HTML generation)
2. THE System SHALL create professional HTML templates for each crew type with light/dark mode support
3. THE HTML templates SHALL accept the crew's JSON export as input data
4. THE HTML generation SHALL be pure Python code (testable, fast, no LLM costs)
5. WHEN a crew completes its JSON export, THE System SHALL call a Python function to generate HTML from template
6. THE HTML generation function SHALL validate the JSON data against the crew's Pydantic export schema
7. THE HTML templates SHALL include professional styling (CSS) with responsive design
8. THE HTML file SHALL be saved to: `output/reports/{session_id}/{crew_name}/{crew_name}_report.html`
9. THE HTML generation SHALL NOT use AI agents, LLM calls, or CrewAI tasks
10. THE HTML generation code SHALL be unit-testable with mock JSON data

### Requirement 3: Python-Based Data Consolidation (NO Aggregator Crew)

**User Story:** As a FinWiz developer, I want data consolidation done in pure Python without any AI crew, so that aggregation is fast, deterministic, testable, and free of LLM costs.

#### Acceptance Criteria

1. THE System SHALL use pure Python code for data consolidation (NO Aggregator Crew, NO AI agents)
2. THE Flow SHALL call a Python consolidation function after all SME crews complete
3. THE Python consolidation function SHALL receive file paths of all SME crew JSON exports as parameters
4. THE Python consolidation function SHALL read all SME crew JSON export files from disk
5. WHEN reading JSON files, THE consolidation function SHALL validate each file against its source crew's Pydantic export schema
6. THE consolidation function SHALL create a consolidated Pydantic export object (ConsolidatedReportExport)
7. THE consolidation function SHALL save the consolidated export to: `output/reports/{session_id}/consolidated_report.json`
8. THE consolidation function SHALL preserve ALL grades, scores, and recommendations exactly as provided by SME crews
9. THE consolidation function SHALL be unit-testable with mock JSON files
10. THE consolidation function SHALL NOT call external APIs or LLMs
11. THE consolidation SHALL be deterministic (same inputs = same outputs)
12. THE consolidation function SHALL complete in milliseconds (not seconds)

### Requirement 4: Comprehensive Crew Evaluation - All Existing Crews

**User Story:** As a FinWiz manager, I want to evaluate ALL existing crews (crypto_crew, deep_analysis, etf_crew, investment_discovery_crew, portfolio_rebalancing_crew, report_crew, stock_crew) to identify tasks that should be Python instead of AI, so that we maximize quality, speed, and cost-efficiency.

#### Acceptance Criteria

1. THE System SHALL evaluate EVERY task in EVERY existing crew to determine if AI is truly necessary
2. THE evaluation SHALL cover: crypto_crew, deep_analysis, etf_crew, investment_discovery_crew, portfolio_rebalancing_crew, report_crew, stock_crew
3. FOR EACH crew, THE System SHALL document:
   - Which tasks require AI (and WHY - what makes them non-deterministic)
   - Which tasks should be Python (and implementation requirements)
   - Which tasks should be removed entirely (redundant or unnecessary)
4. THE evaluation SHALL identify tasks that are:
   - Data fetching (should be Python tools, not AI tasks)
   - Calculations (should be Python functions, not AI tasks)
   - Validations (should be Pydantic, not AI tasks)
   - HTML generation (should be Jinja2 templates, not AI tasks)
   - Data transformation (should be Python, not AI tasks)
5. THE System SHALL create a detailed evaluation document for each crew listing:
   - Current tasks
   - AI necessity assessment (YES/NO with justification)
   - Python replacement requirements (if applicable)
   - Expected cost savings
   - Expected performance improvement
6. THE evaluation SHALL be ruthless - if Python can do it, mark it for replacement
7. THE System SHALL prioritize: quality > speed > cost savings (but achieve all three)

### Requirement 5: Final Report Generation with Python Template (NO AI, NO Crew)

**User Story:** As a FinWiz user, I want the final French report generated using a Python template from consolidated JSON, so that report generation is instant, free, and produces consistent professional output.

#### Acceptance Criteria

1. THE System SHALL use a Jinja2 template for final report generation (NO AI agent, NO crew)
2. THE Flow SHALL call a Python function to generate the final HTML report after consolidation
3. THE final report template SHALL accept the consolidated JSON export as input
4. THE final report template SHALL generate professional French-language HTML with light/dark mode
5. THE final report SHALL include sections for each SME crew's analysis
6. THE final report generation SHALL be pure Python code (no LLM calls, no CrewAI)
7. THE final report HTML SHALL be saved to: `output/reports/{session_id}/final_report.html`
8. THE final report generation SHALL be unit-testable with mock consolidated JSON
9. THE template SHALL include executive summary, detailed findings, and recommendations sections
10. THE template SHALL use professional financial terminology in French
11. THE template SHALL be maintainable by developers (not generated by AI)
12. THE final report generation SHALL complete in milliseconds

### Requirement 6: File-Based Data Passing to Avoid Context Limits

**User Story:** As a FinWiz developer, I want the Flow to pass file paths (not data) between crews, so that we avoid exceeding model context size limits.

#### Acceptance Criteria

1. THE Flow SHALL store file paths in structured state (NOT the actual data)
2. WHEN a crew completes, THE Flow SHALL store the JSON export file path in structured state
3. WHEN passing data to downstream crews, THE Flow SHALL pass file paths as input parameters
4. THE Crews SHALL read data from files when needed (not from Flow state)
5. THE Flow state SHALL remain small and focused on orchestration metadata (file paths, status, timestamps)
6. THE System SHALL NOT pass large data objects through Flow state or crew inputs

### Requirement 7: Concurrent SME Crew Execution with Python Consolidation

**User Story:** As a FinWiz developer, I want all SME crews to run concurrently, then call a Python function for consolidation, so that analysis is fast and consolidation is instant.

#### Acceptance Criteria

1. THE Flow SHALL execute all SME crews (Stock, ETF, Crypto, DeepAnalysis, Discovery, Rebalancing) concurrently using CrewAI Flow's parallel execution patterns
2. THE Flow SHALL use `@listen()` decorators with the same trigger to enable parallel crew execution
3. THE SME crews SHALL NOT depend on each other's outputs for execution
4. WHEN all SME crews complete, THE Flow SHALL call a Python consolidation function using `@listen(and_(...))`
5. THE Flow SHALL pass all crew JSON output file paths to the Python consolidation function
6. THE Python consolidation function SHALL NOT be a CrewAI crew (pure Python function)
7. WHEN a crew fails, THE Flow SHALL continue execution and mark the crew output as unavailable
8. THE Flow SHALL track crew execution status in structured state (pending, running, completed, failed)

### Requirement 8: French Language Final Report

**User Story:** As a FinWiz user, I want the final aggregated report in professional French, so that I can review investment recommendations in my preferred language.

#### Acceptance Criteria

1. THE FinancialExpertAggregatorCrew SHALL generate the final report entirely in French
2. WHEN synthesizing findings, THE FinancialExpertAggregatorCrew SHALL use professional financial terminology in French
3. THE final report SHALL include clear sections for each SME crew's analysis (Actions, ETFs, Cryptomonnaies, Analyse Approfondie, Découverte, Rééquilibrage)
4. THE final report SHALL include executive summary, detailed findings, and actionable recommendations in French
5. THE FinancialExpertAggregatorCrew agent backstory SHALL specify French-speaking financial expert

### Requirement 9: Report File Management

**User Story:** As a FinWiz developer, I want a standardized directory structure for crew outputs, so that JSON and HTML files are easy to locate and manage.

#### Acceptance Criteria

1. THE System SHALL create an output directory structure: `output/reports/{session_id}/{crew_name}/`
2. WHEN a crew generates outputs, THE Crew SHALL save both JSON and HTML files with descriptive filenames including timestamp
3. WHEN saving JSON output, THE Crew SHALL use filename pattern: `{crew_name}_{ticker}_{timestamp}.json`
4. WHEN saving HTML output, THE Crew SHALL use filename pattern: `{crew_name}_{ticker}_{timestamp}.html`
5. WHEN the Flow executes, THE Flow SHALL track all generated file paths in structured state (separate lists for JSON and HTML)
6. THE System SHALL maintain a report manifest JSON file listing all generated outputs with metadata (crew_name, ticker, asset_class, status, file_paths)
7. WHEN the aggregator crew executes, THE FinancialExpertAggregatorCrew SHALL read the report manifest to locate source files

### Requirement 10: Data Integrity Validation

**User Story:** As a FinWiz developer, I want validation that ensures crew reports contain actual analysis data (not fallback values), so that the final report is accurate.

#### Acceptance Criteria

1. WHEN a crew generates a report, THE Crew SHALL validate that all required data fields are present
2. WHEN validating data, THE System SHALL reject reports containing only fallback values (e.g., Grade D with score 0.6)
3. IF a crew report fails validation, THEN THE System SHALL log a detailed error message with the validation failure reason
4. WHEN the aggregator crew reads a report, THE ReportAggregatorCrew SHALL validate the HTML structure and data completeness
5. IF a source report is invalid, THEN THE ReportAggregatorCrew SHALL include a warning in the final report

### Requirement 11: Clean Break from Legacy Architecture

**User Story:** As a FinWiz developer, I want to implement a clean new architecture without backward compatibility constraints, so that we can fix fundamental design flaws.

#### Acceptance Criteria

1. THE System SHALL implement a new architecture without maintaining backward compatibility with the broken legacy system
2. THE System SHALL remove all legacy data merge logic that caused fallback values to persist
3. THE System SHALL remove all legacy portfolio review injection patterns
4. THE System SHALL implement new Pydantic schemas for all crew outputs without legacy field constraints
5. THE System SHALL implement new Flow orchestration without legacy state management patterns

### Requirement 12: Error Handling and Resilience

**User Story:** As a FinWiz developer, I want robust error handling that prevents partial failures from breaking the entire Flow, so that users receive the best possible report even when some crews fail.

#### Acceptance Criteria

1. WHEN a crew fails to generate a report, THE Flow SHALL continue execution with remaining crews
2. WHEN the aggregator crew encounters a missing report, THE ReportAggregatorCrew SHALL include a placeholder section noting the missing analysis
3. IF all source reports are missing, THEN THE ReportAggregatorCrew SHALL generate a minimal report with error details
4. THE System SHALL log all crew execution failures with detailed error messages
5. WHEN a crew times out, THE Flow SHALL mark the crew as failed and continue with remaining crews

### Requirement 13: Flow-Based Routing Logic

**User Story:** As a FinWiz developer, I want all routing and orchestration logic in the CrewAI Flow, so that crews remain simple and focused on their analysis tasks.

#### Acceptance Criteria

1. THE CrewAI Flow SHALL contain ALL routing logic for crew execution sequence
2. THE Crews SHALL NOT contain any routing or orchestration logic
3. THE Crews SHALL NOT decide which other crews to execute
4. THE Flow SHALL use `@listen()`, `@router()`, and `and_()` decorators for all routing decisions
5. WHEN a crew completes, THE Crew SHALL return its output data without making routing decisions
6. THE Flow SHALL determine which crews to execute based on structured state and routing logic
7. THE Crews SHALL remain focused on their single analysis responsibility

### Requirement 14: SME Crew Independence

**User Story:** As a FinWiz developer, I want each SME crew to operate independently without requiring data from other crews, so that crews can execute concurrently without blocking.

#### Acceptance Criteria

1. THE SME crews SHALL NOT read outputs from other SME crews during execution
2. THE SME crews SHALL receive all required inputs from the Flow at kickoff time
3. WHEN a crew requires market context, THE Crew SHALL fetch data directly using its own tools
4. THE SME crews SHALL NOT share state or communicate with each other during execution
5. THE Flow SHALL provide each crew with session metadata (date, timestamp, language) at kickoff
6. WHERE a crew requires ticker information, THE Flow SHALL pass the ticker as an input parameter

### Requirement 15: Performance Optimization

**User Story:** As a FinWiz user, I want the new architecture to maximize execution performance, so that reports are generated quickly.

#### Acceptance Criteria

1. THE System SHALL execute ALL SME crews concurrently using CrewAI Flow's parallel execution (Stock, ETF, Crypto, DeepAnalysis, Discovery, Rebalancing)
2. THE SME crews SHALL use `reasoning=False` and `planning=False` for fast execution
3. THE SME crews SHALL use `allow_delegation=False` since they operate independently
4. WHEN generating outputs, THE Crew SHALL write JSON and HTML files to avoid blocking
5. THE FinancialExpertAggregatorCrew SHALL read and parse source files efficiently
6. THE System SHALL maintain existing caching mechanisms to avoid redundant crew executions
7. THE Flow SHALL use CrewAI's `@listen()` pattern with same trigger for parallel crew execution

### Requirement 16: CrewAI Best Practices Compliance

**User Story:** As a FinWiz developer, I want all crews and flows to follow CrewAI best practices for reasoning, planning, delegation, and state management, so that we achieve optimal performance and maintainability.

#### Acceptance Criteria - Flow State Management

1. THE Flow SHALL use structured Pydantic models for type-safe state management (`Flow[PydanticModel]`)
2. THE Flow SHALL NEVER use `self.inputs` for state management (unstructured, error-prone)
3. ALL Flow methods SHALL return `dict[str, Any]` for downstream listeners
4. THE Flow listeners SHALL receive upstream data as method parameters
5. THE Flow SHALL use `@router` decorator for conditional flow control based on state
6. THE Flow state SHALL contain only orchestration metadata (file paths, status, timestamps, NOT large data objects)

#### Acceptance Criteria - Agent Reasoning Configuration

7. THE System SHALL enable `reasoning=True` ONLY for crews requiring complex multi-step analysis:
   - ✅ Enable: investment_discovery_crew (complex multi-asset discovery)
   - ✅ Enable: portfolio_rebalancing_crew (complex portfolio optimization)
   - ✅ Enable: report_crew (complex data synthesis)
   - ✅ Enable: crypto_crew, stock_crew, etf_crew (complex market analysis)
   - ❌ Disable: deep_analysis_crew (high-volume execution: 66+ runs per portfolio)
8. WHEN `reasoning=True` is enabled, THE Agent SHALL set `max_reasoning_attempts=3` to prevent infinite loops
9. THE System SHALL disable reasoning for high-volume executions (66+ runs) to avoid performance overhead
10. THE System SHALL disable reasoning for simple validation tasks (ticker format checks, data validation)
11. THE System SHALL disable reasoning for final reporters (consolidation only, no new analysis)

#### Acceptance Criteria - Crew Planning Configuration

12. THE System SHALL enable `planning=True` ONLY when ALL conditions are met:
    - Crew has 4+ agents AND
    - Crew has 6+ tasks AND
    - Execution volume ≤ 3 runs
13. THE System SHALL enable planning for these crews:
    - ✅ portfolio_rebalancing_crew (3+ agents, 4+ tasks, single execution)
    - ✅ investment_discovery_crew (4 agents, 7 tasks, single execution)
    - ✅ report_crew (4 agents, 4 tasks, single execution)
14. THE System SHALL disable planning for these crews:
    - ❌ deep_analysis_crew (runs 66+ times per portfolio - overhead × 66 is too costly)
    - ❌ crypto_crew, stock_crew, etf_crew (simpler workflows, single execution)
15. WHEN planning is enabled, THE Crew SHALL set `planning_llm="gpt-5-mini"` for optimal planning quality

#### Acceptance Criteria - Agent Delegation Configuration

16. THE System SHALL enable `allow_delegation=True` ONLY for coordinator/lead agents managing workflow
17. THE System SHALL disable delegation for focused specialist agents (single responsibility)
18. THE System SHALL disable delegation for final reporters (consolidation only)
19. THE final reporter agents SHALL use `@final_reporter` decorator to enforce empty tools and no delegation

#### Acceptance Criteria - Performance Cost Awareness

20. THE System SHALL document performance costs for each feature:
    - `reasoning=True`: 5-15 seconds, 1-3 LLM calls, 500-2000 tokens per cycle
    - `planning=True`: Overhead × execution count (critical for high-volume crews)
    - `allow_delegation=True`: 5-15 seconds per delegation, 1-2 LLM calls
21. THE System SHALL optimize crew configurations based on execution volume:
    - Single execution (1-3 runs): Enable reasoning, planning, delegation as needed
    - High volume (66+ runs): Disable reasoning, planning, delegation for performance
22. THE System SHALL use `async_execution=true` for I/O-bound tasks (except final task which must be synchronous)

#### Acceptance Criteria - Configuration Matrix

23. THE System SHALL implement the following configuration matrix:

| Crew | Reasoning | Planning | Delegation | Execution Volume | Rationale |
|------|-----------|----------|------------|------------------|-----------|
| report_crew | Mixed | ✅ Enable | Mixed | 1 | 4 agents, 4 tasks, complex synthesis |
| investment_discovery | ✅ Enable | ✅ Enable | ✅ Enable | 1 | 4 agents, 7 tasks, complex coordination |
| portfolio_rebalancing | ✅ Enable | ✅ Enable | ✅ Enable | 1 | 3+ agents, 4+ tasks, optimization |
| deep_analysis | ❌ Disable | ❌ Disable | ❌ Disable | 66+ | High volume - avoid overhead |
| crypto_crew | ✅ Enable | ❌ Disable | Mixed | 1 | Complex analysis, simpler workflow |
| stock_crew | ✅ Enable | ❌ Disable | Mixed | 1 | Complex analysis, simpler workflow |
| etf_crew | ✅ Enable | ❌ Disable | Mixed | 1 | Complex analysis, simpler workflow |

#### Acceptance Criteria - Anti-Patterns to Avoid

24. THE System SHALL NOT use `self.inputs` for Flow state management
25. THE System SHALL NOT enable reasoning for high-volume executions (66+ runs)
26. THE System SHALL NOT enable planning for single-agent crews
27. THE System SHALL NOT enable delegation for specialist agents or final reporters
28. THE System SHALL NOT omit `max_reasoning_attempts` when reasoning is enabled
29. THE System SHALL NOT use unstructured Flow state (always use Pydantic models)

### Requirement 17: Batch Deep Analysis Execution for Performance Optimization

**User Story:** As a FinWiz user, I want deep analysis of multiple portfolio holdings to execute concurrently in batches, so that analysis completes in minutes instead of hours.

#### Acceptance Criteria - Batch Crew Execution

1. THE System SHALL execute deep analysis crews in concurrent batches instead of sequentially
2. THE Flow SHALL group holdings into batches of 5-10 tickers for concurrent execution
3. WHEN analyzing 66 holdings, THE System SHALL create 7-14 concurrent batches (not 66 sequential runs)
4. THE Flow SHALL use `asyncio.gather()` or CrewAI Flow parallel patterns for batch execution
5. THE System SHALL configure batch size based on:
   - API rate limits (20 requests per minute for most providers)
   - Memory constraints (5-10 concurrent crews recommended)
   - LLM provider concurrency limits
6. THE Flow SHALL track batch execution progress (batch 1/7, batch 2/7, etc.)
7. WHEN a ticker in a batch fails, THE System SHALL continue with remaining tickers in the batch
8. THE System SHALL log batch execution metrics (batch size, duration, success rate)

#### Acceptance Criteria - Batch API Query Optimization

9. THE System SHALL implement batch API query tools where providers support it
10. THE YahooFinanceBatchTool SHALL fetch data for multiple tickers in a single API call using `yf.download(tickers=['AAPL', 'MSFT', 'GOOGL'])`
11. THE AlphaVantageBatchTool SHALL queue multiple ticker requests and execute with rate limiting
12. THE QuantitativeAnalysisTool SHALL accept multiple tickers and process them efficiently
13. WHEN batch API queries are available, THE Crew SHALL use batch tools instead of single-ticker tools
14. THE batch tools SHALL return structured data with per-ticker results
15. THE batch tools SHALL handle partial failures (some tickers succeed, some fail)
16. THE batch tools SHALL validate all ticker symbols before making API calls

#### Acceptance Criteria - Performance Targets

17. THE System SHALL reduce deep analysis execution time from 3-6 hours to 20-40 minutes for 66 holdings
18. THE System SHALL achieve 80%+ time reduction through batch processing
19. THE System SHALL maintain data quality and validation standards in batch mode
20. THE System SHALL log performance metrics comparing sequential vs batch execution
21. THE System SHALL provide progress indicators during batch execution (e.g., "Analyzing batch 3/7: AAPL, MSFT, GOOGL, TSLA, NVDA")

#### Acceptance Criteria - Batch Tool Implementation

22. THE System SHALL create `YahooFinanceBatchTickerInfoTool` for fetching multiple ticker info in one call
23. THE System SHALL create `YahooFinanceBatchHistoryTool` for fetching multiple ticker histories in one call
24. THE System SHALL create `AlphaVantageBatchOverviewTool` with intelligent rate limiting for multiple tickers
25. THE batch tools SHALL use Pydantic models for input validation (list of tickers)
26. THE batch tools SHALL return `Dict[str, TickerData]` mapping ticker to results
27. THE batch tools SHALL include error handling for individual ticker failures
28. THE batch tools SHALL respect API rate limits (20 RPM for most providers)

#### Acceptance Criteria - Deep Analysis Crew Batch Mode

29. THE DeepAnalysisCrew SHALL support batch mode accepting multiple tickers as input
30. WHEN in batch mode, THE DeepAnalysisCrew SHALL use batch API tools for data fetching
31. THE DeepAnalysisCrew SHALL generate separate DeepAnalysisCrewExport for each ticker
32. THE DeepAnalysisCrew SHALL save batch results to: `output/reports/{session_id}/deep_analysis/batch_{batch_num}/`
33. THE DeepAnalysisCrew batch mode SHALL disable reasoning (`reasoning=False`) for performance
34. THE DeepAnalysisCrew batch mode SHALL use simplified analysis workflow (core metrics only)
35. THE DeepAnalysisCrew batch mode SHALL maintain validation and grading standards

#### Acceptance Criteria - Flow Batch Orchestration

36. THE Flow SHALL implement `analyze_holdings_deep_batch()` method for batch execution
37. THE Flow method SHALL receive list of holdings and batch size as parameters
38. THE Flow method SHALL split holdings into batches and execute concurrently
39. THE Flow method SHALL use `@listen()` with batch completion tracking
40. THE Flow method SHALL aggregate batch results into consolidated state
41. THE Flow method SHALL handle batch failures gracefully (continue with successful batches)
42. THE Flow method SHALL return batch execution summary (total tickers, successful, failed, duration)

#### Acceptance Criteria - Batch Execution Monitoring

43. THE System SHALL log batch execution start with ticker list
44. THE System SHALL log batch execution progress (ticker 1/5 complete, ticker 2/5 complete)
45. THE System SHALL log batch execution completion with metrics (duration, success rate)
46. THE System SHALL track API call counts per batch for rate limit monitoring
47. THE System SHALL provide real-time progress updates to user (optional)

#### Acceptance Criteria - Backward Compatibility

48. THE DeepAnalysisCrew SHALL support both single-ticker mode (existing) and batch mode (new)
49. THE Flow SHALL detect execution mode based on input (single ticker vs list of tickers)
50. THE System SHALL maintain existing single-ticker behavior for non-portfolio analysis
51. THE System SHALL use batch mode automatically for portfolio deep analysis (66+ holdings)

#### Acceptance Criteria - Error Handling and Resilience

52. WHEN a batch fails completely, THE Flow SHALL retry with smaller batch size (divide by 2)
53. WHEN individual tickers fail in a batch, THE System SHALL log failures and continue
54. THE System SHALL collect all batch errors and report them in consolidated summary
55. THE System SHALL NOT fail entire portfolio analysis due to single ticker failures
56. THE System SHALL provide fallback to sequential execution if batch mode fails repeatedly

#### Acceptance Criteria - Configuration and Tuning

57. THE System SHALL expose batch configuration via environment variables:
    - `DEEP_ANALYSIS_BATCH_SIZE` (default: 5)
    - `DEEP_ANALYSIS_MAX_CONCURRENT_BATCHES` (default: 2)
    - `DEEP_ANALYSIS_BATCH_MODE_ENABLED` (default: true)
58. THE System SHALL validate batch configuration on startup
59. THE System SHALL log batch configuration at Flow initialization
60. THE System SHALL allow disabling batch mode for debugging (sequential fallback)

#### Acceptance Criteria - Performance Metrics and Reporting

61. THE System SHALL track and log batch execution metrics:
    - Total execution time (batch vs sequential)
    - Average time per ticker
    - API calls per ticker
    - Success rate per batch
    - Memory usage per batch
62. THE System SHALL generate batch execution report saved to: `output/reports/{session_id}/batch_execution_metrics.json`
63. THE batch execution report SHALL include comparison to estimated sequential execution time
64. THE System SHALL calculate and log time savings percentage

#### Acceptance Criteria - API Rate Limit Management

65. THE System SHALL implement intelligent rate limiting for batch API calls
66. THE System SHALL respect provider-specific rate limits:
    - Yahoo Finance: No strict limit, but throttle to 10 requests/second
    - Alpha Vantage: 5 calls/minute (free tier), 75 calls/minute (premium)
    - Twelve Data: 8 calls/minute (free tier), 800 calls/minute (premium)
67. THE System SHALL queue batch requests and execute with appropriate delays
68. THE System SHALL implement exponential backoff for rate limit errors
69. THE System SHALL log rate limit events and retry attempts

#### Acceptance Criteria - Memory Management

70. THE System SHALL limit concurrent crew instances to prevent memory exhaustion
71. THE System SHALL implement crew instance pooling for batch execution
72. THE System SHALL clean up crew resources after batch completion
73. THE System SHALL monitor memory usage and adjust batch size dynamically if needed
74. THE System SHALL log memory usage warnings when approaching limitsLL log memory usage metrics per batch

#### Acceptance Criteria - Testing and Validation

75. THE System SHALL include unit tests for batch tool implementations
76. THE System SHALL include integration tests for batch crew execution
77. THE System SHALL include performance tests comparing batch vs sequential execution
78. THE System SHALL validate batch results match single-ticker results (data quality)
79. THE System SHALL test error handling for partial batch failures
80. THE System SHALL test rate limit handling and retry logic

### Requirement 18: Python-Based Scoring Engine for Deep Analysis

**User Story:** As a FinWiz developer, I want deep analysis scoring calculations done in pure Python instead of AI reasoning, so that analysis is 10-20x faster, 100% deterministic, fully testable, and eliminates LLM costs for calculations.

**Context:** Current deep analysis uses 5 AI tasks per ticker with extensive LLM reasoning for calculations that are fundamentally deterministic (composite scores, grades, risk scores, recommendations). Analysis from DATA_LOSS_ANALYSIS.md shows that AI provides minimal unique value beyond reformatting tool outputs into prose, while consuming 5-10 minutes and $0.05-0.10 per ticker.

#### Acceptance Criteria - Python Scoring Engine

1. THE System SHALL create a `DeepAnalysisScorer` class in `src/finwiz/scoring/deep_analysis_scorer.py`
2. THE DeepAnalysisScorer SHALL implement deterministic calculation methods for:
   - Composite score (0.0-1.0) using weighted formula: 40% fundamental + 30% technical + 30% risk
   - Letter grade (A+ to F) based on composite score thresholds
   - Investment recommendation (BUY/HOLD/SELL) based on grade and risk score
   - Rationale text explaining the recommendation
3. THE DeepAnalysisScorer SHALL calculate fundamental score from metrics:
   - ROE bonus: +0.2 if >20%, +0.1 if >15%
   - Debt penalty: -0.1 if debt/equity >0.5, -0.2 if >1.0
   - Growth bonus: +0.2 if revenue growth >15%, +0.1 if >10%
4. THE DeepAnalysisScorer SHALL calculate technical score from metrics:
   - RSI analysis: +0.1 if 40-60 (neutral), -0.2 if <30 or >70
   - Trend analysis: +0.3 if strong uptrend (SMA crossover), -0.3 if downtrend
5. THE DeepAnalysisScorer SHALL calculate risk score (0-5 scale) from metrics:
   - Base score: (volatility / 35) * 2.0
   - Drawdown penalty: (abs(max_drawdown) / 50) * 1.5
   - Beta adjustment: +0.5 if >1.5, -0.3 if <0.5
6. THE DeepAnalysisScorer SHALL assign grades using thresholds:
   - A+: ≥0.90, A: ≥0.85, A-: ≥0.80
   - B+: ≥0.75, B: ≥0.70, B-: ≥0.65
   - C+: ≥0.60, C: ≥0.55, C-: ≥0.50
   - D+: ≥0.45, D: ≥0.40, D-: ≥0.35, F: <0.35
7. THE DeepAnalysisScorer SHALL generate recommendations using rules:
   - BUY: grade in [A+, A, A-] AND risk_score ≤ 3.0
   - HOLD: grade in [B+, B] AND risk_score ≤ 3.5, OR grade in [B-, C+, C]
   - SELL: grade in [D+, D, D-, F] OR risk_score > 4.0
8. THE DeepAnalysisScorer SHALL be fully unit-testable with mock input data
9. THE DeepAnalysisScorer SHALL complete all calculations in <1 second per ticker
10. THE DeepAnalysisScorer SHALL produce deterministic results (same input = same output)

#### Acceptance Criteria - Simplified Deep Analysis Crew

11. THE DeepAnalysisCrew SHALL be simplified from 5 tasks to 2 tasks:
    - Task 1: Data Collection (async) - Fetch all data using tools, store in context
    - Task 2: Python Scoring (sync) - Use DeepAnalysisScorer to calculate results
12. THE Data Collection task SHALL fetch data using existing tools:
    - QuantitativeAnalysisTool for technical metrics
    - EnhancedSECAnalysisTool / EnhancedETFAnalysisTool / EnhancedCryptoAnalysisTool for fundamentals
    - StandardizedSentimentTool for sentiment data
13. THE Data Collection task SHALL store fetched data in structured context dict
14. THE Data Collection task SHALL NOT perform any AI reasoning or analysis
15. THE Python Scoring task SHALL call DeepAnalysisScorer with fetched data
16. THE Python Scoring task SHALL NOT use any AI reasoning or LLM calls
17. THE Python Scoring task SHALL return DeepAnalysisResult Pydantic object
18. THE DeepAnalysisCrew SHALL remove these AI tasks:
    - ❌ deep_analysis_task (AI reasoning)
    - ❌ technical_analysis_task (AI reasoning)
    - ❌ risk_assessment_task (AI reasoning)
    - ❌ final_report_task (AI HTML generation)
    - ❌ generate_export_task (AI consolidation)
19. THE DeepAnalysisCrew SHALL disable reasoning for all agents (`reasoning=False`)
20. THE DeepAnalysisCrew SHALL complete analysis in 10-30 seconds per ticker (vs 5-10 minutes)

#### Acceptance Criteria - Data Preservation

21. THE Python scoring approach SHALL preserve ALL data from tool outputs:
    - All raw metrics (volatility, beta, ROE, debt/equity, RSI, MACD, etc.)
    - All sentiment data (sentiment_score, trending_topics, article_count)
    - All technical indicators (support/resistance, trend direction)
    - All fundamental data (revenue, earnings, cash flow)
22. THE Python scoring approach SHALL preserve ALL calculation results:
    - Composite score (0.0-1.0)
    - Letter grade (A+ to F)
    - Investment recommendation (BUY/HOLD/SELL)
    - Risk score (0-5 scale)
23. THE Python scoring approach SHALL generate template-based rationale text:
    - Example: "BUY: Grade A- (0.82 composite score) with moderate risk (2.8/5). Strong fundamentals (ROE 22%) and positive technical momentum (SMA crossover)."
24. THE System SHALL NOT lose any quantitative data by switching from AI to Python
25. THE System SHALL trade AI prose for template-based summaries (acceptable tradeoff)

#### Acceptance Criteria - What We Lose (Acceptable)

26. THE System acknowledges losing these AI-generated outputs (low value):
    - Natural language prose (can be replaced with Jinja2 templates)
    - Generic AI statements like "strong fundamentals" (no unique insight)
    - Arbitrary confidence levels (not statistically grounded)
    - Inconsistent quality (sometimes good, often generic)
    - Occasional creative insights (rare, unpredictable, not worth 5-10 min wait)
27. THE System acknowledges these losses are acceptable because:
    - Natural language can be templated (Jinja2)
    - Generic statements provide no value
    - Confidence levels were arbitrary
    - Inconsistent quality is a bug, not a feature
    - Rare insights don't justify 10-20x performance penalty

#### Acceptance Criteria - What We Gain

28. THE Python scoring approach SHALL provide these benefits:
    - 10-20x faster execution (30 seconds vs 5-10 minutes per ticker)
    - 100% cost reduction on LLM calls for scoring ($0 vs $0.05-0.10 per ticker)
    - Deterministic results (same input = same output)
    - Fully testable (unit tests for all scoring logic)
    - Consistent quality (no AI variability)
    - Maintainable (Python code vs prompt engineering)
29. THE Python scoring approach SHALL reduce 66-holding portfolio analysis from:
    - Current: 20-40 minutes (batch mode) or 3-6 hours (sequential)
    - Target: 10-30 minutes (even without batch mode)
30. THE Python scoring approach SHALL eliminate LLM costs for calculations:
    - Current: $3.30-6.60 per 66-holding portfolio (66 × $0.05-0.10)
    - Target: $0.00 for calculations (only API data costs remain)

#### Acceptance Criteria - Hybrid Approach (Optional)

31. THE System MAY implement optional AI summary generation for natural language polish:
    - Step 1: Python calculates everything (10-30 seconds)
    - Step 2: Optional single LLM call for prose summary (5-10 seconds)
32. THE optional AI summary SHALL be configurable via environment variable:
    - `DEEP_ANALYSIS_AI_SUMMARY=true` (enable AI prose)
    - `DEEP_ANALYSIS_AI_SUMMARY=false` (use templates only, default)
33. THE optional AI summary SHALL cost $0.01 per ticker (single LLM call)
34. THE optional AI summary SHALL complete in 5-10 seconds
35. THE hybrid approach SHALL provide total time of 15-40 seconds (vs 5-10 minutes)
36. THE hybrid approach SHALL provide 80-90% cost savings ($0.01 vs $0.05-0.10)

#### Acceptance Criteria - Performance Validation

37. THE System SHALL measure and log performance metrics:
    - Execution time per ticker (Python vs AI)
    - LLM call count per ticker (Python vs AI)
    - Cost per ticker (Python vs AI)
    - Total time for 66-holding portfolio
38. THE System SHALL validate scoring consistency:
    - Python scores SHALL match AI scores within ±0.05 for composite score
    - Python grades SHALL match AI grades (same thresholds)
    - Python recommendations SHALL match AI recommendations (same logic)
39. THE System SHALL include unit tests for DeepAnalysisScorer:
    - Test composite score calculation with various inputs
    - Test grade assignment for all thresholds
    - Test recommendation logic for all scenarios
    - Test edge cases (missing data, extreme values)
40. THE System SHALL include integration tests comparing Python vs AI results:
    - Same ticker analyzed with both approaches
    - Validate scores, grades, recommendations match
    - Validate performance improvement achieved

#### Acceptance Criteria - Compliance with AI Minimalism

41. THE Python scoring approach SHALL comply with AI Minimalism steering rule:
    - "AI agents and AI tasks are tools, not the alpha and the omega"
    - "Do not overengineer using AI agents. Use vanilla Python for deterministic, rule-based tasks"
42. THE System SHALL use AI ONLY for tasks requiring reasoning:
    - ❌ NOT for calculations (Python formulas)
    - ❌ NOT for HTML generation (Jinja2 templates)
    - ❌ NOT for data validation (Pydantic models)
    - ❌ NOT for data transformation (Python functions)
    - ✅ ONLY for complex synthesis requiring judgment (optional AI summary)
43. THE System SHALL prioritize: quality > speed > cost savings (achieve all three)
44. THE System SHALL be ruthless: if Python can do it, use Python

### Requirement 19: Jinja2 Templates for Deep Analysis Reports

**User Story:** As a FinWiz developer, I want deep analysis HTML reports generated using Jinja2 templates from Python scoring results, so that report generation is instant, free, deterministic, and maintainable.

**Context:** Current deep analysis uses AI agents to generate HTML reports, which is slow (5-10 minutes), expensive ($0.05-0.10), non-deterministic, and violates AI Minimalism principle. HTML generation is a perfect use case for templates.

#### Acceptance Criteria - Template Implementation

1. THE System SHALL create Jinja2 template at `src/finwiz/templates/deep_analysis_report.html.j2`
2. THE template SHALL accept DeepAnalysisResult data as input variables
3. THE template SHALL generate professional French-language HTML report
4. THE template SHALL include sections:
   - Executive summary (Résumé Exécutif) with grade, score, recommendation
   - Key metrics (Métriques Clés) with fundamental, technical, risk scores
   - Rationale (Justification) explaining the recommendation
   - Risk assessment (Évaluation des Risques) with risk factors
   - Data sources (Sources de Données) with citations
5. THE template SHALL include professional CSS styling:
   - Light/dark mode support
   - Responsive design (mobile-friendly)
   - Color-coded grades (A+=green, F=red)
   - Professional financial styling
6. THE template SHALL use emojis strategically for visual appeal:
   - 📊 for analysis sections
   - 📈 for positive trends
   - 📉 for negative trends
   - ⚠️ for risk warnings
   - 💰 for financial metrics
7. THE template SHALL be maintainable by developers (not AI-generated)
8. THE template SHALL support all asset classes (stock, ETF, crypto)

#### Acceptance Criteria - Report Generator

9. THE System SHALL create `DeepAnalysisReportGenerator` class in `src/finwiz/reporting/deep_analysis_report_generator.py`
10. THE DeepAnalysisReportGenerator SHALL use Jinja2 Environment with FileSystemLoader
11. THE DeepAnalysisReportGenerator SHALL load template from `src/finwiz/templates/`
12. THE DeepAnalysisReportGenerator SHALL accept DeepAnalysisResult dict as input
13. THE DeepAnalysisReportGenerator SHALL render template with input data
14. THE DeepAnalysisReportGenerator SHALL return HTML string
15. THE DeepAnalysisReportGenerator SHALL complete in milliseconds (not seconds)
16. THE DeepAnalysisReportGenerator SHALL be unit-testable with mock data
17. THE DeepAnalysisReportGenerator SHALL NOT make any LLM calls
18. THE DeepAnalysisReportGenerator SHALL NOT make any external API calls

#### Acceptance Criteria - Integration with Flow

19. THE Flow SHALL call DeepAnalysisReportGenerator after Python scoring completes
20. THE Flow SHALL pass DeepAnalysisResult to report generator
21. THE Flow SHALL save generated HTML to: `output/reports/{session_id}/deep_analysis/{ticker}_report.html`
22. THE Flow SHALL NOT use AI agents for HTML generation
23. THE Flow SHALL NOT use CrewAI tasks for HTML generation
24. THE HTML generation SHALL complete in <100ms per report

#### Acceptance Criteria - Performance Comparison

25. THE Jinja2 approach SHALL be 100-1000x faster than AI HTML generation:
    - AI: 30-60 seconds per report
    - Jinja2: <100ms per report
26. THE Jinja2 approach SHALL eliminate LLM costs for HTML generation:
    - AI: $0.01-0.02 per report
    - Jinja2: $0.00 per report
27. THE Jinja2 approach SHALL produce consistent, professional output
28. THE Jinja2 approach SHALL be fully testable with unit tests

#### Acceptance Criteria - Template Quality

29. THE template SHALL produce professional-quality HTML reports
30. THE template SHALL match or exceed AI-generated report quality
31. THE template SHALL use proper French financial terminology
32. THE template SHALL include all required sections and data
33. THE template SHALL be print-friendly (CSS print styles)
34. THE template SHALL be accessible (semantic HTML, ARIA labels)

### Requirement 20: Pure Python Architecture Implementation

**User Story:** As a FinWiz developer, I want a complete pure Python architecture that replaces AI crews with deterministic Python functions, so that analysis is fast, cheap, testable, and reliable.

#### Acceptance Criteria - Portfolio Deep Analyzer

1. THE System SHALL implement `PortfolioDeepAnalyzer` class in `src/finwiz/scoring/portfolio_deep_analyzer.py`
2. THE PortfolioDeepAnalyzer SHALL analyze multiple holdings concurrently using Python threading
3. THE PortfolioDeepAnalyzer SHALL use `DeepAnalysisScorer` for all calculations
4. THE PortfolioDeepAnalyzer SHALL generate JSON exports for each holding
5. THE PortfolioDeepAnalyzer SHALL update portfolio holdings with analysis results
6. THE PortfolioDeepAnalyzer SHALL complete analysis in seconds, not minutes
7. THE PortfolioDeepAnalyzer SHALL log performance metrics (time, holdings/second, cost)

#### Acceptance Criteria - Python Report Generator

8. THE System SHALL implement `PythonReportGenerator` class in `src/finwiz/reporting/python_report_generator.py`
9. THE PythonReportGenerator SHALL use Jinja2 templates for HTML generation
10. THE PythonReportGenerator SHALL generate professional French-language reports
11. THE PythonReportGenerator SHALL include portfolio statistics and analysis summaries
12. THE PythonReportGenerator SHALL support light/dark mode with responsive design
13. THE PythonReportGenerator SHALL complete report generation in milliseconds
14. THE PythonReportGenerator SHALL be fully testable with mock data

#### Acceptance Criteria - Integration Functions

15. THE System SHALL provide `analyze_portfolio_with_python()` convenience function
16. THE System SHALL provide `generate_python_report()` convenience function
17. THE integration functions SHALL be importable and callable from Flow methods
18. THE integration functions SHALL handle all error cases gracefully
19. THE integration functions SHALL return structured results with performance metrics

#### Acceptance Criteria - Flow Integration

20. THE Flow SHALL call Python functions directly instead of executing AI crews
21. THE Flow SHALL pass portfolio holdings to `analyze_portfolio_with_python()`
22. THE Flow SHALL pass analysis results to `generate_python_report()`
23. THE Flow SHALL track execution in structured state (file paths, status, metrics)
24. THE Flow SHALL complete entire analysis pipeline in minutes, not hours

#### Acceptance Criteria - Directory Structure

25. THE System SHALL create proper output directory structure:
    - `output/stock/` for stock analysis JSON exports
    - `output/etf/` for ETF analysis JSON exports  
    - `output/crypto/` for crypto analysis JSON exports
    - `output/deep_analysis_consolidated_{session_id}.json` for consolidated results
26. THE System SHALL save final HTML report to `output/finwiz_family_financial_plan.html`
27. THE System SHALL create report manifest with all generated files
28. THE output files SHALL be accessible to backtesting and discovery systems

#### Acceptance Criteria - Performance Validation

29. THE Python architecture SHALL achieve 10-20x speed improvement over AI approach
30. THE Python architecture SHALL achieve 100% cost reduction for calculations
31. THE Python architecture SHALL produce deterministic, reproducible results
32. THE Python architecture SHALL be fully unit-testable
33. THE System SHALL log performance comparisons (Python vs AI metrics)

#### Acceptance Criteria - Demonstration Script

34. THE System SHALL include `scripts/run_python_analysis.py` demonstration script
35. THE demonstration script SHALL showcase complete Python-based analysis pipeline
36. THE demonstration script SHALL load portfolio data and run analysis
37. THE demonstration script SHALL generate reports and log performance metrics
38. THE demonstration script SHALL prove that all components work together correctly

### Requirement 21: Performance Optimization Configuration

**User Story:** As a FinWiz developer, I want configurable performance optimizations for deep analysis, so that I can balance speed, cost, and quality based on use case.

**Context:** PERFORMANCE_OPTIMIZATION_GUIDE.md documents two existing optimizations (GPT-5-mini for risk assessment, minimal tool set) that provide 20-30% speedup. Combined with Python scoring, these optimizations can achieve 10-20x overall speedup.

#### Acceptance Criteria - Configuration Options

1. THE System SHALL support environment variable configuration for optimizations:
   - `RISK_ASSESSMENT_USE_MINI=true` (use GPT-5-mini for risk assessment, default: true)
   - `USE_MINIMAL_RISK_TOOLS=true` (use minimal tool set for risk assessor, default: true)
   - `DEEP_ANALYSIS_AI_SUMMARY=false` (disable optional AI summary, default: false)
   - `DEEP_ANALYSIS_BATCH_SIZE=5` (batch size for concurrent execution, default: 5)
2. THE System SHALL log configuration status at startup
3. THE System SHALL validate configuration values
4. THE System SHALL provide sensible defaults for production use

#### Acceptance Criteria - Optimization Modes

5. THE System SHALL support three optimization modes:
   - **Maximum Speed**: Python scoring + no AI summary + GPT-5-mini + minimal tools
   - **Balanced**: Python scoring + optional AI summary + GPT-5-mini + minimal tools
   - **Baseline**: AI scoring (for comparison/debugging)
6. THE Maximum Speed mode SHALL complete in 10-30 seconds per ticker
7. THE Balanced mode SHALL complete in 15-40 seconds per ticker
8. THE Baseline mode SHALL complete in 5-10 minutes per ticker (current)

#### Acceptance Criteria - Performance Monitoring

9. THE System SHALL log performance metrics for each analysis:
    - Execution time per ticker
    - LLM call count
    - API call count
    - Cost estimate
10. THE System SHALL track cumulative metrics for portfolio analysis:
    - Total execution time
    - Total LLM calls
    - Total API calls
    - Total cost estimate
11. THE System SHALL compare actual vs baseline performance:
    - Time savings percentage
    - Cost savings percentage
    - Speedup factor (e.g., "10x faster")

#### Acceptance Criteria - Validation and Testing

12. THE System SHALL validate that optimizations maintain accuracy:
    - Scores within ±0.05 of baseline
    - Grades match baseline
    - Recommendations match baseline
13. THE System SHALL include performance regression tests:
    - Measure execution time for standard test cases
    - Alert if performance degrades >10%
    - Track performance trends over time
14. THE System SHALL document performance characteristics:
    - Expected execution time per mode
    - Expected cost per mode
    - Accuracy validation results

---

## Appendix: Implementation Failure Analysis and Corrective Action Plan

### Executive Summary

The initial implementation of the report aggregation architecture **FAILED** to deliver the promised outcomes. This document analyzes the critical failures and provides a corrective action plan based on a **PURE PYTHON FIRST** approach.

### Critical Failures Identified

#### 1. **No Speed Improvement Achieved**

- **Problem**: Despite implementing Python-based scoring, execution still takes significant time
- **Root Cause**: Deep analysis still uses AI crews (`DeepAnalysisCrew`) instead of pure Python
- **Evidence**: Log shows "Executing DeepAnalysisCrew for AAPL" - this should be pure Python
- **Impact**: No performance improvement, still 3-6 hours for portfolio analysis

#### 2. **JSON Exports Missing from Output Directory**

- **Problem**: ETF, crypto, and stock JSON exports only created in cache, not in final output
- **Root Cause**: Export functionality not properly integrated into Flow
- **Evidence**: No JSON files found in output directory, only portfolio review
- **Impact**: Downstream systems (backtesting, discovery) cannot access analysis results

#### 3. **A+ Discovery System Broken**

- **Problem**: `total_opportunities_found: 0` and `has_a_plus_analysis: False`
- **Root Cause**: A+ discovery not integrated with deep analysis results
- **Evidence**: Portfolio shows basic validation only, no deep analysis scores
- **Impact**: Users see "no opportunities" when A+ holdings actually exist

#### 4. **Backtesting Pipeline Disconnected**

- **Problem**: "Backtesting : Non exécuté / données non fournies"
- **Root Cause**: Backtesting not connected to discovery results
- **Evidence**: No backtesting data in output despite A+ candidates
- **Impact**: Missing critical backtesting analysis in final report

#### 5. **AI-Generated Reports Instead of Python Templates**

- **Problem**: Final report generated by AI instead of Python templates
- **Root Cause**: Report generation still uses AI crews
- **Evidence**: Report shows AI-generated content, not template-based output
- **Impact**: Inconsistent quality, slow generation, unnecessary LLM costs

#### 6. **Placeholder Final Report**

- **Problem**: `final_report.html` contains placeholder content
- **Root Cause**: Python-based report generation not implemented or called
- **Evidence**: Report contains generic content instead of actual analysis
- **Impact**: Users receive meaningless reports with no real insights

### Root Cause Analysis

The fundamental issue is **architectural**: the system is still using AI crews for tasks that should be pure Python functions. This violates the AI Minimalism principle and prevents achieving the promised performance improvements.

#### What Should Be Python (But Isn't)

1. **Deep Analysis Scoring** - Currently AI crew, should be `DeepAnalysisScorer` class
2. **HTML Report Generation** - Currently AI agents, should be Jinja2 templates
3. **Data Consolidation** - Currently AI crew, should be Python functions
4. **JSON Export Management** - Currently broken, should be Python file operations

#### What Should Remain AI (If Necessary)

1. **Complex Market Analysis** - Only if requiring genuine reasoning
2. **Natural Language Synthesis** - Only as optional enhancement
3. **Strategic Recommendations** - Only if requiring judgment beyond rules

### Expected Outcomes

#### Performance Improvements

- **Speed**: 10-20x faster (10-30 minutes vs 3-6 hours)
- **Cost**: 100% reduction for calculations ($0 vs $3.30-6.60)
- **Reliability**: Deterministic results (same input = same output)
- **Quality**: Consistent professional reports

#### Functional Fixes

- **JSON Exports**: Properly saved to output directories
- **A+ Discovery**: Shows actual opportunities found
- **Backtesting**: Executes when candidates available
- **Final Report**: Contains real analysis data, not placeholders

#### Architectural Benefits

- **AI Minimalism Compliance**: Use Python for deterministic tasks
- **Maintainability**: Python code is testable and debuggable
- **Scalability**: Concurrent processing handles large portfolios
- **Transparency**: All calculations are auditable

### Success Criteria

The implementation will be considered successful when:

1. ✅ Portfolio analysis completes in 10-30 minutes (not 3-6 hours)
2. ✅ JSON exports appear in output directories (not just cache)
3. ✅ A+ discovery shows actual opportunities (not 0)
4. ✅ Backtesting executes when candidates exist
5. ✅ Final report contains real data (not placeholders)
6. ✅ Total cost for calculations is $0 (not $3.30-6.60)
7. ✅ Results are deterministic and reproducible

### Conclusion

The current AI-based approach has fundamentally failed to deliver promised outcomes. A **PURE PYTHON FIRST** approach is required to achieve the performance, cost, and reliability targets. This corrective action plan provides a clear path to success by eliminating AI where deterministic calculations are sufficient and reserving AI only for tasks requiring genuine reasoning.

The key insight is: **If Python can do it, use Python. Be ruthless about eliminating unnecessary AI complexity.**


# Requirements Document: Report Data Quality Fixes

## Introduction

The financial report generation system currently produces reports with hallucinated data, fake URLs, and incomplete information. This spec addresses the root causes by fixing data generation at the source rather than post-processing validation.

## Requirements

### Requirement 1: Real Sentiment Data

**User Story:** As a financial analyst, I want sentiment analysis to use only real news sources with valid URLs, so that I can verify the information and trust the analysis.

#### Acceptance Criteria

1. WHEN sentiment analysis fetches news articles THEN it SHALL only return articles with valid, accessible URLs
2. WHEN a news source provides an invalid URL THEN the system SHALL exclude that article from analysis
3. WHEN no valid articles are available THEN the system SHALL return an empty result with clear messaging
4. IF an article URL contains forbidden patterns (example.com, test.com, etc.) THEN the system SHALL reject that article
5. WHEN sentiment data is returned THEN it SHALL include real publication dates and verifiable sources

### Requirement 2: Valid SEC Filing URLs

**User Story:** As a financial analyst, I want SEC filing citations to use current, working URLs, so that I can access the actual filings referenced in the report.

#### Acceptance Criteria

1. WHEN SEC analysis generates filing URLs THEN it SHALL use the current SEC EDGAR API format
2. WHEN a filing URL is generated THEN the system SHALL verify it returns a 200 status code
3. IF a direct filing URL is unavailable THEN the system SHALL use the company browse page URL
4. WHEN SEC citations are included THEN they SHALL include CIK number, filing type, and filing date
5. WHEN a ticker has no SEC filings THEN the system SHALL clearly state "No SEC filings available" instead of generating fake URLs

### Requirement 3: Complete Portfolio Review

**User Story:** As a portfolio manager, I want the portfolio review to include ALL my holdings from the CSV files, so that I get a complete analysis of my entire portfolio.

#### Acceptance Criteria

1. WHEN portfolio review runs THEN it SHALL process ALL holdings from stock.csv, etf.csv, and crypto.csv
2. WHEN a holding is processed THEN it SHALL be included in the final report regardless of asset class
3. IF a holding fails validation THEN it SHALL still appear in the report with a validation warning
4. WHEN the report is generated THEN it SHALL show a count of total holdings processed vs. holdings in CSV
5. WHEN holdings are missing from the report THEN the system SHALL log which holdings were excluded and why

### Requirement 4: A+ Discovery Integration

**User Story:** As an investment advisor, I want A+ opportunities to be discovered and included in reports, so that I can identify the best investment opportunities for my clients.

#### Acceptance Criteria

1. WHEN discovery crew runs THEN it SHALL save results to output/discovery/ directory
2. WHEN report crew runs THEN it SHALL load A+ opportunities from discovery results
3. IF no A+ opportunities are found THEN the report SHALL clearly state "No A+ opportunities found in current analysis"
4. WHEN A+ opportunities exist THEN they SHALL be displayed with complete data (ticker, score, grade, rationale)
5. WHEN discovery hasn't run THEN the report SHALL state "A+ discovery not run - use --discovery flag"

### Requirement 5: Complete Backtesting Metrics

**User Story:** As a quantitative analyst, I want complete backtesting metrics for all candidates, so that I can evaluate risk-adjusted returns and make informed decisions.

#### Acceptance Criteria

1. WHEN backtesting runs THEN it SHALL calculate annualized return, Sharpe ratio, Sortino ratio, Calmar ratio, max drawdown, and win rate
2. WHEN backtesting results are saved THEN they SHALL include all metrics in a structured format
3. IF a metric cannot be calculated THEN it SHALL be set to null (not "Données non disponibles")
4. WHEN report displays backtesting data THEN it SHALL show actual values or clearly mark as "Not calculated"
5. WHEN backtesting data is incomplete THEN the system SHALL log which metrics are missing and why

### Requirement 6: Data Availability Transparency

**User Story:** As a report consumer, I want to know when data is unavailable or stale, so that I can assess the reliability of the analysis.

#### Acceptance Criteria

1. WHEN data is unavailable THEN the report SHALL clearly state "Data not available" instead of generating fake data
2. WHEN data is stale (>7 days old) THEN the report SHALL include a freshness warning with the data age
3. IF a data source fails THEN the system SHALL log the failure and continue with available data
4. WHEN multiple data sources are used THEN the report SHALL list which sources provided data
5. WHEN the report is generated THEN it SHALL include a data availability summary section

## Success Criteria

- Zero hallucinated URLs in generated reports
- All SEC URLs return 200 status codes
- Portfolio review includes 100% of holdings from CSV files
- A+ opportunities displayed when discovery runs
- Backtesting metrics complete or clearly marked as unavailable
- Data availability clearly communicated in reports
# Requirements Document

## Introduction

This specification defines the integration of Supabase as the centralized data persistence and vector storage layer for FinWiz. The integration will enable historical analysis storage, semantic search capabilities, portfolio evolution tracking, and RAG-enhanced AI agents with access to past analyses.

## Glossary

- **Supabase**: Open-source Firebase alternative providing PostgreSQL database, vector storage (pgvector), and real-time subscriptions
- **Vector Embedding**: Numerical representation of text/data in multi-dimensional space for semantic similarity search
- **RAG (Retrieval-Augmented Generation)**: Pattern combining LLM with knowledge retriever to provide context and reduce hallucinations
- **pgvector**: PostgreSQL extension for vector similarity search
- **Analysis Cache**: Stored analysis results that can be reused to avoid redundant crew executions
- **Portfolio Snapshot**: Point-in-time record of portfolio holdings and their analysis results
- **Semantic Search**: Search based on meaning/context rather than exact keyword matching
- **Data Lineage**: Complete traceability of data from source to final output

## Requirements

### Requirement 1: Database Schema and Connection Management

**User Story:** As a FinWiz developer, I want a robust database schema and connection management system, so that all analysis data is reliably stored and retrievable.

#### Acceptance Criteria

1. WHEN the application starts, THE System SHALL establish a connection to Supabase using environment variables for credentials
2. WHEN the connection is established, THE System SHALL validate the database schema exists and is up-to-date
3. WHEN schema validation fails, THE System SHALL log detailed error messages and fail gracefully
4. WHERE connection pooling is enabled, THE System SHALL manage connection lifecycle with automatic retry logic
5. WHEN database operations fail, THE System SHALL implement exponential backoff retry strategy with maximum 3 attempts

### Requirement 2: Analysis Storage and Retrieval

**User Story:** As a FinWiz user, I want all my analysis results stored in a database, so that I can access historical analyses and avoid redundant computations.

#### Acceptance Criteria

1. WHEN a crew completes an analysis, THE System SHALL store the complete analysis result in the database with timestamp
2. WHEN storing an analysis, THE System SHALL include ticker, asset_class, composite_score, grade, recommendation, and full JSON export
3. WHEN retrieving an analysis, THE System SHALL check if a recent analysis exists (within configurable TTL, default 24 hours)
4. IF a recent analysis exists, THEN THE System SHALL return the cached result instead of executing the crew
5. WHEN multiple analyses exist for the same ticker, THE System SHALL return the most recent analysis by timestamp

### Requirement 3: Vector Embeddings and Semantic Search

**User Story:** As a FinWiz user, I want to search for similar analyses using natural language queries, so that I can find relevant historical insights quickly.

#### Acceptance Criteria

1. WHEN an analysis is stored, THE System SHALL generate vector embeddings for the analysis description and key findings
2. WHEN generating embeddings, THE System SHALL use OpenAI text-embedding-3-small model with 1536 dimensions
3. WHEN a user queries for similar analyses, THE System SHALL convert the query to embeddings and perform vector similarity search
4. WHEN performing vector search, THE System SHALL return the top 5 most similar analyses with similarity scores
5. WHERE similarity score is below 0.7, THE System SHALL exclude results as not sufficiently similar

### Requirement 4: Portfolio Evolution Tracking

**User Story:** As a FinWiz user, I want to track how my portfolio evolves over time, so that I can understand the impact of recommendations and decisions.

#### Acceptance Criteria

1. WHEN a portfolio analysis completes, THE System SHALL create a portfolio snapshot with timestamp and all holdings
2. WHEN creating a snapshot, THE System SHALL store each holding's ticker, quantity, current_value, grade, and recommendation
3. WHEN retrieving portfolio history, THE System SHALL return all snapshots ordered by timestamp descending
4. WHEN comparing snapshots, THE System SHALL calculate changes in holdings, grades, and total portfolio value
5. WHERE a holding appears in multiple snapshots, THE System SHALL track its grade evolution over time

### Requirement 5: RAG-Enhanced AI Agents

**User Story:** As a FinWiz developer, I want AI agents to access historical analyses through RAG, so that recommendations are grounded in past data and reduce hallucinations.

#### Acceptance Criteria

1. WHEN an agent needs context, THE System SHALL query the vector database for relevant historical analyses
2. WHEN retrieving context, THE System SHALL include the top 3 most similar analyses in the agent's prompt
3. WHEN no similar analyses exist, THE System SHALL proceed without RAG context and log the absence
4. WHERE RAG context is provided, THE Agent SHALL cite the historical analyses in its recommendations
5. WHEN RAG retrieval fails, THE System SHALL fall back to standard analysis without historical context

### Requirement 6: Analysis Cache Management

**User Story:** As a FinWiz user, I want intelligent caching of expensive analyses, so that I avoid redundant crew executions and reduce costs.

#### Acceptance Criteria

1. WHEN checking for cached analysis, THE System SHALL consider ticker, asset_class, and analysis_type as cache keys
2. WHEN a cached analysis is found, THE System SHALL validate it is within the TTL (default 24 hours)
3. IF cached analysis is expired, THEN THE System SHALL execute a new analysis and update the cache
4. WHEN cache hit occurs, THE System SHALL log the cache hit and return results in under 1 second
5. WHERE cache is disabled via configuration, THE System SHALL always execute fresh analyses

### Requirement 7: Data Migration and Backward Compatibility

**User Story:** As a FinWiz developer, I want to migrate existing file-based data to Supabase, so that historical analyses are preserved and accessible.

#### Acceptance Criteria

1. WHEN migration is triggered, THE System SHALL scan the output directory for existing JSON exports
2. WHEN processing exports, THE System SHALL validate each export against Pydantic schemas before storage
3. IF validation fails, THEN THE System SHALL log the error and skip the invalid export
4. WHEN storing migrated data, THE System SHALL preserve original timestamps from file metadata
5. WHERE duplicate analyses exist, THE System SHALL keep the most recent version by timestamp

### Requirement 8: Performance and Scalability

**User Story:** As a FinWiz user, I want database operations to be fast and scalable, so that analysis performance is not degraded by persistence.

#### Acceptance Criteria

1. WHEN storing an analysis, THE System SHALL complete the database write in under 500 milliseconds
2. WHEN retrieving an analysis, THE System SHALL complete the database read in under 200 milliseconds
3. WHEN performing vector search, THE System SHALL return results in under 1 second for queries with up to 1000 stored analyses
4. WHERE database operations exceed timeout thresholds, THE System SHALL log performance warnings
5. WHEN database is unavailable, THE System SHALL fall back to file-based storage and continue analysis

### Requirement 8.1: Non-Blocking Asynchronous Operations

**User Story:** As a FinWiz user, I want database operations to never block analysis execution, so that Supabase integration cannot slow down or fail my analyses.

#### Acceptance Criteria

1. WHEN an analysis completes, THE System SHALL store results to Supabase asynchronously in a background task
2. WHEN background storage fails, THE System SHALL log the error but NOT fail the analysis
3. WHEN checking for cached analysis, THE System SHALL set a strict timeout of 2 seconds for database query
4. IF cache check times out, THEN THE System SHALL proceed with fresh analysis as if no cache exists
5. WHERE Supabase is unavailable, THE System SHALL detect this within 5 seconds and disable database operations for the session

### Requirement 8.2: Circuit Breaker Pattern

**User Story:** As a FinWiz developer, I want automatic circuit breaker protection, so that repeated database failures don't impact system performance.

#### Acceptance Criteria

1. WHEN database operations fail 3 consecutive times, THE System SHALL open the circuit breaker
2. WHILE circuit breaker is open, THE System SHALL skip all database operations and use file-based storage
3. WHEN circuit breaker is open for 5 minutes, THE System SHALL attempt to close it with a test query
4. IF test query succeeds, THEN THE System SHALL close the circuit breaker and resume database operations
5. WHERE circuit breaker opens, THE System SHALL log a warning but continue analysis without interruption

### Requirement 9: Security and Data Privacy

**User Story:** As a FinWiz user, I want my financial data to be securely stored and protected, so that sensitive information is not exposed.

#### Acceptance Criteria

1. WHEN connecting to Supabase, THE System SHALL use environment variables for credentials and never hardcode secrets
2. WHEN storing portfolio data, THE System SHALL encrypt sensitive fields (holdings, values) at rest
3. WHEN accessing data, THE System SHALL implement row-level security policies to restrict access
4. WHERE API keys are logged, THE System SHALL mask all but the first 8 characters
5. WHEN data is deleted, THE System SHALL perform soft deletes with retention policies

### Requirement 10: Monitoring and Observability

**User Story:** As a FinWiz developer, I want comprehensive monitoring of database operations, so that I can diagnose issues and optimize performance.

#### Acceptance Criteria

1. WHEN database operations execute, THE System SHALL log operation type, duration, and success/failure status
2. WHEN errors occur, THE System SHALL log detailed error messages with stack traces
3. WHEN cache hits occur, THE System SHALL track cache hit rate and log statistics
4. WHERE performance degrades, THE System SHALL emit warnings when operations exceed thresholds
5. WHEN vector search is performed, THE System SHALL log query text, result count, and similarity scores

## Constraints

- **Zero Impact on Analysis**: Supabase integration MUST NOT slow down or fail analyses
- **Asynchronous by Default**: All write operations must be non-blocking background tasks
- **Strict Timeouts**: Read operations have 2-second timeout, writes have 5-second timeout
- **Circuit Breaker**: Automatic protection after 3 consecutive failures
- **Graceful Degradation**: System must function perfectly without database
- **Optional Feature**: Supabase can be disabled via environment variable (SUPABASE_ENABLED=false)
- **Vector Embeddings**: Use OpenAI text-embedding-3-small (1536 dimensions) for consistency
- **Cache TTL**: Configurable via environment variable (default 24 hours)
- **Row-Level Security**: Database schema must support future multi-user access
- **Data Lineage**: All stored data must comply with lineage standards (source attribution, timestamps)
- **Idempotent Migration**: Running migration multiple times should not create duplicates
- **Performance Target**: Database operations should add < 500ms to analysis time (mostly async)

## Success Metrics

- **Zero Slowdown**: Analysis time with Supabase ≤ analysis time without Supabase + 500ms
- **Zero Failures**: Database issues cause 0% increase in analysis failures
- **Cache Hit Rate**: Target 40%+ cache hit rate for repeated analyses
- **Cost Reduction**: Reduce API costs by 30%+ through analysis reuse
- **Circuit Breaker**: < 5 seconds to detect and disable failing database
- **Reliability**: 99.9% uptime for database operations with graceful fallback
- **Adoption**: 100% of analyses stored in database within 1 month of deployment
- **Search Quality**: Semantic search returns relevant results with 80%+ user satisfaction
- **Background Success**: 95%+ of async writes succeed without blocking analysis

---

**Version**: 1.0  
**Created**: 2025-10-30  
**Status**: Requirements Gathering
# Requirements Document: Supabase Timeout Fix

## Introduction

The Supabase integration is experiencing 100% timeout failures on all database operations, causing the circuit breaker to open and preventing any caching functionality. This document defines requirements to make Supabase completely optional and ensure graceful degradation when unavailable.

## Glossary

- **Supabase**: PostgreSQL database service used for caching analysis results
- **Circuit Breaker**: Pattern that prevents repeated failed operations
- **Graceful Degradation**: System continues functioning when optional components fail
- **Timeout**: Maximum time allowed for a database operation before failing

## Requirements

### Requirement 1: Graceful Degradation

**User Story:** As a FinWiz user, I want the system to work normally even when Supabase is unavailable, so that I can still get portfolio analysis results.

#### Acceptance Criteria

1. WHEN Supabase operations timeout, THE System SHALL continue analysis without caching
2. WHEN Supabase is unavailable, THE System SHALL log warnings but not errors
3. WHEN all Supabase operations fail, THE System SHALL complete the full analysis workflow
4. WHEN circuit breaker opens, THE System SHALL stop attempting Supabase operations
5. THE System SHALL NOT block or delay analysis waiting for Supabase responses

### Requirement 2: Timeout Configuration

**User Story:** As a system administrator, I want configurable timeouts for Supabase operations, so that I can tune performance based on network conditions.

#### Acceptance Criteria

1. THE System SHALL support SUPABASE_TIMEOUT_SECONDS environment variable
2. THE System SHALL default to 10 seconds for read operations
3. THE System SHALL default to 15 seconds for write operations  
4. WHEN timeout is reached, THE System SHALL log the timeout and continue
5. THE System SHALL NOT retry timed-out operations more than 3 times

### Requirement 3: Initialization Validation

**User Story:** As a developer, I want to validate Supabase connectivity at startup, so that I know immediately if caching will work.

#### Acceptance Criteria

1. WHEN System starts, THE System SHALL test Supabase connectivity with a simple query
2. WHEN connectivity test fails, THE System SHALL log a warning and disable caching
3. WHEN connectivity test succeeds, THE System SHALL enable caching features
4. THE System SHALL complete startup within 5 seconds regardless of Supabase status
5. THE System SHALL NOT fail startup if Supabase is unavailable

### Requirement 4: Monitoring and Metrics

**User Story:** As a system administrator, I want visibility into Supabase performance, so that I can diagnose connectivity issues.

#### Acceptance Criteria

1. THE System SHALL log Supabase operation success/failure rates
2. THE System SHALL track average response times for Supabase operations
3. WHEN circuit breaker opens, THE System SHALL log the failure count and reason
4. THE System SHALL expose Supabase health status via metrics endpoint
5. THE System SHALL log Supabase configuration (URL, timeout settings) at startup

### Requirement 5: Fallback Behavior

**User Story:** As a FinWiz user, I want consistent analysis results whether caching works or not, so that I can trust the recommendations.

#### Acceptance Criteria

1. WHEN cache is unavailable, THE System SHALL perform full analysis for all holdings
2. WHEN cache read fails, THE System SHALL proceed with fresh analysis
3. WHEN cache write fails, THE System SHALL complete analysis and log the failure
4. THE System SHALL NOT use stale cached data older than 24 hours
5. THE System SHALL provide the same analysis quality with or without caching
# Requirements Document

## Introduction

This specification defines a comprehensive approach to improve code coverage and stabilize the test suite for the FinWiz financial analysis platform. The current test suite has significant issues including import errors, mocking inconsistencies, JSON serialization failures, and poor test isolation that prevent reliable testing and accurate coverage measurement.

The improvements will focus on fixing broken tests, standardizing mocking patterns, resolving serialization issues, improving test isolation, and establishing comprehensive coverage measurement. This work is critical for maintaining code quality and enabling confident deployments.

## Requirements

### Requirement 1: Fix Critical Test Import and Module Errors

**User Story:** As a developer, I want all tests to import successfully and run without module errors, so that I can execute the full test suite and measure accurate coverage.

#### Acceptance Criteria

1. WHEN running pytest THEN all test files SHALL import successfully without ImportError exceptions
2. WHEN tests reference missing classes or functions THEN they SHALL be updated to use correct import paths
3. WHEN quantitative module tests fail with missing classes THEN the missing classes SHALL be implemented or tests updated
4. WHEN A+ monitoring tests fail with missing enums THEN the missing enums SHALL be added to the appropriate modules
5. WHEN crew tests fail with missing attributes THEN the test mocking SHALL be corrected to match actual module structure

### Requirement 2: Standardize Test Mocking with pytest-mock

**User Story:** As a developer, I want all tests to use pytest-mock consistently, so that mocking behavior is predictable and maintainable across the codebase.

#### Acceptance Criteria

1. WHEN tests use unittest.mock THEN they SHALL be converted to use pytest-mock exclusively
2. WHEN mocking external API calls THEN tests SHALL use the mocker fixture with proper return values
3. WHEN mocking class methods THEN tests SHALL use mocker.patch with correct target paths
4. WHEN tests need to mock attributes THEN they SHALL use mocker.patch.object for proper attribute mocking
5. WHEN async operations are mocked THEN tests SHALL use pytest-asyncio with proper async mocking patterns

### Requirement 3: Resolve JSON Serialization Issues

**User Story:** As a developer, I want all data objects to serialize properly to JSON, so that integration tests and data persistence work correctly.

#### Acceptance Criteria

1. WHEN UsageMetrics objects are serialized THEN they SHALL convert to JSON without TypeError exceptions
2. WHEN datetime objects are included in serialization THEN they SHALL be converted to ISO format strings
3. WHEN Pydantic models are serialized THEN they SHALL use model_dump() with proper serialization modes
4. WHEN CrewAI objects contain non-serializable data THEN custom serializers SHALL be implemented
5. WHEN integration manager stores crew output THEN all data SHALL serialize successfully to JSON files

### Requirement 4: Improve Test Isolation and Performance

**User Story:** As a developer, I want tests to run independently and complete quickly, so that I can run the test suite frequently during development.

#### Acceptance Criteria

1. WHEN tests are executed THEN each test SHALL run independently without shared state dependencies
2. WHEN external services are called THEN all API calls SHALL be mocked to prevent network dependencies
3. WHEN tests run THEN they SHALL complete in under 5 seconds per test suite as specified in quality standards
4. WHEN long-running operations are tested THEN they SHALL use mocked responses instead of actual execution
5. WHEN CrewAI agents are tested THEN LLM calls SHALL be mocked to prevent expensive API usage

### Requirement 5: Establish Comprehensive Code Coverage Measurement

**User Story:** As a developer, I want accurate code coverage reporting, so that I can identify untested code and improve overall test quality.

#### Acceptance Criteria

1. WHEN coverage is measured THEN it SHALL exclude test files and focus only on src/finwiz modules
2. WHEN coverage reports are generated THEN they SHALL show line-by-line coverage with missing lines identified
3. WHEN coverage is below 80% THEN specific areas needing additional tests SHALL be identified and prioritized
4. WHEN new code is added THEN coverage SHALL not decrease below the current baseline
5. WHEN coverage reports are generated THEN they SHALL be available in both terminal and HTML formats

### Requirement 6: Fix Crew Test Architecture Issues

**User Story:** As a developer, I want crew tests to properly mock CrewAI components, so that crew functionality can be tested without executing actual AI agents.

#### Acceptance Criteria

1. WHEN crew tests run THEN they SHALL mock agent creation and execution without calling LLM APIs
2. WHEN crew configurations are tested THEN YAML config loading SHALL be mocked with test data
3. WHEN crew tools are tested THEN tool injection SHALL be mocked to verify correct tool assignment
4. WHEN crew processes are tested THEN the sequential/hierarchical process SHALL be verified without execution
5. WHEN crew outputs are tested THEN Pydantic model validation SHALL be tested with mock data

### Requirement 7: Implement Robust Error Handling in Tests

**User Story:** As a developer, I want tests to handle errors gracefully and provide clear failure messages, so that debugging test failures is efficient.

#### Acceptance Criteria

1. WHEN tests fail THEN error messages SHALL clearly indicate the specific assertion that failed
2. WHEN mocks are not called as expected THEN tests SHALL provide detailed information about actual vs expected calls
3. WHEN serialization fails THEN tests SHALL capture and display the problematic data structure
4. WHEN import errors occur THEN tests SHALL provide clear guidance on missing dependencies or modules
5. WHEN async operations fail THEN tests SHALL properly handle and report async exceptions

### Requirement 8: Create Test Data Factories and Fixtures

**User Story:** As a developer, I want reusable test data and fixtures, so that tests are consistent and maintainable.

#### Acceptance Criteria

1. WHEN tests need financial data THEN they SHALL use Faker library to generate realistic test data
2. WHEN tests need API responses THEN they SHALL use predefined fixtures with realistic response structures
3. WHEN tests need Pydantic models THEN they SHALL use factory functions that create valid model instances
4. WHEN tests need crew configurations THEN they SHALL use fixture files with valid YAML structures
5. WHEN tests need mock objects THEN they SHALL use centralized fixture definitions to ensure consistency

### Requirement 9: Establish Test Categories and Execution Strategy

**User Story:** As a developer, I want to run different types of tests separately, so that I can execute fast unit tests during development and slower integration tests in CI.

#### Acceptance Criteria

1. WHEN running unit tests THEN they SHALL execute with pytest markers to exclude integration tests
2. WHEN running integration tests THEN they SHALL be clearly marked and run separately from unit tests
3. WHEN running performance tests THEN they SHALL have appropriate timeouts and resource limits
4. WHEN running all tests THEN the execution SHALL be organized by test type with clear reporting
5. WHEN tests are categorized THEN the test execution time SHALL be optimized for developer workflow

### Requirement 10: Implement Continuous Coverage Monitoring

**User Story:** As a developer, I want coverage to be monitored continuously, so that coverage regressions are caught early in the development process.

#### Acceptance Criteria

1. WHEN code is committed THEN coverage SHALL be measured and compared to the previous baseline
2. WHEN coverage decreases THEN the developer SHALL be notified with specific files and lines affected
3. WHEN new modules are added THEN they SHALL have minimum 70% test coverage before merging
4. WHEN critical modules are modified THEN they SHALL maintain 90% test coverage
5. WHEN coverage reports are generated THEN they SHALL be stored for historical tracking and trend analysis
