# Critical Fields Validation Implementation

## Problem Statement

**Risk**: Using hardcoded fallback values for missing financial data can lead to incorrect investment recommendations that risk real money.

**Previous Behavior**:
1. API fails to return critical data (e.g., `roe`, `debt_to_equity`)
2. System silently uses hardcoded fallback (e.g., `0.0`, `1.0`)
3. Scoring continues with **fake data**
4. User gets recommendation based on **assumptions, not reality**
5. **Money at risk** from incorrect decisions

## Solution: Fail Fast on Critical Missing Data

### Tiered Approach

We now distinguish between **CRITICAL** and **OPTIONAL** fields:

#### Critical Fields (MUST have real data or analysis fails)

**Stocks**:
- `current_price` - Cannot analyze without price
- `roe` - Core fundamental metric
- `debt_to_equity` - Core risk metric
- `revenue_growth` - Core growth metric
- `volatility` - Core risk metric
- `beta` - Core risk metric

**ETFs**:
- `current_price` - Cannot analyze without price
- `expense_ratio` - Core cost metric
- `tracking_error` - Core performance metric
- `aum` - Core liquidity metric
- `volatility` - Core risk metric

**Crypto**:
- `current_price` - Cannot analyze without price
- `market_cap` - Core size metric
- `volume_24h` - Core liquidity metric
- `volatility` - Core risk metric
- `age_years` - Core maturity metric

#### Optional Fields (Can use safe defaults)

**All Asset Classes**:
- `rsi` - Technical indicator (default: 50.0 neutral)
- `macd` - Technical indicator (default: 0.0 neutral)
- `profit_margin` - Nice to have (default: 0.10 conservative)
- `dividend_yield` - Nice to have (default: 0.0 no dividend)

## Implementation

### New Files

1. **`src/finwiz/config/critical_fields_config.py`**
   - Defines critical vs optional fields per asset class
   - Provides safe defaults for optional fields only
   - Raises `CriticalFieldError` when critical field missing

2. **`tests/unit/scoring/test_critical_fields_validation.py`**
   - 12 comprehensive tests
   - Verifies fail-fast behavior for critical fields
   - Verifies safe defaults for optional fields

### Modified Files

1. **`src/finwiz/scoring/deep_analysis_scorer.py`**
   - `calculate_composite_score()`: Validates critical fields BEFORE scoring
   - `_safe_get_float()`: Checks if field is critical, raises error if missing
   - Error handling: Re-raises `CriticalFieldError` to skip holding

## Behavior Changes

### Before (Dangerous)

```python
# Missing critical field
data = {"asset_class": "stock", "rsi": 55.0}  # No roe, debt_to_equity, etc.

# Silently uses hardcoded fallbacks
result = scorer.calculate_composite_score("AAPL", "stock", data)
# Returns Grade D with score 0.3 based on FAKE DATA
```

### After (Safe)

```python
# Missing critical field
data = {"asset_class": "stock", "rsi": 55.0}  # No roe, debt_to_equity, etc.

# FAILS FAST with clear error
try:
    result = scorer.calculate_composite_score("AAPL", "stock", data)
except CriticalFieldError as e:
    print(f"Cannot analyze {e.ticker}: Missing {e.missing_fields}")
    # Skip this holding - don't make decisions on assumptions
```

## Error Messages

### Critical Field Missing

```
❌ CRITICAL FIELDS MISSING for AAPL: ['roe', 'debt_to_equity']
   Cannot proceed with analysis - would be based on assumptions.
   Recommendation: Check API connectivity and data sources.
```

### Optional Field Missing

```
⚠️ Optional field 'rsi' missing for AAPL, using safe default 50.0
```

## Data Quality Tracking

All defaulted fields are tracked in data quality metrics:

```python
result.data_quality = {
    "field_tracking": {
        "calculated": ["current_price", "roe", "debt_to_equity"],
        "defaulted": ["rsi", "macd"],  # Optional fields with defaults
        "missing": [],  # Would cause CriticalFieldError
    }
}
```

## Data Lineage Tracking

All defaults are tracked in lineage:

```python
lineage.sources = [
    {
        "source_type": "default",
        "source_name": "Safe Default (Optional Field)",
        "field_name": "rsi",
        "raw_value": 50.0,
        "metadata": {"reason": "optional_field_missing", "is_critical": False}
    }
]
```

## API Failure Handling

### Scenario: Yahoo Finance API Down

**Before**: System would use hardcoded fallbacks for ALL fields, producing meaningless analysis.

**After**: System raises `CriticalFieldError` and skips the holding entirely.

```python
# In flow orchestrator
try:
    result = scorer.calculate_composite_score(ticker, asset_class, data)
except CriticalFieldError as e:
    logger.error(f"Skipping {ticker}: {e}")
    # Add to skipped holdings list
    skipped_holdings.append({
        "ticker": ticker,
        "reason": f"Missing critical fields: {e.missing_fields}",
        "recommendation": "Check data sources and retry"
    })
    continue  # Skip to next holding
```

## Benefits

✅ **Safety**: No decisions based on fake data
✅ **Transparency**: Clear errors when data is missing
✅ **Traceability**: All defaults tracked in lineage
✅ **Flexibility**: Optional fields can still use safe defaults
✅ **User Trust**: Users know when analysis is incomplete

## Testing

All 12 tests pass:

```bash
uv run pytest tests/unit/scoring/test_critical_fields_validation.py -v
# 12 passed in 11.77s
```

### Test Coverage

- ✅ Success with all critical fields present
- ✅ Failure when single critical field missing
- ✅ Failure when multiple critical fields missing
- ✅ Safe defaults for optional fields
- ✅ Asset-class specific validation (stock, ETF, crypto)
- ✅ Data quality tracking for defaulted fields
- ✅ Configuration validation

## Migration Notes

### For Existing Code

No changes required for code that provides complete data. Code that was relying on silent fallbacks will now raise `CriticalFieldError`.

### For API Integration

Ensure all critical fields are fetched from APIs. If API is down or data unavailable:

1. **Option 1**: Skip the holding (recommended)
2. **Option 2**: Use cached data if available
3. **Option 3**: Notify user and request manual review

### For Testing

Mock data must include all critical fields for the asset class being tested.

## Configuration

Critical fields can be customized in `src/finwiz/config/critical_fields_config.py`:

```python
CRITICAL_FIELDS = {
    "stock": ["current_price", "roe", "debt_to_equity", ...],
    "etf": ["current_price", "expense_ratio", ...],
    "crypto": ["current_price", "market_cap", ...],
}
```

## Monitoring

Track critical field errors in logs:

```bash
grep "CRITICAL FIELDS MISSING" logs/finwiz.log
```

Monitor data quality metrics:

```python
if result.data_quality["quality_level"] == "low":
    alert("Low data quality detected")
```

## Next Steps

1. **Flow Integration**: Update flow orchestrator to handle `CriticalFieldError`
2. **User Notifications**: Alert users when holdings are skipped
3. **Retry Logic**: Implement retry with exponential backoff for API failures
4. **Caching**: Use cached data as fallback when APIs fail
5. **Monitoring**: Set up alerts for high critical field error rates

---

**Version**: 1.0  
**Created**: 2025-11-01  
**Status**: Implemented and Tested  
**Impact**: HIGH - Prevents financial decisions based on fake data
