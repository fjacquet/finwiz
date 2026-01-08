---
inclusion: always
---

# CrewAI Development Standards for FinWiz

Standards for developing CrewAI crews, agents, tasks, and Flows in FinWiz, including performance optimization, state management, and architectural patterns.

**Last Updated**: 2025-11-15 (Context7 refresh)

## Crew Structure (Required)

All crews must follow this exact structure:

```
src/finwiz/crews/{crew_name}/
├── {crew_name}.py          # @agent, @task, @crew decorators
└── config/
    ├── agents.yaml         # Agent configurations  
    └── tasks.yaml          # Task definitions
```

### CrewBase Decorator Pattern

Use the `@CrewBase` decorator for structured crew definition:

```python
from crewai import Agent, Crew, Task, Process
from crewai.project import CrewBase, agent, crew, task

@CrewBase
class ResearchCrew:
    """Research crew for analyzing topics"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['researcher'],
            tools=[SerperDevTool()],
            verbose=True
        )

    @task
    def research_task(self) -> Task:
        return Task(config=self.tasks_config['research_task'])

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,  # Auto-collected by @agent decorator
            tasks=self.tasks,    # Auto-collected by @task decorator
            process=Process.sequential,
            verbose=True
        )
```

## Agent Configuration

### Standard Agent Pattern

```python
from crewai import Agent, agent
from finwiz.tools.tool_factories import get_stock_crew_tools

@agent
def analyst(self) -> Agent:
    return Agent(
        config=self.agents_config["analyst"],
        tools=get_stock_crew_tools(include_rag=True),
        reasoning=True,
        max_reasoning_attempts=3,  # Prevent infinite loops
        verbose=True,
        allow_delegation=False,  # Only enable for coordinators
        max_iter=20,  # Default: 20 iterations
        max_retry_limit=2,  # Default: 2 retries on error
        respect_context_window=True,  # Manage context size
    )
```

### Complete Agent Parameters

All available agent configuration options:

```python
agent = Agent(
    role="Senior Data Scientist",
    goal="Analyze and interpret complex datasets",
    backstory="Expert with 10+ years experience...",
    llm="gpt-4",  # Default: OPENAI_MODEL_NAME or "gpt-4"
    function_calling_llm=None,  # Optional: Separate LLM for tool calling
    verbose=False,  # Default: False
    allow_delegation=False,  # Default: False (enable for coordinators)
    max_iter=20,  # Default: 20 iterations
    max_rpm=None,  # Optional: Rate limit for API calls
    max_execution_time=None,  # Optional: Maximum execution time in seconds
    max_retry_limit=2,  # Default: 2 retries on error
    allow_code_execution=False,  # Default: False
    code_execution_mode="safe",  # Default: "safe" (options: "safe", "unsafe")
    respect_context_window=True,  # Default: True
    use_system_prompt=True,  # Default: True
    multimodal=False,  # Default: False
    inject_date=False,  # Default: False
    date_format="%Y-%m-%d",  # Default: ISO format
    reasoning=False,  # Default: False (enable for complex analysis)
    max_reasoning_attempts=None,  # Default: None (set to 3 when reasoning=True)
    tools=[],  # Optional: List of tools
    knowledge_sources=None,  # Optional: List of knowledge sources
    embedder=None,  # Optional: Custom embedder configuration
    system_template=None,  # Optional: Custom system prompt template
    prompt_template=None,  # Optional: Custom prompt template
    response_template=None,  # Optional: Custom response template
    step_callback=None,  # Optional: Callback function for monitoring
)
```

### Configuration File (agents.yaml)

```yaml
analyst:
  role: "Financial Analyst"
  goal: "Analyze assets and provide investment recommendations"
  backstory: "Expert analyst with deep market knowledge and quantitative skills"
```

### Agent Configuration Rules

#### Reasoning

- **Enable** (`reasoning=True`) for: Financial analysis, multi-step workflows, complex problem-solving
- **Disable** (`reasoning=False`) for: Simple validators, final reporters, high-volume executions
- **Always** set `max_reasoning_attempts=3` when reasoning is enabled to prevent infinite loops

