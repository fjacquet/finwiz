"""
Utilities for converting files, e.g., HTML to PDF.

Defines `HtmlToPdfTool`, a CrewAI BaseTool that converts a local HTML file
to a PDF using WeasyPrint.
"""

import logging
import os

from crewai.tools import BaseTool
from weasyprint import HTML

logger = logging.getLogger(__name__)


class HtmlToPdfTool(BaseTool):
    """Convert a local HTML file to a PDF using WeasyPrint."""

    name: str = "HTML to PDF Converter"
    description: str = "Converts an HTML file to a PDF file. Input must be the full path to the HTML file."

    def _run(self, html_file_path: str) -> str:
        """
        Convert `html_file_path` to PDF and return a status message.

        Returns an error string if the input file does not exist or is not .html.
        """
        try:
            if not os.path.exists(html_file_path):
                return f"Error: HTML file not found at {html_file_path}"

            if not html_file_path.lower().endswith(".html"):
                return f"Error: Input file {html_file_path} is not an HTML file."

            base_name = os.path.splitext(html_file_path)[0]
            pdf_file_path = base_name + ".pdf"

            HTML(filename=html_file_path).write_pdf(pdf_file_path)
            logger.info(f"Successfully converted {html_file_path} to {pdf_file_path}")
            return f"Successfully converted {html_file_path} to {pdf_file_path}. PDF saved at {pdf_file_path}"
        except Exception as e:
            logger.error(f"Error converting {html_file_path} to PDF: {e}", exc_info=True)
            return f"Error converting {html_file_path} to PDF: {e}"
