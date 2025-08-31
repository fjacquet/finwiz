---
inclusion: always
---

# FinWiz Technical Standards

## Core Technology Stack

**Framework**: CrewAI Flow with Python 3.10+, managed by `uv` package manager
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
All crews must follow this exact structure:
```
src/finwiz/crews/{crew_name}/
├── {crew_name}.py          # @agent, @task, @crew decorators
└── config/
    ├── agents.yaml         # Agent configurations  
    └── tasks.yaml          # Task definitions
```

### File Organization
- **Python files**: `snake_case.py`
- **Schema files**: `PascalCase.schema.json` 
- **Config files**: `kebab-case.yaml`
- **Import order**: stdlib → third-party → local (blank line separated)

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

## Data Validation & Security

### Pydantic Models (Strict)
All inputs/outputs must use Pydantic v2 with strict validation:
```python
from pydantic import BaseModel, Field

class TickerInput(BaseModel):
    symbol: str = Field(..., pattern=r'^[A-Z]{1,5}$')
    
    model_config = {"str_strip_whitespace": True, "str_upper": True}
```

### Environment Variables (Required)
- `OPENAI_API_KEY`, `SERPER_API_KEY`, `FIRECRAWL_API_KEY`, `ALPHA_VANTAGE_API_KEY`
- Never log API keys or sensitive data
- Fail fast with clear messages if keys missing

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