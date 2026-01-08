# SEC.gov 403 Forbidden Error Fix

## Problem

The Enhanced SEC Analysis Tool was failing with 403 Forbidden errors when trying to access SEC.gov:

```
Error: Enhanced SEC analysis failed for AAPL: 403 Client Error: Forbidden for url: 
https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000320193&type=10-K&dateb=&owner=exclude&count=100
```

## Root Cause

SEC.gov has strict requirements for User-Agent headers. The tool was using a browser User-Agent string:

```python
"User-Agent": (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
```

However, SEC.gov requires a proper User-Agent with:
1. Application name and version
2. Contact information (email)

See: https://www.sec.gov/os/accessing-edgar-data

## Solution

Updated the User-Agent in `_download_html()` method to comply with SEC.gov requirements:

```python
"User-Agent": "FinWiz/1.0 (contact@finwiz.com)"
```

This format:
- Identifies the application: "FinWiz/1.0"
- Provides contact information: "(contact@finwiz.com)"
- Complies with SEC.gov's fair access policy

## Files Modified

- `src/finwiz/tools/enhanced_sec_tool.py` - Updated User-Agent in `_download_html()` method

## Verification

The SEC filing URL generator (`sec_filing_url_generator.py`) already had the correct User-Agent format:

```python
"User-Agent": "FinWiz Financial Analysis Tool contact@finwiz.com"
```

So only the enhanced SEC tool needed updating.

## Expected Behavior

After this fix:
- SEC.gov requests should succeed with 200 OK
- 10-K/10-Q filings can be downloaded and analyzed
- Risk assessment tasks can proceed normally

## Testing

Run the stock crew again and verify:
- No 403 Forbidden errors from SEC.gov
- SEC filing analysis completes successfully
- Risk assessment task completes

---

**Date**: 2025-01-10
**Status**: Fixed
**Reference**: https://www.sec.gov/os/accessing-edgar-data
