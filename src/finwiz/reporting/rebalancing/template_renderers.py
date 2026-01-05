"""
Template renderers for rebalancing reports.

This module handles rendering of rebalancing report templates.
"""

import logging

from finwiz.reporting.rebalancing.template_builders import TemplateBuilder

logger = logging.getLogger(__name__)


class TemplateRenderer:
    """Renderer for HTML templates used in rebalancing reports."""

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
