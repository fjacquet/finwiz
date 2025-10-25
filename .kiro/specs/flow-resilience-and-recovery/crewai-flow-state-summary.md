# CrewAI Flow State Management Summary

> Key patterns from CrewAI documentation for implementing flow resilience and recovery

## Core Concepts

### State Lifecycle
1. **Initialization** - State initialized when flow is created
2. **Modification** - Flow methods access and modify state
3. **Transmission** - State passed automatically between methods
4. **Persistence** (optional) - State saved to storage and retrieved
5. **Completion** - Final state reflects cumulative changes

### Two State Approaches

**Unstructured State** (Dictionary-like):
- Flexible, simple for prototyping
- Access via `self.state["key"]`
- No type checking or validation
- ❌ NOT RECOMMENDED for production

**Structured State** (Pydantic Models):
- Type-safe with validation
- Access via `self.state.field`
- IDE autocompletion support
- ✅ RECOMMENDED for FinWiz

## Critical Patterns for FinWiz

### 1. Use Structured State with Pydantic

```python
from pydantic import BaseModel, Field
from crewai.flow.flow import Flow

class ResilienceState(BaseModel):
    # Progress tracking
    holdings_processed: int = 0
    holdings_remaining: int = 0
    total_holdings: int = 0
    
    # Error tracking
    failed_holdings: list[str] = []
    retry_counts: dict[str, int] = {}
    
    # Timing
    start_time: datetime = Field(default_factory=datetime.now)
    last_checkpoint: datetime | None = None
    
    # Results
    analysis_results: dict[str, Any] = {}
    success_rate: float = 0.0

class ResilientFlow(Flow[ResilienceState]):
    # Flow methods here
    pass
```

### 2. Automatic State ID

- Every flow gets unique UUID automatically
- Unstructured: `self.state["id"]`
- Structured: `self.state.id`
- Use for tracking, logging, retrieving persisted states

### 3. State Persistence with @persist()

**Class-Level** (saves after every method):
```python
from crewai.flow.persistence import persist

@persist()  # Saves state after every method
class PersistentFlow(Flow[MyState]):
    @start()
    def step_one(self):
        self.state.value += 1
        return "Done"
```

**Method-Level** (saves after specific methods):
```python
class SelectiveFlow(Flow[MyState]):
    @start()
    def step_one(self):
        self.state.count = 1
        return "Step 1"
    
    @persist()  # Only persist after this method
    @listen(step_one)
    def important_step(self, prev_result):
        self.state.important_data = "Persisted"
        return "Step 2"
```

### 4. Conditional @start() for Resume

```python
class ResumableFlow(Flow[MyState]):
    @start()  # Unconditional start
    def init(self):
        self.state.initialized = True
        return "Init"
    
    @start("init")  # Conditional start - runs after init OR on resume
    def maybe_begin(self):
        if not self.state.already_processed:
            return "Begin processing"
        return "Skip - already done"
```

### 5. Data Passing Between Methods

```python
@start()
def generate_data(self):
    # Return value passed to listeners
    return {"ticker": "AAPL", "data": {...}}

@listen(generate_data)
def process_data(self, data_from_previous):
    # Receive data as parameter
    ticker = data_from_previous["ticker"]
    
    # Also update state
    self.state.last_processed = ticker
    
    # Return for next method
    return {"processed": True}
```

### 6. State-Based Conditional Logic with @router

```python
@router(process_payment)
def check_status(self, previous_result):
    if self.state.is_approved:
        return "approved"
    elif self.state.retry_count < 3:
        return "retry"
    else:
        return "rejected"

@listen("approved")
def handle_approval(self):
    return "Success"

@listen("retry")
def handle_retry(self):
    self.state.retry_count += 1
    return "Retrying"
```

## Best Practices for FinWiz

### 1. Keep State Focused
```python
# ✅ GOOD - Focused state
class AnalysisState(BaseModel):
    holdings_processed: int
    current_ticker: str
    errors: list[ValidationError]

# ❌ BAD - Bloated state
class BloatedState(BaseModel):
    everything: dict  # Too broad
```

### 2. Document State Transitions
```python
@start()
def initialize(self):
    """
    Initialize analysis state.
    State before: {}
    State after: {holdings_processed: 0, start_time: datetime}
    """
    self.state.holdings_processed = 0
    self.state.start_time = datetime.now()
```

### 3. Handle State Errors Gracefully
```python
@listen(previous_step)
def process_data(self, _):
    try:
        value = self.state.some_field
    except AttributeError:
        self.state.errors.append("Missing field")
        value = default_value
    return value
```

### 4. Use State for Progress Tracking
```python
def update_progress(self):
    """Helper to calculate progress"""
    if self.state.total_holdings > 0:
        self.state.progress = (
            self.state.holdings_processed / 
            self.state.total_holdings * 100
        )
```

### 5. Integrate with Crews
```python
@listen(get_parameters)
def execute_crew(self, _):
    # Use state to parameterize crew
    crew = DeepAnalysisCrew()
    result = crew.crew().kickoff(inputs={
        "ticker": self.state.current_ticker,
        "asset_class": self.state.asset_class
    })
    
    # Store result in state
    self.state.analysis_results[self.state.current_ticker] = result
    return "Crew complete"
```

## Implementation Checklist for FinWiz

- [ ] Define structured Pydantic state model
- [ ] Use `Flow[StateModel]` type parameter
- [ ] Apply `@persist()` at class or method level
- [ ] Implement conditional `@start()` for resume
- [ ] Use `@router` for conditional logic
- [ ] Return data from methods for downstream listeners
- [ ] Access state via `self.state.field` (not dict)
- [ ] Track progress in state
- [ ] Store errors in state using ValidationError
- [ ] Use state UUID for logging and tracking
- [ ] Document state transitions in docstrings
- [ ] Implement helper methods for complex state updates

## Key Differences from Custom Checkpointing

| Custom Approach | CrewAI Flow Approach |
|----------------|---------------------|
| Manual file I/O | `@persist()` decorator |
| Custom checkpoint directory | Built-in persistence location |
| Manual state serialization | Automatic Pydantic serialization |
| Custom resume logic | Conditional `@start()` methods |
| Manual UUID generation | Automatic state UUID |
| Custom state validation | Pydantic validation |

## References

- CrewAI Flow State Management Guide (provided)
- FinWiz existing patterns: `flow_orchestrator.py`, `flow_state.py`
- Pydantic v2 documentation for model validation

---

**Version**: 1.0  
**Created**: 2025-01-11  
**Purpose**: Guide implementation of flow resilience using CrewAI native patterns
