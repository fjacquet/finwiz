# DeepAnalysisCrew Documentation

## Overview

The `DeepAnalysisCrew` is a unified CrewAI crew designed for comprehensive single-ticker analysis across all asset classes (stocks, ETFs, and cryptocurrencies). It replaces the need for three separate deep analysis crews by using dynamic tool routing based on the `asset_class` parameter.

**Key Features:**
- Single crew implementation for all asset classes
- Dynamic tool routing based on asset_class parameter
- Comprehensive analysis with grading (A+ to F)
- Fresh data for real money decisions
- API efficiency through smart batching and context sharing
- Reasoning-enabled agents for quality analysis

## Architecture

### Design Philosophy

1. **Unix Philosophy**: One task (analyze single ticker), one outcome (comprehensive analysis)
2. **No Duplication**: One crew handles all asset classes through dynamic tool routing
3. **Accuracy First**: Fresh data for real money decisions (never sacrifice accuracy for cost)
4. **Smart API Usage**: Tool-level batching and context sharing minimize redundant calls

### Crew Structure

```
src/finwiz/crews/deep_analysis/
├── deep_analysis.py           # Main crew class with dynamic tool routing
└── config/
    ├── agents.yaml            # 3 agents: asset_analyst, risk_assessor, investment_reporter
    └── tasks.yaml             # 4 tasks: deep_analysis, technical_analysis, risk_assessment, final_report
```

### Agents

1. **Asset Analyst** - Deep analysis specialist (adapts to asset class)
2. **Risk Assessor** - Risk evaluation specialist
3. **Investment Reporter** - Final report consolidation (NO TOOLS)

### Tasks

1. **Deep Analysis Task** (async) - Comprehensive asset-specific analysis
2. **Technical Analysis Task** (async) - Technical indicators and chart analysis
3. **Risk Assessment Task** (async) - Standardized risk evaluation
4. **Final Report Task** (sync) - Consolidate findings and generate output

## Usage Examples

### Stock Analysis

```python
from finwiz.crews.deep_analysis.deep_analysis import DeepAnalysisCrew

# Initialize crew
crew = DeepAnalysisCrew()

# Execute analysis
result = crew.crew().kickoff(inputs={
    "ticker": "AAPL",
    "asset_class": "stock",
    "current_date": "2025-01-11",
    "full_date": "Saturday, January 11, 2025",
    "report_language": "French"
})

# Access results
print(f"Grade: {result.grade}")
print(f"Composite Score: {result.composite_score}")
```

### ETF Analysis

```python
from finwiz.crews.deep_analysis.deep_analysis import DeepAnalysisCrew

# Initialize crew
crew = DeepAnalysisCrew()

# Execute analysis
result = crew.crew().kickoff(inputs={
    "ticker": "VOO",
    "asset_class": "etf",
    "current_date": "2025-01-11",
    "full_date": "Saturday, January 11, 2025",
    "report_language": "French"
})

# Access results
print(f"Grade: {result.grade}")
print(f"Expense Ratio Analysis: {result.fundamental_score}")
```

### Crypto Analysis

```python
from finwiz.crews.deep_analysis.deep_analysis import DeepAnalysisCrew

# Initialize crew
crew = DeepAnalysisCrew()

# Execute analysis
result = crew.crew().kickoff(inputs={
    "ticker": "BTC",
    "asset_class": "crypto",
    "current_date": "2025-01-11",
    "full_date": "Saturday, January 11, 2025",
    "report_language": "French"
})

# Access results
print(f"Grade: {result.grade}")
print(f"Risk Score: {result.risk_score}")
```

## Dynamic Tool Routing

The crew uses dynamic tool routing to select appropriate tools based on the `asset_class` parameter:

### Tool Routing Logic

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

### Tool Sets by Asset Class

