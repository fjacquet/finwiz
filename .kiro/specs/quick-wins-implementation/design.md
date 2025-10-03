# Design Document

## Overview

The Quick Wins Implementation introduces five independent, high-impact improvements to the FinWiz codebase that enhance code quality, maintainability, and CrewAI compliance. Each improvement is designed to be implemented incrementally without disrupting existing functionality, following FinWiz's architectural principles of modularity, strict validation, and clear separation of concerns.

The design leverages Python's decorator pattern, factory pattern, and structured logging to create reusable, testable components that enforce best practices at compile-time and runtime. All improvements integrate seamlessly with the existing CrewAI framework and FinWiz's tool ecosystem.

### Design Principles

1. **Non-Breaking Changes**: All improvements maintain backward compatibility with existing crews and tools
2. **Incremental Adoption**: Each quick win can be implemented and tested independently
3. **Compile-Time Safety**: Use decorators and type hints to catch errors before runtime
4. **Centralized Configuration**: Factory patterns centralize tool initialization logic
5. **Observability**: Structured logging provides consistent monitoring across all crews

## Architecture

### System Context

```
┌─────────────────────────────────────────────────────────────┐
│                     FinWiz Application                       │
│                                                              │
│  ┌────────────────┐  ┌────────────────┐  ┌───────────────┐ │
│  │  Stock Crew    │  │  Crypto Crew   │  │   ETF Crew    │ │
│  │                │  │                │  │               │ │
│  │  Uses:         │  │  Uses:         │  │  Uses:        │ │
│  │  - Tool        │  │  - Tool        │  │  - Tool       │ │
│  │    Factories   │  │    Factories   │  │    Factories  │ │
│  │  - Task        │  │  - Task        │  │  - Task       │ │
│  │    Decorators  │  │    Decorators  │  │    Decorators │ │
│  │  - Crew Logger │  │  - Crew Logger │  │  - Crew Logger│ │
│  └────────────────┘  └────────────────┘  └───────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              Report Crew (Final Reporter)              │ │
│  │                                                         │ │
│  │  Uses:                                                  │ │
│  │  - @final_reporter decorator (enforces no tools)       │ │
│  │  - Task Decorators (@sync_task for final tasks)        │ │
│  │  - Crew Logger                                          │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                  Utility Layer                          │ │
│  │                                                         │ │
│  │  - src/finwiz/utils/agent_validators.py                │ │
│  │  - src/finwiz/utils/task_decorators.py                 │ │
│  │  - src/finwiz/utils/logging_helpers.py                 │ │
│  │  - src/finwiz/tools/tool_factories.py                  │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Module Organization

```
src/finwiz/
├── tools/
│   └── tool_factories.py          # NEW: Centralized tool initialization
├── utils/
│   ├── agent_validators.py        # NEW: Agent validation decorators
│   ├── task_decorators.py         # NEW: Task execution decorators
│   └── logging_helpers.py         # NEW: Structured logging utilities
└── crews/
    ├── stock_crew/
    │   └── stock_crew.py          # MODIFIED: Uses factories & decorators
    ├── crypto_crew/
    │   └── crypto_crew.py         # MODIFIED: Uses factories & decorators
    ├── etf_crew/
    │   └── etf_crew.py            # MODIFIED: Uses factories & decorators
    └── report_crew/
        └── report_crew.py         # MODIFIED: Uses @final_reporter decorator
```

## Components and Interfaces

### Component 1: Tool Factory Module

**Location**: `src/finwiz/tools/tool_factories.py`

**Purpose**: Centralize tool initialization logic for all crew types, eliminating code duplication and ensuring consistent tool configuration.

**Interface**:

```python
from crewai.tools import BaseTool

def get_stock_crew_tools(
    include_rag: bool = True,
    include_quantitative: bool = True,
    collection_suffix: str = "stock",
) -> list[BaseTool]:
    """
    Get standardized tool set for Stock Crew.
    
    Args:
        include_rag: Whether to include RAG tools for knowledge retrieval
        include_quantitative: Whether to include quantitative analysis tool
        collection_suffix: Suffix for RAG collection name
        
    Returns:
        List of configured tools for stock analysis
    """
    ...

def get_crypto_crew_tools(
    include_rag: bool = True,
    include_quantitative: bool = True,
    collection_suffix: str = "crypto",
) -> list[BaseTool]:
    """Get standardized tool set for Crypto Crew."""
    ...

