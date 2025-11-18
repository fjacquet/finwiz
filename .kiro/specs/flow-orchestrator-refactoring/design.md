# Flow Orchestrator Refactoring Design

## Overview

This design document outlines the refactoring of the monolithic Flow Orchestrator (4426 lines) into focused, single-responsibility orchestrator modules. The refactoring maintains complete backward compatibility while improving maintainability, testability, and code organization.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FinwizFlow (Refactored)                  │
│                  (Flow-specific logic only)                 │
│                        < 300 lines                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ delegates to
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Orchestrator Modules                     │
│                   (Each < 300 lines)                        │
├─────────────────────────────────────────────────────────────┤
│  • ErrorHandlingOrchestrator                                │
│  • ProgressTrackingOrchestrator                             │
│  • UtilityOrchestrator                                      │
│  • DeepAnalysisOrchestrator                                 │
│  • AlternativesMatchingOrchestrator                         │
│  • DiscoveryOrchestrator                                    │
│  • ValidationOrchestrator                                   │
│  • ReportingOrchestrator                                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ uses
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Shared Infrastructure                          │
│  • CrewFactory                                              │
│  • CrewDataIntegrationManager                               │
│  • FlowStateManager                                         │
│  • FinwizState (Pydantic model)                             │
└─────────────────────────────────────────────────────────────┘
```

### Module Responsibilities

Each orchestrator module has a single, clearly defined responsibility:

1. **ErrorHandlingOrchestrator**: Crew execution error handling and error aggregation
2. **ProgressTrackingOrchestrator**: Progress calculation and metrics persistence
3. **UtilityOrchestrator**: Data parsing, grade calculation, URL extraction/validation
4. **DeepAnalysisOrchestrator**: Deep analysis execution and result creation
5. **AlternativesMatchingOrchestrator**: A+ alternative matching for underperforming holdings
6. **DiscoveryOrchestrator**: Discovery crew execution and result consolidation
7. **ValidationOrchestrator**: Input validation and data availability checking
8. **ReportingOrchestrator**: Report consolidation and HTML generation


## Components and Interfaces

### Base Orchestrator Pattern

All orchestrators follow a common pattern:

```python
from typing import Any
from finwiz.flow_state import FinwizState
from finwiz.tools.logger import get_logger

class BaseOrchestrator:
    """Base class for all orchestrators."""
    
    def __init__(self, state: FinwizState, **dependencies):
        self.state = state
        self.logger = get_logger(self.__class__.__name__)
        # Store dependencies (crew_factory, integration_manager, etc.)
```

### ErrorHandlingOrchestrator

```python
class ErrorHandlingOrchestrator(BaseOrchestrator):
    """Handles crew execution errors and error aggregation."""
    
    def execute_crew_with_error_handling(
        self, 
        crew_func: Callable, 
        crew_name: str,
        **kwargs
    ) -> dict[str, Any]:
        """Execute crew with comprehensive error handling."""
        
    def generate_error_summary(
        self, 
        errors: list[Exception]
    ) -> dict[str, Any]:
        """Aggregate errors into actionable summary."""
        
    def generate_error_report(
        self, 
        error_summary: dict[str, Any]
    ) -> str:
        """Generate human-readable error report."""
```

### DeepAnalysisOrchestrator

```python
class DeepAnalysisOrchestrator(BaseOrchestrator):
    """Orchestrates deep analysis execution on portfolio holdings."""
    
    def run_deep_analysis_on_holdings(
        self,
        holdings: list[dict[str, Any]]
    ) -> dict[str, DeepAnalysisResult]:
        """Execute deep analysis on all holdings."""
        
    def create_deep_analysis_result_from_crew_output(
        self,
        crew_output: Any,
        ticker: str,
        asset_class: str
    ) -> DeepAnalysisResult:
        """Parse crew output into structured result."""
        
    def execute_deep_analysis_with_prefetch(
        self,
        holdings: list[dict[str, Any]]
    ) -> dict[str, DeepAnalysisResult]:
        """Execute with batch prefetch optimization."""
        
    def save_batch_metrics_to_file(
        self,
        metrics: dict[str, Any],
        output_path: str
    ) -> None:
        """Save batch metrics to file."""
