# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Quick Reference

```bash
# Essential commands
crewai flow kickoff                    # Run full portfolio analysis
uv sync                                # Install dependencies
make test                              # Unit tests only (< 3 minutes)
make check                             # All quality checks (lint + test + docs)

# Single test
uv run pytest tests/path/test.py -v              # Single file
uv run pytest tests/path/test.py::test_name -v -s  # Single test with output

# Code quality
make lint && make format               # Fix linting and formatting
make mypy                              # Type checking
make check-unittest-mock               # Verify no unittest.mock usage

# Documentation
make docs-serve                        # Preview docs locally

# HTML Reports
make html-reports                      # Generate all HTML reports
```

## Project Overview

FinWiz is an AI-powered financial analysis platform built with CrewAI. It uses autonomous AI agents to analyze stocks, ETFs, cryptocurrencies, and portfolios.

**Key Capabilities:**

- Multi-asset financial analysis (stocks, ETFs, crypto)
- Portfolio review with keep/sell recommendations
- Portfolio rebalancing with optimization
- A+ investment discovery across markets
- Quantitative analysis (Backtrader, TA-Lib, QuantLib)
- Python-based scoring engine (100% cost reduction vs AI)

## Architecture

### Core Principles

1. **AI Minimalism**: Python for deterministic tasks, AI only for reasoning
2. **Pydantic-First**: All outputs validated with strict schemas
3. **File-Based Data Passing**: Pass file paths between crews (not data)
4. **Concurrent Execution**: SME crews run in parallel
5. **Clean Separation**: Analysis (AI) vs presentation (Python templates)
6. **Layered Architecture**: Organize by layer and concern

### Layered Architecture

| Layer           | Directory                      | Responsibility                  |
| --------------- | ------------------------------ | ------------------------------- |
| **Domain**      | `schemas/`, `scoring/`         | Business logic, Pydantic models |
| **Application** | `orchestrators/`, `flows/`     | Workflow orchestration          |
| **Infrastructure** | `data/`, `supabase/`, `cache/` | External APIs, databases     |
| **Presentation** | `api/`, `reporting/`, `templates/` | HTTP, HTML, CLI            |

**Dependency Direction**: `Presentation → Application → Domain ← Infrastructure`

### Key Entry Points

| Purpose | Location |
|---------|----------|
| Main application | `src/finwiz/main.py` |
| Flow orchestration | `src/finwiz/flows/hybrid_analysis_flow.py` |
| Crew factory | `src/finwiz/crew_factory.py` |
| Tool factories | `src/finwiz/tools/tool_factories.py` |
| Schemas | `src/finwiz/schemas/` |
| Scoring engine | `src/finwiz/scoring/deep_analysis_scorer.py` |

**Note**: Each major directory has its own `CLAUDE.md` with detailed patterns. Claude automatically fetches relevant ones when working in subfolders.

## CrewAI Patterns

### Crew Structure

```
crews/{crew_name}/
├── {crew_name}.py          # @agent, @task, @crew decorators
└── config/
    ├── agents.yaml         # Agent configurations
    └── tasks.yaml          # Task definitions
```

### Agent Configuration

```python
@agent
def analyst(self) -> Agent:
    return Agent(
        config=self.agents_config["analyst"],
        tools=get_stock_crew_tools(include_rag=True),
        reasoning=True,              # For complex analysis
        max_reasoning_attempts=3,    # Prevent infinite loops
        allow_delegation=False,      # Only for coordinators
        verbose=True
    )

@final_reporter  # Enforces empty tools
@agent
def reporter(self) -> Agent:
    return Agent(
        config=self.agents_config["reporter"],
        tools=[],  # MUST be empty
        reasoning=False,
        verbose=True
    )
```

### Task YAML Requirements

Every task with `output_json: true` MUST include:

```yaml
analysis_task:
  description: >
    Analyze {ticker} with quantitative metrics

    🚨 JSON OUTPUT REQUIREMENTS 🚨
    - Output MUST be ONLY valid JSON
    - Your ENTIRE response must be a single JSON object
    - Do NOT include any text outside the JSON
    - NO trailing commas in JSON
```

### Flow Architecture

```python
class FinwizFlow(Flow[FinwizState]):
    @start()
    def initialize(self) -> dict[str, Any]:
        self.state.portfolio_review = {}
        return {"status": "initialized"}

    @listen(initialize)
    def analyze_portfolio(self, data: dict[str, Any]) -> dict[str, Any]:
        crew = StockCrew()
        result = crew.crew().kickoff(inputs={"ticker": "AAPL"})
        self.state.deep_analysis_results = result.raw
        return {"results": result.raw}
```

**Flow Rules:**
- ✅ Use `Flow[PydanticModel]` for type safety
- ✅ All methods return `dict[str, Any]`
- ✅ Access state via `self.state.field_name`
- ❌ NEVER use `self.inputs` (deprecated)

