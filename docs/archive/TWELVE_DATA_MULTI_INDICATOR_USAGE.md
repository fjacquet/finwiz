# Twelve Data Multi-Indicator Tool Usage Guide

## Overview

The `TwelveDataMultiIndicatorTool` allows you to fetch multiple technical indicators (RSI, MACD, Bollinger Bands) in a single call, optimizing API usage and reducing latency.

## Benefits

- **Single API Call**: Fetch RSI, MACD, and Bollinger Bands together
- **Optimized Performance**: Reduces API calls from 3 to 1
- **Consistent Parameters**: All indicators use the same symbol and interval
- **Enhanced Insights**: Optional Perplexity Sonar integration for market context

## Installation

The tool is already integrated into FinWiz. Ensure you have the `TWELVE_DATA_API_KEY` environment variable set:

```bash
export TWELVE_DATA_API_KEY="your_api_key_here"
```

## Basic Usage

### Python API

```python
from finwiz.tools.twelve_data_multi_indicator_tool import TwelveDataMultiIndicatorTool

# Create tool instance
tool = TwelveDataMultiIndicatorTool()

# Fetch all indicators with default parameters
result = tool._run(
    symbol="AAPL",
    interval="1day",
    indicators=["rsi", "macd", "bbands"]
)

print(result)
```

### Custom Parameters

```python
# Customize indicator parameters
result = tool._run(
    symbol="SRECHA.SW",
    interval="1day",
    indicators=["rsi", "macd", "bbands"],
    rsi_period=14,           # RSI period
    macd_fast=12,            # MACD fast period
    macd_slow=26,            # MACD slow period
    macd_signal=9,           # MACD signal period
    bbands_period=20,        # Bollinger Bands period
    bbands_stddev=2,         # Bollinger Bands std dev
    outputsize=100           # Number of data points
)
```

### Fetch Specific Indicators

```python
# Fetch only RSI and MACD
result = tool._run(
    symbol="BTC/USD",
    interval="1h",
    indicators=["rsi", "macd"]
)

# Fetch only Bollinger Bands
result = tool._run(
    symbol="SPY",
    interval="1day",
    indicators=["bbands"],
    bbands_period=20,
    bbands_stddev=2
)
```

## Integration with CrewAI

### Adding to Tool Factory

```python
from finwiz.tools.twelve_data_multi_indicator_tool import TwelveDataMultiIndicatorTool

def get_stock_crew_tools():
    """Get tools for stock analysis crew."""
    return [
        TwelveDataMultiIndicatorTool(),
        # ... other tools
    ]
```

### Using in Agent Tasks

```yaml
# config/tasks.yaml
technical_analysis_task:
  description: >
    Perform comprehensive technical analysis for {ticker} using multiple indicators.
    
    Use TwelveDataMultiIndicatorTool to fetch RSI, MACD, and Bollinger Bands in one call:
    - symbol: {ticker}
    - interval: 1day
    - indicators: ["rsi", "macd", "bbands"]
    
    Analyze the combined indicators to identify:
    - Trend direction (MACD)
    - Momentum strength (RSI)
    - Volatility and support/resistance (Bollinger Bands)
    
  expected_output: "Technical analysis with buy/sell signals"
  agent: technical_analyst
```

## Migration from Single Indicator Calls

### Before (3 separate calls)

```python
# Old approach - 3 API calls
rsi_tool = TwelveDataIndicatorTool()
macd_tool = TwelveDataIndicatorTool()
bbands_tool = TwelveDataIndicatorTool()

rsi_result = rsi_tool._run(
    symbol="SRECHA.SW",
    indicator="rsi",
    interval="1day",
    length=14
)

macd_result = macd_tool._run(
    symbol="SRECHA.SW",
    indicator="macd",
    interval="1day",
    fast_period=12,
    slow_period=26,
    signal_period=9
)

bbands_result = bbands_tool._run(
    symbol="SRECHA.SW",
    indicator="bbands",
    interval="1day",
    length=20
)
```

### After (1 combined call)

```python
# New approach - 1 API call
multi_tool = TwelveDataMultiIndicatorTool()

result = multi_tool._run(
    symbol="SRECHA.SW",
    interval="1day",
    indicators=["rsi", "macd", "bbands"],
    rsi_period=14,
    macd_fast=12,
    macd_slow=26,
    macd_signal=9,
    bbands_period=20,
    bbands_stddev=2
)
```

## Response Format

