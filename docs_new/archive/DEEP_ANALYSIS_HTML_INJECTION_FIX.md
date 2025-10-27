---
title: "Deep Analysis Html Injection Fix"
description: "Archived documentation for Deep Analysis Html Injection Fix"
category: "archive"
tags:
  - "archive"
date: "2025-10-26"
source: "archive/DEEP_ANALYSIS_HTML_INJECTION_FIX.md"
---

# Deep Analysis HTML Injection Fix

[TOC]

## Problem

The report crew was generating incorrect reports because:

1. **Portfolio data has placeholder grades**: All holdings show 0.7/C even though deep analysis was run
2. **Real analysis is in HTML files**: The actual grades (A+, A-, B, etc.) are only in `output/deep_analysis/*.html`
3. **Data not merged**: The Flow ran deep analysis but never extracted results back into portfolio_review.json

Example:
- Portfolio says: AAPL grade C (0.7) ❌
- HTML file says: AAPL grade A- (0.82) ✅

## Root Cause

The upstream Flow has a bug where:
1. DeepAnalysisCrew runs for each holding ✅
2. HTML reports are generated ✅
3. Grades are extracted from crew output ❌
4. Portfolio_review.json is updated with real grades ❌

Result: portfolio_review.json has `crew_analysis_used: DeepAnalysisCrew` but still has placeholder data.

## Solution Implemented

**Give the final reporter agent direct access to HTML files** so it can extract real grades itself.

### Changes Made

#### 1. Modified `investment_reporter` Agent (report_crew.py)

```pythonthon
# BEFORE: No tools (enforced by @final_reporter)
@final_reporter
@agent
def investment_reporter(self) -> Agent:
    return Agent(
        config=self.agents_config["investment_reporter"],
        tools=[],  # Empty
    )

# AFTER: Read-only access to deep analysis HTML
@agent
def investment_reporter(self) -> Agent:
    deep_analysis_tools = [
        DirectoryReadTool(directory="output/deep_analysis"),
        FileReadTool(),  # For reading specific HTML files
    ]

    return Agent(
        config=self.agents_config["investment_reporter"],
        tools=deep_analysis_tools,
    )
```text
#### 2. Updated Task Description (tasks.yaml)

Added critical instructions to the `comprehensive_investment_report_task`:

```yaml
⚠️ CRITICAL: READ DEEP ANALYSIS HTML FILES FOR REAL GRADES ⚠️

**PORTFOLIO DATA ISSUE**: The portfolio_review data has PLACEHOLDER grades (all 0.7/C).
The REAL analysis is in the HTML files in output/deep_analysis/.

**YOU MUST**:
1. For each holding, read its deep analysis HTML file:
   - Format: {TICKER}_deep_analysis_{asset_class}.html
   - Example: AAPL_deep_analysis_stock.html
2. Extract the REAL grade from HTML (look for "Grade: A+", "Grade: B", etc.)
3. Extract the REAL composite score
4. Use DirectoryReadTool to list files
5. Use FileReadTool to read specific HTML files
6. IGNORE placeholder grades in portfolio_review (0.7/C)
7. Use grades from HTML files for recommendations
```text
## How It Works

1. **Reporter lists HTML files**: Uses DirectoryReadTool on `output/deep_analysis/`
2. **Reporter reads each file**: Uses FileReadTool to read `{TICKER}_deep_analysis_{asset_class}.html`
3. **Reporter extracts grades**: Parses HTML to find real grade (A+, A-, B, etc.) and composite score
4. **Reporter uses real data**: Generates report with actual analysis, not placeholders

## Example Extraction

From `AAPL_deep_analysis_stock.html`:
```html
<div class="score-large">Score composite: 0.82 / 1.00</div>
<div class="grade Aminus" title="A-">A-</div>
```text
Reporter should extract:
- Grade: A-
- Composite Score: 0.82

## Limitations

This is a **workaround**, not a proper fix. The proper fix would be:

1. Fix the Flow to extract grades from DeepAnalysisCrew output
2. Update portfolio_review.json with real grades
3. Report crew reads structured data (not HTML parsing)

## Benefits

✅ Report now shows real grades (A+, A-, B, etc.)
✅ No changes needed to other agents (integration, allocation, risk)
✅ Works with existing HTML files
✅ Fast to implement

## Drawbacks

❌ HTML parsing is fragile (format changes break it)
❌ Doesn't fix the root cause (Flow bug)
❌ Reporter agent has tools (violates @final_reporter pattern)
❌ Slower execution (reads many HTML files)

## TODO

- [ ] Fix upstream Flow to properly extract and merge deep analysis results
- [ ] Remove HTML parsing workaround once Flow is fixed
- [ ] Restore @final_reporter decorator (empty tools)

## Testing

Run the report crew:
```bash
uv run python run_report_simple.py
```text
Check the generated report for:
- Real grades (not all C)
- Real scores (not all 0.7)
- Proper recommendations based on actual analysis

## Files Modified

- `src/finwiz/crews/report_crew/report_crew.py` - Added tools to investment_reporter
- `src/finwiz/crews/report_crew/config/tasks.yaml` - Added HTML reading instructions
