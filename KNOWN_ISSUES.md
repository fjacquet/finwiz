# Known Issues - Task 5.8 Report Data Flow

## Date: 2025-10-19
## Status: Code Changes Made, Testing Required

---

## Executive Summary

**Critical Issue**: All individual crews (stock, ETF, crypto, discovery) execute successfully and generate proper data, but the **report crew receives NONE of this data**. This is a fundamental data flow failure between the Flow orchestrator and the report crew.

**Root Cause**: Data is being written to disk by crews, but the report crew is either:
1. Not reading from the correct location
2. Not receiving the data in its inputs
3. Reading stale/cached data instead of fresh data

**Impact**: 100% of report content shows "NOT AVAILABLE" despite all data existing.

---

## Issues Breakdown

### ❌ Issue 1: SEC URLs Don't Work

**Symptom**:
```
https://www.sec.gov/ix?doc=/Archives/edgar/data/0000320193/000032019324000070/aapl-20230930.htm
```
Returns 404 error.

**Code Changes Made**:
- Added `get_direct_filing_url()` method to `SECFilingURLGenerator`
- Added `_validate_and_fix_sec_urls()` method to Flow orchestrator
- Added `sec-edgar-downloader` dependency

**Testing Status**: ❌ NOT TESTED
- Unit tests exist: `tests/unit/tools/test_sec_filing_url_generator.py`
- Need to verify: New `get_direct_filing_url()` method works
- Need to verify: URLs are actually validated in Flow

**Expected Fix**: Should generate working browse URLs or direct document URLs

---

### ❌ Issue 2: Discovery Data Not Detected

**Symptom**:
```
Statut de découverte A+ : la découverte A+ n'a pas été exécutée
État: A+ discovery not run — enable INVESTMENT_DISCOVERY feature flag
```

But discovery files exist:
```
output/discovery/a_plus_stocks.json (33KB)
output/discovery/a_plus_etfs.json (21KB)
output/discovery/a_plus_crypto.json (13KB)
output/discovery/discovery_latest.json (404KB)
```

**Code Changes Made**:
- Changed `APlusOpportunityCollection` schema to store full objects (not just symbols)
- Added `APlusOpportunity` class with full data fields
- Updated `APlusDataExtractor` to return full objects
- Added `_extract_market_context()` and `_extract_backtesting_metrics()` methods

**Testing Status**: ❌ NOT TESTED
- Unit tests exist: `tests/unit/crews/test_report_crew_discovery_integration.py`
- Need to verify: Schema changes don't break existing code
- Need to verify: Data flows from disk → extractor → cache → report crew
- Need to verify: Report crew receives `aplus_opportunities` in inputs

**Expected Fix**: Report should show discovery data with grades, scores, rationale

---

### ❌ Issue 3: Backtesting Data Not Available

**Symptom**:
```
Statut Backtesting : Backtesting data not available - discovery not run
```

**Code Changes Made**:
- Added `backtesting_metrics` field to `APlusOpportunityCollection`
- Added `_extract_backtesting_metrics()` method to extract from discovery files

**Testing Status**: ❌ NOT TESTED
- Unit tests exist: `tests/unit/crews/test_report_crew_backtesting_integration.py`
- Need to verify: Backtesting data is in discovery files
- Need to verify: Extraction method works correctly
- Need to verify: Data is passed to report crew

**Expected Fix**: Report should show backtesting metrics (Sharpe, returns, drawdown)

---

### ❌ Issue 4: Ticker Scores Show Defaults (0.7, 2.0)

**Symptom**:
```
Apple  AAPL  KEEP  0.7  2.0 — Medium
Bitcoin BTC-USD KEEP 0.7 2.0 — Medium
```

All tickers show the same default scores instead of actual analysis results.

**Code Changes Made**: ❌ NONE
- Existing code: `DeepAnalysisDataMerger` should merge deep analysis results
- Existing code: `analyze_and_update_portfolio()` calls the merger

**Testing Status**: ❌ NOT VERIFIED
- Need to check: Is `DEEP_PORTFOLIO_ANALYSIS=true` in .env?
- Need to check: Is deep analysis actually running?
- Need to check: Are results being merged correctly?
- Need to check: Logs for merge verification

**Expected Fix**: Report should show actual scores from deep analysis

---

### ❌ Issue 5: Valid Tickers Dropped

**Symptom**:
```
Positions exclues (non affichées) : 7
Raison : tickers non présents dans la liste validated_tickers_list
```

Only 2 out of 9 tickers are shown (AAPL, BTC-USD).

**Code Changes Made**: ❌ NONE

**Testing Status**: ❌ NOT INVESTIGATED
- Need to check: What's in `validated_tickers_list`?
- Need to check: Why are only 2 tickers validated?
- Need to check: Ticker validation logic in `check_portfolio()`

**Expected Fix**: All valid tickers from portfolio CSV should be included

---

### ❌ Issue 6: Deep Analysis Message Despite Being Enabled

**Symptom**:
```
Activer DEEP_PORTFOLIO_ANALYSIS pour métriques détaillées
```

But `DEEP_PORTFOLIO_ANALYSIS=true` is set in .env.

**Code Changes Made**: ❌ NONE

**Testing Status**: ❌ NOT INVESTIGATED
- Need to check: Is deep analysis actually running?
- Need to check: Are results being used in report?
- Related to Issue 4 (ticker scores)

**Expected Fix**: Report should not suggest enabling what's already enabled

---

### ❌ Issue 7: Data Availability Summary Not Provided

**Symptom**:
```
L'objet inputs.data_availability_summary / inputs.data_availability_summary_formatted 
n'a pas été fourni dans le flux d'entrée
```

