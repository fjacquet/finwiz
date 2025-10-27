---
title: "Flow Sequence"
description: "Archived documentation for Flow Sequence"
category: "archive"
tags:
  - "archive"
date: "2025-10-26"
source: "archive/FLOW_SEQUENCE.md"
---

# FinWiz Flow Sequence Documentation

[TOC]

## Overview

This document describes the corrected 6-phase flow sequence for FinWiz, explaining the logical business order and rationale for each phase.

## Flow Diagram

```text
┌─────────────────────────────────────────────────────────────────┐
│                         FINWIZ FLOW                              │
│                    (6-Phase Architecture)                        │
└─────────────────────────────────────────────────────────────────┘

Phase 1: Data Validation
┌──────────────────────────────────────┐
│  validate_data_integration (START)   │
│  - Check API keys                    │
│  - Verify data sources               │
│  - Validate system health            │
└──────────────┬───────────────────────┘
               │
               ▼
Phase 2: Portfolio Analysis (Analyze What You Have)
┌──────────────────────────────────────┐
│  check_portfolio                     │
│  - Load portfolio holdings           │
│  - Generate initial review           │
│  - Identify holdings for analysis    │
└──────────────┬───────────────────────┘
               │
               ▼
Phase 3: Deep Analysis & Update (Evaluate & Merge - ATOMIC)
┌──────────────────────────────────────┐
│  analyze_and_update_portfolio        │
│  ├─ Deep Analysis                    │
│  │  └─ DeepAnalysisCrew per holding  │
│  │     - Grade: A+ to F              │
│  │     - Composite scores            │
│  ├─ Match Alternatives               │
│  │  └─ Find replacements (grade < B) │
│  └─ Update Portfolio (ONCE)          │
│     └─ Merge analysis + alternatives │
└──────────────┬───────────────────────┘
               │
               ▼
Phase 4: Discovery (Find New Opportunities)
┌──────────────────────────────────────┐
│  Discovery Crews (Parallel)          │
│  ├─ check_crypto                     │
│  ├─ check_stock                      │
│  └─ check_etf                        │
│     └─ Find "top 10" candidates      │
│                                      │
│  check_investment_discovery          │
│  └─ Consolidate discoveries          │
│  └─ Find A+ opportunities            │
│  └─ Validate through backtesting     │
└──────────────┬───────────────────────┘
               │
               ▼
Phase 5: Rebalancing (Optimize Allocations)
┌──────────────────────────────────────┐
│  check_portfolio_rebalancing         │
│  - Generate trade recommendations    │
│  - Optimize allocations              │
│  - Include A+ opportunities          │
└──────────────┬───────────────────────┘
               │
               ▼
Phase 6: Reporting (Consolidate & Present)
┌──────────────────────────────────────┐
│  pre_validate_reporter_input         │
│  └─ Validate report inputs           │
│                                      │
│  report                              │
│  └─ Generate final HTML report       │
└──────────────────────────────────────┘
```text
## Phase Details

### Phase 1: Data Validation

**Purpose:** Ensure all data systems are operational before analysis begins.

**Activities:**
- Validate API keys (OpenAI, Serper, Alpha Vantage, etc.)
- Check data source availability
- Verify system health
- Initialize caching and logging

**Output:** System health status

**Why First:** No point analyzing if data sources are unavailable.

---

### Phase 2: Portfolio Analysis

**Purpose:** Analyze what you currently own.

**Activities:**
- Load portfolio holdings from CSV files
- Generate initial portfolio review
- Identify holdings that need deep analysis
- Calculate basic portfolio metrics

**Output:** Initial portfolio review with holdings list

**Why Second:** You need to know what you own before evaluating it.

---

### Phase 3: Deep Analysis & Update (ATOMIC OPERATION)

**Purpose:** Grade holdings, find alternatives, and update portfolio in one atomic operation.

**Activities:**

**3.1 Deep Analysis:**
- Run `DeepAnalysisCrew` on each holding
- Assign grades (A+ to F) based on composite scores
- Calculate fundamental, technical, and risk scores
- Cache results for performance

**3.2 Match Alternatives:**
- Identify underperforming holdings (grade C, D, or F)
- Use `AlternativeFinder` to find better options
- Prioritize A+ candidates from discovery results
- Generate transition strategies

**3.3 Update Portfolio:**
- Regenerate portfolio review with enriched data
- Merge deep analysis results
- Include alternative recommendations
- Update Flow state (ONCE, not twice)

**Output:**
- Deep analysis results per holding
- Alternative recommendations
- Updated portfolio review

