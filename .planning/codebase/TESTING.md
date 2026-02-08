# Testing Patterns

**Analysis Date:** 2026-02-07

## Test Framework

**Runner:**

- `pytest` 8.4.1+
- Config: `pyproject.toml` under `[tool.pytest.ini_options]`

**Assertion Library:**

- Built-in pytest assertions
- `pytest.approx()` for floating-point comparisons

**Run Commands:**

```bash
make test              # Run unit tests only (excludes integration)
make test-all          # Run all tests including integration
make test-integration  # Run integration tests only
make coverage          # Run tests with coverage report (65% minimum)
pytest path/to/test.py::test_function -v -s  # Run single test
pytest -m integration  # Run tests by marker
```

## Test File Organization

**Location:**

- Co-located with code: No (tests in separate directory)
- Separate test directory: Yes

**Naming:**

- Test files: `test_*.py` (e.g., `test_backtesting.py`, `test_risk_scorer.py`)
- Test classes: `Test*` (e.g., `TestRiskScorer`, `TestTrade`)
- Test functions: `test_*` (e.g., `test_should_create_valid_trade_when_all_fields_provided`)

**Structure:**

```
tests/
├── conftest.py                    # Shared fixtures
├── conftest_unittest_blocker.py   # Runtime blocker for unittest.mock
├── fixtures/                      # Test data fixtures
│   ├── api_test_mocks.py
│   ├── asset_data.py
│   ├── market_data.py
│   └── mock_factories.py
├── unit/                          # Unit tests
│   ├── quantitative/
│   │   ├── conftest.py           # Quantitative-specific fixtures
│   │   ├── test_backtesting.py
│   │   └── test_optimization.py
│   ├── scoring/
│   │   ├── test_fundamental_scorer.py
│   │   └── test_risk_scorer.py
│   └── tools/
│       └── test_yahoo_finance_tool.py
├── integration/                   # Integration tests (deselected by default)
├── property/                      # Property-based tests (hypothesis)
└── validation/                    # Validation tests
```

## Test Structure

**Suite Organization:**

```python
from faker import Faker
import pytest
from pytest import approx

from finwiz.scoring.risk_scorer import RiskScorer


class TestRiskScorer:
    """Test suite for RiskScorer."""

    @pytest.fixture
    def scorer(self):
        """Create a RiskScorer instance for tests."""
        return RiskScorer()

    def test_should_calculate_low_volatility_correctly(self, scorer):
        """Test risk scoring with low volatility."""
        # Arrange
        data = {"volatility": 0.08, "max_drawdown": -0.10, "beta": 0.9}

        # Act
        score, details = scorer.calculate_risk_score(data)

        # Assert
        assert score > 0.9
        assert details["volatility_score"] == approx(1.0)
        assert details["drawdown_score"] == approx(1.0)

    def test_should_handle_missing_data_gracefully(self, scorer):
        """Test risk scoring with missing data."""
        data = {}
        score, details = scorer.calculate_risk_score(data)
        assert 0.0 <= score <= 1.0  # Should use defaults
```

**Patterns:**

- Test class per module/class being tested
- `@pytest.fixture` for reusable setup
- AAA pattern: Arrange, Act, Assert (explicitly labeled in complex tests)
- Descriptive test names: `test_should_{action}_when_{condition}`
- One assertion theme per test (can have multiple asserts for same concept)

## Mocking

**Framework:** `pytest-mock` (unittest.mock is BANNED)

**Patterns:**

