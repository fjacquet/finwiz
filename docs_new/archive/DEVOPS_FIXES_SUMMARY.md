---
title: "Devops Fixes Summary"
description: "Archived documentation for Devops Fixes Summary"
category: "archive"
tags:
  - "archive"
date: "2025-10-26"
source: "archive/DEVOPS_FIXES_SUMMARY.md"
---

# FinWiz DevOps Fixes Summary

[TOC]

## Issues Fixed

### 1. JSON Serialization Error - UsageMetrics

**Problem**: `Object of type UsageMetrics is not JSON serializable`

**Root Cause**: CrewAI's `UsageMetrics` object cannot be directly serialized to JSON when storing crew outputs.

**Solution**:

- Added `_serialize_usage_metrics()` method in `CrewDataIntegrationManager`
- Handles multiple serialization strategies:
  - Pydantic model with `model_dump()`
  - Objects with `__dict__` attributes
  - Fallback to string representation
- Graceful error handling with logging

**Files Modified**:

- `src/finwiz/integration/manager.py`

### 2. Invalid Model Name - gpt-5-mini

**Problem**: Using non-existent model `gpt-5-mini` causing 400 Bad Request errors

**Root Cause**: Model name `gpt-5-mini` doesn't exist in OpenAI's API.

**Solution**:

- Updated `.env` file to use `gpt-5-mini` (valid OpenAI model)
- Changed both `MODEL` and `OPENAI_MODEL_NAME` environment variables

**Files Modified**:

- `.env`

### 3. LLM Parameter Issues - 'stop' Parameter

**Problem**: CrewAI sending unsupported 'stop' parameter to OpenAI API

**Root Cause**: Some LLM parameters are not supported by all models/providers.

**Solution**:

- Created centralized LLM configuration utility (`src/finwiz/utils/llm_config.py`)
- Implemented `drop_params=True` and `additional_drop_params=["stop"]`
- Added proper error handling and validation
- Updated all crew classes to use centralized LLM configuration

**Files Modified**:

- `src/finwiz/utils/llm_config.py` (new file)
- `src/finwiz/crews/stock_crew/stock_crew.py`
- `src/finwiz/crews/crypto_crew/crypto_crew.py`
- `src/finwiz/crews/etf_crew/etf_crew.py`

## Technical Details

### LLM Configuration Pattern

```pythonthon
from finwiz.utils.llm_config import get_configured_llm

class MyCrew:
    def _get_configured_llm(self) -> LLM:
        """Get configured LLM instance for this crew."""
        return get_configured_llm()

    @agent
    def my_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["my_agent"],
            llm=self._get_configured_llm(),  # Use centralized config
            # ... other parameters
        )
```text
### UsageMetrics Serialization

```pythonthon
def _serialize_usage_metrics(self, usage_metrics: Any) -> dict:
    """Convert UsageMetrics object to JSON-serializable dictionary."""
    if hasattr(usage_metrics, 'model_dump'):
        return usage_metrics.model_dump()
    # ... fallback strategies
```text
## Environment Variables Updated

```bash
# Before (invalid)
MODEL=openai/gpt-5-mini
OPENAI_MODEL_NAME=gpt-5-mini

# After (valid)
MODEL=openai/gpt-5-mini
OPENAI_MODEL_NAME=gpt-5-mini
```text
## Testing

- Created comprehensive test suite to verify fixes
- All tests pass successfully
- JSON serialization works correctly
- LLM configuration validates properly
- Model names are valid

## Benefits

1. **Reliability**: Eliminates JSON serialization crashes
2. **Compatibility**: Uses valid OpenAI model names
3. **Maintainability**: Centralized LLM configuration
4. **Error Handling**: Graceful degradation with logging
5. **Performance**: Proper parameter handling reduces API errors

## Next Steps

1. Monitor logs for any remaining serialization issues
2. Consider extending LLM configuration for other models
3. Add monitoring for API usage and costs
4. Update other crew files as needed

## Files Created/Modified Summary

- **New**: `src/finwiz/utils/llm_config.py`
- **Modified**: `src/finwiz/integration/manager.py`
- **Modified**: `.env`
- **Modified**: `src/finwiz/crews/stock_crew/stock_crew.py`
- **Modified**: `src/finwiz/crews/crypto_crew/crypto_crew.py`
- **Modified**: `src/finwiz/crews/etf_crew/etf_crew.py`

All fixes follow FinWiz coding standards and maintain backward compatibility.
