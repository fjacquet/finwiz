# Design Document: Unified Deep Analysis Crew for Single-Ticker Analysis

## Overview

This design document specifies the technical architecture for **ONE unified CrewAI crew** (`DeepAnalysisCrew`) optimized for single-ticker deep analysis across all asset classes: stocks, ETFs, and cryptocurrencies. This crew handles all asset types through dynamic tool routing based on the `asset_class` parameter, eliminating code duplication and providing a single source of truth for deep analysis logic.

**Design Principles:**
1. **Unix Philosophy:** One task (analyze single ticker), one outcome (comprehensive analysis)
2. **No Duplication:** One crew handles all asset classes through dynamic tool routing
3. **Accuracy First:** Fresh data for real money decisions (never sacrifice accuracy for cost)
4. **Reasoning Enabled:** Clear task descriptions prevent infinite loops
5. **Smart API Usage:** Tool-level batching and context sharing minimize redundant calls without sacrificing accuracy
6. **Dynamic Routing:** Tools selected based on asset_class parameter at runtime

## Architecture Overview

### High-Level Structure

```
Flow Orchestrator (analyze_holdings_deep)
    ↓
    DeepAnalysisCrew (ONE unified crew for all asset classes)
    ├─ Input: ticker="AAPL", asset_class="stock"
    ├─ Input: ticker="VOO", asset_class="etf"
    └─ Input: ticker="BTC", asset_class="crypto"
         ↓
         Dynamic Tool Selection: get_tools_for_asset_class(asset_class)
         ├─ stock → get_stock_crew_tools()
         ├─ etf → get_etf_crew_tools()
         └─ crypto → get_crypto_crew_tools()
         ↓
         Output: DeepAnalysisResult (ticker, grade, scores, data_freshness)
```

### Component Structure

```
src/finwiz/crews/deep_analysis/
├── deep_analysis.py           # Main crew class with dynamic tool routing
└── config/
    ├── agents.yaml            # 3 agents: asset_analyst, risk_assessor, investment_reporter
    └── tasks.yaml             # 4 tasks: deep_analysis, technical_analysis, risk_assessment, final_report
```

**Key Design Decision:** Single crew implementation with dynamic tool routing eliminates the need for three separate crews (StockDeepAnalysisCrew, EtfDeepAnalysisCrew, CryptoDeepAnalysisCrew), reducing code duplication and maintenance burden.

## Detailed Design

### 1. Unified Crew Structure

**One Crew for All Asset Classes:**

| Crew Name | Directory | Purpose |
|-----------|-----------|---------|
| `DeepAnalysisCrew` | `src/finwiz/crews/deep_analysis/` | Single ticker analysis for ANY asset class (stock/ETF/crypto) |

**Required Inputs:**
- `ticker`: The ticker symbol to analyze (e.g., "AAPL", "VOO", "BTC") - REQUIRED
- `asset_class`: The asset type ("stock", "etf", "crypto") - REQUIRED for tool routing

**Dynamic Tool Routing Implementation:**
```python
def get_tools_for_asset_class(self, asset_class: str) -> list:
    """Route to appropriate tool set based on asset class.
    
    Args:
        asset_class: One of "stock", "etf", "crypto"
        
    Returns:
        List of tools appropriate for the asset class
        
    Raises:
        ValueError: If asset_class is not valid
    """
    if asset_class.lower() == "stock":
        return get_stock_crew_tools(
            include_rag=True,
            include_quantitative=True,
            collection_suffix="stock_deep"
        )
    elif asset_class.lower() == "etf":
        return get_etf_crew_tools(
            include_rag=True,
            include_quantitative=True,
            collection_suffix="etf_deep"
        )
    elif asset_class.lower() == "crypto":
        return get_crypto_crew_tools(
            include_rag=True,
            include_quantitative=True,
            collection_suffix="crypto_deep"
        )
    else:
        raise ValueError(
            f"Invalid asset_class: {asset_class}. "
            f"Must be one of: stock, etf, crypto"
        )
```

**Design Rationale:** Dynamic tool routing allows a single crew implementation to handle all asset classes, eliminating code duplication while maintaining asset-specific analysis capabilities. The `asset_class` parameter acts as a routing key to select the appropriate tool set at runtime.

### 2. Agent Architecture

The unified crew has **3 agents** with consistent roles across all asset classes:

#### Agent 1: Asset Analyst

**Role:** Deep analysis specialist (adapts to asset class)
**Responsibilities:**
- Validate ticker existence on appropriate exchange
- Fetch and analyze asset-specific data (fundamentals/factsheet/on-chain)
- Perform technical analysis (RSI, MACD, Bollinger Bands)
- Calculate quantitative metrics (volatility, Sharpe ratio, asset-specific metrics)
- Generate comprehensive analysis conforming to asset-specific schemas

**Tools:** Dynamic tool set via `get_tools_for_asset_class(asset_class)` method
**Reasoning:** Enabled (`reasoning=True`) with clear single-ticker task descriptions

#### Agent 2: Risk Assessor

**Role:** Risk evaluation specialist
**Responsibilities:**
- Assess market, liquidity, credit, structural risks
- Calculate standardized risk scores (0-5 scale)
- Generate risk mitigation recommendations
- Produce RiskAssessmentStandardized output

**Tools:** Risk-focused tool subset

#### Agent 3: Investment Reporter (FINAL REPORTER)

**Role:** Consolidate findings and generate final report
**Responsibilities:**
- Consume analysis from previous tasks via context (NO external tool calls)
- Synthesize findings into coherent report
- Calculate composite score: `(fundamental_score + technical_score + (1 - risk_score)) / 3`
- Assign grade based on composite score (A+ ≥0.95, A ≥0.85, B ≥0.75, C ≥0.65, D ≥0.55, F <0.55)
- Generate unified `DeepAnalysisResult` output with data freshness timestamps

**Tools:** **EMPTY LIST** (`tools=[]`) - NO EXTERNAL CALLS (ENFORCED)
**Decorator:** `@final_reporter` to enforce empty tools and prevent external API calls
**Reasoning:** Enabled (`reasoning=True`) but operates only on context data

**Design Rationale:** The final reporter must have an empty tools list to ensure it consolidates existing analysis rather than making redundant API calls. The `@final_reporter` decorator enforces this constraint at the framework level.

### 3. Task Architecture

Each crew has **4 tasks** in sequential order:


#### Task 1: Deep Analysis Task

**Agent:** Asset Analyst
**Purpose:** Comprehensive analysis of the provided ticker
**Key Activities:**
- Validate ticker with `TickerValidationTool`
- Fetch asset-specific data (fundamentals/factsheet/on-chain)
- Analyze current market conditions
- Calculate performance metrics

**Output:** Asset-specific analysis object
**Async:** `true` (I/O-bound)

#### Task 2: Technical Analysis Task

**Agent:** Asset Analyst
**Purpose:** Technical indicators and chart analysis
**Key Activities:**
- Fetch technical indicators (RSI, MACD, Bollinger Bands) via batch API
- Identify support/resistance levels
- Analyze price trends and momentum
- Generate buy/sell signals

**Output:** Technical analysis with indicators
**Async:** `true` (I/O-bound)
**Depends On:** Task 1 (uses ticker validation from context)

#### Task 3: Risk Assessment Task

**Agent:** Risk Assessor
**Purpose:** Standardized risk evaluation
**Key Activities:**
- Calculate risk scores across categories
- Assess volatility and drawdown metrics
- Evaluate sentiment and market risks
- Generate mitigation recommendations

**Output:** `RiskAssessmentStandardized`
**Async:** `true` (I/O-bound)
**Depends On:** Task 1, Task 2 (uses analysis from context)

#### Task 4: Final Report Generation Task

**Agent:** Investment Reporter (FINAL REPORTER)
**Purpose:** Consolidate all findings and generate final output
**Key Activities:**
- Consume analysis, technical, and risk data from context
- Calculate composite score from fundamental, technical, and risk scores
- Assign grade (A+ to F) based on composite score
- Generate DeepAnalysisResult with all metadata

**Output:** `DeepAnalysisResult`
**Async:** `false` (final task, must be synchronous per CrewAI)
**Depends On:** Task 1, Task 2, Task 3 (consolidates all previous work)
**Tools:** **EMPTY** - NO TOOLS (enforced by `@final_reporter` decorator)


### 4. Data Models and Schemas

#### Output Schema Structure

Each crew returns a standardized output compatible with the grading system:

```python
class DeepAnalysisResult(BaseModel):
    """Standardized output for deep analysis crews."""
    ticker: str
    asset_class: str  # "stock", "etf", "crypto"
    crew_name: str
    analyzed_at: datetime
    
    # Scores (0.0 to 1.0)
    fundamental_score: float
    technical_score: float
    risk_score: float
    composite_score: float
    
    # Grade (A+ to F)
    grade: str
    
    # Metadata
    cached: bool = False
    data_freshness: Dict[str, datetime]  # Timestamps per data source
```

#### Asset-Specific Schemas (Reuse Existing)

**Stock:**
- `TenKInsight` - Fundamental analysis from SEC filings
- `MarketSentiment` - Sentiment analysis
- `RiskAssessmentStandardized` - Risk evaluation

**ETF:**
- `ETFFactsheet` - Factsheet data
- `ETFTechnicalAnalysis` - Technical indicators
- `RiskAssessmentStandardized` - Risk evaluation

**Crypto:**
- `CryptoThesis` - Investment thesis
- `CryptoTechnicalAnalysis` - Technical indicators
- `RiskAssessmentStandardized` - Risk evaluation


### 5. Tool Assignment Strategy

#### Dynamic Tool Routing

The unified crew uses dynamic tool routing based on asset_class parameter:

```python
def get_tools_for_asset_class(self, asset_class: str) -> list:
    """Route to appropriate tool set based on asset class.
    
    Args:
        asset_class: One of "stock", "etf", "crypto"
        
    Returns:
        List of tools appropriate for the asset class
        
    Raises:
        ValueError: If asset_class is not valid
    """
    if asset_class.lower() == "stock":
        return get_stock_crew_tools(
            include_rag=True,
            include_quantitative=True,
            collection_suffix="stock_deep"
        )
    elif asset_class.lower() == "etf":
        return get_etf_crew_tools(
            include_rag=True,
            include_quantitative=True,
            collection_suffix="etf_deep"
        )
    elif asset_class.lower() == "crypto":
        return get_crypto_crew_tools(
            include_rag=True,
            include_quantitative=True,
            collection_suffix="crypto_deep"
        )
    else:
        raise ValueError(
            f"Invalid asset_class: {asset_class}. "
            f"Must be one of: stock, etf, crypto"
        )
```

**Design Rationale:** Dynamic tool routing allows a single crew implementation to handle all asset classes, eliminating code duplication while maintaining asset-specific analysis capabilities. The `asset_class` parameter acts as a routing key to select the appropriate tool set at runtime.

#### Required Tools by Asset Class

**Stock Tools (via get_stock_crew_tools):**
- `EnhancedSECAnalysisTool` - 10-K/10-Q filings analysis
- `QuantitativeAnalysisTool(asset_class="stock")` - Quantitative metrics
- `TickerValidationTool` - Ticker existence verification
- `YahooFinanceNewsTool` - Company news
- `StandardizedSentimentTool` - Market sentiment
- `TwelveDataIndicatorTool` - Technical indicators
- RAG tools - Knowledge base integration

**ETF Tools (via get_etf_crew_tools):**
- `EnhancedETFAnalysisTool` - Factsheet data
- `QuantitativeAnalysisTool(asset_class="etf")` - Quantitative metrics
- `TickerValidationTool` - Ticker existence verification
- `ETFTrackingAnalysisTool` - Tracking error analysis
- `StandardizedSentimentTool` - Market sentiment
- `TwelveDataIndicatorTool` - Technical indicators
- RAG tools - Knowledge base integration

