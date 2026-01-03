"""
Integration System Logging Configuration.

Main logging classes and global instances for the crew data integration system.
"""

from datetime import datetime
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

    def log_crew_execution_complete(self, crew_name: str, success: bool, execution_time: float, output_files: list[Any] | None = None) -> None:
        """Log the completion of crew execution."""
        extra_data = self.formatter.format_crew_execution_complete(crew_name, success, execution_time, output_files)
        status = "completed successfully" if success else "failed"
        self.logger.info(
            f"Crew {crew_name} execution {status} in {execution_time:.2f}s",
            extra=extra_data if self.config.enable_structured_logging else {},
        )

    def log_data_validation(self, crew_name: str, is_valid: bool, errors: list[Any] | None = None, warnings: list[Any] | None = None) -> None:
        """Log data validation results."""
        extra_data = self.formatter.format_data_validation(crew_name, is_valid, errors, warnings)

        if is_valid:
            self.logger.info(f"Data validation passed for crew: {crew_name}", extra=extra_data if self.config.enable_structured_logging else {})
        else:
            self.logger.error(
                f"Data validation failed for crew: {crew_name} - {len(errors or [])} errors",
                extra=extra_data if self.config.enable_structured_logging else {},
            )

    def log_data_freshness_check(self, fresh_crews: list, stale_crews: list, missing_crews: list, overall_status: str) -> None:
        """Log data freshness check results."""
        extra_data = self.formatter.format_data_freshness_check(fresh_crews, stale_crews, missing_crews, overall_status)
        self.logger.info(
            f"Data freshness check: {overall_status} - Fresh: {len(fresh_crews)}, Stale: {len(stale_crews)}, Missing: {len(missing_crews)}",
            extra=extra_data if self.config.enable_structured_logging else {},
        )

    def log_integration_error(self, error_type: str, crew_name: str, error_message: str, recovery_suggestions: list[Any] | None = None) -> None:
        """Log integration errors with recovery suggestions."""
        extra_data = self.formatter.format_integration_error(error_type, crew_name, error_message, recovery_suggestions)
        self.logger.error(
            f"Integration error [{error_type}] for crew {crew_name}: {error_message}",
            extra=extra_data if self.config.enable_structured_logging else {},
        )

    def log_data_lineage(self, crew_name: str, input_sources: list, output_files: list, transformations: list[Any] | None = None) -> None:
        """Log data lineage information."""
        extra_data = self.formatter.format_data_lineage(crew_name, input_sources, output_files, transformations)
        self.logger.info(
            f"Data lineage for crew {crew_name}: {len(input_sources)} inputs -> {len(output_files)} outputs",
            extra=extra_data if self.config.enable_structured_logging else {},
        )

    def log_performance_metrics(self, operation: str, duration: float, data_size: int | None = None, memory_usage: float | None = None) -> None:
        """Log performance metrics for integration operations."""
        extra_data = self.formatter.format_performance_metrics(operation, duration, data_size, memory_usage)
        self.logger.info(
            f"Performance: {operation} completed in {duration:.2f}s",
            extra=extra_data if self.config.enable_structured_logging else {},
        )

    def log_data_access_operation(self, operation: str, crew_name: str, success: bool, file_paths: list[Any] | None = None, error_message: str | None = None) -> None:
        """Log data access operations for debugging integration issues."""
        extra_data = self.formatter.format_data_access_operation(operation, crew_name, success, file_paths, error_message)

        if success:
            self.logger.info(
                f"Data access successful: {operation} for crew {crew_name}",
                extra=extra_data if self.config.enable_structured_logging else {},
            )
        else:
            self.logger.error(
                f"Data access failed: {operation} for crew {crew_name} - {error_message}",
                extra=extra_data if self.config.enable_structured_logging else {},
            )

    def log_data_transformation(self, crew_name: str, transformation_type: str, input_schema: str, output_schema: str, record_count: int | None = None) -> None:
        """Log data transformation operations."""
        extra_data = self.formatter.format_data_transformation(crew_name, transformation_type, input_schema, output_schema, record_count)
        self.logger.info(
            f"Data transformation: {transformation_type} for crew {crew_name} ({input_schema} -> {output_schema})",
            extra=extra_data if self.config.enable_structured_logging else {},
        )

    def log_dependency_check(self, crew_name: str, dependencies: list, satisfied: list, missing: list, stale: list[Any]) -> None:
        """Log dependency checking results."""
        extra_data = self.formatter.format_dependency_check(crew_name, dependencies, satisfied, missing, stale)
        status = "satisfied" if len(missing) == 0 else f"missing {len(missing)} dependencies"
        self.logger.info(
            f"Dependency check for crew {crew_name}: {status}",
            extra=extra_data if self.config.enable_structured_logging else {},
        )

    def log_schema_validation_detail(
        self, crew_name: str, schema_name: str, validation_errors: list, validation_warnings: list, field_validations: dict[str, Any] | None = None
    ) -> None:
        """Log detailed schema validation results."""
        extra_data = self.formatter.format_schema_validation_detail(crew_name, schema_name, validation_errors, validation_warnings, field_validations)

        if validation_errors:
            self.logger.error(
                f"Schema validation failed for {crew_name} ({schema_name}): {len(validation_errors)} errors",
                extra=extra_data if self.config.enable_structured_logging else {},
            )
        elif validation_warnings:
            self.logger.warning(
                f"Schema validation warnings for {crew_name} ({schema_name}): {len(validation_warnings)} warnings",
                extra=extra_data if self.config.enable_structured_logging else {},
            )
        else:
            self.logger.info(
                f"Schema validation passed for {crew_name} ({schema_name})",
                extra=extra_data if self.config.enable_structured_logging else {},
            )

    def log_data_consolidation(self, source_crews: list, target_file: str, success: bool, record_counts: dict[str, Any] | None = None, error_message: str | None = None) -> None:
        """Log data consolidation operations."""
        extra_data = self.formatter.format_data_consolidation(source_crews, target_file, success, record_counts, error_message)

        if success:
            total_records = sum(record_counts.values()) if record_counts else 0
            self.logger.info(
                f"Data consolidation successful: {len(source_crews)} crews -> {target_file} ({total_records} records)",
                extra=extra_data if self.config.enable_structured_logging else {},
            )
        else:
            self.logger.error(
                f"Data consolidation failed: {error_message}",
                extra=extra_data if self.config.enable_structured_logging else {},
            )

    def start_operation_timing(self, operation_id: str) -> None:
        """Start timing an operation for performance logging."""
        self.operation_start_times[operation_id] = datetime.now()

    def end_operation_timing(self, operation_id: str, operation_name: str, additional_metrics: dict[str, Any] | None = None) -> float:
        """End timing an operation and log performance metrics."""
        if operation_id not in self.operation_start_times:
            self.logger.warning(f"No start time found for operation: {operation_id}")
            return 0.0

        start_time = self.operation_start_times.pop(operation_id)
        duration = (datetime.now() - start_time).total_seconds()

        # Log performance with additional metrics
        metrics = additional_metrics or {}
        self.log_performance_metrics(
            operation=operation_name,
            duration=duration,
            data_size=metrics.get("data_size"),
            memory_usage=metrics.get("memory_usage"),
        )

        return float(duration)

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

    def log_error_recovery_attempt(self, error_type: str, crew_name: str, recovery_action: str, success: bool, details: dict[str, Any] | None = None) -> None:
        """Log error recovery attempts."""
        extra_data = self.formatter.format_error_recovery_attempt(error_type, crew_name, recovery_action, success, details)

        if success:
            self.logger.info(
                f"Error recovery successful: {recovery_action} for {error_type} in crew {crew_name}",
                extra=extra_data if self.config.enable_structured_logging else {},
            )
        else:
            self.logger.error(
                f"Error recovery failed: {recovery_action} for {error_type} in crew {crew_name}",
                extra=extra_data if self.config.enable_structured_logging else {},
            )


# Global instances for easy access
# Note: These imports are at the bottom to avoid circular import issues
def _create_global_instances() -> tuple:
    """Create global instances to avoid circular imports."""
    from finwiz.integration.lineage import DataLineageTracker
    from .analyzer import LogAnalyzer

    integration_logger = IntegrationLogger()
    lineage_tracker = DataLineageTracker()
    log_analyzer = LogAnalyzer(lineage_tracker=lineage_tracker)

    return integration_logger, lineage_tracker, log_analyzer


integration_logger, lineage_tracker, log_analyzer = _create_global_instances()
