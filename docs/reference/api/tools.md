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
```python
from finwiz.tools.yahoo_finance_ticker_info_tool import YahooFinanceTickerInfoTool

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
from finwiz.tools.enhanced_sec_analysis_tool import EnhancedSECAnalysisTool

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
from finwiz.tools.enhanced_etf_analysis_tool import EnhancedETFAnalysisTool

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
from finwiz.tools.enhanced_crypto_analysis_tool import EnhancedCryptoAnalysisTool

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
    "asset_class": "stock"  # "stock", "etf", or "crypto"
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

#### TechnicalIndicatorsTool

Calculates technical indicators for price analysis.

**Purpose**: Generate technical analysis indicators

**Input**: Ticker symbol and timeframe

**Output**: Dictionary with technical indicators

**Example**:
```python
from finwiz.tools.technical_indicators_tool import TechnicalIndicatorsTool

tool = TechnicalIndicatorsTool()
indicators = tool.run({
    "ticker": "AAPL",
    "timeframe": "1d",
    "period": 252  # 1 year of daily data
})

print(f"RSI: {indicators['rsi']}")
print(f"MACD: {indicators['macd']}")
```

**Output Fields**:
- `rsi`: Relative Strength Index
- `macd`: MACD indicator
- `bollinger_bands`: Bollinger Bands (upper, middle, lower)
- `moving_averages`: SMA and EMA (20, 50, 200 periods)
- `stochastic`: Stochastic oscillator
- `williams_r`: Williams %R

### Risk Assessment Tools

Tools for evaluating investment risks and calculating risk metrics.

#### RiskAssessmentTool

Comprehensive risk analysis for investments.

**Purpose**: Evaluate investment risks across multiple dimensions

**Input**: Asset data and market context

**Output**: Standardized risk assessment

**Example**:
```python
from finwiz.tools.risk_assessment_tool import RiskAssessmentTool

tool = RiskAssessmentTool()
risk = tool.run({
    "ticker": "AAPL",
    "asset_class": "stock",
    "market_data": market_data
})

print(f"Risk Score: {risk['risk_score']}")
print(f"Risk Factors: {risk['risk_factors']}")
```

**Output Schema**: `RiskAssessmentStandardized`

**Output Fields**:
- `risk_score`: Overall risk score (1-10 scale)
- `systematic_risk`: Market/sector risk component
- `idiosyncratic_risk`: Asset-specific risk
- `risk_factors`: List of identified risk factors
- `risk_category`: Risk category classification
- `confidence_level`: Assessment confidence

#### VolatilityAnalysisTool

Specialized volatility analysis and forecasting.

**Purpose**: Analyze price volatility patterns and trends

**Input**: Price history and analysis parameters

**Output**: Volatility analysis results

**Example**:
```python
from finwiz.tools.volatility_analysis_tool import VolatilityAnalysisTool

tool = VolatilityAnalysisTool()
volatility = tool.run({
    "ticker": "AAPL",
    "lookback_days": 252
})

print(f"Current Volatility: {volatility['current_volatility']}")
print(f"Volatility Trend: {volatility['volatility_trend']}")
```

### Web Research Tools

Tools for gathering news, sentiment, and market research.

#### StandardizedSentimentTool

Analyzes market sentiment from news and social media.

**Purpose**: Gauge market sentiment for investment decisions

**Input**: Ticker symbol and analysis timeframe

**Output**: Sentiment analysis results

**Example**:
```python
from finwiz.tools.standardized_sentiment_tool import StandardizedSentimentTool

tool = StandardizedSentimentTool()
sentiment = tool.run("AAPL")

print(f"Sentiment Score: {sentiment['sentiment_score']}")
print(f"News Count: {sentiment['news_count']}")
```

**Output Schema**: `MarketSentiment`

**Output Fields**:
- `sentiment_score`: Overall sentiment (-1 to 1)
- `sentiment_category`: Categorical sentiment
- `news_count`: Number of news articles analyzed
- `social_mentions`: Social media mention count
- `sentiment_trend`: Sentiment trend direction
- `key_themes`: Main sentiment themes

#### NewsAnalysisTool

Comprehensive news analysis and impact assessment.

**Purpose**: Analyze news impact on investment prospects

**Input**: Ticker symbol and date range

**Output**: News analysis summary

**Example**:
```python
from finwiz.tools.news_analysis_tool import NewsAnalysisTool

tool = NewsAnalysisTool()
news = tool.run({
    "ticker": "AAPL",
    "days_back": 30
})

print(f"News Impact: {news['impact_score']}")
print(f"Key Headlines: {news['key_headlines']}")
```

### Validation Tools

Tools for data validation and quality assurance.

#### TickerValidationTool

Validates ticker symbols and ensures data availability.

**Purpose**: Verify ticker symbols are valid and tradeable

**Input**: Ticker symbol (string)

**Output**: Validation result

**Example**:
```python
from finwiz.tools.ticker_validation_tool import TickerValidationTool

