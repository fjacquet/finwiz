---
title: "Report File Structure"
description: "Understanding the concepts and design of Report File Structure"
category: "explanations"
tags:
  - "explanations"
date: "2025-10-26"
source: "explanations/REPORT_FILE_STRUCTURE.md"
---

# Report File Structure Documentation

This document describes the output directory structure, file naming conventions, and manifest format for FinWiz's report aggregation architecture.

[TOC]

## Table of Contents

1. [Directory Structure](#directory-structure)
2. [File Naming Conventions](#file-naming-conventions)
3. [Manifest Format](#manifest-format)
4. [File Management](#file-management)
5. [Examples](#examples)

## Directory Structure

### Overview

All reports are organized under `output/reports/{session_id}/` with subdirectories for each crew type:

```text
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
├── consolidated_report.json       # Python consolidation
├── final_report.html              # Python template rendering
└── manifest.json                  # File tracking metadata
```text
### Session ID Format

Session IDs are generated using ISO 8601 timestamp format:

```text
{session_id} = YYYYMMDD_HHMMSS
Example: 20250125_143022
```text
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

**Pattern:** `{ticker}_{timestamp}_export.json`

**Components:**

- `{ticker}`: Asset ticker symbol (uppercase, e.g., AAPL, SPY, BTC)
- `{timestamp}`: ISO 8601 timestamp (YYYYMMDD_HHMMSS)
- `_export.json`: Fixed suffix indicating Pydantic export

**Examples:**

```text
AAPL_20250125_143022_export.json
SPY_20250125_143045_export.json
BTC_20250125_143108_export.json
```text
**Special Cases:**

For portfolio-level crews (no specific ticker):

```text
discovery_20250125_143022_export.json
rebalancing_20250125_143022_export.json
```text
### Report HTML Files

**Pattern:** `{ticker}_{timestamp}_report.html`

**Components:**

- `{ticker}`: Asset ticker symbol (uppercase)
- `{timestamp}`: ISO 8601 timestamp (YYYYMMDD_HHMMSS)
- `_report.html`: Fixed suffix indicating HTML report

**Examples:**

```text
AAPL_20250125_143022_report.html
SPY_20250125_143045_report.html
BTC_20250125_143108_report.html
```text
**Special Cases:**

For portfolio-level crews:

```text
discovery_20250125_143022_report.html
rebalancing_20250125_143022_report.html
```text
### Consolidated Files

**Consolidated JSON:**

```text
consolidated_report.json
```text
**Final HTML Report:**

```text
final_report.html
```text
**Manifest:**

```text
manifest.json
```text
These files are always at the session root level (no timestamp in filename).

## Manifest Format

### Purpose

The manifest tracks all generated files with metadata for:

- File discovery and validation
- Status tracking (completed/failed)
- Metadata aggregation
- Debugging and auditing

### Schema

```json
{
  "session_id": "20250125_143022",
  "created_at": "2025-01-25T14:30:22Z",
  "updated_at": "2025-01-25T14:35:45Z",
  "crews": {
    "stock_crew": {
      "status": "completed",
      "analyses": [
        {
          "ticker": "AAPL",
          "asset_class": "stock",
          "status": "completed",
          "export_path": "stock_crew/AAPL_20250125_143022_export.json",
          "html_path": "stock_crew/AAPL_20250125_143022_report.html",
          "grade": "A",
          "composite_score": 0.85,
          "recommendation": "BUY",
          "created_at": "2025-01-25T14:30:22Z"
        },
        {
          "ticker": "MSFT",
          "asset_class": "stock",
          "status": "completed",
          "export_path": "stock_crew/MSFT_20250125_143030_export.json",
          "html_path": "stock_crew/MSFT_20250125_143030_report.html",
          "grade": "A+",
          "composite_score": 0.92,
          "recommendation": "BUY",
          "created_at": "2025-01-25T14:30:30Z"
        }
      ]
    },
    "etf_crew": {
      "status": "completed",
      "analyses": [
        {
          "ticker": "SPY",
          "asset_class": "etf",
          "status": "completed",
          "export_path": "etf_crew/SPY_20250125_143045_export.json",
          "html_path": "etf_crew/SPY_20250125_143045_report.html",
          "grade": "A",
          "composite_score": 0.88,
          "recommendation": "BUY",
          "created_at": "2025-01-25T14:30:45Z"
        }
      ]
    },
    "crypto_crew": {
      "status": "completed",
      "analyses": [
        {
          "ticker": "BTC",
          "asset_class": "crypto",
          "status": "completed",
          "export_path": "crypto_crew/BTC_20250125_143108_export.json",
          "html_path": "crypto_crew/BTC_20250125_143108_report.html",
          "grade": "B",
          "composite_score": 0.75,
          "recommendation": "HOLD",
          "created_at": "2025-01-25T14:31:08Z"
        }
      ]
    },
    "discovery_crew": {
      "status": "completed",
      "analyses": [
        {
          "ticker": "N/A",
          "asset_class": "mixed",
          "status": "completed",
          "export_path": "discovery_crew/discovery_20250125_143200_export.json",
          "html_path": "discovery_crew/discovery_20250125_143200_report.html",
          "opportunities_count": 5,
          "created_at": "2025-01-25T14:32:00Z"
        }
      ]
    },
    "rebalancing_crew": {
      "status": "completed",
      "analyses": [
        {
          "ticker": "N/A",
          "asset_class": "portfolio",
          "status": "completed",
          "export_path": "rebalancing_crew/rebalancing_20250125_143300_export.json",
          "html_path": "rebalancing_crew/rebalancing_20250125_143300_report.html",
          "trades_count": 3,
          "created_at": "2025-01-25T14:33:00Z"
        }
      ]
    }
  },
  "consolidated": {
    "status": "completed",
    "path": "consolidated_report.json",
    "created_at": "2025-01-25T14:34:00Z"
  },
  "final_report": {
    "status": "completed",
    "path": "final_report.html",
    "created_at": "2025-01-25T14:35:00Z"
  },
  "summary": {
    "total_analyses": 5,
    "completed_analyses": 5,
    "failed_analyses": 0,
    "total_crews": 5,
    "completed_crews": 5,
    "failed_crews": 0
  }
}
```text
### Manifest Fields

#### Root Level

| Field | Type | Description |
|-------|------|-------------|
| `session_id` | string | Unique session identifier (YYYYMMDD_HHMMSS) |
| `created_at` | string | ISO 8601 timestamp of manifest creation |
| `updated_at` | string | ISO 8601 timestamp of last update |
| `crews` | object | Map of crew names to crew metadata |
| `consolidated` | object | Consolidated report metadata |
| `final_report` | object | Final report metadata |
| `summary` | object | Aggregate statistics |

#### Crew Metadata

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Crew execution status: "completed", "failed", "pending" |
| `analyses` | array | List of analysis metadata objects |

#### Analysis Metadata

| Field | Type | Description |
|-------|------|-------------|
| `ticker` | string | Asset ticker symbol (or "N/A" for portfolio-level) |
| `asset_class` | string | Asset class: "stock", "etf", "crypto", "mixed", "portfolio" |
| `status` | string | Analysis status: "completed", "failed" |
| `export_path` | string | Relative path to JSON export |
| `html_path` | string | Relative path to HTML report |
| `grade` | string | Analysis grade: "A+", "A", "B", "C", "D", "F" (optional) |
| `composite_score` | number | Composite score 0.0-1.0 (optional) |
| `recommendation` | string | Investment recommendation: "BUY", "HOLD", "SELL" (optional) |
| `created_at` | string | ISO 8601 timestamp of analysis creation |

#### Summary Statistics

| Field | Type | Description |
|-------|------|-------------|
| `total_analyses` | integer | Total number of analyses |
| `completed_analyses` | integer | Number of completed analyses |
| `failed_analyses` | integer | Number of failed analyses |
| `total_crews` | integer | Total number of crews |
| `completed_crews` | integer | Number of completed crews |
| `failed_crews` | integer | Number of failed crews |

### Manifest Updates

The manifest is updated at key points during execution:

1. **Session Start**: Create manifest with session metadata
2. **Crew Completion**: Add crew metadata and analysis entries
3. **Consolidation**: Add consolidated report metadata
4. **Final Report**: Add final report metadata and update summary

## File Management

### Directory Creation

Directories are created automatically before file writes:

```pythonthon
from pathlib import Path

def ensure_directory(file_path: str) -> None:
    """Ensure parent directory exists for file path."""
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
```text
### File Path Helpers

Standardized helper functions for generating file paths:

```pythonthon
def get_export_path(session_id: str, crew_name: str, ticker: str) -> str:
    """Get path for crew export JSON."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"output/reports/{session_id}/{crew_name}/{ticker}_{timestamp}_export.json"

def get_html_path(session_id: str, crew_name: str, ticker: str) -> str:
    """Get path for crew HTML report."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"output/reports/{session_id}/{crew_name}/{ticker}_{timestamp}_report.html"

def get_consolidated_path(session_id: str) -> str:
    """Get path for consolidated report."""
    return f"output/reports/{session_id}/consolidated_report.json"

def get_final_report_path(session_id: str) -> str:
    """Get path for final HTML report."""
    return f"output/reports/{session_id}/final_report.html"

def get_manifest_path(session_id: str) -> str:
    """Get path for manifest file."""
    return f"output/reports/{session_id}/manifest.json"
```text
### File Validation

Validate file existence and format:

```pythonthon
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
```text
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
```text
## Examples

### Example 1: Single Stock Analysis

**Directory Structure:**

```text
output/reports/20250125_143022/
├── stock_crew/
│   ├── AAPL_20250125_143022_export.json
│   └── AAPL_20250125_143022_report.html
├── consolidated_report.json
├── final_report.html
└── manifest.json
```text
**Manifest:**

```json
{
  "session_id": "20250125_143022",
  "created_at": "2025-01-25T14:30:22Z",
  "crews": {
    "stock_crew": {
      "status": "completed",
      "analyses": [
        {
          "ticker": "AAPL",
          "asset_class": "stock",
          "status": "completed",
          "export_path": "stock_crew/AAPL_20250125_143022_export.json",
          "html_path": "stock_crew/AAPL_20250125_143022_report.html",
          "grade": "A",
          "composite_score": 0.85,
          "recommendation": "BUY"
        }
      ]
    }
  }
}
```text
### Example 2: Full Portfolio Analysis

**Directory Structure:**

```text
output/reports/20250125_143022/
├── stock_crew/
│   ├── AAPL_20250125_143022_export.json
│   ├── AAPL_20250125_143022_report.html
│   ├── MSFT_20250125_143030_export.json
│   └── MSFT_20250125_143030_report.html
├── etf_crew/
│   ├── SPY_20250125_143045_export.json
│   └── SPY_20250125_143045_report.html
├── crypto_crew/
│   ├── BTC_20250125_143108_export.json
│   └── BTC_20250125_143108_report.html
├── deep_analysis_crew/
│   ├── IBM_20250125_143130_export.json
│   └── IBM_20250125_143130_report.html
├── discovery_crew/
│   ├── discovery_20250125_143200_export.json
│   └── discovery_20250125_143200_report.html
├── rebalancing_crew/
│   ├── rebalancing_20250125_143300_export.json
│   └── rebalancing_20250125_143300_report.html
├── consolidated_report.json
├── final_report.html
└── manifest.json
```text
### Example 3: Failed Analysis

**Manifest with Failed Crew:**

```json
{
  "session_id": "20250125_143022",
  "crews": {
    "stock_crew": {
      "status": "failed",
      "error": "API rate limit exceeded",
      "analyses": []
    },
    "etf_crew": {
      "status": "completed",
      "analyses": [
        {
          "ticker": "SPY",
          "status": "completed",
          "export_path": "etf_crew/SPY_20250125_143045_export.json",
          "html_path": "etf_crew/SPY_20250125_143045_report.html"
        }
      ]
    }
  },
  "summary": {
    "total_analyses": 1,
    "completed_analyses": 1,
    "failed_analyses": 0,
    "total_crews": 2,
    "completed_crews": 1,
    "failed_crews": 1
  }
}
```text
## Best Practices

### File Naming

1. **Always use uppercase** for ticker symbols (AAPL, not aapl)
2. **Include timestamps** for versioning and chronological sorting
3. **Use consistent suffixes** (_export.json,_report.html)
4. **Avoid special characters** in filenames (use only alphanumeric, underscore, hyphen)

### Directory Organization

1. **One crew per subdirectory** for clear organization
2. **Session-level consolidation** at root for easy access
3. **Manifest at root** for quick status checks
4. **No nested subdirectories** within crew folders (flat structure)

### Manifest Management

1. **Update atomically** using temporary files and rename
2. **Include timestamps** for all operations
3. **Track failures** with error messages
4. **Aggregate statistics** for quick summaries

### Error Handling

1. **Create directories** before writing files
2. **Validate paths** before operations
3. **Handle missing files** gracefully
4. **Log all file operations** for debugging

## Summary

The file structure provides:

- ✅ **Clear Organization**: Crew-based subdirectories with consistent naming
- ✅ **Easy Discovery**: Manifest tracks all files with metadata
- ✅ **Chronological Sorting**: Timestamp-based naming for version tracking
- ✅ **Status Tracking**: Manifest includes completion status and errors
- ✅ **Filesystem-Safe**: No special characters, consistent conventions

Follow these conventions to maintain consistency across the codebase.

---

**Version**: 1.0
**Last Updated**: 2025-01-25
**Related Docs**:

- [Developer Guide](REPORT_AGGREGATION_DEVELOPER_GUIDE.md)
- [Architecture Design](../.kiro/specs/report-aggregation-architecture/design.md)
- [Requirements](../.kiro/specs/report-aggregation-architecture/requirements.md)
