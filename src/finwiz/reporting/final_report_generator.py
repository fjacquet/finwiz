"""
Final Report Generator - Python-based HTML generation (NO AI).

This module generates the final consolidated French report using Jinja2 templates
from consolidated JSON data. This is pure Python code - fast, testable, and free.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from jinja2 import TemplateNotFound

from finwiz.reporting.base_report_generator import create_report_jinja_env
from finwiz.schemas.crew_exports import ConsolidatedReportExport
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class FinalReportGenerator:
    """
    Generate final French report from consolidated JSON using Python templates.

    This class uses Jinja2 templates for HTML generation - NO AI agents involved.
    Benefits:
    - Fast: Milliseconds instead of seconds
    - Free: No LLM API costs
    - Testable: Unit tests with mock data
    - Deterministic: Same input = same output
    """

    def __init__(self, template_dir: str = "src/finwiz/templates") -> None:
        """
        Initialize Jinja2 environment with template directory.

        Args:
            template_dir: Path to templates directory

        """
        self.template_dir = Path(template_dir)

        # Initialize Jinja2 environment
        self.env = create_report_jinja_env(self.template_dir)

        logger.info(f"FinalReportGenerator initialized with template_dir: {template_dir}")

    def generate_final_report(self, consolidated_data: ConsolidatedReportExport, output_path: str | Path) -> str:
        """
        Generate final HTML report in French from consolidated data.

        This method:
        1. Loads the final_report.html Jinja2 template
        2. Prepares template data from consolidated export
        3. Renders template with data
        4. Saves HTML to specified path
        5. Returns path to generated file

        Completes in milliseconds (not seconds) - pure Python, no AI.

        Args:
            consolidated_data: ConsolidatedReportExport object with all crew results
            output_path: Path to save final HTML report

        Returns:
            Path to generated HTML file (as string)

        Raises:
            TemplateNotFound: If final_report.html template doesn't exist
            IOError: If unable to write output file

        """
        start_time = datetime.now()
        output_path = Path(output_path)

        logger.info(f"Generating final report for session: {consolidated_data.session_id}")

        try:
            # Load template
            template = self.env.get_template("crew_reports/final_report.html")
            logger.debug("Loaded final_report.html template")

            # Prepare template data
            template_data = self._prepare_template_data(consolidated_data)

            # Render template
            html_content = template.render(**template_data)  # nosemgrep: python.flask.security.xss.audit.direct-use-of-jinja2.direct-use-of-jinja2
            logger.debug(f"Rendered template ({len(html_content)} characters)")

            # Save to file
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(html_content, encoding="utf-8")

            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Final report generated successfully in {execution_time:.3f}s: {output_path}")

            return str(output_path)

        except TemplateNotFound as e:
            logger.error(f"Template not found: {e}")
            raise
        except OSError as e:
            logger.error(f"Failed to write output file {output_path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error generating final report: {e}", exc_info=True)
            raise

    def _prepare_template_data(self, consolidated_data: ConsolidatedReportExport) -> dict[str, Any]:
        """
        Prepare data dictionary for template rendering.

        Args:
            consolidated_data: ConsolidatedReportExport object

        Returns:
            Dictionary with all data needed by template

        """
        return {
            # Session metadata
            "session_id": consolidated_data.session_id,
            "consolidation_date": consolidated_data.consolidation_date,
            "total_time": consolidated_data.total_execution_time,
            # Crew results
            "stock_analyses": consolidated_data.stock_analyses,
            "etf_analyses": consolidated_data.etf_analyses,
            "crypto_analyses": consolidated_data.crypto_analyses,
            "deep_analyses": consolidated_data.deep_analyses,
            "discovery_results": consolidated_data.discovery_results,
            "rebalancing_results": consolidated_data.rebalancing_results,
            # Execution status
            "execution_status": consolidated_data.crew_execution_status,
            # Generation timestamp
            "generation_timestamp": datetime.now(),
        }

    def validate_template_exists(self) -> bool:
        """
        Validate that the final_report.html template exists.

        Returns:
            True if template exists, False otherwise

        """
        template_path = self.template_dir / "crew_reports" / "final_report.html"
        exists = template_path.exists()

        if exists:
            logger.debug(f"Template validated: {template_path}")
        else:
            logger.warning(f"Template not found: {template_path}")

        return exists

    def get_template_path(self) -> Path:
        """
        Get the full path to the final_report.html template.

        Returns:
            Path to final_report.html template

        """
        return self.template_dir / "crew_reports" / "final_report.html"
