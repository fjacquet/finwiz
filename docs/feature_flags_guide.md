# FinWiz Feature Flags & Configuration Guide

This guide explains how to use the feature flag system and configuration manager in FinWiz for gradual rollouts, graceful degradation, and environment management.

## Overview

The FinWiz feature flag system provides:

- **Environment-based configuration** for gradual rollouts
- **Circuit breaker patterns** for service reliability
- **Graceful degradation** when services fail
- **Centralized API key management** with validation
- **Multiple evaluation strategies** (boolean, percentage, user lists, time windows)

## Quick Start

### Basic Feature Flag Usage

```python
from finwiz.utils.feature_flags import is_feature_enabled, execute_with_feature_flag

# Check if a feature is enabled
if is_feature_enabled("enhanced_sentiment_analysis"):
    result = perform_enhanced_analysis()
else:
    result = perform_basic_analysis()

# Execute with automatic fallback
result = execute_with_feature_flag(
    "enhanced_sentiment_analysis",
    primary_function=perform_enhanced_analysis,
    fallback_function=perform_basic_analysis,
    ticker="AAPL"
)
```

### Configuration Management

```python
from finwiz.utils.configuration_manager import validate_startup_configuration, get_api_key

# Validate all required API keys at startup
try:
    validate_startup_configuration()
    print("✅ All required API keys configured")
except ConfigurationError as e:
    print(f"❌ Configuration error: {e.remediation_guidance}")

# Get API key for a service
openai_key = get_api_key("OpenAI")
if openai_key:
    # Use the API key
    pass
```

### Graceful Degradation

```python
from finwiz.utils.graceful_degradation import execute_with_degradation

# Execute with automatic retry and fallback
result = await execute_with_degradation(
    service_name="alpha_vantage",
    primary_func=fetch_market_data,
    fallback_func=use_cached_data,
    cache_key="market_data_AAPL",
    ticker="AAPL"
)
```

## Environment Variables

### Feature Flag Configuration

Control feature flags using environment variables:

```bash
# Enable/disable features
FF_ENHANCED_SENTIMENT=true
FF_ADVANCED_TECHNICAL=false
FF_CHART_ANALYSIS=true
FF_TWELVE_DATA=true
FF_PERPLEXITY_RESEARCH=false

# Percentage rollouts (0-100)
FF_ENHANCED_SENTIMENT_ROLLOUT=75.0
FF_ADVANCED_TECHNICAL_ROLLOUT=50.0

# Circuit breaker thresholds
FF_CHART_BREAKER_THRESHOLD=3
FF_CHART_BREAKER_TIMEOUT=300
FF_TWELVE_DATA_BREAKER_THRESHOLD=5
FF_PERPLEXITY_BREAKER_THRESHOLD=5
FF_PERPLEXITY_BREAKER_TIMEOUT=300
```

### API Key Configuration

Configure required API keys:

```bash
# Required keys
OPENAI_API_KEY=sk-your-openai-key-here
SERPER_API_KEY=your-serper-key-here
FIRECRAWL_API_KEY=your-firecrawl-key-here
ALPHA_VANTAGE_API_KEY=your-alpha-vantage-key-here

# Optional keys (controlled by feature flags)
CHART_IMG_API_KEY=your-chart-img-key-here
TWELVE_DATA_API_KEY=your-twelve-data-key-here
COINMARKETCAP_API_KEY=your-coinmarketcap-key-here
KRAKEN_API_KEY=your-kraken-key-here
PPLX_API_KEY=your-perplexity-api-key-here
PPLX_API_KEY=your-perplexity-api-key-here
```

## Available Feature Flags

### Core Features

