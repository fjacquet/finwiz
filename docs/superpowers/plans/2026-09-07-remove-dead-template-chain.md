# Remove the Dead Template Chain — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Delete the sixteen unreachable Jinja templates outside `crew_reports/`, the converter chain that referenced them, and the closed island of report-generator classes whose only inhabitant is its own test — then correct every document that described any of it as live.

**Architecture:** Pure deletion, in dependency order: leaves first (templates), then the converter chain, then the island, each step verified against the tree rather than against this plan. Nothing is refactored and no behavior changes; the live reporting path (`reporting/python_report_generator.py` and `reporting/sections/`) is never touched.

**Tech Stack:** Python 3.12, Jinja2, pytest, ruff, mypy, vulture.

**Spec:** `docs/superpowers/specs/2026-09-07-remove-dead-template-chain-design.md`

## Global Constraints

- **`unittest.mock` is BANNED.** pytest-mock only (`mocker.patch`). Enforced by ruff and `make check-unittest-mock`.
- **Line length 180 characters** (ruff).
- Run tests with `uv run pytest`, never bare `pytest`.
- Commit messages end with:
  ```
  Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
  Claude-Session: https://claude.ai/code/session_01JtXz89ibcafk3p5LP5Ewms
  ```
- Branch is already created: `refactor/remove-dead-template-chain`. Do not create another.
- If a commit fails with `files were modified by this hook` and the file is `uv.lock`, `git add uv.lock` and re-commit. Never use `--no-verify`.
- There is an untracked `output0905/` directory predating this work. Never add it to a commit.
- **Prove dead before deleting.** A present-tense grep says only that nothing calls it today. For every symbol whose deletion this plan asks for, also run `git log -S'<symbol>' --oneline -- .` and read the commit that removed its last reader. If that commit looks like it removed a live caller by accident, STOP and report it. This repo has already restored live aggregation code once after a grep-only deletion.

---

### Task 1: Delete the templates the converter chain owns

**Files:**
- Delete: `src/finwiz/templates/a_plus_discovery.html`, `backtesting_results.html`, `consolidated_report.html`, `deep_analysis_consolidated.html`, `discovery_latest.html`, `optimization_report.html`, `portfolio_processing_summary.html`, `portfolio_review.html`, `validation_report.html`, `base_template.html`, `demo.html`, `portfolio_configuration.html`, `rebalancing_template.html`, `stress_test_section.html`

**Interfaces:**
- Consumes: nothing.
- Produces: a `templates/` directory holding only `crew_reports/`, `partials/`, `enriched_analysis_report.html`, `html_template.html`, `unified_portfolio_report.html` and `CLAUDE.md`. Task 3 deletes the two remaining loose templates.

- [ ] **Step 1: Confirm each template's only referrer is the converter**

Run, for each of the fourteen filenames:

```bash
for t in a_plus_discovery backtesting_results consolidated_report deep_analysis_consolidated \
         discovery_latest optimization_report portfolio_processing_summary portfolio_review \
         validation_report base_template demo portfolio_configuration rebalancing_template \
         stress_test_section; do
  echo "== $t.html"
  grep -rn "$t\.html" src tests 2>/dev/null | grep -v "^src/finwiz/templates/"
done
```

Expected: every hit is in `src/finwiz/infrastructure/json/to_html_converter.py` (the `TEMPLATE_MAPPING` block) or in a `CLAUDE.md`. `base_template.html` additionally appears in `{% extends %}` lines inside the other templates, which are themselves being deleted.

If any template is referenced from live Python outside the converter, STOP and report which.

- [ ] **Step 2: Note the name collision, do not act on it**

`stress_test_section.html` shares a name with `generate_stress_test_section()` in `src/finwiz/reporting/sections/analysis.py`, which is **live** and used by `python_report_generator.py`. That function builds HTML in Python and never opens the template. Confirm with:

```bash
grep -n "stress_test_section" src/finwiz/reporting/sections/analysis.py src/finwiz/reporting/python_report_generator.py
```

Do not touch either file. This step exists so the collision is recorded before the deletion, not discovered after.

- [ ] **Step 3: Delete the fourteen files**

```bash
cd src/finwiz/templates
git rm a_plus_discovery.html backtesting_results.html consolidated_report.html \
       deep_analysis_consolidated.html discovery_latest.html optimization_report.html \
       portfolio_processing_summary.html portfolio_review.html validation_report.html \
       base_template.html demo.html portfolio_configuration.html \
       rebalancing_template.html stress_test_section.html
```

