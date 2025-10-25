# Deep Analysis Cache Bug Fix

## The Bug 🐛

**Issue**: Deep analysis was running every time despite having recent HTML output files, and no JSON cache files were being created.

**Root Cause**: The resilience-enhanced deep analysis method was missing caching logic.

## Investigation

### What We Found

1. **HTML files exist and are current** (Oct 16):
   ```bash
   -rw-r--r--@ 1 fjacquet  staff    24K Oct 16 22:48 AAPL_deep_analysis_stock.html
   ```

2. **JSON cache files are old** (Oct 10-11):
   ```bash
   -rw-r--r--@ 1 fjacquet  staff   1.1K Oct 10 07:13 AAPL_2025-10-10.json
   -rw-r--r--@ 1 fjacquet  staff   447B Oct 11 21:30 AAPL_2025-10-11.json
   ```

3. **Logs showed caching worked on Oct 11**:
   ```
   2025-10-11 15:38:14 - INFO - Cached analysis for AAPL (stock) at cache/portfolio_analysis/stock/AAPL_2025-10-11.json
   ```

4. **Recent runs show no cache creation** - HTML files generated but no JSON cache files.

### The Problem

The system switched from using:
- ❌ `_run_deep_analysis_on_holdings()` (has caching)

To using:
- ❌ `_run_deep_analysis_with_resilience()` → `_execute_deep_analysis_crew()` (no caching)

The resilience method was missing:
1. Cache manager initialization
2. Cache check before crew execution
3. Cache storage after crew execution

## The Fix ✅

### Files Modified

**File**: `src/finwiz/flows/flow_orchestrator.py`

### Changes Made

#### 1. Added Cache Manager to Resilience Method

```python
async def _run_deep_analysis_with_resilience(self, holdings: list[dict]) -> dict[str, Any]:
    # Initialize cache manager (same as in _run_deep_analysis_on_holdings)
    from finwiz.cache.analysis_cache_manager import get_analysis_cache_manager

    cache_ttl_hours = int(os.getenv("PORTFOLIO_CACHE_TTL_HOURS", "24"))
    cache_manager = get_analysis_cache_manager(ttl_hours=cache_ttl_hours)
```

#### 2. Added Cache Check to Crew Execution

```python
async def _execute_deep_analysis_crew(self, ticker: str, asset_class: str, max_reasoning_attempts: int) -> Any:
    # Initialize cache manager
    cache_ttl_hours = int(os.getenv("PORTFOLIO_CACHE_TTL_HOURS", "24"))
    cache_manager = get_analysis_cache_manager(ttl_hours=cache_ttl_hours)

    # Check cache first
    cached_result = cache_manager.get_cached_analysis(ticker, asset_class)
    if cached_result and cached_result.is_fresh(cache_ttl_hours):
        logger.info(f"Using cached analysis for {ticker} (age: {cached_result.age_hours:.1f}h)")
        # Return cached result
        return DeepAnalysisResult(...)
```

#### 3. Added Cache Storage After Execution

```python
    # Parse result using existing _parse_crew_output_for_holding method
    parsed_result = self._parse_crew_output_for_holding(...)

    # Cache the result (same as in _run_deep_analysis_on_holdings)
    cache_manager.cache_analysis(ticker, asset_class, parsed_result)

    # Convert to DeepAnalysisResult
    return DeepAnalysisResult(...)
```

### Bonus Fix: Improved Cache Lookup

Also fixed a secondary issue in `analysis_cache_manager.py` where it only looked for today's cache file. Now it:

1. First tries today's file (fast path)
2. If not found, looks for most recent file regardless of date
3. Checks if the found file is still fresh

## Expected Behavior After Fix

### First Run (Cache Miss)
```
INFO - Executing DeepAnalysisCrew for AAPL (stock) with max_reasoning_attempts=3
INFO - DeepAnalysisCrew execution completed for AAPL
INFO - Cached analysis for AAPL (stock) at cache/portfolio_analysis/stock/AAPL_2025-10-16.json
```

### Second Run (Cache Hit)
```
INFO - Using cached analysis for AAPL (age: 0.5h)
```

### File Structure After Fix
```
output/deep_analysis/
├── AAPL_deep_analysis_stock.html    # HTML report (always generated)

cache/portfolio_analysis/stock/
├── AAPL_2025-10-16.json            # JSON cache (now created!)
```

## Testing the Fix

### Verify Cache is Working

```bash
# Run deep analysis
uv run python src/finwiz/main.py

# Check for new cache files
ls -lh cache/portfolio_analysis/stock/*2025-10-16*

# Check logs for cache messages
grep "Cached analysis for\|Using cached analysis" logs/finwiz.log
```

### Expected Log Messages

**Cache Miss (First Run)**:
```
INFO - Executing DeepAnalysisCrew for AAPL (stock)
INFO - Cached analysis for AAPL (stock) at cache/portfolio_analysis/stock/AAPL_2025-10-16.json
```

**Cache Hit (Second Run)**:
```
INFO - Using cached analysis for AAPL (age: 1.2h)
```

## Configuration

The cache behavior is controlled by:

```bash
# Cache TTL (default: 24 hours)
PORTFOLIO_CACHE_TTL_HOURS=24

# To disable caching (force fresh analysis)
PORTFOLIO_CACHE_TTL_HOURS=0
```

## Impact

### Before Fix ❌
- Deep analysis ran every time (15-30 minutes for 65 holdings)
- No cache files created
- Wasted API calls and time

### After Fix ✅
- Deep analysis uses cache when available
- Cache files created after each run
- Significant time savings on subsequent runs
- Consistent with the original caching behavior

## Root Cause Analysis

**Why did this happen?**

1. **Code Evolution**: The resilience enhancement added a new execution path
2. **Missing Integration**: The new path didn't include existing caching logic
3. **No Tests**: No tests caught the missing caching functionality
4. **Silent Failure**: The system worked (generated HTML) but was inefficient

**Prevention**:
- Add tests for caching behavior
- Ensure new execution paths include all existing features
- Monitor cache hit rates in production

---

**Status**: ✅ **FIXED**  
**Date**: 2025-10-16  
**Impact**: Restored caching functionality to resilience-enhanced deep analysis  
**Files**: `src/finwiz/flows/flow_orchestrator.py`, `src/finwiz/cache/analysis_cache_manager.py`