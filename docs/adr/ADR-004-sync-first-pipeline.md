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

## References

- `src/finwiz/analysis/deep_analysis_pipeline.py`
- `src/finwiz/flows/orchestrator.py`
