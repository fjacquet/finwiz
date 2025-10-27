# Debugging Template Variable Issue

## Problem
`ValueError: Missing required template variable 'portfolio_review' not found in inputs dictionary`

## Enhanced Logging Added

We've added comprehensive logging at three critical points to diagnose the issue:

### 1. Flow Orchestrator - Before Report Generation
**File**: `src/finwiz/flows/flow_orchestrator.py` (line ~1879)

**What to look for in logs**:
```
✅ portfolio_review present in state (type: <class 'dict'>)
```

**If you see**:
```
❌ portfolio_review is missing or empty in Flow state before report generation!
```

**Then**: The issue is that `check_portfolio()` didn't set `self.state.portfolio_review` correctly.

**Possible causes**:
- Portfolio review failed during execution
- `check_portfolio()` was skipped
- Portfolio review file couldn't be loaded
- State was reset after portfolio review

### 2. Crew Factory - Inputs Received
**File**: `src/finwiz/crew_factory.py` (line ~285)

**What to look for in logs**:
```
Inputs keys received: ['current_day', 'current_month', ..., 'portfolio_review', ...]
✅ portfolio_review found in inputs
```

**If you see**:
```
❌ portfolio_review NOT found in inputs - this will cause template variable error
```

**Then**: The issue is that `_state_to_dict()` didn't include `portfolio_review` or it was `None`.

**Possible causes**:
- `model_dump()` excluded `None` values
- `portfolio_review` field is not in FinwizState model
- State serialization issue

### 3. Report Crew - Context Preparation
**File**: `src/finwiz/crews/report_crew/report_crew.py` (line ~935)

**What to look for in logs**:
```
Merging Flow state inputs - available keys: ['current_day', 'current_month', ..., 'portfolio_review', ...]
✅ Preserved key: portfolio_review
Successfully preserved N Flow state keys: ['portfolio_review', 'current_day', ...]
✅ portfolio_review preserved in prepared_context
```

**If you see**:
```
❌ Expected key 'portfolio_review' not found in Flow state inputs
```

**Then**: The issue is that inputs passed to `prepare_crew_context()` don't contain `portfolio_review`.

**If you see**:
```
❌ portfolio_review NOT in prepared_context - template variable error will occur
```

**Then**: The merge logic failed to preserve `portfolio_review`.

## Diagnostic Steps

### Step 1: Run the Application with Logging
```bash
uv run python src/finwiz/main.py --report-only 2>&1 | tee debug_output.log
```

### Step 2: Search for Critical Log Messages

```bash
# Check if portfolio_review is in Flow state
grep "portfolio_review present in state" debug_output.log

# Check if portfolio_review is in crew factory inputs
grep "portfolio_review found in inputs" debug_output.log

# Check if portfolio_review is being preserved
grep "Preserved key: portfolio_review" debug_output.log

# Check for error messages
grep "portfolio_review NOT found" debug_output.log
grep "portfolio_review is missing" debug_output.log
```

### Step 3: Identify the Failure Point

| Log Message | Failure Point | Next Action |
|-------------|---------------|-------------|
| ❌ at Flow Orchestrator | `check_portfolio()` didn't set state | Check portfolio review execution |
| ✅ at Flow Orchestrator, ❌ at Crew Factory | `_state_to_dict()` issue | Check model_dump() behavior |
| ✅ at Crew Factory, ❌ at Report Crew | Merge logic issue | Check prepare_crew_context() |
| ✅ at Report Crew | Template variable still missing | Check task YAML configuration |

## Common Issues and Solutions

### Issue 1: portfolio_review is None
**Symptom**: `model_dump()` excludes `None` values by default

**Solution**: Check if `model_dump()` is called with `exclude_none=False`:
```python
# In flow_orchestrator.py
def _state_to_dict(self) -> dict[str, Any]:
    return self.state.model_dump(exclude_none=False)  # Include None values
```

### Issue 2: portfolio_review not loaded
**Symptom**: Portfolio review file exists but wasn't loaded into state

**Check**:
```bash
# Verify file exists
ls -lh output/portfolio/portfolio_review.json

# Check if it was loaded
grep "Portfolio review generated at" debug_output.log
grep "Failed to load portfolio review JSON" debug_output.log
```

**Solution**: Ensure `check_portfolio()` successfully loads the file:
```python
with open(out_path, encoding="utf-8") as f:
    portfolio_data = json.load(f)
    self.state.portfolio_review = portfolio_data
    logger.info(f"✅ Loaded portfolio_review with {len(portfolio_data.get('holdings', []))} holdings")
```

### Issue 3: Merge logic not executing
**Symptom**: Logs show inputs have `portfolio_review` but it's not preserved

**Check**: Is the merge loop actually running?
```python
if inputs:  # This condition must be True
    for key in ["portfolio_review", ...]:
        if key in inputs:  # This condition must be True for portfolio_review
            if key not in integrated_context:  # This should be True
                integrated_context[key] = inputs[key]
```

**Solution**: Add more granular logging to identify which condition fails.

### Issue 4: Template variable name mismatch
**Symptom**: Everything looks correct but error still occurs

**Check**: Task YAML uses exact key name:
```yaml
# In tasks.yaml
description: |
  Use portfolio data: {portfolio_review}  # Must match exactly
```

**Solution**: Ensure key names match exactly (case-sensitive).

## Quick Test Script

Create `test_state_dict.py`:
```python
from finwiz.flow_state import FinwizState

# Create state with portfolio_review
state = FinwizState()
state.portfolio_review = {"test": "data"}

# Test model_dump()
state_dict = state.model_dump()
print(f"portfolio_review in dict: {'portfolio_review' in state_dict}")
print(f"portfolio_review value: {state_dict.get('portfolio_review')}")

# Test with exclude_none
state2 = FinwizState()  # portfolio_review is None
dict_with_none = state2.model_dump(exclude_none=False)
dict_without_none = state2.model_dump(exclude_none=True)

print(f"\nWith exclude_none=False: {'portfolio_review' in dict_with_none}")
print(f"With exclude_none=True: {'portfolio_review' in dict_without_none}")
```

## Expected Log Flow (Success Case)

```
# 1. Portfolio review execution
INFO - Starting portfolio review with core analysis results available
INFO - Portfolio review generated at output/portfolio/portfolio_review.json
INFO - ✅ Loaded portfolio_review with 65 holdings

# 2. Report generation start
INFO - Starting report generation with enhanced error handling
INFO - ✅ portfolio_review present in state (type: <class 'dict'>)

# 3. Crew factory receives inputs
INFO - Starting report generation crew
INFO - Inputs keys received: [..., 'portfolio_review', ...]
INFO - ✅ portfolio_review found in inputs

# 4. Context preparation
INFO - Merging Flow state inputs - available keys: [..., 'portfolio_review', ...]
INFO - ✅ Preserved key: portfolio_review
INFO - Successfully preserved 8 Flow state keys: ['portfolio_review', ...]
INFO - ✅ portfolio_review preserved in prepared_context

# 5. Report generation success
INFO - Report generation completed successfully
```

## Next Steps Based on Logs

1. **Run the application** with enhanced logging
2. **Capture the logs** to a file
3. **Search for the critical messages** listed above
4. **Identify which checkpoint fails** (1, 2, 3, or 4)
5. **Apply the corresponding solution** from this guide

---

**Status**: Debugging in progress  
**Date**: 2025-10-16  
**Version**: 1.0