**Crypto Tools (via get_crypto_crew_tools):**
- `EnhancedCryptoAnalysisTool` - On-chain metrics
- `QuantitativeAnalysisTool(asset_class="crypto")` - Quantitative metrics
- `TickerValidationTool` - Ticker existence verification (Coinbase)
- `CoinMarketCapTool` - Market data
- `StandardizedSentimentTool` - Market sentiment
- `TwelveDataIndicatorTool` - Technical indicators
- RAG tools - Knowledge base integration

#### Tool Usage Patterns

**Smart Batching (Tool-Level):**
```python
# ✅ Efficient: Batch indicator fetch
indicators = TwelveDataIndicatorTool.fetch_multiple(
    ticker="AAPL",
    indicators=["RSI", "MACD", "BB"]
)  # 1 API call

# ❌ Inefficient: Individual fetches
rsi = TwelveDataIndicatorTool.fetch("AAPL", "RSI")
macd = TwelveDataIndicatorTool.fetch("AAPL", "MACD")
bb = TwelveDataIndicatorTool.fetch("AAPL", "BB")
# 3 API calls
```

**Context Sharing (Crew-Level) with Freshness Validation:**
```python
# Task 1: Fetch and store with timestamp
price_data = YahooFinanceTool.get_price("AAPL")
context["price_data"] = {
    "data": price_data,
    "timestamp": datetime.now()
}

# Task 2: Reuse from context if fresh, otherwise re-fetch
def is_fresh(timestamp, max_age_minutes=5):
    return (datetime.now() - timestamp).total_seconds() < (max_age_minutes * 60)

if "price_data" in context and is_fresh(context["price_data"]["timestamp"]):
    price_data = context["price_data"]["data"]  # Reuse fresh data
else:
    price_data = YahooFinanceTool.get_price("AAPL")  # Re-fetch if stale
    context["price_data"] = {"data": price_data, "timestamp": datetime.now()}
```

**Design Rationale:** Context sharing minimizes redundant API calls, but freshness validation ensures we never use stale data for real money decisions. Accuracy is prioritized over cost savings.

#### API Efficiency Principles (Requirement 11)

**Priority Order:**
1. **Accuracy First** - Never sacrifice data freshness for cost savings
2. **Smart Batching** - Use tool-level batching when available
3. **Context Sharing** - Pass data between tasks to avoid re-fetching
4. **Parallel I/O** - Use async execution for independent data fetching
5. **Avoid Waste** - Don't call reasoning loops that waste tokens

**Acceptable Optimizations:**
- ✅ Caching company fundamentals (changes slowly)
- ✅ Batching indicator requests (same freshness, fewer calls)
- ✅ Sharing data between tasks via context (same execution)

**NOT Acceptable:**
- ❌ Using 24-hour cached prices for buy/sell decisions
- ❌ Using stale sentiment data for risk assessment
- ❌ Skipping data fetches to save costs

**Monitoring Requirements:**
- Log API call counts per ticker
- Log data freshness metrics (% fresh vs cached)
- Log execution time breakdown by task
- Identify optimization opportunities


### 6. Error Handling and Validation

#### Input Validation (Requirement 8)

**Ticker Validation:**
```python
def validate_inputs(ticker: str, asset_class: str) -> None:
    """Validate crew inputs before execution.
    
    Raises:
        ValueError: If ticker is missing or asset_class is invalid
    """
    if not ticker:
        raise ValueError("Ticker parameter is required for deep analysis")
    
    if asset_class.lower() not in ["stock", "etf", "crypto"]:
        raise ValueError(
            f"Invalid asset_class: {asset_class}. "
            f"Must be one of: stock, etf, crypto"
        )
```

#### Graceful Degradation

**Data Source Fallback:**
```python
def fetch_with_fallback(ticker: str, primary_tool, fallback_tool):
    """Attempt primary data source, fall back to secondary if it fails."""
    try:
        return primary_tool.fetch(ticker)
    except Exception as e:
        logger.warning(f"Primary source failed for {ticker}: {e}")
        try:
            return fallback_tool.fetch(ticker)
        except Exception as e2:
            logger.error(f"Fallback source also failed for {ticker}: {e2}")
            raise
```

**Partial Results with Confidence Flags:**
```python
class PartialAnalysisResult(BaseModel):
    """Analysis result with completeness indicators."""
    ticker: str
    asset_class: str
    composite_score: Optional[float] = None
    grade: Optional[str] = None
    
    # Completeness flags
    has_fundamental_data: bool = False
    has_technical_data: bool = False
    has_risk_assessment: bool = False
    
    # Confidence based on data completeness
    confidence_level: float = Field(..., ge=0.0, le=1.0)
    missing_data_reasons: List[str] = []
```

#### Error Logging

**Detailed Error Context:**
```python
try:
    result = crew.kickoff(inputs={"ticker": ticker, "asset_class": asset_class})
except Exception as e:
    logger.error(
        f"Deep analysis failed for {ticker} ({asset_class})",
        extra={
            "ticker": ticker,
            "asset_class": asset_class,
            "error_type": type(e).__name__,
            "error_message": str(e),
            "traceback": traceback.format_exc()
        },
        exc_info=True
    )
    raise
```

#### Preventing Infinite Loops

**Reasoning Loop Detection:**
- Task descriptions explicitly state "SINGLE TICKER MODE"
- No "top 10" language in task descriptions
- Clear input parameters in task descriptions
- Timeout configurations to prevent hangs

**Design Rationale:** Clear error messages and graceful degradation ensure the system remains operational even when individual data sources fail. Detailed logging enables quick diagnosis and resolution of issues.

### 7. Task Descriptions (Reasoning-Compatible)

#### Critical Design Element

Task descriptions must explicitly state "analyze the provided ticker" to prevent reasoning agents from requesting "10 tickers" or entering infinite loops. This is the PRIMARY fix for the 3-6 hour hang issue.

**Design Rationale:** The existing discovery crews have "top 10" language throughout their task descriptions, which causes reasoning agents to expect multiple tickers. By explicitly stating "SINGLE TICKER MODE" and repeating "{ticker}" throughout the description, we prevent the reasoning agent from requesting additional inputs.

**Example (Unified Deep Analysis Task with Dynamic Asset Class):**

```yaml
deep_analysis_task:
  description: >
    Perform comprehensive analysis of the provided {asset_class} ticker: {ticker}
    
    SINGLE TICKER MODE: You are analyzing ONE specific {asset_class}, not screening multiple assets.
    
    CRITICAL: The ticker {ticker} is provided as input. Do NOT request additional tickers.
    
    Analysis Steps for {asset_class}:
    1. Validate the provided ticker {ticker} using TickerValidationTool
    2. Fetch {asset_class}-specific data for {ticker} using appropriate tools
    3. Analyze current market conditions for {ticker}
    4. Calculate performance metrics for {ticker}
    5. Generate comprehensive analysis for {ticker}
    
    Asset Class: {asset_class}
    Today's date: {full_date}
    
    OUTPUT: Return structured analysis for the single ticker {ticker}
```

**Key Phrases (REQUIRED in all task descriptions):**
- "the provided ticker: {ticker}"
- "SINGLE TICKER MODE"
- "Do NOT request additional tickers"
- "for {ticker}" (repeated throughout)
- "{asset_class}" (to adapt description based on asset type)

**Anti-Pattern to Avoid:**
- ❌ "screen and identify the top 10 assets"
- ❌ "analyze multiple tickers"
- ❌ "provide a list of tickers"

### 8. Performance and Data Freshness Requirements

#### Performance Targets (Requirement 7)

**Execution Time:**
- Single ticker analysis: < 5 minutes
- Async tasks for I/O-bound operations
- Parallel execution where possible
- Rate limiting: max_rpm=20

**Async Configuration:**
```yaml
# config/tasks.yaml
deep_analysis_task:
  async_execution: true  # I/O-bound

technical_analysis_task:
  async_execution: true  # I/O-bound

risk_assessment_task:
  async_execution: true  # I/O-bound

final_report_task:
  async_execution: false  # Must be synchronous (CrewAI requirement)
```

#### Data Freshness (CRITICAL - Requirement 7)

**Freshness Validation:**
```python
def validate_data_freshness(data_timestamp: datetime, max_age_minutes: int = 5) -> bool:
    """Validate that data is fresh enough for real money decisions.
    
    Args:
        data_timestamp: When the data was fetched
        max_age_minutes: Maximum acceptable age in minutes
        
    Returns:
        True if data is fresh, False if stale
    """
    age_seconds = (datetime.now() - data_timestamp).total_seconds()
    return age_seconds < (max_age_minutes * 60)
```

**Data Freshness Thresholds:**
- Market prices: 5 minutes maximum
- Technical indicators: 5 minutes maximum
- Sentiment data: 15 minutes maximum
- Company fundamentals: 24 hours maximum
- SEC filings: 7 days maximum (static data)

**Freshness Reporting:**
```python
class DeepAnalysisResult(BaseModel):
    # ... other fields ...
    
    data_freshness: Dict[str, datetime] = Field(
        ...,
        description="Timestamps per data source for transparency"
    )
    
    # Example:
    # {
    #     "price_data": datetime(2025, 1, 11, 10, 30),
    #     "technical_indicators": datetime(2025, 1, 11, 10, 30),
    #     "sentiment": datetime(2025, 1, 11, 10, 15),
    #     "fundamentals": datetime(2025, 1, 10, 15, 00)
    # }
```

**Design Rationale:** Real money decisions require current data. We prioritize accuracy over cost by always fetching fresh data for time-sensitive metrics. Data freshness timestamps provide transparency and enable validation.

#### Caching Strategy (REVISED - Requirement 7)

**What to Cache:**
- ✅ Company information (changes slowly)
- ✅ Historical SEC filings (static data)
- ✅ Historical price data (for backtesting)

**What NOT to Cache:**
- ❌ Current market prices (real-time decisions)
- ❌ Technical indicators (time-sensitive)
- ❌ Sentiment data (rapidly changing)
- ❌ Risk assessments (based on current data)

**Cache TTL by Data Type:**
```python
CACHE_TTL = {
    "company_info": 24 * 60 * 60,      # 24 hours
    "sec_filings": 7 * 24 * 60 * 60,   # 7 days
    "historical_prices": 24 * 60 * 60,  # 24 hours
    # No caching for real-time data
}
```

### 9. Integration with Flow Orchestrator (Consolidated Architecture)

#### Consolidated Flow Method - Single Atomic Operation

**Design Rationale:** The current architecture has three separate Flow methods that perform related operations sequentially:

1. `analyze_holdings_deep()` - Runs DeepAnalysisCrew on each holding
2. `match_alternatives()` - Finds alternatives for underperforming holdings
3. `update_portfolio_review_with_deep_analysis()` - Regenerates portfolio review with enriched data

This creates inefficiency (portfolio review runs twice) and unnecessary complexity (3 @listen decorators). We consolidate into ONE method that performs all operations atomically.

**Critical Requirement Alignment:** This design directly addresses Requirement 4 (Integration with Flow Orchestrator) which mandates:
- Consolidated atomic operation for deep analysis, alternative matching, and portfolio update
- Graceful error handling with degraded functionality
- Structured Flow state management
- Direct crew instantiation pattern (not factory)

#### New Consolidated Method

