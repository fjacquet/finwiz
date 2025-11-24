"""
LLM configuration helpers for CrewAI crews.

This module provides functions for getting configured LLM instances
based on optimization mode. These functions are externalized from crew classes
to make them testable and reusable.
"""

from crewai import LLM

from finwiz.utils.llm_config import get_configured_llm, get_mini_llm
from finwiz.utils.performance_config import get_performance_config_manager


def get_crew_llm() -> LLM:
    """
    Get configured LLM instance for crew based on optimization mode.

    Returns mini model for maximum speed and balanced modes,
    otherwise returns the standard configured LLM.

    Uses environment variables:
        - LLM_MODEL_MINI for performance-optimized operations
        - LLM_MODEL_STANDARD for standard operations

    Returns:
        Configured LLM instance

    """
    perf_config = get_performance_config_manager()

    # Use mini model for maximum speed and balanced modes
    if perf_config.should_use_mini_model():
        return get_mini_llm()
    else:
        return get_configured_llm(model_type="standard")
