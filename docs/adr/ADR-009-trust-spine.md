# ADR-009: Trust Spine

- **Status:** Accepted
- **Date:** 2026-04-28
- **Deciders:** FinWiz Core Team

## Context

v0.3.0 (2026-04-27) revealed three classes of trust-breaking bugs that survived all existing tests:

1. **Silent success** — The `DEEP_PORTFOLIO_ANALYSIS` kill switch defaulted to `"false"`, causing Phase 3 to no-op silently. 62 of 63 holdings were never analyzed, yet the final report read `"✅ FinWiz analysis workflow completed successfully"` and displayed placeholder `grade="D"` / `composite_score=0.6` as if they were real verdicts.

2. **Aggregate timeout discards completed work** — A global 1800s `asyncio.wait_for` wrapped the entire `asyncio.gather`. When it fired, every already-finished future was thrown away. A concrete run lost XRP-USD (finished at 09:00:12, grade=D, 92.3s) because a slow ticker pushed total runtime past the cap 4½ minutes later. (Fixed in v0.3.1 by removal; this ADR codifies the structural rule.)

3. **Python fallback masquerading as AI insight** — When the AI crew returned `None` for qualitative sections, the pipeline silently substituted Python-derived values and emitted status `OK` with no indication of degradation. Consumers (report renderer, downstream orchestrators) had no way to distinguish a genuine AI-produced insight from a Python fallback. This is the "Python-fallback masquerading as AI insight" class: it undermines the stated hybrid architecture.

These three classes share a root cause: no typed contract between pipeline stages, no persistent evidence of what ran vs. what was skipped, and no honest surfacing of degraded results.

## Decision

Introduce a **trust spine** — a set of structural guarantees that make silent failure impossible at the type level:

1. **Typed `StageResult[T]` contract** — Every pipeline stage returns `StageResult[T]` (a discriminated union of `OK[T]`, `DEGRADED[T]`, and `FAILED`). Stages cannot return a bare value; the caller is forced to inspect the outcome variant before consuming the payload.

2. **`@stage` decorator** enforces per-unit timeouts and retry policy, then records each execution to the `RunLedger`. Aggregate `wait_for` patterns are banned by AST static check.

3. **`RunLedger`** — A JSONL artifact written to `output/run_ledger/<run_id>.jsonl` with one line per stage execution (ticker, stage name, status, duration, error if any). Provides a replayable post-mortem without needing to re-run the flow.

4. **`TrustBanner`** — Derived deterministically from `RunLedger` coverage at report time. Four states: `green` (all stages OK), `amber` (≥1 DEGRADED, 0 FAILED), `red` (≥1 FAILED, coverage still sufficient), `blocked` (coverage below threshold — report carries explicit "NE PAS prendre de décisions" warning). No AI involved in banner computation.

5. **Honest degradation** — When the AI crew returns `None`, `qualify` emits `StageResult.DEGRADED` (not `OK`). `synthesize` propagates `confidence='low'`. `emit` writes `confidence='low'` to `EnrichedAnalysis`. The HTML renderer displays an amber "Insight IA indisponible" badge. No silent substitution.

6. **Any-stage `FAILED` short-circuits** — A holding with any `FAILED` stage is marked `AnalysePending` (not analyzed), preventing a partially-run result from being presented as complete.

### Implementation

**Stage modules** (`src/finwiz/analysis/`):

| Module | Responsibility |
|--------|---------------|
| `stages/collect.py` | Raw market data collection |
| `stages/quantify.py` | Python composite scoring |
| `stages/qualify.py` | AI qualitative insights (emits DEGRADED on None) |
| `stages/synthesize.py` | Merge quant + qual, propagate confidence |
| `stages/emit.py` | Write `EnrichedAnalysis` to state |
| `stages/_ledger.py` | `RunLedger` JSONL writer |
| `stages/_resilience.py` | `@stage` decorator (timeout, retry, ledger) |
| `stages/_qualify_fallbacks.py` | Python fallback values (labeled DEGRADED) |
| `stages/_synthesize_helpers.py` | Merge utilities |
| `stages/_synthesize_options.py` | Options IV merge logic |
| `deep_analysis_pipeline.py` | Thin orchestrator (99 lines, down from 1,209) |

**Schemas** (`src/finwiz/schemas/`):

- `StageResult[T]` — Generic discriminated union (`OK`, `DEGRADED`, `FAILED`)
- `RunLedger` — Pydantic model for JSONL entries
- `TrustBanner` — Four-state enum + coverage ratio

**AST static check** (`scripts/check_stage_contract.py`):

- Forbids `asyncio.wait_for` at aggregate scope
- Warns when a stage function returns a bare value instead of `StageResult`
- Wired into `make check` as `make check-stage-contract`

## Consequences

### Positive

- **Silent failure is structurally impossible** — The type system forces every caller to handle `OK / DEGRADED / FAILED`; there is no code path that silently drops a failure.
- **Replayable JSONL post-mortem** — `RunLedger` artifacts survive the process; a future analyst can reconstruct exactly which stage failed, at what time, with what error, without re-running.
- **92% file-size shrink** — `deep_analysis_pipeline.py` went from 1,209 → 99 lines; complexity is distributed across focused single-responsibility modules.
- **TrustBanner honesty** — The report banner is computed from ledger data, not from self-reported crew status. A crew cannot claim success if its `StageResult` says `FAILED`.
- **Amber badge for partial results** — Users see "Insight IA indisponible" when AI returned nothing; they can still trust the Python quantitative scores, just not the narrative.
- **Regression test** — v0.3.0 silent-success class is pinned as a failing test (`tests/regression/test_v030_silent_success.py`); any future regression will be caught immediately.

### Negative

- **More files** — 10 stage modules + 2 schema files replace 1 monolith. Navigating the analysis layer now requires knowing which module owns which stage.
- **Test boundary shift** — Tests must mock at the inner-function boundary (e.g., `stages.qualify._call_ai_crew`) rather than module-level functions. Mocking the pipeline entry point no longer bypasses stage logic.
- **`@stage` decorator overhead** — Each stage invocation now writes a JSONL record and checks timeout; for micro-benchmarks this adds ~1ms per stage. Negligible for real portfolio runs (stages take seconds).

## References

- Spec: `docs/superpowers/specs/2026-04-27-v5.1-trust-spine-design.md`
- Plan: `docs/superpowers/plans/2026-04-27-v5.1-trust-spine.md`
- `scripts/check_stage_contract.py` — AST static check
- `src/finwiz/analysis/stages/` — All stage modules
- `src/finwiz/analysis/deep_analysis_pipeline.py` — Thin orchestrator (99 lines)
- [ADR-003: AI Minimalism](ADR-003-ai-minimalism.md) — Python wins for deterministic work
- [ADR-004: Sync-First Pipeline](ADR-004-sync-first-pipeline.md) — Deterministic execution order
- [ADR-008: Options-Implied Scenario Probabilities](ADR-008-options-implied-scenario-probabilities.md) — Priority chain for probability sources