def get_etf_crew_tools(
    include_rag: bool = True,
    include_quantitative: bool = True,
    collection_suffix: str = "etf",
) -> list[BaseTool]:
    """Get standardized tool set for ETF Crew."""
    ...
```

**Implementation Details**:
- Each factory function returns a list of BaseTool instances
- Tools are organized by category: core research, quantitative, RAG, schema/contract
- Factory functions call existing helper functions (get_stock_research_tools, get_rag_tools, etc.)
- Schema and contract tools use DirectoryReadTool and FileReadTool for accessing JSON schemas
- All parameters have sensible defaults for easy adoption

**Dependencies**:
- `crewai.tools.BaseTool`
- `crewai_tools.DirectoryReadTool`, `FileReadTool`
- `finwiz.tools.finance_tools` (existing)
- `finwiz.tools.quantitative_analysis_tool` (existing)
- `finwiz.tools.rag_tools` (existing)

### Component 2: Agent Validator Module

**Location**: `src/finwiz/utils/agent_validators.py`

**Purpose**: Enforce architectural constraints on agents at initialization time, specifically preventing final reporters from receiving tools.

**Interface**:

```python
from typing import Callable
from crewai import Agent

class FinalReporterError(Exception):
    """Raised when final reporter has tools."""
    pass

def final_reporter(func: Callable) -> Callable:
    """
    Decorator to enforce final reporter has no tools.
    
    Usage:
        @final_reporter
        @agent
        def investment_reporter(self) -> Agent:
            return Agent(config=..., tools=[])
    
    Raises:
        FinalReporterError: If agent has any tools
    """
    ...
```

**Implementation Details**:
- Decorator wraps agent creation functions
- After agent is created, validates that `agent.tools` is empty
- Raises `FinalReporterError` with descriptive message if tools are found
- Logs successful validation for observability
- Uses `functools.wraps` to preserve function metadata
- Error message includes agent role and tool count for debugging

**Dependencies**:
- `crewai.Agent`
- `functools.wraps`
- `finwiz.tools.logger.get_logger`

### Component 3: Task Decorator Module

**Location**: `src/finwiz/utils/task_decorators.py`

**Purpose**: Explicitly mark tasks as async or sync, preventing common errors where final tasks are incorrectly configured as async.

**Interface**:

```python
from typing import Callable
from crewai import Task

def async_task(func: Callable) -> Callable:
    """
    Decorator for async tasks.
    Automatically sets async_execution=True.
    
    Usage:
        @async_task
        @task
        def research_task(self) -> Task:
            return Task(config=...)
    """
    ...

def sync_task(func: Callable) -> Callable:
    """
    Decorator for synchronous tasks.
    Explicitly marks tasks as synchronous (for final tasks).
    
    Usage:
        @sync_task
        @task
        def final_report_task(self) -> Task:
            return Task(config=...)
    """
    ...
```

**Implementation Details**:
- `async_task` sets `task.async_execution = True` after task creation
- `sync_task` sets `task.async_execution = False` after task creation
- Both decorators log configuration for debugging
- Uses `functools.wraps` to preserve function metadata
- Self-documenting: decorator name clearly indicates execution mode

**Dependencies**:
- `crewai.Task`
- `functools.wraps`
- `finwiz.tools.logger.get_logger`

### Component 4: Type Hint Infrastructure

**Location**: Multiple files across `src/finwiz/`

**Purpose**: Add comprehensive type hints to improve IDE support, catch errors early, and make code self-documenting.

**Configuration**: `mypy.ini` at project root

```ini
[mypy]
python_version = 3.10
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
disallow_incomplete_defs = True
check_untyped_defs = True
warn_redundant_casts = True
warn_unused_ignores = True
strict_optional = True

[mypy-crewai.*]
ignore_missing_imports = True

[mypy-crewai_tools.*]
ignore_missing_imports = True

[mypy-dotenv.*]
ignore_missing_imports = True
```

**Implementation Strategy**:
1. Install mypy as dev dependency: `uv add --dev mypy`
2. Create mypy.ini configuration file
3. Run mypy on individual modules to identify missing type hints
4. Add type hints using Python 3.10+ syntax (e.g., `str | None` instead of `Optional[str]`)
5. Focus on public functions and methods first
6. Gradually expand coverage to internal functions

**Example Type Hint Additions**:

```python
# Before
def get_rag_tools(collection_suffix=None):
    config = DEFAULT_RAG_CONFIG.copy()
    ...

