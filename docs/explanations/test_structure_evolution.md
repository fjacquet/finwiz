# Test Structure Evolution

Understanding the evolution and reorganization of FinWiz's test architecture to improve maintainability and follow best practices.

## Overview

This document explains the comprehensive reorganization of the FinWiz test structure, moving from a flat structure to a hierarchical, purpose-driven organization that aligns with the codebase architecture.

## Architectural Principles

### Diátaxis-Inspired Organization

The test structure follows principles similar to the Diátaxis documentation framework:

- **Unit tests**: Fast, isolated, focused testing
- **Integration tests**: Component interaction testing
- **Performance tests**: Speed and resource usage testing
- **Validation tests**: Manual verification scripts

### Domain-Driven Structure

Tests are organized by domain and responsibility. There is no
`tests/performance/` directory — the `performance` pytest marker exists in
`pyproject.toml`, but no directory backs it. The actual top level (`find
tests -type d`) is `fixtures/`, `integration/`, `property/`, `regression/`,
`tools/`, `unit/`, `validation/`:

```
tests/
├── unit/                    # Fast, isolated tests
│   ├── crews/              # AI agent crew tests
│   ├── flow/               # Flow orchestration tests
│   ├── tools/              # Tool functionality tests
│   ├── schemas/            # Data validation tests
│   ├── orchestrators/      # Business logic tests
│   └── utils/              # Utility function tests
├── integration/            # Component interaction tests
├── fixtures/                # Shared test data and factories
├── property/                # Property-based tests
├── regression/              # Regression tests
├── tools/                   # Standalone test/debug scripts (not to be confused with unit/tools/)
└── validation/             # Manual validation scripts
```

## Migration Details

### Before: Flat Structure

The original structure had all tests in a single directory:

```
tests/
├── test_*.py              # All tests mixed together
└── conftest.py           # Shared configuration
```

**Problems**:

- Difficult to navigate
- No clear separation of concerns
- Hard to run specific test categories
- Poor maintainability

### After: Hierarchical Structure

The new structure provides clear organization:

```bash
tests/
├── unit/
│   ├── crews/
│   │   ├── stock_crew/     # Stock analysis crew tests
│   │   ├── etf_crew/       # ETF analysis crew tests
│   │   └── crypto_crew/    # Cryptocurrency analysis crew tests
│   ├── flow/               # Flow orchestration and main app tests
│   ├── tools/              # Tool unit tests (enhanced)
│   ├── schemas/            # Schema validation tests (enhanced)
│   ├── orchestrators/      # Orchestration component tests
│   └── utils/              # Utility function tests (enhanced)
├── integration/             # tests/integration/analysis/ + top-level test_*.py
                             # (no core_analysis/ subdirectory — core_analysis-marked
                             # tests are scattered across tests/unit/ instead)
└── validation/             # Manual validation scripts
```

There is no `tests/performance/` directory (the `performance` marker exists
but nothing backs it with a directory).

## Key Improvements

### 1. Crew-Specific Testing

**New Structure**:

- `tests/unit/crews/stock_crew/` - Stock analysis crew tests
- `tests/unit/crews/etf_crew/` - ETF analysis crew tests
- `tests/unit/crews/crypto_crew/` - Cryptocurrency analysis crew tests

**Benefits**:

- Clear separation by asset class
- Easy to add new crew tests
- Follows CrewAI testing standards
- Avoids testing full crew execution (which hangs)

### 2. Flow Orchestration Testing

**New Structure**:

Neither of these files exists. `tests/unit/flow/` currently contains only
`test_core_analysis_error_handler.py`.

**Benefits**:

- Separates flow logic from business logic
- Tests Flow state management patterns
- Validates CrewAI Flow integration

### 3. Enhanced Tool Testing

**Moved to `tests/unit/tools/`**:

- Enhanced analysis tools (crypto, ETF, SEC)
- Sentiment analysis tools
- Technical analysis tools
- RAG tools
- Report generation tools

**Benefits**:

- Comprehensive tool coverage
- Mock all external dependencies
- Fast execution (< 5 seconds per suite)

### 4. Schema Validation Testing

**Moved to `tests/unit/schemas/`**:

- Pydantic model validation
- Input/output contract testing
- Reporter validation enforcement
- Tool restriction testing

**Benefits**:

- Ensures data integrity
- Validates strict Pydantic models
- Tests schema evolution

### 5. Integration Testing

**`tests/integration/`** (no `core_analysis/` subdirectory — it contains
`analysis/` plus top-level `test_*.py` files):

- Crew output validation
- Data flow validation
- End-to-end analysis workflows
- Validation pipeline testing

**Benefits**:

- Tests component interactions
- Validates real data flows
- Ensures system integration

## Configuration Updates