**Reasoning Behavior**: When enabled, agents will:

1. Plan their approach before executing
2. Reflect on intermediate results
3. Adjust strategy based on outcomes
4. Retry with different approaches on failure

**Performance Cost**: 5-15 seconds, 1-3 LLM calls, 500-2000 tokens per reasoning cycle

#### Delegation

- **Enable** (`allow_delegation=True`) for: Lead/coordinator agents, multi-agent workflows
- **Disable** (`allow_delegation=False`) for: Specialists, final reporters, focused single-purpose agents

**Automatic Tools**: When delegation is enabled, agents automatically get:

- `Delegate Work Tool`: Assign tasks to other agents
- `Ask Question Tool`: Query other agents for information

**Example**:

```python
# ✅ Enable for coordinators
lead_agent = Agent(
    role="Content Lead",
    allow_delegation=True,  # Can delegate to specialists
    ...
)

# ✅ Disable for specialists
specialist_agent = Agent(
    role="Data Analyst", 
    allow_delegation=False,  # Focuses on core expertise
    ...
)
```

### Backstory Templates

**Financial Analysis Agents:**

```yaml
backstory: >
  Expert financial analyst with 15+ years experience in {asset_class} markets.
  Specializes in fundamental analysis, risk assessment, and quantitative metrics.
  Provides data-driven investment recommendations with clear rationale.
```

**Final Reporters:**

```yaml
backstory: >
  Senior investment advisor who synthesizes analysis into actionable recommendations.
  Consolidates findings from research teams WITHOUT external API calls.
```

### Tool Assignment Rules

**Use Tool Factories**:

- `get_stock_crew_tools()` for stock analysis
- `get_etf_crew_tools()` for ETF analysis
- `get_crypto_crew_tools()` for crypto analysis

**Required Tools by Crew**:

**Stock Crew**:

- `QuantitativeAnalysisTool(asset_class="stock")`
- `EnhancedSECAnalysisTool`
- `TickerValidationTool`
- `StandardizedSentimentTool`
- RAG tools via `get_rag_tools()`

**ETF Crew**:

- `QuantitativeAnalysisTool(asset_class="etf")`
- `EnhancedETFAnalysisTool`
- `TickerValidationTool`
- `StandardizedSentimentTool`
- RAG tools

**Crypto Crew**:

- `QuantitativeAnalysisTool(asset_class="crypto")`
- `EnhancedCryptoAnalysisTool`
- `CoinMarketCapTool`
- `TickerValidationTool`
- RAG tools

**Report Crew (SPECIAL)**:

- **Empty tools list** (`tools=[]`)
- Only consume upstream context
- No external API calls

### Final Reporter Pattern

```python
from finwiz.utils.agent_validators import final_reporter

@final_reporter
@agent
def investment_reporter(self) -> Agent:
    return Agent(
        config=self.agents_config['investment_reporter'],
        tools=[],  # MUST be empty - enforced by decorator
        verbose=True
    )
```

## Task Configuration

### Standard Pattern

```yaml
# config/tasks.yaml
stock_analysis_task:
  description: "Analyze stock with quantitative metrics and risk assessment"
  expected_output: "Structured analysis with risk assessment and technical indicators"
  output_pydantic: "TenKInsight"  # Use FinWiz schema
  output_json: true               # Generate machine-readable appendix
  agent: stock_analyst
  async_execution: true           # Enable for I/O-bound tasks
  context:                        # Optional: Use output from other tasks
    - ticker_validation_task      # This task's output becomes context
```

### Task Context and Dependencies

Tasks can use outputs from other tasks as context:

```python
# Tasks with context (enables collaboration)
research_task = Task(
    description="Research the latest developments in quantum computing",
    expected_output="Comprehensive research summary",
    agent=researcher
)

writing_task = Task(
    description="Write an article based on the research findings",
    expected_output="Engaging 800-word article",
    agent=writer,
    context=[research_task]  # Gets research output as context
)

editing_task = Task(
    description="Edit and polish the article for publication",
    expected_output="Publication-ready article",
    agent=editor,
    context=[writing_task]  # Gets article draft as context
)
```

