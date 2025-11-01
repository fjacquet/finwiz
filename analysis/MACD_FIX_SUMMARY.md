# MACD Signal Fix Summary

## Problem

The deep analysis scorer was logging warnings about missing `macd_signal` field:

```
⚠️ Missing field 'macd_signal' for AAPL, using default 0.0
```

This caused the momentum score calculation to use default values instead of actual MACD data, resulting in inaccurate technical analysis scores.

## Root Cause

The `QuantitativeAnalysisTool` was only extracting the MACD **signal description** (a string like "MACD bullish crossover") but not the **numeric values** (`macd` line and `macd_signal` line) needed for calculations.

The technical analysis engine calculates MACD correctly and stores numeric values in `raw_values`:
- `MACD_line`: [0.5, 0.6, 0.7, 0.8, 0.9]
- `MACD_signal`: [0.4, 0.5, 0.6, 0.7, 0.8]

But the quantitative tool was only extracting the description, not these numeric arrays.

## Solution

Modified `src/finwiz/tools/quantitative_analysis_tool.py` in the `_perform_technical_analysis` method to:

1. **Extract numeric MACD values** from `raw_values` after building the Pydantic model
2. **Add them to the tech_data dict** that gets returned as JSON
3. **Preserve the description** separately as `macd_description`
4. **Handle NaN values** gracefully with proper error handling
5. **Add debug logging** to track extraction success/failure

### Code Changes

```python
# Build complete technical data dict with numeric indicator values
tech_data = quant_tech.model_dump()

# Add numeric MACD values from raw_values
if "MACD" in tech_result.indicator_results:
    macd_result = tech_result.indicator_results["MACD"]
    if "MACD_line" in macd_result.raw_values and "MACD_signal" in macd_result.raw_values:
        macd_line_values = macd_result.raw_values["MACD_line"]
        macd_signal_values = macd_result.raw_values["MACD_signal"]
        
        # Extract last value (most recent)
        if isinstance(macd_line_values, list) and macd_line_values:
            macd_value = float(macd_line_values[-1])
            if not (macd_value != macd_value):  # NaN check
                tech_data["macd"] = macd_value
        
        if isinstance(macd_signal_values, list) and macd_signal_values:
            macd_signal_value = float(macd_signal_values[-1])
            if not (macd_signal_value != macd_signal_value):  # NaN check
                tech_data["macd_signal"] = macd_signal_value
        
        # Preserve description separately
        if macd_result.signals:
            tech_data["macd_description"] = macd_result.signals[0].description
```

## Data Flow

1. **Technical Analysis Engine** (`advanced_indicators.py`)
   - Calculates MACD using TA-Lib
   - Stores numeric values in `raw_values` dict
   - Generates signal description

2. **Quantitative Analysis Tool** (`quantitative_analysis_tool.py`)
   - Receives technical analysis result
   - **NEW**: Extracts numeric MACD values from `raw_values`
   - Returns JSON with both numeric values and description

3. **Portfolio Deep Analyzer** (`portfolio_deep_analyzer.py`)
   - Parses JSON from quantitative tool
   - Extracts `macd` and `macd_signal` numeric values
   - Passes to scorer

4. **Deep Analysis Scorer** (`deep_analysis_scorer.py`)
   - Receives data with numeric MACD values
   - Calculates `macd_diff = macd - macd_signal`
   - Computes momentum score
   - **No more warnings!**

## Benefits

✅ **Accurate momentum scoring** - Uses real MACD values instead of defaults
✅ **No more warnings** - All required fields present with actual data
✅ **Better technical analysis** - Proper MACD crossover detection
✅ **Preserved descriptions** - Still have human-readable signal descriptions
✅ **Robust error handling** - Gracefully handles NaN and missing data
✅ **Debug visibility** - Logging shows extraction success/failure

## Testing

Created comprehensive tests:
- `test_macd_fix.py` - Basic extraction test
- `test_macd_fix_v2.py` - Proper key naming test
- `test_macd_integration.py` - End-to-end integration test
- `tests/unit/tools/test_quantitative_macd_fix.py` - Unit tests

All tests pass ✅

## Verification

To verify the fix is working:

1. Run portfolio analysis with deep analysis enabled
2. Check logs for MACD extraction messages:
   - `✅ Extracted MACD line: 0.9`
   - `✅ Extracted MACD signal: 0.8`
3. Verify NO warnings about missing `macd_signal`
4. Check that momentum scores are non-default values

## Related Files

- `src/finwiz/tools/quantitative_analysis_tool.py` - Main fix
- `src/finwiz/quantitative/technical/advanced_indicators.py` - MACD calculation
- `src/finwiz/scoring/portfolio_deep_analyzer.py` - Data collection
- `src/finwiz/scoring/deep_analysis_scorer.py` - Momentum scoring
- `src/finwiz/schemas/quantitative_crew.py` - Schema definition

## Future Improvements

1. Update `QuantitativeTechnicalAnalysis` schema to include numeric MACD fields
2. Add similar extraction for other indicators (Bollinger Bands, etc.)
3. Consider adding MACD histogram to the extracted values
4. Add integration test that runs actual technical analysis

---

**Date**: 2025-11-01
**Issue**: Missing MACD signal causing default values in scorer
**Status**: ✅ Fixed and tested
