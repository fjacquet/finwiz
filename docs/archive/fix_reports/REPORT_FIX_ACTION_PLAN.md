# Report Fix Action Plan

**Date**: 2025-01-07  
**Goal**: Fix hallucinations and data issues in financial report generation

## 🎯 Quick Summary

The generated report has **6 critical issues**:
1. ❌ Fake URLs (example.com)
2. ❌ Broken SEC links
3. ❌ Zero A+ opportunities
4. ❌ Incomplete portfolio review
5. ❌ Missing backtesting data
6. ❌ Hallucinations despite anti-hallucination rules

## 🚀 Immediate Actions (Do First)

### Action 1: Add Report Validation
**File**: Create `src/finwiz/validation/report_validator.py`

```python
"""Report validation to catch hallucinations."""

class ReportValidator:
    FORBIDDEN_PATTERNS = [
        "example.com",
        "test.com",
        "sample.com",
        "placeholder",
        "TODO",
        "TBD"
    ]
    
    def validate_html_report(self, html: str, validated_tickers: list[str]) -> dict:
        """Validate report for hallucinations."""
        issues = []
        
        # Check for forbidden patterns
        for pattern in self.FORBIDDEN_PATTERNS:
            if pattern in html.lower():
                issues.append(f"Found forbidden pattern: {pattern}")
        
        # Check tickers
        import re
        tickers_in_report = re.findall(r'\b[A-Z]{2,5}\b', html)
        invalid = [t for t in set(tickers_in_report) if t not in validated_tickers]
        if invalid:
            issues.append(f"Invalid tickers: {invalid}")
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "validated": len(issues) == 0
        }
```

### Action 2: Fix Sentiment URLs
**File**: `src/finwiz/tools/enhanced_sentiment_tool.py`

Add validation before returning URLs:

```python
def _validate_article_url(self, url: str) -> bool:
    """Validate article URL is real."""
    if not url:
        return False
    if "example.com" in url.lower():
        return False
    if not url.startswith(("http://", "https://")):
        return False
    return True

def _filter_valid_articles(self, articles: list) -> list:
    """Filter out articles with invalid URLs."""
    return [a for a in articles if self._validate_article_url(a.get("url", ""))]
```

### Action 3: Fix SEC URLs
**File**: `src/finwiz/tools/enhanced_sec_analysis_tool.py`

Use SEC EDGAR API for current URLs:

```python
def get_valid_sec_url(self, ticker: str, filing_type: str = "10-K") -> str:
    """Get valid SEC filing URL."""
    try:
        # Get CIK from ticker
        cik = self._get_cik(ticker)
        
        # Return browse URL (always works)
        return f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type={filing_type}"
    except Exception as e:
        logger.warning(f"Could not get SEC URL for {ticker}: {e}")
        return None
```

### Action 4: Check Portfolio Data
**Command**:
```bash
# Check what's in portfolio review
cat output/portfolio/portfolio_review.json | jq '.holdings | length'
cat output/portfolio/portfolio_review.json | jq '.holdings[] | .ticker'

# Check CSV files
cat data/stock.csv
cat data/etf.csv
```

**Expected**: Portfolio review should include ALL holdings from CSV files.

### Action 5: Check A+ Discovery
**Command**:
```bash
# Check if discovery ran
ls -la output/discovery/

# Check discovery results
cat output/discovery/aplus_discovery_results.json | jq '.total_opportunities_found'

# Check if discovery crew was called
grep "discovery" logs/finwiz.log
```

**Expected**: Discovery should find opportunities if run with `--discovery` flag.

### Action 6: Check Backtesting Data
**Command**:
```bash
# Check validation results
cat output/discovery/validation_results.json | jq '.[] | select(.backtesting_results) | .backtesting_results'

# Check if backtesting ran
grep "backtesting" logs/finwiz.log
```

**Expected**: Backtesting results should have complete metrics.

## 📋 Verification Steps

After implementing fixes:

### Step 1: Run Report Generation
```bash
uv run python src/finwiz/main.py --report-only
```

### Step 2: Validate Output
```bash
# Check for example.com
grep -i "example.com" output/finwiz_family_financial_plan.html

# Check for invalid tickers
# (manually verify all tickers are in validated list)

# Check A+ opportunities
grep "a_plus_opportunities" output/finwiz_family_financial_plan.html

# Check portfolio holdings count
grep -c "<tr>" output/finwiz_family_financial_plan.html
```

### Step 3: Manual Review
- [ ] Open HTML in browser
- [ ] Click all URLs - verify they work
- [ ] Check SEC links return valid pages
- [ ] Verify all tickers are real
- [ ] Check backtesting data is complete
- [ ] Verify portfolio shows all holdings

## 🔧 Quick Fixes (Can Do Now)

### Fix 1: Add URL Validation to Report Task

Edit `src/finwiz/crews/report_crew/config/tasks.yaml`:

Add to description:
```yaml
CRITICAL URL VALIDATION:
- Every URL must be validated before inclusion
- Reject URLs containing: example.com, test.com, sample.com
- If no real URL available, use: "Source: [Provider] - URL not available"
- SEC URLs must use format: https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=[CIK]
```

### Fix 2: Add Data Availability Checks

Add to report task:
```yaml
DATA AVAILABILITY HANDLING:
- If sentiment URLs not available: Show "Sentiment data: Not available"
- If A+ opportunities = 0: Show "No A+ opportunities found in current analysis"
- If backtesting incomplete: Show "Backtesting data: Partial - [list available metrics]"
- If portfolio incomplete: Show warning "Portfolio data may be incomplete"
```

### Fix 3: Add Logging

Add to report generation:
```python
logger.info(f"Validated tickers: {len(validated_tickers)}")
logger.info(f"Portfolio holdings: {len(portfolio_holdings)}")
logger.info(f"A+ opportunities: {aplus_count}")
logger.info(f"Sentiment articles: {len(sentiment_articles)}")
logger.info(f"Backtesting results: {len(backtesting_results)}")
```

## 📊 Success Criteria

Report is fixed when:
- ✅ Zero URLs containing "example.com"
- ✅ All SEC URLs return 200 status
- ✅ A+ opportunities shown (if discovery ran)
- ✅ Portfolio shows ALL holdings from CSV
- ✅ Backtesting data complete OR clearly marked as unavailable
- ✅ All tickers in validated list
- ✅ No hallucinated data

## 🎯 Timeline

- **Day 1**: Implement validation (Actions 1-3)
- **Day 2**: Fix data integration (Actions 4-6)
- **Day 3**: Test and verify
- **Day 4**: Document and deploy

## 📝 Notes

- The task configuration already has anti-hallucination rules, but they're not being enforced
- Need validation AFTER generation, not just in instructions
- LLM will fill gaps with fake data unless explicitly prevented
- Better to show "Data not available" than fake data

---

**Next Step**: Start with Action 1 (Report Validation) - this will catch issues immediately.
