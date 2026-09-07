# Design: remove `FinwizFlow`'s inert `@listen` graph

**Issue:** [#193](https://github.com/fjacquet/finwiz/issues/193)
**Date:** 2026-09-07
**Status:** approved

## Problem

`FinwizFlow` carries ten `@listen`-decorated methods forming a graph that never
fires. Its root listens for `validate_data_integration`, which no method on
`FinwizFlow` or its MRO emits — that name belongs to `ValidationOrchestrator`.
With no producer for the root trigger, every listener downstream is unreachable,
`report` included.

The only `@start()` on the MRO that can fire is `run_sequential_workflow`, which
drives all six phases imperatively. `_ConversationalMixin.route_conversation` is
also a `@start()`, but its `@_conversational_only` gate requires a
`ConversationState`; `FinwizState` is not one.

The graph is not merely idle — it is a smaller, older pipeline. It has no node
for stress testing (Phase 3.5), the post-flow cost summaries, or the run gate.
A reader who follows the decorators is reading a previous version of the system
and has no way to tell.

`tests/property/test_backward_compatibility_properties.py` keeps the methods
alive with `hasattr`-shaped assertions, which pass whether or not the chain can
execute. That is why no gate caught this.

## Verified current state

Each listener body is a single delegation to an orchestrator, and every one of
those exact calls already appears in `run_sequential_workflow`
(`src/finwiz/flows/orchestrator.py:186-302`):

| Listener (dead) | Imperative call (live) |
|---|---|
| `analyze_and_update_portfolio` (338) | line 228 |
| `check_portfolio` (343) | line 215 |
| `build_gap_profile` (348) | line 257 |
| `check_crypto` (353) | line 269 |
| `check_stock` (358) | line 270 |
| `check_etf` (363) | line 271 |
| `check_investment_discovery` (368) | line 272 |
| `match_alternatives_after_discovery` (373) | line 278 |
| `pre_validate_reporter_input` (378) | line 284 |
| `report` (383) | line 285 |

The imperative path is a strict superset: it additionally runs
`validate_data_integration` (209), stress testing (242), the LLM cost summaries
and the run gate. Removing the listeners therefore changes no behavior.

(Note against the issue text: `build_gap_profile` *is* a node in the graph. The
graph's missing phases are stress testing, the cost summaries and the run gate.)

## Decision

Delete the graph. Keep `run_sequential_workflow` as the single pipeline.

Repairing the graph was rejected: it would mean inventing a producer for the
root trigger and adding four missing nodes, in service of an orchestration style
nothing in the project asks for. An inert-but-plausible pipeline left documented
as inert was rejected outright — plausibility is what let this survive.

## Scope

**Delete** from `src/finwiz/flows/orchestrator.py`:

- the ten `@listen` methods (lines 337-385)
- the now-unused `listen` and `and_` imports

**Keep:**

- `plot()` and its `plot = "finwiz.main:plot"` entry point. It will render a
  single-node graph, which is an accurate picture of the flow.
- every orchestrator method the listeners delegated to — all are called
  imperatively and are covered by their own unit tests.

**Rewrite** `tests/property/test_flow_delegation_properties.py`'s listener-
delegation property and the three `sampled_from` lists in
`tests/property/test_backward_compatibility_properties.py`. In place of
`hasattr` assertions over method names, a single behavior test drives
`run_sequential_workflow` with mocked orchestrators and asserts the six phases
are invoked, in order. That test fails if the pipeline breaks; the `hasattr`
ones did not.

**Update** the docs that describe a listener pipeline:

- `src/finwiz/flows/CLAUDE.md:34-35` — the "plain `@listen("check_portfolio")`
  listeners" sentence
- `docs/explanations/ORCHESTRATOR_INTERACTIONS.md` — the sequence diagram and
  its surrounding prose
- `docs/REQUIREMENTS.md:58` — the `match_alternatives_after_discovery` reference
- `CHANGELOG.md`

## Testing

- `make test` green.
- The new phase-order test fails when a phase call is removed from
  `run_sequential_workflow` — verified by deleting one call locally before
  writing the implementation.
- `uv run plot` still succeeds and emits a graph.
- Coverage stays above the 65% threshold; the deleted lines were covered only by
  `hasattr` probes, so the ratio moves little.

## Risk

Low. No production call path reaches the deleted methods; CrewAI resolves
listeners by decorator registration at class-definition time, so nothing
resolves them dynamically by name. The one external surface is the property
tests, which are rewritten in the same change.
