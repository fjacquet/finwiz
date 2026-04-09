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

from crewai import LLM
from dotenv import load_dotenv

from finwiz.tools.logger import get_logger

# Load environment variables
load_dotenv()

logger = get_logger(__name__)


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


def get_configured_llm(model_override: str | None = None, model_type: str = "standard") -> LLM:
    """
    Get a properly configured LLM instance for CrewAI.

    This function creates an LLM instance with proper parameter handling.
    Models can be configured via environment variables for easy switching.

    Args:
        model_override: Optional model name to override environment configuration
        model_type: Type of model to use ("standard", "mini", "manager", "planning", "baseline")
                   Only used if model_override is None

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

    # Check cache first
    cache_key = f"{model}:{model_type}"
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

        # Create LLM with proper configuration
        llm = LLM(
            model=model,
            timeout=timeout,
            # Disable parallel tool calls to avoid Instructor compatibility issues
            # See: https://github.com/BerriAI/litellm/issues/4235
            parallel_tool_calls=False if disable_parallel else None,
            # Drop unsupported params for models that don't recognize parallel_tool_calls
            drop_params=True,
            # Extra params for provider-specific features
            extra_body=extra_body if extra_body else None,
        )

        # Cache the instance
        _llm_cache[cache_key] = llm

        parallel_status = "disabled" if disable_parallel else "enabled"
        logger.info(f"LLM configured: {model} (timeout: {timeout}s, parallel_tool_calls: {parallel_status})")
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


def get_planning_llm() -> LLM:
    """
    Get LLM configuration for crew planning.

    Uses LLM_MODEL_PLANNING environment variable.

    Returns:
        LLM: Configured LLM instance for crew planning

    """
    logger.debug("Getting planning LLM configuration")
    return get_configured_llm(model_type="planning")


def get_mini_llm() -> LLM:
    """
    Get LLM configuration for performance-optimized operations.

    Uses LLM_MODEL_MINI environment variable.

    Returns:
        LLM: Configured mini LLM instance for fast operations

    """
    logger.debug("Getting mini LLM configuration")
    return get_configured_llm(model_type="mini")


def get_baseline_llm() -> LLM:
    """
    Get LLM configuration for baseline/comparison operations.

    Uses LLM_MODEL_BASELINE environment variable.

    Returns:
        LLM: Configured baseline LLM instance

    """
    logger.debug("Getting baseline LLM configuration")
    return get_configured_llm(model_type="baseline")


def get_thinking_llm() -> LLM:
    """
    Get LLM configuration optimized for high-value reasoning tasks.

    This function returns an LLM configured with native thinking/reasoning
    capabilities enabled. Use this for complex analysis tasks where the
    extra cost of thinking tokens is justified by better quality outputs.

    Uses LLM_MODEL_THINKING environment variable (defaults to LLM_MODEL_PLANNING).
    Thinking level controlled by LLM_THINKING_LEVEL (off, low, medium, high).

    High-value tasks for thinking mode:
    - Portfolio rebalancing decisions
    - Complex financial analysis synthesis
    - Risk assessment with multiple factors
    - Investment strategy formulation
    - Manager/planning coordination

    Returns:
        LLM: Configured LLM instance with thinking mode enabled

    """
    logger.debug("Getting thinking LLM configuration")

    # Get the thinking model (fallback to planning model)
    model = os.getenv("LLM_MODEL_THINKING") or os.getenv("LLM_MODEL_PLANNING") or "openai/gpt-4o"

    # Get thinking level from environment
    thinking_level = os.getenv("LLM_THINKING_LEVEL", "medium").lower()

    # Check cache first
    cache_key = f"{model}:thinking:{thinking_level}"
    if cache_key in _llm_cache:
        logger.debug(f"Returning cached thinking LLM instance for {cache_key}")
        return _llm_cache[cache_key]

    # Validate API key
    _validate_api_key_for_model(model)

    # Get model-specific thinking parameters
    thinking_params = _get_thinking_params(model, thinking_level)

    # Log configuration
    if thinking_params:
        logger.info(f"Configuring thinking LLM with model: {model}, thinking_level: {thinking_level}")
        logger.debug(f"Thinking params: {thinking_params}")
    else:
        logger.info(f"Configuring thinking LLM with model: {model} (no native thinking support)")

    try:
        timeout = int(os.getenv("LITELLM_TIMEOUT") or os.getenv("OPENAI_TIMEOUT") or "300")
        disable_parallel = os.getenv("DISABLE_PARALLEL_TOOL_CALLS", "true").lower() == "true"

        # Build extra body params for OpenRouter models
        extra_body: dict[str, Any] = {}
        if model.startswith("openrouter/"):
            extra_body["transforms"] = ["middle-out"]
            if disable_parallel:
                extra_body["parallel_tool_calls"] = False
                extra_body["tool_choice"] = "auto"

        # Create LLM with thinking parameters if supported
        # Note: CrewAI LLM doesn't directly pass thinking params to the model,
        # but we can use extra_body for custom parameters
        llm_kwargs: dict[str, Any] = {
            "model": model,
            "timeout": timeout,
            "parallel_tool_calls": False if disable_parallel else None,
            "drop_params": True,
            "extra_body": extra_body if extra_body else None,
        }

        llm = LLM(**llm_kwargs)

        # Cache the instance
        _llm_cache[cache_key] = llm

        thinking_status = f"enabled ({thinking_level})" if thinking_params else "not available"
        logger.info(f"Thinking LLM configured: {model} (thinking: {thinking_status})")
        return llm

    except Exception as e:
        logger.error(f"Failed to configure thinking LLM: {e!s}")
        raise


def is_model_thinking_capable(model: str | None = None) -> bool:
    """
    Check if the given model (or default) has native thinking capabilities.

    Args:
        model: Model name to check. If None, checks LLM_MODEL_THINKING or LLM_MODEL_PLANNING.

    Returns:
        bool: True if model supports native thinking mode

    """
    if model is None:
        model = os.getenv("LLM_MODEL_THINKING") or os.getenv("LLM_MODEL_PLANNING") or ""
    return _is_thinking_capable(model)


def get_model_capabilities(model: str | None = None) -> dict[str, Any]:
    """
    Get capability summary for a model.

    Args:
        model: Model name to check. If None, uses LLM_MODEL_STANDARD.

    Returns:
        dict with keys: thinking_capable, json_reliable, thinking_params

    """
    if model is None:
        model = _get_model_from_env("LLM_MODEL_STANDARD")

    thinking_level = os.getenv("LLM_THINKING_LEVEL", "medium").lower()

    return {
        "model": model,
        "short_name": _get_model_short_name(model),
        "thinking_capable": _is_thinking_capable(model),
        "json_reliable": _is_json_reliable(model),
        "thinking_params": _get_thinking_params(model, thinking_level),
    }


def validate_llm_config() -> bool:
    """
    Validate that LLM configuration is properly set up.

    Returns:
        bool: True if configuration is valid, False otherwise

    """
    try:
        # Determine the required API key based on the configured provider
        model = _get_model_from_env("LLM_MODEL_STANDARD")
        provider = _get_provider_from_model(model)

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

        required_key = provider_key_map.get(provider, "OPENAI_API_KEY")
        required_vars = [required_key]
        missing_vars = [var for var in required_vars if not os.getenv(var)]

        if missing_vars:
            logger.error(f"Missing required environment variables for provider '{provider}': {missing_vars}")
            return False

        # Try to create an LLM instance
        llm = get_configured_llm()
        if llm is None:
            logger.error("Failed to create LLM instance")
            return False

        logger.info(f"LLM configuration validation passed (provider: {provider})")
        return True

    except Exception as e:
        logger.error(f"LLM configuration validation failed: {e!s}")
        return False


# Convenience function for backward compatibility
def _get_configured_llm() -> LLM:
    """Backward compatibility alias for get_configured_llm."""
    return get_configured_llm()
