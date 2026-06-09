# Simplification Pass 1 — Delete Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove all dead and unused code, scripts, docs, and feature flags identified in the approved spec (`docs/superpowers/specs/2026-06-09-codebase-simplification-design.md`), with `make check` green after every task.

**Architecture:** Pure deletion pass — no behavior changes, no refactors. Every task follows the same shape: verify the target is dead with greps, delete code + tests + docs + wiring together, grep for stragglers, run `make check`, commit. Backtesting and rebalancing history are KEEP (do not touch).

**Tech Stack:** Python 3.12, uv, pytest (pytest-mock only — unittest.mock is banned), ruff, mkdocs, pre-commit hooks (docs validation + mkdocs build run on every commit). Prefix shell commands with `rtk` per project convention; use `rtk proxy <cmd>` when you need unfiltered output.

**Verified facts this plan relies on (re-verify in each task before deleting):**
- `tools/notification_service.py` is referenced only by its own test.
- `orchestrators/portfolio_review_enhanced.py` has zero importers (only a stale `.pyc`). It is the ONLY importer of `reporting/portfolio_review_html.py`.
- `orchestrators/portfolio_review_orchestrator.py` is ALIVE (imported at `src/finwiz/orchestrators/validation_orchestrator.py:94`) — keep it; it only mentions `portfolio_review_html` in a docstring.
- Makefile targets `html-example` (line 273) and `html-integration` (line 278) are the only consumers of `examples/`.
- Only these scripts are wired into Makefile / CI / pre-commit: `analyze_test_failures.py`, `check_new_file_size.py`, `cleanup_temp_files.py`, `cleanup_master.py`, `fix_csv_currencies.py`, `generate_html_reports.py`, `generate_demo.py`, `validate_docs.py`.
- 11 feature flags are defined in `create_default_flags()` but never queried (list in Task 6).

---

### Task 0: Branch setup

**Files:** none

- [ ] **Step 1: Create the working branch from up-to-date main**

```bash
rtk git checkout main && rtk git pull && rtk git checkout -b chore/simplify-pass1-delete
```

- [ ] **Step 2: Confirm baseline is green**

Run: `make check`
Expected: exits 0. If it fails, STOP — fix main first; this plan assumes a green baseline.

---

### Task 1: Delete the notification service

**Files:**
- Delete: `src/finwiz/tools/notification_service.py`
- Delete: `tests/unit/tools/test_notification_service.py`
- Delete: `docs/explanations/NOTIFICATION_SERVICE_ARCHITECTURE.md`

- [ ] **Step 1: Verify it is still dead (no new callers since planning)**

```bash
rtk proxy grep -rn "notification_service\|NotificationService" src/finwiz tests --include='*.py' | grep -v "tools/notification_service.py" | grep -v "test_notification_service.py"
```

Expected: no output. If there IS output, STOP and report — the module gained a caller.

- [ ] **Step 2: Delete the three files**

```bash
rtk git rm src/finwiz/tools/notification_service.py tests/unit/tools/test_notification_service.py docs/explanations/NOTIFICATION_SERVICE_ARCHITECTURE.md
```

- [ ] **Step 3: Straggler grep (docs, configs, nav)**

```bash
rtk proxy grep -rni "notification" mkdocs.yml docs Makefile .env.example 2>/dev/null | grep -vi "push\|desktop" | head
```

Expected: no hits referring to the deleted service. Remove any doc lines that link to the deleted page.

- [ ] **Step 4: Validate**

