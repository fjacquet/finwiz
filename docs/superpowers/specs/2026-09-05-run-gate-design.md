# Run Gate — Design

**Date:** 2026-09-05
**Status:** Approved design, ready for implementation planning
**Scope:** `src/finwiz/schemas/run_summary.py` (new), `src/finwiz/analysis/run_gate.py` (new), `src/finwiz/orchestrators/run_gate_orchestrator.py` (new), `scripts/run_gate.py` (new), `src/finwiz/config/settings.py`, `src/finwiz/flow_state_models.py`, `src/finwiz/flows/orchestrator.py`, `src/finwiz/core/app_initializer.py`, `src/finwiz/orchestrators/deep_analysis_orchestrator.py`, `Makefile`
**Roadmap:** workstream A of `docs/superpowers/roadmaps/2026-09-05-reevaluation.md`

## Problem

The 2026-09-05 run was green on every gate the project has. `make check` passed. Every CI workflow passed. The process exited 0. And the run it produced served 28 % of its fact packs from a 19-day-old cache, ran three phases that delivered nothing, and reported a cost of `$0.0000` for 15.9 million tokens because the model was unpriced.

Nothing checks the product after `kickoff()`. `core/app_initializer.py` logs `✅ FinWiz analysis workflow completed successfully` and calls `os._exit(0)` — unconditionally. A degraded run is indistinguishable from a good one to whoever launched it. Establishing each of the three facts above took several greps over `logs/finwiz.log`, which is the weakest artifact the run produces: unstructured, rotated, and written by forty modules with forty ideas of what matters.

The pieces of a verdict already exist, scattered: `RunLedger.coverage()` knows how many holdings reached a verdict; `portfolio_review` knows how many were priced; the cost monitor knows which crews it could price; Phase 3 now logs a fact-pack freshness line (workstream C). What is missing is the place where they meet, the thresholds they are held to, and a consequence.

## Decisions

Three decisions were settled before design and constrain everything below.

1. **A degraded run exits non-zero and writes a structured summary.** `output/run_summary.json` carries every input and every check; the process exits `1` on FAIL. The HTML report is always produced first — it is the evidence of what degraded, and evidence is not destroyed to signal a problem. Nothing consumes the exit code today, so making it truthful costs nothing now and is exactly what a scheduled run (workstream E) needs later.

2. **FAIL means the report is not trustworthy. WARN means a known gap is still a gap.** Coverage, valuation, cost visibility and fact-pack freshness decide trust; they FAIL. Discovery producing nothing, alternatives producing nothing, stress tests missing — these are tracked in the roadmap (workstream D) and WARN. The alternative, failing on everything, makes the gate red from its first run until D ships. A gate that is always red is the mechanism by which Requirement 9.2 became noise (workstream F); this design refuses to build another one.

3. **The gate is the last step of the flow, in-process.** Approach A1 over a post-hoc script (A2) or a report section (A3). The log is too weak a source to parse, and neither freshness nor cost exists in any artifact today — a post-hoc script would need the same JSON persisted first and would then be A1 with extra fragility. The JSON is the contract; the evaluation is a pure function over it.

## Design

### 1. Placement

`FinwizFlow` runs its phases sequentially and ends with `_log_post_flow_summaries()` (`flows/orchestrator.py:293`), which puts the LLM cost summary on state. The gate runs **immediately after that call** — the last act before `Sequential workflow completed`. By then every input exists: the ledger, the priced portfolio, the cost summary, the freshness summary, the phase outcomes.

`core/app_initializer.py` replaces `os._exit(0)` with `os._exit(exit_code_for(flow_state.gate_verdict))`.

### 2. Components

Seven pieces, each with one reason to exist.

| Component | Role | Depends on |
|---|---|---|
| `schemas/run_summary.py` — `RunSummary`, `GateCheck`, `Verdict`, per-domain sub-models | the contract | nothing. Models live in `schemas/`, per project rule |
| `config/settings.py` — `RunGateSettings`, nested as `gate`, env `FINWIZ_GATE__*` | thresholds, overridable without code | the existing `FinWizSettings` with `env_nested_delimiter="__"` |
| `analysis/run_gate.py` — `evaluate(inputs, thresholds) -> list[GateCheck]`, `verdict(checks) -> Verdict`, `exit_code_for(verdict) -> int` | **pure**: numbers in, checks and a verdict out. No state, no IO, no clock | the schema |
| `orchestrators/run_gate_orchestrator.py` — `RunGateOrchestrator(state).run() -> RunSummary` | collects inputs from state, calls `evaluate`, writes the JSON, logs the verdict block, sets `state.run_summary` and `state.gate_verdict` | `RunLedger`, `PortfolioReview`, the cost summary dict, `analysis/run_gate.py` |
| `flows/orchestrator.py` | one guarded call after `_log_post_flow_summaries()` | the orchestrator |
| `core/app_initializer.py` | the exit code | `exit_code_for` |
| `scripts/run_gate.py` + `make gate` | re-evaluate an existing `run_summary.json` against current thresholds; same block, same exit code | `analysis/run_gate.py` and the schema only — never the flow |

