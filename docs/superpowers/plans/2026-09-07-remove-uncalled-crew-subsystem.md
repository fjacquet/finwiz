# Removing the Uncalled Crew Subsystem — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Delete six crews that nothing calls, the factory that builds them, and the reporting and state machinery that exists only to carry their output.

**Architecture:** Deletion proceeds leaves-first — crew packages, then the factory and its dependency-injection wiring, then the reporting chain, then the schemas, state fields and feature flags. Each task must leave both test suites green on its own, so a step that turns out to be wrong can be dropped without unpicking the ones after it. The acceptance test is a live 3-holding `uv run kickoff`, not the unit suite.

**Tech Stack:** Python 3.13, CrewAI (Flow + tools retained), Pydantic v2, pytest, pytest-mock, hypothesis, uv.

**Spec:** `docs/superpowers/specs/2026-09-07-remove-uncalled-crew-subsystem-design.md`

## Global Constraints

- **unittest.mock is BANNED** — use pytest-mock only (`mocker.patch()`). Enforced by ruff and `make check-unittest-mock`.
- **Never run `make lint` or `make check`** — they reformat ~66 unrelated markdown files. Use `uv run ruff check --fix <paths>` and `uv run ruff format <paths>` on touched files only.
- **Never use `git checkout --`, `git restore`, or bare `git stash`/`git stash pop`** — the stash stack is shared with other worktrees. To set work aside use `git stash push -u -m "<unique-tag>"`, capture the SHA from `git stash list --format='%H %gs'`, restore with `git stash apply <sha>`, and drop by re-finding the tag.
- **Never `git add -A` or `git add .`** — always name paths explicitly.
- **`uv.lock` regenerates on every `uv run`** with reordered keys. It is churn, not your change. Never stage it; set it aside with the tagged-stash protocol above if it blocks an operation.
- **Every change ships with the docs it invalidates**, in the same branch, never as a follow-up.
- **`uv run kickoff` costs real money.** Only Tasks 1 and 9 run it, and only with the 3-holding CSV overrides. Never run it with the real portfolio.
- **Do not merge anything.** Open the PR; the human merges.
- **`deep_analysis` stays.** It is the one crew that runs, reached from `analysis/_helpers.py:95`. So do `DeepAnalysisCrewExport`, the Flow framework (`Flow[FinwizState]`, `@start`, `@listen`), and the `crewai.tools` / `crewai_custom_tools` abstraction.

---

## File Structure

**Deleted outright:**

| Path | Lines | Why |
|---|---|---|
| `src/finwiz/crews/stock_crew/` | 901 | no caller; cannot even be instantiated |
| `src/finwiz/crews/etf_crew/` | 775 | no caller |
| `src/finwiz/crews/crypto_crew/` | 852 | no caller |
| `src/finwiz/crews/investment_discovery_crew/` | 1005 | no caller |
| `src/finwiz/crews/portfolio_rebalancing_crew/` | 1172 | no caller |
| `src/finwiz/crews/report_crew/` | 1505 | no caller |
| `src/finwiz/crew_factory.py` | 500 | constructed at `flows/orchestrator.py:107`, never invoked |
| `src/finwiz/reporting/consolidator.py` | — | zero importers |
| `src/finwiz/reporting/export_loaders.py` | — | zero importers |
| `src/finwiz/reporting/html_collector.py` | — | imported only by `consolidator.py` |
| `src/finwiz/reporting/final_report_generator.py` | — | imported only by its own test |
| `src/finwiz/reporting/stock_report_generator.py` | 102 | reachable only through `CREW_GENERATORS` |
| `src/finwiz/reporting/etf_report_generator.py` | — | same |
| `src/finwiz/reporting/crypto_report_generator.py` | — | same |
| `src/finwiz/reporting/rebalancing_report_generator.py` | — | same |
| `src/finwiz/reporting/discovery_report_generator.py` | — | same |
| `tests/validation/stock_crew_validation.py` | — | manual runner for a deleted crew |

**Modified:**

