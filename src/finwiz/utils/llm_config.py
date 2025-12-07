"""
LLM Configuration Utility for FinWiz.

Provides centralized LLM configuration with proper parameter handling
for CrewAI integration. All models are configurable via environment variables.

Environment Variables:
    LLM_MODEL_STANDARD: Standard model for general operations (default: openai/gpt-4o-mini)
    LLM_MODEL_MINI: Mini model for performance-optimized operations (default: openai/gpt-4o-mini)
    LLM_MODEL_MANAGER: Manager model for crew management (default: openai/gpt-4o-mini)
    LLM_MODEL_PLANNING: Planning model for crew planning (default: openai/gpt-4o-mini)
    LLM_MODEL_BASELINE: Baseline model for comparison operations (default: openai/gpt-4o)
    MODEL: Fallback model if specific models not set (default: openai/gpt-4o-mini)
    OPENAI_TIMEOUT: Timeout in seconds (default: 300)
"""

import os

from crewai import LLM
from dotenv import load_dotenv

from finwiz.tools.logger import get_logger

# Load environment variables
load_dotenv()

logger = get_logger(__name__)


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

        # Create LLM with proper configuration
        llm = LLM(
            model=model,
            timeout=timeout,
        )

        # Cache the instance
        _llm_cache[cache_key] = llm

        logger.info(f"LLM configured successfully with model: {model} (timeout: {timeout}s)")
        return llm

    except Exception as e:
        logger.error(f"Failed to configure LLM: {str(e)}")
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


def validate_llm_config() -> bool:
    """
    Validate that LLM configuration is properly set up.

    Returns:
        bool: True if configuration is valid, False otherwise

    """
    try:
        # Check required environment variables
        required_vars = ["OPENAI_API_KEY"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]

        if missing_vars:
            logger.error(f"Missing required environment variables: {missing_vars}")
            return False

        # Try to create an LLM instance
        llm = get_configured_llm()
        if llm is None:
            logger.error("Failed to create LLM instance")
            return False

        logger.info("LLM configuration validation passed")
        return True

    except Exception as e:
        logger.error(f"LLM configuration validation failed: {str(e)}")
        return False


# Convenience function for backward compatibility
def _get_configured_llm() -> LLM:
    """Backward compatibility alias for get_configured_llm."""
    return get_configured_llm()
