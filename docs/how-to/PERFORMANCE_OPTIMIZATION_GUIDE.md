---
title: "Performance Optimization Guide"
description: "Performance optimizations for FinWiz's DeepAnalysisCrew for faster, cost-effective analysis"
category: "how-to"
tags:
  - "performance"
  - "optimization"
  - "configuration"
  - "deep-analysis"
  - "cost-optimization"
date: "2025-10-26"
---

# Performance Optimization Guide

This guide documents the performance optimizations available in FinWiz's DeepAnalysisCrew for faster, more cost-effective analysis.

## Overview

FinWiz includes two configurable performance optimizations for the DeepAnalysisCrew:

1. **Phase 1: GPT-5-mini for Risk Assessment** - Use faster, cheaper LLM for risk calculations
2. **Phase 2: Minimal Tool Set** - Reduce tool initialization overhead for risk assessor

Both optimizations are **enabled by default** and can be configured via environment variables.

## Configuration

### Environment Variables

```bash
# Phase 1: Use GPT-5-mini for risk assessment (default: true)
RISK_ASSESSMENT_USE_MINI=true

# Phase 2: Use minimal tool set for risk assessor (default: true)
USE_MINIMAL_RISK_TOOLS=true
```

### Quick Start

**Default Configuration (Optimized):**

```bash
# Both optimizations enabled (fastest, cheapest)
RISK_ASSESSMENT_USE_MINI=true
USE_MINIMAL_RISK_TOOLS=true
uv run python src/finwiz/main.py --ticker AAPL --asset-class stock
```

**Baseline Configuration (No Optimizations):**

```bash
# Both optimizations disabled (for comparison)
RISK_ASSESSMENT_USE_MINI=false
USE_MINIMAL_RISK_TOOLS=false
uv run python src/finwiz/main.py --ticker AAPL --asset-class stock
```

## Phase 1: GPT-5-mini for Risk Assessment

### Description

The risk assessor agent uses GPT-5-mini instead of the default LLM (GPT-4) for faster, cheaper execution while maintaining accuracy for straightforward risk calculations.

### Benefits

- **Faster Execution**: GPT-5-mini is optimized for speed
- **Lower Cost**: Reduced LLM API costs per analysis
- **Maintained Accuracy**: Risk scores remain consistent for standard calculations

### Implementation

```python
# In src/finwiz/crews/deep_analysis/deep_analysis.py
import os

use_mini = os.getenv("RISK_ASSESSMENT_USE_MINI", "true").lower() == "true"

if use_mini:
    risk_llm = LLM(model="gpt-5-mini")
    logger.info("Risk assessor using GPT-5-mini for faster execution")
else:
    risk_llm = self._get_configured_llm()
    logger.info("Risk assessor using default LLM")
```

### When to Disable

- Complex risk scenarios requiring advanced reasoning
- Regulatory compliance requiring specific model versions
- Comparative analysis with baseline results
- Debugging LLM-related issues

### Configuration

```bash
# Enable (default)
export RISK_ASSESSMENT_USE_MINI=true

# Disable
export RISK_ASSESSMENT_USE_MINI=false
```

## Phase 2: Minimal Tool Set for Risk Assessor

### Description

The risk assessor uses a minimal, focused tool set instead of the full tool set to reduce initialization overhead and improve startup time.

### Benefits

- **Reduced Overhead**: Faster tool initialization
- **Faster Startup**: Quicker agent startup time
- **Focused Tools**: Only essential risk calculation tools loaded

### Minimal Tool Set

The minimal tool set includes only essential tools for risk assessment:

1. **QuantitativeAnalysisTool** - Core risk metrics (VaR, CVaR, volatility, Sharpe ratio)
2. **TickerValidationTool** - Ticker validation
3. **Asset-Specific Tool** - One of:
   - `EnhancedSECAnalysisTool` (for stocks)
   - `EnhancedETFAnalysisTool` (for ETFs)
   - `EnhancedCryptoAnalysisTool` (for crypto)

### Implementation

```python
# In src/finwiz/crews/deep_analysis/deep_analysis.py
def _get_minimal_risk_tools(self, asset_class: str) -> list:
    """Get minimal tool set for risk assessment only."""
    tools = []
    
    # Core risk metrics
    tools.append(QuantitativeAnalysisTool(asset_class=asset_class))
    
    # Ticker validation
    tools.append(TickerValidationTool())
    
    # Asset-specific tool
    if asset_class == "stock":
        tools.append(EnhancedSECAnalysisTool())
    elif asset_class == "etf":
        tools.append(EnhancedETFAnalysisTool())
    elif asset_class == "crypto":
        tools.append(EnhancedCryptoAnalysisTool())
    
    return make_tools_robust(tools)
```

### When to Disable

- Need full tool set for comprehensive analysis
- Debugging tool-related issues
- Comparative analysis with baseline results
- Custom tool requirements

### Configuration

```bash
# Enable (default)
export USE_MINIMAL_RISK_TOOLS=true

# Disable
export USE_MINIMAL_RISK_TOOLS=false
```

## Performance Testing

### Test Scenarios

**Scenario 1: All Optimizations (Fastest)**

