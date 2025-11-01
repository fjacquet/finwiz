# ETF Scoring Bug Report - CORC.SW A+ Grade Issue

## Problem Statement

CORC.SW (ETF) received an **A+ grade** with a composite score of **0.91** despite having:
- **Expense ratio: 20.00%** (TERRIBLE - should be <0.25%)
- **Tracking error: 30.00%** (TERRIBLE - should be <0.20%)
- **Fundamental score: 0.84** (should be ~0.20 for such bad metrics)

## Evidence

### JSON Output
```json
{
  "ticker": "CORC.SW",
  "asset_class": "etf",
  "composite_score": 0.91,
  "grade": "A+",
  "recommendation": "BUY",
  "fundamental_score": 0.84,  // ❌ Should be ~0.20
  "technical_score": 0.92,
  "risk_score": 1.0,
  "fundamental_details": {},  // ❌ EMPTY!
  "technical_details": {},    // ❌ EMPTY!
  "rationale": "...expense ratio of 20.00% and tracking error of 30.00%..."
}
```

## Root Cause Analysis

### Issue 1: Empty Details Dictionaries ❌

**Problem**: `fundamental_details` and `technical_details` are empty in the output.

**Cause**: The `DeepAnalysisResult` schema was missing these fields, so they weren't being stored.

**Fix Applied**: 
1. Added fields to schema in `src/finwiz/flow_state.py`
2. Added fields to result creation in `src/finwiz/scoring/deep_analysis_scorer.py`

### Issue 2: Scoring Logic Confusion 🤔

**Expected Behavior**:
- Expense ratio 20% (0.20 as decimal) → score = 0.2 (lowest)
- Tracking error 30% (0.30 as decimal) → score = 0.2 (lowest)
- Fundamental score = 0.40 × 0.2 + 0.40 × 0.2 + 0.20 × aum_score = **~0.20**

**Actual Behavior**:
- Fundamental score = **0.84** (way too high!)

**Hypothesis**: The data might be coming in the wrong format:
- If expense_ratio = 0.0020 (0.20% as decimal), it would get score = 1.0 ✅
- If tracking_error = 0.0030 (0.30% as decimal), it would get score = 1.0 ✅
- This would give fundamental_score ≈ 0.84 ✅

## Data Format Investigation

### Scoring Thresholds (Current)

```python
# Expense ratio thresholds (as decimals)
if expense_ratio <= 0.10:  # 10% or less → score 1.0
elif expense_ratio <= 0.25:  # 10-25% → score 0.8
elif expense_ratio <= 0.50:  # 25-50% → score 0.6
elif expense_ratio <= 1.00:  # 50-100% → score 0.4
else:  # >100% → score 0.2

# Tracking error thresholds (as decimals)
if tracking_error <= 0.20:  # 20% or less → score 1.0
elif tracking_error <= 0.50:  # 20-50% → score 0.8
elif tracking_error <= 1.00:  # 50-100% → score 0.6
elif tracking_error <= 2.00:  # 100-200% → score 0.4
else:  # >200% → score 0.2
```

### Possible Data Formats

| Format | expense_ratio Value | tracking_error Value | Expected Score | Actual Score |
|--------|-------------------|---------------------|----------------|--------------|
| **Percentage** | 20.0 | 30.0 | 0.20 | ❌ 0.84 |
| **Decimal** | 0.20 | 0.30 | 0.72 | ❌ 0.84 |
| **Basis Points** | 0.0020 | 0.0030 | 0.84 | ✅ 0.84 |

**Conclusion**: The data is likely coming in as **basis points** (0.0020 = 20 basis points = 0.20%) instead of **percentages as decimals** (0.20 = 20%).

## The Bug

**Data Source Confusion**:
- Yahoo Finance or data tools are returning expense ratios in **basis points** (0.0020 = 0.20%)
- Scorer expects **percentages as decimals** (0.20 = 20%)
- Result: 20% expense ratio is interpreted as 0.20% (excellent!) instead of 20% (terrible!)

## Fixes Applied

### 1. Added Logging ✅

Added detailed logging to see actual values:

```python
self.logger.info(f"ETF {ticker}: expense_ratio = {expense_ratio} (raw value)")
self.logger.info(f"ETF {ticker}: expense_score = {expense_score}")
self.logger.info(f"ETF {ticker}: tracking_error = {tracking_error} (raw value)")
self.logger.info(f"ETF {ticker}: tracking_score = {tracking_score}")
```

### 2. Added Details to Output ✅

Modified schema and result creation to include `fundamental_details` and `technical_details` for debugging.

### 3. Fixed Comments ✅

Updated comments to clarify that thresholds are in decimal format (0.10 = 10%, not 0.10%).

## Next Steps

### Required Actions

1. **Run Analysis Again** with logging enabled to see actual values
2. **Identify Data Source** - where is expense_ratio coming from?
3. **Fix Data Format** - normalize to consistent format (percentages as decimals)
4. **Add Validation** - detect unrealistic values and warn

### Validation Rules to Add

```python
# Detect basis points format (values < 0.01 for percentages)
if expense_ratio < 0.01 and expense_ratio > 0:
    logger.warning(f"Expense ratio {expense_ratio} looks like basis points, converting to percentage")
    expense_ratio = expense_ratio * 100  # Convert 0.0020 → 0.20

# Detect percentage format (values > 1.0)
if expense_ratio > 1.0:
    logger.warning(f"Expense ratio {expense_ratio} looks like percentage, converting to decimal")
    expense_ratio = expense_ratio / 100  # Convert 20.0 → 0.20

# Sanity check
if expense_ratio > 5.0:  # 500% expense ratio is impossible
    logger.error(f"Unrealistic expense ratio: {expense_ratio}")
    raise ValueError(f"Invalid expense ratio: {expense_ratio}")
```

## Testing

### Test Case 1: Basis Points Format
```python
data = {
    "expense_ratio": 0.0020,  # 20 basis points = 0.20%
    "tracking_error": 0.0030,  # 30 basis points = 0.30%
}
# Expected: fundamental_score ≈ 0.84 (excellent!)
```

### Test Case 2: Decimal Format
```python
data = {
    "expense_ratio": 0.20,  # 20% as decimal
    "tracking_error": 0.30,  # 30% as decimal
}
# Expected: fundamental_score ≈ 0.72 (good)
```

### Test Case 3: Percentage Format
```python
data = {
    "expense_ratio": 20.0,  # 20% as percentage
    "tracking_error": 30.0,  # 30% as percentage
}
# Expected: fundamental_score ≈ 0.20 (terrible!)
```

## Impact

**HIGH RISK**: This bug causes the system to recommend buying terrible ETFs with high fees and poor tracking.

**User Impact**: Users could lose money by following recommendations for high-cost, poorly-performing ETFs.

**Urgency**: CRITICAL - Must fix before production use.

---

**Status**: 🔍 Investigation in progress
**Date**: 2025-11-01
**Priority**: P0 - CRITICAL
**Assignee**: AI Assistant
