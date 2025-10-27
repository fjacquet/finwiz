---
title: "Corrected Flow Sequence"
description: "Archived documentation for Corrected Flow Sequence"
category: "archive"
tags:
  - "archive"
date: "2025-10-26"
source: "archive/implementation_summaries/corrected_flow_sequence.md"
---

# Corrected Flow Sequence - Logical Business Order

[TOC]

## Business Logic Flow (What Makes Sense)

1. **Validate Input** - Check data integration
2. **Analyze Portfolio** - Deep analysis of existing holdings (stocks, ETFs, crypto)
3. **Find Alternatives** - Replace underperforming holdings (grade C, D, F)
4. **Discover New Opportunities** - Find new A+ investments to add
5. **Propose Rebalancing** - Optimize portfolio allocation
6. **Present Report** - Consolidated recommendations

## Current Implementation (WRONG)

```mermaid
graph TD
    A[validate_data_integration] --> B[check_crypto]
    A --> C[check_stock]
    A --> D[check_etf]
    B --> E[check_portfolio]
    C --> E
    D --> E
    E --> F[analyze_holdings_deep]
    F --> G[match_alternatives]
    G --> H[update_portfolio_review]
    B --> I[check_portfolio_rebalancing]
    C --> I
    D --> I
    G --> J[check_investment_discovery]
    I --> J
    J --> K[pre_validate_reporter_input]
    K --> L[report]
```text
**Problems:**
- Discovery crews (check_crypto, check_stock, check_etf) run BEFORE portfolio analysis
- These are meant to find NEW opportunities, not analyze existing holdings
- Logically backwards: we discover new stuff before analyzing what we have

## Corrected Implementation (RIGHT)

```mermaid
graph TD
    A[validate_data_integration] --> B[check_portfolio]
    B --> C[analyze_and_update_portfolio]
    C --> D[check_crypto]
    C --> E[check_stock]
    C --> F[check_etf]
    D --> G[check_investment_discovery]
    E --> G
    F --> G
    G --> H[check_portfolio_rebalancing]
    H --> I[pre_validate_reporter_input]
    I --> J[report]
```text
**Benefits:**
- Portfolio analysis happens FIRST (analyze what you have)
- Discovery happens AFTER (find what you could add)
- Rebalancing happens LAST (optimize everything together)
- Logical, intuitive flow

## Detailed Flow Steps

### Step 1: Validate Data Integration
```pythonthon
@start()
def validate_data_integration(self) -> dict[str, Any]:
    """Validate data integration system before crew execution."""
```text
### Step 2: Check Portfolio (Initial Review)
```pythonthon
@listen("validate_data_integration")
def check_portfolio(self) -> dict[str, Any]:
    """Generate initial portfolio review of existing holdings."""
    # Generates portfolio review WITHOUT deep analysis
    out_path = run_portfolio_review(flow_state=None)
```text
### Step 3: Analyze and Update Portfolio (Deep Analysis + Alternatives)
```pythonthon
@listen("check_portfolio")
def analyze_and_update_portfolio(self) -> dict[str, Any]:
    """
    Perform deep analysis on holdings, match alternatives, update portfolio.

    This consolidates:
    1. Deep crew analysis on each holding (DeepAnalysisCrew)
    2. Alternative matching for underperforming holdings (grade C, D, F)
    3. Portfolio review regeneration with enriched data
    """
    deep_results = self._run_deep_analysis_on_holdings()
    alternatives = self._match_alternatives_for_holdings(deep_results)
    portfolio_updated = self._update_portfolio_review_with_enriched_data()

    return {
        "deep_analysis_complete": True,
        "analysis_results": deep_results,
        "alternatives_data": alternatives,
        "portfolio_updated": portfolio_updated
    }
```text
### Step 4: Discovery Crews (Find New Opportunities)
```pythonthon
@listen("analyze_and_update_portfolio")
def check_crypto(self) -> dict[str, Any]:
    """Discover top 10 crypto opportunities."""
    # Discovery crew - finds NEW opportunities to add

@listen("analyze_and_update_portfolio")
def check_stock(self) -> dict[str, Any]:
    """Discover top 10 stock opportunities."""
    # Discovery crew - finds NEW opportunities to add

@listen("analyze_and_update_portfolio")
def check_etf(self) -> dict[str, Any]:
    """Discover top 10 ETF opportunities."""
    # Discovery crew - finds NEW opportunities to add
```text
### Step 5: Investment Discovery (Consolidate Opportunities)
```pythonthon
@listen(and_("check_crypto", "check_stock", "check_etf"))
def check_investment_discovery(self) -> dict[str, Any]:
    """Consolidate discovery results into investment opportunities."""
    # Combines results from all discovery crews
```text
### Step 6: Portfolio Rebalancing
```pythonthon
@listen("check_investment_discovery")
def check_portfolio_rebalancing(self) -> dict[str, Any]:
    """Propose portfolio rebalancing with existing + new opportunities."""
    # Now has BOTH:
    # - Portfolio analysis with alternatives
    # - Discovery results with new opportunities
```text
### Step 7: Pre-Validate Reporter Input
```pythonthon
@listen("check_portfolio_rebalancing")
def pre_validate_reporter_input(self) -> dict[str, Any]:
    """Validate and prepare data for final report."""
```text
### Step 8: Generate Report
```pythonthon
@listen("pre_validate_reporter_input")
def report(self) -> dict[str, Any]:
    """Generate final consolidated report."""
```text
## Key Changes Required

