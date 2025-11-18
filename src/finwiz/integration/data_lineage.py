"""
Data Lineage Tracking for Integration System.

Tracks data lineage across crew executions for debugging and auditing.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


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

        # Import here to avoid circular imports
        from .log_config import IntegrationLogger

        self.logger = IntegrationLogger("finwiz.integration.lineage")

        # Track active operations
        self.active_operations = {}

    def track_crew_execution(self, crew_name: str, input_data: dict[str, Any], output_files: list, metadata: dict[str, Any] = None) -> None:
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

    def get_crew_lineage(self, crew_name: str) -> list[Any]:
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
            self.logger.log_integration_error(error_type="DEPENDENCY_TRACKING_ERROR", crew_name=dependent_crew, error_message=str(e))

    def track_data_flow(self, from_crew: str, to_crew: str, data_type: str, transformation: str = None, validation_status: str = None) -> None:
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

    def get_data_flow_graph(self) -> dict[str, Any]:
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

    def get_lineage_summary(self) -> dict[str, Any]:
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

            recent_executions = [exec for exec in executions if datetime.fromisoformat(exec["execution_timestamp"]) > datetime.now() - timedelta(hours=24)]

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
