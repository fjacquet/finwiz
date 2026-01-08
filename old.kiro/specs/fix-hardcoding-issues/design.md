# Design Document: Fix Hardcoding Issues

## Overview

This design addresses systematic hardcoding issues in FinWiz that cause grade inflation, identical risk profiles, and loss of data integrity. The solution implements proper data flow from quantitative analysis tools through scoring engines to final reports, with comprehensive data quality tracking and validation.

### Goals

1. **Eliminate Hardcoded Defaults**: Remove all hardcoded risk metrics, grades, and composite scores
2. **Proper Data Flow**: Ensure calculated values flow correctly from tools to scorers to reports
3. **Data Quality Tracking**: Implement comprehensive tracking of calculated vs defaulted vs missing fields
4. **Fail-Loud Validation**: Replace silent failures with explicit errors for missing critical data
5. **User Transparency**: Display data quality indicators in all reports

### Non-Goals

- Changing the grading scale or scoring algorithms
- Modifying the quantitative analysis calculation methods
- Redesigning the UI/UX of reports (only adding quality indicators)
- Changing the CrewAI workflow or task structure

## Architecture

### Current Architecture (Problematic)

```
┌─────────────────────────────────────────────────────────────┐
│ Quantitative Analysis Tool                                   │
│ ✅ Calculates: volatility, max_drawdown, beta               │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ Crew Output (JSON)                                           │
│ ❌ PROBLEM: Data not properly extracted                     │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ Deep Analysis Scorer                                         │
│ ❌ Falls back to defaults: volatility=0.20, grade="A+"      │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ Reports                                                       │
│ ❌ Shows hardcoded values: 20% volatility, A+ grades        │
└─────────────────────────────────────────────────────────────┘
```

### Target Architecture (Fixed)

```
┌─────────────────────────────────────────────────────────────┐
│ Quantitative Analysis Tool                                   │
│ ✅ Calculates: volatility, max_drawdown, beta               │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ Data Extractor (NEW)                                         │
│ ✅ Properly extracts metrics from crew output                │
│ ✅ Validates required fields present                         │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ Deep Analysis Scorer                                         │
│ ✅ Uses actual values                                        │
│ ✅ Tracks data quality (calculated/defaulted/missing)       │
│ ✅ Raises errors for missing critical data                  │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ Reports with Quality Indicators                              │
│ ✅ Shows actual values: 35% volatility, B grade             │
│ ✅ Displays quality: "✅ High quality data"                 │
└─────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. Data Quality Schema (NEW)

**Location**: `src/finwiz/schemas/data_quality.py`

```python
from pydantic import BaseModel, Field
from typing import Literal

class DataQualityMetrics(BaseModel):
    """Track data quality for analysis results."""
    
    fields_calculated: list[str] = Field(
        default_factory=list,
        description="Fields calculated from real data"
    )
    fields_defaulted: list[str] = Field(
        default_factory=list,
        description="Fields using default values"
    )
```

    fields_missing: list[str] = Field(
        default_factory=list,
        description="Fields completely missing"
    )
    completeness_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Ratio of calculated fields to total fields"
    )
    quality_level: Literal["high", "medium", "low"] = Field(
        ...,
        description="Overall quality assessment"
    )
    
    @classmethod
    def calculate(cls, calculated: list[str], defaulted: list[str], 
                  missing: list[str]) -> "DataQualityMetrics":
        """Calculate quality metrics from field lists."""
        total_fields = len(calculated) + len(defaulted) + len(missing)
        completeness = len(calculated) / total_fields if total_fields > 0 else 0.0
        
        # Determine quality level
        if completeness >= 0.9:
            quality_level = "high"
        elif completeness >= 0.7:
            quality_level = "medium"
        else:
            quality_level = "low"
        
        return cls(
            fields_calculated=calculated,
            fields_defaulted=defaulted,
            fields_missing=missing,
            completeness_score=completeness,
            quality_level=quality_level
        )

```

**Interface**: Used by all analysis result schemas (DeepAnalysisResult, etc.)

### 2. Enhanced Deep Analysis Result Schema

