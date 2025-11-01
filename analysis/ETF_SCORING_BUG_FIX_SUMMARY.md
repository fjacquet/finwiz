# ETF Scoring Bug Fix Summary

## Bug Identified ✅

**Root Cause**: Portfolio deep analyzer was using **hardcoded default values** for critical ETF metrics when real data was unavailable:

```python
# BEFORE (DANGEROUS):
"expense_ratio": perf_data.get("expense_ratio", 0.20),  # Default 20%!
"tracking_error": perf_data.get("tracking_error", 0.30),  # Default 30%!
```

**Impact**: 
- CORC.SW received **A+ grade** with composite score **0.91**
- Used default expense_ratio=0.20 (20%) and tracking_error=0.30 (30%)
- These are **TERRIBLE** values but were treated as real data
- Fundamental score was 0.84 instead of ~0.20

## Why This Happened

1. **QuantitativeAnalysisTool** doesn't return `expense_ratio` or `tracking_error` for ETFs
2. **Portfolio analyzer** used hardcoded defaults instead of failing
3. **Scorer** treated defaults as real data and calculated scores
4. **Result**: Terrible ETF got excellent grade

## Fixes Applied

### 1. Removed Dangerous Defaults ✅

```python
# AFTER (SAFE):
"expense_ratio": perf_data.get("expense_ratio"),  # No default - will fail if missing
"tracking_error": perf_data.get("tracking_error"),  # No default - will fail if missing
```

**Behavior**: If these critical fields are missing, `CriticalFieldError` will be raised and the holding will be skipped.

### 2. Added Detailed Logging ✅

```python
if asset_class == "etf":
    self.logger.info(
        f"✅ Fetched ETF data for {ticker}: "
        f"expense_ratio={data.get('expense_ratio')}, "
        f"tracking_error={data.get('tracking_error')}, "
        f"aum={data.get('aum')}, volatility={data['volatility']:.3f}"
    )
```

### 3. Added Details to Output ✅

Modified `DeepAnalysisResult` schema to include:
- `fundamental_details`: Breakdown of fundamental scoring
- `technical_details`: Breakdown of technical scoring

This allows debugging to see actual values used in scoring.

### 4. Added Scorer Logging ✅

```python
self.logger.info(f"ETF {ticker}: expense_ratio = {expense_ratio} (raw value)")
self.logger.info(f"ETF {ticker}: expense_score = {expense_score}")
self.logger.info(f"ETF {ticker}: tracking_error = {tracking_error} (raw value)")
self.logger.info(f"ETF {ticker}: tracking_score = {tracking_score}")
```

## Expected Behavior After Fix

### Scenario 1: Real Data Available
```python
# ETF with real data
expense_ratio = 0.09  # 9% from API
tracking_error = 0.15  # 15% from API

# Scoring:
expense_score = 1.0  # Excellent!
tracking_score = 1.0  # Excellent!
fundamental_score = 0.84  # Good ETF
grade = "A+"  # Correct!
```

### Scenario 2: Data Missing (After Fix)
```python
# ETF with missing data
expense_ratio = None  # Not available
tracking_error = None  # Not available

# Result:
CriticalFieldError raised
Holding skipped
User notified: "Missing critical fields: expense_ratio, tracking_error"
```

### Scenario 3: Data Missing (Before Fix) ❌
```python
# ETF with missing data
expense_ratio = 0.20  # DEFAULT (20% - terrible!)
tracking_error = 0.30  # DEFAULT (30% - terrible!)

# Scoring:
expense_score = 0.8  # Treated as 20% (good)
tracking_score = 0.8  # Treated as 30% (good)
fundamental_score = 0.84  # WRONG!
grade = "A+"  # WRONG!
```

## Next Steps

### 1. Fix QuantitativeAnalysisTool ⏳

The tool needs to fetch and return `expense_ratio` and `tracking_error` for ETFs:

```python
# In QuantitativeAnalysisTool for ETFs:
if asset_class == "etf":
    # Fetch ETF-specific data
    etf_info = yf.Ticker(symbol).info
    result["expense_ratio"] = etf_info.get("annualReportExpenseRatio")
    result["tracking_error"] = calculate_tracking_error(...)  # Need to calculate
```

### 2. Add Data Source for Tracking Error ⏳

Tracking error requires:
- ETF returns
- Benchmark returns
- Calculation: `std(etf_returns - benchmark_returns)`

Options:
- Calculate from historical data
- Fetch from ETF provider API
- Use Yahoo Finance if available

### 3. Test with Real ETF ⏳

```bash
# Test with SPY (should have complete data)
uv run python -c "
from finwiz.scoring.portfolio_deep_analyzer import PortfolioDeepAnalyzer
from finwiz.schemas.portfolio_review import HoldingDecision

analyzer = PortfolioDeepAnalyzer()
# Create test holding for SPY
# Run analysis
# Verify expense_ratio and tracking_error are fetched
"
```

### 4. Update Critical Fields Config ⏳

Verify that `expense_ratio` and `tracking_error` are in the critical fields list:

```python
# In critical_fields_config.py
CRITICAL_FIELDS = {
    "etf": [
        "current_price",
        "expense_ratio",  # ✅ Already there
        "tracking_error",  # ✅ Already there
        "aum",
        "volatility",
    ],
}
```

## Files Modified

- ✅ `src/finwiz/scoring/portfolio_deep_analyzer.py` - Removed dangerous defaults
- ✅ `src/finwiz/scoring/deep_analysis_scorer.py` - Added logging
- ✅ `src/finwiz/flow_state.py` - Added fundamental_details and technical_details fields

## Testing

### Before Fix
```json
{
  "ticker": "CORC.SW",
  "grade": "A+",
  "fundamental_score": 0.84,
  "fundamental_details": {},  // Empty!
  "rationale": "...expense ratio of 20.00% and tracking error of 30.00%..."
}
```

### After Fix (Expected)
```
❌ SKIPPING CORC.SW: Missing critical fields ['expense_ratio', 'tracking_error']
   Cannot make investment decision without real data.
   Recommendation: Check API connectivity and data sources.
```

## Impact

✅ **Safety**: No more recommendations based on hardcoded defaults
✅ **Transparency**: Users know when data is missing
✅ **Accuracy**: Only real data used for scoring
⚠️ **More Skipped Holdings**: ETFs without expense_ratio/tracking_error will be skipped until data source is fixed

## Priority

**P0 - CRITICAL**: This bug could cause users to buy terrible ETFs with high fees.

**Next Action**: Fix QuantitativeAnalysisTool to fetch ETF-specific metrics.

---

**Status**: ✅ Dangerous defaults removed, fail-fast implemented
**Date**: 2025-11-01
**Impact**: HIGH - Prevents bad investment recommendations
