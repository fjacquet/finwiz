# Core Analysis Integration Tests

This directory contains integration tests for core analysis functionality.

## Structure

- Crew output validation and contracts
- Data integration and flow between crews
- Freshness validation integration
- Cross-crew consistency validation
- Error handling and recovery

## Guidelines

- Test real integration between components
- Use realistic test data and scenarios
- Test data flow from crews through integration system
- Test error scenarios and recovery mechanisms
- Mock only external APIs, not internal components

## Running Tests

```bash
# Run all core analysis integration tests
uv run pytest tests/integration/core_analysis/ -v -m integration

# Run specific integration test categories
uv run pytest tests/integration/core_analysis/test_crew_output_validation.py -v
uv run pytest tests/integration/core_analysis/test_freshness_validation_integration.py -v
```