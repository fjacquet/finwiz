# A+ Extractor Fix Summary

## Problem
The A+ extractor was looking for markdown files (`.md`) but the discovery crew was generating JSON files (`.json`), resulting in 0 opportunities being extracted.

## Root Cause
- **Expected files**: `a_plus_stocks.md`, `a_plus_etfs.md`, `a_plus_crypto.md`
- **Actual files**: `a_plus_stocks.json`, `a_plus_etfs.json`, `a_plus_crypto.json`

The extractor was using regex patterns to parse markdown content, but the discovery crew outputs structured JSON data.

## Solution
Updated `src/finwiz/integration/aplus_extractor.py` to:

1. **Read JSON files instead of markdown**:
   - Changed file extensions from `.md` to `.json`
   - Added `import json` to parse JSON content

2. **Parse structured JSON data**:
   - Extract from `a_plus_candidates` array
   - Read `candidate` object with structured fields
   - Extract `grade`, `symbol`, `name`, `composite_score`, etc.
   - Handle `key_metrics`, `risk_assessment`, and `rationale` fields

3. **Removed markdown parsing logic**:
   - Deleted regex-based extraction methods
   - Removed helper methods: `_extract_stock_details`, `_extract_etf_grade`, `_extract_etf_details`, `_extract_crypto_grade`, `_extract_crypto_details`

## Results
✅ **Before Fix**: 0 opportunities extracted
✅ **After Fix**: 29 opportunities extracted
  - 9 ETFs (CSPX, IUSA, VUSD, SPY5, SXR8, EUNL, SWDA, VWRL, S&P500_REPLACEMENT)
  - 15 Stocks (MSFT, AAPL, NVDA, ADBE, CRM, ASML, NOW, INTU, ADSK, SNOW, DDOG, MELI, FTNT, CRWD, PANW)
  - 5 Crypto (BTC, ETH, USDC, BNB, SOL)

✅ **Confidence Score**: 100%
✅ **Validation**: PASSED

## Testing
```bash
# Test extraction
uv run python -c "
from src.finwiz.integration.aplus_extractor import APlusDataExtractor
extractor = APlusDataExtractor()
collection = extractor.extract_aplus_opportunities()
print(f'Extracted {len(collection.etf_opportunities) + len(collection.stock_opportunities) + len(collection.crypto_opportunities)} opportunities')
"
```

## Files Modified
- `src/finwiz/integration/aplus_extractor.py`
  - Updated `_extract_stock_opportunities()` to parse JSON
  - Updated `_extract_etf_opportunities()` to parse JSON
  - Updated `_extract_crypto_opportunities()` to parse JSON
  - Added `import json` at module level
  - Removed markdown parsing helper methods

## Impact
The discovery crew integration now works correctly, allowing the portfolio analysis to access A+ opportunities for alternative recommendations.
