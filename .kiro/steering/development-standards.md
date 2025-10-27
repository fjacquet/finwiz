# FinWiz Development Standards

Comprehensive development standards for the FinWiz AI-powered financial analysis platform.

## Core Technology Stack

**Framework**: CrewAI Flow with Python 3.12+, managed by `uv` package manager  
**Code Quality**: Ruff (110 char limit), pytest with pytest-mock (unittest.mock BANNED)  
**Data Validation**: Pydantic v2 strict mode, schemas in `src/finwiz/schemas/`

### Essential Commands

```bash
uv run python src/finwiz/main.py    # Run application
uv run pytest -m "not integration"  # Unit tests only
ruff check . && ruff format .        # Lint and format
make check-unittest-mock             # Check for banned unittest.mock
```

### unittest.mock is BANNED ⛔

**CRITICAL**: `unittest.mock` is completely banned with 4-layer enforcement:

1. **Ruff TID rules** - Automatic detection in linting
2. **Pre-commit hook** - Blocks commits with unittest.mock
3. **Runtime blocker** - Raises ImportError on import
4. **Manual check** - `make check-unittest-mock`

**Only pytest-mock is allowed:**

```python
# ✅ CORRECT - Always use this
def test_example(mocker):
    mock_obj = mocker.patch('module.function')
    mock_obj.return_value = 'test'

# ❌ BANNED - Will be blocked by enforcement
from unittest.mock import patch, Mock
```

**Docs**: `docs/TESTING_ENFORCEMENT.md`, `docs/UNITTEST_MOCK_BLACKLIST.md`

## Architecture Patterns

### CrewAI Structure (Required)

All crews must follow this exact structure:

```
src/finwiz/crews/{crew_name}/
├── {crew_name}.py          # @agent, @task, @crew decorators
└── config/
    ├── agents.yaml         # Agent configurations  
    └── tasks.yaml          # Task definitions
```

### Project Layout

```
src/finwiz/
├── crews/           # AI agent crews (crypto, stock, etf, report)
├── tools/           # Domain-specific analysis tools
├── schemas/         # Pydantic models with strict validation
├── orchestrators/   # Flow coordination logic
├── templates/       # HTML report templates
└── main.py         # CrewAI Flow entry point

docs/schemas/        # JSON schemas with examples
tests/              # Test suite with pytest
```

### File Organization

- **Python files**: `snake_case.py`
- **Schema files**: `PascalCase.schema.json`
- **Config files**: `kebab-case.yaml`
- **Import order**: stdlib → third-party → local (blank line separated)
- **One class per file** for crews and major components

### Code Standards

```python
# Required: Type hints for public methods
async def analyze_stock(ticker: str) -> StockAnalysis:
    """Analyze stock with proper error handling."""
    try:
        # Use context managers for resources
        async with httpx.AsyncClient() as client:
            data = await client.get(f"/api/{ticker}")
        return StockAnalysis.model_validate(data.json())
    except ValidationError as e:
        raise InvalidTickerError(f"Invalid data for {ticker}") from e
```

## Core Principles

**Most important rule from Yoda**: Do. Or do not. There is no try. There is no MOST.

**Execute with precision**: Write code that works correctly the first time. No shortcuts, no "try" - either implement properly or don't implement at all.

**Code with intention**: Every line must serve a purpose. Every test must validate behavior. Every function must have a clear responsibility. Half-measures lead to technical debt, bugs, and maintenance nightmares.

**Commit only working code**: If it doesn't pass tests, if it has TODO comments, if it lacks proper error handling - it's not ready. Complete the work or don't submit it.

## Testing Requirements

### Mandatory Patterns

- **Mock all external calls**: APIs, file system, network requests
- **Test naming**: `test_should_{behavior}_when_{condition}`
- **Structure**: Arrange-Act-Assert with clear assertions
- **Performance**: < 5 seconds per test suite
- **Independence**: No shared state between tests

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

- **Mock all external dependencies**: APIs, file system, LLM calls, network requests
- **Fast execution**: Unit tests < 5 seconds per suite
- **Independence**: No shared state between tests
- **Descriptive naming**: `test_should_{behavior}_when_{condition}`
- **Arrange-Act-Assert structure**: Clear test organization

## Data Validation & Security

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

### Environment Variables (Required)