### pytest Markers

Added new test markers in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
markers = [
    "integration: Integration tests (slow, requires API keys)",
    "slow: Slow tests (> 30 seconds)",
    "core_analysis: Core analysis related tests",
    "crew: Crew-specific tests",
    "flow: Flow orchestration tests"
]
```

### Test Discovery

Enhanced test discovery with clear patterns:

```bash
# Run specific test categories
uv run pytest tests/unit/crews/ -v          # Crew tests
uv run pytest tests/unit/flow/ -v           # Flow tests
uv run pytest tests/integration/ -v -m integration  # Integration tests

# Run by marker
uv run pytest -m crew                       # All crew tests
uv run pytest -m flow                       # All flow tests
uv run pytest -m core_analysis              # Core analysis tests
```

## Testing Standards Compliance

### CrewAI Testing Standards

The reorganization follows CrewAI Testing Standards:

- **No full crew execution** in unit tests (causes hangs)
- **Test configuration loading** from YAML files
- **Test tool routing logic** without instantiating crews
- **Mock all external dependencies** using pytest-mock
- **Fast execution** (< 5 seconds per test suite)

### unittest.mock Ban Enforcement

The structure supports the complete ban on `unittest.mock`:

- All tests use `pytest-mock` exclusively
- Enforced by ruff, pre-commit, and the `make check-unittest-mock` grep.
  `tests/conftest_unittest_blocker.py` installs a `sys.meta_path` hook that
  would add runtime enforcement, but nothing imports that module — no `-p`
  entry references it in `pyproject.toml`'s `addopts` — so the runtime layer
  is not actually active; only three layers currently enforce the ban.
- Consistent mocking patterns across all test categories

## Benefits Realized

### Improved Maintainability

- **Clear ownership**: Each test category has a clear purpose
- **Easy navigation**: Developers can quickly find relevant tests
- **Consistent patterns**: Similar tests follow similar structures
- **Reduced duplication**: Shared fixtures and utilities

### Better Test Execution

- **Targeted testing**: Run only relevant test categories
- **Parallel execution**: Independent test suites can run in parallel
- **Faster feedback**: Unit tests complete in seconds
- **Selective integration**: Run expensive tests only when needed

### Enhanced Developer Experience

- **Clear guidelines**: Each directory has README with testing guidelines
- **Consistent structure**: Predictable organization across domains
- **Easy onboarding**: New developers can understand the structure quickly
- **Better IDE support**: Clear file organization improves navigation

## Usage Examples

### Running Specific Test Categories

```bash
# Unit tests only (fast)
uv run pytest tests/unit/ -v

# Specific crew tests
uv run pytest tests/unit/crews/stock_crew/ -v

# Flow orchestration tests
uv run pytest tests/unit/flow/ -v

# Integration tests (slow, requires API keys)
uv run pytest tests/integration/ -v -m integration

# Performance tests (there is no tests/performance/ directory — select by marker instead)
uv run pytest -v -m slow
```

### Running by Test Markers

```bash
# All crew-related tests
uv run pytest -m crew -v

# All flow-related tests
uv run pytest -m flow -v

# Core analysis integration tests
uv run pytest -m core_analysis -v

# All integration tests
uv run pytest -m integration -v
```

## Future Enhancements

### Planned Improvements

1. **Crew-specific unit tests**: Add comprehensive tests for each crew type
2. **Enhanced flow testing**: More comprehensive Flow state management tests
3. **Performance benchmarks**: Establish performance baselines
4. **Visual test reports**: Generate HTML test reports with coverage

### Extensibility

The new structure is designed for easy extension:

- **New crews**: Add to `tests/unit/crews/{new_crew}/`
- **New tools**: Add to `tests/unit/tools/`
- **New integrations**: Add to `tests/integration/{domain}/`
- **New performance tests**: Mark with `@pytest.mark.performance` or `@pytest.mark.slow` (no dedicated `tests/performance/` directory exists)

## Migration Lessons

### What Worked Well

- **Gradual migration**: Moved tests incrementally
- **Clear documentation**: Each directory has clear guidelines
- **Consistent patterns**: Applied same structure across domains
- **Validation**: Verified all tests still work after migration

### Challenges Overcome

- **Test discovery**: Ensured pytest finds all tests correctly
- **Import paths**: Updated relative imports after moves
- **Fixture sharing**: Maintained shared fixtures across directories
- **CI/CD integration**: Updated build scripts for new structure

## Related Documentation

- Testing Standards
- CrewAI Standards
- Development Standards
- [How to: Testing](../development/DEVELOPER_GUIDE.md#testing)

---

**Version**: 1.0
**Last Updated**: 2025-10-28
**Source**: Integrated from analysis/REORGANIZATION_SUMMARY.md
