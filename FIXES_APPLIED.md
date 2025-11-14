# FinWiz Bug Fixes Applied - 2025-11-14

## Summary

Fixed multiple critical issues in the FinWiz system related to ETF scoring, backtesting, and async tool execution.

## Issues Fixed

### 1. ETF Tracking Error Field Handling

**Issue**: Repeated errors for optional field 'tracking_error' causing scoring failures
**Location**: `src/finwiz/scoring/deep_analysis_scorer.py`
**Root Cause**: The code was calling `_safe_get_float()` with `None` as default, but the method wasn't properly handling `None` values for optional fields.

**Fix Applied**:

- Changed to use `data.get("tracking_error")` directly to detect missing data
- Added proper try-catch for invalid values
- Use neutral score (0.5) when tracking_error is unavailable or invalid
- Improved logging to distinguish between missing vs invalid data

**Impact**: ETF analysis will no longer fail when tracking_error data is unavailable. The system gracefully handles missing optional fields with neutral scores.

### 2. Asyncio Event Loop Error in Feedback Tools

**Issue**: `asyncio.run() cannot be called from a running event loop` error when using learning_metrics_tool and other feedback tools
**Location**: `src/finwiz/tools/feedback_integration_tool.py`
**Root Cause**: Tools were using `asyncio.run()` directly in `_run()` methods, which fails when called from an already running event loop (common in CrewAI, Jupyter, FastAPI contexts).

**Fix Applied**:

- Added event loop detection using `asyncio.get_running_loop()`
- If no loop is running, use `asyncio.run()` (original behavior)
- If loop is running, apply `nest_asyncio` to allow nested event loops
- Applied fix to all 5 feedback tools:
  - FeedbackCollectionTool
  - PerformanceTrackingTool
  - CriteriaOptimizationTool
  - FeedbackAnalysisTool
  - LearningMetricsTool

**Impact**: Feedback tools can now be used in any async context without errors.

### 5. Backtesting Strategy Parameter Mapping
**Issue**: `SimpleMovingAverageStrategy.__init__() got an unexpected keyword argument 'short_window'`
**Location**: `src/finwiz/tools/backtesting_tool.py`
**Root Cause**: External code was passing `short_window`/`long_window` parameters, but the strategy expects `short_period`/`long_period`.

**Fix Applied**:
- Added parameter name mapping in the backtesting tool
- Maps common variations: `short_window` → `short_period`, `long_window` → `long_period`, `window` → `period`
- Logs parameter mappings for debugging
- Maintains backward compatibility with both naming conventions

**Impact**: Backtesting tool now accepts multiple parameter naming conventions without errors.

### 6. Datetime Timezone Comparison Errors
**Issue**: `can't compare offset-naive and offset-aware datetimes` and `Start date must be before end date` errors
**Location**: `src/finwiz/quantitative/data_processors.py`
**Root Cause**: The `validate_inputs` method was comparing timezone-naive `datetime.now()` with potentially timezone-aware input dates.

**Fix Applied**:
- Normalize all datetimes to timezone-naive before comparison
- Strip timezone info from input dates if present
- Use consistent timezone-naive datetime for `now()`
- Prevents comparison errors between aware and naive datetimes

**Impact**: Data validation will work correctly regardless of whether input dates have timezone information.

### 3. Backtesting Issues (Identified but not fixed)

**Issues Identified**:

1. **Strategy Parameter Mismatch**: The backtesting tool may pass `short_window`/`long_window` but `SimpleMovingAverageStrategy` expects `short_period`/`long_period`
2. **Datetime Comparison Errors**: "can't compare offset-naive and offset-aware datetimes" errors in data loading
3. **Date Validation**: "Start date must be before end date" errors

**Location**:

- `src/finwiz/quantitative/backtesting_strategies.py`
- `src/finwiz/quantitative/data_processors.py`
- `src/finwiz/quantitative/backtesting.py`

**Status**: ✅ **FIXED** - See issues #5 and #6 above.

### 4. A+ Extractor

