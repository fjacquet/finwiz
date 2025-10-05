---
inclusion: always
---

# Code Quality Standards

## Testing Requirements

### Core Rules

- **Mock External Dependencies**: Use `pytest-mock` for LLM APIs, file system, web requests
- **unittest.mock is BANNED**: 4-layer enforcement (ruff, pre-commit, runtime, makefile) prevents its use
- **Fast Execution**: Unit tests must complete in < 5 seconds
- **Independence**: Tests must not depend on execution order or shared state
- **Descriptive Names**: `test_should_generate_report_when_valid_ticker_provided`
- **Behavior Focus**: Test feature outcomes, not implementation details

### unittest.mock Enforcement

**CRITICAL**: `unittest.mock` is completely banned from this codebase.

**Enforcement Layers:**

1. Ruff linting (TID rules) - Automatic detection
2. Pre-commit hook - Blocks commits
3. Runtime blocker - Prevents imports
4. Manual check - `make check-unittest-mock`

**Only Use pytest-mock:**

```python
# ✅ CORRECT
def test_example(mocker):
    mock_obj = mocker.patch('module.function')
    
# ❌ BANNED - Will be blocked
from unittest.mock import patch
```

See `docs/TESTING_ENFORCEMENT.md` for full details.

### Test Structure

```python
class TestStockAnalysis:
    def test_should_return_buy_recommendation_when_strong_fundamentals(self, mocker):
        # Arrange
        mock_api = mocker.patch('finwiz.tools.yahoo_finance_tool.get_stock_data')
        mock_api.return_value = {'pe_ratio': 15, 'growth_rate': 0.25}
        
        # Act
        result = analyze_stock('AAPL')
        
        # Assert
        assert result.recommendation == 'BUY'
        mock_api.assert_called_once_with('AAPL')
```

## Code Standards

### Python Style (Enforced by Ruff)

- **Line Limit**: 110 characters
- **Type Hints**: Required for all public methods and complex functions
- **Imports**: Standard library, third-party, local (grouped with blank lines)
- **Variables**: Descriptive names (`analysis_result` not `ar`)

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

### Documentation

- **Docstrings**: Required for all public classes and methods (Google style)
- **Type Annotations**: Use for clarity and IDE support
- **Examples**: Include usage examples for complex functions

## Security & Configuration

### API Key Management

- **Never Log**: API keys, tokens, or sensitive data
- **Environment Variables**: Use `.env` for local development
- **Validation**: Check API keys at startup with clear error messages
- **Error Messages**: Generic messages that don't expose internal details

### Input Validation

```python
from pydantic import BaseModel, Field, validator

class TickerInput(BaseModel):
    symbol: str = Field(..., regex=r'^[A-Z]{1,5}$', description="Stock ticker symbol")
    
    @validator('symbol')
    def validate_ticker_format(cls, v):
        if not v.isalpha():
            raise ValueError('Ticker must contain only letters')
        return v.upper()
```

## Performance & Architecture

### Async Patterns

- **I/O Operations**: Use `async/await` for API calls, file operations
- **Concurrent Execution**: Use `asyncio.gather()` for parallel tasks
- **Exception Handling**: Wrap async operations in try/except blocks

### Memory Management

- **Large Data**: Process in chunks, use generators for streaming
- **Resource Cleanup**: Use context managers for file operations
- **Caching**: Cache expensive operations with appropriate TTL

### CrewAI Specific

- **Tool Injection**: Use factory patterns for tool sets
- **Schema Validation**: Strict Pydantic models for all crew outputs
- **Configuration**: Separate YAML config from Python implementation
- **Error Recovery**: Implement retry logic for external API failures