**Location**: `src/finwiz/flow_state.py` (modify existing)

```python
from finwiz.schemas.data_quality import DataQualityMetrics

class DeepAnalysisResult(BaseModel):
    """Enhanced with data quality tracking."""
    
    ticker: str
    asset_class: str
    composite_score: float
    grade: str
    
    # Risk metrics (no longer optional with defaults)
    volatility: float | None = Field(None, description="Actual volatility or None")
    max_drawdown: float | None = Field(None, description="Actual max drawdown or None")
    beta: float | None = Field(None, description="Actual beta or None")
    
    # NEW: Data quality tracking
    data_quality: DataQualityMetrics = Field(
        ...,
        description="Quality metrics for this analysis"
    )
    
    # Validation
    @model_validator(mode='after')
    def validate_grade_matches_score(self) -> 'DeepAnalysisResult':
        """Ensure grade matches composite score."""
        expected_grade = self._score_to_grade(self.composite_score)
        if self.grade != expected_grade:
            raise ValueError(
                f"Grade {self.grade} doesn't match score {self.composite_score} "
                f"(expected {expected_grade})"
            )
        return self
```

### 3. Data Extractor Utility (NEW)

**Location**: `src/finwiz/utils/data_extractor.py`

```python
from typing import Any
import json
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)

class CrewDataExtractor:
    """Extract and validate data from crew outputs."""
    
    def extract_quantitative_metrics(self, crew_output: str | dict) -> dict[str, Any]:
        """
        Extract quantitative metrics from crew output.
        
        Raises:
            ValueError: If critical metrics are missing
        """
        # Parse JSON if string
        if isinstance(crew_output, str):
            data = json.loads(crew_output)
        else:
            data = crew_output
        
        # Extract performance metrics
        perf_metrics = data.get("performance_metrics", {})
        
        # Required fields
        required = ["volatility", "max_drawdown"]
        missing = [f for f in required if f not in perf_metrics or perf_metrics[f] is None]
        
        if missing:
            raise ValueError(
                f"Missing required metrics: {missing}. "
                f"Available keys: {list(perf_metrics.keys())}"
            )
        
        return {
            "volatility": float(perf_metrics["volatility"]),
            "max_drawdown": float(perf_metrics["max_drawdown"]),
            "beta": perf_metrics.get("beta"),  # Optional
            "sharpe_ratio": perf_metrics.get("sharpe_ratio"),
            "sortino_ratio": perf_metrics.get("sortino_ratio"),
        }
```

### 4. Enhanced Deep Analysis Scorer

**Location**: `src/finwiz/scoring/deep_analysis_scorer.py` (modify existing)

**Key Changes**:

1. Remove default values from `_safe_get_float()`
2. Track which fields are calculated vs missing
3. Raise errors for missing critical fields
4. Return data quality metrics

```python
class DeepAnalysisScorer:
    """Enhanced with data quality tracking."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self._calculated_fields: list[str] = []
        self._missing_fields: list[str] = []
    
    def _get_required_float(self, data: dict, key: str, ticker: str) -> float:
        """
        Get required float value, raise error if missing.
        
        Raises:
            ValueError: If key is missing or None
        """
        if key not in data or data[key] is None:
            self.logger.error(f"Missing required field '{key}' for {ticker}")
            self._missing_fields.append(key)
            raise ValueError(f"Missing required field '{key}' for {ticker}")
        
        self._calculated_fields.append(key)
        return float(data[key])
    
    def calculate_risk_score(self, data: dict, ticker: str) -> tuple[float, dict]:
        """
        Calculate risk score with data quality tracking.
        
        Returns:
            Tuple of (risk_score, details_dict)
        
        Raises:
            ValueError: If critical risk metrics are missing
        """
        details = {}
        
        # Reset tracking
        self._calculated_fields = []
        self._missing_fields = []
        
        # Get required metrics (will raise if missing)
        volatility = self._get_required_float(data, "volatility", ticker)
        max_drawdown = self._get_required_float(data, "max_drawdown", ticker)
        
        # Calculate scores
        vol_score = self._calculate_volatility_score(volatility)
        drawdown_score = self._calculate_drawdown_score(max_drawdown)
        
        details["volatility"] = volatility
        details["max_drawdown"] = max_drawdown
        details["volatility_score"] = vol_score
        details["drawdown_score"] = drawdown_score
        
        # Overall risk score
        risk_score = (vol_score + drawdown_score) / 2
        
        return risk_score, details
```

