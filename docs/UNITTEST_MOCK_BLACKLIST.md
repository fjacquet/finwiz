# unittest.mock is BLACKLISTED ⛔

## Summary

`unittest.mock` is **completely banned** from this codebase. We use `pytest-mock` exclusively.

## Enforcement Layers

### 1. 🔍 Ruff Linting (Automatic)

**Status**: ✅ Configured

Ruff will automatically catch and reject `unittest.mock` imports:

```bash
ruff check .
```

**Configuration** (`pyproject.toml`):

```toml
[tool.ruff.lint]
select = ["E", "F", "W", "I", "UP", "ANN", "D", "TID"]

[tool.ruff.lint.flake8-tidy-imports.banned-api]
"unittest.mock".msg = "Use pytest-mock instead. Import 'mocker' fixture in test functions."
"unittest.mock.Mock".msg = "Use pytest-mock instead. Use 'mocker.Mock()' from the mocker fixture."
"unittest.mock.MagicMock".msg = "Use pytest-mock instead. Use 'mocker.MagicMock()' from the mocker fixture."
"unittest.mock.AsyncMock".msg = "Use pytest-mock instead. Use 'mocker.AsyncMock()' from the mocker fixture."
"unittest.mock.patch".msg = "Use pytest-mock instead. Use 'mocker.patch()' from the mocker fixture."
```

### 2. 🚫 Pre-commit Hook (Git)

**Status**: ✅ Installed

The pre-commit hook prevents committing code with `unittest.mock`:

```bash
# Location
.git/hooks/pre-commit

# Make executable
chmod +x .git/hooks/pre-commit

# Test manually
.git/hooks/pre-commit
```

**What it does**:

- Scans all staged Python files
- Blocks commit if `unittest.mock` is found
- Shows helpful error message with pytest-mock examples

### 3. 🛑 Runtime Blocker (Pytest)

**Status**: ✅ Active

A pytest plugin blocks `unittest.mock` imports at test runtime:

```python
# tests/conftest_unittest_blocker.py
# Raises ImportError if unittest.mock is imported
```

**Imported in**: `tests/conftest.py`

**What it does**:

- Intercepts `unittest.mock` imports
- Raises clear error with migration instructions
- Prevents tests from running with unittest.mock

### 4. ✅ Manual Check (Makefile)

**Status**: ✅ Available

Run a manual check anytime:

```bash
make check-unittest-mock
```

**What it does**:

- Searches all test files for `unittest.mock`
- Reports line numbers and file names
- Exits with error code 1 if found

## Quick Reference

### ❌ BANNED

```python
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from unittest.mock import patch as mock_patch
import unittest.mock
```

### ✅ CORRECT

```python
# Just add mocker parameter to your test
def test_example(mocker):
    mock_obj = mocker.patch('module.function')
    mock_obj.return_value = 'test'
```

## Common Replacements

| unittest.mock | pytest-mock |
|--------------|-------------|
| `from unittest.mock import Mock` | `mocker.Mock()` |
| `from unittest.mock import MagicMock` | `mocker.MagicMock()` |
| `from unittest.mock import AsyncMock` | `mocker.AsyncMock()` |
| `from unittest.mock import patch` | `mocker.patch()` |
| `@patch('module.func')` | `mocker.patch('module.func')` |
| `with patch('module.func'):` | `mocker.patch('module.func')` |

## Migration Steps

1. **Remove** the `unittest.mock` import
2. **Add** `mocker` parameter to test function
3. **Replace** `patch()` with `mocker.patch()`
4. **Replace** `Mock()` with `mocker.Mock()`
5. **Remove** context managers (`with patch...`)
6. **Remove** decorators (`@patch...`)

## Example Migration

### Before (BANNED)

```python
from unittest.mock import patch, Mock

def test_api_call():
    with patch('module.api_client') as mock_client:
        mock_client.return_value = {'data': 'test'}
        result = call_api()
        assert result == {'data': 'test'}
```

### After (CORRECT)

```python
def test_api_call(mocker):
    mock_client = mocker.patch('module.api_client')
    mock_client.return_value = {'data': 'test'}
    result = call_api()
    assert result == {'data': 'test'}
```

## Verification Commands

```bash
# Check for unittest.mock usage
make check-unittest-mock

# Run ruff linting
ruff check .

# Run tests (runtime blocker active)
uv run pytest

# Test pre-commit hook
.git/hooks/pre-commit
```

## Documentation

- Full guide: `docs/TESTING_ENFORCEMENT.md`
- Testing standards: `.kiro/steering/testing-standards.md`
- pytest-mock docs: <https://pytest-mock.readthedocs.io/>

## Why This Matters

1. **Consistency**: One mocking approach across entire codebase
2. **Simplicity**: pytest-mock is easier to use and understand
3. **Maintainability**: Less boilerplate, cleaner tests
4. **Best Practice**: pytest-mock is the pytest-recommended approach

---

**Remember**: If you see `unittest.mock` anywhere, it's a bug. Report it or fix it immediately.
