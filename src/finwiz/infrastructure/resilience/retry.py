"""
Retry logic with exponential backoff for FinWiz flow orchestrator.

Provides centralized retry handling using the tenacity library with
error classification and remediation suggestions.
"""

import logging
from collections.abc import Callable
from datetime import datetime

from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from finwiz.config.resilience_config import ResilienceConfig, get_resilience_config
from finwiz.tools.logger import get_logger
from finwiz.validation.result import ValidationError

logger = get_logger(__name__)

# Retryable exception types
RETRYABLE_EXCEPTIONS = (
    ConnectionError,
    TimeoutError,
)


def create_retry_decorator(config: ResilienceConfig | None = None) -> Callable:
    """
    Create a retry decorator with configured parameters.

    Args:
        config: Resilience configuration (uses default if None)

    Returns:
        Configured retry decorator from tenacity

    Example:
        >>> config = get_resilience_config()
        >>> retry_decorator = create_retry_decorator(config)
        >>> @retry_decorator
        ... async def fetch_data():
        ...     return await api_call()

    """
    if config is None:
        config = get_resilience_config()

    return retry(
        stop=stop_after_attempt(config.max_retries),
        wait=wait_exponential(
            multiplier=config.retry_base_delay,
            max=config.retry_max_delay,
        ),
        retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )


def classify_error(error: Exception) -> tuple[str, bool]:
    """
    Classify error as retryable or non-retryable.

    Args:
        error: Exception to classify

    Returns:
        Tuple of (error_type, is_retryable)

    Error Types:
        - network: Connection errors, network issues
        - timeout: Operation timeouts
        - rate_limit: API rate limiting
        - authentication: Authentication failures
        - validation: Data validation errors
        - unknown: Unclassified errors

    Example:
        >>> error = ConnectionError("Network unreachable")
        >>> error_type, is_retryable = classify_error(error)
        >>> assert error_type == "network"
        >>> assert is_retryable is True

    """
    error_str = str(error).lower()

    # Check exception type first
    if isinstance(error, ConnectionError):
        return ("network", True)
    elif isinstance(error, TimeoutError):
        return ("timeout", True)

    # Check error message content
    if "rate limit" in error_str or "too many requests" in error_str:
        return ("rate_limit", True)
    elif "authentication" in error_str or "unauthorized" in error_str or "api key" in error_str:
        return ("authentication", False)
    elif "validation" in error_str or "invalid" in error_str:
        return ("validation", False)
    else:
        return ("unknown", False)


def create_validation_error_from_exception(
    error: Exception,
    ticker: str,
    attempt: int,
) -> ValidationError:
    """
    Create ValidationError from exception for tracking.

    Args:
        error: Exception that occurred
        ticker: Ticker symbol being processed
        attempt: Retry attempt number (1-indexed)

    Returns:
        ValidationError with error details and context

    Example:
        >>> error = ConnectionError("Network unreachable")
        >>> validation_error = create_validation_error_from_exception(error, "AAPL", 2)
        >>> assert validation_error.error_type == "network"
        >>> assert validation_error.context["is_retryable"] is True

    """
    error_type, is_retryable = classify_error(error)

    return ValidationError(
        field_path=f"holding.{ticker}",
        error_type=error_type,
        message=str(error),
        input_value=ticker,
        context={
            "ticker": ticker,
            "attempt": attempt,
            "is_retryable": is_retryable,
            "timestamp": datetime.now().isoformat(),
            "remediation": get_remediation_suggestion(error_type),
        },
    )


def get_remediation_suggestion(error_type: str) -> str:
    """
    Get remediation suggestion for error type.

    Args:
        error_type: Type of error (network, timeout, rate_limit, etc.)

    Returns:
        Human-readable remediation suggestion

    Example:
        >>> suggestion = get_remediation_suggestion("network")
        >>> assert "connectivity" in suggestion.lower()

    """
    suggestions = {
        "network": "Check network connectivity and API status. Verify firewall settings and DNS resolution.",
        "rate_limit": "Reduce parallelism or increase delays between requests. Consider upgrading API tier.",
        "timeout": "Increase timeout value or check API performance. Consider breaking request into smaller chunks.",
        "authentication": "Check API keys in environment variables. Verify key permissions and expiration.",
        "validation": "Check ticker symbols and input data format. Verify data meets schema requirements.",
        "unknown": "Review error details and logs. Check API documentation for specific error codes.",
    }
    return suggestions.get(error_type, suggestions["unknown"])
