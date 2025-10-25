---
inclusion: fileMatch
fileMatchPattern: ['**/crews/**/*.py', '**/orchestrators/**/*.py', 'src/finwiz/main.py']
---

# CrewAI Best Practices

Performance-optimized patterns for CrewAI Flow state management, agent reasoning, crew planning, and multi-agent collaboration in FinWiz.

## Flow State Management (CRITICAL)

### Mandatory Pattern: Structured State

Always use Pydantic models for type-safe Flow state:

```python
from pydantic import BaseModel
from crewai.flow.flow import Flow

class MyFlowState(BaseModel):
    """Type-safe state with validation."""
    holdings_processed: int = 0
    current_ticker: str = ""
    results: dict[str, Any] = {}

class MyFlow(Flow[MyFlowState]):
    @start()
    def initialize(self) -> dict[str, Any]:
        self.state.holdings_processed = 0
        return {"status": "initialized"}
```

**Non-Negotiable Rules:**

- ✅ Use `Flow[PydanticModel]` for type safety
- ✅ All Flow methods return `dict[str, Any]`
- ✅ Access state via `self.state.field_name`
- ❌ NEVER use `self.inputs` (unstructured, error-prone)

### Data Flow Between Methods

Listeners receive upstream data as parameters:

```python
@start()
def generate_data(self) -> dict[str, Any]:
    """Return data for downstream listeners."""
    return {"ticker": "AAPL", "data": {...}}

@listen(generate_data)
def process_data(self, upstream_data: dict[str, Any]) -> dict[str, Any]:
    """Receive data from upstream as parameter."""
    ticker = upstream_data["ticker"]
    self.state.last_processed = ticker
    return {"processed": True}
```

### Conditional Routing

Use `@router` to direct flow based on state:

```python
@router(process_payment)
def check_status(self, previous_result: dict[str, Any]) -> str:
    """Return string to route to specific listener."""
    if self.state.is_approved:
        return "approved"
    elif self.state.retry_count < 3:
        return "retry"
    return "rejected"

@listen("approved")
def handle_approval(self) -> dict[str, Any]:
    return {"status": "success"}
```

## Agent Reasoning (`reasoning=True`)

### When to Enable

**Enable for:**

- Complex multi-step analysis requiring planning
- Error-prone operations needing recovery strategies
- Tasks using multiple tools with dependencies
- Single-execution deep analysis

**Disable for:**

- Simple validation (ticker format checks)
- Direct API calls (single-step fetches)
- Final reporters (consolidation only)
- High-volume executions (66+ runs)
- Time-sensitive operations

### Configuration

```python
# Complex analysis - reasoning enabled
analyst = Agent(
    role="Deep Analysis Specialist",
    reasoning=True,
    max_reasoning_attempts=3,  # Prevent infinite loops
    verbose=True
)

# Simple validation - reasoning disabled
validator = Agent(
    role="Ticker Validator",
    reasoning=False,
    verbose=True
)
```

**Performance Cost:** 5-15 seconds, 1-3 LLM calls, 500-2000 tokens per reasoning cycle

## Crew Planning (`planning=True`)

### Decision Rule

Enable planning when: `(agents >= 4) AND (tasks >= 6) AND (execution_volume <= 3)`

**Enable for:**

- Multi-agent coordination (4+ agents)
- Complex workflows (6+ tasks)
- Low-volume executions (≤3 runs)
- Portfolio rebalancing (single execution)

**Disable for:**

- High-volume executions (66+ runs)
- Single-agent crews
- Simple workflows (<6 tasks)
- Deep analysis crews (repeated per holding)

### Configuration

```python
# High-volume execution - NO planning
class DeepAnalysisCrew(CrewBase):
    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            planning=False,  # Overhead × 66 executions = too costly
            max_rpm=20
        )

# Multi-agent coordination - YES planning
class PortfolioRebalancingCrew(CrewBase):
    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[self.analyzer(), self.risk_assessor(), self.optimizer()],
            tasks=self.tasks,
            planning=True,
            planning_llm="gpt-4o",
            max_rpm=20
        )
```

## Agent Delegation (`allow_delegation=True`)

### When to Enable

