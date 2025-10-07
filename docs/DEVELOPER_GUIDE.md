# FinWiz Developer Guide

Complete guide for developers working on the FinWiz codebase.

## Table of Contents

1.  [Quick Start](#quick-start)
2.  [Architecture Overview](#architecture-overview)
3.  [Core Development Standards](#core-development-standards)
4.  [Common Patterns](#common-patterns)
5.  [Troubleshooting](#troubleshooting)
6.  [See Also](#see-also)

## Quick Start

### Prerequisites

-   Python 3.12+
-   `uv` package manager
-   API keys (see `.env.example`)

### Setup

```bash
# Clone and install
git clone <repo-url>
cd finwiz
uv pip install .

# Set up environment
cp .env.example .env
# Edit .env with your API keys

# Run tests
uv run pytest -m "not integration"

# Run type checking
uv run mypy src/finwiz/

# Run linting
ruff check . && ruff format .
```

### Essential Commands

```bash
# Run application
uv run python src/finwiz/main.py

# Unit tests only (fast)
uv run pytest -m "not integration"

# Integration tests (requires API keys)
uv run pytest -m integration

# Coverage report
uv run pytest --cov=src/finwiz --cov-report=html

# Lint and format
ruff check . && ruff format .

# Type checking
uv run mypy src/finwiz/
```

## Architecture Overview

### Project Structure

```
src/finwiz/
├── crews/              # AI agent crews (crypto, stock, etf, report)
├── tools/              # Domain-specific analysis tools
├── schemas/            # Pydantic models with strict validation
├── orchestrators/      # Flow coordination logic
├── quantitative/       # Quantitative analysis framework
├── integration/        # Data integration components
├── validation/         # Validation system
├── utils/              # Utility functions
└── main.py            # CrewAI Flow entry point
```

### Standard Crew Structure

All crews must follow this structure:

```
src/finwiz/crews/{crew_name}/
├── {crew_name}.py          # @agent, @task, @crew decorators
└── config/
    ├── agents.yaml         # Agent configurations
    └── tasks.yaml          # Task definitions
```

### File Naming Conventions

-   **Python files**: `snake_case.py`
-   **Schema files**: `PascalCase.schema.json`
-   **Config files**: `kebab-case.yaml`
-   **Import order**: stdlib → third-party → local (blank line separated)

## Core Development Standards

FinWiz development is guided by a comprehensive set of standards that are automatically enforced by the AI agent during development. These standards ensure code quality, consistency, and maintainability.

For detailed rules and implementation patterns, refer to the official steering files:

-   **[Technology & Code Quality](/.kiro/steering/tech.md)**: Core technology stack, code standards, and quality requirements.
-   **[Testing Standards](/.kiro/steering/testing-standards.md)**: Rules for writing tests, including mocking strategies and naming conventions.
-   **[CrewAI Standards](/.kiro/steering/crewai-standards.md)**: Best practices for building agents, tasks, and crews.
-   **[Output & Formatting](/.kiro/steering/output-standards.md)**: Standards for generating HTML reports and other outputs.
-   **[Data Validation](/.kiro/steering/validation.md)**: Rules for data validation, schema compliance, and error handling.

## Common Patterns

### Tool Factories

Centralize tool initialization for consistency and maintainability.

```python
from finwiz.tools.tool_factories import get_stock_crew_tools

tools = get_stock_crew_tools(
    include_rag=True,
    include_quantitative=True,
    collection_suffix="stock"
)
```

### Agent Validators

Enforce architectural constraints, such as ensuring final reporters have no tools.

```python
from finwiz.utils.agent_validators import final_reporter

@final_reporter
@agent
def investment_reporter(self) -> Agent:
    return Agent(
        config=self.agents_config['investment_reporter'],
        tools=[],  # Must be empty - enforced by decorator
        verbose=True
    )
```

### Validation Manager

Use a centralized validation manager for all data checks.

```python
from finwiz.validation import get_validation_manager

manager = get_validation_manager()
result = manager.validate_crew_output(data, "stock", "analysis")
```

### Async Operations

Use `asyncio.gather` for concurrent I/O-bound operations to improve performance.

```python
import asyncio

async def analyze_holdings(tickers: list[str]) -> list[Analysis]:
    results = await asyncio.gather(
        *[analyze_ticker(ticker) for ticker in tickers]
    )
    return results
```

## Troubleshooting

### Common Issues

**Issue**: Tests failing with "No module named 'finwiz'"
**Solution**: Install in editable mode: `uv pip install -e .`

**Issue**: Type checking errors with CrewAI
**Solution**: Add `ignore_missing_imports = True` for `crewai.*` in `mypy.ini`.

**Issue**: Validation errors in production
**Solution**: Check the `VALIDATION_STRICTNESS` environment variable (off/warn/error).

### Debugging

Enable verbose logging for detailed output:
`import logging; logging.basicConfig(level=logging.DEBUG)`

## See Also

-   [Architecture Guide](ARCHITECTURE.md) - System design and patterns.
-   [API Reference](API_REFERENCE.md) - Complete API documentation.
-   [Data Quality Guide](DATA_QUALITY_GUIDE.md) - Best practices for ensuring data quality.

---
**Version**: 2.2
**Last Updated**: 2025-10-07