| Flag Name | Description | Default | Strategy |
|-----------|-------------|---------|----------|
| `enhanced_sentiment_analysis` | Multi-source sentiment analysis | Enabled | Percentage |
| `advanced_technical_analysis` | Advanced technical indicators | Enabled | Percentage |
| `chart_analysis` | Chart-img API integration | Enabled | Circuit Breaker |
| `twelve_data_integration` | Twelve Data API integration | Enabled | Circuit Breaker |
| `perplexity_research` | Perplexity Sonar Search integration | Disabled | Circuit Breaker |
| `strict_validation` | Strict Pydantic validation | Enabled | Percentage |
| `async_execution` | Asynchronous task execution | Enabled | Boolean |
| `intelligent_caching` | Advanced caching system | Enabled | Boolean |
| `portfolio_review` | Portfolio review functionality | Enabled | Boolean |

### Feature Flag Strategies

1. **Boolean**: Simple on/off switch
2. **Percentage**: Gradual rollout to percentage of users
3. **User List**: Enable for specific users only
4. **Time Window**: Enable during specific time periods
5. **Circuit Breaker**: Automatic disable on repeated failures

## Circuit Breaker Pattern

The circuit breaker pattern automatically disables failing services:

```python
# Configure circuit breaker
degradation_manager = get_degradation_manager()
degradation_manager.update_service_config(
    "external_api",
    error_threshold=5,        # Open circuit after 5 failures
    circuit_breaker_timeout=300,  # Wait 5 minutes before retry
    recovery_threshold=2      # Close circuit after 2 successes
)

# The circuit breaker will automatically:
# 1. Track failures and successes
# 2. Open circuit when threshold is exceeded
# 3. Use fallback during circuit open state
# 4. Attempt recovery after timeout
# 5. Close circuit on successful recovery
```

## Graceful Degradation Strategies

### Fallback Strategies

1. **Disable**: Completely disable the feature
2. **Cached Only**: Use cached data when available
3. **Reduced Functionality**: Provide limited feature set
4. **Default Values**: Return sensible defaults
5. **Retry with Backoff**: Exponential backoff retry

### Example Implementation

```python
async def analyze_stock_with_degradation(ticker: str):
    # Primary function with potential failure
    async def fetch_live_data():
        response = await external_api.get_stock_data(ticker)
        return response.json()
    
    # Fallback function
    def use_cached_data():
        return cache.get(f"stock_data_{ticker}") or {
            "symbol": ticker,
            "price": 0.0,
            "status": "unavailable"
        }
    
    # Execute with automatic degradation
    return await execute_with_degradation(
        service_name="stock_api",
        primary_func=fetch_live_data,
        fallback_func=use_cached_data,
        cache_key=f"stock_data_{ticker}"
    )
```

## Monitoring and Health Checks

### Service Health Monitoring

```python
from finwiz.utils.graceful_degradation import get_degradation_manager

manager = get_degradation_manager()

# Get health for specific service
health = manager.get_service_health("alpha_vantage")
print(f"Status: {health.status}")
print(f"Error Count: {health.error_count}")
print(f"Success Count: {health.success_count}")

# Get system-wide health summary
summary = manager.get_system_health_summary()
print(f"Overall Health: {summary['overall_health']}")
print(f"Healthy Services: {summary['healthy_services']}/{summary['total_services']}")
```

### Feature Flag Status

```python
from finwiz.utils.feature_flags import get_feature_flags

flags = get_feature_flags()

# Get status of specific flag
status = flags.get_flag_status("enhanced_sentiment_analysis")
print(f"Enabled: {status['enabled']}")
print(f"Strategy: {status['strategy']}")

# List all flags
all_flags = flags.list_all_flags()
for name, status in all_flags.items():
    print(f"{name}: {status['enabled']}")
```

## Best Practices

### 1. Feature Flag Naming

Use descriptive, hierarchical names:
- `enhanced_sentiment_analysis` ✅
- `sentiment` ❌
- `twelve_data_integration` ✅
- `api_integration` ❌

### 2. Gradual Rollouts

Start with small percentages and increase gradually:
```bash
# Week 1: 10% rollout
FF_NEW_FEATURE_ROLLOUT=10.0

# Week 2: 25% rollout
FF_NEW_FEATURE_ROLLOUT=25.0

# Week 3: 50% rollout
FF_NEW_FEATURE_ROLLOUT=50.0

# Week 4: 100% rollout
FF_NEW_FEATURE_ROLLOUT=100.0
```

