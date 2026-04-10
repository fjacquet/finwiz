# ADR-007: Token Consumption Optimization

- **Status:** Accepted
- **Date:** 2026-04-09
- **Deciders:** FinWiz Core Team

## Context

After ADR-006 (context scoping), per-crew token usage was under control, but aggregate
consumption across 7 crews remained excessive due to:

1. **Prompt boilerplate repetition** -- "JSON OUTPUT REQUIREMENTS" (~150 tokens) repeated 33x
   across all `tasks.yaml` files. "ANTI-HALLUCINATION RULES" (~250 tokens) repeated 11x.
   "Read the schema file" instructions (8x) that triggered unnecessary FileReadTool calls.
2. **Verbose agent backstories** -- 80-150 word backstories per agent (25+ agents) when 15
   words suffice (deep_analysis crew already proved this).
3. **No LLM response caps** -- `max_tokens` was never set on `LLM()`, allowing unbounded
   rambling responses.
4. **No pre-call guardrails** -- Token overflow was detected after failure, not prevented.

## Decision

Apply four optimization layers:

1. **Prompt pruning (~10K tokens saved)**
   - Move shared output rules from `tasks.yaml` to `agents.yaml` goal fields (deduplicate 33
     JSON blocks + 11 anti-hallucination blocks).
   - Compress agent backstories to ~15 words (following deep_analysis gold standard).
   - Remove "Read the schema file" instructions -- `output_pydantic` already enforces schemas.
   - Remove redundant JSON output examples where `output_pydantic` is set.

2. **LLM response caps (max_tokens)**
   - Standard: 2048, Mini: 1024, Manager: 1024, Planning: 2048, Baseline: 4096.
   - Deep analysis crew overrides to 6144 (structured JSON output needs ~1500-2000 words;
     raised from 4096 after observing `investment_synthesis` truncation under token pressure).
   - Configurable via `LLM_MAX_TOKENS` environment variable.
   - Cache key includes `max_tokens` to prevent wrong-limit cache hits.

3. **QualitativeInsights field ordering** (`schemas/hybrid_analysis/qualitative.py`)

   `investment_synthesis` moved to first position. LLMs generate fields in schema order;
   placing the most user-visible section first guarantees it is filled before earlier
   sections exhaust the token budget. Zero runtime cost — field access by name is
   unaffected by declaration order.

4. **Schema resilience**
   - `SecAnalysisInsights.risk_factors` field_validator coerces dict entries
     (e.g. `{'risk': '...', 'severity': '...'}`) to plain strings.

5. **Observability**
   - Pre-call token estimation guard in LiteLLM callback (configurable `MAX_PROMPT_TOKENS`).
   - CrewAI `usage_metrics` logged after each crew execution.

### Evaluated and deferred

- **CrewAI Memory**: Evaluated via Context7. `memory=False` remains intentional -- memory
  adds LLM calls for scope inference and risks token overflow from accumulated stores.
- **`kickoff_for_each()` batching**: Evaluated. Deep analysis crew is already optimized
  (1 agent, 1 task, concurrent via ThreadPoolExecutor). Batching would not reduce tokens
  because each holding needs unique context.

## Consequences

### Positive

- ~10K tokens of prompt boilerplate eliminated per pipeline run.
- LLM responses bounded, preventing unbounded rambling and cost overruns.
- Token overflow detected before API call failure via pre-call guard.
- Usage metrics visible per crew for ongoing cost monitoring.

### Negative

- Compressed backstories provide less "persona context" to agents (acceptable -- agent
  behavior is primarily driven by task descriptions, not backstories).
- `max_tokens=2048` may truncate unexpectedly long responses for standard crews (mitigated
  by env var override).

### Risks

- Deep analysis `max_tokens=4096` may still be insufficient if task prompts grow.
  Monitor via `usage_metrics` and adjust as needed.

## References

- `src/finwiz/config/llm/llm_config.py` (max_tokens defaults, cache key)
- `src/finwiz/crews/deep_analysis/deep_analysis.py` (max_tokens=4096 override)
- `src/finwiz/schemas/hybrid_analysis/qualitative.py` (risk_factors field_validator)
- `src/finwiz/infrastructure/monitoring/litellm_callback.py` (pre-call guard)
- `src/finwiz/crew_factory.py` (usage_metrics logging)
- ADR-006: Context Scoping Strategy (predecessor)
