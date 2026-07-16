"""
LLM Configuration Utility for FinWiz.

Provides centralized LLM configuration with proper parameter handling
for CrewAI integration. All models are configurable via environment variables.

Reasoning effort is pinned explicitly (default: low) rather than inherited
from provider defaults — see ``LLM_REASONING_EFFORT`` and
``_get_reasoning_params()``. Hybrid-reasoning models (e.g. glm-5.2,
qwen3.7-plus) otherwise run at whatever effort the provider defaults to,
which inflates latency/output-token cost and eats into the generation
budget that would otherwise go to a complete, well-formed JSON response.

Environment Variables:
    LLM_MODEL_STANDARD: Standard model for general operations
    LLM_MODEL_MINI: Mini model for performance-optimized operations
    LLM_MODEL_MANAGER: Manager model for crew management
    LLM_MODEL_PLANNING: Planning model for crew planning
    LLM_MODEL_BASELINE: Baseline model for comparison operations
    LLM_REASONING_EFFORT: Reasoning effort (low, medium, high, none) - default: low.
        "none" sends no reasoning params at all. Only applied on routes verified
        to accept it (currently: openrouter/* via extra_body); other routes get
        no params regardless of this value, matching existing provider-default
        behavior.
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


def _is_json_reliable(model: str) -> bool:
    """Check if a model has excellent JSON output support."""
    short_name = _get_model_short_name(model)
    return any(json_model in short_name for json_model in JSON_RELIABLE_MODELS)


# Reasoning effort levels accepted for LLM_REASONING_EFFORT. "none" sends no
# reasoning params at all (distinct from an unset env var, which falls back
# to _DEFAULT_REASONING_EFFORT below).
_VALID_REASONING_EFFORTS = {"low", "medium", "high", "none"}
_DEFAULT_REASONING_EFFORT = "low"


def _resolve_reasoning_effort() -> str:
    """
    Resolve LLM_REASONING_EFFORT from the environment.

    Empty or invalid values fall back to the default ("low") with a warning;
    never raises, mirroring _parse_num_retries()'s tolerance for typo'd env
    values.

    Returns:
        One of "low", "medium", "high", "none".
    """
    raw = os.getenv("LLM_REASONING_EFFORT", "").strip().lower()
    if not raw:
        return _DEFAULT_REASONING_EFFORT
    if raw not in _VALID_REASONING_EFFORTS:
        logger.warning(f"Invalid LLM_REASONING_EFFORT={raw!r}, falling back to {_DEFAULT_REASONING_EFFORT!r}")
        return _DEFAULT_REASONING_EFFORT
    return raw


def _get_reasoning_params(model: str, effort: str) -> dict[str, Any]:
    """
    Build provider-appropriate reasoning-effort params for `model`.

    Pins reasoning effort explicitly instead of letting hybrid-reasoning
    models inherit provider defaults (a driver of both inflated qualify-stage
    latency and truncated/malformed JSON output, since reasoning tokens eat
    into the generation budget).

    Only OpenRouter's chat-completions route is verified (against the
    installed crewai/litellm) to accept the unified ``reasoning: {"effort":
    ...}`` field via ``extra_body``: crewai's native OpenAI-compatible
    completion class (used for every ``openrouter/*`` model in this codebase)
    forwards ``extra_body`` straight into the OpenAI SDK's
    ``chat.completions.create(**params)`` call, which merges it into the raw
    request body — the same mechanism already used for OpenRouter's
    ``transforms`` passthrough. OpenRouter documents unsupported request
    parameters as silently ignored rather than rejected, so this is safe to
    send even to non-reasoning models.

    litellm's own ``reasoning_effort``/``thinking`` param mapping for
    OpenRouter (gated on ``litellm.supports_reasoning()``) does NOT apply
    here: crewai routes ``openrouter/*`` models through its native provider
    class, bypassing litellm entirely (confirmed in the installed crewai's
    ``LLM.__new__`` — "openrouter" is in ``SUPPORTED_NATIVE_PROVIDERS``).

    No other route is verified, so "none" (no params sent) is the safe
    fallback for them — matching prior (provider-default) behavior.

    Args:
        model: Full model string (e.g. "openrouter/z-ai/glm-5.2")
        effort: One of "low", "medium", "high", "none"

    Returns:
        Dict to merge into extra_body; empty when no verified route applies.
    """
    if effort == "none":
        return {}
    if model.startswith("openrouter/"):
        return {"reasoning": {"effort": effort}}
    return {}


def _apply_reasoning_effort(extra_body: dict[str, Any], model: str, reasoning_effort: str, reasoning_params: dict[str, Any]) -> None:
    """Merge resolved reasoning params into `extra_body` in place and log the outcome."""
    if reasoning_params:
        extra_body.update(reasoning_params)
        logger.info(f"Reasoning effort pinned: {reasoning_effort} (via extra_body)")
    elif reasoning_effort != "none":
        logger.debug(f"Reasoning effort {reasoning_effort!r} requested but not sent: unverified route for {model}")


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
        LLM_REASONING_EFFORT: Reasoning effort (low, medium, high, none) - default: low
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

    # Reasoning effort is resolved up front (env-driven) because it affects
    # extra_body, which must be part of the cache key below — otherwise a
    # changed LLM_REASONING_EFFORT would silently return a stale cached
    # instance built with the old effort.
    reasoning_effort = _resolve_reasoning_effort()
    reasoning_params = _get_reasoning_params(model, reasoning_effort)

    # Check cache first (include max_tokens + json mode + reasoning effort so callers
    # with different needs get distinct instances)
    cache_key = f"{model}:{model_type}:{max_tokens}:json={force_json_object}:reasoning={reasoning_effort}"
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

        # Explicit reasoning effort: pins hybrid-reasoning models (e.g. glm-5.2,
        # qwen3.7-plus) to a known effort instead of inheriting provider defaults.
        # See _get_reasoning_params() for which routes are verified to accept this.
        _apply_reasoning_effort(extra_body, model, reasoning_effort, reasoning_params)

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
        reasoning_status = reasoning_effort if reasoning_params else "none"
        logger.info(f"LLM configured: {model} (timeout: {timeout}s, max_tokens: {max_tokens}, parallel_tool_calls: {parallel_status}, reasoning_effort: {reasoning_status})")
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
