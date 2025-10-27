---
title: "Crypto Schema Fix"
description: "Archived documentation for Crypto Schema Fix"
category: "archive"
tags:
  - "archive"
date: "2025-10-26"
source: "archive/fix_reports/CRYPTO_SCHEMA_FIX.md"
---

# Crypto Investment Strategy Schema Fix 🚀

[TOC]

## Problem Summary

The crypto investment strategy task was failing with Pydantic validation errors after 3 retry attempts:

### Validation Errors Encountered:

1. **Symbol too long**: `CRYPTO_TOP10_PORTFOLIO` (23 chars) exceeded 10 character limit
2. **Invalid URL format**: `https://polygon.technology/` was rejected by URL validator
3. **Max drawdown sign**: Value was positive (0.62) but schema required negative (≤ 0.0)

## Root Causes

### 1. Symbol Length Constraint
**Issue**: Schema limited `symbol` field to 10 characters, but LLM was generating portfolio identifiers like `CRYPTO_TOP10_PORTFOLIO` (23 chars).

**Location**: Multiple fields in `src/finwiz/schemas/crypto.py`:
- `CryptoThesis.symbol`
- `CryptoQuantitativeMetrics.symbol`
- `CryptoInvestmentStrategy.symbol`

**Why it happened**: The schema was designed for individual crypto symbols (BTC, ETH) but not portfolio-level strategies.

### 2. URL Validation Regex
**Issue**: The regex pattern was too strict and rejected valid URLs with trailing slashes.

**Problem URLs**:
- `https://polygon.technology/` ❌ (rejected)
- `https://cardano.org/` ❌ (rejected)

**Regex issue**: Pattern required `\S+` (non-whitespace) after the path separator, which excluded URLs ending with `/`.

### 3. Max Drawdown Sign Convention
**Issue**: LLM was providing positive drawdown values (0.62 for 62% drawdown) but schema expected negative values (≤ 0.0).

**Why it happened**: Financial convention is ambiguous - some systems use positive percentages, others use negative.

## Solutions Applied

### ✅ Fix 1: Increased Symbol Length Limit

**Changed**: `max_length=10` → `max_length=30`

**Files modified**:
```pythonthon
# src/finwiz/schemas/crypto.py

# CryptoThesis
symbol: str = Field(
    min_length=2,
    max_length=30,  # Was 10
    description="Crypto symbol or portfolio identifier, e.g., BTC or CRYPTO_PORTFOLIO"
)

# CryptoQuantitativeMetrics
symbol: str = Field(
    min_length=2,
    max_length=30,  # Was 10
    description="Crypto symbol or portfolio identifier"
)

# CryptoInvestmentStrategy
symbol: str = Field(
    min_length=2,
    max_length=30,  # Was 10
    description="Crypto symbol or portfolio identifier"
)
```text
**Impact**: Now supports both individual crypto symbols (BTC, ETH) and portfolio identifiers (TOP10PORT, CRYPTO_PORTFOLIO).

### ✅ Fix 2: Relaxed URL Validation Regex

**Changed**: Made path component optional and allowed trailing slashes

**Before**:
```pythonthon
r"(?:/?|[/?]\S+)$"  # Required non-whitespace after /
```text
**After**:
```pythonthon
r"(?:/?|[/?]\S*)?$"  # Optional path, allows trailing /
```text
**Full regex changes**:
```pythonthon
url_pattern = re.compile(
    r"^https?://"
    r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,}\.?|"  # Changed: [A-Z]{2,6} → [A-Z]{2,}
    r"localhost|"
    r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
    r"(?::\d+)?"
    r"(?:/?|[/?]\S*)?$",  # Changed: \S+ → \S* and made optional with ?
    re.IGNORECASE,
)
```text
**Now accepts**:
- ✅ `https://polygon.technology/`
- ✅ `https://cardano.org/`
- ✅ `https://ethereum.org/en/`
- ✅ `https://glassnode.com/`

### ✅ Fix 3: Enhanced Max Drawdown Documentation

**Changed**: Added clear description that drawdown must be negative

**Before**:
```pythonthon
max_drawdown: Optional[float] = Field(None, le=0.0, description="Maximum drawdown percentage")
```text
**After**:
```pythonthon
max_drawdown: Optional[float] = Field(
    None,
    le=0.0,
    description="Maximum drawdown as negative percentage (e.g., -0.62 for 62% drawdown)"
)
```text
### ✅ Fix 4: Updated Task Configuration

**File**: `src/finwiz/crews/crypto_crew/config/tasks.yaml`

**Added**: Comprehensive schema constraints documentation in the task description:

```yaml
CRITICAL SCHEMA CONSTRAINTS:
- symbol: Maximum 30 characters (e.g., "BTC" or "TOP10PORT" for portfolios)
- investment_thesis.symbol: Same as above, maximum 30 characters
- investment_thesis.references: MUST be valid URLs starting with http:// or https://
  * URLs MUST end with a trailing slash if no path (e.g., "https://polygon.technology/")
  * OR have a valid path (e.g., "https://ethereum.org/en/")
  * Examples of VALID URLs:
    - "https://glassnode.com/"
    - "https://ethereum.org/en/"
    - "https://polygon.technology/"
    - "https://cardano.org/"
- quantitative_metrics.max_drawdown: MUST be NEGATIVE or zero (e.g., -0.62 for 62% drawdown, NOT 0.62)
- quantitative_metrics.symbol: Same as symbol field, maximum 30 characters
```text
## Testing

Run diagnostics to verify no linting errors:
```bash
uv run ruff check src/finwiz/schemas/crypto.py
```text
Result: ✅ No diagnostics found

## Expected Behavior After Fix

The LLM should now be able to:

1. ✅ Use portfolio identifiers like `TOP10PORT` or `CRYPTO_PORTFOLIO` (up to 30 chars)
2. ✅ Include valid reference URLs with trailing slashes
3. ✅ Provide negative max drawdown values (-0.62 instead of 0.62)

## Files Modified

1. `src/finwiz/schemas/crypto.py` - Schema definitions
2. `src/finwiz/crews/crypto_crew/config/tasks.yaml` - Task guidance
3. `CRYPTO_SCHEMA_FIX.md` - This documentation

## Next Steps

1. Re-run the crypto crew analysis:
   ```bash
   uv run python src/finwiz/main.py --crypto
   ```

2. Monitor the investment_strategy_task for successful completion

3. Verify the output JSON matches the schema:
   ```bash
   cat output/crypto/crypto_investment_strategy.json | jq .
   ```

## Prevention

To prevent similar issues in the future:

1. **Schema Design**: Consider use cases beyond individual assets (portfolios, baskets, indices)
2. **URL Validation**: Use more permissive regex or standard URL parsing libraries
3. **Clear Documentation**: Add examples in field descriptions showing expected formats
4. **Task Guidance**: Include schema constraints directly in task descriptions for LLM guidance
5. **Validation Testing**: Test schemas with realistic LLM-generated data before deployment

---

**Status**: ✅ Fixed and ready for testing
**Date**: 2025-10-08
**Impact**: High - Unblocks crypto investment strategy generation
