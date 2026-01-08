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