```python
def test_should_fetch_data_from_api(mocker):
    """Test API data fetching."""
    # Mock the external API call
    mock_response = {"ticker": "AAPL", "price": 150.0}
    mock_fetch = mocker.patch(
        "finwiz.data.adapters.yahoo_adapter.fetch_quote",
        return_value=mock_response
    )

    # Execute
    result = get_stock_data("AAPL")

    # Verify
    assert result["price"] == 150.0
    mock_fetch.assert_called_once_with("AAPL")


def test_should_handle_api_failure(mocker):
    """Test error handling when API fails."""
    # Mock API to raise exception
    mocker.patch(
        "finwiz.data.adapters.yahoo_adapter.fetch_quote",
        side_effect=ConnectionError("API unavailable")
    )

    # Execute and assert exception
    with pytest.raises(ConnectionError):
        get_stock_data("AAPL")
```

**What to Mock:**

- External API calls (Yahoo Finance, Alpha Vantage, etc.)
- Database connections
- File system operations (for unit tests)
- Time-sensitive operations (`datetime.now()`)
- Expensive calculations in integration tests

**What NOT to Mock:**

- Pure functions being tested
- Pydantic model validation
- Simple utility functions
- Domain logic (score calculations, business rules)

**Mocker Usage:**

- `mocker.patch("module.path.function")` - Patch function/method
- `mocker.patch.object(obj, "method")` - Patch object method
- `mocker.Mock()` - Create mock object
- `mocker.MagicMock()` - Create mock with magic methods
- `mocker.AsyncMock()` - Create async mock
- `return_value` - Set return value
- `side_effect` - Set exception or dynamic behavior

## Fixtures and Factories

**Test Data:**

```python
# In tests/conftest.py
from faker import Faker
import pytest


@pytest.fixture(scope="session")
def fake():
    """Faker instance for generating test data."""
    return Faker()


@pytest.fixture
def fake_stock_data(fake: Faker) -> dict[str, Any]:
    """Fixture providing realistic stock data."""
    return {
        "ticker": fake.random_element(elements=("AAPL", "MSFT", "GOOGL")),
        "company_name": fake.company(),
        "sector": fake.random_element(elements=("Technology", "Finance")),
        "market_cap": fake.random_int(min=1_000_000_000, max=3_000_000_000_000),
        "price": round(fake.random.uniform(10.0, 500.0), 2),
    }


@pytest.fixture
def stock_data():
    """Fixture providing sample stock data."""
    from tests.fixtures import create_stock_data
    return create_stock_data()
```

**Location:**

- Shared fixtures: `tests/conftest.py`
- Module-specific fixtures: `tests/unit/quantitative/conftest.py`
- Factory functions: `tests/fixtures/mock_factories.py`
- Test data creators: `tests/fixtures/asset_data.py`

**Factory Pattern:**

```python
# In tests/fixtures/asset_data.py
def create_stock_data(
    ticker: str = "AAPL",
    company_name: str = "Apple Inc.",
    sector: str = "Technology",
) -> dict[str, Any]:
    """Create stock data for testing."""
    return {
        "ticker": ticker,
        "company_name": company_name,
        "sector": sector,
        "market_cap": 2_800_000_000_000,
        "price": 175.50,
    }


# In tests/conftest.py
from tests.fixtures import create_stock_data


@pytest.fixture
def stock_data():
    """Fixture providing sample stock data."""
    return create_stock_data()
```

## Coverage

**Requirements:** 65% minimum threshold (enforced by `--cov-fail-under=65`)

**View Coverage:**

```bash
make coverage              # Run tests with coverage
make coverage-report       # Open HTML coverage report in browser
make coverage-check        # Validate coverage meets threshold
```

**Configuration:**

```python
# pyproject.toml
[tool.pytest.ini_options]
addopts = [
    "--cov=src/finwiz",
    "--cov-report=term-missing",
    "--cov-report=html:htmlcov",
    "--cov-fail-under=65",
]
```

**Coverage Reports:**

- Terminal: Shows missing lines per file
- HTML: `htmlcov/index.html` with detailed line-by-line coverage
- Fail threshold: 65% (build fails if below)

## Test Types

**Unit Tests:**

- Scope: Single function/class in isolation
- Location: `tests/unit/`
- Marker: `@pytest.mark.unit` (optional, default)
- Mocking: Heavy use of mocks for dependencies
- Speed: Fast (<1s per test)

