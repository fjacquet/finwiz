# Remove the Error-Handling and Validation Orphans Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Delete seventeen modules unreachable from any entry point — five error-handling helpers and a ten-module validation subtree with the two dead roots holding it up — plus their tests and the residue they leave.

**Architecture:** Four tasks. The two clusters are independent of each other and could be done in either order. Every deletion is a whole file; the risk is not surgery but misidentification, because Cluster B removes ten modules from a package that keeps ten live ones.

**Tech Stack:** Python 3.12, pytest + pytest-mock, ruff, vulture, mkdocs.

**Spec:** `docs/superpowers/specs/2026-09-08-remove-error-handling-validation-orphans-design.md`

## Global Constraints

- **unittest.mock is BANNED.** Use pytest-mock (`mocker.patch()`) only. Enforced by ruff and `make check-unittest-mock`.
- **Prove code is dead before deleting it.** Reachability is not proof. Use `git log -S'<symbol>' --oneline` to find the commit that removed a symbol's last reader, and read that commit. #187 twice deleted from a grep that returned nothing; one of those removed live aggregation that had to be restored.
- **Every sweep greps BOTH forms:** `scripts/foo.py` AND dotted `scripts.foo`. `make check`'s stage-contract gate is invoked as `uv run python -m scripts.check_stage_contract` at `Makefile:165` and looks unwired to a path grep.
- **Every sweep covers:** `src`, `tests`, `scripts`, `Makefile` recipe bodies, `pyproject.toml`, `.pre-commit-config.yaml`, `.github/workflows/`, `mkdocs.yml`.
- **Docs ship in the same branch** as the change that invalidates them, never as a follow-up.
- **Do not take a completion claim over the artifact.** Check the file, not the report. The trace behind this plan reported writing a section it had not written.
- `make check`'s docs-lint step **already fails on `main`**, on three files under `docs/superpowers/` this branch does not touch. Adding no new violation is the bar.
- **Line length 180** (ruff).

---

### Task 1: Delete the error-handling helpers

**Files:**

- Delete: `src/finwiz/orchestrators/error_handling/{fallback,handlers,missing_data,recovery,validation_recovery}.py`
- Delete: `tests/unit/integration/test_error_handlers.py`, `tests/unit/utils/test_missing_data_handler.py`
- Modify: `pyproject.toml:197`

**Interfaces:**

- Consumes: nothing.
- Produces: no `FallbackHandlers`, `ErrorHandlers`, `MissingDataHandler`, `RecoveryStrategies` or `ValidationErrorRecovery` anywhere in the tree. `orchestrators/error_handling/` retains exactly `__init__.py` and `core_analysis_error_handler.py`.

**What must survive:** `core_analysis_error_handler.py` is the package's one live member, imported at `flows/orchestrator.py:25`. `error_handling_orchestrator.py` (a sibling, one directory up) is also live and registered in the orchestrator registry. Neither is in scope.

- [ ] **Step 1: Prove the cluster closed, with history**

```bash
for m in fallback handlers missing_data recovery validation_recovery; do
  echo "=== $m ==="
  grep -rn "error_handling.$m\|error_handling import $m\|from .$m import" src tests scripts --include='*.py'
done
grep -rn "FallbackHandlers\|ErrorHandlers\|MissingDataHandler\|RecoveryStrategies\|ValidationErrorRecovery" src tests scripts Makefile pyproject.toml .github mkdocs.yml 2>/dev/null
```

Expected: every hit is another of the five, or one of the two test files. Specifically expect the internal references `fallback.py:14` → `recovery`, `recovery.py:18` → `handlers`, `validation_recovery.py:15` → `.fallback`. **Any hit from outside that set means the cluster is not closed — STOP and report.**

Read `orchestrators/error_handling_orchestrator.py` lines 1-20 and confirm its only imports are `flow_state` and the logger. Confirm `wc -c src/finwiz/orchestrators/error_handling/__init__.py` is 0 — no re-exports to unwire.

Then the history, which is mandatory:

```bash
git log -S'FallbackHandlers' --oneline --all | head
git log -S'MissingDataHandler' --oneline --all | head
```