| Path | Change |
|---|---|
| `src/finwiz/main.py:21,39` | drop the `StockCrew` import and `__all__` entry, and any sibling crew entries |
| `src/finwiz/flows/orchestrator.py:107` | drop `CrewFactory` construction and its import |
| `src/finwiz/flows/orchestrator_registry.py:30,45,50` | drop `"crew_factory"` from three `deps_keys` tuples |
| `src/finwiz/orchestrators/deep_analysis_orchestrator.py:162,597` | drop `self.crew_factory` and the kwarg it forwards |
| `src/finwiz/orchestrators/alternatives_matching_orchestrator.py` | drop the `crew_factory` constructor parameter |
| `src/finwiz/orchestrators/error_handling_orchestrator.py:25` | drop `crew_factory` from the docstring |
| `src/finwiz/reporting/__init__.py` | drop `CREW_GENERATORS`, `get_generator_for_crew`, and the generator imports |
| `src/finwiz/orchestrators/reporting/crew_html.py` | drop the five crew-export methods, keep `generate_enriched_html_reports` |
| `src/finwiz/orchestrators/reporting_orchestrator.py:165` | drop the `generate_all_crew_html_reports` call |
| `src/finwiz/schemas/crew_exports.py` | keep `CrewExportBase`, `DeepAnalysisCrewExport`; delete the rest after verifying `ConsolidatedReportExport` |
| `src/finwiz/flow_state_models.py:130-148` | delete fifteen `{stock,etf,crypto}_analysis_*` fields |
| `src/finwiz/flow_state_utils.py:51-53,64-74` | delete the branches reading them |
| `src/finwiz/orchestrators/validation_orchestrator.py:275-276,394-396` | delete the branches reading them |
| `src/finwiz/config/features/definitions.py:157-176` | delete `stock_analysis`, `etf_analysis`, `crypto_analysis` |
| `CLAUDE.md` | Key Components table, Crew Pattern section |
| `CHANGELOG.md` | one entry under Removed |

---

## Task 1: Capture the acceptance baseline

**Files:**
- Create: `/tmp/crew-removal-baseline/run_summary.before.json` (outside the repo — never commit it)

**Interfaces:**
- Produces: a `run_summary.json` from unmodified `main`, the yardstick every later task is measured against.

This task runs **before any deletion**. The unit suite passes today with this whole subsystem already dead, so it cannot tell you whether a deletion broke something. Only a live run can.

- [ ] **Step 1: Create the 3-holding portfolio**

```bash
mkdir -p /tmp/crew-removal-baseline/mini
printf 'Name,Ticker,Currency,Active,Quantity\nApple,Yahoo:AAPL,USD,true,5\n' > /tmp/crew-removal-baseline/mini/stock.csv
printf 'Name,Ticker,Currency,Active,Quantity\n2B7K,Yahoo:2B7K.DE,EUR,true,5\n' > /tmp/crew-removal-baseline/mini/etf.csv
printf 'Name,Ticker,Active,Quantity\nBitcoin,BTC,true,0.05\n' > /tmp/crew-removal-baseline/mini/crypto.csv
```

These three tickers exercise all three fact-pack shapes (equity / fund / crypto). Discovery is *not* weakened by the small portfolio — its universe excludes portfolio tickers, so three holdings means a **larger** universe scanned than the real portfolio.

- [ ] **Step 2: Run the baseline kickoff**

```bash
PORTFOLIO_STOCK_CSV=/tmp/crew-removal-baseline/mini/stock.csv \
PORTFOLIO_ETF_CSV=/tmp/crew-removal-baseline/mini/etf.csv \
PORTFOLIO_CRYPTO_CSV=/tmp/crew-removal-baseline/mini/crypto.csv \
uv run kickoff
```

Expected: about 6 minutes, about $0.04, exit code 0.

- [ ] **Step 3: Save the baseline and confirm it is a PASS**

```bash
cp output/run_summary.json /tmp/crew-removal-baseline/run_summary.before.json
uv run python -c "
import json
d = json.load(open('/tmp/crew-removal-baseline/run_summary.before.json'))
print('VERDICT:', d['verdict'])
for c in d['checks']:
    print(f\"  {'OK ' if c['passed'] else 'FAIL'} {c['name']:18} {c['observed'][:60]}\")
"
```

Expected: `VERDICT: PASS` and eight `OK` lines. **If the verdict is not PASS, stop and report** — the baseline must be green or it cannot serve as a comparison.

- [ ] **Step 4: Record both suite baselines**

```bash
uv run pytest -q 2>&1 | tail -2
uv run pytest -m integration -q 2>&1 | tail -2
```

Expected: about `5415 passed, 31 skipped, 0 failed` and `51 passed, 1 skipped, 0 failed`. Write both exact numbers into your report — later tasks compare against them.

- [ ] **Step 5: No commit**

This task produces no repository change. Report the baseline numbers and the eight check names; the next task starts from them.

