# Crew Unit Tests

This directory contains unit tests for individual CrewAI crews.

## Structure

- `stock_crew/` - Tests for stock analysis crew
- `etf_crew/` - Tests for ETF analysis crew  
- `crypto_crew/` - Tests for cryptocurrency analysis crew

## Guidelines

- Each crew should have its own subdirectory
- Test crew agents, tasks, and crew configuration separately
- Mock all external dependencies (APIs, file system, etc.)
- Focus on testing crew logic, not tool functionality
- Use descriptive test names: `test_should_{behavior}_when_{condition}`

## Running Tests

```bash
# Run all crew unit tests
uv run pytest tests/unit/crews/ -v

# Run specific crew tests
uv run pytest tests/unit/crews/stock_crew/ -v
uv run pytest tests/unit/crews/etf_crew/ -v
uv run pytest tests/unit/crews/crypto_crew/ -v
```