The expected reading, which you must confirm rather than assume: **all five were born dead.** `fallback`, `handlers` and `recovery` moved from `integration/` in `ebf3d6bc` ("Phase 3 Big Bang architectural restructuring") and the log shows only that rename plus a lint commit. `missing_data` and `validation_recovery` were added whole in `e015648d` with tests and never wired in. If any log instead shows a commit removing a real caller, STOP and report — that would mean lost behaviour worth considering, as happened with `report_data.py` in Task 2.

- [ ] **Step 2: Delete the five modules and their two tests**

```bash
git rm src/finwiz/orchestrators/error_handling/fallback.py \
       src/finwiz/orchestrators/error_handling/handlers.py \
       src/finwiz/orchestrators/error_handling/missing_data.py \
       src/finwiz/orchestrators/error_handling/recovery.py \
       src/finwiz/orchestrators/error_handling/validation_recovery.py \
       tests/unit/integration/test_error_handlers.py \
       tests/unit/utils/test_missing_data_handler.py
```

- [ ] **Step 3: Remove the stale ruff row**

Delete this line from `pyproject.toml` (around `:197`):

```text
"src/finwiz/orchestrators/error_handling/recovery.py" = ["C901"]
```

- [ ] **Step 4: Sweep for survivors**

```bash
grep -rn "error_handling.fallback\|error_handling.handlers\|error_handling.missing_data\|error_handling.recovery\|error_handling.validation_recovery\|FallbackHandlers\|ErrorHandlers\|MissingDataHandler\|RecoveryStrategies\|ValidationErrorRecovery" \
  src tests scripts Makefile pyproject.toml .pre-commit-config.yaml mkdocs.yml .github 2>/dev/null
ls src/finwiz/orchestrators/error_handling/
```

Expected: only `.md` hits, which Task 4 handles. The directory listing must show exactly `__init__.py` and `core_analysis_error_handler.py`.

- [ ] **Step 5: Run lint and the suite**

Run: `make lint && make test`

Both green. Show the arithmetic:

```bash
git show HEAD:tests/unit/integration/test_error_handlers.py | grep -c "def test_"
git show HEAD:tests/unit/utils/test_missing_data_handler.py | grep -c "def test_"
```

Expect 43 and 17. Their sum must equal the drop from the pre-task baseline. If it does not, something else lost tests — report it.

- [ ] **Step 6: Commit**

```bash
git commit -m "$(cat <<'EOM'
refactor(error_handling): delete five helpers that were never wired in

fallback, handlers, missing_data, recovery and validation_recovery reference only
each other. error_handling_orchestrator.py imports none of them — its only imports
are flow_state and the logger — and the package's one live member is
core_analysis_error_handler, imported at flows/orchestrator.py:25.

All five were born dead rather than orphaned, so there is no lost behaviour here.
fallback/handlers/recovery came from integration/ in ebf3d6bc and git log -S shows
only that rename; missing_data and validation_recovery were added whole in e015648d
with tests and never called. error_handling_orchestrator.py, created in 08588664,
never referenced any of them even in its first version — the intended integration
never happened.

Refs #200.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01JtXz89ibcafk3p5LP5Ewms
EOM
)"
```

---

### Task 2: Delete the validation subtree and its two roots

**Files:**

- Delete: `src/finwiz/validation/{rules,report,report_data,consolidation,freshness,int_pipeline,pipeline_stages,scripts,sec_citation,tool_restrictions}.py`
- Delete: `src/finwiz/integration/cli.py`, `src/finwiz/integration/middleware.py`
- Delete: `tests/unit/validation/{test_rules,test_report_validator,test_consolidation,test_data_freshness_validator}.py`, `tests/unit/integration/test_validation_scripts.py`, `tests/unit/schemas/{test_sec_citation_validator,test_tool_restrictions}.py`
- Modify: `pyproject.toml:193,220,222,223`

**Interfaces:**

