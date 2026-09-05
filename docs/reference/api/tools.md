---
title: "Tools Reference"
description: "Complete reference for FinWiz analysis tools and their capabilities"
category: "reference"
tags:
  - "tools"
  - "api"
  - "reference"
  - "analysis"
date: "2025-10-26"
---

# Tools Reference

> **Outdated / unverified**: Much of this file's tool inventory predates the
> 4-wave migration that moved ~30 tools into the `crewai-custom-tools`
> package and has not been fully re-verified against `src/`. A rewrite is
> planned but not yet done. Until then, trust `src/finwiz/tools/CLAUDE.md`
> and the central package's own docs (`crewai_custom_tools` in
> `.venv/lib/python3.13/site-packages/`) over the specifics below.

Complete reference documentation for FinWiz's analysis tools, including financial data tools, technical analysis tools, and validation utilities.

## Overview

FinWiz tools are specialized components that crews use to gather data, perform calculations, and validate information. Each tool has a specific purpose and provides standardized outputs.

## Tool Categories

### Financial Data Tools

Tools for gathering market data, company information, and financial metrics.

#### YahooFinanceTickerInfoTool

Retrieves comprehensive ticker information from Yahoo Finance.

**Purpose**: Get basic company information and current market data

**Input**: Ticker symbol (string)

**Output**: Dictionary with company information

**Example**:

There is no `finwiz/tools/yahoo_finance_ticker_info_tool.py` — this tool
comes from the central `crewai_custom_tools` package:

```python
from crewai_custom_tools import YahooFinanceTickerInfoTool

tool = YahooFinanceTickerInfoTool()
info = tool.run("AAPL")

print(f"Company: {info['longName']}")
print(f"Sector: {info['sector']}")
print(f"Market Cap: {info['marketCap']}")
```

**Output Fields**:

- `longName`: Company full name
- `sector`: Business sector
- `industry`: Industry classification
- `marketCap`: Market capitalization
- `currentPrice`: Current stock price
- `volume`: Trading volume
- `beta`: Stock beta coefficient

#### EnhancedSECAnalysisTool

Analyzes SEC filings (10-K, 10-Q) for fundamental analysis.

**Purpose**: Extract financial metrics from SEC filings

**Input**: Ticker symbol (string)

**Output**: Dictionary with financial analysis

**Example**:

```python
from finwiz.tools.enhanced_sec_tool import EnhancedSECAnalysisTool

tool = EnhancedSECAnalysisTool()
analysis = tool.run("AAPL")

print(f"Revenue Growth: {analysis['revenue_growth']}")
print(f"ROE: {analysis['roe']}")
```

**Output Fields**:

- `revenue_growth`: Annual revenue growth rate
- `roe`: Return on equity
- `debt_to_equity`: Debt-to-equity ratio
- `profit_margin`: Net profit margin
- `current_ratio`: Current ratio
- `quick_ratio`: Quick ratio

#### EnhancedETFAnalysisTool

Specialized analysis for Exchange-Traded Funds.

**Purpose**: Analyze ETF structure, holdings, and performance

**Input**: ETF ticker symbol (string)

**Output**: Dictionary with ETF analysis

**Example**:

```python
from finwiz.tools.enhanced_etf_tool import EnhancedETFAnalysisTool

tool = EnhancedETFAnalysisTool()
analysis = tool.run("SPY")

print(f"Expense Ratio: {analysis['expense_ratio']}")
print(f"AUM: {analysis['aum']}")
```

**Output Fields**:

- `expense_ratio`: Annual expense ratio
- `aum`: Assets under management
- `tracking_error`: Tracking error vs benchmark
- `dividend_yield`: Current dividend yield
- `top_holdings`: List of top 10 holdings
- `sector_allocation`: Sector breakdown

#### EnhancedCryptoAnalysisTool

Cryptocurrency analysis including market metrics and blockchain data.

**Purpose**: Analyze cryptocurrency fundamentals and market dynamics

**Input**: Crypto ticker symbol (string)

**Output**: Dictionary with crypto analysis

**Example**:

```python
from finwiz.tools.enhanced_crypto_tool import EnhancedCryptoAnalysisTool

tool = EnhancedCryptoAnalysisTool()
analysis = tool.run("BTC")

print(f"Market Cap: {analysis['market_cap']}")
print(f"24h Volume: {analysis['volume_24h']}")
```