```bash
RISK_ASSESSMENT_USE_MINI=true USE_MINIMAL_RISK_TOOLS=true \
  time uv run python src/finwiz/main.py --ticker AAPL --asset-class stock
```

**Scenario 2: Phase 1 Only**

```bash
RISK_ASSESSMENT_USE_MINI=true USE_MINIMAL_RISK_TOOLS=false \
  time uv run python src/finwiz/main.py --ticker AAPL --asset-class stock
```

**Scenario 3: Phase 2 Only**

```bash
RISK_ASSESSMENT_USE_MINI=false USE_MINIMAL_RISK_TOOLS=true \
  time uv run python src/finwiz/main.py --ticker AAPL --asset-class stock
```

**Scenario 4: Baseline (No Optimizations)**

```bash
RISK_ASSESSMENT_USE_MINI=false USE_MINIMAL_RISK_TOOLS=false \
  time uv run python src/finwiz/main.py --ticker AAPL --asset-class stock
```

### Expected Results

| Configuration | Execution Time | Cost | Accuracy |
|--------------|----------------|------|----------|
| All Optimizations | 2-3 min | Low | High |
| Phase 1 Only | 2.5-3.5 min | Low | High |
| Phase 2 Only | 2.5-3.5 min | Medium | High |
| Baseline | 3-4 min | Medium | High |

**Performance Impact:**

- **20-30% reduction** in execution time with all optimizations
- **Lower LLM API costs** with GPT-5-mini
- **Maintained accuracy** for risk calculations

## Validation

### Risk Score Consistency

Compare risk scores between optimized and baseline configurations:

```bash
# Generate optimized results
RISK_ASSESSMENT_USE_MINI=true USE_MINIMAL_RISK_TOOLS=true \
  uv run python src/finwiz/main.py --ticker AAPL --asset-class stock > output_optimized.txt

# Generate baseline results
RISK_ASSESSMENT_USE_MINI=false USE_MINIMAL_RISK_TOOLS=false \
  uv run python src/finwiz/main.py --ticker AAPL --asset-class stock > output_baseline.txt

# Compare risk scores
diff output_optimized.txt output_baseline.txt
```

**Expected Outcome:**

- Risk scores should be within ±0.1 points
- Grades should match (A+, A, B, C, D, F)
- Composite scores should be within ±0.05

### Quality Assurance

**Validation Checklist:**

- [ ] Risk scores consistent between configurations
- [ ] Grades match between configurations
- [ ] Execution time reduced by 20-30%
- [ ] No errors or warnings in logs
- [ ] All tools initialized correctly
- [ ] API calls successful

## Troubleshooting

### Issue: Risk scores differ significantly

**Symptoms:**

- Risk scores differ by >0.2 points between configurations
- Grades don't match (e.g., A+ vs A)

**Solution:**

1. Check logs for errors or warnings
2. Verify API keys are valid
3. Ensure data freshness is consistent
4. Disable optimizations and compare again

### Issue: Performance not improved

**Symptoms:**

- Execution time similar between configurations
- No cost reduction observed

**Solution:**

1. Verify environment variables are set correctly
2. Check logs for optimization status messages
3. Ensure GPT-5-mini is available in your region
4. Monitor API response times

### Issue: Tool initialization errors

**Symptoms:**

- Errors during tool initialization
- Missing tools in minimal set

**Solution:**

1. Disable minimal tools: `USE_MINIMAL_RISK_TOOLS=false`
2. Check tool dependencies are installed
3. Verify asset_class parameter is valid
4. Review logs for specific error messages

## Best Practices

### Production Deployment

**Recommended Configuration:**

```bash
# Enable all optimizations for production
RISK_ASSESSMENT_USE_MINI=true
USE_MINIMAL_RISK_TOOLS=true
```

**Benefits:**

- Faster execution for better user experience
- Lower costs for high-volume analysis
- Maintained accuracy for production use

### Development and Testing

**Recommended Configuration:**

```bash
# Use baseline for development and testing
RISK_ASSESSMENT_USE_MINI=false
USE_MINIMAL_RISK_TOOLS=false
```

**Benefits:**

- Easier debugging with full tool set
- Consistent with historical results
- Better for comparative analysis

### Monitoring

**Key Metrics to Monitor:**

- Execution time per ticker
- LLM API costs
- Risk score consistency
- Error rates
- Tool initialization time

**Logging:**

```python
# Logs indicate optimization status
logger.info("⚡ PHASE 2: Using minimal tool set for risk assessor (3 tools)")
logger.info("Risk assessor using GPT-5-mini for faster execution")
```

## References

- **Implementation Details**: See `PHASE_1_SPEEDUP_IMPLEMENTATION.md` and `PHASE_2_SPEEDUP_IMPLEMENTATION.md`
- **Complete Results**: See `RISK_ASSESSMENT_SPEEDUP_COMPLETE.md`
- **Source Code**: `src/finwiz/crews/deep_analysis/deep_analysis.py`
- **User Guide**: `docs/USER_GUIDE.md` (Deep Analysis Crew section)
- **Developer Guide**: `docs/DEVELOPER_GUIDE.md` (Performance Optimization section)

---

**Version**: 1.0  
**Created**: 2025-01-25  
**Last Updated**: 2025-01-25  
**Status**: Active