```python
# src/finwiz/flows/flow_orchestrator.py

@listen("check_portfolio")
def analyze_and_update_portfolio(self) -> dict[str, Any]:
    """
    Perform deep analysis, match alternatives, and update portfolio review.
    
    This consolidates three operations into one atomic operation:
    1. Deep crew analysis on each holding (using unified DeepAnalysisCrew)
    2. Alternative matching for underperforming holdings (grade C, D, F)
    3. Portfolio review regeneration with enriched data
    
    CrewAI Flow Integration:
    - Triggered after portfolio review completes
    - Checks DEEP_PORTFOLIO_ANALYSIS environment variable
    - Uses direct crew instantiation and crew.kickoff()
    - Updates structured Flow state (self.state)
    - Returns consolidated results for downstream listeners
    
    Returns:
        dict: Consolidated results passed to downstream @listen() methods
    """
    # Check if deep analysis is enabled
    enabled = (os.getenv("DEEP_PORTFOLIO_ANALYSIS") or "false").strip().lower() in {"1", "true", "yes", "on"}
    if not enabled:
        logger.info("Deep portfolio analysis disabled via DEEP_PORTFOLIO_ANALYSIS")
        return {}
    
    try:
        # Step 1: Run deep analysis on holdings
        deep_analysis_results = self._run_deep_analysis_on_holdings()
        
        # Step 2: Match alternatives for underperforming holdings
        alternatives_data = self._match_alternatives_for_holdings(deep_analysis_results)
        
        # Step 3: Update portfolio review with enriched data
        portfolio_updated = self._update_portfolio_review_with_enriched_data()
        
        # Return consolidated results
        return {
            "deep_analysis_complete": True,
            "analysis_results": deep_analysis_results,
            "alternatives_data": alternatives_data,
            "portfolio_updated": portfolio_updated,
            "holdings_analyzed": len(deep_analysis_results),
            "alternatives_found": sum(len(alts) for alts in alternatives_data.values())
        }
        
    except Exception as e:
        logger.error(f"Deep portfolio analysis failed: {e}", exc_info=True)
        self.state.deep_analysis_error = str(e)
        return {"deep_analysis_complete": False, "error": str(e)}


def _run_deep_analysis_on_holdings(self) -> dict[str, Any]:
    """
    Run DeepAnalysisCrew on each portfolio holding.
    
    Returns:
        dict: Analysis results keyed by ticker
    """
    # Load holdings from structured Flow state
    if not hasattr(self.state, "portfolio_review") or not self.state.portfolio_review:
        logger.warning("No portfolio review data available in Flow state")
        return {}
    
    portfolio_data = self.state.portfolio_review
    if "portfolio_review" in portfolio_data:
        holdings = portfolio_data["portfolio_review"].get("holdings", [])
    else:
        holdings = portfolio_data.get("holdings", [])
    
    if not holdings:
        logger.warning("No holdings found in portfolio review data")
        return {}
    
    logger.info(f"Starting deep analysis for {len(holdings)} holdings")
    
    # Initialize cache manager
    from finwiz.cache.analysis_cache_manager import get_analysis_cache_manager
    cache_ttl_hours = int(os.getenv("PORTFOLIO_CACHE_TTL_HOURS", "24"))
    cache_manager = get_analysis_cache_manager(ttl_hours=cache_ttl_hours)
    
    # Import unified deep analysis crew
    from finwiz.crews.deep_analysis.deep_analysis import DeepAnalysisCrew
    
    # Process each holding
    deep_analysis_results = {}
    processed_count = 0
    
    for holding in holdings:
        ticker = holding.get("ticker")
        asset_class = holding.get("asset_class")
        
        if not ticker or not asset_class:
            logger.warning(f"Skipping holding with missing ticker or asset_class: {holding}")
            continue
        
        try:
            # Check cache first
            cached_result = cache_manager.get_cached_analysis(ticker, asset_class)
            if cached_result and cached_result.is_fresh(cache_ttl_hours):
                logger.info(f"Using cached analysis for {ticker} (age: {cached_result.age_hours:.1f}h)")
                analysis_result = cached_result.analysis
                
                # Create DeepAnalysisResult from cached data
                from finwiz.flow_state import DeepAnalysisResult
                deep_result = DeepAnalysisResult(
                    ticker=ticker,
                    asset_class=asset_class,
                    crew_name=analysis_result.crew_name,
                    analyzed_at=analysis_result.analyzed_at,
                    composite_score=analysis_result.composite_score,
                    grade=analysis_result.grade,
                    fundamental_score=analysis_result.fundamental_score,
                    technical_score=analysis_result.technical_score,
                    risk_score=analysis_result.risk_score,
                    cached=True,
                )
                deep_analysis_results[ticker] = deep_result
            else:
                # Use unified crew for all asset classes (SIMPLIFIED)
                crew = DeepAnalysisCrew()
                crew_name = "DeepAnalysisCrew"
                
                # Execute with single ticker AND asset_class
                crew_inputs = {
                    "ticker": ticker,
                    "asset_class": asset_class,  # Required for dynamic tool routing
                    "current_day": self.state.current_day,
                    "current_month": self.state.current_month,
                    "current_year": self.state.current_year,
                    "current_date": self.state.current_date,
                    "full_date": self.state.full_date,
                    "timestamp": self.state.timestamp,
                    "report_language": self.state.report_language,
                }
                
                logger.info(f"Running {crew_name} analysis for {ticker} ({asset_class})")
                result = crew.crew().kickoff(inputs=crew_inputs)
                
                # Parse and store result
                analysis_result = self._parse_crew_output_for_holding(
                    result, ticker, asset_class, crew_name
                )
                
                # Cache the result
                cache_manager.cache_analysis(ticker, asset_class, analysis_result)
                
                # Create DeepAnalysisResult
                from finwiz.flow_state import DeepAnalysisResult
                deep_result = DeepAnalysisResult(
                    ticker=ticker,
                    asset_class=asset_class,
                    crew_name=crew_name,
                    analyzed_at=analysis_result.analyzed_at,
                    composite_score=analysis_result.composite_score,
                    grade=analysis_result.grade,
                    fundamental_score=analysis_result.fundamental_score,
                    technical_score=analysis_result.technical_score,
                    risk_score=analysis_result.risk_score,
                    cached=False,
                )
                deep_analysis_results[ticker] = deep_result
            
            processed_count += 1
            logger.info(f"Deep analysis progress: {processed_count}/{len(holdings)} holdings")
            
        except Exception as e:
            logger.error(f"Deep analysis failed for {ticker}: {e}", exc_info=True)
            continue
    
    # Update structured Flow state
    self.state.deep_analysis_results = deep_analysis_results
    self.state.deep_analysis_success = True
    self.state.deep_analysis_count = processed_count
    
    # Log cache statistics
    cache_manager.log_cache_stats()
    
    logger.info(f"Deep analysis completed for {processed_count} holdings")
    
    return {ticker: result.model_dump(mode='json') for ticker, result in deep_analysis_results.items()}


def _match_alternatives_for_holdings(self, deep_results: dict[str, Any]) -> dict[str, Any]:
    """
    Match A+ alternatives for underperforming holdings.
    
    Args:
        deep_results: Deep analysis results from _run_deep_analysis_on_holdings()
    
    Returns:
        dict: Alternatives data keyed by ticker
    """
    # Check if alternative matching is enabled
    enabled = (os.getenv("PORTFOLIO_ENABLE_ALTERNATIVES") or "true").strip().lower() in {"1", "true", "yes", "on"}
    if not enabled:
        logger.info("Alternative matching disabled via PORTFOLIO_ENABLE_ALTERNATIVES")
        return {}
    
    if not deep_results:
        logger.warning("No deep analysis results available for alternative matching")
        return {}
    
    # Use existing AlternativeFinder tool
    from finwiz.tools.alternative_finder_tool import AlternativeFinder, HoldingProfile
    
    alternative_finder = AlternativeFinder()
    max_alternatives = int(os.getenv("PORTFOLIO_MAX_ALTERNATIVES", "5"))
    
    # Process holdings with grade C or below
    alternatives_data = {}
    alternatives_count = 0
    
    for ticker, analysis in deep_results.items():
        grade = analysis.get("grade", "D")
        
        # Only find alternatives for grades C, D, or F
        if grade in ["C", "D", "F"]:
            try:
                # Create HoldingProfile for AlternativeFinder
                holding_profile = HoldingProfile(
                    ticker=ticker,
                    name=analysis.get("name", ticker),
                    asset_class=analysis.get("asset_class", "stock"),
                    grade=grade,
                    composite_score=analysis.get("composite_score", 0.6),
                    risk_score=analysis.get("risk_score", 2.5),
                )
                
                # Find alternatives using existing tool
                alternatives = alternative_finder.find_alternatives(
                    holding=holding_profile, max_alternatives=max_alternatives
                )
                
                if alternatives:
                    alternatives_data[ticker] = [alt.model_dump(mode='json') for alt in alternatives]
                    alternatives_count += len(alternatives)
                    logger.info(f"Found {len(alternatives)} alternatives for {ticker} (grade: {grade})")
                else:
                    logger.info(f"No alternatives found for {ticker} (grade: {grade})")
                    
            except Exception as e:
                logger.error(f"Alternative matching failed for {ticker}: {e}")
                continue
        else:
            logger.debug(f"Skipping alternative matching for {ticker} (grade: {grade} - B or above)")
    
    # Update structured Flow state
    self.state.portfolio_alternatives = alternatives_data
    self.state.alternatives_success = True
    self.state.alternatives_count = alternatives_count
    
    logger.info(f"Alternative matching completed: {alternatives_count} alternatives for {len(alternatives_data)} holdings")
    
    return alternatives_data


def _update_portfolio_review_with_enriched_data(self) -> bool:
    """
    Regenerate portfolio review with deep analysis results and alternatives.
    
    Returns:
        bool: True if portfolio review was successfully updated
    """
    # Check if deep analysis was performed
    if not self.state.deep_analysis_success:
        logger.info("Skipping portfolio review update - no deep analysis performed")
        return False
    
    logger.info("Updating portfolio review with deep analysis results")
    
    try:
        # Re-run portfolio review with Flow state containing deep analysis
        out_path = run_portfolio_review(flow_state=self.state)
        self.state.portfolio_review_json = str(out_path)
        
        # Reload updated portfolio review
        with open(out_path, encoding="utf-8") as f:
            portfolio_data = json.load(f)
            self.state.portfolio_review = portfolio_data
        
        logger.info(
            f"Portfolio review updated with deep analysis: "
            f"{self.state.deep_analysis_count} holdings analyzed, "
            f"{self.state.alternatives_count} alternatives found"
        )
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to update portfolio review with deep analysis: {e}", exc_info=True)
        logger.warning("Continuing with original portfolio review")
        return False
```

#### Routing Logic Update

**Design Rationale:** The consolidated approach dramatically simplifies the flow orchestrator:

**Before (3 separate methods):**
- `analyze_holdings_deep()` - Runs crews
- `match_alternatives()` - Finds alternatives
- `update_portfolio_review_with_deep_analysis()` - Regenerates portfolio
- 3 @listen decorators
- Portfolio review runs TWICE (initial + update)
- Complex dependency chain

**After (1 consolidated method):**
- `analyze_and_update_portfolio()` - Does everything atomically
- 1 @listen decorator
- Portfolio review runs ONCE (with enriched data)
- Simple, linear flow

**Changes Required:**
1. Rename `analyze_holdings_deep()` to `analyze_and_update_portfolio()`
2. Extract helper methods: `_run_deep_analysis_on_holdings()`, `_match_alternatives_for_holdings()`, `_update_portfolio_review_with_enriched_data()`
3. Remove separate `match_alternatives()` and `update_portfolio_review_with_deep_analysis()` methods
4. Update `check_investment_discovery` listener to wait for `analyze_and_update_portfolio` instead of `match_alternatives`
5. Import `DeepAnalysisCrew` (1 line)
6. Pass `asset_class` parameter in inputs (already done in task 2)

