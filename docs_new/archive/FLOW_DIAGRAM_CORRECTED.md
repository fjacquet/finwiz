---
title: "Flow Diagram Corrected"
description: "Archived documentation for Flow Diagram Corrected"
category: "archive"
tags:
  - "archive"
date: "2025-10-26"
source: "archive/FLOW_DIAGRAM_CORRECTED.md"
---

# FinWiz Flow Diagram - Corrected 6-Phase Sequence

[TOC]

## Overview

This document describes the corrected CrewAI Flow sequence for FinWiz, which now follows the logical business process: analyze what you have → grade holdings → find alternatives → discover new opportunities → optimize allocations → present recommendations.

## Flow Diagram

```text
┌─────────────────────────────────────────────────────────────────┐
│ Phase 1: Data Validation                                        │
│ validate_data_integration (@start)                              │
│ - Check data availability and freshness                         │
│ - Validate integration system is operational                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ Phase 2: Portfolio Analysis                                     │
│ check_portfolio (@listen("validate_data_integration"))          │
│ - Analyze what you currently own                                │
│ - Generate initial portfolio review WITHOUT deep analysis       │
│ - Identify holdings that need evaluation                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ Phase 3: Deep Analysis & Update (Atomic Operation)              │
│ analyze_and_update_portfolio (@listen("check_portfolio"))       │
│ - Deep analysis on each holding (DeepAnalysisCrew)              │
│ - Match alternatives for underperformers (grade C, D, F)        │
│ - Update portfolio review with enriched data (ONCE)             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ Phase 4: Discovery (Parallel Execution)                         │
│ ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│ │ check_crypto    │  │ check_stock     │  │ check_etf       │ │
│ │ (@listen        │  │ (@listen        │  │ (@listen        │ │
│ │ "analyze_and_   │  │ "analyze_and_   │  │ "analyze_and_   │ │
│ │ update_         │  │ update_         │  │ update_         │ │
│ │ portfolio")     │  │ portfolio")     │  │ portfolio")     │ │
│ │                 │  │                 │  │                 │ │
│ │ Top 10 cryptos  │  │ Top 10 stocks   │  │ Top 10 ETFs     │ │
│ └────────┬────────┘  └────────┬────────┘  └────────┬────────┘ │
│          └──────────────┬──────┴──────────────┬────────┘       │
│                         ▼                                       │
│          check_investment_discovery                             │
│          (@listen(and_("check_crypto", "check_stock",           │
│                        "check_etf")))                           │
│          - Consolidate discovery results                        │
│          - Find A+ opportunities across all asset classes       │
│          - Validate through backtesting                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ Phase 5: Rebalancing                                            │
│ check_portfolio_rebalancing                                     │
│ (@listen("check_investment_discovery"))                         │
│ - Generate trade recommendations with complete data             │
│ - Optimize allocations (portfolio + A+ discoveries)             │
│ - Calculate price targets and position sizing                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ Phase 6: Reporting                                              │
│ pre_validate_reporter_input                                     │
│ (@listen("check_portfolio_rebalancing"))                        │
│ - Validate all data available for report generation             │
│ - Consolidate data from all previous phases                     │
│          │                                                       │
│          ▼                                                       │
│ report (@listen("pre_validate_reporter_input"))                 │
│ - Generate comprehensive HTML report in French                  │
│ - Present actionable recommendations                            │
└─────────────────────────────────────────────────────────────────┘
```text
## Flow Rationale

### Why This Order?

1. **Phase 1: Data Validation**
   - Ensures data systems are operational before starting analysis
   - Identifies any missing or stale data early

2. **Phase 2: Portfolio Analysis**
   - **Analyze what you have FIRST** - You must understand your current holdings before finding alternatives
   - Generates baseline portfolio review without deep analysis
   - Establishes the foundation for improvement

3. **Phase 3: Deep Analysis & Update (Atomic)**
   - **Grade each holding** - Understand which holdings are performing well (A+, A, B) vs underperforming (C, D, F)
   - **Identify needs** - Alternative matching identifies which holdings need replacement
   - **Update portfolio ONCE** - Atomic operation ensures portfolio is generated once with complete data
   - **Happens BEFORE discovery** - We need to know what we're looking for before running discovery

