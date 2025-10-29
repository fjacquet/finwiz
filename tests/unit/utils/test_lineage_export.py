"""
Unit tests for lineage export utility.

Tests the LineageExporter class and export functions for JSON,
Python, and R code generation.
"""

from datetime import datetime
from pathlib import Path

import pytest

from finwiz.schemas.data_lineage import DataLineage
from finwiz.utils.lineage_export import LineageExporter, export_lineage_json, export_lineage_python, export_lineage_r


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
        metadata={"weights": {"volatility": 0.4, "max_drawdown": 0.3}},
    )

    lineage.add_calculation(
        step_id="calc_2",
        step_name="grade",
        inputs={"composite_score": 0.85},
        calculation="Grade assignment",
        output="A+",
        metadata={"grading_scale": {"A+": 0.80, "A": 0.70}},
    )

    # Set final values
    lineage.final_values = {"composite_score": 0.85, "grade": "A+"}

    return lineage


class TestLineageExporter:
    """Test suite for LineageExporter class."""

    def test_should_initialize_with_default_output_dir(self):
        """Test LineageExporter initialization with default directory."""
        exporter = LineageExporter()

        assert exporter.output_dir == Path(".")

    def test_should_initialize_with_custom_output_dir(self, tmp_path):
        """Test LineageExporter initialization with custom directory."""
        exporter = LineageExporter(output_dir=tmp_path)

        assert exporter.output_dir == tmp_path
        assert tmp_path.exists()

    def test_should_export_lineage_to_json(self, sample_lineage, tmp_path):
        """Test exporting lineage to JSON file."""
        exporter = LineageExporter(output_dir=tmp_path)

        output_path = exporter.export_json(sample_lineage)

        assert output_path.exists()
        assert output_path.name == "AAPL_lineage.json"
        assert output_path.parent == tmp_path

        # Verify JSON content
        loaded_lineage = DataLineage.model_validate_json(output_path.read_text())
        assert loaded_lineage.ticker == "AAPL"
        assert loaded_lineage.asset_class == "stock"
        assert len(loaded_lineage.sources) == 2
        assert len(loaded_lineage.calculations) == 2

    def test_should_export_json_with_custom_filename(self, sample_lineage, tmp_path):
        """Test exporting JSON with custom filename."""
        exporter = LineageExporter(output_dir=tmp_path)

        output_path = exporter.export_json(sample_lineage, "custom_lineage.json")

        assert output_path.exists()
        assert output_path.name == "custom_lineage.json"

    def test_should_load_lineage_from_json(self, sample_lineage, tmp_path):
        """Test loading lineage from JSON file."""
        exporter = LineageExporter(output_dir=tmp_path)

        # Export first
        output_path = exporter.export_json(sample_lineage)

        # Load back
        loaded_lineage = exporter.load_json(output_path)

        assert loaded_lineage.ticker == sample_lineage.ticker
        assert loaded_lineage.asset_class == sample_lineage.asset_class
        assert len(loaded_lineage.sources) == len(sample_lineage.sources)
        assert len(loaded_lineage.calculations) == len(sample_lineage.calculations)

    def test_should_generate_python_code(self, sample_lineage):
        """Test generating Python reproducibility code."""
        exporter = LineageExporter()

        python_code = exporter.generate_python_code(sample_lineage)

        assert "AAPL" in python_code
        assert "volatility = 0.25" in python_code
        assert "max_drawdown = -0.15" in python_code
        assert "composite_score" in python_code
        assert "grade" in python_code
        assert "0.4*volatility + 0.3*max_drawdown" in python_code

    def test_should_generate_valid_python_syntax(self, sample_lineage):
        """Test that generated Python code has valid syntax."""
        exporter = LineageExporter()

        python_code = exporter.generate_python_code(sample_lineage)

        # Try to compile the code (will raise SyntaxError if invalid)
        compile(python_code, "<string>", "exec")

    def test_should_generate_r_code(self, sample_lineage):
        """Test generating R reproducibility code."""
        exporter = LineageExporter()

        r_code = exporter.generate_r_code(sample_lineage)

        assert "AAPL" in r_code
        assert "volatility <- 0.25" in r_code
        assert "max_drawdown <- -0.15" in r_code
        assert "composite_score" in r_code
        assert "grade" in r_code
        assert "<-" in r_code  # R assignment operator

    def test_should_convert_python_values_to_r(self, sample_lineage):
        """Test Python to R value conversion."""
        exporter = LineageExporter()

        # Test boolean
        assert exporter._python_to_r_value(True) == "TRUE"
        assert exporter._python_to_r_value(False) == "FALSE"

        # Test string
        assert exporter._python_to_r_value("test") == '"test"'

        # Test numbers
        assert exporter._python_to_r_value(42) == "42"
        assert exporter._python_to_r_value(3.14) == "3.14"

        # Test None
        assert exporter._python_to_r_value(None) == "NULL"

        # Test list
        assert exporter._python_to_r_value([1, 2, 3]) == "c(1, 2, 3)"

        # Test dict
        r_dict = exporter._python_to_r_value({"a": 1, "b": 2})
        assert "list(" in r_dict
        assert "a=1" in r_dict
        assert "b=2" in r_dict

    def test_should_export_python_code_to_file(self, sample_lineage, tmp_path):
        """Test exporting Python code to file."""
        exporter = LineageExporter(output_dir=tmp_path)

        output_path = exporter.export_python_code(sample_lineage)

        assert output_path.exists()
        assert output_path.name == "AAPL_reproduce.py"
        assert output_path.suffix == ".py"

        # Verify content
        python_code = output_path.read_text()
        assert "volatility = 0.25" in python_code
        assert "composite_score" in python_code

    def test_should_export_r_code_to_file(self, sample_lineage, tmp_path):
        """Test exporting R code to file."""
        exporter = LineageExporter(output_dir=tmp_path)

        output_path = exporter.export_r_code(sample_lineage)

        assert output_path.exists()
        assert output_path.name == "AAPL_reproduce.R"
        assert output_path.suffix == ".R"

        # Verify content
        r_code = output_path.read_text()
        assert "volatility <- 0.25" in r_code
        assert "composite_score" in r_code

    def test_should_export_all_formats(self, sample_lineage, tmp_path):
        """Test exporting all formats at once."""
        exporter = LineageExporter(output_dir=tmp_path)

        exports = exporter.export_all(sample_lineage)

        assert "json" in exports
        assert "python" in exports
        assert "r" in exports

        assert exports["json"].exists()
        assert exports["python"].exists()
        assert exports["r"].exists()

        assert exports["json"].suffix == ".json"
        assert exports["python"].suffix == ".py"
        assert exports["r"].suffix == ".R"

    def test_should_export_all_with_custom_base_filename(self, sample_lineage, tmp_path):
        """Test exporting all formats with custom base filename."""
        exporter = LineageExporter(output_dir=tmp_path)

        exports = exporter.export_all(sample_lineage, "custom_analysis")

        assert exports["json"].name == "custom_analysis_lineage.json"
        assert exports["python"].name == "custom_analysis_reproduce.py"
        assert exports["r"].name == "custom_analysis_reproduce.R"


class TestConvenienceFunctions:
    """Test suite for convenience functions."""

    def test_should_export_json_via_convenience_function(self, sample_lineage, tmp_path):
        """Test export_lineage_json convenience function."""
        output_path = tmp_path / "test_lineage.json"

        result_path = export_lineage_json(sample_lineage, output_path)

        assert result_path.exists()
        assert result_path == output_path

    def test_should_export_python_via_convenience_function(self, sample_lineage, tmp_path):
        """Test export_lineage_python convenience function."""
        output_path = tmp_path / "test_reproduce.py"

        result_path = export_lineage_python(sample_lineage, output_path)

        assert result_path.exists()
        assert result_path == output_path

    def test_should_export_r_via_convenience_function(self, sample_lineage, tmp_path):
        """Test export_lineage_r convenience function."""
        output_path = tmp_path / "test_reproduce.R"

        result_path = export_lineage_r(sample_lineage, output_path)

        assert result_path.exists()
        assert result_path == output_path