**Stock Tools:**
- `EnhancedSECAnalysisTool` - 10-K/10-Q filings analysis
- `QuantitativeAnalysisTool(asset_class="stock")` - Quantitative metrics
- `TickerValidationTool` - Ticker existence verification
- `YahooFinanceNewsTool` - Company news
- `StandardizedSentimentTool` - Market sentiment
- `TwelveDataIndicatorTool` - Technical indicators
- RAG tools - Knowledge base integration

**ETF Tools:**
- `EnhancedETFAnalysisTool` - Factsheet data
- `QuantitativeAnalysisTool(asset_class="etf")` - Quantitative metrics
- `TickerValidationTool` - Ticker existence verification
- `ETFTrackingAnalysisTool` - Tracking error analysis
- `StandardizedSentimentTool` - Market sentiment
- `TwelveDataIndicatorTool` - Technical indicators
- RAG tools - Knowledge base integration

**Crypto Tools:**
- `EnhancedCryptoAnalysisTool` - On-chain metrics
- `QuantitativeAnalysisTool(asset_class="crypto")` - Quantitative metrics
- `TickerValidationTool` - Ticker existence verification (Coinbase)
- `CoinMarketCapTool` - Market data
- `StandardizedSentimentTool` - Market sentiment
- `TwelveDataIndicatorTool` - Technical indicators
- RAG tools - Knowledge base integration

## Input Parameters

### Required Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `ticker` | str | Ticker symbol to analyze | "AAPL", "VOO", "BTC" |
| `asset_class` | str | Asset type for tool routing | "stock", "etf", "crypto" |

### Optional Parameters

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `current_date` | str | Current date (short format) | Auto-generated |
| `full_date` | str | Current date (full format) | Auto-generated |
| `report_language` | str | Report language | "French" |
| `current_day` | str | Day of month | Auto-generated |
| `current_month` | str | Month name | Auto-generated |
| `current_year` | str | Year | Auto-generated |
| `timestamp` | str | ISO timestamp | Auto-generated |

### Input Validation

```python
# Ticker validation
if not ticker:
    raise ValueError("Ticker parameter is required for deep analysis")

# Asset class validation
if asset_class.lower() not in ["stock", "etf", "crypto"]:
    raise ValueError(
        f"Invalid asset_class: {asset_class}. "
        f"Must be one of: stock, etf, crypto"
    )
```

## Output Schema

### DeepAnalysisResult

```python
class DeepAnalysisResult(BaseModel):
    """Standardized output for deep analysis crews."""
    
    # Identification
    ticker: str                          # Ticker symbol analyzed
    asset_class: str                     # "stock", "etf", "crypto"
    crew_name: str                       # "DeepAnalysisCrew"
    analyzed_at: datetime                # Analysis timestamp
    
    # Scores (0.0 to 1.0)
    fundamental_score: float             # Fundamental analysis score
    technical_score: float               # Technical analysis score
    risk_score: float                    # Risk assessment score
    composite_score: float               # Overall composite score
    
    # Grade (A+ to F)
    grade: str                           # Letter grade based on composite_score
    
    # Metadata
    cached: bool = False                 # Whether result was cached
    data_freshness: Dict[str, datetime]  # Timestamps per data source
```

### Field Descriptions

**Scores:**
- `fundamental_score`: 0.0-1.0 score based on fundamentals/factsheet/on-chain metrics
- `technical_score`: 0.0-1.0 score based on technical indicators and momentum
- `risk_score`: 0.0-1.0 score based on risk assessment (0=low risk, 1=high risk)
- `composite_score`: Weighted average of all scores

**Grade Mapping:**
- A+ ≥ 0.95
- A ≥ 0.85
- B ≥ 0.75
- C ≥ 0.65
- D ≥ 0.55
- F < 0.55

**Data Freshness:**
```python
{
    "price_data": datetime(2025, 1, 11, 10, 30),
    "technical_indicators": datetime(2025, 1, 11, 10, 30),
    "sentiment": datetime(2025, 1, 11, 10, 15),
    "fundamentals": datetime(2025, 1, 10, 15, 00)
}
```

