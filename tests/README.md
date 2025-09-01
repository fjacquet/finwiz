# FinWiz Test Organization

## Directory Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── unit/                    # Fast unit tests (< 5 seconds)
│   ├── crews/              # CrewAI crew unit tests
│   ├── tools/              # Tool unit tests with mocked dependencies
│   ├── schemas/            # Pydantic schema validation tests
│   └── orchestrators/      # Flow orchestration unit tests
├── integration/            # Integration tests with external services
├── validation/             # Manual validation scripts (not automated tests)
└── fixtures/               # Test data and mock responses
```

## Test Categories

### Unit Tests (`tests/unit/`)
- **Purpose**: Fast, isolated tests with mocked dependencies
- **Execution**: `uv run pytest tests/unit/`
- **Requirements**: Must complete in < 5 seconds, no external calls
- **Naming**: `test_should_{behavior}_when_{condition}`
- **Coverage**: Includes validation system, portfolio review, and all tool implementations

### Integration Tests (`tests/integration/`)
- **Purpose**: Test interactions with external APIs and services
- **Execution**: `uv run pytest tests/integration/ -m integration`
- **Requirements**: Marked with `@pytest.mark.integration`
- **Note**: Requires valid API keys and network access

### Validation Scripts (`tests/validation/`)
- **Purpose**: Manual validation of full crew workflows
- **Execution**: Run individually as Python scripts
- **Use Case**: End-to-end testing and debugging

## Running Tests

```bash
# All unit tests (default)
uv run pytest

# Specific test category
uv run pytest tests/unit/tools/
uv run pytest tests/unit/crews/

# Integration tests only
uv run pytest -m integration

# Exclude integration tests
uv run pytest -m "not integration"

# Run with coverage
uv run pytest --cov=src/finwiz

# Verbose output
uv run pytest -v
```

## Test Standards

### Mocking Requirements
- Mock all external API calls using `pytest-mock`
- Mock file system operations
- Mock LLM API calls (OpenAI, etc.)

### Test Structure
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

### Fixtures Usage
- Use shared fixtures from `conftest.py`
- Create domain-specific fixtures in test modules
- Keep test data realistic but sanitized
- Use `APITestMocks` class for standardized mock setups
- Leverage Faker for dynamic test data generation

### Key Test Files
- `test_portfolio_review.py`: Portfolio analysis and decision logic
- `test_validation_infrastructure.py`: Validation system components
- `test_alpha_vantage_news_tool.py`: Alpha Vantage news integration
- `test_standardized_sentiment_tool.py`: Sentiment analysis tools
- `test_contract_*.py`: Schema contract validation