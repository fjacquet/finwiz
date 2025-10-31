"""
Logging utilities for Perplexity integration.

This module contains structured logging utilities and feature flag tracking
for Perplexity API operations with content redaction and security.
"""

import time
from typing import Any

from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class PerplexityFeatureFlagTracker:
    """Tracks feature flag success/failure for Perplexity operations with circuit breaker integration."""

    @staticmethod
    def record_operation_success(ticker: str, analysis_type: str, result_count: int) -> None:
        """Record successful Perplexity operation for feature flag tracking."""
        from finwiz.utils.feature_flags import get_feature_flags

        feature_flags = get_feature_flags()
        feature_flags.record_success("perplexity_research")

        logger.debug(
            "Perplexity feature flag success recorded",
            extra={
                "operation": "feature_flag_success",
                "ticker": ticker,
                "analysis_type": analysis_type,
                "result_count": result_count,
                "timestamp": time.time(),
            },
        )

    @staticmethod
    def record_operation_failure(ticker: str, analysis_type: str, error_type: str, circuit_breaker_triggered: bool = False) -> None:
        """Record failed Perplexity operation for feature flag tracking."""
        from finwiz.utils.feature_flags import get_feature_flags

        feature_flags = get_feature_flags()
        feature_flags.record_failure("perplexity_research")

        logger.warning(
            "Perplexity feature flag failure recorded",
            extra={
                "operation": "feature_flag_failure",
                "ticker": ticker,
                "analysis_type": analysis_type,
                "error_type": error_type,
                "circuit_breaker_triggered": circuit_breaker_triggered,
                "timestamp": time.time(),
            },
        )

    @staticmethod
    def check_circuit_breaker_status() -> dict[str, Any]:
        """Check current circuit breaker status for Perplexity feature flag."""
        from finwiz.utils.feature_flags import get_feature_flags

        feature_flags = get_feature_flags()
        flag_status = feature_flags.get_flag_status("perplexity_research")

        return {
            "is_enabled": feature_flags.is_enabled("perplexity_research"),
            "circuit_breaker_info": flag_status.get("circuit_breaker", {}),
            "fallback_strategy": flag_status.get("fallback_strategy", "unknown"),
        }

    @staticmethod
    def log_circuit_breaker_state_change(old_state: bool, new_state: bool, failure_count: int) -> None:
        """Log circuit breaker state changes."""
        state_change = "opened" if new_state and not old_state else "closed" if not new_state and old_state else "unchanged"

        if state_change != "unchanged":
            logger.warning(
                f"Perplexity circuit breaker {state_change}",
                extra={
                    "operation": "circuit_breaker_state_change",
                    "old_state": "open" if old_state else "closed",
                    "new_state": "open" if new_state else "closed",
                    "failure_count": failure_count,
                    "timestamp": time.time(),
                },
            )


class PerplexityOperationLogger:
    """Structured logging for Perplexity operations with content redaction."""

    @staticmethod
    def log_search_request(ticker: str, analysis_type: str, query_length: int) -> None:
        """Log Perplexity search request with redacted content."""
        logger.info(
            "Perplexity search initiated",
            extra={
                "operation": "perplexity_search",
                "ticker": ticker,
                "analysis_type": analysis_type,
                "query_length": query_length,
                "timestamp": time.time(),
            },
        )

    @staticmethod
    def log_search_success(ticker: str, analysis_type: str, latency_ms: int, result_count: int, http_status: int = 200) -> None:
        """Log successful Perplexity search with performance metrics."""
        logger.info(
            "Perplexity search completed successfully",
            extra={
                "operation": "perplexity_search_success",
                "ticker": ticker,
                "analysis_type": analysis_type,
                "latency_ms": latency_ms,
                "result_count": result_count,
                "http_status": http_status,
                "timestamp": time.time(),
            },
        )

        # Record success for feature flag tracking
        PerplexityFeatureFlagTracker.record_operation_success(ticker, analysis_type, result_count)

    @staticmethod
    def log_search_failure(ticker: str, analysis_type: str, latency_ms: int, error_type: str, http_status: int | None = None) -> None:
        """Log failed Perplexity search with error details."""
        extra_data = {
            "operation": "perplexity_search_failure",
            "ticker": ticker,
            "analysis_type": analysis_type,
            "latency_ms": latency_ms,
            "error_type": error_type,
            "timestamp": time.time(),
        }

        if http_status is not None:
            extra_data["http_status"] = http_status

        logger.warning("Perplexity search failed", extra=extra_data)

        # Check if this failure should trigger circuit breaker
        circuit_breaker_status = PerplexityFeatureFlagTracker.check_circuit_breaker_status()
        circuit_breaker_triggered = not circuit_breaker_status["is_enabled"]

        # Record failure for feature flag tracking
        PerplexityFeatureFlagTracker.record_operation_failure(ticker, analysis_type, error_type, circuit_breaker_triggered)

    @staticmethod
    def log_rate_limit_warning(ticker: str, retry_after: int | None = None) -> None:
        """Log rate limit warnings without exposing sensitive information."""
        extra_data = {
            "operation": "perplexity_rate_limit",
            "ticker": ticker,
            "timestamp": time.time(),
        }

        if retry_after is not None:
            extra_data["retry_after_seconds"] = retry_after

        logger.warning("Perplexity API rate limit encountered", extra=extra_data)

    @staticmethod
    def log_api_failure(ticker: str, error_message: str, attempt: int = 1) -> None:
        """Log API failures with redacted error messages."""
        # Redact sensitive information from error messages
        redacted_message = PerplexityOperationLogger._redact_sensitive_info(error_message)

        logger.warning(
            "Perplexity API failure",
            extra={
                "operation": "perplexity_api_failure",
                "ticker": ticker,
                "error_message": redacted_message,
                "attempt": attempt,
                "timestamp": time.time(),
            },
        )

    @staticmethod
    def log_parsing_metrics(ticker: str, raw_response_size: int, parsed_articles: int) -> None:
        """Log response parsing metrics without exposing content."""
        logger.debug(
            "Perplexity response parsed",
            extra={
                "operation": "perplexity_parsing",
                "ticker": ticker,
                "raw_response_size_bytes": raw_response_size,
                "parsed_articles": parsed_articles,
                "timestamp": time.time(),
            },
        )

    @staticmethod
    def log_feature_flag_status(ticker: str, is_enabled: bool, fallback_strategy: str) -> None:
        """Log current feature flag status for debugging."""
        logger.debug(
            "Perplexity feature flag status checked",
            extra={
                "operation": "feature_flag_status",
                "ticker": ticker,
                "is_enabled": is_enabled,
                "fallback_strategy": fallback_strategy,
                "timestamp": time.time(),
            },
        )

    @staticmethod
    def _redact_sensitive_info(message: str) -> str:
        """Redact sensitive information from error messages."""
        import re

        # Redact API keys
        message = re.sub(r"sk-[a-zA-Z0-9]{48}", "[REDACTED_API_KEY]", message)
        message = re.sub(r"Bearer [a-zA-Z0-9-_]+", "Bearer [REDACTED_TOKEN]", message)

        # Redact other potential sensitive patterns
        message = re.sub(r'api[_-]?key["\s]*[:=]["\s]*[a-zA-Z0-9-_]+', "api_key=[REDACTED]", message, flags=re.IGNORECASE)
        message = re.sub(r'token["\s]*[:=]["\s]*[a-zA-Z0-9-_]+', "token=[REDACTED]", message, flags=re.IGNORECASE)

        return message
