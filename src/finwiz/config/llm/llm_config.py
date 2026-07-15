"""
LLM Configuration Utility for FinWiz.

Provides centralized LLM configuration with proper parameter handling
for CrewAI integration. All models are configurable via environment variables.

Supports modern "thinking" models with native reasoning capabilities:
- DeepSeek V3.2: Native thinking mode for complex reasoning
- Grok 4.x: Reasoning/non-reasoning modes
- Gemini 3 Flash: Configurable thinking_level (minimal, low, medium, high)
- Claude Opus 4.5: Extended thinking capabilities

Environment Variables:
    LLM_MODEL_STANDARD: Standard model for general operations
    LLM_MODEL_MINI: Mini model for performance-optimized operations
    LLM_MODEL_MANAGER: Manager model for crew management
    LLM_MODEL_PLANNING: Planning model for crew planning
    LLM_MODEL_BASELINE: Baseline model for comparison operations
    LLM_MODEL_THINKING: Model for high-value reasoning tasks (defaults to PLANNING)
    LLM_THINKING_LEVEL: Thinking intensity (off, low, medium, high) - default: medium
    MODEL: Fallback model if specific models not set
    OPENAI_TIMEOUT: Timeout in seconds (default: 300)
"""

import os
from typing import Any

import litellm
from crewai import LLM
from dotenv import load_dotenv

from finwiz.tools.logger import get_logger

# Load environment variables
load_dotenv()

logger = get_logger(__name__)

# Module-level litellm retry policy for transient errors. CrewAI's LLM class
# doesn't expose num_retries on its constructor, so we set it on the litellm
# module — it applies to every litellm.completion call made by any CrewAI LLM
# instance. Catches OpenRouter mid-stream drops (RemoteProtocolError /
# "incomplete chunked read") and APIError 502/503/504 with built-in
# exponential backoff. Tunable via LLM_NUM_RETRIES (default: 3).
#
# This module-level setting is the only retry layer: the former
# tools/crewai_retry_patch.py (initialize_retry_mechanism) was a documented
# no-op — its `Agent._get_llm` patch target no longer exists in installed
# CrewAI — and was deleted along with tools/llm_retry.py.
_DEFAULT_LLM_NUM_RETRIES = 3


def _parse_num_retries() -> int:
    """Safely parse LLM_NUM_RETRIES. Empty/invalid -> default; never raises."""
    raw = os.getenv("LLM_NUM_RETRIES", "").strip()
    if not raw:
        return _DEFAULT_LLM_NUM_RETRIES
    try:
        value = int(raw)
    except ValueError:
        # Don't crash module import on a typo'd env value (e.g. LLM_NUM_RETRIES=foo).
        # Logger isn't initialized yet at this point, so use a print warning.
        print(f"[llm_config] Invalid LLM_NUM_RETRIES={raw!r}, falling back to {_DEFAULT_LLM_NUM_RETRIES}")
        return _DEFAULT_LLM_NUM_RETRIES
    return max(0, value)  # Clamp negatives to 0 (litellm treats <=0 as "no retries")


litellm.num_retries = _parse_num_retries()


# =============================================================================
# Model Capabilities Registry
# =============================================================================

# Models with native thinking/reasoning capabilities
THINKING_CAPABLE_MODELS = {
    # DeepSeek models with native thinking
    "deepseek-v3.2": {"thinking_param": "enable_thinking", "default_value": True},
    "deepseek-v3": {"thinking_param": "enable_thinking", "default_value": True},
    # Grok models with reasoning mode
    "grok-4": {"thinking_param": "reasoning", "supports_toggle": True},
    "grok-4.1": {"thinking_param": "reasoning", "supports_toggle": True},
    "grok-4-fast": {"thinking_param": "reasoning", "supports_toggle": True},
    "grok-4.1-fast": {"thinking_param": "reasoning", "supports_toggle": True},
    # Gemini models with thinking_level
    "gemini-3-flash": {"thinking_param": "thinking_level", "levels": ["minimal", "low", "medium", "high"]},
    "gemini-3-flash-preview": {"thinking_param": "thinking_level", "levels": ["minimal", "low", "medium", "high"]},
    "gemini-3-pro": {"thinking_param": "thinking_level", "levels": ["minimal", "low", "medium", "high"]},
    # Claude models with extended thinking
    "claude-opus-4.5": {"thinking_param": "thinking", "budget_param": "thinking_budget"},
    "claude-sonnet-4.5": {"thinking_param": "thinking", "budget_param": "thinking_budget"},
}

