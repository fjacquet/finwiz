# Codebase Simplification: Delete → Merge → Decompose

**Date:** 2026-06-09
**Status:** Approved
**Goal:** Shrink the codebase. Measure success in lines and files removed with `make check` green and the production flow (`crewai flow kickoff`) still working.

## Context and Evidence

- `src/finwiz`: 530 Python files, ~108k lines, 93 directories.
- 24 files exceed 500 lines, concentrated in `tools/` with overlapping variants
  (`enhanced_sentiment_tool` vs `standardized_sentiment_tool`, `enhanced_sec_tool`,
  `enhanced_crypto_tool`, …).
- Largest functions: `get_report_css` (333 lines of CSS in Python),
  `create_default_flags` (239), `ContextPreparationManager.get_integrated_data_context` (235),
  `generate_holdings_table` (181), `run_deep_analysis_concurrent` (154).
- Confirmed dead weight: `tools/notification_service.py` is referenced only by its own test.
  `reporting/portfolio_review_html.py` is believed orphaned (production report path is
  `python_report_generator.py` + `css_styles.py` + `sections/*`).
- `examples/` demos are among the most connected nodes in the dependency graph and are unused.

## Decisions Made

| Decision | Choice |
|---|---|
| Primary goal | Shrink the codebase (not refactor-in-place, not architecture rewrite) |
| Risk level | Provably dead code AND strong-evidence judgment calls; each judgment call gets a one-line justification in its PR |
| Keep | Backtesting subsystem, rebalancing history |
| Delete candidates | Notifications, `examples/` demos, orphaned scripts, dead report path |
| Approach | A: three ordered passes — Delete, Merge, Decompose — each independently shippable |
| Guardrails | Yes: ruff complexity rules + vulture in `make check` |

## Pass 1 — Delete

**Method.** Build the reachability set from production entry points: `main.py` /
`crewai flow kickoff` via `flows/orchestrator.py`, `Makefile` targets, CI workflows, and
test infrastructure (`conftest`). Use two independent signals before deleting anything:
the code-review-graph (`query_graph callers_of`) and `vulture`/grep cross-checks.

**Candidates (confirmed or to verify):**

1. `tools/notification_service.py` + `tests/unit/tools/test_notification_service.py`
   (~700 lines, provably dead — only self-references).
2. `examples/` directory — all demos (user confirmed unused).
3. `reporting/portfolio_review_html.py` and its caller chain
   (`orchestrators/portfolio_review_enhanced.py`, `portfolio_review_orchestrator.py`)
   **if** tracing confirms the chain is unreachable from the production flow.
4. Orphaned `scripts/` (e.g., `create_missing_docs.py`, `convert_json_to_html.py`)
   after confirming absence from `Makefile`, CI, and docs tooling.
5. Unused feature flags in `config/features/definitions.py::create_default_flags` —
   any flag whose key is never passed to `is_feature_enabled()`.

**Rules.** Each deletion removes the module, its tests, schema entries, tool-factory
wiring, and doc references together — no stubs. Backtesting and rebalancing history
are explicitly out of scope for deletion.

**Validation.** `make check` green per PR; one user-run `crewai flow kickoff`
before the wave merges.

**Expected payoff:** ~5–10k lines removed at near-zero risk.

## Pass 2 — Merge (DRY)

**Method.** Clone detection (`pylint --enable=duplicate-code` or `jscpd`) plus graph
semantic search to find duplicate clusters. Per cluster: pick the canonical
implementation (the one on the production path), migrate callers via
`tools/tool_factories.py`, delete the loser, merge its distinct test cases into the
survivor's tests.

**Known targets:**

- Sentiment: merge `enhanced_sentiment_tool` (deep analysis path) and
  `standardized_sentiment_tool` (finance_tools path) into one tool, one schema,
  one test file.
- `enhanced_*` family audit: check `enhanced_sec_tool`, `enhanced_crypto_tool`, etc.
  for plain siblings doing the same job.
- Tool boilerplate: extract the repeated `_run` pattern
  (try/except → error string → cache lookup → API call → format response) into one
  shared helper; each tool keeps only its unique logic.
- Reporting formatters and `orchestrators/extraction/*`: same clone-cluster treatment.

**Rules.** Factory functions remain the only instantiation point. Merged tools keep
the production tool's name/registration so crew YAML configs don't churn. One PR per
cluster for trivial bisection.

## Pass 3 — Decompose (KISS + FP) and Guardrails

**Style: functional core, imperative shell.**

- Large functions split into small pure functions (typed Pydantic data in → data out,
  no I/O, no hidden state) orchestrated by one thin assembler that does the I/O.
  E.g., `get_integrated_data_context` (235 lines) → ~6 pure builders + 1 assembler.
- Stateless `*Manager` classes become module-level functions.
- `get_report_css` moves to a `.css` asset file read at render time; HTML blobs in
  Python move to template files.

**Guardrails (added to `make check`):**

- ruff `C901` (max complexity ~10) and `PLR0915` (max statements), grandfathering
  existing violations via per-file ignores that shrink over time.
- `vulture` dead-code check with a whitelist for false positives.
- Duplication-detector run at the end of each wave with a threshold.

**Validation.** Behavior-preserving only: existing tests are not rewritten and must
keep passing; coverage stays ≥ 65%.

## Delivery

Three PR waves matching the three passes. Each wave is independently shippable and
validated. Pass 1 lands first because deleting code is the cheapest simplification
and de-risks every later refactor.

## Out of Scope

- Architecture rewrite (layer collapse, directory restructuring beyond deletions).
- Behavior changes of any kind; AI-minimalism boundaries stay as they are.
- Coverage enforcement on AI/LLM code paths (existing project rule).
