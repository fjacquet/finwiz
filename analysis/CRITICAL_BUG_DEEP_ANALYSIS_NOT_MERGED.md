# CRITICAL BUG: Deep Analysis Results Not Merged Into Portfolio Review

## Problem Summary

The deep analysis is running successfully and generating correct scores, but the results are NOT being merged back into the portfolio review. This causes the final HTML report to show incorrect placeholder values (0.750, Grade B) instead of the real analysis results.

## Evidence

### 1. Deep Analysis Works Correctly

`output/stock/AAPL_default.json`:
```json
{
  "composite_score": 0.754,
  "grade": "A",
  "recommendation": "BUY",
  "confidence": 0.722,
  "rationale": "AAPL receives a A grade with a composite score of 0.75..."
}
```

### 2. Portfolio Review Has Old Data

`output/portfolio/portfolio_review.json`:
```json
{
  "ticker": "AAPL",
  "composite_score": 0.75,  // ❌ WRONG - Should be 0.754
  "grade": "B",              // ❌ WRONG - Should be "A"
  "rationale_bullets": [
    "⚡ Validation rapide (analyse superficielle)",  // ❌ WRONG - Should have real analysis
    ...
  ]
}
```

### 3. Final HTML Report Shows Wrong Data

`output/finwiz_family_financial_plan.html`:
- All stocks: 0.750, Grade B
- All ETFs: 0.800, Grade B+
- All crypto: 0.750, Grade B

## Root Cause

The flow is:

1. ✅ **Portfolio Review Generated** → Creates `portfolio_review.json` with quick validation scores (0.750)
2. ✅ **Deep Analysis Runs** → Generates correct scores in `output/stock/AAPL_default.json` (0.754, Grade A)
3. ❌ **NO MERGE STEP** → Deep analysis results are NOT merged back into `portfolio_review.json`
4. ❌ **HTML Report Generated** → Uses OLD `portfolio_review.json` with placeholder scores

## Expected Flow

1. Portfolio Review Generated → Quick validation scores
2. Deep Analysis Runs → Real analysis scores
3. **MERGE STEP** → Update `portfolio_review.json` with deep analysis results
4. HTML Report Generated → Uses UPDATED `portfolio_review.json` with real scores

## Where to Fix

The merge should happen in the Flow after deep analysis completes. Look for:

**File**: `src/finwiz/flows/flow_orchestrator.py` or similar

**Method**: Something like `analyze_and_update_portfolio()` or after deep analysis completes

**Required Logic**:
```python
# After deep analysis completes
for ticker in deep_analysis_results:
    # Load deep analysis JSON
    deep_result = load_json(f"output/{asset_class}/{ticker}_default.json")
    
    # Find matching holding in portfolio_review
    for holding in portfolio_review["holdings"]:
        if holding["ticker"] == ticker:
            # UPDATE with deep analysis results
            holding["composite_score"] = deep_result["composite_score"]
            holding["grade"] = deep_result["grade"]
            holding["recommendation"] = deep_result["recommendation"]
            holding["confidence"] = deep_result["confidence"]
            holding["rationale_bullets"] = [deep_result["rationale"]]
            holding["fundamental_score"] = deep_result.get("fundamental_score")
            holding["technical_score"] = deep_result.get("technical_score")
            holding["risk_score"] = deep_result.get("risk_score")
            # ... update other fields
            
# Save updated portfolio_review.json
save_json("output/portfolio/portfolio_review.json", portfolio_review)
```

## Impact

**Severity**: CRITICAL - User sees completely wrong data
**Scope**: ALL holdings (74 positions)
**User Trust**: Severely damaged - all recommendations are wrong

## Verification

After fix, verify:

1. `output/stock/AAPL_default.json` has score 0.754, Grade A
2. `output/portfolio/portfolio_review.json` has SAME score 0.754, Grade A for AAPL
3. `output/finwiz_family_financial_plan.html` shows score 0.754, Grade A for AAPL
4. All three files must match!

## Log Evidence

From `flow_execution.log`:

```
2025-11-01 18:16:04 - finwiz.scoring.deep_analysis_scorer - INFO - ✅ Python scoring completed for AAPL: Grade A (0.754), Recommendation BUY (72.2% confidence)
```

But the HTML report shows Grade B (0.750) - proving the merge never happened.

---

**Status**: CRITICAL BUG - NEEDS IMMEDIATE FIX
**Priority**: P0
**Assigned**: Developer
