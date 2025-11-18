# Codebase Refactoring Patterns

## File Organization Principles

### Schema Models Location

- **Rule**: All Pydantic models belong in `src/finwiz/schemas/`
- **Pattern**: Domain-specific subfolders mirror domain folders
  - `schemas/quantitative/` for quantitative models
  - `schemas/rebalancing/` for rebalancing models
  - `schemas/tools/` for tool input/output models
- **Rationale**: Centralizes all data contracts in one location for easy discovery and maintenance

### Business Logic Location

- **Rule**: Business logic stays in domain-specific folders
  - `quantitative/` for quantitative analysis logic
  - `tools/` for tool implementations
  - `orchestrators/` for orchestration logic
- **Rationale**: Keeps logic close to where it's used

### Helper/Utility Location

- **Rule**: Validators, defaults, and helpers stay with their domain
  - `quantitative/config_validators.py` for config validators
  - `quantitative/config_defaults.py` for default values
- **Rationale**: Keeps related code together for easier maintenance

## File Size Guidelines

### Maximum File Sizes

- **Hard limit**: 300 lines per file
- **Ideal target**: 150-200 lines per file
- **Minimum**: 50 lines (avoid creating tiny files)

### When to Split

- File exceeds 300 lines → **Must split**
- File exceeds 250 lines → **Should split**
- File exceeds 200 lines → **Consider splitting**

### Split Strategy

1. Identify logical components
2. Extract to separate files with single responsibility
3. Create thin re-export layer for backward compatibility
4. Ensure no "monster classes" (multiple responsibilities)

## Test Maintenance During Refactoring

### Critical Rules

- **Never leave failing tests** after refactoring
- **Update test imports** when moving code
- **Fix mock paths** to point to actual import locations
- **Verify all tests pass** before marking task complete

### Mock Path Rules

- Mock at the **source of import**, not the re-export
- If code imports from `config_manager`, mock `config_manager`
- If `config_manager` imports from `utils.feature_flags`, mock `utils.feature_flags`
- Example: `mocker.patch("finwiz.utils.feature_flags.get_feature_flags")`

### Test Verification Checklist

- [ ] All existing tests still pass
- [ ] No new test failures introduced
- [ ] Mock paths updated to correct modules
- [ ] Backward compatibility maintained
- [ ] Re-export layer tested

## Backward Compatibility

### Re-export Pattern

```python
# Old location: src/finwiz/quantitative/config.py
# New structure:
# - src/finwiz/schemas/quantitative/config_models.py (models)
# - src/finwiz/quantitative/config_manager.py (logic)
# - src/finwiz/quantitative/config.py (re-exports)

# In config.py:
from finwiz.schemas.quantitative.config_models import (
    BacktestConfig,
    QuantConfig,
    ScreenerConfig,
)
from finwiz.quantitative.config_manager import (
    QuantitativeConfigManager,
    get_backtest_config,
    get_quant_config,
    get_quantitative_config_manager,
    get_screener_config,
)

__all__ = [
    "BacktestConfig",
    "QuantConfig",
    "ScreenerConfig",
    "QuantitativeConfigManager",
    "get_backtest_config",
    "get_quant_config",
    "get_quantitative_config_manager",
    "get_screener_config",
]
```

### Benefits

- Existing code importing from old location still works
- No breaking changes for consumers
- Gradual migration path for large codebases

## Pre-Refactoring Checklist

Before splitting any large file:

- [ ] **Identify patterns**: Check similar components in codebase
- [ ] **Plan structure**: Sketch out new file organization
- [ ] **Check schemas**: Do Pydantic models need to move to `schemas/`?
- [ ] **Size validation**: Ensure no file will exceed 300 lines
- [ ] **Test planning**: Identify which tests need updating
- [ ] **Backward compat**: Plan re-export layer if needed
- [ ] **Review steering**: Check existing patterns in this file
- [ ] **Execute split**: Make the changes
- [ ] **Update tests**: Fix all test imports and mocks
- [ ] **Verify tests**: Run full test suite
- [ ] **Document**: Add to LESSONS_LEARNED if new pattern discovered

## Common Mistakes to Avoid

### ❌ Don't

- Create Pydantic models in domain folders (they belong in `schemas/`)
- Leave failing tests after refactoring
- Create files without checking existing patterns
- Forget to update test mock paths
- Create "monster classes" (>300 lines)
- Skip backward compatibility layer

### ✅ Do

- Follow existing codebase patterns
- Verify all tests pass before marking complete
- Create thin re-export layers for backward compatibility
- Update test imports and mock paths
- Keep files focused and under 300 lines
- Document lessons learned for future reference

## Example: Correct Refactoring Pattern

**Before**: `src/finwiz/quantitative/config.py` (670 lines)

**After**:

```
src/finwiz/
├── schemas/quantitative/
│   └── config_models.py (270 lines) ← Pydantic models
├── quantitative/
│   ├── config.py (62 lines) ← Re-exports for backward compat
│   ├── config_manager.py (230 lines) ← Manager logic
│   ├── config_defaults.py (173 lines) ← Enums & defaults
│   ├── config_validators.py (66 lines) ← Validators
│   └── config_builders.py (32 lines) ← Backward compat
```

**Result**: 6 focused files, all <300 lines, tests passing ✅

---

**Version**: 1.0  
**Created**: 2025-11-15  
**Purpose**: Guide all future codebase refactoring work
**Source**: Lessons from Task 3.6 (Split quantitative/config.py)