### 5. Alternative Finder Enhancements

**Location**: `src/finwiz/tools/alternative_finder_tool.py` (modify existing)

**Key Changes**:

1. Remove `grade` default value
2. Validate grade is present
3. Raise error if missing

```python
def _extract_alternative_data(self, item: dict) -> dict:
    """
    Extract alternative data with validation.
    
    Raises:
        ValueError: If required fields are missing
    """
    ticker = item.get("ticker")
    if not ticker:
        raise ValueError("Alternative missing 'ticker' field")
    
    # Require explicit grade (no default)
    if "grade" not in item or item["grade"] is None:
        raise ValueError(f"Alternative {ticker} missing 'grade' field")
    
    # Require explicit composite_score (no default)
    if "composite_score" not in item or item["composite_score"] is None:
        raise ValueError(f"Alternative {ticker} missing 'composite_score' field")
    
    return {
        "ticker": ticker,
        "name": item.get("name", ticker),
        "grade": item["grade"],
        "composite_score": float(item["composite_score"]),
    }
```

### 6. Flow Orchestrator Enhancements

**Location**: `src/finwiz/flows/flow_orchestrator.py` (modify existing)

**Key Changes**:

1. Remove default composite_score and grade
2. Use data extractor to parse crew output
3. Validate extracted data
4. Track data quality

```python
from finwiz.utils.data_extractor import CrewDataExtractor

class FinwizFlow(Flow[FinwizState]):
    
    def __init__(self):
        super().__init__()
        self.data_extractor = CrewDataExtractor()
    
    def _process_deep_analysis_result(self, crew_result: Any, ticker: str) -> DeepAnalysisResult:
        """
        Process crew result with proper data extraction and validation.
        
        Raises:
            ValueError: If critical data is missing
        """
        # Extract data using utility
        try:
            metrics = self.data_extractor.extract_quantitative_metrics(crew_result)
        except ValueError as e:
            logger.error(f"Failed to extract metrics for {ticker}: {e}")
            raise
        
        # Extract grade and score
        if not hasattr(crew_result, "grade") or crew_result.grade is None:
            raise ValueError(f"Missing grade for {ticker}")
        
        if not hasattr(crew_result, "composite_score") or crew_result.composite_score is None:
            raise ValueError(f"Missing composite_score for {ticker}")
        
        # Build result with data quality
        return DeepAnalysisResult(
            ticker=ticker,
            grade=crew_result.grade,
            composite_score=crew_result.composite_score,
            volatility=metrics["volatility"],
            max_drawdown=metrics["max_drawdown"],
            beta=metrics.get("beta"),
            data_quality=self._calculate_data_quality(metrics)
        )
```

## Data Models

### DataQualityMetrics Schema

```python
{
    "fields_calculated": ["volatility", "max_drawdown", "composite_score", "grade"],
    "fields_defaulted": [],
    "fields_missing": ["beta"],
    "completeness_score": 0.8,
    "quality_level": "high"
}
```

### Enhanced DeepAnalysisResult

```python
{
    "ticker": "AAPL",
    "asset_class": "stock",
    "composite_score": 0.78,
    "grade": "B+",
    "volatility": 0.24,  # Actual calculated value
    "max_drawdown": -0.18,  # Actual calculated value
    "beta": 1.15,
    "data_quality": {
        "fields_calculated": ["volatility", "max_drawdown", "beta", "composite_score"],
        "fields_defaulted": [],
        "fields_missing": [],
        "completeness_score": 1.0,
        "quality_level": "high"
    }
}
```

## Error Handling

### Error Hierarchy

