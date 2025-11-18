# FinWiz Code Refactoring Roadmap

**Created**: 2025-11-14  
**Status**: Planning Phase  
**Estimated Effort**: 3-4 weeks  
**Risk Level**: Medium

## Executive Summary

This roadmap addresses architectural and code quality issues identified in the FinWiz codebase. The primary focus is on reducing code duplication, improving maintainability, and applying proper design patterns while preserving all existing functionality.

**Key Metrics:**

- **Code Reduction**: ~40% (from ~2,000 to ~1,200 lines in affected files)
- **Maintainability**: Significantly improved through focused classes
- **Test Coverage**: Maintain 80%+ coverage throughout refactoring
- **Performance**: Minimal impact (structural improvements only)

## Phase 1: High Priority Refactoring (Week 1-2)

### 1.1 Split DeepAnalysisScorer God Class

**File**: `src/finwiz/scoring/deep_analysis_scorer.py`  
**Current**: 1,301 lines, 30+ methods  
**Target**: 4 focused classes (~300 lines each)

**Tasks:**

- [ ] Create `FundamentalScorer` class
  - Extract stock/ETF/crypto fundamental scoring logic
  - Move ROE, debt, growth, expense ratio calculations
  - Estimated: 300 lines

- [ ] Create `TechnicalScorer` class
  - Extract technical analysis scoring logic
  - Move RSI, MACD, trend analysis calculations
  - Estimated: 200 lines

- [ ] Create `RiskScorer` class
  - Extract risk assessment scoring logic
  - Move volatility, drawdown, beta calculations
  - Estimated: 200 lines

- [ ] Refactor `DeepAnalysisScorer` as orchestrator
  - Coordinate between component scorers
  - Handle result aggregation
  - Estimated: 400 lines

**Benefits:**

- Single Responsibility Principle compliance
- Easier to test individual components
- Clearer code organization
- Reduced cognitive load

**Testing Strategy:**

- Create unit tests for each new class
- Maintain integration tests for orchestrator
- Verify identical outputs before/after refactoring

---

### 1.2 Implement Strategy Pattern for Asset-Specific Logic

**File**: `src/finwiz/scoring/deep_analysis_scorer.py`  
**Current**: 8+ methods with repeated `if asset_class == "stock"` conditionals  
**Target**: 3 strategy classes + 1 factory

**Tasks:**

- [ ] Create `AssetAnalyzer` abstract base class
  - Define interface for fundamental scoring
  - Define interface for metric extraction
  - Define interface for data validation


- [ ] Implement `StockAnalyzer` strategy
  - ROE, debt-to-equity, revenue growth logic
  - Stock-specific metric extraction
  - Estimated: 150 lines

- [ ] Implement `ETFAnalyzer` strategy
  - Expense ratio, tracking error logic
  - ETF-specific metric extraction
  - Estimated: 150 lines

- [ ] Implement `CryptoAnalyzer` strategy
  - Market cap, volume, age logic
  - Crypto-specific metric extraction
  - Estimated: 150 lines

- [ ] Create `AnalyzerFactory` class
  - Map asset_class to analyzer implementation
  - Handle unknown asset classes gracefully
  - Estimated: 50 lines

**Benefits:**

- Eliminates 200+ lines of duplicate conditional logic
- Easy to add new asset classes
- Clearer separation of concerns
- Improved testability

**Testing Strategy:**

- Unit test each analyzer independently
- Test factory with valid/invalid asset classes
- Integration tests for end-to-end flow

---

### 1.3 Extract Scoring Thresholds to Configuration

**File**: `src/finwiz/scoring/deep_analysis_scorer.py`  
**Current**: Magic numbers scattered across 15+ methods  
**Target**: Centralized configuration class

**Tasks:**

- [ ] Create `ScoringThresholds` dataclass
  - ROE thresholds (excellent, very good, good, acceptable)
  - Debt thresholds (very low, low, moderate, high)
  - Growth thresholds
  - Expense ratio thresholds
  - Volatility thresholds
  - All other scoring thresholds
  - Estimated: 100 lines


- [ ] Update all scoring methods to use thresholds
  - Replace hardcoded values with threshold references
  - Ensure backward compatibility
  - Estimated: 2 hours

