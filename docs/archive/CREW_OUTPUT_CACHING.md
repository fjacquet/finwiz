# Crew Output Caching Feature

## Overview

The crew output caching feature automatically checks for recent crew output files before executing crews, saving significant time by reusing recent results instead of regenerating them.

### Two Complementary Caching Systems

FinWiz uses **two caching systems** that work together:

1. **Crew Output Cache** (this document)
   - **Purpose**: Cache entire crew outputs (discovery crews)
   - **Scope**: Whole crew execution (all tickers together)
   - **For**: Stock/ETF/Crypto discovery crews
   - **Config**: `CREW_CACHE_ENABLED`, `CREW_CACHE_MAX_AGE_HOURS`

2. **Analysis Cache Manager** (separate system)
   - **Purpose**: Cache individual ticker analyses
   - **Scope**: Per-ticker, per-asset-class
   - **For**: Portfolio holding analysis (DeepAnalysisCrew)
   - **Config**: `PORTFOLIO_CACHE_TTL_HOURS`

Both systems are **complementary, not redundant** - they cache different things at different granularities and both provide significant value.

## How It Works

### Automatic Cache Check

Before executing any crew (stock, ETF, crypto), the system:

1. **Checks for existing output files** in `output/{crew_name}/`
2. **Finds the most recent file** (by modification time)
3. **Checks if it's recent enough** (default: 24 hours)
4. **Loads and uses cached data** if available and recent
5. **Executes the crew** only if no recent cache exists

### Cache Metadata

Cached data includes metadata:

```json
{
  "_cache_metadata": {
    "cached": true,
    "cache_file": "output/stock/stock_analysis_2025-10-16.json",
    "cache_age_hours": 2.5,
    "cache_timestamp": "2025-10-16T08:30:00"
  }
}
```

## Configuration

### Environment Variables

```bash
# Enable/disable caching (default: true)
CREW_CACHE_ENABLED=true

# Maximum age in hours for cached files (default: 24)
CREW_CACHE_MAX_AGE_HOURS=24
```

### Example Configurations

**Fast Development** (use 1-hour cache):

```bash
CREW_CACHE_ENABLED=true
CREW_CACHE_MAX_AGE_HOURS=1
```

**Production** (use 24-hour cache):

```bash
CREW_CACHE_ENABLED=true
CREW_CACHE_MAX_AGE_HOURS=24
```

**Always Fresh** (disable caching):

```bash
CREW_CACHE_ENABLED=false
```

## Usage

### Automatic (Default Behavior)

Caching is enabled by default. Just run the application normally:

```bash
uv run python src/finwiz/main.py
```

The system will automatically:

- Use cached stock analysis if < 24 hours old
- Use cached ETF analysis if < 24 hours old
- Use cached crypto analysis if < 24 hours old
- Execute crews only when cache is stale or missing

### Force Fresh Analysis

To bypass cache and force fresh analysis:

```bash
# Disable caching for this run
CREW_CACHE_ENABLED=false uv run python src/finwiz/main.py

# Or delete old cache files
rm -rf output/stock/*.json output/etf/*.json output/crypto/*.json
```

## Log Messages

### Cache Hit (Using Cached Data)

```
INFO - ✅ Using cached stock output from stock_analysis_2025-10-16.json (age: 2.5h)
INFO - ✅ Using cached etf output from etf_analysis_2025-10-16.json (age: 1.8h)
INFO - ✅ Using cached crypto output from crypto_analysis_2025-10-16.json (age: 3.2h)
```

### Cache Miss (Executing Crew)

```
INFO - Cached stock output too old (25.3h > 24.0h), will regenerate
INFO - Starting stock analysis crew (Phase 2: Core Analysis)
```

### Cache Disabled

```
INFO - Crew output caching disabled
INFO - Starting stock analysis crew (Phase 2: Core Analysis)
```

## Benefits

### Time Savings

Typical crew execution times:

- Stock crew: ~5-10 minutes
- ETF crew: ~5-10 minutes
- Crypto crew: ~5-10 minutes
- **Total without cache**: ~15-30 minutes

With caching (if all crews have recent output):

- **Total with cache**: ~5-10 seconds (just loading files)

**Time saved**: ~15-30 minutes per run!

### Cost Savings