Two supporting changes:

- `flow_state_models.py` gains `fact_pack_freshness: dict[str, Any] | None`, `run_summary: dict[str, Any] | None`, `gate_verdict: str | None`.
- `orchestrators/deep_analysis_orchestrator.py` persists the workstream-C freshness summary onto `state.fact_pack_freshness` in the same place it logs it. Today that line is the only trace of the number; after this it is an input.

### 3. The contract

`RunSummary` is one document with one sub-model per domain. Every sub-model carries `available: bool`, so "we could not measure this" is a value, not an absence.

```
RunSummary
  run_id, started_at, finished_at, duration_seconds
  coverage:   available, analyzed, degraded, failed, total          ← RunLedger.coverage()
  valuation:  available, priced, total                               ← PortfolioReview.holdings
  fact_pack:  available, fresh, recent, stale, missing, total,
              oldest_stale_fetched_at                                ← state.fact_pack_freshness
  phases:     discovery_candidates, alternatives_found,
              underperformers, stress_scenarios, optimal_allocation  ← state fields (below)
  cost:       available, total_usd, call_count, cost_known,
              unpriced_crews                                         ← state.llm_cost_summary
  checks:     list[GateCheck]
  verdict:    PASS | WARN | FAIL | ERROR

GateCheck
  name, severity (FAIL | WARN), passed, observed, threshold, detail
```

Sources, exactly:

| Field | Read from |
|---|---|
| `run_id` | `state.run_ledger.run_id`, else `state.id` |
| `coverage` | `state.run_ledger.coverage()` — `CoverageSummary(analyzed, degraded, failed, total)` |
| `valuation.priced` | `len([h for h in portfolio_review.holdings if h.weight is not None])`. **The same set the allocation hero counts.** Deriving the ratio from a different denominator than the one displayed is the defect 5.14.1 fixed |
| `fact_pack` | `state.fact_pack_freshness`, the persisted workstream-C summary |
| `phases.discovery_candidates` | length of the candidate list inside `state.investment_discovery_result`, `0` when `None`. The exact key is a data-shape detail the implementation plan pins after reading one real payload |
| `phases.alternatives_found` | `state.alternatives_count` |
| `phases.underperformers` | `len(state.portfolio_gap_profile["underperformer_slots"])` — the count Phase 3.6 already computed, not a new definition |
| `phases.stress_scenarios` | `state.stress_test_count` |
| `phases.optimal_allocation` | `state.optimal_allocation is not None` — informational until workstream G ships |
| `cost` | `state.llm_cost_summary`: `total_cost`, `call_count`, and `per_crew[*]["cost_known"]`; `unpriced_crews` lists every crew whose `cost_known` is false |

### 4. Checks and thresholds

| Check | Severity | Passes when | Default |
|---|---|---|---|
| `coverage` | FAIL | `analyzed / total ≥ min_coverage_ratio` | 0.95 |
| `valuation` | FAIL | `priced / total ≥ min_priced_ratio` | 0.95 |
| `cost_known` | FAIL | `unpriced_crews` is empty | — |
| `fact_pack_stale` | FAIL | `stale / total ≤ max_stale_ratio` | 0.25 |
| `discovery` | WARN | `discovery_candidates > 0` | — |
| `alternatives` | WARN | `alternatives_found > 0` **or** `underperformers == 0` | — |
| `stress_tests` | WARN | `stress_scenarios > 0` | — |
| `fact_pack_missing` | WARN | `missing == 0` | — |

**A check whose input is `available=False` FAILS with detail `"not measured"`.** It is never skipped. A gate that skips a check when the data is missing is a gate that is passed by breaking the data.

Thresholds live in `RunGateSettings` and are overridable per environment: `FINWIZ_GATE__MIN_COVERAGE_RATIO=0.9`. Severities are **not** configurable — moving a check between FAIL and WARN is a design decision, made in code, reviewed.

