---
title: Mypy Type Checking Standards
inclusion: always
---

# Mypy Type Checking Standards for FinWiz

## Overview

Mypy is a static type checker for Python that helps find bugs by enforcing type hints without running code. This document defines standards for using mypy in the FinWiz codebase.

## Core Principles

1. **Type Safety First**: All public functions and methods must have complete type annotations
2. **Gradual Adoption**: Use per-module configuration to enable strict checking incrementally
3. **Practical Strictness**: Balance type safety with development velocity
4. **Clear Documentation**: Type hints serve as inline documentation

## Configuration

### Project Configuration (pyproject.toml)

```toml
[tool.mypy]
python_version = "3.12"
warn_return_any = true
warn_unused_configs = true
warn_redundant_casts = true
warn_unused_ignores = true
strict_equality = true
check_untyped_defs = true
show_error_codes = true
show_column_numbers = true
pretty = true

# Import discovery
namespace_packages = true
explicit_package_bases = true

# Caching
cache_dir = ".mypy_cache"
sqlite_cache = true

# Exclude patterns
exclude = [
    "^build/",
    "^dist/",
    "^.venv/",
    "^tests/fixtures/",
]

# Per-module overrides for gradual adoption
[[tool.mypy.overrides]]
module = "finwiz.utils.*"
disallow_untyped_defs = true
disallow_incomplete_defs = true

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false
allow_untyped_defs = true

[[tool.mypy.overrides]]
module = [
    "pandas.*",
    "numpy.*",
    "crewai.*",
    "backtrader.*",
]
ignore_missing_imports = true
```

### Alternative: INI Configuration (mypy.ini)

```ini
[mypy]
python_version = 3.12
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
show_error_codes = True
exclude = (?x)(
    ^build/
    | ^dist/
    | ^\.venv/
  )

[mypy-finwiz.utils.*]
disallow_untyped_defs = True
disallow_incomplete_defs = True

[mypy-tests.*]
disallow_untyped_defs = False
allow_untyped_defs = True

[mypy-pandas.*]
ignore_missing_imports = True

[mypy-numpy.*]
ignore_missing_imports = True

[mypy-crewai.*]
ignore_missing_imports = True
```

## Type Annotation Standards

### Function Annotations (Required)

All public functions must have complete type annotations:

```python
from typing import Optional, List, Dict, Any

# ✅ CORRECT - Complete annotations
def calculate_score(
    ticker: str,
    data: Dict[str, Any],
    weights: Optional[Dict[str, float]] = None
) -> float:
    """Calculate composite score with optional weights."""
    if weights is None:
        weights = {"fundamental": 0.6, "technical": 0.4}
    return sum(data.get(k, 0.0) * v for k, v in weights.items())

# ❌ WRONG - Missing return type
def calculate_score(ticker: str, data: Dict[str, Any]):
    return 0.85

# ❌ WRONG - Missing parameter types
def calculate_score(ticker, data):
    return 0.85
```

### Class Annotations (Required)

```python
from typing import ClassVar, Protocol
from dataclasses import dataclass

# ✅ CORRECT - Dataclass with type hints
@dataclass
class StockAnalysis:
    ticker: str
    composite_score: float
    grade: str
    recommendation: str
    confidence: float = 0.8
    
    # Class variable
    _cache: ClassVar[Dict[str, 'StockAnalysis']] = {}
    
    def is_buy_recommendation(self) -> bool:
        """Check if recommendation is BUY."""
        return self.recommendation == "BUY"

# ✅ CORRECT - Protocol for structural typing
class Analyzer(Protocol):
    """Protocol for asset analyzers."""
    
    def analyze(self, ticker: str) -> Dict[str, Any]:
        """Analyze asset and return results."""
        ...
```

### Variable Annotations

```python
from typing import List, Dict, Optional

# ✅ CORRECT - Explicit type for empty containers
tickers: List[str] = []
scores: Dict[str, float] = {}
result: Optional[str] = None

# ✅ CORRECT - Type inferred from assignment
ticker = "AAPL"  # Type: str
score = 0.85  # Type: float

# ❌ AVOID - Ambiguous empty container
results = []  # Mypy can't infer element type
```

## Handling Third-Party Libraries

### Libraries Without Type Stubs

```python
# In pyproject.toml or mypy.ini
[[tool.mypy.overrides]]
module = [
    "crewai.*",
    "backtrader.*",
    "yfinance.*",
]
ignore_missing_imports = true
```

### Using typing_extensions for Backports

```python
import sys

if sys.version_info >= (3, 13):
    from typing import TypeIs
else:
    from typing_extensions import TypeIs

def is_str(x: object) -> TypeIs[str]:
    """Type guard for string checking."""
    return isinstance(x, str)
```