### Required Task Features

- `description`: Clear task objectives
- `expected_output`: Output format description
- `agent`: Responsible agent
- `output_pydantic`: Use existing FinWiz schemas
- `output_json: true`: For machine-readable output
- `async_execution: true`: For I/O-bound tasks (except final task)

### Output Validation

**Use existing FinWiz schemas**:

- Stock: `TenKInsight`, `MarketSentiment`, `RiskAssessmentStandardized`
- ETF: `ETFFactsheet`, `ETFTopHolding`, `RiskAssessmentStandardized`
- Crypto: `CryptoThesis`, `RiskAssessmentStandardized`
- Portfolio: `PortfolioReview`, `HoldingDecision`, `Alternative`

### Task Sequencing

- Use `depends_on` for proper task ordering
- No circular dependencies
- Final task must be synchronous (`async_execution: false`)

### Task Description Format

For reasoning agents, include explicit mode and steps:

```yaml
analysis_task:
  description: >
    Perform comprehensive analysis of the provided {asset_class} ticker: {ticker}
    
    SINGLE TICKER MODE: Analyze ONE specific {asset_class}, not multiple assets.
    The ticker {ticker} is provided as input. Do NOT request additional tickers.
    
    Required Steps:
    1. Validate {ticker} using TickerValidationTool
    2. Fetch {asset_class}-specific data for {ticker}
    3. Calculate quantitative metrics for {ticker}
    4. Generate standardized risk assessment for {ticker}
    5. Provide BUY/HOLD/SELL recommendation with rationale
```

Key elements: "SINGLE TICKER MODE" declaration, repeat `{ticker}` variable throughout

## Crew Configuration

### Standard Pattern

```python
from crewai import Crew, crew, Process

@crew
def crew(self) -> Crew:
    return Crew(
        agents=self.agents,
        tasks=self.tasks,
        process=Process.sequential,
        verbose=True,
        respect_context_window=True,
        max_rpm=20  # Rate limiting
    )
```

### Required Settings

- `process=Process.sequential`: Sequential execution
- `verbose=True`: Enable logging
- `respect_context_window=True`: Manage context size
- `max_rpm=20`: Rate limiting (20 requests per minute)

### Performance Optimization

- Enable `async_execution` for I/O-bound tasks
- Use `depends_on` for proper sequencing
- Final task must be synchronous (CrewAI requirement)
- Implement caching for expensive operations

## Advanced Flow Patterns

### Conditional Starts and Multiple Entry Points

Flows can have multiple start points and conditional triggers:

```python
from crewai.flow.flow import Flow, start, listen, and_, or_

class MultiStartFlow(Flow):
    @start()  # Unconditional start
    def init(self):
        print("Always runs first")
        return {"initialized": True}

    @start("init")  # Conditional start: runs after init OR external trigger
    def maybe_begin(self):
        print("Runs after init or when triggered externally")
        return {"started": True}

    @listen(and_(init, maybe_begin))  # Waits for BOTH
    def proceed(self):
        print("Both init and maybe_begin completed")
        return {"proceeding": True}
```

**Logical Operators**:

- `and_()`: Wait for ALL specified methods
- `or_()`: Wait for ANY specified method
- String names: Listen to router outcomes

### State Visualization and Debugging

Visualize flow state for debugging:

```python
import json
from rich.console import Console
from rich.panel import Panel

class DebugFlow(Flow[MyState]):
    def visualize_state(self):
        """Create visualization of current state"""
        console = Console()
        
        # Convert state to dict
        if hasattr(self.state, "model_dump"):
            state_dict = self.state.model_dump()  # Pydantic v2
        elif hasattr(self.state, "dict"):
            state_dict = self.state.dict()  # Pydantic v1
        else:
            state_dict = dict(self.state)  # Unstructured
        
        # Remove id for cleaner output
        state_dict.pop("id", None)
        
        state_json = json.dumps(state_dict, indent=2, default=str)
        console.print(Panel(state_json, title="Current Flow State"))
    
    @listen(some_method)
    def debug_step(self):
        self.visualize_state()  # Show state at this point
        return {"debug": True}
```

