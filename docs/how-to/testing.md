# Testing Guide

Comprehensive guide to testing FinWiz components and ensuring code quality.

## Testing Philosophy

FinWiz follows a comprehensive testing strategy that emphasizes:

- **Fast Unit Tests**: Mock all external dependencies
- **Reliable Integration Tests**: Test real API interactions
- **Comprehensive Coverage**: Aim for 80%+ code coverage
- **Quality Assurance**: Prevent regressions and ensure reliability

## Testing Framework

### Core Tools

- **pytest**: Primary testing framework
- **pytest-mock**: Mocking framework (unittest.mock is BANNED)
- **pytest-cov**: Coverage measurement
- **faker**: Test data generation

### Banned Practices

**unittest.mock is completely banned** with 4-layer enforcement:

1. **Ruff TID rules** - Automatic detection in linting
2. **Pre-commit hook** - Blocks commits with unittest.mock
3. **Runtime blocker** - Raises ImportError on import
4. **Manual check** - `make check-unittest-mock`

## Test Structure

### Test Organization

```
tests/
├── unit/               # Unit tests (fast, mocked)
│   ├── tools/
│   ├── crews/
│   ├── schemas/
│   └── utils/
├── integration/        # Integration tests (slow, real APIs)
├── fixtures/           # Shared test fixtures
└── conftest.py        # pytest configuration
```

### Naming Conventions

- Test files: `test_{module_name}.py`
- Test classes: `Test{ClassName}`
- Test functions: `test_should_{behavior}_when_{condition}`

## Writing Tests

### Unit Test Pattern

```python
def test_should_return_buy_recommendation_when_strong_metrics(mocker):
    # Arrange - Set up test data and mocks
    mock_api = mocker.patch('finwiz.tools.yahoo_finance_tool.get_data')
    mock_api.return_value = {'pe_ratio': 15, 'growth': 0.25}
    
    # Act - Execute the code under test
    result = analyze_stock('AAPL')
    
    # Assert - Verify the results
    assert result.recommendation == 'BUY'
    mock_api.assert_called_once_with('AAPL')
```

### Mocking External Dependencies

```python
def test_stock_analysis_with_mocked_data(mocker):
    # Mock Yahoo Finance API
    mock_yf = mocker.patch('finwiz.tools.yahoo_finance_tool.yf.Ticker')
    mock_ticker = mocker.Mock()
    mock_ticker.info = {'symbol': 'AAPL', 'marketCap': 3000000000000}
    mock_yf.return_value = mock_ticker
    
    # Mock Alpha Vantage API
    mock_av = mocker.patch('finwiz.tools.alpha_vantage_tool.get_fundamentals')
    mock_av.return_value = {'PE': 25.5, 'EPS': 6.0}
    
    # Test the analysis
    result = analyze_stock('AAPL')
    
    assert result.ticker == 'AAPL'
    assert result.recommendation in ['BUY', 'HOLD', 'SELL']
```

### Testing CrewAI Components

**DO NOT** test full crew execution in unit tests. Instead, test:

```python
def test_should_load_agent_configurations_from_yaml():
    """Test configuration loading without instantiating crew."""
    import yaml
    from pathlib import Path
    
    config_path = Path("src/finwiz/crews/stock_crew/config/agents.yaml")
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    # Verify structure
    assert "stock_analyst" in config
    assert "role" in config["stock_analyst"]

def test_should_validate_required_tools():
    """Test tool configuration without executing crew."""
    from finwiz.crews.stock_crew.stock_crew import StockCrew
    
    crew = StockCrew()
    tools = crew.get_tools_for_asset_class("stock")
    
    # Verify required tools are present
    tool_names = [tool.__class__.__name__ for tool in tools]
    assert "QuantitativeAnalysisTool" in tool_names
    assert "TickerValidationTool" in tool_names
```

## Test Data Generation

### Using Faker

```python
from faker import Faker

fake = Faker()

def test_portfolio_analysis():
    # Generate realistic test data
    ticker = fake.stock_symbol()
    price = fake.pyfloat(min_value=10, max_value=1000, right_digits=2)
    company_name = fake.company()
    
    # Use in test
    result = analyze_holding(ticker, price, company_name)
    assert result is not None
```