## Error Handling

### Graceful Degradation

The crew implements graceful degradation for data source failures:

```python
try:
    # Attempt primary data source
    data = primary_tool.fetch(ticker)
except Exception as e:
    logger.warning(f"Primary source failed for {ticker}: {e}")
    try:
        # Fall back to secondary source
        data = fallback_tool.fetch(ticker)
    except Exception as e2:
        logger.error(f"Fallback source also failed for {ticker}: {e2}")
        # Return partial results with confidence flags
        return PartialAnalysisResult(
            ticker=ticker,
            has_fundamental_data=False,
            confidence_level=0.3,
            missing_data_reasons=["Primary and fallback sources failed"]
        )
```

### Error Types

**Input Validation Errors:**
```python
# Missing ticker
ValueError: "Ticker parameter is required for deep analysis"

# Invalid asset class
ValueError: "Invalid asset_class: invalid. Must be one of: stock, etf, crypto"
```

**Data Source Errors:**
- API rate limit exceeded
- Ticker not found
- Network timeout
- Invalid API response

**Partial Results:**
When data is incomplete, the crew returns partial results with confidence flags:
```python
{
    "ticker": "AAPL",
    "composite_score": 0.75,
    "grade": "B",
    "has_fundamental_data": True,
    "has_technical_data": False,  # Technical data unavailable
    "has_risk_assessment": True,
    "confidence_level": 0.7,  # Reduced confidence
    "missing_data_reasons": ["Technical indicators API timeout"]
}
```

## Performance Expectations

### Execution Time

- **Target**: < 5 minutes per ticker
- **Typical**: 2-3 minutes for complete analysis
- **Factors affecting performance**:
  - API response times
  - Data availability
  - Network latency
  - Reasoning complexity

### Performance Optimization

**Async Execution:**
```yaml
# config/tasks.yaml
deep_analysis_task:
  async_execution: true  # Parallel I/O

technical_analysis_task:
  async_execution: true  # Parallel I/O

risk_assessment_task:
  async_execution: true  # Parallel I/O

final_report_task:
  async_execution: false  # Must be synchronous (CrewAI requirement)
```

**Rate Limiting:**
```python
@crew
def crew(self) -> Crew:
    return Crew(
        agents=self.agents,
        tasks=self.tasks,
        process=Process.sequential,
        max_rpm=20  # 20 requests per minute
    )
```

## API Efficiency Patterns

### Smart Batching (Tool-Level)

**Inefficient (Multiple Individual Calls):**
```python
rsi = fetch_indicator("AAPL", "RSI")
macd = fetch_indicator("AAPL", "MACD")
bb = fetch_indicator("AAPL", "BB")
# 3 API calls
```

**Efficient (Batch Call):**
```python
indicators = fetch_indicators("AAPL", ["RSI", "MACD", "BB"])
# 1 API call
```

### Context Sharing (Crew-Level)

**Inefficient (Re-fetching Same Data):**
```python
# Task 1
price_data = fetch_price("AAPL")

# Task 2
price_data = fetch_price("AAPL")  # Redundant!
```

**Efficient (Context Sharing with Freshness Validation):**
```python
# Task 1: Fetch and store with timestamp
price_data = fetch_price("AAPL")
context["price_data"] = {
    "data": price_data,
    "timestamp": datetime.now()
}

# Task 2: Reuse from context if fresh
def is_fresh(timestamp, max_age_minutes=5):
    return (datetime.now() - timestamp).total_seconds() < (max_age_minutes * 60)

if "price_data" in context and is_fresh(context["price_data"]["timestamp"]):
    price_data = context["price_data"]["data"]  # Reuse fresh data
else:
    price_data = fetch_price("AAPL")  # Re-fetch if stale
    context["price_data"] = {"data": price_data, "timestamp": datetime.now()}
```

