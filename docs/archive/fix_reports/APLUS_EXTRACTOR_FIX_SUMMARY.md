# A+ Extractor Fix Summary

## Issue
The `aplus_extractor.py` was failing with the error:
```
AttributeError: 'NoneType' object has no attribute 'get'
```

This occurred at line 130 when trying to access `risk_assessment.get("score", 5.0)`.

## Root Cause
The `InvestmentCandidate` schema defines `risk_assessment` as `Optional[RiskAssessmentStandardized]`, meaning it can be `None`. The code was calling `.get()` on a potentially `None` value without checking first.

## Fix Applied
Changed the code to use the `or` operator to provide a default empty dict when `risk_assessment` is `None`:

### Before (Line 128-130):
```python
# Extract risk assessment
risk_assessment = candidate.get("risk_assessment", {})
risk_score = risk_assessment.get("score", 5.0)
```

### After (Line 128-130):
```python
# Extract risk assessment
risk_assessment = candidate.get("risk_assessment") or {}
risk_score = risk_assessment.get("score", 5.0)
```

This same fix was applied in two locations:
1. `_extract_stock_opportunities()` - line 128-130
2. `_extract_crypto_opportunities()` - line 253-255

## Test Updates
The test file `tests/unit/tools/test_aplus_extractor.py` was also updated to provide proper JSON data instead of markdown content, matching the actual file format used by the discovery crew.

## Verification
All 18 tests in `test_aplus_extractor.py` now pass successfully:
```bash
uv run pytest tests/unit/tools/test_aplus_extractor.py -v --no-cov
# Result: 18 passed in 0.32s
```

## Files Modified
1. `src/finwiz/integration/aplus_extractor.py` - Fixed null handling for risk_assessment
2. `tests/unit/tools/test_aplus_extractor.py` - Updated test fixtures to use JSON format

## Impact
- No more `AttributeError` when `risk_assessment` is `None`
- Graceful handling of missing risk assessment data
- All tests passing
- Code is more robust and defensive
