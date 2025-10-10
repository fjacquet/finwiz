# Tool Array Input Issue - Comprehensive Fix

## Problem

The agent persistently tries to pass JSON arrays to tools instead of calling them individually:

```
Error: the Action Input is not a valid key, value dictionary.
```

### Example of Incorrect Behavior

Agent tries to pass:
```json
[
  {"ticker": "AAPL", "form_type": "10-K", ...},
  {"ticker": "MSFT", "form_type": "10-K", ...}
]
```

But tools expect individual calls:
```python
tool(ticker="AAPL", form_type="10-K", ...)
tool(ticker="MSFT", form_type="10-K", ...)
```

## Root Cause

The agent is trying to be "efficient" by batch processing all tickers in one tool call. However:

1. **CrewAI tools don't support batch processing** - Each tool call must have individual parameters
2. **Tools expect key-value parameters** - Not JSON strings or arrays
3. **Agent needs explicit instructions** - Without clear guidance, it defaults to batch processing

## Comprehensive Solution

### 1. Added Prominent Warnings

Added critical tool usage rules at the top of both tasks:

```yaml
⚠️ CRITICAL TOOL USAGE RULES ⚠️
- NEVER pass JSON arrays or multiple tickers to tools
- ALWAYS call each tool ONCE PER TICKER individually
- Use the exact parameter names and formats shown in the instructions below
- Tools expect individual parameters, NOT JSON strings or arrays
```

### 2. Explicit Tool Usage Instructions

Added detailed instructions for EVERY tool in BOTH tasks:

**technical_detail_task**:
- Enhanced SEC Analysis Tool
- Quantitative Analysis Tool

**stock_risk_assessment_task**:
- Enhanced SEC Analysis Tool
- Standardized Risk Scoring Tool
- Quantitative Analysis Tool
- Standardized Sentiment Analysis Tool

### 3. Example Parameters for Each Tool

**Enhanced SEC Analysis Tool**:
```yaml
- ticker: "AAPL" (one ticker at a time)
- form_type: "10-K"
- sections: ["Item 1", "Item 1A", "Item 7"]
- risk_assessment: true
- include_perplexity: true
```

**Quantitative Analysis Tool**:
```yaml
- symbol: "AAPL" (one ticker at a time)
- asset_class: "stock"
- analysis_type: "comprehensive"
- timeframe: "1y"
- strategy: "sma_crossover"
```

**Standardized Risk Scoring Tool**:
```yaml
- symbol: "AAPL" (one ticker at a time)
- asset_class: "stock"
- risk_factors: ["list", "of", "identified", "risks"]
```

**Standardized Sentiment Analysis Tool**:
```yaml
- symbol: "AAPL" (one ticker at a time)
- asset_class: "stock"
- max_articles: 50
- days_back: 90
- include_trending: true
```

## Why This Keeps Happening

1. **Agent Optimization**: The LLM tries to optimize by processing multiple items at once
2. **Lack of Context**: Without explicit instructions, the agent doesn't know tool limitations
3. **Pattern Matching**: The agent sees arrays in context and tries to pass them to tools
4. **Insufficient Guidance**: Generic instructions aren't enough - need specific examples

## Prevention Strategy

### For Future Tasks

When creating new tasks that use tools:

1. ✅ Add prominent tool usage warnings at the top
2. ✅ Provide explicit parameter examples for each tool
3. ✅ Emphasize "ONCE PER TICKER" or "ONCE PER ITEM"
4. ✅ Show exact parameter names and formats
5. ✅ Warn against JSON arrays and batch processing

### Template for Tool Instructions

```yaml
X. Tool Name: Use the "Tool Name" with intelligent interpretation:
   - IMPORTANT: Call the tool ONCE PER TICKER with these parameters:
     * parameter1: "value" (one at a time)
     * parameter2: "value"
     * parameter3: value
   - [Additional guidance about using the tool]
```

## Files Modified

- `src/finwiz/crews/stock_crew/config/tasks.yaml`
  - Added warnings to both technical_detail_task and stock_risk_assessment_task
  - Added explicit instructions for all 4 tools used across both tasks

## Expected Behavior

After these fixes:
- ✅ Agent calls tools individually for each ticker
- ✅ Agent uses correct parameter names and formats
- ✅ No JSON array errors
- ✅ Tools execute successfully for each stock
- ✅ Tasks complete without hanging

## Testing

Monitor execution logs for:
- No "Action Input is not a valid key, value dictionary" errors
- Tools called with individual parameters
- Successful tool execution for each ticker
- Task completion

---

**Date**: 2025-01-10
**Status**: Comprehensive fix applied
**Lesson**: LLM agents need VERY explicit tool usage instructions with examples