The tool returns a formatted string with all indicator results:

```
# 📊 Multi-Indicator Technical Analysis: AAPL

**Interval**: 1day
**Indicators**: RSI, MACD, BBANDS

## RSI Analysis
```json
{
  "meta": {...},
  "values": [
    {"datetime": "2025-01-10", "rsi": 65.5},
    ...
  ]
}
```

## MACD Analysis
```json
{
  "meta": {...},
  "values": [
    {"datetime": "2025-01-10", "macd": 1.2, "macd_signal": 0.8, "macd_hist": 0.4},
    ...
  ]
}
```

## BBANDS Analysis
```json
{
  "meta": {...},
  "values": [
    {"datetime": "2025-01-10", "upper_band": 152.5, "middle_band": 150.0, "lower_band": 147.5},
    ...
  ]
}
```

## 🔍 Market Analysis Insights (Perplexity Sonar)
Found 5 recent technical analysis articles:

1. 📊 **Technical Analysis: AAPL Shows Strong Momentum**
   - Publisher: MarketWatch
   - Relevance: 0.95
   - Summary: Apple stock shows bullish technical indicators...
   - URL: https://example.com/article

...

## 📈 Enhanced Analysis Summary
This analysis combines 3 technical indicators from Twelve Data with 5 recent market analysis articles from Perplexity Sonar. The combination provides both quantitative indicators and current market sentiment.

**Note**: Combine multiple technical indicators with fundamental analysis for investment decisions.
```

## Parameters Reference

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `symbol` | str | Required | Ticker symbol (e.g., AAPL, BTC/USD, SPY) |
| `interval` | str | "1day" | Time interval (1min, 5min, 1h, 1day, etc.) |
| `indicators` | list[str] | ["rsi", "macd", "bbands"] | List of indicators to fetch |
| `rsi_period` | int | 14 | RSI calculation period |
| `macd_fast` | int | 12 | MACD fast period |
| `macd_slow` | int | 26 | MACD slow period |
| `macd_signal` | int | 9 | MACD signal period |
| `bbands_period` | int | 20 | Bollinger Bands period |
| `bbands_stddev` | int | 2 | Bollinger Bands standard deviation |
| `outputsize` | int | 100 | Number of data points to return |

## Error Handling

The tool handles errors gracefully:

```python
# Missing API key
result = tool._run(symbol="AAPL")
# Returns: "Error: TWELVE_DATA_API_KEY environment variable not set"

# Invalid symbol
result = tool._run(symbol="INVALID")
# Returns: Error message from Twelve Data API

# Network error
# Returns: "Error performing multi-indicator analysis for AAPL: <error details>"
```

## Best Practices

1. **Use Default Parameters**: Start with default parameters for standard analysis
2. **Batch Indicators**: Always fetch multiple indicators together when possible
3. **Consistent Intervals**: Use the same interval for all indicators
4. **Error Handling**: Always check for error messages in the response
5. **Rate Limiting**: Respect Twelve Data API rate limits (handled automatically)

## Performance Comparison

| Approach | API Calls | Latency | Cost |
|----------|-----------|---------|------|
| Single Indicator Tool (3 calls) | 3 | ~3-6 seconds | 3 credits |
| Multi-Indicator Tool (1 call) | 1 | ~1-2 seconds | 1 credit |

**Savings**: 66% reduction in API calls, 50-66% reduction in latency

## Troubleshooting

### Issue: "TWELVE_DATA_API_KEY environment variable not set"

**Solution**: Set the environment variable:
```bash
export TWELVE_DATA_API_KEY="your_api_key_here"
```

### Issue: Rate limit exceeded

**Solution**: The tool uses automatic rate limiting. If you still hit limits, reduce the frequency of calls or upgrade your Twelve Data plan.

### Issue: Invalid symbol error

**Solution**: Verify the symbol format for your asset type:
- Stocks: `AAPL`, `MSFT`
- Crypto: `BTC/USD`, `ETH/USD`
- ETFs: `SPY`, `QQQ`

## Related Documentation

- [Twelve Data API Documentation](https://twelvedata.com/docs)
- [FinWiz Testing Standards](.kiro/steering/testing-standards.md)
- [FinWiz Technical Standards](.kiro/steering/tech.md)

## Support

For issues or questions:
1. Check the [Twelve Data API status](https://status.twelvedata.com/)
2. Review the tool logs for detailed error messages
3. Verify your API key has sufficient credits
4. Contact FinWiz support with error details
