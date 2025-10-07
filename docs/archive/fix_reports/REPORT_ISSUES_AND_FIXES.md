# Report Generation Issues and Required Fixes

**Date**: 2025-01-07  
**Status**: 🚨 Critical Issues Identified

## 🚨 Critical Issues in Generated Report

### 1. **Fake/Example URLs** ❌

**Problem**:
```html
<a href="https://news.example.com/apple-earnings-2025">
<a href="https://news.example.com/msft-cloud-2025">
<a href="https://news.example.com/btc-etf-inflows-2025">
```

**Root Cause**: LLM is hallucinating news URLs when real sentiment data is not available.

**Fix Required**:
- Ensure `StandardizedSentimentTool` provides real URLs from actual news sources
- Add validation to reject URLs containing "example.com"
- If no real URLs available, show "Source: [Provider Name] - URL not available"

### 2. **Broken SEC Links** ❌

**Problem**:
```
https://www.sec.gov/ix?doc=/Archives/edgar/data/0000320193/000032019324000070/aapl-20230930.htm
```
Returns 404 or is malformed.

**Root Cause**: SEC URLs may be outdated or incorrectly formatted.

**Fix Required**:
- Validate SEC URLs before including in report
- Use SEC EDGAR API to get current filing URLs
- Format: `https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=[CIK]&type=10-K`
- Or use direct filing URLs from SEC API responses

### 3. **Zero A+ Opportunities** ❌

**Problem**:
```
a_plus_opportunities.total_opportunities_found = 0
```

**Root Cause**: Either:
- A+ discovery crew not running
- Discovery results not being passed to report crew
- Discovery crew finding no opportunities (unlikely)

**Fix Required**:
- Verify A+ discovery crew is running: `--discovery` flag
- Check `output/discovery/` for discovery results
- Ensure `CrewDataAccessor.get_aplus_opportunities()` is working
- Add logging to track discovery data flow

### 4. **Incomplete Portfolio Review** ❌

**Problem**: Report only shows 7 holdings (AAPL, MSFT, AMZN, NVDA, META, TSLA, GOOGL) but portfolio likely has more (ETFs, crypto).

**Root Cause**:
- Portfolio review JSON at `output/portfolio/portfolio_review.json` may be incomplete
- ETFs and crypto not being included in portfolio review
- Filtering logic may be excluding valid holdings

**Fix Required**:
- Check `data/etf.csv` and `data/stock.csv` for all holdings
- Verify portfolio review crew processes ALL holdings
- Check filtering logic in report generation
- Ensure crypto holdings (BTC, ETH) are included if present

### 5. **Missing/Incomplete Backtesting Data** ❌

**Problem**:
```
Rendement Annualisé: Données non disponibles
Sharpe: Données non disponibles
Taux de Réussite: Données non disponibles
```

**Root Cause**:
- Backtesting data not being extracted from validation results
- `BacktestingDataExtractor` not being used
- Discovery crew not running backtests
- Data not being passed through integration layer

**Fix Required**:
- Ensure discovery crew runs backtests for all candidates
- Use `BacktestingDataExtractor.extract_backtesting_metrics()`
- Populate `PerformanceMetricsAggregator` with real data
- Pass backtesting data through `CrewDataAccessor.get_backtesting_metrics()`

### 6. **Hallucination Despite Anti-Hallucination Rules** ❌

**Problem**: Task configuration has extensive anti-hallucination rules, but LLM is still inventing data.

**Root Cause**:
- LLM filling gaps when real data is missing
- No validation layer to catch hallucinations
- No enforcement of "use only validated data" rules

**Fix Required**:
- Add post-generation validation to check for:
  - URLs containing "example.com"
  - Tickers not in validated list
  - Dates in the future
  - Suspiciously round numbers
- Implement strict schema validation
- Add "data unavailable" placeholders instead of fake data

## 🔧 Required Fixes by Component

### Fix 1: Sentiment Data Integration

**File**: `src/finwiz/tools/enhanced_sentiment_tool.py`

**Action**:
- Ensure `StandardizedSentimentTool` returns real URLs
- Add URL validation (reject example.com)
- Include publication dates
- Return empty list if no real data available

**Validation**:
```python
def validate_sentiment_url(url: str) -> bool:
    """Validate sentiment URL is real."""
    if "example.com" in url:
        return False
    if not url.startswith("http"):
        return False
    return True
```

### Fix 2: SEC Filing Integration

**File**: `src/finwiz/tools/enhanced_sec_analysis_tool.py`

**Action**:
- Validate SEC URLs before returning
- Use SEC EDGAR API for current URLs
- Test URLs before including in report
- Provide fallback to company CIK page if direct filing unavailable

**Example**:
```python
def get_sec_filing_url(ticker: str, filing_type: str = "10-K") -> str:
    """Get valid SEC filing URL."""
    cik = get_cik_for_ticker(ticker)
    return f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type={filing_type}"
```

### Fix 3: A+ Discovery Integration

**File**: `src/finwiz/integration/data_accessor.py`

