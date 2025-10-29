---
inclusion: always
---


# CrewAI Flow Compliance Standards

**CRITICAL**: Essential patterns for CrewAI Flow integrations. These patterns MUST be followed for all Flow implementations.

## Core Principle

**Follow CrewAI Flow documentation patterns exactly.** Custom approaches lead to architectural inconsistencies and maintenance issues.

## State Management (CRITICAL)

### ✅ REQUIRED Pattern

```python
from pydantic import BaseModel
from crewai.flow import Flow, listen
from typing import Dict, Optional, Any

class FlowState(BaseModel):
    """Structured state with type safety."""
    analysis_results: Dict[str, Any] = {}
    processing_success: bool = False
    error_message: Optional[str] = None

class FinwizFlow(Flow[FlowState]):
    @listen("upstream_method")
    def process_data(self) -> dict[str, Any]:
        # Update structured state
        self.state.processing_success = True
        self.state.analysis_results = {"key": "value"}
        
        # MUST return data for downstream listeners
        return {"processed_data": self.state.analysis_results}
```

### ❌ BANNED Pattern

```python
class BadFlow(Flow):  # Missing structured state
    @listen("upstream_method")
    def process_data(self) -> None:  # Missing return value
        self.inputs["results"] = {"key": "value"}  # Unstructured, error-prone
```

## Flow Method Signatures (CRITICAL)

### Data Passing Pattern

```python
# ✅ REQUIRED - Flow methods return data for downstream listeners
@listen("check_portfolio")
def analyze_holdings(self) -> dict[str, Any]:
    """MUST return dict for downstream listeners."""
    analysis_results = perform_analysis()
    
    # Update structured state
    self.state.analysis_complete = True
    
    # REQUIRED: Return for downstream methods
    return {"analysis": analysis_results}

@listen("analyze_holdings")
def process_results(self, analysis_data: dict[str, Any]) -> dict[str, Any]:
    """MUST receive upstream data as parameter."""
    holdings = analysis_data.get("analysis", {})
    
    processed = process_holdings(holdings)
    return {"processed": processed}
```

### ❌ BANNED Patterns

```python
# Missing return value
@listen("check_portfolio")
def bad_analyze(self) -> None:  # WRONG: Should return dict[str, Any]
    self.inputs["analysis"] = data  # WRONG: Use self.state

# Missing parameter reception
@listen("bad_analyze")
def bad_process(self) -> None:  # WRONG: Should receive parameter
    analysis = self.inputs.get("analysis", {})  # WRONG: Error-prone
```

## Crew Execution Pattern

### ✅ REQUIRED - Direct Crew Instantiation

```python
from finwiz.crews.stock_crew.stock_crew import StockCrew

@listen("check_portfolio")
def analyze_stock(self) -> dict[str, Any]:
    # Direct crew instantiation (CrewAI Flow standard)
    crew = StockCrew()
    result = crew.crew().kickoff(inputs={"ticker": "AAPL"})
    
    # Process and return for downstream listeners
    return {"crew_result": result}
```

### ❌ BANNED - Factory Patterns

```python
@listen("check_portfolio")
def bad_analyze_stock(self) -> dict[str, Any]:
    # WRONG: Using crew_factory (inconsistent with Flow patterns)
    result_data = self.crew_factory.execute_stock_crew(inputs)
    return result_data
```

## State Access After Execution

### ✅ REQUIRED - Structured State Access

```python
# Execute Flow
flow = FinwizFlow()
result = flow.kickoff()

# Access structured state with type safety
final_state = flow.state
if final_state.processing_success:
    for key, value in final_state.analysis_results.items():
        print(f"{key}: {value}")
```

### ❌ BANNED - Unstructured Access

```python
# WRONG: Unstructured state access
flow = BadFlow()
result = flow.kickoff()
results = flow.inputs.get("analysis_results", {})  # No type safety, error-prone
```

## Integration Pattern

### Portfolio Review Integration

```python
# ✅ REQUIRED - Access Flow state after execution
def build_portfolio_review_with_flow_data():
    # Execute Flow
    flow = FinwizFlow()
    flow_result = flow.kickoff()
    
    # Access structured state with type safety
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

## Error Handling Pattern

### ✅ REQUIRED - Graceful Degradation

```python
@listen("check_portfolio")
def analyze_holdings_deep(self) -> dict[str, Any]:
    enabled = os.getenv("DEEP_ANALYSIS_ENABLED", "false").lower() == "true"
    if not enabled:
        logger.info("Deep analysis disabled")
        return {}  # MUST return dict for downstream methods
    
    try:
        results = perform_deep_analysis()
        
        # Update structured state
        self.state.deep_analysis_success = True
        self.state.deep_analysis_results = results
        
        # REQUIRED: Return for downstream methods
        return {"analysis_results": results}
        
    except Exception as e:
        logger.error(f"Deep analysis failed: {e}")
        
        # Update state with error
        self.state.deep_analysis_success = False
        self.state.deep_analysis_error = str(e)
        
        # REQUIRED: Return error info for downstream methods
        return {"analysis_results": {}, "error": str(e)}
```

## Compliance Checklist

**MANDATORY** for all CrewAI Flow implementations:

- [ ] **State Model**: Pydantic model with `Flow[StateModel]` pattern
- [ ] **Method Returns**: All Flow methods return `dict[str, Any]`
- [ ] **Parameter Reception**: Listeners receive upstream data as parameters
- [ ] **State Updates**: Use `self.state` (structured), never `self.inputs`
- [ ] **Crew Execution**: Direct instantiation with `crew.kickoff()`
- [ ] **Error Handling**: Return error info for downstream methods
- [ ] **Type Safety**: All state fields have type annotations
- [ ] **Import Pattern**: `from crewai.flow import Flow, listen`

## Common Anti-Patterns

### ❌ BANNED Patterns
- Using `self.inputs` instead of `self.state`
- Flow methods returning `None` instead of `dict[str, Any]`
- Unstructured state without Pydantic models
- Missing return type annotations (`-> dict[str, Any]`)
- Not receiving parameters in listener methods
- Using crew_factory instead of direct instantiation
- Silent failures without returning error info

## Benefits

✅ **Type Safety**: Pydantic models prevent runtime errors  
✅ **Data Integrity**: Structured state ensures consistency  
✅ **Framework Alignment**: Follows CrewAI best practices  
✅ **Maintainability**: Clear, predictable data flow  
✅ **Debugging**: Structured state simplifies troubleshooting

## Quick Reference

### Flow Class Template

```python
from pydantic import BaseModel
from crewai.flow import Flow, listen
from typing import Dict, Any

class MyFlowState(BaseModel):
    results: Dict[str, Any] = {}
    success: bool = False

class MyFlow(Flow[MyFlowState]):
    @listen("upstream")
    def process(self, data: dict[str, Any]) -> dict[str, Any]:
        # Update state
        self.state.success = True
        # Return for downstream
        return {"processed": data}
```

### Crew Execution Template

```python
from finwiz.crews.stock_crew.stock_crew import StockCrew

@listen("trigger")
def analyze(self) -> dict[str, Any]:
    crew = StockCrew()
    result = crew.crew().kickoff(inputs={"ticker": "AAPL"})
    return {"result": result}
```