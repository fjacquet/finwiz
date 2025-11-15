# Type Hints Progress Report

## Task: 2C.3 Add Missing Type Hints

**Status**: Partially Complete (In Progress)  
**Date**: 2025-01-15

## Summary

Systematic effort to add missing type hints across the FinWiz codebase to achieve mypy strict mode compliance.

### Initial State

- **Total mypy strict errors**: 2,548
- **Most common issues**:
  - Missing type parameters for generic types (dict, list, set): 334 errors
  - Function call argument issues: 448 errors
  - Attribute access on wrong types: 275 errors

### Current State

- **Total mypy strict errors**: 2,512
- **Errors fixed**: 36
- **Progress**: 1.4% reduction

### Files Fixed

1. **src/finwiz/utils/grading_system.py**
   - Added `Any` import
   - Fixed `get_portfolio_grade_summary` return type: `dict` → `dict[str, Any]`
   - Added type annotation for `grade_counts`: `dict[str, int]`
   - Added type annotation for `total_score`: `float`
   - Added type annotation for `average_score`: `float`

2. **src/finwiz/config/critical_fields_config.py**
   - Added `Any` import
   - Fixed `validate_critical_fields` parameter type: `dict` → `dict[str, Any]`

3. **src/finwiz/integration/data_transformation.py**
   - Fixed `serialize_datetime_objects` parameter type: `set | None` → `set[int] | None`

4. **src/finwiz/integration/log_formatters.py**
   - Fixed 12 function signatures with proper Optional types:
     - `dependencies: list` → `list[str] | None`
     - `output_files: list` → `list[str] | None`
     - `errors: list` → `list[str] | None`
     - `warnings: list` → `list[str] | None`
     - `recovery_suggestions: list` → `list[str] | None`
     - `transformations: list` → `list[str] | None`
     - `data_size: int` → `int | None`
     - `memory_usage: float` → `float | None`
     - `file_paths: list` → `list[str] | None`
     - `error_message: str` → `str | None`
     - `record_count: int` → `int | None`
     - `field_validations: dict` → `dict[str, Any] | None`
     - `record_counts: dict` → `dict[str, int] | None`
     - `details: dict` → `dict[str, Any] | None`

5. **src/finwiz/scoring/technical_scorer.py**
   - Added explicit type annotation for `details` dict: `dict[str, Any]`
   - Fixed type inference issue causing string assignment error

6. **src/finwiz/scoring/asset_analyzers/etf_analyzer.py**
   - Fixed None check for `aum` parameter before passing to `_score_aum`

## Remaining Work

### High-Priority Issues (317 errors)

**Missing type parameters for generic types**

- Files with most issues:
  - `src/finwiz/cli/argument_parser.py` (177 errors)
  - `src/finwiz/orchestrators/rebalancing_reporting.py` (115 errors)
  - `src/finwiz/orchestrators/portfolio_review.py` (79 errors)
  - `src/finwiz/tools/rebalancing_sections.py` (70 errors)
  - `src/finwiz/tools/html_report_generator.py` (65 errors)

**Common patterns to fix**:

```python
# Before
def func() -> dict:
    return {}

# After
def func() -> dict[str, Any]:
    return {}

# Before
param: list = None

# After
param: list[str] | None = None
```

### Medium-Priority Issues (448 errors)

**Function call argument type mismatches**

- Requires careful analysis of each call site
- May need to adjust function signatures or add type casts

### Lower-Priority Issues

- Attribute access issues (275 errors)
- Assignment type mismatches (114 errors)
- Operator type issues (68 errors)

## Recommendations

### Approach 1: Gradual Adoption (Recommended)

Continue with per-module strict checking as configured in `pyproject.toml`:

```toml
[[tool.mypy.overrides]]
module = "finwiz.utils.*"
disallow_untyped_defs = true
disallow_incomplete_defs = true
```

**Benefits**:

- Incremental progress
- Easier to review and test
- Less disruptive to development

**Next modules to enable**:

1. `finwiz.integration.*`
2. `finwiz.scoring.*`
3. `finwiz.tools.*`

### Approach 2: Automated Fixes

Use the `fix_type_hints.py` script to batch-fix common patterns:

```bash
python fix_type_hints.py
```

**Benefits**:

- Fast bulk fixes
- Consistent patterns

**Risks**:

- May introduce incorrect types
- Requires thorough testing

### Approach 3: Full Strict Mode

Enable strict mode for entire codebase and fix all 2,512 errors.

**Estimated effort**: 20-40 hours
**Benefits**: Complete type safety
**Risks**: High disruption, potential for introducing bugs

## Testing Strategy

After adding type hints:

1. Run mypy: `mypy src/finwiz --strict`
2. Run full test suite: `pytest`
3. Check for runtime issues
4. Review changes carefully

## Tools Created

### fix_type_hints.py

Automated script to fix common type hint patterns:

- Missing dict type parameters
- Missing list type parameters
- Ensures `Any` import is present

**Usage**:

```bash
python fix_type_hints.py
```

## Conclusion

**Progress made**: 36 errors fixed (1.4% reduction)

**Recommendation**: Continue with **Approach 1 (Gradual Adoption)** by enabling strict checking module-by-module. This provides the best balance of progress and stability.

**Next steps**:

1. Enable strict checking for `finwiz.integration.*` module
2. Fix remaining type issues in that module
3. Move to next module

**Estimated time to complete**:

- Per module: 2-4 hours
- Full codebase: 20-40 hours

---

**Note**: This is a low-priority improvement task. The current configuration with gradual adoption is working well and provides type safety where it matters most (utils, schemas).