**Integration Tests:**

- Scope: Multiple components working together
- Location: `tests/integration/`
- Marker: `@pytest.mark.integration` (required)
- Mocking: Minimal, tests actual integrations
- Speed: Slower (1-30s per test)
- Deselected by default: `-m "not integration"` in pytest config

**Property Tests:**

- Framework: `hypothesis` (installed in dev dependencies)
- Location: `tests/property/`
- Marker: `@pytest.mark.property`
- Purpose: Generate random test cases to find edge cases

**E2E Tests:**

- Not currently used
- Would test entire flow execution

## Common Patterns

**Async Testing:**

```python
@pytest.mark.asyncio
async def test_should_validate_data_async():
    """Test async validation."""
    from finwiz.orchestrators.validation_orchestrator import ValidationOrchestrator

    orchestrator = ValidationOrchestrator(state, integration_manager=None)
    result = await orchestrator.validate_data_integration()

    assert result["integration_manager_available"] is False
```

**Error Testing:**

```python
def test_should_raise_error_for_invalid_price():
    """Test validation of price constraints."""
    from finwiz.quantitative.backtesting import Trade, TradeType, TradeStatus

    with pytest.raises(ValueError, match="entry_price must be positive"):
        Trade(
            trade_id="test",
            symbol="AAPL",
            trade_type=TradeType.BUY,
            status=TradeStatus.OPEN,
            entry_date=datetime.now(),
            entry_price=-100.0,  # Invalid
            quantity=100,
            strategy_name="TestStrategy",
        )
```

**Parametrized Tests:**

```python
@pytest.mark.parametrize(
    "rsi,expected_score",
    [
        (50, 1.0),   # Neutral
        (30, 0.8),   # Oversold (bullish)
        (70, 0.8),   # Overbought (bearish)
        (95, 0.2),   # Extreme overbought
    ],
)
def test_should_score_rsi_correctly(rsi, expected_score):
    """Test RSI scoring across different values."""
    from finwiz.scoring.technical_scorer import TechnicalScorer

    scorer = TechnicalScorer()
    data = {
        "rsi": rsi,
        "current_price": 100,
        "moving_avg_50": 100,
        "moving_avg_200": 100,
        "macd": 0,
        "macd_signal": 0,
    }
    score, details = scorer.calculate_technical_score(data)
    assert details["rsi_score"] == approx(expected_score)
```

**Float Comparisons:**

```python
from pytest import approx

def test_should_calculate_composite_score():
    """Test composite score calculation."""
    result = calculate_composite_score(
        fundamental=0.85,
        technical=0.78,
        risk=0.65,
    )
    assert result == approx(0.77, abs=0.01)  # Allow 1% tolerance
```

**Fixture Composition:**

```python
@pytest.fixture
def scorer():
    """Create scorer instance."""
    return DeepAnalysisScorer()


@pytest.fixture
def sample_data():
    """Create sample data."""
    return {"roe": 0.25, "debt_to_equity": 0.5}


def test_should_score_with_fixtures(scorer, sample_data):
    """Test using multiple fixtures."""
    result = scorer.calculate_composite_score(
        ticker="AAPL",
        asset_class="stock",
        data=sample_data,
    )
    assert result.composite_score > 0.7
```

## Test Markers

**Available Markers:**

```python
# pyproject.toml
[tool.pytest.ini_options]
markers = [
    "integration: marks tests as integration tests (deselected by default)",
    "unit: marks tests as unit tests",
    "slow: marks tests as slow running",
    "asyncio: marks tests as async tests",
    "performance: marks tests as performance tests",
    "benchmark: marks tests as benchmark tests",
    "core_analysis: marks tests as core analysis related",
    "crew: marks tests as crew-specific tests",
    "flow: marks tests as flow orchestration tests",
]
```

