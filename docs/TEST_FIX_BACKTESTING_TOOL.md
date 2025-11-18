# Backtesting Tool Test Fixes - Summary

## Status: ✅ COMPLETE

**File**: `/Users/fjacquet/Projects/kiro/finwiz/tests/unit/tools/test_backtesting_tool.py`

**Results**:
- **Before**: Multiple test failures due to incorrect mock paths
- **After**: 18/18 tests PASSED (100% pass rate)
- **Execution Time**: ~3 seconds (without coverage)

## Root Cause Analysis

The backtesting tool tests were failing due to incorrect mock import paths. The tests were mocking functions at the wrong module locations, causing the real implementations to be called instead of the mocks.

### Architecture Discovery

After analyzing the codebase, we identified the correct import architecture:

1. **BacktestingEngine** (`finwiz.quantitative.backtesting`):
   - Factory function: `get_backtesting_engine()`
   - Directly creates `HistoricalDataManager()` in `__init__()` (line 65)
   - Located at: `finwiz.quantitative.backtesting`

2. **HistoricalDataManager** (`finwiz.quantitative.data`):
   - Factory function: `get_historical_data_manager()`
   - Imported in backtesting_tool.py (line 16)
   - Called in `_run()` method (line 148)

3. **PerformanceAnalyzer** (`finwiz.quantitative.performance`):
   - Factory function: `get_performance_analyzer()`
   - Imported in backtesting_tool.py (line 17)
   - Called in `_run()` method (line 149)

4. **SimpleMovingAverageStrategy** (`finwiz.quantitative.backtesting_strategies`):
   - Strategy class for Backtrader
   - Used in `_get_strategy_class()` method

## Changes Made

### 1. Fixed Import Path for Strategy Class
**File**: `tests/unit/tools/test_backtesting_tool.py`, Line 314

**Before**:
```python
from finwiz.quantitative.backtesting import SimpleMovingAverageStrategy
```

**After**:
```python
from finwiz.quantitative.backtesting_strategies import SimpleMovingAverageStrategy
```

**Reason**: Strategy classes are in `backtesting_strategies.py`, not `backtesting.py`

### 2. Fixed Mock Paths for Basic Backtest Test
**File**: `tests/unit/tools/test_backtesting_tool.py`, Lines 242-277

**Before**:
```python
mock_backtesting_engine = mocker.patch("finwiz.quantitative.backtesting.get_backtesting_engine")
mock_data_manager = mocker.patch("finwiz.quantitative.data.get_historical_data_manager")
mock_perf_analyzer = mocker.patch("finwiz.quantitative.performance.get_performance_analyzer")
```

**After**:
```python
# Line 145: from finwiz.quantitative.backtesting import get_backtesting_engine
# Line 148: data_manager = get_historical_data_manager()
# Line 149: get_performance_analyzer()
mock_backtesting_engine = mocker.patch("finwiz.quantitative.backtesting.get_backtesting_engine")
mock_data_manager = mocker.patch("finwiz.tools.backtesting_tool.get_historical_data_manager")
mock_perf_analyzer = mocker.patch("finwiz.tools.backtesting_tool.get_performance_analyzer")
```

**Reason**:
- `get_backtesting_engine` is imported from quantitative.backtesting in the tool (line 145)
- `get_historical_data_manager` and `get_performance_analyzer` are imported at module level (lines 16-17) but called in `_run()` method, so we mock at the tool's module location

### 3. Fixed Mock Paths for Regime Analysis Test
**File**: `tests/unit/tools/test_backtesting_tool.py`, Lines 276-312

**Before**:
```python
mock_data_manager_class = mocker.patch("finwiz.quantitative.backtesting.HistoricalDataManager")
mock_backtesting_engine = mocker.patch("finwiz.quantitative.backtesting.get_backtesting_engine")
mock_data_manager_func = mocker.patch("finwiz.quantitative.data.get_historical_data_manager")
mock_perf_analyzer = mocker.patch("finwiz.quantitative.performance.get_performance_analyzer")
```

**After**:
```python
# Line 148: data_manager = get_historical_data_manager()
mock_data_manager_func = mocker.patch("finwiz.tools.backtesting_tool.get_historical_data_manager")
mock_backtesting_engine = mocker.patch("finwiz.quantitative.backtesting.get_backtesting_engine")
mock_perf_analyzer = mocker.patch("finwiz.tools.backtesting_tool.get_performance_analyzer")
```

