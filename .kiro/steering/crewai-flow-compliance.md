# CrewAI Flow Compliance Standards

**CRITICAL**: This document contains essential lessons learned from deep portfolio analysis implementation. These patterns MUST be followed for all CrewAI Flow integrations.

## Core Principle

**Always follow CrewAI Flow documentation patterns exactly.** Mixing patterns or creating custom approaches leads to architectural inconsistencies and maintenance issues.

## State Management (CRITICAL)

### ✅ CORRECT Pattern

```python
from pydantic import BaseModel
from crewai.flow import Flow
from typing import Dict, Optional, Any

class MyFlowState(BaseModel):
    # Structured fields with type safety
    analysis_results: Dict[str, Any] = {}
    processing_success: bool = False
    error_message: Optional[str] = None

class MyFlow(Flow[MyFlowState]):
    @listen("upstream_method")
    def process_data(self) -> dict[str, Any]:
        # Update structured state
        self.state.processing_success = True
        self.state.analysis_results = {"key": "value"}
        
        # Return data for downstream methods
        return {"processed_data": self.state.analysis_results}
```

### ❌ WRONG Pattern

```python
class BadFlow(Flow):  # No structured state
    @listen("upstream_method")
    def process_data(self) -> None:  # No return value
        # Unstructured state updates
        self.inputs["results"] = {"key": "value"}  # Error-prone
        # No return for downstream methods
```

## Flow Method Signatures (CRITICAL)

### Data Passing Between Methods

```python
# ✅ CORRECT - Proper Flow data passing
@listen("check_portfolio")
def analyze_holdings(self) -> dict[str, Any]:
    """Returns data for downstream listeners."""
    analysis_results = perform_analysis()
    
    # Update state
    self.state.analysis_complete = True
    
    # Return for downstream methods
    return {"analysis": analysis_results}

@listen("analyze_holdings")
def process_results(self, analysis_data: dict[str, Any]) -> dict[str, Any]:
    """Receives data from upstream method as parameter."""
    holdings = analysis_data.get("analysis", {})
    
    processed = process_holdings(holdings)
    return {"processed": processed}

# ❌ WRONG - No data passing
@listen("check_portfolio")
def bad_analyze(self) -> None:  # Should return dict
    self.inputs["analysis"] = perform_analysis()  # Only state update

@listen("bad_analyze")
def bad_process(self) -> None:  # Should receive parameter
    # Has to access state directly instead of receiving parameter
    analysis = self.inputs.get("analysis", {})  # Error-prone
```

## Crew Execution Patterns (CRITICAL)

### ✅ CORRECT - Direct Crew Instantiation

```python
from finwiz.crews.stock_crew.stock_crew import StockCrew

@listen("check_portfolio")
def analyze_stock(self) -> dict[str, Any]:
    # Direct crew instantiation (CrewAI Flow pattern)
    crew = StockCrew()
    result = crew.crew().kickoff(inputs={"ticker": "AAPL"})
    
    # Process result and return
    return {"crew_result": result}
```

### ❌ WRONG - Mixed Patterns

```python
@listen("check_portfolio")
def bad_analyze_stock(self) -> dict[str, Any]:
    # Using crew_factory (inconsistent with Flow patterns)
    result_data = self.crew_factory.execute_stock_crew(inputs)
    return result_data
```

## State Access After Flow Execution

### ✅ CORRECT - Structured State Access

```python
# Execute Flow
flow = MyFlow()
result = flow.kickoff()

# Access structured state with type safety
final_state = flow.state
if final_state.processing_success:
    for key, value in final_state.analysis_results.items():
        print(f"{key}: {value}")
```

### ❌ WRONG - Unstructured Access

```python
# Bad state access
flow = BadFlow()
result = flow.kickoff()

# Error-prone unstructured access
results = flow.inputs.get("analysis_results", {})  # No type safety
```

## Integration with Existing Systems

### Portfolio Review Integration

```python
# ✅ CORRECT - Access Flow state after execution
def build_portfolio_review_with_flow_data():
    # Execute Flow
    flow = FinwizFlow()
    flow_result = flow.kickoff()
    
    # Access structured state
    if flow.state.deep_analysis_success:
        deep_results = flow.state.deep_analysis_results
        alternatives = flow.state.portfolio_alternatives
        
        # Merge into portfolio review
        for decision in portfolio_decisions:
            if decision.ticker in deep_results:
                analysis = deep_results[decision.ticker]
                decision.composite_score = analysis.composite_score
                decision.grade = analysis.grade
```

## Error Handling in Flow Methods

### ✅ CORRECT - Graceful Degradation

```python
@listen("check_portfolio")
def analyze_holdings_deep(self) -> dict[str, Any]:
    enabled = os.getenv("DEEP_ANALYSIS_ENABLED", "false").lower() == "true"
    if not enabled:
        logger.info("Deep analysis disabled")
        return {}  # Return empty dict for downstream methods
    
    try:
        # Perform analysis
        results = perform_deep_analysis()
        
        # Update state
        self.state.deep_analysis_success = True
        self.state.deep_analysis_results = results
        
        # Return for downstream methods
        return {"analysis_results": results}
        
    except Exception as e:
        logger.error(f"Deep analysis failed: {e}")
        
        # Update state with error
        self.state.deep_analysis_success = False
        self.state.deep_analysis_error = str(e)
        
        # Return error info for downstream methods
        return {"analysis_results": {}, "error": str(e)}
```

## Flow Compliance Checklist

Before implementing any CrewAI Flow integration:

- [ ] **State Model**: Defined Pydantic model for Flow state
- [ ] **Flow Class**: Uses `Flow[StateModel]` pattern
- [ ] **Method Returns**: All Flow methods return `dict[str, Any]`
- [ ] **Parameter Reception**: Listeners receive upstream data as parameters
- [ ] **State Updates**: Uses `self.state` (structured) not `self.inputs`
- [ ] **Crew Execution**: Direct instantiation with `crew.kickoff()`
- [ ] **Error Handling**: Returns error info for downstream methods
- [ ] **Type Safety**: All state fields have proper type annotations
- [ ] **Documentation**: Follows exact CrewAI Flow documentation patterns

## Common Mistakes to Avoid

### ❌ State Management Mistakes
- Using `self.inputs` instead of `self.state`
- No return values from Flow methods
- Unstructured state without Pydantic models

### ❌ Method Signature Mistakes
- Missing return type annotations
- Not receiving parameters in listener methods
- Returning `None` instead of `dict[str, Any]`

### ❌ Integration Mistakes
- Mixing crew_factory with direct instantiation
- Inconsistent data passing patterns
- Not following CrewAI Flow documentation

### ❌ Error Handling Mistakes
- Not returning error info for downstream methods
- Silent failures without state updates
- Breaking Flow execution chain on errors

## Benefits of Proper Flow Compliance

✅ **Type Safety**: Pydantic models prevent runtime errors
✅ **Data Integrity**: Structured state ensures consistent data
✅ **Framework Alignment**: Follows CrewAI best practices
✅ **Maintainability**: Clear, predictable data flow
✅ **Debugging**: Structured state makes issues easier to trace
✅ **IDE Support**: Type hints enable better development experience

## Enforcement

These patterns are MANDATORY for all CrewAI Flow integrations. Code reviews should verify:

1. **Structured state management** with Pydantic models
2. **Proper method signatures** with return values and parameters
3. **Consistent crew execution** patterns
4. **Framework compliance** with CrewAI Flow documentation

---

**Version**: 1.0  
**Created**: 2025-01-08  
**Purpose**: Capture critical lessons from deep portfolio analysis Flow integration