# System Operations Guide

Complete guide for FinWiz system operations including feedback learning, portfolio monitoring, knowledge base, and integration configuration.

## Table of Contents

1. [Feedback Learning System](#feedback-learning-system)
2. [Portfolio Monitoring](#portfolio-monitoring)
3. [Knowledge Base Strategy](#knowledge-base-strategy)
4. [Integration Configuration](#integration-configuration)

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

### Caching Strategy

To optimize performance, FinWiz implements intelligent caching:

```python
# Cache configuration
CACHE_BACKEND=hybrid        # Memory + file
CACHE_TTL=2700             # 45 minutes
CACHE_STRATEGY=ttl         # Time-based eviction
```

**Cache TTL by Data Type**:

- Price data: 1 hour
- News articles: 6 hours
- SEC filings: 24 hours
- Company fundamentals: 24 hours
- Technical indicators: 1 hour

### Best Practices

1. **Use Caching**: Enable hybrid caching for best performance
2. **Respect Rate Limits**: Configure max_rpm appropriately
3. **Fallback Strategy**: Implement graceful degradation
4. **Monitor Costs**: Track API usage and costs
5. **Data Freshness**: Validate data timestamps

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

**Freshness Checking**:

```python
from finwiz.integration.data_accessor import DataAccessor

accessor = DataAccessor()

# Check if data is fresh
is_fresh = accessor.is_data_fresh(
    crew_type="stock",
    ticker="AAPL",
    max_age_hours=24
)

if not is_fresh:
    # Trigger new analysis
    await accessor.trigger_crew_analysis("stock", "AAPL")
```

### Validation

**Validation Modes**:

- `strict_validation=true`: Fail on validation errors
- `strict_validation=false`: Warn on validation errors
- `continue_on_warnings=true`: Continue despite warnings

**Validation Process**:

1. Schema validation (Pydantic)
2. Data freshness check
3. Required field validation
4. Data type validation
5. Business rule validation

### Error Handling

**Retry Strategy**:

```python
# Automatic retry with exponential backoff
max_retries: 3
retry_delay: 2  # seconds (doubles each retry)

# Retry sequence: 2s, 4s, 8s
```

**Graceful Degradation**:

- Use cached data if available
- Fall back to baseline analysis
- Continue with partial data
- Log warnings for manual review

### Monitoring

**Integration Metrics**:

```python
from finwiz.integration.data_accessor import DataAccessor

accessor = DataAccessor()
metrics = accessor.get_integration_metrics()

print(f"Total requests: {metrics['total_requests']}")
print(f"Cache hit rate: {metrics['cache_hit_rate']:.2%}")
print(f"Average latency: {metrics['avg_latency_ms']}ms")
print(f"Error rate: {metrics['error_rate']:.2%}")
```

**Health Check**:

```bash
# Check integration system health
uv run python -c "from finwiz.integration.data_accessor import DataAccessor; print(DataAccessor().health_check())"
```

## Best Practices

### Feedback Learning

1. **Collect Regularly**: Prompt users for feedback after recommendations
2. **Track Performance**: Monitor all A+ investments for at least 1 year
3. **Review Insights**: Monthly review of learning insights
4. **Validate Changes**: Backtest all criteria adjustments
5. **Document Decisions**: Keep audit trail of criteria changes

### Portfolio Monitoring

1. **Set Appropriate Thresholds**: Balance sensitivity vs noise
2. **Configure Quiet Hours**: Respect user preferences
3. **Test Notifications**: Verify email/SMS delivery
4. **Review Alerts**: Weekly review of alert patterns
5. **Adjust Rules**: Refine monitoring rules based on experience

### Knowledge Base

1. **Enable Caching**: Use hybrid caching for performance
2. **Monitor Costs**: Track API usage and costs
3. **Validate Freshness**: Check data timestamps
4. **Implement Fallbacks**: Graceful degradation on API failures
5. **Rate Limit**: Respect API rate limits

### Integration

1. **Configure Freshness**: Set appropriate thresholds per crew
2. **Enable Validation**: Use strict validation in production
3. **Monitor Metrics**: Track cache hit rate and latency
4. **Handle Errors**: Implement retry and fallback strategies
5. **Log Everything**: Enable structured logging for debugging

---

**Version**: 2.0  
**Last Updated**: 2025-03-10
