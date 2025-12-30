# Task Completion Checklist

## Before Committing

### 1. Run Tests
```bash
make test
```
All tests must pass. Never leave failing tests.

### 2. Run Linting
```bash
make lint && make format
```

### 3. Run Type Checking
```bash
make mypy
```

### 4. Check for unittest.mock
```bash
make check-unittest-mock
```
No unittest.mock imports allowed.

### 5. All Quality Checks
```bash
make check
```
This runs lint + test + docs validation.

## After Refactoring
- Verify ALL tests pass (not just new ones)
- Update test imports when moving code
- Fix mock paths to point to actual import locations
- Create re-export layer for backward compatibility

## Code Review Checklist
- [ ] No unittest.mock usage
- [ ] Type hints on all public functions
- [ ] Pydantic models in `schemas/` folder
- [ ] JSON serialization uses `default=str`
- [ ] File under 300 lines
- [ ] Final reporters have empty tools
- [ ] `max_reasoning_attempts` set when reasoning enabled

## Changelog
Update CHANGELOG.md when implementing features or fixes:
- Use categories: Added, Changed, Deprecated, Removed, Fixed, Security
- Include brief context about what changed and why