- [ ] **Step 4: Run the suite**

Run: `make test`
Expected: green. Nothing should reference these files at runtime. A failure here means one of them was live — report it rather than restoring blindly.

- [ ] **Step 5: Commit**

```bash
git commit -m "$(cat <<'EOM'
refactor(templates): delete the fourteen templates the dead converter owned

Nine were referenced only from TEMPLATE_MAPPING in the JsonToHtmlConverter
chain, which has had no caller since 5b8279ab removed the storage subsystem in
January. base_template.html was the {% extends %} parent of those nine plus
demo.html. The remaining four -- demo.html, portfolio_configuration.html (0
bytes), rebalancing_template.html, stress_test_section.html -- had no reference
anywhere at all.

The converter itself goes in the next commit; deleting the templates while
leaving it pointing at them is the mistake #194 was filed to document.

Note: stress_test_section.html shares a name with the live
generate_stress_test_section() in reporting/sections/analysis.py. They are
unrelated -- that function builds HTML in Python and never opened this file.

Refs #194.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01JtXz89ibcafk3p5LP5Ewms
EOM
)"
```

---

### Task 2: Delete the converter chain

**Files:**
- Delete: `src/finwiz/infrastructure/json/to_html_converter.py` (452 lines)
- Delete: `src/finwiz/reporting/html_auto_generator.py`
- Delete: `tests/unit/utils/test_json_to_html_converter.py`
- Modify: any `__init__.py` that re-exports the deleted names

**Interfaces:**
- Consumes: Task 1's deletions.
- Produces: no `JsonToHtmlConverter`, `TEMPLATE_MAPPING`, `auto_generate_html` or `auto_generate_html_for_crew` anywhere in the tree.

- [ ] **Step 1: Prove the chain dead, with history**

```bash
grep -rn "JsonToHtmlConverter\|to_html_converter" src tests
grep -rn "auto_generate_html" src tests
git log -S'auto_generate_html' --oneline -- . | head
git log -S'JsonToHtmlConverter' --oneline -- . | head
```

The expected picture, which you must confirm rather than assume: `JsonToHtmlConverter`'s only callers are `auto_generate_html` and `auto_generate_html_for_crew` in `reporting/html_auto_generator.py`, plus `tests/unit/utils/test_json_to_html_converter.py`. Neither function has any caller in `src/` or `tests/`.

Read the commit that removed `auto_generate_html`'s last caller — expected to be **5b8279ab**, which deliberately removed the storage subsystem (`store_crew_output()` in the old `integration/storage.py`) and left this orphan behind. Confirm that reading. If the commit instead looks like it removed a live caller by accident, STOP and report.

Also check for dynamic reach before deleting: `pyproject.toml` `[project.scripts]` (expected to hold only `kickoff`, `run_crew`, `plot`), the `Makefile`, and any string-keyed registry.

- [ ] **Step 2: Delete the three files**

```bash
git rm src/finwiz/infrastructure/json/to_html_converter.py \
       src/finwiz/reporting/html_auto_generator.py \
       tests/unit/utils/test_json_to_html_converter.py
```

The test goes with the class deliberately: it is the converter's last remaining caller, and keeping the converter alive to satisfy its own test is the pattern #187 and #193 both existed to remove.

- [ ] **Step 3: Clean up any re-export**

```bash
grep -rn "to_html_converter\|html_auto_generator\|JsonToHtmlConverter\|auto_generate_html" src tests
```

Expected after Step 2: only `CLAUDE.md` hits, which Task 4 handles. Any surviving Python hit is an `__init__.py` re-export — remove that line and re-run until only docs remain.

- [ ] **Step 4: Run lint and the suite**

Run: `make lint && make test`
Expected: both green. `make lint` includes vulture; if it now reports something newly dead in `infrastructure/json/`, record it and raise it after the branch merges — do not widen this task.

- [ ] **Step 5: Commit**

```bash
git commit -m "$(cat <<'EOM'
refactor(reporting): delete the JsonToHtmlConverter chain

auto_generate_html lost its last caller in 5b8279ab, which removed the storage
subsystem (store_crew_output in the old integration/storage.py) and left this
behind. auto_generate_html_for_crew was born dead in ebf3d6bc and never had a
caller in this repo's history. Neither is reachable from an entry point, a
Makefile target, or any registry.

test_json_to_html_converter.py goes with the class: it was the converter's last
remaining caller, and keeping code alive to satisfy its own test is what #187
and #193 were both about.

Refs #194.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01JtXz89ibcafk3p5LP5Ewms
EOM
)"
```

