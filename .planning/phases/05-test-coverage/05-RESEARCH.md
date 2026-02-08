# Phase 5: Test Coverage - Research

**Researched:** 2026-02-08
**Domain:** Python testing (pytest, pytest-mock, pytest-asyncio) for CrewAI/Pydantic application
**Confidence:** HIGH

## Summary

Phase 5 fills critical test gaps across four areas: orchestrator integration tests (TEST-01), crew output parsing tests (TEST-02), data adapter fallback tests (TEST-03), and HTML output validation tests (TEST-04). Research investigated the current codebase structure, existing test patterns, public APIs of components under test, and the tools/libraries available.

The codebase already has a mature test infrastructure: pytest with pytest-mock (unittest.mock is BANNED), Faker-based fixtures in `tests/fixtures/`, `tests/conftest.py` with shared fixtures, and `pytest-asyncio` with `asyncio_mode = "auto"`. Existing test patterns in `tests/unit/orchestrators/` and `tests/unit/data/` provide clear templates to follow. The enriched analysis report generator uses Jinja2 with `autoescape=True`, which is the correct XSS defense.

**Primary recommendation:** Write targeted tests that exercise real FinwizState mutations, CrewAI output format variations, adapter fallback waterfall chains, and HTML well-formedness. Use `mocker` (pytest-mock) exclusively. Follow existing test patterns in `tests/unit/orchestrators/test_validation_orchestrator.py` as the reference style.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest | >=8.4.1 | Test framework | Already configured in pyproject.toml |
| pytest-mock | >=3.14.1 | Mocking (wraps unittest.mock) | MANDATORY - unittest.mock is banned |
| pytest-asyncio | >=0.24.0 | Async test support | Already configured, `asyncio_mode = "auto"` |
| pytest-cov | >=7.0.0 | Coverage reporting | Already configured, 65% minimum |
| Faker | >=33.1.0 | Test data generation | Already used in conftest.py fixtures |
| hypothesis | >=6.148.1 | Property-based testing | Already used in tests/property/ |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| beautifulsoup4 | >=4.14.2 | HTML parsing/validation | Already a project dependency; use for HTML structure validation |
| lxml | (via bs4) | HTML parser backend | Use `html.parser` (stdlib) for safety; lxml is available but not required |
| pydantic | >=2.11.7 | Schema validation in tests | Already core dependency; use `ValidationError` for schema failure tests |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| beautifulsoup4 | html5lib | bs4 already in deps, html5lib adds new dependency |
| Manual XSS checks | bleach library | Jinja2 autoescape already handles XSS; checking for `<script>` tags with bs4 is sufficient |
| pytest-html | raw coverage | Already have htmlcov; no need for test report HTML |

**Installation:** No new dependencies needed. All libraries are already in `pyproject.toml`.

## Architecture Patterns

### Existing Test Directory Structure
```
tests/
├── conftest.py                              # Shared fixtures (stock_data, etf_data, etc.)
├── conftest_unittest_blocker.py             # Blocks unittest.mock imports
├── fixtures/
│   ├── __init__.py                          # Re-exports create_* functions
│   ├── asset_data.py                        # create_stock_data(), create_etf_data(), etc.
│   ├── mock_factories.py                    # mock_crew_result, mock_api_response fixtures
│   ├── market_data.py                       # Market data factories
│   ├── schema_fixtures.py                   # Schema test data
│   └── reporter_test_data.py                # Reporter test data
├── unit/
│   ├── orchestrators/                       # 14 test files for orchestrators
│   │   ├── test_validation_orchestrator.py  # REFERENCE PATTERN for orchestrator tests
│   │   ├── test_deep_analysis_orchestrator.py
│   │   ├── test_reporting_orchestrator.py
│   │   └── ...
│   ├── data/
│   │   ├── adapters/
│   │   │   ├── test_base_adapter.py         # REFERENCE PATTERN for adapter tests
│   │   │   └── test_industry_averages.py
│   │   └── test_data_source_orchestrator.py # REFERENCE PATTERN for fallback tests
│   ├── reporting/
│   │   ├── test_crew_report_generators.py
│   │   ├── test_deep_analysis_report_generator.py
│   │   └── test_report_section_generators.py
│   └── ...
├── integration/
│   ├── conftest.py                          # Integration-specific fixtures
│   ├── test_orchestrator_integration.py     # DataSourceOrchestrator integration tests
│   ├── test_data_source_orchestrator.py     # End-to-end adapter tests
│   └── ...
└── property/                                # Property-based tests using hypothesis
    ├── test_deep_analysis_orchestrator_properties.py
    ├── test_flow_delegation_properties.py
    └── ...
```

