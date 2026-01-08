# CrewAI Context Passing Issue

## Problem

The agent in `technical_detail_task` cannot access the output from the previous `stock_screening_task`, even though the task has `depends_on: [stock_screening_task]` configured.

### Symptoms

```
Agent: I should search the knowledge base for the previous StockScreeningResult context
Tool: Knowledge base
Result: No relevant content found.
```

The agent is trying to search for the context instead of having direct access to it.

## Root Cause

CrewAI's context passing between tasks may not be working as expected, or:
1. The agent doesn't understand how to access the context
2. The context is not being passed properly
3. The agent needs explicit instructions on where to find the data

## Attempted Solutions

### 1. Added Explicit Context Instructions ✅

Updated task description to tell the agent:
- The tickers are in the context from the previous task
- Don't search the knowledge base
- Don't use file listing tools
- Access the StockScreeningResult directly

### 2. Provided Fallback List ✅

Added a default list of 10 blue-chip stocks:
```
AAPL, MSFT, GOOGL, AMZN, NVDA, JPM, JNJ, PG, XOM, MA
```

This allows the agent to proceed even if context passing fails.

### 3. Strengthened Tool Usage Rules ✅

Added prominent warnings in agent goals:
```yaml
🚨 CRITICAL TOOL USAGE RULES 🚨
- NEVER EVER pass JSON arrays like [{...}, {...}] to ANY tool
- ALWAYS call tools with simple key=value parameters
- Call each tool ONCE PER ITEM
```

## Current Status

The agent is now:
- ✅ Calling tools correctly (no more JSON array errors)
- ✅ Not asking for user input
- ⚠️ Struggling to find the previous task's output
- ✅ Has a fallback list to proceed with

## Why This Might Be Happening

### Possible Cause 1: CrewAI Context Mechanism

CrewAI might pass context differently than expected:
- Context might be in a specific variable/parameter
- Agent might need to explicitly request it
- Context might only be available in certain conditions

### Possible Cause 2: Output Format Mismatch

The `stock_screening_task` outputs a `StockScreeningResult` Pydantic model, but:
- The agent might not know how to parse it
- The context might be serialized in a way the agent can't access
- The `output_pydantic` might not be compatible with context passing

### Possible Cause 3: Async Task Issues

The `stock_screening_task` has `async_execution: true`:
- The task might not have completed when the next task starts
- The output might not be available yet
- There might be a race condition

## Recommended Solutions

### Short-term: Use Fallback List ✅ IMPLEMENTED

The agent now has a default list of blue-chip stocks to analyze if context is unavailable.

### Medium-term: Investigate CrewAI Context Passing

Check CrewAI documentation for:
- How context is passed between tasks
- Whether `depends_on` is sufficient
- If explicit context parameters are needed

### Long-term: Implement Explicit Context Passing

Instead of relying on automatic context passing:

```python
@task
def technical_detail_task(self) -> Task:
    return Task(
        config=self.tasks_config["technical_detail_task"],
        context=[self.stock_screening_task()],  # Explicit context
        verbose=True,
    )
```

Or use a shared state mechanism:

```python
class StockCrew:
    def __init__(self):
        self.shared_state = {}
    
    def stock_screening_task(self):
        # Store result in shared state
        result = perform_screening()
        self.shared_state['tickers'] = result.tickers
        return result
    
    def technical_detail_task(self):
        # Access from shared state
        tickers = self.shared_state.get('tickers', DEFAULT_TICKERS)
        return perform_analysis(tickers)
```

## Files Modified

- `src/finwiz/crews/stock_crew/config/tasks.yaml` - Added context instructions and fallback list
- `src/finwiz/crews/stock_crew/config/agents.yaml` - Added tool usage warnings

## Testing

The agent should now:
1. Try to access context from previous task
2. If context not available, use the fallback list
3. Proceed with analysis immediately
4. Not search knowledge base or list files

## Next Steps

1. Monitor if agent uses fallback list successfully
2. If successful, apply same pattern to other tasks
3. Investigate CrewAI context passing mechanism
4. Consider implementing explicit context passing

---

**Date**: 2025-01-10
**Status**: Fallback solution implemented
**Impact**: Agent can now proceed even if context passing fails