---

### Task 3: Delete the report-generator island

This is the largest task and the one with a real chance of surprise. Verify the chain end to end **before** deleting anything, in the order given, and stop at the first link that does not hold.

**Files:**
- Delete: `src/finwiz/tools/scenario_comparison_report_generator.py` (101 lines)
- Delete: `src/finwiz/tools/scenario_report_renderer.py` (360)
- Delete: `src/finwiz/tools/scenario_report_sections.py` (224)
- Delete: `src/finwiz/tools/html_report_generator.py` (188)
- Delete: `src/finwiz/tools/reporting/` — `report_formatters.py` (526), `report_sections.py` (327), `__init__.py` (15)
- Delete: `tests/unit/tools/test_scenario_comparison_report_generator.py` (258)
- Delete: `src/finwiz/templates/html_template.html`, `src/finwiz/templates/unified_portfolio_report.html`

**Interfaces:**
- Consumes: Tasks 1 and 2.
- Produces: no `HTMLReportGenerator`, `HTMLReportFormatter`, `ReportSectionBuilder`, `ReportSection` or scenario-report symbol anywhere. `src/finwiz/tools/reporting/` ceases to exist.

- [ ] **Step 1: Verify the chain, link by link**

```bash
echo "== who imports the scenario trio (expect: only its own test)"
grep -rn "ScenarioComparisonReportGenerator\|scenario_report_renderer\|scenario_report_sections" src tests | grep -v "^src/finwiz/tools/scenario_"

echo "== who imports HTMLReportGenerator (expect: only scenario_comparison_report_generator.py)"
grep -rn "HTMLReportGenerator\|html_report_generator" src tests | grep -v "^src/finwiz/tools/html_report_generator.py"

echo "== who imports HTMLReportFormatter / tools.reporting (expect: only html_report_generator.py)"
grep -rn "HTMLReportFormatter\|tools.reporting\|tools/reporting" src tests | grep -v "^src/finwiz/tools/reporting/"

echo "== who imports report_sections symbols (expect: only html_report_generator.py)"
grep -rn "ReportSectionBuilder\|from finwiz.tools.reporting.report_sections" src tests | grep -v "^src/finwiz/tools/reporting/"
```

Every link must come back with only the expected referrer (plus `CLAUDE.md` files). If ANY of these returns a caller outside the island — especially anything under `src/finwiz/reporting/`, `orchestrators/`, or a crew — STOP and report. `src/finwiz/reporting/` is a different, live package with a confusingly similar name; do not confuse `finwiz.reporting` (live) with `finwiz.tools.reporting` (the island).

- [ ] **Step 2: Confirm with history**

```bash
git log -S'ScenarioComparisonReportGenerator' --oneline -- src | head
git log -S'HTMLReportGenerator' --oneline -- src | head
```

`src/finwiz/tools/CLAUDE.md:45-62` records that this trio was verified dead at merge-base 171b8145 and that its last two consumers (`orchestrators/portfolio_rebalancing.py`, `rebalancing_report_generator.py`) are already gone. Confirm that against the history rather than trusting the note.

- [ ] **Step 3: Confirm the two remaining templates belong to this island only**

```bash
grep -rn "html_template.html\|unified_portfolio_report.html" src tests
```

Expected: only `src/finwiz/tools/reporting/report_formatters.py:35-36`, which this task deletes.

- [ ] **Step 4: Delete the island**

```bash
git rm -r src/finwiz/tools/reporting/
git rm src/finwiz/tools/html_report_generator.py \
       src/finwiz/tools/scenario_comparison_report_generator.py \
       src/finwiz/tools/scenario_report_renderer.py \
       src/finwiz/tools/scenario_report_sections.py \
       tests/unit/tools/test_scenario_comparison_report_generator.py \
       src/finwiz/templates/html_template.html \
       src/finwiz/templates/unified_portfolio_report.html
```

- [ ] **Step 5: Sweep for orphaned imports**

```bash
grep -rn "tools.reporting\|html_report_generator\|scenario_report\|ScenarioComparison\|HTMLReport" src tests
```

