"""
LLM Configuration Utility for FinWiz.

Provides centralized LLM configuration with proper parameter handling
for CrewAI integration, including drop_params for unsupported parameters.
"""

import os

from crewai import LLM
from dotenv import load_dotenv

from finwiz.tools.logger import get_logger

# Load environment variables
load_dotenv()

logger = get_logger(__name__)


def get_configured_llm(model_override: str | None = None) -> LLM:
    """
    Get a properly configured LLM instance for CrewAI.

    This function creates an LLM instance with proper parameter handling,
    including dropping unsupported parameters like 'stop' that cause
    400 Bad Request errors with certain models.

    Args:
        model_override: Optional model name to override the default from environment

    Returns:
        LLM: Configured LLM instance ready for CrewAI use

    Raises:
        EnvironmentError: If required API keys are missing

    """
    # Get model configuration from environment or use override
    model = model_override or os.getenv("MODEL", "openai/gpt-4o-mini")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    if not openai_api_key:
        raise OSError("OPENAI_API_KEY not found in environment variables. Please set your OpenAI API key in the .env file.")

    # Log the model being used
    logger.info(f"Configuring LLM with model: {model}")

    try:
        # Create LLM with drop_params to handle unsupported parameters
        llm = LLM(
            model=model,
            drop_params=True,
            additional_drop_params=["stop"],  # Drop the 'stop' parameter that causes issues
            timeout=int(os.getenv("OPENAI_TIMEOUT", "300")),
            max_retries=3,
        )

        logger.info("LLM configured successfully with drop_params enabled")
        return llm

    except Exception as e:
        logger.error(f"Failed to configure LLM: {str(e)}")
        raise


def get_llm_for_crew(crew_name: str) -> LLM:
    """
    Get LLM configuration specific to a crew.

    Args:
        crew_name: Name of the crew (for logging purposes)

    Returns:
        LLM: Configured LLM instance

    """
    logger.debug(f"Getting LLM configuration for crew: {crew_name}")
    return get_configured_llm()


def get_manager_llm() -> LLM:
    """
    Get LLM configuration for crew manager.

    This ensures the manager LLM also has proper parameter handling
    to avoid 'stop' parameter errors.

    Returns:
        LLM: Configured LLM instance for crew manager

    """
    logger.debug("Getting manager LLM configuration")
    return get_configured_llm()


def get_planning_llm() -> LLM:
    """
    Get LLM configuration for crew planning.

    This ensures the planning LLM also has proper parameter handling
    to avoid 'stop' parameter errors.

    Returns:
        LLM: Configured LLM instance for crew planning

    """
    logger.debug("Getting planning LLM configuration")
    return get_configured_llm()


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
