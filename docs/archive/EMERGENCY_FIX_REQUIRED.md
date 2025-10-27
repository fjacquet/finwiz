# EMERGENCY FIX REQUIRED - Schema Change Broke Data Loading

## Date: 2025-10-19 10:18
## Severity: CRITICAL - 100% Data Loss

---

## The Smoking Gun

From `flow_execution.log`:
```
2025-10-19 10:18:09 - CRITICAL DATA CHECK BEFORE REPORT GENERATION
2025-10-19 10:18:09 - ✅ portfolio_review present in state (type: <class 'dict'>)
2025-10-19 10:18:09 - ⚠️ aplus_opportunities is None/empty in Flow state
2025-10-19 10:18:09 - ✅ data_availability_summary present in state
2025-10-19 10:18:09 - ✅ data_availability_summary_formatted present in state
2025-10-19 10:18:09 - ⚠️ sec_filing_urls is empty
```

**Root Cause**: Our schema change to `APlusOpportunityCollection` broke the data loading from disk.

---

## What We Broke

### Change Made:
```python
# OLD (worked):
class APlusOpportunityCollection(BaseModel):
    etf_opportunities: list[str]  # Just symbols
    stock_opportunities: list[str]
    crypto_opportunities: list[str]

# NEW (broken):
class APlusOpportunityCollection(BaseModel):
    etf_opportunities: list[APlusOpportunity]  # Full objects
    stock_opportunities: list[APlusOpportunity]
    crypto_opportunities: list[APlusOpportunity]
```

### What Broke:
1. **APlusDataExtractor** tries to create `APlusOpportunity` objects from dicts
2. **Validation fails** because dict structure doesn't match `APlusOpportunity` schema
3. **Returns None** instead of data
4. **Report gets nothing**

---

## Evidence from Report

1. **Discovery**: "has_a_plus_analysis = false" - Should be true
2. **Tickers**: All show 0.7/2.0 defaults - Deep analysis didn't merge
3. **SEC URLs**: Empty - Extraction failed
4. **Backtesting**: Not available - Part of discovery data

---

## The Fix

### Option 1: Revert Schema Change (FASTEST - 2 minutes)

```python
# Revert to original schema
class APlusOpportunityCollection(BaseModel):
    etf_opportunities: list[str]  # Back to symbols
    stock_opportunities: list[str]
    crypto_opportunities: list[str]
    # Keep new fields
    market_context: dict[str, Any] | None = None
    backtesting_metrics: dict[str, Any] | None = None
```

### Option 2: Fix Data Extractor (PROPER - 30 minutes)

Make `APlusDataExtractor` handle both old and new formats:

```python
def _extract_stock_opportunities(self) -> list[APlusOpportunity]:
    # ... existing code ...
    
    try:
        opportunity = APlusOpportunity(
            symbol=symbol,
            name=company_name,
            grade=grade,
            composite_score=composite_score,
            confidence=confidence,
            risk_score=risk_score,
            allocation_recommendation=allocation_rec,
            replacement_note=replacement,
            rationale=rationale,
            key_metrics=key_metrics
        )
        opportunities.append(opportunity)
    except ValidationError as e:
        # Fallback: return dict if validation fails
        logger.warning(f"Could not create APlusOpportunity for {symbol}: {e}")
        opportunities.append({
            "symbol": symbol,
            "name": company_name,
            # ... other fields
        })
```

### Option 3: Make Schema Backward Compatible (BEST - 1 hour)

```python
class APlusOpportunity(BaseModel):
    symbol: str
    name: str = ""  # Optional with default
    grade: str = "N/A"  # Optional with default
    composite_score: float = 0.0  # Optional with default
    # ... all fields optional with defaults
    
    @classmethod
    def from_symbol(cls, symbol: str) -> "APlusOpportunity":
        """Create from just a symbol (backward compat)."""
        return cls(symbol=symbol)
```

---

## Immediate Action Required

1. **REVERT** the schema change (Option 1)
2. **RUN** the flow again to verify it works
3. **THEN** implement proper fix (Option 2 or 3)
4. **TEST** before committing

---

## Files to Revert

1. `src/finwiz/schemas/integration_models.py`
   - Revert `APlusOpportunityCollection` to use `list[str]`
   - Keep new fields (`market_context`, `backtesting_metrics`)

2. `src/finwiz/integration/aplus_extractor.py`
   - Revert to return `list[dict]` instead of `list[APlusOpportunity]`
   - Keep new extraction methods

---

## Why This Happened

**We changed the schema without testing the data loading pipeline.**

The discovery files contain:
```json
{
  "a_plus_candidates": [
    {
      "candidate": {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        // ... more fields
      }
    }
  ]
}
```

But our new `APlusOpportunity` schema expects different field names or structure, causing validation to fail.

---

## Lesson Learned

**NEVER change data schemas without:**
1. Checking what data actually looks like in files
2. Testing the data loading pipeline
3. Running the full flow to verify
4. Having backward compatibility

---

## Next Steps

1. **STOP** - Don't make more changes
2. **REVERT** - Go back to working schema
3. **TEST** - Verify flow works again
4. **PLAN** - Design proper migration strategy
5. **IMPLEMENT** - With tests this time
6. **VERIFY** - Run full flow before committing

---

## Status: BLOCKED

**Cannot proceed until schema is reverted and flow works again.**
