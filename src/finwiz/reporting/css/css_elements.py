"""Element-specific CSS styles for rebalancing reports.

Uses CSS variables from the shared design tokens (_design_tokens.html)
for consistent theming across all reports.
Asset files live in ../assets/css_*.css.
"""

from functools import cache
from pathlib import Path

_ASSETS = Path(__file__).parent.parent / "assets"


@cache
def get_base_styles() -> str:
    """Get base CSS styles for rebalancing reports."""
    return (_ASSETS / "css_base_styles.css").read_text(encoding="utf-8")


@cache
def get_table_styles() -> str:
    """Get table CSS styles."""
    return (_ASSETS / "css_table_styles.css").read_text(encoding="utf-8")


@cache
def get_action_styles() -> str:
    """Get action and status CSS styles."""
    return (_ASSETS / "css_action_styles.css").read_text(encoding="utf-8")


@cache
def get_trade_styles() -> str:
    """Get trade details CSS styles."""
    return (_ASSETS / "css_trade_styles.css").read_text(encoding="utf-8")


@cache
def get_risk_styles() -> str:
    """Get risk analysis CSS styles."""
    return (_ASSETS / "css_risk_styles.css").read_text(encoding="utf-8")


@cache
def get_cost_styles() -> str:
    """Get cost analysis CSS styles."""
    return (_ASSETS / "css_cost_styles.css").read_text(encoding="utf-8")
