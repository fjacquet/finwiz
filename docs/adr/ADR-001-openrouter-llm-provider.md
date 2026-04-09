# ADR-001: OpenRouter as Unified LLM Gateway

- **Status:** Accepted
- **Date:** 2025-01-15
- **Deciders:** FinWiz Core Team

## Context

FinWiz analyzes 66+ holdings across stocks, ETFs, and crypto, each requiring multiple
LLM calls for qualitative analysis. We need model flexibility across providers (OpenAI,
Anthropic, Google, Mistral) without vendor lock-in. Token limits vary per model, and cost
management is critical given the volume of analysis runs.

A unified gateway simplifies API key management, enables dynamic model switching, and
provides automatic context window management across heterogeneous model providers.

## Decision

Use OpenRouter as the unified LLM gateway via LiteLLM integration.

- Model selection is configured via environment variables: `LLM_MODEL_STANDARD`,
  `LLM_MODEL_MINI`, `LLM_MODEL_MANAGER`, `LLM_MODEL_PLANNING`.
- Middle-out context compression handles automatic token management when prompts
  approach model context limits.
- Parallel tool calls are disabled for OpenRouter models to avoid serialization issues.
- All LLM configuration is centralized in `src/finwiz/config/llm/llm_config.py`.

## Consequences

### Positive

- Single API key for all model providers.
- Model switching without code changes (env var only).
- Automatic context compression prevents token overflow errors.
- Cost visibility through OpenRouter dashboard.

### Negative

- Additional network hop adds latency to every LLM call.
- Dependency on OpenRouter availability as a third-party service.

### Risks

- OpenRouter outage affects all crews simultaneously with no automatic failover.
- Pricing markup on top of base model costs.

## References

- `src/finwiz/config/llm/llm_config.py`
- [OpenRouter documentation](https://openrouter.ai/docs)
