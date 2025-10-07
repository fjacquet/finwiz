# System Operations Guide

Complete guide for FinWiz system operations including feedback learning, portfolio monitoring, knowledge base, and integration configuration.

## Table of Contents

1. [Feedback Learning System](#feedback-learning-system)
2. [Portfolio Monitoring](#portfolio-monitoring)
3. [Knowledge Base Strategy](#knowledge-base-strategy)
4. [Intelligent Caching System](#intelligent-caching-system)
5. [Feature Flags & Configuration](#feature-flags--configuration)
6. [Integration Configuration](#integration-configuration)

## Feedback Learning System

### Overview

The Feedback Learning System continuously improves investment discovery by collecting user feedback, tracking performance, and automatically adjusting criteria based on real-world results.

### Components

**1. Feedback Collection**:

- Recommendation acceptance/rejection tracking
- Sentiment analysis (very positive to very negative)
- Confidence ratings (1-5 scale)
- Detailed reasoning collection
- User comments for qualitative insights

**2. Performance Tracking**:

- Alpha calculation vs benchmarks
- Grade maintenance monitoring (A+ retention)
- Risk-adjusted returns (Sharpe, Sortino ratios)
- Drawdown analysis and volatility tracking
- Market regime performance analysis

**3. Learning Engine**:

- Adaptive criteria adjustment based on feedback patterns
- Asset-specific learning for ETFs, stocks, and crypto
- Market regime adaptation
- Statistical significance testing
- Backtesting validation before implementation

### Usage

**Collect Feedback**:

```python
from finwiz.services.feedback_service import get_feedback_service

service = get_feedback_service()

# Submit feedback
await service.submit_feedback(
    recommendation_id="rec_123",
    user_id="user_456",
    accepted=True,
    sentiment="positive",
    confidence=4,
    reasoning="Strong fundamentals and low expense ratio"
)
```

**Track Performance**:

```python
# Track investment performance
await service.track_performance(
    symbol="VTI",
    asset_type="etf",
    performance_data={
        "total_return": 0.12,
        "alpha": 0.02,
        "sharpe_ratio": 1.5,
        "max_drawdown": -0.08
    }
)
```

**Get Learning Insights**:

```python
# Get learning insights
insights = await service.get_learning_insights()

print(f"Total feedback: {insights['total_feedback']}")
print(f"Acceptance rate: {insights['acceptance_rate']:.2%}")
print(f"Criteria adjustments: {len(insights['criteria_adjustments'])}")
```

## Portfolio Monitoring

### Overview

Real-time portfolio monitoring with drift detection, alert generation, and multi-channel notifications.

### Components

**1. Portfolio Monitor**:

- Continuous drift monitoring
- Health dashboard (1-10 scale)
- Alert generation with configurable rules
- Alert lifecycle management

**2. Notification Service**:

- Email notifications (HTML and plain text)
- SMS notifications for critical issues
- User preference management
- Rate limiting and quiet hours

**3. Alert System**:

- Multiple urgency levels (LOW, MEDIUM, HIGH, CRITICAL)
- Configurable thresholds
- Automated monitoring loops
- Error recovery

### Configuration

**Monitoring Rules**:

```python
from finwiz.quantitative.portfolio_monitor import MonitoringRule

rule = MonitoringRule(
    rule_id="portfolio_monitor",
    rule_name="Standard Portfolio Monitoring",
    max_deviation_threshold=0.08,  # 8% threshold
    check_frequency_minutes=60,
    alert_urgency="MEDIUM"
)
```

**Notification Preferences**:

```python
from finwiz.tools.notification_service import NotificationPreferences

preferences = NotificationPreferences(
    user_id="user_123",
    email_enabled=True,
    sms_enabled=True,
    min_alert_level="MEDIUM",
    quiet_hours_start="22:00",
    quiet_hours_end="08:00"
)
```

### Usage

**Start Monitoring**:

```python
from finwiz.quantitative.portfolio_monitor import PortfolioMonitor

monitor = PortfolioMonitor()

# Start monitoring
await monitor.start_monitoring(
    portfolio_config=config,
    monitoring_rule=rule
)
```

**Get Health Dashboard**:

```python
# Get portfolio health
dashboard = await monitor.get_health_dashboard(portfolio_config)

print(f"Health Score: {dashboard.health_score}/10")
print(f"Status: {dashboard.status}")
print(f"Active Alerts: {len(dashboard.active_alerts)}")
```

**Send Notifications**:

```python
from finwiz.tools.notification_service import NotificationService

service = NotificationService()

# Send alert notification
await service.send_notification(
    user_id="user_123",
    alert=alert,
    notification_type="email"
)
```

### Alert Levels

| Level | Threshold | Response Time | Notification |
|-------|-----------|---------------|--------------|
| **CRITICAL** | >10% deviation | Immediate | Email + SMS |
| **HIGH** | 8-10% deviation | 1 hour | Email + SMS |
| **MEDIUM** | 5-8% deviation | 4 hours | Email |
| **LOW** | 3-5% deviation | 24 hours | Email (digest) |

## Knowledge Base Strategy

### Real-Time Information Retrieval

FinWiz uses **real-time information retrieval** instead of a static knowledge base to ensure all financial analysis is based on current data.

### Why Real-Time

**Advantages**:

- Always current data (no staleness)
- Access to entire public web
- No database maintenance overhead
- Captures breaking news and events

**Challenges**:

- Higher API costs
- Slower than cached data
- Rate limiting considerations

### Key Tools

**Web Search**:

- `SerperDevTool` - General web searches
- `FirecrawlScrapeWebsiteTool` - Extract specific URLs
- `YoutubeVideoSearchTool` - Video content

**Financial Data**:

- `YahooFinanceNewsTool` - Latest financial news
- `YahooFinanceTickerInfoTool` - Ticker information
- `AlphaVantageNewsSentimentTool` - News sentiment

**Specialized**:

- `EnhancedSECAnalysisTool` - SEC filings
- `CoinMarketCapTool` - Crypto data
- `PerplexitySearchTool` - Enhanced research (optional)

## Intelligent Caching System

The FinWiz caching system provides intelligent caching capabilities to improve performance, reduce API costs, and enhance system responsiveness. It supports multiple backends, configurable strategies, and comprehensive performance monitoring.

### Architecture Overview

The caching system consists of:

1. **CacheManager**: Central orchestrator for all caching operations
2. **Multiple Backends**: Memory, file, and hybrid storage options
3. **Eviction Strategies**: TTL, LRU, LFU, and adaptive algorithms
4. **Performance Monitoring**: Comprehensive statistics and hit rate tracking
5. **Cache Warming**: Pre-loading of frequently accessed data

### Core Components

#### CacheManager

The `CacheManager` class provides the main interface for caching operations:

```python
from finwiz.utils.cache_manager import get_cache_manager, CacheConfig

# Get the global cache manager instance
cache = get_cache_manager()

# Basic operations
await cache.set("key", {"data": "value"}, ttl=3600)
result = await cache.get("key")
await cache.delete("key")

# Bulk operations
await cache.clear()  # Clear all entries
await cache.cleanup_expired()  # Remove expired entries
```

#### Cache Configuration

Configure caching behavior through `CacheConfig`:

```python
from finwiz.utils.cache_manager import CacheConfig, CacheBackend, CacheStrategy

config = CacheConfig(
    backend=CacheBackend.HYBRID,        # memory, file, or hybrid
    default_ttl=2700,                   # 45 minutes default TTL
    max_memory_items=1000,              # Memory cache size limit
    max_file_size_mb=100,               # File cache size limit
    cache_directory="cache",            # Cache file directory
    strategy=CacheStrategy.TTL,         # Eviction strategy
    enable_compression=True,            # Compress cached data
    auto_cleanup=True,                  # Automatic cleanup
    cleanup_interval=3600,              # Cleanup every hour
    hit_rate_threshold=0.7              # Minimum effective hit rate
)

cache = CacheManager(config)
```

### Cache Backends

#### Memory Backend (`CacheBackend.MEMORY`)

- **Pros**: Fastest access, no disk I/O
- **Cons**: Limited by available RAM, data lost on restart
- **Use Case**: Temporary data, high-frequency access patterns

#### File Backend (`CacheBackend.FILE`)

- **Pros**: Persistent across restarts, larger capacity
- **Cons**: Slower than memory, disk I/O overhead
- **Use Case**: Long-term caching, large datasets

#### Hybrid Backend (`CacheBackend.HYBRID`) - Recommended

- **Pros**: Combines speed of memory with persistence of files
- **Cons**: Slightly more complex management
- **Use Case**: Production environments, balanced performance

### Eviction Strategies

#### TTL (Time-To-Live) - Default

- Removes entries when they exceed their TTL
- Simple and predictable behavior
- Good for time-sensitive data

#### LRU (Least Recently Used)

- Removes least recently accessed entries
- Good for access pattern-based caching
- Maintains frequently used data

#### LFU (Least Frequently Used)

- Removes least frequently accessed entries
- Good for popularity-based caching
- Keeps most popular data in cache

#### Adaptive

- Dynamically adjusts strategy based on access patterns
- Combines multiple strategies for optimal performance
- Best for varied workloads

### Environment Configuration

Configure caching through environment variables:

```bash
# Cache backend configuration
CACHE_BACKEND=hybrid                    # memory, file, hybrid
CACHE_TTL=2700                         # Default TTL in seconds
CACHE_MAX_MEMORY_ITEMS=1000            # Memory cache size limit
CACHE_MAX_FILE_SIZE_MB=100             # File cache size limit
CACHE_DIRECTORY=cache                  # Cache directory path
CACHE_STRATEGY=ttl                     # ttl, lru, lfu, adaptive
CACHE_AUTO_CLEANUP=true                # Enable auto cleanup
CACHE_CLEANUP_INTERVAL=3600            # Cleanup interval in seconds
CACHE_ENABLE_COMPRESSION=true          # Enable data compression
CACHE_HIT_RATE_THRESHOLD=0.7           # Minimum effective hit rate
```

## Feature Flags & Configuration

This guide explains how to use the feature flag system and configuration manager in FinWiz for gradual rollouts, graceful degradation, and environment management.

### Overview

The FinWiz feature flag system provides:

- **Environment-based configuration** for gradual rollouts
- **Circuit breaker patterns** for service reliability
- **Graceful degradation** when services fail
- **Centralized API key management** with validation
- **Multiple evaluation strategies** (boolean, percentage, user lists, time windows)

### Quick Start

#### Basic Feature Flag Usage

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

#### Configuration Management

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

### Environment Variables

#### Feature Flag Configuration

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

#### API Key Configuration

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
```

### Circuit Breaker Pattern

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
```

## Integration Configuration

### Overview

Centralized data management and coordination between analysis crews with validation, freshness checking, and error handling.

### Configuration File

**Location**: `config/integration.yaml`

```yaml
integration:
  output_dir: "output"
  
  freshness:
    default_max_age_hours: 24
    crew_thresholds:
      stock: 24      # Stock analysis valid for 24 hours
      etf: 48        # ETF analysis valid for 48 hours
      crypto: 12     # Crypto analysis valid for 12 hours
      discovery: 72  # Discovery valid for 72 hours
      portfolio: 168 # Portfolio review valid for 1 week
  
  validation:
    strict_validation: true
    timeout_seconds: 30
    continue_on_warnings: true
  
  error_handling:
    max_retries: 3
    retry_delay: 2
    graceful_degradation: true
  
  logging:
    level: "INFO"
    structured: true
    log_lineage: true
    log_performance: false
```

### Environment Variables

**Location**: `.env`

```bash
# Core Settings
FINWIZ_INTEGRATION_OUTPUT_DIR=output
FINWIZ_INTEGRATION_DEFAULT_MAX_AGE_HOURS=24
FINWIZ_INTEGRATION_STRICT_VALIDATION=true
FINWIZ_INTEGRATION_LOG_LEVEL=INFO

# Data Freshness Thresholds
FINWIZ_STOCK_MAX_AGE_HOURS=24
FINWIZ_ETF_MAX_AGE_HOURS=48
FINWIZ_CRYPTO_MAX_AGE_HOURS=12
FINWIZ_DISCOVERY_MAX_AGE_HOURS=72
FINWIZ_PORTFOLIO_MAX_AGE_HOURS=168

# Validation Settings
FINWIZ_STRICT_VALIDATION=true
FINWIZ_VALIDATION_TIMEOUT=30
FINWIZ_CONTINUE_ON_WARNINGS=true

# Error Handling
FINWIZ_MAX_RETRIES=3
FINWIZ_RETRY_DELAY=2
FINWIZ_GRACEFUL_DEGRADATION=true
```

### Data Freshness

**Freshness Thresholds**:

- **Stock**: 24 hours (daily updates sufficient)
- **ETF**: 48 hours (less volatile)
- **Crypto**: 12 hours (high volatility)
- **Discovery**: 72 hours (weekly discovery runs)
- **Portfolio**: 168 hours (weekly reviews)

### Validation

**Validation Modes**:

- `strict_validation=true`: Fail on validation errors
- `strict_validation=false`: Warn on validation errors
- `continue_on_warnings=true`: Continue despite warnings

### Error Handling

**Retry Strategy**:

- Automatic retry with exponential backoff (max_retries: 3, retry_delay: 2s)

**Graceful Degradation**:

- Use cached data if available
- Fall back to baseline analysis
- Continue with partial data

## Best Practices

### Feedback Learning

1. **Collect Regularly**: Prompt users for feedback after recommendations
2. **Track Performance**: Monitor all A+ investments for at least 1 year
3. **Review Insights**: Monthly review of learning insights

### Portfolio Monitoring

1. **Set Appropriate Thresholds**: Balance sensitivity vs noise
2. **Configure Quiet Hours**: Respect user preferences
3. **Test Notifications**: Verify email/SMS delivery

### Knowledge Base & Caching

1. **Enable Caching**: Use hybrid caching for performance
2. **Monitor Costs**: Track API usage and costs
3. **Validate Freshness**: Check data timestamps

### Integration

1. **Configure Freshness**: Set appropriate thresholds per crew
2. **Enable Validation**: Use strict validation in production
3. **Monitor Metrics**: Track cache hit rate and latency

---

**Version**: 2.0  
**Last Updated**: 2025-03-10
