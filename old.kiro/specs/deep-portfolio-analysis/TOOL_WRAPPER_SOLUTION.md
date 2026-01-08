# Tool Wrapper Solution - Adapting Tools to Handle Malformed Input

## The Right Approach

Instead of fighting the LLM's behavior, we **adapt the tools** to handle the malformed input gracefully.

## Solution: Robust Tool Wrapper

Created a wrapper that intercepts tool calls and fixes common issues:

### What It Does

1. **Detects JSON arrays**: `[{"ticker": "AAPL"}, {...}]`
2. **Extracts first valid item**: Takes the first dict with actual parameters
3. **Parses JSON strings**: Handles stringified JSON
4. **Provides fallback**: Returns empty dict if parsing fails
5. **Logs fixes**: Records what was fixed for debugging

### Implementation

**File**: `src/finwiz/tools/robust_tool_wrapper.py`

```python
class RobustToolWrapper:
    @staticmethod
    def parse_input(raw_input: Any, args_schema: Type[BaseModel]) -> dict[str, Any]:
        # Handle dict, string, list, etc.
        # Extract first valid item from arrays
        # Parse JSON strings
        # Return clean dict
        
    @staticmethod
    def wrap_tool(tool: BaseTool) -> BaseTool:
        # Wrap tool's _run method
        # Fix inputs before execution
        # Handle errors gracefully
```

**Usage**:
```python
from finwiz.tools.robust_tool_wrapper import make_tools_robust

# Wrap all tools
raw_tools = get_stock_crew_tools()
tools = make_tools_robust(raw_tools)
```

### How It Works

**Before** (fails):
```
LLM passes: [{"ticker": "AAPL", "form_type": "10-K"}, {"ticker": "MSFT", ...}]
Tool receives: Array (invalid)
Result: Error - "Action Input is not a valid key, value dictionary"
```

**After** (succeeds):
```
LLM passes: [{"ticker": "AAPL", "form_type": "10-K"}, {"ticker": "MSFT", ...}]
Wrapper extracts: {"ticker": "AAPL", "form_type": "10-K"}
Tool receives: Clean dict (valid)
Result: Success - Tool executes with first item
```

## Benefits

1. **No LLM Changes Needed**: Works with existing LLM behavior
2. **Transparent**: Tools work normally, wrapper is invisible
3. **Robust**: Handles multiple malformed input patterns
4. **Logged**: Records all fixes for debugging
5. **Scalable**: Apply to all tools with one function call

## Files Created

- `src/finwiz/tools/robust_tool_wrapper.py` - Main wrapper implementation
- `src/finwiz/tools/tool_input_fixer.py` - Alternative simpler implementation

## Files Modified

- `src/finwiz/crews/stock_crew/stock_crew.py` - Applied wrapper to tools
- `src/finwiz/tools/enhanced_sec_tool.py` - Added kwargs handling

## Next Steps

1. **Test with stock crew** - Verify wrapper works
2. **Apply to other crews** - Crypto, ETF, Report
3. **Monitor logs** - Check what inputs are being fixed
4. **Refine as needed** - Add more patterns if discovered

## Why This Works

The wrapper acts as a **translation layer** between the LLM's output and the tool's expected input:

```
LLM → Malformed Input → Wrapper → Clean Input → Tool → Result
```

This is much more reliable than trying to teach the LLM to format inputs correctly.

## Limitations

- **Only processes first item**: If LLM passes array of 10 items, only first is used
- **May lose data**: Other items in array are discarded
- **Not perfect**: Some edge cases may still fail

## Future Improvements

1. **Batch processing**: Process all items in array, not just first
2. **Smart selection**: Choose best item from array based on completeness
3. **Validation**: Verify extracted params match schema before calling tool
4. **Metrics**: Track how often fixes are needed

---

**Date**: 2025-01-10
**Status**: Implemented and ready to test
**Impact**: Should eliminate "Action Input is not a valid key, value dictionary" errors
