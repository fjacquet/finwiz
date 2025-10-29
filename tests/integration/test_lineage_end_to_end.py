"""
Integration test for data lineage end-to-end.

Tests the complete lineage workflow from creation to export and visualization.
"""

import json
from datetime import datetime

import pytest

from finwiz.schemas.data_lineage import DataLineage
from finwiz.utils.lineage_export import LineageExporter
from finwiz.utils.lineage_html_integration import (
    add_lineage_to_report_data,
    generate_lineage_section_html,
    get_lineage_quality_badge,
)
from finwiz.utils.lineage_query import LineageQuery
from finwiz.utils.lineage_visualizer import LineageVisualizer


@pytest.mark.integration
class TestLineageEndToEnd:
    """Integration tests for complete lineage workflow."""

    def test_complete_lineage_workflow(self, tmp_path):
        """Test complete workflow: create → query → export → visualize → HTML."""
        # Step 1: Create lineage
        lineage = DataLineage(
            ticker="AAPL",
            asset_class="stock",
            scorer_version="1.0.0",
            formula_version="1.0.0",
        )

        # Add data sources
        lineage.add_source(
            source_id="src_volatility",
            source_type="api",
            source_name="Yahoo Finance",
            field_name="volatility",
            raw_value=0.25,
            timestamp=datetime.now().isoformat(),
            metadata={"endpoint": "/quote"},
        )

        lineage.add_source(
            source_id="src_max_drawdown",
            source_type="api",
            source_name="Yahoo Finance",
            field_name="max_drawdown",
            raw_value=-0.15,
            timestamp=datetime.now().isoformat(),
        )

        lineage.add_source(
            source_id="src_beta",
            source_type="default",
            source_name="DeepAnalysisScorer",
            field_name="beta",
            raw_value=1.0,
            timestamp=datetime.now().isoformat(),
            metadata={"reason": "field_missing"},
        )

        # Add transformations
        lineage.add_transformation(
            transformation_id="trans_volatility",
            operation="type_conversion",
            input_values={"volatility": "0.25"},
            output_value=0.25,
            formula="float(value)",
        )

        # Add calculations
        lineage.add_calculation(
            step_id="calc_composite",
            step_name="composite_score",
            inputs={"volatility": 0.25, "max_drawdown": -0.15, "beta": 1.0},
            calculation="Weighted average of risk metrics",
            formula="0.4*volatility + 0.3*max_drawdown + 0.3*beta",
            output=0.85,
            metadata={"weights": {"volatility": 0.4, "max_drawdown": 0.3, "beta": 0.3}},
        )

        lineage.add_calculation(
            step_id="calc_grade",
            step_name="grade",
            inputs={"composite_score": 0.85},
            calculation="Grade assignment based on composite score",
            formula="grading_scale[0.850]",
            output="A+",
            metadata={"grading_scale": {"A+": 0.80, "A": 0.70, "B": 0.60}},
        )

        # Set final values
        lineage.final_values = {
            "composite_score": 0.85,
            "grade": "A+",
            "volatility": 0.25,
            "max_drawdown": -0.15,
            "beta": 1.0,
        }

        # Verify lineage structure
        assert lineage.ticker == "AAPL"
        assert len(lineage.sources) == 3
        assert len(lineage.transformations) == 1
        assert len(lineage.calculations) == 2
        assert lineage.completeness == 1.0

        # Step 2: Query lineage
        query = LineageQuery()

        # Query ticker lineage
        ticker_lineage = query.get_ticker_lineage("AAPL", lineage=lineage)
        assert ticker_lineage is not None
        assert ticker_lineage.ticker == "AAPL"

        # Query metric lineage
        vol_lineage = query.get_metric_lineage("AAPL", "volatility", lineage=lineage)
        assert vol_lineage is not None
        assert vol_lineage["metric"] == "volatility"
        assert vol_lineage["source"].raw_value == 0.25
        assert len(vol_lineage["transformations"]) == 1
        assert len(vol_lineage["calculations"]) == 1

        # Query score lineage
        score_lineage = query.get_score_lineage("AAPL", "composite_score", lineage=lineage)
        assert score_lineage is not None
        assert score_lineage["output"] == 0.85
        assert len(score_lineage["inputs"]) == 3

        # Query grade lineage
        grade_lineage = query.get_grade_lineage("AAPL", lineage=lineage)
        assert grade_lineage is not None
        assert grade_lineage["grade"] == "A+"
        assert grade_lineage["composite_score"] == 0.85

        # Get defaulted fields
        defaulted = query.get_defaulted_fields("AAPL", lineage=lineage)
        assert "beta" in defaulted

        # Get lineage summary
        summary = query.get_lineage_summary("AAPL", lineage=lineage)
        assert summary["total_sources"] == 3
        assert summary["total_calculations"] == 2
        assert summary["completeness"] == 1.0

        # Step 3: Export lineage
        exporter = LineageExporter(output_dir=tmp_path)

        # Export JSON
        json_path = exporter.export_json(lineage)
        assert json_path.exists()
        assert json_path.suffix == ".json"

        # Verify JSON content
        with open(json_path) as f:
            json_data = json.load(f)
            assert json_data["ticker"] == "AAPL"
            assert len(json_data["sources"]) == 3

        # Load JSON back
        loaded_lineage = exporter.load_json(json_path)
        assert loaded_lineage.ticker == "AAPL"
        assert len(loaded_lineage.sources) == 3

        # Export Python code
        python_path = exporter.export_python_code(lineage)
        assert python_path.exists()
        assert python_path.suffix == ".py"

        # Verify Python code
        python_code = python_path.read_text()
        assert "volatility = 0.25" in python_code
        assert "composite_score" in python_code
        assert "0.4*volatility + 0.3*max_drawdown + 0.3*beta" in python_code

        # Verify Python syntax
        compile(python_code, str(python_path), "exec")

        # Export R code
        r_path = exporter.export_r_code(lineage)
        assert r_path.exists()
        assert r_path.suffix == ".R"

        # Verify R code
        r_code = r_path.read_text()
        assert "volatility <- 0.25" in r_code
        assert "composite_score" in r_code

        # Export all formats
        all_exports = exporter.export_all(lineage)
        assert "json" in all_exports
        assert "python" in all_exports
        assert "r" in all_exports

        # Step 4: Visualize lineage
        visualizer = LineageVisualizer()

        # Generate Mermaid flowchart
        flowchart = visualizer.generate_mermaid_flowchart(lineage)
        assert "flowchart LR" in flowchart
        assert "volatility" in flowchart
        assert "composite_score" in flowchart
        assert "sourceNode" in flowchart
        assert "calcNode" in flowchart

        # Generate sequence diagram
        sequence = visualizer.generate_mermaid_sequence(lineage)
        assert "sequenceDiagram" in sequence
        assert "AAPL" in sequence

        # Generate graph
        graph = visualizer.generate_mermaid_graph(lineage)
        assert "graph LR" in graph
        assert "volatility" in graph

        # Generate HTML with diagram
        html = visualizer.generate_html_with_diagram(lineage)
        assert "<!DOCTYPE html>" in html
        assert "mermaid" in html
        assert "AAPL" in html

        # Step 5: HTML integration
        lineage_dict = lineage.model_dump()

        # Generate lineage section HTML
        section_html = generate_lineage_section_html(lineage_dict, "AAPL")
        assert "Data Lineage" in section_html
        assert "mermaid" in section_html
        assert "beta" in section_html  # Defaulted field warning

        # Add lineage to report data
        report_data = {"ticker": "AAPL", "grade": "A+", "score": 0.85}
        updated_report = add_lineage_to_report_data(report_data, lineage_dict)
        assert updated_report["has_lineage"] is True
        assert "lineage_summary" in updated_report
        assert updated_report["lineage_summary"]["total_sources"] == 3
        assert "beta" in updated_report["lineage_summary"]["defaulted_fields"]

        # Get quality badge
        badge = get_lineage_quality_badge(lineage_dict)
        assert "badge" in badge
        assert "⚠️" in badge  # Has defaults

        # Step 6: Verify complete workflow
        assert lineage.ticker == "AAPL"
        assert json_path.exists()
        assert python_path.exists()
        assert r_path.exists()
        assert "flowchart" in flowchart  # Mermaid syntax
        assert updated_report["has_lineage"] is True

        print("\n✅ Complete lineage workflow test passed!")
        print(f"   - Created lineage with {len(lineage.sources)} sources")
        print(f"   - Queried {len(lineage.calculations)} calculations")
        print(f"   - Exported to {len(all_exports)} formats")
        print(f"   - Generated {3} diagram types")
        print("   - Integrated into HTML reports")
        print(f"   - All files saved to {tmp_path}")

    def test_lineage_with_no_defaults(self, tmp_path):
        """Test lineage workflow with high-quality data (no defaults)."""
        lineage = DataLineage(ticker="MSFT", asset_class="stock")

        # Add only API sources (no defaults)
        lineage.add_source(
            source_id="src_1",
            source_type="api",
            source_name="Yahoo Finance",
            field_name="volatility",
            raw_value=0.20,
            timestamp=datetime.now().isoformat(),
        )

        lineage.add_calculation(
            step_id="calc_1",
            step_name="composite_score",
            inputs={"volatility": 0.20},
            calculation="Score calculation",
            output=0.90,
        )

        lineage.final_values = {"composite_score": 0.90, "grade": "A+"}

        # Get quality badge
        badge = get_lineage_quality_badge(lineage.model_dump())
        assert "✅ High Quality Data" in badge
        assert "#28a745" in badge  # Green color

        # Export and verify
        exporter = LineageExporter(output_dir=tmp_path)
        json_path = exporter.export_json(lineage, "msft_high_quality.json")
        assert json_path.exists()

        print("\n✅ High-quality lineage test passed!")
        print("   - No defaulted fields")
        print("   - Quality badge: High Quality Data")

    def test_lineage_with_many_defaults(self, tmp_path):
        """Test lineage workflow with low-quality data (many defaults)."""
        lineage = DataLineage(ticker="TEST", asset_class="stock")

        # Add mostly default sources
        lineage.add_source(
            source_id="src_1",
            source_type="default",
            source_name="Default",
            field_name="volatility",
            raw_value=0.20,
            timestamp=datetime.now().isoformat(),
        )

        lineage.add_source(
            source_id="src_2",
            source_type="default",
            source_name="Default",
            field_name="beta",
            raw_value=1.0,
            timestamp=datetime.now().isoformat(),
        )

        lineage.final_values = {"composite_score": 0.60, "grade": "C"}

        # Get quality badge
        badge = get_lineage_quality_badge(lineage.model_dump())
        assert "⚠️ Limited Data" in badge
        assert "#dc3545" in badge  # Red color

        # Generate HTML section
        html = generate_lineage_section_html(lineage.model_dump(), "TEST")
        assert "⚠️ Note:" in html
        assert "default values" in html

        print("\n✅ Low-quality lineage test passed!")
        print("   - 2 defaulted fields")
        print("   - Quality badge: Limited Data")
        print("   - Warning displayed in HTML")
