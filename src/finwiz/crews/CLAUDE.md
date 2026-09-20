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
    ├── llm_config.py      # LLM configuration utilities
    ├── performance_validation.py
    └── tool_routing.py
```

`context_preparation.py`, `data_extraction_helpers.py`, and `data_integration_helpers.py`
were deleted — their only consumer, `report_crew/report_crew.py`, was deleted along with
the rest of the crew subsystem (see `../../CLAUDE.md`). `llm_config.py` stays live
(`get_crew_model_string()` backs `infrastructure/resilience/crew_execution.py`'s cost
tracker); `tool_routing.py` and `performance_validation.py` here are stale duplicates of
`deep_analysis/tool_routing.py` / `deep_analysis/performance_validation.py` — dead since
before the crew subsystem was removed, tracked separately on issue #194.

## Major Entry Points

### Core Crew Class

| File | Class/Function | Purpose |
|------|---------------|---------|
| `deep_analysis/deep_analysis.py` | `DeepAnalysisCrew` | Per-holding comprehensive analysis |

### Helper Functions

| File | Function | Purpose |
|------|----------|---------|
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

## Prompt layout: static prefix first

`deep_analysis/config/agents.yaml` and `tasks.yaml` are ordered for
OpenRouter's implicit Gemini prompt cache, which serves a cache read (10× cheaper
input) when two requests share a prefix longer than ~1 024 tokens. CrewAI renders
the agent `goal` into the system prompt and the task `description` into the user
turn, so:

- the `goal` must contain no `{placeholder}`;
- every static rule (language, anti-hallucination, no-tools, the five sections,
  Python-controlled fields, required structure, output rules) comes first in the
  `description`, then a `---` line, then the per-holding data (date, holding,
  `{fact_pack_block}`, CONTEXT, `{retry_guidance}`).

`tests/unit/crews/test_deep_analysis_prompt_layout.py` pins this: the first `{`
in the description must sit after 3 000 characters of static text. When editing
the prompt, add rules to the top block and data to the bottom block. Holdings run
in parallel, so the first wave of a run misses the cache; the gain is cents per
run, and the layout costs nothing to keep.

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
- `finwiz.infrastructure.decorators.task_decorators` - Decorators for tasks
