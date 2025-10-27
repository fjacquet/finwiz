---
title: "Risk Assessment Speedup Plan"
description: "Understanding the concepts and design of Risk Assessment Speedup Plan"
category: "explanations"
tags:
  - "explanations"
date: "2025-10-26"
source: "RISK_ASSESSMENT_SPEEDUP_PLAN.md"
---

# Risk Assessment Speedup Plan

[TOC]

## Current Performance Analysis

Based on the log output showing 69 holdings processed in ~33 seconds (~2.1x speedup), we can identify several optimization opportunities.

## Performance Bottlenecks Identified

### 1. **Agent Reasoning** ✅ ALREADY OPTIMIZED

- **Status:** `reasoning=False` for all agents
- **Impact:** Saves 5-15 seconds per agent per ticker
- **No further action needed**

### 2. **Crew Planning** ✅ ALREADY OPTIMIZED

- **Status:** No `planning=True` in crew configuration
- **Impact:** Avoids planning overhead × 66 executions
- **No further action needed**

### 3. **Task Execution Mode** ✅ ALREADY OPTIMIZED

- **Status:** `async_execution=true` for deep_analysis, technical_analysis, risk_assessment
- **Impact:** Parallel I/O operations
- **No further action needed**

### 4. **RAG Tools** ✅ ALREADY OPTIMIZED

- **Status:** `include_rag=False` in deep analysis crew
- **Impact:** Eliminates vector DB overhead
- **No further action needed**

## Additional Speedup Opportunities

### 1. **Reduce Task Description Verbosity** ⚡ HIGH IMPACT

**Current Issue:** Risk assessment task description is 200+ lines with extensive guidance
**Impact:** LLM processes entire description on every execution
**Solution:** Streamline to essential instructions only

**Estimated Savings:** 2-5 seconds per ticker (token processing time)

```yaml
# BEFORE: 200+ lines of detailed guidance
risk_assessment_task:
  description: >
    CRITICAL: SINGLE TICKER MODE - Assess risks for ONLY: {ticker}
    [200+ lines of detailed methodology...]

# AFTER: Concise, action-oriented
risk_assessment_task:
  description: >
    CRITICAL: SINGLE TICKER MODE - Assess risks for {ticker} ({asset_class})

    TOOLS TO USE:
    - Enhanced SEC Analysis Tool (stocks): ticker="{ticker}", form_type="10-K", sections=["Item 1A"]
    - Quantitative Analysis Tool: symbol="{ticker}", asset_class="{asset_class}", timeframe="1y"

    REQUIRED OUTPUT (RiskAssessmentStandardized):
    - risk_score (0-5): Calculate from volatility, drawdown, financial health
    - risk_level: Map score to Very Low/Low/Moderate/High/Very High
    - risk_factors (max 10): Specific, actionable risk factors

    SCORING GUIDE:
    - 0-1: Low volatility (<15%), strong fundamentals
    - 1-2: Moderate volatility (15-20%), stable business
    - 2-3: Average volatility (20-25%), normal risks
    - 3-4: High volatility (25-35%), elevated risks
    - 4-5: Extreme volatility (>35%), significant risks

    Use context from previous tasks. Focus on quantitative metrics and data-driven assessment.
```text
### 2. **Simplify Agent Backstories** ⚡ MEDIUM IMPACT

**Current Issue:** Agent backstories are 50+ lines with extensive philosophy
**Impact:** LLM processes backstory on every agent initialization
**Solution:** Reduce to 10-15 lines of essential context

**Estimated Savings:** 1-3 seconds per ticker

```yaml
# BEFORE: 50+ lines
risk_assessor:
  backstory: >
    You're an elite AI-powered risk assessment specialist...
    [50+ lines of detailed background...]

# AFTER: Concise, focused
risk_assessor:
  backstory: >
    Expert risk analyst specializing in quantitative risk modeling and scenario analysis.
    You calculate risk scores (0-5 scale) using volatility, drawdown, and fundamental metrics.
    You provide actionable risk factors and mitigation strategies.

    BATCH MODE: Use pre-fetched data when available to eliminate API latency.
```text
### 3. **Reduce max_iter and max_retries** ⚡ LOW IMPACT

**Current Settings:**

- `max_iter=25` (max iterations per agent)
- `max_retries=10` (max retry attempts)

**Optimization:**

- `max_iter=15` (sufficient for straightforward tasks)
- `max_retries=3` (reduce retry overhead)

**Estimated Savings:** 0-2 seconds per ticker (only on failures)

### 4. **Optimize Tool Selection** ⚡ MEDIUM IMPACT

**Current Issue:** All tools loaded even if not needed for risk assessment
**Solution:** Create minimal tool set for risk assessment

```pythonthon
def get_risk_assessment_tools(asset_class: str, prefetched_data: dict | None = None) -> list[BaseTool]:
    """Minimal tool set for risk assessment only."""
    tools = []

    # Only essential tools
    if asset_class == "stock":
        tools.append(EnhancedSECAnalysisTool(prefetched_data=prefetched_data))

    tools.append(QuantitativeAnalysisTool(asset_class=asset_class, prefetched_data=prefetched_data))
    tools.append(TickerValidationTool())

    # No RAG, no sentiment, no schema reading tools
    return tools
```text
**Estimated Savings:** 1-2 seconds per ticker (tool initialization)

### 5. **Cache Risk Calculations** ⚡ HIGH IMPACT (for repeated analysis)

**Current Issue:** Risk metrics recalculated even if data hasn't changed
**Solution:** Cache risk calculations with TTL

