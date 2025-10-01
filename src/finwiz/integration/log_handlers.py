"""
Integration System Log Handlers.

Log handler setup and configuration for the crew data integration system.
"""

import logging
from pathlib import Path

from .config import get_integration_config
from .log_formatters import StructuredFormatter


class IntegrationLogHandler:
    """Manages log handlers for integration operations."""

    def __init__(self, name: str = "finwiz.integration", log_dir: Path | None = None) -> None:
        """
        Initialize the integration log handler.

        Args:
            name: Logger name
            log_dir: Directory for log files (optional)

        """
        self.config = get_integration_config()
        self.logger = logging.getLogger(name)
        self.log_dir = log_dir or Path("logs")

        if not self.logger.handlers:
            self._setup_handlers()

    def _setup_handlers(self) -> None:
        """Set up the logger with appropriate handlers and formatters."""
        # Set log level
        log_level = getattr(logging, self.config.log_level.upper(), logging.INFO)
        self.logger.setLevel(log_level)

        # Console handler
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(self.config.log_format)
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

        # File handler (if log directory exists or can be created)
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(self.log_dir / "integration.log", encoding="utf-8")

            # Use structured formatter if enabled
            if self.config.enable_structured_logging:
                file_formatter = StructuredFormatter(self.config.log_format)
            else:
                file_formatter = logging.Formatter(self.config.log_format)

            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
        except Exception as e:
            self.logger.warning(f"Could not set up file logging: {e}")

    def add_custom_handler(self, handler: logging.Handler) -> None:
        """Add a custom log handler."""
        self.logger.addHandler(handler)

    def remove_handler(self, handler: logging.Handler) -> None:
        """Remove a log handler."""
        self.logger.removeHandler(handler)

    def get_logger(self) -> logging.Logger:
        """Get the configured logger instance."""
        return self.logger
