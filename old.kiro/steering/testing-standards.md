---
inclusion: always
---

# Testing Standards for FinWiz

Comprehensive testing standards for FinWiz development.

## Core Testing Principles

### 1. Mock All External Dependencies

- **Always use `pytest-mock`** (never `unittest.mock`)
- **unittest.mock is BANNED** - 4 enforcement layers prevent its use
- Mock APIs, file system, network requests, LLM calls
- No real external calls in tests
- Deterministic test execution

### unittest.mock Enforcement (CRITICAL)

**unittest.mock is COMPLETELY BANNED from this codebase.**

We have 4 layers of enforcement:

1. **Ruff Linting** - TID rules automatically catch unittest.mock imports
2. **Pre-commit Hook** - Blocks commits containing unittest.mock
3. **Runtime Blocker** - Raises ImportError if unittest.mock is imported
4. **Manual Check** - `make check-unittest-mock` for verification

**Why Banned:**

- Consistency: One mocking approach across entire codebase
- Simplicity: pytest-mock is easier and cleaner
- Best Practice: pytest-mock is the pytest-recommended approach

**Enforcement Commands:**

```bash
# Check for violations
make check-unittest-mock

# Ruff will catch it
ruff check .

# Pre-commit blocks it
git commit -m "test"

# Runtime blocker prevents import
uv run pytest
```

**Migration Required:**

```python
# ❌ BANNED - Will be blocked by all 4 enforcement layers
from unittest.mock import Mock, patch, MagicMock, AsyncMock

# ✅ REQUIRED - Only acceptable approach
def test_example(mocker):
    mock_obj = mocker.patch('module.function')
    mock_obj.return_value = 'test'
```

**Documentation:**

- Full guide: `docs/TESTING_ENFORCEMENT.md`
- Quick reference: `docs/UNITTEST_MOCK_BLACKLIST.md`
- Implementation: `UNITTEST_MOCK_ENFORCEMENT_SUMMARY.md`

### 2. Fast Execution

- Unit tests must complete in < 5 seconds per suite
- No network calls, no database access
- Use in-memory data structures
- Parallel test execution when possible

### 3. Test Independence

- No shared state between tests
- Each test can run in isolation
- No test execution order dependencies
- Clean setup and teardown

### 4. Descriptive Naming

- Pattern: `test_should_{behavior}_when_{condition}`
- Clear, readable test names
- Self-documenting tests

## Test Structure

### Arrange-Act-Assert Pattern

```python
def test_should_return_buy_recommendation_when_strong_metrics(mocker):
    # Arrange - Set up test data and mocks
    mock_api = mocker.patch('finwiz.tools.yahoo_finance_tool.get_data')
    mock_api.return_value = {'pe_ratio': 15, 'growth': 0.25}
    
    # Act - Execute the code under test
    result = analyze_stock('AAPL')
    
    # Assert - Verify the results
    assert result.recommendation == 'BUY'
    mock_api.assert_called_once_with('AAPL')
```

## Test Organization

### Directory Structure

```
tests/
├── unit/               # Unit tests (fast, mocked)
│   ├── tools/
│   ├── crews/
│   ├── schemas/
│   └── utils/
├── integration/        # Integration tests (slow, real APIs)
├── fixtures/           # Shared test fixtures
└── conftest.py        # pytest configuration
```

### Test File Naming

- Test files: `test_{module_name}.py`
- Test classes: `Test{ClassName}`
- Test functions: `test_should_{behavior}_when_{condition}`

## Mocking Strategy

### Using pytest-mock

```python
def test_should_fetch_stock_data_when_valid_ticker(mocker):
    # Mock external API call
    mock_get = mocker.patch('finwiz.tools.yahoo_finance_tool.yf.Ticker')
    mock_ticker = mocker.Mock()
    mock_ticker.info = {'symbol': 'AAPL', 'price': 150.0}
    mock_get.return_value = mock_ticker
    
    # Test the function
    result = get_stock_data('AAPL')
    
    # Verify
    assert result['symbol'] == 'AAPL'
    assert result['price'] == 150.0
    mock_get.assert_called_once_with('AAPL')
```

### Common Mocking Patterns

**Mock API Calls**:

```python
mock_api = mocker.patch('module.api_call')
mock_api.return_value = {'data': 'value'}
```

**Mock File Operations**:

```python
mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data='content'))
```

**Mock Environment Variables**:

```python
mocker.patch.dict('os.environ', {'API_KEY': 'test_key'})
```

**Mock Datetime**:

