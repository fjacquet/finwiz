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