tool = TickerValidationTool()
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

#### DataQualityTool

Assesses data quality and freshness for analysis.

**Purpose**: Ensure data meets quality standards for analysis

**Input**: Data source and quality parameters

**Output**: Data quality assessment

**Example**:
```python
from finwiz.tools.data_quality_tool import DataQualityTool

tool = DataQualityTool()
quality = tool.run({
    "data_source": "yahoo_finance",
    "ticker": "AAPL",
    "required_fields": ["price", "volume", "market_cap"]
})

print(f"Quality Score: {quality['quality_score']}")
print(f"Missing Fields: {quality['missing_fields']}")
```

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
ALPHA_VANTAGE_RATE_LIMIT=5
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
tool = QuantitativeAnalysisTool(
    asset_class="stock",
    lookback_days=252,
    confidence_level=0.95,
    enable_caching=True
)
```

### Tool Factories

Use tool factories for standardized tool sets:

```python
from finwiz.tools.tool_factories import get_stock_crew_tools

# Get complete tool set for stock analysis
tools = get_stock_crew_tools(
    include_rag=True,
    include_quantitative=True,
    collection_suffix="stock"
)

# Get minimal tool set for risk assessment
minimal_tools = get_minimal_risk_tools("stock")
```

## Error Handling

### Common Error Types

Tools use standardized error handling:

```python
# API timeout error
{
    "error": "TimeoutError",
    "message": "API request timed out",
    "details": {
        "timeout_seconds": 30,
        "retry_suggested": True
    }
}

# Data validation error
{
    "error": "ValidationError",
    "message": "Invalid ticker format",
    "details": {
        "ticker": "INVALID",
        "expected_format": "1-5 uppercase letters"
    }
}

# Rate limit error
{
    "error": "RateLimitError",
    "message": "API rate limit exceeded",
    "details": {
        "retry_after_seconds": 60,
        "current_limit": "5 requests/minute"
    }
}
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
    cache_ttl=3600  # 1 hour
)
```

### Batch Processing

Some tools support batch processing:

```python
# Batch ticker validation
tool = TickerValidationTool()
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
- **Technical analysis**: `QuantitativeAnalysisTool` + `TechnicalIndicatorsTool`
- **Risk assessment**: `RiskAssessmentTool` + `VolatilityAnalysisTool`
- **Market sentiment**: `StandardizedSentimentTool`

### Input Validation

Always validate inputs before tool execution:

```python
# Validate ticker format
if not re.match(r'^[A-Z]{1,5}$', ticker):
    raise ValueError(f"Invalid ticker format: {ticker}")

# Validate asset class
if asset_class not in ['stock', 'etf', 'crypto']:
    raise ValueError(f"Invalid asset class: {asset_class}")
```

### Output Processing

Process tool outputs consistently:

```python
# Check for errors
if 'error' in result:
    logger.error(f"Tool execution failed: {result['error']}")
    return None

# Validate required fields
required_fields = ['price', 'volume', 'market_cap']
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
    return Agent(
        config=self.agents_config["analyst"],
        tools=[
            YahooFinanceTickerInfoTool(),
            QuantitativeAnalysisTool(asset_class="stock"),
            RiskAssessmentTool()
        ]
    )
```

### Custom Tool Development

Create custom tools following FinWiz patterns:

```python
from finwiz.tools.base_tool import BaseTool

class CustomAnalysisTool(BaseTool):
    def __init__(self, custom_param: str):
        super().__init__()
        self.custom_param = custom_param
    
    def run(self, ticker: str) -> dict:
        # Custom analysis logic
        result = self._perform_analysis(ticker)
        
        # Validate output
        self._validate_output(result)
        
        return result
    
    def _perform_analysis(self, ticker: str) -> dict:
        # Implementation details
        pass
    
    def _validate_output(self, result: dict) -> None:
        # Output validation
        pass
```

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
validation_tool = TickerValidationTool()
if validation_tool.run(ticker)['is_valid']:
    result = analysis_tool.run(ticker)
```

**Issue**: Missing data fields
```python
# Solution: Check data quality and use fallbacks
quality_tool = DataQualityTool()
quality = quality_tool.run({"ticker": ticker})
if quality['quality_score'] < 0.8:
    logger.warning("Low data quality detected")
```

## Related Documentation

- **[Crews Reference](crews.md)** - How crews use tools
- **[Schemas Reference](schemas.md)** - Tool output schemas
- **[Configuration Reference](configuration.md)** - Tool configuration options
- **[Performance Guide](../../how-to/performance_optimization.md)** - Tool optimization

---

**Version**: 2.0  
**Last Updated**: 2025-10-26