- `OPENAI_API_KEY`, `SERPER_API_KEY`, `FIRECRAWL_API_KEY`, `ALPHA_VANTAGE_API_KEY`
- Never log API keys or sensitive data
- Fail fast with clear messages if keys missing

### API Key Management

- **Never log**: API keys, tokens, or sensitive financial data
- **Environment variables only**: Use `.env` for local development
- **Startup validation**: Check all required keys with clear error messages
- **Error messages**: Generic to users, detailed internally

### Input Validation

- All inputs must use strict Pydantic models
- Sanitize ticker symbols, amounts, dates
- Never log personal financial information
- Validate all external API responses before processing

## Performance Patterns

### Async Operations (Required for I/O)

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

## Python Style (Ruff Enforced)

- **Line limit**: 110 characters
- **Type hints**: Required for all public methods
- **Import order**: stdlib → third-party → local (blank line separated)
- **Naming**: Descriptive variables (`analysis_result` not `ar`)
- **Functions**: Pure functions preferred, avoid side effects

## CrewAI Compliance

- **Tool factories**: Use `get_{asset_class}_crew_tools()` patterns
- **Schema validation**: Strict Pydantic models for all crew outputs
- **Flow state**: Use `Flow[StateModel]` with structured Pydantic models
- **Final reporters**: Must have empty tools list (enforced by `@final_reporter`)
- **Configuration**: Separate YAML config from Python implementation

## Tool Development

### Tool Factory Pattern

```python
# tools/{domain}_tools.py
def get_{domain}_tools() -> list:
    """Return curated tool set for domain analysis."""
    return [tool1(), tool2(), tool3()]
```

### External API Integration

- Always implement retry logic with exponential backoff
- Mock all external calls in tests using pytest-mock
- Handle rate limits and API errors gracefully
- Cache expensive operations when appropriate

## Import Standards

```python
# Standard library
import asyncio
from typing import Dict, List, Optional

# Third-party
from crewai import Agent, Task
from pydantic import BaseModel

# Local imports
from finwiz.schemas.common import BaseAnalysis
from finwiz.tools.finance_tools import get_market_data
```

## Financial Analysis Standards

### Asset-Specific Requirements

- **Cryptocurrencies**: Technical analysis, volatility patterns, regulatory risks
- **Stocks**: Fundamental analysis (10-K filings), technical indicators, sector comparisons  
- **ETFs**: Expense ratios, tracking error, holdings diversification

### Standardized Outputs (Required)

```python
# Risk Assessment
risk_score: int = Field(..., ge=1, le=10, description="1=Very Low, 10=Very High")
risk_factors: List[str] = Field(..., description="Specific risk categories")

# Investment Recommendations
recommendation: str = Field(..., pattern="^(BUY|HOLD|SELL)$")
confidence: float = Field(..., ge=0.0, le=1.0)
time_horizon: str = Field(..., pattern="^(SHORT|MEDIUM|LONG)$")
rationale: str = Field(..., min_length=50, description="Detailed reasoning")
```

### Data Quality Standards

- Always cite data sources with as-of dates
- Use multiple providers for validation when possible
- Acknowledge data limitations and potential inaccuracies
- Use standardized financial terminology
- Include relevant benchmarks and peer comparisons

## Product Requirements

### Core Mission

AI-powered financial research platform using autonomous CrewAI agents to analyze cryptocurrencies, stocks, and ETFs with actionable investment recommendations.

### Output Standards

- **Recommendations**: Clear BUY/HOLD/SELL with rationale and time horizon
- **Risk Assessment**: Standardized 1-10 scale with systematic vs idiosyncratic risks
- **Report Format**: HTML with PDF conversion, multi-language support (French default)
- **Data Sources**: Always cite sources with as-of dates

### Quality Requirements

- Real-time market data integration
- Professional financial terminology
- Regulatory compliance considerations
- Portfolio context and diversification analysis
- Autonomous agent execution with minimal user input

## Pre-Commit Quality Checklist

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

## Essential Commands

```bash
# Run tests (unit only)
uv run pytest -m "not integration"

# Check for banned unittest.mock
make check-unittest-mock

# Lint and format
ruff check . && ruff format .

# Type checking
mypy src/finwiz/
```

---

**Version**: 1.0  
**Last Updated**: 2025-10-26  
**Consolidated from**: finwiz-guide.md, tech.md, quality.md, structure.md