# FinWiz Developer Guide

Complete guide for developers working on the FinWiz codebase.

## Table of Contents

1.  [Quick Start](#quick-start)
2.  [Architecture Overview](#architecture-overview)
3.  [Core Development Standards](#core-development-standards)
4.  [Common Patterns & Workflows](#common-patterns--workflows)
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

# Lint, format, and type check
ruff check . && ruff format .
uv run mypy src/finwiz/

# Documentation development
make docs-install              # Install documentation dependencies
make docs-serve               # Start development server
make docs-build               # Build static site
make docs-validate            # Validate documentation quality
ruff check . --fix && ruff format . && uv run mypy src/finwiz/

# Performance testing with optimizations
RISK_ASSESSMENT_USE_MINI=true USE_MINIMAL_RISK_TOOLS=true uv run python src/finwiz/main.py

# Baseline testing without optimizations
RISK_ASSESSMENT_USE_MINI=false USE_MINIMAL_RISK_TOOLS=false uv run python src/finwiz/main.py
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

## Core Development Standards

FinWiz development is guided by a comprehensive set of standards that are automatically enforced by the AI agent during development. These standards ensure code quality, consistency, and maintainability.

**For detailed rules and implementation patterns, refer to the official steering files in the `/.kiro/steering/` directory:**

-   **[Technology & Code Quality](/.kiro/steering/tech.md)**: Core technology stack, code standards (style, error handling, documentation), and quality requirements.
-   **[Testing Standards](/.kiro/steering/testing-standards.md)**: Rules for writing tests, including mocking strategies (`pytest-mock` only), naming conventions, and coverage.
-   **[CrewAI Standards](/.kiro/steering/crewai-standards.md)**: Best practices for building agents, tasks, and crews, including async patterns.
-   **[Output & Formatting](/.kiro/steering/output-standards.md)**: Standards for generating HTML reports and other outputs.
-   **[Data Validation](/.kiro/steering/validation.md)**: Rules for data validation, schema compliance, and error handling.

## Common Patterns & Workflows

This section provides practical examples of how to apply the project's standards in common development scenarios.

### Using Tool Factories

Centralize tool initialization for consistency.

```python
from finwiz.tools.tool_factories import get_stock_crew_tools

# Get a standardized set of tools for the stock crew
tools = get_stock_crew_tools(
    include_rag=True,
    include_quantitative=True,
    collection_suffix="stock"
)
```

### Enforcing Agent Constraints

Use decorators to enforce architectural rules, like ensuring final reporters have no tools.

```python
from finwiz.utils.agent_validators import final_reporter

@final_reporter
@agent
def investment_reporter(self) -> Agent:
    return Agent(
        config=self.agents_config['investment_reporter'],
        tools=[],  # This is enforced by the @final_reporter decorator
        verbose=True
    )
```

### Using Task Decorators

Explicitly mark task execution modes to improve clarity and prevent errors.

```python
from finwiz.utils.task_decorators import async_task, sync_task

@async_task
@task
def research_task(self) -> Task:
    # This task will run asynchronously
    return Task(...)

@sync_task
@task
def final_report_task(self) -> Task:
    # The final task in a sequential process must be synchronous
    return Task(...)
```

### Adding a New Crew

1.  Create the directory structure: `src/finwiz/crews/my_crew/config`.
2.  Create `my_crew.py`, `agents.yaml`, and `tasks.yaml`.
3.  Implement the crew, following the patterns for agent validation and task decorators.
4.  Add comprehensive unit tests for the new crew.

### Adding a New Tool

1.  Create the tool in a relevant module under `src/finwiz/tools/`.
2.  Add the new tool to the appropriate factory function in `src/finwiz/tools/tool_factories.py`.
3.  Write unit tests to cover the new tool's functionality.

### Performance Optimization

FinWiz includes performance optimizations for the DeepAnalysisCrew that can be configured via environment variables.

**GPT-5-mini for Risk Assessment (Phase 1)**

The risk assessor agent can use GPT-5-mini instead of the default LLM for faster, cheaper execution:

```python
# In deep_analysis.py
import os

use_mini = os.getenv("RISK_ASSESSMENT_USE_MINI", "true").lower() == "true"

if use_mini:
    risk_llm = LLM(model="gpt-5-mini")
else:
    risk_llm = self._get_configured_llm()
```

**Configuration:**
```bash
# Enable (default)
RISK_ASSESSMENT_USE_MINI=true

# Disable for baseline comparison
RISK_ASSESSMENT_USE_MINI=false
```

**Minimal Tool Set for Risk Assessor (Phase 2)**

The risk assessor can use a minimal tool set instead of the full tool set to reduce initialization overhead:

```python
# In deep_analysis.py
use_minimal_risk_tools = os.getenv("USE_MINIMAL_RISK_TOOLS", "true").lower() == "true"

if use_minimal_risk_tools:
    risk_tools = self.get_tools_for_asset_class(asset_class, minimal=True)
else:
    risk_tools = analyst_tools
```

**Minimal Tool Set Includes:**
- `QuantitativeAnalysisTool` (core risk metrics)
- `TickerValidationTool` (ticker validation)
- Asset-specific tool (SEC/ETF/Crypto analysis)

**Configuration:**
```bash
# Enable (default)
USE_MINIMAL_RISK_TOOLS=true

# Disable for full tool set
USE_MINIMAL_RISK_TOOLS=false
```

**Testing Performance Optimizations:**

```bash
# Test with all optimizations (fastest)
RISK_ASSESSMENT_USE_MINI=true USE_MINIMAL_RISK_TOOLS=true \
  time uv run python src/finwiz/main.py --ticker AAPL --asset-class stock

# Test with Phase 1 only
RISK_ASSESSMENT_USE_MINI=true USE_MINIMAL_RISK_TOOLS=false \
  time uv run python src/finwiz/main.py --ticker AAPL --asset-class stock

# Test baseline (no optimizations)
RISK_ASSESSMENT_USE_MINI=false USE_MINIMAL_RISK_TOOLS=false \
  time uv run python src/finwiz/main.py --ticker AAPL --asset-class stock
```

**Expected Performance Impact:**
- 20-30% reduction in execution time
- Lower LLM API costs (GPT-5-mini is cheaper)
- Maintained accuracy for risk calculations

**When to Disable Optimizations:**
- Debugging tool-related issues
- Comparative analysis with baseline results
- Complex risk scenarios requiring advanced reasoning
- Regulatory compliance requiring specific model versions

## Troubleshooting

### Common Issues

**Issue**: Tests failing with "No module named 'finwiz'"
**Solution**: Install the project in editable mode: `uv pip install -e .`

**Issue**: Type checking errors related to CrewAI
**Solution**: Ensure `mypy.ini` is configured to ignore missing imports for `crewai.*` and `crewai_tools.*`.

**Issue**: Validation errors in production
**Solution**: Check the `VALIDATION_STRICTNESS` environment variable. Set it to `warn` for debugging or `error` for strict enforcement.

### Debugging

Enable verbose logging for detailed output from the application and crews:
`import logging; logging.basicConfig(level=logging.DEBUG)`

## See Also

-   [Architecture Guide](ARCHITECTURE.md) - System design and data flow.
-   [API Reference](API_REFERENCE.md) - Complete API documentation for tools and schemas.
-   [Data Quality and Flow Guide](DATA_QUALITY_AND_FLOW_GUIDE.md) - Best practices for ensuring data integrity.
-   [User Guide](USER_GUIDE.md) - Guide for deploying, operating, and migrating the application.

---
**Version**: 2.2
**Last Updated**: 2025-10-07