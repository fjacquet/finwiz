# FinWiz Caching System

The FinWiz caching system provides intelligent caching capabilities to improve performance, reduce API costs, and enhance system responsiveness. It supports multiple backends, configurable strategies, and comprehensive performance monitoring.

## Architecture Overview

The caching system consists of:

1. **CacheManager**: Central orchestrator for all caching operations
2. **Multiple Backends**: Memory, file, and hybrid storage options
3. **Eviction Strategies**: TTL, LRU, LFU, and adaptive algorithms
4. **Performance Monitoring**: Comprehensive statistics and hit rate tracking
5. **Cache Warming**: Pre-loading of frequently accessed data

## Core Components

### CacheManager

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

### Cache Configuration

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

## Cache Backends

### Memory Backend (`CacheBackend.MEMORY`)

- **Pros**: Fastest access, no disk I/O
- **Cons**: Limited by available RAM, data lost on restart
- **Use Case**: Temporary data, high-frequency access patterns

### File Backend (`CacheBackend.FILE`)

- **Pros**: Persistent across restarts, larger capacity
- **Cons**: Slower than memory, disk I/O overhead
- **Use Case**: Long-term caching, large datasets

### Hybrid Backend (`CacheBackend.HYBRID`) - Recommended

- **Pros**: Combines speed of memory with persistence of files
- **Cons**: Slightly more complex management
- **Use Case**: Production environments, balanced performance

## Eviction Strategies

### TTL (Time-To-Live) - Default

```python
config.strategy = CacheStrategy.TTL
```

- Removes entries when they exceed their TTL
- Simple and predictable behavior
- Good for time-sensitive data

### LRU (Least Recently Used)

```python
config.strategy = CacheStrategy.LRU
```

- Removes least recently accessed entries
- Good for access pattern-based caching
- Maintains frequently used data

### LFU (Least Frequently Used)

```python
config.strategy = CacheStrategy.LFU
```

- Removes least frequently accessed entries
- Good for popularity-based caching
- Keeps most popular data in cache

### Adaptive

```python
config.strategy = CacheStrategy.ADAPTIVE
```

- Dynamically adjusts strategy based on access patterns
- Combines multiple strategies for optimal performance
- Best for varied workloads

## Environment Configuration

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

## Usage Patterns

### Function Caching Decorator

```python
from finwiz.utils.cache_manager import cached

@cached(key="stock_data", ttl=1800)
async def get_stock_data(ticker: str):
    """Fetch stock data with automatic caching."""
    # Expensive API call
    return await api_client.get_stock_info(ticker)

# Usage
data = await get_stock_data("AAPL")  # Fetches from API
data = await get_stock_data("AAPL")  # Returns from cache
```

### Manual Caching

```python
from finwiz.utils.cache_manager import get_cache_manager, cache_key

cache = get_cache_manager()

# Generate consistent cache keys
key = cache_key("stock", ticker, "daily", date.today())

# Check cache first
result = await cache.get(key)
if result is None:
    # Fetch from API
    result = await expensive_api_call(ticker)
    # Cache the result
    await cache.set(key, result, ttl=3600)

return result
```

### Tagged Caching

```python
# Cache with tags for selective invalidation
await cache.set(
    key="stock_AAPL_daily",
    value=stock_data,
    ttl=3600,
    tags={"stock", "AAPL", "daily"}
)

# Clear all stock-related cache entries
await cache.clear(tags={"stock"})
```

## Performance Monitoring

### Cache Statistics

```python
# Get comprehensive statistics
stats = cache.get_stats()

print(f"Cache Performance:")
print(f"  Hit Rate: {stats['hit_rate']:.2%}")
print(f"  Total Hits: {stats['hits']}")
print(f"  Total Misses: {stats['misses']}")
print(f"  Entry Count: {stats['entry_count']}")
print(f"  Memory Usage: {stats['total_size_mb']:.1f} MB")
print(f"  Average Age: {stats['average_age_seconds']:.1f} seconds")
```

### Performance Optimization

```python
# Monitor cache effectiveness
stats = cache.get_stats()
if stats['hit_rate'] < 0.5:
    # Low hit rate - consider adjusting TTL or strategy
    logger.warning(f"Low cache hit rate: {stats['hit_rate']:.2%}")

# Cache warming for frequently accessed data
async def warm_cache():
    """Pre-load frequently accessed data."""
    popular_tickers = ["AAPL", "GOOGL", "MSFT", "TSLA"]
    
    for ticker in popular_tickers:
        try:
            data = await get_stock_data(ticker)
            await cache.set(f"stock_{ticker}", data, ttl=7200)
        except Exception as e:
            logger.warning(f"Cache warming failed for {ticker}: {e}")

# Start cache warming
await cache.warm_cache([warm_cache])
```

## Integration with FinWiz Components

### API Tool Integration

```python
class EnhancedYahooFinanceTool:
    def __init__(self):
        self.cache = get_cache_manager()
    
    async def get_ticker_info(self, ticker: str):
        """Get ticker info with caching."""
        cache_key = cache_key("yahoo_ticker", ticker)
        
        # Try cache first
        result = await self.cache.get(cache_key)
        if result is not None:
            return result
        
        # Fetch from API
        result = await self._fetch_ticker_info(ticker)
        
        # Cache for 30 minutes
        await self.cache.set(cache_key, result, ttl=1800)
        
        return result
```

