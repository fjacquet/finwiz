# Actionable Fix Plan - Report Data Flow Issues

## Date: 2025-10-19
## Status: READY TO IMPLEMENT

---

## Executive Summary

**TWO CRITICAL ISSUES** identified that cause "NOT AVAILABLE" in the report:

1. **Discovery Data Schema Mismatch** - APlusDataExtractor returns dicts with wrong field names
2. **Data Already Fixed** - data_availability_summary and sec_filing_urls ARE being set and passed correctly

**ACTUAL PROBLEM**: The discovery data extraction is failing silently due to Pydantic validation errors, returning None instead of data.

---

## Issue 1: Discovery Data Schema Mismatch (CRITICAL)

### Root Cause

The `APlusDataExtractor` methods return dicts with field names that don't match the `APlusOpportunity` Pydantic schema:

**What the extractor returns:**
```python
{
    "symbol": "AAPL",
    "company_name": "Apple Inc.",  # ❌ Wrong field name
    "grade": "A+",
    "rank": 1,
    "allocation_recommendation": "...",
    "replacement_note": "...",
    "risk_score": 2.5,
    "confidence": 0.9
    # ❌ Missing: composite_score, rationale, key_metrics
}
```

**What APlusOpportunity expects:**
```python
{
    "symbol": "AAPL",
    "name": "Apple Inc.",  # ✅ Correct field name
    "grade": "A+",
    "composite_score": 0.95,  # ✅ Required
    "confidence": 0.9,
    "risk_score": 2.5,
    "allocation_recommendation": "...",
    "replacement_note": "...",
    "rationale": ["..."],  # ✅ Required (list)
    "key_metrics": {...}  # ✅ Required (dict)
}
```

### The Fix

Update `src/finwiz/integration/aplus_extractor.py` methods to return dicts matching the schema:

#### Fix `_extract_stock_opportunities()` (line ~115)

```python
def _extract_stock_opportunities(self) -> list[dict[str, any]]:
    """Extract A+ stock opportunities from a_plus_stocks.json file."""
    stock_file = self.discovery_dir / "a_plus_stocks.json"

    if not stock_file.exists():
        self.logger.warning(f"Stock A+ file not found: {stock_file}")
        return []

    try:
        content = stock_file.read_text(encoding="utf-8")
        data = json.loads(content)
        opportunities = []

        candidates = data.get("a_plus_candidates", [])

        for idx, item in enumerate(candidates):
            candidate = item.get("candidate", {})

            # Only include A+ and A grades
            grade = candidate.get("grade", "")
            if grade not in ["A+", "A"]:
                continue

            symbol = candidate.get("symbol", "")
            company_name = candidate.get("name", "")
            composite_score = item.get("composite_score", 0.85)  # ✅ Extract from item
            confidence = item.get("confidence_level", 0.8)

            # Extract risk assessment
            risk_assessment = candidate.get("risk_assessment") or {}
            risk_score = risk_assessment.get("score", 5.0)

            # Extract rationale as list
            rationale = item.get("rationale", [])
            if isinstance(rationale, str):
                rationale = [rationale]  # Convert string to list

            # Extract key metrics
            key_metrics = item.get("key_metrics", {})

            # ✅ Return dict matching APlusOpportunity schema
            opportunity = {
                "symbol": symbol,
                "name": company_name,  # ✅ Changed from company_name
                "grade": grade,
                "composite_score": composite_score,  # ✅ Added
                "confidence": confidence,
                "risk_score": risk_score,
                "allocation_recommendation": " ".join(rationale[:2]) if rationale else "",
                "replacement_note": candidate.get("recommended_action", ""),
                "rationale": rationale,  # ✅ Added as list
                "key_metrics": key_metrics,  # ✅ Added as dict
            }

            opportunities.append(opportunity)

        self.logger.info(f"Extracted {len(opportunities)} stock A+ opportunities")
        return opportunities

    except Exception as e:
        self.logger.error(f"Failed to extract stock opportunities: {str(e)}", exc_info=True)
        return []
```

#### Fix `_extract_etf_opportunities()` (line ~170)

