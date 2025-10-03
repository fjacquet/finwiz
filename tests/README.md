# FinWiz Test Organization

## Directory Structure

```bash
tests/
├── conftest.py              # Shared fixtures and configuration
├── unit/                    # Fast unit tests (< 5 seconds)
│   ├── crews/              # CrewAI crew unit tests
│   │   ├── stock_crew/     # Stock analysis crew tests
│   │   ├── etf_crew/       # ETF analysis crew tests
│   │   └── crypto_crew/    # Cryptocurrency analysis crew tests
│   ├── flow/               # Flow orchestration and main app tests
│   ├── tools/              # Tool unit tests with mocked dependencies
│   ├── schemas/            # Pydantic schema validation tests
│   ├── orchestrators/      # Flow orchestration unit tests
│   └── utils/              # Utility function tests
├── integration/            # Integration tests with external services
│   └── core_analysis/      # Core analysis integration tests
├── performance/            # Performance and benchmark tests
├── validation/             # Manual validation scripts (not automated tests)
└── fixtures/               # Test data and mock responses
```

## Test Categories

### Unit Tests (`tests/unit/`)

- **Purpose**: Fast, isolated tests with mocked dependencies
- **Execution**: `uv run pytest tests/unit/`
- **Requirements**: Must complete in < 5 seconds, no external calls
- **Naming**: `test_should_{behavior}_when_{condition}`
- **Coverage**: Includes validation system, portfolio review, schema contract validation, and all tool implementations

### Integration Tests (`tests/integration/`)

- **Purpose**: Test interactions with external APIs and services
- **Execution**: `uv run pytest tests/integration/ -m integration`
- **Requirements**: Marked with `@pytest.mark.integration`
- **Note**: Requires valid API keys and network access

### Core Analysis Integration Tests (`tests/integration/core_analysis/`)

- **Purpose**: Test core analysis crew integration and data flow
- **Execution**: `uv run pytest tests/integration/core_analysis/ -m integration`
- **Coverage**: Crew output validation, data integration, freshness validation

### Contract Tests (`tests/test_contract_*.py`)
- **Purpose**: Validate Pydantic schema contracts and data boundaries
- **Execution**: `uv run pytest tests/test_contract_*.py`
- **Coverage**: 
  - `test_contract_reporter.py`: ReporterInput aggregate schema with `extra='forbid'` validation
  - `test_contract_stock.py`: Stock-specific schemas (TenKInsight, MarketSentiment)
  - `test_contract_risk.py`: RiskAssessmentStandardized with 0-5 scale validation
- **Requirements**: Ensure strict schema compliance and prevent data drift

### Validation Scripts (`tests/validation/`)
- **Purpose**: Manual validation of full crew workflows
- **Execution**: Run individually as Python scripts
- **Use Case**: End-to-end testing and debugging

## Running Tests

```bash
# All unit tests (default)
uv run pytest

# Specific test categories
uv run pytest tests/unit/tools/
uv run pytest tests/unit/crews/
uv run pytest tests/unit/crews/stock_crew/
uv run pytest tests/unit/flow/

# Integration tests only
uv run pytest -m integration

# Core analysis integration tests
uv run pytest tests/integration/core_analysis/ -m integration

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
- `test_contract_reporter.py`: ReporterInput schema contract validation with strict Pydantic validation
- `test_contract_stock.py`: Stock-specific schema validation (TenKInsight, MarketSentiment)
- `test_contract_risk.py`: RiskAssessmentStandardized schema validation and bounds checking
- `test_ai_reasoning_integration.py`: AI reasoning integration tests for crew execution
- `test_ai_reasoning_configuration.py`: AI agent reasoning configuration validation

## Test Coverage Stabilization

### Current Status
The test suite has undergone comprehensive stabilization to address critical issues:

- **Import Errors**: All test files now import successfully without module errors
- **Mocking Standardization**: Converted from `unittest.mock` to `pytest-mock` exclusively
- **JSON Serialization**: Implemented custom serializers for CrewAI objects (UsageMetrics, datetime)
- **Test Isolation**: Improved test independence and eliminated shared state issues
- **Coverage Infrastructure**: Established comprehensive coverage measurement and reporting

### Critical Fixes Implemented
1. **Serialization Issues**: Custom JSON encoders for non-serializable objects
2. **Mock Consistency**: Standardized mocking patterns across all test files
3. **Error Handling**: Robust error handling with clear failure messages
4. **Performance**: All unit tests execute in under 5 seconds
5. **AI Reasoning Tests**: Comprehensive tests for AI agent reasoning capabilities

### Coverage Targets
- **Overall Coverage**: Minimum 80% code coverage
- **Critical Modules**: 90% coverage for core analysis components
- **New Code**: No coverage regression below current baseline
- **Reporting**: HTML and terminal coverage reports available