4. **Phase 4: Discovery (Parallel)**
   - **Find solutions for identified needs** - Discovery crews find A+ opportunities to address the needs identified in Phase 3
   - **Runs AFTER we know what we need** - Discovery is targeted, not blind
   - **Parallel execution** - Crypto, stock, and ETF discovery run simultaneously for efficiency
   - **Consolidation** - Investment discovery consolidates results and validates through backtesting

5. **Phase 5: Rebalancing**
   - **Optimize with complete information** - Has access to both portfolio analysis (Phase 2-3) AND discovery results (Phase 4)
   - **Generate trade recommendations** - Knows what to sell (underperformers) and what to buy (A+ discoveries)
   - **Calculate allocations** - Optimizes portfolio with full context

6. **Phase 6: Reporting**
   - **Present comprehensive recommendations** - Has access to all data from previous phases
   - **Actionable insights** - User receives complete picture with clear next steps

## Key Improvements Over Previous Flow

### ❌ Old Flow (Incorrect)
```text
validate → discovery (crypto/stock/etf) → portfolio → deep_analysis → alternatives → update → rebalancing → report
```text
**Problems:**
- Discovery ran BEFORE portfolio analysis (backwards)
- Couldn't find alternatives (discovery hadn't run yet)
- Portfolio generated TWICE (inefficient)
- Rebalancing lacked context (ran in parallel with discovery)

### ✅ New Flow (Correct)
```text
validate → portfolio → deep_analysis_and_update → discovery → rebalancing → report
```text
**Benefits:**
- Logical business order (analyze → grade → find alternatives → discover → optimize → report)
- Portfolio generated ONCE (atomic operation)
- Discovery targeted (knows what to look for)
- Rebalancing has complete data (portfolio + discoveries)
- No race conditions

## Execution Flow

### Sequential Phases
1. Phase 1 → Phase 2 → Phase 3 (sequential)
2. Phase 3 → Phase 4 (parallel discovery crews)
3. Phase 4 → Phase 5 → Phase 6 (sequential)

### Parallel Execution
- **Phase 4 only**: check_crypto, check_stock, check_etf run in parallel
- All other phases are sequential

### Atomic Operations
- **Phase 3**: Deep analysis + alternatives + portfolio update (all-or-nothing)

## Data Flow

### Phase 1 → Phase 2
- Data availability report
- Stale data warnings
- Refresh recommendations

### Phase 2 → Phase 3
- Portfolio review with holdings
- Holdings requiring deep analysis

### Phase 3 → Phase 4
- Deep analysis results (grades for each holding)
- Identified needs (holdings requiring alternatives)
- Updated portfolio review

### Phase 4 → Phase 5
- Discovery results (top 10 per asset class)
- A+ opportunities
- Backtesting validation

### Phase 5 → Phase 6
- Trade recommendations
- Price targets
- Position sizing
- Allocation optimization

### Phase 6 → Output
- Comprehensive HTML report
- Actionable recommendations
- Complete analysis summary

## Listener Decorator Summary

| Method | Listener | Triggers |
|--------|----------|----------|
| `validate_data_integration` | `@start()` | `check_portfolio` |
| `check_portfolio` | `@listen("validate_data_integration")` | `analyze_and_update_portfolio` |
| `analyze_and_update_portfolio` | `@listen("check_portfolio")` | `check_crypto`, `check_stock`, `check_etf` |
| `check_crypto` | `@listen("analyze_and_update_portfolio")` | `check_investment_discovery` |
| `check_stock` | `@listen("analyze_and_update_portfolio")` | `check_investment_discovery` |
| `check_etf` | `@listen("analyze_and_update_portfolio")` | `check_investment_discovery` |
| `check_investment_discovery` | `@listen(and_("check_crypto", "check_stock", "check_etf"))` | `check_portfolio_rebalancing` |
| `check_portfolio_rebalancing` | `@listen("check_investment_discovery")` | `pre_validate_reporter_input` |
| `pre_validate_reporter_input` | `@listen("check_portfolio_rebalancing")` | `report` |
| `report` | `@listen("pre_validate_reporter_input")` | (end) |

---

**Version:** 1.0
**Date:** 2025-01-11
**Status:** ✅ IMPLEMENTED
