# Report File Structure Documentation

This document describes the output directory structure and file naming conventions for FinWiz's report aggregation architecture.

> **Note:** An earlier version of this document also described a `manifest.json` file tracking all generated files per session. No such manifest exists in the codebase — nothing writes, reads, or validates one. That section has been removed.

## Table of Contents

1. [Directory Structure](#directory-structure)
2. [File Naming Conventions](#file-naming-conventions)
3. [File Management](#file-management)
4. [Examples](#examples)

## Directory Structure

### Overview

All reports are organized under `output/reports/{session_id}/` with subdirectories for each crew type:

```
output/reports/{session_id}/
├── stock_crew/
│   ├── AAPL_export.json          # Pydantic-validated export
│   ├── AAPL_report.html          # Python-generated HTML
│   ├── MSFT_export.json
│   └── MSFT_report.html
├── etf_crew/
│   ├── SPY_export.json
│   ├── SPY_report.html
│   ├── QQQ_export.json
│   └── QQQ_report.html
├── crypto_crew/
│   ├── BTC_export.json
│   ├── BTC_report.html
│   ├── ETH_export.json
│   └── ETH_report.html
├── deep_analysis_crew/
│   ├── AAPL_export.json
│   ├── AAPL_report.html
│   ├── IBM_export.json
│   └── IBM_report.html
├── discovery_crew/
│   ├── discovery_export.json     # No ticker (portfolio-level)
│   └── discovery_report.html
├── rebalancing_crew/
│   ├── rebalancing_export.json   # No ticker (portfolio-level)
│   └── rebalancing_report.html
```

**None of `consolidated_report.json`, `final_report.html`, or
`manifest.json` are written here.** `consolidated_report.json` is only
produced by `ReportConsolidator`, which has no caller anywhere in `src/`.
`final_report.html` is a Jinja2 template *name* inside the unused
`final_report_generator.py`, not an output path anything writes to. There
is no manifest of any kind — `manifest` doesn't appear anywhere in `src/`
or `tests/`. The actual final report is written outside this per-session
tree entirely, at `output/finwiz_family_financial_plan.html`
(`PythonReportGenerator`'s default `output_dir` is `"output"`, and
`report_crew/config/tasks.yaml:924` confirms the same path). See "Manifest
Format" below for more detail on what doesn't exist.

### Session ID Format

Session IDs are generated using ISO 8601 timestamp format:

```
{session_id} = YYYYMMDD_HHMMSS
Example: 20250125_143022
```

This format ensures:

- Chronological sorting
- Human-readable timestamps
- Unique session identification
- No special characters (filesystem-safe)

### Crew Subdirectories

Each crew has its own subdirectory under the session:

| Crew Type | Directory Name | Purpose |
|-----------|---------------|---------|
| Stock Crew | `stock_crew/` | Stock analysis reports |
| ETF Crew | `etf_crew/` | ETF analysis reports |
| Crypto Crew | `crypto_crew/` | Cryptocurrency analysis reports |
| Deep Analysis Crew | `deep_analysis_crew/` | Deep analysis for underperformers |
| Discovery Crew | `discovery_crew/` | A+ opportunity discovery |
| Rebalancing Crew | `rebalancing_crew/` | Portfolio rebalancing recommendations |

## File Naming Conventions

### Export JSON Files

**Pattern:** `{ticker}_export.json` — **no timestamp is embedded** in
per-ticker filenames, unlike a previous version of this doc claimed. The
directory tree above already shows the correct pattern
(`AAPL_export.json`), which contradicted the timestamped pattern
documented here.

**Components:**

- `{ticker}`: Asset ticker symbol (uppercase, e.g., AAPL, SPY, BTC)
- `_export.json`: Fixed suffix indicating Pydantic export

**Examples:**

```
AAPL_export.json
SPY_export.json
BTC_export.json
```

(Source: `src/finwiz/scoring/crew_export_generator.py:77-78`;
`src/finwiz/crews/etf_crew/config/tasks.yaml:308,311`;
`src/finwiz/reporting/stock_report_generator.py:100-101`.)

### Report HTML Files

**Pattern:** `{ticker}_report.html` — again, no timestamp.

**Examples:**

```
AAPL_report.html
SPY_report.html
BTC_report.html
```

### Consolidated Files — mostly do not exist

- **`consolidated_report.json`**: Only produced by `ReportConsolidator`,
  which has no caller anywhere in `src/` — it's effectively dead code.
- **`final_report.html`**: Not a real output path. It's a Jinja2 template
  *name* referenced inside the unused `final_report_generator.py`.
- **`manifest.json`**: Does not exist. `manifest` doesn't appear anywhere
  in `src/` or `tests/` — nothing writes, reads, or validates a manifest.

**The actual final report** is written to
`output/finwiz_family_financial_plan.html`, outside the per-session
`output/reports/{session_id}/` tree entirely.

## Manifest Format — NOT IMPLEMENTED

There is no manifest of any kind in this codebase. The schema, update
points, and worked examples that previously followed this heading (a
`manifest.json` supposedly tracking file status, updated at session start,
crew completion, consolidation, and final report) describe a feature that
was never built. If file-tracking/manifest functionality is added in the
future, document it here — until then, treat any reference elsewhere in
this repo's docs to a manifest as aspirational, not real.

## File Management

### Directory Creation

Directories are created automatically before file writes:

```python
from pathlib import Path

def ensure_directory(file_path: str) -> None:
    """Ensure parent directory exists for file path."""
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
```

### File Path Helpers

Standardized helper functions for generating file paths:

These illustrative helpers are not real functions in the codebase — they
show the naming convention the actual per-crew, per-ticker paths follow
(see `src/finwiz/scoring/crew_export_generator.py:77-78`). There is no
`get_consolidated_path`, `get_final_report_path`, or `get_manifest_path`
equivalent in `src/`, because none of those three files are written by
anything (see "Consolidated Files" above).

```python
def get_export_path(session_id: str, crew_name: str, ticker: str) -> str:
    """Get path for crew export JSON. No timestamp — see File Naming Conventions above."""
    return f"output/reports/{session_id}/{crew_name}/{ticker}_export.json"

def get_html_path(session_id: str, crew_name: str, ticker: str) -> str:
    """Get path for crew HTML report. No timestamp — see File Naming Conventions above."""
    return f"output/reports/{session_id}/{crew_name}/{ticker}_report.html"
```

The one file that *is* always produced — the family financial plan HTML —
lives outside this per-session tree entirely, at
`output/finwiz_family_financial_plan.html` (see "Consolidated Files"
above).

### File Validation

Validate file existence and format:

```python
def validate_export_file(file_path: str, schema_class: type) -> bool:
    """Validate export file exists and conforms to schema."""
    if not Path(file_path).exists():
        return False

    try:
        with open(file_path) as f:
            data = json.load(f)
        schema_class.model_validate(data)
        return True
    except (json.JSONDecodeError, ValidationError):
        return False
```

### Cleanup Policies

**Retention Policy:**

- Keep reports for 30 days by default
- Archive old reports to compressed storage
- Delete reports older than 90 days

**Cleanup Script:**

```bash
#!/bin/bash
# cleanup_old_reports.sh

# Archive reports older than 30 days
find output/reports -type d -mtime +30 -exec tar -czf {}.tar.gz {} \; -exec rm -rf {} \;

# Delete archives older than 90 days
find output/reports -name "*.tar.gz" -mtime +90 -delete
```

## Examples

### Example 1: Single Stock Analysis

**Directory Structure:**

```
output/reports/20250125_143022/
└── stock_crew/
    ├── AAPL_export.json
    └── AAPL_report.html
```

There is no `consolidated_report.json`, `final_report.html`, or
`manifest.json` alongside it — see "Consolidated Files" above.

### Example 2: Full Portfolio Analysis

**Directory Structure:**

```
output/reports/20250125_143022/
├── stock_crew/
│   ├── AAPL_export.json
│   ├── AAPL_report.html
│   ├── MSFT_export.json
│   └── MSFT_report.html
├── etf_crew/
│   ├── SPY_export.json
│   └── SPY_report.html
├── crypto_crew/
│   ├── BTC_export.json
│   └── BTC_report.html
├── deep_analysis_crew/
│   ├── IBM_export.json
│   └── IBM_report.html
├── discovery_crew/
│   ├── discovery_export.json
│   └── discovery_report.html
└── rebalancing_crew/
    ├── rebalancing_export.json
    └── rebalancing_report.html
```

The family financial plan HTML for this run is written separately, at
`output/finwiz_family_financial_plan.html` — not inside this session
directory.

## Best Practices

### File Naming

1. **Always use uppercase** for ticker symbols (AAPL, not aapl)
2. **Use consistent suffixes** (_export.json,_report.html) — no timestamp is embedded in the filename itself; chronological ordering comes from the session ID directory
3. **Avoid special characters** in filenames (use only alphanumeric, underscore, hyphen)

### Directory Organization

1. **One crew per subdirectory** for clear organization
2. **Session ID as the top-level directory** for grouping a run's per-crew exports
3. **No nested subdirectories** within crew folders (flat structure)

### Error Handling

1. **Create directories** before writing files
2. **Validate paths** before operations
3. **Handle missing files** gracefully
4. **Log all file operations** for debugging

## Summary

The file structure provides:

- ✅ **Clear Organization**: Crew-based subdirectories with consistent naming
- ✅ **Chronological Sorting**: Timestamp-based session ID for run ordering
- ✅ **Filesystem-Safe**: No special characters, consistent conventions

There is no manifest and no consolidated/final-report file inside the
per-session tree — see "Consolidated Files" above.

Follow these conventions to maintain consistency across the codebase.

---

**Version**: 1.0
**Last Updated**: 2025-01-25
**Related Docs**:

- [Developer Guide](REPORT_AGGREGATION_DEVELOPER_GUIDE.md)
- Architecture Design (internal spec)
- Requirements (internal spec)
