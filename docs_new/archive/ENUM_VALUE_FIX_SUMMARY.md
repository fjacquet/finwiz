---
title: "Enum Value Fix Summary"
description: "Archived documentation for Enum Value Fix Summary"
category: "archive"
tags:
  - "archive"
date: "2025-10-26"
source: "archive/fix_reports/ENUM_VALUE_FIX_SUMMARY.md"
---

# Enum Value Validation Fix

[TOC]

## Date: 2025-10-05

## Problem

Agents were returning JSON with values that don't match the Literal/Enum constraints in Pydantic schemas, causing validation errors:

### Example Errors:

1. **CryptoMarketAnalysis**:
   - Agent returned: `"market_sentiment": "Cautiously Positive"`
   - Schema expects: `'bullish', 'bearish', 'neutral', 'mixed'`
   - Error: `Input should be 'bullish', 'bearish', 'neutral' or 'mixed'`

2. **CryptoRiskProfile** (via RiskAssessmentStandardized):
   - Agent returned: `"scale": "0-5"`
   - Schema expects: `'0_5', 'L_M_H', 'L_M_H_VH'`
   - Agent returned: `"level": "moderate"`
   - Schema expects: `'Low', 'Medium', 'High', 'Very High'`

## Root Cause

LLMs naturally use human-friendly values (like "Cautiously Positive" or "moderate") rather than the exact enum values defined in schemas. Without explicit guidance, they don't know the precise allowed values.

## Solution

Added "REQUIRED ENUM VALUES" sections to task descriptions that explicitly list the exact allowed values for each enum field.

### Pattern Used:

```yaml
REQUIRED ENUM VALUES (use EXACTLY these values):
- field_name: MUST be one of: "value1", "value2", "value3" (additional guidance)
```text
## Changes Made

### Crypto Crew Tasks (`src/finwiz/crews/crypto_crew/config/tasks.yaml`)

#### 1. market_analysis_task
Added enum instructions for:
- `market_sentiment`: "bullish", "bearish", "neutral", "mixed"

#### 2. risk_assessment_task
Added enum instructions for:
- `risk_assessment.scale`: "0_5", "L_M_H", "L_M_H_VH"
- `risk_assessment.level`: "Low", "Medium", "High", "Very High"

## Expected Impact

By providing explicit enum values in the task descriptions:
1. Agents will use the exact values required by schemas
2. Pydantic validation will pass on first attempt
3. CrewAI won't need to invoke its schema parser for error recovery
4. This avoids triggering the union type bug in CrewAI's schema parser

## Next Steps

If validation errors persist for other fields:
1. Identify the failing enum/Literal field from the error message
2. Add a "REQUIRED ENUM VALUES" section to the relevant task description
3. List the exact allowed values with clear formatting

## Testing

Run the crypto crew again to verify:
```bash
uv run crewai flow kickoff
```text
Expected result: Agents should now use correct enum values and pass Pydantic validation.

---

**Status:** ✅ Complete for crypto crew market_analysis_task and risk_assessment_task
**Next:** Monitor for additional enum validation errors in other tasks/crews