**Benefits:**
- Eliminates redundant portfolio review generation (runs once instead of twice)
- Reduces flow complexity (1 method instead of 3)
- Atomic operation (all-or-nothing semantics)
- Clearer code organization (related operations grouped together)
- Easier to maintain and test
- Consistent behavior across all asset classes
- Simpler dependency chain for downstream listeners

#### Flow Sequence Correction (CRITICAL)

**Design Rationale:** The current flow has discovery BEFORE portfolio analysis, which is backwards from the logical business process. This violates Requirement 4.9-4.16 which mandates the correct sequence.

**Current (INCORRECT) Flow:**
```
validate_data_integration → discovery crews → check_portfolio → analyze_holdings_deep
```

**Problems:**
- ❌ Discovery runs before we know what we own
- ❌ Alternative matching happens before discovery provides A+ candidates
- ❌ Portfolio generated twice (initial + update)
- ❌ Rebalancing lacks complete context

**Corrected (REQUIRED) Flow:**
```
Phase 1: Validation
├─ validate_data_integration

Phase 2: Portfolio Analysis
├─ check_portfolio (generates initial portfolio review)

Phase 3: Deep Analysis & Update (ATOMIC)
├─ analyze_and_update_portfolio
│  ├─ Deep analysis: DeepAnalysisCrew analyzes each holding
│  ├─ Match alternatives: Identifies holdings needing alternatives (grade C, D, F)
│  └─ Update portfolio: Merges deep analysis + alternatives (ONCE)

Phase 4: Discovery
├─ check_crypto, check_stock, check_etf (parallel)
├─ check_investment_discovery (consolidates A+ opportunities)

Phase 5: Rebalancing
├─ check_portfolio_rebalancing (optimizes with complete data)

Phase 6: Reporting
├─ pre_validate_reporter_input → report
```

**Listener Decorator Changes:**
```python
# Phase 2: Portfolio Analysis
@listen("validate_data_integration")  # Changed from and_("check_stock", "check_etf", "check_crypto")
def check_portfolio(self):
    pass

# Phase 3: Deep Analysis & Update
@listen("check_portfolio")  # New consolidated method
def analyze_and_update_portfolio(self):
    pass

# Phase 4: Discovery
@listen("analyze_and_update_portfolio")  # Changed from "validate_data_integration"
def check_crypto(self):
    pass

@listen("analyze_and_update_portfolio")  # Changed from "validate_data_integration"
def check_stock(self):
    pass

@listen("analyze_and_update_portfolio")  # Changed from "validate_data_integration"
def check_etf(self):
    pass

@listen(and_("check_crypto", "check_stock", "check_etf"))  # Changed from and_("match_alternatives", "check_portfolio_rebalancing")
def check_investment_discovery(self):
    pass

# Phase 5: Rebalancing
@listen("check_investment_discovery")  # Changed from and_("check_stock", "check_etf", "check_crypto")
def check_portfolio_rebalancing(self):
    pass
```

**Why This Order (Requirement 4.9-4.16):**
1. **Portfolio First:** Analyze what you own before finding alternatives
2. **Deep Analysis:** Grade each holding (A+ to F)
3. **Identify Needs:** Alternative matching identifies underperformers
4. **Find Solutions:** Discovery provides A+ candidates
5. **Update Once:** Portfolio review generated ONCE with complete data
6. **Optimize:** Rebalancing has access to portfolio + discoveries
7. **Report:** Present comprehensive recommendations

**Critical Benefits:**
- ✅ Logical business flow (analyze → grade → discover → optimize → report)
- ✅ Portfolio generated ONCE (not twice)
- ✅ Discovery runs AFTER we know what needs improvement
- ✅ Alternative matching identifies needs, discovery provides solutions
- ✅ Rebalancing has complete information
- ✅ No race conditions in parallel listeners


### 8. API Efficiency and Smart Tool Usage (Requirement 11)

#### Design Philosophy

**Priority Order:**
1. **Accuracy First:** Real money decisions require current, accurate data
2. **Efficiency Second:** Minimize redundant calls through smart design
3. **Cost Third:** Optimize where possible without compromising accuracy

**Design Rationale:** Requirement 11 mandates intelligent API usage without sacrificing data freshness. This section defines patterns for achieving both goals.

#### Smart Batching (Tool-Level)

**Pattern:** Use batch APIs when tools support them for multiple related data points.

```python
# ✅ EFFICIENT: Batch indicator fetch (1 API call)
indicators = TwelveDataIndicatorTool.fetch_multiple(
    ticker="AAPL",
    indicators=["RSI", "MACD", "BB"]
)

# ❌ INEFFICIENT: Individual fetches (3 API calls)
rsi = TwelveDataIndicatorTool.fetch("AAPL", "RSI")
macd = TwelveDataIndicatorTool.fetch("AAPL", "MACD")
bb = TwelveDataIndicatorTool.fetch("AAPL", "BB")
```

**Implementation in Tasks:**
- Technical analysis task SHALL use batch indicator APIs
- Tools that support batching SHALL be used with batch parameters
- Individual calls SHALL only be made when batching is not supported

#### Context Sharing (Crew-Level)

**Pattern:** Pass data between tasks via context to avoid redundant API calls.

```python
# Task 1: Fetch and store with timestamp
price_data = YahooFinanceTool.get_price("AAPL")
context["price_data"] = {
    "data": price_data,
    "timestamp": datetime.now(),
    "source": "yahoo_finance"
}

# Task 2: Reuse from context if fresh
cached_data = context.get("price_data")
if cached_data and is_fresh(cached_data["timestamp"], max_age_minutes=5):
    price_data = cached_data["data"]  # Reuse
else:
    price_data = YahooFinanceTool.get_price("AAPL")  # Re-fetch if stale
```

**Implementation Rules:**
- Tasks SHALL check context for existing data before making API calls
- Context data SHALL include timestamps for freshness validation
- Stale data SHALL be re-fetched rather than reused
- Context sharing SHALL NOT compromise data accuracy

#### Parallel Execution

**Pattern:** Use async_execution for independent I/O-bound tasks.

```yaml
# config/tasks.yaml
deep_analysis_task:
  async_execution: true  # Can run in parallel with technical_analysis_task

technical_analysis_task:
  async_execution: true  # Can run in parallel with deep_analysis_task
  
risk_assessment_task:
  async_execution: true  # Can run in parallel after dependencies complete
  depends_on:
    - deep_analysis_task
    - technical_analysis_task

final_report_task:
  async_execution: false  # Must be synchronous (CrewAI requirement)
  depends_on:
    - risk_assessment_task
```

**Benefits:**
- Parallel I/O operations reduce total execution time
- Rate limits still respected (max_rpm=20 at crew level)
- Fallback to sequential execution on failure

#### Monitoring and Optimization

**Logging Requirements (Requirement 11.6-11.10):**

```python
# Log API call counts per ticker
logger.info(f"API calls for {ticker}: {api_call_count}")

# Log data freshness metrics
logger.info(f"Data freshness: {fresh_count}/{total_count} fresh ({fresh_pct:.1f}%)")

# Log execution time breakdown
logger.info(f"Task execution times: deep_analysis={t1:.2f}s, technical={t2:.2f}s")

# Identify optimization opportunities
if api_call_count > expected_calls:
    logger.warning(f"Potential optimization: {api_call_count} calls (expected {expected_calls})")
```

#### Acceptable vs Unacceptable Patterns

**✅ ACCEPTABLE:**
- Caching company fundamentals (changes slowly)
- Batching indicator requests (same freshness, fewer calls)
- Sharing data between tasks via context (same execution)
- Parallel I/O for independent data fetching

**❌ NOT ACCEPTABLE:**
- Using 24-hour cached prices for buy/sell decisions
- Using stale sentiment data for risk assessment
- Skipping data fetches to save costs
- Compromising data freshness for efficiency

#### Implementation in DeepAnalysisCrew

The unified crew SHALL implement these patterns:

1. **Batch Indicators:** Technical analysis task uses batch API for RSI, MACD, BB
2. **Context Sharing:** Price data fetched once, shared across tasks
3. **Parallel Tasks:** First 3 tasks run async, final task synchronous
4. **Freshness Validation:** All context data includes timestamps
5. **Monitoring:** Log API calls, freshness metrics, execution times

### 9. Error Handling and Validation (Requirement 8)

#### Design Philosophy

**Graceful Degradation:** The crew SHALL handle errors gracefully and provide partial results when possible, rather than failing completely.

**Clear Error Messages:** All errors SHALL include actionable information for debugging and resolution.

#### Validation Strategy

**Input Validation:**

```python
def validate_inputs(ticker: str, asset_class: str) -> None:
    """Validate crew inputs before execution.
    
    Raises:
        ValueError: If inputs are invalid with clear message
    """
    if not ticker:
        raise ValueError(
            "Ticker parameter is required. "
            "Provide a valid ticker symbol (e.g., 'AAPL', 'VOO', 'BTC')"
        )
    
    if not asset_class:
        raise ValueError(
            "Asset class parameter is required. "
            "Must be one of: stock, etf, crypto"
        )
    
    valid_asset_classes = ["stock", "etf", "crypto"]
    if asset_class.lower() not in valid_asset_classes:
        raise ValueError(
            f"Invalid asset_class: {asset_class}. "
            f"Must be one of: {', '.join(valid_asset_classes)}"
        )
```

**Ticker Validation:**

```python
# First task: Validate ticker existence
validation_result = TickerValidationTool.validate(ticker, asset_class)

if not validation_result.is_valid:
    raise InvalidTickerError(
        f"Ticker '{ticker}' not found on {asset_class} exchanges. "
        f"Reason: {validation_result.error_message}"
    )
```

#### Fallback Strategies

**Data Source Failures:**

```python
# Try primary source
try:
    data = PrimaryDataSource.fetch(ticker)
except APIError as e:
    logger.warning(f"Primary source failed: {e}, trying fallback")
    
    # Try fallback source
    try:
        data = FallbackDataSource.fetch(ticker)
    except APIError as e2:
        logger.error(f"All data sources failed: primary={e}, fallback={e2}")
        
        # Return partial results with confidence flag
        return PartialAnalysisResult(
            ticker=ticker,
            confidence_level=0.3,
            error_message="Data sources unavailable",
            partial_data=cached_data_if_available
        )
```

**Incomplete Analysis:**

```python
# If some tasks fail, return partial results
if fundamental_analysis_failed:
    logger.warning(f"Fundamental analysis failed for {ticker}")
    result.fundamental_score = None
    result.confidence_level *= 0.7  # Reduce confidence
    result.warnings.append("Fundamental analysis unavailable")

# Still return result with available data
return result
```

#### Reasoning Loop Prevention

**Task Description Pattern (Requirement 5.6):**

```yaml
deep_analysis_task:
  description: >
    Perform comprehensive analysis of the provided {asset_class} ticker: {ticker}
    
    SINGLE TICKER MODE: You are analyzing ONE specific {asset_class}, not screening multiple assets.
    
    CRITICAL: The ticker {ticker} is provided as input. Do NOT request additional tickers.
    
    Analysis Steps for {asset_class}:
    1. Validate the provided ticker {ticker} using TickerValidationTool
    2. Fetch {asset_class}-specific data for {ticker}
    3. Analyze current market conditions for {ticker}
    4. Calculate performance metrics for {ticker}
    5. Generate comprehensive analysis for {ticker}
```

**Key Phrases to Prevent Loops:**
- "SINGLE TICKER MODE"
- "the provided ticker: {ticker}"
- "Do NOT request additional tickers"
- Repeat "{ticker}" throughout description

#### Error Logging

