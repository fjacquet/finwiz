# FinWiz Root Folder Cleanup Plan

## Current Issues

### 1. Root Folder Clutter

The root directory contains 40+ files, many of which are temporary documentation, fix summaries, or test files that should be organized elsewhere.

### 2. Duplicate Documentation Folders

- `docs/` - Main MkDocs documentation (properly structured with Diátaxis framework)
- `docs_new/` - Appears to be a duplicate/staging area with overlapping content

### 3. Misplaced Test Files

Several test files are in root instead of `tests/` directory:

- `test_etf_data_fetch.py`
- `test_etf_expense_fallback.py`
- `test_etf_optional_fields.py`
- `test_etf_scoring_bug.py`
- `test_tracking_error.py`
- `test_yahoo_finance_data.py`
- `verify_macd_fix.py`

### 4. Temporary/Status Files

- `flow_execution.log`
- `deployment_status.json`
- `crewai_flow.html`
- `supabase.txt`
- `new.md`

### 5. Fix/Summary Documentation

Multiple fix summary files that should be archived:

- `CODEBASE_ANALYSIS_REPORT.md`
- `ISSUE_RESOLVED_SUMMARY.md`
- `OPENAI_STOP_PARAMETER_FIX.md`
- `QUICK_FIX_REFERENCE.md`
- `REASONING_LOOP_FIX.md`
- `RISK_SCORE_DISPLAY_FIX.md`
- `YAHOO_FINANCE_DATA_AVAILABILITY.md`

## Cleanup Actions

### Phase 1: Archive Historical Documentation

**Create archive directory:**

```bash
mkdir -p docs/archive/fixes
mkdir -p docs/archive/analysis
```

**Move fix summaries to archive:**

- `CODEBASE_ANALYSIS_REPORT.md` → `docs/archive/analysis/`
- `ISSUE_RESOLVED_SUMMARY.md` → `docs/archive/fixes/`
- `OPENAI_STOP_PARAMETER_FIX.md` → `docs/archive/fixes/`
- `QUICK_FIX_REFERENCE.md` → `docs/archive/fixes/`
- `REASONING_LOOP_FIX.md` → `docs/archive/fixes/`
- `RISK_SCORE_DISPLAY_FIX.md` → `docs/archive/fixes/`
- `YAHOO_FINANCE_DATA_AVAILABILITY.md` → `docs/archive/analysis/`

### Phase 2: Move Test Files

**Move to tests directory:**

```bash
mv test_*.py tests/manual/
mv verify_macd_fix.py tests/manual/
```

Create `tests/manual/README.md` explaining these are one-off verification tests.

### Phase 3: Clean Temporary Files

**Keep output files (real program output):**

- `flow_execution.log` - Keep (program output)
- `deployment_status.json` - Keep (program output)
- `crewai_flow.html` - Keep (program output)

**Relocate or remove:**

- `supabase.txt` → Move to `docs/reference/` if contains useful info
- `new.md` → Delete if scratch file, or move to docs if useful

### Phase 4: Consolidate Documentation Folders

**Decision needed:** Keep `docs/` or `docs_new/`?

**Recommendation: Keep `docs/`, archive `docs_new/`**

Reasoning:

- `docs/` has proper Diátaxis structure (tutorials, how-to, reference, explanations)
- `docs/` is configured in `mkdocs.yml`
- `docs_new/` appears to be a staging area with many duplicates

**Action:**

```bash
# Review docs_new for any unique content
# Move unique content to docs/
# Archive docs_new
mv docs_new docs_archive_$(date +%Y%m%d)
```

### Phase 5: Organize Remaining Documentation

**Keep in root (essential files):**

- `README.md` - Main project README
- `ToDo.md` - Active task tracking
- `sec-api.md` - API documentation (consider moving to docs/reference/)

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

### Phase 6: Update Documentation Structure

**Ensure docs/ follows Diátaxis:**

```
docs/
├── index.md                    # Homepage
├── tutorials/                  # Learning-oriented
│   ├── getting_started.md
│   ├── first_analysis.md
│   └── portfolio_analysis.md
├── how-to/                    # Problem-solving
│   ├── setup_environment.md
│   ├── configure_api_keys.md
│   └── performance_optimization.md
├── reference/                 # Information-oriented
│   ├── api/
│   ├── cli_commands.md
│   └── schemas/
├── explanations/              # Understanding-oriented
│   ├── architecture.md
│   ├── flow_architecture.md
│   └── design_principles.md
└── archive/                   # Historical documentation
    ├── fixes/
    └── analysis/
```

## Expected Results

### Root Directory After Cleanup

**Files (15-20 total):**

- Configuration files (10-12)
- Essential documentation (2-3)
- Lock files (1-2)

**Directories:**

- Standard project directories (src, tests, docs, etc.)
- No duplicate or staging directories

### Benefits

1. **Clarity**: Easy to find essential files
2. **Maintainability**: Clear organization reduces confusion
3. **Professionalism**: Clean root directory for open source project
4. **Documentation**: Single source of truth in `docs/`
5. **Testing**: All tests in proper location

## Implementation Order

1. ✅ Create archive directories
2. ✅ Move fix summaries to archive
3. ✅ Move test files to tests/manual/
4. ✅ Remove temporary files
5. ✅ Evaluate docs_new/ content
6. ✅ Archive or merge docs_new/
7. ✅ Update documentation index
8. ✅ Verify mkdocs.yml configuration
9. ✅ Test documentation build
10. ✅ Update README with new structure

## Validation

After cleanup, verify:

- [ ] Root directory has <20 files
- [ ] All tests in tests/ directory
- [ ] Documentation builds successfully: `make docs-build`
- [ ] No broken links in documentation
- [ ] All essential files accessible
- [ ] Git history preserved

## Rollback Plan

If issues arise:

1. All moves are reversible (files not deleted)
2. Archive directories contain all moved content
3. Git history allows reverting changes
4. Documentation backup in docs_archive_YYYYMMDD/

---

**Status**: Ready for implementation
**Estimated Time**: 30-45 minutes
**Risk Level**: Low (no deletions, only moves)
