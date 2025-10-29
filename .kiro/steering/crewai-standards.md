---
inclusion: always
---

# CrewAI Development Standards for FinWiz

Standards for developing CrewAI crews, agents, tasks, and Flows in FinWiz, including performance optimization, state management, and architectural patterns.

## Crew Structure (Required)

All crews must follow this exact structure:

```
src/finwiz/crews/{crew_name}/
├── {crew_name}.py          # @agent, @task, @crew decorators
└── config/
    ├── agents.yaml         # Agent configurations  
    └── tasks.yaml          # Task definitions
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
        verbose=True
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

- **Enable** (`reasoning=True`) for: Financial analysis, multi-step workflows
- **Disable** (`reasoning=False`) for: Simple validators, final reporters
- **Always** set `max_reasoning_attempts=3` when reasoning is enabled

#### Delegation

- **Enable** (`allow_delegation=True`) for: Lead/coordinator agents only
- **Disable** (`allow_delegation=False`) for: Specialists, final reporters

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
  depends_on:
    - ticker_validation_task      # Ensure proper sequencing
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

def analyze_stock(self, ticker: str):
    crew = StockCrew()
    result = crew.crew().kickoff(inputs={"ticker": ticker})
    return result

# ❌ WRONG - Using crew_factory (mixed patterns)
def bad_analyze_stock(self, ticker: str):
    result_data = self.crew_factory.execute_stock_crew(inputs)  # Inconsistent
    return result_data
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

✅ **Type Safety**: Pydantic models prevent data corruption
✅ **Data Integrity**: Structured state ensures consistent data access
✅ **Framework Compliance**: Follows CrewAI Flow best practices
✅ **Maintainability**: Clear data flow and type definitions
✅ **Debugging**: Structured state makes debugging easier
✅ **IDE Support**: Type hints enable better autocomplete and error detection

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
