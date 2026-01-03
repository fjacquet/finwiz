"""
Unit tests for lineage visualizer.

Tests the LineageVisualizer class and Mermaid.js diagram generation.
"""

from datetime import datetime

import pytest

from finwiz.schemas.data_lineage import DataLineage
from finwiz.reporting.data_lineage.lineage_visualizer import (
    LineageVisualizer,
    generate_html_diagram,
    generate_mermaid_flowchart,
    generate_mermaid_sequence,
)


@pytest.fixture
def sample_lineage():
    """Create sample lineage for testing."""
    lineage = DataLineage(
        ticker="AAPL",
        asset_class="stock",
        scorer_version="1.0.0",
        formula_version="1.0.0",
    )

    # Add data sources
    lineage.add_source(
        source_id="src_1",
        source_type="api",
        source_name="Yahoo Finance",
        field_name="volatility",
        raw_value=0.25,
        timestamp=datetime.now().isoformat(),
    )

    lineage.add_source(
        source_id="src_2",
        source_type="api",
        source_name="Yahoo Finance",
        field_name="max_drawdown",
        raw_value=-0.15,
        timestamp=datetime.now().isoformat(),
    )

    # Add calculation
    lineage.add_calculation(
        step_id="calc_1",
        step_name="composite_score",
        inputs={"volatility": 0.25, "max_drawdown": -0.15},
        calculation="Weighted average",
        formula="0.4*volatility + 0.3*max_drawdown",
        output=0.85,
    )

    lineage.add_calculation(
        step_id="calc_2",
        step_name="grade",
        inputs={"composite_score": 0.85},
        calculation="Grade assignment",
        output="A+",
    )

    # Set final values
    lineage.final_values = {"composite_score": 0.85, "grade": "A+"}

    return lineage


