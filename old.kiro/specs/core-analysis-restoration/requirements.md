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
