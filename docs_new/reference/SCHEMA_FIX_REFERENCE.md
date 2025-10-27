---
title: "Schema Fix Reference"
description: "Complete reference documentation for Schema Fix Reference"
category: "reference"
tags:
  - "reference"
date: "2025-10-26"
source: "archive/SCHEMA_FIX_REFERENCE.md"
---

# Schema Fix Reference - APlusOpportunity Field Mapping

Quick reference for the schema changes made to fix discovery data extraction.

## Field Name Changes

### Before (BROKEN) → After (FIXED)

| Asset Type | Old Field Name | New Field Name | Notes |
|------------|---------------|----------------|-------|
| Stock | `company_name` | `name` | Unified field across all asset types |
| ETF | `fund_name` | `name` | Unified field across all asset types |
| Crypto | `crypto_name` | `name` | Unified field across all asset types |

## Required Fields Added

All extraction methods now include these required fields:

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `composite_score` | `float` | Quality score (0.0-1.0) | `0.96` |
| `rationale` | `list[str]` | Investment rationale points | `["ROE 45%", "Revenue CAGR 36%"]` |
| `key_metrics` | `dict[str, Any]` | Asset-specific metrics | `{"roe": 45.0, "revenue_growth": 36.0}` |

## Complete APlusOpportunity Schema

```pythonthon
class APlusOpportunity(BaseModel):
    symbol: str                      # Required: Ticker symbol
    name: str                        # Required: Company/fund name (UNIFIED)
    grade: str                       # Required: Investment grade (A+, A, etc.)
    composite_score: float           # Required: 0.0-1.0
    confidence: float                # Required: 0.0-1.0
    risk_score: float                # Required: 0.0-10.0
    allocation_recommendation: str   # Optional: Allocation guidance
    replacement_note: str            # Optional: What this might replace
    rationale: list[str]             # Required: Investment rationale points
    key_metrics: dict[str, Any]      # Required: Key financial metrics
```text
## Extraction Method Templates

### Stock Extraction

```pythonthon
opportunity = {
    "symbol": symbol,
    "name": company_name,                    # ✅ Unified field
    "grade": grade,
    "composite_score": composite_score,      # ✅ Added
    "confidence": confidence,
    "risk_score": risk_score,
    "allocation_recommendation": "...",
    "replacement_note": "...",
    "rationale": rationale,                  # ✅ Added (list)
    "key_metrics": key_metrics,              # ✅ Added (dict)
}
```text
### ETF Extraction

```pythonthon
opportunity = {
    "symbol": symbol,
    "name": fund_name,                       # ✅ Unified field
    "grade": grade,
    "composite_score": composite_score,      # ✅ Added
    "confidence": confidence,
    "risk_score": risk_score,
    "allocation_recommendation": "...",
    "replacement_note": "...",
    "rationale": rationale,                  # ✅ Added (list)
    "key_metrics": {                         # ✅ Added (dict)
        "ter": ter,
        "aum_usd": aum,
        "aum_formatted": aum_str
    },
}
```text
### Crypto Extraction

```pythonthon
opportunity = {
    "symbol": symbol.replace("-USD", ""),
    "name": crypto_name,                     # ✅ Unified field
    "grade": grade,
    "composite_score": composite_score,      # ✅ Added
    "confidence": confidence,
    "risk_score": risk_score,
    "allocation_recommendation": "...",
    "replacement_note": "...",
    "rationale": rationale,                  # ✅ Added (list)
    "key_metrics": key_metrics,              # ✅ Added (dict)
}
```text
## Key Metrics by Asset Type

### Stock Key Metrics
```pythonthon
{
    "roe": 45.0,
    "revenue_growth": 36.0,
    "pe_ratio": 25.0,
    "debt_to_equity": 0.3
}
```text
### ETF Key Metrics
```pythonthon
{
    "ter": 0.0022,
    "aum_usd": 17500000000,
    "aum_formatted": "$17.5B",
    "tracking_error": 0.15
}
```text
### Crypto Key Metrics
```pythonthon
{
    "market_cap": 1200000000000,
    "volume_24h": 30000000000,
    "circulating_supply": 19000000
}
```text
## Rationale Format

Always ensure rationale is a list:

```pythonthon
# Extract rationale as list
rationale = item.get("rationale", [])
if isinstance(rationale, str):
    rationale = [rationale]  # Convert string to list
```text
## Common Mistakes to Avoid

❌ **Don't use asset-specific field names:**
```pythonthon
opportunity = {
    "company_name": "Apple",  # WRONG
    "fund_name": "Vanguard",  # WRONG
    "crypto_name": "Bitcoin"  # WRONG
}
```text
✅ **Use unified `name` field:**
```pythonthon
opportunity = {
    "name": "Apple"     # CORRECT
}
```text
❌ **Don't forget required fields:**
```pythonthon
opportunity = {
    "symbol": "AAPL",
    "name": "Apple",
    "grade": "A+"
    # Missing: composite_score, rationale, key_metrics
}
```text
✅ **Include all required fields:**
```pythonthon
opportunity = {
    "symbol": "AAPL",
    "name": "Apple",
    "grade": "A+",
    "composite_score": 0.98,
    "rationale": ["ROE 45%"],
    "key_metrics": {"roe": 45.0}
}
```text
## Validation Changes

### Old (BROKEN)
```pythonthon
# Tried to create set from APlusOpportunity objects
all_symbols = collection.stock_opportunities + collection.etf_opportunities
if len(all_symbols) != len(set(all_symbols)):  # TypeError: unhashable type
    errors.append("Duplicate symbols found")
```text
### New (FIXED)
```pythonthon
# Extract symbols first, then create set
all_symbols = (
    [opp.symbol for opp in collection.stock_opportunities]
    + [opp.symbol for opp in collection.etf_opportunities]
    + [opp.symbol for opp in collection.crypto_opportunities]
)
if len(all_symbols) != len(set(all_symbols)):
    errors.append("Duplicate symbols found")
```text
---

**Quick Check**: If you see Pydantic validation errors mentioning missing fields or wrong field names, refer to this guide to ensure your extraction methods match the schema exactly.