Against the 2026-09-05 run: `coverage` PASS (64/64), `valuation` PASS (63/64 = 98 %), `cost_known` FAIL (three crews unpriced — should PASS after workstream B; to confirm), `fact_pack_stale` FAIL (18/64 = 28 %), `discovery` WARN (0), `alternatives` WARN (0 for 17), `stress_tests` PASS, `fact_pack_missing` PASS. **Verdict: FAIL.** That is the correct verdict for that run.

### 5. Verdict, exit code, output

Aggregation: any FAIL → `FAIL`; else any WARN → `WARN`; else `PASS`. WARNs never escalate by accumulation — three WARNs are `WARN`. That is what keeps the signal legible.

| Verdict | Exit | Meaning |
|---|---|---|
| `PASS` | 0 | nothing to report |
| `WARN` | 0 | known gaps, still gaps |
| `FAIL` | 1 | the report is not trustworthy |
| `ERROR` | 2 | the gate itself could not evaluate |

The distinction between `0` and `2` is the point: "nothing to report" and "I did not look" must never share an exit code.

The log block, one line per check, verdict last, each line grep-able by its prefix:

```
run gate: coverage        PASS  64/64 analysed (min 95%)
run gate: valuation       PASS  63/64 priced (min 95%)
run gate: cost_known      FAIL  3 crews unpriced: deep_analysis_crypto, deep_analysis_etf, deep_analysis_stock
run gate: fact_pack_stale FAIL  18/64 stale = 28% (max 25%)
run gate: discovery       WARN  0 candidates
run gate: alternatives    WARN  0 found for 17 underperformers
run gate: stress_tests    PASS  6 scenarios
run gate: fact_pack_missing PASS  0 missing
run gate: verdict FAIL — output/run_summary.json
```

Output: `RunSummary.model_dump_json(indent=2)` to `output/run_summary.json`, overwritten each run, plus a dated copy at `output/run_ledger/<run_id>.summary.json` beside the ledger — the history workstream E will read.

### 6. Failure of the gate itself

The report is written before the gate runs. The gate never raises into the flow. The orchestrator wraps everything: on any exception it logs **with traceback** (`logger.exception`, the convention established in PR #158), sets `state.gate_verdict = "ERROR"`, and returns. The process exits `2`.

Absent inputs are not exceptions. A `None` ledger, a `None` cost summary, a missing freshness field — each collector returns its sub-model with `available=False`, and the corresponding check FAILs with `"not measured"`. The gate always produces a summary; what varies is what the summary says.

### 7. The standalone

`make gate` → `uv run python scripts/run_gate.py output/run_summary.json`.

It loads the JSON, **re-evaluates** against the current `RunGateSettings` — not the stored verdict — prints the same block, exits with the same code. Change a threshold in `.env`, run `make gate`, see the effect without a 23-minute kickoff. It imports `schemas/run_summary.py` and `analysis/run_gate.py` and nothing else; it must work with no flow, no state, no network.

### 8. Testing

All offline, under the pytest-socket guard, pytest-mock only.

| Test | Asserts |
|---|---|
| `evaluate`, per check | both sides of every threshold, with the 2026-09-05 values as the nominal cases: 64/64, 63/64, 18/64, 0 candidates, 17 underperformers |
| unavailable input | `available=False` → FAIL, detail `"not measured"`; never absent from `checks` |
| aggregation | FAIL > WARN > PASS; three WARNs are WARN; an empty check list is PASS |
| `exit_code_for` | PASS→0, WARN→0, FAIL→1, ERROR→2 |
| valuation collector | unpriced holdings excluded from `priced`, never from `total` |
| orchestrator, state as `SimpleNamespace` | JSON written, round-trips through `RunSummary.model_validate_json`; a collector raising → verdict ERROR, traceback in caplog, nothing raised |
| `scripts/run_gate.py` | changed threshold changes the verdict; exit codes; no `finwiz.flows` import |
| `app_initializer` | `os._exit` (mocked) receives the code of the verdict |

Deterministic Python end to end; fully inside the coverage gate.

## Risks

**The first real run will exit 1.** 28 % stale exceeds 25 %; if workstream B did not resolve pricing, `cost_known` fails too. This is intended — the gate tells the truth about a run known to be degraded. The first `PASS` comes from fixing Perplexity's failure rate or from deciding, in review, that a higher threshold is acceptable. It never comes from lowering the bar until the light turns green.

**Anything that calls `crewai flow kickoff` and expects 0 will now see 1 or 2.** Nothing does today — no cron, no CI. Whoever wires one later (workstream E) is the intended consumer.

> **Correction, 2026-09-05 (verified during implementation).** As written this is
> false, and the difference matters to whoever wires workstream E. The vendored
> `crewai` CLI catches `CalledProcessError` in `crewai_cli/run_crew.py:771-776`,
> prints it, and returns — so `crewai flow kickoff` exits **0 regardless of the
> verdict**. The gate's exit code is only observable via `uv run kickoff`, which
> is what Task 8 and any cron or CI wrapper must call. Nothing in this repo
> consumes the CLI's status today (`make gate` invokes `scripts/run_gate.py`
> directly), so nothing is broken by this — but a consumer wired to
> `crewai flow kickoff` would silently see every run as a pass, which is the
> exact failure this gate exists to prevent.