**Enable for:**

- Coordinator/lead agents managing workflow
- Multi-agent workflows with dependencies
- Agents needing to ask questions

**Disable for:**

- Focused specialists (single responsibility)
- Final reporters (consolidation only)
- Single-purpose agents

### Configuration

```python
@agent
def coordinator(self) -> Agent:
    """Lead agent that delegates to specialists."""
    return Agent(
        config=self.agents_config["coordinator"],
        reasoning=True,
        allow_delegation=True,
        verbose=True
    )

@agent
def specialist(self) -> Agent:
    """Focused specialist with no delegation."""
    return Agent(
        config=self.agents_config["specialist"],
        reasoning=True,
        allow_delegation=False,
        verbose=True
    )

@final_reporter
@agent
def reporter(self) -> Agent:
    """Final reporter consolidates without tools or delegation."""
    return Agent(
        config=self.agents_config["reporter"],
        tools=[],  # Enforced by @final_reporter decorator
        allow_delegation=False,
        reasoning=False,
        verbose=True
    )
```

**Performance Cost:** 5-15 seconds per delegation, 1-2 LLM calls

## Performance Decision Matrix

| Feature | Enable When | Disable When | Cost per Use |
|---------|-------------|--------------|--------------|
| `reasoning=True` | Complex multi-step, error recovery | Simple validation, high-volume | 5-15s, 1-3 calls |
| `planning=True` | 4+ agents, 6+ tasks, ≤3 runs | High-volume, single agent | Overhead × count |
| `allow_delegation=True` | Coordinators, multi-agent | Specialists, reporters | 5-15s per delegation |

## Implementation Checklist

### Flow Implementation

- [ ] Use `Flow[PydanticModel]` for structured state
- [ ] All Flow methods return `dict[str, Any]`
- [ ] Listeners receive upstream data as parameters
- [ ] Never use `self.inputs` for state management
- [ ] Use `@router` for conditional flow control

### Agent Configuration

- [ ] `reasoning=True` only for complex analysis
- [ ] `max_reasoning_attempts=3` when reasoning enabled
- [ ] `allow_delegation=True` only for coordinators
- [ ] Final reporters: `tools=[]`, `allow_delegation=False`, `reasoning=False`
- [ ] Use `@final_reporter` decorator for enforcement

### Crew Setup

- [ ] `planning=True` only when: 4+ agents, 6+ tasks, ≤3 runs
- [ ] `max_rpm=20` for rate limiting
- [ ] `respect_context_window=True` for context management
- [ ] `verbose=True` for debugging

### Performance Optimization

- [ ] Disable reasoning for high-volume executions (66+ runs)
- [ ] Disable planning for repeated crew runs
- [ ] Use `async_execution=true` for I/O-bound tasks (except final task)
- [ ] Consider execution volume when enabling features

## Common Patterns

### Single-Execution Complex Analysis

```python
# Portfolio rebalancing (runs once)
crew = Crew(
    agents=[coordinator, analyst, optimizer],  # 3+ agents
    tasks=self.tasks,  # 6+ tasks
    planning=True,  # Complex coordination
    reasoning=True,  # Complex decisions
    max_rpm=20
)
```

### High-Volume Simple Analysis

```python
# Deep analysis per holding (runs 66+ times)
crew = Crew(
    agents=[analyst],  # Single agent
    tasks=self.tasks,  # Simple workflow
    planning=False,  # Avoid overhead
    reasoning=False,  # Fast execution
    max_rpm=20
)
```

### Multi-Agent Coordination

```python
# Coordinator delegates to specialists
coordinator = Agent(
    reasoning=True,
    allow_delegation=True  # Can delegate
)

specialist = Agent(
    reasoning=True,
    allow_delegation=False  # Focused execution
)
```

## Anti-Patterns to Avoid

❌ Using `self.inputs` instead of `self.state`
❌ Flow methods not returning `dict[str, Any]`
❌ Enabling reasoning for high-volume executions
❌ Enabling planning for single-agent crews
❌ Final reporters with non-empty tools
❌ Missing `max_reasoning_attempts` when reasoning enabled
❌ Delegation enabled for specialist agents
