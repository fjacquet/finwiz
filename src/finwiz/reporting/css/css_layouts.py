"""Layout and interactive CSS styles for rebalancing reports.

Uses CSS variables from the shared design tokens (_design_tokens.html)
for consistent theming across all reports.
Asset files live in ../assets/css_*.css.
"""

from functools import cache
from pathlib import Path

_ASSETS = Path(__file__).parent.parent / "assets"


@cache
def get_scenario_styles() -> str:
    """Get scenario card CSS styles."""
    return (_ASSETS / "css_scenario_styles.css").read_text(encoding="utf-8")


@cache
def get_execution_styles() -> str:
    """Get execution summary CSS styles."""
    return (_ASSETS / "css_execution_styles.css").read_text(encoding="utf-8")


@cache
def get_interactive_styles() -> str:
    """Get interactive element CSS styles."""
    return (_ASSETS / "css_interactive_styles.css").read_text(encoding="utf-8")


@cache
def get_responsive_styles() -> str:
    """Get responsive and print CSS styles."""
    return (_ASSETS / "css_responsive_styles.css").read_text(encoding="utf-8")
