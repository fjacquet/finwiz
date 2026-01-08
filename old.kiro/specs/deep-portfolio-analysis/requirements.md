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