- [ ] Add configuration loading from YAML/JSON (optional)
  - Allow runtime threshold tuning
  - Support A/B testing of thresholds
  - Estimated: 4 hours

**Benefits:**

- Single source of truth for thresholds
- Easy to tune scoring parameters
- Better documentation of scoring logic
- Supports experimentation

**Testing Strategy:**

- Test with default thresholds
- Test with custom thresholds
- Verify score consistency

---

### 1.4 Eliminate Duplicate JSON Parsing in APlusExtractor

**File**: `src/finwiz/integration/aplus_extractor.py`  
**Current**: Same JSON loading pattern in 3 methods (~200 lines duplicated)  
**Target**: Single reusable helper method

**Tasks:**

- [ ] Create `_load_and_parse_json()` helper method
  - Handle file existence checks
  - Handle empty file cases
  - Clean JSON content
  - Parse and validate structure
  - Estimated: 50 lines

- [ ] Refactor `_extract_stock_opportunities()`
  - Use new helper method
  - Reduce from ~100 lines to ~30 lines

- [ ] Refactor `_extract_etf_opportunities()`
  - Use new helper method
  - Reduce from ~100 lines to ~30 lines

- [ ] Refactor `_extract_crypto_opportunities()`
  - Use new helper method
  - Reduce from ~100 lines to ~30 lines


**Benefits:**

- Eliminates 200+ lines of duplicate code
- Consistent error handling
- Single point of maintenance
- Easier to add new opportunity types

**Testing Strategy:**

- Test with valid JSON files
- Test with missing files
- Test with empty files
- Test with malformed JSON
- Verify identical output before/after

---

### 1.5 Apply Template Method Pattern to Opportunity Extraction

**File**: `src/finwiz/integration/aplus_extractor.py`  
**Current**: 90% identical logic across 3 extraction methods  
**Target**: Base class + 3 concrete implementations

**Tasks:**

- [ ] Create `OpportunityExtractor` abstract base class
  - Define template method `extract()`
  - Define abstract methods: `_should_include()`, `_build_opportunity()`
  - Estimated: 80 lines

- [ ] Implement `StockOpportunityExtractor`
  - Stock-specific inclusion logic
  - Stock-specific opportunity building
  - Estimated: 60 lines

- [ ] Implement `ETFOpportunityExtractor`
  - ETF-specific inclusion logic
  - ETF-specific opportunity building
  - Estimated: 60 lines

- [ ] Implement `CryptoOpportunityExtractor`
  - Crypto-specific inclusion logic
  - Crypto-specific opportunity building
  - Estimated: 60 lines

- [ ] Update `APlusDataExtractor` to use extractors
  - Instantiate appropriate extractor
  - Call extract method
  - Estimated: 30 lines


**Benefits:**

- Reduces ~300 lines to ~290 lines (but much clearer)
- Eliminates duplicate extraction logic
- Easy to add new asset types
- Follows Open/Closed Principle

**Testing Strategy:**

- Test each extractor independently
- Verify identical output for each asset type
- Test with edge cases (missing fields, invalid data)

---

## Phase 2: Medium Priority Refactoring (Week 3)

### 2.1 Break Down Long Methods

**Files**: Multiple  
**Target**: No method over 50 lines

**Tasks:**

- [ ] Refactor `calculate_composite_score()` (100+ lines)
  - Extract `_initialize_tracking()`
  - Extract `_validate_critical_fields()`
  - Extract `_calculate_component_scores()`
  - Extract `_compute_weighted_score()`
  - Extract `_build_result()`
  - Estimated: 4 hours

- [ ] Refactor `create_detailed_analysis()` (150+ lines)
  - Already has good helper methods
  - Consider extracting data quality checks
  - Estimated: 2 hours

- [ ] Refactor `_build_rationale()` (80+ lines)
  - Extract asset-specific rationale builders
  - Use strategy pattern from Phase 1
  - Estimated: 3 hours

**Benefits:**

- Improved readability
- Easier to test individual steps
- Better error isolation
- Reduced cognitive complexity

**Testing Strategy:**

- Unit test each extracted method
- Integration test for full flow
- Verify identical behavior


---

### 2.2 Extract Repeated Scoring Pattern

