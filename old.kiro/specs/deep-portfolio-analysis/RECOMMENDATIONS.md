# Recommendations for Resolving Crew Execution Issues

## Current Situation

You have **4 critical issues fixed** for the stock crew:
1. ✅ Agent input loop
2. ✅ Tool input format (with explicit instructions)
3. ✅ SEC.gov 403 errors
4. ✅ FAISS missing dependency

However, the **systemic tool array issue** persists across all crews.

## Immediate Recommendations

### 1. Restart Stock Crew Execution (PRIORITY 1)

The current execution is using the old environment without FAISS. You need to:

```bash
# Kill the current execution (Ctrl+C)
# Then restart with the new environment
uv run python src/finwiz/main.py
```

**Why**: All fixes are in place, but the running process doesn't have them.

### 2. Monitor for Success Indicators

Watch for:
- ✅ No "Could not import faiss" errors
- ✅ No "Action Input is not a valid key, value dictionary" errors  
- ✅ Tools called individually (one ticker at a time)
- ✅ Tasks completing without hanging
- ✅ Final HTML report generated

### 3. If Still Hanging - Reduce Scope

If the stock crew still hangs, try reducing the analysis scope:

**Option A**: Reduce number of stocks
```yaml
# In stock_screening_task description
# Change from 10 stocks to 3 stocks for testing
"screen and identify the top 3 stable, blue-chip stocks"
```

**Option B**: Disable expensive tools temporarily
```python
# In stock_crew.py
tools = get_stock_crew_tools(
    include_rag=False,  # Disable RAG temporarily
    include_quantitative=True,
    collection_suffix="stock",
)
```

**Option C**: Reduce max iterations
```python
# In stock_crew.py crew() method
max_iter=10,  # Reduce from 25 to 10
max_retries=3,  # Reduce from 10 to 3
```

## Medium-Term Recommendations

### 4. Fix Other Crews (After Stock Crew Works)

Apply the same fixes to crypto and ETF crews:

**Crypto Crew**:
- Add tool usage warnings to `src/finwiz/crews/crypto_crew/config/tasks.yaml`
- Add execution rules to `src/finwiz/crews/crypto_crew/config/agents.yaml`

**ETF Crew**:
- Same as crypto crew

**Template to use**:
```yaml
⚠️ CRITICAL TOOL USAGE RULES ⚠️
- NEVER pass JSON arrays or multiple items to tools
- ALWAYS call each tool ONCE PER ITEM individually
- Use the exact parameter names and formats shown below
- Tools expect individual parameters, NOT JSON strings or arrays
```

### 5. Add System-Level Safeguards

**Option A**: Add agent-level constraints
```python
# In each crew's agent definitions
Agent(
    max_iter=15,  # Limit iterations per agent
    max_execution_time=600,  # 10 minute timeout
    allow_delegation=False,  # Prevent delegation loops
)
```

**Option B**: Add tool validation wrapper
```python
# Create src/finwiz/tools/tool_validator.py
class ToolInputValidator:
    @staticmethod
    def validate_input(input_data):
        if isinstance(input_data, str):
            try:
                parsed = json.loads(input_data)
                if isinstance(parsed, list):
                    raise ValueError(
                        "Tool does not accept arrays. "
                        "Call the tool once per item."
                    )
            except json.JSONDecodeError:
                pass
        return input_data
```

## Long-Term Recommendations

### 6. Improve Tool Documentation

Add clear examples to each tool's docstring:

```python
class EnhancedSECAnalysisTool(BaseTool):
    """
    Enhanced SEC filing analysis tool.
    
    USAGE:
    ✅ CORRECT: tool(ticker="AAPL", form_type="10-K")
    ❌ WRONG: tool([{"ticker": "AAPL"}, {"ticker": "MSFT"}])
    
    Call this tool ONCE PER TICKER, not with arrays.
    """
```

### 7. Add Crew Execution Monitoring

Create a monitoring system:

```python
# src/finwiz/utils/crew_monitor.py
class CrewMonitor:
    def __init__(self, max_duration=1800):  # 30 minutes
        self.start_time = time.time()
        self.max_duration = max_duration
        
    def check_timeout(self):
        if time.time() - self.start_time > self.max_duration:
            raise TimeoutError("Crew execution exceeded maximum duration")
```

### 8. Implement Graceful Degradation

If a tool fails repeatedly, skip it:

```python
def call_tool_with_fallback(tool, params, max_retries=3):
    for attempt in range(max_retries):
        try:
            return tool(**params)
        except Exception as e:
            if attempt == max_retries - 1:
                logger.warning(f"Tool {tool.name} failed, using fallback")
                return {"status": "skipped", "reason": str(e)}
            time.sleep(2 ** attempt)  # Exponential backoff
```

## Decision Tree

```
Is stock crew still hanging after restart?
├─ NO → Great! Apply same fixes to other crews
└─ YES → Is it the same tool array error?
    ├─ YES → Reduce scope (fewer stocks, disable tools)
    └─ NO → Check logs for new error type
        ├─ Timeout → Reduce max_iter and max_retries
        ├─ API errors → Check API keys and rate limits
        └─ Other → Create new issue document
```

## Success Criteria

You'll know it's working when:
1. ✅ Stock crew completes in < 30 minutes
2. ✅ All 4 tasks complete successfully
3. ✅ HTML report is generated
4. ✅ No "Action Input is not a valid key, value dictionary" errors
5. ✅ Logs show tools called individually

## Next Steps

1. **NOW**: Restart stock crew with new environment
2. **Monitor**: Watch for 10-15 minutes
3. **If successful**: Apply fixes to other crews
4. **If still hanging**: Reduce scope and retry
5. **Document**: Update status in CURRENT_STATUS.md

---

**Date**: 2025-01-10
**Priority**: Restart stock crew execution first
**Expected**: Should work with all fixes in place