**Output Fields**:

- `market_cap`: Market capitalization
- `volume_24h`: 24-hour trading volume
- `circulating_supply`: Circulating supply
- `max_supply`: Maximum supply
- `price_change_24h`: 24-hour price change
- `volatility`: Price volatility measure

### Technical Analysis Tools

Tools for technical analysis, charting, and quantitative metrics.

#### QuantitativeAnalysisTool

Comprehensive quantitative analysis including risk metrics and technical indicators.

**Purpose**: Calculate quantitative metrics for investment analysis

**Input**:

```python
{
    "ticker": "AAPL",
    "asset_class": "stock",  # "stock", "etf", or "crypto"
}
```

**Output**: Dictionary with quantitative metrics

**Example**:

```python
from finwiz.tools.quantitative_analysis_tool import QuantitativeAnalysisTool

tool = QuantitativeAnalysisTool(asset_class="stock")
analysis = tool.run("AAPL")

print(f"Sharpe Ratio: {analysis['sharpe_ratio']}")
print(f"VaR: {analysis['var_95']}")
```

**Output Fields**:

- `sharpe_ratio`: Risk-adjusted return measure
- `sortino_ratio`: Downside risk-adjusted return
- `var_95`: Value at Risk (95% confidence)
- `cvar_95`: Conditional Value at Risk
- `max_drawdown`: Maximum drawdown
- `volatility`: Annualized volatility
- `beta`: Market beta coefficient
- `alpha`: Jensen's alpha

#### TechnicalIndicatorsTool — NOT IMPLEMENTED

There is no `TechnicalIndicatorsTool` class or `finwiz/tools/technical_indicators_tool.py`
module anywhere in the codebase (`grep -rn 'class TechnicalIndicatorsTool' src/`
finds no matches). Technical indicator calculation instead lives in the
`finwiz.quantitative.technical` subpackage — see
`TechnicalAnalysisEngine.analyze_symbol()` in
`src/finwiz/quantitative/technical/engine.py`, documented in
[Quantitative Analysis Framework](../quantitative_analysis.md).

### Risk Assessment Tools

Tools for evaluating investment risks and calculating risk metrics.

#### StandardizedRiskScoringTool

Comprehensive risk analysis for investments (central `crewai_custom_tools` package, tool name `risk_scoring`).

**Purpose**: Evaluate investment risks across multiple dimensions

**Input**: Asset data and market context

**Output**: Standardized risk assessment (0-10 risk score with factors)

**Example**:

```python
from crewai_custom_tools import StandardizedRiskScoringTool

tool = StandardizedRiskScoringTool()
risk = tool.run({"ticker": "AAPL", "asset_class": "stock", "market_data": market_data})

print(f"Risk Score: {risk['risk_score']}")
print(f"Risk Factors: {risk['risk_factors']}")
```

#### VolatilityAnalysisTool — NOT IMPLEMENTED

There is no `VolatilityAnalysisTool` class or
`finwiz/tools/volatility_analysis_tool.py` module anywhere in the codebase.
Volatility metrics are produced as part of `QuantitativeAnalysisTool`'s
output (see above), not by a standalone tool.

### Web Research Tools

Tools for gathering news, sentiment, and market research.

#### StandardizedSentimentAnalysisTool

Analyzes market sentiment from news and social media. The class is named
`StandardizedSentimentAnalysisTool`, not `StandardizedSentimentTool`
(that name does not exist and importing it raises `ImportError`).

**Purpose**: Gauge market sentiment for investment decisions

**Input**: Ticker symbol and analysis timeframe

**Output**: Sentiment analysis results

**Example**:

```python
from finwiz.tools.standardized_sentiment_tool import StandardizedSentimentAnalysisTool

tool = StandardizedSentimentAnalysisTool()
sentiment = tool.run("AAPL")

print(f"Mean Score: {sentiment['mean_score']}")
print(f"Counts: {sentiment['counts']}")
```

**Output Schema**: `MarketSentiment` (`src/finwiz/schemas/stock.py:81`)

**Output Fields** (the real model, not the sentiment_score/category/
news_count/social_mentions/trend/themes shape previously documented here):

- `schema_version`: Schema version integer
- `ticker`: Ticker symbol
- `mean_score`: Aggregated sentiment score (-1.0 to 1.0)
- `counts`: Dict of `pos`/`neu`/`neg` article counts
- `top_pos`: Top positive headlines (`SentimentItem` list)
- `top_neg`: Top negative headlines (`SentimentItem` list)

