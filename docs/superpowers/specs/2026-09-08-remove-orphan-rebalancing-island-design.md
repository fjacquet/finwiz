# Design: remove the orphan rebalancing island and its neighbours

**Issue:** [#195](https://github.com/fjacquet/finwiz/issues/195)
**Date:** 2026-09-08
**Status:** approved

## Problem

Four unrelated things were left behind by #187 and earlier passes: a closed
island of quantitative rebalancing code that nothing reaches, an orchestrator
method that never had a caller, six operator-facing labels naming crews that no
longer exist, and a reporting phase that renders 64 HTML files a second time and
throws them away. A fifth group — residue found while reviewing #194 — is folded
in because it is the same species and would otherwise need its own branch.

None is a correctness defect. Every one of them passes `make check` today.

## Method

A read-only trace built an AST import graph over all 435 modules under `src/` and
ran reachability from the real entry points: `finwiz.main` plus the nine modules
named in the string-keyed registry at `flows/orchestrator_registry.py:26-71`
(`importlib.import_module` dispatch) and the parallel `__getattr__` registry at
`orchestrators/__init__.py:10-31`. Those two registries are the only dynamic reach
in `src/`. Result: 357 modules reached, 78 unreached.

Every claim below was then checked a second way — `git log -S'<symbol>'` to find
the commit that removed each symbol's last reader, and to read what that commit
was for. The full findings are at `.superpowers/sdd/trace-195-findings.md`.

**Module-level unreachability is necessary but not sufficient.** #187 twice
concluded a symbol was dead from a grep that returned nothing, and one of those
conclusions deleted live aggregation that had to be restored. Nothing in this
spec rests on reachability alone.

### Six things the issue gets wrong

Recorded because a reader who trusts the issue text over this spec will make
worse decisions, not better ones.

1. **The stated risk in Q3 is inverted.** The issue withholds the label rename
   because `validation/flow.py`'s `CrewDataContract` registry might share a
   namespace with the tracker labels. It cannot: `validation/flow.py` has exactly
   one importer in the repository, its own test. The dictionary is never
   constructed at runtime. There is no coupling to break.
2. **`integration/validation.py:62` does not consume those labels.** Its
   `crew_name` comes from `freshness_report.missing_data`, which enumerates the
   hardcoded directory names `["stock", "etf", "crypto", "discovery", "portfolio"]`
   at `orchestrators/registry/registry_data_retrieval.py:57` — so the string it
   would render is "Run **stock** crew", not `stock_crew`. It also never executes:
   both accessor entry points (`integration/accessor.py:81,94`) are uncalled. Two
   separate stale-naming problems, not one.
3. **`OptimizationFailedError` is dead too.** #187's commit message correctly
   distinguished it from a same-named class in the orchestrator, but left the
   impression the survivor was live. `exceptions/orchestrator.py` is dead in full.
4. **The `portfolio_monitor` half of the island was not orphaned by #187.** Its
   last reader was `examples/portfolio_monitoring_demo.py`, deleted in `462d5f8b`
   (PR #64, 2026-06-10). Three months earlier, different cause. It was never wired
   into the flow at all.
5. **The island has eleven members, not seven** — see below.
6. **`generate_final_report` never had a caller to remove.** Born dead at
   `4600d1a7`.

## Decision

Five deletions and one rename, in one branch. Each is independently verifiable;
none depends on another's outcome.

### 1. The quantitative rebalancing island

Eleven modules, 2,782 lines, 1,199 statements. The issue estimated ~630
statements across seven modules; the measured figure for those same seven is 696,
and three more modules belong to the same closed set.

| Module | Lines | Statements | Only importers |
|---|---|---|---|
| `quantitative/rebalancing_engine.py` | 29 | 5 | `monitoring_engine.py:15`, `portfolio_monitor.py:25` |
| `quantitative/execution_engine.py` | 207 | 53 | `rebalancing_engine.py:10` |
| `quantitative/trade_generation.py` | 154 | 61 | `execution_engine.py:20` |
| `quantitative/trade_recommendation_system.py` | 474 | 218 | `execution_engine.py:21` |
| `quantitative/portfolio_monitor.py` | 355 | 169 | own test only |
| `quantitative/monitoring_engine.py` | 136 | 74 | `portfolio_monitor.py:23` |
| `quantitative/monitoring_alerts.py` | 259 | 116 | `portfolio_monitor.py:17` |
| `quantitative/optimization_algorithms.py` | 507 | 239 | `execution_engine.py:13`, `rebalancing_engine.py:11` |
| `quantitative/portfolio_analyzer.py` | 525 | 219 | `monitoring_engine.py:14`, `portfolio_monitor.py:24` |
| `quantitative/scenario_analyzer.py` | 90 | 28 | own test only |
| `exceptions/orchestrator.py` | 46 | 17 | `exceptions/__init__.py:14-16` re-export only |
| **Total** | **2,782** | **1,199** | |

Nothing outside the set reaches in. The only non-island references anywhere are
the five test files that die with them (2,687 lines) and documentation.

`rebalancing_engine.py` is not an implementation — it is an 803-byte
back-compatibility shim re-exporting `RebalancingEngine` from `execution_engine`
and five names from `optimization_algorithms`. Worth knowing before someone reads
its 29 lines and concludes the island is small.

`exceptions/__init__.py` loses its three re-exports (`:14-16`, `:25-27`).

**Boundary case, decided:** `quantitative/cost_analyzer.py` **stays**. Deleting
the island orphans it — its only `src/` importer is
`trade_recommendation_system.py:13` — but it is re-exported from
`quantitative/__init__.py:29-38` and named in `__all__` alongside six of its
types. That makes it importable-but-unimported, not unreachable. Removing a
public re-export is an API change, a different decision from removing dead code,
and it is not this issue's decision to make.

**`schemas/portfolio_rebalancing.py` stays.** It is imported by 17 modules
including live ones (`tools/portfolio_price_service.py:20`, `schemas/__init__.py:90`).
The name is the only thing it shares with the island.

### 2. `ReportingOrchestrator.generate_final_report()`

`reporting_orchestrator.py:119-149`, plus `_extract_portfolio_review` and
`_extract_deep_analysis` (`orchestrators/reporting/data_loading.py:247-275`),
which are exclusive to it.

The issue deferred this because the method "reads keys whose producer needs
tracing first". Traced: the only consolidated payload live code produces is
`CrewDataAccessor.get_consolidated_reporter_input()`, whose sole live caller is
`validation_orchestrator.py:248` — feeding portfolio review, never this method.
The `"portfolio_review"` key is written to flow state at
`validation_orchestrator.py:118` and read by the live path through
`_get_portfolio_review_from_state()`, not through here.

**The trap:** the other helpers in `data_loading.py` are shared with the live
report route (`generate_python_report()` at `reporting_orchestrator.py:60-107`
calls `_get_portfolio_review_from_state` → `_convert_to_portfolio_review` →
`_read_deep_analysis_from_files` → `_merge_deep_analysis_into_portfolio` →
`_save_merged_portfolio_review` → `_generate_python_report`). Only the two
`_extract_*` wrappers die. This is surgery inside a live file, unlike everything
else in this spec.

### 3. The `*_crew` labels

Six string literals in one file — `discovery_orchestrator.py:87,114,166,193,245,268`
— renamed:

| Old | New |
|---|---|
| `"crypto_crew"` | `"crypto_discovery"` |
| `"stock_crew"` | `"stock_discovery"` |
| `"etf_crew"` | `"etf_discovery"` |

The new names match what the code already calls these paths: each site wraps a
pure-Python Phase 4 discovery scanner, saved via `_save_discovery_results("stock", …)`,
and the surrounding comment already reads "Track actual Python execution outcome".
No crew is involved and none has existed since #187.

What the rename touches, in full: one write-only in-memory dict.
`DataAvailabilityTracker` (`integration/availability.py`) stores each label in
`self._tracked_sources` and exposes seven read methods —
`get_availability_summary`, `get_freshness_warnings`, `get_source_status`,
`is_source_available`, `is_source_stale`, `get_tracked_source_names`,
`format_summary_for_report` — **every one of which has zero callers outside the
class**. Nothing persists: a grep for these labels across both the current and
previous runs' `output/` trees returns no matches, so no cache key, no on-disk
JSON, no `run_summary`, and no reading of old data is affected.

Two further items travel with this, independent of each other and of the rename:

- **`validation/flow.py` and its test are deleted.** This is the module the issue
  named as the reason not to touch the labels. Proving it dead is what makes the
  rename safe; leaving it in place would mean acting on the conclusion while
  preserving the hazard it was drawn from. Its only importer is
  `tests/unit/validation/test_data_flow_validator.py` (546 lines), which goes with
  it. The other ten modules of the `validation/` subtree the trace flagged are
  **out of scope** — they need their own `git log -S` pass.
- **`integration/validation.py:54-79`'s advice text is rewritten** to stop telling
  an operator to "run the stock crew". The path is dead, so this is wording, not
  behavior; the fix is cheap and the string is wrong either way.

### 4. The duplicate render

Delete the reporting-phase pass: `generate_enriched_html_reports`,
`orchestrators/reporting/enriched_html.py` (`EnrichedHtmlMixin`), and its call
site at `reporting_orchestrator.py:85-89`. **Keep** the analysis-time render in
`deep_analysis_orchestrator.py:388-391`.

Measured on the 2026-09-07 run's real artifacts rather than reasoned from code:
64 `_report.html` files and 64 `_enriched.html` files, and all 64 pairs diff to
exactly two lines — the same one:

```text
<             <p>Rapport généré par FinWiz le 2026-09-07 22:11:41</p>
---
>             <p>Rapport généré par FinWiz le 2026-09-07 22:15:28</p>
```

Same byte count, same 1,172 lines, same content. Both passes use the same
renderer over the same template; one renders from the in-memory model, the other
from the JSON just serialized from that model.

`_report.html` is canonical: it is what `reporting/sections/holdings.py:55` and
`orchestrators/reporting/enrichment.py:276` build the report's per-holding links
from, plus four more references. Nothing anywhere references `_enriched.html`
except the deleted function's own test and one doc example. The reporting phase
is producing 64 orphan files per run and paying a full second render to do it.

**The trap:** `EnrichedHtmlMixin._iter_enriched_files` is a `NotImplementedError`
stub (`enriched_html.py:22-24`). The real `_iter_enriched_files`
(`orchestrators/reporting/enrichment.py:193`) is also used by
`_iter_enriched_records` and **must survive**.

### 5. Residue from #194's review

| Item | Why |
|---|---|
| `bin/regenerate_reports.py` | imports `src.finwiz.tools.html_output_tool`, a path never tracked in this repo's history — the import has always been wrong |
| `bin/debug_config.py` | imports `finwiz.utils.config_loader`; `src/finwiz/utils/` holds only a `CLAUDE.md`. Also appends `bin/src` to `sys.path`, a directory that has never existed |
| `scripts/verify_html_reports.py` + its 187-line test | checks for output artifacts the chain #194 deleted would have produced. PR #64's own plan listed it for deletion and it survived the pass |
| `tools/rebalancing_calculations.py` + its 598-line test | zero `src/` importers; already self-documented as dead at `tools/CLAUDE.md:44` |
| `pyproject.toml` per-file-ignores × 4 | `:164` `tools/etf_crew.py` and `:204` `quantitative/constraint_handlers.py` are already stale; `:207` `portfolio_analyzer.py` and `:209` `trade_recommendation_system.py` become stale the moment this branch's island deletion lands |

`bin/` is left empty and is removed.

### 6. Documentation

`quantitative/CLAUDE.md:26-31,72`, `exceptions/CLAUDE.md:21-22,30-31,36,43,46,59-60`,
`reporting/CLAUDE.md:55,75`, `tools/CLAUDE.md:44`,
`docs/how-to/OPERATIONS_GUIDE.md:1185,1188,1208` (documents `PortfolioMonitor`
usage that will not exist), `docs/tutorials/portfolio_analysis.md:97`, and
`CHANGELOG.md`.

## Verification

**The grep rule, which this trace violated once itself.** A `scripts/` path grep
misses the dotted module form. `make check`'s own stage-contract gate is invoked
as `uv run python -m scripts.check_stage_contract` at `Makefile:165` and looks
unwired to a path grep — the trace briefly concluded it was an unwired gate
contradicting ADR-009 before catching the error. Every deletion sweep in this plan
must grep for **both** `scripts/foo.py` and `scripts.foo`, and must cover `src`,
`tests`, `scripts`, `bin`, `Makefile` recipe bodies, `pyproject.toml`,
`.pre-commit-config.yaml`, `.github/workflows/` and `mkdocs.yml`. #194 lost this
lesson twice; it is written down here so #195 does not lose it a third time.

- `make check` — must not move from its current state. Its docs-lint step fails on
  `main` already, on three files under `docs/superpowers/` that this branch does
  not touch. Adding no new violation is the bar.
- `make test` green, and the test-count drop accounted for exactly: count
  `def test_` in each deleted test file and show the arithmetic.
- `make coverage` ≥ 65%. Deleting well-covered dead code moves the ratio; report
  the real number rather than predicting it.
- `make deadcode` (vulture) — will not catch anything here (it has no notion of an
  unreachable module, which is why this code survived), but must not newly report
  something the deletions expose.
- `uv run plot` exits 0.
- **A pipeline run** — the only proof that matters for items 2 and 4, which touch
  the live reporting path. It must produce its HTML report, and `output/` must
  contain 64 `_report.html` files and **zero** `_enriched.html` files.

## Risk

Items 1, 5 and the `validation/flow.py` half of 3 are whole-file deletion of code
with no importer, verified twice. Low.

Item 3's rename is as safe as a rename gets — six literals feeding a write-only
sink, nothing persisted.

**Items 2 and 4 carry the real risk**, and for the same reason: both are surgery
inside files the live report path uses. Item 2 removes two wrappers from a
`data_loading.py` whose other helpers are load-bearing. Item 4 removes a mixin
whose stub method shares a name with a live one in a sibling module. Both traps
are named above; both are the kind a grep-driven edit walks into. The pipeline run
is what proves them, not the unit suite.
