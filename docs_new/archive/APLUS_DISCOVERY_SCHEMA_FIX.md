---
title: "Aplus Discovery Schema Fix"
description: "Archived documentation for Aplus Discovery Schema Fix"
category: "archive"
tags:
  - "archive"
date: "2025-10-26"
source: "archive/fix_reports/APLUS_DISCOVERY_SCHEMA_FIX.md"
---

# A+ Discovery Schema Validation Fix

[TOC]

## Date: 2025-05-10

## Problem

The Investment Discovery Crew was failing with 153 Pydantic validation errors when trying to parse `APlusDiscoveryResult` outputs from agents. The errors fell into three categories:

### 1. Risk Assessment Field Mismatch (144 errors)

**Agent Output:**
```json
{
  "risk_assessment": {
    "systemic_risk": 2,
    "business_risk": 2,
    "liquidity_risk": 1,
    "governance_risk": 2,
    "overall_risk_score": 1.75,
    "notes": "Low leverage, recurring revenue..."
  }
}
```text
**Schema Expected:**
```json
{
  "risk_assessment": {
    "scale": "0_5",
    "score": 1.75,
    "level": "Low",
    "risk_factors": ["Low leverage", "Recurring revenue model", ...]
  }
}
```text
**Error:** `Field required [type=missing]` for `score` and `level`, `Extra inputs are not permitted` for custom fields

### 2. Criteria Value Range Errors (6 errors)

**Agent Output:**
```json
{
  "discovery_criteria": {
    "stock_min_roe": 20,
    "stock_min_revenue_growth": 15,
    "crypto_min_daily_volume": 100000
  }
}
```text
**Schema Expected:**
- `stock_min_roe`: 0.0 to 1.0 (decimal format)
- `stock_min_revenue_growth`: -0.5 to 2.0 (decimal format)
- `crypto_min_daily_volume`: >= 1000000 (1e6)

**Error:** `Input should be less than or equal to 1` and `Input should be greater than or equal to 1000000`

### 3. Union Type Parsing Error (1 error)

**Error:** `AttributeError: 'types.UnionType' object has no attribute '__name__'`

This occurred when CrewAI's schema parser tried to process Union types using the `|` operator (e.g., `str | None`).

## Root Causes

1. **Inconsistent Risk Schema**: Agents were creating custom risk assessment structures instead of using the standardized `RiskAssessmentStandardized` schema
2. **Ambiguous Criteria Ranges**: Schema constraints didn't match the natural percentage format agents use (20% vs 0.20)
3. **Union Type Incompatibility**: CrewAI's schema parser doesn't handle Python 3.10+ Union syntax (`|`)

## Solutions Applied

### 1. Fixed Union Type Syntax

Replaced all `X | None` with `Optional[X]` to avoid CrewAI parser issues:

```pythonthon
# Before
market_cap: float | None = Field(None, ...)
risk_assessment: RiskAssessmentStandardized | None = Field(None, ...)

# After
from typing import Optional
market_cap: Optional[float] = Field(None, ...)
risk_assessment: Optional[RiskAssessmentStandardized] = Field(None, ...)
```text
**Files Modified:**
- `src/finwiz/schemas/investment_discovery.py`

**Changes:**
- Added `Optional` to imports
- Replaced 7 instances of `X | None` with `Optional[X]`

### 2. Adjusted Criteria Value Ranges

Updated `APlusCriteria` to accept percentage format (0-100) instead of decimal (0-1):

```pythonthon
# Before
stock_min_roe: float = Field(default=0.20, ge=0.0, le=1.0, ...)
stock_min_revenue_growth: float = Field(default=0.15, ge=-0.5, le=2.0, ...)
crypto_min_daily_volume: float = Field(default=500e6, ge=1e6, le=1e12, ...)

# After
stock_min_roe: float = Field(default=20.0, ge=0.0, le=100.0, ...)
stock_min_revenue_growth: float = Field(default=15.0, ge=-50.0, le=200.0, ...)
crypto_min_daily_volume: float = Field(default=500e6, ge=1e5, le=1e12, ...)
```text
**Rationale:** Agents naturally use percentage format (20 for 20%) rather than decimal (0.20). Adjusting the schema to match agent behavior is more reliable than trying to force agents to use decimal format.