### Error Handling in Flows

Graceful error handling with state tracking:

```python
class RobustFlow(Flow[MyState]):
    @listen("check_portfolio")
    def analyze_holdings_deep(self) -> dict[str, Any]:
        enabled = os.getenv("DEEP_ANALYSIS_ENABLED", "false").lower() == "true"
        if not enabled:
            logger.info("Deep analysis disabled")
            return {}  # MUST return dict
        
        try:
            results = perform_deep_analysis()
            
            # Update state on success
            self.state.deep_analysis_success = True
            self.state.deep_analysis_results = results
            
            return {"analysis_results": results}
            
        except Exception as e:
            logger.error(f"Deep analysis failed: {e}")
            
            # Update state with error
            self.state.deep_analysis_success = False
            self.state.deep_analysis_error = str(e)
            
            # REQUIRED: Return error info for downstream
            return {"analysis_results": {}, "error": str(e)}
```

### Progress Tracking

Track progress through long-running flows:

```python
class ProgressFlow(Flow[MyState]):
    @start()
    def initialize(self):
        self.state.total_steps = 3
        self.state.current_step = 0
        self.state.progress = 0.0
        self.update_progress()
        return "Initialized"

    def update_progress(self):
        """Helper method to calculate progress"""
        if self.state.total_steps > 0:
            self.state.progress = (self.state.current_step / self.state.total_steps) * 100
            print(f"Progress: {self.state.progress:.1f}%")

    @listen(initialize)
    def step_one(self, _):
        # Do work...
        self.state.current_step = 1
        self.update_progress()
        return "Step 1 complete"
```

## Implementation Checklist

### Flow Implementation

- [ ] Use `Flow[PydanticModel]` for structured state (type safety)
- [ ] All Flow methods return `dict[str, Any]` for downstream listeners
- [ ] Listeners receive upstream data as method parameters
- [ ] Never use `self.inputs` for state management (deprecated)
- [ ] Use `@router` for conditional flow control
- [ ] State includes auto-generated `id` field (UUID)
- [ ] Error handling returns dict with error info
- [ ] Consider `@persist` for long-running or resumable flows

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

### CrewAI Compliance

- [ ] Follows standard crew structure
- [ ] Uses `@agent`, `@task`, `@crew` decorators
- [ ] Agent configs in `agents.yaml`
- [ ] Task configs in `tasks.yaml`
- [ ] Uses tool factories for tool assignment
- [ ] Uses `output_pydantic` with FinWiz schemas
- [ ] I/O-bound tasks have `async_execution: true`
- [ ] Final task has `async_execution: false`
- [ ] Final reporters have empty tools list
- [ ] Generates `RiskAssessmentStandardized` objects
- [ ] Proper task sequencing with `depends_on`
- [ ] Rate limiting configured (`max_rpm`)

## Common Patterns

### Tool Factory Usage

```python
# Get standardized tool set
tools = get_stock_crew_tools(
    include_rag=True,           # Include RAG tools
    include_quantitative=True,  # Include quantitative analysis
    collection_suffix="stock"   # RAG collection suffix
)
```

### Agent Validator Usage

```python
from finwiz.utils.agent_validators import final_reporter

@final_reporter  # Enforces empty tools list
@agent
def reporter(self) -> Agent:
    return Agent(
        config=self.agents_config['reporter'],
        tools=[],
        verbose=True
    )
```

### Context Passing

```python
# In task implementation
def analyze_stock(self, context):
    # Get data from previous tasks
    validation_result = context.get("validation_result")
    
    # Perform analysis
    analysis = self.perform_analysis(validation_result)
    
    # Return for next task
    return analysis
```

## Error Handling

### Graceful Degradation