## Testing Standards

- **Framework**: pytest with pytest-mock (NEVER unittest.mock)
- **Coverage**: Minimum 65% (configured in pyproject.toml)
- **Test Data**: Faker library for realistic data

```python
# ❌ WRONG
from unittest.mock import Mock, patch

# ✅ CORRECT
def test_example(mocker):
    mock_obj = mocker.Mock()
    mocker.patch('module.function', return_value="result")
```

### Test Markers

```bash
pytest -m unit              # Unit tests only
pytest -m integration       # Integration tests
pytest -m slow              # Slow-running tests
```

## AI Minimalism

**Core Principle**: AI agents are tools, not the solution. Use Python for deterministic tasks.

### Use AI For

✅ Analysis requiring reasoning
✅ Synthesis of complex information
✅ Generating insights from unstructured data
✅ Natural language understanding

### Use Python For

❌ HTML generation (Jinja2)
❌ Data consolidation
❌ Calculations/formulas (numpy)
❌ Data validation (Pydantic)
❌ Template rendering

**Cost Example**: 100 HTML reports - AI: $5-10, 500-1000s | Python: $0, 1-2s

## Anti-Patterns

**Flow/State:**
- ❌ Using `self.inputs` instead of `self.state`
- ❌ Flow methods not returning `dict[str, Any]`
- ❌ Discovery crews running before portfolio analysis

**Agents:**
- ❌ Final reporters with tools
- ❌ Missing `max_reasoning_attempts` when reasoning enabled
- ❌ Enabling reasoning for high-volume (66+ runs)
- ❌ Enabling planning for single-agent crews
- ❌ Hardcoded tool lists (use tool factories)

**Code:**
- ❌ Using `unittest.mock` instead of pytest-mock
- ❌ Missing type hints on public functions
- ❌ Putting Pydantic models in domain folders (use `schemas/`)
- ❌ Using `json.dumps()` without `default=str`
- ❌ Leaving failing tests after refactoring

**Data:**
- ❌ Generating fake data to fill gaps
- ❌ HTML generation in orchestrators (use `reporting/`)
- ❌ Direct database calls from orchestrators

## Common Issues & Fixes

### JSON Serialization Errors

```python
# Always use default=str
json.dumps(data, default=str)
# Or use Pydantic
model.model_dump_json(indent=2)
```

### CrewAI Agent Input Loops

1. Check `max_reasoning_attempts` is set (default: 3)
2. Ensure task description repeats `{ticker}` explicitly
3. Verify `reasoning=False` for high-volume executions

### Mock Path Errors

```python
# Mock at the import location, not definition
mocker.patch('finwiz.crews.stock_crew.stock_crew.some_function')
```

### Pydantic Validation Errors

- Check schema uses `extra='forbid'`
- Verify all fields match schema exactly
- Use `model.model_dump(exclude_unset=True)` to skip None fields

## Code Standards

### Type Hints (Python 3.12+)

- Use `str | None` instead of `Optional[str]`
- Use `list[Type]` instead of `List[Type]`
- All public functions must have type hints

### File Size Limits

- **Hard limit**: 300 lines
- **Ideal target**: 150-200 lines
- File >300 lines → MUST split

### JSON Serialization

```python
# ❌ WRONG
result = json.dumps(data)

# ✅ CORRECT
result = json.dumps(data, default=str)

# ✅ BEST
result = model.model_dump_json(indent=2)
```

## MCP Servers

### Context7

Provides up-to-date library documentation. Use to verify API compatibility.

### Task Master AI

```bash
task-master next                    # Get next task
task-master show <id>               # View task details
task-master set-status --id=<id> --status=done
```

## Environment Variables

```bash
# Required
OPENAI_API_KEY=your_key
SERPER_API_KEY=your_key

# Performance
BATCH_PREFETCH_ENABLED=true
DEEP_ANALYSIS_BATCH_SIZE=5

# Validation
VALIDATION_STRICTNESS=warn  # off/warn/error
```

## Steering Documents

The `.kiro/steering/` directory contains specialized guides:

| Document | Purpose |
|----------|---------|
| `crewai-standards.md` | Complete CrewAI patterns |
| `ai-minimalism.md` | Python vs AI decision framework |
| `flow-architecture-lessons.md` | Flow design patterns |
| `testing-standards.md` | pytest-mock patterns |
| `claude-code-usage.md` | Claude Code best practices |
| `backtrader-standards.md` | Backtesting integration |
| `talib-standards.md` | Technical analysis |

## Changelog

Maintain [CHANGELOG.md](CHANGELOG.md) using Keep a Changelog format:

```markdown
### Fixed
- Resolved JSON serialization error by adding `default=str`
```