---

## Task 2: Delete the six crew packages

**Files:**
- Delete: `src/finwiz/crews/{stock,etf,crypto,investment_discovery,portfolio_rebalancing,report}_crew/` (whole directories)
- Delete: `tests/validation/stock_crew_validation.py`
- Modify: `src/finwiz/main.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `src/finwiz/crews/` containing only `deep_analysis/` and `helpers/`.

- [ ] **Step 1: Confirm nothing outside the factory imports them**

```bash
grep -rn "stock_crew\|etf_crew\|crypto_crew\|investment_discovery_crew\|portfolio_rebalancing_crew\|report_crew" src --include="*.py" \
  | grep -vE "^src/finwiz/crews/(stock|etf|crypto|investment_discovery|portfolio_rebalancing|report)_crew/" \
  | grep -v "^src/finwiz/crew_factory.py"
```

Expected: hits only in `main.py`, `reporting/__init__.py`, `reporting/html_collector.py` and `orchestrators/registry/registry_data_retrieval.py`. Those are handled in Tasks 3, 5 and 8. **If you see any other file, stop and report it** — the inventory missed something and the plan needs correcting before you delete.

- [ ] **Step 2: Delete the directories**

```bash
rm -rf src/finwiz/crews/stock_crew src/finwiz/crews/etf_crew src/finwiz/crews/crypto_crew \
       src/finwiz/crews/investment_discovery_crew src/finwiz/crews/portfolio_rebalancing_crew \
       src/finwiz/crews/report_crew
