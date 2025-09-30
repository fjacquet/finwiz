# Design Document

## Overview

This design outlines a simple, incremental approach to modernize the FinWiz codebase by addressing three core issues: large complex classes, inconsistent testing patterns, and CrewAI framework compliance. The approach prioritizes minimal changes that deliver maximum impact while preserving all existing functionality.

## Architecture

### Current State Analysis

The codebase currently has:
- Large classes (like `PerplexityAnalysisIntegration` with 975+ lines)
- Mixed testing approaches (unittest.mock vs pytest-mock)
- Some crews not following CrewAI decorator patterns
- Complex utility classes mixed with business logic

### Target State

After modernization:
- All classes under 200 lines with single responsibilities
- Consistent pytest-mock usage across all tests
- All crews using @agent, @task, @crew decorators with YAML configs
- Clear separation between utilities and business logic

## Components and Interfaces

### 1. Class Decomposition Strategy

#### Large Class Identification
```python
# Example: Current PerplexityAnalysisIntegration (975 lines)
# Split into:
class PerplexityClient:           # API communication (50-100 lines)
class PerplexityParser:           # Response parsing (50-100 lines)  
class PerplexityErrorHandler:     # Error handling (50-100 lines)
class PerplexityLogger:           # Logging utilities (50-100 lines)
```

#### Decomposition Rules
- **Single Responsibility**: Each class does one thing well
- **Composition over Inheritance**: Use dependency injection for shared functionality
- **Utility Extraction**: Move helper functions to separate modules

### 2. CrewAI Pattern Standardization

#### Standard Crew Structure
```
src/finwiz/crews/{crew_name}/
├── {crew_name}.py          # @agent, @task, @crew decorators only
└── config/
    ├── agents.yaml         # Agent definitions
    └── tasks.yaml          # Task definitions
```

#### Decorator Pattern
```python
from crewai import Agent, Task, Crew
from crewai.flow import flow

class StockCrew:
    @agent
    def analyst(self) -> Agent:
        return Agent(config=self.agents_config['analyst'])
    
    @task  
    def analyze_stock(self) -> Task:
        return Task(config=self.tasks_config['analyze_stock'])
    
    @crew
    def crew(self) -> Crew:
        return Crew(agents=[self.analyst()], tasks=[self.analyze_stock()])
```

### 3. Testing Standardization

#### pytest-mock Migration Pattern
```python
# Before (unittest.mock)
from unittest.mock import patch, MagicMock

def test_api_call():
    with patch('module.api_client') as mock_client:
        mock_client.return_value = {'data': 'test'}
        # test code

# After (pytest-mock)
def test_api_call(mocker):
    mock_client = mocker.patch('module.api_client')
    mock_client.return_value = {'data': 'test'}
    # test code
```

## Data Models

### Configuration Models
```python
from pydantic import BaseModel

class CrewConfig(BaseModel):
    """Simple crew configuration."""
    agents_config: dict
    tasks_config: dict
    
class ToolConfig(BaseModel):
    """Simple tool configuration."""
    api_key: str | None = None
    timeout: int = 30
    retries: int = 3
```

### Refactored Class Interfaces
```python
class APIClient(Protocol):
    """Simple interface for API clients."""
    async def call(self, endpoint: str, params: dict) -> dict: ...

class DataParser(Protocol):
    """Simple interface for data parsers."""
    def parse(self, raw_data: str) -> dict: ...
```

## Error Handling

### Simple Error Strategy
- Keep existing error handling patterns
- Extract error handling logic from large classes into focused error handler classes
- Maintain current graceful fallback behavior (especially for Perplexity integration)

```python
class PerplexityErrorHandler:
    """Focused error handling for Perplexity integration."""
    
    def handle_api_error(self, error: Exception) -> dict:
        """Simple error handling with fallback."""
        if "rate limit" in str(error).lower():
            return self._create_rate_limit_response()
        return self._create_generic_error_response(error)
```

## Testing Strategy

### Migration Approach
1. **Identify unittest.mock usage**: Search codebase for `unittest.mock` imports
2. **Convert incrementally**: Replace with pytest-mock patterns file by file
3. **Validate behavior**: Ensure tests still pass with same coverage

### Test Structure
```python
# Standard test pattern
def test_should_do_something_when_condition(mocker):
    # Arrange
    mock_dependency = mocker.patch('module.dependency')
    mock_dependency.return_value = expected_data
    
    # Act
    result = function_under_test()
    
    # Assert
    assert result == expected_result
    mock_dependency.assert_called_once()
```

## Implementation Plan

### Phase 1: Class Decomposition
1. Identify classes >200 lines (starting with largest)
2. Analyze responsibilities within each class
3. Extract utilities and helper functions first
4. Split business logic into focused classes
5. Update imports and dependencies

### Phase 2: CrewAI Standardization  
1. Audit existing crews for decorator usage
2. Convert crews to use @agent, @task, @crew patterns
3. Move configuration to YAML files
4. Update crew initialization code

### Phase 3: Testing Migration
1. Search for all unittest.mock usage
2. Convert tests to pytest-mock patterns
3. Run test suite to ensure no regressions
4. Update test documentation

### Migration Safety
- **Incremental changes**: One class/crew/test file at a time
- **Preserve interfaces**: Keep public APIs unchanged during refactoring
- **Continuous testing**: Run tests after each change
- **Rollback ready**: Each change should be easily reversible

## Success Criteria

### Measurable Outcomes
- **Class Size**: No classes >200 lines
- **Test Consistency**: 100% pytest-mock usage (0% unittest.mock)
- **CrewAI Compliance**: All crews use decorator patterns with YAML configs
- **Functionality**: All existing features work unchanged
- **Performance**: No performance regressions

### Quality Gates
- All tests pass
- Ruff linting passes
- No increase in complexity metrics
- Documentation updated for changed components