- Consumes: nothing from Task 1.
- Produces: `src/finwiz/validation/` retains exactly ten modules plus `__init__.py` and `CLAUDE.md`. No `CrewIntegrationMiddleware`, no `ToolRestrictionValidator`.

**THE RISK IN THIS TASK.** Ten modules go from a package that keeps ten. These MUST survive:

`ai_output.py`, `contract.py`, `enums.py`, `int_manager.py`, `manager.py`, `quality_metrics.py`, `registry.py`, `result.py`, `template.py`, `url.py`

`validation/__init__.py` re-exports from `contract`, `enums`, `manager`, `registry`, `result` and `template` — all survivors. It names **none** of the ten being deleted, so unlike `cost_analyzer` in #195 there is no public re-export making this an API change. Confirm that yourself in Step 2 rather than trusting it.

- [ ] **Step 1: Prove the ten dead, and the roots with them**

```bash
for m in rules report report_data consolidation freshness int_pipeline pipeline_stages scripts sec_citation tool_restrictions; do
  echo "=== validation/$m ==="
  grep -rn "validation\.$m\b\|from \.$m import\|validation import $m\b" src tests scripts --include='*.py'
done
grep -rn "integration.cli\|integration.middleware\|CrewIntegrationMiddleware" src tests scripts Makefile pyproject.toml .github 2>/dev/null
grep -n "cli\|middleware" pyproject.toml | grep -i "scripts"
```

**A GREP TRAP you must not fall into:** searching for `validation.report` false-matches `from .report import ReporterInput` at `schemas/__init__.py:132` and `schemas/validate.py:11`. That `.report` is `schemas/report.py`, a live and unrelated file. `validation/report.py` has zero production importers.

Expected shape, which you must confirm rather than assume — note this differs from what issue #200 says:

- One real chain: `int_pipeline.py` → `pipeline_stages.py` → `{rules.py, sec_citation.py}`. `pipeline_stages.py:18-21` imports `.rules` and `.sec_citation` but **NOT** `.report`.
- Five standalone orphans with no importer at all: `report.py`, `report_data.py`, `consolidation.py`, `freshness.py`, `tool_restrictions.py`.
- `scripts.py` imported only by `integration/cli.py`; `int_pipeline.py` imported only by `integration/middleware.py`.
- Both roots have zero importers, and `[project.scripts]` holds only `kickoff`, `run_crew`, `plot`.

Then the history for the three that were once live:

```bash
git log -S'DataFreshnessValidator' --oneline --all | head
git log -S'ReportDataValidator' --oneline --all | head
git log -S'DataConsolidationValidator' --oneline --all | head
```

Expected: `freshness.py` was orphaned by `249cab36` ("Wave-3 noise purge"), which deleted `integration/freshness_validated_tool.py` as a documented dead-code purge. `report_data.py` and `consolidation.py` were **silently dropped** in `4600d1a7`'s decomposition — their calls existed in the old `flow_orchestrator.py` and the successor orchestrators never picked them up. **That is expected and already filed as #202.** Do not restore them, do not widen scope; just confirm the reading matches.

- [ ] **Step 2: Confirm `__init__.py` re-exports only survivors**

```bash
cat src/finwiz/validation/__init__.py
```

Read it in full. It must import only from `contract`, `enums`, `manager`, `registry`, `result` and `template`. If it names ANY of the ten you are deleting, STOP and report — that changes the analysis the way `cost_analyzer`'s re-export did in #195.

- [ ] **Step 3: Delete the twelve modules and seven tests**

```bash
git rm src/finwiz/validation/rules.py \
       src/finwiz/validation/report.py \
       src/finwiz/validation/report_data.py \
       src/finwiz/validation/consolidation.py \
       src/finwiz/validation/freshness.py \
       src/finwiz/validation/int_pipeline.py \
       src/finwiz/validation/pipeline_stages.py \
       src/finwiz/validation/scripts.py \
       src/finwiz/validation/sec_citation.py \
       src/finwiz/validation/tool_restrictions.py \
       src/finwiz/integration/cli.py \
       src/finwiz/integration/middleware.py \
       tests/unit/validation/test_rules.py \
       tests/unit/validation/test_report_validator.py \
       tests/unit/validation/test_consolidation.py \
       tests/unit/validation/test_data_freshness_validator.py \
       tests/unit/integration/test_validation_scripts.py \
       tests/unit/schemas/test_sec_citation_validator.py \
       tests/unit/schemas/test_tool_restrictions.py
```

