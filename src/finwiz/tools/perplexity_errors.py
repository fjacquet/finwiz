"""
Error handling classes and utilities for Perplexity integration.

This module contains custom exception classes and error management utilities
for handling various types of failures in Perplexity API interactions.
"""

from typing import Any

from finwiz.schemas.perplexity import SonarSearchResult


class PerplexityError(Exception):
    """Base exception for Perplexity integration errors."""

    pass


class PerplexityRateLimitError(PerplexityError):
    """Raised when rate limits are exceeded."""

    def __init__(self, retry_after: int | None = None, message: str = "Rate limit exceeded"):
        self.retry_after = retry_after
        super().__init__(f"{message}{f', retry after {retry_after} seconds' if retry_after else ''}")


class PerplexityAPIError(PerplexityError):
    """Raised when API returns an error response."""

    def __init__(self, status_code: int | None, message: str):
        self.status_code = status_code
        super().__init__(f"API error{f' {status_code}' if status_code else ''}: {message}")


class PerplexityTimeoutError(PerplexityError):
    """Raised when requests timeout."""

    pass


class PerplexityConnectionError(PerplexityError):
    """Raised when connection fails."""

    pass


class PerplexityFallbackManager:
    """Manages fallback strategies for Perplexity integration failures."""

    @staticmethod
    def create_fallback_result(
        query: str, ticker: str, asset_type: str, analysis_type: str, error_message: str
    ) -> SonarSearchResult:
        """Create a fallback result when Perplexity fails."""
        return SonarSearchResult(
            query=query,
            ticker=ticker,
            asset_type=asset_type,
            analysis_type=analysis_type,
            results=[],
            total_results=0,
            search_time_ms=0,
            success=False,
            error_message=error_message,
            fallback_used=True,
        )

    @staticmethod
    def should_retry_error(error: Exception, attempt: int, max_retries: int) -> bool:
        """Determine if an error should trigger a retry."""
        if attempt >= max_retries:
            return False

        error_str = str(error).lower()

        # Always retry on rate limits, timeouts, and connection errors
        retryable_patterns = [
            "rate limit",
            "429",
            "timeout",
            "connection",
            "network",
            "502",
            "503",
            "504",
            "temporary",
            "unavailable",
        ]

        return any(pattern in error_str for pattern in retryable_patterns)

    @staticmethod
    def calculate_backoff_delay(attempt: int, base_delay: float = 1.0, max_delay: float = 60.0) -> float:
        """Calculate exponential backoff delay with jitter."""
        import random

        # Exponential backoff: base_delay * (2 ^ attempt)
        delay = min(base_delay * (2**attempt), max_delay)

        # Add jitter (±25% of delay)
        jitter = delay * 0.25 * (2 * random.random() - 1)

        return max(0.1, delay + jitter)

    @staticmethod
    def extract_rate_limit_info(error: Exception) -> dict[str, Any]:
        """Extract rate limit information from error."""
        error_str = str(error)
        info = {"is_rate_limit": False}

        if "rate limit" in error_str.lower() or "429" in error_str:
            info["is_rate_limit"] = True

            # Try to extract retry-after value
            import re

            retry_match = re.search(r"retry[_\s]*after[:\s]*(\d+)", error_str, re.IGNORECASE)
            if retry_match:
                try:
                    info["retry_after"] = int(retry_match.group(1))
                except ValueError:
                    pass

        return info
