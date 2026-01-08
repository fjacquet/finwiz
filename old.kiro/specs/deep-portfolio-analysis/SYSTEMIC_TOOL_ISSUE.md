# Systemic Tool Usage Issue Across All Crews

## Problem

Agents across **all crews** (stock, crypto, ETF) are consistently trying to pass JSON arrays to tools instead of calling them with individual parameters:

```
Error: the Action Input is not a valid key, value dictionary.
```

### Examples

**Stock Crew**:
```json
[{"ticker": "AAPL", "form_type": "10-K", ...}, {"ticker": "MSFT", ...}]
```

**Crypto Crew**:
```json
[{"file_path": "docs/schemas/CryptoThesis.schema.json"}, {...}]
```

## Root Cause

This is a **fundamental LLM behavior issue**:

1. **LLM Optimization**: The model tries to be "efficient" by batch processing
2. **Pattern Matching**: Sees arrays in context and tries to pass them to tools
3. **Insufficient Guidance**: Generic task descriptions don't prevent this behavior
4. **Tool Interface Confusion**: LLM doesn't understand CrewAI tool calling conventions

## Why This Keeps Happening

Even with explicit instructions like:
```yaml
⚠️ CRITICAL TOOL USAGE RULES ⚠️
- NEVER pass JSON arrays or multiple tickers to tools
- ALWAYS call each tool ONCE PER TICKER individually
```

The LLM still tries to batch process because:
- Instructions are buried in long task descriptions
- LLM prioritizes efficiency over explicit rules
- Tool calling happens at a lower level than task understanding
- The error feedback loop doesn't teach the LLM to change behavior

## Current Status

### Fixed Crews
- ✅ **Stock Crew**: Added explicit tool usage instructions to both tasks

### Needs Fixing
- ❌ **Crypto Crew**: Same issue with "Read a file's content" tool
- ❌ **ETF Crew**: Likely has same issues (not tested yet)
- ❌ **Report Crew**: May have issues if it uses tools

## Potential Solutions

### Option 1: Fix All Crew Configs (Current Approach)
**Pros**: 
- Addresses the issue at the source
- Provides explicit guidance to agents

**Cons**:
- Time-consuming to update all crews
- May not fully prevent the behavior
- Requires maintenance for new crews

### Option 2: Tool Wrapper with Validation
Create a wrapper that validates tool inputs before execution:

```python
class ToolInputValidator:
    def validate_and_call(self, tool, input_data):
        if isinstance(input_data, (list, str)):
            if self._looks_like_json_array(input_data):
                raise ValueError(
                    "Tool does not accept arrays. "
                    "Call the tool once per item individually."
                )
        return tool(**input_data)
```

**Pros**:
- Catches the issue at runtime
- Provides clear error messages
- Works across all crews automatically

**Cons**:
- Requires modifying tool infrastructure
- May break existing functionality

### Option 3: Custom LLM Prompt Engineering
Add system-level instructions to the LLM configuration:

```python
llm = LLM(
    model="gpt-4",
    system_message=(
        "CRITICAL: When using tools, NEVER pass JSON arrays or lists. "
        "Always call tools with individual parameters, one item at a time. "
        "If you need to process multiple items, call the tool multiple times."
    )
)
```

**Pros**:
- Applies to all agents automatically
- Addresses the issue at the LLM level
- Easy to implement

**Cons**:
- May not be strong enough to override LLM behavior
- Could interfere with other LLM capabilities

### Option 4: Reduce Agent Autonomy
Limit what agents can do:

```python
Agent(
    max_iter=10,  # Reduce max iterations
    max_execution_time=300,  # 5 minute timeout
    allow_delegation=False,
    tools=[specific_tool_list],  # Only essential tools
)
```

**Pros**:
- Prevents endless loops
- Forces faster completion

**Cons**:
- May reduce analysis quality
- Doesn't fix the root cause

## Recommended Approach

**Hybrid Solution**:

1. **Immediate**: Add explicit tool instructions to all crew configs (Option 1)
2. **Short-term**: Add system-level LLM prompt (Option 3)
3. **Long-term**: Implement tool input validation (Option 2)

### Implementation Priority

1. ✅ **Stock Crew** - Already fixed
2. 🔄 **Crypto Crew** - Fix next (currently failing)
3. 🔄 **ETF Crew** - Fix after crypto
4. 🔄 **Report Crew** - Check if needed
5. 🔄 **System-level LLM prompt** - Add to `llm_config.py`
6. 🔄 **Tool validation wrapper** - Implement in `tool_factories.py`

## Files to Modify

### Immediate (Crew Configs)
- `src/finwiz/crews/crypto_crew/config/tasks.yaml`
- `src/finwiz/crews/crypto_crew/config/agents.yaml`
- `src/finwiz/crews/etf_crew/config/tasks.yaml`
- `src/finwiz/crews/etf_crew/config/agents.yaml`

### Short-term (LLM Config)
- `src/finwiz/utils/llm_config.py` - Add system message

### Long-term (Tool Infrastructure)
- `src/finwiz/tools/tool_factories.py` - Add validation wrapper
- `src/finwiz/tools/base_tool.py` - Create if needed

## Testing Strategy

After each fix:
1. Run the crew with test inputs
2. Monitor for "Action Input is not a valid key, value dictionary" errors
3. Check that tools are called individually
4. Verify task completion without hanging

## Lessons Learned

1. **LLMs need VERY explicit instructions** - Generic guidance isn't enough
2. **Tool calling is a weak point** - LLMs struggle with tool interfaces
3. **Error feedback doesn't teach** - Failed tool calls don't change behavior
4. **Prevention > Correction** - Better to prevent the issue than handle errors
5. **System-level fixes are better** - Crew-level fixes are maintenance-heavy

---

**Date**: 2025-01-10
**Status**: Systemic issue identified, stock crew fixed, others pending
**Priority**: HIGH - Blocks all crew executions