**File**: `src/finwiz/scoring/deep_analysis_scorer.py`  
**Current**: Same threshold-based scoring in 10+ places  
**Target**: Reusable `calculate_threshold_score()` function

**Tasks:**

- [ ] Create `calculate_threshold_score()` utility function
  - Accept value, thresholds list, reverse flag
  - Return score between 0.0 and 1.0
  - Estimated: 30 lines

- [ ] Update ROE scoring to use utility
- [ ] Update debt scoring to use utility
- [ ] Update growth scoring to use utility
- [ ] Update expense ratio scoring to use utility
- [ ] Update all other threshold-based scoring
  - Estimated: 3 hours total

**Benefits:**

- Eliminates 100+ lines of duplicate logic
- Consistent scoring behavior
- Easier to modify scoring algorithm
- Better testability

**Testing Strategy:**

- Unit test utility function with various inputs
- Test reverse scoring (lower is better)
- Verify identical scores before/after

---

### 2.3 Create Base Class for Async Feedback Tools

**File**: `src/finwiz/tools/feedback_integration_tool.py`  
**Current**: Same async pattern in 5 tool classes  
**Target**: Single base class with shared logic

**Tasks:**

- [ ] Create `AsyncFeedbackTool` base class
  - Implement `_run()` with event loop handling
  - Define abstract `_arun()` method
  - Estimated: 40 lines

- [ ] Refactor `FeedbackCollectionTool` to inherit base
- [ ] Refactor `FeedbackRetrievalTool` to inherit base
- [ ] Refactor `FeedbackAnalysisTool` to inherit base
- [ ] Refactor `FeedbackReportTool` to inherit base
- [ ] Refactor `FeedbackExportTool` to inherit base
  - Estimated: 2 hours total


**Benefits:**

- Eliminates 50+ lines of duplicate code
- Consistent async handling
- Easier to add new feedback tools
- Single point for event loop logic

**Testing Strategy:**

- Test base class with mock implementations
- Test each tool independently
- Verify async behavior in different contexts

---

### 2.4 Standardize Error Handling Across Tools

**Files**: All tool files  
**Current**: Inconsistent error responses  
**Target**: Standardized `ToolResult` class

**Tasks:**

- [ ] Create `ToolResult` dataclass
  - `success: bool`
  - `data: dict[str, Any]`
  - `error: str | None`
  - `to_dict()` method
  - Estimated: 30 lines

- [ ] Update all tools to use `ToolResult`
  - FeedbackCollectionTool
  - FeedbackRetrievalTool
  - FeedbackAnalysisTool
  - FeedbackReportTool
  - FeedbackExportTool
  - All other tools
  - Estimated: 4 hours

**Benefits:**

- Consistent error handling
- Easier to parse tool results
- Better error messages
- Improved debugging

**Testing Strategy:**

- Test success cases
- Test error cases
- Verify consistent response format

---

### 2.5 Extract Nested Conditionals to Guard Clauses

**File**: `src/finwiz/integration/aplus_extractor.py`  
**Current**: Deep nesting in opportunity building  
**Target**: Flat structure with guard clauses

**Tasks:**

- [ ] Create `_extract_moat_info()` helper
  - Handle string type
  - Handle dict type
  - Handle other types
  - Estimated: 30 lines


- [ ] Create `_extract_diversification_info()` helper
  - Handle various data structures
  - Use guard clauses
  - Estimated: 30 lines

- [ ] Refactor opportunity building methods
  - Use extracted helpers
  - Reduce nesting depth
  - Estimated: 2 hours

**Benefits:**

- Improved readability
- Reduced cyclomatic complexity
- Easier to test edge cases
- Better error handling

**Testing Strategy:**

- Test with various data structures
- Test with missing fields
- Test with invalid types

---

## Phase 3: Low Priority Improvements (Week 4)

### 3.1 Improve Timezone Handling

**File**: `src/finwiz/quantitative/data_processors.py`  
**Current**: Manual timezone stripping  
**Target**: Robust utility function

**Tasks:**

- [ ] Create `normalize_to_naive()` utility function
  - Handle aware datetimes
  - Handle naive datetimes
  - Convert to UTC
  - Estimated: 20 lines

- [ ] Update `validate_inputs()` to use utility
- [ ] Update other datetime handling code
  - Estimated: 1 hour

