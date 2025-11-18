# Test Stabilization Quick Start Guide

**Current Status**: 86.1% pass rate (435 failures / 3,160 tests)
**Target**: >95% pass rate (<50 failures)
**Estimated Timeline**: 6-8 days with parallel execution

---

## Immediate Actions

### 1. Start with Quick Wins (Phase 1)

**Expected Impact**: 180 failures fixed → 91% pass rate
**Timeline**: 1-2 days
**Parallelization**: HIGH (5 concurrent tasks)

#### Task 1A: Fix Import Errors (~80 failures)

```bash
# Run to identify all import errors
uv run pytest tests/unit/ -v --tb=short 2>&1 | grep -E "ImportError|ModuleNotFoundError" > import_errors.log

# Common patterns to fix:
# OLD: from finwiz.quantitative.config import BacktestConfig
# NEW: from finwiz.schemas.quantitative.config_models import BacktestConfig

# OLD: from finwiz.quantitative.cost_analyzer import CostAnalyzer
# NEW: from finwiz.quantitative.cost_analysis import CostAnalyzer
```

**Agent**: `@python-import-specialist`
**Priority**: 🔴 CRITICAL - START FIRST

#### Task 1B: Fix Mock Configuration (~100 failures)

```bash
# Common mock issues:
# 1. Missing attributes on mocks
# 2. Incorrect mock spec
# 3. Missing return values

# Example fix pattern:
# BEFORE:
mock_config = mocker.Mock()

# AFTER:
mock_config = mocker.Mock(spec=['api_keys', 'validate', 'get'])
mock_config.api_keys = {'OPENAI_API_KEY': 'test-key'}
mock_config.validate.return_value = True
```

**Agent**: `@pytest-expert`
**Priority**: 🔴 CRITICAL - START IN PARALLEL

---

### 2. Schema & API Fixes (Phase 2)

**Expected Impact**: 110 failures fixed → 94% pass rate
**Timeline**: 2-3 days
**Parallelization**: MEDIUM (3 concurrent tasks)

#### Task 2A: Fix Schema Validations (~60 failures)

```bash
# Common schema issues:
# 1. Renamed fields
# 2. Missing required fields
# 3. Type changes

# Example fix pattern:
# BEFORE:
portfolio = PortfolioData(
    positions=[...],
    estimated_cost=100.0  # Old field name
)

# AFTER:
portfolio = PortfolioData(
    positions=[...],
    total_estimated_cost=100.0,  # New field name
    rebalancing_metadata={...}  # New required field
)
```

**Agent**: `@pydantic-expert`
**Priority**: 🟡 HIGH - START AFTER PHASE 1

#### Task 2B: Fix API Signatures (~50 failures)

```bash
# Common signature issues:
# 1. Added/removed parameters
# 2. Changed parameter order
# 3. Changed return types

# Example fix pattern:
# BEFORE:
result = analyzer.analyze_portfolio(positions)

# AFTER:
result = analyzer.analyze_portfolio(
    positions=positions,
    config=config  # New required parameter
)
```

**Agent**: `@python-api-expert`
**Priority**: 🟡 HIGH - START AFTER PHASE 1

---

### 3. Specialized Fixes (Phase 3)

**Expected Impact**: 105 failures fixed → 98% pass rate
**Timeline**: 2-3 days
**Parallelization**: LOW (requires deep analysis)

#### Task 3A: Fix Async/Await (~30 failures)

```bash
# Common async issues:
# 1. Missing async keyword
# 2. Missing await
# 3. Missing pytest.mark.asyncio

# Example fix pattern:
# BEFORE:
def test_async_function(mocker):
    result = async_function()
    assert result == expected

# AFTER:
@pytest.mark.asyncio
async def test_async_function(mocker):
    result = await async_function()
    assert result == expected
```

**Agent**: `@async-python-expert`
**Priority**: 🟡 MEDIUM - PARALLEL WITH PHASE 3

---

## Progress Tracking Commands

### Check Current Status

```bash
# Run all tests and get summary
uv run pytest tests/unit/ -v --tb=no -q 2>&1 | tail -5

# Count failures by module
uv run pytest tests/unit/ -v --tb=no 2>&1 | grep "FAILED" | cut -d'/' -f3 | sort | uniq -c | sort -rn

# Check test execution time
time uv run pytest tests/unit/ --tb=no -q
```

### Monitor Phase Progress

```bash
# Phase 1 target: 435 → 255 failures (86.1% → 91% pass rate)
# Phase 2 target: 255 → 145 failures (91% → 94.9% pass rate)
# Phase 3 target: 145 → 40 failures (94.9% → 98.2% pass rate)
# Phase 4 target: 40 → 12 failures (98.2% → 99.6% pass rate)
```

---

## Parallel Execution Strategy

### Maximum Parallelization (Phase 1)

**5 Concurrent Agents**:

1. `@python-import-specialist` → Fix imports in tools/
2. `@python-import-specialist` → Fix imports in quantitative/
3. `@pytest-expert` → Fix mocks in tools/
4. `@pytest-expert` → Fix mocks in quantitative/
5. `@test-infrastructure-expert` → Fix mocks in utils/schemas/integration/

