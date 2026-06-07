"""
LLM configuration helpers for CrewAI crews.

This module provides functions for getting configured LLM instances
based on optimization mode. These functions are externalized from crew classes
to make them testable and reusable.
"""

import os

from crewai import LLM

from finwiz.config.llm.llm_config import get_configured_llm, get_mini_llm
from finwiz.config.performance.performance_config import get_performance_config_manager


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


def get_crew_model_string() -> str:
    """Return the model id ``get_crew_llm()`` would use, without building an LLM.

    Used by the cost tracker for litellm price lookup. Resolving the string
    directly (rather than constructing an ``LLM``) keeps the cost path free of
    API-key validation side effects. Mirrors ``get_crew_llm``'s mini-vs-standard
    decision and the env fallback chain in ``config.llm.llm_config``.
    """
    perf_config = get_performance_config_manager()
    env_var = "LLM_MODEL_MINI" if perf_config.should_use_mini_model() else "LLM_MODEL_STANDARD"
    return os.getenv(env_var) or os.getenv("MODEL") or "openai/gpt-4o-mini"