### 3. Circuit Breaker Configuration

Configure appropriate thresholds based on service characteristics:
- **High-reliability services**: Lower thresholds (3-5 failures)
- **External APIs**: Higher thresholds (5-10 failures)
- **Critical services**: Shorter timeouts (1-5 minutes)
- **Non-critical services**: Longer timeouts (10-30 minutes)

### 4. Fallback Design

Always provide meaningful fallbacks:
- **Cached data** for real-time services
- **Default values** for configuration
- **Simplified functionality** for complex features
- **Error messages** with guidance for users

### 5. Testing

Test both enabled and disabled states:
```python
def test_feature_enabled_and_disabled():
    # Test with feature enabled
    with patch.dict(os.environ, {"FF_ENHANCED_SENTIMENT": "true"}):
        result = analyze_sentiment("AAPL")
        assert "trending_topics" in result
    
    # Test with feature disabled
    with patch.dict(os.environ, {"FF_ENHANCED_SENTIMENT": "false"}):
        result = analyze_sentiment("AAPL")
        assert result["source"] == "basic"
```

## Troubleshooting

### Common Issues

1. **Feature not working despite being enabled**
   - Check API key configuration
   - Verify service health status
   - Check circuit breaker state

2. **Configuration errors at startup**
   - Verify all required API keys are set
   - Check environment variable names
   - Review feature flag dependencies

3. **Services frequently failing**
   - Check API rate limits
   - Verify network connectivity
   - Review error logs for patterns

### Debug Commands

```python
# Check configuration status
from finwiz.utils.configuration_manager import get_configuration_manager
config = get_configuration_manager()
summary = config.get_configuration_summary()
print(summary)

# Check feature flag status
from finwiz.utils.feature_flags import get_feature_flags
flags = get_feature_flags()
print(flags.list_all_flags())

# Check service health
from finwiz.utils.graceful_degradation import get_degradation_manager
manager = get_degradation_manager()
print(manager.get_system_health_summary())
```

## Perplexity Sonar Integration

The `PERPLEXITY_RESEARCH` feature flag enables Perplexity Sonar Search integration as a supplementary research capability for FinWiz analyst crews. This integration provides enhanced financial research with real-time web search capabilities while maintaining operational stability through circuit breaker protection and graceful fallback.

### Configuration

#### Environment Variables

```bash
# Enable the feature flag
FF_PERPLEXITY_RESEARCH=true

# Required: Perplexity API key
PPLX_API_KEY=your-perplexity-api-key-here

# Optional: Circuit breaker configuration
FF_PERPLEXITY_BREAKER_THRESHOLD=5      # Open circuit after 5 failures
FF_PERPLEXITY_BREAKER_TIMEOUT=300      # Wait 5 minutes before retry
```

#### API Key Setup