**Reason**:
- Mock at the actual import location in `backtesting_tool.py`, not the original module
- Removed unnecessary `HistoricalDataManager` class mock (not needed when mocking the factory function correctly)

## Key Lessons Learned

### 1. Mock at Import Location, Not Definition Location
**Rule**: When mocking functions, mock them where they are **imported and used**, not where they are **defined**.

**Example**:
```python
# backtesting_tool.py (top of file)
from finwiz.quantitative.data import get_historical_data_manager

# backtesting_tool.py (_run method)
def _run(self):
    data_manager = get_historical_data_manager()  # Called here

# Test - Mock at the tool's module location
mocker.patch("finwiz.tools.backtesting_tool.get_historical_data_manager")
```

### 2. Trace Import Flow Carefully
For lazy imports (imports inside methods), mock at the import statement location:

```python
# backtesting_tool.py (_run method)
def _run(self):
    from finwiz.quantitative.backtesting import get_backtesting_engine  # Imported here
    engine = get_backtesting_engine()

# Test - Mock at the original module (since import is inside method)
mocker.patch("finwiz.quantitative.backtesting.get_backtesting_engine")
```

### 3. Factory Functions vs Direct Instantiation
- **Factory function** (`get_backtesting_engine()`): Mock the factory function
- **Direct instantiation** (`HistoricalDataManager()`): Mock the class itself

In this case, we use factory functions everywhere, so we mock the factory functions.

### 4. pytest-mock is Required (Not unittest.mock)
FinWiz enforces pytest-mock usage:
- ✅ Use `mocker.patch()` (pytest-mock)
- ❌ Never use `unittest.mock.patch()` (banned by ruff rules)

## Test Coverage

All 18 tests now pass:

1. ✅ `test_should_create_valid_input_with_defaults`
2. ✅ `test_should_create_valid_input_with_custom_values`
3. ✅ `test_should_validate_backtest_period_range`
4. ✅ `test_should_validate_initial_capital_positive`
5. ✅ `test_should_create_valid_market_regime`
6. ✅ `test_should_create_valid_backtesting_result`
7. ✅ `test_should_have_correct_tool_properties`
8. ✅ `test_should_run_basic_backtest_successfully`
9. ✅ `test_should_perform_regime_analysis_when_enabled`
10. ✅ `test_should_get_correct_strategy_class`
11. ✅ `test_should_calculate_additional_metrics`
12. ✅ `test_should_identify_market_regimes`
13. ✅ `test_should_validate_strategy_performance`
14. ✅ `test_should_handle_empty_benchmark_data_gracefully`
15. ✅ `test_should_handle_backtesting_errors_gracefully`
16. ✅ `test_should_validate_high_performing_strategy`
17. ✅ `test_should_validate_poor_performing_strategy`
18. ✅ `test_should_create_backtesting_tool_instance`

## Verification Commands

```bash
# Run all backtesting tool tests
uv run pytest tests/unit/tools/test_backtesting_tool.py -v

# Run specific test
uv run pytest tests/unit/tools/test_backtesting_tool.py::TestBacktestingTool::test_should_perform_regime_analysis_when_enabled -xvs

# Run without coverage check
uv run pytest tests/unit/tools/test_backtesting_tool.py -v --no-cov
```

## Related Files

**Implementation**:
- `/Users/fjacquet/Projects/kiro/finwiz/src/finwiz/tools/backtesting_tool.py`
- `/Users/fjacquet/Projects/kiro/finwiz/src/finwiz/quantitative/backtesting.py`
- `/Users/fjacquet/Projects/kiro/finwiz/src/finwiz/quantitative/backtesting_strategies.py`
- `/Users/fjacquet/Projects/kiro/finwiz/src/finwiz/quantitative/data.py`
- `/Users/fjacquet/Projects/kiro/finwiz/src/finwiz/quantitative/performance.py`

**Tests**:
- `/Users/fjacquet/Projects/kiro/finwiz/tests/unit/tools/test_backtesting_tool.py`

## Next Steps

This test file is now fully fixed and can serve as a reference for fixing similar mock path issues in other test files. The patterns established here should be applied to:

1. Other tool tests with quantitative module dependencies
2. Tests that use factory functions from the quantitative module
3. Any test experiencing "real implementation called instead of mock" issues

---

**Date**: 2025-11-16
**Status**: Complete
**Pass Rate**: 18/18 (100%)
**Execution Time**: ~3 seconds