```python
mock_now = mocker.patch('datetime.datetime')
mock_now.now.return_value = datetime(2025, 3, 10)
```

## Test Data Generation

### Using Faker

```python
from faker import Faker

fake = Faker()

def test_portfolio_analysis():
    # Generate realistic test data
    ticker = fake.stock_symbol()
    price = fake.pyfloat(min_value=10, max_value=1000, right_digits=2)
    company_name = fake.company()
    
    # Use in test
    result = analyze_holding(ticker, price, company_name)
    assert result is not None
```

### Faker Patterns

```python
# Stock data
ticker = fake.stock_symbol()  # 'AAPL', 'GOOGL', etc.
price = fake.pyfloat(min_value=10, max_value=1000)
company = fake.company()

# Financial data
revenue = fake.pyfloat(min_value=1e6, max_value=1e9)
pe_ratio = fake.pyfloat(min_value=5, max_value=50)
market_cap = fake.pyfloat(min_value=1e9, max_value=1e12)

# Dates
date = fake.date_between(start_date='-1y', end_date='today')
```

## Test Requirements

### Coverage Target

- **Minimum**: 80% code coverage
- **Target**: 90%+ for critical modules
- **Tools**: pytest-cov for coverage measurement

```bash
# Run with coverage
uv run pytest --cov=src/finwiz --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Test Categories

**Unit Tests** (mark: default):

```python
def test_should_calculate_score():
    # Fast, isolated unit test
    pass
```

**Integration Tests** (mark: `integration`):

```python
@pytest.mark.integration
def test_should_fetch_real_stock_data():
    # Slow, requires API keys
    pass
```

**Slow Tests** (mark: `slow`):

```python
@pytest.mark.slow
def test_should_backtest_strategy():
    # Long-running test
    pass
```

## Running Tests

### Essential Commands

```bash
# Unit tests only (fast)
uv run pytest -m "not integration"

# Integration tests (requires API keys)
uv run pytest -m integration

# Specific test file
uv run pytest tests/unit/tools/test_alternative_finder_tool.py

# Specific test function
uv run pytest tests/unit/tools/test_alternative_finder_tool.py::test_should_find_alternatives

# With coverage
uv run pytest --cov=src/finwiz --cov-report=html

# Verbose output
uv run pytest -v

# Stop on first failure
uv run pytest -x

# Run in parallel (requires pytest-xdist)
uv run pytest -n auto
```

## Fixtures

### Common Fixtures

```python
# conftest.py
import pytest
from faker import Faker

@pytest.fixture
def fake():
    """Faker instance for test data generation."""
    return Faker()

@pytest.fixture
def sample_ticker():
    """Sample ticker for testing."""
    return "AAPL"

@pytest.fixture
def sample_price_data():
    """Sample price data for testing."""
    return {
        'current_price': 150.0,
        'high': 155.0,
        'low': 145.0,
        'volume': 1000000
    }

@pytest.fixture
def mock_validation_manager(mocker):
    """Mock validation manager."""
    mock = mocker.Mock()
    mock.validate_crew_output.return_value = mocker.Mock(
        is_valid=True,
        sanitized_data={'ticker': 'AAPL'}
    )
    return mock
```

## Best Practices

### 1. Test One Thing

```python
# Good ✅
def test_should_return_buy_when_strong_fundamentals():
    result = analyze_stock(strong_fundamentals)
    assert result.recommendation == 'BUY'

# Bad ❌
def test_stock_analysis():
    # Tests multiple things
    result = analyze_stock(data)
    assert result.recommendation == 'BUY'
    assert result.risk_score < 3
    assert result.confidence > 0.8
```

### 2. Use Descriptive Assertions

```python
# Good ✅
assert result.grade == 'A+', f"Expected A+ grade, got {result.grade}"

# Bad ❌
assert result.grade == 'A+'
```

### 3. Test Edge Cases

```python
def test_should_handle_missing_data():
    result = analyze_stock(ticker=None)
    assert result.error == 'Invalid ticker'

def test_should_handle_empty_price_history():
    result = calculate_targets(price_history=[])
    assert result.confidence_level < 0.5
```

### 4. Mock at the Right Level

```python
# Good ✅ - Mock at the boundary
mock_api = mocker.patch('finwiz.tools.yahoo_finance_tool.get_data')

