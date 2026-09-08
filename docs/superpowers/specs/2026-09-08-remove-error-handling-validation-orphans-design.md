# Design: remove the error-handling and validation orphans

**Issue:** [#200](https://github.com/fjacquet/finwiz/issues/200) (tier 1)
**Date:** 2026-09-08
**Status:** approved

## Problem

Two clusters of modules cannot be reached from any entry point: five helpers under
`orchestrators/error_handling/` and a ten-module subtree under `validation/` held up
by two dead root modules in `integration/`. Seventeen files, 5,060 lines, plus 4,482
lines of tests that exercise nothing else.

Nothing is broken. Every one of these passes `make check` today, several with high
test coverage, because `vulture` at confidence 80 reports unused symbols *within* a
file and has no notion of an unreachable module.

## Method

A read-only trace built an AST import graph over all 435 modules under `src/` and ran
reachability from the real entry points — `finwiz.main` plus the two dynamic
registries (`flows/orchestrator_registry.py:26-71`, `orchestrators/__init__.py:10-31`),
which are the only dynamic reach in `src/`. That produced the candidate list.

Reachability alone is **not** the justification. Each module was then traced through
`git log -S'<symbol>'` to the commit that removed its last reader, and that commit was
read to establish what it was for. #187 twice concluded a symbol was dead from a grep
that returned nothing; one of those deleted live aggregation that had to be restored.
Full findings: `.superpowers/sdd/trace-200-findings.md`.

### What the issue gets wrong

1. **The stated import chain is inaccurate.** #200 describes
   `int_pipeline → pipeline_stages → rules, report, sec_citation` as one chain.
   `pipeline_stages.py:18-21` imports `.rules` and `.sec_citation` but **not**
   `.report`. The real shape is one two-step chain plus **five standalone orphans**
   (`report.py`, `report_data.py`, `consolidation.py`, `freshness.py`,
   `tool_restrictions.py`), each reachable from nothing and never part of the chain.
   No deletion verdict changes; the commit messages must describe the real shape.
2. **The count is 17 files, not 15.** `integration/cli.py` and
   `integration/middleware.py` are the roots holding the validation subtree up. Both
   have zero importers of their own and no purpose without the subtree, so they go too
   — 494 additional lines.
3. **Test coverage is not uniform.** #200 says these clusters "sit at 72-92% coverage".
   Eight of the seventeen files have **zero** tests: `fallback.py`, `recovery.py`,
   `validation_recovery.py`, `report_data.py`, `int_pipeline.py`,
   `pipeline_stages.py`, `cli.py`, `middleware.py`.

A grep trap worth naming: searching for `validation.report` false-matches
`from .report import ReporterInput` in `schemas/__init__.py:132` and
`schemas/validate.py:11`. That `.report` is `schemas/report.py`, a live and unrelated
file.

## Decision

Delete all seventeen, their tests, and the residue they leave.

### Cluster A — error-handling helpers (5 files, 1,480 lines)

`orchestrators/error_handling/{fallback,handlers,missing_data,recovery,validation_recovery}.py`

`error_handling_orchestrator.py:8-13` imports only `flow_state` and the logger. The
package's one live member is `core_analysis_error_handler`, imported at
`flows/orchestrator.py:25`. The five reference only each other: `fallback.py:14` →
`recovery`, `recovery.py:18` → `handlers`, `validation_recovery.py:15` → `.fallback`.
`__init__.py` is 0 bytes, so there is nothing to unwire.

**All five were born dead** — a stronger finding than the issue assumed, because it
means there is no lost behaviour to consider restoring. `fallback`, `handlers` and
`recovery` came from `integration/` and `git log -S` on each class returns only the
rename (`ebf3d6bc`) and one lint commit; at that rename's parent they still referenced
only each other. `missing_data` and `validation_recovery` were added whole in
`e015648d` with tests and never wired in. `error_handling_orchestrator.py` itself,
created in `08588664`, never referenced any of them in its first version — the
intended integration never happened at all.

Tests: `tests/unit/integration/test_error_handlers.py` (43) and
`tests/unit/utils/test_missing_data_handler.py` (17). The other three files have none.

### Cluster B — the validation subtree (12 files, 3,580 lines)

Ten modules — `validation/{rules,report,report_data,consolidation,freshness,int_pipeline,pipeline_stages,scripts,sec_citation,tool_restrictions}.py`
— plus the two roots, `integration/cli.py` and `integration/middleware.py`.

`validation/__init__.py` re-exports only live modules (`contract`, `enums`, `manager`,
`registry`, `result`, `template`). **None of the ten appears in its `__all__`**, so
this is not the situation that kept `cost_analyzer` alive in #195, where a public
re-export made deletion an API change rather than a dead-code removal.

Ten modules in the same package stay: `ai_output`, `contract`, `enums`, `int_manager`,
`manager`, `quality_metrics`, `registry`, `result`, `template`, `url`. This is surgery
inside a live package, not the removal of a self-contained directory.

Both roots are dead: `integration/cli.py` has no `[project.scripts]` entry (only
`kickoff`, `run_crew`, `plot` exist) and no importer anywhere;
`integration/middleware.py`'s sole class `CrewIntegrationMiddleware` has never had an
importer outside its own file in the entire history.

Three of the ten were once live, and each lost its caller in an identifiable commit:

- **`freshness.py`** — the cleanest case. `249cab36` ("Wave-3 noise purge and debt
  sweep") deleted `integration/freshness_validated_tool.py`, which wrapped
  `DataFreshnessValidator`, as a verified dead-code purge and said so in its own commit
  message. Intentional, documented, already-settled precedent.
- **`report_data.py`** and **`consolidation.py`** — these were **silently dropped**, not
  retired. `4600d1a7` (the November 2025 monolith decomposition) shows
  `ReportDataValidator().validate_report_inputs(state_dict)` and
  `DataConsolidationValidator(registry_manager)` running in the old
  `flow_orchestrator.py`; the successor orchestrators created in that same commit
  reference neither. Two validation steps stopped running and nobody noticed for ten
  months. **This is filed separately as [#202](https://github.com/fjacquet/finwiz/issues/202)** —
  whether those checks should return is a question about today's pipeline, not about
  this dead code, and deleting the orphans does not decide it. Note the same commit is
  where `generate_final_report` was born dead (#195); it dropped at least three things.

`tool_restrictions.py` was raised from medium-high to **high** confidence by a focused
second pass, on three grounds. Its two classes have never had a production importer in
any commit. The live `ValidationOrchestrator.pre_validate_reporter_input()`
(`validation_orchestrator.py:135`, called at `flows/orchestrator.py:284`) shares the
words but reimplements the behaviour — it imports nothing from `tool_restrictions`.
And decisively, **its subject no longer exists**: the module's docstring says it
enforces "that the final reporter crew has no external tools", and its
`RESTRICTED_AGENTS` dict holds exactly one entry, `investment_reporter` — an agent on
the `report_crew` that #187 deleted. It guards an architectural rule about a component
that is gone.

Tests: seven files, 226 tests. `report_data`, `int_pipeline`, `pipeline_stages` and
both roots have none.

### Residue

Five `pyproject.toml` per-file-ignores rows whose files this branch deletes — `:193`
(`integration/cli.py`), `:197` (`error_handling/recovery.py`), `:220`
(`validation/consolidation.py`), `:222` (`validation/scripts.py`), `:223`
(`validation/sec_citation.py`). Rows `:221` (`quality_metrics.py`) and `:224`
(`url.py`) are for live modules and **stay**.

Ruff drops unmatched rows silently, so a green `make lint` is no evidence a row is
live. That block accumulated residue across at least four separate cleanups
before #195 emptied it; it must not start refilling.

### Documentation

`orchestrators/CLAUDE.md:17,43-49,84`, `validation/CLAUDE.md` (its directory tree names
all ten candidates and its entry-points table several), `integration/CLAUDE.md:18,22,33,35`
(documents `middleware.py` and `cli.py` as live), and
`docs/explanations/DATA_QUALITY_AND_FLOW_GUIDE.md:145,169`, which shows example code
importing `DataConsolidationValidator` and `ReportDataValidator` as current guidance.
That last one is actively misleading and the examples go rather than get annotated.

`docs/superpowers/plans/2026-06-10-simplification-pass3-decompose.md:430-431` records a
historical rename of two of these modules. It is a history document, true when written,
and stays untouched — the same rule that governs released CHANGELOG entries.

## Testing

- `make check` must not move from its current state. Its docs-lint step already fails
  on `main` on three `docs/superpowers/` files this branch does not touch; adding no
  new violation is the bar.
- `make test` green, with the drop accounted for exactly: count `def test_` per deleted
  test file and show the arithmetic. Expect roughly 286 fewer.
- `make coverage` ≥ 65%. Deleting well-covered dead code moves the ratio; report the
  real number rather than predicting it.
- `make deadcode` (vulture) must not newly report something the deletions expose.
- `uv run plot` exits 0.
- **A pipeline run.** Cluster B is surgery inside a live package, and
  `validation_orchestrator` runs in Phases 1, 2 and 6. The run is what proves the live
  validation path is untouched.

## Risk

Lower than #195's, because nothing here is surgery inside a live *file* — every
deletion is a whole file, and the two clusters have no relationship to each other.

The risk that remains is misidentification, and it has one shape: **a live module in
the same package as a dead one.** `validation/` keeps ten modules and loses ten. The
mitigations are that `validation/__init__.py` was read in full and re-exports none of
the ten, and that each of the ten was traced individually rather than by directory.

The one lesson this branch adds to the previous three: **do not take a subagent's
completion claim over the artifact.** The trace reported writing a second-pass section
that it had not written; the file was unchanged. Verify the file, not the report.