Expected: `CLAUDE.md` hits only (Task 4's job). Any Python hit is a dangling import — remove it. Then:

Run: `make lint && make test`
Expected: both green, no `ImportError`, no collection errors.

- [ ] **Step 6: Confirm the live reporting path is untouched**

Run: `uv run pytest tests/unit/reporting/ -v`
Expected: green. This is the package whose name resembles the deleted one; this step proves the right thing was deleted.

- [ ] **Step 7: Commit**

```bash
git commit -m "$(cat <<'EOM'
refactor(tools): delete the dead report-generator island

A closed chain whose only inhabitant was its own test:
HTMLReportFormatter's sole consumer was HTMLReportGenerator, whose sole
consumer was ScenarioComparisonReportGenerator, whose sole consumer was
tests/unit/tools/test_scenario_comparison_report_generator.py.
report_sections.py was imported only by html_report_generator.py. Its two real
consumers -- orchestrators/portfolio_rebalancing.py and
rebalancing_report_generator.py -- were removed earlier.

tools/CLAUDE.md had already recorded this and assigned it here: "When #194
clears the scenario trio, delete HTMLReportGenerator in the same pass -- it
becomes a true orphan then."

html_template.html and unified_portfolio_report.html go with it. Their reading
code was real -- one Path.read_text, one genuine jinja2.Template().render() --
but the methods holding it had no caller.

Note finwiz.tools.reporting (deleted) is not finwiz.reporting (live, and
untouched).

Refs #194.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01JtXz89ibcafk3p5LP5Ewms
EOM
)"
```

---

### Task 4: Correct the documentation

**Files:**
- Modify: `src/finwiz/templates/CLAUDE.md`
- Modify: `src/finwiz/tools/CLAUDE.md`
- Modify: `src/finwiz/reporting/CLAUDE.md`
- Modify: `CHANGELOG.md`

**Interfaces:**
- Consumes: Tasks 1-3.
- Produces: no document describing any deleted file as live.

- [ ] **Step 1: `src/finwiz/templates/CLAUDE.md`**

Three places are now false:
- the directory tree (around lines 15-19) lists `backtesting_results.html`, `optimization_report.html`, `validation_report.html` and "[other specialized templates]"
- the **Major Entry Points** table (lines 21-29) lists `portfolio_review.html`, `a_plus_discovery.html`, `deep_analysis_consolidated.html` and `rebalancing_template.html` — all four deleted
- **Related Modules** (line 90) points at `finwiz.tools.html_report_generator`, deleted

Rewrite the tree to what is actually on disk after Task 3 (`crew_reports/`, `partials/`, `enriched_analysis_report.html`, `CLAUDE.md`), reduce the entry-points table to the templates that survive, and drop the `html_report_generator` line from Related Modules. Verify against `ls -1 src/finwiz/templates/` rather than against this plan.

- [ ] **Step 2: `src/finwiz/tools/CLAUDE.md`**

Lines 45-62 describe the scenario trio and `html_report_generator.py` as pending deletions for #194, with tree entries for each. That work is now done: remove those tree entries and the explanatory comment blocks. Also remove the `report_formatters.py` / `HTMLReportFormatter` entry (around line 83) and any `tools/reporting/` subtree entry.

Do not delete the surrounding notes about files that still exist.

- [ ] **Step 3: `src/finwiz/reporting/CLAUDE.md`**

Line 29's tree entry `html_auto_generator.py  # auto_generate_html()` and line 69's table row `| html_auto_generator.py | auto_generate_html() | Auto-generate from crew exports |` both name a deleted file. Remove both rows.

- [ ] **Step 4: CHANGELOG**

Under `[Unreleased]`, in the `### Removed` section (matching the file's existing heading style):

```markdown
- The dead HTML template chain: sixteen Jinja templates outside
  `crew_reports/`, `JsonToHtmlConverter` and its `TEMPLATE_MAPPING`,
  `auto_generate_html` / `auto_generate_html_for_crew`, and the report-generator
  island behind them (`HTMLReportGenerator`, `HTMLReportFormatter`, the scenario
  report trio, and `tools/reporting/`). None had a reachable caller; the live
  reporting path in `finwiz.reporting` is unaffected. ([#194](https://github.com/fjacquet/finwiz/issues/194))
```

- [ ] **Step 5: Verify no document still describes deleted code**

```bash
grep -rn "html_report_generator\|JsonToHtmlConverter\|auto_generate_html\|ScenarioComparison\|rebalancing_template\|base_template.html\|html_template.html\|unified_portfolio_report" \
  src docs README.md CHANGELOG.md | grep -v "docs/superpowers/"
```

Expected: only the CHANGELOG entry. Every other hit is a document still describing deleted code — fix it and say in your report what it was.

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "$(cat <<'EOM'
docs: stop describing the deleted template chain as live

templates/CLAUDE.md advertised four deleted templates as major entry points and
pointed at a deleted module. tools/CLAUDE.md carried the scenario trio and
html_report_generator.py as pending #194 deletions, which this branch performed.
reporting/CLAUDE.md listed html_auto_generator.py in two places.

Refs #194.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01JtXz89ibcafk3p5LP5Ewms
EOM
)"
```

---

### Task 5: Full check and pull request

**Files:** none modified unless a check fails.

- [ ] **Step 1: Full check**

Run: `make check`
Expected: it must not regress from its state on `main`. Note that `make check` currently **fails on `main`** at the `docs-lint` step, from markdownlint violations in pre-existing `docs/superpowers/` documents. That failure is not yours. Judge every other sub-target on its own exit status, and confirm this branch's own documents add no new markdownlint violations:

```bash
make docs-lint 2>&1 | grep "dead-template-chain"
```
Expected: no output.

- [ ] **Step 2: Coverage**

Run: `make coverage`
Expected: ≥ 65%. Deleting `test_json_to_html_converter.py` and `test_scenario_comparison_report_generator.py` removes covered lines along with the code they covered, so the ratio may move either way. Report the real number. Do not add tests to pad it.

- [ ] **Step 3: Prove the live report still renders**

The deletion's real risk is having cut something the live path needed. Run the pipeline's report generation and confirm it still produces HTML:

Run: `uv run pytest tests/unit/reporting/ tests/unit/tools/ -v`
Expected: green.

Then confirm the flow still constructs: `uv run plot`
Expected: exits 0.

- [ ] **Step 4: Open the pull request**

```bash
git push -u origin refactor/remove-dead-template-chain
gh pr create --title "refactor: delete the dead HTML template chain and the island behind it" --body "$(cat <<'EOM'
Closes #194.

## What

Sixteen Jinja templates outside `crew_reports/` had no reachable caller. They
were not independent files but the leaves of a chain, so the chain goes with
them:

- **Templates** — nine referenced only from `TEMPLATE_MAPPING`, their
  `base_template.html` parent, four referenced nowhere at all, plus
  `html_template.html` and `unified_portfolio_report.html`.
- **Converter** — `JsonToHtmlConverter`, `auto_generate_html`,
  `auto_generate_html_for_crew`. `auto_generate_html` lost its last caller in
  5b8279ab, which deliberately removed the storage subsystem and left this
  orphan behind; `auto_generate_html_for_crew` was born dead in ebf3d6bc.
- **The island** — `HTMLReportFormatter` ← `HTMLReportGenerator` ←
  `ScenarioComparisonReportGenerator` ← its own test, plus `tools/reporting/`
  and the scenario renderer/sections pair. A closed chain whose only inhabitant
  was a test. `tools/CLAUDE.md` had already recorded this and assigned it to
  #194.

Two tests are deleted with the code they were the last callers of. Keeping code
alive to satisfy its own test is the pattern #187 and #193 both removed.

## What is NOT touched

`finwiz.reporting` — the live path, `python_report_generator.py` and
`reporting/sections/` — is untouched. Do not confuse it with the deleted
`finwiz.tools.reporting`.

`stress_test_section.html` (deleted) shares a name with
`generate_stress_test_section()` in `reporting/sections/analysis.py`, which is
live. That function builds HTML in Python and never opened the template.

`crew_reports/` and `enriched_analysis_report.html` are live and kept.

## Test plan

- [ ] `make check` — no regression against `main` (which already fails at
      `docs-lint` from pre-existing violations in unrelated documents)
- [ ] `make coverage` ≥ 65%
- [ ] `uv run pytest tests/unit/reporting/ tests/unit/tools/ -v` green — proves
      the live reporting path survived
- [ ] `uv run plot` exits 0

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01JtXz89ibcafk3p5LP5Ewms
EOM
)"
```

Fill the checkboxes from what you actually observe, not from this template.

- [ ] **Step 5: Report the PR URL and stop**

Do not merge. The user merges with `gh pr merge --merge` (never squash, never rebase).
