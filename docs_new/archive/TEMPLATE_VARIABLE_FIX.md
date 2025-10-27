---
title: "Template Variable Fix"
description: "Archived documentation for Template Variable Fix"
category: "archive"
tags:
  - "archive"
date: "2025-10-26"
source: "archive/TEMPLATE_VARIABLE_FIX.md"
---

# Template Variable Fix - Additional Issue Resolved

[TOC]

## Problem Encountered

After implementing the ticker validation fix, a new error appeared:

```text
ValueError: Missing required template variable 'Template variable 'portfolio_review'
not found in inputs dictionary' in description
```text
### Root Cause

The task configuration in `src/finwiz/crews/report_crew/config/tasks.yaml` uses template variables like `{portfolio_review}` that expect certain keys at the top level of the inputs dictionary.

However, `prepare_crew_context()` was returning only the integrated context structure (with keys like `consolidated_crew_data`, `core_analysis_summary`, etc.) without preserving the original Flow state keys that tasks expect.

## Solution Implemented

### Modified `report_crew.py` - `prepare_crew_context()` method

Added logic to preserve Flow state template variables by merging them with the integrated context:

```pythonthon
def prepare_crew_context(self, max_age_hours: int = 24, inputs: dict[str, Any] | None = None) -> dict[str, Any]:
    """Prepare integrated context for crew execution."""
    try:
        # Get integrated data context
        integrated_context = self.get_integrated_data_context(max_age_hours, inputs)

        # CRITICAL: Merge original Flow state inputs to preserve template variables
        # The task configuration expects certain top-level keys like portfolio_review
        if inputs:
            # Preserve original Flow state data that tasks expect
            for key in ["portfolio_review", "current_day", "current_month", "current_year",
                       "current_date", "full_date", "timestamp", "report_language"]:
                if key in inputs and key not in integrated_context:
                    integrated_context[key] = inputs[key]
                    logger.debug(f"Preserved Flow state key: {key}")

        # ... rest of the method (ticker validation, etc.)

        return integrated_context
```text
## What This Fixes

### ✅ Template Variable Compatibility
- Tasks can now access `{portfolio_review}` and other template variables
- Original Flow state data preserved alongside integrated context
- No breaking changes to existing task configurations

### ✅ Backward Compatibility
- Existing task YAML files work without modification
- Both old-style (Flow state) and new-style (integrated context) data available
- Graceful handling when keys don't exist

### ✅ Complete Data Access
- Integrated context: `consolidated_crew_data`, `aplus_opportunities`, etc.
- Flow state: `portfolio_review`, `current_date`, `timestamp`, etc.
- Validated tickers: `validated_tickers_list`, `ticker_count`

## Template Variables Preserved

The following keys from Flow state are now preserved in the prepared context:

1. **portfolio_review** - Portfolio holdings and decisions
2. **current_day** - Current day (e.g., "16")
3. **current_month** - Current month (e.g., "October")
4. **current_year** - Current year (e.g., "2025")
5. **current_date** - Formatted date (e.g., "October 16, 2025")
6. **full_date** - Full date string
7. **timestamp** - Execution timestamp
8. **report_language** - Report language (e.g., "fr")

## Data Flow After Fix

```text
Flow State (inputs)
    ├─ portfolio_review
    ├─ current_date
    ├─ timestamp
    └─ ... (other Flow state keys)
        ↓
prepare_crew_context(inputs)
    ↓
get_integrated_data_context(inputs)
    ├─ consolidated_crew_data
    ├─ aplus_opportunities
    ├─ validated_tickers_list
    └─ ... (integrated context keys)
        ↓
Merge Flow state keys into integrated context
    ├─ IF key in inputs AND key not in integrated_context
    └─ THEN integrated_context[key] = inputs[key]
        ↓
Return merged context with BOTH:
    ├─ Integrated data (new structure)
    └─ Flow state data (template variables)
        ↓
crew.kickoff(inputs=merged_context)
    ↓
Tasks can access:
    ├─ {portfolio_review} ✅
    ├─ {current_date} ✅
    ├─ inputs.validated_tickers_list[] ✅
    └─ inputs.aplus_opportunities ✅
```text
## Why This Approach

### Option 1: Update Task YAML (Rejected)
- Would require changing all task descriptions
- Breaking change for existing configurations
- More maintenance overhead

### Option 2: Merge Contexts (Chosen) ✅
- No changes to task YAML files
- Backward compatible
- Preserves both old and new data structures
- Minimal code changes

## Testing

To verify the fix works:

```bash
# Run report generation
uv run python src/finwiz/main.py --report-only

# Look for success messages:
# ✅ "Preserved Flow state key: portfolio_review"
# ✅ "Preserved Flow state key: current_date"
# ✅ "Crew context prepared with N validated tickers"
# ✅ "Report generation completed successfully"
```text
## Error Handling

If a template variable is still missing after the merge:

1. **Check Flow state** - Ensure the key exists in Flow orchestrator's `_state_to_dict()`
2. **Check preservation list** - Add the key to the preservation list if needed
3. **Check task YAML** - Verify the template variable name matches exactly

## Related Files

- **Modified**: `src/finwiz/crews/report_crew/report_crew.py` (lines 920-985)
- **Task Config**: `src/finwiz/crews/report_crew/config/tasks.yaml` (uses template variables)
- **Flow State**: `src/finwiz/flows/flow_orchestrator.py` (provides original inputs)

## Complete Fix Summary

This fix completes the ticker validation implementation by ensuring:

1. ✅ **Ticker validation** - Tickers extracted and validated (Part 1)
2. ✅ **Template variables** - Flow state keys preserved (Part 2)
3. ✅ **Data integration** - Both structures available to tasks
4. ✅ **Backward compatibility** - No breaking changes

---

**Status**: ✅ **FIXED AND TESTED**
**Date**: 2025-10-16
**Version**: 1.1 (Template Variable Fix)
