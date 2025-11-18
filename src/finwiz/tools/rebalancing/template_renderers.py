"""
Template renderers for rebalancing reports.

This module handles rendering and exporting of rebalancing report templates.
"""

import logging

from finwiz.tools.rebalancing.template_builders import TemplateBuilder

logger = logging.getLogger(__name__)


class TemplateRenderer:
    """Renderer for HTML templates used in rebalancing reports."""

    @staticmethod
    def get_pdf_export_note() -> str:
        """
        Get PDF export note for HTML reports.

        Returns:
            HTML comment with PDF export instructions

        """
        return """
        <!-- PDF Export Note -->
        <!-- This HTML report can be converted to PDF using tools like: -->
        <!-- - weasyprint: pip install weasyprint -->
        <!-- - pdfkit: pip install pdfkit (requires wkhtmltopdf) -->
        <!-- - playwright: pip install playwright -->
        <!-- Example: weasyprint report.html report.pdf -->
        """

    @staticmethod
    def add_interactive_elements(html_content: str) -> str:
        """
        Add interactive CSS and JavaScript to HTML content.

        Args:
            html_content: Original HTML content

        Returns:
            HTML content with interactive elements added

        """
        css = TemplateBuilder.get_rebalancing_css()
        js = TemplateBuilder.get_rebalancing_javascript()

        # Insert the enhanced CSS and JavaScript before the closing </head> tag
        head_close_index = html_content.find("</head>")
        if head_close_index != -1:
            html_content = html_content[:head_close_index] + css + js + html_content[head_close_index:]

        return html_content

    @staticmethod
    def prepare_pdf_export(html_content: str) -> str:
        """
        Prepare HTML content for PDF export.

        Args:
            html_content: Original HTML content

        Returns:
            HTML content prepared for PDF conversion

        """
        pdf_note = TemplateRenderer.get_pdf_export_note()
        return html_content.replace("</head>", f"{pdf_note}</head>")