```python
class DataQualityError(Exception):
    """Base exception for data quality issues."""
    pass

class MissingRequiredFieldError(DataQualityError):
    """Raised when required field is missing."""
    
    def __init__(self, ticker: str, field: str, context: dict = None):
        self.ticker = ticker
        self.field = field
        self.context = context or {}
        message = f"Missing required field '{field}' for {ticker}"
        super().__init__(message)

class GradeScoreMismatchError(DataQualityError):
    """Raised when grade doesn't match composite score."""
    
    def __init__(self, ticker: str, grade: str, score: float, expected_grade: str):
        self.ticker = ticker
        self.grade = grade
        self.score = score
        self.expected_grade = expected_grade
        message = (
            f"Grade mismatch for {ticker}: "
            f"grade={grade}, score={score}, expected={expected_grade}"
        )
        super().__init__(message)
```

### Error Handling Strategy

1. **Critical Fields**: Raise `MissingRequiredFieldError`
   - grade, composite_score, volatility, max_drawdown

2. **Optional Fields**: Set to None, track in data_quality
   - beta, sharpe_ratio, sortino_ratio

3. **Validation Errors**: Raise `GradeScoreMismatchError`
   - Grade doesn't match score

4. **Logging**: All errors logged with full context
   - Ticker, asset_class, missing fields, attempted operation

## Testing Strategy

### Unit Tests

**Test File**: `tests/unit/test_data_quality.py`

```python
def test_should_raise_error_when_volatility_missing():
    """Verify error raised for missing volatility."""
    data = {"max_drawdown": -0.15}  # Missing volatility
    
    scorer = DeepAnalysisScorer()
    
    with pytest.raises(MissingRequiredFieldError) as exc_info:
        scorer.calculate_risk_score(data, "AAPL")
    
    assert exc_info.value.field == "volatility"
    assert exc_info.value.ticker == "AAPL"

def test_should_track_calculated_fields():
    """Verify data quality tracking."""
    data = {
        "volatility": 0.25,
        "max_drawdown": -0.18,
        "beta": 1.15
    }
    
    scorer = DeepAnalysisScorer()
    score, details = scorer.calculate_risk_score(data, "AAPL")
    
    assert "volatility" in scorer._calculated_fields
    assert "max_drawdown" in scorer._calculated_fields
    assert len(scorer._missing_fields) == 0
```

### Integration Tests

**Test File**: `tests/integration/test_hardcoding_fixes.py`

```python
@pytest.mark.integration
def test_should_calculate_unique_risk_metrics():
    """Verify different assets have different risk metrics."""
    tickers = ["AAPL", "TSLA", "SPY", "BTC-USD", "ETH-USD"]
    results = []
    
    for ticker in tickers:
        crew = DeepAnalysisCrew()
        result = crew.kickoff(inputs={"ticker": ticker, "asset_class": "stock"})
        results.append(result)
    
    # Verify volatility values are unique
    volatilities = [r.volatility for r in results]
    assert len(set(volatilities)) == len(volatilities), "Volatilities should be unique"
    
    # Verify no hardcoded 0.20 value
    assert 0.20 not in volatilities, "Should not use hardcoded 0.20"

@pytest.mark.integration  
def test_should_have_realistic_grade_distribution():
    """Verify realistic grade distribution."""
    # Analyze 20 random stocks
    results = analyze_random_stocks(count=20)
    
    grade_counts = Counter(r.grade for r in results)
    
    # Should not be >50% A+
    a_plus_pct = grade_counts.get("A+", 0) / len(results)
    assert a_plus_pct < 0.5, f"Too many A+ grades: {a_plus_pct:.1%}"
    
    # Should have variety
    assert len(grade_counts) >= 3, "Should have at least 3 different grades"
```

## Deployment Strategy

### Phase 1: Risk Metrics (Week 1)

**Goal**: Fix risk metrics data flow

**Changes**:

- Add `CrewDataExtractor` utility
- Modify `DeepAnalysisScorer` to use extractor
- Add error handling for missing metrics
- Add logging for data quality

**Validation**:

- Run on 10 test tickers
- Verify unique volatility/drawdown values
- Check logs for warnings

**Rollback**: Feature flag `STRICT_RISK_VALIDATION=false`

### Phase 2: Grades and Scores (Week 2)

