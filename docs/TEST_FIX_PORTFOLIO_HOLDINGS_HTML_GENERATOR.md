# Portfolio Holdings HTML Generator Test Fixes

## Summary

Fixed all 12 failing tests in `tests/unit/tools/test_portfolio_holdings_html_generator.py`

**Results**: 13/13 tests passing (100% pass rate)

## Issues Identified and Fixed

### 1. Schema Field Mismatch: Risk Assessment (Lines 96, 98)

**Problem**: Code accessed `h.risk.overall_risk_score` but schema uses `h.risk.score`

**Root Cause**: RiskAssessmentStandardized schema has `score` field, not `overall_risk_score`

**Fix**:
```python
# Before
current_risk = h.risk.overall_risk_score
alt_risk = alt.risk_score if hasattr(alt, "risk_score") else current_risk

# After
current_risk = h.risk.score
alt_risk = alt.risk_score_standardized
```

**Files Modified**:
- `/Users/fjacquet/Projects/kiro/finwiz/src/finwiz/tools/portfolio_holdings_html_generator.py`

### 2. Schema Field Mismatch: Alternative Risk Score (Line 98)

**Problem**: Alternative schema uses `risk_score_standardized`, not `risk_score`

**Root Cause**: Alternative schema field naming convention differs from HoldingDecision

**Fix**: Use correct field name `alt.risk_score_standardized`

### 3. Schema Field Missing: Alternative Rationale (Lines 569-570)

**Problem**: Code accessed `alt.rationale` but Alternative schema doesn't have this field

**Root Cause**: Alternative uses `thesis_bullets` (list), not `rationale` (string)

**Fix**:
```python
# Before
rationale_preview = alt.rationale[:200] + "..." if len(alt.rationale) > 200 else alt.rationale

# After
thesis_text = " | ".join(alt.thesis_bullets[:3]) if alt.thesis_bullets else "Voir analyse détaillée"
```

### 4. CSS String Concatenation Issue (Lines 271-321)

**Problem**: Multi-line string with explicit `"""` continuation caused CSS truncation

**Root Cause**: Python triple-quote continuation creates implicit string concatenation that wasn't working correctly in this context

**Fix**: Changed from triple-quote multi-line string to explicit string concatenation with parentheses
```python
# Before
css = """
body{...}
.container{...;"""
"""box-shadow:...}
"""

# After
css = (
    "body{...}"
    ".container{...;"
    "box-shadow:...}"
    "@media print{...}"
    "@media (max-width: 768px){...}"
)
```

## Schema Documentation

### RiskAssessmentStandardized (src/finwiz/schemas/common.py)

```python
class RiskAssessmentStandardized(BaseModel):
    scale: Literal["0_5", "L_M_H", "L_M_H_VH"] = "0_5"
    score: float = Field(ge=0.0, le=5.0)  # ✅ Use this
    level: RiskLevel
    risk_factors: list[str] = Field(default_factory=list, max_length=10)
```

### Alternative (src/finwiz/schemas/portfolio_review.py)

```python
class Alternative(BaseModel):
    ticker: str
    name: str
    asset_class: AssetClass
    composite_score: float = Field(ge=0.0, le=1.0)
    grade: Grade
    grade_description: str
    recommended_action: str
    risk_score_standardized: float = Field(ge=0.0, le=5.0)  # ✅ Use this
    thesis_bullets: list[str]  # ✅ Use this (not 'rationale')
    transition_strategy: str
    swap_timing: Literal["immediate", "gradual", "tax_optimized"]
```

### HoldingDecision (src/finwiz/schemas/portfolio_review.py)

```python
class HoldingDecision(BaseModel):
    asset_class: AssetClass
    ticker: str
    decision: Decision
    composite_score: float
    grade: Grade
    risk: RiskAssessmentStandardized  # ✅ Access via .score
    rationale_bullets: list[str]  # Different from Alternative!
    alternatives: list[Alternative]
    price_targets: Optional[PriceTargets]
    crew_analysis_used: Optional[str]
    data_freshness: Literal["fresh", "recent", "stale"]
    analysis_date: Optional[datetime]
```

## Test Results

### Before Fixes
- **Pass Rate**: 1/13 (7.7%)
- **Failing Tests**: 12
- **Primary Issue**: AttributeError on schema field access

### After Fixes
- **Pass Rate**: 13/13 (100%)
- **Failing Tests**: 0
- **All Assertions**: Passing

## Key Lessons

1. **Always check actual schema definitions** - Don't assume field names
2. **RiskAssessmentStandardized uses `score`**, not `overall_risk_score`
3. **Alternative uses `thesis_bullets`**, not `rationale`
4. **Alternative uses `risk_score_standardized`**, not `risk_score`
5. **CSS string concatenation** - Use explicit parentheses for multi-line CSS
6. **Schema field naming** - Different schemas use different conventions (rationale_bullets vs thesis_bullets)

## Testing Pattern Used

This fix followed the **Orchestrator Pattern** (similar to HTMLReportGenerator):
- Generator class for HTML report creation
- Pydantic schemas for data validation
- BeautifulSoup for safe HTML generation
- F-strings for template rendering (AI Minimalism principle)

## Files Modified

1. `/Users/fjacquet/Projects/kiro/finwiz/src/finwiz/tools/portfolio_holdings_html_generator.py`
   - Fixed `h.risk.overall_risk_score` → `h.risk.score`
   - Fixed `alt.risk_score` → `alt.risk_score_standardized`
   - Fixed `alt.rationale` → `alt.thesis_bullets` with proper formatting
   - Fixed CSS string concatenation for media queries

## Verification

All tests pass with proper schema field access:
```bash
pytest tests/unit/tools/test_portfolio_holdings_html_generator.py -v
# Result: 13 passed in 8.98s
```

## Related Schemas

- `src/finwiz/schemas/common.py` - RiskAssessmentStandardized
- `src/finwiz/schemas/portfolio_review.py` - Alternative, HoldingDecision, PortfolioReview
- Follow schema definitions exactly - no assumptions!