## Type Narrowing and Guards

### Using isinstance for Type Narrowing

```python
from typing import Union

def process_value(value: Union[int, str]) -> str:
    """Process value with type narrowing."""
    if isinstance(value, int):
        # Mypy knows value is int here
        return str(value * 2)
    else:
        # Mypy knows value is str here
        return value.upper()
```

### Custom Type Guards

```python
from typing import TypeGuard, List, Any

def is_string_list(val: List[Any]) -> TypeGuard[List[str]]:
    """Check if list contains only strings."""
    return all(isinstance(x, str) for x in val)

def process_strings(items: List[Any]) -> None:
    """Process list if it contains only strings."""
    if is_string_list(items):
        # Mypy knows items is List[str] here
        for item in items:
            print(item.upper())  # OK - item is str
```

## Handling Optional and None

### Explicit None Checks

```python
from typing import Optional

# ✅ CORRECT - Explicit None check
def increment(x: Optional[int]) -> int:
    if x is None:
        return 0
    # Mypy knows x is int here
    return x + 1

# ❌ WRONG - No None check
def increment(x: Optional[int]) -> int:
    return x + 1  # Error: Cannot add None and int
```

### Using Optional vs Union

```python
from typing import Optional, Union

# These are equivalent
def func1(x: Optional[str]) -> None: ...
def func2(x: Union[str, None]) -> None: ...
def func3(x: str | None) -> None: ...  # Python 3.10+

# Prefer the shortest form
def func(x: str | None) -> None: ...  # ✅ BEST (Python 3.10+)
```

## Error Suppression (Use Sparingly)

### Inline Type Ignore

```python
# ✅ ACCEPTABLE - Specific error code
result = legacy_function()  # type: ignore[no-untyped-call]

# ✅ ACCEPTABLE - With explanation
data = external_api.get_data()  # type: ignore[attr-defined]  # API lacks stubs

# ❌ AVOID - Generic ignore without code
result = some_function()  # type: ignore
```

### Function-Level Suppression

```python
import typing

@typing.no_type_check
def legacy_function():
    """Old function without type hints - to be refactored."""
    return complex_untyped_logic()
```

### Module-Level Configuration

```python
# At top of file
# mypy: disallow-any-generics
# mypy: warn-return-any

# Or to disable checking for entire file (avoid if possible)
# mypy: ignore-errors
```

## Using Any (Avoid When Possible)

```python
from typing import Any, Dict

# ❌ AVOID - Too permissive
def process_data(data: Any) -> Any:
    return data.transform()

# ✅ BETTER - More specific
def process_data(data: Dict[str, Any]) -> Dict[str, float]:
    return {k: float(v) for k, v in data.items()}

# ✅ BEST - Fully typed
def process_data(data: Dict[str, str]) -> Dict[str, float]:
    return {k: float(v) for k, v in data.items()}
```

## Generics and Type Variables

```python
from typing import TypeVar, Generic, List

T = TypeVar('T')

class Stack(Generic[T]):
    """Generic stack implementation."""
    
    def __init__(self) -> None:
        self._items: List[T] = []
    
    def push(self, item: T) -> None:
        """Push item onto stack."""
        self._items.append(item)
    
    def pop(self) -> T:
        """Pop item from stack."""
        return self._items.pop()

# Usage with type checking
int_stack: Stack[int] = Stack()
int_stack.push(42)  # OK
int_stack.push("string")  # Error: Argument has incompatible type
```

## Protocols for Structural Typing

```python
from typing import Protocol

class Drawable(Protocol):
    """Protocol for drawable objects."""
    
    def draw(self) -> None:
        """Draw the object."""
        ...

class Circle:
    """Circle implementation."""
    
    def draw(self) -> None:
        print("Drawing circle")

class Square:
    """Square implementation."""
    
    def draw(self) -> None:
        print("Drawing square")

def render(shape: Drawable) -> None:
    """Render any drawable shape."""
    shape.draw()

# Both work without explicit inheritance
render(Circle())  # OK
render(Square())  # OK
```

## Running Mypy

### Command Line

```bash
# Check entire project
mypy src/finwiz

# Check specific module
mypy --module finwiz.utils.datetime_utils

# Check specific package
mypy --package finwiz.scoring

# With strict mode
mypy --strict src/finwiz/utils

# Show error codes
mypy --show-error-codes src/

# Generate HTML report
mypy --html-report ./mypy-report src/
```

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        args: [--config-file=pyproject.toml]
        additional_dependencies:
          - types-requests
          - types-PyYAML