**Detailed Logging for Debugging:**

```python
try:
    result = crew.kickoff(inputs=crew_inputs)
except Exception as e:
    logger.error(
        f"DeepAnalysisCrew failed for {ticker} ({asset_class})",
        exc_info=True,
        extra={
            "ticker": ticker,
            "asset_class": asset_class,
            "error_type": type(e).__name__,
            "error_message": str(e),
            "crew_name": "DeepAnalysisCrew"
        }
    )
    raise
```

#### Integration with Flow Orchestrator

**Graceful Degradation in Flow:**

```python
@listen("check_portfolio")
def analyze_and_update_portfolio(self) -> dict[str, Any]:
    """Atomic operation with graceful error handling."""
    try:
        # Step 1: Deep analysis
        deep_results = self._run_deep_analysis_on_holdings()
        
        # Step 2: Match alternatives (continues even if some analyses failed)
        alternatives = self._match_alternatives_for_holdings(deep_results)
        
        # Step 3: Update portfolio (continues with partial data)
        portfolio_updated = self._update_portfolio_review_with_enriched_data()
        
        return {
            "deep_analysis_complete": True,
            "analysis_results": deep_results,
            "alternatives_data": alternatives,
            "portfolio_updated": portfolio_updated
        }
        
    except Exception as e:
        logger.error(f"Deep portfolio analysis failed: {e}", exc_info=True)
        
        # Update state with error
        self.state.deep_analysis_error = str(e)
        
        # Return error info for downstream methods
        return {
            "deep_analysis_complete": False,
            "error": str(e),
            "analysis_results": {},
            "alternatives_data": {}
        }
```

**Per-Holding Error Handling:**

```python
for holding in holdings:
    ticker = holding.get("ticker")
    asset_class = holding.get("asset_class")
    
    try:
        # Attempt analysis
        crew = DeepAnalysisCrew()
        result = crew.crew().kickoff(inputs={"ticker": ticker, "asset_class": asset_class})
        deep_analysis_results[ticker] = result
        
    except InvalidTickerError as e:
        logger.error(f"Invalid ticker {ticker}: {e}")
        # Skip this holding, continue with others
        continue
        
    except Exception as e:
        logger.error(f"Deep analysis failed for {ticker}: {e}", exc_info=True)
        # Skip this holding, continue with others
        continue
```

### 10. Crew Configuration

#### Unified Crew Setup with Dynamic Tool Routing

```python
from crewai import Agent, Crew, Task, Process
from crewai.project import CrewBase, agent, crew, task
from finwiz.tools.tool_factories import (
    get_stock_crew_tools,
    get_etf_crew_tools,
    get_crypto_crew_tools
)
from finwiz.utils.llm_config import get_configured_llm
from finwiz.utils.agent_validators import final_reporter

@CrewBase
class DeepAnalysisCrew:
    """Unified deep analysis crew for single ticker across all asset classes.
    
    Handles stocks, ETFs, and cryptocurrencies through dynamic tool routing
    based on the asset_class parameter.
    """
    
    def __init__(self):
        # Load configurations
        self.agents_config = load_yaml("config/agents.yaml")
        self.tasks_config = load_yaml("config/tasks.yaml")
        super().__init__()
    
    def get_tools_for_asset_class(self, asset_class: str) -> list:
        """Route to appropriate tool set based on asset class.
        
        Args:
            asset_class: One of "stock", "etf", "crypto"
            
        Returns:
            List of tools appropriate for the asset class
            
        Raises:
            ValueError: If asset_class is not valid
        """
        asset_class_lower = asset_class.lower()
        
        if asset_class_lower == "stock":
            return get_stock_crew_tools(
                include_rag=True,
                include_quantitative=True,
                collection_suffix="stock_deep"
            )
        elif asset_class_lower == "etf":
            return get_etf_crew_tools(
                include_rag=True,
                include_quantitative=True,
                collection_suffix="etf_deep"
            )
        elif asset_class_lower == "crypto":
            return get_crypto_crew_tools(
                include_rag=True,
                include_quantitative=True,
                collection_suffix="crypto_deep"
            )
        else:
            raise ValueError(
                f"Invalid asset_class: {asset_class}. "
                f"Must be one of: stock, etf, crypto"
            )
    
    @agent
    def asset_analyst(self) -> Agent:
        """Asset analyst that adapts to any asset class."""
        # Note: Tools will be set dynamically based on asset_class input
        return Agent(
            config=self.agents_config["asset_analyst"],
            tools=[],  # Set dynamically in crew() method
            verbose=True,
            reasoning=True,  # Enabled with proper task descriptions
            llm=get_configured_llm()
        )
    
    @agent
    def risk_assessor(self) -> Agent:
        """Risk assessor that adapts to any asset class."""
        return Agent(
            config=self.agents_config["risk_assessor"],
            tools=[],  # Set dynamically in crew() method
            verbose=True,
            reasoning=True,
            llm=get_configured_llm()
        )
    
    @final_reporter
    @agent
    def investment_reporter(self) -> Agent:
        """Final reporter that consolidates analysis from context."""
        return Agent(
            config=self.agents_config["investment_reporter"],
            tools=[],  # MUST be empty - enforced by decorator
            verbose=True,
            reasoning=True,
            llm=get_configured_llm()
        )
    
    @task
    def deep_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config["deep_analysis_task"],
            agent=self.asset_analyst(),
            async_execution=True,
            reasoning=True
        )
    
    @task
    def technical_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config["technical_analysis_task"],
            agent=self.asset_analyst(),
            async_execution=True,
            reasoning=True
        )
    
    @task
    def risk_assessment_task(self) -> Task:
        return Task(
            config=self.tasks_config["risk_assessment_task"],
            agent=self.risk_assessor(),
            async_execution=True,  # I/O-bound
            reasoning=True
        )
    
    @task
    def final_report_task(self) -> Task:
        return Task(
            config=self.tasks_config["final_report_task"],
            agent=self.investment_reporter(),
            async_execution=False,  # Final task must be sync
            reasoning=True
        )
    
    @crew
    def crew(self) -> Crew:
        """Create crew with dynamically assigned tools based on asset_class input."""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            respect_context_window=True,
            max_rpm=20
        )
```

**Design Rationale:** The unified crew uses a single implementation with dynamic tool routing. Tools are assigned based on the `asset_class` parameter passed in the `kickoff()` inputs. This eliminates code duplication while maintaining asset-specific analysis capabilities.

**Note on Tool Assignment:** Tools are initially set to empty lists and will be dynamically assigned when the crew is executed with the `asset_class` parameter. This allows the same crew instance to handle different asset classes.


### 9. Agent Configuration (agents.yaml)

#### Unified Deep Analysis Crew

**Design Note:** The unified crew uses generic agent names that adapt to any asset class through dynamic tool routing and template variables in task descriptions.

```yaml
asset_analyst:
  role: "Deep Analysis Specialist"
  goal: >
    Perform comprehensive analysis of the provided {asset_class} ticker: {ticker}
    to evaluate its investment potential and provide actionable insights for 
    keep/sell decisions.
  backstory: >
    You are an expert financial analyst specializing in deep-dive analysis of 
    individual assets across stocks, ETFs, and cryptocurrencies. You analyze 
    fundamentals, technicals, and market conditions to provide accurate assessments 
    for portfolio management decisions. You work with ONE {asset_class} at a time, 
    providing detailed analysis rather than comparative screening.
    
    CRITICAL: You are analyzing a SINGLE ticker ({ticker}), not screening multiple 
    assets. Do NOT request additional tickers or ask for "top 10" lists.

risk_assessor:
  role: "Risk Assessment Specialist"
  goal: >
    Evaluate all risk dimensions for the provided {asset_class} ticker: {ticker}
    using standardized methodology and provide clear risk scores (0-5 scale) and 
    mitigation strategies.
  backstory: >
    You are a risk assessment expert specializing in financial risk evaluation 
    across all asset classes. You analyze market risk, liquidity risk, credit risk, 
    and asset-specific risks to provide comprehensive risk profiles. You use 
    standardized 0-5 risk scoring and provide actionable mitigation recommendations.
    
    CRITICAL: You are assessing risks for a SINGLE ticker ({ticker}), not comparing 
    multiple assets.

investment_reporter:
  role: "Investment Report Synthesizer"
  goal: >
    Consolidate analysis findings from previous tasks and generate final investment
    report with composite score and grade for the provided {asset_class} ticker: {ticker}.
  backstory: >
    You are a senior investment analyst who synthesizes research from multiple
    specialists into coherent investment recommendations. You consume analysis
    from context (NO external tools) and calculate composite scores and grades
    based on fundamental, technical, and risk assessments.
    
    CRITICAL: You have NO tools available. All data comes from previous tasks via 
    context. Your role is to consolidate and synthesize, not to fetch new data.
```

**Design Rationale:** 
- **Generic Names:** `asset_analyst` instead of `stock_analyst` allows the same agent to handle any asset class
- **Template Variables:** `{asset_class}` and `{ticker}` adapt descriptions dynamically
- **Single Ticker Emphasis:** "CRITICAL" sections prevent reasoning agents from requesting multiple tickers
- **Tool Restrictions:** Investment reporter explicitly states "NO tools available" to prevent external calls

### 10. Task Configuration Examples

#### Unified Deep Analysis Tasks (tasks.yaml)

**Design Note:** Tasks use `{asset_class}` template variable to adapt descriptions dynamically. The same task definitions work for stocks, ETFs, and cryptocurrencies.

