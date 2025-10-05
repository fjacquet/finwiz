# Design Document

## Overview

This design outlines a comprehensive, systematic approach to modernize the **entire FinWiz codebase** by addressing four core issues: large complex classes, inconsistent testing patterns, CrewAI framework compliance, and insecure HTML generation. The approach prioritizes incremental refactoring that delivers maximum impact while preserving all existing functionality.

**Scope:** This is a codebase-wide modernization effort that will systematically refactor all Python files, tests, crews, and HTML generation code in the FinWiz project.

## Architecture

### Current State Analysis

**Codebase Audit Required:** The following issues exist across the entire codebase:

- Large classes (e.g., `PerplexityAnalysisIntegration` with 975+ lines, and others to be identified)
- Mixed testing approaches (unittest.mock vs pytest-mock) across all test files
- Some crews not following CrewAI decorator patterns
- Complex utility classes mixed with business logic
- HTML generation using insecure string concatenation (f-strings, +, str.format())
- Inconsistent HTML output formatting and encoding

### Target State

After comprehensive modernization:

- **All classes** under 200 lines with single responsibilities
- **100% pytest-mock** usage across entire test suite (0% unittest.mock)
- **All crews** using @agent, @task, @crew decorators with YAML configs
- **All HTML generation** using bs4 (BeautifulSoup) with proper escaping
- Clear separation between utilities and business logic throughout codebase
- Consistent, secure, and maintainable code patterns everywhere

## Components and Interfaces

### 0. Codebase Discovery and Inventory

Before refactoring, we need a complete inventory:

```python
# Discovery script to identify all files needing modernization
class CodebaseAuditor:
    def find_large_classes(self) -> list[tuple[str, int]]:
        """Find all classes >200 lines with their line counts."""
        
    def find_unittest_mock_usage(self) -> list[str]:
        """Find all test files using unittest.mock."""
        
    def find_non_compliant_crews(self) -> list[str]:
        """Find crews not using decorator patterns."""
        
    def find_html_string_generation(self) -> list[str]:
        """Find all files using string concatenation for HTML."""
```

**Output:** Comprehensive inventory document listing all files requiring refactoring.

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
# Before (unittest.mock) - TO BE ELIMINATED FROM ENTIRE CODEBASE
from unittest.mock import patch, MagicMock

def test_api_call():
    with patch('module.api_client') as mock_client:
        mock_client.return_value = {'data': 'test'}
        # test code

# After (pytest-mock) - REQUIRED FOR ALL TESTS
def test_api_call(mocker):
    mock_client = mocker.patch('module.api_client')
    mock_client.return_value = {'data': 'test'}
    # test code
```

**Migration Scope:** All test files in `tests/` directory must be converted.

### 4. HTML Generation Standardization

#### bs4 Migration Pattern

```python
# Before (string concatenation) - TO BE ELIMINATED FROM ENTIRE CODEBASE
def generate_report(title: str, data: dict) -> str:
    html = f"<html><head><title>{title}</title></head>"
    html += f"<body><h1>{title}</h1>"
    html += f"<p>{data['content']}</p></body></html>"
    return html

# After (bs4) - REQUIRED FOR ALL HTML GENERATION
from bs4 import BeautifulSoup, Tag

def generate_report(title: str, data: dict) -> str:
    soup = BeautifulSoup("", "html.parser")
    html = soup.new_tag("html")
    
    head = soup.new_tag("head")
    title_tag = soup.new_tag("title")
    title_tag.string = title  # Automatic escaping
    head.append(title_tag)
    
    body = soup.new_tag("body")
    h1 = soup.new_tag("h1")
    h1.string = title
    body.append(h1)
    
    p = soup.new_tag("p")
    p.string = data['content']  # Automatic XSS protection
    body.append(p)
    
    html.append(head)
    html.append(body)
    soup.append(html)
    
    return soup.prettify(formatter="html")
```

**Migration Scope:** All Python files generating HTML must be converted to use bs4.

**Security Benefits:**

- Automatic HTML entity escaping prevents XSS
- Proper UTF-8 encoding handling
- Well-formed HTML structure guaranteed
- Better code readability and maintainability

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

### Phase 0: Discovery and Inventory (REQUIRED FIRST)

1. **Scan entire codebase** to identify all files needing modernization
2. **Generate inventory report** with:
   - All classes >200 lines (sorted by size)
   - All test files using unittest.mock
   - All crews not using decorator patterns
   - All files using string concatenation for HTML
3. **Prioritize refactoring order** (largest/most critical first)
4. **Create tracking document** for progress monitoring

### Phase 1: Class Decomposition (Codebase-Wide)

1. **Process all identified large classes** (starting with largest)
2. Analyze responsibilities within each class
3. Extract utilities and helper functions first
4. Split business logic into focused classes
5. Update imports and dependencies
6. **Verify no class >200 lines remains** (except documented exceptions)

### Phase 2: CrewAI Standardization (All Crews)

1. **Audit all existing crews** for decorator usage
2. **Convert every crew** to use @agent, @task, @crew patterns
3. Move configuration to YAML files for all crews
4. Update crew initialization code throughout codebase
5. **Verify all crews follow standard structure**

### Phase 3: Testing Migration (Entire Test Suite)

1. **Search entire test suite** for all unittest.mock usage
2. **Convert all test files** to pytest-mock patterns
3. Run test suite after each file conversion
4. **Verify 0% unittest.mock usage** remains
5. Update test documentation

### Phase 4: HTML Generation Migration (All HTML Code)

1. **Identify all Python files** generating HTML
2. **Convert all HTML generation** to use bs4
3. Add beautifulsoup4 to pyproject.toml dependencies
4. **Verify no string concatenation** for HTML remains
5. Update coding standards documentation

### Migration Safety

- **Incremental changes**: One file at a time, but process ALL files
- **Preserve interfaces**: Keep public APIs unchanged during refactoring
- **Continuous testing**: Run tests after each change
- **Progress tracking**: Maintain checklist of completed files
- **Rollback ready**: Each change should be easily reversible
- **Completion verification**: Final audit to ensure 100% coverage

## Success Criteria

### Measurable Outcomes (100% Coverage Required)

- **Class Size**: 0 classes >200 lines (except documented exceptions)
- **Test Consistency**: 100% pytest-mock usage, 0% unittest.mock usage
- **CrewAI Compliance**: 100% of crews use decorator patterns with YAML configs
- **HTML Security**: 100% of HTML generation uses bs4, 0% string concatenation
- **Functionality**: All existing features work unchanged
- **Performance**: No performance regressions

### Quality Gates

- All tests pass (100% pass rate maintained)
- Ruff linting passes (no new violations)
- No increase in complexity metrics
- Documentation updated for all changed components
- Final audit confirms 100% completion of all four modernization goals

### Completion Verification

```bash
# Verify no large classes remain
find src -name "*.py" -exec wc -l {} \; | awk '$1 > 200 {print}'

# Verify no unittest.mock usage remains
grep -r "unittest.mock" tests/

# Verify all crews use decorators
grep -r "@agent\|@task\|@crew" src/finwiz/crews/

# Verify no HTML string concatenation remains
grep -r "f\"<\|\"<.*>\".*+" src/ --include="*.py"

# Verify bs4 is in dependencies
grep "beautifulsoup4" pyproject.toml
```
