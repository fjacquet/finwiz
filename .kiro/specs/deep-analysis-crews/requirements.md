# Requirements Document: Deep Analysis Crews for Single-Ticker Analysis

> **⚠️ SUPERSEDED**: This spec described the original 3-agent design. The implementation was simplified to 2 agents (asset_analyst, investment_reporter) during Python/AI Hybrid refactoring. See `.kiro/specs/python-ai-hybrid-analysis/` for current architecture.

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
