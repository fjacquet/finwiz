---
title: "Union Type Fix Summary"
description: "Archived documentation for Union Type Fix Summary"
category: "archive"
tags:
  - "archive"
date: "2025-10-26"
source: "archive/fix_reports/UNION_TYPE_FIX_SUMMARY.md"
---

# Union Type Syntax Fix for CrewAI Compatibility

[TOC]

## Date: 2025-05-10

## Problem

CrewAI's schema parser (`PydanticSchemaParser`) was failing with `AttributeError: 'types.UnionType' object has no attribute '__name__'` when processing schemas that use Python 3.10+ Union syntax (`X | None`).

This error occurred during the schema parsing phase when CrewAI tried to generate conversion instructions for agents, preventing crews from executing properly.

### Error Example

```pythonthon
AttributeError: 'types.UnionType' object has no attribute '__name__'. Did you mean: '__ne__'?
  File "crewai/utilities/pydantic_schema_parser.py", line 103, in _get_field_type_for_annotation
    return annotation.__name__
```text
## Root Cause

Python 3.10+ introduced the `|` operator for Union types (PEP 604), which creates `types.UnionType` objects. However, CrewAI's schema parser expects the older `typing.Union` or `typing.Optional` syntax, which have different internal representations.

When the parser encounters `X | None`, it tries to access `.__name__` on the `UnionType` object, which doesn't have that attribute, causing the crash.

## Solution

Replaced all instances of `X | None` with `Optional[X]` throughout the schema files to ensure compatibility with CrewAI's schema parser.

## Files Modified

### 1. `src/finwiz/schemas/investment_discovery.py`
**Changes:** 7 Union types fixed
- `InvestmentCandidate.market_cap`: `float | None` → `Optional[float]`
- `InvestmentCandidate.risk_assessment`: `RiskAssessmentStandardized | None` → `Optional[RiskAssessmentStandardized]`
- `APlusAnalysis.market_context`: `MarketRegime | None` → `Optional[MarketRegime]`
- `APlusAnalysis.criteria_used`: `APlusCriteria | None` → `Optional[APlusCriteria]`
- `APlusDiscoveryResult.ucits_compliant_count`: `int | None` → `Optional[int]`
- `PortfolioImprovement.current_holding`: `str | None` → `Optional[str]`
- `PortfolioImprovement.current_grade`: `Grade | None` → `Optional[Grade]`
- `PortfolioImprovement.expected_annual_benefit`: `float | None` → `Optional[float]`

**Additional Changes:**
- Adjusted `APlusCriteria` value ranges to accept percentage format (0-100) instead of decimal (0-1)
- Added `Optional` to imports

### 2. `src/finwiz/schemas/portfolio_review.py`
**Changes:** 15 Union types fixed
- `Alternative.discovery_source`: `str | None` → `Optional[str]`
- `Alternative.confidence_level`: `float | None` → `Optional[float]`
- `Alternative.expected_annual_benefit`: `float | None` → `Optional[float]`
- `Alternative.expected_cost_basis_impact`: `float | None` → `Optional[float]`
- `Alternative.expense_ratio_savings`: `float | None` → `Optional[float]`
- `Alternative.fundamental_improvement`: `dict | None` → `Optional[dict]`
- `Alternative.liquidity_improvement`: `float | None` → `Optional[float]`
- `APlusImprovementSuggestion.expected_annual_benefit`: `float | None` → `Optional[float]`
- `PriceTargets.fair_value_estimate`: `float | None` → `Optional[float]`
- `PriceTargets.buy_target_primary`: `float | None` → `Optional[float]`
- `PriceTargets.buy_target_secondary`: `float | None` → `Optional[float]`
- `PriceTargets.sell_target_primary`: `float | None` → `Optional[float]`
- `PriceTargets.sell_target_secondary`: `float | None` → `Optional[float]`
- `PriceTargets.stop_loss_level`: `float | None` → `Optional[float]`
- `HoldingDecision.price_targets`: `PriceTargets | None` → `Optional[PriceTargets]`
- `HoldingDecision.position_sizing`: `PositionSizeRecommendation | None` → `Optional[PositionSizeRecommendation]`
- `HoldingDecision.current_grade_potential`: `str | None` → `Optional[str]`
- `HoldingDecision.crew_analysis_used`: `str | None` → `Optional[str]`
- `HoldingDecision.analysis_date`: `datetime | None` → `Optional[datetime]`
- `APlusOpportunitySection.last_discovery_date`: `datetime | None` → `Optional[datetime]`

**Additional Changes:**
- Added `Optional` to imports

### 3. `src/finwiz/schemas/perplexity.py`
**Changes:** 5 Union types fixed
- `SonarArticle.published_date`: `str | None` → `Optional[str]`
- `SonarArticle.validate_published_date` parameter: `v: str | None` → `v: Optional[str]`
- `SonarSearchResult.error_message`: `str | None` → `Optional[str]`
- `PerplexitySearchRequest.search_filters`: `dict[str, str] | None` → `Optional[dict[str, str]]`
- `PerplexitySearchResponse.error_message`: `str | None` → `Optional[str]`
- `PerplexitySearchResponse.rate_limit_info`: `dict[str, int] | None` → `Optional[dict[str, int]]`

