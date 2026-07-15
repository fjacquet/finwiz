# Investment Discovery Tools - Unit Test Suite

## Overview

This document provides a comprehensive overview of the unit test suite for the Investment Discovery Tools: the A+ Scoring Tool, the A+ Screening Tool, and the Backtesting Tool.

**Wave 3 Task 10 note:** `APlusScoringTool` and the renamed `APlusScreeningTool`
(finwiz's old `MarketScreeningTool`, tool name now `aplus_screening`) moved to
the central `crewai_custom_tools` package. Their dedicated unit test files
(`test_a_plus_scoring_tool.py`, `test_market_screening_tool.py`) moved with
them — see `crewai_custom_tools`' `tests/test_analytics_aplus_scoring.py` and
`tests/test_analytics_aplus_screening.py`. Only `test_backtesting_tool.py`
(local tool, unaffected by the swap) and
`test_investment_discovery_tools_comprehensive.py` (integration tests across
all three tools, now parsing the central tools' `ok()`/`err()` JSON envelopes
with `parse_tool_result()`) remain in this directory.

## Test Files

### 1. `test_backtesting_tool.py`

Comprehensive tests for the Backtesting Tool covering:

#### Input Validation Tests

- BacktestingInput schema validation
- Parameter range validation (period, capital, etc.)
- Strategy class mapping validation

#### Core Backtesting Tests

- Basic backtesting execution with mocked engines
- Multi-regime analysis functionality
- Market regime identification from benchmark data
- Additional metrics calculation (Sortino, Information Ratio, etc.)

#### Validation Logic Tests

- Strategy performance validation with various scenarios
- High-performing vs poor-performing strategy validation
- Validation scoring and threshold checking
- Edge case handling (no trades, insufficient data)

#### Error Handling Tests

- Backtesting engine failures
- Empty or corrupted benchmark data
- Insufficient historical data scenarios

### 2. `test_investment_discovery_tools_comprehensive.py`

Advanced integration and edge case tests covering:

#### A+ Scoring Tool Advanced Tests

- Extreme market conditions handling
- Edge case asset values (threshold boundaries)
- Confidence calculation with varying data completeness
- Concurrent scoring request handling
- Thread safety validation

#### A+ Screening Tool Advanced Tests

- Large screening universe efficiency (1000+ symbols)
- API failure graceful handling during screening
- Invalid screening criteria edge cases
- Market data caching efficiency validation
- Invalid market region fallback handling

#### Backtesting Tool Advanced Tests

- Complex market regime identification
- Extreme performance scenario validation
- Corrupted benchmark data handling
- Strategy with no trades handling
- Date range calculation validation

#### Integration Tests

- Cross-tool data consistency validation
- Tool chain error handling
- Concurrent tool usage testing
- End-to-end workflow validation

## Key Testing Patterns

### 1. Arrange-Act-Assert Structure

All tests follow the clear AAA pattern for maintainability and readability.

### 2. Mock Usage

- **External API calls**: All external dependencies are mocked using `pytest-mock`
- **Database operations**: Mocked to avoid external dependencies
- **File system operations**: Mocked for fast, isolated testing

### 3. Parametrized Tests

Used extensively for testing multiple scenarios with the same logic:

```python
@pytest.mark.parametrize(
    "asset_type,expected_symbols",
    [
        ("etf", ["SPY", "VOO", "VTI"]),
        ("stock", ["AAPL", "MSFT", "GOOGL"]),
        ("crypto", ["BTC", "ETH", "ADA"]),
    ],
)
```

### 4. Error Scenario Testing

Comprehensive error handling validation:

- Invalid inputs
- API failures
- Data corruption
- Network timeouts
- Resource exhaustion

### 5. Performance Testing

- Large dataset handling
- Concurrent request processing
- Memory usage validation
- Execution time boundaries

## Test Data Management

### Fixtures and Sample Data

- **Sample ETF Data**: Realistic expense ratios, AUM, tracking errors
- **Sample Stock Data**: ROE, revenue growth, debt ratios, market caps
- **Sample Crypto Data**: Market caps, volumes, age, adoption metrics
- **Market Context Data**: VIX levels, inflation rates, interest rate trends

### Mock Data Strategies

- **Known Good Data**: High-quality investments that should score well
- **Known Poor Data**: Low-quality investments that should score poorly
- **Edge Case Data**: Boundary values and threshold testing
- **Corrupted Data**: Invalid, missing, or malformed data

## Quality Assurance

### Code Coverage

- All public methods are tested
- All error paths are covered
- Edge cases and boundary conditions are validated

### Test Isolation

- No shared state between tests
- Each test can run independently
- Deterministic test outcomes

### Performance Requirements

- All tests complete in < 5 seconds total
- No external network calls during testing
- Memory usage remains bounded

## Continuous Integration

### Test Execution

```bash
# Run the investment discovery tool tests that remain local to finwiz
uv run pytest tests/unit/tools/test_backtesting_tool.py \
              tests/unit/tools/test_investment_discovery_tools_comprehensive.py -v

# A+ Scoring / A+ Screening tool tests now live in crewai-custom-tools:
# uv run pytest tests/test_analytics_aplus_scoring.py tests/test_analytics_aplus_screening.py
# (run from a checkout of that package)

# Run with coverage
uv run pytest tests/unit/tools/test_*_tool.py --cov=src/finwiz/tools
```

### Quality Gates

- All tests must pass
- No test execution time > 5 seconds
- All external dependencies must be mocked
- Code follows FinWiz quality standards (ruff compliance)

## Future Enhancements

### Potential Test Additions

1. **Load Testing**: Stress testing with very large datasets
2. **Security Testing**: Input sanitization and injection prevention
3. **Internationalization**: Multi-language support testing
4. **Accessibility**: Ensuring outputs are accessible
5. **Performance Benchmarking**: Regression testing for performance

### Test Maintenance

- Regular review of test data relevance
- Update mocks when external APIs change
- Refactor tests as tools evolve
- Add tests for new features and bug fixes

## Conclusion

The Investment Discovery Tools test suite provides comprehensive coverage of all three core tools with 99 tests covering functionality, edge cases, error handling, and integration scenarios. The tests ensure reliability, performance, and maintainability of the investment discovery system while following FinWiz quality standards and best practices.