```python
try:
    result = await crew.kickoff()
except Exception as e:
    logger.error(f"Crew execution failed: {e}")
    # Fall back to baseline analysis
    result = baseline_analysis()
```

### Retry Logic

```python
# Automatic retry with exponential backoff
max_retries = 3
retry_delay = 2  # seconds (doubles each retry)
```

## Performance Optimization

### Agent Reasoning (`reasoning=True`)

#### When to Enable

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

**Performance Cost:** 5-15 seconds, 1-3 LLM calls, 500-2000 tokens per reasoning cycle

### Crew Planning (`planning=True`)

#### Decision Rule

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

#### Configuration Examples

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

### Agent Delegation (`allow_delegation=True`)

**Enable for:**

- Coordinator/lead agents managing workflow
- Multi-agent workflows with dependencies
- Agents needing to ask questions

**Disable for:**

- Focused specialists (single responsibility)
- Final reporters (consolidation only)
- Single-purpose agents

**Performance Cost:** 5-15 seconds per delegation, 1-2 LLM calls

### Performance Decision Matrix

| Feature | Enable When | Disable When | Cost per Use |
|---------|-------------|--------------|--------------|
| `reasoning=True` | Complex multi-step, error recovery | Simple validation, high-volume | 5-15s, 1-3 calls |
| `planning=True` | 4+ agents, 6+ tasks, ≤3 runs | High-volume, single agent | Overhead × count |
| `allow_delegation=True` | Coordinators, multi-agent | Specialists, reporters | 5-15s per delegation |

## Best Practices

1. **Use Tool Factories**: Centralize tool initialization
2. **Validate Outputs**: Use `output_pydantic` with schemas
3. **Enable Async**: For I/O-bound tasks (except final)
4. **Empty Final Tools**: Final reporters have no tools
5. **Rate Limiting**: Configure `max_rpm` appropriately
6. **Context Management**: Use `respect_context_window`
7. **Error Handling**: Implement graceful degradation
8. **Logging**: Enable `verbose=True` for debugging
9. **Performance Optimization**: Consider execution volume when enabling features

## Flow State Management (CRITICAL)

### Mandatory Pattern: Structured State

Always use Pydantic models for type-safe Flow state:

```python
from pydantic import BaseModel, Field
from crewai.flow.flow import Flow, listen, start
from typing import Dict, List, Optional

class MyFlowState(BaseModel):
    """Type-safe state with validation."""
    holdings_processed: int = 0
    current_ticker: str = ""
    results: Dict[str, Any] = {}
    # Note: 'id' field is automatically added to all states

class MyFlow(Flow[MyFlowState]):
    @start()
    def initialize(self) -> dict[str, Any]:
        # Access auto-generated ID
        print(f"Flow ID: {self.state.id}")
        
        # Update structured state
        self.state.holdings_processed = 0
        
        # Return data for downstream listeners
        return {"status": "initialized"}
```

**Non-Negotiable Rules:**

- ✅ Use `Flow[PydanticModel]` for type safety and validation
- ✅ All Flow methods return `dict[str, Any]` for downstream listeners
- ✅ Access state via `self.state.field_name` (structured)
- ✅ State automatically includes `id` field (UUID)
- ❌ NEVER use `self.inputs` (unstructured, error-prone, deprecated pattern)

### Unstructured State (Not Recommended)

For simple flows, unstructured state is possible but discouraged:

```python
class UnstructuredFlow(Flow):
    @start()
    def first_method(self):
        # State is a dictionary
        print(f"State ID: {self.state['id']}")
        self.state['counter'] = 0
        self.state['message'] = "Hello"
```

**Use structured state for:**

- Complex flows with multiple fields
- Type safety and validation
- Better IDE support (autocomplete)
- Production code

### Data Flow Between Methods

**CRITICAL**: Return values from one method are passed as parameters to listening methods:

```python
@start()
def generate_data(self) -> dict[str, Any]:
    """Return data for downstream listeners."""
    data = {"ticker": "AAPL", "price": 150.0}
    
    # Update state
    self.state.current_ticker = "AAPL"
    
    # REQUIRED: Return for downstream methods
    return data

@listen(generate_data)
def process_data(self, data_from_previous_step: dict[str, Any]) -> dict[str, Any]:
    """Receive data from upstream as parameter."""
    ticker = data_from_previous_step["ticker"]
    price = data_from_previous_step["price"]
    
    # Update state
    self.state.last_processed = ticker
    
    # Process and return for next method
    processed = f"Processed {ticker} at ${price}"
    return {"processed": processed}

@listen(process_data)
def finalize_data(self, processed_data: dict[str, Any]):
    """Access both passed data and state."""
    result = processed_data["processed"]
    last_ticker = self.state.last_processed
    
    print(f"Result: {result}")
    print(f"Last processed ticker: {last_ticker}")
    
    return {"final": result}
```

**Key Points**:

- Return values are passed as method parameters
- State is updated separately via `self.state`
- Both mechanisms work together for data flow

### Conditional Routing

Use `@router` to direct flow based on state or conditions:

```python
from crewai.flow.flow import Flow, listen, router, start
from pydantic import BaseModel

class PaymentState(BaseModel):
    amount: float = 0.0
    is_approved: bool = False
    retry_count: int = 0

class PaymentFlow(Flow[PaymentState]):
    @start()
    def process_payment(self):
        # Simulate payment processing
        self.state.amount = 100.0
        self.state.is_approved = self.state.amount < 1000
        return "Payment processed"

    @router(process_payment)
    def check_approval(self, previous_result):
        """Return string to route to specific listener."""
        if self.state.is_approved:
            return "approved"
        elif self.state.retry_count < 3:
            return "retry"
        else:
            return "rejected"

    @listen("approved")
    def handle_approval(self):
        return f"Payment of ${self.state.amount} approved!"

    @listen("retry")
    def handle_retry(self):
        self.state.retry_count += 1
        print(f"Retrying payment (attempt {self.state.retry_count})...")
        return "Retry initiated"

    @listen("rejected")
    def handle_rejection(self):
        return f"Payment of ${self.state.amount} rejected after {self.state.retry_count} retries."
```

**Router Rules**:

- Router method returns a string that matches a listener name
- Multiple listeners can wait for different router outcomes
- Router enables conditional branching in flows

## Flow Persistence (Optional)

### Class-Level Persistence

Apply `@persist` decorator to save state after every method:

```python
from crewai.flow.flow import Flow, listen, start
from crewai.flow.persistence import persist
from pydantic import BaseModel

class CounterState(BaseModel):
    value: int = 0

@persist()  # Apply to entire flow class
class PersistentCounterFlow(Flow[CounterState]):
    @start()
    def increment(self):
        self.state.value += 1
        print(f"Incremented to {self.state.value}")
        return self.state.value

    @listen(increment)
    def double(self, value):
        self.state.value = value * 2
        print(f"Doubled to {self.state.value}")
        return self.state.value

# First run
flow1 = PersistentCounterFlow()
result1 = flow1.kickoff()

# Second run - state is automatically loaded
flow2 = PersistentCounterFlow()
result2 = flow2.kickoff()  # Continues from previous state
```

### Method-Level Persistence

Apply `@persist` to specific methods for granular control:

```python
class SelectivePersistFlow(Flow):
    @start()
    def first_step(self):
        self.state["count"] = 1
        return "First step"

    @persist()  # Only persist after this method
    @listen(first_step)
    def important_step(self, prev_result):
        self.state["count"] += 1
        self.state["important_data"] = "This will be persisted"
        return "Important step completed"

    @listen(important_step)
    def final_step(self, prev_result):
        self.state["count"] += 1
        return f"Complete with count {self.state['count']}"
```

**When to Use Persistence**:

- Long-running workflows that may be interrupted
- Human-in-the-loop scenarios requiring resumption
- Cyclic operations that build on previous runs
- Audit trails requiring state history

**Default Storage**: SQLite (can be configured)