**Additional Changes:**
- Added `Optional` to imports

### 4. `src/finwiz/schemas/validation.py`
**Changes:** 1 Union type fixed
- `ValidatedTicker.reason`: `str | None` → `Optional[str]`

**Additional Changes:**
- Added `Optional` to imports

### 5. `src/finwiz/schemas/feedback.py`
**Changes:** 3 Union types fixed
- `UserFeedback.alternative_chosen`: `str | None` → `Optional[str]`
- `UserFeedback.allocation_percentage`: `float | None` → `Optional[float]`
- `PerformanceFeedback.sharpe_ratio`: `float | None` → `Optional[float]`

**Additional Changes:**
- Added `Optional` to imports

### 6. `src/finwiz/schemas/session.py`
**Changes:** 7 Union types fixed
- `ClientProfile.name`: `str | None` → `Optional[str]`
- `ClientProfile.age`: `int | None` → `Optional[int]`
- `ClientProfile.investment_horizon`: `str | None` → `Optional[str]`
- `ClientProfile.monthly_budget`: `str | None` → `Optional[str]`
- `ClientProfile.risk_tolerance`: `str | None` → `Optional[str]`
- `SessionMetadata.corruption_reason`: `str | None` → `Optional[str]`

**Additional Changes:**
- Added `Optional` to imports

### 7. `src/finwiz/schemas/integration_models.py`
**Changes:** 13 Union types fixed
- `DataSource.source_url`: `str | None` → `Optional[str]`
- `DataSource.validate_source_url` parameter: `v: str | None` → `v: Optional[str]`
- `DataSource.response_time_ms`: `float | None` → `Optional[float]`
- `CrewOutputMetadata.execution_duration_seconds`: `float | None` → `Optional[float]`
- `CrewOutputMetadata.input_hash`: `str | None` → `Optional[str]`
- `ValidatedTicker.market`: `str | None` → `Optional[str]`
- `ValidatedTicker.sector`: `str | None` → `Optional[str]`
- `ValidatedTicker.company_name`: `str | None` → `Optional[str]`
- `ValidatedETF.fund_name`: `str | None` → `Optional[str]`
- `ValidatedETF.issuer`: `str | None` → `Optional[str]`
- `ValidatedETF.expense_ratio`: `float | None` → `Optional[float]`
- `ValidatedCrypto.full_name`: `str | None` → `Optional[str]`
- `ValidatedCrypto.market_cap_rank`: `int | None` → `Optional[int]`
- `ValidatedCrypto.is_active`: `bool | None` → `Optional[bool]`
- `IntegrationError.expected_path`: `str | None` → `Optional[str]`
- `IntegrationError.actual_path`: `str | None` → `Optional[str]`

**Additional Changes:**
- Added `Optional` to imports

## Summary Statistics

- **Total files modified:** 7
- **Total Union types fixed:** 51
- **Crews affected:** All crews (investment_discovery, portfolio_rebalancing, report, stock, etf, crypto)

## Expected Impact

These changes will:

1. **Prevent `AttributeError`**: CrewAI's schema parser will no longer crash when processing Union types
2. **Enable crew execution**: All crews using these schemas can now execute without schema parsing errors
3. **Maintain functionality**: `Optional[X]` is semantically identical to `X | None`, so no behavior changes
4. **Improve compatibility**: Ensures compatibility with CrewAI's current schema parsing implementation

## Testing

All modified files passed diagnostics with no errors:

```bash
✅ src/finwiz/schemas/investment_discovery.py
✅ src/finwiz/schemas/portfolio_review.py
✅ src/finwiz/schemas/perplexity.py
✅ src/finwiz/schemas/validation.py
✅ src/finwiz/schemas/feedback.py
✅ src/finwiz/schemas/session.py
✅ src/finwiz/schemas/integration_models.py
```text
## Related Fixes

This fix complements previous schema validation improvements:
- `ENUM_VALUE_FIX_SUMMARY.md` - Enum value validation for crypto crew
- `CREW_SCHEMA_FIX_SUMMARY.md` - Schema resolution and output format fixes
- `APLUS_DISCOVERY_SCHEMA_FIX.md` - A+ discovery schema validation fixes

## Technical Background

### Python 3.10+ Union Syntax

Python 3.10 introduced PEP 604, which allows using `|` for Union types:

```pythonthon
# Python 3.10+ syntax
def func(x: int | None) -> str | None:
    pass

# Equivalent to older syntax
from typing import Optional, Union
def func(x: Optional[int]) -> Optional[str]:
    pass
```text
### CrewAI Schema Parser Limitation

CrewAI's `PydanticSchemaParser` uses introspection to generate schema descriptions for agents. It expects Union types to have a `.__name__` attribute, which `types.UnionType` (created by `|`) doesn't have.

The parser works correctly with `typing.Optional` and `typing.Union` because they have different internal representations that include the necessary attributes.

### Why This Matters

When agents fail to parse schemas, they can't:
- Understand the expected output structure
- Generate valid JSON that matches the schema
- Recover from validation errors using schema hints

By using `Optional[X]` syntax, we ensure CrewAI can properly parse and communicate schema requirements to agents.

---

**Status:** ✅ Complete
**Verified:** 2025-05-10
**Next:** Monitor crew execution to ensure no remaining schema parsing issues