### Parallel Execution

Tasks with `async_execution: true` run in parallel when possible:

```python
# These tasks run in parallel (all async)
- deep_analysis_task (async)
- technical_analysis_task (async)
- risk_assessment_task (async)

# Final task waits for all async tasks to complete
- final_report_task (sync)
```

### Monitoring Metrics

The crew logs performance metrics for monitoring:

```python
# API call counts
logger.info(f"API calls for {ticker}: {api_call_count}")

# Data freshness
logger.info(f"Data freshness: {fresh_count}/{total_count} fresh ({fresh_pct:.1f}%)")

# Execution time breakdown
logger.info(f"Task times: deep={t1:.2f}s, technical={t2:.2f}s, risk={t3:.2f}s, report={t4:.2f}s")

# Total execution time
logger.info(f"Total analysis time for {ticker}: {total_time:.2f}s")
```

## Integration with Flow Orchestrator

### Flow Sequence (6 Phases)

The DeepAnalysisCrew integrates into the corrected 6-phase flow:

```
Phase 1: Data Validation
├─ validate_data_integration (start)

Phase 2: Portfolio Analysis (Analyze What You Have)
├─ check_portfolio
│  └─ Generates initial portfolio review
│  └─ Identifies holdings that need deep analysis

Phase 3: Deep Analysis & Update (Evaluate & Merge) ⭐ DeepAnalysisCrew runs here
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

### Why This Order?

**Portfolio BEFORE Discovery (Logical Business Order):**
1. **Analyze what you have** - Portfolio holdings analysis identifies what needs improvement
2. **Grade your holdings** - Deep analysis assigns grades (A+ to F)
3. **Identify needs** - Alternative matching identifies holdings needing replacement (grade < B)
4. **Find solutions** - Discovery provides A+ candidates to match those needs
5. **Update portfolio** - Merge deep analysis + A+ alternatives in one operation
6. **Optimize allocations** - Rebalancing with complete information
7. **Present recommendations** - Final consolidated report

**Consolidated Atomic Operation (Efficiency & Integrity):**
- ✅ Portfolio generated ONCE (not twice)
- ✅ No race conditions (all operations sequential)
- ✅ Atomic semantics (all-or-nothing)
- ✅ Simpler dependency chain (1 method instead of 3)

### Flow Integration Code

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
            "portfolio_updated": portfolio_updated
        }
        
    except Exception as e:
        logger.error(f"Deep portfolio analysis failed: {e}", exc_info=True)
        return {"deep_analysis_complete": False, "error": str(e)}


def _run_deep_analysis_on_holdings(self) -> dict[str, Any]:
    """Run DeepAnalysisCrew on each portfolio holding."""
    # Import unified deep analysis crew
    from finwiz.crews.deep_analysis.deep_analysis import DeepAnalysisCrew
    
    # Process each holding
    for holding in holdings:
        ticker = holding.get("ticker")
        asset_class = holding.get("asset_class")
        
        # Use unified crew for all asset classes
        crew = DeepAnalysisCrew()
        
        # Execute with single ticker AND asset_class
        result = crew.crew().kickoff(inputs={
            "ticker": ticker,
            "asset_class": asset_class,  # Required for dynamic tool routing
            "current_date": self.state.current_date,
            "full_date": self.state.full_date
        })
```

## Routing Logic: Discovery vs Deep Analysis

### When to Use DeepAnalysisCrew

**Use DeepAnalysisCrew when:**
- ✅ Analyzing a SPECIFIC ticker you already own
- ✅ Evaluating individual portfolio holdings
- ✅ Need detailed grade (A+ to F) for a single asset
- ✅ Making keep/sell decisions
- ✅ Calculating composite scores

**Example Use Cases:**
- "Analyze my AAPL holding - should I keep or sell?"
- "What grade does my VOO ETF deserve?"
- "Evaluate my BTC position"

