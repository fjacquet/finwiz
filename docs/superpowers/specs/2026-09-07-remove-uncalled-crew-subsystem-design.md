# Removing the uncalled crew subsystem

**Date:** 2026-09-07
**Issue:** #187
**Status:** approved, awaiting implementation plan

## The problem

Six of the seven crews in this repository have no caller. Neither do the factory
that builds them, the modules that would consolidate their output, nor the
report generators that would render it.

This was not a mistake at the time. Discovery moved from AI crews to Python
scoring — the repository's own **AI Minimalism** rule, applied correctly. What
went wrong is that nothing was deleted afterwards and the documentation kept
describing the old flow, so the dead code went on looking alive for months.
`CLAUDE.md` still asserted `Phase 4: Discovery (crypto/stock/etf crews)`
until #190 corrected it.

The cost is not disk space. It is that a reader cannot tell which parts of this
codebase run. `stock_crew` rotted until it could no longer be instantiated at
all — `agents.yaml`, `tasks.yaml` and the `@agent` methods diverged, giving
`KeyError: 'sec_analyst'` — and nothing anywhere reported it, because nothing
calls it. That is what a subsystem with no caller does: it stops being code and
becomes scenery, and the next person copies the scenery.

## Evidence

Static, from the source tree:

| `CrewFactory` method | Production callers |
|---|---|
| `execute_stock_crew` | 0 |
| `execute_etf_crew` | 0 |
| `execute_crypto_crew` | 0 |
| `execute_portfolio_rebalancing_crew` | 0 |
| `execute_investment_discovery_crew` | 0 |
| `execute_report_crew` | 0 |
| `create_crew_inputs_for_portfolio_rebalancing` | 0 |
| `create_crew_inputs_for_investment_discovery` | 0 |

`CrewFactory` itself is constructed at `flows/orchestrator.py:107` and logs
`Crew factory initialized`. Not one of its methods is then called. It is a
constructed, abandoned object.

`reporting/consolidator.py` and `reporting/export_loaders.py` have **zero
importers** anywhere in `src/` or `tests/`.

Behavioural, from a real run (2026-09-06, 64 holdings, completed):

- **No `*_export.json` exists anywhere under `output/`.** That file is the only
  artefact these crews produce. Not one has ever been written.
- `discovery_orchestrator.py` logs `Using Python analysis` for crypto, stock and
  ETF, and holds no crew reference at all.
- The run logged, three times, `Consolidated <asset> crew data: 0 ticker
  analyses, avg score: 0.000` (`registry_data_retrieval.py:173`), and
  `Consolidated data from 5 crews` (`cache.py:98`).

That last point matters more than the rest, and is the reason this is a design
question rather than a delete-and-go. Those calls are **live code querying
absent producers**. They do not fail; they return zero and carry on. Deleting
the crews without them would leave the queries orphaned — trading a dead
subsystem for a live one that searches for nothing.

The one crew that runs is `deep_analysis`, reached from
`analysis/_helpers.py:95`, bypassing `CrewFactory` entirely.

## What goes

- The six crew packages: `stock_crew` (901 lines), `etf_crew` (775),
  `crypto_crew` (852), `investment_discovery_crew` (1005),
  `portfolio_rebalancing_crew` (1172), `report_crew` (1505) — **6,210 lines**.
- `crew_factory.py` in full, and its construction site in `flows/orchestrator.py`.
- `reporting/consolidator.py` and `reporting/export_loaders.py`.
- The per-crew report generators and the `reporting/__init__.py` registry
  entries that map crew names to them.
- The `html_collector.py` crew-name mapping and the `ConsolidatedReportExport`
  fields that only the dead path fills.
- `schemas/crew_exports.py` — every export class **except**
  `DeepAnalysisCrewExport` and whatever `CrewExportBase` it needs.
- The `stock_analysis`, `etf_analysis` and `crypto_analysis` feature flags, and
  any flag gating the other three executors.
- The `{crew}_analysis_error / disabled / success / fallback / result` fields on
  `FinwizState`, and the `validation_orchestrator` branches that read them.
- The crew-data query paths in `registry_data_retrieval.py` and `cache.py` that
  return zero for stock, ETF and crypto.
- `tests/validation/stock_crew_validation.py` — a manual runner for a crew that
  will not exist.
- Every test whose only subject is the above.