```yaml
deep_analysis_task:
  description: >
    Perform comprehensive analysis of the provided {asset_class} ticker: {ticker}
    
    SINGLE TICKER MODE: You are analyzing ONE specific {asset_class}, not screening multiple assets.
    The ticker {ticker} is provided as input. Do NOT request additional tickers.
    
    Analysis Steps for {asset_class}:
    1. Validate {ticker} using TickerValidationTool
    2. Fetch {asset_class}-specific data for {ticker} using appropriate tools
       - Stock: EnhancedSECAnalysisTool for 10-K/10-Q filings
       - ETF: EnhancedETFAnalysisTool for factsheet data
       - Crypto: EnhancedCryptoAnalysisTool for on-chain metrics
    3. Extract key metrics appropriate for {asset_class}
    4. Analyze current market conditions for {ticker}
    5. Calculate performance metrics for {ticker}
    
    Use smart API batching where possible (e.g., fetch multiple metrics in one call).
    Share data via context for subsequent tasks.
    
    Asset Class: {asset_class}
    Today's date: {full_date}
    
    OUTPUT: Return {asset_class}-specific analysis schema for {ticker}
  expected_output: >
    Comprehensive analysis for the single {asset_class} ticker {ticker}
    conforming to asset-specific Pydantic schema (TenKInsight/ETFFactsheet/CryptoThesis).
  agent: asset_analyst
  async_execution: true

technical_analysis_task:
  description: >
    Perform technical analysis of the provided {asset_class} ticker: {ticker}
    
    SINGLE TICKER MODE: Analyze the ONE ticker provided, not multiple assets.
    
    Technical Analysis Steps:
    1. Fetch technical indicators for {ticker} using batch API:
       - RSI, MACD, Bollinger Bands in ONE call (smart batching)
    2. Identify support/resistance levels for {ticker}
    3. Analyze price trends and momentum for {ticker}
    4. Generate buy/sell signals for {ticker}
    5. Use QuantitativeAnalysisTool(asset_class="{asset_class}") for {ticker}
    
    Reuse price data from context if available (avoid redundant fetches).
    Check data freshness before reusing (max age: 5 minutes).
    
    Asset Class: {asset_class}
    Today's date: {full_date}
    
    OUTPUT: Return technical analysis for {ticker}
  expected_output: >
    Technical analysis with indicators, support/resistance, and signals
    for the single {asset_class} ticker {ticker}.
  agent: asset_analyst
  async_execution: true
  depends_on:
    - deep_analysis_task

risk_assessment_task:
  description: >
    Evaluate risks for the provided {asset_class} ticker: {ticker}
    
    SINGLE TICKER MODE: Assess risks for the ONE ticker provided.
    
    Risk Assessment Steps:
    1. Calculate volatility and drawdown metrics for {ticker}
    2. Assess {asset_class}-specific risks:
       - Stock: market risk, liquidity risk, credit risk, company-specific risks
       - ETF: tracking error, liquidity, counterparty, structural risks
       - Crypto: extreme volatility, regulatory, technology, market manipulation risks
    3. Use StandardizedRiskScoringTool for {ticker}
    4. Generate risk scores (0-5 scale) for {ticker}
    5. Provide mitigation recommendations for {ticker}
    
    Reuse analysis data from context (avoid redundant fetches).
    
    Asset Class: {asset_class}
    Today's date: {full_date}
    
    OUTPUT: Return RiskAssessmentStandardized for {ticker}
  expected_output: >
    Comprehensive risk assessment for the single {asset_class} ticker {ticker}
    conforming to RiskAssessmentStandardized Pydantic schema with 0-5 risk scores.
  agent: risk_assessor
  output_pydantic: RiskAssessmentStandardized
  async_execution: true  # I/O-bound
  depends_on:
    - deep_analysis_task
    - technical_analysis_task

final_report_task:
  description: >
    Generate final investment report for the provided {asset_class} ticker: {ticker}
    
    FINAL REPORTER: Consolidate findings from previous tasks (NO external tools).
    
    Report Generation Steps:
    1. Retrieve analysis from context (deep_analysis_task output)
    2. Retrieve technical analysis from context (technical_analysis_task output)
    3. Retrieve risk assessment from context (risk_assessment_task output)
    4. Calculate composite score: (fundamental_score + technical_score + (1 - risk_score)) / 3
    5. Assign grade based on composite score:
       - A+ (≥0.95), A (≥0.85), B (≥0.75), C (≥0.65), D (≥0.55), F (<0.55)
    6. Generate DeepAnalysisResult with all metadata and data freshness timestamps
    
    CRITICAL: You have NO tools available. All data comes from previous tasks via context.
    DO NOT attempt to fetch new data. Your role is to consolidate and synthesize only.
    
    Asset Class: {asset_class}
    Today's date: {full_date}
    
    OUTPUT: Return DeepAnalysisResult for {ticker}
  expected_output: >
    Final investment report for the single {asset_class} ticker {ticker} with composite
    score, grade, and all analysis metadata conforming to DeepAnalysisResult schema.
  agent: investment_reporter
  output_pydantic: DeepAnalysisResult
  async_execution: false  # Final task must be synchronous (CrewAI requirement)
  depends_on:
    - deep_analysis_task
    - technical_analysis_task
    - risk_assessment_task
```

**Design Rationale:**
- **Template Variables:** `{asset_class}` and `{ticker}` make tasks adapt to any asset type
- **Single Ticker Emphasis:** "SINGLE TICKER MODE" and "ONE ticker" prevent reasoning loops
- **Smart API Usage:** Explicit instructions for batching and context sharing
- **Data Freshness:** Instructions to check freshness before reusing context data
- **Final Reporter Constraints:** Explicit "NO tools available" prevents external calls


### 11. Data Freshness Strategy

**Design Principle:** Accuracy First - Never sacrifice data freshness for cost savings. Real money decisions require current market data.

#### Timestamp Tracking

```python
class DataFreshnessTracker:
    """Track data freshness for transparency."""
    
    def __init__(self):
        self.timestamps = {}
    
    def record(self, source: str, timestamp: datetime):
        """Record when data was fetched."""
        self.timestamps[source] = timestamp
    
    def get_report(self) -> Dict[str, str]:
        """Generate freshness report."""
        return {
            source: ts.isoformat()
            for source, ts in self.timestamps.items()
        }
    
    def is_stale(self, source: str, max_age_minutes: int = 5) -> bool:
        """Check if data is stale based on threshold."""
        if source not in self.timestamps:
            return True
        age = datetime.now() - self.timestamps[source]
        return age.total_seconds() > (max_age_minutes * 60)
```

#### Usage in Tasks

```python
# Task 1: Record timestamps
price_data = fetch_price("AAPL")
freshness_tracker.record("price_data", datetime.now())
context["price_data"] = price_data
context["freshness"] = freshness_tracker

# Task 2: Check freshness before reusing
freshness = context["freshness"]
if freshness.is_stale("price_data", max_age_minutes=5):
    # Re-fetch if stale (accuracy over efficiency)
    price_data = fetch_price("AAPL")
    freshness_tracker.record("price_data", datetime.now())
else:
    # Reuse from context (same execution, still fresh)
    price_data = context["price_data"]
```

#### Caching Policy (CRITICAL)

**Cache (Static Data Only):**
- Company information (name, sector, industry) - changes rarely
- Historical SEC filings (10-K, 10-Q) - historical documents
- ETF prospectus documents - static documents
- Crypto whitepaper/tokenomics - foundational documents

**Do NOT Cache (Dynamic Data):**
- Current market prices - changes every second
- Technical indicators - calculated from current prices
- Sentiment scores - changes with news flow
- On-chain metrics - real-time blockchain data
- News headlines - time-sensitive information

**Design Rationale:** 
- **Priority 1: Accuracy** - Real money decisions require current data
- **Priority 2: Efficiency** - Minimize redundant calls through smart design (batching, context sharing)
- **Priority 3: Cost** - Optimize where possible without compromising accuracy

**What We DON'T Do:**
- ❌ Cache market prices for 24 hours (stale data = bad investment decisions)
- ❌ Skip data fetches to save API costs (accuracy matters more than cost)
- ❌ Use old analysis for current decisions (market conditions change)

**What We DO:**
- ✅ Cache static company fundamentals (changes slowly)
- ✅ Use tool-level batching when available (fetch RSI+MACD+BB in one call)
- ✅ Share data between tasks via context (avoid re-fetching within same execution)
- ✅ Parallelize independent API calls (faster execution, not fewer calls)


### 12. API Efficiency Through Intelligent Tool Usage

**Design Principle:** Minimize redundant API calls without sacrificing data accuracy. Smart design over cost-cutting.

#### Smart Batching (Tool-Level)

**Concept:** When tools support batch operations, fetch multiple related data points in one API call.

```python
# ❌ Inefficient: Multiple Individual Calls (3 API calls)
rsi = TwelveDataIndicatorTool.fetch("AAPL", "RSI")
macd = TwelveDataIndicatorTool.fetch("AAPL", "MACD")
bb = TwelveDataIndicatorTool.fetch("AAPL", "BB")

# ✅ Efficient: Batch Call (1 API call, same freshness)
indicators = TwelveDataIndicatorTool.fetch_multiple(
    ticker="AAPL",
    indicators=["RSI", "MACD", "BB"]
)
```

**Design Rationale:** Tool-level batching reduces API calls while maintaining data freshness. All indicators are fetched at the same time, so there's no accuracy trade-off.

#### Context Sharing (Crew-Level)

**Concept:** Pass data between tasks via context to avoid re-fetching within the same crew execution.

```python
# ❌ Inefficient: Re-fetching Same Data (2 API calls)
# Task 1
price_data = fetch_price("AAPL")

# Task 2
price_data = fetch_price("AAPL")  # Redundant!

# ✅ Efficient: Context Sharing (1 API call)
# Task 1: Fetch and store
price_data = fetch_price("AAPL")
context["price_data"] = {
    "data": price_data,
    "timestamp": datetime.now()
}

# Task 2: Reuse from context
price_data = context["price_data"]["data"]
# Verify freshness before reusing
if context["price_data"]["timestamp"] < datetime.now() - timedelta(minutes=5):
    # Re-fetch if stale
    price_data = fetch_price("AAPL")
```

**Design Rationale:** Within a single crew execution (typically <5 minutes), data remains fresh. Context sharing avoids redundant fetches while maintaining accuracy.

#### Parallel Execution

**Concept:** Use async execution to parallelize independent I/O operations.

```python
# Async execution for I/O-bound tasks
@task
def deep_analysis_task(self) -> Task:
    return Task(
        config=self.tasks_config["deep_analysis_task"],
        async_execution=True  # Parallel I/O
    )

@task
def technical_analysis_task(self) -> Task:
    return Task(
        config=self.tasks_config["technical_analysis_task"],
        async_execution=True  # Parallel I/O
    )

# Final task must be synchronous (CrewAI requirement)
@task
def final_report_task(self) -> Task:
    return Task(
        config=self.tasks_config["final_report_task"],
        async_execution=False  # Must be sync
    )
```

**Parallel API Calls:**

```python
import asyncio

async def fetch_all_data(ticker: str):
    """Fetch multiple data sources in parallel."""
    results = await asyncio.gather(
        fetch_price(ticker),
        fetch_fundamentals(ticker),
        fetch_sentiment(ticker),
        return_exceptions=True
    )
    return results
```

**Design Rationale:** Parallel execution reduces total execution time without reducing the number of API calls. All data is still fetched fresh, just faster.

#### Monitoring and Optimization

```python
class APIEfficiencyMetrics:
    """Track API efficiency metrics."""
    
    def __init__(self):
        self.api_calls = {}
        self.batch_opportunities = []
        self.context_reuses = 0
    
    def record_api_call(self, tool_name: str, ticker: str):
        """Record API call."""
        key = f"{tool_name}:{ticker}"
        self.api_calls[key] = self.api_calls.get(key, 0) + 1
    
    def record_batch_opportunity(self, tool_name: str, indicators: list):
        """Record opportunity for batching."""
        self.batch_opportunities.append({
            "tool": tool_name,
            "indicators": indicators,
            "potential_savings": len(indicators) - 1
        })
    
    def record_context_reuse(self):
        """Record context data reuse."""
        self.context_reuses += 1
    
    def get_efficiency_report(self) -> dict:
        """Generate efficiency report."""
        return {
            "total_api_calls": sum(self.api_calls.values()),
            "api_calls_by_tool": self.api_calls,
            "batch_opportunities": self.batch_opportunities,
            "context_reuses": self.context_reuses
        }
```

#### Expected Performance

- **Target:** <5 minutes per ticker
- **Breakdown:**
  - Task 1 (Deep Analysis): ~2 minutes
  - Task 2 (Technical): ~1 minute
  - Task 3 (Risk): ~1 minute
  - Task 4 (Final Report): ~30 seconds
  - Overhead: ~30 seconds

- **Current (Broken):** 3-6 hours (infinite reasoning loops)
- **Improvement:** 36x to 72x faster

**Cost vs Accuracy Balance:**

- **Priority 1: Accuracy** - Real money decisions require current data
- **Priority 2: Efficiency** - Minimize redundant calls through smart design
- **Priority 3: Cost** - Optimize where possible without compromising 1 & 2


### 13. Error Handling and Graceful Degradation

#### Error Handling Strategy

```python
class DeepAnalysisError(Exception):
    """Base exception for deep analysis crews."""
    pass

class TickerValidationError(DeepAnalysisError):
    """Raised when ticker is invalid or not found."""
    pass

class DataFetchError(DeepAnalysisError):
    """Raised when data sources fail."""
    pass

# In crew execution
try:
    result = crew.crew().kickoff(inputs={"ticker": ticker})
except TickerValidationError as e:
    logger.error(f"Invalid ticker {ticker}: {e}")
    return create_error_result(ticker, "INVALID_TICKER")
except DataFetchError as e:
    logger.warning(f"Data fetch failed for {ticker}: {e}")
    return create_partial_result(ticker, available_data)
except Exception as e:
    logger.error(f"Unexpected error for {ticker}: {e}")
    return create_error_result(ticker, "ANALYSIS_FAILED")
```