- Fewer API calls to OpenAI, Serper, etc.
- Reduced token usage
- Lower operational costs

### Development Efficiency

- Faster iteration during development
- Quick testing of downstream components
- Easier debugging of report generation

## Cache Invalidation

Cache is automatically invalidated when:

1. **File age exceeds max age** (default: 24 hours)
2. **Cache is disabled** via environment variable
3. **Output files are deleted** manually

### Manual Cache Invalidation

```bash
# Invalidate all crew caches
rm -rf output/stock/*.json output/etf/*.json output/crypto/*.json

# Invalidate specific crew cache
rm output/stock/*.json

# Invalidate old files only (keep recent)
find output/stock -name "*.json" -mtime +1 -delete
```

## Implementation Details

### Files Modified

1. **src/finwiz/utils/crew_output_cache.py** (new)
   - `CrewOutputCache` class
   - Cache checking and loading logic
   - File age calculation

2. **src/finwiz/crew_factory.py** (modified)
   - Added cache initialization
   - Added cache checks before crew execution
   - Added cache metadata to responses

### Supported Crews

Currently caching is implemented for:

- ✅ Stock crew (`execute_stock_crew`)
- ✅ ETF crew (`execute_etf_crew`)
- ✅ Crypto crew (`execute_crypto_crew`)

Not cached (by design):

- ❌ Report crew (always generates fresh reports)
- ❌ Portfolio review (needs fresh data)
- ❌ Discovery crew (needs fresh screening)
- ❌ Rebalancing crew (needs fresh calculations)

## Testing

### Test Cache Functionality

```python
from finwiz.utils.crew_output_cache import get_crew_output_cache

# Create cache instance
cache = get_crew_output_cache(max_age_hours=24)

# Check cache info
info = cache.get_cache_info("stock")
print(f"Cache exists: {info['exists']}")
print(f"Cache age: {info.get('age_hours', 'N/A')}h")
print(f"Is recent: {info.get('is_recent', False)}")

# Get cached data
cached_data = cache.get_cached_crew_output("stock")
if cached_data:
    print("✅ Using cached data")
else:
    print("❌ No recent cache, will execute crew")
```

### Verify Cache is Working

```bash
# Run once (will execute crews)
uv run python src/finwiz/main.py

# Check logs for crew execution
grep "Starting.*crew" logs/finwiz.log

# Run again immediately (should use cache)
uv run python src/finwiz/main.py

# Check logs for cache usage
grep "Using cached.*output" logs/finwiz.log
```

## Troubleshooting

### Cache Not Being Used

**Check 1**: Is caching enabled?

```bash
grep "Crew output caching" logs/finwiz.log
# Should see: "Crew output caching enabled (max age: 24h)"
```

**Check 2**: Do output files exist?

```bash
ls -lh output/stock/*.json output/etf/*.json output/crypto/*.json
```

**Check 3**: Are files recent enough?

```bash
# Check file age (macOS)
stat -f "%Sm" output/stock/*.json

# Check file age (Linux)
stat -c "%y" output/stock/*.json
```

### Cache Too Old

If cache is always too old, increase max age:

```bash
CREW_CACHE_MAX_AGE_HOURS=48 uv run python src/finwiz/main.py
```

### Want Fresh Data

To force fresh analysis:

```bash
# Option 1: Disable cache
CREW_CACHE_ENABLED=false uv run python src/finwiz/main.py

# Option 2: Delete cache files
rm output/stock/*.json output/etf/*.json output/crypto/*.json
```

## Best Practices

### Development

- Use **1-hour cache** for rapid iteration
- Disable cache when testing crew changes
- Keep cache enabled for report testing

### Production

- Use **24-hour cache** for daily reports
- Use **6-hour cache** for intraday updates
- Disable cache for critical real-time analysis

### CI/CD

- Disable cache in CI/CD pipelines
- Always generate fresh data for releases
- Use cache for integration tests

## Future Enhancements

Potential improvements:

1. **Smart invalidation** - Invalidate cache when input data changes
2. **Partial caching** - Cache individual ticker analyses
3. **Cache warming** - Pre-generate cache during off-hours
4. **Cache sharing** - Share cache across multiple runs
5. **Cache compression** - Compress old cache files

---

**Status**: ✅ Implemented and tested  
**Date**: 2025-10-16  
**Version**: 1.0