### When to Use Discovery Crews

**Use Discovery Crews (StockCrew, EtfCrew, CryptoCrew) when:**
- ✅ Screening for NEW investment opportunities
- ✅ Finding "top 10" candidates in a category
- ✅ Discovering assets you don't currently own
- ✅ Comparative analysis across multiple assets

**Example Use Cases:**
- "Find me the top 10 growth stocks"
- "Discover low-cost diversified ETFs"
- "Identify promising DeFi projects"

### Comparison Table

| Feature | DeepAnalysisCrew | Discovery Crews |
|---------|------------------|-----------------|
| **Purpose** | Analyze ONE specific ticker | Screen and find top 10 candidates |
| **Input** | ticker + asset_class | Screening criteria |
| **Output** | DeepAnalysisResult with grade | List of opportunities |
| **Use Case** | Portfolio holdings evaluation | Investment discovery |
| **Tool Routing** | Dynamic based on asset_class | Fixed per crew type |
| **Reasoning Mode** | "SINGLE TICKER MODE" | "Top 10 screening" |

## Troubleshooting

### Common Issues

#### 1. Reasoning Loops (3-6 Hour Hangs)

**Symptom:**
- Crew hangs for hours with `'ready': False`
- Reasoning agent repeatedly asks for "10 tickers" or "KB auth"

**Cause:**
- Task descriptions contain "top 10" language
- Reasoning agent expects multiple tickers

**Solution:**
- Task descriptions explicitly state "SINGLE TICKER MODE"
- Repeat "{ticker}" throughout task description
- Use phrases like "the provided ticker: {ticker}"
- Avoid "screen", "identify top 10", "multiple assets"

**Prevention:**
```yaml
# ✅ CORRECT - Single ticker mode
deep_analysis_task:
  description: >
    Perform comprehensive analysis of the provided {asset_class} ticker: {ticker}
    
    SINGLE TICKER MODE: You are analyzing ONE specific {asset_class}.
    The ticker {ticker} is provided as input. Do NOT request additional tickers.

# ❌ WRONG - Top 10 language
bad_task:
  description: >
    Screen and identify the top 10 {asset_class} assets
```

#### 2. Stale Data

**Symptom:**
- Analysis based on outdated prices or sentiment
- Recommendations don't reflect current market conditions

**Cause:**
- Using cached data beyond freshness threshold
- Not validating data timestamps

**Solution:**
- Implement freshness validation:
```python
def is_fresh(timestamp, max_age_minutes=5):
    return (datetime.now() - timestamp).total_seconds() < (max_age_minutes * 60)

if not is_fresh(cached_data["timestamp"]):
    # Re-fetch data
    fresh_data = fetch_current_data()
```

**Data Freshness Thresholds:**
- Market prices: 5 minutes maximum
- Technical indicators: 5 minutes maximum
- Sentiment data: 15 minutes maximum
- Company fundamentals: 24 hours maximum

#### 3. API Failures

**Symptom:**
- Crew execution fails with API errors
- Incomplete analysis results

**Cause:**
- API rate limits exceeded
- Network timeouts
- Invalid API keys

**Solution:**
- Implement retry logic with exponential backoff
- Use fallback data sources
- Return partial results with confidence flags

```python
try:
    data = primary_api.fetch(ticker)
except RateLimitError:
    logger.warning("Rate limit exceeded, using fallback")
    data = fallback_api.fetch(ticker)
except TimeoutError:
    logger.error("API timeout, returning partial results")
    return PartialAnalysisResult(confidence_level=0.5)
```

#### 4. Invalid Asset Class

**Symptom:**
```
ValueError: Invalid asset_class: invalid. Must be one of: stock, etf, crypto
```

**Cause:**
- Incorrect asset_class parameter passed to crew

**Solution:**
- Validate asset_class before crew execution:
```python
valid_asset_classes = ["stock", "etf", "crypto"]
if asset_class.lower() not in valid_asset_classes:
    raise ValueError(f"Invalid asset_class: {asset_class}")
```