# Models with excellent JSON/structured output support
JSON_RELIABLE_MODELS = [
    "deepseek-v3.2",
    "deepseek-v3",
    "gemini-3-flash",
    "gemini-3-flash-preview",
    "grok-4",
    "grok-4.1",
    "grok-4-fast",
    "grok-4.1-fast",
    "claude-opus-4.5",
    "claude-sonnet-4.5",
]


def _get_model_short_name(model: str) -> str:
    """
    Extract the short model name from a full model path.

    Args:
        model: Full model path (e.g., "openrouter/x-ai/grok-4.1-fast")

    Returns:
        Short model name (e.g., "grok-4.1-fast")
    """
    # Handle openrouter format: openrouter/provider/model-name
    parts = model.split("/")
    if len(parts) >= 3 and parts[0] == "openrouter":
        return parts[-1]  # Return last part (model name)
    elif len(parts) >= 2:
        return parts[-1]  # Return last part
    return model


def _is_thinking_capable(model: str) -> bool:
    """Check if a model has native thinking capabilities."""
    short_name = _get_model_short_name(model)
    return any(cap_model in short_name for cap_model in THINKING_CAPABLE_MODELS)


def _is_json_reliable(model: str) -> bool:
    """Check if a model has excellent JSON output support."""
    short_name = _get_model_short_name(model)
    return any(json_model in short_name for json_model in JSON_RELIABLE_MODELS)


def _get_thinking_params(model: str, thinking_level: str = "medium") -> dict[str, Any]:
    """
    Get model-specific thinking parameters.

    Args:
        model: Model name
        thinking_level: Thinking intensity (off, low, medium, high)

    Returns:
        Dict of thinking parameters to pass to the model
    """
    if thinking_level == "off":
        return {}

    short_name = _get_model_short_name(model)
    params: dict[str, Any] = {}

    for cap_model, config in THINKING_CAPABLE_MODELS.items():
        if cap_model in short_name:
            thinking_param = config.get("thinking_param")

            if "levels" in config:
                # Gemini-style thinking_level
                level_map = {"low": "low", "medium": "medium", "high": "high"}
                params[thinking_param] = level_map.get(thinking_level, "medium")
            elif "budget_param" in config:
                # Claude-style thinking with budget
                params[thinking_param] = {"type": "enabled"}
                # Budget in tokens: low=1024, medium=4096, high=16384
                budget_map = {"low": 1024, "medium": 4096, "high": 16384}
                params[config["budget_param"]] = budget_map.get(thinking_level, 4096)
            elif config.get("supports_toggle"):
                # Grok-style reasoning toggle
                params[thinking_param] = True
            else:
                # DeepSeek-style enable_thinking
                params[thinking_param] = config.get("default_value", True)

            break

    return params


# =============================================================================
# LLM Instance Cache
# =============================================================================

# Cache for LLM instances to avoid repeated initialization
_llm_cache: dict[str, LLM] = {}


def _get_model_from_env(env_var: str, fallback: str = "openai/gpt-4o-mini") -> str:
    """
    Get model name from environment variable with fallback chain.

    Args:
        env_var: Specific environment variable to check (e.g., "LLM_MODEL_STANDARD")
        fallback: Default model if env_var not set

    Returns:
        Model name string

    """
    # Try specific env var first, then MODEL, then fallback
    return os.getenv(env_var) or os.getenv("MODEL") or fallback


def _get_provider_from_model(model: str) -> str:
    """
    Extract provider name from model string.

    Args:
        model: Model string (e.g., "openai/gpt-4o-mini", "anthropic/claude-3")

    Returns:
        Provider name (e.g., "openai", "anthropic")

    """
    if "/" in model:
        return model.split("/")[0].lower()
    # Default to openai for models without provider prefix
    return "openai"