## CrewAI Flow Integration (CRITICAL)

### Flow Architecture Compliance

**CRITICAL LESSON**: Always follow CrewAI Flow documentation patterns exactly. Mixing patterns leads to architectural inconsistencies.

### Proper Flow State Management

```python
# ✅ CORRECT - Structured Flow state with Pydantic
from pydantic import BaseModel
from crewai.flow import Flow

class FinwizState(BaseModel):
    portfolio_review: Optional[Dict[str, Any]] = None
    deep_analysis_results: Dict[str, DeepAnalysisResult] = {}
    deep_analysis_success: bool = False

class FinwizFlow(Flow[FinwizState]):
    # Flow methods use self.state (structured)
    def analyze_data(self):
        self.state.deep_analysis_success = True
        return {"results": "data"}

# ❌ WRONG - Unstructured dict state
class BadFlow(Flow):
    def analyze_data(self):
        self.inputs["some_key"] = "value"  # Unstructured, error-prone
```

### Proper Flow Method Signatures

```python
# ✅ CORRECT - Flow methods return data for downstream listeners
@listen("check_portfolio")
def analyze_holdings_deep(self) -> dict[str, Any]:
    # Process data
    results = {"analysis": analysis_data}
    
    # Update structured state
    self.state.deep_analysis_results = results
    
    # Return for downstream Flow methods
    return results

@listen("analyze_holdings_deep")
def match_alternatives(self, analysis_data: dict[str, Any]) -> dict[str, Any]:
    # Receive data from upstream Flow method as parameter
    holdings = analysis_data.get("analysis", {})
    
    # Process and return
    return {"alternatives": alternatives_data}

# ❌ WRONG - No return values, only state updates
@listen("check_portfolio")
def bad_analyze(self) -> None:  # Should return dict
    self.inputs["results"] = data  # Should use self.state
    # No return value for downstream methods
```

### Direct Crew Execution Pattern

```python
# ✅ CORRECT - Direct crew instantiation and execution
from finwiz.crews.stock_crew.stock_crew import StockCrew
from crewai.flow.flow import Flow, listen, start
from pydantic import BaseModel

class AnalysisState(BaseModel):
    ticker: str = ""
    analysis_result: dict = {}

class AnalysisFlow(Flow[AnalysisState]):
    @start()
    def initialize(self):
        self.state.ticker = "AAPL"
        return {"ticker": self.state.ticker}
    
    @listen(initialize)
    def analyze_stock(self, data):
        ticker = data["ticker"]
        
        # Direct crew instantiation (CrewAI Flow standard)
        crew = StockCrew()
        result = crew.crew().kickoff(inputs={"ticker": ticker})
        
        # Update state
        self.state.analysis_result = result.raw
        
        # Return for downstream methods
        return {"result": result.raw}

# ❌ WRONG - Using crew_factory (mixed patterns)
def bad_analyze_stock(self, ticker: str):
    result_data = self.crew_factory.execute_stock_crew(inputs)  # Inconsistent
    return result_data
```

### Integrating Crews into Flows

Complete example of crew integration:

```python
from crewai.flow.flow import Flow, listen, start
from pydantic import BaseModel
from random import randint
from .crews.poem_crew.poem_crew import PoemCrew

class PoemState(BaseModel):
    sentence_count: int = 1
    poem: str = ""

class PoemFlow(Flow[PoemState]):
    @start()
    def generate_sentence_count(self):
        print("Generating sentence count")
        self.state.sentence_count = randint(1, 5)
        return {"count": self.state.sentence_count}

    @listen(generate_sentence_count)
    def generate_poem(self, data):
        print("Generating poem")
        count = data["count"]
        
        # Execute crew with inputs
        result = PoemCrew().crew().kickoff(
            inputs={"sentence_count": count}
        )
        
        # Store in state
        self.state.poem = result.raw
        
        return {"poem": result.raw}

    @listen(generate_poem)
    def save_poem(self, data):
        print("Saving poem")
        with open("poem.txt", "w") as f:
            f.write(data["poem"])
        
        return {"saved": True}

# Execute flow
poem_flow = PoemFlow()
poem_flow.kickoff()
```

