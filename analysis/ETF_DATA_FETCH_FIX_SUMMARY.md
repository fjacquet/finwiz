# ETF Data Fetch Fix Summary

## Problem

QuantitativeAnalysisTool was not fetching ETF-specific metrics (expense_ratio, tracking_error, AUM), causing the portfolio analyzer to use dangerous hardcoded defaults.

## Solution Implemented

### 1. Added ETF Data Fetching to QuantitativeAnalysisTool ✅

Modified `_perform_performance_analysis()` to fetch ETF-specific data from Yahoo Finance:

```python
if input_data.asset_class == "etf":
    import yfinance as yf
    
    ticker = yf.Ticker(input_data.symbol)
    info = ticker.info
    
    # Fetch expense ratio
    expense_ratio = info.get("netExpenseRatio") or info.get("annualReportExpenseRatio")
    if expense_ratio is not None:
        # Convert from percentage (0.0945%) to decimal (0.000945)
        perf_dict["expense_ratio"] = float(expense_ratio) / 100.0
    
    # Fetch AUM
    total_assets = info.get("totalAssets")
    if total_assets is not None:
        perf_dict["aum"] = float(total_assets)
```

### 2. Yahoo Finance Field Mapping

| FinWiz Field | Yahoo Finance Key | Format | Example |
|--------------|------------------|--------|---------|
| `expense_ratio` | `netExpenseRatio` | Percentage → Decimal | 0.0945% → 0.000945 |
| `aum` | `totalAssets` | Dollars | $672,726,646,784 |
| `tracking_error` | ⚠️ Not available | Must calculate | TODO |

### 3. Data Format Conversion

**Critical**: Yahoo Finance returns expense ratio as a percentage (0.0945 = 0.0945%), but our scorer expects decimal format (0.000945 = 0.0945%).

**Conversion**:
```python
expense_ratio_decimal = expense_ratio / 100.0
# 0.0945 / 100.0 = 0.000945
```

### 4. Removed Dangerous Defaults ✅

Portfolio analyzer no longer uses hardcoded defaults:

```python
# BEFORE (DANGEROUS):
"expense_ratio": perf_data.get("expense_ratio", 0.20),  # 20% default!

# AFTER (SAFE):
"expense_ratio": perf_data.get("expense_ratio"),  # None if missing → CriticalFieldError
```

## Test Results

### SPY (S&P 500 ETF)
```
✅ Expense Ratio: 0.0945% (netExpenseRatio)
✅ AUM: $672.73B (totalAssets)
⚠️ Tracking Error: Not available (must calculate)
```

### QQQ (Nasdaq-100 ETF)
```
✅ Expense Ratio: Available via netExpenseRatio
✅ AUM: $385.76B (totalAssets)
⚠️ Tracking Error: Not available (must calculate)
```

### VTI (Total Stock Market ETF)
```
✅ Expense Ratio: Available via netExpenseRatio
✅ AUM: $2,016.76B (totalAssets)
⚠️ Tracking Error: Not available (must calculate)
```

## Scoring Thresholds (Reminder)

Our scorer expects expense ratios as **decimals** (not percentages):

```python
# Expense ratio thresholds (as decimals)
if expense_ratio <= 0.0010:  # 0.10% or less → score 1.0
elif expense_ratio <= 0.0025:  # 0.10-0.25% → score 0.8
elif expense_ratio <= 0.0050:  # 0.25-0.50% → score 0.6
elif expense_ratio <= 0.0100:  # 0.50-1.00% → score 0.4
else:  # >1.00% → score 0.2
```

**Wait, this is wrong!** The thresholds in the scorer are:

```python
if expense_ratio <= 0.10:  # This is 10%, not 0.10%!
```

## CRITICAL BUG FOUND! 🚨

The scorer thresholds are **100x too high**!

### Current Thresholds (WRONG):
- `<= 0.10` = 10% (should be 0.10%)
- `<= 0.25` = 25% (should be 0.25%)
- `<= 0.50` = 50% (should be 0.50%)

### Correct Thresholds (for typical ETFs):
- `<= 0.0010` = 0.10% (excellent)
- `<= 0.0025` = 0.25% (good)
- `<= 0.0050` = 0.50% (acceptable)
- `<= 0.0100` = 1.00% (high)
- `> 0.0100` = >1.00% (very high)

## Next Steps

### 1. Fix Scorer Thresholds ⏳ CRITICAL

The expense ratio and tracking error thresholds in `deep_analysis_scorer.py` need to be divided by 100:

```python
# Current (WRONG):
if expense_ratio <= 0.10:  # 10%

# Should be:
if expense_ratio <= 0.0010:  # 0.10%
```

### 2. Implement Tracking Error Calculation ⏳

Tracking error requires:
- ETF historical returns
- Benchmark historical returns
- Calculation: `std(etf_returns - benchmark_returns) * sqrt(252)`

Options:
- Fetch benchmark data from Yahoo Finance
- Calculate from historical data
- Use a default benchmark (e.g., SPY for US equity ETFs)

### 3. Test with Real Portfolio ⏳

Test the complete flow with a real portfolio containing ETFs.

## Files Modified

- ✅ `src/finwiz/tools/quantitative_analysis_tool.py` - Added ETF data fetching
- ✅ `src/finwiz/scoring/portfolio_deep_analyzer.py` - Removed dangerous defaults
- ⏳ `src/finwiz/scoring/deep_analysis_scorer.py` - Need to fix thresholds

## Impact

✅ **Expense Ratio**: Now fetched from Yahoo Finance
✅ **AUM**: Now fetched from Yahoo Finance
⚠️ **Tracking Error**: Still missing (will trigger CriticalFieldError)
🚨 **Scorer Thresholds**: Need urgent fix (100x too high)

---

**Status**: ⚠️ Partial fix - Data fetching works, but scorer thresholds are wrong
**Date**: 2025-11-01
**Priority**: P0 - CRITICAL (scorer thresholds must be fixed)