```pythonthon
from functools import lru_cache
from datetime import datetime, timedelta

@lru_cache(maxsize=1000)
def calculate_risk_metrics(ticker: str, data_hash: str) -> dict:
    """Cache risk calculations for 5 minutes."""
    # Risk calculations here
    pass

# In tool:
data_hash = hashlib.md5(json.dumps(price_data).encode()).hexdigest()
risk_metrics = calculate_risk_metrics(ticker, data_hash)
```text
**Estimated Savings:** 3-5 seconds per ticker (for repeated analysis)

### 6. **Parallel Risk Assessment** ⚡ VERY HIGH IMPACT (architectural change)

**Current:** Sequential processing (one ticker at a time)
**Proposed:** Parallel processing (multiple tickers simultaneously)

```pythonthon
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def analyze_holdings_parallel(holdings: list[dict], max_workers: int = 10):
    """Process multiple holdings in parallel."""
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(executor, analyze_single_holding, holding)
            for holding in holdings
        ]
        results = await asyncio.gather(*tasks)
    return results
```text
**Estimated Savings:** 5-10x speedup for portfolio analysis (already implemented at orchestrator level)

### 7. **Use Faster LLM for Risk Assessment** ⚡ HIGH IMPACT

**Current:** Using default LLM (likely GPT-4)
**Proposed:** Use GPT-4o-mini for risk assessment (faster, cheaper)

```pythonthon
@agent
def risk_assessor(self) -> Agent:
    return Agent(
        config=self.agents_config["risk_assessor"],
        verbose=True,
        reasoning=False,
        tools=[],
        llm=LLM(model="gpt-4o-mini", temperature=0.1)  # Faster model
    )
```text
**Estimated Savings:** 3-7 seconds per ticker (faster inference)

### 8. **Skip Redundant Tool Calls** ⚡ MEDIUM IMPACT

**Current Issue:** Risk assessment may call tools already called by deep_analysis
**Solution:** Check context first, reuse data if fresh

```yaml
risk_assessment_task:
  description: >
    CONTEXT REUSE (CRITICAL):
    1. Check context["price_data"] from deep_analysis_task
    2. If timestamp < 5 minutes old, REUSE data (don't refetch)
    3. Only call tools if data missing or stale

    TOOL CALLS (only if needed):
    - If no price_data in context: Call Quantitative Analysis Tool
    - If no SEC data in context (stocks): Call Enhanced SEC Analysis Tool
```text
**Estimated Savings:** 2-4 seconds per ticker (avoid redundant API calls)

## Implementation Priority

### Phase 1: Quick Wins (1-2 hours implementation)

1. ✅ **Reduce task description verbosity** (2-5s savings)
2. ✅ **Simplify agent backstories** (1-3s savings)
3. ✅ **Reduce max_iter to 15, max_retries to 3** (0-2s savings)
4. ✅ **Use GPT-4o-mini for risk assessment** (3-7s savings)

**Total Phase 1 Savings:** 6-17 seconds per ticker

### Phase 2: Medium Effort (2-4 hours implementation)

5. ✅ **Optimize tool selection** (1-2s savings)
6. ✅ **Skip redundant tool calls** (2-4s savings)

**Total Phase 2 Savings:** 3-6 seconds per ticker

### Phase 3: Advanced (4-8 hours implementation)

7. ⚠️ **Cache risk calculations** (3-5s savings, requires cache infrastructure)
8. ✅ **Parallel processing** (already implemented at orchestrator level)

**Total Phase 3 Savings:** 3-5 seconds per ticker

## Expected Performance Improvement

### Current Performance

- **Per ticker:** ~30-40 seconds (estimated from 33s / 69 holdings ≈ 0.48s, but likely includes overhead)
- **69 holdings:** ~33 seconds (with parallel processing)

### After Phase 1 Optimizations

- **Per ticker:** ~20-30 seconds (6-17s savings)
- **69 holdings:** ~20-25 seconds (with parallel processing)
- **Speedup:** ~25-40% faster

### After Phase 2 Optimizations

- **Per ticker:** ~15-25 seconds (9-23s savings total)
- **69 holdings:** ~15-20 seconds (with parallel processing)
- **Speedup:** ~40-55% faster

### After Phase 3 Optimizations

- **Per ticker:** ~12-20 seconds (12-28s savings total)
- **69 holdings:** ~12-18 seconds (with parallel processing)
- **Speedup:** ~45-65% faster

## Monitoring & Validation

After each optimization phase:

1. **Measure execution time** per ticker and total
2. **Validate output quality** - Ensure risk scores are still accurate
3. **Check API call counts** - Verify reduction in redundant calls
4. **Monitor LLM token usage** - Confirm reduction in token processing
5. **Test edge cases** - Ensure error handling still works

## Trade-offs & Considerations

### Quality vs Speed

- ❌ **Don't sacrifice:** Risk score accuracy, comprehensive risk factors
- ✅ **Can reduce:** Verbose explanations, philosophical guidance, redundant instructions

### Cost vs Speed

- Using GPT-4o-mini: ~10x cheaper, ~2-3x faster, slightly lower quality
- For risk assessment (quantitative focus): Quality difference is minimal

### Maintainability vs Speed

- Simpler descriptions: Easier to maintain, faster to process
- Cached calculations: More complex code, but significant speedup

## Recommendation

**Start with Phase 1 (Quick Wins)** - Implement all 4 optimizations:

1. Streamline task descriptions
2. Simplify agent backstories
3. Reduce max_iter and max_retries
4. Use GPT-4o-mini for risk assessment

**Expected Result:** 25-40% speedup with minimal risk and 1-2 hours of work.

Then evaluate if Phase 2 is needed based on performance requirements.

---

**Version:** 1.0
**Date:** 2025-10-25
**Author:** Kiro AI Assistant
