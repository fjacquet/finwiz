# CrewAI Development Standards for FinWiz

Standards for developing CrewAI crews, agents, and tasks in FinWiz.

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

### Standard Pattern

```python
from crewai import Agent, agent
from finwiz.tools.tool_factories import get_stock_crew_tools

@agent
def stock_analyst(self) -> Agent:
    return Agent(
        config=self.agents_config["stock_analyst"],
        tools=get_stock_crew_tools(
            include_rag=True,
            include_quantitative=True,
            collection_suffix="stock"
        ),
        verbose=True
    )
```

### Configuration File (agents.yaml)

```yaml
stock_analyst:
  role: "Stock Analyst"
  goal: "Analyze stock fundamentals and provide investment recommendations"
  backstory: "Expert financial analyst with deep knowledge of equity markets"
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

## CrewAI Compliance Checklist

When creating or modifying crews:

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

## Best Practices

1. **Use Tool Factories**: Centralize tool initialization
2. **Validate Outputs**: Use `output_pydantic` with schemas
3. **Enable Async**: For I/O-bound tasks (except final)
4. **Empty Final Tools**: Final reporters have no tools
5. **Rate Limiting**: Configure `max_rpm` appropriately
6. **Context Management**: Use `respect_context_window`
7. **Error Handling**: Implement graceful degradation
8. **Logging**: Enable `verbose=True` for debugging

## Anti-Patterns (Avoid)

❌ **Hardcoded tool lists** - Use tool factories instead
❌ **Tools in final reporter** - Must be empty
❌ **Async final task** - Must be synchronous
❌ **Missing output_pydantic** - Always use schemas
❌ **No rate limiting** - Always configure max_rpm
❌ **Circular dependencies** - Check task sequencing
❌ **Missing validation** - Always validate outputs

---

**Version**: 2.0  
**Last Updated**: 2025-03-10
