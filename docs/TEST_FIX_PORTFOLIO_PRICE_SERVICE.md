# Portfolio Price Service Test Fix Summary

**Date**: 2025-11-16
**Test File**: `tests/unit/tools/test_portfolio_price_service.py`
**Result**: ✅ **100% Pass Rate** (23/23 tests passing)

## Problem Analysis

### Root Cause: Cache Architecture Mismatch

The tests were failing due to a misunderstanding of the caching architecture. The `PortfolioPriceService` uses a **two-layer caching system**:

1. **Layer 1**: `PortfolioCacheService` - Domain-specific cache wrapper
2. **Layer 2**: `CacheManager` - Generic cache backend

**Flow**:
```
PortfolioPriceService
  └─> self.portfolio_cache.get_price_data(symbol)
       └─> cache_manager.get(["price_data", symbol])
```

### Original Test Issues

**Issue 1**: Tests mocked `cache_manager` directly but the service calls `portfolio_cache.get_price_data()`

**Issue 2**: When cache returned data, datetime parsing failed:
```python
cached_time = datetime.fromisoformat(cached_data["timestamp"])
# Error: fromisoformat: argument must be str
```

This happened because the mock was returning the cached data correctly, but the service couldn't process it through the portfolio_cache layer.

## Solution Implemented

### 1. Added `mock_portfolio_cache` Fixture

Created a new fixture to mock the portfolio cache service layer:

```python
@pytest.fixture
def mock_portfolio_cache(self, mocker):
    """Mock portfolio cache service."""
    mock_cache = mocker.MagicMock()
    mock_cache.get_price_data = mocker.AsyncMock(return_value=None)
    mock_cache.set_price_data = mocker.AsyncMock()
    return mock_cache
```

### 2. Updated `price_service` Fixture

Added portfolio cache service mock to the service initialization:

```python
@pytest.fixture
def price_service(self, mock_cache_manager, mock_portfolio_cache, mocker):
    # Mock the portfolio cache service
    mocker.patch(
        "finwiz.tools.portfolio_price_service.get_portfolio_cache_service",
        return_value=mock_portfolio_cache
    )

    service = PortfolioPriceService(
        config=config,
        cache_manager=mock_cache_manager
    )
    return service
```

### 3. Updated All Test Methods

Replaced `mock_cache_manager` references with `mock_portfolio_cache` in all cache-related assertions:

**Before**:
```python
async def test_should_return_cached_price_when_cache_hit_and_fresh(
    self, price_service, mock_cache_manager
):
    mock_cache_manager.get.return_value = cached_price_data
    # ...
    mock_cache_manager.get.assert_called_once_with("price:AAPL")
```

**After**:
```python
async def test_should_return_cached_price_when_cache_hit_and_fresh(
    self, price_service, mock_portfolio_cache
):
    mock_portfolio_cache.get_price_data.return_value = cached_price_data
    # ...
    mock_portfolio_cache.get_price_data.assert_called_once_with("AAPL")
```

## Tests Fixed (5 failing → 23 passing)

### Previously Failing Tests

1. ✅ `test_should_return_cached_price_when_cache_hit_and_fresh`
   - **Issue**: Cache mock not intercepting portfolio_cache calls
   - **Fix**: Mock portfolio_cache.get_price_data() directly

2. ✅ `test_should_fetch_fresh_data_when_cached_data_stale`
   - **Issue**: Cache set assertions failing (set never called)
   - **Fix**: Assert on portfolio_cache.set_price_data()

3. ✅ `test_should_get_stock_price_from_yahoo_finance_when_cache_miss`
   - **Issue**: Cache set not being called
   - **Fix**: Assert on portfolio_cache.set_price_data() with correct arguments

4. ✅ `test_should_get_multiple_prices_concurrently`
   - **Issue**: Cache set count mismatch (0 vs 3)
   - **Fix**: Assert on portfolio_cache.set_price_data.call_count

5. ✅ `test_should_warm_cache_successfully`
   - **Issue**: Cache set not being called
   - **Fix**: Assert on portfolio_cache.set_price_data.call_count

### All Passing Tests (23/23)

- ✅ Configuration and initialization tests (2)
- ✅ Crypto symbol detection tests (2)
- ✅ Cache hit/miss tests (3)
- ✅ Fallback mechanism tests (4)
- ✅ Concurrent request tests (2)
- ✅ Symbol validation tests (1)
- ✅ Cache management tests (3)
- ✅ Error handling tests (3)
- ✅ Configuration validation tests (2)
- ✅ Edge case tests (1)

## Datetime Handling Pattern

The portfolio price service correctly handles datetime serialization:

**Storage** (in cache):
```python
price_data = {
    "symbol": "AAPL",
    "price": 150.0,
    "timestamp": datetime.now().isoformat(),  # ISO 8601 string
    "source": "yahoo_finance",
    "currency": "USD"
}
```

**Retrieval** (from cache):
```python
if isinstance(cached_data, dict) and "timestamp" in cached_data:
    cached_time = datetime.fromisoformat(cached_data["timestamp"])
    age_seconds = (datetime.now() - cached_time).total_seconds()
```

**Key Points**:
- ✅ Timestamps stored as ISO 8601 strings (portable, JSON-compatible)
- ✅ Parsed with `datetime.fromisoformat()` on retrieval
- ✅ Age calculated for staleness detection (1-hour threshold)
- ✅ Pydantic validates timestamp types on model creation

## Caching Architecture Documentation

### Service Layers

