"""
Error Handling Orchestrator for FinWiz Flow.

This module provides centralized error handling utilities for crew execution,
including error aggregation, summary generation, and error reporting.
"""

from collections.abc import Callable
from datetime import datetime
from typing import Any

from finwiz.flow_state import FinwizState
from finwiz.tools.logger import get_logger


class ErrorHandlingOrchestrator:
    """Handles crew execution errors and error aggregation."""

    def __init__(self, state: FinwizState, **dependencies: Any) -> None:
        """
        Initialize the ErrorHandlingOrchestrator.

        Args:
            state: FinwizState instance for tracking errors
            **dependencies: Additional dependencies (crew_factory, integration_manager, etc.)

        """
        self.state = state
        self.logger = get_logger(self.__class__.__name__)
        self.dependencies = dependencies

    def execute_crew_with_error_handling(
        self,
        crew_func: Callable[..., Any],
        crew_name: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Execute crew with comprehensive error handling.

        Args:
            crew_func: Callable crew function to execute
            crew_name: Name of the crew being executed
            **kwargs: Arguments to pass to crew_func

        Returns:
            Dictionary with success status, data, and error information:
            {
                "success": bool,
                "data": Any,  # Result data if successful
                "error": {
                    "message": str,
                    "type": str,
                    "context": dict[str, Any],
                    "timestamp": str,
                    "retryable": bool
                } | None
            }

        """
        try:
            self.logger.info(f"Executing crew: {crew_name}")
            result = crew_func(**kwargs)

            self.logger.info(f"Crew {crew_name} executed successfully")
            return {"success": True, "data": result, "error": None}

        except Exception as e:
            error_info = {
                "message": str(e),
                "type": type(e).__name__,
                "context": {"crew_name": crew_name, **kwargs},
                "timestamp": datetime.now().isoformat(),
                "retryable": self._is_retryable_error(e),
            }

            self.logger.error(f"Crew {crew_name} failed: {error_info['message']}", exc_info=True)

            # Track error in state
            self.state.errors.append(f"{crew_name}: {error_info['message']}")
            self.state.crew_execution_errors[crew_name] = str(error_info["message"])
            self.state.crew_execution_status[crew_name] = "failed"

            return {"success": False, "data": None, "error": error_info}

    def generate_error_summary(self, errors: list[Exception]) -> dict[str, Any]:
        """
        Aggregate errors into actionable summary.

        Args:
            errors: List of Exception objects to aggregate

        Returns:
            Dictionary containing aggregated error information:
            {
                "total_errors": int,
                "error_types": dict[str, int],
                "retryable_count": int,
                "non_retryable_count": int,
                "errors": list[dict[str, Any]],
                "timestamp": str
            }

        """
        error_summary = {
            "total_errors": len(errors),
            "error_types": {},
            "retryable_count": 0,
            "non_retryable_count": 0,
            "errors": [],
            "timestamp": datetime.now().isoformat(),
        }

        for error in errors:
            error_type = type(error).__name__
            error_message = str(error)
            is_retryable = self._is_retryable_error(error)

            # Count error types
            error_summary["error_types"][error_type] = error_summary["error_types"].get(error_type, 0) + 1

            # Count retryable vs non-retryable
            if is_retryable:
                error_summary["retryable_count"] += 1
            else:
                error_summary["non_retryable_count"] += 1

            # Add error details
            error_summary["errors"].append(
                {
                    "message": error_message,
                    "type": error_type,
                    "retryable": is_retryable,
                    "context": getattr(error, "context", {}),
                }
            )

        self.logger.info(
            f"Generated error summary: {error_summary['total_errors']} total errors, "
            f"{error_summary['retryable_count']} retryable, "
            f"{error_summary['non_retryable_count']} non-retryable"
        )

        return error_summary

    def generate_error_report(self, error_summary: dict[str, Any]) -> str:
        """
        Generate human-readable error report.

        Args:
            error_summary: Dictionary containing aggregated error information

        Returns:
            Formatted error report string

        """
        report_lines = [
            "=" * 80,
            "ERROR REPORT",
            "=" * 80,
            f"Generated: {error_summary.get('timestamp', 'N/A')}",
            f"Total Errors: {error_summary.get('total_errors', 0)}",
            "",
            "Error Breakdown:",
            f"  - Retryable: {error_summary.get('retryable_count', 0)}",
            f"  - Non-retryable: {error_summary.get('non_retryable_count', 0)}",
            "",
        ]

        # Add error type distribution
        error_types = error_summary.get("error_types", {})
        if error_types:
            report_lines.append("Error Types:")
            for error_type, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
                report_lines.append(f"  - {error_type}: {count}")
            report_lines.append("")

        # Add detailed error list
        errors = error_summary.get("errors", [])
        if errors:
            report_lines.append("Detailed Errors:")
            for idx, error in enumerate(errors, 1):
                report_lines.append(f"\n{idx}. {error.get('type', 'Unknown')}")
                report_lines.append(f"   Message: {error.get('message', 'N/A')}")
                report_lines.append(f"   Retryable: {error.get('retryable', False)}")

                context = error.get("context", {})
                if context:
                    report_lines.append("   Context:")
                    for key, value in context.items():
                        report_lines.append(f"     - {key}: {value}")

        report_lines.append("")
        report_lines.append("=" * 80)

        report = "\n".join(report_lines)
        self.logger.debug("Generated error report")

        return report

    def _is_retryable_error(self, error: Exception) -> bool:
        """
        Determine if an error is retryable.

        Args:
            error: Exception to check

        Returns:
            True if error is retryable, False otherwise

        """
        # Network/timeout errors are typically retryable
        retryable_types = (
            "TimeoutError",
            "ConnectionError",
            "HTTPError",
            "RequestException",
            "APIError",
            "RateLimitError",
        )

        error_type = type(error).__name__

        # Check if error type is in retryable list
        if error_type in retryable_types:
            return True

        # Check error message for retryable indicators
        error_message = str(error).lower()
        retryable_keywords = [
            "timeout",
            "connection",
            "rate limit",
            "too many requests",
            "service unavailable",
            "temporary",
        ]

        for keyword in retryable_keywords:
            if keyword in error_message:
                return True

        # Non-retryable by default (validation errors, logic errors, etc.)
        return False
