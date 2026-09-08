# Remove the Orphan Rebalancing Island Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Delete the closed quantitative rebalancing island, an orchestrator method that never had a caller, a duplicate HTML render pass, and assorted dead residue — and rename six operator-facing labels that name crews deleted in #187.

**Architecture:** Six independent tasks. Four are whole-file deletion of code with no importer. Two — Task 2 and Task 4 — are surgery inside files the live report path uses, and each has a named trap that a grep-driven edit walks into.

**Tech Stack:** Python 3.12, pytest + pytest-mock, ruff, vulture, mkdocs.

**Spec:** `docs/superpowers/specs/2026-09-08-remove-orphan-rebalancing-island-design.md`

## Global Constraints

- **unittest.mock is BANNED.** Use pytest-mock (`mocker.patch()`) only. Enforced by ruff and `make check-unittest-mock`.
- **Prove code is dead before deleting it.** A present-tense grep is not proof. Use `git log -S'<symbol>' --oneline` to find the commit that removed a symbol's last reader, and read that commit to say what it was for. #187 twice concluded a symbol was dead from a grep that returned nothing; one of those deleted live aggregation that had to be restored.
- **Every sweep greps BOTH forms:** `scripts/foo.py` AND the dotted `scripts.foo`. `make check`'s own stage-contract gate is invoked as `uv run python -m scripts.check_stage_contract` at `Makefile:165` and looks unwired to a path grep.
- **Every sweep covers:** `src`, `tests`, `scripts`, `bin`, `Makefile` recipe bodies, `pyproject.toml`, `.pre-commit-config.yaml`, `.github/workflows/`, `mkdocs.yml`. #194 lost this lesson twice.
- **Docs ship in the same branch** as the change that invalidates them, never as a follow-up.
- **Line length 180** (ruff).
- `make check`'s docs-lint step **already fails on `main`**, on three files under `docs/superpowers/` that this branch does not touch. Adding no new violation is the bar.

---

### Task 1: Delete the quantitative rebalancing island

**Files:**

- Delete: `src/finwiz/quantitative/{rebalancing_engine,execution_engine,trade_generation,trade_recommendation_system,portfolio_monitor,monitoring_engine,monitoring_alerts,optimization_algorithms,portfolio_analyzer,scenario_analyzer}.py`
- Delete: `src/finwiz/exceptions/orchestrator.py`
- Delete: `tests/unit/quantitative/{test_rebalancing_engine,test_portfolio_monitor,test_trade_recommendation_system,test_portfolio_analyzer,test_scenario_analyzer}.py`
- Modify: `src/finwiz/exceptions/__init__.py:13-17,24-27`

**Interfaces:**

- Consumes: nothing.
- Produces: no `RebalancingEngine`, `PortfolioMonitor`, `OptimizationAlgorithms`, `PortfolioAnalyzer`, `ScenarioAnalyzer`, `TradeRecommendationSystem`, `PortfolioRebalancingError`, `InsufficientPriceDataError` or `OptimizationFailedError` anywhere in the tree.

- [ ] **Step 1: Prove the island closed, with history**

```bash
for m in rebalancing_engine execution_engine trade_generation trade_recommendation_system \
         portfolio_monitor monitoring_engine monitoring_alerts optimization_algorithms \
         portfolio_analyzer scenario_analyzer; do
  echo "=== $m ==="
  grep -rn "quantitative.$m\|quantitative import.*$m" src tests scripts bin --include='*.py'
done
grep -rn "exceptions.orchestrator\|PortfolioRebalancingError\|InsufficientPriceDataError\|OptimizationFailedError" src tests scripts bin
```

Expected: every hit is either another island module, one of the five test files listed above, or `exceptions/__init__.py`. **Any hit from outside that set means the island is not closed — STOP and report.**

Then the history, which is mandatory:

```bash
git log -S'RebalancingEngine' --oneline | head
git log -S'PortfolioMonitor' --oneline | head
```

The expected reading, which you must confirm rather than assume:

- `RebalancingEngine` and both exceptions lost their last outside reader in **`fe4bb2a4`** ("refactor(orchestrators,reporting): delete PortfolioRebalancingOrchestrator and its html-builder helper", #187). `orchestrators/portfolio_rebalancing.py` was the sole outside importer.
- `PortfolioMonitor` lost its last reader in **`462d5f8b`** (PR #64, 2026-06-10), which deleted `examples/portfolio_monitoring_demo.py`. That half of the island has been dead three months longer, by a different cause.

If either commit instead looks like it removed a live caller by accident, STOP and report.

- [ ] **Step 2: Confirm the two boundary cases stay**

```bash
grep -n "cost_analyzer\|CostAnalyzer" src/finwiz/quantitative/__init__.py
grep -rln "schemas.portfolio_rebalancing\|schemas import portfolio_rebalancing" src | wc -l
```

Expected: `cost_analyzer` IS re-exported in `quantitative/__init__.py` (~lines 29-38) and named in `__all__` — **it stays**, even though this deletion orphans its only `src/` importer. Removing a public re-export is an API change, not a dead-code removal.

Expected: `schemas/portfolio_rebalancing.py` has many importers including live ones — **it stays**. It shares only a name with the island.

- [ ] **Step 3: Delete the modules and their tests**

```bash
git rm src/finwiz/quantitative/rebalancing_engine.py \
       src/finwiz/quantitative/execution_engine.py \
       src/finwiz/quantitative/trade_generation.py \
       src/finwiz/quantitative/trade_recommendation_system.py \
       src/finwiz/quantitative/portfolio_monitor.py \
       src/finwiz/quantitative/monitoring_engine.py \
       src/finwiz/quantitative/monitoring_alerts.py \
       src/finwiz/quantitative/optimization_algorithms.py \
       src/finwiz/quantitative/portfolio_analyzer.py \
       src/finwiz/quantitative/scenario_analyzer.py \
       src/finwiz/exceptions/orchestrator.py \
       tests/unit/quantitative/test_rebalancing_engine.py \
       tests/unit/quantitative/test_portfolio_monitor.py \
       tests/unit/quantitative/test_trade_recommendation_system.py \
       tests/unit/quantitative/test_portfolio_analyzer.py \
       tests/unit/quantitative/test_scenario_analyzer.py
```

- [ ] **Step 4: Remove the three re-exports**

In `src/finwiz/exceptions/__init__.py`, delete the import block:

```python
from finwiz.exceptions.orchestrator import (
    InsufficientPriceDataError,
    OptimizationFailedError,
    PortfolioRebalancingError,
)
```

and these three `__all__` entries together with the `# Orchestrator exceptions` comment above them:

```text
    # Orchestrator exceptions
    "PortfolioRebalancingError",
    "InsufficientPriceDataError",
    "OptimizationFailedError",
```

The `data_quality` imports and their three `__all__` entries stay.

- [ ] **Step 5: Check `quantitative/__init__.py` for island re-exports**

```bash
grep -n "rebalancing_engine\|execution_engine\|trade_generation\|trade_recommendation\|portfolio_monitor\|monitoring_engine\|monitoring_alerts\|optimization_algorithms\|portfolio_analyzer\|scenario_analyzer" src/finwiz/quantitative/__init__.py
```

Remove any line that imports or re-exports a deleted module, including its `__all__` entry. Leave `cost_analyzer` alone.

- [ ] **Step 6: Sweep for survivors**

```bash
grep -rn "rebalancing_engine\|execution_engine\|trade_generation\|trade_recommendation_system\|portfolio_monitor\|monitoring_engine\|monitoring_alerts\|optimization_algorithms\|portfolio_analyzer\|scenario_analyzer\|exceptions.orchestrator\|PortfolioRebalancingError\|InsufficientPriceDataError\|OptimizationFailedError" \
  src tests scripts bin Makefile pyproject.toml .pre-commit-config.yaml mkdocs.yml .github 2>/dev/null
```

Expected after Steps 3-5: only `.md` hits, which Task 6 handles. Any surviving Python hit is an import you missed — fix it and re-run until only docs remain.

- [ ] **Step 7: Run lint and the suite**

Run: `make lint && make test`

Both must be green. Count the tests you removed and check the arithmetic:

```bash
for f in test_rebalancing_engine test_portfolio_monitor test_trade_recommendation_system \
         test_portfolio_analyzer test_scenario_analyzer; do
  echo -n "$f: "; git show HEAD:tests/unit/quantitative/$f.py | grep -c "def test_"
done
```

The sum must equal the drop in the passing count from the pre-task baseline. If it does not, something else lost tests — report it.

- [ ] **Step 8: Commit**

```bash
git commit -m "$(cat <<'EOM'
refactor(quantitative): delete the orphan rebalancing island

Eleven modules, 2782 lines, 1199 statements, plus the five test files that were
their only non-island referrers.

RebalancingEngine and the two orchestrator exceptions lost their last outside
reader in fe4bb2a4 (#187), which deleted PortfolioRebalancingOrchestrator — the
sole importer. PortfolioMonitor's half died earlier and separately: 462d5f8b
(PR #64, 2026-06-10) removed examples/portfolio_monitoring_demo.py, its only
consumer. It was never wired into the flow.

The issue named seven modules; optimization_algorithms, portfolio_analyzer and
scenario_analyzer belong to the same closed set. exceptions/orchestrator.py is
dead in full — OptimizationFailedError has no raiser or catcher either.

cost_analyzer.py stays: this deletion orphans it, but it is re-exported in
quantitative/__init__.py's __all__, which makes removing it an API change rather
than a dead-code removal. schemas/portfolio_rebalancing.py stays — 17 importers,
several live.

Refs #195.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01JtXz89ibcafk3p5LP5Ewms
EOM
)"
```

---

### Task 2: Delete `generate_final_report` and its two exclusive helpers

**Files:**

- Modify: `src/finwiz/orchestrators/reporting_orchestrator.py:119-149`
- Modify: `src/finwiz/orchestrators/reporting/data_loading.py:247-275`
- Modify: `tests/unit/orchestrators/test_reporting_orchestrator.py` (remove tests of the deleted method, if any)

**Interfaces:**

- Consumes: nothing from Task 1.
- Produces: no `generate_final_report`, `_extract_portfolio_review` or `_extract_deep_analysis`. Every other `data_loading.py` helper survives unchanged.

**THE TRAP IN THIS TASK.** `data_loading.py` is shared with the live report path. Only two of its helpers are exclusive to the method being deleted. These six MUST survive, because `generate_python_report()` (`reporting_orchestrator.py:60-107`) calls them:

`_get_portfolio_review_from_state`, `_convert_to_portfolio_review`, `_read_deep_analysis_from_files`, `_merge_deep_analysis_into_portfolio`, `_save_merged_portfolio_review`, `_generate_python_report`.

Deleting any of those breaks production reporting. This is surgery inside a live file, not a file deletion.

- [ ] **Step 1: Prove zero callers, and read the history**

```bash
grep -rn "generate_final_report\|_extract_portfolio_review\|_extract_deep_analysis" src tests scripts bin docs
git log --all -S'generate_final_report' --oneline -- src/finwiz/orchestrators/reporting_orchestrator.py
```

Expected: `generate_final_report` has no caller anywhere. `_extract_portfolio_review` is called only at `reporting_orchestrator.py:137`; `_extract_deep_analysis` only at `:140` — both inside the method being deleted. One unrelated hit in `.claude/skills/output-standards/SKILL.md:204` is a CrewAI `@task` example, not a call.

Expected from the log: **exactly one commit**, `4600d1a7` ("refactor(orchestrators): Decompose monolithic flow orchestrator into modular specialized orchestrators"). There is no last-caller commit to find — the method was born dead as a decomposition-era transcription. The only `.generate_final_report(...)` call that ever existed targets a different class in `flow_orchestrator_original.py.bak:4243`, whose `FinalReportGenerator` was deleted separately in `2351111e`.

If the log shows a commit that removed a real call site, STOP and report.

- [ ] **Step 2: Confirm the six shared helpers have live callers**

```bash
for h in _get_portfolio_review_from_state _convert_to_portfolio_review _read_deep_analysis_from_files \
         _merge_deep_analysis_into_portfolio _save_merged_portfolio_review _generate_python_report; do
  echo "=== $h ==="; grep -rn "$h" src/finwiz/orchestrators/ | grep -v "def $h"
done
```

Each must show at least one call from `generate_python_report` in `reporting_orchestrator.py`. **Do not delete any of them.**

- [ ] **Step 3: Delete the method**

Remove `generate_final_report` from `src/finwiz/orchestrators/reporting_orchestrator.py` — the whole `def generate_final_report(` block from its signature through its final `raise`, including the docstring.

- [ ] **Step 4: Delete the two exclusive helpers**

Remove `_extract_portfolio_review` and `_extract_deep_analysis` from `src/finwiz/orchestrators/reporting/data_loading.py` — both complete `def` blocks including docstrings. Leave `_load_json_file` above them and `_save_merged_portfolio_review` below them intact.

- [ ] **Step 5: Remove any test of the deleted method**

```bash
grep -n "generate_final_report\|_extract_portfolio_review\|_extract_deep_analysis" tests/unit/orchestrators/test_reporting_orchestrator.py
```

Delete each test function that exercises a deleted name — the whole `def test_...` block, plus any decorator and any fixture used by nothing else. If the grep returns nothing, note that in your report and move on.

- [ ] **Step 6: Prove the live report path still works**

Run: `uv run pytest tests/unit/orchestrators/ tests/unit/reporting/ -q`

Both directories must be green. This is the check that catches a wrongly-deleted shared helper.

- [ ] **Step 7: Run lint and the full suite**

Run: `make lint && make test`

- [ ] **Step 8: Commit**

```bash
git commit -m "$(cat <<'EOM'
refactor(orchestrators): delete generate_final_report, never called

The method was born dead at 4600d1a7, a decomposition-era transcription of a
flow that lived in flow_orchestrator_original.py.bak. The only
.generate_final_report(...) call that has ever existed in this repository
targeted a different class, FinalReportGenerator, deleted separately in 2351111e.
There is no last-caller commit because there was never a caller.

_extract_portfolio_review and _extract_deep_analysis go with it — they had no
other caller. The six sibling helpers in data_loading.py stay: generate_python_report
uses all of them, and that is the live report path.

Refs #195.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01JtXz89ibcafk3p5LP5Ewms
EOM
)"
```

---

### Task 3: Rename the `*_crew` labels; delete `validation/flow.py`; fix the advice text

**Files:**

- Modify: `src/finwiz/orchestrators/discovery_orchestrator.py:87,114,166,193,245,268`
- Delete: `src/finwiz/validation/flow.py`
- Delete: `tests/unit/validation/test_data_flow_validator.py`
- Modify: `src/finwiz/integration/validation.py:54-79`

**Interfaces:**

- Consumes: nothing.
- Produces: no `"stock_crew"`, `"etf_crew"` or `"crypto_crew"` string literal anywhere in `src/`; no `CrewDataContract`.

Three independent items that happen to share a subject. None depends on another.

- [ ] **Step 1: Confirm the rename is inert**

```bash
grep -rn "availability_tracker\|DataAvailabilityTracker\|_tracked_sources\|get_availability_summary" src tests
grep -rn "stock_crew\|etf_crew\|crypto_crew" output/ output0905/ 2>/dev/null
```

The expected picture, which you must confirm:

`DataAvailabilityTracker` (`integration/availability.py`) has seven read methods — `get_availability_summary` (`:131`), `get_freshness_warnings` (`:182`), `get_source_status` (`:212`), `is_source_available` (`:225`), `is_source_stale` (`:241`), `get_tracked_source_names` (`:262`), `format_summary_for_report` (`:272`) — and **every one has zero callers outside the class**. The tracker is a write-only sink. The second grep must return **no matches**: these labels are persisted nowhere, so no cache key, no on-disk JSON and no `run_summary` depends on them.

If any read method turns out to have a caller, or if the labels appear in `output/`, STOP and report — the rename is no longer free.

- [ ] **Step 2: Rename the six literals**

In `src/finwiz/orchestrators/discovery_orchestrator.py`, replace exactly these six `source=` values:

| Line | Old | New |
|---|---|---|
| 87 | `source="crypto_crew"` | `source="crypto_discovery"` |
| 114 | `source="crypto_crew"` | `source="crypto_discovery"` |
| 166 | `source="stock_crew"` | `source="stock_discovery"` |
| 193 | `source="stock_crew"` | `source="stock_discovery"` |
| 245 | `source="etf_crew"` | `source="etf_discovery"` |
| 268 | `source="etf_crew"` | `source="etf_discovery"` |

The new names describe what the code actually does: each site wraps a pure-Python Phase 4 discovery scanner whose results are saved by `_save_discovery_results("stock", …)`. The comment above two of these sites already reads "Track actual Python execution outcome".

- [ ] **Step 3: Prove `validation/flow.py` dead, then delete it**

```bash
grep -rn "validation.flow\|validation import flow\|CrewDataContract\|DataFlowValidator" src tests scripts bin
git log -S'CrewDataContract' --oneline | head
```

Expected: exactly one importer, `tests/unit/validation/test_data_flow_validator.py:7`. Nothing in `src/` imports it.

**Do not be fooled by** `src/finwiz/validation/ai_output.py:404,458` — those are the English words "validation flow" inside a docstring and a log message, not imports.

Then:

```bash
git rm src/finwiz/validation/flow.py tests/unit/validation/test_data_flow_validator.py
```

Check `src/finwiz/validation/__init__.py` for a re-export of anything from `flow.py` and remove it if present.

**Scope note:** the trace flagged ten more modules in the `validation/` subtree as unreachable. They are **out of scope** — they need their own `git log -S` pass. Delete only `flow.py`.

- [ ] **Step 4: Fix the advice text**

In `src/finwiz/integration/validation.py`, the loop at `:54` iterates `freshness_report.missing_data`, whose values are output **directory** names (`"stock"`, `"etf"`, `"crypto"`, `"discovery"`, `"portfolio"` — hardcoded at `orchestrators/registry/registry_data_retrieval.py:57`), not crew names. Rewrite the four operator-facing strings so they stop naming crews:

```text
                        error_message=f"No data found for {crew_name}",
                        expected_path=str(self.integration_manager.output_dir / crew_name),
                        recovery_suggestions=[
                            f"Run the pipeline to populate output/{crew_name}",
                            f"Check whether the {crew_name} phase completed successfully",
                        ],
```

and in the `stale_data` loop below it:

```text
                        error_message=f"Stale data detected for {crew_name}",
                        recovery_suggestions=[
                            f"Re-run the pipeline to refresh output/{crew_name}",
                            "Check whether the run completed successfully",
                        ],
```

**Leave the `crew_name` loop variable and the `IntegrationError.crew_name` field alone.** Renaming a schema field is a wider change than this task, and the field is what other code reads.

- [ ] **Step 5: Sweep**

```bash
grep -rn "stock_crew\|etf_crew\|crypto_crew\|CrewDataContract" src tests scripts bin Makefile pyproject.toml .github mkdocs.yml 2>/dev/null
```

Expected: no hits outside `.md` files. Docs are Task 6's.

- [ ] **Step 6: Run lint and the suite**

Run: `make lint && make test`

- [ ] **Step 7: Commit**

```bash
git commit -m "$(cat <<'EOM'
refactor(discovery): name the discovery scanners, not deleted crews

#187 deleted stock_crew, etf_crew and crypto_crew but left six source= labels
naming them. #195 withheld the rename because validation/flow.py's
CrewDataContract registry carried the same three keys and the namespaces had not
been established.

They are unrelated. validation/flow.py has exactly one importer in the repository
— its own test — so that dictionary is never constructed at runtime. The tracker
the labels feed is a write-only sink: all seven of DataAvailabilityTracker's read
methods have zero callers outside the class, and a grep across two runs' output/
trees finds these labels in no cache key, no JSON and no run_summary. There was
no coupling to break.

So: the six literals become *_discovery, naming the pure-Python Phase 4 scanners
that actually produce the data; validation/flow.py and its 546-line test are
deleted; and integration/validation.py's advice stops telling an operator to run
a crew. That advice never reaches anyone — both accessor entry points are
uncalled — and it was never sourced from these labels anyway: its values are the
hardcoded output directory names.

Refs #195.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01JtXz89ibcafk3p5LP5Ewms
EOM
)"
```

---

### Task 4: Delete the duplicate render pass

**Files:**

- Delete: `src/finwiz/orchestrators/reporting/enriched_html.py`
- Modify: `src/finwiz/orchestrators/reporting_orchestrator.py:17,22,85-89`
- Modify: `tests/unit/orchestrators/test_reporting_orchestrator.py:976-1017`

**Interfaces:**

- Consumes: nothing from Tasks 1-3.
- Produces: no `EnrichedHtmlMixin` or `generate_enriched_html_reports`. A run writes `{ticker}_report.html` and no `{ticker}_enriched.html`.

**THE TRAP IN THIS TASK.** `EnrichedHtmlMixin._iter_enriched_files` (`enriched_html.py:22-24`) is a `NotImplementedError` stub declared for type-checking. The **real** `_iter_enriched_files` lives at `orchestrators/reporting/enrichment.py:193`, is provided by `ReportEnrichmentMixin`, and is **also used by `_iter_enriched_records`**. Delete the stub with its file; the real one must survive untouched.

- [ ] **Step 1: Confirm which render is canonical**

```bash
grep -rn "_report\.html" src tests | grep -v "^docs"
grep -rn "_enriched\.html" src tests docs scripts bin Makefile
```

Expected: `_report.html` is referenced by `reporting/sections/holdings.py:55` (the per-holding link the final report builds), `holdings.py:50,109`, `orchestrators/reporting/enrichment.py:276` (`distilled["report_link"]`), `reporting/individual_report_generator.py:230`, and two test files.

Expected: `_enriched.html` is referenced by **nothing** except the deleted function's own test (`test_reporting_orchestrator.py:1002`) and one doc example (`reporting/CLAUDE.md:75`).

If anything live reads `_enriched.html`, STOP and report — the wrong side is being deleted.

- [ ] **Step 2: Confirm the outputs really are redundant**

There are real artifacts on disk from the 2026-09-07 run.

```bash
diff output/stock/AAPL_report.html output/stock/AAPL_enriched.html
```

Expected: exactly two differing lines, both the `<p>Rapport généré par FinWiz le …</p>` generation timestamp. Same byte count otherwise. If the files differ in content, STOP and report — the passes are not redundant after all.

- [ ] **Step 3: Verify the stub-versus-real distinction before deleting**

```bash
grep -n "_iter_enriched_files" src/finwiz/orchestrators/reporting/enriched_html.py \
                              src/finwiz/orchestrators/reporting/enrichment.py
grep -n "_iter_enriched_records" src/finwiz/orchestrators/reporting/enrichment.py
```

Expected: `enriched_html.py` has the `raise NotImplementedError` stub; `enrichment.py:193` has the real implementation, and `_iter_enriched_records` calls it. Confirm this yourself before Step 4 — it is the one way this task can break production reporting.

- [ ] **Step 4: Delete the file, the import, the base class and the call site**

```bash
git rm src/finwiz/orchestrators/reporting/enriched_html.py
```

In `src/finwiz/orchestrators/reporting_orchestrator.py`:

Remove the import at line 17:

```python
from finwiz.orchestrators.reporting.enriched_html import EnrichedHtmlMixin
```

Change the class declaration at line 22 from:

```python
class ReportingOrchestrator(ReportDataLoadingMixin, ReportEnrichmentMixin, EnrichedHtmlMixin):
```

to:

```python
class ReportingOrchestrator(ReportDataLoadingMixin, ReportEnrichmentMixin):
```

Remove the call site (lines 85-89), the whole block:

```python
            # Generate individual HTML reports from enriched JSON files
            enriched_html_paths = self.generate_enriched_html_reports()
            enriched_count = sum(len(paths) for paths in enriched_html_paths.values())
            if enriched_count > 0:
                self.logger.info(f"✅ Generated {enriched_count} individual HTML reports from enriched data")
```

The `_generate_python_report` call above it and the `self.state.report_generation_success = True` block below it both stay.

- [ ] **Step 5: Remove the tests of the deleted function**

```bash
grep -n "generate_enriched_html_reports\|EnrichedHtmlMixin" tests/unit/orchestrators/test_reporting_orchestrator.py
```

Delete each test function exercising the deleted name — the whole `def test_...` block including decorators. Around `:976-1017`.

- [ ] **Step 6: Prove the live report path survives**

Run: `uv run pytest tests/unit/orchestrators/ tests/unit/reporting/ -q`

Both green. Then confirm the real `_iter_enriched_files` is still reachable:

```bash
grep -n "_iter_enriched_files\|_iter_enriched_records" src/finwiz/orchestrators/reporting/enrichment.py
```

Both must still be present.

- [ ] **Step 7: Run lint and the full suite**

Run: `make lint && make test`

- [ ] **Step 8: Commit**

```bash
git commit -m "$(cat <<'EOM'
refactor(reporting): delete the second, redundant HTML render pass

_store_enriched_analysis renders {ticker}_report.html at analysis time;
generate_enriched_html_reports re-read every {ticker}_enriched.json in the
reporting phase and rendered {ticker}_enriched.html from it — same renderer, same
template, once from the in-memory model and once from the JSON serialized from
that same model.

Measured on the 2026-09-07 run rather than reasoned from the code: all 64 file
pairs differ by exactly one line, the generation timestamp. Same byte count, same
1172 lines.

_report.html is the canonical one — reporting/sections/holdings.py:55 and
orchestrators/reporting/enrichment.py:276 build the report's per-holding links
from it, and nothing anywhere reads _enriched.html except the deleted function's
own test. The reporting phase was producing 64 orphan files per run and paying a
full second render to do it.

EnrichedHtmlMixin's _iter_enriched_files was a NotImplementedError stub; the real
one in enrichment.py:193 is shared with _iter_enriched_records and is untouched.

Refs #195.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01JtXz89ibcafk3p5LP5Ewms
EOM
)"
```

---

### Task 5: Delete the residue found during #194's review

**Files:**

- Delete: `bin/regenerate_reports.py`, `bin/debug_config.py` (and the now-empty `bin/`)
- Delete: `scripts/verify_html_reports.py`, `tests/unit/scripts/test_verify_html_reports.py`
- Delete: `src/finwiz/tools/rebalancing_calculations.py`, `tests/unit/tools/test_rebalancing_calculations.py`
- Modify: `pyproject.toml:164,204,207,209`

**Interfaces:**

- Consumes: Task 1's island deletion (two of the four `pyproject.toml` rows become stale only after it lands).
- Produces: no `bin/` directory; no `RebalancingCalculations`; every `per-file-ignores` path resolving to a real file.

- [ ] **Step 1: Prove each item dead — BOTH grep forms**

```bash
grep -rn "regenerate_reports\|debug_config\|verify_html_reports\|rebalancing_calculations\|RebalancingCalculations" \
  src tests scripts bin Makefile pyproject.toml .pre-commit-config.yaml mkdocs.yml .github docs 2>/dev/null
grep -rn "scripts\.verify_html_reports\|scripts\.regenerate\|bin\." Makefile .github 2>/dev/null
```

The second grep matters: `make check`'s stage-contract gate is wired as `uv run python -m scripts.check_stage_contract` at `Makefile:165` and a `scripts/` path grep misses it entirely. The trace that produced this plan was itself briefly fooled by exactly that.

Expected: `bin/regenerate_reports.py` imports `src.finwiz.tools.html_output_tool` (`:16`), a path never tracked in this repo's history — verify with `git log -- src/finwiz/tools/html_output_tool.py`, which must return nothing. `bin/debug_config.py` imports `finwiz.utils.config_loader` (`:17`); confirm `src/finwiz/utils/` contains only a `CLAUDE.md`. `verify_html_reports.py`'s only consumer is its own test. `RebalancingCalculations` has zero `src/` importers and is already self-documented as dead at `tools/CLAUDE.md:44`.

- [ ] **Step 2: Delete the six files**

```bash
git rm bin/regenerate_reports.py bin/debug_config.py \
       scripts/verify_html_reports.py tests/unit/scripts/test_verify_html_reports.py \
       src/finwiz/tools/rebalancing_calculations.py tests/unit/tools/test_rebalancing_calculations.py
rmdir bin 2>/dev/null || true
```

- [ ] **Step 3: Sweep the whole per-file-ignores block, not just the four known rows**

Do not hand-edit only the four lines this plan names. Check every literal path key in `[tool.ruff.lint.per-file-ignores]` against the filesystem:

```bash
python3 - <<'PY'
import pathlib, re
s = pathlib.Path("pyproject.toml").read_text()
block = s.split("[tool.ruff.lint.per-file-ignores]")[1].split("\n[")[0]
for line in block.splitlines():
    m = re.match(r'\s*"([^"]+)"\s*=', line)
    if m and "*" not in m.group(1) and not pathlib.Path(m.group(1)).exists():
        print("STALE:", m.group(1))
PY
```

Remove every row it reports. Expect at least four: `src/finwiz/tools/etf_crew.py` (`:164`, deleted in `4a8185e1`), `src/finwiz/quantitative/constraint_handlers.py` (`:204`, deleted in `5cea937d`), and `portfolio_analyzer.py` (`:207`) plus `trade_recommendation_system.py` (`:209`), which Task 1 deleted. Glob patterns like `tests/**/*.py` are fine and must stay.

Ruff drops unmatched entries silently, so a green lint run is not evidence these rows are live. That is why they accumulated.

- [ ] **Step 4: Run lint and the suite**

Run: `make lint && make test`

Removing a `per-file-ignore` can only expose a violation, never hide one — so a clean lint run here is real proof the removed rows were dead.

- [ ] **Step 5: Commit**

```bash
git commit -m "$(cat <<'EOM'
chore: delete the dead scripts, tool and stale lint exemptions

bin/ is a directory where nothing runs. regenerate_reports.py imports
src.finwiz.tools.html_output_tool, a path never tracked in this repository's
history — that import has been wrong since it was written. debug_config.py
imports finwiz.utils.config_loader, which does not exist, and appends bin/src to
sys.path, a directory that has never existed. Neither is referenced by any
Makefile target, entry point, pre-commit hook or workflow.

scripts/verify_html_reports.py checks for output artifacts the chain #194 deleted
would have produced; PR #64's own plan listed it for deletion and it survived
that pass. RebalancingCalculations had zero src/ importers and was already
self-documented as dead in tools/CLAUDE.md.

The per-file-ignores rows were swept whole against the tree rather than row by
row: ruff drops unmatched entries silently, which is how they accumulated across
three separate cleanups.

Refs #195.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01JtXz89ibcafk3p5LP5Ewms
EOM
)"
```

---

### Task 6: Documentation, full check, and PR

**Files:**

- Modify: `src/finwiz/quantitative/CLAUDE.md:26-31,72`
- Modify: `src/finwiz/exceptions/CLAUDE.md:21-22,30-31,36,43,46,59-60`
- Modify: `src/finwiz/reporting/CLAUDE.md:55,75`
- Modify: `src/finwiz/tools/CLAUDE.md:44`
- Modify: `docs/how-to/OPERATIONS_GUIDE.md:1185,1188,1208`
- Modify: `docs/tutorials/portfolio_analysis.md:97`
- Modify: `CHANGELOG.md`

**Interfaces:**

- Consumes: every prior task's deletions.
- Produces: no documentation naming a symbol this branch removed, outside `docs/superpowers/`.

- [ ] **Step 1: Find every stale doc reference**

```bash
grep -rln "rebalancing_engine\|execution_engine\|trade_generation\|trade_recommendation_system\|portfolio_monitor\|PortfolioMonitor\|monitoring_engine\|monitoring_alerts\|optimization_algorithms\|portfolio_analyzer\|scenario_analyzer\|PortfolioRebalancingError\|InsufficientPriceDataError\|OptimizationFailedError\|generate_final_report\|generate_enriched_html_reports\|EnrichedHtmlMixin\|_enriched\.html\|CrewDataContract\|stock_crew\|etf_crew\|crypto_crew\|rebalancing_calculations\|RebalancingCalculations\|verify_html_reports\|regenerate_reports\|debug_config" \
  src docs .planning --include='*.md' | grep -v "^docs/superpowers/"
```

This list is authoritative — larger than the file list above if the greps find more. Update every file it names.

**Do not edit anything under `docs/superpowers/`** — those specs and plans describe this deletion and are correct as written.

- [ ] **Step 2: Rewrite each file**

Delete passages describing removed symbols rather than annotating them. Where a doc shows a usage example importing a deleted name, **remove the example** — an example that cannot run is worse than no example.

Specific known items:

- `quantitative/CLAUDE.md:26-31,72` — the module tree and description list island members.
- `exceptions/CLAUDE.md` — remove the three orchestrator exceptions throughout; the `data_quality` exceptions stay.
- `reporting/CLAUDE.md:55` documents `generate_enriched_html_reports()` as a sanctioned path; `:75` shows the `_enriched.html` output path in an example. Both become wrong.
- `tools/CLAUDE.md:44` — the `RebalancingCalculations` row goes with the file.
- `OPERATIONS_GUIDE.md:1185,1188,1208` documents `PortfolioMonitor` usage that will not exist.
- `docs/tutorials/portfolio_analysis.md:97` references `quantitative/portfolio_monitor.py`.

- [ ] **Step 3: Add the CHANGELOG entry**

Under the existing `## [Unreleased]` → `### Removed` heading, following the format of the `#193` and `#194` entries already there:

```markdown
- The orphan quantitative rebalancing island (eleven modules, ~1,200 statements),
  `ReportingOrchestrator.generate_final_report()`, the duplicate enriched-HTML
  render pass, `validation/flow.py`, `RebalancingCalculations`, and two dead
  scripts under `bin/`. None had a reachable caller. The six `*_crew` availability
  labels now name the Python discovery scanners that actually produce the data.
  ([#195](https://github.com/fjacquet/finwiz/issues/195))
```

- [ ] **Step 4: Verify the docs now tell the truth**

Re-run Step 1's grep. Expected: only `docs/superpowers/` hits, plus any past-tense prose you wrote that names a deleted symbol while describing its removal — that is correct and expected; note it in your report.

Then check every claim you wrote is true of the tree as it stands. #194's review found a doc asserting a script had been deleted when it had not.

- [ ] **Step 5: Build the docs**

Run: `uv run mkdocs build --strict --clean`

It fails on broken internal links. If you deleted a section another doc linked to, fix the linking doc.

- [ ] **Step 6: Run the full check**

Run: `make check`

Expected: docs-lint fails on `docs/superpowers/plans/2026-09-07-remove-uncalled-crew-subsystem.md`, `docs/superpowers/specs/2026-09-07-remove-uncalled-crew-subsystem-design.md` and `docs/superpowers/specs/2026-09-06-per-asset-class-fact-pack-design.md` — **pre-existing on `main`, none touched by this branch**. Confirm the failure names only files absent from `git diff --name-only <merge-base>..HEAD`. If it names a file you touched, fix that file.

Also run:

```bash
make coverage
uv run plot
```

Coverage must be ≥ 65% — report the real number. `plot` must exit 0.

- [ ] **Step 7: Run the pipeline**

This is the only proof for Tasks 2 and 4, which touched the live report path. The unit suite cannot show that a run still produces its report.

Run: `uv run kickoff`

Then verify the duplicate render is gone and the canonical one survives:

```bash
ls output/{stock,etf,crypto}/*_report.html 2>/dev/null | wc -l    # expect 64-ish, non-zero
ls output/{stock,etf,crypto}/*_enriched.html 2>/dev/null | wc -l  # expect 0
```

A non-zero `_enriched.html` count means Task 4's call site was not fully removed. A zero `_report.html` count means the analysis-time render broke — investigate before proceeding.

If a full run is not possible in your environment, say so explicitly in your report rather than skipping the step silently.

- [ ] **Step 8: Commit and open the PR**

```bash
git add -A
git commit -m "$(cat <<'EOM'
docs(#195): retire the deleted subsystems from the documentation

Refs #195.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01JtXz89ibcafk3p5LP5Ewms
EOM
)"
git push -u origin refactor/remove-orphan-rebalancing-island
```

Then open the PR with `gh pr create`, body covering: what was deleted and the history proving each dead; the two traps (the shared `data_loading.py` helpers, the `_iter_enriched_files` stub versus the real one); the six places issue #195's own text was wrong; the measured evidence for the duplicate render; and the verification numbers including the pipeline run. Close with:

```text
Closes #195.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01JtXz89ibcafk3p5LP5Ewms
```

---

## Out of scope — for a follow-up issue

The trace behind this plan ran reachability over all 435 modules and found **78 unreachable**. This branch deletes only what #195 named plus the #194 residue. Two clusters were hand-verified as high confidence and deliberately left:

- **Error-handling helpers:** `orchestrators/error_handling/{fallback,handlers,missing_data,recovery,validation_recovery}.py`. `error_handling_orchestrator.py` imports none of them; the package's single live member is `core_analysis_error_handler`.
- **Validation subtree:** the ten `validation/` modules besides `flow.py`, rooted at two dead entry modules — `integration/cli.py` (no `[project.scripts]` entry) and `integration/middleware.py` (no importers).

Plus medium-confidence leads across `reporting/individual_report_generator.py`, nine more `quantitative/` modules, six `schemas/` modules, and clusters in `tools/`, `infrastructure/` and `integration/`.

**Module-level unreachability is necessary but not sufficient.** Each needs its own `git log -S` pass before deletion — that is exactly where #187 went wrong twice. Full evidence is in `.superpowers/sdd/trace-195-findings.md`.