```python
def _extract_etf_opportunities(self) -> list[dict[str, any]]:
    """Extract A+ ETF opportunities from a_plus_etfs.json file."""
    etf_file = self.discovery_dir / "a_plus_etfs.json"

    if not etf_file.exists():
        self.logger.warning(f"ETF A+ file not found: {etf_file}")
        return []

    try:
        content = etf_file.read_text(encoding="utf-8")
        data = json.loads(content)
        opportunities = []

        candidates = data.get("a_plus_candidates", [])

        for idx, item in enumerate(candidates):
            candidate = item.get("candidate", {})

            # Only include A+ and A grades
            grade = candidate.get("grade", "")
            if grade not in ["A+", "A"]:
                continue

            symbol = candidate.get("symbol", "")
            fund_name = candidate.get("name", "")
            composite_score = item.get("composite_score", 0.85)  # ✅ Extract from item
            confidence = item.get("confidence_level", 0.9)

            # Extract key metrics
            key_metrics = item.get("key_metrics", {})
            ter = key_metrics.get("ter", 0.0)
            aum = key_metrics.get("aum_usd", 0)

            # Format AUM for display
            if aum >= 1e9:
                aum_str = f"${aum / 1e9:.1f}B"
            elif aum >= 1e6:
                aum_str = f"${aum / 1e6:.1f}M"
            else:
                aum_str = f"${aum:,.0f}"

            # Add formatted AUM to key_metrics
            key_metrics["aum_formatted"] = aum_str

            # Extract rationale as list
            rationale = item.get("rationale", [])
            if isinstance(rationale, str):
                rationale = [rationale]

            # Extract risk assessment
            risk_assessment = candidate.get("risk_assessment") or {}
            risk_score = risk_assessment.get("score", 3.0)

            # ✅ Return dict matching APlusOpportunity schema
            opportunity = {
                "symbol": symbol,
                "name": fund_name,  # ✅ Changed from fund_name
                "grade": grade,
                "composite_score": composite_score,  # ✅ Added
                "confidence": confidence,
                "risk_score": risk_score,
                "allocation_recommendation": " ".join(rationale[:2]) if rationale else "",
                "replacement_note": candidate.get("recommended_action", ""),
                "rationale": rationale,  # ✅ Added as list
                "key_metrics": key_metrics,  # ✅ Added as dict (includes ter, aum, aum_formatted)
            }

            opportunities.append(opportunity)

        self.logger.info(f"Extracted {len(opportunities)} ETF A+ opportunities")
        return opportunities

    except Exception as e:
        self.logger.error(f"Failed to extract ETF opportunities: {str(e)}", exc_info=True)
        return []
```

#### Fix `_extract_crypto_opportunities()` (line ~240)

```python
def _extract_crypto_opportunities(self) -> list[dict[str, any]]:
    """Extract A+ crypto opportunities from a_plus_crypto.json file."""
    crypto_file = self.discovery_dir / "a_plus_crypto.json"

    if not crypto_file.exists():
        self.logger.warning(f"Crypto A+ file not found: {crypto_file}")
        return []

    try:
        content = crypto_file.read_text(encoding="utf-8")
        data = json.loads(content)
        opportunities = []

        candidates = data.get("a_plus_candidates", [])

        for idx, item in enumerate(candidates):
            candidate = item.get("candidate", {})

            # Only include A+ and A grades
            grade = candidate.get("grade", "")
            if grade not in ["A+", "A"]:
                continue

            symbol = candidate.get("symbol", "")
            crypto_name = candidate.get("name", "")
            composite_score = item.get("composite_score", 0.80)  # ✅ Extract from item
            confidence = item.get("confidence_level", 0.85)

            # Extract key metrics
            key_metrics = item.get("key_metrics", {})

            # Extract rationale as list
            rationale = item.get("rationale", [])
            if isinstance(rationale, str):
                rationale = [rationale]

            # Extract risk assessment
            risk_assessment = candidate.get("risk_assessment") or {}
            risk_score = risk_assessment.get("score", 6.0)  # Crypto typically higher risk

            # ✅ Return dict matching APlusOpportunity schema
            opportunity = {
                "symbol": symbol,
                "name": crypto_name,  # ✅ Changed from crypto_name
                "grade": grade,
                "composite_score": composite_score,  # ✅ Added
                "confidence": confidence,
                "risk_score": risk_score,
                "allocation_recommendation": " ".join(rationale[:2]) if rationale else "",
                "replacement_note": candidate.get("recommended_action", ""),
                "rationale": rationale,  # ✅ Added as list
                "key_metrics": key_metrics,  # ✅ Added as dict
            }

            opportunities.append(opportunity)

        self.logger.info(f"Extracted {len(opportunities)} crypto A+ opportunities")
        return opportunities

    except Exception as e:
        self.logger.error(f"Failed to extract crypto opportunities: {str(e)}", exc_info=True)
        return []
```