### New Test Files Location
```
tests/
├── unit/
│   ├── orchestrators/
│   │   └── test_orchestrator_state_integration.py  # TEST-01: FinwizState mutation tests
│   ├── crews/
│   │   └── test_crew_output_parsing.py             # TEST-02: CrewAI output format tests
│   ├── data/
│   │   └── test_adapter_fallback_scenarios.py      # TEST-03: Complete fallback tests
│   └── reporting/
│       └── test_html_output_validation.py          # TEST-04: HTML validity tests
```

### Pattern 1: Orchestrator Test with Real FinwizState (REFERENCE)
**What:** Instantiate real `FinwizState()`, create orchestrator with mocked dependencies, call methods, verify state mutations.
**When to use:** TEST-01 - All orchestrator integration tests
**Example:**
```python
# Source: tests/unit/orchestrators/test_validation_orchestrator.py (lines 17-58)
class TestValidationOrchestrator:
    @pytest.fixture
    def state(self):
        return FinwizState()

    @pytest.fixture
    def orchestrator(self, state, mocker):
        integration_manager = mocker.Mock()
        data_accessor = mocker.Mock()
        return ValidationOrchestrator(
            state,
            integration_manager=integration_manager,
            data_accessor=data_accessor,
        )

    def test_should_validate_reporter_input_successfully(self, orchestrator, mocker):
        consolidated_data = {
            "consolidated_crew_data": {
                "stock": [{"ticker": "AAPL"}],
                "etf": [{"ticker": "SPY"}],
            },
        }
        orchestrator.data_accessor.get_consolidated_reporter_input.return_value = consolidated_data
        orchestrator.integration_manager.get_crew_data_with_freshness_check.return_value = {"data": "test"}

        result = orchestrator.pre_validate_reporter_input()

        assert result["success"] is True
        assert orchestrator.state.consolidated_data == consolidated_data  # STATE MUTATION VERIFIED
```

### Pattern 2: Mock Crew Result with Output Variants (REFERENCE)
**What:** Use `mocker.Mock()` to create crew results with different output formats (pydantic, json_dict, raw).
**When to use:** TEST-02 - Crew output parsing tests
**Example:**
```python
# Source: tests/fixtures/mock_factories.py (lines 88-127)
@pytest.fixture
def mock_crew_result(mocker):
    def _factory(raw="Analysis complete", pydantic=None, json_dict=None):
        mock_result = mocker.Mock()
        mock_result.raw = raw
        mock_result.pydantic = pydantic
        mock_result.json_dict = json_dict or {}
        return mock_result
    return _factory
```

### Pattern 3: Async Data Adapter Test (REFERENCE)
**What:** Use `@pytest.mark.asyncio` with `mocker.AsyncMock()` for async adapter methods.
**When to use:** TEST-03 - Data adapter fallback tests
**Example:**
```python
# Source: tests/unit/data/test_data_source_orchestrator.py (lines 103-116)
@pytest.mark.asyncio
async def test_should_use_fallback_when_all_sources_fail(self, orchestrator, mocker):
    for adapter in orchestrator.adapters:
        mocker.patch.object(adapter, "is_available", return_value=False)

    result = await orchestrator.get_fundamental_data("AAPL", sector="Technology")

    assert result.used_fallback is True
    assert "IndustryAverages" in result.sources_succeeded
```