**Action**:
- Add logging to track A+ discovery data
- Verify `get_aplus_opportunities()` returns data
- Check discovery crew output files exist
- Add fallback message if no opportunities found

**Logging**:
```python
logger.info(f"A+ opportunities found: {len(opportunities)}")
if len(opportunities) == 0:
    logger.warning("No A+ opportunities found - discovery may not have run")
```

### Fix 4: Complete Portfolio Review

**File**: `src/finwiz/orchestrators/portfolio_review.py`

**Action**:
- Ensure ALL holdings from CSV files are processed
- Include ETFs, stocks, AND crypto
- Don't filter out any valid holdings
- Log each holding being processed

**Verification**:
```python
# Read all holdings
stock_holdings = read_csv("data/stock.csv")
etf_holdings = read_csv("data/etf.csv")
crypto_holdings = read_csv("data/crypto.csv")  # If exists

total_holdings = len(stock_holdings) + len(etf_holdings) + len(crypto_holdings)
logger.info(f"Processing {total_holdings} total holdings")
```

### Fix 5: Backtesting Data Extraction

**File**: `src/finwiz/integration/backtesting_extractor.py`

**Action**:
- Extract ALL backtesting metrics from validation results
- Don't return "Données non disponibles" - return actual data or None
- Populate Sharpe, Sortino, Calmar ratios
- Include annualized returns and win rates

**Required Data**:
```python
{
    "annualized_return": 0.15,  # 15%
    "sharpe_ratio": 1.8,
    "sortino_ratio": 2.1,
    "calmar_ratio": 1.5,
    "max_drawdown": -0.25,  # -25%
    "win_rate": 0.58,  # 58%
    "total_trades": 120
}
```

### Fix 6: Post-Generation Validation

**New File**: `src/finwiz/validation/report_validator.py`

**Action**:
- Create validator to check generated HTML
- Reject reports with hallucinations
- Validate all URLs are real
- Verify all tickers are in validated list
- Check dates are not in future

**Implementation**:
```python
class ReportValidator:
    def validate_report(self, html_content: str, validated_tickers: list[str]) -> ValidationResult:
        """Validate generated report for hallucinations."""
        issues = []
        
        # Check for example URLs
        if "example.com" in html_content:
            issues.append("Found example.com URLs - hallucination detected")
        
        # Check for invalid tickers
        tickers_in_report = extract_tickers(html_content)
        invalid_tickers = [t for t in tickers_in_report if t not in validated_tickers]
        if invalid_tickers:
            issues.append(f"Invalid tickers found: {invalid_tickers}")
        
        # Check for future dates
        dates_in_report = extract_dates(html_content)
        future_dates = [d for d in dates_in_report if d > datetime.now()]
        if future_dates:
            issues.append(f"Future dates found: {future_dates}")
        
        return ValidationResult(is_valid=len(issues) == 0, issues=issues)
```

## 🎯 Implementation Priority

### Priority 1 (Critical - Fix Immediately)
1. ✅ Add post-generation validation to catch hallucinations
2. ✅ Fix sentiment URLs (no example.com)
3. ✅ Fix SEC URLs (validate before including)
4. ✅ Complete portfolio review (all holdings)

### Priority 2 (High - Fix Soon)
5. ✅ A+ discovery integration (ensure data flows)
6. ✅ Backtesting data extraction (complete metrics)

### Priority 3 (Medium - Improve)
7. ⚠️ Add data freshness checks
8. ⚠️ Improve error messages when data missing
9. ⚠️ Add retry logic for failed data fetches

## 📋 Testing Checklist

After fixes, verify:

- [ ] No URLs containing "example.com"
- [ ] All SEC URLs return 200 status
- [ ] A+ opportunities > 0 (if discovery ran)
- [ ] Portfolio review shows ALL holdings from CSV
- [ ] Backtesting data complete (no "non disponibles")
- [ ] All tickers in report are in validated list
- [ ] No dates in the future
- [ ] All sentiment sources have real URLs
- [ ] Data freshness warnings are accurate

## 🔍 Debugging Commands

```bash
# Check if discovery ran
ls -la output/discovery/

# Check portfolio review output
cat output/portfolio/portfolio_review.json | jq '.holdings | length'

# Check validated tickers
cat output/validation/validated_tickers.json | jq '.validated_tickers | length'

# Check sentiment data
cat output/sentiment/sentiment_analysis.json | jq '.articles[0]'

# Check backtesting data
cat output/discovery/validation_results.json | jq '.[] | select(.backtesting_results)'
```

## 📝 Next Steps

1. Implement post-generation validation (Priority 1)
2. Fix sentiment and SEC URL generation (Priority 1)
3. Verify portfolio review completeness (Priority 1)
4. Test A+ discovery integration (Priority 2)
5. Complete backtesting data extraction (Priority 2)
6. Run full end-to-end test with validation
7. Document validation process

---

**Status**: Issues documented, fixes required  
**Impact**: High - Report contains hallucinated data  
**Urgency**: Critical - Fix before next report generation