**Thresholds are guesses until measured.** 0.95 / 0.95 / 0.25 are set from one run. `make gate` exists precisely so they can be revisited against the JSON of several runs without relaunching any of them.

## Implementation order

1. `schemas/run_summary.py` — the contract first; everything downstream is typed against it.
2. `analysis/run_gate.py` + tests — pure, offline, no dependency on the rest.
3. `config/settings.py` — `RunGateSettings`; a test that `FINWIZ_GATE__MAX_STALE_RATIO` overrides the default.
4. `flow_state_models.py` fields + persist the freshness summary in `deep_analysis_orchestrator.py`.
5. `orchestrators/run_gate_orchestrator.py` + tests — collectors, JSON, verdict block, ERROR path.
6. `flows/orchestrator.py` call + `core/app_initializer.py` exit code + test.
7. `scripts/run_gate.py` + `make gate` + tests.
8. Live `crewai flow kickoff`: expect exit 1, read `output/run_summary.json`, confirm every number against the log by hand once. Then `make gate` on that file.

Each step leaves the suite green. Steps 1–5 change no production behaviour; step 6 is the first that can change an exit code.

## Done when

- A live run writes `output/run_summary.json` and the dated copy, logs the verdict block, and exits with the code of its verdict.
- Every check reads the source named in §3; the valuation ratio uses the hero's denominator.
- An unavailable input FAILs its check with `"not measured"`.
- Forcing an exception inside a collector yields verdict ERROR, exit 2, a traceback in the log, and a report that was still written.
- `make gate` on the produced JSON reproduces the verdict, and a changed threshold changes it.
- `make check` green.

## Amendments after code review (2026-09-05)

The review of the implementation branch found the design under-specified in five
places. The rulings below supersede §3–§5 where they conflict.

- **`coverage` counts every holding that produced a verdict.** §4 says
  `analyzed / total`, but `RunLedger.coverage()` computes `analyzed` as
  `analyzed - degraded`, so degraded holdings were subtracted from the numerator
  and never added back: a run in which all 64 holdings produced a verdict, four
  of them degraded, FAILed at "60/64 analysed" while `TrustBanner` called the
  same run amber. A degraded holding is amber, not absent. The check is
  `(analyzed + degraded) / total`, and its observed string shows the
  composition, not a bare ratio.
- **`CoverageInput.failed` is dropped.** It is `total - analyzed - degraded` by
  construction; the coverage check shows it derived. Nothing read it.
- **`phases.optimal_allocation` is dropped.** §3 called it informational until
  workstream G, but nothing under `src/` ever writes `state.optimal_allocation`,
  so every summary recorded `false` — which reads as a measured fact and is not
  one. Workstream G reintroduces it together with its writer.
- **`PhasesInput` carries `underperformers_available`.** Phase 3.6 fail-softs to
  `PortfolioGapProfile(is_empty=True)`, whose `underperformer_slots` is an empty
  list — so "nobody needs replacing" and "the profile was never built" both
  arrived as `underperformers == 0`, and zero underperformers is exactly what
  passes the `alternatives` check. `is_empty` is the flag that tells them apart.
- **`cost_known` is read, not inferred.** Live runs derive the flag from
  `unpriced_crews`, so the two agree; `make gate` re-judges stored files, where
  a summary saying `cost_known: false` with an empty crew list passed as
  "$0.00 over 5 calls".
- **An un-judged run exits 2.** §5 gives exit 1 to FAIL. A crash before the gate
  ran used to exit 1 too, through Python's default handler, so a reader of the
  contract concluded "the gate failed this run" about a run nobody evaluated.
  `core/app_initializer.py` defaults its exit code to ERROR before the phases
  run; only a verdict lowers it. A bad `FINWIZ_GATE__*` threshold in
  `scripts/run_gate.py` is the same class of collision and gets the same answer.