### Anti-Patterns to Avoid
- **unittest.mock import:** BANNED. Use `mocker` fixture from pytest-mock exclusively.
- **`from unittest.mock import Mock`:** Will fail at import time (conftest_unittest_blocker.py blocks it).
- **`self.inputs` in flow methods:** DEPRECATED. Always use `self.state`.
- **`json.dumps` without `default=str`:** Will crash on datetime objects.
- **Test files >300 lines:** Split into focused modules.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Mock CrewAI results | Custom mock classes | `mock_crew_result` fixture from `tests/fixtures/mock_factories.py` | Already handles pydantic/json_dict/raw variants |
| Test data generation | Hard-coded dicts | `Faker` + existing `create_stock_data()` etc. from `tests/fixtures/` | Generates realistic, varied data |
| FinwizState setup | Manual field assignment | `FinwizState()` constructor with defaults | Pydantic model has sensible defaults for all fields |
| HTML parsing in tests | Regex on HTML strings | `BeautifulSoup(html, "html.parser")` | Already a project dependency |
| Async test setup | Manual event loop management | `@pytest.mark.asyncio` with `asyncio_mode = "auto"` | Already configured in pyproject.toml |
| XSS vector testing | Custom sanitizer | Check for `<script>` tags via BeautifulSoup + verify Jinja2 `autoescape=True` | Jinja2 autoescape is the actual defense |

**Key insight:** The project already has comprehensive fixture infrastructure. New tests should reuse existing factories and patterns rather than creating parallel infrastructure.

## Common Pitfalls

### Pitfall 1: Using unittest.mock Instead of pytest-mock
**What goes wrong:** Import error at runtime due to `conftest_unittest_blocker.py` + ruff lint failure
**Why it happens:** Muscle memory from other projects
**How to avoid:** Always use `mocker` fixture parameter. `mocker.Mock()`, `mocker.patch()`, `mocker.AsyncMock()`
**Warning signs:** `from unittest.mock import` anywhere in test code

### Pitfall 2: Not Awaiting Async Orchestrator Methods
**What goes wrong:** Tests pass but don't actually run the async code; get `RuntimeWarning: coroutine was never awaited`
**Why it happens:** `validate_data_integration()` and `check_portfolio()` are `async` methods; `check_crypto()`, `report()` are sync
**How to avoid:** Check the source code for `async def` vs `def`. Use `await` for async methods. `asyncio_mode = "auto"` means tests just need `async def test_...`
**Warning signs:** Tests that always pass regardless of assertions

### Pitfall 3: Testing CrewAI Output Parsing Without All Three Formats
**What goes wrong:** Missing coverage for json_dict or raw fallback paths
**Why it happens:** Only testing the happy path (pydantic output)
**How to avoid:** Test all three branches in crew_factory.py: (1) `result.pydantic` present, (2) `result.json_dict` present but no pydantic, (3) raw fallback only
**Warning signs:** CrewAI output access cascade code (lines 64-70 of crew_factory.py) has three distinct branches

### Pitfall 4: Not Testing State Mutation Side Effects
**What goes wrong:** Test verifies return value but misses that state was not properly updated
**Why it happens:** Orchestrator methods both return results AND mutate `self.state`
**How to avoid:** Always assert BOTH the return value AND the relevant state field changes
**Warning signs:** Orchestrator methods with `self.state.field = value` assignments

### Pitfall 5: HTML Tests That Only Check Content, Not Structure
**What goes wrong:** HTML is malformed (unclosed tags, broken encoding) but content checks pass
**Why it happens:** String-based assertions like `assert "AAPL" in html` ignore structure
**How to avoid:** Parse with BeautifulSoup, check for `<html>`, `<head>`, `<meta charset>`, proper nesting
**Warning signs:** Tests that use `assert "text" in html_string` without any structural validation

### Pitfall 6: Forgetting to Mock File I/O in Orchestrator Tests
**What goes wrong:** Tests write real files to `output/` directory or fail when reading CSVs
**Why it happens:** `ReportingOrchestrator.report()` writes HTML files; `check_portfolio()` reads CSVs
**How to avoid:** Mock file operations with `mocker.patch("pathlib.Path.write_text")` or `mocker.patch("builtins.open")`
**Warning signs:** Tests that create files in `output/` or require real CSV data

## Code Examples

Verified patterns from the actual codebase:

### Creating FinwizState for Testing
```python
# Source: tests/unit/orchestrators/test_deep_analysis_orchestrator.py (lines 23-33)
@pytest.fixture
def state(self):
    return FinwizState(
        session_id="test_session",
        current_day=17,
        current_month=11,
        current_year=2025,
        current_date="2025-11-17",
        full_date="November 17, 2025",
        timestamp="2025-11-17T10:00:00",
        report_language="en",
    )
```