**Why Consolidated:**
- ✅ Portfolio generated ONCE (not twice)
- ✅ No race conditions (atomic operation)
- ✅ Simpler dependency chain
- ✅ All-or-nothing semantics

**Why Third:** You need to evaluate what you own before finding new opportunities.

---

### Phase 4: Discovery

**Purpose:** Find NEW investment opportunities across all asset classes.

**Activities:**

**4.1 Discovery Crews (Parallel):**
- `check_crypto` - Find top 10 promising cryptocurrencies
- `check_stock` - Find top 10 promising stocks
- `check_etf` - Find top 10 stable ETFs
- Each crew screens and ranks candidates

**4.2 Investment Discovery:**
- Consolidate discovery results
- Find A+ opportunities
- Validate through backtesting
- Match to portfolio needs identified in Phase 3

**Output:**
- Top 10 candidates per asset class
- A+ opportunities with backtesting validation
- Recommendations matched to portfolio needs

**Why Fourth:**
- Discovery runs AFTER we know what needs improvement
- Alternative matching (Phase 3) identifies needs
- Discovery provides solutions to match those needs
- Avoids discovering assets we already own

---

### Phase 5: Rebalancing

**Purpose:** Optimize portfolio allocations with complete information.

**Activities:**
- Generate trade recommendations
- Optimize allocations
- Include A+ opportunities from discovery
- Calculate position sizing
- Assess rebalancing costs

**Output:**
- Trade recommendations
- Optimized allocations
- Cost analysis

**Why Fifth:**
- Rebalancing needs BOTH portfolio analysis AND discovery results
- Can't optimize without knowing what alternatives exist
- Has complete data (holdings + grades + alternatives + discoveries)

---

### Phase 6: Reporting

**Purpose:** Consolidate all analysis and present recommendations.

**Activities:**
- Validate report inputs
- Generate comprehensive HTML report
- Include all phases' results
- Present in French (default)
- Provide actionable recommendations

**Output:** Final HTML report

**Why Last:** Reporting consolidates everything that came before.

---

## Flow Rationale

### Why Portfolio BEFORE Discovery?

**Logical Business Order:**
1. **Analyze what you have** - Portfolio holdings analysis
2. **Grade your holdings** - Deep analysis assigns grades
3. **Identify needs** - Alternative matching finds what needs replacement
4. **Find solutions** - Discovery provides A+ candidates
5. **Optimize** - Rebalancing with complete information
6. **Present** - Final consolidated report

**Problems with Discovery First (Old Flow):**
- ❌ Discovery runs before knowing what you own
- ❌ Can't match alternatives without discovery results
- ❌ Wasted resources (may discover assets you already own)
- ❌ Rebalancing lacks context (runs in parallel with discovery)

**Benefits of Portfolio First (New Flow):**
- ✅ Logical business process
- ✅ Alternative matching identifies needs
- ✅ Discovery provides solutions
- ✅ Rebalancing has complete data
- ✅ No wasted effort

### Why Consolidated Atomic Operation?

**Old Flow (3 Separate Methods):**
```text
1. analyze_holdings_deep()
2. match_alternatives()
3. update_portfolio_review_with_deep_analysis()
```text
**Problems:**
- Portfolio review generated TWICE (inefficient)
- Race conditions (discovery could start before portfolio update)
- Complex dependency chains (3 @listen decorators)

**New Flow (1 Atomic Method):**
```text
analyze_and_update_portfolio()
├─ Deep analysis
├─ Match alternatives
└─ Update portfolio (ONCE)
```text
**Benefits:**
- ✅ Portfolio generated ONCE
- ✅ No race conditions
- ✅ Simpler dependency chain
- ✅ Atomic semantics (all-or-nothing)

## Crew Routing Logic

### Discovery Crews vs Deep Analysis Crew

| Feature | Discovery Crews | DeepAnalysisCrew |
|---------|----------------|------------------|
| **Purpose** | Screen and find "top 10" | Analyze ONE specific ticker |
| **Input** | Screening criteria | ticker + asset_class |
| **Output** | List of opportunities | DeepAnalysisResult with grade |
| **Use Case** | Investment discovery | Portfolio holdings evaluation |
| **When** | Phase 4 (Discovery) | Phase 3 (Deep Analysis) |

### When to Use Each

**Use DeepAnalysisCrew when:**
- ✅ Analyzing specific tickers you already own
- ✅ Evaluating individual portfolio holdings
- ✅ Making keep/sell decisions
- ✅ Getting detailed grades (A+ to F)