- [ ] **Step 4: Remove the four stale ruff rows**

Delete these lines from `pyproject.toml`:

```text
"src/finwiz/integration/cli.py" = ["C901"]
"src/finwiz/validation/consolidation.py" = ["C901"]
"src/finwiz/validation/scripts.py" = ["C901"]
"src/finwiz/validation/sec_citation.py" = ["C901"]
```

**Do NOT remove** the rows for `src/finwiz/validation/quality_metrics.py` or `src/finwiz/validation/url.py` — both files survive.

- [ ] **Step 5: Verify the ten survivors are intact**

```bash
ls src/finwiz/validation/
grep -rn "from finwiz.validation import\|from finwiz.validation\." src --include='*.py' | head -20
```

The listing must show exactly: `CLAUDE.md`, `__init__.py`, `ai_output.py`, `contract.py`, `enums.py`, `int_manager.py`, `manager.py`, `quality_metrics.py`, `registry.py`, `result.py`, `template.py`, `url.py`. Every remaining import in `src/` must name one of those.

- [ ] **Step 6: Sweep**

```bash
grep -rn "validation.rules\|validation.report\b\|validation.report_data\|validation.consolidation\|validation.freshness\|validation.int_pipeline\|validation.pipeline_stages\|validation.scripts\|validation.sec_citation\|validation.tool_restrictions\|integration.cli\|integration.middleware" \
  src tests scripts Makefile pyproject.toml .pre-commit-config.yaml mkdocs.yml .github 2>/dev/null
```

Expected: only `.md` hits, which Task 4 handles.

- [ ] **Step 7: Run lint and the suite**

Run: `make lint && make test`

Show the arithmetic — count `def test_` in each of the seven deleted test files at the pre-task commit and confirm the sum equals the drop. Expect roughly 226.

- [ ] **Step 8: Commit**

```bash
git commit -m "$(cat <<'EOM'
refactor(validation): delete the ten orphaned validators and their two dead roots

Not one chain, as #200 describes, but one chain plus five standalone orphans:
int_pipeline -> pipeline_stages -> {rules, sec_citation}, with report, report_data,
consolidation, freshness and tool_restrictions each reachable from nothing at all.
pipeline_stages does not import report.

The two roots go with them. integration/cli.py has no [project.scripts] entry and no
importer; integration/middleware.py's CrewIntegrationMiddleware has never had an
importer outside its own file in the entire history. Neither has any purpose without
the subtree it holds up.

Three were once live. freshness lost its caller in 249cab36, a documented dead-code
purge that deleted integration/freshness_validated_tool.py. report_data and
consolidation were not retired but silently dropped in 4600d1a7's decomposition —
filed as #202, since whether those checks should return is a question about today's
pipeline rather than about this dead code.

tool_restrictions enforced that the final reporter crew has no external tools. Its
RESTRICTED_AGENTS dict names one agent, investment_reporter, on the report_crew that
#187 deleted. The live pre_validate_reporter_input reimplements the name, not the code.

The ten live modules in the same package are untouched, and validation/__init__.py
re-exports none of the deleted ten.

Refs #200.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01JtXz89ibcafk3p5LP5Ewms
EOM
)"
```

---

### Task 3: Sweep the whole per-file-ignores block

**Files:**

- Modify: `pyproject.toml`

**Interfaces:**

- Consumes: Tasks 1 and 2's deletions.
- Produces: every literal path key in `[tool.ruff.lint.per-file-ignores]` resolves to a file that exists.

Tasks 1 and 2 each removed the rows they knew about. This task catches what they missed. That block collected residue across at least four separate cleanups before #195 emptied it; #200's own text names it as a standing collector.

- [ ] **Step 1: Sweep every literal path key against the filesystem**