#### Partial Results

```python
def create_partial_result(ticker: str, available_data: dict) -> DeepAnalysisResult:
    """Create result with available data, flag missing data."""
    return DeepAnalysisResult(
        ticker=ticker,
        fundamental_score=available_data.get("fundamental_score", 0.5),
        technical_score=available_data.get("technical_score", 0.5),
        risk_score=available_data.get("risk_score", 0.5),
        composite_score=0.5,
        grade="C",  # Conservative grade for incomplete data
        confidence_flag="PARTIAL_DATA",
        missing_data=list(available_data.get("missing", []))
    )
```


### 14. Testing Strategy

#### Unit Tests

```python
def test_stock_deep_analysis_crew_single_ticker(mocker):
    """Test that crew analyzes single ticker without requesting more."""
    # Arrange
    mock_tools = mocker.patch('finwiz.tools.tool_factories.get_stock_crew_tools')
    crew = StockDeepAnalysisCrew()
    
    # Act
    result = crew.crew().kickoff(inputs={"ticker": "AAPL"})
    
    # Assert
    assert result is not None
    assert "AAPL" in str(result)
    # Verify no requests for additional tickers
    assert "provide 10 tickers" not in str(result).lower()
```

#### Integration Tests

```python
@pytest.mark.integration
def test_stock_deep_analysis_with_real_data():
    """Test crew with real API calls (slow, requires API keys)."""
    crew = StockDeepAnalysisCrew()
    result = crew.crew().kickoff(inputs={
        "ticker": "AAPL",
        "full_date": "2025-01-11"
    })
    
    assert result is not None
    assert result.ticker == "AAPL"
    assert 0.0 <= result.composite_score <= 1.0
    assert result.grade in ["A+", "A", "B", "C", "D", "F"]
```

#### Performance Tests

```python
def test_crew_completes_within_5_minutes():
    """Ensure crew doesn't hang indefinitely."""
    import signal
    
    def timeout_handler(signum, frame):
        raise TimeoutError("Crew exceeded 5 minute timeout")
    
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(300)  # 5 minutes
    
    try:
        crew = StockDeepAnalysisCrew()
        result = crew.crew().kickoff(inputs={"ticker": "AAPL"})
        assert result is not None
    finally:
        signal.alarm(0)
```


### 15. Monitoring and Metrics

#### Metrics to Track

```python
class CrewMetrics:
    """Track crew execution metrics."""
    
    def __init__(self):
        self.metrics = {
            "execution_time": 0.0,
            "api_calls": {},
            "data_freshness": {},
            "cache_hits": 0,
            "cache_misses": 0,
            "errors": []
        }
    
    def record_api_call(self, tool_name: str):
        """Record API call by tool."""
        self.metrics["api_calls"][tool_name] = \
            self.metrics["api_calls"].get(tool_name, 0) + 1
    
    def record_execution_time(self, seconds: float):
        """Record total execution time."""
        self.metrics["execution_time"] = seconds
    
    def get_summary(self) -> dict:
        """Get metrics summary."""
        return {
            "execution_time_seconds": self.metrics["execution_time"],
            "total_api_calls": sum(self.metrics["api_calls"].values()),
            "api_calls_by_tool": self.metrics["api_calls"],
            "cache_hit_rate": self._calculate_cache_hit_rate(),
            "errors": len(self.metrics["errors"])
        }
```

#### Logging Strategy

```python
import logging

logger = logging.getLogger("finwiz.crews.deep_analysis")

# Log crew start
logger.info(f"Starting {crew_name} analysis for {ticker}")

# Log task completion
logger.info(f"Completed {task_name} for {ticker} in {duration}s")

# Log API calls
logger.debug(f"API call: {tool_name} for {ticker}")

# Log data freshness
logger.info(f"Data freshness for {ticker}: {freshness_report}")

# Log completion
logger.info(f"Completed {crew_name} for {ticker}: grade={grade}, score={score}")
```


## Key Design Decisions

### Decision 1: Unified Crew vs Separate Crews

**Decision:** Implement ONE unified `DeepAnalysisCrew` with dynamic tool routing instead of three separate crews (StockDeepAnalysisCrew, EtfDeepAnalysisCrew, CryptoDeepAnalysisCrew).

**Rationale:**
- **No Code Duplication:** Single implementation eliminates duplicate code across asset classes
- **Easier Maintenance:** Changes apply to all asset classes automatically
- **Consistent Behavior:** Guaranteed consistency in analysis approach across asset types
- **Simpler Integration:** Flow orchestrator only needs to import and instantiate one crew
- **Reduced Testing Burden:** Test one crew implementation instead of three
- **Clean Architecture:** Separation of concerns - crew logic vs tool selection

**Trade-offs:**
- Slightly more complex tool routing logic (mitigated by clear `get_tools_for_asset_class()` method)
- Tools must be assigned dynamically (handled by passing `asset_class` in inputs)

**Alternative Considered:** Three separate crews (StockDeepAnalysisCrew, EtfDeepAnalysisCrew, CryptoDeepAnalysisCrew) with duplicated code. Rejected due to maintenance burden and code duplication.

### Decision 2: Dynamic Tool Routing Method

**Decision:** Implement `get_tools_for_asset_class(asset_class)` method within the crew class.

**Rationale:**
- **Encapsulation:** Tool routing logic lives with the crew that uses it
- **Type Safety:** Raises ValueError for invalid asset_class values
- **Testability:** Easy to unit test tool routing logic
- **Clarity:** Clear method signature makes intent obvious

**Alternative Considered:** External routing function. Rejected because it separates routing logic from the crew that depends on it.

### Decision 3: Empty Tools List for Final Reporter

**Decision:** Investment reporter agent MUST have empty tools list, enforced by `@final_reporter` decorator.

**Rationale:**
- **Prevents Redundant API Calls:** Final reporter consolidates existing analysis, shouldn't fetch new data
- **Framework Enforcement:** `@final_reporter` decorator prevents accidental tool assignment
- **Clear Intent:** Empty tools list signals that agent operates only on context
- **Cost Efficiency:** Avoids unnecessary API calls in final consolidation step

**Alternative Considered:** Allow tools but document that they shouldn't be used. Rejected because it relies on documentation rather than enforcement.

### Decision 4: Reasoning Enabled with Explicit Task Descriptions

**Decision:** Enable `reasoning=True` on all agents and tasks, with explicit "SINGLE TICKER MODE" language in task descriptions.

**Rationale:**
- **Prevents Infinite Loops:** Explicit language prevents reasoning agent from requesting "10 tickers"
- **Quality Analysis:** Reasoning enables agents to plan and validate their approach
- **Root Cause Fix:** Addresses the 3-6 hour hang issue at its source (task descriptions)
- **Maintains Benefits:** Keeps reasoning benefits while preventing misuse

**Alternative Considered:** Disable reasoning (`reasoning=False`). Rejected because it sacrifices analysis quality to work around poor task descriptions.

## Implementation Checklist

### Phase 1: Create Unified DeepAnalysisCrew (Priority 1)

- [ ] Create directory structure: `src/finwiz/crews/deep_analysis/`
- [ ] Create `deep_analysis.py` with unified crew class
- [ ] Implement `get_tools_for_asset_class()` method with dynamic routing
- [ ] Create `config/agents.yaml` with 3 agents (asset_analyst, risk_assessor, investment_reporter)
- [ ] Create `config/tasks.yaml` with 4 tasks (deep_analysis, technical_analysis, risk_assessment, final_report)
- [ ] Add "SINGLE TICKER MODE" language to all task descriptions
- [ ] Use `{asset_class}` template variable in task descriptions for dynamic adaptation
- [ ] Apply `@final_reporter` decorator to investment_reporter agent
- [ ] Enable `reasoning=True` on all agents and tasks
- [ ] Implement error handling for invalid asset_class values
- [ ] Write unit tests for dynamic tool routing
- [ ] Write unit tests for single-ticker analysis (no "10 tickers" requests)
- [ ] Write integration tests with real tickers (stock, ETF, crypto)

### Phase 2: Update Flow Orchestrator (Priority 2)

- [ ] Update `src/finwiz/flows/flow_orchestrator.py` in `analyze_holdings_deep()` method
- [ ] Import unified `DeepAnalysisCrew` class
- [ ] Remove if/elif routing logic (simplified to single crew instantiation)
- [ ] Pass both `ticker` AND `asset_class` in kickoff inputs
- [ ] Verify integration with existing `_parse_crew_output_for_holding()` method
- [ ] Test with real portfolio data (multiple asset classes)
- [ ] Verify no infinite reasoning loops (complete within 5 minutes)
- [ ] Verify data freshness (prices <5 minutes old)

### Phase 3: Documentation and Cleanup (Priority 3)

- [ ] Add header comment to `src/finwiz/crews/stock_crew/config/tasks.yaml`
- [ ] Add header comment to `src/finwiz/crews/etf_crew/config/tasks.yaml`
- [ ] Add header comment to `src/finwiz/crews/crypto_crew/config/tasks.yaml`
- [ ] Comments should state: "DISCOVERY CREW - Designed to screen and identify top 10 assets"
- [ ] Comments should state: "For single-ticker deep analysis, use DeepAnalysisCrew instead"
- [ ] Update crew docstrings to clarify discovery vs deep analysis purposes
- [ ] Document API call patterns per asset_class
- [ ] Document expected execution time per asset_class
- [ ] Add logging for data freshness metrics
- [ ] Add logging for API call counts

### Phase 4: Monitoring and Optimization (Priority 4)

