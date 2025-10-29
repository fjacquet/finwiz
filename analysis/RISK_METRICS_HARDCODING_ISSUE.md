# Risk Metrics Hardcoding Issue Analysis

## Problem Statement

All risk analyses across ETF, crypto, and stock assets show identical values:

- **Volatilité Annuelle**: 20.0%
- **Drawdown Maximum**: -15.0%

This suggests hardcoded default values are being used instead of actual calculated metrics.

## Root Cause Analysis

### 1. Default Values in Deep Analysis Scorer

**Location**: `src/finwiz/scoring/deep_analysis_scorer.py` (lines 474, 490)

```python
# Line 474: Default volatility
volatility = self._safe_get_float(data, "volatility", 0.20)  # 20% default

# Line 490: Default max drawdown  
max_drawdown = self._safe_get_float(data, "max_drawdown", -0.20)  # -20% default
```

**Why this happens**:

- When `data` dict doesn't contain "volatility" or "max_drawdown" keys
- The `_safe_get_float()` method returns the default value (0.20 and -0.20)
- These defaults are then used for scoring and displayed in reports

### 2. Data Flow Chain

```
QuantitativeAnalysisTool
  ↓ (calculates real metrics)
PerformanceMetrics
  ↓ (volatility, max_drawdown calculated correctly)
DeepAnalysisScorer
  ↓ (expects data dict with these keys)
❌ MISSING: Data not properly passed to scorer
  ↓ (falls back to defaults)
Default values used: 0.20, -0.20
```

### 3. Actual Calculation Code (CORRECT)

**Location**: `src/finwiz/quantitative/performance_metrics.py` (lines 90, 156-180)

```python
# Line 90: Volatility calculation (CORRECT)
volatility = returns.std() * np.sqrt(252)

# Lines 156-180: Max drawdown calculation (CORRECT)
def calculate_max_drawdown(self, returns: pd.Series) -> tuple[float, int]:
    cumulative = (1 + returns).cumprod()
    running_max = cumulative.expanding().max()
    drawdown = (cumulative - running_max) / running_max
    max_drawdown = drawdown.min()
    # ... duration calculation
    return max_drawdown, max_duration
```

**The calculations are correct** - the issue is in data passing.

## Why All Assets Show Same Values

### Default Values Used Everywhere

When quantitative analysis fails or data is incomplete:

1. **Stock analysis**: Falls back to `volatility=0.20, max_drawdown=-0.20`
2. **ETF analysis**: Falls back to `volatility=0.20, max_drawdown=-0.20`  
3. **Crypto analysis**: Falls back to `volatility=0.20, max_drawdown=-0.20`

### Additional Default Locations

**Location**: `src/finwiz/utils/crew_export_migrator.py` (line 194)

```python
# Extract risk metrics with defaults
volatility = risk_details.get("volatility", 0.2)
max_drawdown = risk_details.get("max_drawdown", -0.15)  # Note: -0.15 here
```

**Location**: `src/finwiz/tools/a_plus_scoring_tool.py` (line 446)

```python
volatility = data.get("volatility", 0.2)
max_drawdown = data.get("max_drawdown", 0.2)
```

## Impact

### User Experience

- ❌ All assets appear to have identical risk profiles
- ❌ Cannot differentiate between low-volatility ETFs and high-volatility crypto
- ❌ Risk assessments are meaningless
- ❌ Investment decisions based on incorrect data

### Data Integrity

- ❌ Real calculated metrics are being discarded
- ❌ Default values mask data collection failures
- ❌ No visibility into which assets have real vs default data

## Solution Strategy

### Immediate Fixes

#### 1. Fix Data Passing in Deep Analysis Crew

**File**: `src/finwiz/crews/deep_analysis/deep_analysis.py`

Ensure quantitative analysis results are properly extracted and passed to scorer:

```python
# Extract from quantitative analysis tool output
quant_data = json.loads(quantitative_result)
performance_metrics = quant_data.get("performance_metrics", {})

# Pass to scorer with explicit keys
data_for_scorer = {
    "volatility": performance_metrics.get("volatility"),
    "max_drawdown": performance_metrics.get("max_drawdown"),
    # ... other metrics
}
```

#### 2. Add Validation Flags

**File**: `src/finwiz/scoring/deep_analysis_scorer.py`

Track when defaults are used:

```python
def _safe_get_float(self, data: dict, key: str, default: float) -> tuple[float, bool]:
    """Return (value, is_default_used)."""
    if key in data and data[key] is not None:
        return float(data[key]), False
    return default, True

# Usage
volatility, vol_is_default = self._safe_get_float(data, "volatility", 0.20)
if vol_is_default:
    logger.warning(f"Using default volatility {volatility} for {ticker}")
    details["volatility_source"] = "default"
else:
    details["volatility_source"] = "calculated"
```

#### 3. Fail Loudly on Missing Data

Instead of silently using defaults, raise warnings or errors:

```python
if "volatility" not in data or data["volatility"] is None:
    raise ValueError(f"Missing volatility data for {ticker}")
```

### Long-term Improvements

#### 1. Schema Validation

Use Pydantic to enforce required fields:

```python
class QuantitativeAnalysisResult(BaseModel):
    volatility: float = Field(..., description="Required: Annualized volatility")
    max_drawdown: float = Field(..., description="Required: Maximum drawdown")
    # ... other required fields
```

#### 2. Data Quality Monitoring

Track data completeness:

```python
class DataQualityMetrics(BaseModel):
    fields_calculated: list[str]
    fields_defaulted: list[str]
    data_completeness_score: float  # 0.0-1.0
```

#### 3. Separate Default Handling

Create explicit fallback strategies:

```python
class RiskMetricsWithQuality(BaseModel):
    volatility: float
    volatility_quality: Literal["calculated", "estimated", "default"]
    max_drawdown: float
    max_drawdown_quality: Literal["calculated", "estimated", "default"]
```

## Testing Strategy

### Unit Tests

```python
def test_should_use_calculated_volatility_not_default(mocker):
    """Verify real volatility is used when available."""
    data = {
        "volatility": 0.35,  # Real value
        "max_drawdown": -0.42  # Real value
    }
    
    scorer = DeepAnalysisScorer()
    result = scorer.calculate_risk_score(data)
    
    assert result["volatility"] == 0.35  # Not 0.20
    assert result["max_drawdown"] == -0.42  # Not -0.20

def test_should_warn_when_using_default_values(mocker, caplog):
    """Verify warnings are logged when defaults are used."""
    data = {}  # Missing volatility and max_drawdown
    
    scorer = DeepAnalysisScorer()
    result = scorer.calculate_risk_score(data)
    
    assert "Using default volatility" in caplog.text
    assert result["volatility"] == 0.20  # Default used
```

### Integration Tests

```python
@pytest.mark.integration
def test_should_calculate_real_risk_metrics_for_stock():
    """End-to-end test with real data."""
    crew = DeepAnalysisCrew()
    result = crew.kickoff(inputs={"ticker": "AAPL", "asset_class": "stock"})
    
    # Verify real metrics, not defaults
    assert result.risk_details["volatility"] != 0.20
    assert result.risk_details["max_drawdown"] != -0.20
    assert result.risk_details["volatility_source"] == "calculated"
```

## Verification Checklist

After implementing fixes:

- [ ] Run deep analysis on 3 different stocks - verify different volatility values
- [ ] Run deep analysis on 3 different ETFs - verify different drawdown values
- [ ] Run deep analysis on 3 different cryptos - verify different risk metrics
- [ ] Check logs for "Using default" warnings - should be minimal
- [ ] Verify HTML reports show asset-specific risk values
- [ ] Confirm data quality flags are populated correctly

## Priority

**CRITICAL** - This affects the core value proposition of FinWiz:

- Risk assessment is a key feature
- Users rely on these metrics for investment decisions
- Current state provides misleading information

## Estimated Effort

- **Investigation**: ✅ Complete
- **Fix implementation**: 2-4 hours
- **Testing**: 2-3 hours
- **Validation**: 1-2 hours
- **Total**: 5-9 hours

## Next Steps

1. ✅ Document the issue (this file)
2. ⏳ Implement data passing fix in deep analysis crew
3. ⏳ Add validation flags and warnings
4. ⏳ Write unit tests for default detection
5. ⏳ Run integration tests with real tickers
6. ⏳ Verify HTML reports show correct values
7. ⏳ Update documentation with data quality indicators

---

**Created**: 2025-10-28  
**Status**: Investigation Complete, Fix Pending  
**Priority**: CRITICAL
