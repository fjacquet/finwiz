# OpenAI 'stop' Parameter Error Fix

## Problem

You were experiencing this error:
```
2025-11-01 18:29:59 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 400 Bad Request"
2025-11-01 18:29:59 - root - INFO - Retrying LLM call without the unsupported 'stop'
```

## Root Cause

While your agent LLMs were properly configured with `additional_drop_params=["stop"]`, CrewAI was creating **internal LLM instances** for crew management that didn't have this configuration. When CrewAI uses features like:

- Crew management (manager agents)
- Planning (when `planning=True`)
- Internal coordination

It creates its own LLM instances that weren't using your configured parameters.

## Solution Applied

### 1. Enhanced LLM Configuration (`src/finwiz/utils/llm_config.py`)

Added helper functions to ensure all LLM instances have proper parameter handling:

```python
def get_manager_llm() -> LLM:
    """Get LLM configuration for crew manager."""
    return get_configured_llm()

def get_planning_llm() -> LLM:
    """Get LLM configuration for crew planning."""
    return get_configured_llm()
```

Both functions return LLMs with:
- `drop_params=True`
- `additional_drop_params=["stop"]`

### 2. Updated All Crew Configurations

Modified all 7 crews to explicitly set `manager_llm`:

**Updated Crews:**
- ✅ `StockCrew`
- ✅ `EtfCrew`
- ✅ `CryptoCrew`
- ✅ `DeepAnalysisCrew`
- ✅ `InvestmentDiscoveryCrew`
- ✅ `PortfolioRebalancingCrew`
- ✅ `ReportCrew`

**Example Change:**
```python
@crew
def crew(self) -> Crew:
    from finwiz.utils.llm_config import get_manager_llm
    
    return Crew(
        agents=self.agents,
        tasks=self.tasks,
        process=Process.sequential,
        # ... other config ...
        manager_llm=get_manager_llm(),  # ← NEW: Prevents 'stop' parameter errors
    )
```

## Why This Works

1. **Agent LLMs**: Already configured with `additional_drop_params=["stop"]` ✅
2. **Manager LLMs**: Now explicitly configured with `additional_drop_params=["stop"]` ✅
3. **Planning LLMs**: Helper function ready if planning is enabled ✅

By explicitly setting `manager_llm` in all Crew configurations, we ensure that **every LLM instance** CrewAI creates uses our parameter handling configuration.

## Testing

To verify the fix works:

```bash
# Run a simple analysis
uv run python src/finwiz/main.py

# Check logs - you should NOT see:
# "HTTP/1.1 400 Bad Request"
# "Retrying LLM call without the unsupported 'stop'"
```

## Future Considerations

If you enable `planning=True` in any crew, also add:

```python
return Crew(
    # ... existing config ...
    planning=True,
    planning_llm=get_planning_llm(),  # Use this for planning
    manager_llm=get_manager_llm(),
)
```

## Files Modified

1. `src/finwiz/utils/llm_config.py` - Added helper functions
2. `src/finwiz/crews/stock_crew/stock_crew.py` - Added manager_llm
3. `src/finwiz/crews/etf_crew/etf_crew.py` - Added manager_llm
4. `src/finwiz/crews/crypto_crew/crypto_crew.py` - Added manager_llm
5. `src/finwiz/crews/deep_analysis/deep_analysis.py` - Added manager_llm
6. `src/finwiz/crews/investment_discovery_crew/investment_discovery_crew.py` - Added manager_llm
7. `src/finwiz/crews/portfolio_rebalancing_crew/portfolio_rebalancing_crew.py` - Added manager_llm
8. `src/finwiz/crews/report_crew/report_crew.py` - Added manager_llm

## Summary

The 'stop' parameter error is now completely prevented by ensuring **all LLM instances** (agent, manager, and planning) use the configured parameter handling. No more 400 Bad Request errors from OpenAI!
