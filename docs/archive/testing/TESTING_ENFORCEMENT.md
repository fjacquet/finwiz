# Testing Standards Enforcement

## unittest.mock is BANNED

This project **strictly prohibits** the use of `unittest.mock`. We use `pytest-mock` exclusively for all mocking needs.

## Why pytest-mock

1. **Simpler API**: No need for context managers or decorators
2. **Better integration**: Works seamlessly with pytest fixtures
3. **Automatic cleanup**: Mocks are automatically cleaned up after each test
4. **Consistency**: One mocking approach across the entire codebase

## Enforcement Mechanisms

We have multiple layers of enforcement to prevent `unittest.mock` usage:

### 1. Ruff Linting (Automatic)

Ruff is configured to ban `unittest.mock` imports:

```bash
# This will fail if unittest.mock is found
ruff check .
```

Configuration in `pyproject.toml`:

```toml
[tool.ruff.lint.flake8-tidy-imports.banned-api]
"unittest.mock".msg = "Use pytest-mock instead. Import 'mocker' fixture in test functions."
```

### 2. Pre-commit Hook (Git)

A pre-commit hook prevents committing code with `unittest.mock`:

```bash
# Automatically runs on git commit
git commit -m "Your message"
```

The hook is located at `.git/hooks/pre-commit` and is automatically installed.

### 3. Runtime Blocker (Pytest)

A pytest plugin blocks `unittest.mock` imports at test runtime:

```python
# In tests/conftest_unittest_blocker.py
# This raises an ImportError if unittest.mock is imported
```

### 4. Makefile Check (Manual)

Run a manual check anytime:

```bash
make check-unittest-mock
```

## How to Use pytest-mock

### Basic Mocking

```python
# ❌ WRONG - unittest.mock
from unittest.mock import patch, Mock

def test_example():
    with patch('module.function') as mock_func:
        mock_func.return_value = 'test'
        # test code

# ✅ CORRECT - pytest-mock
def test_example(mocker):
    mock_func = mocker.patch('module.function')
    mock_func.return_value = 'test'
    # test code
```

### Mock Objects

```python
# ❌ WRONG
from unittest.mock import Mock, MagicMock

def test_example():
    mock_obj = Mock()
    magic_mock = MagicMock()

# ✅ CORRECT
def test_example(mocker):
    mock_obj = mocker.Mock()
    magic_mock = mocker.MagicMock()
```

### Async Mocking

```python
# ❌ WRONG
from unittest.mock import AsyncMock

async def test_example():
    mock_func = AsyncMock(return_value='test')

# ✅ CORRECT
async def test_example(mocker):
    mock_func = mocker.AsyncMock(return_value='test')
```

### Patching Objects

```python
# ❌ WRONG
from unittest.mock import patch

def test_example():
    with patch.object(MyClass, 'method') as mock_method:
        mock_method.return_value = 'test'

# ✅ CORRECT
def test_example(mocker):
    mock_method = mocker.patch.object(MyClass, 'method')
    mock_method.return_value = 'test'
```

### Multiple Patches

```python
# ❌ WRONG
from unittest.mock import patch

@patch('module.function2')
@patch('module.function1')
def test_example(mock_func1, mock_func2):
    pass

# ✅ CORRECT
def test_example(mocker):
    mock_func1 = mocker.patch('module.function1')
    mock_func2 = mocker.patch('module.function2')
```

## Common Patterns

### Mocking API Calls

```python
def test_should_fetch_stock_data_when_valid_ticker(mocker):
    # Arrange
    mock_api = mocker.patch('finwiz.tools.yahoo_finance_tool.get_data')
    mock_api.return_value = {'symbol': 'AAPL', 'price': 150.0}
    
    # Act
    result = get_stock_data('AAPL')
    
    # Assert
    assert result['symbol'] == 'AAPL'
    mock_api.assert_called_once_with('AAPL')
```

### Mocking File Operations

```python
def test_should_read_config_file(mocker):
    mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data='config data'))
    
    result = read_config('config.txt')
    
    assert result == 'config data'
    mock_open.assert_called_once_with('config.txt', 'r')
```

### Mocking Environment Variables

```python
def test_should_use_api_key_from_env(mocker):
    mocker.patch.dict('os.environ', {'API_KEY': 'test_key'})
    
    result = get_api_key()
    
    assert result == 'test_key'
```

## Troubleshooting

### "unittest.mock is BANNED" Error

If you see this error, you're trying to import `unittest.mock`. Replace it with `pytest-mock`:

1. Remove the `unittest.mock` import
2. Add `mocker` parameter to your test function
3. Use `mocker.patch()` instead of `patch()`

### Pre-commit Hook Not Working

If the pre-commit hook isn't running:

```bash
# Make it executable
chmod +x .git/hooks/pre-commit

# Test it manually
.git/hooks/pre-commit
```

### Ruff Not Catching It

Make sure you have the latest configuration:

```bash
# Update ruff
uv sync

# Run ruff check
ruff check tests/
```

## Migration Guide

If you have existing tests with `unittest.mock`:

1. Remove the import: `from unittest.mock import ...`
2. Add `mocker` parameter: `def test_example(mocker):`
3. Replace `patch()` with `mocker.patch()`
4. Replace `Mock()` with `mocker.Mock()`
5. Remove context managers (`with patch...`)
6. Remove decorators (`@patch...`)

## Questions

See the full testing standards in `docs/testing-standards.md` or the steering rules in `.kiro/steering/testing-standards.md`.

---

**Remember**: unittest.mock is BANNED. Use pytest-mock exclusively.
