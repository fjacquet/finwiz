# LLM Configuration Guide

## Overview

FinWiz now supports flexible LLM model configuration through environment variables. You can easily switch between different models without modifying code.

## Environment Variables

Configure different models for different purposes in your `.env` file:

```bash
# Standard Model - Used for general crew operations and analysis
LLM_MODEL_STANDARD=openai/gpt-4o-mini

# Mini Model - Used for performance-optimized operations (maximum speed mode)
LLM_MODEL_MINI=openai/gpt-4o-mini

# Manager Model - Used for crew manager operations
LLM_MODEL_MANAGER=openai/gpt-4o-mini

# Planning Model - Used for crew planning operations
LLM_MODEL_PLANNING=openai/gpt-4o-mini

# Baseline Model - Used for baseline/comparison operations
LLM_MODEL_BASELINE=openai/gpt-4o

# Fallback - Used if specific models not set
MODEL=openai/gpt-4o-mini

# Timeout configuration
OPENAI_TIMEOUT=300
```

## Response Length Limits (max_tokens)

Each model type has a default `max_tokens` cap to prevent unbounded output:

| Model Type | Default max_tokens | Use Case |
|------------|-------------------|----------|
| mini | 1024 | Fast, high-volume operations |
| manager | 1024 | Crew coordination |
| standard | 2048 | General analysis |
| planning | 2048 | Strategic planning |
| baseline | 4096 | Quality benchmarking |

Override globally via environment variable:

```bash
LLM_MAX_TOKENS=3000  # Override default for all model types
```

Override per-call in code:

```python
llm = get_configured_llm(model_type="standard", max_tokens=4096)
```

The deep analysis crew uses `max_tokens=4096` because its structured JSON output requires 1500-2000 words.

### Pre-call Token Guard

A configurable guard logs errors when estimated prompt tokens exceed the threshold:

```bash
MAX_PROMPT_TOKENS=100000  # Default: 100K tokens
```

## Supported Model Formats

Use the LiteLLM format: `provider/model-name`

### Examples

**OpenAI:**

```bash
LLM_MODEL_STANDARD=openai/gpt-4o
LLM_MODEL_MINI=openai/gpt-4o-mini
```

**Anthropic Claude:**

```bash
LLM_MODEL_STANDARD=anthropic/claude-3-5-sonnet-20241022
LLM_MODEL_MINI=anthropic/claude-3-haiku-20240307
```

**Google Gemini:**

```bash
LLM_MODEL_STANDARD=gemini/gemini-pro
LLM_MODEL_MINI=gemini/gemini-flash-lite-latest
```

**Mistral:**

```bash
LLM_MODEL_STANDARD=mistral/mistral-large-latest
LLM_MODEL_MINI=mistral/mistral-small-latest
```

## Model Types Explained

### Standard Model (`LLM_MODEL_STANDARD`)

- Used for general crew operations
- Default for most analysis tasks
- Balance between performance and cost

### Mini Model (`LLM_MODEL_MINI`)

- Used in maximum speed optimization mode
- Faster and cheaper operations
- Suitable for high-volume processing

### Manager Model (`LLM_MODEL_MANAGER`)

- Used for crew manager operations
- Coordinates multi-agent workflows
- Can be same as standard or more powerful

### Planning Model (`LLM_MODEL_PLANNING`)

- Used for crew planning operations
- Strategic decision-making
- Can be same as standard or more powerful

### Baseline Model (`LLM_MODEL_BASELINE`)

- Used for comparison and baseline operations
- Typically a more powerful model
- Used for quality benchmarking

## Usage Examples

### Example 1: Cost Optimization

Use cheaper models for most operations:

```bash
LLM_MODEL_STANDARD=openai/gpt-4o-mini
LLM_MODEL_MINI=openai/gpt-4o-mini
LLM_MODEL_MANAGER=openai/gpt-4o-mini
LLM_MODEL_PLANNING=openai/gpt-4o-mini
LLM_MODEL_BASELINE=openai/gpt-4o
```

### Example 2: Performance Optimization

Use fast models for speed:

```bash
LLM_MODEL_STANDARD=gemini/gemini-flash-lite-latest
LLM_MODEL_MINI=gemini/gemini-flash-lite-latest
LLM_MODEL_MANAGER=gemini/gemini-flash-lite-latest
LLM_MODEL_PLANNING=gemini/gemini-flash-lite-latest
LLM_MODEL_BASELINE=openai/gpt-4o
```

### Example 3: Quality Focus

Use powerful models for best results:

```bash
LLM_MODEL_STANDARD=anthropic/claude-3-5-sonnet-20241022
LLM_MODEL_MINI=anthropic/claude-3-haiku-20240307
LLM_MODEL_MANAGER=anthropic/claude-3-5-sonnet-20241022
LLM_MODEL_PLANNING=anthropic/claude-3-5-sonnet-20241022
LLM_MODEL_BASELINE=openai/gpt-4o
```

## Programmatic Usage

### Using Specific Model Types

```python
from finwiz.utils.llm_config import (
    get_configured_llm,
    get_mini_llm,
    get_manager_llm,
    get_planning_llm,
    get_baseline_llm
)

# Get standard model
standard_llm = get_configured_llm(model_type="standard")

# Get mini model for performance
mini_llm = get_mini_llm()

# Get manager model
manager_llm = get_manager_llm()

# Get planning model
planning_llm = get_planning_llm()

# Get baseline model
baseline_llm = get_baseline_llm()
```

### Override with Specific Model

```python
# Override with specific model
custom_llm = get_configured_llm(model_override="anthropic/claude-3-opus-20240229")
```

## Performance Configuration Integration

The LLM configuration works seamlessly with FinWiz's performance optimization modes:

```python
from finwiz.utils.performance_config import OptimizationMode, get_performance_config_manager

# Set optimization mode
perf_config = get_performance_config_manager()
perf_config.set_mode(OptimizationMode.MAXIMUM_SPEED)

# Crews will automatically use mini model in maximum speed mode
```

## Troubleshooting

### Model Not Found

If you get a "model not found" error:

1. Check the model name format: `provider/model-name`
2. Verify the model is available for your API key
3. Check API key is set: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc.

### Timeout Issues

If operations timeout:

```bash
# Increase timeout (in seconds)
OPENAI_TIMEOUT=600
```

### Cost Concerns

Monitor costs by:

1. Using mini models for high-volume operations
2. Setting `LLM_MODEL_MINI` to cheapest available model
3. Enabling maximum speed mode for batch processing

## Migration from Hardcoded Models

### Before (Hardcoded)

```python
llm = LLM(
    model="openai/gpt-4o-mini",
    timeout=300,
    max_retries=3,
)
```

### After (Environment-Driven)

```python
from finwiz.utils.llm_config import get_configured_llm

llm = get_configured_llm(model_type="standard")
```

## Best Practices

1. **Set all model types** in `.env` for consistency
2. **Use mini models** for high-volume operations
3. **Test with different models** to find optimal cost/performance balance
4. **Monitor costs** when using premium models
5. **Keep baseline model powerful** for quality comparisons
6. **Document model choices** in your deployment configuration

## See Also

- [Performance Configuration](how-to/performance_optimization.md)
- [Environment Variables](reference/environment_variables.md)
- CrewAI Standards (.kiro/steering/crewai-standards.md in project root)
