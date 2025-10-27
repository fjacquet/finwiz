---
title: "Crew Schema Fix Summary"
description: "Archived documentation for Crew Schema Fix Summary"
category: "archive"
tags:
  - "archive"
date: "2025-10-26"
source: "archive/fix_reports/CREW_SCHEMA_FIX_SUMMARY.md"
---

# CrewAI Schema Resolution and Output Format Fix

[TOC]

## Date: 2025-10-05

## Problems Solved

### 1. Schema Resolution Issue (KeyError)
**Problem:** All crews were failing to instantiate with `KeyError` for schema class names (e.g., `'CryptoMarketAnalysis'`, `'MarketTrend'`, `'ETFMarketTrend'`, etc.)

**Root Cause:** CrewAI's `map_all_task_variables()` method looks for Pydantic classes marked with `is_output_pydantic` or `is_output_json` attributes. Simply assigning classes as attributes wasn't sufficient.

**Solution:** Import and use CrewAI's `@output_pydantic` and `@output_json` decorators to mark schema classes:

```pythonthon
from crewai.project import CrewBase, agent, crew, output_pydantic, output_json, task

# In __init__ before super().__init__():
self.CryptoMarketAnalysis = output_pydantic(CryptoMarketAnalysis)
self.ReporterInput = output_pydantic(output_json(ReporterInput))  # For JSON-first tasks
```text
**Files Modified:**
- `src/finwiz/crews/crypto_crew/crypto_crew.py`
- `src/finwiz/crews/stock_crew/stock_crew.py`
- `src/finwiz/crews/etf_crew/etf_crew.py`
- `src/finwiz/crews/investment_discovery_crew/investment_discovery_crew.py`
- `src/finwiz/crews/report_crew/report_crew.py`
- `src/finwiz/crews/portfolio_rebalancing_crew/portfolio_rebalancing_crew.py`

**Result:** ✅ All crews now instantiate successfully

---

### 2. LLM Output Wrapping Issue (Pydantic ValidationError)
**Problem:** Agents were returning JSON with wrapper fields (e.g., `{"profiles": [...], "metadata": {...}}`) instead of the expected schema structure, causing Pydantic validation errors with `extra='forbid'`.

**Root Cause:** LLMs naturally tend to wrap outputs in organizational structures, but Pydantic schemas with `extra='forbid'` reject any fields not explicitly defined.

**Solution:** Added explicit "CRITICAL OUTPUT FORMAT" instructions to all task descriptions to guide the LLM:

```yaml
CRITICAL OUTPUT FORMAT:
- Return ONLY the [SchemaName] object directly - do NOT wrap it in additional fields
- Do NOT add wrapper fields like "data", "results", "analysis", etc.
- The JSON must match the [SchemaName] schema exactly

IMPORTANT: Return the object directly without any wrapper fields.
```text
**Tasks Updated (21 total):**

**Crypto Crew** (4 tasks):
- market_analysis_task → CryptoMarketAnalysis
- technical_analysis_task → CryptoTechnicalAnalysis
- risk_assessment_task → CryptoRiskProfile
- investment_strategy_task → CryptoInvestmentStrategy

**Stock Crew** (3 tasks):
- market_technical_analysis_task → MarketTrend
- stock_screening_task → StockScreeningResult
- technical_detail_task → StockTechnicalAnalysis

**ETF Crew** (3 tasks):
- etf_market_trends_task → ETFMarketTrend
- etf_screening_task → ETFScreeningResult
- etf_technical_detail_task → ETFTechnicalAnalysis

**Investment Discovery Crew** (5 tasks):
- etf_discovery_task → APlusDiscoveryResult
- stock_discovery_task → APlusDiscoveryResult
- crypto_discovery_task → APlusDiscoveryResult
- validation_task → ValidationResult
- optimization_task → OptimizationResult

**Portfolio Rebalancing Crew** (5 tasks):
- analyze_holding_task → HoldingDecision
- calculate_price_targets_task → PriceTargets
- find_alternatives_task → Alternative
- portfolio_analysis_task → PortfolioAnalysis
- rebalancing_optimization_task → RebalancingRecommendation

**Report Crew** (3 tasks):
- comprehensive_financial_integration_task → ReporterInput
- optimal_portfolio_allocation_task → PortfolioConfiguration
- risk_assessment_mitigation_task → RiskAssessmentStandardized

**Files Modified:**
- `src/finwiz/crews/crypto_crew/config/tasks.yaml`
- `src/finwiz/crews/stock_crew/config/tasks.yaml`
- `src/finwiz/crews/etf_crew/config/tasks.yaml`
- `src/finwiz/crews/investment_discovery_crew/config/tasks.yaml`
- `src/finwiz/crews/portfolio_rebalancing_crew/config/tasks.yaml`
- `src/finwiz/crews/report_crew/config/tasks.yaml`

**Expected Impact:** These instructions should significantly reduce or eliminate Pydantic validation errors caused by agents wrapping their outputs in unexpected fields.

---

## Testing

All crews instantiate successfully after the fixes:
```bash
✅ CryptoCrew
✅ StockCrew
✅ EtfCrew
✅ InvestmentDiscoveryCrew
✅ PortfolioRebalancingCrew
✅ ReportCrew
```text
## Next Steps

1. Run the full flow with `uv run crewai flow kickoff` to test agent execution
2. Monitor for any remaining Pydantic validation errors
3. If errors persist, add more specific schema examples in task descriptions
4. Consider adding schema validation in pre-execution hooks for early detection

## Technical Details

### CrewAI Schema Resolution Mechanism

CrewAI's `CrewBase.__init__()` calls `map_all_task_variables()` which:
1. Gets all callable attributes via `_get_all_functions()`
2. Filters for those with `is_output_pydantic` or `is_output_json` attributes
3. Builds dictionaries of available schemas
4. Maps YAML `output_pydantic`/`output_json` strings to actual classes

Without the decorators, classes don't have these marker attributes, causing KeyError.

### Pydantic Strict Mode

FinWiz schemas use `model_config = ConfigDict(extra="forbid")` which:
- Rejects any fields not explicitly defined in the schema
- Ensures data integrity and prevents schema drift
- Requires exact schema compliance from LLM outputs

The format instructions guide LLMs to respect this constraint.

---

**Status:** ✅ Complete
**Verified:** 2025-10-05
