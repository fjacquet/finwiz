"""
Utility functions for Perplexity feature flag integration.

Provides standardized helper functions for consistent feature flag checking,
logging, and error handling across all Perplexity-integrated tools.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from finwiz.config.features.flags import get_feature_flags
from finwiz.tools.logger import get_logger

if TYPE_CHECKING:
    from finwiz.tools.perplexity_analysis_integration import PerplexityAnalysisIntegration

logger = get_logger(__name__)


def initialize_perplexity_integration(tool_name: str) -> PerplexityAnalysisIntegration | None:
    """
    Initialize Perplexity integration with standardized logging.

    Args:
        tool_name: Name of the tool for logging purposes

    Returns:
        PerplexityAnalysisIntegration instance or None if disabled/unavailable

    """
    feature_flags = get_feature_flags()

    if not feature_flags.is_enabled("perplexity_research"):
        logger.debug(f"Perplexity research feature flag disabled for {tool_name}")
        return None

    try:
        from finwiz.tools.perplexity_analysis_integration import PerplexityAnalysisIntegration

        integration = PerplexityAnalysisIntegration()
        if integration.is_available:
            logger.info(f"Perplexity Sonar integration initialized for {tool_name}")
            return integration
        else:
            logger.warning(f"Perplexity integration initialized but API key not available for {tool_name}")
            return None

    except Exception as e:
        logger.error(f"Failed to initialize Perplexity integration for {tool_name}: {e!s}")
        return None


def is_perplexity_enabled(integration: PerplexityAnalysisIntegration | None) -> bool:
    """
    Check if Perplexity integration is enabled and available.

    Args:
        integration: PerplexityAnalysisIntegration instance or None

    Returns:
        True if Perplexity is enabled and available, False otherwise

    """
    if not integration:
        return False

    feature_flags = get_feature_flags()
    return feature_flags.is_enabled("perplexity_research") and integration.is_available


def record_perplexity_success(tool_name: str, result_count: int, ticker: str) -> None:
    """
    Record successful Perplexity operation with standardized logging.

    Args:
        tool_name: Name of the tool for logging
        result_count: Number of results retrieved
        ticker: Ticker symbol analyzed

    """
    feature_flags = get_feature_flags()
    feature_flags.record_success("perplexity_research")
    logger.info(f"Retrieved {result_count} Perplexity insights for {ticker} in {tool_name}")


def record_perplexity_failure(tool_name: str, ticker: str, error_message: str) -> None:
    """
    Record failed Perplexity operation with standardized logging.

    Args:
        tool_name: Name of the tool for logging
        ticker: Ticker symbol that failed
        error_message: Error message to log

    """
    feature_flags = get_feature_flags()
    feature_flags.record_failure("perplexity_research")
    logger.warning(f"Perplexity search failed for {ticker} in {tool_name}: {error_message}")