---

## Issue 2: Data Availability Summary (ALREADY FIXED)

### Status: ✅ WORKING CORRECTLY

The code analysis shows:

1. **Flow Orchestrator** (line 2416-2417):
   - ✅ Sets `self.state.data_availability_summary`
   - ✅ Sets `self.state.data_availability_summary_formatted`

2. **State to Dict** (line 120):
   - ✅ Calls `self.state.model_dump()` which includes ALL fields

3. **Report Crew** (line 972-973):
   - ✅ Lists `data_availability_summary` in `required_keys`
   - ✅ Lists `data_availability_summary_formatted` in `required_keys`
   - ✅ Preserves these keys from Flow state inputs

**CONCLUSION**: This is working correctly. The issue is that the report shows "NOT AVAILABLE" because the discovery data is None (due to Issue 1), which affects the overall data availability status.

---

## Issue 3: SEC Filing URLs (ALREADY FIXED)

### Status: ✅ WORKING CORRECTLY

The code analysis shows:

1. **Flow Orchestrator** (line 2432-2433):
   - ✅ Calls `_extract_sec_filing_urls()`
   - ✅ Sets `self.state.sec_filing_urls`

2. **Report Crew** (line 977):
   - ✅ Lists `sec_filing_urls` in `required_keys`
   - ✅ Preserves this key from Flow state inputs

**CONCLUSION**: This is also working correctly. The SEC URLs should appear in the report once the flow runs successfully.

---

## Implementation Steps

### Step 1: Fix Discovery Data Extraction (30 minutes)

1. Open `src/finwiz/integration/aplus_extractor.py`
2. Update `_extract_stock_opportunities()` method (lines ~115-170)
3. Update `_extract_etf_opportunities()` method (lines ~170-240)
4. Update `_extract_crypto_opportunities()` method (lines ~240-310)
5. Save the file

### Step 2: Test the Fix (10 minutes)

```bash
# Run the full flow
uv run python src/finwiz/main.py

# Check the logs for:
# - "Extracted X stock A+ opportunities"
# - "Extracted X ETF A+ opportunities"
# - "Extracted X crypto A+ opportunities"
# - "✅ Preserved aplus_opportunities: X A+ opportunities found"

# Open the generated report
open output/finwiz_family_financial_plan.html

# Verify:
# - Discovery section shows A+ opportunities (not "discovery not run")
# - Data availability section shows actual data (not "NOT PROVIDED")
# - SEC filing URLs are present for stock holdings
```

### Step 3: Verify Success (5 minutes)

Check the report for:

1. **Discovery Section**:
   - ✅ Shows "Opportunités A+" section
   - ✅ Lists discovered opportunities with tickers and grades
   - ✅ Shows composite scores and confidence levels

2. **Data Availability Section**:
   - ✅ Shows actual source counts (not "NOT PROVIDED")
   - ✅ Shows freshness warnings if applicable
   - ✅ Shows timestamp

3. **SEC Filing Links**:
   - ✅ Stock holdings have clickable SEC EDGAR links
   - ✅ Links point to actual SEC filings

---

## Why This Fix Works

1. **Root Cause**: The `APlusDataExtractor` was returning dicts with field names that didn't match the `APlusOpportunity` Pydantic schema
2. **Validation Failure**: When trying to create `APlusOpportunity(**opp)`, Pydantic validation failed
3. **Silent Failure**: The exception was caught and None was returned
4. **Cascade Effect**: No discovery data → report shows "NOT AVAILABLE"

**The Fix**: Update the extractor to return dicts that exactly match the Pydantic schema, so validation succeeds and data flows through to the report.

---

## Files to Modify

1. `src/finwiz/integration/aplus_extractor.py` - Fix all three extraction methods

---

## Expected Outcome

After this fix:

- ✅ Discovery data will load successfully
- ✅ Report will show A+ opportunities
- ✅ Data availability section will show actual data
- ✅ SEC filing URLs will appear for stocks
- ✅ No more "NOT AVAILABLE" messages

---

## Rollback Plan

If the fix causes issues:

```bash
# Revert the changes
git checkout src/finwiz/integration/aplus_extractor.py

# Run the flow again
uv run python src/finwiz/main.py
```

---

**Status**: READY TO IMPLEMENT
**Estimated Time**: 45 minutes total
**Risk**: LOW (only changes data extraction, doesn't affect flow logic)

