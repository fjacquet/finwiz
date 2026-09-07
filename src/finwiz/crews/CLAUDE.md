# Crews Module

This directory contains FinWiz's CrewAI agent crews — specialized teams of AI
agents that perform qualitative financial analysis. `deep_analysis` is
currently the only crew that runs in production; see `../../CLAUDE.md`'s
"Crew Pattern" section for why the six per-asset-class crews that used to
live here (`stock_crew`, `etf_crew`, `crypto_crew`,
`investment_discovery_crew`, `portfolio_rebalancing_crew`, `report_crew`)
were deleted, along with `CrewFactory`.

## Directory Structure

```
crews/
├── deep_analysis/         # Per-holding deep analysis crew (the only crew that runs)
│   ├── config/
│   ├── deep_analysis.py   # Main deep analysis crew
│   ├── performance_validation.py  # Performance validation logic
│   └── tool_routing.py    # Dynamic tool selection
└── helpers/               # Shared crew utilities
    ├── context_preparation.py    # Context building helpers
    ├── data_extraction_helpers.py
    ├── data_integration_helpers.py
    ├── llm_config.py      # LLM configuration utilities
    ├── performance_validation.py
    └── tool_routing.py
```

## Major Entry Points

### Core Crew Class

| File | Class/Function | Purpose |
|------|---------------|---------|
| `deep_analysis/deep_analysis.py` | `DeepAnalysisCrew` | Per-holding comprehensive analysis |

### Helper Functions

| File | Function | Purpose |
|------|----------|---------|
| `helpers/context_preparation.py` | `prepare_crew_context()` | Build context for crew execution |
| `helpers/llm_config.py` | `get_crew_llm()` | Build the `LLM` instance for crew agents |
| `helpers/llm_config.py` | `get_crew_model_string()` | Model identifier as a string |
| `helpers/tool_routing.py` | `get_tools_for_asset_class()` | Dynamic tool selection by asset class |
| `helpers/tool_routing.py` | `get_minimal_risk_tools()` | Reduced tool set for risk-only work |

## Adding a new crew

Use the `/new-crew` skill (`.claude/skills/new-crew/SKILL.md`) to scaffold a
new crew — it generates `crews/<name>/{crew.py, config/agents.yaml,
config/tasks.yaml}` with the correct `@CrewBase`/`@agent`/`@task` decorators,
tool-factory wiring, and an output Pydantic schema, following the same
pattern `deep_analysis` uses.

## Critical Rules

1. **Tool Factories**: Use `get_*_crew_tools()` functions from `finwiz.tools.tool_factories`, never hardcode tools
2. **YAML Configs**: Agent and task configs must be in `config/` directory
3. **Async Execution**: Only final task should be synchronous
4. **Reasoning**: Enable for complex analysis, disable for high-volume runs

## Testing

```bash
# Test the deep_analysis crew
uv run pytest tests/unit/crews/test_deep_analysis_crew.py -v

# Test all crews
uv run pytest tests/unit/crews/ -v
```

## Related Modules

- `finwiz.tools.tool_factories` - Tool initialization
- `finwiz.schemas.crew_exports` - Pydantic export schemas
- `finwiz.infrastructure.decorators.agent_validators` - Decorators for agents
- `finwiz.infrastructure.decorators.task_decorators` - Decorators for tasks