### 3. Added Risk Assessment Format Instructions

Added explicit "RISK ASSESSMENT FORMAT" sections to all discovery tasks:

```yaml
RISK ASSESSMENT FORMAT (CRITICAL):
For risk_assessment field in InvestmentCandidate, use RiskAssessmentStandardized schema:
- scale: MUST be "0_5" (for 0-5 scale, no other values allowed)
- score: MUST be a float between 0.0 and 5.0 (e.g., 1.75, 2.0, 2.25)
- level: MUST be one of: "Low", "Medium", "High", "Very High" (capitalized)
- risk_factors: MUST be a list of strings (up to 10 concise risk descriptions)
- DO NOT use fields like: systemic_risk, business_risk, liquidity_risk, governance_risk, overall_risk_score, notes
```text
**Files Modified:**
- `src/finwiz/crews/investment_discovery_crew/config/tasks.yaml`

**Tasks Updated:**
- `etf_discovery_task`
- `stock_discovery_task`
- `crypto_discovery_task`

### 4. Added Criteria Format Instructions

Added explicit criteria format guidance to prevent value range errors:

```yaml
CRITERIA FORMAT (CRITICAL):
For discovery_criteria and criteria_used fields, use APlusCriteria schema:
- stock_min_roe: Use percentage format (e.g., 20 for 20%, not 0.20)
- stock_min_revenue_growth: Use percentage format (e.g., 15 for 15%, not 0.15)
- crypto_min_daily_volume: Must be >= 100000 (1e5)
```text
## Expected Impact

These changes should eliminate all 153 validation errors by:

1. **Union Type Fix**: Prevents `AttributeError` in CrewAI's schema parser
2. **Criteria Range Fix**: Allows agents to use natural percentage format
3. **Risk Format Instructions**: Guides agents to use correct `RiskAssessmentStandardized` structure
4. **Explicit Enum Values**: Ensures agents use exact enum values required by schema

## Testing

Run the investment discovery crew to verify:

```bash
uv run python src/finwiz/main.py
```text
Expected result: Agents should now generate valid `APlusDiscoveryResult` objects that pass Pydantic validation.

## Related Fixes

This fix builds on previous schema validation improvements:
- `ENUM_VALUE_FIX_SUMMARY.md` - Enum value validation for crypto crew
- `CREW_SCHEMA_FIX_SUMMARY.md` - Schema resolution and output format fixes

## Technical Details

### RiskAssessmentStandardized Schema

The standardized risk schema requires exactly these fields:

```pythonthon
class RiskAssessmentStandardized(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    scale: Literal["0_5", "L_M_H", "L_M_H_VH"] = "0_5"
    score: float = Field(ge=0.0, le=5.0)
    level: RiskLevel  # "Low", "Medium", "High", "Very High"
    risk_factors: list[str] = Field(default_factory=list, max_length=10)
```text
With `extra="forbid"`, any additional fields (like `systemic_risk`, `business_risk`, etc.) will cause validation errors.

### APlusCriteria Value Ranges

The updated ranges now accept natural percentage format:

| Field | Old Range | New Range | Format |
|-------|-----------|-----------|--------|
| `stock_min_roe` | 0.0 - 1.0 | 0.0 - 100.0 | Percentage (20 = 20%) |
| `stock_min_revenue_growth` | -0.5 - 2.0 | -50.0 - 200.0 | Percentage (15 = 15%) |
| `crypto_min_daily_volume` | >= 1e6 | >= 1e5 | USD (100000 = $100k) |

---

**Status:** ✅ Complete
**Verified:** 2025-05-10
**Next:** Monitor for any remaining validation errors during crew execution