# After
from crewai.tools import BaseTool

def get_rag_tools(collection_suffix: str | None = None) -> list[BaseTool]:
    """Get RAG tools for knowledge retrieval and storage."""
    config = DEFAULT_RAG_CONFIG.copy()
    ...
```

**Dependencies**:
- `mypy` (dev dependency)
- Python 3.10+ type hint syntax

### Component 5: Logging Helper Module

**Location**: `src/finwiz/utils/logging_helpers.py`

**Purpose**: Provide structured, consistent logging across all crews for better observability and debugging.

**Interface**:

```python
from typing import Any

class CrewLogger:
    """Standardized logging for crews."""
    
    def __init__(self, crew_name: str):
        """
        Initialize crew logger.
        
        Args:
            crew_name: Name of the crew for log identification
        """
        ...
    
    def log_start(self, inputs: dict[str, Any]) -> None:
        """
        Log crew execution start.
        
        Args:
            inputs: Input parameters passed to crew
        """
        ...
    
    def log_complete(self, duration: float) -> None:
        """
        Log crew execution completion.
        
        Args:
            duration: Execution duration in seconds
        """
        ...
    
    def log_error(self, error: Exception) -> None:
        """
        Log crew execution error.
        
        Args:
            error: Exception that occurred during execution
        """
        ...
```

**Implementation Details**:
- `CrewLogger` wraps existing `get_logger` functionality
- Each method logs with structured `extra` fields for parsing
- `log_start` includes crew name, input keys, and event type
- `log_complete` includes crew name, duration, and event type
- `log_error` includes crew name, error type, full exception info, and event type
- All logs use consistent event naming: "crew_start", "crew_complete", "crew_error"
- Duration tracking uses `time.time()` for simplicity

**Usage Pattern in Crews**:

```python
from finwiz.utils.logging_helpers import CrewLogger
import time

class StockCrew:
    def __init__(self):
        super().__init__()
        self.logger = CrewLogger("StockCrew")
    
    def kickoff(self, inputs: dict) -> Any:
        """Execute crew with structured logging."""
        self.logger.log_start(inputs)
        start_time = time.time()
        
        try:
            result = super().kickoff(inputs)
            duration = time.time() - start_time
            self.logger.log_complete(duration)
            return result
        except Exception as e:
            self.logger.log_error(e)
            raise
```

**Dependencies**:
- `finwiz.tools.logger.get_logger`
- `typing.Any`

## Data Models

### FinalReporterError

```python
class FinalReporterError(Exception):
    """
    Raised when final reporter has tools.
    
    This exception is raised by the @final_reporter decorator when
    an agent designated as a final reporter is created with tools,
    violating the architectural constraint that final reporters
    should only consume upstream context.
    """
    pass
```

### CrewLogger State

```python
class CrewLogger:
    crew_name: str          # Name of the crew for identification
    logger: logging.Logger  # Underlying logger instance
```

### Tool Factory Return Types

All factory functions return `list[BaseTool]` where `BaseTool` is from `crewai.tools`.

## Error Handling

### Tool Factory Errors

**Scenario**: Tool initialization fails (e.g., missing API key, invalid configuration)

**Handling**:
- Factory functions propagate exceptions from underlying tool constructors
- Crews should handle tool initialization errors in their `__init__` methods
- Existing error handling patterns in crews remain unchanged

### Agent Validator Errors

**Scenario**: Final reporter is created with tools

**Handling**:
```python
try:
    agent = create_final_reporter()
except FinalReporterError as e:
    logger.error(f"Agent validation failed: {e}")
    raise
```

**Error Message Format**:
```
FinalReporterError: Final reporter 'Investment Reporter' must have NO tools. 
Found 3 tools. Final reporters should only consume upstream context.
```

### Task Decorator Errors

**Scenario**: Task creation fails or task object is invalid

**Handling**:
- Decorators assume task creation succeeds
- If task creation fails, exception propagates before decorator logic runs
- No additional error handling needed in decorators

### Type Checking Errors

**Scenario**: mypy detects type inconsistencies

**Handling**:
- Errors are caught at development time, not runtime
- Developer fixes type hints or adds `# type: ignore` comments with justification
- CI/CD pipeline can enforce mypy checks

### Logging Errors

**Scenario**: Logging fails (e.g., disk full, permission denied)

