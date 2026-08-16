# ADR-005: Reasoning Models Disabled by Default

- **Status:** Accepted, but **not reflected in the current codebase** — see note below
- **Date:** 2025-03-01
- **Deciders:** FinWiz Core Team

> **2026-08 note:** This decision does not match current code.
> `reasoning=True` is set on 27 agent definitions across six crews (vs. 6
> `reasoning=False`), and reasoning effort is applied by default via
> `LLM_REASONING_EFFORT` (default `"low"`, not disabled). Left as a
> historical record of the original rationale; treat the "Decision" section
> below as **not current**.

## Context

Modern LLMs offer extended thinking/reasoning capabilities (DeepSeek V3.2, Grok 4.x,
Gemini 3 Flash, Claude Opus 4.5) that improve output quality for complex tasks. However,
reasoning mode consumes 2-3x more tokens per call. With 66+ holdings analyzed per run and
multiple crew calls per holding, the cumulative token cost is a primary concern. The
AI minimalism strategy (ADR-003) already limits AI to qualitative tasks, reducing the
need for deep reasoning on most calls.

## Decision

Disable reasoning/thinking mode by default on all crew agents.

- `reasoning=False` was intended as the default on all crew agent configurations.
- Thinking capability is configurable via the `LLM_REASONING_EFFORT`
  environment variable (`low`/`medium`/`high`/`none`; default `"low"`) — not
  `LLM_THINKING_LEVEL`, which does not exist. Reasoning effort is applied by
  default, not disabled.
- `max_reasoning_attempts=3` acts as a safety guard when reasoning is explicitly enabled.
- The LLM config layer resolves the effort level via `_resolve_reasoning_effort()`
  and applies parameters through `_get_reasoning_params()` /
  `_apply_reasoning_effort()` — not `_is_thinking_capable()` /
  `_get_thinking_params()`, which don't exist in this file or anywhere else
  in the codebase.

## Consequences

### Positive

- 2-3x token savings per crew call compared to reasoning-enabled mode.
- Faster execution -- no extended thinking latency.
- Lower per-run cost, critical for daily portfolio analysis workflows.

### Negative

- May miss complex reasoning patterns that require multi-step logical chains.
- Qualitative insights may be shallower without extended thinking.

### Risks

- Quality reduction for edge cases requiring deep reasoning (e.g., complex SEC filings).
- Can be mitigated by selectively enabling reasoning for specific crews if needed.

## References

- `src/finwiz/config/llm/llm_config.py` (`_resolve_reasoning_effort`, `_get_reasoning_params`, `_apply_reasoning_effort`)
- ADR-003 (AI Minimalism)
