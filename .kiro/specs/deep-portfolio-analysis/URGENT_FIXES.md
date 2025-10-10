# Urgent Data Integration Fixes

## Critical Issues Found

### 1. Discovery Data Not Reaching Reporter ❌
**Problem**: Discovery crew runs successfully and creates files, but reporter says "discovery not run"
- Files exist: `output/discovery/a_plus_*.json` ✅
- Flow extracts data: "Extracted A+ opportunities via integration system: 9 ETFs, 20 stocks, 5 crypto" ✅
- Reporter receives: "discovery not run / A+ analysis not executed" ❌

**Root Cause**: Report crew checks for files using `APlusDiscoveryAccessor.has_discovery_results()` instead of checking Flow state inputs first.

**Fix**: Update `_get_discovery_status()` to check inputs first, then fall back to file checking.

---

### 2. Backtesting Data Not Available ❌
**Problem**: Reporter says "Backtesting data not available - discovery not run"
- Discovery DID run (files exist)
- Backtesting data should be extracted from discovery results
- Reporter not receiving backtesting metadata

**Root Cause**: Similar to #1 - backtesting data accessor not checking Flow state inputs.

**Fix**: Update backtesting data extraction to check inputs first.

---

### 3. Market Context Data Missing ❌
**Problem**: Reporter shows:
- "Niveau VIX actuel : Non disponible"
- "Indicateurs macro (inflation, taux) : Non disponibles"
- "Niveau de stress du marché : Non déterminé"

**Root Cause**: Market context data from discovery results not being passed to reporter.

**Discovery files contain**:
```json
"market_context": {
  "regime_type": "mixed",
  "vix_level": 17.5,
  "inflation_rate": 3.1,
  "interest_rate_trend": "rising",
  "market_stress_level": "moderate",
  "assessment_date": "2025-10-09T00:00:00Z"
}
```

**Fix**: Extract and pass market context from discovery results to reporter.

---

### 4. Portfolio Holdings Grading Issues ❌
**Problem**: AAPL, ASML, MSFT showing as D grade
- These are high-quality stocks
- Likely using shallow validation instead of deep analysis
- Deep analysis disabled by default

**Root Cause**: 
1. `DEEP_PORTFOLIO_ANALYSIS=false` by default
2. Shallow validation gives conservative grades
3. No crew analysis performed

**Fix**: 
- Enable deep analysis by default OR
- Improve shallow validation scoring OR
- Make it clear in report that shallow validation is being used

---

### 5. Data Availability Summary Missing ❌
**Problem**: Reporter says "data_availability_summary (manquant)"
- Cannot determine data freshness
- Cannot prioritize crew refresh
- Missing transparency footer

**Root Cause**: `data_availability_summary` not being generated or passed to reporter.

**Fix**: Ensure data availability summary is generated and included in reporter inputs.

---

## Implementation Priority

### Priority 1: Discovery Data Integration (CRITICAL)
**Impact**: Users see "discovery not run" even though it ran successfully
**Effort**: 2-3 hours
**Files**:
- `src/finwiz/crews/report_crew/report_crew.py` - Update `_get_discovery_status()`
- `src/finwiz/crews/report_crew/report_crew.py` - Update `_prepare_integrated_data()`

**Changes**:
```python
def _get_discovery_status(self, inputs: dict[str, Any]) -> dict[str, Any]:
    """
    Get A+ discovery status with clear messaging.
    
    Args:
        inputs: Reporter inputs from Flow state
        
    Returns:
        Dictionary with discovery status information
    """
    # FIRST: Check if discovery data was provided in inputs
    if inputs.get("aplus_opportunities"):
        return {
            "has_results": True,
            "message": "A+ discovery results available",
            "status": "available"
        }
    
    # SECOND: Check if discovery data exists in Flow state
    if inputs.get("investment_discovery_structured"):
        return {
            "has_results": True,
            "message": "A+ discovery results available",
            "status": "available"
        }
    
    # THIRD: Fall back to file-based checking
    has_results = self.discovery_accessor.has_discovery_results()
    
    if has_results:
        return {
            "has_results": True,
            "message": "A+ discovery results available",
            "status": "available"
        }
    else:
        return {
            "has_results": False,
            "message": "A+ discovery not run - use --discovery flag to enable discovery analysis",
            "status": "not_run",
        }
```

### Priority 2: Market Context Extraction (HIGH)
**Impact**: Missing VIX, inflation, interest rates in report
**Effort**: 1-2 hours
**Files**:
- `src/finwiz/flows/flow_orchestrator.py` - Extract market context from discovery
- `src/finwiz/crews/report_crew/report_crew.py` - Use market context in report

**Changes**:
```python
# In flow_orchestrator.py - check_investment_discovery()
if discovery_result:
    # Extract market context from discovery results
    market_context = discovery_result.get("market_context", {})
    self.state.market_context = market_context
    
    # Log market context
    logger.info(f"Market context extracted: VIX={market_context.get('vix_level')}, "
                f"regime={market_context.get('regime_type')}")
```

### Priority 3: Backtesting Data Integration (HIGH)
**Impact**: Missing backtesting metrics in report
**Effort**: 2-3 hours
**Files**:
- `src/finwiz/integration/backtesting_extractor.py` - Check inputs first
- `src/finwiz/crews/report_crew/report_crew.py` - Update backtesting status check

### Priority 4: Data Availability Summary (MEDIUM)
**Impact**: Missing data freshness transparency
**Effort**: 2-3 hours
**Files**:
- `src/finwiz/flows/flow_orchestrator.py` - Generate availability summary
- `src/finwiz/crews/report_crew/report_crew.py` - Use availability summary

### Priority 5: Portfolio Grading Improvement (MEDIUM)
**Impact**: High-quality stocks showing as D grade
**Effort**: 3-4 hours
**Options**:
1. Enable deep analysis by default (set `DEEP_PORTFOLIO_ANALYSIS=true`)
2. Improve shallow validation scoring algorithm
3. Add clear messaging about shallow vs deep analysis

---

## Testing Plan

### Test 1: Discovery Data Integration
```bash
# Run with discovery enabled
export DEEP_PORTFOLIO_ANALYSIS=true
uv run python src/finwiz/main.py

# Check report for:
# - "A+ discovery results available" ✅
# - Discovery opportunities displayed ✅
# - Market context (VIX, inflation) displayed ✅
```

### Test 2: Backtesting Data
```bash
# Check report for:
# - Backtesting metrics displayed ✅
# - "Backtesting data available" ✅
```

### Test 3: Portfolio Grading
```bash
# Check report for:
# - AAPL, MSFT, ASML grades (should be A or B, not D) ✅
# - Clear indication of analysis depth ✅
```

---

## Root Cause Analysis

**Why is this happening?**

The report crew was designed to work independently by reading files directly. However, the Flow architecture passes data through state, not files. This creates a disconnect:

1. **Flow State** → Contains all data from crews
2. **Report Crew** → Ignores Flow state, reads files directly
3. **Result** → Report crew can't find data that's already in memory

**The Fix**: Report crew should prioritize Flow state inputs over file-based checking.

---

## Success Criteria

After fixes:
- ✅ Discovery status shows "available" when discovery ran
- ✅ A+ opportunities displayed in report
- ✅ Market context (VIX, inflation, rates) displayed
- ✅ Backtesting metrics displayed
- ✅ High-quality stocks (AAPL, MSFT, ASML) show appropriate grades
- ✅ Data availability summary shows freshness status
- ✅ No "data not available" messages when data exists

---

**Created**: 2025-01-09
**Priority**: CRITICAL
**Estimated Total Effort**: 10-15 hours
