# CrewAI Agent Reasoning Summary

> Key patterns from CrewAI documentation for implementing agent reasoning in resilient flows

## Overview

Agent reasoning allows agents to reflect on tasks and create execution plans before starting work. This is critical for resilient flows where agents need to handle complex, multi-step operations that may fail.

## Core Concept

When `reasoning=True`, the agent:
1. **Reflects** on the task and creates a detailed plan
2. **Evaluates** whether it's ready to execute
3. **Refines** the plan as necessary (up to max_reasoning_attempts)
4. **Injects** the reasoning plan into the task description
5. **Executes** the task with the plan as context

## Basic Usage

```python
from crewai import Agent

agent = Agent(
    role="Data Analyst",
    goal="Analyze complex datasets and provide insights",
    backstory="You are an experienced data analyst.",
    reasoning=True,  # Enable reasoning
    max_reasoning_attempts=3  # Optional: limit refinement cycles
)
```

## Configuration Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `reasoning` | bool | False | Enable/disable reasoning |
| `max_reasoning_attempts` | int | None | Max refinement attempts (None = unlimited) |

## Reasoning Process Flow

```
Task Assigned
    ↓
[Reasoning Phase]
    ↓
1. Understand task requirements
    ↓
2. Create execution plan
    ↓
3. Identify potential challenges
    ↓
4. Plan tool usage
    ↓
5. Define expected outcome
    ↓
Evaluate: Ready? ──No──→ Refine plan (if attempts remain)
    ↓ Yes
Inject plan into task description
    ↓
Execute task with plan context
```

## Example Reasoning Output

```
Task: Analyze the provided sales data and identify key trends.

Reasoning Plan:

1. Understanding of the task:
   I need to analyze sales data to identify key trends for business decisions.

2. Key steps I'll take:
   - Examine data structure and available fields
   - Perform exploratory data analysis
   - Analyze sales by time periods
   - Analyze by product categories and customer segments
   - Identify top 3 most significant trends

3. Approach to challenges:
   - Missing values: decide whether to fill or filter
   - Outliers: investigate validity vs errors
   - Non-obvious trends: apply statistical methods

4. Use of available tools:
   - Data analysis tools for exploration and visualization
   - Statistical tools for pattern identification
   - Knowledge retrieval for sales analysis best practices

5. Expected outcome:
   Concise report highlighting top 3 sales trends with supporting evidence.

READY: I am ready to execute the task.
```

## Error Handling

**Built-in Robustness:**
- If reasoning fails, agent proceeds WITHOUT the plan
- Task execution continues (graceful degradation)
- Errors are logged but don't block execution

```python
import logging

logging.basicConfig(level=logging.INFO)

agent = Agent(
    role="Data Analyst",
    goal="Analyze data",
    reasoning=True,
    max_reasoning_attempts=3
)

# If reasoning fails, it's logged and execution continues
result = agent.execute_task(task)
```

## Best Practices for FinWiz

### 1. Enable Reasoning for Complex Tasks

```python
# ✅ GOOD - Reasoning for complex analysis
deep_analyst = Agent(
    role="Deep Analysis Specialist",
    goal="Perform comprehensive holding analysis",
    reasoning=True,  # Complex task needs planning
    max_reasoning_attempts=3
)

# ❌ BAD - Reasoning for simple tasks (overhead)
simple_validator = Agent(
    role="Ticker Validator",
    goal="Validate ticker format",
    reasoning=True  # Overkill for simple validation
)
```

### 2. Set Reasonable Attempt Limits

```python
# ✅ GOOD - Reasonable limit
agent = Agent(
    role="Analyst",
    reasoning=True,
    max_reasoning_attempts=3  # Prevents infinite loops
)

# ⚠️ RISKY - No limit
agent = Agent(
    role="Analyst",
    reasoning=True,
    max_reasoning_attempts=None  # Could loop indefinitely
)
```

### 3. Combine with Task Descriptions

```python
# ✅ GOOD - Clear task description helps reasoning
task = Task(
    description="""
    Analyze holding {ticker} for {asset_class}.
    
    SINGLE TICKER MODE: Analyze ONE specific ticker.
    Do NOT request additional tickers.
    
    Steps:
    1. Validate ticker
    2. Fetch fundamental data
    3. Perform technical analysis
    4. Assess risks
    5. Generate grade (A+ to F)
    """,
    expected_output="DeepAnalysisResult with grade and scores",
    agent=analyst
)
```

### 4. Use with Retry Logic

```python
# Reasoning helps agent understand retry context
@retry(stop=stop_after_attempt(3))
def analyze_with_reasoning(ticker: str):
    analyst = Agent(
        role="Deep Analyst",
        reasoning=True,
        max_reasoning_attempts=2  # Quick planning per retry
    )
    
    task = Task(
        description=f"Analyze {ticker}. Previous attempts failed - be thorough.",
        agent=analyst
    )
    
    return analyst.execute_task(task)
```

## Integration with FinWiz Resilience

### Reasoning + State Management