**Goal**: Fix grade and composite score defaults

**Changes**:

- Remove grade defaults from Alternative Finder
- Remove score defaults from Flow Orchestrator
- Add validation for grade-score matching
- Implement `DataQualityMetrics` schema

**Validation**:

- Run portfolio analysis on 5 portfolios
- Verify realistic grade distribution
- Check data quality metrics

**Rollback**: Feature flag `STRICT_GRADE_VALIDATION=false`

### Phase 3: UI Indicators (Week 3)

**Goal**: Add data quality indicators to reports

**Changes**:

- Update HTML templates with quality indicators
- Add hover tooltips for field details
- Style quality badges (high/medium/low)

**Validation**:

- Generate 10 test reports
- Verify quality indicators display correctly
- Test in light/dark mode

**Rollback**: Feature flag `SHOW_QUALITY_INDICATORS=false`

## Monitoring and Metrics

### Key Metrics to Track

1. **Grade Distribution**
   - Target: A+ < 10%, A < 20%, B < 40%, C < 30%, D/F < 10%
   - Alert: If A+ > 50%

2. **Data Quality**
   - Target: >80% high quality analyses
   - Alert: If <60% high quality

3. **Error Rate**
   - Target: <5% MissingRequiredFieldError
   - Alert: If >10% error rate

4. **Risk Metric Variance**
   - Target: Volatility std dev > 0.05
   - Alert: If all values within 0.02 range

### Logging Strategy

```python
# INFO: Successful analysis
logger.info(
    f"Analysis complete for {ticker}: "
    f"grade={grade}, score={score:.2f}, "
    f"quality={quality_level} ({completeness:.1%})"
)

# WARNING: Using defaults
logger.warning(
    f"Low data quality for {ticker}: "
    f"calculated={len(calculated)}, "
    f"missing={len(missing)}, "
    f"completeness={completeness:.1%}"
)

# ERROR: Missing required data
logger.error(
    f"Missing required fields for {ticker}: {missing_fields}. "
    f"Available: {list(data.keys())}"
)
```

## Success Criteria

### Quantitative Metrics

1. **Risk Metrics Variance**
   - ✅ Volatility std dev > 0.05 across 20 test assets
   - ✅ Max drawdown std dev > 0.05 across 20 test assets
   - ✅ No hardcoded 0.20 or -0.15 values in outputs

2. **Grade Distribution**
   - ✅ A+ grades < 15% of total
   - ✅ At least 4 different grades in 20-asset sample
   - ✅ Grade matches composite score in 100% of cases

3. **Data Quality**
   - ✅ >80% of analyses have "high" quality
   - ✅ <5% of analyses fail with missing data errors
   - ✅ All analyses include data_quality metrics

### Qualitative Metrics

1. **User Trust**
   - ✅ Reduced "why is everything A+?" support tickets
   - ✅ Positive feedback on analysis accuracy
   - ✅ Increased engagement with recommendations

2. **Developer Experience**
   - ✅ Clear error messages for debugging
   - ✅ Consistent data handling patterns
   - ✅ Easy to add new quality checks

## Migration Path

### Backward Compatibility

During rollout, support both old and new behavior:

```python
# Feature flag for gradual rollout
STRICT_VALIDATION = os.getenv("STRICT_DATA_VALIDATION", "false").lower() == "true"

def get_grade(item: dict, ticker: str) -> str:
    """Get grade with optional strict validation."""
    if "grade" not in item or item["grade"] is None:
        if STRICT_VALIDATION:
            raise MissingRequiredFieldError(ticker, "grade")
        else:
            logger.warning(f"Missing grade for {ticker}, using fallback")
            return "C"  # Conservative fallback
    return item["grade"]
```

### Deprecation Timeline

- **Week 1-2**: Deploy with `STRICT_VALIDATION=false` (warnings only)
- **Week 3-4**: Enable `STRICT_VALIDATION=true` in staging
- **Week 5**: Enable in production
- **Week 6**: Remove feature flags and old code

---

**Version**: 1.0  
**Created**: 2025-10-28  
**Status**: Design Complete
