# Portfolio Holdings Analysis - Performance Optimizations

Comprehensive guide to the performance optimizations implemented for portfolio holdings analysis.

## Overview

The portfolio holdings analysis system includes several performance optimizations to handle portfolios of varying sizes efficiently:

- **Intelligent Caching**: Multi-tier caching with TTL support
- **Rate Limiting**: Prevents API rate limit violations
- **Parallel Processing**: Batch processing with asyncio
- **Connection Pooling**: Efficient HTTP connection management

## Performance Targets

| Portfolio Size | Target Time | Status |
|---------------|-------------|--------|
| Small (< 20 holdings) | < 5 minutes | ✅ Achieved |
| Medium (20-50 holdings) | < 15 minutes | ✅ Achieved |
| Large (50-100 holdings) | < 30 minutes | ✅ Achieved |

## Caching Strategy

### Cache Layers

1. **Memory Cache** (L1)
   - Fastest access
   - Limited capacity (500 items default)
   - LRU eviction strategy

2. **File Cache** (L2)
   - Persistent across sessions
   - Larger capacity
   - Automatic cleanup

3. **Hybrid Mode** (Default)
   - Combines both layers
   - Best performance

### Cache TTL Configuration

```python
from finwiz.tools.holding_analyzer_orchestrator import HoldingAnalyzerOrchestrator

orchestrator = HoldingAnalyzerOrchestrator(
    enable_caching=True,
    enable_rate_limiting=True,
    parallel_batch_size=10,
)
```

**Default TTL Values:**

- Crew analysis: 7 days (604,800 seconds)
- Price data: 1 hour (3,600 seconds)
- Baseline analysis: 1 hour (3,600 seconds)

### Cache Key Generation

Cache keys are generated deterministically from:

- Ticker symbol
- Asset class (stock/etf/crypto)
- Analysis type

Example:

```python
cache_key = cache_key("holding_analysis", "AAPL", "stock")
# Result: "holding_analysis:AAPL:stock"
```

### Cache Invalidation

Automatic invalidation occurs when:

- TTL expires
- Manual cache clear requested
- Cache capacity exceeded (LRU eviction)

Manual cache clearing:

```python
# Clear all cache
await orchestrator.cache_manager.clear()

# Clear by tags
await orchestrator.cache_manager.clear(tags={"holding_analysis", "stock"})
```

## Rate Limiting

### API Provider Limits

| Provider | Requests/Min | Requests/Hour | Cooldown |
|----------|--------------|---------------|----------|
| Alpha Vantage | 5 | 500 | 12s |
| Yahoo Finance | 60 | 2000 | 1s |
| Twelve Data | 8 | 800 | 7.5s |
| SEC EDGAR | 10 | 600 | 6s |
| Perplexity | 30 | 1200 | 2s |

### Rate Limiting Features

1. **Sliding Window**: Tracks requests over time windows
2. **Exponential Backoff**: Automatic retry with increasing delays
3. **Burst Protection**: Limits rapid successive requests
4. **Jitter**: Adds randomness to prevent thundering herd

### Configuration

```python
from finwiz.utils.rate_limiter import RateLimitConfig, APIProvider

custom_config = {
    APIProvider.YAHOO_FINANCE: RateLimitConfig(
        requests_per_minute=60,
        requests_per_hour=2000,
        burst_limit=10,
        cooldown_seconds=1.0,
        max_retries=3,
        base_backoff=1.0,
        max_backoff=30.0,
        jitter=True,
    )
}
```

### Retry Strategy

Automatic retries occur for:

- Rate limit errors (429)
- Temporary server errors (502, 503, 504)
- Timeout errors
- Connection errors

Retry delays use exponential backoff:

```
Attempt 1: 1s
Attempt 2: 2s
Attempt 3: 4s
Max: 60s (configurable)
```

## Parallel Processing

### Batch Processing

Holdings are processed in configurable batches:

```python
orchestrator = HoldingAnalyzerOrchestrator(
    parallel_batch_size=10,  # Process 10 holdings at a time
)
```

**Benefits:**

- Prevents overwhelming the system
- Respects rate limits
- Allows progress monitoring
- Handles failures gracefully

### Async Implementation

Uses Python's `asyncio` for concurrent execution:

```python
async def analyze_holdings_parallel(holdings: list[dict]) -> list[HoldingAnalysis]:
    """Analyze multiple holdings in parallel."""
    results = []
    
    # Process in batches
    for batch in chunks(holdings, batch_size=10):
        # Create async tasks
        tasks = [analyze_holding_async(h) for h in batch]
        
        # Execute in parallel
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        results.extend(batch_results)
    
    return results
```

### Error Handling

Parallel processing includes robust error handling:

1. **Exception Isolation**: One failure doesn't stop others
2. **Baseline Fallback**: Failed analyses get baseline data
3. **Logging**: All errors logged with context
4. **Retry Logic**: Automatic retries for transient errors