1. **Obtain API Key**: Sign up at [Perplexity AI](https://www.perplexity.ai/) and get your API key
2. **Set Environment Variable**: Add `PPLX_API_KEY=your-key-here` to your `.env` file
3. **Verify Configuration**: The system will validate the API key at startup

#### Security Considerations

- **Never commit API keys** to version control
- **Use environment variables** for all deployments
- **Rotate keys regularly** as per security best practices
- **Monitor usage** to detect unauthorized access

### Circuit Breaker Behavior

The Perplexity integration implements a circuit breaker pattern for reliability:

1. **Closed State** (Normal): API calls proceed normally
2. **Open State** (Failing): After 5 consecutive failures, circuit opens
3. **Half-Open State** (Testing): After 300 seconds, attempts one test call
4. **Recovery**: Successful test call closes the circuit

#### Circuit Breaker States

```python
# Check circuit breaker status
from finwiz.utils.feature_flags import get_feature_flags

flags = get_feature_flags()
status = flags.get_flag_status("perplexity_research")

if status.get('circuit_breaker'):
    cb = status['circuit_breaker']
    print(f"State: {cb['state']}")  # CLOSED, OPEN, or HALF_OPEN
    print(f"Failures: {cb['failure_count']}/{cb['threshold']}")
    print(f"Next retry: {cb['next_retry_time']}")
```

### Integration Points

Perplexity enhances multiple analysis tools across the FinWiz platform:

#### Enhanced Sentiment Analysis

```python
from finwiz.tools.enhanced_sentiment_tool import EnhancedSentimentAnalysisTool

# Initialize tool (automatically detects feature flag)
tool = EnhancedSentimentAnalysisTool()

# Run analysis with optional Perplexity enhancement
result = tool._run(ticker="AAPL", asset_type="stock")

# Check if Perplexity data was included
if result.get("sonar_articles"):
    print(f"Enhanced with {len(result['sonar_articles'])} Sonar insights")
    for article in result["sonar_articles"]:
        print(f"- {article['title']} ({article['publisher']})")
```

#### Technical Analysis Enhancement

```python
# Technical analysis tools automatically include Perplexity insights
# when the feature flag is enabled, providing:
# - Recent analyst price targets
# - Technical commentary from financial news
# - Market sentiment indicators
```

#### Fundamental Analysis Enhancement

```python
# Fundamental analysis tools leverage Perplexity for:
# - Recent earnings reports and SEC filings
# - Management commentary and guidance
# - Regulatory updates and compliance news
```

### Usage Examples

#### Basic Integration Check

```python
from finwiz.utils.feature_flags import is_feature_enabled

if is_feature_enabled("perplexity_research"):
    print("✅ Perplexity integration is active")
    # Enhanced analysis will include Sonar results
else:
    print("ℹ️ Using traditional data sources only")
    # Analysis proceeds with existing providers
```

#### Manual Perplexity Search

```python
from finwiz.tools.perplexity_search_tool import PerplexitySearchTool

# Direct usage of Perplexity tool
tool = PerplexitySearchTool()
result = tool._run(query="AAPL earnings Q4 2024 financial analysis")

print(f"Search results: {result}")
```

#### Error Handling Example

```python
from finwiz.utils.feature_flags import execute_with_feature_flag

# Automatic fallback on Perplexity failure
def enhanced_analysis(ticker):
    # This function uses Perplexity
    return get_perplexity_insights(ticker)

def basic_analysis(ticker):
    # This function uses traditional sources
    return get_yahoo_finance_data(ticker)

# Execute with automatic fallback
result = execute_with_feature_flag(
    "perplexity_research",
    primary_function=enhanced_analysis,
    fallback_function=basic_analysis,
    ticker="AAPL"
)
```

### Fallback Strategy

When Perplexity is unavailable, the system gracefully degrades:

#### Analysis Tools Fallback

- **Sentiment Analysis**: Yahoo Finance + Alpha Vantage news
- **Technical Analysis**: Traditional technical indicators only
- **Fundamental Analysis**: SEC EDGAR + standard financial data
- **Crypto Analysis**: CoinMarketCap + exchange data
- **ETF Analysis**: Fund prospectus + holdings data

#### Fallback Triggers

1. **API Key Missing**: Logs warning, disables integration
2. **Rate Limit Exceeded**: Implements exponential backoff
3. **Network Timeout**: Falls back to cached data if available
4. **Circuit Breaker Open**: Uses traditional data sources
5. **Invalid Response**: Logs error, continues with existing data

### Performance Monitoring

#### Response Time Monitoring

```python
# Monitor Perplexity API performance
from finwiz.utils.monitoring import get_performance_metrics

metrics = get_performance_metrics("perplexity_search")
print(f"Average response time: {metrics['avg_response_time']}ms")
print(f"Success rate: {metrics['success_rate']}%")
print(f"Rate limit hits: {metrics['rate_limit_count']}")
```

#### Health Check

```python
from finwiz.utils.graceful_degradation import get_degradation_manager

manager = get_degradation_manager()
health = manager.get_service_health("perplexity")

print(f"Service Status: {health.status}")
print(f"Success Rate: {health.success_rate}%")
print(f"Last Error: {health.last_error_time}")
```

### Troubleshooting

#### Common Issues

1. **Feature not working despite being enabled**
   ```bash
   # Check API key configuration
   echo $PPLX_API_KEY
   
   # Verify feature flag
   echo $FF_PERPLEXITY_RESEARCH
   
   # Check service health
   python -c "from finwiz.utils.graceful_degradation import get_degradation_manager; print(get_degradation_manager().get_service_health('perplexity'))"
   ```

2. **Rate limiting issues**
   ```python
   # Check rate limit status
   from finwiz.utils.feature_flags import get_feature_flags
   flags = get_feature_flags()
   status = flags.get_flag_status("perplexity_research")
   
   if 'rate_limit' in status:
       print(f"Rate limit: {status['rate_limit']}")
       print(f"Reset time: {status['rate_limit_reset']}")
   ```

3. **Circuit breaker frequently opening**
   ```bash
   # Increase failure threshold
   FF_PERPLEXITY_BREAKER_THRESHOLD=10
   
   # Increase timeout
   FF_PERPLEXITY_BREAKER_TIMEOUT=600
   ```

#### Debug Commands

```python
# Complete diagnostic check
from finwiz.utils.configuration_manager import validate_startup_configuration
from finwiz.utils.feature_flags import get_feature_flags
from finwiz.utils.graceful_degradation import get_degradation_manager

# Check configuration
try:
    validate_startup_configuration()
    print("✅ Configuration valid")
except Exception as e:
    print(f"❌ Configuration error: {e}")

# Check feature flag
flags = get_feature_flags()
perplexity_status = flags.get_flag_status("perplexity_research")
print(f"Perplexity flag: {perplexity_status}")

# Check service health
manager = get_degradation_manager()
health = manager.get_service_health("perplexity")
print(f"Service health: {health}")
```

#### Performance Benchmarking

```python
# Run performance benchmark
import time
from finwiz.tools.perplexity_search_tool import PerplexitySearchTool

tool = PerplexitySearchTool()

# Measure response time
start_time = time.time()
result = tool._run(query="AAPL financial analysis")
end_time = time.time()

response_time = (end_time - start_time) * 1000
print(f"Response time: {response_time:.2f}ms")

# Check if within acceptable limits (≤2× baseline)
baseline_ms = 1000  # Assume 1 second baseline
if response_time <= 2 * baseline_ms:
    print("✅ Performance within acceptable limits")
else:
    print("⚠️ Performance degraded, consider circuit breaker adjustment")
```

### Best Practices

#### Gradual Rollout

```bash
# Start with feature disabled for testing
FF_PERPLEXITY_RESEARCH=false

# Enable for development/testing
FF_PERPLEXITY_RESEARCH=true

# Monitor performance and error rates before full rollout
```

#### Error Handling

```python
# Always implement proper error handling
try:
    if is_feature_enabled("perplexity_research"):
        enhanced_data = get_perplexity_insights(ticker)
        traditional_data = get_traditional_data(ticker)
        return combine_data_sources(enhanced_data, traditional_data)
    else:
        return get_traditional_data(ticker)
except Exception as e:
    logger.warning(f"Perplexity integration failed: {e}")
    return get_traditional_data(ticker)  # Always have fallback
```

#### Monitoring and Alerting

- **Set up alerts** for circuit breaker state changes
- **Monitor response times** and set thresholds
- **Track success/failure rates** for operational insights
- **Log performance metrics** for capacity planning

## Example Integration

See `examples/feature_flag_integration.py` for a complete working example demonstrating:
- Feature flag evaluation
- Configuration management
- Graceful degradation
- Circuit breaker patterns
- Service health monitoring

Run the example:
```bash
uv run python examples/feature_flag_integration.py
```

This will demonstrate the complete feature flag system in action with simulated API calls, failures, and recovery scenarios.