# Coding Conventions

**Analysis Date:** 2026-02-07

## Naming Patterns

**Files:**

- Python modules: `snake_case.py`
- Test files: `test_*.py` (e.g., `test_backtesting.py`)
- Configuration: `lowercase.yaml` (e.g., `agents.yaml`, `tasks.yaml`)
- Documentation: `UPPERCASE.md` (e.g., `CLAUDE.md`)

**Functions:**

- Functions and methods: `snake_case()` (e.g., `calculate_risk_score()`)
- Private functions: `_leading_underscore()` (e.g., `_safe_get_float()`)
- Async functions: `async def snake_case()` (e.g., `async def validate_data_integration()`)

**Variables:**

- Local variables: `snake_case` (e.g., `composite_score`, `risk_metrics`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`, `DEFAULT_TIMEOUT`)
- Private attributes: `_leading_underscore` (e.g., `self._data_quality_metrics`)

**Types:**

- Classes: `PascalCase` (e.g., `RiskScorer`, `DeepAnalysisOrchestrator`)
- Pydantic models: `PascalCase` (e.g., `FinwizState`, `StockCrewExport`)
- Enums: `PascalCase` for class, `UPPER_SNAKE_CASE` for values
- Type aliases: `PascalCase` (e.g., `ConfigDict`)

## Code Style

**Formatting:**

- Tool: `ruff format`
- Line length: 180 characters (configured in `pyproject.toml`)
- Indent: 4 spaces (no tabs)
- String quotes: Double quotes `"text"` (configured in ruff)
- Docstring code format: Enabled (formats code snippets in docstrings)

**Linting:**

- Tool: `ruff check --fix`
- Rules enabled: `E` (pycodestyle errors), `F` (pyflakes), `W` (warnings), `I` (import sorting), `UP` (pyupgrade), `TID` (tidy imports)
- Rules ignored: `E501` (line too long - handled by formatter), `F841` (unused variable), `W291` (trailing whitespace)
- Per-file ignores: Tests skip `ANN` (annotations), `D100-D103` (docstrings)

## Import Organization

**Order:**

1. `from __future__ import annotations` (if needed for forward references)
2. Standard library imports
3. Third-party imports (sorted alphabetically)
4. Local imports from `finwiz.*` (sorted alphabetically)

**Example:**

```python
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from finwiz.exceptions import DataQualityError
from finwiz.schemas.crew_exports import StockCrewExport
from finwiz.tools.logger import get_logger
```

**Path Aliases:**

- No path aliases configured
- All imports use full module paths: `from finwiz.scoring.risk_scorer import RiskScorer`

## Error Handling

**Patterns:**

- Use custom exceptions from `finwiz.exceptions`:
  - `DataQualityError` - Data validation issues
  - `MissingRequiredFieldError` - Required fields missing
  - `PortfolioRebalancingError` - Rebalancing failures
  - `InsufficientPriceDataError` - Price data unavailable
  - `OptimizationFailedError` - Optimization failures
- Always log errors before raising: `self.logger.error(f"Error: {e}", exc_info=True)`
- Wrap external API calls in try/except
- Return error dictionaries for graceful degradation: `{"error": str(e), "success": False}`
- Use `exc_info=True` in logger.error() for stack traces

**Example:**

```python
from finwiz.exceptions import DataQualityError
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)

def calculate_score(data: dict) -> float:
    try:
        if "required_field" not in data:
            raise DataQualityError("Missing required field")
        return data["required_field"] * 1.5
    except Exception as e:
        logger.error(f"Score calculation failed: {e}", exc_info=True)
        raise
```

## Logging

**Framework:** Standard library `logging` with custom configuration via `finwiz.tools.logger`

**Patterns:**

- Get logger: `from finwiz.tools.logger import get_logger` then `logger = get_logger(__name__)`
- Always use `__name__` for logger names (enables hierarchical logging)
- Log levels:
  - `logger.debug()` - Detailed diagnostic info
  - `logger.info()` - General informational messages
  - `logger.warning()` - Warning messages (non-critical issues)
  - `logger.error()` - Error messages with `exc_info=True`
  - `logger.critical()` - Critical failures

**Example:**

```python
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)

def process_data(ticker: str):
    logger.info(f"Processing {ticker}")
    try:
        result = fetch_data(ticker)
        logger.debug(f"Fetched {len(result)} records")
        return result
    except Exception as e:
        logger.error(f"Failed to process {ticker}: {e}", exc_info=True)
        raise
```

**Configuration:**

- Console handler: `INFO` level, format `"%(asctime)s - %(name)s - %(levelname)s - %(message)s"`
- File handler: Daily rotation in `logs/finwiz.log`, 30-day retention
- Error file handler: `ERROR+` level in `logs/finwiz_error.log`, 10MB rotation

## Comments

**When to Comment:**

- Complex algorithms requiring explanation
- Non-obvious business logic
- Workarounds for third-party library issues
- TODO markers for future improvements (use `TODO:` prefix)
- Phase numbers for refactoring tracking (e.g., `# Phase 2A.3: Uses centralized thresholds`)

**Docstrings:**