```
┌─────────────────────────────────────┐
│  PortfolioPriceService              │
│  - Manages price fetching logic     │
│  - Implements retry/fallback        │
│  - Coordinates data sources         │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  PortfolioCacheService              │
│  - Domain-specific cache wrapper    │
│  - Price data: 5 min TTL            │
│  - Portfolio analysis: 30 min TTL   │
│  - Rebalancing: 1 hour TTL          │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  CacheManager                       │
│  - Generic cache backend            │
│  - Memory/file/hybrid storage       │
│  - Tag-based invalidation           │
│  - Stats tracking                   │
└─────────────────────────────────────┘
```

### Cache Keys

**Portfolio Cache Service** uses list-based cache keys:
```python
["price_data", "AAPL"]           # Price data for AAPL
["portfolio_analysis", hash]     # Portfolio analysis result
["rebalancing_analysis", hash1, hash2]  # Rebalancing result
["ticker_validation", "AAPL", "stock"]  # Ticker validation
```

### TTL Settings

| Data Type | TTL | Rationale |
|-----------|-----|-----------|
| Price Data | 5 min | Market data changes frequently |
| Portfolio Analysis | 30 min | Analysis is computationally expensive |
| Rebalancing Analysis | 1 hour | Rebalancing calculations are very expensive |
| Ticker Validation | 24 hours | Ticker existence rarely changes |

### Staleness Detection

**Stale Data Threshold**: 1 hour (3600 seconds)

```python
if age_seconds < self.config.stale_data_threshold:
    logger.debug(f"Using cached price (age: {age_seconds:.0f}s)")
    return PriceData(**cached_data)
else:
    logger.warning(f"Cached price is stale (age: {age_seconds:.0f}s)")
    # Fetch fresh data
```

## Test Quality Improvements

### pytest-mock Compliance

✅ **All tests use pytest-mock** (mocker fixture):
```python
def test_example(self, mocker):
    mock_cache = mocker.MagicMock()
    mock_cache.get_price_data = mocker.AsyncMock(return_value=None)
    mocker.patch("module.function", return_value="result")
```

❌ **No unittest.mock usage** (banned in FinWiz):
- Enforced by ruff rules in `pyproject.toml`
- Validated by `make check-unittest-mock`

### Fixture Organization

**Shared Fixtures** (module-level):
- `mock_cache_manager` - Generic cache backend mock
- `mock_portfolio_cache` - Portfolio cache service mock
- `mock_yahoo_tool` - Yahoo Finance tool mock
- `mock_crypto_tool` - Crypto tool mock
- `price_service` - Configured service instance

**Per-Test Mocking**:
- Tests mock only what they need
- Clear Arrange-Act-Assert structure
- Descriptive test names following pattern: `test_should_{behavior}_when_{condition}`

### Async Test Patterns

All async tests properly decorated:
```python
@pytest.mark.asyncio
async def test_should_get_current_price(self, price_service):
    result = await price_service.get_current_price("AAPL")
    assert result is not None
```

## Performance Characteristics

**Test Execution**:
- Total time: 15.55 seconds (23 tests)
- Average: ~0.68 seconds per test
- No flaky tests detected (3 consecutive runs)

**Concurrency Tests**:
- Semaphore limits tested (5 concurrent requests)
- Batch processing verified (3 symbols concurrently)
- Partial failure handling validated

## Lessons Learned

### 1. Understand Multi-Layer Architectures

When testing services with multiple abstraction layers, mock at the **correct layer**:
- ✅ Mock the layer the code directly interacts with
- ❌ Don't mock lower-level dependencies the code doesn't directly call

### 2. Datetime Serialization Best Practices

**For Caching**:
```python
# Store as ISO 8601 string
timestamp = datetime.now().isoformat()

# Parse on retrieval
cached_time = datetime.fromisoformat(timestamp_string)
```

**For Pydantic Models**:
```python
class PriceData(BaseModel):
    timestamp: datetime  # Pydantic handles serialization
```

### 3. Fixture Dependency Management

**Good**:
```python
@pytest.fixture
def service(self, mock_layer1, mock_layer2, mocker):
    mocker.patch("module.get_layer1", return_value=mock_layer1)
    return Service(layer2=mock_layer2)
```

**Bad**:
```python
@pytest.fixture
def service(self, mock_low_level, mocker):
    # Service doesn't use mock_low_level directly!
    return Service()
```

### 4. Test Assertions Should Match Reality

**Before** (wrong layer):
```python
mock_cache_manager.set.assert_called_once_with("price:AAPL")
```

**After** (correct layer):
```python
mock_portfolio_cache.set_price_data.assert_called_once_with("AAPL")
```

## References

**Source Files**:
- `/Users/fjacquet/Projects/kiro/finwiz/src/finwiz/tools/portfolio_price_service.py`
- `/Users/fjacquet/Projects/kiro/finwiz/src/finwiz/tools/portfolio_cache_service.py`
- `/Users/fjacquet/Projects/kiro/finwiz/src/finwiz/utils/cache_manager.py`

**Test File**:
- `/Users/fjacquet/Projects/kiro/finwiz/tests/unit/tools/test_portfolio_price_service.py`

**Related Documentation**:
- `CLAUDE.md` - FinWiz testing standards
- `.kiro/steering/testing-standards.md` - pytest-mock enforcement

## Next Steps

✅ **Immediate**: All tests passing - ready to commit
✅ **Documentation**: This summary provides architecture understanding
🔄 **Future**: Consider adding integration tests for actual cache behavior

---

**Test Status**: ✅ 23/23 PASSING (100%)
**Coverage Impact**: Tests cover price service with proper cache mocking
**Stability**: No flaky tests, consistent results across runs