### Crew Integration

```python
class StockCrew:
    def __init__(self):
        self.cache = get_cache_manager()
    
    async def analyze_stock(self, ticker: str):
        """Analyze stock with caching support."""
        analysis_key = cache_key("stock_analysis", ticker, date.today())
        
        # Check for cached analysis
        cached_analysis = await self.cache.get(analysis_key)
        if cached_analysis is not None:
            logger.info(f"Using cached analysis for {ticker}")
            return cached_analysis
        
        # Perform fresh analysis
        analysis = await self._perform_analysis(ticker)
        
        # Cache analysis for 4 hours
        await self.cache.set(analysis_key, analysis, ttl=14400)
        
        return analysis
```

## Best Practices

### 1. Cache Key Design

```python
# Good: Hierarchical, descriptive keys
key = cache_key("crew", "stock", "analysis", ticker, date.today())

# Bad: Flat, ambiguous keys
key = f"{ticker}_data"
```

### 2. TTL Selection

```python
# Real-time data: Short TTL
await cache.set("market_price", price, ttl=60)  # 1 minute

# Daily data: Medium TTL
await cache.set("daily_analysis", analysis, ttl=3600)  # 1 hour

# Static data: Long TTL
await cache.set("company_info", info, ttl=86400)  # 24 hours
```

### 3. Error Handling

```python
async def cached_api_call(key: str, api_func: Callable):
    """Robust cached API call with error handling."""
    try:
        # Try cache first
        result = await cache.get(key)
        if result is not None:
            return result
    except Exception as e:
        logger.warning(f"Cache get failed: {e}")
    
    # Fetch from API
    try:
        result = await api_func()
        
        # Try to cache result
        try:
            await cache.set(key, result, ttl=1800)
        except Exception as e:
            logger.warning(f"Cache set failed: {e}")
        
        return result
    except Exception as e:
        logger.error(f"API call failed: {e}")
        raise
```

### 4. Memory Management

```python
# Monitor memory usage
stats = cache.get_stats()
if stats['memory_usage_mb'] > 500:  # 500 MB threshold
    # Force cleanup
    await cache.cleanup_expired()
    
    # Consider reducing cache size
    cache.config.max_memory_items = 500
```

## Testing Cache Behavior

### Unit Testing

```python
import pytest
from finwiz.utils.cache_manager import CacheManager, CacheConfig

@pytest.mark.asyncio
async def test_cache_basic_operations():
    """Test basic cache operations."""
    cache = CacheManager()
    
    # Test set/get
    await cache.set("test_key", "test_value", ttl=60)
    result = await cache.get("test_key")
    assert result == "test_value"
    
    # Test expiration
    await cache.set("expire_key", "value", ttl=0)
    await asyncio.sleep(0.1)
    result = await cache.get("expire_key")
    assert result is None

@pytest.mark.asyncio
async def test_cache_statistics():
    """Test cache statistics tracking."""
    cache = CacheManager()
    
    # Generate some cache activity
    await cache.set("key1", "value1")
    await cache.get("key1")  # Hit
    await cache.get("key2")  # Miss
    
    stats = cache.get_stats()
    assert stats['hits'] == 1
    assert stats['misses'] == 1
    assert stats['hit_rate'] == 0.5
```

### Integration Testing

```python
@pytest.mark.asyncio
async def test_crew_caching_integration():
    """Test caching integration with crew operations."""
    crew = StockCrew()
    
    # First analysis should hit API
    analysis1 = await crew.analyze_stock("AAPL")
    
    # Second analysis should use cache
    analysis2 = await crew.analyze_stock("AAPL")
    
    # Results should be identical
    assert analysis1 == analysis2
    
    # Verify cache was used
    stats = crew.cache.get_stats()
    assert stats['hits'] >= 1
```

## Troubleshooting

### Common Issues

1. **Low Hit Rate**

   ```python
   # Check TTL settings
   stats = cache.get_stats()
   if stats['hit_rate'] < 0.3:
       # Increase TTL or check key consistency
       logger.warning("Consider increasing cache TTL")
   ```

2. **Memory Usage**

   ```python
   # Monitor memory consumption
   if stats['memory_usage_mb'] > 1000:  # 1GB threshold
       await cache.cleanup_expired()
       # Consider file or hybrid backend
   ```

3. **Cache Misses**

   ```python
   # Debug cache key generation
   key = cache_key("debug", ticker, date.today())
   logger.debug(f"Generated cache key: {key}")
   
   # Check if key exists
   exists = await cache.get(key) is not None
   logger.debug(f"Key exists in cache: {exists}")
   ```

### Performance Tuning

1. **Backend Selection**
   - Use `memory` for small, frequently accessed data
   - Use `file` for large, persistent data
   - Use `hybrid` for balanced performance (recommended)

2. **Strategy Optimization**
   - Use `TTL` for time-sensitive data
   - Use `LRU` for access pattern-based caching
   - Use `adaptive` for mixed workloads

3. **TTL Tuning**
   - Monitor data freshness requirements
   - Balance between performance and accuracy
   - Use shorter TTLs for volatile data

The caching system is designed to be transparent and non-intrusive, providing significant performance improvements while maintaining data accuracy and system reliability.