rm -f tests/validation/stock_crew_validation.py
```

- [ ] **Step 3: Remove the `main.py` exports**

In `src/finwiz/main.py`, delete the import at line 21 and the `"StockCrew"` entry in `__all__` at line 39, plus any sibling crew imports and `__all__` entries. Keep `DeepAnalysisCrew` if present.

- [ ] **Step 4: Delete the tests whose only subject was those crews**

```bash
ls tests/unit/crews/
```

Delete every test file whose subject is one of the six deleted crews. Keep anything testing `deep_analysis` or `crews/helpers`. List every file you delete in your report.

- [ ] **Step 5: Run both suites**

```bash
uv run pytest -q 2>&1 | tail -3
```

Expected: green, **or** failures only in `tests/unit/test_crew_factory.py` and `tests/unit/crews/test_crew_output_parsing.py`, which import the deleted crews through `CrewFactory`. Those go in Task 3 — do not patch them here, and do not delete `crew_factory.py` here either. If the only failures are those two files, that is the expected state; say so in your report and proceed.

- [ ] **Step 6: Commit**

```bash
git add -u src/finwiz/crews src/finwiz/main.py tests
git commit -m "refactor: delete the six crews nothing calls"
```

---

## Task 3: Delete CrewFactory and its injection wiring

**Files:**
- Delete: `src/finwiz/crew_factory.py`, `tests/unit/test_crew_factory.py`, `tests/unit/crews/test_crew_output_parsing.py`
- Modify: `src/finwiz/flows/orchestrator.py`, `src/finwiz/flows/orchestrator_registry.py`, `src/finwiz/orchestrators/deep_analysis_orchestrator.py`, `src/finwiz/orchestrators/alternatives_matching_orchestrator.py`, `src/finwiz/orchestrators/error_handling_orchestrator.py`

**Interfaces:**
- Consumes: Task 2's deleted crews.
- Produces: three orchestrators whose constructors no longer accept `crew_factory`.

`CrewFactory` is constructed once and never invoked. It is threaded through dependency injection to three orchestrators, one of which forwards it to a fourth. No `crew_factory.<method>(` call exists anywhere.

- [ ] **Step 1: Re-confirm it is never invoked**

```bash
grep -rnE "crew_factory\.[a-z_]+\(" src --include="*.py" | grep -v "^src/finwiz/crew_factory.py"
```

Expected: **no output**. If there is any output, stop and report — the premise of this task is false.

- [ ] **Step 2: Delete the module and its tests**

```bash
rm -f src/finwiz/crew_factory.py tests/unit/test_crew_factory.py tests/unit/crews/test_crew_output_parsing.py
```

Check `tests/unit/crews/test_crew_output_parsing.py` before deleting: if it also covers `deep_analysis` output parsing, keep the file and delete only the crew-factory tests inside it. Say which you did.

- [ ] **Step 3: Remove the construction site**

In `src/finwiz/flows/orchestrator.py`, delete the `CrewFactory` import and lines 107-108:

```python
        # Initialize crew factory
        crew_factory = CrewFactory(integration_manager, error_handler)
        logger.info("Crew factory initialized")
```

Then remove `crew_factory` from wherever that local is passed into the dependency dict.

- [ ] **Step 4: Remove it from the registry's dependency keys**

In `src/finwiz/flows/orchestrator_registry.py`, remove `"crew_factory"` from the `deps_keys` tuples at lines 30, 45 and 50, leaving the other keys untouched.

- [ ] **Step 5: Remove it from the orchestrators**

- `deep_analysis_orchestrator.py:162` — delete `self.crew_factory = dependencies.get("crew_factory")`.
- `deep_analysis_orchestrator.py:597` — delete the `crew_factory=self.crew_factory,` argument.
- `alternatives_matching_orchestrator.py` — delete the `crew_factory` constructor parameter and any assignment of it.
- `error_handling_orchestrator.py:25` — remove `crew_factory` from the docstring's dependency list.

- [ ] **Step 6: Run both suites**

```bash
uv run pytest -q 2>&1 | tail -3
uv run pytest -m integration -q 2>&1 | tail -3
```

Expected: both green, integration back to `51 passed, 1 skipped` minus any test of a deleted crew. Fix any remaining failure that names `crew_factory` before committing.

- [ ] **Step 7: Commit**

```bash
git add -u src/finwiz tests
git commit -m "refactor: delete CrewFactory, constructed at startup and never invoked"
```

---

## Task 4: Delete the zero-importer reporting modules

**Files:**
- Delete: `src/finwiz/reporting/consolidator.py`, `src/finwiz/reporting/export_loaders.py`, `src/finwiz/reporting/html_collector.py`, `src/finwiz/reporting/final_report_generator.py`
- Delete: the tests whose only subject is those modules

**Interfaces:**
- Produces: a `reporting/` package with no crew-export consolidation path.

`consolidator.py` and `export_loaders.py` have zero importers anywhere in `src/` or `tests/`. `html_collector.py` is imported only by `consolidator.py`; `final_report_generator.py` only by its own test. They fall as a group.

- [ ] **Step 1: Re-confirm the importer counts**

```bash
for m in consolidator export_loaders html_collector final_report_generator; do
  echo -n "$m: "
  grep -rn "reporting.$m\|from .$m" src tests --include="*.py" | grep -v "^src/finwiz/reporting/$m.py" | wc -l
done
```

Expected: `consolidator: 0`, `export_loaders: 0`, `html_collector: 1` (from `consolidator.py`), `final_report_generator: 1` (its test). Any other number means a live consumer appeared — **stop and report**.

- [ ] **Step 2: Delete the modules**

```bash
rm -f src/finwiz/reporting/consolidator.py src/finwiz/reporting/export_loaders.py \
      src/finwiz/reporting/html_collector.py src/finwiz/reporting/final_report_generator.py
```

- [ ] **Step 3: Delete their tests**

```bash
grep -rln "consolidator\|export_loaders\|html_collector\|final_report_generator" tests --include="*.py"
```

Delete every file listed whose only subject is one of the four. For a file that also tests something surviving, delete only the relevant classes. List what you did.

- [ ] **Step 4: Remove any re-exports**

```bash
grep -n "consolidator\|export_loaders\|html_collector\|final_report_generator" src/finwiz/reporting/__init__.py
```

Delete the matching import and `__all__` lines.

- [ ] **Step 5: Run the suite**

```bash
uv run pytest -q 2>&1 | tail -3
```

Expected: green.

- [ ] **Step 6: Commit**

```bash
git add -u src/finwiz/reporting tests
git commit -m "refactor: delete the reporting modules nothing imports"
```

---

## Task 5: Delete the per-crew report generators and their registry

**Files:**
- Delete: `src/finwiz/reporting/{stock,etf,crypto,rebalancing,discovery}_report_generator.py`
- Modify: `src/finwiz/reporting/__init__.py`, `src/finwiz/orchestrators/reporting/crew_html.py`, `src/finwiz/orchestrators/reporting_orchestrator.py`

**Interfaces:**
- Consumes: Task 4's deletions.
- Produces: `crew_html.py` retaining only `generate_enriched_html_reports`.

This is the spec's **risk 2**, and the answer is established: `generate_all_crew_html_reports` *is* called from live code (`reporting_orchestrator.py:165`), but it never executed in a real run — the 2026-09-06 run logged zero occurrences of `No HTML generator registered` or `Generated HTML report:`, because `crew_export_paths` is always empty. The 64 real reports come from `generate_enriched_html_reports`, which uses `EnrichedAnalysisReportGenerator` directly and never touches the registry.

- [ ] **Step 1: Prove the live path does not use the registry**

```bash
grep -n "EnrichedAnalysisReportGenerator\|get_generator_for_crew" src/finwiz/orchestrators/reporting/crew_html.py
```

Expected: `EnrichedAnalysisReportGenerator` inside `generate_enriched_html_reports` (about line 215), `get_generator_for_crew` inside `generate_crew_html_report` (about line 135). Two separate paths. **If they share a path, stop and report** — the deletion would then take a live generator with it.

- [ ] **Step 2: Delete the five generators**

```bash
rm -f src/finwiz/reporting/stock_report_generator.py src/finwiz/reporting/etf_report_generator.py \
      src/finwiz/reporting/crypto_report_generator.py src/finwiz/reporting/rebalancing_report_generator.py \
      src/finwiz/reporting/discovery_report_generator.py
```

Keep `base_report_generator.py`, `deep_analysis_report_generator.py`, `enriched_analysis_report_generator.py`, `individual_report_generator.py`, `python_report_generator.py`, `section_generators.py`, `css_styles.py`, `markdown_fragment.py`, `html_auto_generator.py`.

- [ ] **Step 3: Delete the registry**

In `src/finwiz/reporting/__init__.py`, delete the five generator imports, the `CREW_GENERATORS` dict, and the `get_generator_for_crew` function, plus their `__all__` entries.

- [ ] **Step 4: Delete the crew-export half of `crew_html.py`**

Delete these five methods: `generate_html_from_export`, `store_crew_export_paths`, `get_crew_export_path`, `generate_crew_html_report`, `generate_all_crew_html_reports`. Keep `_iter_enriched_files` and `generate_enriched_html_reports`. Remove the now-unused `get_generator_for_crew` import.

- [ ] **Step 5: Delete the call site**

In `src/finwiz/orchestrators/reporting_orchestrator.py`, delete line 165's `html_reports = self.generate_all_crew_html_reports(crew_export_paths)` and whatever builds `crew_export_paths` for it. Keep line 89's `generate_enriched_html_reports()` call — that is the live one.

- [ ] **Step 6: Delete their tests**

```bash
rm -f tests/unit/reporting/test_crew_report_generators.py
grep -rln "generate_all_crew_html_reports\|get_generator_for_crew\|CREW_GENERATORS" tests --include="*.py"
```

Delete or trim every file listed. List what you did.

- [ ] **Step 7: Run both suites**

```bash
uv run pytest -q 2>&1 | tail -3
uv run pytest -m integration -q 2>&1 | tail -3
```

Expected: both green.

- [ ] **Step 8: Commit**

```bash
git add -u src/finwiz tests
git commit -m "refactor: delete the per-crew report generators and their registry"
```

---

## Task 6: Trim the export schemas

**Files:**
- Modify: `src/finwiz/schemas/crew_exports.py`

**Interfaces:**
- Consumes: Tasks 4 and 5.
- Produces: `crew_exports.py` exporting `CrewExportBase` and `DeepAnalysisCrewExport` only, plus whatever `ConsolidatedReportExport` still needs.

This is the spec's **risk 1**. `DeepAnalysisCrewExport` inherits `CrewExportBase`, so the base survives. `ConsolidatedReportExport` must be checked field by field rather than assumed dead.

- [ ] **Step 1: Establish who still consumes each class**

```bash
for c in StockCrewExport ETFCrewExport CryptoCrewExport DiscoveryCrewExport RebalancingCrewExport DiscoveryOpportunity ConsolidatedReportExport CrewExportBase DeepAnalysisCrewExport; do
  echo -n "  $c: "
  grep -rn "$c" src tests --include="*.py" | grep -v "^src/finwiz/schemas/crew_exports.py" | wc -l
done
```

Record every count in your report. A class at 0 is deletable. **`ConsolidatedReportExport` is the one to think about**: if it is above 0, read each consumer and decide whether it survives with the crew fields removed, or goes entirely. Do not guess — quote the consumer in your report.

- [ ] **Step 2: Delete the dead classes**

Delete `StockCrewExport`, `ETFCrewExport`, `CryptoCrewExport`, `DiscoveryCrewExport`, `RebalancingCrewExport`, and `DiscoveryOpportunity` if its count is 0. Keep `CrewExportBase` and `DeepAnalysisCrewExport`.

- [ ] **Step 3: Resolve `ConsolidatedReportExport` per Step 1**

If it has no consumer, delete it. If it has consumers, delete only the fields typed by the classes removed in Step 2, and state in your report which fields you removed and which consumer you checked.

- [ ] **Step 4: Verify the surviving model still builds**

```bash
uv run python -c "
from finwiz.schemas.crew_exports import CrewExportBase, DeepAnalysisCrewExport
print('fields:', sorted(DeepAnalysisCrewExport.model_fields))
"
```

Expected: prints the field list without raising.

- [ ] **Step 5: Run the suite**

```bash
uv run pytest -q 2>&1 | tail -3
```

Expected: green.

- [ ] **Step 6: Commit**

```bash
git add -u src/finwiz/schemas tests
git commit -m "refactor: keep only the export schemas that still have a producer"
```

---

## Task 7: Delete the crew state fields and their readers

**Files:**
- Modify: `src/finwiz/flow_state_models.py:130-148`, `src/finwiz/flow_state_utils.py:51-53,64-74`, `src/finwiz/orchestrators/validation_orchestrator.py:275-276,394-396`

**Interfaces:**
- Produces: a `FinwizState` with no `{stock,etf,crypto}_analysis_*` field.

Fifteen fields — five each for stock, ETF and crypto. Nothing has written them since the executors lost their callers, so every reader has been reading defaults.

The spec records the decision explicitly: these are **deleted, not kept as no-op fields**. The standing *"remove the switch, not the surface"* rule covers kill switches, where the gate goes and the field stays for caller stability. These are not a switch — they are the recorded state of a subsystem that will not exist, and `validation_orchestrator` branches on them today.

- [ ] **Step 1: List every reader**

```bash
grep -rn "stock_analysis_\|etf_analysis_\|crypto_analysis_" src tests --include="*.py"
```

Record the full list. Expected in `src/`: `flow_state_models.py`, `flow_state_utils.py`, `validation_orchestrator.py`. Any other file means an unmapped reader — **stop and report**. `deep_analysis_*` fields are a different set and must not be touched.

- [ ] **Step 2: Delete the fields**

Delete lines 130-148 of `src/finwiz/flow_state_models.py` — the fifteen fields and their section comments. Do **not** touch `deep_analysis_results`, `deep_analysis_success` or `deep_analysis_error` at lines 211-214.

- [ ] **Step 3: Delete the readers in `flow_state_utils.py`**

Lines 51-53 compute `stock_available` / `etf_available` / `crypto_available`; lines 64-74 branch on the `_error` and `_disabled` fields. Delete them and simplify whatever consumed those locals. If a function becomes empty or always returns the same value, delete the function and its call sites too, and say so.

- [ ] **Step 4: Delete the readers in `validation_orchestrator.py`**

Lines 275-276 build `failed_crews` and `disabled_crews` from `["stock", "etf", "crypto"]`; lines 394-396 read `_success`, `_fallback` and `_result` via `getattr`. Delete both, and whatever they fed.

- [ ] **Step 5: Verify the state model still constructs**

```bash
uv run python -c "
from finwiz.flow_state_models import FinwizState
s = FinwizState()
leftover = [f for f in FinwizState.model_fields if f.startswith(('stock_analysis','etf_analysis','crypto_analysis'))]
assert not leftover, leftover
print('clean; deep_analysis_success still present:', 'deep_analysis_success' in FinwizState.model_fields)
"
```

Expected: `clean; deep_analysis_success still present: True`.

- [ ] **Step 6: Run both suites**

```bash
uv run pytest -q 2>&1 | tail -3
uv run pytest -m integration -q 2>&1 | tail -3
```

Expected: both green. Tests asserting the deleted fields must be deleted, not rewritten to assert `None`.

- [ ] **Step 7: Commit**

```bash
git add -u src/finwiz tests
git commit -m "refactor: delete the crew analysis state fields and their readers"
```

---

## Task 8: Delete the feature flags and the crew-data queries

**Files:**
- Modify: `src/finwiz/config/features/definitions.py:157-176`, `src/finwiz/orchestrators/registry/registry_data_retrieval.py`, `src/finwiz/integration/cache.py`

**Interfaces:**
- Produces: no `stock_analysis` / `etf_analysis` / `crypto_analysis` flag, and no query that consolidates crew data for those three names.

This is the spec's **risk 3**. `registry_data_retrieval.py:173` logged `Consolidated <asset> crew data: 0 ticker analyses, avg score: 0.000` three times in a real run, and `cache.py:98` logged `Consolidated data from 5 crews`. These are live calls querying producers that no longer exist. The producers are already gone by this task; the queries must follow, or the deletion trades a dead subsystem for a live one searching for nothing.

- [ ] **Step 1: Delete the three flags**

In `src/finwiz/config/features/definitions.py`, delete the `stock_analysis`, `etf_analysis` and `crypto_analysis` `FeatureFlagConfig` blocks (about lines 157-176). Leave `portfolio_rebalancing` and `investment_discovery` alone for now — Step 3 decides them.

```bash
grep -rn "stock_analysis\|etf_analysis\|crypto_analysis" src tests --include="*.py"
```

Delete every remaining reference. Also remove the `FF_STOCK_ANALYSIS` / `FF_ETF_ANALYSIS` / `FF_CRYPTO_ANALYSIS` lines from `.env.example` if present — **never read or print `.env` itself**, only `.env.example`, and only variable names.

- [ ] **Step 2: Decide the crew-data queries**

```bash
grep -rn "crew_name" src/finwiz/orchestrators/registry/registry_data_retrieval.py | head -20
grep -rn "crew_name\|for crew" src/finwiz/integration/cache.py | head -20
```

Both are **generic** helpers keyed by crew name, not stock/ETF/crypto-specific. So the question is not "delete the function" but "who still calls it, and with which names?" Find the callers:

```bash
grep -rn "consolidate_crew_data\|get_.*crew_data" src --include="*.py" | grep -v "def "
```

If every remaining caller passes only deleted crew names, delete the caller and then the helper. If any caller passes `deep_analysis`, keep the helper and delete only the dead names from the list it iterates. **Quote the caller list in your report** — this is the step most likely to be got wrong by assumption.

- [ ] **Step 3: Resolve the two remaining flags**

`portfolio_rebalancing` and `investment_discovery` gated executors deleted in Task 3. Check whether anything else reads them:

```bash
grep -rn "portfolio_rebalancing\"\|investment_discovery\"" src --include="*.py" | grep -v definitions.py
```

If nothing does, delete both flags too. If something does, keep them and say what. Note that `CLAUDE.md` already records that Investment Discovery runs unconditionally and its kill switch was removed — so a surviving flag there would be worth flagging as a contradiction rather than silently keeping.

- [ ] **Step 4: Verify no flag lookup fails**

```bash
uv run python -c "
from finwiz.config.features.flags import is_feature_enabled
for f in ('perplexity_research','quantitative_analysis'):
    print(f, is_feature_enabled(f))
"
```

Expected: prints both without raising. A `KeyError` means you deleted a flag something still reads.

- [ ] **Step 5: Run both suites**

```bash
uv run pytest -q 2>&1 | tail -3
uv run pytest -m integration -q 2>&1 | tail -3
```

Expected: both green.

- [ ] **Step 6: Commit**

```bash
git add -u src/finwiz tests .env.example
git commit -m "refactor: delete the crew feature flags and the queries with no producer"
```

---

## Task 9: Documentation and live acceptance

**Files:**
- Modify: `CLAUDE.md`, `CHANGELOG.md`, `src/finwiz/analysis/CLAUDE.md` if it mentions the deleted crews

**Interfaces:**
- Consumes: every prior task.
- Produces: the merged branch's PR.

- [ ] **Step 1: Update `CLAUDE.md`**

The Key Components table still has a `Crew factory` row pointing at a deleted module — delete the row. The Crew Pattern section currently explains that only `deep_analysis` runs and lists six inert crews (added by #190); rewrite it to describe only what exists:

```markdown
### Crew Pattern

`deep_analysis` is the only crew. It lives in `crews/deep_analysis/` with
`config/agents.yaml`, `config/tasks.yaml`, and a crew class using `@CrewBase`,
and is reached from `analysis/_helpers.py`. Six other crews existed until
2026-09-07 and were deleted: nothing had called them since Phase 4 discovery
moved to Python scoring.
```

Check the architecture diagram and the Tool factories row for references to the deleted crews and correct them.

- [ ] **Step 2: Update `CHANGELOG.md`**

Add under `## [Unreleased]`:

```markdown
### Removed

- **Six crews that nothing called**, along with `CrewFactory`, the crew-export
  consolidation modules, the per-crew report generators, the crew analysis
  state fields and the feature flags that gated them. Phase 4 discovery moved
  to Python scoring some time ago; the crews were never deleted and had
  rotted — `stock_crew` could no longer even be instantiated. No behaviour
  changes: no `*_export.json` had ever been produced. About 8,000 lines.
```

- [ ] **Step 3: Confirm the source tree matches the spec's "Done when"**

```bash
ls src/finwiz/crews/
test ! -f src/finwiz/crew_factory.py && echo "crew_factory: gone"
grep -rn "crewai" src --include="*.py" | grep -vE "crews/deep_analysis|flows/|tools/|crewai_custom_tools" | head
```

Expected: `crews/` shows only `deep_analysis` and `helpers`; `crew_factory: gone`; the last command prints little or nothing.

- [ ] **Step 4: Run both suites one final time**

```bash
uv run pytest -q 2>&1 | tail -3
uv run pytest -m integration -q 2>&1 | tail -3
```

Expected: both green. Record the numbers against Task 1's baseline; the totals will be lower because deleted tests are gone. State the delta.

- [ ] **Step 5: The acceptance test — a live kickoff**

```bash
PORTFOLIO_STOCK_CSV=/tmp/crew-removal-baseline/mini/stock.csv \
PORTFOLIO_ETF_CSV=/tmp/crew-removal-baseline/mini/etf.csv \
PORTFOLIO_CRYPTO_CSV=/tmp/crew-removal-baseline/mini/crypto.csv \
uv run kickoff
```

- [ ] **Step 6: Compare against the baseline field by field**

```bash
uv run python -c "
import json
before = json.load(open('/tmp/crew-removal-baseline/run_summary.before.json'))
after  = json.load(open('output/run_summary.json'))
print('verdict:', before['verdict'], '->', after['verdict'])
b = {c['name']: (c['passed'], c['observed']) for c in before['checks']}
a = {c['name']: (c['passed'], c['observed']) for c in after['checks']}
assert set(b) == set(a), f'check set changed: {set(b) ^ set(a)}'
for name in b:
    flag = 'same' if b[name] == a[name] else 'CHANGED'
    print(f'  {flag:8} {name:18} {b[name][1][:40]!r} -> {a[name][1][:40]!r}')
"
```

Expected: `verdict: PASS -> PASS`, the same eight check names, and every check still passing. `observed` strings may differ in figures that legitimately vary between runs (durations, candidate counts, cost). A check flipping from passed to failed, or a check name appearing or disappearing, is a **failure of this task** — report it and stop rather than committing.

- [ ] **Step 7: Commit and open the PR**

```bash
git add -u CLAUDE.md CHANGELOG.md src/finwiz/analysis/CLAUDE.md
git commit -m "docs: the crews that no longer exist"
git push -u origin <branch>
gh pr create --title "refactor: remove the uncalled crew subsystem" --body "<summary>"
```

The PR body must carry the before/after verdict comparison from Step 6, both suite deltas, and the resolution of the spec's three named risks. **Do not merge** — the human merges.

---

## Self-Review

**Spec coverage.** Every item in the spec's "What goes" list maps to a task: crew packages (2), factory (3), consolidator and export_loaders (4), per-crew generators and registry (5), export schemas (6), state fields and validation branches (7), feature flags and the zero-returning queries (8), documentation (9). The spec's three named risks are Tasks 6, 5 and 8 respectively, each with an explicit "quote it in your report, do not assume" step. The spec's eight "Done when" criteria are checked in Task 9 Steps 3, 4 and 6.

**Placeholder scan.** No "TBD" or "handle edge cases". The three genuinely conditional steps — `ConsolidatedReportExport` in Task 6, the query callers in Task 8 Step 2, and the two remaining flags in Task 8 Step 3 — each state both branches and what to record, rather than deferring the decision.

**Type consistency.** `CrewExportBase` and `DeepAnalysisCrewExport` are named identically in Tasks 6 and 9. `generate_enriched_html_reports` is the survivor in Task 5 and is not touched later. The `{stock,etf,crypto}_analysis_*` prefix set in Task 7 is disjoint from the `deep_analysis_*` set, and Step 5 asserts exactly that.

**One deliberate gap.** Task 2 Step 5 expects two named test files to fail, because deleting the crews breaks them before Task 3 deletes their subject. Making Task 2 green on its own would mean deleting `crew_factory.py` there, which merges two reviewable units. The expected failure is stated so a reviewer does not read it as a defect.
