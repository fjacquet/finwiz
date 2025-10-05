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