**Use Discovery Crews when:**
- ✅ Finding NEW investment opportunities
- ✅ Screening for "top 10" candidates
- ✅ Discovering assets you don't own
- ✅ Comparative analysis across multiple assets

## Implementation Details

### Flow Listener Decorators

```pythonthon
# Phase 1: Validation
@start()
def validate_data_integration(self):
    pass

# Phase 2: Portfolio Analysis
@listen("validate_data_integration")
def check_portfolio(self):
    pass

# Phase 3: Deep Analysis & Update (ATOMIC)
@listen("check_portfolio")
def analyze_and_update_portfolio(self) -> dict[str, Any]:
    # Consolidated operation
    deep_results = self._run_deep_analysis_on_holdings()
    alternatives = self._match_alternatives_for_holdings(deep_results)
    portfolio_updated = self._update_portfolio_review_with_enriched_data()
    return consolidated_results

# Phase 4: Discovery (Parallel)
@listen("analyze_and_update_portfolio")
def check_crypto(self):
    pass

@listen("analyze_and_update_portfolio")
def check_stock(self):
    pass

@listen("analyze_and_update_portfolio")
def check_etf(self):
    pass

@listen(and_("check_crypto", "check_stock", "check_etf"))
def check_investment_discovery(self):
    pass

# Phase 5: Rebalancing
@listen("check_investment_discovery")
def check_portfolio_rebalancing(self):
    pass

# Phase 6: Reporting
@listen("check_portfolio_rebalancing")
def pre_validate_reporter_input(self):
    pass

@listen("pre_validate_reporter_input")
def report(self):
    pass
```text
### Data Flow

```text
validate_data_integration
    ↓ (system health)
check_portfolio
    ↓ (portfolio review)
analyze_and_update_portfolio
    ↓ (deep analysis + alternatives + updated portfolio)
check_crypto, check_stock, check_etf (parallel)
    ↓ (discovery results)
check_investment_discovery
    ↓ (A+ opportunities)
check_portfolio_rebalancing
    ↓ (trade recommendations)
pre_validate_reporter_input
    ↓ (validated inputs)
report
    ↓ (final HTML report)
```text
## Performance Considerations

### Execution Time

**Phase 1:** < 10 seconds (validation)
**Phase 2:** 30-60 seconds (portfolio analysis)
**Phase 3:** 2-5 minutes per holding (deep analysis)
**Phase 4:** 3-5 minutes per crew (discovery)
**Phase 5:** 1-2 minutes (rebalancing)
**Phase 6:** 30-60 seconds (reporting)

**Total:** 10-20 minutes for complete flow (depends on portfolio size)

### Optimization

**Parallel Execution:**
- Discovery crews run in parallel (Phase 4)
- Deep analysis tasks use async execution

**Caching:**
- Deep analysis results cached (24 hours default)
- Discovery results cached (72 hours default)
- Portfolio review cached (168 hours default)

**API Efficiency:**
- Smart batching of indicator requests
- Context sharing between tasks
- Fresh data validation

## Troubleshooting

### Flow Not Executing in Correct Order

**Check listener decorators:**
```bash
# Verify @listen decorators match flow sequence
grep -n "@listen" src/finwiz/flows/flow_orchestrator.py
```text
### Portfolio Generated Twice

**Symptom:** Portfolio review appears twice in logs

**Cause:** Old flow methods not removed

**Solution:** Ensure only `analyze_and_update_portfolio()` generates portfolio

### Discovery Running Before Portfolio

**Symptom:** Discovery crews execute before portfolio analysis

**Cause:** Incorrect @listen decorators

**Solution:** Discovery crews should listen to `"analyze_and_update_portfolio"`, not `"validate_data_integration"`

## Summary

The corrected 6-phase flow follows logical business order:

1. **Validate** - Check data systems
2. **Portfolio** - Analyze what you have
3. **Deep Analysis** - Grade holdings, match alternatives, update portfolio (ATOMIC)
4. **Discovery** - Find A+ opportunities for identified needs
5. **Rebalancing** - Optimize with complete data
6. **Reporting** - Present recommendations

**Key Improvements:**
- ✅ Portfolio BEFORE discovery (logical order)
- ✅ Consolidated atomic operation (efficiency)
- ✅ Portfolio generated ONCE (not twice)
- ✅ No race conditions (sequential dependencies)
- ✅ Complete data for rebalancing (portfolio + discoveries)

---

**Version**: 1.0
**Last Updated**: 2025-01-11
**Status**: Production Ready