## What stays

- `deep_analysis` and `DeepAnalysisCrewExport`. It is the one crew that runs.
- The **Flow framework** — `Flow[FinwizState]`, `@start`, `@listen`, 14 usages
  in `orchestrator.py` alone. It is the phase state machine and is load-bearing.
- The **tool abstraction** — `crewai.tools` (15 imports) and
  `crewai_custom_tools` (20+) across `tools/`.
- `tools/tool_factories.py` entries still used by `deep_analysis`. The
  `get_stock_crew_tools()` / `get_etf_crew_tools()` helpers must be checked
  individually: some are called by the dead crews only, some by tool routing
  that survives.

## Decisions taken

**The `FinwizState` crew fields are deleted, not kept as no-ops.** The
repository's standing rule is *remove the switch, not the surface* — when a kill
switch goes, the gate goes and the field stays for caller stability. That rule
does not apply here. These fields are not a switch; they are the recorded state
of a subsystem that will not exist. A field named `stock_analysis_success` that
can only ever be `None` is a question the codebase can no longer answer, and
`validation_orchestrator` currently branches on it.

**Order: leaves first.** Crews, then the factory, then the reporting chain, then
the flags and state fields, then the tests. Each step must leave the suite green
on its own, so a step that turns out to be wrong can be dropped without
unpicking the ones after it.

**The suite is not the acceptance test.** 5,415 unit tests pass today with this
entire subsystem dead — they would very likely pass with it deleted and with it
half-deleted. The judge is a **live 3-holding `uv run kickoff`** (~$0.04, ~6
min, via the `PORTFOLIO_*_CSV` overrides) which must still return `VERDICT:
PASS` with all eight gate checks green. Run it before the first deletion and
after the last, and compare `output/run_summary.json` field by field.

**Documentation ships with the change**, per the repository's standing rule.
`CLAUDE.md`'s Key Components table, the Crew Pattern section, and the
architecture diagram all change again once the code matches #190's description.

## Risks

The blast radius crosses reporting and validation, which are live. Three
specific hazards:

1. **`schemas/crew_exports.py` is shared.** `DeepAnalysisCrewExport` must
   survive, and it inherits `CrewExportBase`. Removing sibling classes must not
   disturb the base or its validators.
2. **`ConsolidatedReportExport` may be partly live.** The reporting orchestrator
   produced 64 HTML reports from `*_enriched.json`, not from crew exports — but
   the consolidated export type may still be constructed with empty crew fields.
   Each field needs checking before removal, not assuming.
3. **The zero-returning query paths are called from live code.** Removing the
   producers is safe; removing the callers requires knowing whether anything
   downstream reads their empty results as meaningful (an empty list that means
   "no stock analyses" may currently be feeding a report section that will
   otherwise get `KeyError`).

Each is a "verify at implementation time, do not assume" item. The plan should
carry them as explicit steps, not as caveats.

## Out of scope

**Whether CrewAI itself should stay.** After this deletion the system has one
agent and one task. CrewAI's headline feature is crews of collaborating agents,
and there will be exactly one agent left; the repository's own guidance says
*CrewAI only for reasoning, not for wrapping single API calls*. A one-agent,
one-task crew sits close to that line — defensible, because qualitative analysis
is reasoning, but a fair question.

It is not this spec's question. The Flow framework and the tool abstraction keep
CrewAI load-bearing regardless of how many crews exist, so the two decisions are
independent. This deletion is what makes the other one askable; it does not
answer it.

## Done when

1. No `crews/` package other than `deep_analysis` remains, and `crew_factory.py`
   is gone.
2. `grep -rn "crewai" src/` returns hits only from `deep_analysis`, the Flow
   orchestrator, `tools/`, and `crewai_custom_tools` consumers.
3. No module imports `consolidator` or `export_loaders`, because neither exists.
4. `FinwizState` has no `{crew}_analysis_*` field, and nothing branches on one.
5. No log line reports `Consolidated <asset> crew data: 0 ticker analyses`,
   because nothing asks.
6. The full default suite is green, and `-m integration` is green.
7. A live 3-holding `uv run kickoff` returns `VERDICT: PASS` with all eight
   checks green, and its `run_summary.json` matches the pre-deletion baseline
   field for field except `duration_seconds`.
8. `CLAUDE.md` describes the crews that exist.