#### NewsAnalysisTool — NOT IMPLEMENTED

There is no `NewsAnalysisTool` class or `finwiz/tools/news_analysis_tool.py`
module anywhere in the codebase. News-driven analysis is covered by
`StandardizedSentimentAnalysisTool` above and by
`AlphaVantageNewsSentimentTool` (from `crewai_custom_tools`).

### Validation Tools

Tools for data validation and quality assurance.

#### TickerExistenceValidationTool

Validates ticker symbols and ensures data availability (central `crewai_custom_tools` package).

**Purpose**: Verify ticker symbols are valid and tradeable

**Input**: Ticker symbol (string)

**Output**: Validation result

**Example**:

```python
from crewai_custom_tools import TickerExistenceValidationTool

tool = TickerExistenceValidationTool()
validation = tool.run("AAPL")

print(f"Valid: {validation['is_valid']}")
print(f"Exchange: {validation['exchange']}")
```

**Output Schema**: `ValidatedTicker`

**Output Fields**:

- `ticker`: Validated ticker symbol
- `is_valid`: Boolean validation result
- `exchange`: Primary exchange
- `asset_type`: Asset type classification
- `currency`: Trading currency
- `market_status`: Market status (open/closed)

#### DataQualityTool — NOT IMPLEMENTED

There is no `DataQualityTool` class or `finwiz/tools/data_quality_tool.py`
module anywhere in the codebase. Data-quality validation instead lives in
`finwiz.quantitative.data_validators` and the `finwiz.validation` package.

## Tool Configuration

### Environment Variables

Configure tool behavior through environment variables:

```bash
# API Configuration
YAHOO_FINANCE_TIMEOUT=30
ALPHA_VANTAGE_TIMEOUT=60
SEC_API_TIMEOUT=120

# Rate Limiting
YAHOO_FINANCE_RATE_LIMIT=60
SEC_API_RATE_LIMIT=10

# Data Quality
DATA_FRESHNESS_THRESHOLD_HOURS=24
MIN_DATA_QUALITY_SCORE=0.8
ENABLE_DATA_VALIDATION=true
```

### Tool Initialization

Most tools can be initialized with custom parameters:

```python
# Basic initialization
tool = QuantitativeAnalysisTool(asset_class="stock")

# Custom configuration
tool = QuantitativeAnalysisTool(asset_class="stock", lookback_days=252, confidence_level=0.95, enable_caching=True)
```

### Tool Factories

Use tool factories for standardized tool sets. `get_stock_crew_tools` only
accepts `include_quantitative`, `include_valuation`, and `prefetched_data` —
passing `include_rag` or `collection_suffix` raises `TypeError`.
`get_minimal_risk_tools` is not in `tool_factories` at all; it lives in
`finwiz.crews.helpers.tool_routing` (re-exported from `finwiz.crews.helpers`):

```python
from finwiz.tools.tool_factories import get_stock_crew_tools
from finwiz.crews.helpers import get_minimal_risk_tools

# Get complete tool set for stock analysis
tools = get_stock_crew_tools(
    include_quantitative=True,
    include_valuation=True,
)

# Get minimal tool set for risk assessment
minimal_tools = get_minimal_risk_tools("stock")
```

## Error Handling

### Common Error Types

Tools use standardized error handling:

```python
# API timeout error
{"error": "TimeoutError", "message": "API request timed out", "details": {"timeout_seconds": 30, "retry_suggested": True}}

# Data validation error
{"error": "ValidationError", "message": "Invalid ticker format", "details": {"ticker": "INVALID", "expected_format": "1-5 uppercase letters"}}

# Rate limit error
{"error": "RateLimitError", "message": "API rate limit exceeded", "details": {"retry_after_seconds": 60, "current_limit": "5 requests/minute"}}
```

### Retry Logic

Tools implement automatic retry with exponential backoff:

```python
# Retry configuration
max_retries = 3
base_delay = 1.0  # seconds
max_delay = 60.0  # seconds
backoff_factor = 2.0
```

### Graceful Degradation

Tools provide fallback behavior when primary data sources fail:

```python
# Primary data source
try:
    data = primary_api.get_data(ticker)
except APIError:
    # Fallback to secondary source
    data = fallback_api.get_data(ticker)
    data["data_source"] = "fallback"
    data["confidence"] = 0.8  # Reduced confidence
```

## Performance Optimization

### Caching

Enable caching for expensive operations:

```python
# Enable caching with TTL
tool = QuantitativeAnalysisTool(
    enable_caching=True,
    cache_ttl=3600,  # 1 hour
)
```

### Batch Processing

Some tools support batch processing:

```python
# Batch ticker validation
tool = TickerExistenceValidationTool()
results = tool.run_batch(["AAPL", "MSFT", "GOOGL"])
```

### Async Operations

Use async versions for better performance:

```python
import asyncio


# Async tool execution
async def analyze_multiple_tickers(tickers):
    tool = QuantitativeAnalysisTool(asset_class="stock")

    tasks = [tool.run_async(ticker) for ticker in tickers]
    results = await asyncio.gather(*tasks)

    return dict(zip(tickers, results))
```

## Best Practices

### Tool Selection

Choose appropriate tools for your analysis needs:

- **Basic company info**: `YahooFinanceTickerInfoTool`
- **Fundamental analysis**: `EnhancedSECAnalysisTool`
- **Technical analysis**: `QuantitativeAnalysisTool` (`TechnicalIndicatorsTool` does not exist — see `finwiz.quantitative.technical` instead)
- **Risk assessment**: `StandardizedRiskScoringTool` (`VolatilityAnalysisTool` does not exist)
- **Market sentiment**: `StandardizedSentimentAnalysisTool`

### Input Validation

Always validate inputs before tool execution:

```python
# Validate ticker format
if not re.match(r"^[A-Z]{1,5}$", ticker):
    raise ValueError(f"Invalid ticker format: {ticker}")

# Validate asset class
if asset_class not in ["stock", "etf", "crypto"]:
    raise ValueError(f"Invalid asset class: {asset_class}")
```

### Output Processing

Process tool outputs consistently:

```python
# Check for errors
if "error" in result:
    logger.error(f"Tool execution failed: {result['error']}")
    return None

# Validate required fields
required_fields = ["price", "volume", "market_cap"]
missing_fields = [f for f in required_fields if f not in result]
if missing_fields:
    logger.warning(f"Missing fields: {missing_fields}")
```

### Resource Management

Manage resources efficiently:

```python
# Use context managers for tools with resources
with QuantitativeAnalysisTool(asset_class="stock") as tool:
    result = tool.run("AAPL")
    # Tool resources automatically cleaned up

# Explicit cleanup for long-running processes
tool = QuantitativeAnalysisTool(asset_class="stock")
try:
    result = tool.run("AAPL")
finally:
    tool.cleanup()
```

## Integration Examples

### Crew Integration

Use tools within CrewAI crews:

```python
from crewai import Agent, Task, Crew


@agent
def analyst(self) -> Agent:
    return Agent(config=self.agents_config["analyst"], tools=[YahooFinanceTickerInfoTool(), QuantitativeAnalysisTool(asset_class="stock"), StandardizedRiskScoringTool()])
```

### Custom Tool Development

For current guidance on building custom tools, see `src/finwiz/tools/CLAUDE.md`
(local tools extend `crewai.tools.BaseTool` directly; there is no
`finwiz.tools.base_tool` module).

## Troubleshooting

### Common Issues

**Issue**: Tool execution timeout

```python
# Solution: Increase timeout or check network connectivity
tool = YahooFinanceTickerInfoTool(timeout=60)
```

**Issue**: Rate limit exceeded

```python
# Solution: Add delays or reduce request frequency
import time

time.sleep(1)  # Add delay between requests
```

**Issue**: Invalid ticker symbol

```python
# Solution: Validate ticker before tool execution
validation_tool = TickerExistenceValidationTool()
if validation_tool.run(ticker)["is_valid"]:
    result = analysis_tool.run(ticker)
```

**Issue**: Missing data fields

`DataQualityTool` does not exist. Data-quality validation lives in
`finwiz.quantitative.data_validators` and `finwiz.validation` — use those
modules directly rather than a crew tool.

## Related Documentation

- **[Crews Reference](crews.md)** - How crews use tools
- **[Schemas Reference](schemas.md)** - Tool output schemas

---

**Version**: 2.0
**Last Updated**: 2025-10-26
