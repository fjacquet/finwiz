# ADR-004: Synchronous-First Analysis Pipeline

- **Status:** Accepted
- **Date:** 2025-01-25
- **Deciders:** FinWiz Core Team

## Context

Financial calculations require deterministic execution order. The analysis pipeline flows
through data collection, quantitative scoring, qualitative AI analysis, and synthesis --
each stage depending on the output of the previous one. Async execution introduces
non-determinism that makes debugging difficult and can produce inconsistent results
in scoring pipelines. Traceability is critical for financial analysis where users must
understand how a recommendation was derived.

## Decision

The Python analysis pipeline is strictly synchronous. Async is used only where appropriate.

- The core pipeline (`collect` -> `calculate` -> `generate` -> `synthesize`) runs
  synchronously with deterministic ordering.
- Async execution is permitted only at the CrewAI task level (`async_execution: true`
  in YAML) for I/O-bound operations within a single crew.
- Flow orchestration in `FinwizFlow` delegates to synchronous orchestrators.
- Each pipeline stage completes fully before the next begins.

## Consequences

### Positive

- Deterministic, reproducible results across runs with identical inputs.
- Straightforward debugging with standard stack traces and logging.
- Simple error handling -- exceptions propagate naturally up the call stack.
- Testable with standard pytest without async fixtures or event loop management.

### Negative

- No parallelism in the Python pipeline; holdings are processed sequentially.
- Slower wall-clock time for large portfolios (66+ holdings).

### Risks

- Sequential processing is mitigated by batch data prefetch at the collection stage.
- If portfolio size grows significantly, may need to revisit with per-holding parallelism.

## Correction Note (2026-08-16)

The implementation has diverged from the "synchronous-first" decision described above;
this note records the drift without editing the original decision text.

- **Async is no longer confined to the CrewAI task level.** The qualify stage runs the
  qualitative crew and the strategic Perplexity research concurrently on a
  `ThreadPoolExecutor(max_workers=2)`, and each crew call itself is dispatched via
  `asyncio.run` (or a thread pool when a loop is already running).
  See `src/finwiz/analysis/stages/qualify.py:97-112,266-268`.
- **Holdings are not processed sequentially.** The production path,
  `DeepAnalysisOrchestrator.run_deep_analysis_concurrent`, analyzes holdings concurrently
  on an asyncio loop with a `Semaphore(max_workers)` over a
  `ThreadPoolExecutor(max_workers * 2)`, where `max_workers` comes from
  `DEEP_ANALYSIS_BATCH_SIZE` (default 5). See
  `src/finwiz/orchestrators/deep_analysis_orchestrator.py:248,443,476,504`.

The "Negative" consequence and the "No parallelism" framing above should be read as
historical context for the original decision, not as a description of current behavior.

## References

- `src/finwiz/analysis/deep_analysis_pipeline.py`
- `src/finwiz/flows/orchestrator.py`