**Usage:**

```python
@pytest.mark.integration
def test_should_fetch_real_data():
    """Integration test with real API."""
    pass


@pytest.mark.slow
def test_should_backtest_strategy():
    """Slow test that takes >10s."""
    pass


@pytest.mark.asyncio
async def test_should_run_async():
    """Async test."""
    pass
```

**Running by Marker:**

```bash
pytest -m integration      # Run only integration tests
pytest -m "not integration"  # Skip integration tests (default)
pytest -m "slow or integration"  # Run slow or integration
pytest -m "unit and not slow"    # Run fast unit tests
```

## Test Configuration

**pytest.ini_options:**

```python
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"

addopts = [
    "--cov=src/finwiz",
    "--cov-report=term-missing",
    "--cov-report=html:htmlcov",
    "--cov-fail-under=65",
    "--strict-markers",     # Fail on unknown markers
    "--strict-config",      # Fail on config errors
    "-ra",                  # Show extra test summary info
    "--tb=short",           # Shorter traceback format
    "-m", "not integration" # Skip integration by default
]

filterwarnings = [
    "ignore::DeprecationWarning",
    "ignore::PendingDeprecationWarning",
]
```

## unittest.mock Enforcement

**Runtime Blocker:**

```python
# tests/conftest_unittest_blocker.py
class UnittestMockBlocker:
    """Block unittest.mock imports and provide helpful error messages."""

    def find_module(self, fullname: str, path: Any = None):
        if fullname == "unittest.mock":
            return self
        return None

    def load_module(self, fullname: str):
        raise ImportError(
            "\n\n"
            "❌ unittest.mock is BANNED in this project!\n"
            "\n"
            "✅ Use pytest-mock instead:\n"
            "   def test_example(mocker):\n"
            "       mock_obj = mocker.patch('module.function')\n"
        )


sys.meta_path.insert(0, UnittestMockBlocker())
```

**Ruff Enforcement:**

```python
# pyproject.toml
[tool.ruff.lint.flake8-tidy-imports.banned-api]
"unittest.mock".msg = "Use pytest-mock instead. Import 'mocker' fixture."
```

**Makefile Check:**

```bash
make check-unittest-mock   # Check for unittest.mock violations
```

## Test Naming Convention

**Pattern:** `test_should_{action}_when_{condition}`

**Examples:**

- `test_should_create_valid_trade_when_all_fields_provided`
- `test_should_validate_positive_entry_price_when_provided`
- `test_should_calculate_pnl_correctly_for_long_position`
- `test_should_handle_missing_data_gracefully`
- `test_should_raise_error_for_invalid_input`

**Benefits:**

- Readable as specifications
- Clear intent from name alone
- Easy to understand test failures

## Test Data Generation

**Using Faker:**

```python
from faker import Faker

fake = Faker()

def test_with_faker(fake: Faker):
    """Test with generated data."""
    ticker = fake.pystr(min_chars=3, max_chars=5).upper()
    price = fake.pyfloat(min_value=10, max_value=500, right_digits=2)
    date = fake.date_time_this_year()

    assert len(ticker) <= 5
    assert 10 <= price <= 500
```

**Using Fixtures:**

```python
def test_with_fixtures(stock_data, etf_data, crypto_data):
    """Test with fixture data."""
    assert stock_data["ticker"] == "AAPL"
    assert etf_data["ticker"] == "SPY"
    assert crypto_data["ticker"] == "BTC"
```

## Quality Checks

**Full Quality Suite:**

```bash
make check   # Run lint + test + unittest.mock check + docs validation
```

**Individual Checks:**

```bash
make lint                   # Ruff linting and formatting
make test                   # Unit tests only
make test-all               # All tests including integration
make coverage               # Tests with coverage report
make check-unittest-mock    # Check for banned unittest.mock
make docs-validate          # Validate documentation
```

---

*Testing analysis: 2026-02-07*
