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
