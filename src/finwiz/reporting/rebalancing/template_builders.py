"""
Template builders for rebalancing reports.

This module delegates to CSS and JavaScript builders for template generation.
"""

import logging

from finwiz.reporting.css.css_styles import get_rebalancing_css
from finwiz.reporting.js.javascript_code import get_rebalancing_javascript

logger = logging.getLogger(__name__)


class TemplateBuilder:
    """Builder for CSS and JavaScript templates used in rebalancing reports."""

    @staticmethod
    def get_rebalancing_css() -> str:
        """
        Get CSS styles for rebalancing reports.

        Returns:
            CSS styles as string

        """
        return get_rebalancing_css()

    @staticmethod
    def get_rebalancing_javascript() -> str:
        """
        Get JavaScript code for rebalancing reports.

        Returns:
            JavaScript code as string

        """
        return get_rebalancing_javascript()
