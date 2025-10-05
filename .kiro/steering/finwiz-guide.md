---
inclusion: always
---

# FinWiz Development Guide

## Core Technology Stack

**Framework**: CrewAI Flow with Python 3.12+, managed by `uv` package manager  
**Code Quality**: Ruff (110 char limit), pytest with pytest-mock  
**Data Validation**: Pydantic v2 strict mode, schemas in `src/finwiz/schemas/`

### Essential Commands

```bash
uv run python src/finwiz/main.py    # Run application
uv run pytest -m "not integration"  # Unit tests only
ruff check . && ruff format .        # Lint and format
```

## Architecture Patterns

### CrewAI Structure (Required)

```
src/finwiz/crews/{crew_name}/
├── {crew_name}.py          # @agent, @task, @crew decorators
└── config/
    ├── agents.yaml         # Agent configurations  
    └── tasks.yaml          # Task definitions
```

### Code Organization

- **Python files**: `snake_case.py`
- **Schema files**: `PascalCase.schema.json`
- **Config files**: `kebab-case.yaml`
- **Import order**: stdlib → third-party → local (blank line separated)
- **One class per file** for crews and major components

### Pydantic Models (Strict Validation)

```python
from pydantic import BaseModel, Field

class TickerInput(BaseModel):
    symbol: str = Field(..., pattern=r'^[A-Z]{1,5}$')
    
    model_config = {"str_strip_whitespace": True, "str_upper": True}
```

## Testing Standards

### Core Requirements

- **Mock all external calls**: Use `pytest-mock`, never `unittest.mock`
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

## Security & Environment

### API Keys (Critical)

- **Required**: `OPENAI_API_KEY`, `SERPER_API_KEY`, `FIRECRAWL_API_KEY`, `ALPHA_VANTAGE_API_KEY`
- **Storage**: Use `.env` file for local development (never commit)
- **Validation**: Check all keys at startup with clear error messages
- **Never log**: API keys, tokens, or sensitive data

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
