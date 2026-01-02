# LLM Model Analysis for FinWiz (January 2025)

This document analyzes the best LLM models available via OpenRouter for the FinWiz financial analysis platform.

## Model Selection Criteria

For FinWiz, we prioritize:
1. **JSON Output Quality** - Structured outputs are critical for crew communication
2. **Tool Calling Reliability** - Agents need reliable function calling
3. **Financial Domain Knowledge** - Understanding of finance terminology
4. **Cost Efficiency** - Balance quality with operational costs
5. **Native Thinking** - Modern models with built-in reasoning capabilities

## Analyzed Models

### Tier 1: Premium Quality

#### Claude Opus 4.5 (`openrouter/anthropic/claude-opus-4.5`)
- **SWE-bench Score**: 80.9% (highest available)
- **Context**: 200K tokens
- **Strengths**:
  - Best overall quality and reasoning
  - Extended thinking with configurable budget
  - 50-75% fewer tool calling errors
  - 76% fewer tokens than Sonnet for same tasks
- **Cost**: $15/$75 per 1M tokens (input/output)
- **Thinking Mode**: `thinking` param with `thinking_budget` (1K-16K tokens)
- **Best For**: Manager, Planning, high-value decisions

#### Grok 4.1 Fast (`openrouter/x-ai/grok-4.1-fast`)
- **Context**: 2M tokens (largest available)
- **Strengths**:
  - Finance domain expertise (trained on financial data)
  - Excellent structured output support
  - Very large context for portfolio analysis
  - Fast inference
- **Cost**: ~$5/$15 per 1M tokens
- **Thinking Mode**: `reasoning` toggle (on/off)
- **Best For**: Standard analysis, financial research

### Tier 2: Cost-Effective Excellence

#### DeepSeek V3.2 (`openrouter/deepseek/deepseek-v3.2`)
- **Context**: 128K tokens
- **Strengths**:
  - Native JSON mode with validation
  - Native thinking + tool calling combined
  - Extremely cost-effective
  - Excellent structured outputs
- **Cost**: ~$0.14/$0.28 per 1M tokens
- **Thinking Mode**: `enable_thinking` (boolean)
- **Best For**: Baseline, high-volume tasks, JSON generation

#### Gemini 3 Flash Preview (`openrouter/google/gemini-3-flash-preview`)
- **Context**: 1M tokens
- **Strengths**:
  - 3x faster than Gemini 2.5 Pro
  - Configurable thinking levels
  - Excellent JSON output
  - Deterministic outputs available
- **Cost**: ~$0.10/$0.40 per 1M tokens
- **Thinking Mode**: `thinking_level` (minimal, low, medium, high)
- **Best For**: Mini model, performance-optimized operations

### Tier 3: Free/Budget Options

#### Mistral Devstral 2512 (`openrouter/mistralai/devstral-2512:free`)
- **Context**: 256K tokens
- **Cost**: FREE
- **Strengths**: Good coding, large context
- **Best For**: Development, testing, budget scenarios

#### Xiaomi MiMo-V2-Flash (`openrouter/xiaomi/mimo-v2-flash:free`)
- **SWE-bench Score**: 73.4%
- **Speed**: 150 tokens/sec (fastest open source)
- **Cost**: FREE
- **Best For**: Ultra-fast inference, budget mini model

#### OpenAI GPT-OSS-20B (`openrouter/openai/gpt-oss-20b`)
- **RAM Required**: 16GB
- **Cost**: Very low
- **Best For**: Local deployment scenarios

## Configuration Options

### Option A: Performance + Cost Optimal
```bash
LLM_MODEL_STANDARD=openrouter/deepseek/deepseek-v3.2
LLM_MODEL_MINI=openrouter/google/gemini-3-flash-preview
LLM_MODEL_MANAGER=openrouter/deepseek/deepseek-v3.2
LLM_MODEL_PLANNING=openrouter/x-ai/grok-4.1-fast
LLM_MODEL_BASELINE=openrouter/mistralai/devstral-2512:free
LLM_MODEL_THINKING=openrouter/x-ai/grok-4.1-fast
```
**Estimated Cost**: $0.50-2/day for typical usage

### Option B: Quality Maximum (Recommended)
```bash
LLM_MODEL_STANDARD=openrouter/x-ai/grok-4.1-fast
LLM_MODEL_MINI=openrouter/google/gemini-3-flash-preview
LLM_MODEL_MANAGER=openrouter/anthropic/claude-opus-4.5
LLM_MODEL_PLANNING=openrouter/anthropic/claude-opus-4.5
LLM_MODEL_BASELINE=openrouter/deepseek/deepseek-v3.2
LLM_MODEL_THINKING=openrouter/anthropic/claude-opus-4.5
```
**Estimated Cost**: $5-15/day for typical usage