**Benefits:**

- More robust timezone handling
- Consistent datetime normalization
- Prevents timezone-related bugs

**Testing Strategy:**

- Test with aware datetimes
- Test with naive datetimes
- Test with various timezones

---

### 3.2 Extract Regex Patterns to Constants

**Files**: `scripts/verify_html_reports.py`, `scripts/generate_html_reports.py`  
**Current**: Inline regex patterns  
**Target**: Module-level constants

**Tasks:**

- [ ] Extract patterns to module constants
  - TICKER_PATTERN
  - TICKER_TITLE_PATTERN
  - NUMERIC_PATTERN
  - GRADE_PATTERN
  - Estimated: 30 minutes


- [ ] Update code to use constants
- [ ] Add documentation for patterns
  - Estimated: 30 minutes

**Benefits:**

- Easier to maintain patterns
- Better documentation
- Reusable across functions
- Compile once, use many times

**Testing Strategy:**

- Verify identical matching behavior
- Test with various HTML structures

---

### 3.3 Add Missing Type Hints

**Files**: Various  
**Current**: ~95% type coverage  
**Target**: 100% type coverage

**Tasks:**

- [ ] Audit all functions for missing type hints
- [ ] Add return type annotations
- [ ] Add parameter type annotations
- [ ] Run mypy in strict mode
  - Estimated: 4 hours

**Benefits:**

- Better IDE support
- Catch type errors early
- Improved documentation
- Easier refactoring

**Testing Strategy:**

- Run mypy with strict mode
- Verify no type errors
- Test with various inputs

---

## Implementation Guidelines

### Before Starting Any Refactoring

1. **Create Feature Branch**

   ```bash
   git checkout -b refactor/phase-1-scorer-split
   ```

2. **Run Full Test Suite**

   ```bash
   uv run pytest --cov=src/finwiz --cov-report=html
   ```

   - Ensure 80%+ coverage
   - All tests passing

3. **Document Current Behavior**
   - Capture input/output examples
   - Document edge cases
   - Note any quirks or workarounds

### During Refactoring

1. **Test-Driven Refactoring**
   - Write tests for new classes/methods FIRST
   - Ensure tests pass with old implementation
   - Refactor code
   - Verify tests still pass

2. **Incremental Changes**
   - Make small, focused commits
   - Each commit should be deployable
   - Run tests after each commit

3. **Preserve Behavior**
   - No functional changes during refactoring
   - Identical outputs for identical inputs
   - Same error handling behavior


4. **Code Review**
   - Self-review before committing
   - Peer review for major changes
   - Check against steering rules

### After Refactoring

1. **Verify Test Coverage**

   ```bash
   uv run pytest --cov=src/finwiz --cov-report=html
   ```

   - Maintain or improve coverage
   - No decrease in test quality

2. **Run Integration Tests**

   ```bash
   uv run pytest -m integration
   ```

   - Verify end-to-end functionality
   - Test with real data

3. **Performance Benchmarking**
   - Compare execution time before/after
   - Ensure no performance regression
   - Document any improvements

4. **Update Documentation**
   - Update docstrings
   - Update architecture docs
   - Update steering rules if needed

5. **Merge Strategy**
   - Squash commits for clean history
   - Write comprehensive merge commit message
   - Tag release if appropriate

---

## Risk Mitigation

### High Risk Areas

1. **DeepAnalysisScorer Refactoring**
   - **Risk**: Breaking scoring logic
   - **Mitigation**: Extensive unit tests, comparison testing
   - **Rollback Plan**: Keep old implementation in parallel initially

2. **APlusExtractor Refactoring**
   - **Risk**: Data extraction failures
   - **Mitigation**: Test with all existing JSON files
   - **Rollback Plan**: Feature flag for new vs old implementation

3. **Async Tool Refactoring**
   - **Risk**: Event loop issues
   - **Mitigation**: Test in various async contexts
   - **Rollback Plan**: Keep old implementations as fallback

### Testing Strategy

1. **Unit Tests**
   - Test each new class/method independently
   - Mock external dependencies
   - Cover edge cases

2. **Integration Tests**
   - Test full workflows
   - Use real data samples
   - Verify identical outputs