```bash
python3 - <<'PY'
import pathlib, re
s = pathlib.Path("pyproject.toml").read_text()
block = s.split("[tool.ruff.lint.per-file-ignores]")[1].split("\n[")[0]
stale = []
for line in block.splitlines():
    m = re.match(r'\s*"([^"]+)"\s*=', line)
    if m and "*" not in m.group(1) and not pathlib.Path(m.group(1)).exists():
        stale.append(m.group(1))
print("STALE:", stale or "none — clean")
PY
```

- [ ] **Step 2: Remove every row it reports**

Glob patterns (`tests/**/*.py`, `src/finwiz/schemas/**/*.py`, `scripts/**/*.py`, `tests/property/*.py`, `src/finwiz/crews/**/*.py`) are fine and must stay — the script skips them by design.

If Step 1 printed "none — clean", this task is already satisfied by Tasks 1 and 2. Record that and skip to Step 4; do not invent work.

- [ ] **Step 3: Re-run the sweep to confirm clean**

Run the Step 1 script again. It must print `STALE: none — clean`.

- [ ] **Step 4: Run lint**

Run: `make lint`

Removing a `per-file-ignore` can only expose a violation, never hide one, so a clean run here is real proof the removed rows were dead. Ruff drops unmatched rows silently, which is exactly how they accumulated.

- [ ] **Step 5: Commit (skip if Step 1 found nothing)**

```bash
git commit -m "$(cat <<'EOM'
chore: sweep the per-file-ignores block against the tree

Tasks 1 and 2 each removed the rows they knew about; this catches the rest. Ruff
drops unmatched entries silently, so a green lint run is not evidence a row is live —
which is how this block collected residue across four separate cleanups.

Refs #200.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01JtXz89ibcafk3p5LP5Ewms
EOM
)"
```

---

### Task 4: Documentation, full check, and PR

**Files:**

- Modify: `src/finwiz/orchestrators/CLAUDE.md:17,43-49,84`
- Modify: `src/finwiz/validation/CLAUDE.md`
- Modify: `src/finwiz/integration/CLAUDE.md:18,22,33,35`
- Modify: `docs/explanations/DATA_QUALITY_AND_FLOW_GUIDE.md:145,169`
- Modify: `CHANGELOG.md`

**Interfaces:**

- Consumes: every prior task's deletions.
- Produces: no documentation naming a deleted module, outside `docs/superpowers/`.

- [ ] **Step 1: Find every stale reference — this grep is authoritative**

```bash
grep -rn "error_handling.fallback\|error_handling.handlers\|error_handling.missing_data\|error_handling.recovery\|error_handling.validation_recovery\|FallbackHandlers\|ErrorHandlers\|MissingDataHandler\|RecoveryStrategies\|ValidationErrorRecovery\|validation.rules\|validation.report_data\|validation.consolidation\|validation.freshness\|validation.int_pipeline\|validation.pipeline_stages\|validation.scripts\|validation.sec_citation\|validation.tool_restrictions\|ToolRestrictionValidator\|ReporterInputValidator\|DataFreshnessValidator\|ReportDataValidator\|DataConsolidationValidator\|CrewIntegrationMiddleware\|integration.cli\|integration.middleware" \
  src docs .planning --include='*.py' --include='*.md' | grep -v "^docs/superpowers/"
```

This output is the file list, not the table above. If it names a file nobody predicted, that file is in scope. #194's docs task shipped with three files missed because someone worked from a hand-maintained list.

It covers `.py` as well as `.md`: a stale docstring is documentation too, and the last two branches each shipped one.

- [ ] **Step 2: Rewrite each file**

Delete passages describing removed modules rather than annotating them. Where a doc shows an example importing a deleted symbol, **remove the example** — one that cannot run is worse than none.

Known items:

