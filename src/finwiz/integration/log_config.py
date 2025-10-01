"""
Integration System Logging Configuration.

Main logging classes and global instances for the crew data integration system.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from .config import get_integration_config
from .log_formatters import IntegrationLogFormatter
from .log_handlers import IntegrationLogHandler


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
        self.operation_start_times = {}

    def log_crew_execution_start(self, crew_name: str, dependencies: list = None) -> None:
        """Log the start of crew execution."""
        extra_data = self.formatter.format_crew_execution_start(crew_name, dependencies)
        self.logger.info(
            f"Starting execution for crew: {crew_name}", extra=extra_data if self.config.enable_structured_logging else {}
        )

    def log_crew_execution_complete(self, crew_name: str, success: bool, execution_time: float, output_files: list = None) -> None:
        """Log the completion of crew execution."""
        extra_data = self.formatter.format_crew_execution_complete(crew_name, success, execution_time, output_files)
        status = "completed successfully" if success else "failed"
        self.logger.info(
            f"Crew {crew_name} execution {status} in {execution_time:.2f}s",
            extra=extra_data if self.config.enable_structured_logging else {},
        )

    def log_data_validation(self, crew_name: str, is_valid: bool, errors: list = None, warnings: list = None) -> None:
        """Log data validation results."""
        extra_data = self.formatter.format_data_validation(crew_name, is_valid, errors, warnings)

        if is_valid:
            self.logger.info(
                f"Data validation passed for crew: {crew_name}", extra=extra_data if self.config.enable_structured_logging else {}
            )
        else:
            self.logger.error(
                f"Data validation failed for crew: {crew_name} - {len(errors or [])} errors",
                extra=extra_data if self.config.enable_structured_logging else {},
            )

    def log_data_freshness_check(self, fresh_crews: list, stale_crews: list, missing_crews: list, overall_status: str) -> None:
        """Log data freshness check results."""
        extra_data = self.formatter.format_data_freshness_check(fresh_crews, stale_crews, missing_crews, overall_status)
        self.logger.info(
            f"Data freshness check: {overall_status} - "
            f"Fresh: {len(fresh_crews)}, Stale: {len(stale_crews)}, Missing: {len(missing_crews)}",
            extra=extra_data if self.config.enable_structured_logging else {},
        )

    def log_integration_error(self, error_type: str, crew_name: str, error_message: str, recovery_suggestions: list = None) -> None:
        """Log integration errors with recovery suggestions."""
        extra_data = self.formatter.format_integration_error(error_type, crew_name, error_message, recovery_suggestions)
        self.logger.error(
            f"Integration error [{error_type}] for crew {crew_name}: {error_message}",
            extra=extra_data if self.config.enable_structured_logging else {},
        )

    def log_data_lineage(self, crew_name: str, input_sources: list, output_files: list, transformations: list = None) -> None:
        """Log data lineage information."""
        extra_data = self.formatter.format_data_lineage(crew_name, input_sources, output_files, transformations)
        self.logger.info(
            f"Data lineage for crew {crew_name}: {len(input_sources)} inputs -> {len(output_files)} outputs",
            extra=extra_data if self.config.enable_structured_logging else {},
        )

    def log_performance_metrics(self, operation: str, duration: float, data_size: int = None, memory_usage: float = None) -> None:
        """Log performance metrics for integration operations."""
        extra_data = self.formatter.format_performance_metrics(operation, duration, data_size, memory_usage)
        self.logger.info(
            f"Performance: {operation} completed in {duration:.2f}s",
            extra=extra_data if self.config.enable_structured_logging else {},
        )

    def log_data_access_operation(
        self, operation: str, crew_name: str, success: bool, file_paths: list = None, error_message: str = None
    ) -> None:
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

    def log_data_transformation(
        self, crew_name: str, transformation_type: str, input_schema: str, output_schema: str, record_count: int = None
    ) -> None:
        """Log data transformation operations."""
        extra_data = self.formatter.format_data_transformation(
            crew_name, transformation_type, input_schema, output_schema, record_count
        )
        self.logger.info(
            f"Data transformation: {transformation_type} for crew {crew_name} ({input_schema} -> {output_schema})",
            extra=extra_data if self.config.enable_structured_logging else {},
        )

    def log_dependency_check(self, crew_name: str, dependencies: list, satisfied: list, missing: list, stale: list) -> None:
        """Log dependency checking results."""
        extra_data = self.formatter.format_dependency_check(crew_name, dependencies, satisfied, missing, stale)
        status = "satisfied" if len(missing) == 0 else f"missing {len(missing)} dependencies"
        self.logger.info(
            f"Dependency check for crew {crew_name}: {status}",
            extra=extra_data if self.config.enable_structured_logging else {},
        )

    def log_schema_validation_detail(
        self, crew_name: str, schema_name: str, validation_errors: list, validation_warnings: list, field_validations: dict = None
    ) -> None:
        """Log detailed schema validation results."""
        extra_data = self.formatter.format_schema_validation_detail(
            crew_name, schema_name, validation_errors, validation_warnings, field_validations
        )

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

    def log_data_consolidation(
        self, source_crews: list, target_file: str, success: bool, record_counts: dict = None, error_message: str = None
    ) -> None:
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

    def end_operation_timing(self, operation_id: str, operation_name: str, additional_metrics: dict = None) -> float:
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

        return duration

    def log_system_health_check(self, component: str, status: str, details: dict = None) -> None:
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

    def log_error_recovery_attempt(
        self, error_type: str, crew_name: str, recovery_action: str, success: bool, details: dict = None
    ) -> None:
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


class DataLineageTracker:
    """
    Tracks data lineage across crew executions for debugging and auditing.

    Enhanced with comprehensive data flow tracking and analysis.
    """

    def __init__(self, lineage_file: Path = None) -> None:
        """
        Initialize the lineage tracker.

        Args:
            lineage_file: Path to store lineage data

        """
        self.lineage_file = lineage_file or Path("output/integration/metadata/data_lineage.json")
        self.logger = IntegrationLogger("finwiz.integration.lineage")

        # Track active operations
        self.active_operations = {}

    def track_crew_execution(
        self, crew_name: str, input_data: dict[str, Any], output_files: list, metadata: dict[str, Any] = None
    ) -> None:
        """
        Track a crew execution in the lineage.

        Args:
            crew_name: Name of the executed crew
            input_data: Input data sources and dependencies
            output_files: Generated output files
            metadata: Additional metadata about the execution

        """
        try:
            lineage_entry = {
                "crew_name": crew_name,
                "execution_timestamp": datetime.now().isoformat(),
                "input_data": input_data,
                "output_files": [str(f) for f in output_files],
                "metadata": metadata or {},
            }

            # Load existing lineage
            lineage_data = self._load_lineage()

            # Add new entry
            if "executions" not in lineage_data:
                lineage_data["executions"] = []

            lineage_data["executions"].append(lineage_entry)

            # Keep only last 100 executions to prevent file from growing too large
            if len(lineage_data["executions"]) > 100:
                lineage_data["executions"] = lineage_data["executions"][-100:]

            # Save updated lineage
            self._save_lineage(lineage_data)

            self.logger.log_data_lineage(crew_name=crew_name, input_sources=list(input_data.keys()), output_files=output_files)

        except Exception as e:
            self.logger.log_integration_error(error_type="LINEAGE_TRACKING_ERROR", crew_name=crew_name, error_message=str(e))

    def get_crew_lineage(self, crew_name: str) -> list:
        """Get lineage history for a specific crew."""
        try:
            lineage_data = self._load_lineage()
            executions = lineage_data.get("executions", [])
            return [exec for exec in executions if exec["crew_name"] == crew_name]
        except Exception:
            return []

    def track_data_dependency(self, dependent_crew: str, source_crew: str, dependency_type: str, file_path: str = None) -> None:
        """Track data dependencies between crews."""
        try:
            dependency_entry = {
                "dependent_crew": dependent_crew,
                "source_crew": source_crew,
                "dependency_type": dependency_type,
                "file_path": file_path,
                "timestamp": datetime.now().isoformat(),
            }

            lineage_data = self._load_lineage()

            if "dependencies" not in lineage_data:
                lineage_data["dependencies"] = []

            lineage_data["dependencies"].append(dependency_entry)

            # Keep only last 500 dependencies to prevent file from growing too large
            if len(lineage_data["dependencies"]) > 500:
                lineage_data["dependencies"] = lineage_data["dependencies"][-500:]

            self._save_lineage(lineage_data)

            self.logger.log_dependency_check(
                crew_name=dependent_crew,
                dependencies=[source_crew],
                satisfied=[source_crew] if file_path else [],
                missing=[] if file_path else [source_crew],
                stale=[],
            )

        except Exception as e:
            self.logger.log_integration_error(
                error_type="DEPENDENCY_TRACKING_ERROR", crew_name=dependent_crew, error_message=str(e)
            )

    def track_data_flow(
        self, from_crew: str, to_crew: str, data_type: str, transformation: str = None, validation_status: str = None
    ) -> None:
        """Track data flow between crews."""
        try:
            flow_entry = {
                "from_crew": from_crew,
                "to_crew": to_crew,
                "data_type": data_type,
                "transformation": transformation,
                "validation_status": validation_status,
                "timestamp": datetime.now().isoformat(),
            }

            lineage_data = self._load_lineage()

            if "data_flows" not in lineage_data:
                lineage_data["data_flows"] = []

            lineage_data["data_flows"].append(flow_entry)

            # Keep only last 1000 flows
            if len(lineage_data["data_flows"]) > 1000:
                lineage_data["data_flows"] = lineage_data["data_flows"][-1000:]

            self._save_lineage(lineage_data)

            self.logger.log_data_transformation(
                crew_name=to_crew,
                transformation_type=transformation or "direct_flow",
                input_schema=f"{from_crew}_{data_type}",
                output_schema=f"{to_crew}_{data_type}",
            )

        except Exception as e:
            self.logger.log_integration_error(error_type="DATA_FLOW_TRACKING_ERROR", crew_name=to_crew, error_message=str(e))

    def get_data_flow_graph(self) -> dict:
        """Get a graph representation of data flows between crews."""
        try:
            lineage_data = self._load_lineage()
            flows = lineage_data.get("data_flows", [])

            # Build adjacency list representation
            graph = {}
            for flow in flows:
                from_crew = flow["from_crew"]
                to_crew = flow["to_crew"]

                if from_crew not in graph:
                    graph[from_crew] = []

                graph[from_crew].append(
                    {
                        "target": to_crew,
                        "data_type": flow["data_type"],
                        "transformation": flow.get("transformation"),
                        "timestamp": flow["timestamp"],
                    }
                )

            return graph

        except Exception as e:
            self.logger.log_integration_error(error_type="GRAPH_GENERATION_ERROR", crew_name="system", error_message=str(e))
            return {}

    def get_lineage_summary(self) -> dict:
        """Get a summary of data lineage for monitoring."""
        try:
            lineage_data = self._load_lineage()

            executions = lineage_data.get("executions", [])
            dependencies = lineage_data.get("dependencies", [])
            flows = lineage_data.get("data_flows", [])

            # Calculate summary statistics
            crew_execution_counts = {}
            for execution in executions:
                crew_name = execution["crew_name"]
                crew_execution_counts[crew_name] = crew_execution_counts.get(crew_name, 0) + 1

            recent_executions = [
                exec
                for exec in executions
                if datetime.fromisoformat(exec["execution_timestamp"]) > datetime.now() - timedelta(hours=24)
            ]

            return {
                "total_executions": len(executions),
                "recent_executions_24h": len(recent_executions),
                "crew_execution_counts": crew_execution_counts,
                "total_dependencies": len(dependencies),
                "total_data_flows": len(flows),
                "active_crews": list(crew_execution_counts.keys()),
                "last_updated": datetime.now().isoformat(),
            }

        except Exception as e:
            self.logger.log_integration_error(error_type="LINEAGE_SUMMARY_ERROR", crew_name="system", error_message=str(e))
            return {}

    def _load_lineage(self) -> dict[str, Any]:
        """Load lineage data from file."""
        try:
            if self.lineage_file.exists():
                with open(self.lineage_file, encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass

        return {"executions": []}

    def _save_lineage(self, lineage_data: dict[str, Any]) -> None:
        """Save lineage data to file."""
        self.lineage_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.lineage_file, "w", encoding="utf-8") as f:
            json.dump(lineage_data, f, indent=2, ensure_ascii=False)


class LogAnalyzer:
    """Utility class for analyzing integration logs and debugging issues."""

    def __init__(self, log_dir: Path = None, lineage_tracker: DataLineageTracker = None) -> None:
        """
        Initialize the log analyzer.

        Args:
            log_dir: Directory containing log files
            lineage_tracker: Data lineage tracker instance

        """
        self.log_dir = log_dir or Path("logs")
        self.lineage_tracker = lineage_tracker or DataLineageTracker()
        self.logger = IntegrationLogger("finwiz.integration.analyzer")

    def analyze_crew_execution_patterns(self, hours_back: int = 24) -> dict:
        """Analyze crew execution patterns for debugging."""
        try:
            self.lineage_tracker.get_lineage_summary()

            # Get recent execution data
            lineage_data = self.lineage_tracker._load_lineage()
            executions = lineage_data.get("executions", [])

            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            recent_executions = [exec for exec in executions if datetime.fromisoformat(exec["execution_timestamp"]) > cutoff_time]

            # Analyze patterns
            execution_frequency = {}
            success_rates = {}
            average_durations = {}

            for execution in recent_executions:
                crew_name = execution["crew_name"]

                # Count executions
                execution_frequency[crew_name] = execution_frequency.get(crew_name, 0) + 1

                # Track success/failure (if available in metadata)
                metadata = execution.get("metadata", {})
                if "success" in metadata:
                    if crew_name not in success_rates:
                        success_rates[crew_name] = {"success": 0, "total": 0}

                    success_rates[crew_name]["total"] += 1
                    if metadata["success"]:
                        success_rates[crew_name]["success"] += 1

                # Track durations (if available)
                if "execution_time_seconds" in metadata:
                    if crew_name not in average_durations:
                        average_durations[crew_name] = []
                    average_durations[crew_name].append(metadata["execution_time_seconds"])

            # Calculate averages
            for crew_name in average_durations:
                durations = average_durations[crew_name]
                average_durations[crew_name] = {
                    "average": sum(durations) / len(durations),
                    "min": min(durations),
                    "max": max(durations),
                    "count": len(durations),
                }

            # Calculate success rates as percentages
            for crew_name in success_rates:
                rates = success_rates[crew_name]
                success_rates[crew_name]["percentage"] = (rates["success"] / rates["total"]) * 100

            return {
                "analysis_period_hours": hours_back,
                "total_executions": len(recent_executions),
                "execution_frequency": execution_frequency,
                "success_rates": success_rates,
                "average_durations": average_durations,
                "analysis_timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            self.logger.log_integration_error(error_type="EXECUTION_ANALYSIS_ERROR", crew_name="system", error_message=str(e))
            return {}

    def identify_integration_bottlenecks(self) -> dict:
        """Identify potential bottlenecks in the integration pipeline."""
        try:
            data_flow_graph = self.lineage_tracker.get_data_flow_graph()

            # Analyze flow patterns
            bottlenecks = {"high_dependency_crews": [], "slow_crews": [], "frequent_failure_crews": [], "stale_data_sources": []}

            # Find crews with many dependencies (potential bottlenecks)
            dependency_counts = {}
            for source_crew, flows in data_flow_graph.items():
                for flow in flows:
                    target_crew = flow["target"]
                    dependency_counts[target_crew] = dependency_counts.get(target_crew, 0) + 1

            # Identify high-dependency crews (top 20% or more than 3 dependencies)
            if dependency_counts:
                max_deps = max(dependency_counts.values())
                threshold = max(3, max_deps * 0.8)

                for crew, count in dependency_counts.items():
                    if count >= threshold:
                        bottlenecks["high_dependency_crews"].append({"crew": crew, "dependency_count": count})

            # Analyze execution patterns for slow crews
            execution_analysis = self.analyze_crew_execution_patterns()
            durations = execution_analysis.get("average_durations", {})

            if durations:
                # Find crews with above-average execution times
                all_averages = [data["average"] for data in durations.values()]
                if all_averages:
                    avg_duration = sum(all_averages) / len(all_averages)

                    for crew, duration_data in durations.items():
                        if duration_data["average"] > avg_duration * 1.5:  # 50% above average
                            bottlenecks["slow_crews"].append(
                                {"crew": crew, "average_duration": duration_data["average"], "max_duration": duration_data["max"]}
                            )

            # Find crews with low success rates
            success_rates = execution_analysis.get("success_rates", {})
            for crew, rate_data in success_rates.items():
                if rate_data["percentage"] < 80:  # Less than 80% success rate
                    bottlenecks["frequent_failure_crews"].append(
                        {"crew": crew, "success_rate": rate_data["percentage"], "total_attempts": rate_data["total"]}
                    )

            return bottlenecks

        except Exception as e:
            self.logger.log_integration_error(error_type="BOTTLENECK_ANALYSIS_ERROR", crew_name="system", error_message=str(e))
            return {}

    def generate_debug_report(self, crew_name: str = None) -> dict:
        """Generate a comprehensive debug report for integration issues."""
        try:
            report = {
                "report_timestamp": datetime.now().isoformat(),
                "crew_filter": crew_name,
                "lineage_summary": self.lineage_tracker.get_lineage_summary(),
                "execution_patterns": self.analyze_crew_execution_patterns(),
                "bottlenecks": self.identify_integration_bottlenecks(),
                "data_flow_graph": self.lineage_tracker.get_data_flow_graph(),
            }

            # Add crew-specific analysis if requested
            if crew_name:
                report["crew_specific"] = {
                    "lineage_history": self.lineage_tracker.get_crew_lineage(crew_name),
                    "recent_executions": [
                        exec
                        for exec in self.lineage_tracker._load_lineage().get("executions", [])
                        if exec["crew_name"] == crew_name
                    ][-10:],  # Last 10 executions
                }

            return report

        except Exception as e:
            self.logger.log_integration_error(
                error_type="DEBUG_REPORT_ERROR", crew_name=crew_name or "system", error_message=str(e)
            )
            return {"error": str(e)}

    def export_debug_report(self, output_file: Path = None, crew_name: str = None) -> Path:
        """Export debug report to a JSON file."""
        try:
            report = self.generate_debug_report(crew_name)

            if not output_file:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"integration_debug_report_{timestamp}.json"
                if crew_name:
                    filename = f"integration_debug_report_{crew_name}_{timestamp}.json"
                output_file = self.log_dir / filename

            # Ensure directory exists
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # Write report
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False, default=str)

            self.logger.logger.info(f"Debug report exported to: {output_file}")
            return output_file

        except Exception as e:
            self.logger.log_integration_error(
                error_type="DEBUG_EXPORT_ERROR", crew_name=crew_name or "system", error_message=str(e)
            )
            raise


# Global instances for easy access
integration_logger = IntegrationLogger()
lineage_tracker = DataLineageTracker()
log_analyzer = LogAnalyzer(lineage_tracker=lineage_tracker)
