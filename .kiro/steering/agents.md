---
inclusion: always
---

# CrewAI Agent Configuration Standards

Guidelines for configuring CrewAI agents in FinWiz crews.

## Agent Configuration Patterns

### Standard Agent Definition

```python
from crewai import Agent, agent
from finwiz.tools.tool_factories import get_stock_crew_tools

@agent
def analyst(self) -> Agent:
    return Agent(
        config=self.agents_config["analyst"],
        tools=get_stock_crew_tools(include_rag=True),
        reasoning=True,  # Enable for complex analysis
        max_reasoning_attempts=3,  # Prevent infinite loops
        allow_delegation=True,  # Enable for coordinators
        verbose=True
    )
```

### Agent Configuration File (agents.yaml)

```yaml
analyst:
  role: "Financial Analyst"
  goal: "Analyze assets and provide investment recommendations"
  backstory: "Expert analyst with deep market knowledge"
```

## When to Enable Agent Features

### Reasoning (`reasoning=True`)

**✅ Enable for:**
- Complex multi-step analysis (deep portfolio analysis)
- Error-prone operations requiring planning
- Tasks using multiple tools
- Recovery scenarios after failures

**❌ Disable for:**
- Simple validation (ticker format checks)
- Direct API calls (single-step fetches)
- Final reporters (consolidation only)
- Time-sensitive operations

**Configuration:**
```python
analyst = Agent(
    reasoning=True,
    max_reasoning_attempts=3  # Prevent loops
)
```

### Delegation (`allow_delegation=True`)

**✅ Enable for:**
- Coordinator/lead agents
- Agents needing to ask questions
- Multi-agent workflows with dependencies

**❌ Disable for:**
- Focused specialists
- Final reporters
- Simple single-purpose agents

### Memory (`memory=True`)

**✅ Enable for:**
- Agents learning from past executions
- Iterative improvement scenarios
- Long-running analysis sessions

**❌ Disable for:**
- Stateless operations
- One-time analyses
- High-volume executions (memory overhead)

## Tool Assignment by Agent Role

### Analysis Agents (Stock/ETF/Crypto)

**Required Tools:**
```python
tools = get_{asset_class}_crew_tools(
    include_rag=True,
    include_quantitative=True,
    collection_suffix="{asset_class}"
)
```

**Key Tools:**
- `QuantitativeAnalysisTool(asset_class="{type}")`
- `TickerValidationTool` (always validate first)
- `StandardizedSentimentTool`
- Asset-specific tools (`EnhancedSECAnalysisTool`, `EnhancedETFAnalysisTool`, etc.)
- RAG tools for knowledge retrieval

**Configuration:**
```python
analyst = Agent(
    reasoning=True,  # Complex analysis
    allow_delegation=True,  # Can ask specialists
    max_reasoning_attempts=3
)
```

### Specialist Agents (Risk, Technical, Sentiment)

**Tool Assignment:**
- Focused tool subset for specialty
- No delegation (focused execution)
- Reasoning enabled for complex calculations

**Example:**
```python
risk_assessor = Agent(
    tools=[risk_analysis_tool, data_validation_tool],
    reasoning=True,
    allow_delegation=False  # Focused specialist
)
```

### Final Reporter Agents

**CRITICAL RULES:**
- **Empty tools list** (`tools=[]`)
- **No delegation** (`allow_delegation=False`)
- **No reasoning** (consolidation only)
- Consume upstream context via task dependencies

**Enforced Pattern:**
```python
from finwiz.utils.agent_validators import final_reporter

@final_reporter  # Enforces empty tools
@agent
def reporter(self) -> Agent:
    return Agent(
        config=self.agents_config['reporter'],
        tools=[],  # MUST be empty
        allow_delegation=False,
        verbose=True
    )
```

## Agent Backstory Guidelines

### Purpose of Backstories

Backstories guide agent behavior and decision-making. Write clear, specific backstories that:

- Define expertise and knowledge domain
- Set expectations for output quality
- Establish collaboration patterns
- Clarify decision-making authority

### Backstory Patterns

**Analysis Agents:**
```yaml
backstory: >
  Expert financial analyst with 15+ years experience in {asset_class} markets.
  Specializes in fundamental analysis, risk assessment, and quantitative metrics.
  Known for thorough research and data-driven recommendations.
```

**Specialist Agents:**
```yaml
backstory: >
  Technical analysis specialist focusing on {specialty}.
  Uses multiple indicators and timeframes for comprehensive analysis.
  Provides actionable insights with clear confidence levels.
```

