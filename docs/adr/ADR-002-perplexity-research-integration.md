# ADR-002: Perplexity Research Integration

- **Status:** Accepted
- **Date:** 2025-02-01
- **Deciders:** FinWiz Core Team

## Context

AI-driven financial analysis requires current market data that extends beyond LLM training
data cutoff dates. Real-time news, SEC filings, earnings reports, and market sentiment
cannot be reliably sourced from static model knowledge. Web search capability fills this
gap but must be optional and fault-tolerant to avoid blocking the analysis pipeline.

## Decision

Integrate Perplexity API for real-time research, gated behind a feature flag.

- Feature flag `PERPLEXITY_RESEARCH_ENABLED` controls activation via
  `src/finwiz/config/features/definitions.py`.
- Circuit breaker pattern provides graceful degradation when the API is unavailable.
- Dedicated Pydantic schemas in `src/finwiz/schemas/perplexity.py` define response models.
- Research results are injected into crew context alongside Python-collected data.

## Consequences

### Positive

- Access to current market data, news, and SEC filings beyond LLM training cutoff.
- Configurable via feature flag -- no code changes needed to enable/disable.
- Graceful fallback when Perplexity is unavailable; analysis continues without it.

### Negative

- Additional per-query API cost on top of LLM costs.
- Another API key (`PERPLEXITY_API_KEY`) to manage and rotate.

### Risks

- Rate limiting under heavy load (66+ holdings queried in rapid succession).
- Perplexity API contract changes could break integration.

## Correction Note (2026-08-16)

The feature flag name in the Decision above does not match the code and never has: the
flag is registered as `perplexity_research` and is driven by the env var
`FF_PERPLEXITY_RESEARCH` (default `True`), not `PERPLEXITY_RESEARCH_ENABLED`. The circuit
breaker thresholds are also configurable via `FF_PERPLEXITY_BREAKER_THRESHOLD` and
`FF_PERPLEXITY_BREAKER_TIMEOUT`. See `src/finwiz/config/features/definitions.py:178-186`.

## References

- `src/finwiz/tools/perplexity_analysis_integration.py`
- `src/finwiz/config/features/definitions.py`
- `src/finwiz/schemas/perplexity.py`
