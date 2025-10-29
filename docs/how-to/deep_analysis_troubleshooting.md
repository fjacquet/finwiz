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

#### 2. All Positions Have Grade ≥ B (Normal Behavior)

**Symptoms**: Deep analysis shows 0 analyses but portfolio has positions
**Verification**: Check grades in the position table

**This is normal behavior!** Deep analysis only runs on underperforming positions (grade < B).

**Expected Message**:

```
✅ No Deep Analysis Required
All your positions have a satisfactory grade (≥B).
Deep analysis only runs on positions requiring special attention (grade < B).
```

#### 3. Analysis Process Error

**Symptoms**: Errors in execution logs
**Verification**: Check application logs

**Solutions**:

1. Review detailed logs
2. Verify API keys are configured
3. Check network connectivity

#### 4. Incorrect Configuration

**Symptoms**: Deep analysis is not enabled
**Verification**: Check `DEEP_PORTFOLIO_ANALYSIS=true`

**Solutions**:

1. Enable `DEEP_PORTFOLIO_ANALYSIS=true`
2. Restart the analysis

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

```bash
# Check environment variables
grep -r "DEEP_PORTFOLIO_ANALYSIS" .
```

## Deep Analysis Logic

Deep analysis execution follows this logic:

| Grade | Deep Analysis | Reason |
|-------|---------------|---------|
| A+, A, A- | ❌ No | Excellent positions |
| B+, B | ❌ No | Satisfactory positions |
| B-, C+, C, C-, D, F | ✅ Yes | Positions requiring attention |

## Message Improvements

### Before (Misleading)

```html
✅ Deep Analysis Completed
Python deep analysis was successfully executed on 0 positions.
```

### After (Clear)

```html
✅ No Deep Analysis Required
All your positions have a satisfactory grade (≥B).
Deep analysis only runs on positions requiring special attention (grade < B).
```

## Implementation Fix

The misleading message was fixed in `src/finwiz/reporting/python_report_generator.py`:

```python
def _generate_deep_analysis_section(self, deep_analysis_results: dict[str, Any] | None) -> str:
    """Generate deep analysis section with improved messaging."""
    if not deep_analysis_results:
        return self._generate_no_deep_analysis_section()

    successful = deep_analysis_results.get("successful_analyses", 0)
    failed = deep_analysis_results.get("failed_analyses", 0)
    total = deep_analysis_results.get("total_holdings", 0)
    
    # Improved messaging based on context
    if successful == 0 and failed == 0:
        if total == 0:
            status_class = "warning"
            status_icon = "ℹ️"
            status_title = "Empty Portfolio"
            status_message = "No positions to analyze in the portfolio."
        else:
            status_class = "success"
            status_icon = "✅"
            status_title = "No Deep Analysis Required"
            status_message = "All your positions have a satisfactory grade (≥B). Deep analysis only runs on positions requiring special attention."
    else:
        status_class = "success"
        status_icon = "✅"
        status_title = "Deep Analysis Completed"
        status_message = f"Python deep analysis was successfully executed on {successful} positions."

    return self._render_deep_analysis_template(
        successful, failed, total, status_class, status_icon, status_title, status_message
    )
```

## Verification Checklist

To verify the exact cause, check:

1. **Position table** in the report - how many positions and what grades?
2. **Recent logs** - are there any errors?
3. **Configuration** - is deep analysis enabled?
4. **Environment variables** - are all required API keys set?

## Related Documentation

- [Performance Troubleshooting](performance_troubleshooting.md)
- [API Troubleshooting](api_troubleshooting.md)
- [Deep Analysis Integration](DEEP_ANALYSIS_INTEGRATION.md)

---

**Version**: 1.0  
**Last Updated**: 2025-10-28  
**Source**: Integrated from analysis/DIAGNOSTIC_ANALYSE_APPROFONDIE.md and analysis/FIX_ANALYSE_APPROFONDIE_MESSAGE.md
