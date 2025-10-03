# Test Fixtures Documentation

## Overview

This directory contains reusable test data and mock responses for the FinWiz test suite. The fixtures are designed to provide realistic, consistent test data while maintaining test isolation and performance.

## Fixture Categories

### Core Fixtures (conftest.py)

#### Financial Data Fixtures
- `fake_client_profile`: Generates realistic client profiles with demographics and investment preferences
- `fake_financial_data`: Creates financial data including portfolio values, income, and investment amounts
- `fake_stock_data`: Generates stock market data with realistic tickers, prices, and metrics
- `fake_portfolio_holdings`: Creates portfolio holdings with decisions and risk assessments
- `fake_investment_recommendations`: Generates investment recommendations across asset classes

#### Timestamp Fixtures
- `fake_timestamps`: Creates consistent timestamp sequences for testing temporal logic
- `fake_html_metadata`: Generates HTML metadata for report testing

#### Mock Fixtures
- `mock_ticker`: Pre-configured yfinance.Ticker mock
- `mock_openai`: Pre-configured OpenAI client mock
- `mock_get`: Pre-configured HTTP GET request mock

### Specialized Fixtures

#### API Response Fixtures (api_responses.py)
```python
# Mock API responses for external services
YAHOO_FINANCE_RESPONSES = {
    "AAPL": {
        "price": 150.25,
        "pe_ratio": 25.4,
        "market_cap": 2500000000000
    }
}

ALPHA_VANTAGE_RESPONSES = {
    "sentiment": {
        "overall_sentiment_score": 0.75,
        "articles": [...]
    }
}
```

#### Crew Configuration Fixtures (crew_configs.py)
```python
# Mock YAML configurations for crew testing
STOCK_CREW_CONFIG = {
    "agents": {
        "market_analyst": {
            "role": "Market Technical Analyst",
            "goal": "Analyze market conditions"
        }
    },
    "tasks": {
        "analysis_task": {
            "description": "Perform technical analysis"
        }
    }
}
```

#### Financial Data Factory (financial_data.py)
```python
class FinancialDataFactory:
    @staticmethod
    def create_stock_data(ticker="AAPL"):
        """Generate realistic stock data for testing"""
        return {
            "ticker": ticker,
            "price": fake.pydecimal(left_digits=3, right_digits=2),
            "volume": fake.random_int(min=1000000, max=100000000),
            "pe_ratio": fake.pydecimal(left_digits=2, right_digits=2)
        }
    
    @staticmethod
    def create_portfolio_data(num_holdings=5):
        """Generate realistic portfolio data"""
        return [
            FinancialDataFactory.create_holding()
            for _ in range(num_holdings)
        ]
```

#### Serialization Helpers (serialization_helpers.py)
```python
class SerializationHelpers:
    @staticmethod
    def create_serializable_usage_metrics():
        """Create serializable UsageMetrics for testing"""
        return {
            "total_tokens": 1000,
            "prompt_tokens": 800,
            "completion_tokens": 200,
            "successful_requests": 1
        }
    
    @staticmethod
    def create_serializable_crew_result():
        """Create serializable crew result for testing"""
        return {
            "output": "Test analysis result",
            "usage_metrics": SerializationHelpers.create_serializable_usage_metrics(),
            "execution_time": 45.2,
            "timestamp": "2025-02-10T10:30:00Z"
        }
```

## Usage Examples

### Basic Fixture Usage
```python
def test_stock_analysis(fake_stock_data):
    # Use pre-generated stock data
    result = analyze_stock(fake_stock_data["ticker"])
    assert result.price == fake_stock_data["price"]
```

### Mock Configuration
```python
def test_api_call(mock_get):
    # Configure mock response
    mock_get.return_value.json.return_value = {"price": 150.25}
    
    # Test API call
    result = fetch_stock_price("AAPL")
    assert result == 150.25
    mock_get.assert_called_once()
```

### Complex Data Generation
```python
def test_portfolio_analysis(fake_data_generator, fake_client_profile, fake_portfolio_holdings):
    # Generate complete test scenario
    html_content = fake_data_generator.generate_session_html(
        fake_client_profile,
        fake_portfolio_holdings,
        {"stocks": ["AAPL"], "etfs": ["SPY"], "crypto": ["BTC"]}
    )
    
    # Test HTML parsing
    result = parse_portfolio_html(html_content)
    assert len(result.holdings) == len(fake_portfolio_holdings)
```

## Fixture Design Principles

### Realistic Data
- Use Faker library for generating realistic financial data
- Maintain logical relationships between data points
- Include edge cases and boundary conditions

### Consistency
- Fixed seeds for reproducible test results
- Consistent data formats across fixtures
- Standardized naming conventions

### Performance
- Lazy loading of expensive fixtures
- Caching of reusable data structures
- Minimal memory footprint

### Isolation
- No shared state between tests
- Independent fixture instances
- Proper cleanup after test execution

## Best Practices

### Fixture Selection
```python
# Good: Use specific fixtures for focused tests
def test_stock_price_calculation(fake_stock_data):
    pass

# Better: Use factory methods for customized data
def test_high_pe_stock_analysis():
    stock_data = FinancialDataFactory.create_stock_data(pe_ratio=50.0)
    pass
```

### Mock Configuration
```python
# Good: Configure mocks with realistic responses
def test_api_integration(mocker):
    mock_api = mocker.patch('module.api_call')
    mock_api.return_value = APIResponseFixtures.get_stock_response("AAPL")
    pass
```

### Data Validation
```python
# Good: Validate fixture data structure
def test_fixture_validity(fake_stock_data):
    assert "ticker" in fake_stock_data
    assert isinstance(fake_stock_data["price"], Decimal)
    assert fake_stock_data["price"] > 0
```

## Maintenance Guidelines

### Adding New Fixtures
1. Create fixture in appropriate category file
2. Document fixture purpose and usage
3. Add example usage in tests
4. Update this README with new fixture information

### Updating Existing Fixtures
1. Maintain backward compatibility when possible
2. Update all dependent tests
3. Document breaking changes
4. Consider deprecation path for major changes

### Performance Monitoring
1. Monitor fixture generation time
2. Optimize expensive fixture creation
3. Use session-scoped fixtures for expensive setup
4. Profile memory usage of large fixtures

## Troubleshooting

### Common Issues

**Fixture Not Found**:
- Check fixture is defined in conftest.py or imported properly
- Verify fixture name spelling and scope

**Inconsistent Test Results**:
- Ensure Faker seed is set for reproducibility
- Check for shared state between fixtures
- Verify fixture isolation

**Performance Issues**:
- Use appropriate fixture scope (function/class/session)
- Cache expensive computations
- Minimize fixture dependencies

**Serialization Errors**:
- Use SerializationHelpers for complex objects
- Ensure all fixture data is JSON serializable
- Handle datetime and Decimal objects properly

## Future Enhancements

### Planned Improvements
- **Dynamic Fixture Generation**: Runtime fixture customization
- **Fixture Validation**: Automatic fixture data validation
- **Performance Optimization**: Advanced caching strategies
- **Documentation Generation**: Automatic fixture documentation

### Integration Enhancements
- **Database Fixtures**: Mock database responses
- **File System Fixtures**: Mock file operations
- **Network Fixtures**: Mock network responses
- **Time Fixtures**: Mock time-dependent operations

This fixture system provides a robust foundation for reliable, maintainable testing while supporting the complex financial analysis requirements of the FinWiz platform.