```

### CI/CD Integration

```yaml
# .github/workflows/type-check.yml
name: Type Check

on: [push, pull_request]

jobs:
  mypy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install mypy
          pip install -r requirements.txt
      - name: Run mypy
        run: mypy src/finwiz
```

## Gradual Adoption Strategy

### Phase 1: Core Utilities (Current)

```toml
[[tool.mypy.overrides]]
module = "finwiz.utils.*"
disallow_untyped_defs = true
disallow_incomplete_defs = true
```

### Phase 2: Schemas and Models

```toml
[[tool.mypy.overrides]]
module = "finwiz.schemas.*"
disallow_untyped_defs = true
disallow_incomplete_defs = true
```

### Phase 3: Business Logic

```toml
[[tool.mypy.overrides]]
module = [
    "finwiz.scoring.*",
    "finwiz.quantitative.*",
]
disallow_untyped_defs = true
```

### Phase 4: Full Strict Mode

```toml
[tool.mypy]
strict = true
```

## Common Patterns

### Async Functions

```python
from typing import List
import asyncio

async def fetch_data(ticker: str) -> Dict[str, Any]:
    """Fetch data asynchronously."""
    await asyncio.sleep(1)
    return {"ticker": ticker, "price": 150.0}

async def fetch_multiple(tickers: List[str]) -> List[Dict[str, Any]]:
    """Fetch data for multiple tickers."""
    tasks = [fetch_data(t) for t in tickers]
    return await asyncio.gather(*tasks)
```

### Context Managers

```python
from typing import Iterator
from contextlib import contextmanager

@contextmanager
def database_connection(url: str) -> Iterator[Connection]:
    """Context manager for database connection."""
    conn = connect(url)
    try:
        yield conn
    finally:
        conn.close()
```

### Decorators

```python
from typing import TypeVar, Callable, Any
from functools import wraps

F = TypeVar('F', bound=Callable[..., Any])

def retry(max_attempts: int = 3) -> Callable[[F], F]:
    """Decorator to retry function on failure."""
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
            return None  # Never reached
        return wrapper  # type: ignore[return-value]
    return decorator
```

## Debugging Type Issues

### Using reveal_type

```python
from typing import reveal_type

def process(value: int | str) -> None:
    reveal_type(value)  # Revealed type is "int | str"
    
    if isinstance(value, int):
        reveal_type(value)  # Revealed type is "int"
        print(value + 1)
```

### Understanding Error Messages

```python
# Error: Argument 1 to "func" has incompatible type "str"; expected "int"
func("123")  # Wrong type

# Error: Incompatible return value type (got "None", expected "int")
def func() -> int:
    return None  # Wrong return type

# Error: "str" has no attribute "append"
text = "hello"
text.append("world")  # Wrong method for str
```

## Best Practices

### DO ✅

- Add type hints to all public functions and methods
- Use specific types instead of `Any` when possible
- Enable strict checking for new modules
- Use protocols for structural typing
- Document complex type relationships
- Run mypy in CI/CD pipeline
- Use type guards for runtime type checking

### DON'T ❌

- Use `Any` as a default type
- Ignore type errors without understanding them
- Use `# type: ignore` without error codes
- Skip type hints for "simple" functions
- Disable type checking for entire modules
- Mix typed and untyped code in same module
- Forget to update type hints when refactoring

## Resources

- **Official Mypy Documentation**: https://mypy.readthedocs.io/
- **Python Typing Module**: https://docs.python.org/3/library/typing.html
- **typing_extensions**: https://github.com/python/typing_extensions
- **Type Hints Cheat Sheet**: https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html

## Quick Reference

| Type | Usage | Example |
|------|-------|---------|
| `int`, `str`, `float`, `bool` | Basic types | `x: int = 42` |
| `List[T]` | List of type T | `items: List[str] = []` |
| `Dict[K, V]` | Dictionary | `scores: Dict[str, float] = {}` |
| `Optional[T]` | T or None | `result: Optional[str] = None` |
| `Union[T1, T2]` | T1 or T2 | `value: Union[int, str]` |
| `T \| None` | T or None (3.10+) | `value: str \| None` |
| `Any` | Any type (avoid) | `data: Any` |
| `Callable[[Args], Return]` | Function type | `func: Callable[[int], str]` |
| `TypeVar` | Generic type variable | `T = TypeVar('T')` |
| `Protocol` | Structural typing | `class P(Protocol): ...` |

---

**Version**: 1.0  
**Created**: 2025-11-15  
**Purpose**: Standardize mypy usage and type checking in FinWiz  
**Source**: Context7 mypy documentation
