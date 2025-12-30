# Suggested Commands for FinWiz Development

## Essential Commands
```bash
# Run full portfolio analysis
crewai flow kickoff

# Install dependencies
uv sync

# Unit tests only (< 3 minutes)
make test

# All quality checks (lint + test + docs)
make check
```

## Testing Commands
```bash
# Single test file
uv run pytest tests/unit/tools/test_tool_factories.py -v

# Single test with output
uv run pytest tests/unit/tools/test_tool_factories.py::test_name -v -s

# Run with pattern matching
uv run pytest -k "test_stock" -v

# Coverage report
make coverage
```

## Code Quality
```bash
# Linting
make lint

# Auto-format
make format

# Type checking
make mypy

# Check for unittest.mock violations (BANNED)
make check-unittest-mock
```

## Documentation
```bash
# Preview docs locally
make docs-serve

# Lint markdown
make docs-lint

# Validate structure
make docs-validate
```

## HTML Reports
```bash
# Generate all HTML reports
make html-reports

# Convert JSON to HTML
make html-convert
```

## Cleanup
```bash
# Clean cache directories
make clean

# Full codebase cleanup
make cleanup
```

## Darwin-Specific Utils
Standard Unix commands work on macOS Darwin:
- `git`, `ls`, `cd`, `grep`, `find`, `cat`, `head`, `tail`
- Use `open` to open files/folders in Finder
- Use `pbcopy`/`pbpaste` for clipboard