```


### AlternativesMatchingOrchestrator

```python
class AlternativesMatchingOrchestrator(BaseOrchestrator):
    """Finds and matches A+ alternatives for underperforming holdings."""
    
    def match_alternatives_for_holdings(
        self,
        holdings: list[dict[str, Any]],
        discovery_results: dict[str, Any]
    ) -> dict[str, list[dict[str, Any]]]:
        """Match alternatives from discovery results."""
        
    def match_alternatives_after_discovery(
        self,
        discovery_data: dict[str, Any]
    ) -> dict[str, list[dict[str, Any]]]:
        """Flow listener for alternative matching."""
```

### ReportingOrchestrator

```python
class ReportingOrchestrator(BaseOrchestrator):
    """Generates consolidated reports and final HTML output."""
    
    def report(self) -> str:
        """Main report generation entry point."""
        
    def consolidate_reports(
        self,
        crew_export_paths: dict[str, list[str]]
    ) -> dict[str, Any]:
        """Consolidate crew reports into single structure."""
        
    def generate_final_report(
        self,
        consolidated_data: dict[str, Any]
    ) -> str:
        """Generate final HTML report."""
        
    def generate_html_from_export(
        self,
        export_data: dict[str, Any],
        template_name: str
    ) -> str:
        """Generate HTML using Jinja2 templates."""
        
    def store_crew_export_paths(
        self,
        crew_name: str,
        export_paths: list[str]
    ) -> None:
        """Store crew export paths in state."""
        
    def get_crew_export_path(
        self,
        crew_name: str,
        ticker: str
    ) -> str:
        """Calculate crew export path."""
```

### DiscoveryOrchestrator

```python
class DiscoveryOrchestrator(BaseOrchestrator):
    """Executes discovery analysis for crypto, stocks, and ETFs."""
    
    def check_crypto(self) -> dict[str, Any]:
        """Execute crypto discovery crew."""
        
    def check_stock(self) -> dict[str, Any]:
        """Execute stock discovery crew."""
        
    def check_etf(self) -> dict[str, Any]:
        """Execute ETF discovery crew."""
        
    def check_investment_discovery(self) -> dict[str, Any]:
        """Consolidate discovery results."""