- [ ] Implement metrics tracking for crew execution
- [ ] Log API call counts per ticker
- [ ] Log data freshness metrics (% fresh vs cached)
- [ ] Identify opportunities for tool-level batching
- [ ] Log execution time breakdown by task
- [ ] Monitor for reasoning loops or performance issues
- [ ] Document optimization recommendationsml` with 2 agents
- [ ] Create `config/tasks.yaml` with 3 tasks
- [ ] Implement tool factory integration
- [ ] Add reasoning-compatible task descriptions
- [ ] Implement data freshness tracking
- [ ] Add error handling and graceful degradation
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Update flow orchestrator routing
- [ ] Test with real portfolio data
- [ ] Document API call patterns

### Phase 3: CryptoDeepAnalysisCrew (Priority 3)

- [ ] Create directory structure: `src/finwiz/crews/crypto_deep_analysis/`
- [ ] Create `crypto_deep_analysis.py` with crew class
- [ ] Create `config/agents.yaml` with 2 agents
- [ ] Create `config/tasks.yaml` with 3 tasks
- [ ] Implement tool factory integration
- [ ] Add reasoning-compatible task descriptions
- [ ] Implement data freshness tracking
- [ ] Add error handling and graceful degradation
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Update flow orchestrator routing
- [ ] Test with real portfolio data
- [ ] Document API call patterns

### Phase 4: Integration and Documentation

- [ ] Update flow orchestrator with all three crews
- [ ] Add routing logic documentation
- [ ] Create performance benchmarks
- [ ] Document API call patterns and costs
- [ ] Add monitoring dashboards
- [ ] Update user documentation
- [ ] Add troubleshooting guide


## Risk Mitigation

### Risk 1: Reasoning Loops

**Mitigation:**
- Explicit task descriptions stating "SINGLE TICKER MODE"
- Repeated use of "{ticker}" variable throughout descriptions
- Clear statements: "Do NOT request additional tickers"
- Testing with reasoning enabled before deployment

### Risk 2: Data Staleness

**Mitigation:**
- Timestamp tracking for all data sources
- Freshness validation before using cached data
- Clear documentation of what can/cannot be cached
- Transparency in output (include data-as-of timestamps)

### Risk 3: API Rate Limits

**Mitigation:**
- Sequential execution of crews (not parallel)
- max_rpm=20 configuration
- Retry logic with exponential backoff
- Graceful degradation on rate limit errors

### Risk 4: Performance Degradation

**Mitigation:**
- 5-minute timeout per crew execution
- Async execution for I/O-bound tasks
- Parallel API calls where possible
- Performance monitoring and alerting

### Risk 5: Integration Issues

**Mitigation:**
- Minimal changes to flow orchestrator
- Backward-compatible output format
- Comprehensive integration tests
- Phased rollout (ETF first, then Stock, then Crypto)

## Success Metrics

1. **No Infinite Loops:** 0 instances of 3+ hour hangs
2. **Performance:** 95% of analyses complete in <5 minutes
3. **Data Freshness:** 100% of price data <5 minutes old
4. **Accuracy:** Grade consistency with manual analysis >90%
5. **API Efficiency:** <50 API calls per ticker on average
6. **Error Rate:** <5% of analyses fail completely
7. **Cache Appropriateness:** 0% of dynamic data cached

---

**Version:** 1.0  
**Created:** 2025-01-11  
**Status:** Ready for Implementation


## Requirements Traceability Matrix

This section maps design elements to specific requirements, ensuring complete coverage.

### Requirement 1: Single Ticker Analysis with Dynamic Asset Class Routing

**Design Elements:**
- Section 1: Unified Crew Structure - Single crew for all asset classes
- Section 1.1: Dynamic Tool Routing Implementation - `get_tools_for_asset_class()` method
- Section 6: Task Descriptions - "SINGLE TICKER MODE" language prevents reasoning loops
- Section 10: Crew Configuration - Accepts ticker + asset_class parameters

**Acceptance Criteria Coverage:**
- 1.1: Task descriptions explicitly state single-ticker mode ✅
- 1.2: Crew accepts ticker and asset_class parameters ✅
- 1.3: Dynamic routing based on asset_class ✅
- 1.4-1.5: Reasoning-compatible task descriptions ✅
- 1.6: ValueError raised for invalid asset_class ✅
- 1.7: Ticker is primary input, not optional ✅

### Requirement 2: Comprehensive Asset-Specific Analysis

**Design Elements:**
- Section 1.1: Dynamic Tool Routing - Routes to asset-specific tools
- Section 2: Agent Architecture - Asset analyst adapts to asset class
- Section 3: Task Architecture - 4 tasks cover all analysis aspects
- Section 5: Tool Assignment Strategy - Asset-specific tool factories

**Acceptance Criteria Coverage:**
- 2.1-2.5 (Stock): EnhancedSECAnalysisTool, QuantitativeAnalysisTool, technical indicators ✅
- 2.6-2.10 (ETF): EnhancedETFAnalysisTool, tracking error, technical indicators ✅
- 2.11-2.15 (Crypto): EnhancedCryptoAnalysisTool, on-chain metrics, technical indicators ✅
- 2.16-2.18 (Common): TickerValidationTool, StandardizedSentimentTool, QuantitativeAnalysisTool ✅

### Requirement 3: Standardized Output Schema

**Design Elements:**
- Section 4: Data Models and Schemas - DeepAnalysisResult schema
- Section 4.1: Output Schema Structure - Standardized fields across asset classes
- Section 4.2: Asset-Specific Schemas - Reuse existing schemas

**Acceptance Criteria Coverage:**
- 3.1: Returns unified DeepAnalysisResult ✅
- 3.2: Includes all score fields (fundamental, technical, risk, composite) ✅
- 3.3: Includes grade (A+ to F) ✅
- 3.4: Includes asset_class field ✅
- 3.5: Conforms to FinWiz schema standards ✅
- 3.6: Cacheable by analysis_cache_manager ✅
- 3.7: Includes ticker, asset_class, analyzed_at, crew_name ✅
- 3.8: Includes data_freshness timestamps ✅

### Requirement 4: Integration with Flow Orchestrator

**Design Elements:**
- Section 7: Integration with Flow Orchestrator - Consolidated architecture
- Section 7.1: Consolidated Flow Method - Single atomic operation
- Section 7.2: Routing Logic Update - Flow sequence correction
- Section 7.3: Flow Sequence Correction - Listener decorator changes

**Acceptance Criteria Coverage:**
- 4.1-4.5 (Consolidated Method): Single atomic operation with error handling ✅
- 4.6-4.13 (Deep Analysis Integration): Direct crew instantiation, dynamic routing ✅
- 4.14-4.16 (Alternative Matching): Uses AlternativeFinder, stores in Flow state ✅
- 4.17-4.19 (Portfolio Update): Regenerates once with enriched data ✅
- 4.20-4.26 (Flow Sequence): Corrected listener decorators, logical business flow ✅

### Requirement 5: Reasoning-Enabled Design

**Design Elements:**
- Section 6: Task Descriptions - Reasoning-compatible language
- Section 10: Crew Configuration - reasoning=True on agents and tasks

**Acceptance Criteria Coverage:**
- 5.1: Reasoning creates plan for single-ticker analysis ✅
- 5.2: Sets 'ready': True for single-ticker inputs ✅
- 5.3: Does NOT request additional tickers ✅
- 5.4: Identifies required tools and data sources ✅
- 5.5: Proceeds to execution without loops ✅
- 5.6: Task descriptions explicitly state "analyze the provided ticker" ✅

### Requirement 6: Tool and Data Source Usage

**Design Elements:**
- Section 5: Tool Assignment Strategy - Tool factories per asset class
- Section 5.1: Tool Factories - get_stock/etf/crypto_crew_tools()
- Section 1.1: Dynamic Tool Routing - Routes to appropriate tools

**Acceptance Criteria Coverage:**
- 6.1-6.4 (Stock Tools): EnhancedSECAnalysisTool, QuantitativeAnalysisTool, TickerValidationTool ✅
- 6.5-6.8 (ETF Tools): EnhancedETFAnalysisTool, QuantitativeAnalysisTool, TickerValidationTool ✅
- 6.9-6.12 (Crypto Tools): EnhancedCryptoAnalysisTool, QuantitativeAnalysisTool, CoinMarketCapTool ✅
- 6.13-6.16 (Common Tools): StandardizedSentimentTool, TwelveDataIndicatorTool, RAG tools ✅

### Requirement 7: Performance and Data Freshness

**Design Elements:**
- Section 8: API Efficiency and Smart Tool Usage - Data freshness priority
- Section 3: Task Architecture - Async execution for I/O-bound tasks
- Section 10: Crew Configuration - max_rpm=20 rate limiting

**Acceptance Criteria Coverage:**
- 7.1-7.5 (Data Freshness): Fetch current data, validate timestamps, flag stale data ✅
- 7.6-7.10 (Performance): <5 min execution, async tasks, rate limiting ✅
- 7.11-7.15 (Caching): Static data only, fresh data prioritized, appropriate TTL ✅

### Requirement 8: Error Handling and Validation

**Design Elements:**
- Section 9: Error Handling and Validation - Comprehensive error handling
- Section 9.1: Validation Strategy - Input and ticker validation
- Section 9.2: Fallback Strategies - Data source fallbacks, partial results
- Section 9.3: Reasoning Loop Prevention - Task description patterns

**Acceptance Criteria Coverage:**
- 8.1: Clear error for invalid ticker ✅
- 8.2: Fallback sources before failing ✅
- 8.3: Partial results with confidence flags ✅
- 8.4: Detailed error logging ✅
- 8.5: No infinite reasoning loops ✅
- 8.6: ValueError for missing ticker ✅

### Requirement 9: Crew Structure and Organization

**Design Elements:**
- Section 10: Crew Configuration - Standard CrewAI structure
- Section 2: Agent Architecture - 3 agents (asset_analyst, risk_assessor, investment_reporter)
- Section 3: Task Architecture - 4 tasks (deep_analysis, technical_analysis, risk_assessment, final_report)

**Acceptance Criteria Coverage:**
- 9.1: Standard CrewAI structure (deep_analysis/deep_analysis.py, config/*.yaml) ✅
- 9.2: 3 agents as specified ✅
- 9.3: 4 tasks as specified ✅
- 9.4: Uses @agent, @task, @crew decorators ✅
- 9.5: Uses get_configured_llm() ✅
- 9.6: reasoning=True enabled ✅
- 9.7: Task descriptions mention "analyze the provided {ticker}" ✅
- 9.8: Implements get_tools_for_asset_class() ✅
- 9.9: investment_reporter uses @final_reporter decorator ✅

### Requirement 11: API Efficiency Through Intelligent Tool Usage

**Design Elements:**
- Section 8: API Efficiency and Smart Tool Usage - Complete implementation
- Section 8.1: Smart Batching - Batch APIs for multiple indicators
- Section 8.2: Context Sharing - Pass data between tasks
- Section 8.3: Parallel Execution - Async tasks for I/O operations
- Section 8.4: Monitoring and Optimization - Logging requirements

**Acceptance Criteria Coverage:**
- 11.1-11.5 (Smart Batching): Use batch APIs when available ✅
- 11.6-11.10 (Context Sharing): Pass data via context with timestamps ✅
- 11.11-11.15 (Parallel Execution): Async execution for independent tasks ✅
- 11.16-11.20 (Monitoring): Log API calls, freshness, execution times ✅

## Design Completeness Verification

### All Requirements Addressed

✅ **Requirement 1:** Single Ticker Analysis with Dynamic Asset Class Routing  
✅ **Requirement 2:** Comprehensive Asset-Specific Analysis  
✅ **Requirement 3:** Standardized Output Schema  
✅ **Requirement 4:** Integration with Flow Orchestrator (Consolidated Architecture)  
✅ **Requirement 5:** Reasoning-Enabled Design  
✅ **Requirement 6:** Tool and Data Source Usage  
✅ **Requirement 7:** Performance and Data Freshness  
✅ **Requirement 8:** Error Handling and Validation  
✅ **Requirement 9:** Crew Structure and Organization  
✅ **Requirement 11:** API Efficiency Through Intelligent Tool Usage

### Design Principles Alignment

✅ **Unix Philosophy:** One task (analyze single ticker), one outcome (comprehensive analysis)  
✅ **No Duplication:** One crew handles all asset classes through dynamic tool routing  
✅ **Accuracy First:** Fresh data for real money decisions (never sacrifice accuracy for cost)  
✅ **Reasoning Enabled:** Clear task descriptions prevent infinite loops  
✅ **Smart API Usage:** Tool-level batching and context sharing minimize redundant calls  
✅ **Dynamic Routing:** Tools selected based on asset_class parameter at runtime

### Critical Design Decisions

1. **Single Unified Crew:** Eliminates code duplication across asset classes
2. **Dynamic Tool Routing:** Routes to appropriate tools based on asset_class parameter
3. **Consolidated Flow Method:** Atomic operation for deep analysis + alternatives + portfolio update
4. **Flow Sequence Correction:** Portfolio analysis BEFORE discovery (logical business order)
5. **Reasoning-Compatible Tasks:** "SINGLE TICKER MODE" language prevents infinite loops
6. **Final Reporter Pattern:** Empty tools list enforced by @final_reporter decorator
7. **API Efficiency:** Smart batching, context sharing, parallel execution without sacrificing accuracy
8. **Graceful Degradation:** Partial results with confidence flags when data sources fail

---

**Design Document Version:** 2.0  
**Last Updated:** 2025-01-11  
**Status:** Complete - All requirements addressed