### Option C: Budget Minimal
```bash
LLM_MODEL_STANDARD=openrouter/deepseek/deepseek-v3.2
LLM_MODEL_MINI=openrouter/xiaomi/mimo-v2-flash:free
LLM_MODEL_MANAGER=openrouter/mistralai/devstral-2512:free
LLM_MODEL_PLANNING=openrouter/deepseek/deepseek-v3.2
LLM_MODEL_BASELINE=openrouter/mistralai/devstral-2512:free
LLM_MODEL_THINKING=openrouter/deepseek/deepseek-v3.2
```
**Estimated Cost**: $0.05-0.50/day

## Native Thinking Mode Support

Modern LLMs have native "thinking" capabilities that differ from CrewAI's `reasoning=True`:

| Mechanism | What it does | Cost |
|-----------|--------------|------|
| CrewAI `reasoning=True` | Multiple LLM calls with self-critique | 2-3x normal cost |
| Native Thinking | Internal reasoning tokens in single call | 1.2-2x normal cost |

### Model-Specific Thinking Parameters

| Model | Parameter | Values |
|-------|-----------|--------|
| DeepSeek V3.x | `enable_thinking` | `true`/`false` |
| Grok 4.x | `reasoning` | `true`/`false` |
| Gemini 3 | `thinking_level` | `minimal`, `low`, `medium`, `high` |
| Claude Opus 4.5 | `thinking` + `thinking_budget` | `enabled` + token count |

### Thinking Level Guidelines

- **off**: Fastest, cheapest - use for simple formatting tasks
- **low**: Light reasoning - basic analysis, data extraction
- **medium**: Balanced (default) - standard analysis
- **high**: Maximum reasoning - portfolio rebalancing, complex decisions

## Use Case Recommendations

| Use Case | Recommended Model | Why |
|----------|-------------------|-----|
| Portfolio Rebalancing | Claude Opus 4.5 | Best reasoning, fewer errors |
| Stock Analysis | Grok 4.1 Fast | Finance expertise, large context |
| ETF Analysis | Grok 4.1 Fast | Finance expertise |
| Crypto Analysis | DeepSeek V3.2 | Good JSON, cost-effective |
| Manager Coordination | Claude Opus 4.5 | Best coordination |
| Planning | Claude Opus 4.5 | Optimal token usage |
| Mini/Fast Tasks | Gemini 3 Flash | Speed + quality |
| Baseline/Comparison | DeepSeek V3.2 | Excellent JSON mode |
| High-Value Decisions | Claude Opus 4.5 with high thinking | Best quality |

## Cost Comparison (per 1M tokens)

| Model | Input | Output | Thinking |
|-------|-------|--------|----------|
| Claude Opus 4.5 | $15 | $75 | +$15-75 |
| Grok 4.1 Fast | $5 | $15 | +$5-15 |
| Gemini 3 Flash | $0.10 | $0.40 | +$0.05-0.20 |
| DeepSeek V3.2 | $0.14 | $0.28 | +$0.07-0.14 |
| Devstral 2512 | FREE | FREE | N/A |
| MiMo-V2-Flash | FREE | FREE | N/A |

## Implementation Notes

The `llm_config.py` module now includes:

1. **Model Capabilities Registry** - Tracks which models support thinking
2. **`get_thinking_llm()`** - Returns LLM configured for high-value tasks
3. **`is_model_thinking_capable()`** - Check if model supports native thinking
4. **`get_model_capabilities()`** - Get full capability summary

### Environment Variables

```bash
# Standard model configuration
LLM_MODEL_STANDARD=openrouter/x-ai/grok-4.1-fast
LLM_MODEL_MINI=openrouter/google/gemini-3-flash-preview
LLM_MODEL_MANAGER=openrouter/anthropic/claude-opus-4.5
LLM_MODEL_PLANNING=openrouter/anthropic/claude-opus-4.5
LLM_MODEL_BASELINE=openrouter/deepseek/deepseek-v3.2

# Thinking configuration
LLM_MODEL_THINKING=openrouter/anthropic/claude-opus-4.5
LLM_THINKING_LEVEL=medium  # off, low, medium, high
```

## Future Considerations

1. **Dynamic Model Selection** - Auto-select model based on task complexity
2. **Cost Tracking** - Monitor spending per model type
3. **Quality Metrics** - Track JSON validity rates per model
4. **Fallback Chains** - Automatic fallback on rate limits

---

*Analysis performed: January 2025*
*OpenRouter API used for model access*
