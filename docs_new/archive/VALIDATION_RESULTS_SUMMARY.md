---
title: "Validation Results Summary"
description: "Archived documentation for Validation Results Summary"
category: "archive"
tags:
  - "archive"
date: "2025-10-26"
source: "archive/fix_reports/VALIDATION_RESULTS_SUMMARY.md"
---

# Report Validation Results Summary

**Date**: 2025-01-07
**Report**: `output/finwiz_family_financial_plan.html`
**Status**: ❌ **FAILED VALIDATION**

[TOC]

## 📊 Validation Statistics

- **Total Checks**: 6
- **Errors**: 14 (1 critical, 13 warnings)
- **Warnings**: 3
- **Tickers Found**: 26
- **URLs Found**: 7

## 🚨 Critical Issues (Must Fix)

### 1. Hallucinated URLs ❌
**Error**: Found forbidden URL pattern: `example.com`

**Locations**:
- `news.example.com/apple-earnings-2025`
- `news.example.com/msft-cloud-2025`
- `news.example.com/btc-etf-inflows-2025`

**Impact**: HIGH - These are fake URLs that don't work

**Fix**:
- Update sentiment tool to use real news URLs
- If no URL available, show "Source: [Provider] - URL not available"
- Already implemented URL validation in `sentiment_sources.py`

### 2. Placeholder Text ❌
**Error**: Found placeholder text: `[à renseigner]`

**Location**: Contacts section

**Impact**: MEDIUM - Incomplete report

**Fix**: Either fill in real contacts or remove the placeholder

## ⚠️ Warnings (Should Fix)

### 3. Unvalidated Tickers (13 warnings)
Most are false positives from the regex:
- `SELL`, `KEEP`, `AI`, `IA`, `US`, `ET`, `MD` - Not actual tickers, just words
- `CVX`, `XOM`, `BRK`, `ASML` - Real tickers but not in validated list
- `WSJ` - News source, not a ticker

**Impact**: LOW - Mostly false positives

**Fix**:
- Improve ticker detection regex to avoid common words
- Add CVX, XOM, BRK.B, ASML to validated tickers if they should be included

### 4. Future Dates (3 warnings)
**Warning**: Report date is `2025-10-31` (in the future)

**Impact**: LOW - Likely intentional for demo/test

**Fix**: Use current date or clearly mark as projection

## ✅ What's Working

- URL detection is working
- Placeholder text detection is working
- Ticker extraction is working (though needs refinement)
- Date validation is working

## 🔧 Fixes Implemented

### ✅ Completed
1. **Created `ReportValidator`** - Comprehensive validation system
2. **Added URL validation to sentiment tool** - Rejects example.com URLs
3. **Created validation script** - Easy to run validation

### 🚧 In Progress
4. **SEC URL validation** - Need to ensure SEC URLs are current
5. **Portfolio completeness check** - Verify all holdings included
6. **A+ discovery integration** - Ensure data flows through

### 📋 To Do
7. **Improve ticker regex** - Reduce false positives
8. **Add post-generation validation** - Run automatically after report generation
9. **Fix placeholder text** - Remove or fill in contacts section
10. **Verify data completeness** - Check backtesting, A+, portfolio data

## 🎯 Priority Actions

### Immediate (Fix Now)
1. ✅ Remove example.com URLs from sentiment data
2. ⚠️ Remove or fill placeholder text `[à renseigner]`
3. ⚠️ Use current date instead of future date

### High Priority (Fix Soon)
4. ⚠️ Verify SEC URLs are working
5. ⚠️ Check portfolio completeness (all holdings)
6. ⚠️ Verify A+ opportunities data

### Medium Priority (Improve)
7. ⚠️ Improve ticker detection to reduce false positives
8. ⚠️ Add automated validation to report generation
9. ⚠️ Complete backtesting data extraction

## 📝 Next Steps

1. **Run report generation with fixes**:
   ```bash
   uv run python src/finwiz/main.py --report-only
   ```

2. **Validate again**:
   ```bash
   uv run python scripts/validate_report.py output/finwiz_family_financial_plan.html
   ```

3. **Check specific issues**:
   ```bash
   # Check for example.com
   grep -i "example.com" output/finwiz_family_financial_plan.html

   # Check for placeholders
   grep -i "à renseigner" output/finwiz_family_financial_plan.html

   # Check portfolio holdings
   grep -c "<tr>" output/finwiz_family_financial_plan.html
   ```

## 🎓 Lessons Learned

1. **Validation is essential** - LLMs will hallucinate when data is missing
2. **Post-generation validation catches issues** - Can't rely on instructions alone
3. **URL validation is critical** - Easy to generate fake URLs
4. **Ticker detection needs refinement** - Too many false positives from common words

## 📊 Success Criteria

Report will pass validation when:
- ✅ Zero example.com URLs
- ✅ Zero placeholder text
- ✅ All SEC URLs return 200 status
- ✅ All tickers in validated list (or improve regex)
- ✅ Dates are current or clearly marked as projections

---

**Validation Tool**: `scripts/validate_report.py`
**Validator Class**: `src/finwiz/validation/report_validator.py`
**URL Validation**: `src/finwiz/tools/sentiment_sources.py`
