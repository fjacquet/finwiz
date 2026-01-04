"""
Data Lineage Tracking for Integration System.

Tracks data lineage across crew executions for debugging and auditing.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


class DataLineageTracker:
    """
    Tracks data lineage across crew executions for debugging and auditing.

    Enhanced with comprehensive data flow tracking and analysis.
    """

    def __init__(self, lineage_file: Path | None = None) -> None:
        """
        Initialize the lineage tracker.

        Args:
            lineage_file: Path to store lineage data

        """
        self.lineage_file = lineage_file or Path("output/integration/metadata/data_lineage.json")

        # Use standard logging to avoid circular imports with IntegrationLogger
        self.logger = logging.getLogger("finwiz.integration.lineage")

        # Track active operations
        self.active_operations: dict[str, Any] = {}

    def track_crew_execution(self, crew_name: str, input_data: dict[str, Any], output_files: list, metadata: dict[str, Any] | None = None) -> None:
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

            self.logger.info(f"Tracked crew execution: {crew_name}, inputs={list(input_data.keys())}, outputs={len(output_files)} files")

        except Exception as e:
            self.logger.error(f"Lineage tracking error for {crew_name}: {e}")

    def get_crew_lineage(self, crew_name: str) -> list[Any]:
        """Get lineage history for a specific crew."""
        try:
            lineage_data = self._load_lineage()
            executions = lineage_data.get("executions", [])
            return [exec for exec in executions if exec["crew_name"] == crew_name]
        except Exception:
            return []

    def track_data_dependency(self, dependent_crew: str, source_crew: str, dependency_type: str, file_path: str | None = None) -> None:
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

            status = "satisfied" if file_path else "missing"
            self.logger.debug(f"Tracked dependency: {dependent_crew} <- {source_crew} ({dependency_type}) [{status}]")

        except Exception as e:
            self.logger.error(f"Dependency tracking error for {dependent_crew}: {e}")

    def track_data_flow(self, from_crew: str, to_crew: str, data_type: str, transformation: str | None = None, validation_status: str | None = None) -> None:
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

            transform_str = f" via {transformation}" if transformation else ""
            self.logger.debug(f"Tracked data flow: {from_crew} -> {to_crew} ({data_type}){transform_str}")

        except Exception as e:
            self.logger.error(f"Data flow tracking error for {to_crew}: {e}")

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
            self.logger.error(f"Graph generation error: {e}")
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
            self.logger.error(f"Lineage summary error: {e}")
            return {}

    def _load_lineage(self) -> dict[str, Any]:
        """Load lineage data from file."""
        try:
            if self.lineage_file.exists():
                with open(self.lineage_file, encoding="utf-8") as f:
                    result: dict[str, Any] = json.load(f)
                    return result
        except Exception:
            pass

        return {"executions": []}

    def _save_lineage(self, lineage_data: dict[str, Any]) -> None:
        """Save lineage data to file."""
        self.lineage_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.lineage_file, "w", encoding="utf-8") as f:
            json.dump(lineage_data, f, indent=2, ensure_ascii=False)