3. **Regression Tests**
   - Capture current outputs as baselines
   - Compare new outputs to baselines
   - Flag any differences for review

4. **Performance Tests**
   - Benchmark critical paths
   - Compare before/after
   - Set performance budgets

---

## Success Metrics

### Code Quality Metrics

- **Lines of Code**: Reduce by ~40% in affected files
- **Cyclomatic Complexity**: Reduce average from 15 to <10
- **Code Duplication**: Reduce from 30% to <5%
- **Test Coverage**: Maintain 80%+ coverage


### Maintainability Metrics

- **Time to Add New Asset Class**: Reduce from 4 hours to 1 hour
- **Time to Modify Scoring Logic**: Reduce from 2 hours to 30 minutes
- **Time to Debug Issues**: Reduce by 50%
- **Onboarding Time**: Reduce by 40%

### Performance Metrics

- **Execution Time**: No regression (±5% acceptable)
- **Memory Usage**: No regression (±10% acceptable)
- **API Calls**: No increase

---

## Timeline

### Week 1: Phase 1 Tasks 1.1-1.3

- Monday-Tuesday: Split DeepAnalysisScorer (1.1)
- Wednesday-Thursday: Implement Strategy Pattern (1.2)
- Friday: Extract Scoring Thresholds (1.3)

### Week 2: Phase 1 Tasks 1.4-1.5

- Monday-Tuesday: Eliminate Duplicate JSON Parsing (1.4)
- Wednesday-Friday: Apply Template Method Pattern (1.5)

### Week 3: Phase 2 All Tasks

- Monday: Break Down Long Methods (2.1)
- Tuesday: Extract Repeated Scoring Pattern (2.2)
- Wednesday: Create Base Class for Async Tools (2.3)
- Thursday: Standardize Error Handling (2.4)
- Friday: Extract Nested Conditionals (2.5)

### Week 4: Phase 3 All Tasks + Documentation

- Monday-Tuesday: Low Priority Improvements (3.1-3.3)
- Wednesday-Thursday: Documentation Updates
- Friday: Final Review and Merge

---

## Checklist

### Phase 1 Completion Criteria

- [ ] All Phase 1 tasks completed
- [ ] All tests passing
- [ ] Test coverage ≥80%
- [ ] No performance regression
- [ ] Code review completed
- [ ] Documentation updated
- [ ] Merged to main branch

### Phase 2 Completion Criteria

- [ ] All Phase 2 tasks completed
- [ ] All tests passing
- [ ] Test coverage ≥80%
- [ ] No performance regression
- [ ] Code review completed
- [ ] Documentation updated
- [ ] Merged to main branch

### Phase 3 Completion Criteria

- [ ] All Phase 3 tasks completed
- [ ] All tests passing
- [ ] Test coverage ≥80%
- [ ] No performance regression
- [ ] Code review completed
- [ ] Documentation updated
- [ ] Merged to main branch
- [ ] Roadmap archived

---

## Notes

### Dependencies

- No external dependencies required
- All refactoring uses existing libraries
- Python 3.8+ features only

### Backward Compatibility

- All refactoring maintains backward compatibility
- No breaking changes to public APIs
- Existing tests should pass without modification


### Communication

- Update team on progress weekly
- Flag blockers immediately
- Share learnings in team meetings
- Document decisions in ADRs (Architecture Decision Records)

### Future Considerations

- Consider extracting more configuration to YAML/JSON
- Evaluate caching strategies for expensive operations
- Consider async/await for I/O-bound operations
- Explore parallel processing for batch operations

---

## Appendix A: File Structure After Refactoring

