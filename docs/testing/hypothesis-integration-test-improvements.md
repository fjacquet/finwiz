# Hypothesis Property-Based Testing for Integration Tests

**Date**: 2025-11-22  
**Status**: Proposal  
**Author**: AI Analysis

## Executive Summary

This document evaluates the current integration test suite for the Hybrid Analysis Flow and proposes comprehensive improvements using Hypothesis property-based testing. The current tests (17 total) use example-based testing with hardcoded values. By adopting property-based testing, we can:

- **10-100x more test coverage** with the same code
- **Discover edge cases** we haven't thought of
- **Reduce test maintenance** by removing hardcoded values
- **Improve test quality** with invariant-based assertions

## Current Test Suite Analysis

### Test Files (1,494 total lines)

- `test_hybrid_analysis_performance.py` (135 lines, 5 tests) - ✅ ALL PASSING
- `test_hybrid_analysis_e2e.py` (462 lines, 9 tests) - ✅ ALL PASSING
- `test_hybrid_analysis_reliability.py` (466 lines, 8 tests) - ⚠️ 3/8 PASSING
- `test_hybrid_analysis_quality.py` (431 lines, ~10 tests) - Status unknown

### Current Problems

#### 1. **Hardcoded Test Data**

```python
# ❌ Current approach
tickers = [f"TICK{i:02d}" for i in range(100)]  # Always same tickers
batch_size = 100  # Always same size
```

**Issues**:

- Always tests with same 100 tickers
- Doesn't test edge cases (1 ticker, 1000 tickers, empty batch)
- Can't find bugs that only appear with specific ticker formats

#### 2. **Brittle Mocks**

```python
# ❌ Current approach - breaks when schema changes
mock_analysis = QuantitativeAnalysis(
    composite_score=0.85,  # Hardcoded
    fundamental_score=0.90,  # Hardcoded
    # ...
)
```

**Issues**:

- Test fails when schema adds required fields
- Doesn't test score ranges (0.0-1.0)
- Doesn't validate relationships (fundamental + technical = composite?)

#### 3. **Success Rate Tests Are Deterministic**

```python
# ❌ Current - always passes with mock
assert success_rate >= 0.95  # Always 100% with perfect mock
```

**Issues**:

- Mock always succeeds, so test is meaningless
- Doesn't test actual reliability under various conditions
- Can't detect race conditions or timing issues

## Hypothesis Improvement Proposals

### Phase 1: Convert Batch Processing Tests (2-4 hours)

#### Current Test

```python
def test_should_achieve_95_percent_success_rate(self, mock_hybrid_flow_complete):
    batch_size = 100
    tickers = [f"TICK{i:02d}" for i in range(batch_size)]
    # ... hardcoded test
```

#### Improved with Hypothesis

```python
from hypothesis import given, settings
from hypothesis import strategies as st

@given(
    batch_size=st.integers(min_value=1, max_value=200),
    failure_rate=st.floats(min_value=0.0, max_value=0.05),  # 0-5% failures
)
@settings(max_examples=50, deadline=30000)  # 50 random scenarios
def test_should_achieve_95_percent_success_rate_property(
    self, mock_hybrid_flow_complete, batch_size, failure_rate
):
    """
    PROPERTY: Success rate ≥ 95% for ANY batch size with ≤5% random failures.

    Hypothesis will generate 50 different scenarios:
    - batch_size could be: 1, 50, 100, 127, 199, etc.
    - failure_rate could be: 0.0%, 2.3%, 4.8%, etc.
    """
    # Arrange - Create mock that fails at the specified rate
    successful = 0
    failed = 0

    for i in range(batch_size):
        # Simulate random failure based on failure_rate
        if random.random() < failure_rate:
            failed += 1
        else:
            flow = HybridAnalysisFlow()
            flow.state.ticker = f"TICK{i:04d}"
            flow.state.asset_class = "stock"
            flow.state.company_name = f"Company {i}"
            result = flow.kickoff()

            if isinstance(result, EnrichedAnalysis):
                successful += 1
            else:
                failed += 1

    # Assert - PROPERTY: success rate should be ≥ 95% when failure rate ≤ 5%
    actual_success_rate = successful / batch_size if batch_size > 0 else 1.0
    expected_min_success = 1.0 - failure_rate

    assert actual_success_rate >= expected_min_success * 0.95, (
        f"Success rate {actual_success_rate:.1%} below expected "
        f"{expected_min_success * 0.95:.1%} for batch_size={batch_size}, "
        f"failure_rate={failure_rate:.1%}"
    )
```

**Benefits**:

- Tests 50 different batch sizes (not just 100)
- Tests various failure rates (0-5%)
- Finds edge cases: batch_size=1, failure_rate=4.99%
- **If it fails**, Hypothesis shrinks to minimal failing example

### Phase 2: Property-Based Mock Generation (4-6 hours)

Create custom Hypothesis strategies for realistic test data:

```python
from hypothesis import strategies as st

# Strategy: Valid ticker symbols
@st.composite
def ticker_strategy(draw):
    """Generate realistic ticker symbols."""
    length = draw(st.integers(min_value=1, max_value=5))
    return draw(st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Nd")),
        min_size=length,
        max_size=length
    ))

# Strategy: Valid EnrichedAnalysis results
@st.composite
def enriched_analysis_strategy(draw):
    """Generate valid EnrichedAnalysis with property-based constraints."""
    # Scores must be in valid ranges
    fundamental_score = draw(st.floats(min_value=0.0, max_value=1.0))
    technical_score = draw(st.floats(min_value=0.0, max_value=1.0))

    # PROPERTY: Composite score is weighted average
    composite_score = (fundamental_score * 0.6 + technical_score * 0.4)

    # PROPERTY: Grade derived from composite score
    if composite_score >= 0.9:
        grade = draw(st.sampled_from(["A+", "A"]))
    elif composite_score >= 0.8:
        grade = draw(st.sampled_from(["A-", "B+"]))
    # ... etc

    return create_complete_enriched_analysis(
        composite_score=composite_score,
        fundamental_score=fundamental_score,
        technical_score=technical_score,
        grade=grade,
        # ... all fields generated with valid relationships
    )

# Use in tests
@given(analysis=enriched_analysis_strategy())
def test_enriched_analysis_invariants(self, analysis):
    """PROPERTY: EnrichedAnalysis always maintains score/grade consistency."""
    # Invariant 1: Composite score in valid range
    assert 0.0 <= analysis.final_score <= 1.0

    # Invariant 2: Grade matches score
    if analysis.final_score >= 0.9:
        assert analysis.final_grade in ["A+", "A"]
    elif analysis.final_score >= 0.8:
        assert analysis.final_grade in ["A-", "B+", "B"]
    # ... etc

    # Invariant 3: Report meets minimum word count
    assert analysis.report_word_count >= 2000
```

**Benefits**:

- Tests with 100 different valid `EnrichedAnalysis` objects
- Validates invariants (score ↔ grade consistency)
- Finds schema violations automatically
- **Self-documenting**: Properties show business rules

### Phase 3: Performance Property Tests (3-4 hours)

```python
@given(
    num_holdings=st.integers(min_value=1, max_value=100),
    batch_size=st.integers(min_value=1, max_value=10),
)
@settings(max_examples=30, deadline=60000)
def test_processing_time_scales_linearly_property(
    self, mock_hybrid_flow_complete, num_holdings, batch_size
):
    """
    PROPERTY: Processing time should scale linearly with holdings.

    Time(n holdings) ≈ Time(1 holding) * n / batch_size
    """
    # Baseline: Time for single holding
    start = time.time()
    flow = HybridAnalysisFlow()
    flow.state.ticker = "BASE"
    flow.state.asset_class = "stock"
    result = flow.kickoff()
    baseline_time = time.time() - start

    # Batch: Time for N holdings
    start = time.time()
    for i in range(num_holdings):
        flow = HybridAnalysisFlow()
        flow.state.ticker = f"TICK{i}"
        flow.state.asset_class = "stock"
        result = flow.kickoff()
    batch_time = time.time() - start

    # PROPERTY: Should scale linearly (within 20% variance)
    expected_time = baseline_time * num_holdings / batch_size
    variance_allowed = 0.20

    assert batch_time <= expected_time * (1 + variance_allowed), (
        f"Processing {num_holdings} holdings took {batch_time:.2f}s, "
        f"expected ~{expected_time:.2f}s (baseline: {baseline_time:.2f}s)"
    )
```

**Benefits**:

- Tests performance with random holdings counts (1-100)
- Validates linear scaling assumption
- Detects performance regressions automatically
- **If it fails**, shows minimal example: "fails at 47 holdings"

### Phase 4: Fallback Mechanism Properties (2-3 hours)

```python
@given(
    crew_failure_rate=st.floats(min_value=0.0, max_value=1.0),
    data_failure_rate=st.floats(min_value=0.0, max_value=1.0),
)
@settings(max_examples=40)
def test_fallback_always_produces_result_property(
    self, mocker, crew_failure_rate, data_failure_rate
):
    """
    PROPERTY: System ALWAYS produces a result, even with failures.

    Fallback cascade:
    1. Full analysis (Python + AI) - ideal
    2. Python-only analysis - fallback
    3. Minimal analysis - ultimate fallback
    """
    # Mock with random failures
    def mock_crew_with_failures(*args, **kwargs):
        if random.random() < crew_failure_rate:
            raise Exception("Crew failed")
        return create_qualitative_insights()

    def mock_data_with_failures(*args, **kwargs):
        if random.random() < data_failure_rate:
            raise Exception("Data collection failed")
        return create_fundamental_data()

    mocker.patch("...crew...", side_effect=mock_crew_with_failures)
    mocker.patch("...data...", side_effect=mock_data_with_failures)

    # Act
    flow = HybridAnalysisFlow()
    flow.state.ticker = "AAPL"
    flow.state.asset_class = "stock"
    result = flow.kickoff()

    # PROPERTY: ALWAYS get a result (never None, never exception)
    assert result is not None
    assert isinstance(result, EnrichedAnalysis)

    # PROPERTY: Confidence reflects data quality
    if crew_failure_rate > 0.5 or data_failure_rate > 0.5:
        assert result.recommendation_confidence in ["LOW", "MEDIUM"]

    # PROPERTY: Minimal viable analysis
    assert result.ticker is not None
    assert result.final_recommendation in ["BUY", "HOLD", "SELL"]
```

