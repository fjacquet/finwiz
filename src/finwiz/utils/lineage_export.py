"""
Lineage Export Utility for FinWiz.

Provides export functionality for data lineage, including JSON export
and reproducibility code generation in Python and R.
"""

import logging
from pathlib import Path
from typing import Any

from finwiz.schemas.data_lineage import DataLineage

logger = logging.getLogger(__name__)


class LineageExporter:
    """
    Export data lineage to various formats.

    Supports JSON export, Python code generation, and R code generation
    for reproducibility.
    """

    def __init__(self, output_dir: Path | None = None):
        """
        Initialize lineage exporter.

        Args:
            output_dir: Optional directory for export files.
                       Defaults to current directory.

        """
        self.output_dir = output_dir or Path(".")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_json(self, lineage: DataLineage, filename: str | None = None) -> Path:
        """
        Export lineage to JSON file.

        Args:
            lineage: DataLineage object to export
            filename: Optional filename. Defaults to {ticker}_lineage.json

        Returns:
            Path to exported JSON file

        """
        if filename is None:
            filename = f"{lineage.ticker}_lineage.json"

        output_path = self.output_dir / filename

        try:
            # Export using Pydantic's model_dump_json for proper serialization
            json_data = lineage.model_dump_json(indent=2)

            with open(output_path, "w") as f:
                f.write(json_data)

            logger.info(f"Exported lineage for {lineage.ticker} to {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to export lineage to JSON: {e}")
            raise

    def load_json(self, filepath: Path | str) -> DataLineage:
        """
        Load lineage from JSON file.

        Args:
            filepath: Path to JSON file

        Returns:
            DataLineage object

        """
        try:
            with open(filepath) as f:
                return DataLineage.model_validate_json(f.read())

        except Exception as e:
            logger.error(f"Failed to load lineage from JSON: {e}")
            raise

    def generate_python_code(self, lineage: DataLineage) -> str:
        """
        Generate Python code to reproduce calculations.

        Args:
            lineage: DataLineage object

        Returns:
            Python code as string

        """
        code_lines = [
            '"""',
            f"Reproducibility code for {lineage.ticker} analysis.",
            "",
            f"Generated from lineage data on {lineage.analysis_timestamp}",
            f"Scorer version: {lineage.scorer_version}",
            f"Formula version: {lineage.formula_version}",
            '"""',
            "",
            "# Data sources",
        ]

        # Add data sources as variables
        for source in lineage.sources:
            code_lines.append(f"{source.field_name} = {repr(source.raw_value)}  # from {source.source_name}")

        code_lines.append("")
        code_lines.append("# Transformations")

        # Add transformations
        for transform in lineage.transformations:
            if transform.formula:
                code_lines.append(f"# {transform.operation}: {transform.formula}")
            for input_name, input_value in transform.input_values.items():
                code_lines.append(f"{input_name}_transformed = {repr(transform.output_value)}")

        code_lines.append("")
        code_lines.append("# Calculations")

        # Add calculations
        for calc in lineage.calculations:
            code_lines.append(f"# {calc.calculation}")
            if calc.formula:
                code_lines.append(f"# Formula: {calc.formula}")

            # Generate calculation code
            if calc.step_name == "composite_score":
                # Special handling for composite score
                inputs_str = ", ".join(f"{k}={v}" for k, v in calc.inputs.items())
                code_lines.append(f"{calc.step_name} = {calc.formula}  # {inputs_str}")
            elif calc.step_name == "grade":
                # Special handling for grade assignment
                code_lines.append(f"# Grading scale: {calc.metadata.get('grading_scale', {})}")
                code_lines.append(f"{calc.step_name} = {repr(calc.output)}")
            else:
                code_lines.append(f"{calc.step_name} = {repr(calc.output)}")

            code_lines.append("")

        # Add final values
        code_lines.append("# Final results")
        for key, value in lineage.final_values.items():
            code_lines.append(f"final_{key} = {repr(value)}")

        code_lines.append("")
        code_lines.append("# Verification")
        code_lines.append(f'print(f"Ticker: {lineage.ticker}")')
        code_lines.append(f'print(f"Asset Class: {lineage.asset_class}")')
        for key, value in lineage.final_values.items():
            code_lines.append(f'print(f"{key}: {{final_{key}}}")')

        return "\n".join(code_lines)

    def generate_r_code(self, lineage: DataLineage) -> str:
        """
        Generate R code to reproduce calculations.

        Args:
            lineage: DataLineage object

        Returns:
            R code as string

        """
        code_lines = [
            "# Reproducibility code for " + lineage.ticker + " analysis",
            "#",
            "# Generated from lineage data on " + lineage.analysis_timestamp,
            "# Scorer version: " + str(lineage.scorer_version),
            "# Formula version: " + str(lineage.formula_version),
            "",
            "# Data sources",
        ]

        # Add data sources as variables
        for source in lineage.sources:
            r_value = self._python_to_r_value(source.raw_value)
            code_lines.append(f"{source.field_name} <- {r_value}  # from {source.source_name}")

        code_lines.append("")
        code_lines.append("# Transformations")

        # Add transformations
        for transform in lineage.transformations:
            if transform.formula:
                code_lines.append(f"# {transform.operation}: {transform.formula}")
            for input_name, input_value in transform.input_values.items():
                r_value = self._python_to_r_value(transform.output_value)
                code_lines.append(f"{input_name}_transformed <- {r_value}")

        code_lines.append("")
        code_lines.append("# Calculations")

        # Add calculations
        for calc in lineage.calculations:
            code_lines.append(f"# {calc.calculation}")
            if calc.formula:
                # Convert Python formula to R syntax
                r_formula = calc.formula.replace("*", " * ").replace("+", " + ")
                code_lines.append(f"# Formula: {r_formula}")

            # Generate calculation code
            if calc.step_name == "composite_score":
                # Special handling for composite score
                r_formula = calc.formula.replace("*", " * ")
                code_lines.append(f"{calc.step_name} <- {r_formula}")
            elif calc.step_name == "grade":
                # Special handling for grade assignment
                code_lines.append(f"# Grading scale: {calc.metadata.get('grading_scale', {})}")
                r_value = self._python_to_r_value(calc.output)
                code_lines.append(f"{calc.step_name} <- {r_value}")
            else:
                r_value = self._python_to_r_value(calc.output)
                code_lines.append(f"{calc.step_name} <- {r_value}")

            code_lines.append("")

        # Add final values
        code_lines.append("# Final results")
        for key, value in lineage.final_values.items():
            r_value = self._python_to_r_value(value)
            code_lines.append(f"final_{key} <- {r_value}")

        code_lines.append("")
        code_lines.append("# Verification")
        code_lines.append(f'cat("Ticker: {lineage.ticker}\\n")')
        code_lines.append(f'cat("Asset Class: {lineage.asset_class}\\n")')
        for key in lineage.final_values.keys():
            code_lines.append(f'cat("{key}:", final_{key}, "\\n")')

        return "\n".join(code_lines)

    def _python_to_r_value(self, value: Any) -> str:
        """
        Convert Python value to R syntax.

        Args:
            value: Python value

        Returns:
            R syntax string

        """
        if isinstance(value, bool):
            return "TRUE" if value else "FALSE"
        elif isinstance(value, str):
            return f'"{value}"'
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, dict):
            # Convert dict to R list
            items = [f"{k}={self._python_to_r_value(v)}" for k, v in value.items()]
            return f"list({', '.join(items)})"
        elif isinstance(value, list):
            # Convert list to R vector
            items = [self._python_to_r_value(v) for v in value]
            return f"c({', '.join(items)})"
        elif value is None:
            return "NULL"
        else:
            return repr(value)

    def export_python_code(self, lineage: DataLineage, filename: str | None = None) -> Path:
        """
        Export Python reproducibility code to file.

        Args:
            lineage: DataLineage object
            filename: Optional filename. Defaults to {ticker}_reproduce.py

        Returns:
            Path to exported Python file

        """
        if filename is None:
            filename = f"{lineage.ticker}_reproduce.py"

        output_path = self.output_dir / filename

        try:
            python_code = self.generate_python_code(lineage)

            with open(output_path, "w") as f:
                f.write(python_code)

            logger.info(f"Exported Python code for {lineage.ticker} to {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to export Python code: {e}")
            raise

    def export_r_code(self, lineage: DataLineage, filename: str | None = None) -> Path:
        """
        Export R reproducibility code to file.

        Args:
            lineage: DataLineage object
            filename: Optional filename. Defaults to {ticker}_reproduce.R

        Returns:
            Path to exported R file

        """
        if filename is None:
            filename = f"{lineage.ticker}_reproduce.R"

        output_path = self.output_dir / filename

        try:
            r_code = self.generate_r_code(lineage)

            with open(output_path, "w") as f:
                f.write(r_code)

            logger.info(f"Exported R code for {lineage.ticker} to {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to export R code: {e}")
            raise

    def export_all(self, lineage: DataLineage, base_filename: str | None = None) -> dict[str, Path]:
        """
        Export lineage in all formats.

        Args:
            lineage: DataLineage object
            base_filename: Optional base filename (without extension)

        Returns:
            Dictionary mapping format to file path

        """
        if base_filename is None:
            base_filename = lineage.ticker

        exports = {}

        try:
            exports["json"] = self.export_json(lineage, f"{base_filename}_lineage.json")
            exports["python"] = self.export_python_code(lineage, f"{base_filename}_reproduce.py")
            exports["r"] = self.export_r_code(lineage, f"{base_filename}_reproduce.R")

            logger.info(f"Exported all formats for {lineage.ticker}")
            return exports

        except Exception as e:
            logger.error(f"Failed to export all formats: {e}")
            raise


# Convenience functions
def export_lineage_json(lineage: DataLineage, output_path: Path | str) -> Path:
    """Export lineage to JSON file."""
    exporter = LineageExporter(output_dir=Path(output_path).parent)
    return exporter.export_json(lineage, Path(output_path).name)


def export_lineage_python(lineage: DataLineage, output_path: Path | str) -> Path:
    """Export Python reproducibility code."""
    exporter = LineageExporter(output_dir=Path(output_path).parent)
    return exporter.export_python_code(lineage, Path(output_path).name)


def export_lineage_r(lineage: DataLineage, output_path: Path | str) -> Path:
    """Export R reproducibility code."""
    exporter = LineageExporter(output_dir=Path(output_path).parent)
    return exporter.export_r_code(lineage, Path(output_path).name)
