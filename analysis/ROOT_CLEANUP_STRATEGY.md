# Root Folder Cleanup Strategy

## Analysis Summary

**Current State:**

- Root has 40+ files (should be ~15-20)
- Two documentation folders: `docs/` (structured) and `docs_new/` (staging/duplicates)
- Test files scattered in root
- Multiple fix/summary documents from development
- Output files (logs, HTML, JSON) that are legitimate program outputs

## Cleanup Strategy

### Phase 1: Archive Historical Documentation

**Create archive structure:**

```bash
mkdir -p docs/archive/fixes
mkdir -p docs/archive/analysis
mkdir -p docs/archive/development
```

**Move fix summaries:**

- `CODEBASE_ANALYSIS_REPORT.md` → `docs/archive/analysis/`
- `ISSUE_RESOLVED_SUMMARY.md` → `docs/archive/fixes/`
- `OPENAI_STOP_PARAMETER_FIX.md` → `docs/archive/fixes/`
- `QUICK_FIX_REFERENCE.md` → `docs/archive/fixes/`
- `REASONING_LOOP_FIX.md` → `docs/archive/fixes/`
- `RISK_SCORE_DISPLAY_FIX.md` → `docs/archive/fixes/`
- `YAHOO_FINANCE_DATA_AVAILABILITY.md` → `docs/archive/analysis/`

### Phase 2: Organize Test Files

**Create manual test directory:**

```bash
mkdir -p tests/manual
```

**Move test files:**

- `test_etf_data_fetch.py` → `tests/manual/`
- `test_etf_expense_fallback.py` → `tests/manual/`
- `test_etf_optional_fields.py` → `tests/manual/`
- `test_etf_scoring_bug.py` → `tests/manual/`
- `test_tracking_error.py` → `tests/manual/`
- `test_yahoo_finance_data.py` → `tests/manual/`
- `verify_macd_fix.py` → `tests/manual/`

**Create README:**

```bash
# tests/manual/README.md
# Manual Test Scripts

These are one-off verification scripts used during development to test specific fixes or features.
They are not part of the automated test suite but are kept for reference and manual verification.
```

### Phase 3: Relocate Reference Documentation

**Move to docs/reference/:**

- `sec-api.md` → `docs/reference/sec_api_reference.md` (already has good structure)

**Evaluate and decide:**

- `supabase.txt` → Contains tutorial content, move to `docs/reference/supabase_rag_tutorial.md` or delete if redundant
- `new.md` → Contains French requirements doc, move to `docs/archive/development/requirements_v3_french.md`

### Phase 4: Handle docs_new/

**Strategy: Merge unique content, then archive**

1. **Identify unique content in docs_new/**
   - Compare with docs/ to find non-duplicate files
   - Extract any valuable content not in docs/

2. **Merge valuable content:**
   - Move unique explanations to `docs/explanations/`
   - Move unique references to `docs/reference/`
   - Update cross-references

3. **Archive docs_new:**

   ```bash
   mv docs_new docs_archive_$(date +%Y%m%d)
   ```

### Phase 5: Keep Essential Files

**Configuration files (keep in root):**

- `.env.example`
- `.gitignore`
- `.markdownlint.jsonc`
- `.nojekyll`
- `.pre-commit-config.yaml`
- `.python-version`
- `Makefile`
- `mkdocs.yml`
- `mypy.ini`
- `pyproject.toml`
- `uv.lock`

**Documentation (keep in root):**

- `README.md` - Main project README
- `ToDo.md` - Active task tracking

**Output files (keep in root - legitimate program output):**

- `flow_execution.log`
- `deployment_status.json`
- `crewai_flow.html`

**Temporary cleanup files (delete after review):**

- `CLEANUP_PLAN.md` (this file)
- `ROOT_CLEANUP_STRATEGY.md` (this file)

## Expected Final State

### Root Directory Structure

```
finwiz/
├── .github/              # GitHub workflows
├── .kiro/                # Kiro configuration
├── analysis/             # Analysis output
├── bin/                  # Executable scripts
├── cache/                # Cache directory
├── config/               # Configuration files
├── data/                 # Data files
├── db/                   # Database files
├── docs/                 # Documentation (MkDocs)
├── examples/             # Example scripts
├── input/                # Input files
├── logs/                 # Log files
├── output/               # Output files
├── reports/              # Generated reports
├── scripts/              # Utility scripts
├── site/                 # Built documentation
├── src/                  # Source code
├── tests/                # Test suite
│   ├── unit/
│   ├── integration/
│   └── manual/           # NEW: Manual test scripts
├── .env.example
├── .gitignore
├── .markdownlint.jsonc
├── .nojekyll
├── .pre-commit-config.yaml
├── .python-version
├── crewai_flow.html      # Program output
├── deployment_status.json # Program output
├── flow_execution.log    # Program output
├── Makefile
├── mkdocs.yml
├── mypy.ini
├── pyproject.toml
├── README.md
├── ToDo.md
└── uv.lock
```

**Total root files: ~18** (down from 40+)

### Documentation Structure

```
docs/
├── index.md
├── tutorials/            # Learning-oriented
├── how-to/              # Problem-solving
├── reference/           # Information-oriented
│   ├── sec_api_reference.md  # MOVED from root
│   └── ...
├── explanations/        # Understanding-oriented
├── archive/             # NEW: Historical documentation
│   ├── fixes/          # Fix summaries
│   ├── analysis/       # Analysis reports
│   └── development/    # Development docs
└── ...
```

## Benefits

1. **Clarity**: Root directory is clean and professional
2. **Organization**: All documentation in proper locations
3. **Maintainability**: Easy to find files
4. **Preservation**: Historical docs archived, not deleted
5. **Standards**: Follows Diátaxis framework for docs

## Implementation Checklist

- [ ] Create archive directories
- [ ] Move fix summaries to archive
- [ ] Create tests/manual/ directory
- [ ] Move test files to tests/manual/
- [ ] Create tests/manual/README.md
- [ ] Move sec-api.md to docs/reference/
- [ ] Evaluate supabase.txt and new.md
- [ ] Analyze docs_new/ for unique content
- [ ] Merge unique content from docs_new/
- [ ] Archive docs_new/ folder
- [ ] Verify mkdocs.yml configuration
- [ ] Test documentation build: `make docs-build`
- [ ] Update README if needed
- [ ] Commit changes with clear message

## Rollback Plan

All operations are moves, not deletions:

- Archive directories contain all moved content
- docs_archive_YYYYMMDD preserves docs_new/
- Git history allows reverting any changes
- No data loss risk

---

**Status**: Ready for implementation
**Risk**: Low (no deletions, only organization)
**Time**: 20-30 minutes