## Connection Pooling

### HTTP Connection Management

The orchestrator manages HTTP connections efficiently:

```python
# Connection pool configuration
self._connection_pool_size = 10
self._active_connections = 0
```

**Benefits:**

- Reuses TCP connections
- Reduces connection overhead
- Improves throughput
- Lowers latency

### Best Practices

1. **Reuse Connections**: Keep connections alive between requests
2. **Limit Pool Size**: Prevent resource exhaustion
3. **Timeout Configuration**: Set appropriate timeouts
4. **Graceful Shutdown**: Close connections properly

## Performance Monitoring

### Cache Statistics

Monitor cache effectiveness:

```python
stats = orchestrator.cache_manager.get_stats()

print(f"Hit rate: {stats['hit_rate']:.1%}")
print(f"Hits: {stats['hits']}")
print(f"Misses: {stats['misses']}")
print(f"Memory usage: {stats['total_size_mb']:.2f} MB")
```

### Rate Limiter Statistics

Monitor API usage:

```python
from finwiz.utils.rate_limiter import APIProvider

stats = orchestrator.rate_limiter.get_stats(APIProvider.YAHOO_FINANCE)

print(f"Requests last minute: {stats['requests_last_minute']}")
print(f"Requests last hour: {stats['requests_last_hour']}")
print(f"Total requests: {stats['total_requests']}")
```

### Performance Metrics

Key metrics to monitor:

- **Analysis Time**: Total time to analyze portfolio
- **Average Per Holding**: Time per holding analysis
- **Cache Hit Rate**: Percentage of cache hits
- **API Request Count**: Number of external API calls
- **Error Rate**: Percentage of failed analyses

## Benchmarking

Run the performance benchmark:

```bash
uv run python examples/portfolio_performance_benchmark.py
```

Expected output:

```
📊 Testing with 25 holdings...
✅ Optimized (caching + parallel): 12.34s
   - Holdings analyzed: 25
   - Average per holding: 0.494s
   - Batch size: 10

⚠️  Basic (no cache, sequential): 45.67s
   - Holdings analyzed: 25
   - Average per holding: 1.827s

💡 Performance improvement: 73.0%
   - Time saved: 33.33s
```

## Optimization Tips

### For Small Portfolios (< 20 holdings)

- Use default settings
- Enable caching for repeated analyses
- Batch size: 10

### For Medium Portfolios (20-50 holdings)

- Increase batch size to 15
- Enable aggressive caching
- Monitor rate limits

```python
orchestrator = HoldingAnalyzerOrchestrator(
    enable_caching=True,
    enable_rate_limiting=True,
    parallel_batch_size=15,
)
```

### For Large Portfolios (50-100 holdings)

- Increase batch size to 20
- Use hybrid cache backend
- Implement cache warming
- Monitor memory usage

```python
from finwiz.utils.cache_manager import CacheConfig, CacheBackend

orchestrator = HoldingAnalyzerOrchestrator(
    enable_caching=True,
    enable_rate_limiting=True,
    parallel_batch_size=20,
)

# Configure cache
orchestrator.cache_manager.config = CacheConfig(
    backend=CacheBackend.HYBRID,
    default_ttl=604800,  # 7 days
    max_memory_items=1000,
    auto_cleanup=True,
)
```

## Troubleshooting

### Slow Performance

**Symptoms**: Analysis takes longer than expected

**Solutions**:

1. Check cache hit rate (should be > 70%)
2. Verify rate limiting isn't too aggressive
3. Increase parallel batch size
4. Check network connectivity

### High Memory Usage

**Symptoms**: Memory consumption increases over time

**Solutions**:

1. Enable auto cleanup
2. Reduce max_memory_items
3. Use file-based caching
4. Clear cache periodically

### Rate Limit Errors

**Symptoms**: 429 errors or API rejections

**Solutions**:

1. Reduce parallel batch size
2. Increase cooldown periods
3. Enable rate limiting
4. Use caching to reduce API calls

## Future Enhancements

Planned optimizations:

1. **Distributed Caching**: Redis/Memcached support
2. **Predictive Caching**: Pre-load likely needed data
3. **Adaptive Batching**: Dynamic batch size based on load
4. **Circuit Breaker**: Automatic failover for degraded APIs
5. **Compression**: Reduce cache storage size

## References

- [Cache Manager Implementation](../src/finwiz/utils/cache_manager.py)
- [Rate Limiter Implementation](../src/finwiz/utils/rate_limiter.py)
- [Holding Analyzer Orchestrator](../src/finwiz/tools/holding_analyzer_orchestrator.py)
- [Performance Tests](../tests/unit/tools/test_holding_analyzer_orchestrator_performance.py)

---

**Last Updated**: 2025-04-10  
**Version**: 1.0
