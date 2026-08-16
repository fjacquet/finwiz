# Deep Analysis Troubleshooting

Comprehensive troubleshooting guide for FinWiz deep analysis issues, including diagnostic procedures and common solutions.

## Common Issue: Zero Deep Analyses

### Problem Description

The deep analysis report shows:

- 🔬 **0 Successful Analyses**
- 🔬 **0 Failed Analyses**
- 🔬 **0.0% Success Rate**

### Root Causes and Solutions

#### 1. Empty Portfolio

**Symptoms**: No positions in the portfolio
**Verification**: Check the "Detailed Position Analysis" section

**Solution**:

1. Add positions to the portfolio
2. Verify portfolio data is correctly loaded

#### 2. Deep Analysis Produced No Results (Always Investigate — Not Normal)

**There is no grade-based gate on deep analysis.** The deep-analysis
orchestrator takes `portfolio_review.get("holdings", [])` unfiltered and
passes the *entire* list to `run_deep_analysis_concurrent` — every holding
in the portfolio is analyzed regardless of grade
(`orchestrators/deep_analysis_orchestrator.py:228,234,249`). If the report
shows 0/0/0.0%, it means the phase failed to produce results for a
portfolio that does have holdings, not that all positions were "good
enough" to skip.

**Verification**: Check the run logs for errors during Phase 3 (Deep
Analysis & Portfolio Update); an all-zero result with a non-empty portfolio
indicates a failure, not skipped-by-design behavior.

**Note**: A report section may still render text like "No Deep Analysis
Required... only runs on positions requiring special attention" as a
fallback message when zero holdings were processed
(`reporting/sections/analysis.py`) — that wording is itself stale/misleading
and should not be read as confirming grade-based filtering exists.

#### 3. Analysis Process Error

**Symptoms**: Errors in execution logs
**Verification**: Check application logs

**Solutions**:

1. Review detailed logs
2. Verify API keys are configured
3. Check network connectivity

#### 4. Incorrect Configuration — NOT APPLICABLE (kill switch removed)

The `DEEP_PORTFOLIO_ANALYSIS` kill switch has been removed. Deep analysis
now **always runs**, with no env-var gate — the orchestrator's own comment
explains why: "this is a financial trust system. A '✅ completed' report on
zero analyses is worse than a hard failure. The previous
DEEP_PORTFOLIO_ANALYSIS kill switch defaulted to 'false' and silently
no-op'd the entire phase, producing reports with placeholder grades that
users mistook for real verdicts"
(`orchestrators/deep_analysis_orchestrator.py:216-221`). Setting this
variable has no effect on whether Phase 3 executes; if you're seeing zero
analyses, look at root causes #1 and #3 instead.

## Diagnostic Procedures

### Step 1: Verify Portfolio Content

```bash
# Search for position count in the report
grep -A5 -B5 "positions" output/finwiz_family_financial_plan.html
```

### Step 2: Check Position Grades

```bash
# Search for grades in the report
grep -A10 "Detailed Position Analysis" output/finwiz_family_financial_plan.html
```

### Step 3: Check Error Logs

```bash
# Search for recent errors
find . -name "*.log" -exec grep -l "deep.*analysis\|analyse.*approfondie" {} \;
```

### Step 4: Verify Configuration

`DEEP_PORTFOLIO_ANALYSIS` no longer exists — see root cause #4 above. There
is nothing to check here; skip this step.

## Deep Analysis Logic

**There is no grade-based gate.** Every holding in the portfolio runs
through deep analysis, regardless of grade (A+ through F) — see root cause
2 above for the exact code reference. A previous version of this guide
documented a grade cutoff (skip A+ through B, analyze B- and below); that
was never true of the code and should be disregarded.

## Message Improvements

### Before (Misleading)

```html
✅ Deep Analysis Completed
Python deep analysis was successfully executed on 0 positions.
```

### After (Clear) — this message text is still misleading

```html
✅ No Deep Analysis Needed
All your positions have satisfactory grades (>=B). Deep analysis only runs
on positions needing attention.
```

This exact string is still in `reporting/sections/analysis.py` today, but
it only fires when `successful == 0 and failed == 0` (i.e. the run
processed zero holdings) — it is not evidence of grade-based filtering,
which does not exist (see "Deep Analysis Logic" above). Read this message
as "the run produced no results," not "your portfolio was too good to
need analysis."

## Implementation Fix

`python_report_generator.py`'s `_generate_deep_analysis_section` is a 3-line
delegator, not the implementation shown in a previous version of this
guide — `_generate_no_deep_analysis_section()` and
`_render_deep_analysis_template(...)` don't exist anywhere in the codebase.
The real logic lives in
`finwiz.reporting.sections.analysis.generate_deep_analysis_section`:

```python
# src/finwiz/reporting/python_report_generator.py
def _generate_deep_analysis_section(self, deep_analysis_results: dict[str, Any] | None) -> str:
    """Generate deep analysis section (delegates to module)."""
    from finwiz.reporting.section_generators import generate_deep_analysis_section

    return generate_deep_analysis_section(deep_analysis_results)
```

```python
# src/finwiz/reporting/sections/analysis.py (the real implementation)
def generate_deep_analysis_section(deep_analysis_results: dict[str, Any] | None) -> str:
    """Generate deep analysis section."""
    if not deep_analysis_results:
        # "not deep_analysis_results" branch — a "Deep analysis not available" warning

    successful = deep_analysis_results.get("successful_analyses", 0)
    failed = deep_analysis_results.get("failed_analyses", 0)
    total = deep_analysis_results.get("total_holdings", 0)

    if successful > 0:
        status_title = "Deep Analysis Completed"
    elif failed > 0:
        # Don't dress a pure-failure run up as "no action needed"
        status_title = "Deep Analysis Failed"
    else:
        status_title = "No Deep Analysis Needed"
    # ...
```

There are three branches here, not two — the earlier version of this doc
omitted the "Deep Analysis Failed" case, which exists specifically so a
run that failed on every holding isn't dressed up as "nothing needed
attention."

## Verification Checklist

To verify the exact cause, check:

1. **Position table** in the report - how many positions and what grades?
2. **Recent logs** - are there any errors?
3. **Configuration** - is deep analysis enabled?
4. **Environment variables** - are all required API keys set?

---

**Version**: 1.0
**Last Updated**: 2025-10-28
**Source**: Integrated from analysis/DIAGNOSTIC_ANALYSE_APPROFONDIE.md and analysis/FIX_ANALYSE_APPROFONDIE_MESSAGE.md