**Handling**:
- Logging errors should not crash crew execution
- Existing logger error handling in `finwiz.tools.logger` handles these cases
- `CrewLogger` methods do not catch exceptions; they rely on underlying logger

## Testing Strategy

### Unit Tests Structure

```
tests/
├── unit/
│   ├── tools/
│   │   └── test_tool_factories.py
│   ├── utils/
│   │   ├── test_agent_validators.py
│   │   ├── test_task_decorators.py
│   │   └── test_logging_helpers.py
│   └── crews/
│       ├── test_stock_crew.py      # Updated to verify factory usage
│       ├── test_crypto_crew.py     # Updated to verify factory usage
│       ├── test_etf_crew.py        # Updated to verify factory usage
│       └── test_report_crew.py     # Updated to verify decorator usage
```

### Test Coverage Requirements

1. **Tool Factories** (test_tool_factories.py):
   - Test each factory function returns correct number of tools
   - Test optional parameters (include_rag, include_quantitative)
   - Test collection_suffix parameter affects RAG tools
   - Test all returned tools are BaseTool instances
   - Mock underlying tool constructors to avoid external dependencies

2. **Agent Validators** (test_agent_validators.py):
   - Test @final_reporter allows agents with no tools
   - Test @final_reporter rejects agents with tools
   - Test error message includes agent role and tool count
   - Test decorator preserves function metadata
   - Test logging on successful validation

3. **Task Decorators** (test_task_decorators.py):
   - Test @async_task sets async_execution=True
   - Test @sync_task sets async_execution=False
   - Test decorators preserve function metadata
   - Test logging on task configuration

4. **Logging Helpers** (test_logging_helpers.py):
   - Test CrewLogger initialization
   - Test log_start includes correct structured fields
   - Test log_complete includes duration
   - Test log_error includes exception info
   - Mock underlying logger to verify calls

5. **Crew Integration Tests** (test_*_crew.py):
   - Test crews initialize with factory-provided tools
   - Test final reporters use @final_reporter decorator
   - Test tasks use appropriate decorators
   - Test crews use CrewLogger for execution tracking
   - Mock external dependencies (APIs, file system)

### Testing Patterns

**Mocking Strategy**:
- Use `pytest-mock` (mocker fixture) for all mocking
- Mock external tool constructors in factory tests
- Mock logger calls in logging helper tests
- Mock Agent and Task creation in decorator tests

**Test Naming Convention**:
```python
def test_should_{expected_behavior}_when_{condition}():
    """Test description."""
    # Arrange
    ...
    # Act
    ...
    # Assert
    ...
```

**Example Test**:
```python
def test_should_return_correct_tools_when_stock_factory_called(mocker):
    """Test stock crew factory returns expected tool set."""
    # Arrange
    mock_stock_tools = mocker.patch('finwiz.tools.finance_tools.get_stock_research_tools')
    mock_stock_tools.return_value = [mocker.Mock(spec=BaseTool)]
    
    # Act
    tools = get_stock_crew_tools(include_rag=False, include_quantitative=False)
    
    # Assert
    assert len(tools) > 0
    assert all(isinstance(t, BaseTool) for t in tools)
    mock_stock_tools.assert_called_once()
```

### Performance Testing

- Unit tests must complete in < 5 seconds per test suite
- No external API calls in unit tests
- No file system operations except mocked ones
- Use in-memory data structures for test fixtures

### Integration Testing

- Integration tests verify end-to-end crew execution with new components
- Mark integration tests with `@pytest.mark.integration`
- Integration tests can be skipped in CI with `pytest -m "not integration"`

## Migration Strategy

### Phase 1: Tool Factories (No Breaking Changes)

1. Create `src/finwiz/tools/tool_factories.py`
2. Implement factory functions
3. Add unit tests for factories
4. Update one crew (e.g., StockCrew) to use factory
5. Test updated crew thoroughly
6. Update remaining crews (CryptoCrew, ETFCrew)
7. Verify all crews pass existing tests

### Phase 2: Agent Validators (No Breaking Changes)

1. Create `src/finwiz/utils/agent_validators.py`
2. Implement @final_reporter decorator
3. Add unit tests for decorator
4. Apply decorator to ReportCrew agents
5. Verify ReportCrew passes existing tests
6. Apply to any other final reporter agents

### Phase 3: Task Decorators (No Breaking Changes)