class TestLineageVisualizer:
    """Test suite for LineageVisualizer class."""

    def test_should_initialize_visualizer(self):
        """Test LineageVisualizer initialization."""
        visualizer = LineageVisualizer()

        assert visualizer is not None
        assert visualizer.logger is not None

    def test_should_generate_mermaid_flowchart(self, sample_lineage):
        """Test generating Mermaid.js flowchart."""
        visualizer = LineageVisualizer()

        diagram = visualizer.generate_mermaid_flowchart(sample_lineage)

        assert "flowchart LR" in diagram
        assert "AAPL" in diagram
        assert "volatility" in diagram
        assert "max_drawdown" in diagram
        assert "composite_score" in diagram
        assert "grade" in diagram
        assert "sourceNode" in diagram
        assert "calcNode" in diagram

    def test_should_generate_flowchart_with_td_direction(self, sample_lineage):
        """Test generating flowchart with top-down direction."""
        visualizer = LineageVisualizer()

        diagram = visualizer.generate_mermaid_flowchart(sample_lineage, direction="TD")

        assert "flowchart TD" in diagram

    def test_should_generate_flowchart_without_values(self, sample_lineage):
        """Test generating flowchart without values in labels."""
        visualizer = LineageVisualizer()

        diagram = visualizer.generate_mermaid_flowchart(sample_lineage, include_values=False)

        assert "flowchart LR" in diagram
        assert "volatility" in diagram
        # Values should not be in labels
        assert "0.25" not in diagram or "<br/>0.25<br/>" not in diagram

    def test_should_include_node_styles(self, sample_lineage):
        """Test that diagram includes node style definitions."""
        visualizer = LineageVisualizer()

        diagram = visualizer.generate_mermaid_flowchart(sample_lineage)

        assert "classDef sourceNode" in diagram
        assert "classDef calcNode" in diagram
        assert "classDef resultNode" in diagram
        assert "fill:#e3f2fd" in diagram  # Source node color
        assert "fill:#e8f5e9" in diagram  # Calc node color

    def test_should_include_connections(self, sample_lineage):
        """Test that diagram includes connections between nodes."""
        visualizer = LineageVisualizer()

        diagram = visualizer.generate_mermaid_flowchart(sample_lineage)

        # Should have arrows connecting nodes
        assert "-->" in diagram

    def test_should_generate_mermaid_sequence_diagram(self, sample_lineage):
        """Test generating Mermaid.js sequence diagram."""
        visualizer = LineageVisualizer()

        diagram = visualizer.generate_mermaid_sequence(sample_lineage)

        assert "sequenceDiagram" in diagram
        assert "AAPL" in diagram
        assert "Data Sources" in diagram
        assert "Calculations" in diagram
        assert "Final Results" in diagram
        assert "->>" in diagram  # Sequence diagram arrows

    def test_should_generate_mermaid_graph(self, sample_lineage):
        """Test generating Mermaid.js graph diagram."""
        visualizer = LineageVisualizer()

        diagram = visualizer.generate_mermaid_graph(sample_lineage)

        assert "graph LR" in diagram
        assert "AAPL" in diagram
        assert "volatility" in diagram
        assert "composite_score" in diagram
        assert "style" in diagram  # Node styling

    def test_should_generate_html_with_flowchart(self, sample_lineage):
        """Test generating complete HTML page with flowchart."""
        visualizer = LineageVisualizer()

        html = visualizer.generate_html_with_diagram(sample_lineage, diagram_type="flowchart")

        assert "<!DOCTYPE html>" in html
        assert "<html" in html
        assert "mermaid" in html
        assert "AAPL" in html
        assert "flowchart LR" in html
        assert "script" in html

    def test_should_generate_html_with_sequence_diagram(self, sample_lineage):
        """Test generating HTML page with sequence diagram."""
        visualizer = LineageVisualizer()

        html = visualizer.generate_html_with_diagram(sample_lineage, diagram_type="sequence")

        assert "<!DOCTYPE html>" in html
        assert "sequenceDiagram" in html

    def test_should_generate_html_with_graph(self, sample_lineage):
        """Test generating HTML page with graph diagram."""
        visualizer = LineageVisualizer()

        html = visualizer.generate_html_with_diagram(sample_lineage, diagram_type="graph")

        assert "<!DOCTYPE html>" in html
        assert "graph LR" in html

    def test_should_raise_error_for_invalid_diagram_type(self, sample_lineage):
        """Test that invalid diagram type raises error."""
        visualizer = LineageVisualizer()

        with pytest.raises(ValueError, match="Invalid diagram type"):
            visualizer.generate_html_with_diagram(sample_lineage, diagram_type="invalid")

    def test_should_include_metadata_in_html(self, sample_lineage):
        """Test that HTML includes lineage metadata."""
        visualizer = LineageVisualizer()

        html = visualizer.generate_html_with_diagram(sample_lineage)

        assert "Asset Class:" in html
        assert "stock" in html
        assert "Analysis Timestamp:" in html
        assert "Scorer Version:" in html
        assert "Completeness:" in html

    def test_should_handle_empty_lineage(self):
        """Test handling lineage with no sources or calculations."""
        lineage = DataLineage(ticker="TEST", asset_class="stock")
        visualizer = LineageVisualizer()

        diagram = visualizer.generate_mermaid_flowchart(lineage)

        assert "flowchart LR" in diagram
        assert "TEST" in diagram


class TestConvenienceFunctions:
    """Test suite for convenience functions."""

    def test_should_generate_flowchart_via_convenience_function(self, sample_lineage):
        """Test generate_mermaid_flowchart convenience function."""
        diagram = generate_mermaid_flowchart(sample_lineage)

        assert "flowchart LR" in diagram
        assert "AAPL" in diagram

    def test_should_generate_flowchart_with_td_direction(self, sample_lineage):
        """Test flowchart with TD direction via convenience function."""
        diagram = generate_mermaid_flowchart(sample_lineage, direction="TD")

        assert "flowchart TD" in diagram

    def test_should_generate_sequence_via_convenience_function(self, sample_lineage):
        """Test generate_mermaid_sequence convenience function."""
        diagram = generate_mermaid_sequence(sample_lineage)

        assert "sequenceDiagram" in diagram
        assert "AAPL" in diagram

    def test_should_generate_html_via_convenience_function(self, sample_lineage):
        """Test generate_html_diagram convenience function."""
        html = generate_html_diagram(sample_lineage)

        assert "<!DOCTYPE html>" in html
        assert "AAPL" in html
        assert "mermaid" in html
