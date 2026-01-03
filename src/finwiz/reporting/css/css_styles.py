"""CSS styles for rebalancing reports."""

from finwiz.reporting.css.css_elements import (
    get_action_styles,
    get_base_styles,
    get_cost_styles,
    get_risk_styles,
    get_table_styles,
    get_trade_styles,
)
from finwiz.reporting.css.css_layouts import (
    get_execution_styles,
    get_interactive_styles,
    get_responsive_styles,
    get_scenario_styles,
)


def get_rebalancing_css() -> str:
    """
    Get CSS styles for rebalancing reports.

    Returns:
        CSS styles as string

    """
    css_parts = [
        get_base_styles(),
        get_table_styles(),
        get_action_styles(),
        get_trade_styles(),
        get_risk_styles(),
        get_cost_styles(),
        get_scenario_styles(),
        get_execution_styles(),
        get_interactive_styles(),
        get_responsive_styles(),
    ]

    return f"<style>\n{''.join(css_parts)}\n</style>"
