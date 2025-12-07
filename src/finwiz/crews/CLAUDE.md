# Crews Module

This directory contains all CrewAI agent crews for the FinWiz platform. Each crew is a specialized team of AI agents that performs specific financial analysis tasks.

## Directory Structure

```
crews/
├── crypto_crew/           # Cryptocurrency analysis crew
│   ├── config/
│   │   ├── agents.yaml    # Agent configurations
│   │   └── tasks.yaml     # Task definitions
│   └── crypto_crew.py     # Crew implementation
├── deep_analysis/         # Per-holding deep analysis crew
│   ├── config/
│   ├── deep_analysis.py   # Main deep analysis crew
│   ├── performance_validation.py  # Performance validation logic
│   └── tool_routing.py    # Dynamic tool selection
├── etf_crew/              # ETF analysis crew
│   ├── config/
│   └── etf_crew.py
├── helpers/               # Shared crew utilities
│   ├── context_preparation.py    # Context building helpers
│   ├── data_extraction_helpers.py
│   ├── data_integration_helpers.py
│   ├── llm_config.py      # LLM configuration utilities
│   ├── performance_validation.py
│   └── tool_routing.py
├── investment_discovery_crew/  # A+ investment discovery
│   ├── config/
│   └── investment_discovery_crew.py
├── portfolio_rebalancing_crew/  # Portfolio optimization
│   ├── config/
│   └── portfolio_rebalancing_crew.py
├── report_crew/           # Final report generation (NO tools)
│   ├── config/
│   ├── agents.py          # Agent definitions
│   ├── report_crew.py     # Crew implementation
│   └── tasks.py           # Task definitions
└── stock_crew/            # Stock analysis crew
    ├── config/
    └── stock_crew.py
```

## Major Entry Points

### Core Crew Classes

| File | Class/Function | Purpose |
|------|---------------|---------|
| `stock_crew/stock_crew.py` | `StockCrew` | Stock analysis with 10-K insights, technical analysis |
| `etf_crew/etf_crew.py` | `EtfCrew` | ETF analysis with factsheet, holdings analysis |
| `crypto_crew/crypto_crew.py` | `CryptoCrew` | Cryptocurrency analysis with on-chain metrics |
| `deep_analysis/deep_analysis.py` | `DeepAnalysisCrew` | Per-holding comprehensive analysis |
| `investment_discovery_crew/investment_discovery_crew.py` | `InvestmentDiscoveryCrew` | A+ opportunity discovery |
| `portfolio_rebalancing_crew/portfolio_rebalancing_crew.py` | `PortfolioRebalancingCrew` | Portfolio optimization and rebalancing |
| `report_crew/report_crew.py` | `ReportCrew` | Final consolidated report generation |

### Helper Functions

| File | Function | Purpose |
|------|----------|---------|
| `helpers/context_preparation.py` | `prepare_crew_context()` | Build context for crew execution |
| `helpers/llm_config.py` | `get_llm_config()` | Get LLM configuration for agents |
| `helpers/tool_routing.py` | `route_tools_for_asset()` | Dynamic tool selection by asset class |

## Crew Structure Pattern

Every crew follows this exact pattern:

```python
from crewai import Agent, Crew, Task, agent, crew, task
from finwiz.tools.tool_factories import get_stock_crew_tools
from finwiz.utils.agent_validators import final_reporter

@CrewBase
class StockCrew:
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["analyst"],
            tools=get_stock_crew_tools(),
            reasoning=True,
            max_reasoning_attempts=3,
            verbose=True
        )

    @final_reporter  # Enforces NO tools
    @agent
    def reporter(self) -> Agent:
        return Agent(
            config=self.agents_config["reporter"],
            tools=[],  # MUST be empty
            verbose=True
        )

    @task
    def analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config["analysis"],
            agent=self.analyst()
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )
```

## Critical Rules

1. **Final Reporters**: Must have empty tools list and use `@final_reporter` decorator
2. **Tool Factories**: Use `get_*_crew_tools()` functions, never hardcode tools
3. **YAML Configs**: Agent and task configs must be in `config/` directory
4. **Async Execution**: Only final task should be synchronous
5. **Reasoning**: Enable for complex analysis, disable for high-volume (66+ runs)

## Config File Templates

### agents.yaml
```yaml
analyst:
  role: Financial Analyst
  goal: Perform comprehensive analysis of {ticker}
  backstory: >
    Expert financial analyst with deep expertise in {asset_class} analysis.
  verbose: true
  allow_delegation: false
```

### tasks.yaml
```yaml
analysis_task:
  description: >
    Analyze {ticker} with quantitative metrics

    🚨 JSON OUTPUT REQUIREMENTS 🚨
    - Output MUST be ONLY valid JSON
    - NO trailing commas in JSON
  expected_output: "Structured analysis with risk assessment"
  output_pydantic: "TenKInsight"
  output_json: true
  agent: analyst
  async_execution: true
```

## Testing

```bash
# Test specific crew
uv run pytest tests/unit/crews/test_stock_crew.py -v

# Test all crews
uv run pytest tests/unit/crews/ -v
```

## Related Modules

- `finwiz.tools.tool_factories` - Tool initialization
- `finwiz.schemas.crew_exports` - Pydantic export schemas
- `finwiz.utils.agent_validators` - Decorators for agents
- `finwiz.utils.task_decorators` - Decorators for tasks