### Change 1: Move Discovery Crews
```pythonthon
# BEFORE: Discovery runs first
@listen("validate_data_integration")
def check_crypto(self) -> dict[str, Any]:

# AFTER: Discovery runs after portfolio analysis
@listen("analyze_and_update_portfolio")
def check_crypto(self) -> dict[str, Any]:
```text
### Change 2: Update check_portfolio Listener
```pythonthon
# BEFORE: Waits for discovery crews
@listen(and_("check_stock", "check_etf", "check_crypto"))
def check_portfolio(self) -> dict[str, Any]:

# AFTER: Runs right after validation
@listen("validate_data_integration")
def check_portfolio(self) -> dict[str, Any]:
```text
### Change 3: Update check_portfolio_rebalancing Listener
```pythonthon
# BEFORE: Runs in parallel with portfolio analysis
@listen(and_("check_stock", "check_etf", "check_crypto"))
def check_portfolio_rebalancing(self) -> dict[str, Any]:

# AFTER: Runs after discovery consolidation
@listen("check_investment_discovery")
def check_portfolio_rebalancing(self) -> dict[str, Any]:
```text
### Change 4: Update check_investment_discovery Listener
```pythonthon
# BEFORE: Waits for alternatives + rebalancing
@listen(and_("match_alternatives", "check_portfolio_rebalancing"))
def check_investment_discovery(self) -> dict[str, Any]:

# AFTER: Waits for all discovery crews
@listen(and_("check_crypto", "check_stock", "check_etf"))
def check_investment_discovery(self) -> dict[str, Any]:
```text
## Benefits of Corrected Flow

1. **Logical Order** - Analyze what you have before looking for new things
2. **Better Context** - Discovery crews can use portfolio analysis results
3. **Smarter Rebalancing** - Has both portfolio analysis AND discovery results
4. **Clearer Intent** - Each step builds on previous steps
5. **No Confusion** - Discovery crews clearly run for finding NEW opportunities

## Implementation Impact

### Files to Update
- `src/finwiz/flows/flow_orchestrator.py` - Update all @listen decorators
- `.kiro/specs/deep-analysis-crews/requirements.md` - Update flow requirements
- `.kiro/specs/deep-analysis-crews/design.md` - Update architecture diagrams
- `.kiro/specs/deep-analysis-crews/tasks.md` - Add new task for flow reordering
- `crewai_flow.html` - Update flow diagram

### Testing Impact
- Integration tests need to verify new execution order
- Ensure discovery crews receive portfolio context
- Verify rebalancing has access to both portfolio + discovery data

## Summary

**Old Flow:** Discovery → Portfolio → Alternatives → Rebalancing → Report
**New Flow:** Portfolio → Alternatives → Discovery → Rebalancing → Report

This matches the logical business process and makes the system much more intuitive!