**Code Changes Made**:
- Added logging to verify `data_availability_summary` is in state
- Added logging to verify `data_availability_summary_formatted` is in state

**Testing Status**: ❌ NOT TESTED
- Need to verify: Is data in Flow state?
- Need to verify: Is data passed to report crew inputs?
- Need to verify: Report crew can access the data

**Expected Fix**: Report footer should show data availability summary

---

## Existing Unit Tests

### Tests That Should Cover These Issues

1. **SEC URLs**:
   - `tests/unit/tools/test_sec_filing_url_generator.py`
   - `tests/unit/tools/test_enhanced_sec_tool.py`

2. **Discovery Detection**:
   - `tests/unit/crews/test_report_crew_discovery_integration.py`
   - `tests/unit/integration/test_aplus_discovery_accessor.py`

3. **Backtesting**:
   - `tests/unit/crews/test_report_crew_backtesting_integration.py`

4. **Data Availability**:
   - `tests/unit/crews/test_report_crew_availability_tracker.py`

5. **Report Integration**:
   - `tests/integration/core_analysis/test_report_crew_integration.py`
   - `tests/integration/test_report_data_quality.py`

### Test Status: ❓ UNKNOWN

We don't know if these tests:
- Are up to date with recent code changes
- Actually pass
- Cover the real issues we're seeing

---

## Recommended Testing Approach

### Phase 1: Run Existing Tests (5 minutes)

```bash
# Run SEC URL tests
uv run pytest tests/unit/tools/test_sec_filing_url_generator.py -v

# Run discovery integration tests
uv run pytest tests/unit/crews/test_report_crew_discovery_integration.py -v

# Run report integration tests
uv run pytest tests/integration/core_analysis/test_report_crew_integration.py -v
```

### Phase 2: Run Full Flow with Debug Logging (10 minutes)

```bash
# Enable all features
export DEEP_PORTFOLIO_ANALYSIS=true
export INVESTMENT_DISCOVERY=true

# Run flow with full logging
uv run crewai flow kickoff 2>&1 | tee debug_run.log

# Check for our debug markers
grep "✅\|❌\|⚠️" debug_run.log
grep "aplus_opportunities present" debug_run.log
grep "data_availability_summary present" debug_run.log
```

### Phase 3: Inspect Generated Report (2 minutes)

```bash
# Find the report
find . -name "*.html" -mmin -10

# Check for issues
grep "discovery not run" report.html
grep "NOT AVAILABLE" report.html
grep "0.7" report.html  # Default scores
```

### Phase 4: Fix Issues One by One

Based on test results and logs, fix issues in priority order:
1. Discovery data flow (most critical)
2. Data availability summary
3. Ticker validation
4. SEC URLs
5. Backtesting
6. Deep analysis integration

---

## Files Modified (Untested)

1. `src/finwiz/schemas/integration_models.py`
   - Added `APlusOpportunity` class
   - Updated `APlusOpportunityCollection` schema
   - **Risk**: May break existing code that expects strings

2. `src/finwiz/integration/aplus_extractor.py`
   - Returns full objects instead of dicts
   - Added market context and backtesting extraction
   - **Risk**: May fail if discovery files don't have expected structure

3. `src/finwiz/flows/flow_orchestrator.py`
   - Added SEC URL validation
   - Added comprehensive logging
   - **Risk**: Validation may slow down execution

4. `src/finwiz/tools/sec_filing_url_generator.py`
   - Added `get_direct_filing_url()` method
   - **Risk**: May fail if SEC API changes or rate limits

5. `src/finwiz/crews/report_crew/report_crew.py`
   - Changed feature flag messages
   - **Risk**: None (cosmetic change)

6. `pyproject.toml`
   - Added `sec-edgar-downloader` dependency
   - **Risk**: May have version conflicts

---

## Success Criteria (How We'll Know It's Fixed)

### Must Have (Blocking)
- [ ] Discovery data appears in report with full details
- [ ] All valid tickers are included (not dropped)
- [ ] Data availability summary shows in footer

### Should Have (Important)
- [ ] SEC URLs work (browse or direct)
- [ ] Ticker scores show actual analysis (not 0.7/2.0)
- [ ] Backtesting metrics appear (if available)

### Nice to Have (Enhancement)
- [ ] Deep analysis message only shows when actually disabled
- [ ] Market context data appears
- [ ] All unit tests pass

---

## Risk Assessment

**High Risk Changes**:
- Schema changes to `APlusOpportunityCollection` (may break existing code)
- Data extractor returning different types (may cause type errors)

**Medium Risk Changes**:
- SEC URL validation (may slow down or fail)
- New dependency (may have conflicts)

**Low Risk Changes**:
- Logging additions (cosmetic)
- Message updates (cosmetic)

---

## Next Steps

1. **Run existing unit tests** to establish baseline
2. **Run full flow** with debug logging to see actual failures
3. **Fix issues one by one** based on test results
4. **Verify each fix** before moving to next issue
5. **Update this document** with findings

---

## Confidence Level: 40%

**Why Low Confidence**:
- No testing done on any changes
- Schema changes are risky
- Data flow not verified end-to-end
- Multiple issues may be interconnected

**What Would Increase Confidence**:
- Running tests and seeing results
- Verifying data flow with logs
- Testing one fix at a time
- Seeing actual report output

---

## Contact

If you encounter issues not listed here, check:
- `CRITICAL_DATA_FLOW_FIX.md` - Initial problem analysis
- `COMPREHENSIVE_FIX_PLAN.md` - Detailed fix plan
- `FINAL_FIXES_APPLIED.md` - Summary of changes made
- `SEC_DATA_EXTRACTION_FIX.md` - SEC URL fix details
