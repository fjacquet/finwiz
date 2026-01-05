"""
Template management for rebalancing reports.

This module provides backward compatibility for template management.
The actual implementation has been split into:
- template_builders.py: CSS and JavaScript builders
- template_renderers.py: HTML rendering
"""

import logging

from finwiz.reporting.rebalancing.template_builders import TemplateBuilder
from finwiz.reporting.rebalancing.template_renderers import TemplateRenderer

logger = logging.getLogger(__name__)


class RebalancingTemplates:
    """
    Template and styling management for rebalancing reports.

    This class provides backward compatibility by delegating to the split
    TemplateBuilder and TemplateRenderer classes.
    """

    @staticmethod
    def get_rebalancing_css() -> str:
        """
        Get CSS styles for rebalancing reports.

        Returns:
            CSS styles as string

        """
        return TemplateBuilder.get_rebalancing_css()

    @staticmethod
    def get_rebalancing_javascript() -> str:
        """
        Get JavaScript code for rebalancing reports.

        Returns:
            JavaScript code as string

        """
        return TemplateBuilder.get_rebalancing_javascript()

    @staticmethod
    def add_interactive_elements(html_content: str) -> str:
        """
        Add interactive CSS and JavaScript to HTML content.

        Args:
            html_content: Original HTML content

        Returns:
            HTML content with interactive elements added

        """
        return TemplateRenderer.add_interactive_elements(html_content)
