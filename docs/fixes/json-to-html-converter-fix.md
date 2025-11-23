# JSON to HTML Converter Fix

**Date**: 2025-11-23  
**Issue**: Failed conversions for deep_analysis_stock_output JSON files  
**Status**: ✅ Fixed

## Problem

The JSON to HTML converter was failing to convert 31 deep analysis output files with the error:

```
'processing_time_seconds' is undefined
```

The template `enriched_analysis_report.html` expected fields that didn't exist in the JSON output structure.

## Root Cause

The deep analysis JSON files have a different structure than expected:

```json
{
  "raw_output": "ticker='AAPL' composite_score=0.85 ...",
  "metadata": {
    "crew_name": "deep_analysis_stock",
    "storage_timestamp": "2025-11-23T21:11:39.133361"
  }
}
```

The template expected direct fields like `processing_time_seconds`, `fundamental_metrics`, etc., but these were embedded in the `raw_output` string.

## Solution

Enhanced the `_prepare_context` method in `JsonToHtmlConverter` to:

1. **Detect deep_analysis files** with `raw_output` structure
2. **Parse the raw_output string** to extract key=value pairs and dict structures
3. **Provide default values** for all missing template fields
4. **Map parsed data** to expected template field names

### Key Changes

1. Added `_parse_raw_output()` method to extract fields from the string representation
2. Added comprehensive default values for missing template fields:
   - `processing_time_seconds`: 0.0
   - `llm_cost_dollars`: 0.0
   - `fundamental_metrics`: Extracted from `fundamental_details`
   - `technical_indicators`: Extracted from `technical_details`
   - `risk_metrics`: Extracted from `risk_details`
   - Empty structures for missing sections (SEC insights, scenarios, etc.)

## Results

- **Before**: 31 failed conversions with warnings
- **After**: 36 successful conversions, only 1 unrelated failure
- **Test Coverage**: 6 new unit tests covering the fix

## Files Modified

- `src/finwiz/utils/json_to_html_converter.py`
  - Enhanced `_prepare_context()` method
  - Added `_parse_raw_output()` helper method

## Tests Added

- `tests/unit/utils/test_json_to_html_converter.py`
  - Test conversion without processing_time field
  - Test raw_output parsing
  - Test default value provision
  - Test malformed JSON handling
  - Test empty JSON handling
  - Test asset class inference

## Verification

```bash
# Run converter
python -c "from src.finwiz.utils.json_to_html_converter import convert_all_json_to_html; convert_all_json_to_html()"

# Run tests
python -m pytest tests/unit/utils/test_json_to_html_converter.py -v
```

## Impact

- ✅ All deep analysis JSON files now convert to HTML successfully
- ✅ No more warning messages in logs
- ✅ HTML reports are generated with default values for missing fields
- ✅ Backward compatible with existing JSON structures

## Future Improvements

Consider standardizing the deep analysis output format to match the template expectations directly, eliminating the need for parsing and default values.
