---
name: new-crew
description: "Scaffold a new CrewAI crew following FinWiz conventions. Creates crews/<name>/{crew.py, config/agents.yaml, config/tasks.yaml} with correct @CrewBase/@agent/@task decorators, tool-factory wiring, and an output Pydantic schema. Use when adding a new crew (e.g., /new-crew sector_rotation)."
---

# Scaffold a New FinWiz Crew

Apply when the user invokes `/new-crew <name>` or asks to "add a new crew called X".

## Inputs

- `<name>` — snake_case crew name (e.g., `sector_rotation`, `dividend_screener`)

If the user did not provide a name, ask once, then proceed.

## What to Create

Follow the project's canonical layout exactly (see `src/finwiz/crews/deep_analysis/` as reference — the only crew currently in the codebase):

```
src/finwiz/crews/<name>/
├── __init__.py
├── <name>.py               # @CrewBase class with @agent/@task/@crew
└── config/
    ├── agents.yaml         # Agent roles, goals, backstories
    └── tasks.yaml          # Task descriptions + expected_output
```

Also add:

- `src/finwiz/schemas/<name>_output.py` — Pydantic model for `output_pydantic`
- `src/finwiz/tools/tool_factories.py` — append `get_<name>_crew_tools()` if the crew needs tools

## Hard Rules (project CLAUDE.md)

1. **Final reporter agents** must have `tools=[]` and the `@final_reporter` decorator from
   `finwiz.infrastructure.decorators.agent_validators`. (The old `finwiz.utils.agent_validators`
   path in earlier copies of this skill never existed.) Note that #187 deleted `report_crew`,
   the decorator's only user, so it currently enforces nothing — it is kept as the guardrail
   for the next reporter crew, not as a description of existing code.
2. **Tool instantiation** — never instantiate tools directly; call the factory from `tools/tool_factories.py`.
3. **Pydantic models** live in `schemas/`, never in the crew directory.
4. **Tasks** declare `output_pydantic=<YourSchema>` (not raw dicts).
5. **AI Minimalism** — if the crew's job is deterministic (scoring, aggregation, file IO), push back and suggest a Python module under `analysis/`, `scoring/`, or `orchestrators/` instead.

## Scaffold Steps

1. Read the reference crew: `src/finwiz/crews/deep_analysis/deep_analysis.py` and its YAML configs.
2. Copy the structure into the new path, rename classes/agents/tasks.
3. Create the output schema in `schemas/`. Export it from `schemas/__init__.py`.
4. Wire a tool factory in `tools/tool_factories.py` if tools are needed.
5. Do **not** wire it into `flows/orchestrator.py` (directly or via an orchestrator) until the user confirms which phase it belongs in and who calls it — that's a deliberate architectural decision. A crew that's constructed but never invoked is dead weight (see `CLAUDE.md`'s "Crew Pattern" section on why `CrewFactory` and the six crews it wired up were deleted).

## Verification Checklist

- [ ] `uv run python -c "from finwiz.crews.<name>.<name> import <Name>Crew; print(<Name>Crew)"` imports cleanly
- [ ] YAML files parse (`python -c "import yaml; yaml.safe_load(open('src/finwiz/crews/<name>/config/agents.yaml'))"`)
- [ ] Output schema validates (`uv run python -c "from finwiz.schemas.<name>_output import <Name>Output; print(<Name>Output.model_json_schema())"`)
- [ ] `make lint` clean
- [ ] A minimal smoke test at `tests/unit/crews/test_<name>.py` — instantiate the crew, assert agent/task counts

## Anti-patterns to refuse

- Creating a crew whose only job is scoring or aggregation → propose a Python module in `scoring/` instead (AI Minimalism).
- Adding new tools inline in the crew file → must go through `tool_factories.py`.
- Constructing the crew somewhere but never calling its `.kickoff()`/execution path → that's exactly the dead-weight pattern that got `CrewFactory` and six crews deleted; wire the new crew into an actual caller (an orchestrator or `analysis/_helpers.py`-style entry point) in the same change, not "later."