### Common Test Fixtures

```python
# conftest.py
import pytest
from faker import Faker

@pytest.fixture
def fake():
    """Faker instance for test data generation."""
    return Faker()

@pytest.fixture
def sample_stock_data():
    """Sample stock data for testing."""
    return {
        'ticker': 'AAPL',
        'price': 150.00,
        'pe_ratio': 25.5,
        'market_cap': 3000000000000
    }

@pytest.fixture
def mock_validation_manager(mocker):
    """Mock validation manager."""
    mock = mocker.Mock()
    mock.validate_crew_output.return_value = mocker.Mock(
        is_valid=True,
        sanitized_data={'ticker': 'AAPL'}
    )
    return mock
```

## Running Tests

### Essential Commands

```bash
# Unit tests only (fast)
uv run pytest -m "not integration"

# Integration tests (requires API keys)
uv run pytest -m integration

# Specific test file
uv run pytest tests/unit/tools/test_yahoo_finance_tool.py

# With coverage
uv run pytest --cov=src/finwiz --cov-report=html

# Verbose output
uv run pytest -v

# Stop on first failure
uv run pytest -x
```

### Test Markers

```python
# Unit test (default)
def test_unit_functionality():
    pass

# Integration test
@pytest.mark.integration
def test_real_api_call():
    pass

# Slow test
@pytest.mark.slow
def test_long_running_process():
    pass
```

## Coverage Requirements

- **Minimum**: 80% code coverage
- **Target**: 90%+ for critical modules
- **Exclusions**: Test files, configuration files

```bash
# Generate coverage report
uv run pytest --cov=src/finwiz --cov-report=html --cov-report=term

# View HTML report
open htmlcov/index.html
```

## Best Practices

### Test Design

1. **Test One Thing**: Each test should verify one specific behavior
2. **Descriptive Names**: Use `test_should_{behavior}_when_{condition}` pattern
3. **Arrange-Act-Assert**: Clear test structure
4. **Independent Tests**: No shared state between tests
5. **Fast Execution**: Unit tests should complete in < 5 seconds

### Mocking Strategy

1. **Mock at Boundaries**: Mock external APIs, not internal functions
2. **Use pytest-mock**: Never use unittest.mock (banned)
3. **Realistic Data**: Mock responses should match real API responses
4. **Verify Interactions**: Assert that mocks were called correctly

### Error Testing

```python
def test_should_handle_invalid_ticker(mocker):
    # Mock API to raise exception
    mock_api = mocker.patch('finwiz.tools.yahoo_finance_tool.get_data')
    mock_api.side_effect = ValueError("Invalid ticker")
    
    # Test error handling
    with pytest.raises(InvalidTickerError):
        analyze_stock('INVALID')
```

## Integration Testing

### API Key Requirements

```bash
# Required for integration tests
export OPENAI_API_KEY="sk-proj-..."
export ALPHA_VANTAGE_API_KEY="..."
export YAHOO_FINANCE_API_KEY="..."
```

### Integration Test Example

```python
@pytest.mark.integration
def test_real_stock_analysis():
    """Integration test with real APIs."""
    result = analyze_stock('AAPL')
    
    assert result.ticker == 'AAPL'
    assert result.confidence_level > 0.0
    assert result.recommendation in ['BUY', 'HOLD', 'SELL']
    assert len(result.data_sources) > 0
```

## Continuous Integration

### Pre-commit Hooks

```bash
# Install pre-commit hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

### CI Pipeline

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          uv run pytest -m "not integration"
          uv run pytest --cov=src/finwiz
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Check PYTHONPATH and module structure
2. **Mock Not Working**: Verify patch target path
3. **Slow Tests**: Check for real API calls, add mocks
4. **Flaky Tests**: Remove shared state, improve isolation

### Debugging Tests

```bash
# Run with debugging
uv run pytest -v -s --tb=long

# Run specific test with debugging
uv run pytest -v -s tests/unit/test_specific.py::test_function

# Use pdb for debugging
uv run pytest --pdb
```

## Related Documentation

- [Development Standards](../explanations/development_standards.md)
- [Code Quality](../how-to/code_quality.md)
- [CrewAI Testing](../explanations/crewai_testing.md)