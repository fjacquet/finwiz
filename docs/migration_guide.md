# FinWiz Migration Guide

This guide helps you migrate to the latest version of FinWiz with enhanced validation, caching, and testing capabilities.

## New Features Overview

### 1. Data Validation Infrastructure
- Centralized validation system with configurable strictness modes
- Schema registry for Pydantic model management
- Structured error handling with detailed context

### 2. Intelligent Caching System
- Multi-backend caching (memory/file/hybrid)
- Configurable TTL and eviction strategies
- Performance monitoring and cache warming

### 3. Dynamic Test Data Framework
- Faker-based test data generation
- Standardized pytest-mock integration
- APITestMocks for consistent external API mocking

## Environment Variables

Add these new environment variables to your `.env` file:

```bash
# Validation Configuration
VALIDATION_STRICTNESS=warn              # off, warn, error

# Caching Configuration
CACHE_BACKEND=hybrid                    # memory, file, hybrid
CACHE_TTL=2700                         # Default TTL in seconds
CACHE_MAX_MEMORY_ITEMS=1000            # Memory cache size limit
CACHE_MAX_FILE_SIZE_MB=100             # File cache size limit
CACHE_DIRECTORY=cache                  # Cache directory path
CACHE_STRATEGY=ttl                     # ttl, lru, lfu, adaptive
CACHE_AUTO_CLEANUP=true                # Enable auto cleanup
CACHE_CLEANUP_INTERVAL=3600            # Cleanup interval in seconds
```

## Code Migration

### 1. Validation Integration

#### Before (Optional)
```python
# Manual validation
try:
    validated_data = MySchema.model_validate(data)
except ValidationError as e:
    logger.error(f"Validation failed: {e}")
    raise
```

#### After (Recommended)
```python
from finwiz.validation import get_validation_manager

# Centralized validation with configurable strictness
manager = get_validation_manager()
result = manager.validate_crew_output(data, "stock", "analysis")

if result.is_valid:
    clean_data = result.sanitized_data
else:
    # Handle based on validation mode
    for error in result.errors:
        logger.error(f"Error at {error.field_path}: {error.message}")
```

### 2. Caching Integration

#### Before (Manual caching)
```python
# Manual cache management
cache_file = f"cache/{ticker}_data.json"
if os.path.exists(cache_file):
    with open(cache_file) as f:
        return json.load(f)

# Fetch and cache
data = await api_call(ticker)
with open(cache_file, 'w') as f:
    json.dump(data, f)
```

#### After (Intelligent caching)
```python
from finwiz.utils.cache_manager import get_cache_manager, cached

# Automatic caching with decorator
@cached(key="stock_data", ttl=1800)
async def get_stock_data(ticker: str):
    return await api_call(ticker)

# Or manual caching
cache = get_cache_manager()
result = await cache.get(f"stock_{ticker}")
if result is None:
    result = await api_call(ticker)
    await cache.set(f"stock_{ticker}", result, ttl=1800)
```

### 3. Test Data Migration

#### Before (Static test data)
```python
def test_stock_analysis():
    # Static test data
    ticker = "AAPL"
    expected_price = 150.0
    
    # Mock with static responses
    mock_api.return_value = {"symbol": "AAPL", "price": 150.0}
```

#### After (Dynamic test data)
```python
from tests.fixtures.api_test_mocks import APITestMocks
from faker import Faker

def test_stock_analysis(mocker):
    fake = Faker()
    
    # Dynamic test data
    ticker = fake.stock_ticker()
    expected_price = fake.stock_price()
    
    # Standardized mocking
    mocks = APITestMocks(mocker)
    mocks.setup_yahoo_finance_success(ticker=ticker, price=expected_price)
```

## Backward Compatibility

### Validation System
- **Default Mode**: WARN mode ensures existing workflows continue
- **Disable Option**: Set `VALIDATION_STRICTNESS=off` to disable validation
- **Gradual Adoption**: Add validation incrementally to existing crews

### Caching System
- **Optional**: Caching is completely optional and non-breaking
- **Transparent**: Existing code works without modification
- **Performance**: Automatic performance improvements when enabled

### Testing Framework
- **Existing Tests**: All existing tests continue to work
- **Gradual Migration**: Migrate tests to use Faker and APITestMocks incrementally
- **Mock Compatibility**: pytest-mock is backward compatible with unittest.mock

## Migration Steps

### Step 1: Update Environment Configuration
1. Add new environment variables to `.env`
2. Set `VALIDATION_STRICTNESS=warn` for gradual adoption
3. Configure caching based on your performance needs

### Step 2: Enable Validation (Optional)
1. Import validation manager in crew classes
2. Add validation calls at crew boundaries
3. Handle validation results based on your error handling strategy

### Step 3: Enable Caching (Optional)
1. Identify expensive operations (API calls, computations)
2. Add caching decorators or manual caching
3. Monitor cache performance and adjust TTL settings

### Step 4: Migrate Tests (Recommended)
1. Install Faker: Already included in dependencies
2. Replace static test data with Faker-generated data
3. Use APITestMocks for consistent external API mocking
4. Run tests to ensure compatibility

### Step 5: Monitor and Optimize
1. Monitor validation warnings and errors
2. Check cache hit rates and performance metrics
3. Adjust configuration based on usage patterns

## Troubleshooting

### Validation Issues
```python
# Debug validation problems
from finwiz.validation import get_validation_manager

manager = get_validation_manager()
result = manager.validate_crew_output(data, "stock", "analysis")

if not result.is_valid:
    for error in result.errors:
        print(f"Field: {error.field_path}")
        print(f"Error: {error.message}")
        print(f"Value: {error.input_value}")
```

### Caching Issues
```python
# Debug cache problems
from finwiz.utils.cache_manager import get_cache_manager

cache = get_cache_manager()
stats = cache.get_stats()

print(f"Hit rate: {stats['hit_rate']:.2%}")
print(f"Entry count: {stats['entry_count']}")
print(f"Memory usage: {stats['total_size_mb']:.1f} MB")
```

### Test Migration Issues
```python
# Ensure Faker generates appropriate data
from faker import Faker

fake = Faker()
fake.add_provider('finwiz.tests.providers.FinancialProvider')  # Custom provider

# Generate realistic financial data
ticker = fake.stock_ticker()  # Returns valid ticker format
price = fake.stock_price(min_value=1.0, max_value=1000.0)
```

## Performance Considerations

### Validation Performance
- WARN mode has minimal overhead
- OFF mode has zero validation overhead
- ERROR mode provides strictest validation

### Caching Performance
- Hybrid backend provides best balance
- Memory backend is fastest but limited
- File backend is persistent but slower

### Test Performance
- Dynamic data generation is fast
- Mocked APIs eliminate network overhead
- Parallel test execution with pytest-xdist

## Support and Resources

- **Documentation**: See `docs/validation_system.md` and `docs/caching_system.md`
- **Examples**: Check `tests/` directory for usage examples
- **Configuration**: Review environment variable documentation
- **Performance**: Monitor cache statistics and validation metrics

This migration is designed to be non-breaking and can be adopted incrementally based on your needs and timeline.