# Codebase Cleanup — Design Spec

**Branch:** `chore/codebase-cleanup`
**Date:** 2026-06-06

## Context

A graph + grep audit of FinWiz surfaced three classes of cleanup:

- **Tier 1** — 8 functions with zero references in `src/` or `tests/`, not exported in any
  `__init__.py`, not decorators/hooks (~530 lines). High-confidence dead code.
- **Tier 2** — ~223 more graph-flagged unreferenced functions in `src/finwiz/`, false-positive-prone
  (CrewAI decorators, monkeypatches, polymorphic interfaces, CLI/string dispatch, framework callbacks).
- **Tier 3** — god-files exceeding the project's 300-line norm: `reporting/section_generators.py`
  (1146L), `orchestrators/reporting_orchestrator.py` (876L), plus oversized functions.

Goal: remove genuinely dead code and decompose the god-files **without breaking anything**, with an
auditable cross-check trail. User decisions: do **everything (1+2+3)**; Tier 2 removal is
**conservative**; god-file splits use **re-export shims**; **decompose first** then sweep;
**cross-check before cleaning**; work **on a branch**; use **Serena** symbolic tools.

## Approach (decompose-first, cross-checked, Serena-powered)

Everything runs on `chore/codebase-cleanup`. Cross-check precedes any deletion; decomposition (P2)
precedes the dead-code sweep (P3). Every step is an atomic commit gated by tests + mypy, so any step
is independently revertible against the P0 green baseline.

### P0 — Baseline & isolate

- Commit the finished **Portfolio-Aware Opportunity Cascade** work as its own commit so cleanup
  commits are isolated/reviewable. Exclude unrelated `uv.lock` and the `.serena/` cache.
- Activate the Serena project and read its `initial_instructions` (Serena protocol).
- Capture a **GREEN baseline**: run the test suite + `make mypy`; record what passes before any change.

### P1 — Cross-check (analysis only; NO deletions/moves)

Two independent signals must agree before a function is eligible for removal. Per candidate, mark
**CONFIRMED dead** only if ALL hold:

1. Serena `find_referencing_symbols(name, file)` → **0 references** (language-aware; authoritative).
2. grep fallback for indirect use → **0**, across `src/` + `tests/` **and `crews/**/*.yaml`**
   (CrewAI wires agents/tools by name in `agents.yaml`/`tasks.yaml`) — catches `getattr`/string dispatch.
3. Not exported in any `__init__.py`.
4. `find_symbol(include_body=True)` shows no `@agent`/`@task`/`@tool`/`@final_reporter`/`@property`
   and it is not a litellm/monkeypatch framework callback.

Fail any gate → **QUARANTINE** (untouched, logged with reason). Output: a committed
`cross-check-report.md` (CONFIRMED + QUARANTINE lists with evidence) as the audit trail. Also map the
god-file decomposition boundaries (which symbols group into which new submodule).

### P2 — Decompose god-files (re-export shims)

- `get_symbols_overview` each god-file → group cohesive symbols into focused submodules.
- Per group: `find_symbol(include_body=True)` to read → `create_text_file` new submodule → remove the
  moved symbols from the original via Serena edits → original becomes a thin `from .sub import *` shim.
- **Confirmed-dead symbols in these files are NOT moved** (deleted in P3 instead).
- One file at a time; full suite + `make mypy` after each; atomic commit per file.
- Targets: `reporting/section_generators.py`, `orchestrators/reporting_orchestrator.py`. Oversized
  functions (e.g. `context_preparation.get_integrated_data_context`) are optional follow-ups, not in
  the first cut unless they fall out naturally.

### P3 — Remove confirmed dead code

- Tier 1 (8 funcs) first, then Tier 2 **CONFIRMED only**, in directory-sized atomic commits.
- Tests + `make mypy` after each batch. QUARANTINE list never touched.

### P4 — Final verification & PR

- Full `make check` + `make mypy` + semgrep on touched files.
- Open PR including `cross-check-report.md` and a per-phase changelog.

## Error handling / rollback

Atomic commit per move/removal-batch. After each: affected tests + `make mypy` (catches broken
imports from moves) + `make check`. Red → `git revert` that commit, move the item to QUARANTINE,
continue. The P0 green baseline is the reference for "did I break something."

## Out of scope

- Tier 3 oversized-function decomposition beyond the two god-files (follow-up).
- Any QUARANTINE-listed function (kept until individually proven dead).
- `uv.lock` / dependency changes; behavior changes of any kind.

## Verification

- Per phase: targeted suites + `make mypy` green.
- Final: `make check` (lint + tests + unittest.mock ban + docs + file-size + stage-contract) green;
  `make mypy` clean; semgrep clean on touched files; `git diff` shows only intended removals/moves +
  shims; re-export shims keep all prior import paths working (verified by the unchanged test suite).
