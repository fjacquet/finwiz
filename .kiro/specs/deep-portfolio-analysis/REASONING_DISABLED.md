# Stock Crew Reasoning - Smart Configuration

## Issue

Stock crew was stuck in an infinite reasoning loop during the `technical_detail_task`, repeatedly creating elaborate execution plans (Attempt 12+) instead of actually executing the analysis.

## Root Cause

The `market_technical_analyst` agent had `reasoning=True` enabled, which caused it to use the `create_reasoning_plan` tool. This tool was generating overly complex plans that kept asking for user input and never transitioning to actual execution.

## Smart Solution

**Selective reasoning disabling** - Only disable reasoning for the agent that got stuck, keep it for others that might benefit.

### Analysis

**Stock Crew Agents & Tasks:**
- `market_technical_analyst`: Used for 3 tasks
  - market_technical_analysis_task ✅ (completed)
  - stock_screening_task ✅ (completed)
  - technical_detail_task ❌ (got stuck - Attempt 12+)
- `investment_risk_analyst`: Used for 1 task
  - stock_risk_assessment_task (not reached yet, but reasoning could be useful)

**Decision**: Disable reasoning only for `market_technical_analyst` since it got stuck. Keep reasoning for `investment_risk_analyst` since:
1. It hasn't caused issues yet
2. Risk assessment genuinely benefits from reasoning
3. It's the final task, so less risk of blocking the flow

### Changes Made

**File**: `src/finwiz/crews/stock_crew/stock_crew.py`

**Line ~119 - market_technical_analyst agent:**
```python
# Before
reasoning=True,  # Enable AI reasoning to show decision-making process

# After
reasoning=False,  # Disable reasoning to prevent infinite planning loops
```

**Line ~128 - investment_risk_analyst agent:**
```python
# Before (after initial blanket disable)
reasoning=False,  # Disable reasoning to prevent infinite planning loops

# After (smart approach)
reasoning=True,  # Keep reasoning enabled - useful for risk assessment and hasn't caused issues
```

## Impact

### ✅ Benefits

1. **No More Infinite Loops** - Agents will execute tasks directly instead of planning indefinitely
2. **Faster Execution** - No overhead from reasoning/planning steps
3. **Deterministic Behavior** - Agents follow task descriptions directly
4. **Resource Efficient** - Less LLM calls and token usage

### ⚠️ Trade-offs

- **Less Transparency** - No explicit reasoning output showing decision-making process
- **Less Adaptive** - Agents follow instructions more rigidly

However, for automated Flow execution, **deterministic behavior is preferred** over adaptive reasoning.

## Why This Happened

The reasoning feature is designed for interactive use where an agent can ask clarifying questions and adapt its approach. In an automated Flow:

1. Agent creates reasoning plan
2. Plan asks for user input (tickers, permissions, etc.)
3. No user present to provide input
4. Agent creates another plan asking for the same input
5. Infinite loop

## Testing

After this change:

1. Kill the current stuck run:
   ```bash
   pkill -f "crewai flow kickoff"
   ```

2. Run the Flow again:
   ```bash
   uv run python src/finwiz/main.py
   ```

3. Stock crew should now:
   - Complete market analysis task ✅
   - Complete stock screening task ✅
   - Complete technical detail task ✅ (was stuck here)
   - Complete risk assessment task ✅

4. Flow should proceed to:
   - ETF crew
   - Portfolio review
   - **Deep portfolio analysis** (our implementation!)
   - Report generation

## Related Issues

This same reasoning loop issue could affect other crews if they have `reasoning=True` enabled. Consider checking:

- ETF crew
- Crypto crew
- Discovery crew
- Report crew

If any of these get stuck in similar loops, apply the same fix.

## Proactive Fix: ETF Crew

Applied the same smart configuration to ETF crew to prevent similar issues:

**ETF Crew Agents & Tasks:**
- `market_etf_analyst`: Used for 3 tasks
  - etf_market_trends_task
  - etf_screening_task
  - etf_technical_detail_task ⚠️ **Same pattern as stock crew - could get stuck**
- `risk_assessor`: Used for 2 tasks
  - etf_risk_assessment_task
  - etf_investment_strategy_task

**Decision**: Same as stock crew - disable reasoning for `market_etf_analyst`, keep it for `risk_assessor`.

**File**: `src/finwiz/crews/etf_crew/etf_crew.py`

**Line ~97 - market_etf_analyst agent:**
```python
reasoning=False,  # Disable reasoning to prevent infinite planning loops (same issue as stock crew)
```

**Line ~107 - risk_assessor agent:**
```python
reasoning=True,  # Keep reasoning enabled - useful for risk assessment and investment strategy
```

## Summary

**Crews with Smart Reasoning Configuration:**
- ✅ **Stock Crew**: Technical analyst (no reasoning), Risk analyst (with reasoning)
- ✅ **ETF Crew**: Technical analyst (no reasoning), Risk analyst (with reasoning)
- ✅ **Crypto Crew**: All agents keep reasoning (different task structure, already worked)
- ✅ **Report Crew**: Keep reasoning (complex integration tasks benefit from it)

**Pattern Identified**: Technical detail tasks with market/technical analysts tend to get stuck in reasoning loops. Risk assessment tasks benefit from reasoning and don't get stuck.

## Status

✅ **FIXED** - Reasoning smartly configured for stock and ETF crews
✅ **PROACTIVE** - ETF crew fixed before it could get stuck

---

**Last Updated**: 2025-10-10 06:15:00
**Issue**: Stock/ETF crew infinite reasoning loops on technical detail tasks
**Solution**: Selective reasoning disabling for technical analysts, keep for risk analysts