1. Create `src/finwiz/utils/task_decorators.py`
2. Implement @async_task and @sync_task decorators
3. Add unit tests for decorators
4. Apply decorators to one crew (e.g., StockCrew)
5. Test updated crew thoroughly
6. Apply to remaining crews

### Phase 4: Type Hints (Gradual Adoption)

1. Install mypy: `uv add --dev mypy`
2. Create mypy.ini configuration
3. Run mypy on one module (e.g., tool_factories.py)
4. Add type hints to that module
5. Verify mypy passes for that module
6. Gradually expand to other modules
7. Focus on public APIs first

### Phase 5: Logging Helpers (No Breaking Changes)

1. Create `src/finwiz/utils/logging_helpers.py`
2. Implement CrewLogger class
3. Add unit tests for CrewLogger
4. Update one crew to use CrewLogger
5. Test updated crew thoroughly
6. Update remaining crews

### Rollback Strategy

Each phase is independent and can be rolled back without affecting other phases:

- **Tool Factories**: Revert crew files to use direct tool initialization
- **Agent Validators**: Remove decorator, keep agent definitions unchanged
- **Task Decorators**: Remove decorators, keep task definitions unchanged
- **Type Hints**: Remove type hints, code remains functional
- **Logging Helpers**: Revert to direct logger usage

## Performance Considerations

### Tool Factory Performance

- Factory functions are called once per crew initialization
- No performance impact on crew execution
- Tool initialization time remains unchanged

### Decorator Performance

- Decorators add minimal overhead (< 1ms per agent/task creation)
- Validation logic is simple (checking list length)
- No impact on crew execution performance

### Logging Performance

- Structured logging adds minimal overhead (< 1ms per log call)
- Logging is asynchronous in production
- No impact on crew execution performance

### Type Checking Performance

- Type checking happens at development time, not runtime
- No performance impact on production code
- CI/CD pipeline may take slightly longer (< 30 seconds)

## Security Considerations

### API Key Handling

- Tool factories do not change API key handling
- Existing security patterns remain in place
- No new security vulnerabilities introduced

### Input Validation

- Agent validators enforce architectural constraints
- No user input is processed by validators
- No injection vulnerabilities

### Logging Security

- CrewLogger does not log sensitive data (API keys, credentials)
- Follows existing logging security patterns
- Structured fields do not include PII

## Dependencies

### New Dependencies

- `mypy` (dev dependency only)

### Existing Dependencies

- `crewai` (unchanged)
- `crewai_tools` (unchanged)
- `pytest` (unchanged)
- `pytest-mock` (unchanged)

### Version Compatibility

- Python 3.10+ required (for modern type hint syntax)
- Compatible with current CrewAI version
- No breaking changes to existing dependencies

## Documentation Updates

### Code Documentation

- Add docstrings to all new functions and classes
- Include usage examples in docstrings
- Document decorator behavior and constraints

### README Updates

- Add section on tool factories
- Add section on agent/task decorators
- Add section on structured logging
- Update development setup to include mypy

### Architecture Documentation

- Update architecture diagrams to show new utility modules
- Document decorator patterns and when to use them
- Document factory pattern for tool initialization

## Success Metrics

### Code Quality Metrics

- **Code Consistency**: Improve from 60% to 90%
- **Type Coverage**: Improve from 40% to 80%
- **Test Coverage**: Maintain > 80% coverage
- **CrewAI Compliance**: Improve from 85% to 95%

### Developer Experience Metrics

- **IDE Autocomplete**: Improved with type hints
- **Error Detection**: Earlier error detection with mypy
- **Debugging**: Easier with structured logging
- **Maintainability**: Reduced code duplication with factories

### Performance Metrics

- **Test Execution Time**: < 5 seconds per unit test suite
- **Crew Initialization Time**: No significant change
- **Crew Execution Time**: No significant change
- **CI/CD Pipeline Time**: < 30 seconds additional for mypy

## Future Enhancements

### Potential Improvements

1. **Tool Factory Configuration**: Move tool configuration to YAML files
2. **Decorator Composition**: Create composite decorators for common patterns
3. **Logging Aggregation**: Integrate with centralized logging service
4. **Type Hint Enforcement**: Make mypy checks mandatory in CI/CD
5. **Performance Monitoring**: Add performance metrics to CrewLogger

### Extensibility

- Factory pattern can be extended to other crew types
- Decorator pattern can be applied to other components
- Logging pattern can be extended to other modules
- Type hints can be gradually expanded to entire codebase
