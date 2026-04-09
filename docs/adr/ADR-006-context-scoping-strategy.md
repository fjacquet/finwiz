# ADR-006: Context Scoping Strategy

- **Status:** Accepted
- **Date:** 2025-02-15
- **Deciders:** FinWiz Core Team

## Context

CrewAI injects the full raw output of upstream tasks into downstream task prompts via the
`context:` parameter. With 5-6 task chains per crew, accumulated context reached
200K-335K tokens, causing overflow errors and costs exceeding $1 per crew run. Memory
accumulation across crew runs compounded the problem, with memory stores growing to 968KB+.

## Decision

Apply multiple context scoping strategies to control token usage in crew inputs.

1. **Summarized inputs**: `_build_crew_inputs()` summarizes Python metrics to top-N items
   as formatted strings, not raw dicts.
2. **Text truncation**: `_truncate_text()` caps large text fields to 500 characters.
3. **Memory disabled**: `memory=False` on all 6 crews to prevent accumulated memory bloat.
4. **Context window respect**: `respect_context_window=True` on all crews enables
   automatic truncation at the framework level.
5. **Task removal**: Removed `generate_enriched_analysis_task` from the deep analysis
   crew -- Python synthesis replaces AI-driven consolidation.
6. **Token monitoring**: LiteLLM callback alerts when estimated tokens exceed 100K.

## Consequences

### Positive

- Crew inputs reduced to ~500 tokens vs 100K+ for raw dictionary serialization.
- Predictable and controllable per-run costs.
- Token monitoring provides early warning before overflow errors occur.

### Negative

- AI may miss details that were present in unsummarized raw metrics.
- Top-N summarization requires manual tuning per metric type.

### Risks

- Over-aggressive summarization could omit critical data points for edge-case holdings.
- Tuning top-N values requires periodic review as portfolio composition changes.

## References

- `src/finwiz/analysis/deep_analysis_pipeline.py` (`_build_crew_inputs`, `_summarize_metrics`, `_truncate_text`)
- `src/finwiz/infrastructure/monitoring/litellm_callback.py`
