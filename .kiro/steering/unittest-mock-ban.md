---
inclusion: always
---

# unittest.mock is BANNED ⛔

## CRITICAL RULE

**`unittest.mock` is COMPLETELY BANNED from this codebase.**

This is enforced by 4 layers of protection. Any attempt to use `unittest.mock` will be blocked.

## Why Banned

1. **Consistency**: One mocking approach across entire codebase
2. **Simplicity**: pytest-mock is easier and cleaner
3. **Best Practice**: pytest-mock is the pytest-recommended approach
4. **Maintainability**: Less boilerplate, cleaner tests

## Enforcement Layers

### 1. Ruff Linting (Automatic)

- TID rules in `pyproject.toml` ban all unittest.mock imports
- Runs automatically with `ruff check .`
- Shows clear error messages with pytest-mock alternatives

### 2. Pre-commit Hook (Git)

- Located at `.git/hooks/pre-commit`
- Blocks commits containing unittest.mock
- Shows migration instructions

### 3. Runtime Blocker (Pytest)

- Plugin in `tests/conftest_unittest_blocker.py`
- Raises ImportError if unittest.mock is imported
- Prevents tests from running with unittest.mock

### 4. Manual Check (Makefile)

- Command: `make check-unittest-mock`
- Searches all test files for violations
- Reports line numbers and file names

## Required Pattern

**ALWAYS use pytest-mock:**

```python
def test_example(mocker):
    # Mock external calls
    mock_api = mocker.patch('module.api_call')
    mock_api.return_value = {'data': 'test'}
    
    # Mock objects
    mock_obj = mocker.Mock()
    mock_magic = mocker.MagicMock()
    mock_async = mocker.AsyncMock()
    
    # Test code
    result = function_under_test()
    
    # Verify
    assert result == expected
    mock_api.assert_called_once()
```

## Banned Patterns

**NEVER use these (will be blocked):**

```python
# ❌ BANNED - All of these are blocked
from unittest.mock import Mock
from unittest.mock import MagicMock
from unittest.mock import AsyncMock
from unittest.mock import patch
from unittest.mock import patch as mock_patch
import unittest.mock

# ❌ BANNED - Decorators
@patch('module.function')
def test_example(mock_func):
    pass

# ❌ BANNED - Context managers
def test_example():
    with patch('module.function') as mock_func:
        pass
```

## Quick Migration

| unittest.mock | pytest-mock |
|--------------|-------------|
| `from unittest.mock import Mock` | `mocker.Mock()` |
| `from unittest.mock import MagicMock` | `mocker.MagicMock()` |
| `from unittest.mock import AsyncMock` | `mocker.AsyncMock()` |
| `from unittest.mock import patch` | `mocker.patch()` |
| `@patch('module.func')` | `mocker.patch('module.func')` |
| `with patch('module.func'):` | `mocker.patch('module.func')` |

## Verification Commands

```bash
# Check for violations
make check-unittest-mock

# Run linting (includes TID rules)
ruff check .

# Run tests (runtime blocker active)
uv run pytest

# Try to commit (pre-commit hook active)
git commit -m "Your message"
```

## What Happens If You Try

### Ruff Linting

```bash
$ ruff check tests/unit/test_example.py
TID251 `unittest.mock` is banned: Use pytest-mock instead.
```

### Pre-commit Hook

```bash
$ git commit -m "test"
❌ ERROR: unittest.mock found in test_example.py
   Use pytest-mock instead. Import 'mocker' fixture in test functions.
🚫 Commit blocked: unittest.mock is banned in this project
```

### Runtime Blocker

```python
$ uv run pytest tests/unit/test_example.py
ImportError: 
❌ unittest.mock is BANNED in this project!

✅ Use pytest-mock instead:
   def test_example(mocker):
       mock_obj = mocker.patch('module.function')
```

### Manual Check

```bash
$ make check-unittest-mock
❌ ERROR: unittest.mock found in test files!
tests/unit/test_example.py:9:from unittest.mock import patch
```

## Documentation

- **Full Guide**: `docs/TESTING_ENFORCEMENT.md`
- **Quick Reference**: `docs/UNITTEST_MOCK_BLACKLIST.md`
- **Implementation**: `UNITTEST_MOCK_ENFORCEMENT_SUMMARY.md`
- **Testing Standards**: `.kiro/steering/testing-standards.md`

## Common Patterns

### Mock API Calls

```python
def test_should_fetch_data(mocker):
    mock_api = mocker.patch('finwiz.tools.yahoo_finance_tool.get_data')
    mock_api.return_value = {'symbol': 'AAPL', 'price': 150.0}
    
    result = get_stock_data('AAPL')
    
    assert result['symbol'] == 'AAPL'
    mock_api.assert_called_once_with('AAPL')
```

### Mock File Operations

```python
def test_should_read_file(mocker):
    mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data='content'))
    
    result = read_config('config.txt')
    
    assert result == 'content'
```

### Mock Environment Variables

```python
def test_should_use_env_var(mocker):
    mocker.patch.dict('os.environ', {'API_KEY': 'test_key'})
    
    result = get_api_key()
    
    assert result == 'test_key'
```

### Async Mocking

```python
async def test_should_call_async_function(mocker):
    mock_async = mocker.AsyncMock(return_value='test')
    mocker.patch('module.async_function', mock_async)
    
    result = await call_async_function()
    
    assert result == 'test'
    mock_async.assert_called_once()
```

## Remember

- ✅ **pytest-mock only** - Use `mocker` fixture
- ❌ **unittest.mock banned** - 4 layers prevent its use
- 📚 **Documentation available** - See docs/ directory
- 🔍 **Enforcement active** - Cannot bypass

---

**If you see unittest.mock anywhere, it's a bug. Fix it immediately.**
