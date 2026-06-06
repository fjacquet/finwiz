"""
Integration System Logging Configuration.

Main logging classes and global instances for the crew data integration system.
"""

from pathlib import Path
from typing import Any

from finwiz.integration.config import get_integration_config

from .formatters import IntegrationLogFormatter
from .handlers import IntegrationLogHandler


class IntegrationLogger:
    """
    Specialized logger for integration operations with structured logging support.

    Enhanced with comprehensive data integration operation logging.
    """

    def __init__(self, name: str = "finwiz.integration", log_dir: Path | None = None) -> None:
        """
        Initialize the integration logger.

        Args:
            name: Logger name
            log_dir: Directory for log files (optional)

        """
        self.config = get_integration_config()
        self.handler = IntegrationLogHandler(name, log_dir)
        self.logger = self.handler.get_logger()
        self.formatter = IntegrationLogFormatter()

        # Initialize operation tracking
        self.operation_start_times: dict[str, Any] = {}

    def log_crew_execution_start(self, crew_name: str, dependencies: list[Any] | None = None) -> None:
        """Log the start of crew execution."""
        extra_data = self.formatter.format_crew_execution_start(crew_name, dependencies)
        self.logger.info(f"Starting execution for crew: {crew_name}", extra=extra_data if self.config.enable_structured_logging else {})

    def log_integration_error(self, error_type: str, crew_name: str, error_message: str, recovery_suggestions: list[Any] | None = None) -> None:
        """Log integration errors with recovery suggestions."""
        extra_data = self.formatter.format_integration_error(error_type, crew_name, error_message, recovery_suggestions)
        self.logger.error(
            f"Integration error [{error_type}] for crew {crew_name}: {error_message}",
            extra=extra_data if self.config.enable_structured_logging else {},
        )

    def log_performance_metrics(self, operation: str, duration: float, data_size: int | None = None, memory_usage: float | None = None) -> None:
        """Log performance metrics for integration operations."""
        extra_data = self.formatter.format_performance_metrics(operation, duration, data_size, memory_usage)
        self.logger.info(
            f"Performance: {operation} completed in {duration:.2f}s",
            extra=extra_data if self.config.enable_structured_logging else {},
        )

    def log_system_health_check(self, component: str, status: str, details: dict[str, Any] | None = None) -> None:
        """Log system health check results."""
        extra_data = self.formatter.format_system_health_check(component, status, details)

        if status == "healthy":
            self.logger.info(
                f"Health check passed for {component}",
                extra=extra_data if self.config.enable_structured_logging else {},
            )
        else:
            self.logger.warning(
                f"Health check failed for {component}: {status}",
                extra=extra_data if self.config.enable_structured_logging else {},
            )


# Global instances for easy access
# Note: These imports are at the bottom to avoid circular import issues
def _create_global_instances() -> tuple:
    """Create global instances to avoid circular imports."""
    from .analyzer import LogAnalyzer

    integration_logger = IntegrationLogger()
    log_analyzer = LogAnalyzer()

    return integration_logger, log_analyzer


integration_logger, log_analyzer = _create_global_instances()