```python
from crewai.flow.flow import Flow, listen, start
from pydantic import BaseModel

class AnalysisState(BaseModel):
    current_ticker: str = ""
    reasoning_plans: dict[str, str] = {}  # Store plans
    execution_attempts: dict[str, int] = {}

class ResilientAnalysisFlow(Flow[AnalysisState]):
    @listen("prepare_analysis")
    def analyze_holding(self, ticker_data):
        ticker = ticker_data["ticker"]
        
        # Create agent with reasoning
        analyst = Agent(
            role="Deep Analyst",
            reasoning=True,
            max_reasoning_attempts=3
        )
        
        # Store reasoning plan in state
        self.state.current_ticker = ticker
        
        # Execute with reasoning
        result = analyst.execute_task(task)
        
        # Track in state
        self.state.execution_attempts[ticker] = 1
        
        return result
```

### Reasoning + Error Recovery

```python
def analyze_with_reasoning_and_recovery(ticker: str, attempt: int = 1):
    """Analyze with reasoning, adjusting plan based on previous failures."""
    
    # Adjust reasoning attempts based on retry count
    max_attempts = max(1, 4 - attempt)  # Fewer attempts on retries
    
    analyst = Agent(
        role="Deep Analyst",
        reasoning=True,
        max_reasoning_attempts=max_attempts
    )
    
    # Include failure context in task description
    failure_context = ""
    if attempt > 1:
        failure_context = f"\nPrevious {attempt-1} attempts failed. Be extra thorough."
    
    task = Task(
        description=f"""
        Analyze {ticker} for deep portfolio analysis.
        {failure_context}
        
        Focus on:
        - Data validation
        - Error handling
        - Comprehensive analysis
        """,
        agent=analyst
    )
    
    try:
        return analyst.execute_task(task)
    except Exception as e:
        if attempt < 3:
            logger.warning(f"Attempt {attempt} failed, retrying with reasoning")
            return analyze_with_reasoning_and_recovery(ticker, attempt + 1)
        raise
```

## When to Use Reasoning in FinWiz

### ✅ Use Reasoning For:
- **Deep analysis tasks** - Complex multi-step analysis
- **Error-prone operations** - Tasks that often fail
- **Multi-tool tasks** - Tasks requiring multiple tools
- **Complex decision-making** - Tasks with conditional logic
- **Recovery scenarios** - Retries after failures

### ❌ Don't Use Reasoning For:
- **Simple validation** - Ticker format checks
- **Direct API calls** - Single-step data fetches
- **Final reporters** - Consolidation tasks (no tools)
- **Fast operations** - Time-sensitive tasks
- **Deterministic tasks** - No decision-making needed

## Performance Considerations

### Reasoning Overhead
- **Time**: Adds 5-15 seconds per task
- **API Calls**: 1-3 additional LLM calls
- **Tokens**: ~500-2000 tokens per reasoning cycle

### Optimization Strategies
```python
# Strategy 1: Limit attempts for retries
if is_retry:
    max_attempts = 1  # Quick planning on retries
else:
    max_attempts = 3  # Thorough planning on first try

# Strategy 2: Disable for simple tasks
if task_complexity == "simple":
    reasoning = False
else:
    reasoning = True

# Strategy 3: Adjust based on success rate
if success_rate > 0.9:
    reasoning = False  # Task is reliable
else:
    reasoning = True  # Task needs planning
```

## Monitoring Reasoning

```python
import logging

# Enable detailed logging
logging.basicConfig(level=logging.DEBUG)

# Log reasoning plans
@listen("analyze_holding")
def analyze_with_logging(self, ticker_data):
    analyst = Agent(
        role="Analyst",
        reasoning=True,
        max_reasoning_attempts=3
    )
    
    # Reasoning plan is logged automatically
    result = analyst.execute_task(task)
    
    # Store plan in state for analysis
    if hasattr(result, 'reasoning_plan'):
        self.state.reasoning_plans[ticker] = result.reasoning_plan
    
    return result
```

## Implementation Checklist for FinWiz

- [ ] Enable reasoning for DeepAnalysisCrew agents
- [ ] Set `max_reasoning_attempts=3` to prevent loops
- [ ] Update task descriptions to be reasoning-friendly
- [ ] Store reasoning plans in flow state for debugging
- [ ] Adjust reasoning based on retry attempts
- [ ] Monitor reasoning overhead in performance metrics
- [ ] Disable reasoning for simple validation tasks
- [ ] Log reasoning plans for failed analyses
- [ ] Test reasoning with various failure scenarios
- [ ] Document which agents use reasoning and why

## Key Takeaways

1. **Reasoning improves reliability** - Agents plan before executing
2. **Set attempt limits** - Prevent infinite reasoning loops
3. **Graceful degradation** - Reasoning failures don't block execution
4. **Clear task descriptions** - Help reasoning process
5. **Monitor overhead** - Reasoning adds time and API calls
6. **Use selectively** - Not all tasks need reasoning
7. **Store plans in state** - Useful for debugging and recovery

## References

- CrewAI Agent Reasoning Documentation (provided)
- FinWiz existing patterns: `deep_analysis.py`, `flow_orchestrator.py`
- Task 1 implementation notes on reasoning-compatible descriptions

---

**Version**: 1.0  
**Created**: 2025-01-11  
**Purpose**: Guide implementation of agent reasoning for resilient flow execution
