---
title: "Fix"
description: "Archived documentation for Fix"
category: "archive"
tags:
  - "archive"
date: "2025-10-26"
source: "archive/README_FIX.md"
---

# Discovery Data Schema Fix - Complete Guide

[TOC]

## Quick Summary

✅ **Fix Status**: IMPLEMENTED AND TESTED
⏳ **Next Step**: Run the flow to see the fix in action

## What Was Fixed

Fixed the schema mismatch in `APlusDataExtractor` that was causing discovery data to fail Pydantic validation silently, resulting in "NOT AVAILABLE" appearing in reports.

## The Problem

The extractor returned dictionaries with field names that didn't match the `APlusOpportunity` schema:
- Used `company_name`, `fund_name`, `crypto_name` instead of unified `name`
- Missing required fields: `composite_score`, `rationale`, `key_metrics`
- Caused silent Pydantic validation failures

## The Solution

Updated three extraction methods to return dictionaries matching the exact schema:
- ✅ Unified field name: `name` (not `company_name`/`fund_name`/`crypto_name`)
- ✅ Added `composite_score` (float, 0.0-1.0)
- ✅ Added `rationale` (list of strings)
- ✅ Added `key_metrics` (dict with asset-specific metrics)
- ✅ Fixed validation to extract symbols before duplicate checking

## Test Results

```bash
$ uv run pytest tests/unit/tools/test_aplus_extractor.py -v --no-cov
=============== 18 passed in 0.36s ===============
```text
All tests passing, no linting errors, ready for production.

## Current Situation

The HTML report currently shows "discovery not run" because:
1. Discovery JSON files exist with correct data (15 A+ stocks, multiple ETFs/crypto)
2. Report was generated **before** the fix was applied
3. Flow state has `has_a_plus_analysis: False`

## Next Steps

Run the flow to generate a new report with the fix:

```bash
uv run python src/finwiz/main.py
```text
Expected results:
- ✅ Discovery data loads successfully
- ✅ Report shows A+ opportunities section populated
- ✅ Data availability shows actual counts (not "NOT PROVIDED")
- ✅ SEC filing URLs appear for stocks

## Files Modified

1. `src/finwiz/integration/aplus_extractor.py` - Fixed extraction methods
2. `tests/unit/tools/test_aplus_extractor.py` - Updated tests

## Documentation

- `IMPLEMENTATION_SUMMARY.md` - Detailed implementation notes
- `SCHEMA_FIX_REFERENCE.md` - Quick reference for schema changes
- `FIX_COMPLETED.md` - Completion summary
- `CURRENT_STATUS.md` - Current state analysis
- `README_FIX.md` - This file

## Verification

After running the flow, check:

```bash
# Check logs for successful extraction
grep "Extracted.*A+ opportunities" flow_execution.log

# Expected:
# "Extracted 15 stock A+ opportunities"
# "Extracted X ETF A+ opportunities"
# "Extracted X crypto A+ opportunities"

# Open the new report
open output/finwiz_family_financial_plan.html

# Verify discovery section shows actual data
```text
## Rollback (if needed)

```bash
git checkout src/finwiz/integration/aplus_extractor.py tests/unit/tools/test_aplus_extractor.py
```text
---

**Ready to deploy**: The fix is complete, tested, and ready for the next flow run.