### Flow State Access After Execution

```python
# ✅ CORRECT - Access structured state after Flow execution
flow = FinwizFlow()
result = flow.kickoff()

# Access final state with type safety
final_state = flow.state
for ticker, analysis in final_state.deep_analysis_results.items():
    print(f"{ticker}: {analysis.grade}")

# ❌ WRONG - Accessing unstructured inputs
bad_results = flow.inputs.get("deep_analysis_results", {})  # Error-prone
```

### Flow Integration Checklist

When integrating with CrewAI Flow:

- [ ] **Structured State**: Use `Flow[StateModel]` with Pydantic models
- [ ] **Method Signatures**: Flow methods return `dict[str, Any]` for downstream listeners
- [ ] **Parameter Passing**: Listeners receive upstream data as method parameters
- [ ] **State Updates**: Use `self.state` (structured) not `self.inputs` (unstructured)
- [ ] **Crew Execution**: Direct instantiation with `crew.kickoff()`, not factory patterns
- [ ] **Data Flow**: Return values from Flow methods, not just state updates
- [ ] **Type Safety**: Pydantic validation for all Flow state fields
- [ ] **Documentation Compliance**: Follow exact CrewAI Flow documentation patterns

### Common Flow Integration Mistakes

❌ **State Management**:

- Using `self.inputs` dict instead of structured `self.state`
- Missing return values from Flow methods
- Not receiving parameters in listener methods

❌ **Crew Execution**:

- Using `crew_factory` instead of direct crew instantiation
- Mixing execution patterns within the same codebase

❌ **Data Passing**:

- Only updating state without returning data
- Not following listener parameter patterns
- Inconsistent data flow between methods

❌ **Type Safety**:

- Using unstructured dicts instead of Pydantic models
- Missing type annotations for Flow state fields
- No validation for Flow state updates

### Flow Architecture Benefits

✅ **Type Safety**: Pydantic models prevent data corruption and runtime errors
✅ **Data Integrity**: Structured state ensures consistent data access patterns
✅ **Framework Compliance**: Follows official CrewAI Flow documentation patterns
✅ **Maintainability**: Clear data flow and type definitions improve code clarity
✅ **Debugging**: Structured state makes debugging easier with visualization tools
✅ **IDE Support**: Type hints enable better autocomplete and error detection
✅ **Validation**: Pydantic validates state updates automatically
✅ **Persistence**: Easy to save/restore flow state with `@persist` decorator
✅ **Resumability**: Flows can be interrupted and resumed from last checkpoint

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

## Anti-Patterns (Avoid)

❌ **Using `self.inputs` instead of `self.state`**
❌ **Flow methods not returning `dict[str, Any]`**
❌ **Enabling reasoning for high-volume executions**
❌ **Enabling planning for single-agent crews**
❌ **Final reporters with non-empty tools**
❌ **Missing `max_reasoning_attempts` when reasoning enabled**
❌ **Delegation enabled for specialist agents**
❌ **Hardcoded tool lists** - Use tool factories instead
❌ **Tools in final reporter** - Must be empty
❌ **Async final task** - Must be synchronous
❌ **Missing output_pydantic** - Always use schemas
❌ **No rate limiting** - Always configure max_rpm
❌ **Circular dependencies** - Check task sequencing
❌ **Missing validation** - Always validate outputs
❌ **Unstructured Flow state** - Use Pydantic models with `Flow[StateModel]`
❌ **Missing Flow method return values** - Always return data for downstream listeners
❌ **Mixed crew execution patterns** - Use direct instantiation consistently
❌ **Ignoring CrewAI Flow documentation** - Follow patterns exactly

---

**Version**: 4.0  
**Last Updated**: 2025-10-26  
**Consolidated from**: crewai-best-practices.md, agents.md  
**Major Update**: Comprehensive consolidation of CrewAI standards, performance optimization, and Flow patterns
