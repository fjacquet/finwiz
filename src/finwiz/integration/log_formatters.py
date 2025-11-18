"""
Integration System Log Formatters.

Specialized log formatting utilities for the crew data integration system.
"""

import json
import logging
from datetime import datetime
from typing import Any


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging with JSON output."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with structured data."""
        # Get the basic formatted message
        message = super().format(record)

        # Add structured data if available
        if hasattr(record, "extra") and record.extra:
            structured_data = {
                "timestamp": datetime.now().isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                **record.extra,
            }
            return json.dumps(structured_data, ensure_ascii=False)

        return message


class IntegrationLogFormatter:
    """Handles log message formatting for integration operations."""

    @staticmethod
    def format_crew_execution_start(crew_name: str, dependencies: list[str] | None = None) -> dict[str, Any]:
        """Format crew execution start log data."""
        return {
            "event_type": "crew_execution_start",
            "crew_name": crew_name,
            "dependencies": dependencies or [],
            "timestamp": datetime.now().isoformat(),
        }

    @staticmethod
    def format_crew_execution_complete(crew_name: str, success: bool, execution_time: float, output_files: list[str] | None = None) -> dict[str, Any]:
        """Format crew execution completion log data."""
        return {
            "event_type": "crew_execution_complete",
            "crew_name": crew_name,
            "success": success,
            "execution_time_seconds": execution_time,
            "output_files": output_files or [],
            "timestamp": datetime.now().isoformat(),
        }

    @staticmethod
    def format_data_validation(crew_name: str, is_valid: bool, errors: list[str] | None = None, warnings: list[str] | None = None) -> dict[str, Any]:
        """Format data validation log data."""
        return {
            "event_type": "data_validation",
            "crew_name": crew_name,
            "is_valid": is_valid,
            "error_count": len(errors or []),
            "warning_count": len(warnings or []),
            "errors": errors or [],
            "warnings": warnings or [],
            "timestamp": datetime.now().isoformat(),
        }

    @staticmethod
    def format_data_freshness_check(fresh_crews: list[str], stale_crews: list[str], missing_crews: list[str], overall_status: str) -> dict[str, Any]:
        """Format data freshness check log data."""
        return {
            "event_type": "data_freshness_check",
            "fresh_crews": fresh_crews,
            "stale_crews": stale_crews,
            "missing_crews": missing_crews,
            "overall_status": overall_status,
            "timestamp": datetime.now().isoformat(),
        }

    @staticmethod
    def format_integration_error(error_type: str, crew_name: str, error_message: str, recovery_suggestions: list[str] | None = None) -> dict[str, Any]:
        """Format integration error log data."""
        return {
            "event_type": "integration_error",
            "error_type": error_type,
            "crew_name": crew_name,
            "error_message": error_message,
            "recovery_suggestions": recovery_suggestions or [],
            "timestamp": datetime.now().isoformat(),
        }

    @staticmethod
    def format_data_lineage(crew_name: str, input_sources: list[str], output_files: list[str], transformations: list[str] | None = None) -> dict[str, Any]:
        """Format data lineage log data."""
        return {
            "event_type": "data_lineage",
            "crew_name": crew_name,
            "input_sources": input_sources,
            "output_files": output_files,
            "transformations": transformations or [],
            "timestamp": datetime.now().isoformat(),
        }

    @staticmethod
    def format_performance_metrics(operation: str, duration: float, data_size: int | None = None, memory_usage: float | None = None) -> dict[str, Any]:
        """Format performance metrics log data."""
        return {
            "event_type": "performance_metrics",
            "operation": operation,
            "duration_seconds": duration,
            "data_size_bytes": data_size,
            "memory_usage_mb": memory_usage,
            "timestamp": datetime.now().isoformat(),
        }

    @staticmethod
    def format_data_access_operation(operation: str, crew_name: str, success: bool, file_paths: list[str] | None = None, error_message: str | None = None) -> dict[str, Any]:
        """Format data access operation log data."""
        return {
            "event_type": "data_access_operation",
            "operation": operation,
            "crew_name": crew_name,
            "success": success,
            "file_paths": file_paths or [],
            "error_message": error_message,
            "timestamp": datetime.now().isoformat(),
        }

    @staticmethod
    def format_data_transformation(crew_name: str, transformation_type: str, input_schema: str, output_schema: str, record_count: int | None = None) -> dict[str, Any]:
        """Format data transformation log data."""
        return {
            "event_type": "data_transformation",
            "crew_name": crew_name,
            "transformation_type": transformation_type,
            "input_schema": input_schema,
            "output_schema": output_schema,
            "record_count": record_count,
            "timestamp": datetime.now().isoformat(),
        }

    @staticmethod
    def format_dependency_check(crew_name: str, dependencies: list[str], satisfied: list[str], missing: list[str], stale: list[str]) -> dict[str, Any]:
        """Format dependency check log data."""
        return {
            "event_type": "dependency_check",
            "crew_name": crew_name,
            "dependencies": dependencies,
            "satisfied": satisfied,
            "missing": missing,
            "stale": stale,
            "all_satisfied": len(missing) == 0,
            "timestamp": datetime.now().isoformat(),
        }

    @staticmethod
    def format_schema_validation_detail(
        crew_name: str, schema_name: str, validation_errors: list[str], validation_warnings: list[str], field_validations: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Format detailed schema validation log data."""
        return {
            "event_type": "schema_validation_detail",
            "crew_name": crew_name,
            "schema_name": schema_name,
            "validation_errors": validation_errors,
            "validation_warnings": validation_warnings,
            "field_validations": field_validations or {},
            "error_count": len(validation_errors),
            "warning_count": len(validation_warnings),
            "timestamp": datetime.now().isoformat(),
        }

    @staticmethod
    def format_data_consolidation(
        source_crews: list[str], target_file: str, success: bool, record_counts: dict[str, int] | None = None, error_message: str | None = None
    ) -> dict[str, Any]:
        """Format data consolidation log data."""
        return {
            "event_type": "data_consolidation",
            "source_crews": source_crews,
            "target_file": target_file,
            "success": success,
            "record_counts": record_counts or {},
            "total_records": sum(record_counts.values()) if record_counts else 0,
            "error_message": error_message,
            "timestamp": datetime.now().isoformat(),
        }

    @staticmethod
    def format_system_health_check(component: str, status: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
        """Format system health check log data."""
        return {
            "event_type": "system_health_check",
            "component": component,
            "status": status,
            "details": details or {},
            "timestamp": datetime.now().isoformat(),
        }

    @staticmethod
    def format_error_recovery_attempt(error_type: str, crew_name: str, recovery_action: str, success: bool, details: dict[str, Any] | None = None) -> dict[str, Any]:
        """Format error recovery attempt log data."""
        return {
            "event_type": "error_recovery_attempt",
            "error_type": error_type,
            "crew_name": crew_name,
            "recovery_action": recovery_action,
            "success": success,
            "details": details or {},
            "timestamp": datetime.now().isoformat(),
        }