def _validate_api_key_for_model(model: str) -> None:
    """
    Validate that the appropriate API key exists for the model provider.

    Args:
        model: Model string to validate

    Raises:
        OSError: If required API key is missing

    """
    provider_key_map = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "google": "GOOGLE_API_KEY",
        "gemini": "GOOGLE_API_KEY",
        "mistral": "MISTRAL_API_KEY",
        "cohere": "COHERE_API_KEY",
        "azure": "AZURE_OPENAI_API_KEY",
        "groq": "GROQ_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
    }

    provider = _get_provider_from_model(model)
    required_key = provider_key_map.get(provider, "OPENAI_API_KEY")

    if not os.getenv(required_key):
        raise OSError(f"{required_key} not found in environment variables. Required for model: {model}. Please set your API key in the .env file.")


def get_configured_llm(
    model_override: str | None = None,
    model_type: str = "standard",
    max_tokens: int | None = None,
    force_json_object: bool = False,
) -> LLM:
    """
    Get a properly configured LLM instance for CrewAI.

    This function creates an LLM instance with proper parameter handling.
    Models can be configured via environment variables for easy switching.

    Args:
        model_override: Optional model name to override environment configuration
        model_type: Type of model to use ("standard", "mini", "manager", "planning", "baseline")
                   Only used if model_override is None
        force_json_object: When True, request provider-enforced JSON output via
                   ``extra_body.response_format = {"type": "json_object"}``. Use only for
                   crews whose every turn is a JSON emission (no tool calls / prose), e.g.
                   the deep-analysis qualitative crew. Routed through ``extra_body`` rather
                   than CrewAI's native ``response_format`` param because CrewAI raises for
                   providers (OpenRouter) that litellm doesn't flag as schema-capable, even
                   though OpenRouter honors response_format at the request level.

    Returns:
        LLM: Configured LLM instance ready for CrewAI use

    Raises:
        EnvironmentError: If required API keys are missing

    Environment Variables:
        LLM_MODEL_STANDARD: Standard model (default: openai/gpt-4o-mini)
        LLM_MODEL_MINI: Mini model for performance (default: openai/gpt-4o-mini)
        LLM_MODEL_MANAGER: Manager model (default: openai/gpt-4o-mini)
        LLM_MODEL_PLANNING: Planning model (default: openai/gpt-4o-mini)
        LLM_MODEL_BASELINE: Baseline model (default: openai/gpt-4o)
        MODEL: Fallback if specific model not set
        OPENAI_TIMEOUT: Timeout in seconds (default: 300)

    """
    # Determine which model to use
    if model_override:
        model = model_override
    else:
        # Map model_type to environment variable
        model_env_map = {
            "standard": "LLM_MODEL_STANDARD",
            "mini": "LLM_MODEL_MINI",
            "manager": "LLM_MODEL_MANAGER",
            "planning": "LLM_MODEL_PLANNING",
            "baseline": "LLM_MODEL_BASELINE",
        }

        env_var = model_env_map.get(model_type, "LLM_MODEL_STANDARD")

        # Get appropriate fallback based on model type
        fallback = "openai/gpt-4o" if model_type == "baseline" else "openai/gpt-4o-mini"
        model = _get_model_from_env(env_var, fallback)

    # Check cache first (include max_tokens + json mode so callers with different needs get distinct instances)
    cache_key = f"{model}:{model_type}:{max_tokens}:json={force_json_object}"
    if cache_key in _llm_cache:
        logger.debug(f"Returning cached LLM instance for {cache_key}")
        return _llm_cache[cache_key]

    # Validate API key for the model's provider
    _validate_api_key_for_model(model)

    # Log the model being used
    logger.info(f"Configuring LLM ({model_type}) with model: {model}")

    try:
        # Get timeout from environment (check multiple env vars for compatibility)
        timeout = int(os.getenv("LITELLM_TIMEOUT") or os.getenv("OPENAI_TIMEOUT") or "300")

        # Determine max_tokens: explicit override > env var > defaults by model type
        if max_tokens is None:
            env_max = os.getenv("LLM_MAX_TOKENS")
            if env_max:
                max_tokens = int(env_max)
            else:
                max_tokens_defaults = {
                    "standard": 20480,
                    "mini": 10240,
                    "manager": 10240,
                    "planning": 20480,
                    "baseline": 40960,
                }
                max_tokens = max_tokens_defaults.get(model_type, 20480)

        # Check if parallel tool calls should be disabled
        # Some providers (OpenRouter/Novita) + Instructor don't support parallel tool calls
        disable_parallel = os.getenv("DISABLE_PARALLEL_TOOL_CALLS", "true").lower() == "true"

        # Build extra body params
        extra_body: dict[str, Any] = {}

        # Add OpenRouter middle-out transform for automatic context compression
        # This prevents token overflow errors (e.g., 302K tokens vs 131K limit)
        if model.startswith("openrouter/"):
            extra_body["transforms"] = ["middle-out"]
            # Explicitly disable parallel tool calls for OpenRouter models
            # This is required because some models ignore the top-level parallel_tool_calls param
            # Also set tool_choice to enforce single tool execution
            if disable_parallel:
                extra_body["parallel_tool_calls"] = False
                extra_body["tool_choice"] = "auto"
            logger.info("OpenRouter middle-out transform enabled for automatic context compression")

        # Provider-enforced JSON output: eliminates markdown-fenced / malformed JSON at the
        # source. Injected via extra_body (request-level) so CrewAI's response_format guard
        # is bypassed; OpenRouter and OpenAI-compatible providers honor it. Validated live
        # against openrouter/mistralai/mistral-small-2603.
        if force_json_object:
            extra_body["response_format"] = {"type": "json_object"}
            logger.info("Provider JSON mode enabled (response_format=json_object via extra_body)")

        # Create LLM with proper configuration.
        # Note: retry on transient errors is handled at the litellm module level
        # (litellm.num_retries set at import time in this file).
        llm = LLM(
            model=model,
            timeout=timeout,
            max_tokens=max_tokens,
            # Disable parallel tool calls to avoid Instructor compatibility issues
            # See: https://github.com/BerriAI/litellm/issues/4235
            parallel_tool_calls=False if disable_parallel else None,
            # NOTE: do not pass drop_params=True here. crewai's litellm-backed LLM
            # already forces litellm.drop_params = True globally on init, so it's
            # redundant there — and for natively-routed providers (openai/, etc.)
            # crewai forwards unrecognized kwargs straight into the SDK call params,
            # so drop_params leaks into client.beta.chat.completions.parse(**params)
            # and raises TypeError: unexpected keyword argument 'drop_params'.
            # Extra params for provider-specific features
            extra_body=extra_body if extra_body else None,
        )

        # Cache the instance
        _llm_cache[cache_key] = llm

        parallel_status = "disabled" if disable_parallel else "enabled"
        logger.info(f"LLM configured: {model} (timeout: {timeout}s, max_tokens: {max_tokens}, parallel_tool_calls: {parallel_status})")
        return llm

    except Exception as e:
        logger.error(f"Failed to configure LLM: {e!s}")
        raise


def get_llm_for_crew(crew_name: str) -> LLM:
    """
    Get LLM configuration specific to a crew.

    Uses LLM_MODEL_STANDARD environment variable.

    Args:
        crew_name: Name of the crew (for logging purposes)

    Returns:
        LLM: Configured LLM instance

    """
    logger.debug(f"Getting LLM configuration for crew: {crew_name}")
    return get_configured_llm(model_type="standard")


def get_manager_llm() -> LLM:
    """
    Get LLM configuration for crew manager.

    Uses LLM_MODEL_MANAGER environment variable.

    Returns:
        LLM: Configured LLM instance for crew manager

    """
    logger.debug("Getting manager LLM configuration")
    return get_configured_llm(model_type="manager")


def get_mini_llm() -> LLM:
    """
    Get LLM configuration for performance-optimized operations.

    Uses LLM_MODEL_MINI environment variable.

    Returns:
        LLM: Configured mini LLM instance for fast operations

    """
    logger.debug("Getting mini LLM configuration")
    return get_configured_llm(model_type="mini")


# Convenience function for backward compatibility
def _get_configured_llm() -> LLM:
    """Backward compatibility alias for get_configured_llm."""
    return get_configured_llm()
