"""
Deep Analysis Report Generator.

Python-based HTML report generation using Jinja2 templates.
Replaces AI-based report generation with fast, deterministic templates.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)


class DeepAnalysisReportGenerator:
    """
    Python-based report generator for deep analysis results.

    Uses Jinja2 templates to generate professional HTML reports from
    DeepAnalysisResult data. Provides fast (<100ms), deterministic,
    and testable report generation without LLM calls.
    """

    def __init__(self, template_dir: str | Path | None = None):
        """
        Initialize the report generator.

        Args:
            template_dir: Directory containing Jinja2 templates.
                         Defaults to src/finwiz/templates/crew_reports/

        """
        if template_dir is None:
            # Default to crew_reports template directory
            current_file = Path(__file__)
            template_dir = current_file.parent.parent / "templates" / "crew_reports"

        self.template_dir = Path(template_dir)
        self.logger = logger

        # Initialize Jinja2 environment
        # Use parent directory so templates can reference each other correctly
        template_parent_dir = self.template_dir.parent
        self.env = Environment(
            loader=FileSystemLoader(str(template_parent_dir)),
            autoescape=True,  # Security: auto-escape HTML
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Load the deep analysis template
        try:
            self.template = self.env.get_template("crew_reports/deep_analysis_report.html.j2")
            self.logger.info(f"✅ Loaded deep analysis template from {self.template_dir}")
        except Exception as e:
            self.logger.error(f"❌ Failed to load deep analysis template: {e}")
            raise

    def generate_report(self, result_data: dict[str, Any]) -> str:
        """
        Generate HTML report from DeepAnalysisResult data.

        Args:
            result_data: Dictionary containing DeepAnalysisResult data
                        (either from DeepAnalysisResult.model_dump() or crew export)

        Returns:
            Complete HTML report as string

        Raises:
            ValueError: If required data fields are missing
            RuntimeError: If template rendering fails

        """
        start_time = time.time()

        try:
            # Validate required fields
            self._validate_input_data(result_data)

            # Prepare template variables
            template_vars = self._prepare_template_variables(result_data)

            # Render template
            html_content = self.template.render(**template_vars)

            # Calculate performance metrics
            execution_time = time.time() - start_time

            # Log performance (target: <100ms)
            if execution_time < 0.1:  # 100ms
                self.logger.info(f"✅ Report generated in {execution_time * 1000:.1f}ms for {result_data.get('ticker', 'unknown')} (target: <100ms)")
            else:
                self.logger.warning(f"⚠️ Report generation took {execution_time * 1000:.1f}ms for {result_data.get('ticker', 'unknown')} (target: <100ms)")

            return html_content

        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"❌ Report generation failed after {execution_time * 1000:.1f}ms for {result_data.get('ticker', 'unknown')}: {e}")
            raise RuntimeError(f"Failed to generate report: {e}") from e

    def _validate_input_data(self, data: dict[str, Any]) -> None:
        """
        Validate that required fields are present in input data.

        Args:
            data: Input data dictionary

        Raises:
            ValueError: If required fields are missing

        """
        required_fields = ["ticker", "asset_class", "composite_score", "grade", "recommendation", "confidence", "rationale"]

        missing_fields = []
        for field in required_fields:
            if field not in data or data[field] is None:
                missing_fields.append(field)

        if missing_fields:
            raise ValueError(f"Missing required fields for report generation: {missing_fields}")

        # Validate asset class
        valid_asset_classes = ["stock", "etf", "crypto"]
        if data["asset_class"] not in valid_asset_classes:
            raise ValueError(f"Invalid asset_class '{data['asset_class']}'. Must be one of: {valid_asset_classes}")

        # Validate grade
        valid_grades = ["A+", "A", "B", "C", "D", "F"]
        if data["grade"] not in valid_grades:
            raise ValueError(f"Invalid grade '{data['grade']}'. Must be one of: {valid_grades}")

        # Validate recommendation
        valid_recommendations = ["BUY", "HOLD", "SELL"]
        if data["recommendation"] not in valid_recommendations:
            raise ValueError(f"Invalid recommendation '{data['recommendation']}'. Must be one of: {valid_recommendations}")

    def _prepare_template_variables(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Prepare variables for template rendering.

        Args:
            data: Input data dictionary

        Returns:
            Dictionary of template variables

        """
        # Start with all input data
        template_vars = data.copy()

        # Add generation metadata
        template_vars["generation_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Ensure analysis_date is properly formatted
        if data.get("analysis_date"):
            if isinstance(data["analysis_date"], str):
                # Try to parse string date
                try:
                    template_vars["analysis_date"] = datetime.fromisoformat(data["analysis_date"].replace("Z", "+00:00"))
                except ValueError:
                    template_vars["analysis_date"] = datetime.now()
            elif not isinstance(data["analysis_date"], datetime):
                template_vars["analysis_date"] = datetime.now()
        else:
            template_vars["analysis_date"] = datetime.now()

        # Ensure component scores exist (required by template)
        template_vars.setdefault("fundamental_score", 0.5)
        template_vars.setdefault("technical_score", 0.5)
        template_vars.setdefault("risk_score", 0.5)

        # Ensure component details exist (for template safety)
        template_vars.setdefault("fundamental_details", {})
        template_vars.setdefault("technical_details", {})
        template_vars.setdefault("risk_details", {})

        # Ensure data sources exist
        if "data_sources" not in template_vars or not template_vars["data_sources"]:
            template_vars["data_sources"] = self._get_default_data_sources(data.get("asset_class", "stock"))

        # Ensure session_id exists
        template_vars.setdefault("session_id", "default")

        # Extract sentiment data for report enrichment (Phase 16)
        template_vars.setdefault("sentiment_data", data.get("sentiment_data", None))

        return template_vars

    def _get_default_data_sources(self, asset_class: str) -> list[str]:
        """Get default data sources based on asset class."""
        base_sources = ["Yahoo Finance API", "Moteur de scoring Python FinWiz"]

        if asset_class == "stock":
            base_sources.extend(["SEC EDGAR Database", "Alpha Vantage API"])
        elif asset_class == "etf":
            base_sources.extend(["ETF.com", "Morningstar"])
        elif asset_class == "crypto":
            base_sources.extend(["CoinMarketCap API", "CoinGecko API"])

        return base_sources

    def generate_and_save_report(self, result_data: dict[str, Any], output_path: str | Path) -> str:
        """
        Generate HTML report and save to file.

        Args:
            result_data: Dictionary containing DeepAnalysisResult data
            output_path: Path where to save the HTML file

        Returns:
            Generated HTML content

        Raises:
            ValueError: If required data fields are missing
            RuntimeError: If template rendering or file saving fails

        """
        try:
            # Generate HTML content
            html_content = self.generate_report(result_data)

            # Ensure output directory exists
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Save to file
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html_content)

            self.logger.info(f"✅ Report saved to {output_path} for {result_data.get('ticker', 'unknown')}")

            return html_content

        except Exception as e:
            self.logger.error(f"❌ Failed to generate and save report to {output_path}: {e}")
            raise

    def validate_template(self) -> bool:
        """
        Validate that the template can be loaded and rendered with sample data.

        Returns:
            True if template is valid, False otherwise

        """
        try:
            # Create sample data for validation
            sample_data = {
                "ticker": "TEST",
                "asset_class": "stock",
                "composite_score": 0.75,
                "grade": "A",
                "recommendation": "BUY",
                "confidence": 0.85,
                "rationale": "Sample rationale for template validation.",
                "fundamental_score": 0.80,
                "technical_score": 0.70,
                "risk_score": 0.75,
                "fundamental_details": {"roe": 0.15, "debt_to_equity": 0.3},
                "technical_details": {"rsi": 55.0, "trend_direction": "uptrend"},
                "risk_details": {"volatility": 0.20, "max_drawdown": -0.15, "beta": 1.1},
            }

            # Try to render template
            html_content = self.generate_report(sample_data)

            # Basic validation - check that key elements are present
            required_elements = ["TEST", "BUY", "Grade A", "75%"]
            for element in required_elements:
                if element not in html_content:
                    self.logger.error(f"Template validation failed: missing '{element}'")
                    return False

            self.logger.info("✅ Template validation successful")
            return True

        except Exception as e:
            self.logger.error(f"❌ Template validation failed: {e}")
            return False


# Convenience function for direct usage
def generate_deep_analysis_report(result_data: dict[str, Any]) -> str:
    """
    Convenience function to generate a deep analysis report.

    Args:
        result_data: Dictionary containing DeepAnalysisResult data

    Returns:
        Generated HTML report as string

    """
    generator = DeepAnalysisReportGenerator()
    return generator.generate_report(result_data)