- `orchestrators/CLAUDE.md:17,43-49,84` — the directory tree lists all five Cluster A modules.
- `validation/CLAUDE.md` — its directory tree names all ten deleted modules and its entry-points table several. Rewrite the tree to the ten survivors: `ai_output`, `contract`, `enums`, `int_manager`, `manager`, `quality_metrics`, `registry`, `result`, `template`, `url`.
- `integration/CLAUDE.md:18,22,33,35` — documents `middleware.py` (`CrewIntegrationMiddleware`) and `cli.py` (`main()`, `cmd_health`, `cmd_validate`, `cmd_status`) as live components.
- `docs/explanations/DATA_QUALITY_AND_FLOW_GUIDE.md:145,169` — shows example code importing `DataConsolidationValidator` and `ReportDataValidator` as current guidance. **This is the worst of them**: it reads as live instruction for code that has not run since November 2025.

**Do NOT edit** `docs/superpowers/plans/2026-06-10-simplification-pass3-decompose.md:430-431`. It records a historical rename, was true when written, and is history rather than guidance — the same rule that governs released CHANGELOG entries.

- [ ] **Step 3: Add the CHANGELOG entry**

Under `## [Unreleased]` → `### Removed`, matching the format of the `#193`/`#194`/`#195` entries already there:

```markdown
- Seventeen modules unreachable from any entry point: five `orchestrators/error_handling/`
  helpers that were never wired in, ten orphaned `validation/` modules, and the two dead
  roots in `integration/` holding that subtree up. Two of the validation modules had
  stopped running silently in 4600d1a7 — see [#202](https://github.com/fjacquet/finwiz/issues/202).
  ([#200](https://github.com/fjacquet/finwiz/issues/200))
```

**Do not rewrite released CHANGELOG entries** that mention any deleted symbol. They were true when written.

- [ ] **Step 4: Verify the docs tell the truth**

Re-run Step 1's grep. Expected: only `docs/superpowers/` hits, plus any past-tense prose you wrote describing the removal — that is correct; note it in your report.

Then check every claim you wrote is true of the tree as it stands. #194 shipped a doc asserting a script had been deleted when it had not.

- [ ] **Step 5: Build the docs**

Run: `uv run mkdocs build --strict --clean`

It fails on broken internal links. If you deleted a section another doc linked to, fix the linking doc.

- [ ] **Step 6: Run the full check**

```bash
make check
make coverage
uv run plot
```

`make check`'s docs-lint fails on `docs/superpowers/plans/2026-09-07-remove-uncalled-crew-subsystem.md`, its `-design.md`, and `2026-09-06-per-asset-class-fact-pack-design.md` — **pre-existing on `main`, none touched by this branch.** Confirm the failure names only files absent from `git diff --name-only <merge-base>..HEAD`. If it names a file you touched, fix that file.

Coverage must be ≥ 65% — report the real number. `plot` must exit 0.

- [ ] **Step 7: Run the pipeline**

Cluster B removed ten modules from a package whose `ValidationOrchestrator` runs in Phases 1, 2 and 6. The unit suite cannot prove a run still completes.

Run: `uv run kickoff`

Then confirm from `output/run_summary.json` that the run reached its verdict and the phases populated. Report the verdict and any FAIL-severity check.

If a full run is not possible in your environment, say so **explicitly** in your report rather than skipping it silently. Do not infer or fake the result.

- [ ] **Step 8: Commit**

```bash
git add -A
git commit -m "$(cat <<'EOM'
docs(#200): retire the deleted validators and error handlers from the documentation

Refs #200.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01JtXz89ibcafk3p5LP5Ewms
EOM
)"
```

Do **not** push or open the PR. Report back; the controller handles the PR after a final whole-branch review.

---

## Out of scope

This is tier 1 of #200 only. The reachability run found 78 unreachable modules; the tier 2 clusters — `integration/{extractor,backtesting_pipeline_connector}`, nine more `quantitative/` modules, six `schemas/`, and clusters in `tools/`, `infrastructure/`, `reporting/` and `orchestrators/discovery/` — each need their own `git log -S` pass before anyone deletes them. Module-level unreachability is necessary but not sufficient, and that is exactly where #187 went wrong twice.

Whether the two validators dropped in `4600d1a7` should be reinstated is [#202](https://github.com/fjacquet/finwiz/issues/202), not this branch.
