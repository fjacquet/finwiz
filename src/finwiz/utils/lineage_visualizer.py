"""
Lineage Visualization Utility for FinWiz.

Provides visualization functionality for data lineage using Mermaid.js
flowcharts and other diagram formats.
"""

import logging
from typing import Literal

from finwiz.schemas.data_lineage import DataLineage

logger = logging.getLogger(__name__)


class LineageVisualizer:
    """
    Visualize data lineage using various diagram formats.

    Primary format is Mermaid.js flowcharts for easy embedding in HTML reports.
    """

    def __init__(self) -> None:
        """Initialize lineage visualizer."""
        self.logger = logger

    def generate_mermaid_flowchart(
        self, lineage: DataLineage, direction: Literal["LR", "TD"] = "LR", include_values: bool = True
    ) -> str:
        """
        Generate Mermaid.js flowchart diagram.

        Args:
            lineage: DataLineage object to visualize
            direction: Diagram direction (LR=left-to-right, TD=top-to-down)
            include_values: Whether to include values in node labels

        Returns:
            Mermaid.js diagram code as string

        """
        lines = [f"flowchart {direction}"]

        # Add title as comment
        lines.append(f"    %% Data Lineage for {lineage.ticker} ({lineage.asset_class})")
        lines.append("")

        # Define node styles
        lines.append("    %% Node styles")
        lines.append("    classDef sourceNode fill:#e3f2fd,stroke:#1976d2,stroke-width:2px")
        lines.append("    classDef transformNode fill:#fff3e0,stroke:#f57c00,stroke-width:2px")
        lines.append("    classDef calcNode fill:#e8f5e9,stroke:#388e3c,stroke-width:2px")
        lines.append("    classDef resultNode fill:#fce4ec,stroke:#c2185b,stroke-width:2px")
        lines.append("")

        # Track node IDs
        node_ids = {}
        node_counter = 0

        # Add data source nodes
        lines.append("    %% Data Sources")
        for source in lineage.sources:
            node_id = f"src{node_counter}"
            node_counter += 1
            node_ids[f"source_{source.field_name}"] = node_id

            # Create label
            if include_values:
                label = f"{source.field_name}<br/>{source.raw_value}<br/><small>{source.source_name}</small>"
            else:
                label = f"{source.field_name}<br/><small>{source.source_name}</small>"

            lines.append(f'    {node_id}["{label}"]:::sourceNode')

        lines.append("")

        # Add transformation nodes
        if lineage.transformations:
            lines.append("    %% Transformations")
            for transform in lineage.transformations:
                node_id = f"trans{node_counter}"
                node_counter += 1
                node_ids[f"transform_{transform.transformation_id}"] = node_id

                # Create label
                label = f"{transform.operation}"
                if transform.formula:
                    label += f"<br/><small>{transform.formula}</small>"

                lines.append(f'    {node_id}["{label}"]:::transformNode')

            lines.append("")

        # Add calculation nodes
        lines.append("    %% Calculations")
        for calc in lineage.calculations:
            node_id = f"calc{node_counter}"
            node_counter += 1
            node_ids[f"calc_{calc.step_name}"] = node_id

            # Create label
            if include_values:
                label = f"{calc.step_name}<br/>{calc.output}"
            else:
                label = calc.step_name

            if calc.formula:
                label += f"<br/><small>{calc.formula}</small>"

            lines.append(f'    {node_id}["{label}"]:::calcNode')

        lines.append("")

        # Add final result nodes
        lines.append("    %% Final Results")
        for key, value in lineage.final_values.items():
            # Skip if already added as calculation
            if f"calc_{key}" in node_ids:
                continue

            node_id = f"result{node_counter}"
            node_counter += 1
            node_ids[f"result_{key}"] = node_id

            if include_values:
                label = f"{key}<br/><strong>{value}</strong>"
            else:
                label = key

            lines.append(f'    {node_id}["{label}"]:::resultNode')

        lines.append("")

        # Add edges (connections)
        lines.append("    %% Connections")

        # Connect sources to transformations
        for transform in lineage.transformations:
            transform_node = node_ids.get(f"transform_{transform.transformation_id}")
            if not transform_node:
                continue

            for input_name in transform.input_values.keys():
                source_node = node_ids.get(f"source_{input_name}")
                if source_node:
                    lines.append(f"    {source_node} --> {transform_node}")

        # Connect sources and transformations to calculations
        for calc in lineage.calculations:
            calc_node = node_ids.get(f"calc_{calc.step_name}")
            if not calc_node:
                continue

            for input_name in calc.inputs.keys():
                # Check if input comes from a source
                source_node = node_ids.get(f"source_{input_name}")
                if source_node:
                    lines.append(f"    {source_node} --> {calc_node}")
                    continue

                # Check if input comes from another calculation
                input_calc_node = node_ids.get(f"calc_{input_name}")
                if input_calc_node:
                    lines.append(f"    {input_calc_node} --> {calc_node}")

        # Connect calculations to final results
        for key in lineage.final_values.keys():
            calc_node = node_ids.get(f"calc_{key}")
            result_node = node_ids.get(f"result_{key}")

            if calc_node and result_node:
                lines.append(f"    {calc_node} --> {result_node}")

        return "\n".join(lines)

    def generate_mermaid_sequence(self, lineage: DataLineage) -> str:
        """
        Generate Mermaid.js sequence diagram.

        Shows the temporal sequence of data flow and calculations.

        Args:
            lineage: DataLineage object to visualize

        Returns:
            Mermaid.js sequence diagram code

        """
        lines = ["sequenceDiagram"]
        lines.append(f"    title Data Lineage Sequence for {lineage.ticker}")
        lines.append("")

        # Define participants
        lines.append("    participant Sources as Data Sources")
        lines.append("    participant Transform as Transformations")
        lines.append("    participant Calc as Calculations")
        lines.append("    participant Result as Final Results")
        lines.append("")

        # Add data source steps
        for source in lineage.sources:
            lines.append(f"    Sources->>Transform: {source.field_name} = {source.raw_value}")

        # Add transformation steps
        for transform in lineage.transformations:
            operation = transform.operation
            if transform.formula:
                operation += f" ({transform.formula})"
            lines.append(f"    Transform->>Calc: {operation}")

        # Add calculation steps
        for calc in lineage.calculations:
            formula = calc.formula or calc.calculation
            lines.append(f"    Calc->>Result: {calc.step_name} = {formula}")

        # Add final results
        for key, value in lineage.final_values.items():
            lines.append(f"    Result->>Result: {key} = {value}")

        return "\n".join(lines)

    def generate_mermaid_graph(self, lineage: DataLineage) -> str:
        """
        Generate Mermaid.js graph diagram.

        Shows relationships between all lineage components.

        Args:
            lineage: DataLineage object to visualize

        Returns:
            Mermaid.js graph code

        """
        lines = ["graph LR"]
        lines.append(f"    %% Data Lineage Graph for {lineage.ticker}")
        lines.append("")

        # Add nodes with styling
        node_counter = 0
        node_ids = {}

        # Sources
        for source in lineage.sources:
            node_id = f"S{node_counter}"
            node_counter += 1
            node_ids[f"source_{source.field_name}"] = node_id
            lines.append(f"    {node_id}[{source.field_name}]")
            lines.append(f"    style {node_id} fill:#e3f2fd,stroke:#1976d2")

        # Calculations
        for calc in lineage.calculations:
            node_id = f"C{node_counter}"
            node_counter += 1
            node_ids[f"calc_{calc.step_name}"] = node_id
            lines.append(f"    {node_id}[{calc.step_name}]")
            lines.append(f"    style {node_id} fill:#e8f5e9,stroke:#388e3c")

        lines.append("")

        # Add edges
        for calc in lineage.calculations:
            calc_node = node_ids.get(f"calc_{calc.step_name}")
            if not calc_node:
                continue

            for input_name in calc.inputs.keys():
                source_node = node_ids.get(f"source_{input_name}")
                if source_node:
                    lines.append(f"    {source_node} --> {calc_node}")

                input_calc_node = node_ids.get(f"calc_{input_name}")
                if input_calc_node:
                    lines.append(f"    {input_calc_node} --> {calc_node}")

        return "\n".join(lines)

    def generate_html_with_diagram(
        self, lineage: DataLineage, diagram_type: Literal["flowchart", "sequence", "graph"] = "flowchart"
    ) -> str:
        """
        Generate complete HTML page with embedded Mermaid.js diagram.

        Args:
            lineage: DataLineage object to visualize
            diagram_type: Type of diagram to generate

        Returns:
            Complete HTML page as string

        """
        # Generate diagram code
        if diagram_type == "flowchart":
            diagram_code = self.generate_mermaid_flowchart(lineage)
        elif diagram_type == "sequence":
            diagram_code = self.generate_mermaid_sequence(lineage)
        elif diagram_type == "graph":
            diagram_code = self.generate_mermaid_graph(lineage)
        else:
            raise ValueError(f"Invalid diagram type: {diagram_type}")

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Data Lineage - {lineage.ticker}</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        .info {{
            background-color: white;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .diagram-container {{
            background-color: white;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow-x: auto;
        }}
        .mermaid {{
            text-align: center;
        }}
    </style>
</head>
<body>
    <h1>📊 Data Lineage: {lineage.ticker}</h1>
    
    <div class="info">
        <p><strong>Asset Class:</strong> {lineage.asset_class}</p>
        <p><strong>Analysis Timestamp:</strong> {lineage.analysis_timestamp}</p>
        <p><strong>Scorer Version:</strong> {lineage.scorer_version or "N/A"}</p>
        <p><strong>Formula Version:</strong> {lineage.formula_version or "N/A"}</p>
        <p><strong>Completeness:</strong> {lineage.completeness * 100:.1f}%</p>
    </div>
    
    <div class="diagram-container">
        <div class="mermaid">
{diagram_code}
        </div>
    </div>
    
    <script>
        mermaid.initialize({{ startOnLoad: true, theme: 'default' }});
    </script>
</body>
</html>"""

        return html


# Convenience functions
def generate_mermaid_flowchart(lineage: DataLineage, direction: Literal["LR", "TD"] = "LR") -> str:
    """Generate Mermaid.js flowchart for lineage."""
    visualizer = LineageVisualizer()
    return visualizer.generate_mermaid_flowchart(lineage, direction)


def generate_mermaid_sequence(lineage: DataLineage) -> str:
    """Generate Mermaid.js sequence diagram for lineage."""
    visualizer = LineageVisualizer()
    return visualizer.generate_mermaid_sequence(lineage)


def generate_html_diagram(lineage: DataLineage, diagram_type: Literal["flowchart", "sequence", "graph"] = "flowchart") -> str:
    """Generate complete HTML page with Mermaid.js diagram."""
    visualizer = LineageVisualizer()
    return visualizer.generate_html_with_diagram(lineage, diagram_type)