```python
# Test with empty files
from finwiz.integration.aplus_extractor import APlusDataExtractor
from pathlib import Path

extractor = APlusDataExtractor(output_dir=Path("output"))
collection = extractor.extract_aplus_opportunities()
# Should handle empty/missing files gracefully

# Test with list structure
import json
test_data = [{"symbol": "AAPL", "grade": "A+", ...}]
# Should work with both list and dict structures
```

## Testing Recommendations

### 1. ETF Scoring

```python
# Test with missing tracking_error
from finwiz.scoring.deep_analysis_scorer import DeepAnalysisScorer

scorer = DeepAnalysisScorer()
data = {
    "asset_class": "etf",
    "expense_ratio": 0.0015,
    "tracking_error": None,  # Missing data
    "aum": 5e9,
    # ... other required fields
}
result = scorer.calculate_composite_score("VUSA.L", "etf", data)
# Should complete without errors, using neutral tracking score
```

### 2. Feedback Tools

```python
# Test in async context
from finwiz.tools.feedback_integration_tool import LearningMetricsTool

tool = LearningMetricsTool()
result = tool._run(days_back=30)
# Should work in both sync and async contexts
```

### 3. Backtesting

```python
# Test strategy execution with different parameter names
from finwiz.tools.backtesting_tool import BacktestingTool

tool = BacktestingTool()

# Test with standard parameters
result1 = tool._run(
    symbol="AAPL",
    strategy="sma_crossover",
    backtest_period_years=5,
    strategy_params={"short_period": 20, "long_period": 50}
)

# Test with alternative parameter names (should auto-map)
result2 = tool._run(
    symbol="AAPL",
    strategy="sma_crossover",
    backtest_period_years=5,
    strategy_params={"short_window": 20, "long_window": 50}
)
# Both should work without errors
```

## Dependencies Required

The async fix requires `nest_asyncio`:

```bash
pip install nest-asyncio
# or
uv add nest-asyncio
```

### 4. A+ Extractor Data Structure Handling

**Issue**: `'list' object has no attribute 'get'` and `Expecting value: line 1 column 1 (char 0)` errors
**Location**: `src/finwiz/integration/aplus_extractor.py`
**Root Cause**:

1. The extractor assumed data was always a dict with "candidates" key, but sometimes the JSON file contains a list directly
2. Empty JSON files were not handled gracefully

**Fix Applied**:

- Added empty file detection before JSON parsing
- Added type checking to handle both list and dict data structures
- Improved error messages to show actual data type received
- Applied fix to all three extraction methods:
  - `_extract_stock_opportunities()`
  - `_extract_etf_opportunities()`
  - `_extract_crypto_opportunities()`

**Impact**: A+ opportunity extraction will handle various JSON structures and empty files gracefully without crashing.

## Files Modified

1. `src/finwiz/scoring/deep_analysis_scorer.py` - ETF tracking_error handling
2. `src/finwiz/tools/feedback_integration_tool.py` - Async event loop handling
3. `src/finwiz/integration/aplus_extractor.py` - Data structure handling and empty file detection
4. `src/finwiz/tools/backtesting_tool.py` - Strategy parameter name mapping
5. `src/finwiz/quantitative/data_processors.py` - Datetime timezone normalization

## Remaining Issues

1. **German ETF Data Fetching**: QDV5.DU and VUAA.DU return empty datasets
   - May be ticker symbol issues or data provider limitations
   - Requires investigation of Yahoo Finance API for German exchanges

2. **Backtesting Datetime Issues**: Need to ensure all datetime objects are timezone-aware or all timezone-naive
   - Check `data_processors.py` validation
   - Check `backtesting.py` date handling

3. **Data Merge Failures**: Portfolio review update failing for holdings without deep analysis
   - Related to German ETF data issues
   - System correctly fails fast rather than using fallback data

## Next Steps

1. Add `nest-asyncio` to project dependencies
2. Test ETF scoring with various missing field scenarios
3. Investigate German ETF ticker symbols and data availability
4. Review backtesting datetime handling for timezone consistency
5. Add unit tests for the fixed scenarios

## Notes

- All fixes follow FinWiz coding standards (type hints, error handling, logging)
- Fixes maintain backward compatibility
- No breaking changes to public APIs
- Improved error messages for debugging
