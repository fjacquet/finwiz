# Requirements Document

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