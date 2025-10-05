"""
Log Analysis Utilities for Integration System.

Utility class for analyzing integration logs and debugging issues.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

from .data_lineage import DataLineageTracker


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

        # Import here to avoid circular imports
        from .log_config import IntegrationLogger

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