### Creating DeepAnalysisResult for Testing
```python
# Source: tests/unit/orchestrators/test_deep_analysis_orchestrator.py (lines 51-69)
@pytest.fixture
def mock_deep_analysis_result(self) -> DeepAnalysisResult:
    return DeepAnalysisResult(
        ticker="AAPL",
        asset_class="stock",
        crew_name="DeepAnalysisCrew",
        grade="A",
        composite_score=0.82,
        fundamental_score=0.85,
        technical_score=0.78,
        risk_score=0.80,
        recommendation="BUY",
        rationale="Strong fundamentals with solid growth potential.",
        fundamental_details={"pe_ratio": 25.0, "roe": 0.30},
        technical_details={"rsi": 55.0, "macd": 1.2},
        risk_details={"volatility": 0.15, "beta": 1.1},
        data_freshness_hours=0.5,
        confidence_level=0.85,
    )
```

### Crew Output Parsing Cascade (What to Test)
```python
# Source: src/finwiz/crew_factory.py (lines 64-70, repeated for stock/etf/crypto)
# This is the ACTUAL code pattern tests must exercise:
if hasattr(result, "pydantic") and result.pydantic:
    result_data["crypto_analysis_result"] = result.pydantic.model_dump()
elif hasattr(result, "json_dict") and result.json_dict:
    result_data["crypto_analysis_result"] = result.json_dict
else:
    result_data["crypto_analysis_result"] = {
        "raw_output": result.raw if hasattr(result, "raw") else str(result)
    }
```

### Data Adapter Fallback Chain (What to Test)
```python
# Source: src/finwiz/data/data_source_orchestrator.py (lines 84-100)
# Waterfall Strategy:
# 1. YFinance (primary, fast, free)
# 2. Alpha Vantage (fallback, good fundamentals) -- TODO: not yet async
# 3. Intrinio (fallback, SEC filings) -- TODO: not yet async
# 4. Tiingo/EOD (international stocks) -- TODO: not yet async
# 5. Industry Averages (last resort, always available)
```

### HTML Report Generation with Jinja2 Autoescape
```python
# Source: src/finwiz/reporting/enriched_analysis_report_generator.py (lines 57-62)
self.env = Environment(
    loader=FileSystemLoader(str(self.template_dir)),
    autoescape=True,  # Security: auto-escape HTML
    trim_blocks=True,
    lstrip_blocks=True,
)
```

### Async Adapter Test Pattern
```python
# Source: tests/unit/data/test_data_source_orchestrator.py (lines 248-297)
@pytest.mark.asyncio
async def test_should_merge_data_from_multiple_sources(self, orchestrator, mocker):
    partial_data_1 = FundamentalData(
        ticker="AAPL", source="Source1", timestamp=datetime.now(),
        confidence=0.9, return_on_equity=0.25, debt_to_equity=0.5,
    )
    partial_data_2 = FundamentalData(
        ticker="AAPL", source="Source2", timestamp=datetime.now(),
        confidence=0.8, revenue_growth=0.15, profit_margin=0.20,
    )

    mock_adapter_1 = mocker.Mock(spec=orchestrator.adapters[0])
    mock_adapter_1.source_name = "Source1"
    mock_adapter_1.is_available.return_value = True
    mock_adapter_1.get_fundamental_data = mocker.AsyncMock(return_value=partial_data_1)

    mock_adapter_2 = mocker.Mock(spec=orchestrator.adapters[0])
    mock_adapter_2.source_name = "Source2"
    mock_adapter_2.is_available.return_value = True
    mock_adapter_2.get_fundamental_data = mocker.AsyncMock(return_value=partial_data_2)

    orchestrator.adapters = [mock_adapter_1, mock_adapter_2]
    result = await orchestrator.get_fundamental_data("AAPL")

    assert result.return_on_equity == 0.25  # From Source1
    assert result.profit_margin == 0.20      # From Source2
```

## Component Inventory (What to Test)

### TEST-01: Orchestrator Integration Tests

**Orchestrators and their state-mutating methods:**