# Bad ❌ - Mock too deep
mock_requests = mocker.patch('requests.get')
```

## Anti-Patterns (Avoid)

❌ **Using unittest.mock** - BANNED with 4-layer enforcement (ruff, pre-commit, runtime, makefile)
❌ **Real API calls** - Mock all external dependencies
❌ **Shared state** - Each test should be independent
❌ **Long tests** - Keep unit tests fast (< 5 seconds)
❌ **Unclear names** - Use descriptive test names
❌ **Testing implementation** - Test behavior, not implementation
❌ **No assertions** - Every test must have assertions
❌ **Brittle tests** - Don't test internal details

### unittest.mock Violations

If you see `unittest.mock` anywhere in the codebase:

1. **It's a bug** - Report or fix immediately
2. **Cannot be committed** - Pre-commit hook blocks it
3. **Cannot pass linting** - Ruff TID rules catch it
4. **Cannot run tests** - Runtime blocker prevents import

**Quick Fix:**

```python
# Remove this line
from unittest.mock import patch

# Add mocker parameter
def test_example(mocker):
    mock_obj = mocker.patch('module.function')
```

## Test Quality Checklist

Before committing tests:

1. ✅ **No unittest.mock** - Use pytest-mock exclusively (ENFORCED)
2. ✅ **All external dependencies mocked**
3. ✅ **Fast execution** (< 5 seconds for unit tests)
4. ✅ **Independent tests** (no shared state)
5. ✅ **Descriptive names** (test_should_X_when_Y)
6. ✅ **Arrange-Act-Assert** structure
7. ✅ **Clear assertions** with messages
8. ✅ **Edge cases covered**
9. ✅ **No real API calls**
10. ✅ **Proper fixtures** used
11. ✅ **Coverage** maintained (80%+)

### Pre-Commit Verification

```bash
# Check for unittest.mock violations
make check-unittest-mock

# Run linting (includes TID rules)
ruff check .

# Run tests (runtime blocker active)
uv run pytest

# Try to commit (pre-commit hook active)
git commit -m "Your message"
```

## CrewAI Testing Standards (CRITICAL)

### The Problem with CrewAI Testing

**CRITICAL LESSON LEARNED**: Do not attempt to unit test full CrewAI crew execution. It leads to hanging tests and is impractical.

When testing CrewAI crews, attempting to instantiate and execute crews in unit tests causes:

1. **Hanging tests** - Tests timeout or never complete
2. **Complex mocking** - Requires mocking the entire CrewAI framework, LLM calls, and agent initialization
3. **Slow execution** - Even with mocks, initialization takes 10+ seconds per test
4. **Brittle tests** - Tests break when CrewAI internals change

### The Solution: Test What Matters

Focus unit tests on **testable business logic**, not framework execution:

#### ✅ DO Test

1. **Configuration loading** - Verify YAML files load correctly
2. **Tool routing logic** - Test `get_tools_for_asset_class()` method logic
3. **Input validation** - Test parameter validation (asset_class, ticker)
4. **Method existence** - Verify required methods exist
5. **File existence** - Verify configuration files exist

#### ❌ DON'T Test

1. **Crew execution** - Don't call `crew.kickoff()` in unit tests
2. **Agent creation** - Don't instantiate agents with `@agent` decorator
3. **Task execution** - Don't execute tasks with `@task` decorator
4. **LLM calls** - Don't mock OpenAI/LLM responses
5. **Full workflow** - Don't test end-to-end crew workflows

### CrewAI Testing Examples

#### ❌ BAD - Tries to test crew execution

```python
def test_crew_execution(self, mocker):
    """This will hang or timeout!"""
    crew = DeepAnalysisCrew()  # Hangs during initialization
    
    # Mock everything (impractical)
    mocker.patch.object(crew, "asset_analyst", return_value=mock_agent)
    mocker.patch.object(crew, "crew", return_value=mock_crew)
    
    # This will still hang or be very slow
    result = crew.kickoff(inputs={"ticker": "AAPL", "asset_class": "stock"})
```

#### ✅ GOOD - Tests configuration and logic

```python
def test_should_load_agent_configurations_from_yaml(self):
    """Fast, focused test of configuration loading."""
    import yaml
    from pathlib import Path
    
    config_path = Path("src/finwiz/crews/deep_analysis/config/agents.yaml")
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    # Verify structure
    assert "asset_analyst" in config
    assert "role" in config["asset_analyst"]

def test_should_validate_asset_class_parameter(self):
    """Test validation logic without instantiating crew."""
    valid_asset_classes = ["stock", "etf", "crypto"]
    
    for asset_class in valid_asset_classes:
        assert asset_class.lower() in ["stock", "etf", "crypto"]
    
    invalid_asset_classes = ["bond", "option"]
    for asset_class in invalid_asset_classes:
        assert asset_class.lower() not in ["stock", "etf", "crypto"]
