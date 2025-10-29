"""
Structured logging utilities for FinWiz crews.

This module provides standardized logging helpers for crew execution tracking,
including start, completion, and error logging with structured extra fields.

Usage:
    from finwiz.utils.logging_helpers import CrewLogger

    class MyCrew:
        def __init__(self) -> None:
            self.logger = CrewLogger("MyCrew")

        def kickoff(self, inputs: dict) -> Any:
            self.logger.log_start(inputs)
            start_time = time.time()

            try:
                result = super().kickoff(inputs)
                duration = time.time() - start_time
                self.logger.log_complete(duration)
                return result
            except Exception as e:
                self.logger.log_error(e)
                raise
"""

from typing import Any

from finwiz.tools.logger import get_logger


class CrewLogger:
    """Standardized logging for crews with structured extra fields."""

    def __init__(self, crew_name: str) -> None:
        """
        Initialize crew logger.

        Args:
            crew_name: Name of the crew for log identification

        """
        self.crew_name = crew_name
        self.logger = get_logger(f"finwiz.crews.{crew_name}")

    def log_start(self, inputs: dict[str, Any]) -> None:
        """
        Log crew execution start with structured fields.

        Args:
            inputs: Input parameters passed to crew

        """
        input_keys = list(inputs.keys()) if inputs else []
        self.logger.info(
            f"Starting {self.crew_name} execution",
            extra={
                "crew": self.crew_name,
                "input_keys": input_keys,
                "event": "crew_start",
            },
        )

    def log_complete(self, duration: float) -> None:
        """
        Log crew execution completion with duration tracking.

        Args:
            duration: Execution duration in seconds

        """
        self.logger.info(
            f"{self.crew_name} execution completed in {duration:.2f}s",
            extra={
                "crew": self.crew_name,
                "duration": duration,
                "event": "crew_complete",
            },
        )

    def log_error(self, error: Exception) -> None:
        """
        Log crew execution error with exception details.

        Args:
            error: Exception that occurred during execution

        """
        self.logger.error(
            f"{self.crew_name} execution failed: {type(error).__name__}",
            extra={
                "crew": self.crew_name,
                "error_type": type(error).__name__,
                "event": "crew_error",
            },
            exc_info=True,
        )