| Orchestrator | Method | Async? | State Fields Mutated |
|---|---|---|---|
| `ValidationOrchestrator` | `validate_data_integration()` | YES | (none directly, returns dict) |
| `ValidationOrchestrator` | `check_portfolio()` | YES | `portfolio_review`, `portfolio_review_success`, `portfolio_review_json`, `portfolio_review_error` |
| `ValidationOrchestrator` | `pre_validate_reporter_input()` | NO | `consolidated_data`, `integrated_data_available`, `market_sentiment`, `ticker_validation`, `aplus_opportunities`, `portfolio_allocation_updates`, `aplus_availability_status`, `core_analysis_summary` |
| `DeepAnalysisOrchestrator` | `analyze_and_update_portfolio()` | YES | `deep_analysis_results`, `deep_analysis_success`, `deep_analysis_error`, `portfolio_alternatives`, `alternatives_success`, `alternatives_count` |
| `DiscoveryOrchestrator` | `check_crypto()` | NO | `crypto_analysis_success`, `crypto_result` |
| `DiscoveryOrchestrator` | `check_stock()` | NO | `stock_analysis_success`, `stock_result` |
| `DiscoveryOrchestrator` | `check_etf()` | NO | `etf_analysis_success`, `etf_result` |
| `ReportingOrchestrator` | `report()` | NO | `final_report_path` |
| `ErrorHandlingOrchestrator` | `execute_crew_with_error_handling()` | NO | `errors` list, `error_summaries` |

**Key state mutations to verify:**
1. `check_portfolio()` sets `portfolio_review` dict AND `portfolio_review_success` boolean
2. `analyze_and_update_portfolio()` sets `deep_analysis_results` AND updates `portfolio_review["holdings"]` in-place
3. Error paths set `*_error` fields AND `*_success = False`
4. `pre_validate_reporter_input()` consolidates all data into `consolidated_data`

### TEST-02: Crew Output Parsing Tests

**CrewAI result object has three output formats:**
1. `result.pydantic` -- Pydantic model instance (preferred)
2. `result.json_dict` -- Dictionary from JSON parsing
3. `result.raw` -- Raw string output (fallback)

**The access cascade pattern in `crew_factory.py`:**
- Lines 64-70 (crypto), 119-125 (stock), 174-180 (etf), 230-236 (rebalancing), 270-277 (discovery)
- Same pattern repeated 5 times: check pydantic -> check json_dict -> fallback to raw

**What malformed outputs look like:**
- `result.pydantic = None` and `result.json_dict = None` -- forces raw fallback
- `result.pydantic = None` and `result.json_dict = {"key": "value"}` -- uses json_dict
- `result.pydantic.model_dump()` raises `AttributeError` -- needs error handling test
- `result.raw` contains non-JSON text -- should still work (stored as `{"raw_output": ...}`)

### TEST-03: Data Adapter Fallback Tests

**Adapter chain in `DataSourceOrchestrator`:**
- `self.adapters` list: currently `[YFinanceAdapter]` (others are TODO)
- `self.fallback_adapter`: `IndustryAveragesAdapter` (always available)
- Waterfall: try adapters in order, skip unavailable, stop when complete

**Failure scenarios to test:**
1. All adapters return `is_available() == False` -> falls to IndustryAverages
2. Primary adapter raises `DataAcquisitionError` -> next adapter tried
3. Primary adapter raises `TimeoutError` -> next adapter tried
4. Primary adapter returns invalid data (`is_valid() == False`) -> rejected, next tried
5. All adapters fail AND IndustryAverages fails -> partial result with warnings
6. Primary returns partial data, fallback fills remaining fields (merge behavior)
7. Total timeout (10s) exceeded during orchestration

**Existing coverage gaps:**
- No test for IndustryAverages adapter failure (it always works, but the error path exists)
- No test for all adapters failing AND fallback failing
- No test for partial data degradation (some fields filled, some not)

### TEST-04: HTML Output Validation Tests

**HTML generation entry points:**
1. `EnrichedAnalysisReportGenerator.generate_report()` -- Jinja2 template-based, has `autoescape=True`
2. `PythonReportGenerator.generate_family_financial_plan()` -- generates consolidated report
3. `auto_generate_html()` in `html_auto_generator.py` -- JSON-to-HTML conversion
4. `JsonToHtmlConverter.convert_file()` in `infrastructure/json/to_html_converter.py`

**HTML template used:** `src/finwiz/templates/enriched_analysis_report.html`
- Declares `<html lang="fr">`, `<meta charset="UTF-8">`
- Has CSS (both light and dark mode)
- Uses Jinja2 template variables with autoescaping

