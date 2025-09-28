# Flow Unit Tests

This directory contains unit tests for flow orchestration and main application logic.

## Structure

- Flow orchestration tests (FinwizFlow)
- Session management tests
- Main application integration tests

## Guidelines

- Test flow state management and transitions
- Mock crew executions and external dependencies
- Test error handling and graceful degradation
- Focus on orchestration logic, not individual crew functionality
- Test flow inputs/outputs and data passing between crews

## Running Tests

```bash
# Run all flow unit tests
uv run pytest tests/unit/flow/ -v
```