Run: `make check`
Expected: exits 0 (pre-commit's mkdocs build will also catch broken nav at commit time).

- [ ] **Step 5: Commit**

```bash
rtk git add -A && rtk git commit -m "chore: delete dead notification service (only referenced by its own test)"
```

---

### Task 2: Delete examples/ and its Makefile targets

**Files:**
- Delete: `examples/` (entire directory, 18 files — user confirmed unused)
- Modify: `Makefile` (help lines 34–35, targets at lines 273–280)

- [ ] **Step 1: Verify nothing outside Makefile references examples/**

```bash
rtk proxy grep -rn "from examples\|import examples\|examples/" src/finwiz tests .github .pre-commit-config.yaml pyproject.toml mkdocs.yml 2>/dev/null | head
```

Expected: no output (docs/ hits are handled in Step 3).

- [ ] **Step 2: Delete the directory and remove the Makefile targets**

```bash
rtk git rm -r examples/
```

In `Makefile`, delete these two help lines (currently 34–35):

```makefile
	@echo "  make html-example - Run inline HTML generation examples"
	@echo "  make html-integration - Run HTML integration examples"
```

and these two targets (currently 273–280):

```makefile
html-example:
	@echo "🚀 Running inline HTML generation examples..."
	python examples/inline_html_example.py
	@echo "✅ Examples completed - check output/examples/ directory"

html-integration:
	@echo "🔄 Running HTML integration examples..."
	python examples/integration_example.py
```

Also remove `html-example` / `html-integration` from any `.PHONY:` line.

- [ ] **Step 3: Straggler grep in docs**

```bash
rtk proxy grep -rn "examples/" docs --include='*.md' | grep -v superpowers | head
```

Remove or rewrite any doc lines pointing at deleted demos (e.g. in `docs/tutorials/USER_GUIDE.md`).

- [ ] **Step 4: Validate**

Run: `make check`
Expected: exits 0.

- [ ] **Step 5: Commit**

```bash
rtk git add -A && rtk git commit -m "chore: delete unused examples/ demos and their Makefile targets"
```

---

### Task 3: Delete the dead portfolio-review report chain

**Files:**
- Delete: `src/finwiz/orchestrators/portfolio_review_enhanced.py`
- Delete: `src/finwiz/reporting/portfolio_review_html.py`
- Modify: `src/finwiz/orchestrators/portfolio_review_orchestrator.py:10` (stale docstring only — this module is ALIVE, do not delete it)

- [ ] **Step 1: Verify the chain is dead**

```bash
rtk proxy grep -rn "portfolio_review_enhanced" src/finwiz tests Makefile .github --include='*.py' | grep -v "orchestrators/portfolio_review_enhanced.py"
rtk proxy grep -rn "portfolio_review_html" src/finwiz tests --include='*.py' | grep -v "portfolio_review_enhanced.py" | grep -v "portfolio_review_html.py"
```

Expected: first command → no output. Second command → only the docstring mention at `portfolio_review_orchestrator.py:10`. Anything else: STOP and report.

- [ ] **Step 2: Delete the two modules and any dedicated tests**

```bash
rtk git rm src/finwiz/orchestrators/portfolio_review_enhanced.py src/finwiz/reporting/portfolio_review_html.py
rtk proxy grep -rln "portfolio_review_enhanced\|portfolio_review_html" tests | xargs -r rtk git rm
```

- [ ] **Step 3: Fix the stale docstring**

In `src/finwiz/orchestrators/portfolio_review_orchestrator.py` line 10, the docstring says HTML generation is delegated to `finwiz.reporting.portfolio_review_html`. Replace that sentence to point at the real production path:

```python
HTML generation is delegated to the reporting layer (finwiz.reporting.python_report_generator).
```

- [ ] **Step 4: Straggler grep (docs + reporting `__init__` exports)**

```bash
rtk proxy grep -rn "portfolio_review_html\|portfolio_review_enhanced" src/finwiz docs mkdocs.yml | head
```

Expected: no output. Remove any `__init__.py` re-exports or doc references found.

- [ ] **Step 5: Validate**

Run: `make check`
Expected: exits 0. The existing tests in `tests/unit/orchestrators/test_portfolio_review.py` cover the kept orchestrator and must still pass.

- [ ] **Step 6: Commit**

```bash
rtk git add -A && rtk git commit -m "chore: delete orphaned portfolio_review_enhanced + portfolio_review_html (production report path is python_report_generator)"
```

---

### Task 4: Purge orphaned scripts/

**Files:**
- Keep (wired into Makefile/CI/pre-commit — verified): `scripts/analyze_test_failures.py`, `scripts/check_new_file_size.py`, `scripts/cleanup_temp_files.py`, `scripts/cleanup_master.py`, `scripts/fix_csv_currencies.py`, `scripts/generate_html_reports.py`, `scripts/generate_demo.py`, `scripts/validate_docs.py`, `scripts/__init__.py`
- Delete: everything else in `scripts/`, including `archive/`, the three `README*/QUICK_START*` markdown files, both `.sh` jekyll scripts, `rollback.sh`, `verify_*.sh`, and all unwired Python scripts (`build_docs.py`, `deploy_docs.py`, `migrate_docs.py`, `migration_models.py`, `migration_rules.yml`, `create_missing_docs.py`, `convert_json_to_html.py`, `run_python_analysis.py`, `run_python_analysis_fixed.py`, `validate_finwiz_architecture.py`, `mkdocs_schema_plugin.py`, `setup_schema_plugin.py`, `test_schema_plugin.py`, `integrate_schemas.py`, `fix_mypy_mechanical.py`, `fix_mypy_tier1.py`, `extract_mypy_context.py`, `check_imports.py`, `check_docs_quality.py`, `check_jekyll_syntax.py`, `check_stage_contract.py`, `add_json_requirements.py`, `monitor_deployment.py`, `monitor_supabase_metrics.py`, `organize_documentation.py`, `invalidate_fact_pack.py`, `test_graceful_degradation.py`, `test_report_generation.py`, `validate_build.py`, `validate_report.py`, `validate_success_criteria.py`, `validate_supabase_deployment.py`, `verify_html_reports.py`, `verify_logging.py`, `zero_downtime_deploy.py`)

- [ ] **Step 1: Mechanically verify every deletion candidate is unwired**

```bash
cd /Users/fjacquet/Projects/finwiz
KEEP="analyze_test_failures|check_new_file_size|cleanup_temp_files|cleanup_master|fix_csv_currencies|generate_html_reports|generate_demo|validate_docs|__init__"
for f in scripts/*.py scripts/*.sh scripts/*.yml scripts/*.md; do
  base=$(basename "$f"); stem="${base%.*}"
  echo "$stem" | grep -qE "$KEEP" && continue
  hits=$(grep -rln "$stem" Makefile .github .pre-commit-config.yaml mkdocs.yml pyproject.toml src/finwiz tests 2>/dev/null | head -3)
  [ -n "$hits" ] && echo "WIRED — DO NOT DELETE: $f -> $hits"
done
```

Expected: no `WIRED` lines. Any file flagged WIRED moves to the keep list — record it in the commit message.

- [ ] **Step 2: Check kept scripts don't import deleted ones**

```bash
rtk proxy grep -n "^import \|^from " scripts/analyze_test_failures.py scripts/check_new_file_size.py scripts/cleanup_temp_files.py scripts/cleanup_master.py scripts/fix_csv_currencies.py scripts/generate_html_reports.py scripts/generate_demo.py scripts/validate_docs.py | grep -v "^.*:.*\b(os|sys|re|json|pathlib|argparse|subprocess|typing|collections|datetime)\b" | head -20
```

Expected: no imports of sibling scripts slated for deletion. If found, keep that sibling too.

- [ ] **Step 3: Delete everything not on the keep list**

```bash
cd /Users/fjacquet/Projects/finwiz/scripts
rtk git rm -r archive/ QUICK_START_VERIFY.md README_VALIDATION.md README_VERIFY_DATA_QUALITY.md \
  add_json_requirements.py build_docs.py check-jekyll-syntax.sh check_docs_quality.py check_imports.py \
  check_jekyll_syntax.py check_stage_contract.py convert_json_to_html.py create_missing_docs.py \
  deploy_docs.py extract_mypy_context.py fix_all_jekyll_syntax.py fix_mypy_mechanical.py fix_mypy_tier1.py \
  integrate_schemas.py invalidate_fact_pack.py migrate_docs.py migration_models.py migration_rules.yml \
  mkdocs_schema_plugin.py monitor_deployment.py monitor_supabase_metrics.py organize_documentation.py \
  rollback.sh run_python_analysis.py run_python_analysis_fixed.py setup_schema_plugin.py \
  switch-to-jekyll.sh test_graceful_degradation.py test_report_generation.py test_schema_plugin.py \
  validate_build.py validate_finwiz_architecture.py validate_report.py \
  validate_success_criteria.py validate_supabase_deployment.py verify_data_integrity.sh \
  verify_data_quality.sh verify_diagnostic_logging.sh verify_html_reports.py verify_logging.py \
  zero_downtime_deploy.py
```

**NOT in the list (keep — wired):** `validate_docs.py` (pre-commit line 33), `check_new_file_size.py` (pre-commit + CI), and the other 6 keep-list scripts. Double-check the command above contains none of them before running.

- [ ] **Step 4: Straggler grep**

```bash
rtk proxy grep -rn "create_missing_docs\|convert_json_to_html\|migrate_docs\|build_docs\|deploy_docs\|verify_html_reports\|schema_plugin" Makefile .github .pre-commit-config.yaml mkdocs.yml docs --include='*' 2>/dev/null | grep -v superpowers | head
```

Expected: no output. Remove any doc lines referencing deleted scripts.

- [ ] **Step 5: Validate**

Run: `make check`
Expected: exits 0. Also run `uv run pre-commit run --all-files` once — it exercises validate_docs + mkdocs build directly. Expected: all hooks pass or skip.

- [ ] **Step 6: Commit**

```bash
rtk git add -A && rtk git commit -m "chore: purge orphaned scripts/ (keep only Makefile/CI/pre-commit-wired scripts)"
```

---

### Task 5: Purge meta-docs and historical doc logs

**Files:**
- Delete: `docs/DOCUMENTATION_ENHANCEMENT_SUMMARY.md`, `docs/DOCUMENTATION_ORGANIZATION.md`, `docs/IMPROVEMENT_PLAN.md`, `docs/MKDOCS_SETUP.md`, `docs/QUICK_START_MKDOCS.md`
- Delete: `docs/fixes/` (entire directory, 6 files of historical fix logs)
- Delete: `docs/reference/IMPLEMENTATION_SUMMARIES.md`
- Modify: `mkdocs.yml` nav (only if any of these appear — verified absent at planning time)

- [ ] **Step 1: Verify none are in the mkdocs nav or cross-linked**

```bash
rtk proxy grep -n "DOCUMENTATION_ENHANCEMENT_SUMMARY\|DOCUMENTATION_ORGANIZATION\|IMPROVEMENT_PLAN\|MKDOCS_SETUP\|QUICK_START_MKDOCS\|fixes/\|IMPLEMENTATION_SUMMARIES" mkdocs.yml
rtk proxy grep -rln "DOCUMENTATION_ENHANCEMENT_SUMMARY\|IMPROVEMENT_PLAN\|MKDOCS_SETUP\|QUICK_START_MKDOCS\|IMPLEMENTATION_SUMMARIES\|fixes/" docs --include='*.md' | grep -v superpowers | head
```

Expected: no nav hits. For cross-links found in other docs, delete the linking lines as part of Step 2.

- [ ] **Step 2: Delete**

```bash
rtk git rm docs/DOCUMENTATION_ENHANCEMENT_SUMMARY.md docs/DOCUMENTATION_ORGANIZATION.md docs/IMPROVEMENT_PLAN.md docs/MKDOCS_SETUP.md docs/QUICK_START_MKDOCS.md docs/reference/IMPLEMENTATION_SUMMARIES.md
rtk git rm -r docs/fixes/
```

- [ ] **Step 3: Sweep for auto-generated doc stubs**

`scripts/create_missing_docs.py` (deleted in Task 4) mass-produced templated stub pages. Find its leftovers by template fingerprint — open `create_missing_docs.py` in git history (`rtk git show HEAD~1:scripts/create_missing_docs.py | head -60`) to read the exact boilerplate phrases it emits, then:

```bash
rtk proxy grep -rln "<distinctive boilerplate phrase from the generator>" docs --include='*.md' | grep -v superpowers
```

For each hit: if the page has no inbound links (`grep -rn "<filename>" docs mkdocs.yml --include='*' | grep -v "<the file itself>"` → empty) and its content is still the unmodified template, `rtk git rm` it.

- [ ] **Step 4: Validate (docs hooks are the real gate here)**

Run: `uv run mkdocs build --strict 2>&1 | tail -5` then `make check`
Expected: both exit 0.

- [ ] **Step 5: Commit**

```bash
rtk git add -A && rtk git commit -m "docs: purge meta-docs, historical fix logs, and auto-generated stubs (git history records these)"
```

---

### Task 6: Remove never-queried feature flags

**Files:**
- Modify: `src/finwiz/config/features/definitions.py` (`create_default_flags()`, lines 89–327)
- Modify: `.env.example` (drop matching `FF_*` lines)
- Modify: feature-flag tests under `tests/` that assert on the removed names or on flag counts

**Candidate flags (defined but never queried via `is_feature_enabled(...)` or `feature_flags.is_enabled(...)` — verified at planning time):**
`advanced_technical_analysis`, `async_execution`, `chart_analysis`, `derivatives_pricing`, `enhanced_sentiment_analysis`, `intelligent_caching`, `portfolio_optimization`, `portfolio_review`, `rebalancing_api`, `rebalancing_monitoring`, `twelve_data_integration`

- [ ] **Step 1: Re-verify each candidate is unqueried (guards against dynamic lookups)**

```bash
cd /Users/fjacquet/Projects/finwiz
for f in advanced_technical_analysis async_execution chart_analysis derivatives_pricing enhanced_sentiment_analysis intelligent_caching portfolio_optimization portfolio_review rebalancing_api rebalancing_monitoring twelve_data_integration; do
  echo "== $f"
  grep -rn "\"$f\"\|'$f'" src/finwiz --include='*.py' | grep -v "features/definitions.py"
done
```

Expected: no hits per flag (a hit means the flag IS used — drop it from the removal list and note it). Note: `portfolio_review` the FLAG is distinct from the `portfolio_review_orchestrator` MODULE; only string-literal flag lookups count.

- [ ] **Step 2: Remove each confirmed flag's `FeatureFlagConfig(...)` block**

In `create_default_flags()` each flag is one dict entry of this shape — delete the whole entry for each confirmed-dead flag:

```python
        "advanced_technical_analysis": FeatureFlagConfig(
            name="advanced_technical_analysis",
            enabled=get_env_bool("FF_ADVANCED_TECHNICAL", True),
            strategy=FeatureFlagStrategy.PERCENTAGE,
            rollout_percentage=get_env_float("FF_ADVANCED_TECHNICAL_ROLLOUT", 100.0),
            fallback_strategy=FallbackStrategy.REDUCED_FUNCTIONALITY,
            description="Advanced technical indicators and confluence detection",
        ),
```

Locate each block with: `rtk proxy grep -n 'name="<flag>"' src/finwiz/config/features/definitions.py`

- [ ] **Step 3: Clean .env.example and tests**

```bash
rtk proxy grep -n "FF_ADVANCED_TECHNICAL\|FF_CHART\|FF_ENHANCED_SENTIMENT\|FF_TWELVE_DATA\|FF_ASYNC\|FF_DERIVATIVES\|FF_INTELLIGENT_CACHING\|FF_PORTFOLIO_OPTIMIZATION\|FF_PORTFOLIO_REVIEW\|FF_REBALANCING_API\|FF_REBALANCING_MONITORING" .env.example
rtk proxy grep -rln "advanced_technical_analysis\|chart_analysis\|enhanced_sentiment_analysis\|twelve_data_integration\|derivatives_pricing\|intelligent_caching\|portfolio_optimization\|rebalancing_api\|rebalancing_monitoring\|async_execution" tests --include='*.py'
```

Delete matching `.env.example` lines. In each test file found: remove assertions/parametrize entries for removed flags; fix any flag-count assertions.

- [ ] **Step 4: Validate**

Run: `make test` then `make check`
Expected: exits 0, no test failures.

- [ ] **Step 5: Commit**

```bash
rtk git add -A && rtk git commit -m "chore: remove feature flags that are defined but never queried"
```

**Known oddity (record in PR, do NOT fix here):** `is_feature_enabled("batch_prefetch")` is queried in src but `batch_prefetch` has no definition in `create_default_flags()` — it falls through to default behavior. Out of scope for a deletion pass.

---

### Task 7: Deduplicate top-level doc guides into Diátaxis structure

**Files:**
- Compare/merge: `docs/USER_GUIDE.md` (31K, in nav line 161) vs `docs/tutorials/USER_GUIDE.md`
- Move: `docs/DEVELOPER_GUIDE.md` (49K, in nav line 162) → `docs/development/DEVELOPER_GUIDE.md`
- Modify: `mkdocs.yml` nav lines 161–162

- [ ] **Step 1: Compare the two USER_GUIDE files**

```bash
diff docs/USER_GUIDE.md docs/tutorials/USER_GUIDE.md | head -40
wc -l docs/USER_GUIDE.md docs/tutorials/USER_GUIDE.md
```

Decision rule: keep the longer/newer file's content at `docs/tutorials/USER_GUIDE.md`. If they diverge substantively (not just one being a stale subset), merge unique sections from the loser into the keeper before deleting.

- [ ] **Step 2: Consolidate USER_GUIDE**

```bash
# if root file is the keeper:
mv docs/USER_GUIDE.md docs/tutorials/USER_GUIDE.md
rtk git add docs/tutorials/USER_GUIDE.md && rtk git rm docs/USER_GUIDE.md 2>/dev/null || rtk git add -A
```

- [ ] **Step 3: Move DEVELOPER_GUIDE into development/**

```bash
rtk git mv docs/DEVELOPER_GUIDE.md docs/development/DEVELOPER_GUIDE.md
```

- [ ] **Step 4: Update mkdocs nav**

In `mkdocs.yml` (currently lines 161–162) change:

```yaml
      - User Guide: USER_GUIDE.md
      - Developer Guide: DEVELOPER_GUIDE.md
```

to:

```yaml
      - User Guide: tutorials/USER_GUIDE.md
      - Developer Guide: development/DEVELOPER_GUIDE.md
```

- [ ] **Step 5: Fix inbound links**

```bash
rtk proxy grep -rn "(\.\./)?USER_GUIDE\.md\|(\.\./)?DEVELOPER_GUIDE\.md" docs --include='*.md' | grep -v "tutorials/USER_GUIDE\|development/DEVELOPER_GUIDE" | head
```

Update each link found to the new paths.

- [ ] **Step 6: Validate**

Run: `uv run mkdocs build --strict 2>&1 | tail -5` then `make check`
Expected: both exit 0.

- [ ] **Step 7: Commit**

```bash
rtk git add -A && rtk git commit -m "docs: merge top-level guides into Diátaxis hierarchy (tutorials/, development/)"
```

---

### Task 8: Vulture sweep for remaining whole-module orphans (second signal)

**Files:** determined by findings; only WHOLE modules with zero inbound imports qualify — single unused functions are Pass 3 scope.

- [ ] **Step 1: Run vulture at high confidence**

```bash
uvx vulture src/finwiz --min-confidence 90 | head -40
```

- [ ] **Step 2: For each file where vulture flags essentially everything, confirm zero importers**

```bash
# for each candidate module 'foo':
rtk proxy grep -rn "from finwiz.<pkg>.foo import\|import finwiz.<pkg>.foo\|from finwiz.<pkg> import .*foo" src/finwiz tests --include='*.py' | grep -v "<pkg>/foo.py"
```

Expected for a true orphan: no output. Delete the module + its test file + doc page with `rtk git rm`, one justification line per module in the commit message. **KEEP-list reminder: anything under backtesting or rebalancing-history stays regardless of vulture output.**

- [ ] **Step 3: Validate**

Run: `make check`
Expected: exits 0.

- [ ] **Step 4: Commit (skip if nothing found)**

```bash
rtk git add -A && rtk git commit -m "chore: delete vulture-confirmed orphan modules (zero importers, justifications in body)"
```

---

### Task 9: Final validation and PR

**Files:** none

- [ ] **Step 1: Full quality gate**

Run: `make check && make coverage`
Expected: both exit 0; coverage ≥ 65% (deleting dead code usually RAISES coverage; if it drops below 65%, a deleted test was covering live code — investigate before proceeding).

- [ ] **Step 2: Measure the win**

```bash
rtk git diff --stat main...HEAD | tail -3
find src/finwiz -name '*.py' | xargs wc -l | tail -1
```

Record lines/files removed for the PR description.

- [ ] **Step 3: USER GATE — ask the user to run the production flow**

Ask the user to run `crewai flow kickoff` and confirm the run completes and the HTML report renders. Do NOT merge before this confirmation (spec requirement).

- [ ] **Step 4: Push and open the PR**

```bash
rtk git push -u origin chore/simplify-pass1-delete
gh pr create --title "chore: simplification pass 1 — delete dead code, scripts, docs, flags" --body "$(cat <<'EOF'
## Summary
Pass 1 of the approved simplification spec (docs/superpowers/specs/2026-06-09-codebase-simplification-design.md): pure deletion, zero behavior change.

- Dead notification service (+test, +doc)
- Unused examples/ demos (+Makefile targets)
- Orphaned portfolio_review_enhanced + portfolio_review_html report chain
- ~45 orphaned scripts/ files (keep-list: only Makefile/CI/pre-commit-wired)
- Meta-docs, docs/fixes/ historical logs, implementation summaries
- 11 never-queried feature flags (+.env.example lines, +tests)
- Vulture-confirmed orphan modules (justifications per commit)

## Test plan
- [x] make check green after every commit
- [x] make coverage ≥ 65%
- [x] mkdocs build --strict green
- [ ] User-run `crewai flow kickoff` completes with rendered report

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

---

## Out of Scope (later passes)

- Pass 2 (Merge): sentiment tool unification, `enhanced_*` family audit, `_run` boilerplate helper — gets its own plan after this PR merges.
- Pass 3 (Decompose + guardrails): function splits, CSS/HTML extraction, ruff C901/PLR0915, vulture in `make check`.
- Any behavior change whatsoever.
