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