**Benefits**:

- Tests ALL possible failure combinations
- Validates fallback cascade works
- Ensures system never crashes (no uncaught exceptions)
- **Hypothesis finds the breaking point**: "fails when crew=87% AND data=92%"

## Implementation Plan

### Phase 1: Quick Wins (Week 1)

1. ✅ Convert batch processing tests to property-based
2. ✅ Add ticker generation strategy
3. ✅ Test with 50-100 random scenarios

**Effort**: 2-4 hours  
**Impact**: Find edge cases in batch processing  
**Risk**: Low - additive, doesn't break existing tests

### Phase 2: Core Strategies (Week 2)

1. ✅ Create `enriched_analysis_strategy()`
2. ✅ Create `quantitative_analysis_strategy()`
3. ✅ Create `qualitative_insights_strategy()`
4. ✅ Validate score/grade invariants

**Effort**: 4-6 hours  
**Impact**: Catch schema violations, validate business rules  
**Risk**: Low - complements existing property tests

### Phase 3: Performance Properties (Week 3)

1. ✅ Add linear scaling tests
2. ✅ Add cost estimation properties
3. ✅ Add memory usage invariants

**Effort**: 3-4 hours  
**Impact**: Detect performance regressions early  
**Risk**: Medium - requires performance baseline

### Phase 4: Reliability Properties (Week 4)

1. ✅ Add fallback mechanism properties
2. ✅ Add error recovery properties
3. ✅ Add concurrent execution tests

**Effort**: 2-3 hours  
**Impact**: Validate system resilience  
**Risk**: Medium - may expose real bugs

## Comparison: Before vs After

### Before (Example-Based)

```python
def test_should_achieve_95_percent_success_rate(self):
    # Tests exactly 1 scenario
    batch_size = 100
    tickers = ["TICK00", "TICK01", ..., "TICK99"]
    # ...
```

**Coverage**: 1 scenario  
**Edge cases**: None  
**Maintenance**: High (hardcoded values)  
**Failure debugging**: "Test failed" (no context)

### After (Property-Based)

```python
@given(batch_size=st.integers(1, 200), failure_rate=st.floats(0.0, 0.05))
@settings(max_examples=50)
def test_should_achieve_95_percent_success_rate_property(self, batch_size, failure_rate):
    # Tests 50 random scenarios
    # ...
```

**Coverage**: 50 scenarios per run  
**Edge cases**: Automatically discovered  
**Maintenance**: Low (generates data)  
**Failure debugging**: "Fails with batch_size=47, failure_rate=0.0423" (minimal example)

## Expected Outcomes

### Quantitative Benefits

- **10-100x test coverage** (50-100 scenarios vs 1)
- **90% reduction** in hardcoded test data
- **50% faster** test writing (strategies reusable)
- **Edge case discovery**: 5-10 new bugs expected

### Qualitative Benefits

- **Better documentation**: Properties describe business rules
- **Regression prevention**: Catches schema changes automatically
- **Confidence**: "Tested with 5,000 random inputs" vs "tested with 10 examples"
- **Maintainability**: No more updating hardcoded values when schemas change

## Risks and Mitigations

### Risk 1: Slower Test Execution

**Mitigation**: Use `@settings(max_examples=20)` for fast feedback, `max_examples=100` for CI

### Risk 2: Flaky Tests

**Mitigation**: Use `@settings(derandomize=True)` for deterministic runs, seed control

### Risk 3: Hard to Debug Failures

**Mitigation**: Hypothesis automatically shrinks to minimal failing example

### Risk 4: Learning Curve

**Mitigation**: Start with simple strategies, reuse existing property test patterns from `tests/property/`

## Conclusion

The current integration tests provide basic coverage but miss edge cases and are brittle. By adopting Hypothesis property-based testing:

1. **We test 10-100x more scenarios** with the same code
2. **We find bugs** we didn't know existed
3. **We reduce maintenance** by eliminating hardcoded values
4. **We improve confidence** with invariant-based testing

**Recommendation**: Implement Phase 1 (Quick Wins) immediately. The existing property test infrastructure in `tests/property/` shows the team already understands Hypothesis - we should extend this to integration tests.

**Next Steps**:

1. Review this proposal with team
2. Implement Phase 1 (batch processing) as proof of concept
3. Measure results (edge cases found, test coverage increase)
4. Decide on Phases 2-4 based on Phase 1 outcomes