```

### CrewAI Testing Strategy

#### Unit Tests (Fast, Focused)

- Test configuration loading from YAML
- Test tool routing logic
- Test input validation
- Test method existence
- **Run time: < 1 second per test**

#### Integration Tests (Slow, Optional)

- Test actual crew execution with real LLM calls
- Mark with `@pytest.mark.integration`
- Require API keys
- **Run time: 30+ seconds per test**
- **Only run manually or in CI**

#### Manual Testing

- Test full workflows manually
- Use actual tickers and real data
- Verify output quality
- **This is where you validate the crew actually works**

### CrewAI Testing Implementation Pattern

```python
class TestDeepAnalysisCrew:
    """Test cases for DeepAnalysisCrew - focused on configuration and logic."""
    
    def test_should_load_agent_configurations_from_yaml(self):
        """Test configuration loading without instantiating crew."""
        import yaml
        from pathlib import Path
        
        config_path = Path("src/finwiz/crews/deep_analysis/config/agents.yaml")
        with open(config_path) as f:
            config = yaml.safe_load(f)
        
        required_agents = ["asset_analyst", "investment_reporter"]
        for agent_name in required_agents:
            assert agent_name in config
            assert "role" in config[agent_name]
            assert "goal" in config[agent_name]
    
    def test_should_have_required_methods(self):
        """Test method existence without calling them."""
        from finwiz.crews.deep_analysis.deep_analysis import DeepAnalysisCrew
        
        assert hasattr(DeepAnalysisCrew, "get_tools_for_asset_class")
        assert hasattr(DeepAnalysisCrew, "kickoff")
        assert hasattr(DeepAnalysisCrew, "asset_analyst")
```

### Why This Approach Works

1. **Fast** - Tests complete in < 1 second
2. **Reliable** - No hanging or timeouts
3. **Maintainable** - Tests don't break when CrewAI updates
4. **Practical** - Tests verify what actually matters
5. **Clear** - Easy to understand what's being tested

### When to Use Integration Tests

Only create integration tests when:

1. You need to verify actual LLM behavior
2. You're testing a critical production workflow
3. You have time for slow tests (30+ seconds)
4. You're willing to maintain complex mocks or use real API calls

Mark them clearly:

```python
@pytest.mark.integration
@pytest.mark.slow
def test_should_execute_full_crew_workflow():
    """Integration test - requires API keys and is slow."""
    # This is acceptable for integration tests
    crew = DeepAnalysisCrew()
    result = crew.kickoff(inputs={"ticker": "AAPL", "asset_class": "stock"})
    assert result is not None
```

## Example Test Suite

```python
"""
Unit tests for AlternativeFinder tool.
"""
import pytest
from finwiz.tools.alternative_finder_tool import AlternativeFinder, HoldingProfile

class TestAlternativeFinder:
    """Test suite for AlternativeFinder."""

    @pytest.fixture
    def finder(self, tmp_path):
        """Create finder instance with temp directory."""
        return AlternativeFinder(output_dir=tmp_path)

    @pytest.fixture
    def sample_holding(self):
        """Create sample holding for testing."""
        return HoldingProfile(
            ticker="IBM",
            name="IBM Corporation",
            asset_class="stock",
            grade="D",
            composite_score=0.55
        )

    def test_should_find_no_alternatives_when_grade_b_or_above(self, finder):
        """Test that no alternatives found for B+ or better grades."""
        # Arrange
        holding = HoldingProfile(
            ticker="AAPL",
            name="Apple Inc.",
            asset_class="stock",
            grade="B",
            composite_score=0.75
        )

        # Act
        alternatives = finder.find_alternatives(holding)

        # Assert
        assert len(alternatives) == 0

    def test_should_find_aplus_alternatives_when_underperforming(
        self, finder, sample_holding, mocker
    ):
        """Test finding A+ alternatives for underperforming stock."""
        # Arrange
        mock_discovery = mocker.patch.object(
            finder, '_find_aplus_alternatives'
        )
        mock_discovery.return_value = [
            mocker.Mock(ticker='MSFT', grade='A+')
        ]

        # Act
        alternatives = finder.find_alternatives(sample_holding)

        # Assert
        assert len(alternatives) > 0
        assert alternatives[0].ticker == 'MSFT'
        mock_discovery.assert_called_once()
```

---

**Version**: 3.0  
**Last Updated**: 2025-10-26  
**Consolidated from**: unittest-mock-ban.md, crewai-testing-standards.md