### Medium Parallelization (Phase 2)

**3 Concurrent Agents**:

1. `@pydantic-expert` → Fix portfolio & rebalancing schemas
2. `@pydantic-expert` → Fix deep analysis & crew schemas
3. `@python-api-expert` → Fix API signatures across all modules

### Low Parallelization (Phase 3+)

**2-3 Concurrent Agents**:

- Sequential flow fixes (not parallelizable)
- Async fixes (parallel by test file)
- Test logic fixes (parallel by domain)

---

## Success Criteria Checkpoints

### Phase 1 Checkpoint

- [ ] Pass rate ≥91% (was 86.1%)
- [ ] Import errors eliminated
- [ ] Mock configuration errors eliminated
- [ ] No new failures introduced

### Phase 2 Checkpoint

- [ ] Pass rate ≥94% (was 91%)
- [ ] Schema validation errors eliminated
- [ ] API signature errors eliminated
- [ ] No regression in Phase 1 fixes

### Phase 3 Checkpoint

- [ ] Pass rate ≥98% (was 94%)
- [ ] Async/await errors eliminated
- [ ] Flow state errors eliminated
- [ ] Test logic errors fixed

### Phase 4 Checkpoint

- [ ] Pass rate ≥99% (was 98%)
- [ ] Crew tests refactored following standards
- [ ] <15 failures remaining

### Phase 5 Checkpoint

- [ ] Test execution time <3 minutes (was 6.5 minutes)
- [ ] Parallel execution working
- [ ] No flaky tests

### Final Checkpoint

- [ ] Pass rate >95% (<50 failures)
- [ ] Test execution time <3 minutes
- [ ] Stable across 3 consecutive runs
- [ ] Coverage ≥65%
- [ ] Documentation updated

---

## Common Error Patterns Reference

### Import Errors

```python
# Pattern 1: Module reorganization
OLD: from finwiz.quantitative.config import BacktestConfig
NEW: from finwiz.schemas.quantitative.config_models import BacktestConfig

# Pattern 2: File splits
OLD: from finwiz.quantitative.cost_analyzer import CostAnalyzer, CostCalculator
NEW: from finwiz.quantitative.cost_analysis import CostAnalyzer
NEW: from finwiz.quantitative.cost_calculators import CostCalculator

# Pattern 3: Re-exports (backward compatibility)
# Original location should have: from new.location import Symbol
```

### Mock Configuration Errors

```python
# Pattern 1: Missing attributes
BEFORE: mock_obj = mocker.Mock()
AFTER: mock_obj = mocker.Mock(spec=['attr1', 'attr2'])

# Pattern 2: Missing return values
BEFORE: mock_func = mocker.Mock()
AFTER: mock_func = mocker.Mock(return_value=expected_value)

# Pattern 3: Incomplete spec
BEFORE: mock_client = mocker.Mock(spec=Client)
AFTER: mock_client = mocker.Mock(spec=Client)
        mock_client.timeout = 30
        mock_client.max_retries = 3
```

### Schema Validation Errors

```python
# Pattern 1: Renamed fields
OLD: PortfolioData(estimated_cost=100)
NEW: PortfolioData(total_estimated_cost=100)

# Pattern 2: Missing required fields
OLD: RebalancingNeed(ticker="AAPL")
NEW: RebalancingNeed(ticker="AAPL", rebalancing_metadata={...})

# Pattern 3: Type changes
OLD: portfolio_value=100  # int
NEW: portfolio_value=100.0  # float
```

### API Signature Errors

```python
# Pattern 1: New required parameter
OLD: analyze_portfolio(positions)
NEW: analyze_portfolio(positions, config=config)

# Pattern 2: Removed parameter
OLD: calculate_metrics(data, use_cache=True)
NEW: calculate_metrics(data)  # caching is always enabled

# Pattern 3: Changed return type
OLD: result = calculate()  # returns dict
NEW: result = calculate()  # returns Pydantic model
    result.model_dump()  # to get dict
```

---

## Risk Mitigation

### High-Risk Changes

1. **Flow state changes**: Can break multiple tests

   - **Mitigation**: Fix sequentially, verify after each file

2. **CrewAI test refactoring**: Large structural changes

   - **Mitigation**: Follow .kiro/steering/crewai-testing-standards.md exactly

3. **Schema changes**: Can cascade across modules
   - **Mitigation**: Create comprehensive mapping before changes

### Rollback Strategy

```bash
# If a batch of changes breaks tests:
1. git stash  # Save current changes
2. Verify tests pass without changes
3. git stash pop  # Re-apply changes
4. Fix issues incrementally
5. Commit working subset
```

---

## Next Steps

1. **Read full plan**: See TEST_STABILIZATION_PLAN.md for complete details
2. **Start Phase 1**: Deploy 5 concurrent agents for import & mock fixes
3. **Monitor progress**: Check pass rate after each phase
4. **Escalate blockers**: If any phase takes >150% of estimate

---

**Priority**: 🚨 CRITICAL - BLOCKING ALL REFACTORING
**Owner**: Task Orchestrator Bridge + Claude 007 Agents
**Status**: READY FOR EXECUTION