```
src/finwiz/
├── scoring/
│   ├── deep_analysis_scorer.py          # Orchestrator (400 lines)
│   ├── fundamental_scorer.py            # NEW (300 lines)
│   ├── technical_scorer.py              # NEW (200 lines)
│   ├── risk_scorer.py                   # NEW (200 lines)
│   ├── scoring_thresholds.py            # NEW (100 lines)
│   ├── scoring_utils.py                 # NEW (100 lines)
│   └── asset_analyzers/                 # NEW directory
│       ├── __init__.py
│       ├── base.py                      # AssetAnalyzer ABC (50 lines)
│       ├── stock_analyzer.py            # StockAnalyzer (150 lines)
│       ├── etf_analyzer.py              # ETFAnalyzer (150 lines)
│       ├── crypto_analyzer.py           # CryptoAnalyzer (150 lines)
│       └── factory.py                   # AnalyzerFactory (50 lines)
│
├── integration/
│   ├── aplus_extractor.py               # Main class (300 lines)
│   └── opportunity_extractors/          # NEW directory
│       ├── __init__.py
│       ├── base.py                      # OpportunityExtractor ABC (80 lines)
│       ├── stock_extractor.py           # StockOpportunityExtractor (60 lines)
│       ├── etf_extractor.py             # ETFOpportunityExtractor (60 lines)
│       └── crypto_extractor.py          # CryptoOpportunityExtractor (60 lines)
│
├── tools/
│   ├── feedback_integration_tool.py     # Refactored (400 lines)
│   ├── base_tools.py                    # NEW (100 lines)
│   └── tool_result.py                   # NEW (50 lines)
│
└── utils/
    ├── datetime_utils.py                # NEW (50 lines)
    └── scoring_utils.py                 # NEW (100 lines)
```

---

## Appendix B: Example Code Snippets

### Before: Repeated Conditional Logic

```python
def calculate_fundamental_score(self, asset_class: str, data: dict) -> tuple[float, dict]:
    if asset_class == "stock":
        roe = self._safe_get_float(data, "roe", 0.0)
        if roe >= 0.20:
            roe_score = 1.0
        elif roe >= 0.15:
            roe_score = 0.8
        # ... 50 more lines
    elif asset_class == "etf":
        expense = self._safe_get_float(data, "expense_ratio", 1.0)
        if expense <= 0.001:
            expense_score = 1.0
        elif expense <= 0.0025:
            expense_score = 0.8
        # ... 50 more lines
    elif asset_class == "crypto":
        # ... 50 more lines
```

### After: Strategy Pattern

```python
def calculate_fundamental_score(self, asset_class: str, data: dict) -> tuple[float, dict]:
    analyzer = AnalyzerFactory.get_analyzer(asset_class)
    return analyzer.calculate_fundamental_score(data)
```

---

## Appendix C: Testing Examples

### Unit Test for New FundamentalScorer

```python
def test_fundamental_scorer_stock_excellent_roe(mocker):
    """Test stock scoring with excellent ROE."""
    scorer = FundamentalScorer()
    data = {"roe": 0.25, "debt_to_equity": 0.2, "revenue_growth": 0.20}
    
    score, details = scorer.calculate_stock_score(data)
    
    assert score >= 0.8
    assert details["roe_score"] == 1.0
    assert "excellent" in details["roe_assessment"].lower()
```

### Integration Test for Refactored Scorer

```python
def test_deep_analysis_scorer_maintains_behavior(mocker):
    """Verify refactored scorer produces identical results."""
    # Setup
    old_scorer = OldDeepAnalysisScorer()
    new_scorer = DeepAnalysisScorer()
    test_data = load_test_data("AAPL")
    
    # Execute
    old_result = old_scorer.calculate_composite_score("AAPL", "stock", test_data)
    new_result = new_scorer.calculate_composite_score("AAPL", "stock", test_data)
    
    # Verify identical behavior
    assert old_result.composite_score == new_result.composite_score
    assert old_result.grade == new_result.grade
    assert old_result.recommendation == new_result.recommendation
```

---

## Appendix D: Performance Benchmarks

### Baseline Performance (Before Refactoring)

```
DeepAnalysisScorer.calculate_composite_score():
  - Average: 1.2s
  - P95: 1.8s
  - P99: 2.5s

APlusExtractor.extract_all_opportunities():
  - Average: 0.8s
  - P95: 1.2s
  - P99: 1.8s
```

### Target Performance (After Refactoring)

```
DeepAnalysisScorer.calculate_composite_score():
  - Average: ≤1.3s (±10%)
  - P95: ≤1.9s
  - P99: ≤2.6s

APlusExtractor.extract_all_opportunities():
  - Average: ≤0.9s (±10%)
  - P95: ≤1.3s
  - P99: ≤1.9s
```

---

**End of Roadmap**

For questions or clarifications, contact the development team.