#### 5. Missing Ticker

**Symptom:**
```
ValueError: Ticker parameter is required for deep analysis
```

**Cause:**
- Ticker parameter not provided in crew inputs

**Solution:**
- Always provide ticker in kickoff inputs:
```python
result = crew.crew().kickoff(inputs={
    "ticker": "AAPL",  # Required
    "asset_class": "stock"  # Required
})
```

### Debug Logging

Enable verbose logging for troubleshooting:

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Run crew with verbose=True
crew = DeepAnalysisCrew()
result = crew.crew().kickoff(inputs={...})
```

### Performance Debugging

Monitor execution time and API calls:

```python
import time

start_time = time.time()

# Run crew
result = crew.crew().kickoff(inputs={...})

end_time = time.time()
execution_time = end_time - start_time

logger.info(f"Execution time: {execution_time:.2f}s")
logger.info(f"API calls: {api_call_count}")
logger.info(f"Data freshness: {fresh_count}/{total_count}")
```

## Best Practices

### 1. Always Provide Both Parameters

```python
# ✅ CORRECT
result = crew.crew().kickoff(inputs={
    "ticker": "AAPL",
    "asset_class": "stock"
})

# ❌ WRONG - Missing asset_class
result = crew.crew().kickoff(inputs={
    "ticker": "AAPL"
})
```

### 2. Validate Data Freshness

```python
# Check data timestamps
if result.data_freshness:
    for source, timestamp in result.data_freshness.items():
        age_minutes = (datetime.now() - timestamp).total_seconds() / 60
        if age_minutes > 30:
            logger.warning(f"{source} data is {age_minutes:.1f} minutes old")
```

### 3. Handle Partial Results

```python
# Check confidence level
if result.confidence_level < 0.7:
    logger.warning(f"Low confidence analysis for {ticker}: {result.confidence_level}")
    logger.warning(f"Missing data: {result.missing_data_reasons}")
```

### 4. Cache Results Appropriately

```python
from finwiz.cache.analysis_cache_manager import get_analysis_cache_manager

cache_manager = get_analysis_cache_manager(ttl_hours=24)

# Check cache first
cached_result = cache_manager.get_cached_analysis(ticker, asset_class)
if cached_result and cached_result.is_fresh(24):
    return cached_result.analysis

# Run crew and cache result
result = crew.crew().kickoff(inputs={...})
cache_manager.cache_analysis(ticker, asset_class, result)
```

### 5. Monitor Performance

```python
# Log execution metrics
logger.info(f"Analysis complete for {ticker}")
logger.info(f"  Grade: {result.grade}")
logger.info(f"  Composite Score: {result.composite_score:.3f}")
logger.info(f"  Execution Time: {execution_time:.2f}s")
logger.info(f"  API Calls: {api_call_count}")
logger.info(f"  Data Freshness: {fresh_pct:.1f}%")
```

## Summary

The DeepAnalysisCrew provides:

✅ **Unified Implementation** - One crew for all asset classes
✅ **Dynamic Tool Routing** - Automatic tool selection based on asset_class
✅ **Comprehensive Analysis** - Fundamental, technical, and risk assessment
✅ **Standardized Output** - DeepAnalysisResult with grades (A+ to F)
✅ **API Efficiency** - Smart batching and context sharing
✅ **Fresh Data** - Real-time analysis for real money decisions
✅ **Error Handling** - Graceful degradation with partial results
✅ **Performance** - < 5 minutes per ticker with parallel execution

For additional support, see:
- `docs/USER_GUIDE.md` - User-facing documentation
- `docs/ARCHITECTURE.md` - System architecture
- `.kiro/specs/deep-analysis-crews/` - Complete specification

---

**Version**: 1.0  
**Last Updated**: 2025-01-11  
**Status**: Production Ready