```


### ValidationOrchestrator

```python
class ValidationOrchestrator(BaseOrchestrator):
    """Validates data and prepares for reporting."""
    
    def pre_validate_reporter_input(
        self,
        consolidated_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Validate reporter input data."""
        
    def check_core_analysis_availability(self) -> dict[str, Any]:
        """Check which core analyses are available."""
        
    def extract_market_conditions(self) -> dict[str, Any]:
        """Extract market conditions from core analysis."""
        
    def extract_market_context_from_core_analysis(
        self,
        core_analysis_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Extract market context information."""
```

### ProgressTrackingOrchestrator

```python
class ProgressTrackingOrchestrator(BaseOrchestrator):
    """Tracks and reports execution progress."""
    
    def update_progress(
        self,
        holdings_processed: int,
        total_holdings: int
    ) -> None:
        """Update progress metrics in state."""
        
    def save_batch_metrics_to_file(
        self,
        metrics: dict[str, Any],
        output_path: str
    ) -> None:
        """Save batch metrics to file."""
```

### UtilityOrchestrator

```python
class UtilityOrchestrator(BaseOrchestrator):
    """Utility functions for data processing."""
    
    def parse_crew_output_for_holding(
        self,
        crew_output: Any,
        ticker: str
    ) -> dict[str, Any]:
        """Parse crew output for specific holding."""
        
    def calculate_grade_distribution(
        self,
        holdings: list[dict[str, Any]]
    ) -> dict[str, int]:
        """Calculate grade distribution across holdings."""
        
    def extract_sec_filing_urls(
        self,
        crew_output: Any
    ) -> list[str]:
        """Extract SEC filing URLs from crew output."""
        
    def validate_and_fix_sec_urls(
        self,
        urls: list[str]
    ) -> list[str]:
        """Validate and fix malformed SEC URLs."""
```


## Data Models

### Orchestrator Dependencies

```python
from dataclasses import dataclass
from typing import Any

@dataclass
class OrchestratorDependencies:
    """Shared dependencies for all orchestrators."""
    crew_factory: CrewFactory
    integration_manager: CrewDataIntegrationManager
    error_handler: CoreAnalysisErrorHandler
    state_manager: FlowStateManager
    resilience_config: ResilienceConfig
    batch_prefetch_config: BatchPrefetchConfig
```

### Refactored FinwizFlow

```python
@persist()
class FinwizFlow(Flow[FinwizState]):
    """Refactored Flow with delegation to orchestrators."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Initialize shared dependencies
        self.deps = self._initialize_dependencies()
        
        # Initialize orchestrators (lazy loading)
        self._error_handler_orch = None
        self._progress_orch = None
        self._utility_orch = None
        self._deep_analysis_orch = None
        self._alternatives_orch = None
        self._discovery_orch = None
        self._validation_orch = None
        self._reporting_orch = None
    
    @property
    def error_handler_orch(self) -> ErrorHandlingOrchestrator:
        """Lazy load error handling orchestrator."""
        if self._error_handler_orch is None:
            self._error_handler_orch = ErrorHandlingOrchestrator(
                self.state, **self.deps
            )
        return self._error_handler_orch
    
    # Similar lazy loading for other orchestrators...
    
    @start()
    def validate_data_integration(self) -> dict[str, Any]:
        """Flow listener - delegates to ValidationOrchestrator."""
        return self.validation_orch.validate_data_integration()
    
    @listen("validate_data_integration")
    def check_portfolio(self) -> dict[str, Any]:
        """Flow listener - delegates to ValidationOrchestrator."""
        return self.validation_orch.check_portfolio()
    
    # Other Flow listeners delegate similarly...
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: File Size Constraint

*For any* orchestrator module file, the line count should not exceed 300 lines
**Validates: Requirements 1.1, 1.2**

### Property 2: Single Responsibility

*For any* orchestrator module, all methods should relate to the module's stated responsibility
**Validates: Requirements 1.3**

### Property 3: Import Backward Compatibility

*For any* existing import path from flow_orchestrator, the import should resolve successfully after refactoring
**Validates: Requirements 1.4, 10.1**

### Property 4: Error Handling Graceful Degradation

*For any* crew execution error, the ErrorHandlingOrchestrator should handle it without raising unhandled exceptions
**Validates: Requirements 2.1**

### Property 5: Error Aggregation Completeness

*For any* set of multiple errors, the ErrorHandlingOrchestrator should include all errors in the aggregated summary
**Validates: Requirements 2.2**

### Property 6: Error Information Actionability

*For any* error summary generated, it should contain message, context, and timestamp fields
**Validates: Requirements 2.3**

### Property 7: Successful Result Pass-Through

*For any* successful crew execution, the ErrorHandlingOrchestrator should return the result unmodified
**Validates: Requirements 2.4**

### Property 8: Deep Analysis Completeness

*For any* portfolio with N holdings, the DeepAnalysisOrchestrator should execute analysis on all N holdings
**Validates: Requirements 3.1**

### Property 9: Deep Analysis Result Structure

*For any* deep analysis result, it should conform to the DeepAnalysisResult Pydantic schema
**Validates: Requirements 3.2**

### Property 10: Deep Analysis Parsing Correctness

*For any* crew output, the DeepAnalysisOrchestrator should extract ticker, grade, and composite_score fields
**Validates: Requirements 3.5**

### Property 11: Alternative Matching Conditional

*For any* holding with grade >= B, the AlternativesMatchingOrchestrator should not find alternatives
**Validates: Requirements 4.1**

### Property 12: Alternative Structure Validation

*For any* matched alternative, it should contain ticker, asset_class, and grade fields
**Validates: Requirements 4.3**

### Property 13: Report Consolidation Completeness

*For any* set of crew reports, the ReportingOrchestrator should include all reports in the consolidated output
**Validates: Requirements 5.1**

### Property 14: HTML Report Generation

*For any* consolidated data, the ReportingOrchestrator should generate valid HTML output
**Validates: Requirements 5.2**

### Property 15: Export Path Correctness

*For any* crew name and ticker, the calculated export path should follow the pattern: `output/{crew_name}/{ticker}_export.json`
**Validates: Requirements 5.4**


### Property 16: Discovery Result Consolidation

*For any* set of discovery results from multiple asset classes, the DiscoveryOrchestrator should consolidate all results
**Validates: Requirements 6.4**

### Property 17: Discovery Error Handling

*For any* discovery crew failure, the DiscoveryOrchestrator should handle the error gracefully and continue with other crews
**Validates: Requirements 6.5**

### Property 18: Validation Data Availability Check

*For any* reporter input validation, the ValidationOrchestrator should verify presence of required data fields
**Validates: Requirements 7.1**

### Property 19: Core Analysis Verification

*For any* core analysis availability check, the ValidationOrchestrator should verify all required analyses exist
**Validates: Requirements 7.2**

### Property 20: Market Context Structure

*For any* extracted market context, it should contain overall_sentiment, market_trends, and risk_factors fields
**Validates: Requirements 7.4**

### Property 21: Progress Calculation Accuracy

*For any* progress update with N processed out of M total holdings, the percentage should equal (N/M) * 100
**Validates: Requirements 8.3**

### Property 22: Grade Distribution Aggregation

*For any* set of holdings with grades, the UtilityOrchestrator should count all grades correctly
**Validates: Requirements 9.2**

### Property 23: URL Extraction Completeness

*For any* crew output containing SEC URLs, the UtilityOrchestrator should extract all URLs
**Validates: Requirements 9.3**

### Property 24: URL Validation and Correction

*For any* malformed SEC URL, the UtilityOrchestrator should fix it to a valid format
**Validates: Requirements 9.4**

### Property 25: Flow Listener Delegation

*For any* Flow listener method call, it should delegate to the appropriate orchestrator method
**Validates: Requirements 10.2**

### Property 26: Behavioral Equivalence

*For any* input to the refactored Flow, the output should match the original implementation's output
**Validates: Requirements 10.3**

### Property 27: API Compatibility

*For any* public method in the original Flow, it should exist with the same signature in the refactored Flow
**Validates: Requirements 10.5**


## Error Handling

### Error Handling Strategy

1. **Orchestrator-Level Error Handling**: Each orchestrator handles its own errors and returns error information in a structured format
2. **ErrorHandlingOrchestrator**: Provides centralized error handling utilities for crew execution
3. **State-Based Error Tracking**: All errors are tracked in FinwizState for transparency
4. **Graceful Degradation**: Errors in one orchestrator should not prevent other orchestrators from executing

### Error Response Format

```python
{
    "success": bool,
    "data": Any,  # Result data if successful
    "error": {
        "message": str,
        "type": str,
        "context": dict[str, Any],
        "timestamp": str,
        "retryable": bool
    } | None
}
```

### Error Propagation

```python
class ErrorHandlingOrchestrator:
    def execute_crew_with_error_handling(self, crew_func, crew_name, **kwargs):
        try:
            result = crew_func(**kwargs)
            return {"success": True, "data": result, "error": None}
        except Exception as e:
            error_info = {
                "message": str(e),
                "type": type(e).__name__,
                "context": {"crew_name": crew_name, **kwargs},
                "timestamp": datetime.now().isoformat(),
                "retryable": self._is_retryable_error(e)
            }
            self.logger.error(f"Crew {crew_name} failed: {error_info}")
            return {"success": False, "data": None, "error": error_info}
```


## Testing Strategy

### Dual Testing Approach

This refactoring requires both **unit testing** and **property-based testing** to ensure correctness:

- **Unit tests** verify specific examples, edge cases, and integration points
- **Property tests** verify universal properties that should hold across all inputs
- Together they provide comprehensive coverage: unit tests catch concrete bugs, property tests verify general correctness

### Unit Testing

Unit tests focus on:
- Specific examples that demonstrate correct behavior
- Integration points between orchestrators and Flow
- Edge cases (empty inputs, missing data, etc.)
- Mock-based testing of crew execution

**Example Unit Tests:**

```python
def test_error_handling_orchestrator_handles_crew_failure(mocker):
    """Test error handling for crew execution failure."""
    # Arrange
    state = FinwizState()
    orch = ErrorHandlingOrchestrator(state)
    mock_crew = mocker.Mock(side_effect=Exception("Crew failed"))
    
    # Act
    result = orch.execute_crew_with_error_handling(
        mock_crew, "test_crew"
    )
    
    # Assert
    assert result["success"] is False
    assert result["error"] is not None
    assert "Crew failed" in result["error"]["message"]

def test_deep_analysis_orchestrator_creates_valid_results(mocker):
    """Test deep analysis result creation."""
    # Arrange
    state = FinwizState()
    orch = DeepAnalysisOrchestrator(state)
    crew_output = mocker.Mock(
        raw="Analysis complete",
        pydantic={"composite_score": 0.85, "grade": "A"}
    )
    
    # Act
    result = orch.create_deep_analysis_result_from_crew_output(
        crew_output, "AAPL", "stock"
    )
    
    # Assert
    assert isinstance(result, DeepAnalysisResult)
    assert result.ticker == "AAPL"
    assert result.asset_class == "stock"
    assert result.composite_score == 0.85
    assert result.grade == "A"
```


### Property-Based Testing

Property tests verify universal properties using **Hypothesis** (Python's property-based testing library):

**Configuration:**
- Minimum 100 iterations per property test
- Use `@given` decorator with Hypothesis strategies
- Tag each test with the property number from design doc

**Example Property Tests:**

```python
from hypothesis import given, strategies as st

@given(
    holdings=st.lists(
        st.fixed_dictionaries({
            "ticker": st.text(min_size=1, max_size=5),
            "grade": st.sampled_from(["A+", "A", "B", "C", "D", "F"])
        }),
        min_size=1,
        max_size=20
    )
)
def test_property_deep_analysis_completeness(holdings):
    """
    **Feature: flow-orchestrator-refactoring, Property 8: Deep Analysis Completeness**
    
    For any portfolio with N holdings, the DeepAnalysisOrchestrator 
    should execute analysis on all N holdings.
    """
    # Arrange
    state = FinwizState()
    orch = DeepAnalysisOrchestrator(state)
    
    # Act
    results = orch.run_deep_analysis_on_holdings(holdings)
    
    # Assert
    assert len(results) == len(holdings)
    for holding in holdings:
        assert holding["ticker"] in results

@given(
    grade=st.sampled_from(["A+", "A", "B", "C", "D", "F"])
)
def test_property_alternative_matching_conditional(grade):
    """
    **Feature: flow-orchestrator-refactoring, Property 11: Alternative Matching Conditional**
    
    For any holding with grade >= B, the AlternativesMatchingOrchestrator 
    should not find alternatives.
    """
    # Arrange
    state = FinwizState()
    orch = AlternativesMatchingOrchestrator(state)
    holding = {"ticker": "TEST", "grade": grade}
    
    # Act
    alternatives = orch.match_alternatives_for_holdings([holding], {})
    
    # Assert
    if grade in ["A+", "A", "B"]:
        assert len(alternatives.get("TEST", [])) == 0
    # Grades C, D, F may have alternatives (not tested here)

@given(
    processed=st.integers(min_value=0, max_value=100),
    total=st.integers(min_value=1, max_value=100)
)
def test_property_progress_calculation_accuracy(processed, total):
    """
    **Feature: flow-orchestrator-refactoring, Property 21: Progress Calculation Accuracy**
    
    For any progress update with N processed out of M total holdings, 
    the percentage should equal (N/M) * 100.
    """
    # Arrange
    state = FinwizState()
    orch = ProgressTrackingOrchestrator(state)
    
    # Ensure processed <= total
    processed = min(processed, total)
    
    # Act
    orch.update_progress(processed, total)
    
    # Assert
    expected_percentage = (processed / total) * 100
    assert abs(state.progress_percentage - expected_percentage) < 0.01
```


### Integration Testing

Integration tests verify orchestrator interactions:

```python
def test_flow_orchestrator_integration(mocker):
    """Test full Flow execution with orchestrators."""
    # Arrange
    flow = FinwizFlow()
    
    # Mock crew executions
    mocker.patch.object(flow.crew_factory, "execute_stock_crew", 
                       return_value={"result": "stock_analysis"})
    mocker.patch.object(flow.crew_factory, "execute_etf_crew",
                       return_value={"result": "etf_analysis"})
    
    # Act
    result = flow.kickoff()
    
    # Assert
    assert flow.state.stock_analysis_success
    assert flow.state.etf_analysis_success
    assert flow.state.final_report_path is not None

def test_orchestrator_error_propagation(mocker):
    """Test error propagation between orchestrators."""
    # Arrange
    flow = FinwizFlow()
    mocker.patch.object(flow.crew_factory, "execute_stock_crew",
                       side_effect=Exception("Stock crew failed"))
    
    # Act
    result = flow.kickoff()
    
    # Assert
    assert flow.state.stock_analysis_error is not None
    assert "Stock crew failed" in flow.state.stock_analysis_error
    # Other crews should still execute
    assert flow.state.etf_analysis_success or flow.state.crypto_analysis_success
```

### Regression Testing

Regression tests ensure backward compatibility:

```python
def test_existing_imports_still_work():
    """Test that existing import paths still work."""
    # These imports should not raise ImportError
    from finwiz.flows.flow_orchestrator import FinwizFlow
    from finwiz.flows.flow_orchestrator import FinwizState
    
    assert FinwizFlow is not None
    assert FinwizState is not None

def test_existing_tests_pass():
    """Run existing test suite without modification."""
    # This test verifies that all existing tests in
    # tests/unit/flows/test_flow_orchestrator.py still pass
    import pytest
    result = pytest.main([
        "tests/unit/flows/test_flow_orchestrator.py",
        "-v"
    ])
    assert result == 0  # All tests passed
```


### Test Coverage Requirements

- **Minimum Coverage**: 80% for all orchestrator modules
- **Target Coverage**: 90%+ for critical orchestrators (ErrorHandling, DeepAnalysis)
- **Property Test Iterations**: Minimum 100 per property test

### Test Organization

```
tests/
├── unit/
│   ├── orchestrators/
│   │   ├── test_error_handling_orchestrator.py
│   │   ├── test_progress_tracking_orchestrator.py
│   │   ├── test_utility_orchestrator.py
│   │   ├── test_deep_analysis_orchestrator.py
│   │   ├── test_alternatives_matching_orchestrator.py
│   │   ├── test_discovery_orchestrator.py
│   │   ├── test_validation_orchestrator.py
│   │   └── test_reporting_orchestrator.py
│   └── flows/
│       └── test_flow_orchestrator_refactored.py
├── integration/
│   └── test_orchestrator_integration.py
└── property/
    └── test_orchestrator_properties.py
```

### Testing Checklist

Before marking refactoring complete:

- [ ] All unit tests pass (existing + new)
- [ ] All property tests pass (100+ iterations each)
- [ ] Integration tests pass
- [ ] Regression tests pass (existing test suite)
- [ ] Code coverage ≥ 80% for all orchestrators
- [ ] No breaking changes to public API
- [ ] All imports from old paths still work
- [ ] Mock paths updated in existing tests
- [ ] File size constraints verified (all files < 300 lines)


## Implementation Strategy

### Phase 1: Foundation (ErrorHandling, ProgressTracking, Utility)

These orchestrators have minimal dependencies and provide utilities for others:

1. Create `src/finwiz/orchestrators/` directory
2. Implement `ErrorHandlingOrchestrator` with error handling utilities
3. Implement `ProgressTrackingOrchestrator` with progress calculation
4. Implement `UtilityOrchestrator` with parsing and validation utilities
5. Write unit tests for each orchestrator
6. Write property tests for each orchestrator

### Phase 2: Core Orchestrators (DeepAnalysis, Alternatives, Discovery, Validation)

These orchestrators implement core business logic:

1. Implement `DeepAnalysisOrchestrator` with deep analysis execution
2. Implement `AlternativesMatchingOrchestrator` with alternative matching
3. Implement `DiscoveryOrchestrator` with discovery crew execution
4. Implement `ValidationOrchestrator` with validation logic
5. Write unit tests for each orchestrator
6. Write property tests for each orchestrator

### Phase 3: Reporting (ReportingOrchestrator)

This orchestrator depends on all others:

1. Implement `ReportingOrchestrator` with report consolidation
2. Write unit tests
3. Write property tests

### Phase 4: Flow Refactoring

Refactor the main Flow to use orchestrators:

1. Create orchestrator initialization in `FinwizFlow.__init__`
2. Implement lazy loading properties for orchestrators
3. Update Flow listeners to delegate to orchestrators
4. Create re-export layer for backward compatibility
5. Update imports in Flow to use orchestrators

### Phase 5: Testing and Validation

Comprehensive testing phase:

1. Run all existing tests (should pass without modification)
2. Run new unit tests for orchestrators
3. Run property tests (100+ iterations each)
4. Run integration tests
5. Verify file size constraints (all files < 300 lines)
6. Verify code coverage (≥ 80%)
7. Update test mock paths if needed

### Phase 6: Documentation and Cleanup

Final documentation and cleanup:

1. Update docstrings for all orchestrators
2. Update Flow docstrings to reference orchestrators
3. Create migration guide for developers
4. Update architecture documentation
5. Remove any dead code
6. Final code review


## Backward Compatibility

### Re-export Layer

The refactored `flow_orchestrator.py` maintains backward compatibility through re-exports:

```python
# src/finwiz/flows/flow_orchestrator.py (refactored)

# Re-export orchestrators for backward compatibility
from finwiz.orchestrators.error_handling_orchestrator import ErrorHandlingOrchestrator
from finwiz.orchestrators.progress_tracking_orchestrator import ProgressTrackingOrchestrator
from finwiz.orchestrators.utility_orchestrator import UtilityOrchestrator
from finwiz.orchestrators.deep_analysis_orchestrator import DeepAnalysisOrchestrator
from finwiz.orchestrators.alternatives_matching_orchestrator import AlternativesMatchingOrchestrator
from finwiz.orchestrators.discovery_orchestrator import DiscoveryOrchestrator
from finwiz.orchestrators.validation_orchestrator import ValidationOrchestrator
from finwiz.orchestrators.reporting_orchestrator import ReportingOrchestrator

# Re-export state for backward compatibility
from finwiz.flow_state import FinwizState, DeepAnalysisResult, FlowStateManager

__all__ = [
    "FinwizFlow",
    "FinwizState",
    "DeepAnalysisResult",
    "FlowStateManager",
    "ErrorHandlingOrchestrator",
    "ProgressTrackingOrchestrator",
    "UtilityOrchestrator",
    "DeepAnalysisOrchestrator",
    "AlternativesMatchingOrchestrator",
    "DiscoveryOrchestrator",
    "ValidationOrchestrator",
    "ReportingOrchestrator",
]
```

### Import Compatibility

All existing imports continue to work:

```python
# These imports still work after refactoring
from finwiz.flows.flow_orchestrator import FinwizFlow
from finwiz.flows.flow_orchestrator import FinwizState
from finwiz.flows.flow_orchestrator import DeepAnalysisResult

# New imports also available
from finwiz.orchestrators.deep_analysis_orchestrator import DeepAnalysisOrchestrator
from finwiz.orchestrators.error_handling_orchestrator import ErrorHandlingOrchestrator
```

### API Compatibility

All public methods maintain the same signatures:

```python
# Original API
flow = FinwizFlow()
result = flow.kickoff()

# Still works after refactoring
flow = FinwizFlow()
result = flow.kickoff()  # Same behavior, same output
```


## Benefits Summary

### Maintainability

- **Focused Modules**: Each orchestrator < 300 lines with single responsibility
- **Clear Boundaries**: Well-defined interfaces between orchestrators
- **Easy Navigation**: Developers can quickly find relevant code
- **Reduced Cognitive Load**: Smaller files are easier to understand

### Testability

- **Unit Testing**: Each orchestrator can be tested independently
- **Property Testing**: Universal properties verified across all inputs
- **Mock Isolation**: Easy to mock dependencies for testing
- **Test Organization**: Clear test structure mirrors code structure

### Reusability

- **Independent Orchestrators**: Can be used outside of Flow context
- **Composable**: Orchestrators can be combined in different ways
- **Extensible**: Easy to add new orchestrators without modifying existing ones

### Robustness

- **Isolated Changes**: Changes to one orchestrator don't affect others
- **Error Isolation**: Errors in one orchestrator don't cascade
- **Graceful Degradation**: System continues working even if one orchestrator fails

### Performance

- **Lazy Loading**: Orchestrators loaded only when needed
- **Parallel Potential**: Independent orchestrators can run in parallel
- **Reduced Memory**: Only active orchestrators consume memory

### Developer Experience

- **Clear Structure**: Easy to understand system architecture
- **Quick Onboarding**: New developers can understand code faster
- **Confident Changes**: Isolated changes reduce fear of breaking things
- **Better Reviews**: Smaller files make code reviews more effective