**Final Reporters:**
```yaml
backstory: >
  Senior investment advisor who synthesizes complex analysis into clear,
  actionable recommendations. Focuses on consolidating findings from
  research teams without conducting additional research.
```

### Collaboration Guidance in Backstories

When `allow_delegation=True`, include collaboration guidance:

```yaml
backstory: >
  Lead analyst coordinating with specialists. Delegates technical analysis
  to technical_analyst and risk assessment to risk_assessor when needed.
  Synthesizes inputs into comprehensive investment recommendations.
```

## Task Description Guidelines for Agents

### Reasoning-Compatible Descriptions

When `reasoning=True`, task descriptions must be explicit:

```yaml
analysis_task:
  description: >
    Perform comprehensive analysis of the provided {asset_class} ticker: {ticker}
    
    SINGLE TICKER MODE: You are analyzing ONE specific {asset_class}, not screening.
    The ticker {ticker} is provided as input. Do NOT request additional tickers.
    
    Analysis Steps:
    1. Validate {ticker} using TickerValidationTool
    2. Fetch {asset_class}-specific data for {ticker}
    3. Calculate quantitative metrics for {ticker}
    4. Generate risk assessment for {ticker}
    5. Provide investment recommendation for {ticker}
    
    Focus on data validation, error handling, and comprehensive analysis.
```

**Key Elements:**
- Explicit mode declaration (SINGLE TICKER vs SCREENING)
- Repeat input variables throughout (`{ticker}`, `{asset_class}`)
- Clear step-by-step instructions
- Specific tool mentions
- Error handling guidance

### Multi-Agent Task Descriptions

When `allow_delegation=True`, clarify collaboration:

```yaml
coordination_task:
  description: >
    Lead comprehensive analysis of {ticker} by coordinating with specialists.
    
    Delegation Strategy:
    - Delegate technical analysis to technical_analyst
    - Delegate risk assessment to risk_assessor
    - Synthesize findings into final recommendation
    
    Do NOT perform specialist work yourself. Focus on coordination and synthesis.
```

## Agent Performance Optimization

### Async Execution

Enable for I/O-bound tasks (except final task):

```yaml
analysis_task:
  agent: analyst
  async_execution: true  # Parallel execution
```

**Rules:**
- ✅ Enable for data fetching, API calls
- ❌ Disable for final task (CrewAI requirement)
- ❌ Disable for tasks with strict ordering

### Rate Limiting

Configure at crew level to prevent API throttling:

```python
@crew
def crew(self) -> Crew:
    return Crew(
        agents=self.agents,
        tasks=self.tasks,
        max_rpm=20  # 20 requests per minute
    )
```

### Context Window Management

```python
@crew
def crew(self) -> Crew:
    return Crew(
        agents=self.agents,
        tasks=self.tasks,
        respect_context_window=True  # Automatic context management
    )
```

## Agent Configuration Checklist

When creating or modifying agents:

- [ ] Agent defined with `@agent` decorator
- [ ] Configuration loaded from `agents.yaml`
- [ ] Tools assigned via factory functions
- [ ] `reasoning=True` for complex tasks only
- [ ] `max_reasoning_attempts=3` when reasoning enabled
- [ ] `allow_delegation` set appropriately
- [ ] `verbose=True` for debugging
- [ ] Final reporters have empty tools (enforced by `@final_reporter`)
- [ ] Backstory provides clear guidance
- [ ] Task descriptions are reasoning-compatible
- [ ] Async execution enabled for I/O tasks
- [ ] Rate limiting configured at crew level

## Common Agent Patterns

### Single-Purpose Analyst

```python
@agent
def validator(self) -> Agent:
    return Agent(
        config=self.agents_config["validator"],
        tools=[TickerValidationTool()],
        reasoning=False,  # Simple validation
        allow_delegation=False,
        verbose=True
    )
```

### Multi-Tool Coordinator

```python
@agent
def lead_analyst(self) -> Agent:
    return Agent(
        config=self.agents_config["lead_analyst"],
        tools=get_stock_crew_tools(include_rag=True),
        reasoning=True,
        max_reasoning_attempts=3,
        allow_delegation=True,  # Can delegate to specialists
        verbose=True
    )
```

### Final Reporter

```python
from finwiz.utils.agent_validators import final_reporter

@final_reporter
@agent
def reporter(self) -> Agent:
    return Agent(
        config=self.agents_config["reporter"],
        tools=[],  # Enforced empty
        allow_delegation=False,
        verbose=True
    )
```

---

**Version**: 3.0  
**Last Updated**: 2025-01-11  
**Focus**: Agent configuration, reasoning, delegation, and task descriptions
