# Developer Guide

Complete guide for developing with FinWiz, including architecture, standards, and best practices.

## Development Environment

### Setup

1. **Clone and install**:
```bash
git clone https://github.com/finwiz/finwiz.git
cd finwiz
uv sync --group dev
```

2. **Set up pre-commit hooks**:
```bash
uv run pre-commit install
```

3. **Run tests**:
```bash
uv run pytest -m "not integration"
```

## Architecture Overview

FinWiz uses a modular architecture built on CrewAI Flow:

```
src/finwiz/
├── crews/           # AI agent crews (crypto, stock, etf, report)
├── tools/           # Domain-specific analysis tools
├── schemas/         # Pydantic models with strict validation
├── orchestrators/   # Flow coordination logic
├── templates/       # HTML report templates
└── main.py         # CrewAI Flow entry point
```

### Core Components

- **CrewAI Flows**: Orchestrate multi-agent analysis workflows
- **Pydantic Schemas**: Strict data validation and type safety
- **Analysis Tools**: Modular tools for different asset classes
- **HTML Templates**: Professional report generation

## Development Standards

### Code Quality

**Required Tools**:
- `ruff` for linting and formatting (110 char limit)
- `pytest` with `pytest-mock` for testing
- `mypy` for type checking

**Essential Commands**:
```bash
uv run python src/finwiz/main.py    # Run application
uv run pytest -m "not integration"  # Unit tests only
ruff check . && ruff format .        # Lint and format
make check-unittest-mock             # Check for banned unittest.mock
```

### Testing Requirements

**unittest.mock is BANNED** ⛔ - Use `pytest-mock` exclusively:

```python
# ✅ CORRECT - Always use this
def test_example(mocker):
    mock_obj = mocker.patch('module.function')
    mock_obj.return_value = 'test'

# ❌ BANNED - Will be blocked by enforcement
from unittest.mock import patch, Mock
```

**Test Patterns**:
- Mock all external dependencies (APIs, file system, LLM calls)
- Test naming: `test_should_{behavior}_when_{condition}`
- Structure: Arrange-Act-Assert with clear assertions
- Performance: < 5 seconds per test suite

### Type Safety

All public methods must have complete type annotations:

```python
# ✅ CORRECT
def analyze_stock(ticker: str, period: int = 365) -> StockAnalysis:
    return StockAnalysis(ticker=ticker, period=period)

# ❌ WRONG - Missing return type
def analyze_stock(ticker: str):
    return StockAnalysis(ticker=ticker)
```

## CrewAI Development

### Crew Structure

All crews must follow this exact structure:

```
src/finwiz/crews/{crew_name}/
├── {crew_name}.py          # @agent, @task, @crew decorators
└── config/
    ├── agents.yaml         # Agent configurations  
    └── tasks.yaml          # Task definitions
```

### Agent Configuration

```python
from crewai import Agent, agent
from finwiz.tools.tool_factories import get_stock_crew_tools

@agent
def analyst(self) -> Agent:
    return Agent(
        config=self.agents_config["analyst"],
        tools=get_stock_crew_tools(include_rag=True),
        reasoning=True,
        max_reasoning_attempts=3,
        verbose=True
    )
```

### Flow State Management

Always use Pydantic models for type-safe Flow state:

```python
from pydantic import BaseModel
from crewai.flow.flow import Flow

class MyFlowState(BaseModel):
    holdings_processed: int = 0
    current_ticker: str = ""
    results: dict[str, Any] = {}

class MyFlow(Flow[MyFlowState]):
    @start()
    def initialize(self) -> dict[str, Any]:
        self.state.holdings_processed = 0
        return {"status": "initialized"}
```

## Data Validation

### Pydantic Models (Strict)

All inputs/outputs must use Pydantic v2 with strict validation:

```python
from pydantic import BaseModel, Field, field_validator

class TickerInput(BaseModel):
    symbol: str = Field(..., pattern=r'^[A-Z]{1,5}$')
    
    model_config = {
        "str_strip_whitespace": True,
        "str_upper": True,
        "extra": "forbid"  # Reject unknown fields
    }
    
    @field_validator('symbol')
    @classmethod
    def validate_ticker_format(cls, v: str) -> str:
        if not v.isalpha():
            raise ValueError('Ticker must contain only letters')
        return v.upper()
```