- Google-style docstrings for all public functions and classes
- Args, Returns, Raises sections
- Examples for complex functions
- Docstrings required except for tests (per-file ignore: `D100-D103`)

**Example:**

```python
def calculate_composite_score(
    fundamental: float,
    technical: float,
    risk: float,
) -> float:
    """
    Calculate composite score from component scores.

    Weights: 40% fundamental, 30% technical, 30% risk.

    Args:
        fundamental: Fundamental score (0-1)
        technical: Technical score (0-1)
        risk: Risk score (0-1, where 1 = low risk)

    Returns:
        Composite score (0-1)

    Example:
        >>> calculate_composite_score(0.8, 0.7, 0.6)
        0.73
    """
    return 0.4 * fundamental + 0.3 * technical + 0.3 * risk
```

## Function Design

**Size:** Maximum 300 lines per file (enforced by convention, not tooling). Split larger files into focused modules.

**Parameters:**

- Use type hints for all parameters: `def func(ticker: str, data: dict[str, Any]) -> float:`
- Use `dict[str, Any]` for flexible dictionaries
- Use Pydantic models for complex structured data
- Default values after required parameters: `def func(ticker: str, threshold: float = 0.5) -> float:`

**Return Values:**

- Always use type hints: `-> dict[str, Any]`, `-> float`, `-> tuple[float, dict]`
- Return tuples for multiple values: `return score, details`
- Return dictionaries for complex results: `return {"score": 0.85, "grade": "A", "details": {...}}`
- Use Pydantic models for validated return values

**Example:**

```python
def calculate_risk_score(data: dict[str, Any]) -> tuple[float, dict[str, Any]]:
    """Calculate risk score with details."""
    details = {}
    volatility = data.get("volatility", 0.20)
    vol_score = 1.0 if volatility <= 0.10 else 0.8
    details["volatility"] = volatility
    details["volatility_score"] = vol_score
    return vol_score, details
```

## Module Design

**Exports:**

- Use `__all__` to control public API: `__all__ = ["RiskScorer", "calculate_score"]`
- Import from centralized locations: `from finwiz.exceptions import DataQualityError`
- Re-export in `__init__.py` for convenience

**Barrel Files:**

- Used in `__init__.py` for module exports
- Example: `finwiz/exceptions/__init__.py` re-exports from submodules

**Example `__init__.py`:**

```python
from finwiz.scoring.fundamental_scorer import FundamentalScorer
from finwiz.scoring.risk_scorer import RiskScorer
from finwiz.scoring.technical_scorer import TechnicalScorer

__all__ = [
    "FundamentalScorer",
    "RiskScorer",
    "TechnicalScorer",
]
```

## Critical Rules

**unittest.mock BANNED:**

- Enforced by `ruff` via `tool.ruff.lint.flake8-tidy-imports.banned-api`
- Runtime blocker in `tests/conftest_unittest_blocker.py`
- Checked by `make check-unittest-mock`
- Use `pytest-mock` instead: `mocker.patch()`, `mocker.Mock()`

**json.dumps:**

- Always use `default=str` to handle datetime and non-serializable types
- Example: `json.dumps(data, default=str, indent=2)`
- Pydantic models: Use `.model_dump_json()` instead

**Pydantic models:**

- ALL models go in `src/finwiz/schemas/`, not in domain folders
- Use `model_config = {"extra": "forbid"}` for strict validation
- Use `Field()` for validation constraints: `Field(..., ge=0.0, le=1.0)`

**Flow methods:**

- Must return `dict[str, Any]` (CrewAI Flow requirement)
- NEVER use `self.inputs` (deprecated) - use `self.state` instead

**Tool instantiation:**

- Use factory functions from `finwiz.tools.tool_factories` (e.g., `get_stock_crew_tools()`)
- Never instantiate tools directly

**AI Minimalism:**

- Use Python for deterministic tasks (scoring, data collection, synthesis)
- AI only for qualitative reasoning
- When Python and AI disagree, Python wins

## Type Checking

**Tool:** `mypy` with gradual adoption

**Configuration:**

- Enabled for: `finwiz.utils.*`, `finwiz.schemas.*`
- Relaxed for: Tests, third-party libraries without stubs
- Disabled error codes: `import-untyped`, `call-arg`, `attr-defined`, `union-attr`, `operator`, `index`, `var-annotated`

**Pattern:**

```python
from typing import Any

def process_data(ticker: str, data: dict[str, Any]) -> dict[str, Any]:
    """Process data with type hints."""
    result: dict[str, Any] = {}
    score: float = calculate_score(data)
    result["score"] = score
    return result
```

## File Structure

**Maximum file size:** 300 lines

**When to split:**

- Break large files into focused modules
- Example: `flow_state.py` split into `flow_state_models.py` and `flow_state_utils.py`
- Use subdirectories for related modules (e.g., `schemas/quantitative/`)

**Directory patterns:**

- `src/finwiz/` - Source code
- `tests/unit/` - Unit tests
- `tests/integration/` - Integration tests
- `tests/fixtures/` - Test data fixtures
- `.planning/codebase/` - Codebase documentation

---

*Convention analysis: 2026-02-07*
