---
title: "Development"
description: "Complete reference documentation for Development"
category: "reference"
tags:
  - "reference"
date: "2025-10-26"
source: "archive/consolidation_reports/DEVELOPMENT_GUIDE.md"
---

# FinWiz Development Guide

This guide provides comprehensive information for developers working on the FinWiz codebase, including coding standards, design patterns, and best practices.

## Table of Contents

- [Quick Start](#quick-start)
- [Development Patterns](#development-patterns)
- [Code Quality Standards](#code-quality-standards)
- [Testing Guidelines](#testing-guidelines)
- [Type Hints and Static Analysis](#type-hints-and-static-analysis)
- [Logging and Observability](#logging-and-observability)
- [Common Workflows](#common-workflows)

## Quick Start

### Prerequisites

- Python 3.10+
- `uv` package manager
- API keys (see `.env.example`)

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
```text
## Development Patterns

FinWiz implements several standardized patterns to ensure code quality, consistency, and maintainability.

### Tool Factories

**Purpose**: Centralize tool initialization logic for all crews, eliminating code duplication and ensuring consistent configuration.

**Location**: `src/finwiz/tools/tool_factories.py`

**Usage**:

```pythonthon
from finwiz.tools.tool_factories import (
    get_stock_crew_tools,
    get_crypto_crew_tools,
    get_etf_crew_tools
)

# Get standardized tool set
tools = get_stock_crew_tools(
    include_rag=True,           # Include RAG tools
    include_quantitative=True,  # Include quantitative analysis
    collection_suffix="stock"   # RAG collection suffix
)
```text
**Available Factories**:

- `get_stock_crew_tools()` - Stock analysis tools
- `get_crypto_crew_tools()` - Cryptocurrency analysis tools
- `get_etf_crew_tools()` - ETF analysis tools

**Benefits**:

- Single source of truth for tool configuration
- Easy to add/remove tools globally
- Consistent tool sets across crews
- Optional parameters for flexibility

**When to Use**:

- When creating new crews
- When updating tool configurations
- When adding new tool types

### Agent Validators

**Purpose**: Enforce architectural constraints at initialization time, specifically preventing final reporters from receiving tools.

**Location**: `src/finwiz/utils/agent_validators.py`

**Usage**:

```pythonthon
from finwiz.utils.agent_validators import final_reporter
from crewai import Agent, agent

@final_reporter
@agent
def investment_reporter(self) -> Agent:
    """Final reporter that consolidates upstream analysis."""
    return Agent(
        config=self.agents_config['investment_reporter'],
        tools=[],  # Must be empty - enforced by decorator
        verbose=True
    )
```text
**Validation Rules**:

- Final reporters must have `tools=[]` (empty list)
- Decorator raises `FinalReporterError` if tools are found
- Error message includes agent role and tool count
- Successful validation is logged for observability

**Error Example**:

```text
FinalReporterError: Final reporter 'Investment Reporter' must have NO tools.
Found 3 tools. Final reporters should only consume upstream context.
```text
**When to Use**:

- For all final reporter agents (investment_reporter, translator, etc.)
- When creating new report-generation agents
- To enforce separation of concerns (research vs. reporting)

### Task Decorators

**Purpose**: Explicitly mark task execution modes to prevent common errors where final tasks are incorrectly configured as async.

**Location**: `src/finwiz/utils/task_decorators.py`

**Usage**:

```pythonthon
from finwiz.utils.task_decorators import async_task, sync_task
from crewai import Task, task

@async_task
@task
def research_task(self) -> Task:
    """Parallel research task."""
    return Task(
        config=self.tasks_config['research'],
        agent=self.researcher()
    )

@sync_task
@task
def final_report_task(self) -> Task:
    """Final task - must be synchronous."""
    return Task(
        config=self.tasks_config['final_report'],
        agent=self.reporter()
    )
```text
**Decorator Behavior**:

- `@async_task` - Sets `task.async_execution = True`
- `@sync_task` - Sets `task.async_execution = False`
- Both decorators log configuration for debugging

**Important Rules**:

- Final tasks in sequential workflows **must** use `@sync_task` (CrewAI requirement)
- Parallel tasks should use `@async_task` for better performance
- Decorators preserve function metadata using `functools.wraps`

**When to Use**:

- For all tasks in all crews
- When creating new tasks
- To make execution mode explicit and self-documenting

### Structured Logging

**Purpose**: Provide consistent structured logging across all crews for better observability and debugging.

**Location**: `src/finwiz/utils/logging_helpers.py`

**Usage**:

```pythonthon
from finwiz.utils.logging_helpers import CrewLogger
import time
from typing import Any

class StockCrew:
    def __init__(self):
        super().__init__()
        self.logger = CrewLogger("StockCrew")

    def kickoff(self, inputs: dict) -> Any:
        """Execute crew with structured logging."""
        self.logger.log_start(inputs)
        start_time = time.time()

        try:
            result = super().kickoff(inputs)
            duration = time.time() - start_time
            self.logger.log_complete(duration)
            return result
        except Exception as e:
            self.logger.log_error(e)
            raise
```text
**Log Methods**:

- `log_start(inputs)` - Log crew execution start with input keys
- `log_complete(duration)` - Log successful completion with duration
- `log_error(error)` - Log errors with full exception info

**Log Structure**:

```pythonthon
# log_start() output
{
    "crew": "StockCrew",
    "input_keys": ["ticker", "analysis_type"],
    "event": "crew_start"
}

# log_complete() output
{
    "crew": "StockCrew",
    "duration": 45.2,
    "event": "crew_complete"
}

# log_error() output
{
    "crew": "StockCrew",
    "error_type": "ValidationError",
    "event": "crew_error",
    "exc_info": True
}
```text
**Benefits**:

- Consistent log format across all crews
- Structured fields for easy parsing
- Performance tracking with execution duration
- Comprehensive error logging

**When to Use**:

- In all crew `kickoff()` methods
- When tracking execution flow
- For performance monitoring
- For debugging and troubleshooting

## Code Quality Standards

### Python Style

FinWiz follows strict Python style guidelines enforced by Ruff:

- **Line Limit**: 110 characters
- **Import Order**: stdlib → third-party → local (blank line separated)
- **Naming Conventions**:
  - Files: `snake_case.py`
  - Classes: `PascalCase`
  - Functions/Variables: `snake_case`
  - Constants: `UPPER_SNAKE_CASE`

**Example**:

```pythonthon
# Standard library
import asyncio
from typing import Any

# Third-party
from crewai import Agent, Task
from pydantic import BaseModel

# Local imports
from finwiz.schemas.common import BaseAnalysis
from finwiz.tools.finance_tools import get_market_data
```text
### Error Handling

Use custom exception classes with clear error messages:

```pythonthon
class FinWizError(Exception):
    """Base exception for FinWiz application."""
    pass

class InvalidTickerError(FinWizError):
    """Raised when ticker symbol is invalid or not found."""

    def __init__(self, ticker: str):
        super().__init__(f"Invalid ticker symbol: {ticker}")
        self.ticker = ticker
```text
### Documentation

- **Docstrings**: Required for all public classes and methods (Google style)
- **Type Annotations**: Required for all public methods
- **Examples**: Include usage examples for complex functions

**Example**:

```pythonthon
def analyze_stock(ticker: str, period: str = "1y") -> StockAnalysis:
    """
    Analyze stock with comprehensive metrics.

    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL')
        period: Analysis period (default: '1y')

    Returns:
        StockAnalysis object with metrics and recommendations

    Raises:
        InvalidTickerError: If ticker is invalid or not found

    Example:
        >>> analysis = analyze_stock('AAPL', period='6mo')
        >>> print(analysis.recommendation)
        'BUY'
    """
    ...
```text
## Testing Guidelines

### Test Structure

All tests follow the Arrange-Act-Assert pattern:

```pythonthon
def test_should_return_buy_recommendation_when_strong_metrics(mocker):
    # Arrange
    mock_api = mocker.patch('finwiz.tools.yahoo_finance_tool.get_data')
    mock_api.return_value = {'pe_ratio': 15, 'growth': 0.25}

    # Act
    result = analyze_stock('AAPL')

    # Assert
    assert result.recommendation == 'BUY'
    mock_api.assert_called_once_with('AAPL')
```text
### Test Naming

Use descriptive names that explain behavior:

```text
test_should_{expected_behavior}_when_{condition}
```text
Examples:

- `test_should_return_buy_recommendation_when_strong_fundamentals`
- `test_should_raise_error_when_invalid_ticker_provided`
- `test_should_cache_results_when_same_ticker_requested_twice`

### Mocking Strategy

**Always use pytest-mock** (never `unittest.mock`):

```pythonthon
def test_stock_analysis(mocker):
    # Mock external API calls
    mock_api = mocker.patch('finwiz.tools.yahoo_finance_tool.get_stock_data')
    mock_api.return_value = {'symbol': 'AAPL', 'price': 150.0}

    # Mock file system operations
    mock_file = mocker.patch('pathlib.Path.write_text')

    # Test your code
    result = analyze_and_save('AAPL')

    # Verify mocks were called correctly
    mock_api.assert_called_once_with('AAPL')
    mock_file.assert_called_once()
```text
### Test Requirements

- **Performance**: Unit tests must complete in < 5 seconds per suite
- **Independence**: Tests must not depend on execution order
- **No External Calls**: Mock all APIs, file system, network requests
- **Coverage**: Maintain > 80% code coverage
- **Isolation**: No shared state between tests

### Test Categories

```bash
# Unit tests only (fast)
uv run pytest -m "not integration"

# Integration tests (requires API keys)
uv run pytest -m integration

# Contract tests (schema validation)
uv run pytest tests/test_contract_*.py

# All tests
uv run pytest -v
```text
## Type Hints and Static Analysis

### Type Hint Standards

FinWiz uses Python 3.10+ type hints with mypy for static analysis.

**Modern Syntax**:

```pythonthon
# ✅ Use Python 3.10+ syntax
def get_data(ticker: str | None = None) -> dict[str, Any]:
    ...

# ❌ Don't use old syntax
from typing import Optional, Dict, Any
def get_data(ticker: Optional[str] = None) -> Dict[str, Any]:
    ...
```text
**Required Type Hints**:

- All public function parameters
- All public function return types
- Complex internal functions
- Class attributes (when not obvious)

**Example**:

```pythonthon
from crewai.tools import BaseTool

def get_stock_crew_tools(
    include_rag: bool = True,
    include_quantitative: bool = True,
    collection_suffix: str = "stock",
) -> list[BaseTool]:
    """
    Get standardized tool set for Stock Crew.

    Args:
        include_rag: Whether to include RAG tools
        include_quantitative: Whether to include quantitative analysis
        collection_suffix: Suffix for RAG collection name

    Returns:
        List of configured tools for stock analysis
    """
    tools: list[BaseTool] = []
    # Implementation...
    return tools
```text
### Mypy Configuration

Configuration is in `mypy.ini`:

```ini
[mypy]
python_version = 3.10
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
disallow_incomplete_defs = True
check_untyped_defs = True
strict_optional = True

[mypy-crewai.*]
ignore_missing_imports = True

[mypy-crewai_tools.*]
ignore_missing_imports = True
```text
### Running Type Checks

```bash
# Check all modules
uv run mypy src/finwiz/

# Check specific module
uv run mypy src/finwiz/tools/tool_factories.py

# Check with verbose output
uv run mypy --verbose src/finwiz/
```text
## Logging and Observability

### Logging Levels

- **DEBUG**: Detailed information for debugging
- **INFO**: General informational messages
- **WARNING**: Warning messages for potential issues
- **ERROR**: Error messages for failures
- **CRITICAL**: Critical errors that may cause system failure

### Structured Logging

Always use structured logging with extra fields:

```pythonthon
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)

# Good - structured logging
logger.info(
    "Stock analysis completed",
    extra={
        "ticker": "AAPL",
        "duration": 45.2,
        "recommendation": "BUY"
    }
)

# Bad - string interpolation
logger.info(f"Stock analysis for AAPL completed in 45.2s: BUY")
```text
### Security Considerations

**Never log sensitive data**:

- API keys
- Tokens
- Personal financial information
- Full error traces in production

```pythonthon
# ✅ Safe logging
logger.info("API call completed", extra={"ticker": ticker, "status": "success"})

# ❌ Unsafe logging
logger.info(f"API call with key {api_key} failed: {full_error}")
```text
## Common Workflows

### Adding a New Crew

1. Create crew directory structure:

```bash
mkdir -p src/finwiz/crews/my_crew/config
touch src/finwiz/crews/my_crew/__init__.py
touch src/finwiz/crews/my_crew/my_crew.py
touch src/finwiz/crews/my_crew/config/agents.yaml
touch src/finwiz/crews/my_crew/config/tasks.yaml
```text
2. Implement crew with patterns:

```pythonthon
from crewai import Agent, Task, Crew, agent, task, crew
from finwiz.tools.tool_factories import get_stock_crew_tools
from finwiz.utils.agent_validators import final_reporter
from finwiz.utils.task_decorators import async_task, sync_task
from finwiz.utils.logging_helpers import CrewLogger

class MyCrew:
    def __init__(self):
        self.logger = CrewLogger("MyCrew")
        self.tools = get_stock_crew_tools()

    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['researcher'],
            tools=self.tools
        )

    @final_reporter
    @agent
    def reporter(self) -> Agent:
        return Agent(
            config=self.agents_config['reporter'],
            tools=[]
        )

    @async_task
    @task
    def research_task(self) -> Task:
        return Task(config=self.tasks_config['research'])

    @sync_task
    @task
    def report_task(self) -> Task:
        return Task(config=self.tasks_config['report'])

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[self.researcher(), self.reporter()],
            tasks=[self.research_task(), self.report_task()],
            process=Process.sequential
        )
```text
3. Add tests:

```pythonthon
def test_my_crew_initialization(mocker):
    # Mock tool factories
    mock_tools = mocker.patch('finwiz.tools.tool_factories.get_stock_crew_tools')
    mock_tools.return_value = []

    # Test crew initialization
    crew = MyCrew()
    assert crew is not None
    assert len(crew.crew().agents) == 2
```text
### Adding a New Tool

1. Create tool module:

```pythonthon
# src/finwiz/tools/my_tool.py
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

class MyToolInput(BaseModel):
    """Input schema for MyTool."""
    ticker: str = Field(..., description="Stock ticker symbol")

class MyTool(BaseTool):
    name: str = "my_tool"
    description: str = "Description of what the tool does"
    args_schema: type[BaseModel] = MyToolInput

    def _run(self, ticker: str) -> str:
        """Execute the tool."""
        # Implementation
        return f"Result for {ticker}"
```text
2. Add to tool factory:

```pythonthon
# src/finwiz/tools/tool_factories.py
from finwiz.tools.my_tool import MyTool

def get_stock_crew_tools(...) -> list[BaseTool]:
    tools = [
        # Existing tools...
        MyTool(),
    ]
    return tools
```text
3. Add tests:

```pythonthon
def test_my_tool_execution(mocker):
    tool = MyTool()
    result = tool._run(ticker="AAPL")
    assert "AAPL" in result
```text
### Running Quality Checks

Before committing code:

```bash
# 1. Format code
ruff format .

# 2. Check linting
ruff check .

# 3. Run type checking
uv run mypy src/finwiz/

# 4. Run tests
uv run pytest -m "not integration"

# 5. Check coverage
uv run pytest --cov=src/finwiz --cov-report=html
```text
### Debugging Tips

1. **Enable verbose logging**:

```pythonthon
import logging
logging.basicConfig(level=logging.DEBUG)
```text
2. **Use CrewLogger for structured logs**:

```pythonthon
logger = CrewLogger("MyCrew")
logger.log_start({"ticker": "AAPL"})
```text
3. **Check mypy for type errors**:

```bash
uv run mypy --verbose src/finwiz/tools/my_tool.py
```text
4. **Run specific test**:

```bash
uv run pytest tests/unit/tools/test_my_tool.py::test_specific_function -v
```text
## Additional Resources

- [Agent Handbook](agent_handbook.md) - Guidelines for AI agents
- [Design Principles](DESIGN_PRINCIPLES.md) - Core architectural principles
- [Validation System](validation_system.md) - Data validation infrastructure
- [Caching System](caching_system.md) - Intelligent caching capabilities
- [Quick Wins Implementation](QUICK_WINS_IMPLEMENTATION.md) - Recent improvements

---

For questions or contributions, please refer to the main README.md or open an issue.