## Security Standards

### API Key Management

- **Never log**: API keys, tokens, or sensitive financial data
- **Environment variables only**: Use `.env` for local development
- **Startup validation**: Check all required keys with clear error messages

```python
# ✅ CORRECT
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable not set")

# ❌ WRONG - Hardcoded
api_key = "sk-proj-abc123..."
```

### Input Validation

- All inputs must use strict Pydantic models
- Sanitize ticker symbols, amounts, dates
- Never log personal financial information

## Performance Patterns

### Async Operations

```python
# Use asyncio.gather() for parallel operations
results = await asyncio.gather(
    get_stock_data(ticker),
    get_news_data(ticker),
    get_sentiment_data(ticker)
)

# Always use timeouts and proper error handling
async with httpx.AsyncClient(timeout=30.0) as client:
    response = await client.get(url)
```

### Memory Management

- Process large datasets in chunks
- Use generators for streaming data
- Always use context managers for file operations
- Implement caching with appropriate TTL

## HTML Report Generation

### Template System

FinWiz uses Jinja2 templates for professional HTML reports:

```python
from finwiz.utils.html_generator import save_json_with_html

# Automatically generate HTML from JSON data
json_path, html_path = save_json_with_html(
    data=analysis_result,
    file_path="output/portfolio_review.json"
)
```

### Custom Templates

Create custom templates in `src/finwiz/templates/`:

```html
{% extends "base_template.html" %}

{% block content %}
<div class="header">
    <h1>📊 {{ title }}</h1>
</div>

<div class="section">
    <h2>Analysis Results</h2>
    {% for item in results %}
        <div class="card">{{ item.summary }}</div>
    {% endfor %}
</div>
{% endblock %}
```

## Testing Framework

### Unit Tests

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

### Integration Tests

Mark with `@pytest.mark.integration` and require API keys:

```python
@pytest.mark.integration
def test_should_fetch_real_stock_data():
    # Requires API keys and network access
    result = get_stock_data('AAPL')
    assert result is not None
```

## Common Patterns

### Tool Factory Pattern

```python
# tools/{domain}_tools.py
def get_{domain}_tools() -> list:
    """Return curated tool set for domain analysis."""
    return [tool1(), tool2(), tool3()]
```

### Error Handling

```python
class FinWizError(Exception):
    """Base exception for FinWiz application."""
    pass

class InvalidTickerError(FinWizError):
    """Raised when ticker symbol is invalid or not found."""
    
    def __init__(self, ticker: str):
        super().__init__(f"Invalid ticker symbol: {ticker}")
        self.ticker = ticker
```

## Pre-Commit Checklist

Before committing code:

- [ ] **No unittest.mock** - Use pytest-mock exclusively (ENFORCED)
- [ ] **All external dependencies mocked** in tests
- [ ] **Fast test execution** (< 5 seconds per suite)
- [ ] **Type hints** on all public methods
- [ ] **Pydantic validation** for all inputs/outputs
- [ ] **API keys** in environment variables only
- [ ] **Error handling** with custom exceptions
- [ ] **Async patterns** for I/O operations
- [ ] **Context managers** for resource cleanup
- [ ] **Descriptive naming** for variables and functions

## Debugging

### Common Issues

1. **CrewAI hanging**: Check reasoning loops and max_attempts
2. **Validation errors**: Verify Pydantic schema compliance
3. **API rate limits**: Implement proper retry logic
4. **Memory issues**: Use generators and proper cleanup

### Debugging Tools

```bash
# Verbose logging
export LOG_LEVEL=DEBUG

# Enable profiling
export ENABLE_PROFILING=true

# Test specific components
uv run pytest tests/unit/tools/test_specific_tool.py -v
```

## Contributing

1. **Fork** the repository
2. **Create** a feature branch
3. **Follow** development standards
4. **Add** comprehensive tests
5. **Submit** a pull request

See [Architecture](architecture.md) for detailed system design and [API Reference](api-reference.md) for complete API documentation.