**What to validate:**
1. Well-formedness: `<!DOCTYPE html>`, `<html>`, `<head>`, `<body>` present
2. Character encoding: `<meta charset="UTF-8">` present
3. XSS prevention: Jinja2 `autoescape=True` is set; injected `<script>` tags are escaped
4. Content completeness: Key sections present (ticker, grade, recommendation, executive summary)
5. CSS presence: `<style>` block with expected class names

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|---|---|---|---|
| `unittest.mock` | `pytest-mock` (`mocker` fixture) | Project rule since inception | Must use `mocker.patch()`, never `from unittest.mock import` |
| `asyncio_mode = "strict"` | `asyncio_mode = "auto"` | pyproject.toml config | Tests auto-detect async; no need for explicit `@pytest.mark.asyncio` in many cases |
| `str(result.raw)` for crew output | Pydantic cascade (`result.pydantic` -> `json_dict` -> `raw`) | Phase 1 (ERRH-03) | Tests must cover all three output paths |
| Individual adapter calls | `DataSourceOrchestrator` waterfall | Phase implementation | Test the orchestrator, not individual adapters |

**Deprecated/outdated:**
- `self.inputs` in flows: Use `self.state` instead
- `str(result)` for crew output: Use pydantic cascade
- `Mock()` from unittest: Use `mocker.Mock()`

## Open Questions

Things that couldn't be fully resolved:

1. **Concurrent execution testing for `run_deep_analysis_concurrent()`**
   - What we know: Uses `asyncio.gather()` with `ThreadPoolExecutor` and semaphore-based concurrency
   - What's unclear: Whether concurrent state mutations need locking (they might race on `self._enriched_analyses`)
   - Recommendation: Test with 2-3 holdings in concurrent mode to verify results are collected correctly; don't test for thread safety (that's a Phase 4 concern)

2. **HTML template loading in CI**
   - What we know: `EnrichedAnalysisReportGenerator` loads templates from `src/finwiz/templates/`
   - What's unclear: Whether template directory resolution works correctly when tests run from project root vs from `tests/` directory
   - Recommendation: Use the default template_dir (None) in tests; if it fails, pass explicit path

3. **Coverage threshold impact**
   - What we know: Current coverage is 26.57%, target is 65%
   - What's unclear: How many new tests are needed to close the gap
   - Recommendation: Focus on the four TEST requirements rather than chasing coverage percentage; quality > quantity

## Sources

### Primary (HIGH confidence)
- `tests/conftest.py` -- Shared fixtures, Faker usage, mock patterns (read directly)
- `tests/unit/orchestrators/test_validation_orchestrator.py` -- Reference orchestrator test pattern (read directly)
- `tests/unit/data/test_data_source_orchestrator.py` -- Reference adapter fallback test pattern (read directly)
- `tests/fixtures/mock_factories.py` -- Mock crew result factory pattern (read directly)
- `src/finwiz/flows/orchestrator.py` -- FinwizFlow, orchestrator delegation (read directly)
- `src/finwiz/flow_state_models.py` -- FinwizState, DeepAnalysisResult Pydantic models (read directly)
- `src/finwiz/crew_factory.py` -- CrewAI output parsing cascade pattern (read directly)
- `src/finwiz/data/data_source_orchestrator.py` -- Waterfall fallback chain (read directly)
- `src/finwiz/data/adapters/base_adapter.py` -- BaseDataAdapter, FundamentalData, error classes (read directly)
- `src/finwiz/reporting/enriched_analysis_report_generator.py` -- Jinja2 autoescape, template rendering (read directly)
- `pyproject.toml` -- pytest config, markers, coverage threshold (read directly)

### Secondary (MEDIUM confidence)
- [beautifulsoup4 PyPI](https://pypi.org/project/beautifulsoup4/) -- HTML parsing for test validation
- [bleach PyPI](https://pypi.org/project/bleach/) -- XSS sanitization reference (not needed since Jinja2 autoescape handles it)

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries already in project, patterns verified from source code
- Architecture: HIGH - Read all existing tests and source files directly
- Pitfalls: HIGH - Identified from actual codebase constraints (BANNED unittest.mock, async methods, etc.)
- Component inventory: HIGH - Traced every state-mutating method and output format variation from source

**Research date:** 2026-02-08
**Valid until:** 2026-03-08 (stable patterns, unlikely to change)
