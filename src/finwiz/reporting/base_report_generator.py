"""
Base Report Generator for crew-specific HTML reports.

Provides common functionality for Jinja2-based report generation:
- Template loading and environment setup
- Common filters (format_percentage, format_currency, format_date)
- Abstract interface for crew-specific generators
- Performance logging

This is the foundation for AI Minimalism - HTML generation via Python templates
instead of LLM calls (100% cost reduction, 500x faster, 100% reliable).
"""

import time
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


def create_report_jinja_env(template_dir: Path | str) -> Environment:
    """Jinja2 environment with the report-rendering configuration shared by all generators."""
    return Environment(  # nosemgrep: python.flask.security.xss.audit.direct-use-of-jinja2.direct-use-of-jinja2
        loader=FileSystemLoader(str(template_dir)),
        autoescape=True,  # Security: auto-escape HTML
        trim_blocks=True,
        lstrip_blocks=True,
    )


class BaseReportGenerator(ABC):
    """
    Abstract base class for crew-specific report generators.

    Subclasses must implement:
    - get_template_name(): Return the template path relative to templates dir
    - get_required_fields(): Return list of required data fields
    - prepare_template_variables(): Prepare data for template rendering
    """

    def __init__(self, template_dir: str | Path | None = None):
        """
        Initialize the report generator.

        Args:
            template_dir: Directory containing Jinja2 templates.
                         Defaults to src/finwiz/templates/

        """
        if template_dir is None:
            # Default to templates directory
            current_file = Path(__file__)
            template_dir = current_file.parent.parent / "templates"

        self.template_dir = Path(template_dir)
        self.logger = logger

        # Initialize Jinja2 environment with common configuration
        self.env = create_report_jinja_env(self.template_dir)

        # Register common filters
        self._register_common_filters()

        # Load template
        try:
            self.template = self.env.get_template(self.get_template_name())
            self.logger.info(f"Loaded template: {self.get_template_name()}")
        except Exception as e:
            self.logger.error(f"Failed to load template {self.get_template_name()}: {e}")
            raise

    def _register_common_filters(self) -> None:
        """Register common Jinja2 filters used across all report templates."""
        self.env.filters["format_percentage"] = self._format_percentage
        self.env.filters["format_currency"] = self._format_currency
        self.env.filters["format_date"] = self._format_date
        self.env.filters["format_number"] = self._format_number
        self.env.filters["grade_color"] = self._grade_color

    @staticmethod
    def _format_percentage(value: float | None, decimals: int = 1) -> str:
        """Format a decimal value as percentage."""
        if value is None:
            return "N/A"
        return f"{value * 100:.{decimals}f}%"

    @staticmethod
    def _format_currency(value: float | None, currency: str = "$", decimals: int = 2) -> str:
        """Format a value as currency."""
        if value is None:
            return "N/A"
        return f"{currency}{value:,.{decimals}f}"

    @staticmethod
    def _format_date(value: datetime | str | None, fmt: str = "%Y-%m-%d") -> str:
        """Format a datetime value."""
        if value is None:
            return "N/A"
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return str(value)
        return value.strftime(fmt)

    @staticmethod
    def _format_number(value: float | None, decimals: int = 2) -> str:
        """Format a number with thousands separators."""
        if value is None:
            return "N/A"
        return f"{value:,.{decimals}f}"

    @staticmethod
    def _grade_color(grade: str) -> str:
        """Return CSS color class for a grade."""
        colors = {
            "A+": "text-emerald-500",
            "A": "text-green-500",
            "B": "text-lime-500",
            "C": "text-yellow-500",
            "D": "text-orange-500",
            "F": "text-red-500",
        }
        return colors.get(grade, "text-gray-500")

    @abstractmethod
    def get_template_name(self) -> str:
        """
        Return the template path relative to templates directory.

        Returns:
            Template path (e.g., "crew_reports/stock_report.html")

        """
        pass

    @abstractmethod
    def get_required_fields(self) -> list[str]:
        """
        Return list of required fields for this report type.

        Returns:
            List of required field names

        """
        pass

    @abstractmethod
    def prepare_template_variables(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Prepare variables for template rendering.

        Args:
            data: Input data dictionary

        Returns:
            Dictionary of template variables

        """
        pass

    def _apply_common_defaults(self, template_vars: dict[str, Any]) -> dict[str, Any]:
        """Apply defaults that every subclass needs in prepare_template_variables.

        Handles: analysis_date formatting, session_id, data_sources guard,
        and report path defaults.  Call this once at the start of every
        subclass ``prepare_template_variables`` implementation (after
        ``template_vars = data.copy()``) so the common boilerplate stays in
        one place.

        Args:
            template_vars: Mutable copy of the input data dict.

        Returns:
            The same dict (mutated in-place and returned for chaining).

        """
        # Ensure analysis_date is formatted as a string for templates.
        if "analysis_date" not in template_vars or not template_vars["analysis_date"]:
            template_vars["analysis_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(template_vars["analysis_date"], datetime):
            template_vars["analysis_date"] = template_vars["analysis_date"].strftime("%Y-%m-%d %H:%M:%S")

        # Ensure session_id exists.
        template_vars.setdefault("session_id", "default")

        # Ensure data sources list exists (subclass _get_default_data_sources() provides the values).
        if "data_sources" not in template_vars or not template_vars["data_sources"]:
            template_vars["data_sources"] = self._get_default_data_sources()

        # Ensure report paths exist.
        template_vars.setdefault("report_json_path", "N/A")
        template_vars.setdefault("report_html_path", "N/A")

        return template_vars

    @abstractmethod
    def _get_default_data_sources(self) -> list[str]:
        """Return the default data-source list for this generator.

        Abstract so a new subclass cannot silently ship generic data-source
        attributions in its reports; ``_apply_common_defaults`` relies on it.

        Returns:
            List of data source description strings.

        """

    def validate_data(self, data: dict[str, Any]) -> bool:
        """
        Validate that required fields are present in input data.

        Args:
            data: Input data dictionary

        Returns:
            True if all required fields present

        Raises:
            ValueError: If required fields are missing

        """
        required = self.get_required_fields()
        missing = [f for f in required if f not in data or data[f] is None]

        if missing:
            raise ValueError(f"Missing required fields for report generation: {missing}")

        return True

    def generate_report(self, data: dict[str, Any]) -> str:
        """
        Generate HTML report from data.

        Args:
            data: Dictionary containing report data

        Returns:
            Complete HTML report as string

        Raises:
            ValueError: If required data fields are missing
            RuntimeError: If template rendering fails

        """
        start_time = time.time()

        try:
            # Validate required fields
            self.validate_data(data)

            # Prepare template variables (subclass implementation)
            prepared_data = self.prepare_template_variables(data)

            # Wrap in 'data' object as expected by templates
            template_vars = {
                "data": prepared_data,
                "generation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "generator_class": self.__class__.__name__,
            }

            # Render template
            html_content = self.template.render(**template_vars)

            # Performance logging (target: <100ms)
            execution_time = time.time() - start_time
            ticker = data.get("ticker", "unknown")
            if execution_time < 0.1:
                self.logger.info(f"Report generated in {execution_time * 1000:.1f}ms for {ticker}")
            else:
                self.logger.warning(f"Report generation took {execution_time * 1000:.1f}ms for {ticker} (target: <100ms)")

            return html_content

        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Report generation failed after {execution_time * 1000:.1f}ms: {e}")
            raise RuntimeError(f"Failed to generate report: {e}") from e

    def generate_and_save_report(self, data: dict[str, Any], output_path: str | Path) -> str:
        """
        Generate HTML report and save to file.

        Args:
            data: Dictionary containing report data
            output_path: Path where to save the HTML file

        Returns:
            Generated HTML content

        """
        try:
            html_content = self.generate_report(data)

            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html_content)

            self.logger.info(f"Report saved to {output_path}")
            return html_content

        except Exception as e:
            self.logger.error(f"Failed to generate and save report to {output_path}: {e}")
            raise

    def validate_template(self) -> bool:
        """
        Validate that the template can be loaded and rendered with sample data.

        Returns:
            True if template is valid, False otherwise

        """
        try:
            sample_data = self.get_sample_data()
            html_content = self.generate_report(sample_data)

            # Basic validation - check content was generated
            if not html_content or len(html_content) < 100:
                self.logger.error("Template validation failed: content too short")
                return False

            self.logger.info(f"Template validation successful for {self.__class__.__name__}")
            return True

        except Exception as e:
            self.logger.error(f"Template validation failed: {e}")
            return False

    def get_sample_data(self) -> dict[str, Any]:
        """
        Return sample data for template validation.

        Subclasses should override to provide type-specific sample data.

        Returns:
            Dictionary with sample data

        """
        # Default sample data - subclasses should override
        return {
            "ticker": "TEST",
            "asset_class": "stock",
            "composite_score": 0.75,
            "grade": "A",
            "recommendation": "BUY",
            "confidence": 0.85,
            "rationale": "Sample rationale for template validation.",
            "session_id": "test-session",
        }
