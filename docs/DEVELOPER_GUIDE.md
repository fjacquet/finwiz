# FinWiz Developer Guide

Complete guide for developers working on the FinWiz codebase.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Architecture Overview](#architecture-overview)
3. [CrewAI Development Standards](#crewai-development-standards)
4. [Testing Standards](#testing-standards)
5. [Code Quality Standards](#code-quality-standards)
6. [Common Patterns](#common-patterns)
7. [Troubleshooting](#troubleshooting)

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

- **Python files**: `snake_case.py`
- **Schema files**: `PascalCase.schema.json`
- **Config files**: `kebab-case.yaml`
- **Import order**: stdlib → third-party → local (blank line separated)

## CrewAI Development Standards

### Agent Configuration

```python
from crewai import Agent, agent
from finwiz.tools.tool_factories import get_stock_crew_tools

@agent
def stock_analyst(self) -> Agent:
    return Agent(
        config=self.agents_config["stock_analyst"],
        tools=get_stock_crew_tools(
            include_rag=True,
            include_quantitative=True,
            collection_suffix="stock"
        ),
        verbose=True
    )
```

### Task Configuration

```yaml
# config/tasks.yaml
stock_analysis_task:
  description: "Analyze stock with quantitative metrics"
  expected_output: "Structured analysis with risk assessment"
  output_pydantic: "TenKInsight"  # Use FinWiz schema
  output_json: true
  agent: stock_analyst
  async_execution: true
```

### Crew Configuration

```python
from crewai import Crew, crew, Process

@crew
def crew(self) -> Crew:
    return Crew(
        agents=self.agents,
        tasks=self.tasks,
        process=Process.sequential,
        verbose=True,
        respect_context_window=True,
        max_rpm=20
    )
```

### Required Tools by Crew Type

**Stock Crew**:

- `QuantitativeAnalysisTool(asset_class="stock")`
- `EnhancedSECAnalysisTool`
- `TickerValidationTool`
- `StandardizedSentimentTool`
- RAG tools via `get_rag_tools()`

**ETF Crew**:

- `QuantitativeAnalysisTool(asset_class="etf")`
- `EnhancedETFAnalysisTool`
- `TickerValidationTool`
- `StandardizedSentimentTool`
- RAG tools via `get_rag_tools()`

**Crypto Crew**:

- `QuantitativeAnalysisTool(asset_class="crypto")`
- `EnhancedCryptoAnalysisTool`
- `CoinMarketCapTool`
- `TickerValidationTool`
- RAG tools via `get_rag_tools()`

**Report Crew** (SPECIAL):

- Final reporters must have **empty tools list** (`tools=[]`)
- Only consume upstream context
- No external API calls

### CrewAI Compliance Checklist

When creating or modifying crews:

- [ ] Follows standard crew structure
- [ ] Uses `@agent`, `@task`, `@crew` decorators
- [ ] Agent configs in `agents.yaml`
- [ ] Task configs in `tasks.yaml`
- [ ] Uses tool factories for tool assignment
- [ ] Uses `output_pydantic` with FinWiz schemas
- [ ] I/O-bound tasks have `async_execution: true`
- [ ] Final task has `async_execution: false`
- [ ] Final reporters have empty tools list
- [ ] Generates `RiskAssessmentStandardized` objects

## Testing Standards

### Test Organization

```
tests/
├── unit/               # Unit tests (fast, mocked)
├── integration/        # Integration tests (slow, real APIs)
├── fixtures/           # Shared test fixtures
└── conftest.py        # pytest configuration
```

### Test Naming Convention

```python
def test_should_{behavior}_when_{condition}():
    """Test that describes expected behavior."""
    # Arrange
    # Act
    # Assert
```

### Mocking Strategy

**Always use `pytest-mock`, never `unittest.mock`**:

```python
def test_should_return_buy_recommendation_when_strong_metrics(mocker):
    # Arrange
    mock_api = mocker.patch('finwiz.tools.yahoo_finance_tool.get_data')
    mock_api.return_value = {'pe_ratio': 15, 'growth': 0.25}
    
    # Act
    result = analyze_stock('AAPL')
    
    # Assert
    assert result.recommendation == 'BUY'
    mock_api.assert_called_once_with('AAPL')
```

### Test Requirements

- **Mock all external calls**: APIs, file system, network requests
- **Fast execution**: Unit tests < 5 seconds per suite
- **Independence**: No shared state between tests
- **Arrange-Act-Assert**: Clear test structure
- **Descriptive names**: `test_should_{behavior}_when_{condition}`

### Test Data Generation

Use Faker for realistic test data:

```python
from faker import Faker

fake = Faker()

def test_portfolio_analysis():
    # Generate realistic test data
    ticker = fake.stock_symbol()
    price = fake.pyfloat(min_value=10, max_value=1000)
    # ... test logic
```

### Running Tests

```bash
# Unit tests only (fast)
uv run pytest -m "not integration"

# Integration tests (requires API keys)
uv run pytest -m integration

# Specific test file
uv run pytest tests/unit/tools/test_alternative_finder_tool.py

# With coverage
uv run pytest --cov=src/finwiz --cov-report=html

# Verbose output
uv run pytest -v
```

## Code Quality Standards

### Type Hints

**Required for all public methods**:

```python
def analyze_stock(
    ticker: str,
    asset_class: AssetClass,
    current_price: float
) -> StockAnalysis:
    """Analyze stock with proper type hints."""
    ...
```

**Use modern Python 3.10+ syntax**:

```python
# ✅ Correct
def get_price(ticker: str) -> float | None:
    ...

# ❌ Avoid
from typing import Optional
def get_price(ticker: str) -> Optional[float]:
    ...
```

### Pydantic Models

**Use strict validation**:

```python
from pydantic import BaseModel, Field

class TickerInput(BaseModel):
    symbol: str = Field(..., pattern=r'^[A-Z]{1,5}$')
    
    model_config = {
        "str_strip_whitespace": True,
        "str_upper": True,
        "extra": "forbid"  # Prevent schema drift
    }
```

### Error Handling

```python
class FinWizError(Exception):
    """Base exception for FinWiz application."""
    pass

class InvalidTickerError(FinWizError):
    """Raised when ticker symbol is invalid."""
    
    def __init__(self, ticker: str):
        super().__init__(f"Invalid ticker symbol: {ticker}")
        self.ticker = ticker
```

### Logging

```python
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)

logger.info("Analyzing holding", extra={
    "ticker": ticker,
    "asset_class": asset_class,
    "cache_hit": cache_hit
})
```

### Code Style

- **Line limit**: 110 characters
- **Docstrings**: Google style for all public classes/methods
- **Imports**: Grouped and sorted (stdlib, third-party, local)
- **Variables**: Descriptive names (`analysis_result` not `ar`)

### HTML Generation Standards

**MANDATORY: Use BeautifulSoup4 for all HTML generation**

```python
from bs4 import BeautifulSoup, Tag

def generate_report(title: str, data: dict) -> str:
    """Generate HTML report using bs4 for security and maintainability."""
    soup = BeautifulSoup("", "html.parser")
    html = soup.new_tag("html")
    
    head = soup.new_tag("head")
    title_tag = soup.new_tag("title")
    title_tag.string = title  # Automatic XSS escaping
    head.append(title_tag)
    
    body = soup.new_tag("body")
    h1 = soup.new_tag("h1")
    h1.string = title
    body.append(h1)
    
    # User data is automatically escaped
    p = soup.new_tag("p")
    p.string = data['content']  # Safe from XSS
    body.append(p)
    
    html.append(head)
    html.append(body)
    soup.append(html)
    
    return soup.prettify(formatter="html")  # UTF-8 safe output
```

**HTML Generation Rules**:

- ✅ **REQUIRED**: Use `bs4.BeautifulSoup` and `bs4.Tag` objects
- ✅ **REQUIRED**: Use `.prettify(formatter="html")` for UTF-8 output
- ✅ **REQUIRED**: Rely on bs4's automatic XSS escaping for user data
- ❌ **FORBIDDEN**: String concatenation (`f"<html>{content}</html>"`)
- ❌ **FORBIDDEN**: Manual HTML building (`html += "<div>"`)
- ❌ **FORBIDDEN**: `.format()` or `%` formatting for HTML

**Security Benefits**:

- Automatic HTML entity escaping prevents XSS vulnerabilities
- Proper UTF-8 encoding handling
- Well-formed HTML structure guaranteed
- Better code readability and maintainability

### Linting and Formatting

```bash
# Check and format
ruff check . && ruff format .

# Type checking
uv run mypy src/finwiz/
```

## Common Patterns

### Tool Factories

Centralize tool initialization:

```python
from finwiz.tools.tool_factories import get_stock_crew_tools

tools = get_stock_crew_tools(
    include_rag=True,
    include_quantitative=True,
    collection_suffix="stock"
)
```

### Agent Validators

Enforce architectural constraints:

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

Use centralized validation:

```python
from finwiz.validation import get_validation_manager

manager = get_validation_manager()

# Validate crew output
result = manager.validate_crew_output(data, "stock", "analysis")
if result.is_valid:
    processed_data = result.sanitized_data
else:
    for error in result.errors:
        logger.error(f"Validation error: {error.message}")
```

### Async Operations

Use async for I/O-bound operations:

```python
import asyncio

async def analyze_holdings(tickers: list[str]) -> list[Analysis]:
    # Parallel analysis
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
**Solution**: Add to `mypy.ini`:

```ini
[mypy-crewai.*]
ignore_missing_imports = True
```

**Issue**: Validation errors in production
**Solution**: Check `VALIDATION_STRICTNESS` environment variable (off/warn/error)

**Issue**: Cache not working
**Solution**: Check `CACHE_BACKEND` and `CACHE_TTL` environment variables

### Debug Mode

Enable verbose logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Performance Profiling

```bash
# Profile test execution
uv run pytest --profile

# Profile application
python -m cProfile -o profile.stats src/finwiz/main.py
```

## See Also

- [Architecture Guide](ARCHITECTURE.md) - System design and patterns
- [API Reference](API_REFERENCE.md) - Complete API documentation
- [Agent Handbook](agent_handbook.md) - Agent guidelines
- [Testing Guide](test_coverage_stabilization.md) - Comprehensive testing guide

---

**Version**: 2.0  
**Last Updated**: 2025-03-10
