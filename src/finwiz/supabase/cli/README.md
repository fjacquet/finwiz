# Supabase Migration CLI

Command-line interface for migrating file-based exports to Supabase.

## Overview

The migration CLI scans the `output/` directory for JSON export files and migrates them to the Supabase database. It includes:

- **Idempotency**: Prevents duplicate migrations by tracking migrated files
- **Dry-run mode**: Preview migrations without executing
- **Progress tracking**: Visual progress bar during migration
- **Error reporting**: Detailed error messages and summary report
- **Asset class filtering**: Migrate specific asset classes only

## Prerequisites

1. **Supabase configured**: Set environment variables:
   ```bash
   SUPABASE_ENABLED=true
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-anon-key
   ```

2. **Database schema**: Ensure tables exist (see `db/migrations/`)

## Usage

### Basic Migration

Migrate all exports:

```bash
python -m finwiz.supabase.cli.migrate
```

Or using the main entry point:

```bash
python src/finwiz/main.py migrate
```

### Dry-Run Mode

Preview migration without executing:

```bash
python -m finwiz.supabase.cli.migrate --dry-run
```

This shows:
- Total files found
- Which files will be migrated
- Which files will be skipped (already migrated)

### Migrate Specific Asset Classes

Migrate only stock exports:

```bash
python -m finwiz.supabase.cli.migrate --asset-class stock
```

Migrate multiple asset classes:

```bash
python -m finwiz.supabase.cli.migrate --asset-class stock --asset-class etf
```

### Force Re-Migration

Re-migrate files that were already migrated:

```bash
python -m finwiz.supabase.cli.migrate --force
```

**Warning**: This will create duplicate records in the database.

### Custom Output Directory

Migrate from a custom directory:

```bash
python -m finwiz.supabase.cli.migrate --output-dir /path/to/exports
```

### Verbose Logging

Enable debug logging:

```bash
python -m finwiz.supabase.cli.migrate --verbose
```

## Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--output-dir DIR` | Base directory for exports | `output` |
| `--asset-class CLASS` | Asset class to migrate (stock, etf, crypto) | All |
| `--dry-run` | Preview without executing | False |
| `--force` | Force re-migration of existing files | False |
| `--verbose`, `-v` | Enable debug logging | False |

## Output

### Progress Bar

During migration, a progress bar shows:
- Current file number / total files
- Percentage complete
- Current file being processed

Example:
```
[████████████████████████--------------------------] 48/100 (48.0%) - output/stock/AAPL_default.json
```

### Summary Report

After migration, a summary report shows:
```
======================================================================
MIGRATION SUMMARY
======================================================================
Total files scanned:    100
Successfully migrated:  95
Skipped (duplicates):   3
Failed:                 2
Success rate:           95.0%

----------------------------------------------------------------------
ERRORS:
----------------------------------------------------------------------
  • output/stock/INVALID_default.json
    Error: Invalid JSON in file
  • output/etf/BROKEN_default.json
    Error: Missing required field: composite_score
======================================================================
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success (all files migrated or skipped) |
| 1 | Failure (one or more files failed) |
| 130 | Interrupted by user (Ctrl+C) |

## Idempotency

The migration service tracks migrated files using SHA256 hashes. This prevents duplicate migrations when running the command multiple times.

To check if a file has been migrated:
1. Calculate SHA256 hash of file content
2. Query `migration_history` table for matching hash
3. Skip if found (unless `--force` is used)

## File Format

Expected JSON export format:

```json
{
  "ticker": "AAPL",
  "asset_class": "stock",
  "composite_score": 0.85,
  "grade": "A",
  "recommendation": "BUY",
  "analysis_timestamp": "2025-10-30T22:17:44Z",
  ...
}
```

Required fields:
- `ticker`: Asset ticker symbol
- `asset_class`: Asset class (stock, etf, crypto)
- `composite_score`: Composite score (0.0-1.0)
- `grade`: Grade (A+, A, B, C, D, F)
- `recommendation`: Recommendation (BUY, HOLD, SELL)

## Troubleshooting

### "Supabase is not enabled"

Set environment variables:
```bash
export SUPABASE_ENABLED=true
export SUPABASE_URL=https://your-project.supabase.co
export SUPABASE_KEY=your-anon-key
```

### "No export files found"

Check that:
1. Output directory exists (`output/`)
2. Asset class directories exist (`output/stock/`, etc.)
3. JSON files exist in asset class directories

### "Invalid JSON in file"

The JSON file is malformed. Check:
1. File is valid JSON (use `jq` or JSON validator)
2. File is not corrupted
3. File encoding is UTF-8

### "Missing required field"

The export data is missing required fields. Check:
1. File contains all required fields (see File Format above)
2. Field names match exactly (case-sensitive)

## Examples

### Migrate all exports with progress

```bash
python -m finwiz.supabase.cli.migrate
```

### Preview migration for stocks only

```bash
python -m finwiz.supabase.cli.migrate --asset-class stock --dry-run
```

### Force re-migration with verbose logging

```bash
python -m finwiz.supabase.cli.migrate --force --verbose
```

### Migrate from custom directory

```bash
python -m finwiz.supabase.cli.migrate --output-dir /data/finwiz/exports
```

## Integration with FinWiz

The migration CLI can be integrated into deployment workflows:

```bash
# After deployment, migrate existing exports
python -m finwiz.supabase.cli.migrate

# Or as part of a script
python src/finwiz/main.py migrate --dry-run  # Preview
python src/finwiz/main.py migrate            # Execute
```

## Performance

Migration performance depends on:
- Number of files to migrate
- Network latency to Supabase
- Database performance

Typical performance:
- **Small dataset** (< 100 files): 10-30 seconds
- **Medium dataset** (100-1000 files): 1-5 minutes
- **Large dataset** (> 1000 files): 5-30 minutes

The migration service uses:
- Async operations for non-blocking execution
- Exponential backoff retry for failed operations
- Batch processing for efficient database writes

---

**Version**: 1.0  
**Created**: 2025-10-31  
**Status**: Ready for use
