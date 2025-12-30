# FinWiz Architecture Overview

## Directory Structure
```
src/finwiz/
├── crews/           # CrewAI agent crews (stock, etf, crypto, etc.)
├── flows/           # CrewAI Flow orchestration
├── data/            # Data acquisition layer
├── orchestrators/   # Business logic coordination
├── quantitative/    # Quant analysis (Backtrader, TA-Lib, QuantLib)
├── integration/     # Data integration and validation
├── tools/           # Custom financial tools and factories
├── schemas/         # Pydantic data models (ALL models here)
├── scoring/         # Deterministic Python scoring
├── reporting/       # Report generation
├── templates/       # Jinja2 templates
├── utils/           # Utilities (decorators, logging)
└── validation/      # Validation infrastructure
```

## Core Design Principles
1. **AI Minimalism**: Python for deterministic, AI for reasoning
2. **Pydantic-First**: All outputs validated with strict schemas
3. **File-Based Data Passing**: Pass file paths between crews
4. **Concurrent Execution**: SME crews run in parallel

## Flow Architecture
Uses CrewAI Flow with Pydantic state:
- All Flow methods return `dict[str, Any]`
- Access state via `self.state.field_name`
- NEVER use `self.inputs` (deprecated)

## Crew Structure
Each crew follows:
```
crews/{crew_name}/
├── {crew_name}.py      # @agent, @task, @crew decorators
└── config/
    ├── agents.yaml     # Agent configurations
    └── tasks.yaml      # Task definitions
```

## Key Patterns
- **Tool Factories**: `get_stock_crew_tools()`, `get_etf_crew_tools()`
- **Final Reporter**: Must have empty tools, use `@final_reporter` decorator
- **Python Scoring**: `DeepAnalysisScorer` for deterministic calculations
- **HTML Reports**: Jinja2 templates (NO AI)
